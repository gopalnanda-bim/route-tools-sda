# route-tools-sda

**pyRevit tools for routing and numbering electrical devices in Revit**

## Who is this for?

This extension is designed for:

- Electrical planners (Elektroplaner)
- BIM modellers working in TGA
- Fire alarm (BMA), emergency lighting (Sicherheitsbeleuchtung),
  and PA / SAA projects



---

## Background: Numbering in German execution planning

In German TGA execution planning (Ausführungsplanung), systems such as:

- Emergency Lighting (Sicherheitsbeleuchtung)
- Fire Alarm Systems (BMA)
- Voice Alarm / PA Systems (SAA / ELA)

follow a **two-level numbering logic**.

Each device is identified by:
- a **loop / circuit number**
- and a **device number within that loop**

Typical notation:

- `1 / 1` to `1 / 10` → devices on loop 1  
- `2 / 1` to `2 / 10` → devices on loop 2  

In Revit, these values are usually stored in **two separate instance parameters**.

Assigning and maintaining this numbering manually is:
- time-consuming
- error-prone
- difficult to update when layouts change

---

## Features

### Draw Route

- Run the tool in a 2D plan view
- Click devices in the desired order along a system route
- The tool:
  - Draws route detail lines
  - Assigns a common loop / circuit value to all selected devices
  - Automatically numbers devices sequentially within that loop
  - Applies a configurable maximum device count

Example result:
- Loop `1` → `1/1`, `1/2`, `1/3`, …
- Loop `2` → `2/1`, `2/2`, `2/3`, …

---

### Reorder Route

- Select existing route detail lines (TAB to select the connected chain)
- Run the tool
- Choose which parameter should be renumbered
- The tool:
  - Detects devices along the route
  - Renumbers them based on route direction
  - Optionally reverses direction
  - Optionally assigns a loop / circuit value

This is especially useful when layouts change and numbering must be corrected
without manually editing parameters.

---

## Why this matters in practice

The route lines represent **real system logic**:

- Each line corresponds to one loop or circuit
- The line becomes the reference for numbering consistency

Instead of manually managing multiple parameters,
the planner controls numbering **graphically and logically** through routes.

This significantly speeds up execution planning
and reduces numbering errors in real projects.

---

## Requirements

- Autodesk Revit 2020 or newer
- pyRevit (IronPython)
- 2D Views only (Plan / RCP / Drafting)

## Installation

1. Install pyRevit (https://docs.pyrevitlabs.io/)
2. Clone this repository into:

%APPDATA%\pyRevit\Extensions

3. Restart Revit

## Roadmap (planned)

- Improve robustness of route detection for complex layouts
- Optional settings storage for frequently used parameters
- Additional QA and edge-case handling based on real project usage

