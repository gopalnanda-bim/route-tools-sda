# route-tools-sda

pyRevit tools for routing and numbering electrical devices in Revit

## Who is this for?

This extension is designed for:
- Electrical planners (Elektroplaner)
- BIM modellers working in TGA
- Fire alarm (BMA), emergency lighting (Sicherheitsbeleuchtung), and PA/SAA projects

It is **not** intended for architects or general Revit users.

## How it works 

### Background: Numbering in German execution planning (Ausführungsplanung)

In German TGA execution planning (Ausführungsplanung), systems such as:

- Emergency Lighting (Sicherheitsbeleuchtung)
- Fire Alarm Systems (BMA)
- Voice Alarm / PA Systems (SAA / ELA)

follow a **two-level numbering logic**.

Each device is identified by:
- a **loop / circuit number**
- and a **device number within that loop**

A typical notation is:

- `1 / 1` to `1 / 10` → devices on loop 1  
- `2 / 1` to `2 / 10` → devices on loop 2  

In Revit, these values are usually stored in **two separate instance parameters**, for example:
- `Loop` / `Circuit`
- `Device Number`

Assigning and maintaining these parameters manually is **time-consuming and error-prone**, especially when layouts change.

---

### Draw Route

1. Run the tool in a 2D plan view
2. Click devices in the desired order along a system route
3. The tool:
   - Draws a route line for the loop
   - Assigns the same loop / circuit value to all selected devices
   - Automatically numbers devices sequentially within that loop

This allows planners to quickly generate numbering such as:
- Loop `1` → `1/1`, `1/2`, `1/3`, …
- Loop `2` → `2/1`, `2/2`, `2/3`, …

without manually editing parameters for each device.

---

### Reorder Route

1. Select existing route detail lines (TAB to select the connected chain)
2. Run the tool
3. Choose which parameter should be renumbered
4. The tool:
   - Detects devices along the route
   - Renumbers them based on the route direction
   - Optionally reverses direction or sets a loop / circuit value

This is especially useful when layouts change and numbering must be corrected
without deleting and re-entering parameter values.

---

## Why this matters in practice

The route lines represent **real system logic**:
- each line corresponds to one loop or circuit
- the line becomes the reference for numbering consistency

Instead of manually managing multiple parameters,
the planner controls numbering **graphically and logically** through the route.

This significantly speeds up execution planning
and reduces numbering errors in real projects.
