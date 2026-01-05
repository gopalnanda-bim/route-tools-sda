# -*- coding: utf-8 -*-
# Draw Route (v1.0.0) — robust lib imports
# - Click devices in order (Esc to finish)
# - Draws Detail Lines
# - Sets:
#   * FOLLOW_FIELD = sequence number
#   * LEAD_FIELD   = same value for all picked
# - Max item cap, duplicate-safe

__title__   = "Draw Route"
__version__ = "1.0.0"
__author__  = "Gopal Nanda"

# ---------- robust lib loader ----------
import os, sys
script_dir = os.path.dirname(__file__)
ext_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(script_dir))))
lib_path = os.path.join(ext_root, "lib")
if lib_path not in sys.path:
    sys.path.append(lib_path)

from param_utils import coerce_set_text_param
from view_utils import is_2d_view_supporting_detail_curves, get_elem_point_on_view_plane
# -------------------------------------

from pyrevit import revit, forms
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI.Selection import ObjectType, ISelectionFilter
from Autodesk.Revit.Exceptions import OperationCanceledException
from System.Collections.Generic import List

doc   = revit.doc
uidoc = revit.uidoc
view  = doc.ActiveView

# ---- Defaults ----
DEFAULT_LEAD_FIELD = "ibb_Stromkreis"
DEFAULT_FOLL_FIELD = "ibb_Nummer"
DEFAULT_LEAD_VALUE = "1"
DEFAULT_START_NUM  = "1"
DEFAULT_MAX_ITEMS  = "20"
PAD_LEN            = 1
# ------------------

def abort(msg, title="Cancelled"):
    forms.alert(msg, title=title)
    raise SystemExit

def list_line_styles():
    out = []
    try:
        lines_cat = doc.Settings.Categories.get_Item(BuiltInCategory.OST_Lines)
        for sc in lines_cat.SubCategories:
            gs = sc.GetGraphicsStyle(GraphicsStyleType.Projection)
            if gs:
                out.append((sc.Name, gs))
    except:
        pass
    out.sort(key=lambda t: t[0].lower())
    return out

def choose_line_style():
    items = list_line_styles()
    if not items:
        abort("No line styles found under category 'Lines'.", "Error")

    names = [n for n,_ in items]
    picked = forms.SelectFromList.show(
        names,
        title="Choose line style",
        multiselect=False,
        default_selection=[names[0]]
    )
    if not picked:
        raise SystemExit
    return picked, dict(items)[picked]

def ensure_sketch_plane(v):
    if v.SketchPlane:
        return
    origin = getattr(v, "Origin", XYZ(0,0,0))
    plane = Plane.CreateByNormalAndOrigin(XYZ.BasisZ, origin)
    t = Transaction(doc, "Create SketchPlane")
    t.Start()
    v.SketchPlane = SketchPlane.Create(doc, plane)
    t.Commit()

def create_detail_line(v, p1, p2, gs):
    z = getattr(v, "Origin", XYZ(0,0,0)).Z
    p1 = XYZ(p1.X, p1.Y, z)
    p2 = XYZ(p2.X, p2.Y, z)
    dl = doc.Create.NewDetailCurve(v, Line.CreateBound(p1, p2))
    if gs:
        dl.LineStyle = gs

class ParamFilter(ISelectionFilter):
    def __init__(self, lead, foll):
        self.lead = lead
        self.foll = foll
    def AllowElement(self, e):
        if not e: return False
        return (e.LookupParameter(self.lead) and
                e.LookupParameter(self.foll))
    def AllowReference(self, ref, pt): return False

# ----------- Guard -----------
if not is_2d_view_supporting_detail_curves(view):
    abort("This tool only works in 2D views (Plan / RCP / Drafting).", "Unsupported View")

# ----------- Setup -----------
lead_field = forms.ask_for_string(DEFAULT_LEAD_FIELD, "Leading field (loop / circuit):")
if not lead_field: raise SystemExit

foll_field = forms.ask_for_string(DEFAULT_FOLL_FIELD, "Numbering field:")
if not foll_field: raise SystemExit

lead_value = forms.ask_for_string(DEFAULT_LEAD_VALUE, "Leading field value:")
if not lead_value: raise SystemExit

start_num = int(forms.ask_for_string(DEFAULT_START_NUM, "Start number:"))
max_items = int(forms.ask_for_string(DEFAULT_MAX_ITEMS, "Maximum number of devices:"))

line_name, gs = choose_line_style()

summary = (
    "Summary\n\n"
    "Leading field: {lf} = {lv}\n"
    "Numbering field: {ff}\n"
    "Start number: {sn}\n"
    "Max devices: {mx}\n"
    "Line style: {ls}\n\n"
    "Start now?"
).format(lf=lead_field, lv=lead_value, ff=foll_field, sn=start_num, mx=max_items, ls=line_name)

if not forms.alert(summary, title="Confirm", yes=True, no=True):
    raise SystemExit

ensure_sketch_plane(view)

forms.alert("Click devices in order.\nPress Esc to finish.", title="Draw Route", ok=False)

# ----------- Picking -----------
picked = []
points = []
clicked = set()
filt = ParamFilter(lead_field, foll_field)

t = Transaction(doc, "Draw Route")
t.Start()

n = start_num
while True:
    if len(picked) >= max_items:
        break
    try:
        ref = uidoc.Selection.PickObject(ObjectType.Element, filt, "Pick next device")
    except OperationCanceledException:
        break

    e = doc.GetElement(ref.ElementId)
    if e.Id in clicked:
        continue
    clicked.add(e.Id)

    pt = get_elem_point_on_view_plane(e, view)
    if not pt:
        continue

    coerce_set_text_param(e.LookupParameter(foll_field), str(n).zfill(PAD_LEN))

    if points:
        create_detail_line(view, points[-1], pt, gs)

    picked.append(e)
    points.append(pt)
    n += 1

for e in picked:
    coerce_set_text_param(e.LookupParameter(lead_field), lead_value)

t.Commit()

uidoc.Selection.SetElementIds(List[ElementId]([e.Id for e in picked]))

forms.alert(
    "Done.\n\n"
    "Devices: {cnt}\n"
    "{ff}: {a} .. {b}".format(
        cnt=len(picked),
        ff=foll_field,
        a=start_num,
        b=n-1
    ),
    title="Draw Route"
)
