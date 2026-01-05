# -*- coding: utf-8 -*-
from Autodesk.Revit.DB import ViewType, XYZ, LocationPoint, LocationCurve

def is_2d_view_supporting_detail_curves(v):
    bad = [ViewType.ThreeD, ViewType.Schedule, ViewType.DrawingSheet]
    return v and hasattr(v, "ViewType") and (v.ViewType not in bad)

def get_elem_point_on_view_plane(e, v):
    """Prefer LocationPoint/Curve; fallback to bbox; project Z to view plane."""
    p = None
    try:
        loc = e.Location
        if isinstance(loc, LocationPoint):
            p = loc.Point
        elif isinstance(loc, LocationCurve):
            p = loc.Curve.Evaluate(0.5, True)
    except:
        p = None

    if p is None:
        bb = e.get_BoundingBox(v) or e.get_BoundingBox(None)
        if not bb:
            return None
        p = (bb.Min + bb.Max) * 0.5

    z = getattr(v, "Origin", XYZ(0,0,0)).Z if hasattr(v, "Origin") else p.Z
    return XYZ(p.X, p.Y, z)
