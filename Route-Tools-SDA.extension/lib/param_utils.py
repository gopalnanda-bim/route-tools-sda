# -*- coding: utf-8 -*-
from Autodesk.Revit.DB import StorageType

def coerce_set_text_param(p, text_value):
    """Set String param; set Integer param if digits; return True/False."""
    if not p or p.IsReadOnly:
        return False
    try:
        st = p.StorageType
        if st == StorageType.String:
            p.Set(text_value)
            return True
        if st == StorageType.Integer:
            s = (text_value or "").strip()
            if s.lstrip("-").isdigit():
                p.Set(int(s))
                return True
            return False
        return False
    except:
        return False
