# -*- coding: utf-8 -*-
# Reorder Route (v1.0.0) — robust lib imports
# Workflow:
# 1) Select route Detail Lines first (TAB chain selection), then run tool
# 2) Tool reconstructs the chain, matches endpoints to nearby elements (SNAP)
# 3) Then asks: which FIELD to renumber, start, max items, reverse, etc.
# 4) Optional: set a leading/loop field=value for all affected
# 5) Optional: pick custom START element
# 6) Summary confirm -> apply -> report

__title__   = "Reorder Route"
__version__ = "1.0.0"
__author__  = "Gopal Nanda"

# ---------- robust lib loader (NO package imports) ----------
import os
import sys

script_dir = os.path.dirname(__file__)
# script.py -> .pushbutton -> .panel -> .tab -> .extension
ext_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(script_dir))))
lib_path = os.path.join(ext_root, "lib")
if lib_path not in sys.path:
    sys.path.append(lib_path)

from param_utils import coerce_set_text_param
from view_utils import is_2d_view_supporting_detail_curves, get_elem_point_on_view_plane
# -----------------------------------------------------------

from pyrevit import revit, forms
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI.Selection import ISelectionFilter, ObjectType
from Autodesk.Revit.Exceptions import OperationCanceledException
from System.Collections.Generic import List

doc   = revit.doc
uidoc = revit.uidoc
view  = doc.ActiveView

# --- settings ---
FT_PER_MM = 1.0 / 304.8
PAD_LEN   = 1
SNAP_MM   = 250.0
SNAP_FT2  = (SNAP_MM * FT_PER_MM) ** 2
DEFAULT_MAX_SEQ = 20

DEFAULT_LEAD_FIELD = "ibb_Stromkreis"
DEFAULT_LEAD_VALUE = "1"
# ----------------

def abort(msg, title="Cancelled"):
    forms.alert(msg, title=title)
    raise SystemExit

def pt2d(xyz):
    return XYZ(xyz.X, xyz.Y, 0.0)

def dist2(a, b):
    dx = a.X - b.X
    dy = a.Y - b.Y
    return dx*dx + dy*dy

class Node(object):
    __slots__ = ("pt", "edges", "id")
    def __init__(self, pt, nid):
        self.pt = pt
        self.edges = []
        self.id = nid

def add_node(nodes, pt, tol2):
    for n in nodes:
        if dist2(n.pt, pt) <= tol2:
            return n
    nd = Node(pt, len(nodes))
    nodes.append(nd)
    return nd

def traverse_chain(nodes, start_id, visited_edge):
    order = [start_id]
    prev  = None
    cur   = start_id
    while True:
        nbrs = nodes[cur].edges[:]
        if prev is not None and prev in nbrs:
            nbrs.remove(prev)

        next_id = None
        for nb in nbrs:
            key = tuple(sorted((cur, nb)))
            if key not in visited_edge:
                next_id = nb
                visited_edge.add(key)
                break

        if next_id is None:
            break

        order.append(next_id)
        prev, cur = cur, next_id

    return order

class AnyElementFilter(ISelectionFilter):
    def AllowElement(self, e):
        return True if e else False
    def AllowReference(self, ref, pt):
        return False

def get_writable_param_names_intersection(elems):
    """Show only fields that are writable (String/Integer) on ALL matched elements."""
    if not elems:
        return []

    sets = []
    for e in elems:
        s = set()
        try:
            for p in e.Parameters:
                if (p and (not p.IsReadOnly) and p.Definition and
                    p.StorageType in (StorageType.String, StorageType.Integer)):
                    s.add(p.Definition.Name)
        except:
            pass
        sets.append(s)

    inter = set.intersection(*sets) if sets else set()
    return sorted(list(inter), key=lambda x: x.lower())

# ----------------- START -----------------
if not is_2d_view_supporting_detail_curves(view):
    abort("This tool only works in 2D views (Plan / RCP / Drafting).", title="Unsupported View")

# 1) Collect selected detail lines
sel_ids = list(uidoc.Selection.GetElementIds())
if not sel_ids:
    abort("Select your route Detail Lines first (TAB chain selection), then run this tool.", title="No Selection")

curves = []
for eid in sel_ids:
    el = doc.GetElement(eid)
    if not isinstance(el, CurveElement) or not el.ViewSpecific:
        continue
    crv = el.GeometryCurve
    if crv and crv.IsBound:
        curves.append((pt2d(crv.GetEndPoint(0)), pt2d(crv.GetEndPoint(1))))

if not curves:
    abort("No valid Detail Lines found in your selection.", title="Nothing to Do")

# 2) Build chain(s)
nodes = []
tol2 = (3.0 * FT_PER_MM) ** 2  # ~3mm tolerance
for p0, p1 in curves:
    n0 = add_node(nodes, p0, tol2)
    n1 = add_node(nodes, p1, tol2)
    n0.edges.append(n1.id)
    n1.edges.append(n0.id)

start_nodes = [n.id for n in nodes if len(n.edges) == 1] or [nodes[0].id]
visited = set()
chains  = []

for sid in start_nodes:
    if len(nodes[sid].edges) == 0:
        continue
    order = traverse_chain(nodes, sid, visited)
    if order and len(order) > 1:
        chains.append(order)

if not chains:
    abort("Could not reconstruct a route from the selected lines. Check for gaps.", title="No Route Detected")

# 3) Find candidates in view
candidates = []
for e in FilteredElementCollector(doc, view.Id).WhereElementIsNotElementType():
    pt = get_elem_point_on_view_plane(e, view)
    if not pt:
        continue
    candidates.append((e, pt2d(pt)))

