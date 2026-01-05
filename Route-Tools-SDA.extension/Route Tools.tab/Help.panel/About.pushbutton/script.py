# -*- coding: utf-8 -*-
from pyrevit import forms

forms.alert(
    "SDA Route Tools\n\n"
    "Version: 1.0.0\n"
    "Author: Gopal Nanda\n\n"
    "Description:\n"
    "Tools for routing, numbering, and reordering technical devices in Revit.\n"
    "Designed for:\n"
    "- Sicherheitsbeleuchtung\n"
    "- Brandmeldeanlagen (BMA)\n"
    "- Sprachalarmanlagen (SAA)\n\n"
    "Workflow:\n"
    "• Draw Route: Click devices to draw routes and assign loop + numbering\n"
    "• Reorder Route: Select route lines and renumber devices automatically\n\n"
    "Notes:\n"
    "• Works in 2D views (Plan / RCP)\n"
    "• Parameters must be writable (String / Integer)\n\n"
    "Contact:\n"
    "LinkedIn: linkedin.com/in/gopal-nanda\n"
    "GitHub: github.com/<your-username>",
    title="About SDA Route Tools"
)