if not candidates:
    abort("No elements with usable location found in this view.", title="Nothing to Do")

# 4) Match route nodes -> nearest elements
used = set()
matched = []

for order in chains:
    for nid in order:
        pt = nodes[nid].pt
        best = None
        bestd2 = None
        for e, ep in candidates:
            if e.Id in used:
                continue
            d2 = dist2(pt, ep)
            if d2 <= SNAP_FT2 and (bestd2 is None or d2 < bestd2):
                best, bestd2 = e, d2
        if best:
            matched.append(best)
            used.add(best.Id)

if not matched:
    abort("No devices matched to the selected route.\nCurrent SNAP is {:.0f} mm.".format(SNAP_MM),
          title="No Matches Found")

# 5) Ask what to do with this route (field to renumber)
param_choices = get_writable_param_names_intersection(matched)
if not param_choices:
    abort("No common writable String/Integer instance field found on ALL matched elements.",
          title="No Fields Found")

foll_field = forms.SelectFromList.show(
    param_choices,
    title="What should happen to this route?",
    multiselect=False,
    button_name="Renumber this field"
)
if not foll_field:
    raise SystemExit

# 6) Ask renumber settings
start_str = forms.ask_for_string(default="1", prompt="Start number for '{}':".format(foll_field))
if start_str is None:
    raise SystemExit
start_str = start_str.strip()
if not start_str.lstrip("-").isdigit():
    abort("Start number must be an integer.", title="Invalid Input")
start_num = int(start_str)

max_str = forms.ask_for_string(default=str(DEFAULT_MAX_SEQ), prompt="Max devices to renumber on this route:")
if max_str is None:
    raise SystemExit
max_str = max_str.strip()
if (not max_str.isdigit()) or int(max_str) <= 0:
    abort("Max devices must be a positive integer.", title="Invalid Input")
MAX_SEQ = int(max_str)

reverse = forms.alert("Reverse direction?", title="Direction", yes=True, no=True, cancel=False)

set_loop = forms.alert(
    "Also set a leading/loop field for ALL affected devices?",
    title="Leading Field",
    yes=True, no=True, cancel=False
)

lead_field = None
lead_value = None
if set_loop:
    lead_field = forms.ask_for_string(default=DEFAULT_LEAD_FIELD, prompt="Leading field name (e.g. ibb_Stromkreis):")
    if lead_field is None:
        raise SystemExit
    lead_field = lead_field.strip()
    if not lead_field:
        abort("Leading field name cannot be empty.", title="Invalid Input")

    lead_value = forms.ask_for_string(default=DEFAULT_LEAD_VALUE, prompt="Value to set for '{}':".format(lead_field))
    if lead_value is None:
        raise SystemExit
    lead_value = lead_value.strip()
    if not lead_value:
        abort("Leading field value cannot be empty.", title="Invalid Input")

pick_start = forms.alert(
    "Pick a custom START device?",
    title="Start Device",
    yes=True, no=True, cancel=False
)

# Prepare list, cap, direction
to_renumber = matched[:]
if len(to_renumber) > MAX_SEQ:
    to_renumber = to_renumber[:MAX_SEQ]

if pick_start:
    try:
        picked_ref = uidoc.Selection.PickObject(ObjectType.Element, AnyElementFilter(), "Pick START device")
        start_elem = doc.GetElement(picked_ref.ElementId)
        if start_elem in to_renumber:
            idx = to_renumber.index(start_elem)
            to_renumber = to_renumber[idx:] + to_renumber[:idx]
        else:
            forms.alert("That device is not part of the matched route. Using auto-start.", title="Note")
    except OperationCanceledException:
        pass
    except:
        pass

if reverse:
    to_renumber.reverse()

# 7) Summary confirmation
summary = (
    "Summary\n\n"
    "Detected devices on route: {m}\n"
    "Will update (cap {mx}): {c}\n\n"
    "Renumber:\n"
    "  Field: {ff}\n"
    "  Range: {a} -> {b}\n"
    "  Direction: {dir}\n\n"
    "{loop}"
    "Apply now?"
).format(
    m=len(matched),
    mx=MAX_SEQ,
    c=len(to_renumber),
    ff=foll_field,
    a=start_num,
    b=start_num + len(to_renumber) - 1,
    dir=("Reversed" if reverse else "Forward"),
    loop=("Leading:\n  {} = '{}'\n\n".format(lead_field, lead_value) if set_loop else "")
)

if not forms.alert(summary, title="Confirm", yes=True, no=True, cancel=False):
    raise SystemExit

# 8) Apply (single transaction)
lead_fail = 0
num_fail  = 0

t = Transaction(doc, "Reorder Route")
t.Start()

if set_loop:
    for e in to_renumber:
        p = e.LookupParameter(lead_field)
        if not coerce_set_text_param(p, lead_value):
            lead_fail += 1

n = start_num
for e in to_renumber:
    p = e.LookupParameter(foll_field)
    val = str(n).zfill(PAD_LEN) if PAD_LEN else str(n)
    if not coerce_set_text_param(p, val):
        num_fail += 1
    n += 1

t.Commit()

uidoc.Selection.SetElementIds(List[ElementId]([e.Id for e in to_renumber]))

forms.alert(
    "Done.\n\n"
    "Updated: {cnt}\n"
    "Range: {a} .. {b}\n"
    "SNAP: {snap:.0f} mm\n"
    "{warn}".format(
        cnt=len(to_renumber),
        a=start_num,
        b=n - 1,
        snap=SNAP_MM,
        warn=("Warnings: {} renumber failed, {} leading failed.".format(num_fail, lead_fail)
              if (num_fail or lead_fail) else "")
    ),
    title="Reorder Route"
)
