# Connector Routing — Style and Glue Selection by Diagram Family

Decision-tree reference the visio-master runtime consults when it picks a
connector master, a glue mode, a `ConRouteStyle` / `DynamicConnectorRouteStyle`
value, an `AvenueSizeX/Y` and `BlockSizeX/Y` spacing pair, a `LineJumpStyle`
profile, and the per-connector `ShapeRouteStyle` / `ConFixedCode` /
`WalkPreference` overrides for any diagram family the project ships. The rules
encoded here are what `connector_planner.py` reads at template-instantiation
time and what `vsdx_quality_checker.py` lints against after the fact.

> Two cells govern almost every routing question: `BeginX` / `EndX` (the
> *formula* in these cells determines glue mode — `PNT(Sheet.N!PinX,
> Sheet.N!PinY)` is dynamic, `PAR(PNT(Sheet.N!Connections.X<row>,
> Sheet.N!Connections.Y<row>))` is static) and `DynamicConnectorRouteStyle`
> (the page-level routing engine). Everything else — `ConFixedCode`,
> `ConLineRouteExt`, `ShapeRouteStyle`, `WalkPreference`, `ConLineJumpCode`,
> `LineJumpFactorX/Y`, `AvenueSizeX/Y`, `BlockSizeX/Y` — fine-tunes the default
> these two produce.

---

## 1. The two-question decision

Before dropping any connector, the runtime answers two orthogonal questions
and a single integer-valued tertiary:

1. **Should the connector re-attach to a different side when endpoints move?**
   - Yes → dynamic (shape-to-shape) glue. Endpoint formula
     `PNT(Sheet.<id>!PinX, Sheet.<id>!PinY)`. `Connect.ToPart = visWholeShape (3)`.
   - No → static (point-to-point) glue. Endpoint formula
     `PAR(PNT(Sheet.<id>!Connections.X<row>, Sheet.<id>!Connections.Y<row>))`.
     `Connect.ToPart = visConnectionPoint (100) + row`.
2. **Which routing engine should compute the path?**
   - Page-wide default → write the integer constant into
     `PageSheet!DynamicConnectorRouteStyle` (`Cells("DynamicConnectorRouteStyle")`)
     and leave each connector's `ShapeRouteStyle = 0`.
   - Per-connector override → write the integer into the connector's
     `ShapeRouteStyle` cell (Shape Layout section). Non-zero wins over the page.
3. **How tightly should the engine bind to current geometry?**
   - `ConFixedCode = 0` lets the router rebuild the path on every recalc.
   - `ConFixedCode = 1` (`visLOFlagsRouteOnce`) freezes the path after the
     first auto-route — Visio respects user nudges.
   - `ConFixedCode = 2` keeps the existing path and never re-routes.
   - `ConFixedCode = 6` is `2 | 4`; never re-routes and never splits when a
     2-D shape is dropped on the line.

The diagram family answers all three at once. Section 2 covers question (1),
section 4 covers question (2), section 6 covers question (3), and section 5
fuses them into a single per-family configuration matrix.

---

## 2. Glue-mode rule by diagram family

### 2.1 Why glue mode is structural, not cosmetic

`Page.Layout()` only treats a connector as participating in placement when
**both** endpoints are bound shape-to-shape (dynamic glue). Static-glued
endpoints are honoured by the *router* (`RouteStyle`) but ignored by the
*placer* (`PlaceStyle`) — the placement algorithms cannot infer parent / child
relationships through static glue because static glue carries no semantic of
"connects to whole shape", only "connects to coordinate (x, y) on whichever
shape currently occupies that pin".

Concretely: with static glue, calling `Page.Layout()` on a Hierarchy
(`PlaceStyle = 17`) layout will still place the 2-D nodes by tree order, but
the connectors will not flip from "left side of parent" to "top of parent" if
the placer decides to reorganise. The connector's geometry is rebuilt against
the new positions of the same fixed connection-point rows — which often
produces the spaghetti that motivates a redesign.

### 2.2 Glue-mode policy table

| Diagram family                      | Default glue mode  | Endpoint formula written by `GlueTo`                | Why                                                                                                                          |
|-------------------------------------|--------------------|-----------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------|
| Org chart                           | Dynamic            | `PNT(Sheet.N!PinX, Sheet.N!PinY)`                   | `PlaceStyle = 17`/`23` requires shape-to-shape glue; node positions change every Layout call.                                |
| Basic flowchart                     | Dynamic            | `PNT(Sheet.N!PinX, Sheet.N!PinY)`                   | `PlaceStyle = 1`/`2` and `RouteStyle = 8`/`9`; lanes and rows reflow on add.                                                 |
| Cross-functional flowchart (lanes)  | Dynamic for tasks; static for lane-anchor decorations | mixed                                | Tasks reflow inside lanes; lane title blocks have `FixedCode=4` and decorations glue to fixed rows.                          |
| BPMN sequence flow                  | Dynamic            | `PNT(Sheet.N!PinX, Sheet.N!PinY)`                   | Sequence flow auto-attaches to the cheapest gateway side.                                                                   |
| BPMN message flow                   | Static (gateway anchored) | `PAR(PNT(Sheet.N!Connections.X<row>, ...))`   | Message flow must enter and leave specific marked rows on the participant pool.                                              |
| Tree / dendrogram                   | Dynamic            | `PNT(Sheet.N!PinX, Sheet.N!PinY)`                   | `PlaceStyle = 1`/`2`, `RouteStyle = 10`/`11`.                                                                                |
| Network topology (logical)          | Dynamic            | `PNT(Sheet.N!PinX, Sheet.N!PinY)`                   | Use `RouteStyle = visLORouteNetwork (12)` so endpoints find shortest path.                                                  |
| Mind map / radial                   | Dynamic            | `PNT(Sheet.N!PinX, Sheet.N!PinY)`                   | `PlaceStyle = 6 (Radial)`, `RouteStyle = 7 (Straight)`; centre re-anchors as ring count grows.                              |
| State diagram (UML)                 | Dynamic            | `PNT(Sheet.N!PinX, Sheet.N!PinY)`                   | Self-transitions and re-entries; placement reflows.                                                                         |
| Class diagram (UML)                 | Static for inheritance arrows; dynamic for associations | mixed                              | Inheritance triangles point at a fixed top-centre row; loose associations re-attach.                                       |
| Sequence diagram (UML)              | Static              | `PAR(PNT(Sheet.N!Connections.X<row>, ...))`         | Lifelines are fixed vertical guides; messages anchor to numbered activation rows.                                          |
| Rack diagram (server / network gear)| **Static** (always) | `PAR(PNT(Sheet.N!Connections.X<row>, ...))`         | Rack U-positions are physical; cables enter port `Connections.X<row>` deterministically — re-routing would lie about ports. |
| Floor plan (with anchored equipment)| **Static** for anchored items; dynamic for furniture loops | mixed                       | Workstations, fire alarms, RJ-45 sockets must keep exact wall coordinates; movable furniture can reflow.                   |
| Electrical / P&ID schematic         | **Static** (always) | `PAR(PNT(Sheet.N!Connections.X<row>, ...))`         | Component pins are physical (anode/cathode); wiring is read by analysis tools that match pin numbers.                       |
| Piping & instrumentation (P&ID)     | **Static** (always) | `PAR(PNT(Sheet.N!Connections.X<row>, ...))`         | Inlet / outlet nozzles are deterministic; static glue preserves nozzle assignment across edits.                              |
| Wiring loom diagram                 | **Static** (always) | `PAR(PNT(Sheet.N!Connections.X<row>, ...))`         | Wire numbers map 1:1 to pin numbers.                                                                                        |
| AWS / Azure / GCP architecture      | Dynamic for service edges; static for "managed-by" annotations | mixed                  | Service icons reflow inside layer containers; annotation arrows usually pin to corner rows.                                |
| Site map / wireframe                | Dynamic            | `PNT(Sheet.N!PinX, Sheet.N!PinY)`                   | Reflow to fit the canvas as nav grows.                                                                                       |
| Gantt / timeline (visio template)   | Static              | `PAR(PNT(Sheet.N!Connections.X<row>, ...))`         | Milestone bars sit at fixed time-axis coordinates; dependency arrows must hit specific row Y.                                |

The cells the runtime touches to encode the static-glue answer are
**`Connections.X<row>`**, **`Connections.Y<row>`**, **`Connections.DirX<row>`**,
**`Connections.DirY<row>`**, and **`Connections.Type<row>`** rows in the
target shape's `Connections` section. Row indices are 1-based in formulas
(`Connections.X1`, `Connections.X2`, …) but 0-based in `ToPart` arithmetic
(`visConnectionPoint = 100`, row 0; row 1 → `101`).

### 2.3 Inspecting glue mode at runtime

```python
# Returns "static", "dynamic", "unattached", or "error"
def glue_mode(connect_obj):
    if connect_obj.FromPart == -1:        # visConnectFromError
        return "error"
    if connect_obj.ToPart == 3:           # visWholeShape
        return "dynamic"
    if connect_obj.ToPart >= 100:         # visConnectionPoint base
        return "static"
    return "unattached"
```

`Connect.FromPart` is `9` (`visBegin`) or `12` (`visEnd`); `Connect.ToPart`
is `3` for whole-shape, `100 + row` for a specific connection point, `1` /
`4` for guides, `2` for guide intersections, `7` for an angle. Anything not
in that list means the formula resolved to a non-canonical target — usually a
sign of hand-edited XML.

### 2.4 Why "static for fixed-position diagrams" is non-negotiable

Three diagram families are *physical layouts* — every shape's position
corresponds to a real-world location:

- **Rack diagrams.** A `1U` server's `PinY` is determined by which of the 42
  rack units it occupies. Cables enter the back panel at `Connections.X1`
  through `Connections.X8` (the eight NIC ports). If `Page.Layout()` reflowed
  the cables to "the cheapest side" — i.e. the front panel — the diagram
  would tell you to plug a fibre transceiver into the LCD bezel.
- **Floor plans.** Wall outlets, fire alarms, sprinklers, IT closets each
  have an absolute (x, y) on the building plan. Connections (RJ-45 cable
  runs, sprinkler trunks) anchor to numbered ports on each device. Reflow
  destroys the building-plan correspondence.
- **P&ID and electrical schematics.** Component pins / nozzles are numbered
  per IEC 60617 / ISA-5.1 and are read by downstream analysis (SPICE,
  Aspen). Static glue is the only way the connector knows which numbered
  pin it terminates at.

For these families, the runtime forces:

```text
ConFixedCode      = 6         # never re-route, never split
ShapeRouteStyle   = 16        # visLORouteCenterToCenter (or 1, RightAngle)
ConLineRouteExt   = 1         # straight (no auto-NURBS)
WalkPreference    = 0         # honour the user's chosen first axis
```

and writes the endpoint formula directly with
`Cell.GlueTo(target.Cells("Connections.X<row>"))`. Calling `Page.Layout()`
on such a page leaves the connectors' `BeginX` / `EndX` formulas intact and
only resnaps geometry against the (also fixed) target rows.

---

## 3. The static / dynamic mode boundary in code

### 3.1 The exact API call that produces each mode

| Result                              | Visio API                                                              | Resulting `BeginX` formula                                |
|-------------------------------------|------------------------------------------------------------------------|-----------------------------------------------------------|
| Dynamic, shape-to-shape             | `conn.Cells("BeginX").GlueTo(target.Cells("PinX"))`                    | `PNT(Sheet.N!PinX, Sheet.N!PinY)`                          |
| Dynamic, shape-to-shape (alt API)   | `conn.Cells("BeginX").GlueToPos(target, 0.5, 0.5)`                     | `PNT(Sheet.N!PinX, Sheet.N!PinY)` (centred)               |
| Static, point-to-point (named row)  | `conn.Cells("BeginX").GlueTo(target.Cells("Connections.X1"))`          | `PAR(PNT(Sheet.N!Connections.X1, Sheet.N!Connections.Y1))` |
| Static, point-to-point (raw coords) | `conn.Cells("BeginX").Formula = f"PNT({x:.4f},{y:.4f})"`                | `PNT(<x>, <y>)`                                            |
| Unattached (free coordinate)        | `conn.Cells("BeginX").FormulaForceU = "2.5 in"`                        | literal                                                   |
| Tear glue down                      | `conn.Cells("BeginX").Unglue()` (or overwrite with literal)             | literal                                                   |

Both `GlueTo` and `GlueToPos` round-trip through Visio's recalc engine
and update the page-level `Connect` collection. Setting `BeginX.Formula`
to a hand-built `PNT(...)` works but the `Connect` row only materialises
after the next recalc — read `page.Connects.Count` to force it.

### 3.2 Inspecting which side of the target the dynamic glue picked

After `Page.Layout()` has run, the auto-router will have decided which side
of the target a dynamic connector enters. That side is exposed only
indirectly through `Connect.ToCell.Name` — when Visio decides "enter from
the top", it auto-creates an outward-pointing connection point and rewrites
the formula to reference `Connections.X<row>` of the new row, even though
you originally wrote `PinX`. To detect this:

```python
for cn in page.Connects:
    if cn.ToCell.Name == "PinX":
        side = "centre"
    else:                                                # Connections.X<row>
        target = cn.ToSheet
        row = int(cn.ToCell.Name.replace("Connections.X", ""))
        dx = target.Cells(f"Connections.DirX{row}").ResultIU
        dy = target.Cells(f"Connections.DirY{row}").ResultIU
        side = {(0, 1): "top", (0, -1): "bottom",
                (1, 0): "right", (-1, 0): "left"}.get((dx, dy), "diag")
```

The runtime uses this to verify rack and P&ID diagrams have not silently
flipped to the wrong port after a Layout call (anti-pattern §10.5).

---

## 4. Routing engines (`ConRouteStyle` and `DynamicConnectorRouteStyle`)

### 4.1 Full constant table — the per-page and per-connector routing values

Each value is a `VisCellVals` enumeration constant. The cell on the page is
`PageSheet!DynamicConnectorRouteStyle`; the cell on a single connector is
`ShapeRouteStyle` (modern) or `ConRouteStyle` (legacy alias). Both accept
the same values; per-connector wins when non-zero.

| Constant                            | Int   | Geometry                          | Best paired with `PlaceStyle`         | Use                                                   |
|-------------------------------------|-------|-----------------------------------|---------------------------------------|-------------------------------------------------------|
| `visLORouteDefault`                 | 0     | Inherit from page                 | n/a                                   | Connector-level cell; means "use page".                |
| `visLORouteRightAngle`              | 1     | 90° corners                       | Any tree / hierarchy / flowchart      | The canonical flowchart connector.                     |
| `visLORouteFlowchartNS`             | 2 / 8 | Right-angle vertical              | `1` / `3` (TopToBottom / BottomToTop) | Flowchart top-down. **Note**: `RouteStyle` cell uses 2; `DynamicConnectorRouteStyle` uses 8. |
| `visLORouteFlowchartWE`             | 3 / 9 | Right-angle horizontal            | `2` / `4` (LeftToRight / RightToLeft) | Flowchart left-right. Same alias caveat.               |
| `visLORouteOrgNS` / `OrgChartNS`    | 4     | Right-angle, top-of-parent enter  | Hierarchy 16-21 (vertical)            | Standard top-down org chart.                            |
| `visLORouteOrgWE` / `OrgChartEW`    | 5     | Right-angle, side-of-parent enter | Hierarchy 22-27 (horizontal)          | Sideways org chart.                                     |
| `visLORouteOrgChartNSCompact`       | 6     | Right-angle, compact lateral      | Hierarchy 16-21                       | Tighter spacing for printed org charts.                |
| `visLORouteOrgChartEWCompact`       | 7     | Right-angle, compact lateral      | Hierarchy 22-27                       | Sideways compact.                                       |
| `visLORouteSimple`                  | 6     | Free-form right-angle             | Compact / radial                      | Legacy alias (collides with `OrgChartNSCompact`); avoid in new code. |
| `visLORouteStraight`                | 7 / 2 | Straight line                     | Radial (6)                            | Mind maps. **Note**: `RouteStyle` uses 7; on connectors `ShapeRouteStyle = 2`. |
| `visLORouteCircular`                | 8     | Tangent arcs around centre        | Circular (5)                          | Bus / ring topology.                                    |
| `visLORouteRightAngleSimple`        | 9     | Right-angle without jumps          | Any                                   | Same shape as RightAngle but with `LineJumpCode = 0`.   |
| `visLORouteTreeNS`                  | 10    | T-junctions, vertical              | `1` / `3`                              | Family tree / dendrogram top-down.                     |
| `visLORouteTreeWE`                  | 11    | T-junctions, horizontal            | `2` / `4`                              | Family tree left-right.                                |
| `visLORouteNetwork` / `NetworkNS`   | 12    | Right-angle, no preferred axis     | "Network" (mesh)                       | Network topology vertical preference.                  |
| `visLORouteNetworkWE`               | 13    | Right-angle, horiz preference      | Network                                | Network topology horizontal.                            |
| `visLORouteFlowchartNSCrossRoutes`  | 14    | Right-angle with merges            | `1`                                    | Flowcharts with merge symbols.                          |
| `visLORouteFlowchartWECrossRoutes`  | 15    | Right-angle with merges, horiz     | `2`                                    | Flowcharts with merge symbols, sideways.                |
| `visLORouteCenterToCenter`          | 16    | Straight from centre to centre     | Free-form                              | "Straight connector" master baked-in.                   |
| `visLORouteSimpleNS`                | 17    | Simple right-angle, vertical       | Free-form                              | Wireframe and mind-map outliners.                       |
| `visLORouteSimpleEW`                | 18    | Simple right-angle, horizontal     | Free-form                              | Wireframe and mind-map outliners.                       |
| `visLORouteSimpleNSCenter`          | 25    | Right-angle anchored to centres    | Free-form                              | Use when shapes are tiny and you want centred entry.    |
| `visLORouteSimpleEWCenter`          | 26    | Right-angle anchored to centres, EW | Free-form                              | Same, horizontal.                                       |
| `visLORouteSimpleVertTree`          | 27    | Simple vertical tree                | `1` / `3`                              | Modern lightweight tree.                                |
| `visLORouteSimpleHorzTree`          | 28    | Simple horizontal tree              | `2` / `4`                              | Modern lightweight tree.                                |
| `visLORouteNone`                    | 31    | Literal `BeginX`/`EndX`             | Static-glue diagrams                   | Disables router; rack / P&ID use this.                 |

The numeric duplication between `RouteStyle` (used by `Page.Layout()` for
re-routing during placement) and `DynamicConnectorRouteStyle` (used by the
runtime router as connectors move) is genuine — Visio chose to recycle the
enum but mapped some constants to different ints in the two cells.
`connector_planner.py` reads from a single canonical table keyed by
`(cell_name, family)` to avoid the off-by-six confusion of `OrgChartNS = 4`
vs `OrgChartNSCompact = 6` and `Simple = 6`.

### 4.2 Page-level vs per-connector vs per-master cascade

The router consults cells in this priority order:

1. **Connector**'s `ShapeRouteStyle` cell. Non-zero wins over everything.
2. **Connector**'s `ConRouteStyle` cell (legacy; some master files still ship
   this and not `ShapeRouteStyle`).
3. **Page**'s `DynamicConnectorRouteStyle` cell.
4. **Page**'s `RouteStyle` cell (only consulted by `Page.Layout()` reroute
   pass, not by the live router).
5. The hardcoded global default of `visLORouteRightAngle (1)`.

`PageSheet!RouteStyle` and `PageSheet!DynamicConnectorRouteStyle` are *two
different cells* and they do *not* shadow each other. Set the first to drive
`Page.Layout()`'s reroute pass; set the second to drive the live router that
fires when shapes move outside `Layout()`. Most templates set both to the
same constant; the runtime always writes both.

### 4.3 Per-family routing engine table

| Family                              | `PageSheet!DynamicConnectorRouteStyle` | `PageSheet!RouteStyle` (Layout pass) | `PageSheet!PlaceStyle`             |
|-------------------------------------|----------------------------------------|--------------------------------------|------------------------------------|
| Org chart, T→B, centred             | 4 (`OrgChartNS`)                       | 4 (`OrgNS`)                          | 17 (Hierarchy T→B Center)          |
| Org chart, L→R, middle              | 5 (`OrgChartEW`)                       | 5 (`OrgWE`)                          | 23 (Hierarchy L→R Middle)          |
| Compact org chart, printed          | 6 (`OrgChartNSCompact`)                | 4                                    | 17 with `AvenueSizeX = 0.25 in`    |
| Basic flowchart, T→B                | 8 (`FlowchartNS`)                      | 2 (`FlowchartNS`)                    | 1 (TopToBottom Tree)               |
| Basic flowchart, L→R                | 9 (`FlowchartEW`)                      | 3 (`FlowchartWE`)                    | 2 (LeftToRight Tree)               |
| Cross-functional flowchart, horiz lanes | 9 (`FlowchartEW`)                  | 3                                    | 2                                  |
| Cross-functional flowchart, vert lanes  | 8 (`FlowchartNS`)                  | 2                                    | 1                                  |
| BPMN sequence flow                  | 9 (`FlowchartEW`)                      | 3                                    | 2                                  |
| BPMN message flow                   | 1 (`RightAngle`)                       | 1                                    | 0 (Default)                        |
| Tree / dendrogram, T→B              | 10 (`TreeNS`)                          | 10                                   | 1                                  |
| Tree / dendrogram, L→R              | 11 (`TreeEW`)                          | 11                                   | 2                                  |
| Network topology (logical)          | 12 (`Network`)                         | 12                                   | 0 (let user place)                 |
| Mind map / radial                   | 16 (`CenterToCenter`) or 7 (`Straight`)| 7                                    | 6 (Radial)                         |
| Sequence diagram (UML)              | 17 (`SimpleNS`)                        | 1                                    | 0 (manual)                         |
| State / class diagram (UML)         | 1 (`RightAngle`)                       | 1                                    | 0                                  |
| Rack diagram                        | 31 (`None`) or 1 (`RightAngle`)        | 0                                    | 0 (manual; pinned)                 |
| Floor plan, anchored equipment      | 31 (`None`) or 1                       | 0                                    | 0                                  |
| Electrical / P&ID                   | 31 (`None`)                            | 0                                    | 0                                  |
| Wiring loom                         | 31 (`None`)                            | 0                                    | 0                                  |
| AWS / Azure / GCP architecture      | 1 (`RightAngle`)                       | 1                                    | 23 (Hierarchy L→R Middle) inside containers |
| Wireframe / site map                | 17 (`SimpleNS`) or 18 (`SimpleEW`)     | 1                                    | 1 or 2                             |
| Gantt / timeline                    | 1 (`RightAngle`) or 31                 | 0                                    | 0                                  |

The "or" entries are the canonical and the fallback the runtime emits when
the diagram is marked `physical: true` in the project YAML; physical
diagrams force `RouteStyle = 0` so `Page.Layout()` cannot reroute.

---

## 5. Per-family configuration matrix (the master table)

This is the table `connector_planner.py` indexes by `family` to emit the
full ShapeSheet block in one batch (`PageSheet.SetFormulas`).

| Family        | Glue   | `DynConnRouteStyle` | `RouteStyle` (Layout) | `PlaceStyle` | `AvenueSizeX` | `AvenueSizeY` | `BlockSizeX` | `BlockSizeY` | `LineJumpStyle` | `LineJumpCode` | Per-conn `ConFixedCode` | Per-conn `ConLineRouteExt` |
|---------------|--------|---------------------|-----------------------|--------------|---------------|---------------|--------------|--------------|-----------------|----------------|-------------------------|----------------------------|
| OrgChart T→B  | dyn    | 4                   | 4                     | 17           | 0.5 in        | 0.4 in        | 0.25 in      | 0.25 in      | 0 (none)        | 0              | 0                       | 0                          |
| OrgChart L→R  | dyn    | 5                   | 5                     | 23           | 0.4 in        | 0.5 in        | 0.25 in      | 0.25 in      | 0               | 0              | 0                       | 0                          |
| Flowchart T→B | dyn    | 8                   | 2                     | 1            | 0.5 in        | 0.5 in        | 0.375 in     | 0.375 in     | 1 (arc)         | 1              | 0                       | 0                          |
| Flowchart L→R | dyn    | 9                   | 3                     | 2            | 0.5 in        | 0.5 in        | 0.375 in     | 0.375 in     | 1               | 1              | 0                       | 0                          |
| Swim-lane T→B | dyn    | 8                   | 2                     | 1            | 0.5 in        | 0.5 in        | 0.375 in     | 0.375 in     | 1               | 1              | 0                       | 0                          |
| BPMN seq      | dyn    | 9                   | 3                     | 2            | 0.5 in        | 0.4 in        | 0.375 in     | 0.375 in     | 2 (gap)         | 1              | 0                       | 0                          |
| BPMN msg      | static | 1                   | 1                     | 0            | n/a           | n/a           | n/a          | n/a          | 2               | 1              | 1 (`RouteOnce`)         | 1 (straight)               |
| Tree T→B      | dyn    | 10                  | 10                    | 1            | 0.4 in        | 0.4 in        | 0.25 in      | 0.25 in      | 0               | 0              | 0                       | 0                          |
| Tree L→R      | dyn    | 11                  | 11                    | 2            | 0.4 in        | 0.4 in        | 0.25 in      | 0.25 in      | 0               | 0              | 0                       | 0                          |
| Network       | dyn    | 12                  | 12                    | 0            | 0.5 in        | 0.5 in        | 0.5 in       | 0.5 in       | 1               | 3              | 0                       | 0                          |
| Mind map      | dyn    | 16                  | 7                     | 6            | 0.75 in       | 0.75 in       | n/a          | n/a          | 0               | 0              | 0                       | 2 (curved)                 |
| State (UML)   | dyn    | 1                   | 1                     | 0            | 0.5 in        | 0.5 in        | 0.375 in     | 0.375 in     | 1               | 1              | 0                       | 0                          |
| Class (UML)   | mixed  | 1                   | 1                     | 0            | 0.5 in        | 0.5 in        | 0.375 in     | 0.375 in     | 0               | 0              | 1 on inheritance        | 0                          |
| Sequence (UML)| static | 17                  | 1                     | 0            | n/a           | n/a           | n/a          | n/a          | 0               | 0              | 6                       | 1                          |
| Rack          | static | 31                  | 0                     | 0            | n/a           | n/a           | n/a          | n/a          | 0               | 0              | 6                       | 1                          |
| Floor plan    | mixed  | 31                  | 0                     | 0            | n/a           | n/a           | n/a          | n/a          | 0               | 0              | 6 on anchored / 0 furn. | 1                          |
| P&ID          | static | 31                  | 0                     | 0            | n/a           | n/a           | n/a          | n/a          | 0               | 0              | 6                       | 1                          |
| Electrical    | static | 31                  | 0                     | 0            | n/a           | n/a           | n/a          | n/a          | 5 (none)        | 0              | 6                       | 1                          |
| Wiring loom   | static | 31                  | 0                     | 0            | n/a           | n/a           | n/a          | n/a          | 0               | 0              | 6                       | 1                          |
| Cloud arch    | dyn    | 1                   | 1                     | 23           | 0.5 in        | 0.4 in        | 0.25 in      | 0.25 in      | 1               | 1              | 0                       | 0                          |
| Wireframe     | dyn    | 17                  | 1                     | 1            | 0.375 in      | 0.375 in      | 0.25 in      | 0.25 in      | 0               | 0              | 0                       | 0                          |
| Gantt         | static | 31                  | 0                     | 0            | n/a           | n/a           | n/a          | n/a          | 0               | 0              | 6                       | 1                          |

`n/a` for the spacing columns means the row is not written by
`SetFormulas` for that family — the runtime omits the cell so the
page-level defaults from the template stay in force. Writing `0.0 in`
would force the page to clamp at the engine minimum (`0.0625 in`).

### 5.1 The full block as Python `SetFormulas`

```python
# connector_planner.py — emits the per-family block in one round-trip
SECTION_OBJECT      = 1
ROW_PAGE_LAYOUT     = 24
COL_PLACE_STYLE     = 0
COL_ROUTE_STYLE     = 1
COL_AVENUE_SIZE_X   = 4
COL_AVENUE_SIZE_Y   = 5
COL_BLOCK_SIZE_X    = 6
COL_BLOCK_SIZE_Y    = 7
COL_RESIZE_PAGE     = 9
COL_LINE_JUMP_CODE  = 10
COL_LINE_JUMP_STYLE = 11

def apply_family(page, profile: dict) -> None:
    src, formulas = [], []
    for name, value in profile["page_layout_cells"].items():
        col = {
            "PlaceStyle":      COL_PLACE_STYLE,
            "RouteStyle":      COL_ROUTE_STYLE,
            "AvenueSizeX":     COL_AVENUE_SIZE_X,
            "AvenueSizeY":     COL_AVENUE_SIZE_Y,
            "BlockSizeX":      COL_BLOCK_SIZE_X,
            "BlockSizeY":      COL_BLOCK_SIZE_Y,
            "ResizePage":      COL_RESIZE_PAGE,
            "LineJumpCode":    COL_LINE_JUMP_CODE,
            "LineJumpStyle":   COL_LINE_JUMP_STYLE,
        }[name]
        src.extend([SECTION_OBJECT, ROW_PAGE_LAYOUT, col])
        formulas.append(str(value))
    # DynamicConnectorRouteStyle is a named cell in the same row but uses
    # a different column index; address by name for clarity.
    page.PageSheet.SetFormulas(src, formulas, 0)
    page.PageSheet.Cells("DynamicConnectorRouteStyle").FormulaForceU = (
        str(profile["dynamic_connector_route_style"])
    )
```

### 5.2 Per-connector cells the runtime writes after `SetFormulas`

The page-level batch above does not touch per-connector cells. Those are
written one connector at a time, immediately after `Drop`:

| Cell                  | Section          | Static-glue families | Dynamic-glue families | Notes                                                       |
|-----------------------|------------------|----------------------|-----------------------|-------------------------------------------------------------|
| `ShapeRouteStyle`     | Shape Layout     | from §5 table        | `0` (inherit page)    | Non-zero overrides page-level routing for this connector.   |
| `ConFixedCode`        | Shape Layout     | `6` (never re-route, never split) | `0`              | Bit 0 = RouteOnce, bit 1 = NeverReroute, bit 2 = NoSplit.    |
| `ConLineRouteExt`     | Shape Layout     | `1` (straight)        | `0` (default)         | `1` forbids NURBS; `2` forces curved.                       |
| `WalkPreference`      | Shape Layout     | `0`                   | from family policy    | `0` horiz-then-vert, `1` vert-then-horiz.                   |
| `ConLineJumpCode`     | Shape Layout     | from §6               | `0` (page default)    | Per-connector jump filter.                                   |
| `ConLineJumpStyle`    | Shape Layout     | from §6               | `0`                   | Per-connector jump style override.                           |
| `BeginArrow`          | 1-D Endpoints    | varies                | usually `0`           | `VisArrowValues` ID; `4 = filled`.                          |
| `EndArrow`            | 1-D Endpoints    | varies                | usually `4`           | `VisArrowValues` ID; `4 = filled`.                          |

For the static-glue families the runtime additionally pre-wires the
`BegTrigger` / `EndTrigger` cells with `_XFTRIGGER(target!EventXFMod)`
expressions — these mirror what `Cell.GlueTo` would have written, but the
runtime emits them by formula because `GlueTo` to a `Connections.X<row>`
cell will silently rewrite the formula on the next recalc if the row
referenced is later renumbered. Direct formula authoring is the only way
to keep the binding stable across stencil edits.

---


## 6. Line jumps — when crossings are unavoidable

Line jumps are visual hints rendered where two connectors cross on a 2-D
page. The choice is governed by six cells (three on the page, three on
each connector) and one global `Application.Settings` flag.

### 6.1 The page-level jump cells

| Cell                | Section     | Default   | Values (`VisCellVals`)                                                  |
|---------------------|-------------|-----------|-------------------------------------------------------------------------|
| `LineJumpStyle`     | Page Layout | `0`       | `0=visLOJumpNone`, `1=Arc`, `2=Gap`, `3=Square`, `4=Sides2`, `5=Sides3`, … `9=Sides7` |
| `LineJumpCode`      | Page Layout | `1`       | `0=none`, `1=horizontal-jumps-vertical`, `2=vertical-jumps-horizontal`, `3=last-routed-jumps` |
| `LineJumpFactorX`   | Page Layout | `0.66666` | Multiplier on jump width relative to line weight.                        |
| `LineJumpFactorY`   | Page Layout | `0.66666` | Multiplier on jump height.                                               |
| `LineToLineX`       | Page Layout | `0.125 in`| Minimum spacing between two parallel connectors.                          |
| `LineToLineY`       | Page Layout | `0.125 in`| Minimum spacing between two parallel connectors.                          |
| `LineToNodeX`       | Page Layout | `0.125 in`| Minimum spacing between a connector and a non-endpoint shape.            |
| `LineToNodeY`       | Page Layout | `0.125 in`| Minimum spacing between a connector and a non-endpoint shape.            |
| `PageLineJumpDirX`  | Page Layout | `0`       | `0=default`, `1=up`, `2=down`.                                            |
| `PageLineJumpDirY`  | Page Layout | `0`       | `0=default`, `1=left`, `2=right`.                                         |



### 6.2 The per-connector jump cells

| Cell                  | Default | Values                                                                    |
|-----------------------|---------|---------------------------------------------------------------------------|
| `ConLineJumpCode`     | `0`     | `0=page default`, `1=always jump`, `2=never jump`, `3=defer to other`     |
| `ConLineJumpStyle`    | `0`     | `0=page default`, `1..5` same as `LineJumpStyle`                          |
| `ConLineJumpDirX`     | `0`     | `0=page default`, `1=up`, `2=down`                                        |
| `ConLineJumpDirY`     | `0`     | `0=page default`, `1=left`, `2=right`                                     |

The classic electrical-bus pattern (one straight backbone, every spur
arcs over it) is encoded as: backbone `ConLineJumpCode = 2` plus spurs
`ConLineJumpCode = 1`. The runtime detects this pattern by tag
(`User.msvShapeCategories="Bus"`) and emits the cells directly.

### 6.3 Per-family jump policy

| Family                              | Page `LineJumpStyle` | Page `LineJumpCode` | Per-connector overrides                     |
|-------------------------------------|----------------------|---------------------|---------------------------------------------|
| Org chart, Tree, Hierarchy          | `0` (none)           | `0`                 | none — single-source trees rarely cross     |
| Basic flowchart                     | `1` (Arc)            | `1`                 | none                                        |
| Cross-functional flowchart          | `1` (Arc)            | `1`                 | swim-lane decorations: `ConLineJumpCode=2`  |
| BPMN sequence flow                  | `2` (Gap)            | `1`                 | none                                        |
| BPMN message flow                   | `2` (Gap)            | `1`                 | none                                        |
| Network topology                    | `1` (Arc)            | `3` (last-routed)   | backbone bus: `ConLineJumpCode=2`           |
| Mind map / Radial                   | `0`                  | `0`                 | none — radial cannot cross                  |
| State / Class diagram               | `1` (Arc)            | `1`                 | self-transitions: `ConLineJumpCode=2`       |
| Sequence diagram                    | `0`                  | `0`                 | activations are vertical-only; never cross  |
| Rack / P&ID / Electrical / Wiring   | `0` or `5` (none)    | `0`                 | every connector explicitly `=2` (never jump)|
| Cloud architecture                  | `1` (Arc)            | `1`                 | none                                        |
| Wireframe / Site map                | `0`                  | `0`                 | none                                        |
| Gantt / timeline                    | `0`                  | `0`                 | none                                        |

`LineJumpFactorX` / `LineJumpFactorY` default to `0.66666` and the
runtime keeps that value for every family except printed schematics
(both bumped to `1.5` to make jumps visible at print resolution).
Setting the factor to zero is an anti-pattern (§10.3); use `0.05` for
near-invisible jumps.



---

## 7. Walk preference, route extension, and curvature

`WalkPreference`, `ConLineRouteExt`, and `ShapeRouteStyle` are the three
per-connector cells that fine-tune what the chosen routing engine
actually draws. They are read on every recalc, so changes take effect
without calling `Layout()`.

### 7.1 `WalkPreference` — first-axis bias

`WalkPreference` controls which axis the right-angle router tries first
when computing the orthogonal path between two endpoints. Values:

| Value | Meaning                                  | Visual result                                           |
|-------|------------------------------------------|---------------------------------------------------------|
| `0`   | Horizontal-then-vertical                 | Connector exits sideways first, then turns up or down. |
| `1`   | Vertical-then-horizontal                 | Connector exits up or down first, then turns sideways. |

For a top-down flowchart you almost always want `WalkPreference = 1`
(the connector should exit downward from the predecessor's bottom
midpoint, not sideways then down). For a left-right flowchart leave it
at `0`. The default of `0` is wrong for org charts; the runtime forces
`1` for all `OrgChartNS` families.

### 7.2 `ConLineRouteExt` — geometry rendering

| Value | Constant                  | Effect                                                                       |
|-------|---------------------------|------------------------------------------------------------------------------|
| `0`   | `visLORouteExtDefault`    | Inherit from master (Dynamic connector master defaults to right-angle).      |
| `1`   | `visLORouteExtStraight`   | Straight line segments only; corners forced to 90°.                          |
| `2`   | `visLORouteExtNURBS`      | Curved Bezier between right-angle bend points.                              |

Setting `ConLineRouteExt = 2` on a Dynamic connector master gives you
the look of the "Curved connector" master without changing the master
reference, and lets the Layout engine still treat the shape as routable
(the genuine Curved connector master has hard-coded geometry that
`Page.Layout()` will not rebuild). For mind maps and radial diagrams
this is the recommended encoding.

### 7.3 `ShapeRouteStyle` — overriding the page

`ShapeRouteStyle` is what the runtime writes when one connector inside
an otherwise homogeneous diagram needs a different style — typically the
"summary" arrow on a flowchart that needs `visLORouteCenterToCenter (16)`
to cut diagonally across the page. Per-shape value wins over page-level
`DynamicConnectorRouteStyle` whenever non-zero.

```python
# Make this connector's path a straight diagonal regardless of page setting
conn.Cells("ShapeRouteStyle").FormulaForceU = "16"  # CenterToCenter
```

Setting `ShapeRouteStyle = 0` reverts to inheriting the page.



---

## 8. Drop strategies — `Drop` vs `DropConnected` vs `AutoConnect`

Three APIs land a 1-D shape on a page; pick one per family.

### 8.1 `Page.Drop(master, x, y)` plus `Cell.GlueTo`

The lowest-level option. The runtime drops the Dynamic connector master
at an arbitrary coordinate, then writes both endpoint formulas via
`GlueTo`. Used when:

- Glue mode must be static (`GlueTo target.Cells("Connections.X<row>")`).
- The runtime needs to control endpoint formulas precisely (anchored
  rows on rack equipment, P&ID nozzles).
- Both endpoints already exist; no new 2-D shape is being created.

```python
conn = page.Drop(connector_master, 0, 0)
conn.Cells("BeginX").GlueTo(src.Cells("PinX"))                     # dynamic
conn.Cells("EndX").GlueTo(dst.Cells("Connections.X3"))             # static
```

### 8.2 `Page.DropConnected(master, target, placeFlags, connectorMaster)`

The single-call API that creates a new 2-D shape *and* glues a Dynamic
connector to it. Returns the new 2-D shape; the connector is reachable
via `page.Connects` afterward. Always shape-to-shape glue. Used when:

- Building a chain of equally-sized nodes (BPMN sequence flow,
  flowchart spine).
- The 2-D shape's master is parameterised by `placeFlags`
  (`visAutoConnectDirRight (1)`, `Down (4)`, etc.).

```python
new_shape = page.DropConnected(
    activity_master,         # the new 2-D shape's master
    source_shape,            # existing 2-D shape to connect from
    1,                       # visAutoConnectDirRight
    None,                    # None = use Dynamic connector master
)
```

`DropConnected` always uses the page-level `DynamicConnectorRouteStyle`;
to override per-connector you must locate the new connector in
`page.Connects` and write `ShapeRouteStyle` after the fact.

### 8.3 `Shape.AutoConnect(direction, connectorMaster, [target])`

The same engine that powers the blue arrows in the Visio UI. Two modes:

- **With target**: pass `visAutoConnectDirNone (0)` plus a `target`
  shape. AutoConnect drops a Dynamic connector glued shape-to-shape on
  both ends. Equivalent to `DropConnected` but with the existing target.
- **Without target**: pass a direction (`visAutoConnectDirRight (1)`,
  `Left (2)`, `Up (3)`, `Down (4)`) and *no* target. AutoConnect spawns a
  copy of the source shape's master in that direction and connects to
  the copy.

```python
# Connect existing shapes
conn = src.AutoConnect(0, None, dst)              # 0 = visAutoConnectDirNone

# Spawn a copy to the right and connect
new_copy = src.AutoConnect(1, None, None)         # 1 = visAutoConnectDirRight
```



### 8.4 Per-family preferred drop strategy

| Family                              | Preferred API                          | Why                                                                |
|-------------------------------------|----------------------------------------|--------------------------------------------------------------------|
| Org chart                           | `DropConnected` (down) or `Drop`+`GlueTo` | Fast batch creation; routing inherits page-level `OrgChartNS`.    |
| Basic flowchart                     | `DropConnected`                        | Spine-style chain; placement does not require manual coordinates.  |
| Cross-functional flowchart          | `Drop` + `GlueTo`                      | Tasks must land in the correct lane (Y-coordinate matters).        |
| BPMN sequence flow                  | `DropConnected` per-step               | Step-by-step graph generation matches BPMN authoring flow.          |
| BPMN message flow                   | `Drop` + `GlueTo` (static row)         | Must enter pool participant at numbered marker.                     |
| Tree / dendrogram                   | `DropConnected`                        | Tree placement is the auto-layout engine's strongest case.         |
| Network topology                    | `Drop` + `AutoConnect`                 | Random topology benefits from per-edge `AutoConnect` shortcut.     |
| Mind map                            | `DropConnected` (radial)               | Auto-fanned out from centre.                                       |
| State / Class diagram               | `Drop` + `GlueTo`                      | Self-loops and aggregations need exact endpoint placement.         |
| Sequence diagram                    | `Drop` + `GlueTo` (static)             | Lifelines are fixed guides; messages anchor to numbered rows.      |
| Rack diagram                        | `Drop` + `GlueTo` (static)             | Cables must terminate on numbered ports.                            |
| Floor plan                          | `Drop` + `GlueTo` (mixed)              | Wall outlets are static; movable furniture uses dynamic.           |
| Electrical / P&ID / Wiring          | `Drop` + `GlueTo` (static)             | Pin numbers are physically meaningful.                              |
| Cloud architecture                  | `DropConnected` (with container hint)  | Service icons land in their layer container; arrows reflow.        |
| Wireframe / Site map                | `DropConnected`                        | Hierarchy of pages.                                                |
| Gantt / timeline                    | `Drop` + `GlueTo` (static)             | Bars sit on time-axis Y; dependencies anchor to milestone rows.    |

The runtime exposes a single `connect(family, src, dst, **opts)` entry
point that dispatches to the right API based on the family policy. The
caller never invokes `Drop` / `DropConnected` / `AutoConnect` directly.

---

## 9. The connector-master selection rule

Visio ships four 1-D masters in `CONNEC_M.vssx`. The runtime's choice is
not just "always Dynamic connector" — three families benefit from
master-baked geometry:

| `Master.NameU`                | Used by families                                     | Encoded constants                                                  |
|-------------------------------|------------------------------------------------------|--------------------------------------------------------------------|
| `Dynamic connector`           | OrgChart, Flowchart, BPMN, Tree, Network, State, Class, Cloud, Wireframe | `ShapeRouteStyle = 0` (inherit page); `ConLineRouteExt = 0` |
| `Dynamic connector` (arrowed) | Same as above, but where arrowheads are universal    | `EndArrow = 4` (filled), preset                                    |
| `Curved connector`            | Mind map, soft state diagrams                         | `ConLineRouteExt = 2` baked in                                     |
| `Straight connector`          | Center-to-center diagrams, sequence-diagram messages  | `ShapeRouteStyle = 16` (`CenterToCenter`) baked in                |

Static-glue families (rack, P&ID, electrical, wiring, Gantt) always use
`Dynamic connector` as the master and immediately overwrite
`ShapeRouteStyle`, `ConFixedCode`, `ConLineRouteExt`, and the endpoint
formulas — the master choice is incidental because every routing cell
is rewritten.



---

## 10. Anti-patterns

The patterns below are what the linter (`vsdx_quality_checker.py`)
flags. Each entry shows the offending cell state, why it breaks, and the
runtime's preferred encoding.

### 10.1 Dynamic glue on a rack diagram

**Symptom**: rack diagram with `Connect.ToPart = 3` (`visWholeShape`) on
any cable connector.

**Why it breaks**: cables are physical. The auto-router will pick "the
cheapest entry side" which on a rack is the *front* of a server, but the
cable must enter the *rear* NIC port. The diagram becomes wrong even if
it looks pretty.

**Fix**: rewrite endpoint formulas to reference the numbered NIC row.

```python
conn.Cells("BeginX").GlueTo(switch.Cells("Connections.X4"))   # static row
conn.Cells("EndX").GlueTo(server.Cells("Connections.X1"))     # static row
conn.Cells("ConFixedCode").FormulaForceU = "6"                # never re-route
conn.Cells("ShapeRouteStyle").FormulaForceU = "31"            # visLORouteNone
```

The linter rule: `family in {"rack","pid","electrical","wiring"} and any(c.ToPart == 3)` is an error.

### 10.2 Static glue on an org chart

**Symptom**: org chart where every connector's `Connect.ToPart` is in
`[100, 200)` (a connection-point row).

**Why it breaks**: `Page.Layout()` placement (`PlaceStyle = 17`)
requires shape-to-shape glue to discover parent / child relationships.
With static glue, `Layout()` still moves the boxes by tree order but
the connectors never re-flip — the result is spaghetti as soon as the
tree grows past two levels.

**Fix**:

```python
conn.Cells("BeginX").GlueTo(parent.Cells("PinX"))             # dynamic
conn.Cells("EndX").GlueTo(child.Cells("PinX"))                # dynamic
page.Layout()
```

The linter rule: `family in {"orgchart","tree","flowchart"} and any(100 <= c.ToPart < 200)` is a warning.

### 10.3 `LineJumpFactorX = 0`

**Symptom**: jumps render as a one-pixel gap instead of an arc.

**Why it breaks**: Visio still draws the jump glyph but at zero size, so
it looks like a rendering bug. Reviewers report "the diagram has a
glitch".

**Fix**: never write `0`. Use `0.05` for a near-invisible jump or `0` on
`LineJumpStyle` instead to disable the jump entirely.

### 10.4 `visLORouteCenterToCenter` on the page

**Symptom**: every connector cuts diagonally through other shapes.

**Why it breaks**: `visLORouteCenterToCenter (16)` is meant for the
single "Straight connector" master, not for the page default. Setting
`PageSheet!DynamicConnectorRouteStyle = 16` forces every connector to
ignore obstacles.

**Fix**: page should be `1` (`RightAngle`) or family-appropriate
(`OrgChartNS = 4`, `FlowchartNS = 8`, `TreeNS = 10`, `Network = 12`).
Per-connector override via `ShapeRouteStyle = 16` is fine for the rare
"summary" arrow.



### 10.5 Dynamic glue silently re-flipping

**Symptom**: a rack diagram authored with `GlueTo(server.Cells("PinX"))`
that, after a `Page.Layout()` call, ends up with `Connect.ToCell.Name`
referencing `Connections.X<row>` for a row that doesn't even exist on
the master.

**Why it breaks**: `GlueTo(PinX)` writes a dynamic glue formula. The
auto-router then picks "the cheapest side" and rewrites the formula to
hit the closest connection point; if there is no connection point on
that side, Visio auto-creates one. The diagram now references a
runtime-created row that disappears on save / reload.

**Fix**: never call `GlueTo(PinX)` on a static-glue family. Always
target a numbered row, and set `ConFixedCode = 6` so the router cannot
rewrite.

The linter check after `Page.Layout()`:

```python
def detect_silent_flip(page) -> list[tuple[int, str]]:
    issues = []
    for cn in page.Connects:
        if cn.ToCell.Name == "PinX":
            continue                                           # genuinely dynamic
        target = cn.ToSheet
        row_match = cn.ToCell.Name.replace("Connections.X", "")
        if not row_match.isdigit():
            continue
        row = int(row_match)
        # Compare against the master's published connection-point count
        published = int(target.Master.Cells("User.msvConnectionPointCount").ResultIU)
        if row > published:
            issues.append((cn.FromSheet.ID, f"runtime-created row {row}"))
    return issues
```

### 10.6 Mixing `RouteStyle = 6` and `visLORouteSimple`

**Symptom**: `RouteStyle = 6` selected on a Compact Tree but
connectors look like an org chart.

**Why it breaks**: integer `6` aliases two different constants —
`visLORouteOrgChartNSCompact` (`6`) on the page-layout cell and
`visLORouteSimple` (`6`) on the `RouteStyle` cell used by `Layout()`.
Different cells, same value, different semantics.

**Fix**: never reuse the integer literal `6`; route every assignment
through the `(cell_name, family)` lookup table in
`connector_planner.py`. Tests assert the lookup never returns `6` for
`DynamicConnectorRouteStyle` if the family is "compact" — it should
return `visLORouteRightAngle (1)` instead.

### 10.7 Calling `Page.Layout()` on a Dropped-but-not-yet-glued connector

**Symptom**: `Page.Layout()` returns silently but the connector still
sits at `(0, 0)` of the page; or `Connect.FromPart == -1`
(`visConnectFromError`).

**Why it breaks**: `Drop` puts the connector on the page; `GlueTo` glues
it. If `Layout()` is called between those two steps, the connector has
no Connect rows and the placer ignores it; the router then sees a
floating 1-D shape with no targets.

**Fix**: always sequence `Drop` → `GlueTo(begin)` → `GlueTo(end)` →
`Layout()`. Verify with `len(page.Connects) == 2 * connector_count`
before invoking the layout pass.

### 10.8 Forgetting `pythoncom.CoInitialize()` on a worker thread

**Symptom**: `GlueTo` raises `com_error` HRESULT `0x800401F0`
(`CO_E_NOTINITIALIZED`) on the second call from a non-main thread.

**Why it breaks**: pywin32 marshalling needs an initialised COM
apartment per thread.

**Fix**: pair every `CoInitialize()` with `CoUninitialize()` in a
`finally`; never share a Visio.Application reference across threads
without re-initialising.



### 10.9 Setting `ConFixedCode = 2` and then expecting `Layout()` to clean up

**Symptom**: `Layout()` runs, every other connector is re-routed, but
one specific connector is still tangled.

**Why it breaks**: `ConFixedCode = 2` (`visLOFlagsNeverReroute`) tells
the router "leave this one alone forever". Layout still places the 2-D
shapes around it but the connector geometry stays put.

**Fix**: only set `ConFixedCode = 2` (or `6`) on connectors that genuinely
must not be re-routed (rack cables, wiring schematics). For everything
else use `0`. To preserve a single user-edited path through a
`Layout()` pass, use `ConFixedCode = 1` (`visLOFlagsRouteOnce`)
instead — the router will route once on creation, then freeze.

### 10.10 Deleting a connection-point row that is the target of static glue

**Symptom**: after editing a master to remove a connection point, every
connector that referenced it now reports `Connect.FromPart = -1`
(`visConnectFromError`); on save / reload Visio rewrites those endpoints
to literal coordinates and the static glue is permanently lost.

**Fix**: enumerate `page.Connects` *before* deleting the row, call
`Cell.Unglue` on every connector pointing at it, then re-glue to the
intended row after the deletion.

### 10.11 Page-level `LineJumpStyle = 0` while expecting jumps

**Symptom**: `ConLineJumpCode = 1` set on a connector, but no jumps
render.

**Why it breaks**: `ConLineJumpCode` is a *filter* ("which connectors
participate in jumping"), not a *style*. The actual visual style comes
from `LineJumpStyle` on the page (or `ConLineJumpStyle` per-connector).
If the page is `0` (`visLOJumpNone`) the entire jump system is off.

**Fix**: set `LineJumpStyle = 1` (Arc) or `2` (Gap) on the page first,
then use `ConLineJumpCode` to control which connectors jump.

### 10.12 Reading `visLORouteFlowchartNS` on `RouteStyle` and `DynamicConnectorRouteStyle` and getting different ints

**Symptom**: copy-paste of `RouteStyle = 2` to
`DynamicConnectorRouteStyle = 2` gives a "Flowchart NS" path during
`Layout()` but `visLORouteStraight` (the live router's interpretation of
`2` on `DynamicConnectorRouteStyle`) once a shape is dragged.

**Why it breaks**: the `VisCellVals` enum is recycled across two cells
with different mappings:

| Cell                                     | Value `2`                | Value `8`                |
|------------------------------------------|--------------------------|--------------------------|
| `PageSheet!RouteStyle` (Layout pass)     | `visLORouteFlowchartNS`  | `visLORouteCircular`     |
| `PageSheet!DynamicConnectorRouteStyle`   | `visLORouteStraight`     | `visLORouteFlowchartNS`  |
| `Shape!ShapeRouteStyle` (per-connector)  | `visLORouteStraight`     | `visLORouteFlowchartNS`  |

**Fix**: `connector_planner.py` keys constants by `(cell_name, family)`
and never copies a literal across cells. The runtime asserts the family
table contains the correct integer per cell.



---

## 11. Verification queries the linter runs

After the diagram is built but before saving, the runtime walks
`page.Connects` and `page.PageSheet` to confirm the family policy is
honoured. The four core asserts share one helper module.

```python
GLUE_POLICY = {
    "orgchart":  "dynamic", "flowchart": "dynamic", "tree":      "dynamic",
    "network":   "dynamic", "mindmap":   "dynamic", "state":     "dynamic",
    "rack":      "static",  "pid":       "static",  "electrical":"static",
    "wiring":    "static",  "sequence":  "static",  "gantt":     "static",
}
STATIC_FAMILIES = {"rack", "pid", "electrical", "wiring", "gantt", "sequence"}

def assert_glue_policy(page, family: str) -> None:
    expected = GLUE_POLICY[family]
    for cn in page.Connects:
        if cn.FromPart == -1:                                  # visConnectFromError
            raise AssertionError(f"Dangling glue on {cn.FromSheet.NameU}")
        actual = "dynamic" if cn.ToPart == 3 else "static"     # visWholeShape vs row
        if actual != expected and family != "mixed":
            raise AssertionError(f"{family} expects {expected} got {actual}")

def assert_route_cells(page, family: str, profile: dict) -> None:
    ps = page.PageSheet
    for cell, expected in profile["page_layout_cells"].items():
        actual = int(ps.Cells(cell).ResultIU)
        if actual != int(expected):
            raise AssertionError(f"page.{cell}={actual}, expected {expected}")

def assert_static_overrides(page, family: str) -> None:
    if family not in STATIC_FAMILIES:
        return
    for shape in page.Shapes:
        if not shape.OneD:
            continue
        cfc = int(shape.Cells("ConFixedCode").ResultIU)
        srs = int(shape.Cells("ShapeRouteStyle").ResultIU)
        if cfc != 6 or srs not in (1, 31):
            raise AssertionError(
                f"{shape.NameU}: ConFixedCode={cfc}, ShapeRouteStyle={srs}"
            )

def assert_minimum_spacing(page) -> None:
    # Visio clamps below 0.0625 in (1.5875 mm) — read-back can mislead
    ps = page.PageSheet
    if ps.Cells("LineToLineX").Result("in") < 0.0625:
        raise AssertionError("LineToLineX below engine clamp")
    if ps.Cells("LineToLineY").Result("in") < 0.0625:
        raise AssertionError("LineToLineY below engine clamp")
```

For static-glue families, every `Connect.ToCell` must also reference a
row that exists on the *master*, not one the auto-router invented. The
detection logic is in §10.5 (`detect_silent_flip`).

### 11.1 Verification table — what to assert per family

| Family            | Glue check | Route cells              | Per-conn overrides              | Spacing |
|-------------------|------------|--------------------------|----------------------------------|---------|
| OrgChart          | dynamic    | DynConnRoute=4, Place=17 | `ShapeRouteStyle=0`             | yes     |
| Flowchart         | dynamic    | DynConnRoute=8, Place=1  | `ShapeRouteStyle=0`             | yes     |
| Tree              | dynamic    | DynConnRoute=10, Place=1 | `ShapeRouteStyle=0`             | yes     |
| Network           | dynamic    | DynConnRoute=12          | `ShapeRouteStyle=0`             | yes     |
| Mind map          | dynamic    | DynConnRoute=16, Place=6 | `ConLineRouteExt=2`             | partial |
| State             | dynamic    | DynConnRoute=1           | `ShapeRouteStyle=0`             | yes     |
| Rack              | static     | DynConnRoute=31, Place=0 | `ConFixedCode=6`, `ShapeRouteStyle=31` | n/a |
| P&ID / Electrical | static     | DynConnRoute=31, Place=0 | `ConFixedCode=6`                | n/a     |
| Sequence (UML)    | static     | DynConnRoute=17, Place=0 | `ConFixedCode=6`                | n/a     |
| Gantt             | static     | DynConnRoute=31, Place=0 | `ConFixedCode=6`                | n/a     |

Static-glue families skip the spacing assertions because
`AvenueSizeX/Y` and `BlockSizeX/Y` are never written for them.

---

## 12. Diagnostic queries (run-time triage)

When a connector "looks wrong" the runtime can dump every relevant cell
in one pass. The output is fed to `troubleshooting.md`'s decision tree.

```python
def diagnose_connector(conn) -> dict:
    """Snapshot every routing-relevant cell on a single connector."""
    cells = [
        "BeginX", "BeginY", "EndX", "EndY",
        "ShapeRouteStyle", "ConFixedCode", "ConLineRouteExt",
        "WalkPreference",
        "ConLineJumpCode", "ConLineJumpStyle",
        "ConLineJumpDirX", "ConLineJumpDirY",
        "BeginArrow", "EndArrow", "BeginArrowSize", "EndArrowSize",
        "BegTrigger", "EndTrigger",
    ]
    out = {"NameU": conn.NameU, "ID": conn.ID}
    for cell in cells:
        c = conn.Cells(cell)
        out[cell] = {"formula": c.FormulaU, "result": c.ResultIU}
    # Walk Connects for this connector
    out["connects"] = []
    for cn in conn.ContainingPage.Connects:
        if cn.FromSheet.ID == conn.ID:
            out["connects"].append({
                "FromCell": cn.FromCell.Name,
                "FromPart": cn.FromPart,
                "ToShape":  cn.ToSheet.NameU,
                "ToCell":   cn.ToCell.Name,
                "ToPart":   cn.ToPart,
            })
    return out
```



### 12.1 Triage table — symptom → cell to inspect

| Symptom                                                | Cell(s) to inspect                                 |
|--------------------------------------------------------|----------------------------------------------------|
| Connector floats free; no glue at all                  | `BeginX`, `EndX` formulas; `Connect.FromPart`     |
| Connector enters wrong side of the target              | `Connect.ToCell.Name`; `WalkPreference`           |
| Auto-layout reflowed and cables now lie about ports    | `ConFixedCode` (must be `6` for static)            |
| Diagonal line through an obstacle                      | `ShapeRouteStyle` (probably `16` by accident)      |
| Connector rendered as straight, not right-angle         | `ShapeRouteStyle` (should be `1`); `ConLineRouteExt` |
| Connector rendered curved when family expects straight  | `ConLineRouteExt` (must be `1`)                    |
| Two connectors cross with no jump                       | `LineJumpStyle` on PageSheet; `ConLineJumpCode`   |
| Jumps render as one-pixel gaps                          | `LineJumpFactorX`, `LineJumpFactorY` (probably `0`)|
| `Page.Layout()` does nothing for one connector          | `ConFixedCode` (probably `2`); also glue mode      |
| Arrow missing on what should be a directed edge         | `EndArrow`, `BeginArrow` (`VisArrowValues`)        |
| Arrow at the wrong end                                  | `EndArrow=0` and `BeginArrow=4` swapped            |
| `Connect.FromPart = -1`                                 | `BeginX`/`EndX` formula was hand-edited; re-glue  |

### 12.2 Why three values for `ConLineRouteExt`

| Value | What the engine draws                                                   |
|-------|-------------------------------------------------------------------------|
| `0`   | Inherit master geometry (Dynamic connector → right-angle).             |
| `1`   | Forced straight segments only; corners are perfect 90°.                 |
| `2`   | NURBS-smoothed Bezier between bend points.                              |

The runtime sets `1` for every static-glue family because the linter
otherwise cannot distinguish "intentionally curved schematic" from "the
auto-router smoothed the path and now the cable looks like it goes
through a server instead of around it".

---

## 13. End-to-end runtime call sequence per family

The canonical sequence the runtime emits when building a page from a
graph data structure. Every family follows the same skeleton; only the
constants change.

```python
def build_page(graph, family: str) -> None:
    profile = FAMILY_PROFILES[family]
    page = doc.Pages.Item(1)
    apply_family(page, profile)                                # §5.1

    # Drop 2-D shapes
    shapes = {}
    for node_id, attrs in graph.nodes.items():
        master = stencils[profile["master_for_node"]]
        s = page.Drop(master, attrs.get("x", 0), attrs.get("y", 0))
        s.Text = attrs["label"]
        shapes[node_id] = s

    # Connect them according to family policy
    conn_master = stencils[profile["connector_master"]]
    for src_id, dst_id, edge_attrs in graph.edges:
        conn = page.Drop(conn_master, 0, 0)
        if profile["glue"] == "static":
            row_b = edge_attrs["src_row"]
            row_e = edge_attrs["dst_row"]
            conn.Cells("BeginX").GlueTo(
                shapes[src_id].Cells(f"Connections.X{row_b}"))
            conn.Cells("EndX").GlueTo(
                shapes[dst_id].Cells(f"Connections.X{row_e}"))
            conn.Cells("ConFixedCode").FormulaForceU = "6"
            conn.Cells("ShapeRouteStyle").FormulaForceU = (
                str(profile["per_conn"]["ShapeRouteStyle"]))
            conn.Cells("ConLineRouteExt").FormulaForceU = "1"
        else:                                                  # dynamic
            conn.Cells("BeginX").GlueTo(shapes[src_id].Cells("PinX"))
            conn.Cells("EndX").GlueTo(shapes[dst_id].Cells("PinX"))
        conn.Cells("EndArrow").FormulaForceU = (
            str(edge_attrs.get("end_arrow", 4)))

    # Layout pass for dynamic-glue families only
    if profile["call_layout"]:
        page.Layout()
    page.ResizeToFitContents()

    # Verify
    assert_glue_policy(page, family)
    assert_route_cells(page, family, profile)
    assert_static_overrides(page, family)
```



### 13.1 Why static-glue families skip `Page.Layout()`

For static-glue families `profile["call_layout"]` is `False`. Two
reasons: (1) the placer (`PlaceStyle`) cannot move statically-pinned
shapes, their positions are user-given; (2) the router pass would
honour `ConFixedCode = 6` and skip every connector anyway, but it
would still recompute the page bounding box and possibly resize the
page via `ResizePage = TRUE` — rarely desired for a fixed-scale floor
plan or rack. Instead the runtime calls `page.ResizeToFitContents()`
directly.

### 13.2 Mixed-glue families (cross-functional flowchart, floor plan, class diagram)

Three families combine glue modes. The runtime walks edges twice:

- First pass: dynamic edges only. Set `ShapeRouteStyle = 0` so they
  inherit `DynamicConnectorRouteStyle`. `Page.Layout()` reflows them.
- Second pass: static edges. Set `ConFixedCode = 6`,
  `ShapeRouteStyle = 31`, `ConLineRouteExt = 1`. `Page.Layout()` skips
  every connector with `ConFixedCode >= 2`, so the static edges stay
  where they were authored while the dynamic edges still reflow.

---

## 14. Routing options master cell index

Quick lookup of every cell touched by the runtime, grouped by the
ShapeSheet section it lives in. Defaults written explicitly are marked
`*` (written even when matching the engine default, to make ShapeSheet
inspection deterministic across Visio builds).

| Section                | Cell                                | Default     | Per-family writer                                                       |
|------------------------|-------------------------------------|-------------|-------------------------------------------------------------------------|
| Page Layout (page)     | `PlaceStyle`                        | `0`         | §5 master table                                                         |
| Page Layout (page)     | `RouteStyle`                        | `1`         | §5 master table                                                         |
| Page Layout (page)     | `DynamicConnectorRouteStyle` *      | `1`         | §5 master table                                                         |
| Page Layout (page)     | `AvenueSizeX/Y` *                   | `0.375 in`  | §5; skipped for static families                                          |
| Page Layout (page)     | `BlockSizeX/Y` *                    | `0.25 in`   | §5; skipped for static families                                          |
| Page Layout (page)     | `ResizePage`                        | `0`         | `TRUE` for dynamic, `FALSE` for static (page calls `ResizeToFitContents` instead) |
| Page Layout (page)     | `LineJumpStyle`                     | `0`         | §6.3                                                                    |
| Page Layout (page)     | `LineJumpCode`                      | `1`         | §6.3                                                                    |
| Page Layout (page)     | `LineJumpFactorX/Y`                 | `0.66666`   | bump to `1.5` for printed schematics                                    |
| Page Layout (page)     | `LineToLineX/Y`, `LineToNodeX/Y`    | `0.125 in`  | rare; engine clamps below `0.0625 in`                                    |
| Page Layout (page)     | `PageLineJumpDirX/Y`                | `0`         | rare                                                                     |
| Page Layout (page)     | `PlowCode`, `DynamicsOff`, `CtrlAsInput`, `EnableGrid` | `0`/`1`     | template-static; flipped only for printed schematics                    |
| Shape Layout (1-D)     | `ShapeRouteStyle`                   | `0`         | static: `31` or `1`; dynamic: `0`                                        |
| Shape Layout (1-D)     | `ConFixedCode`                      | `0`         | static: `6`; dynamic: `0`; `1` to freeze a user-edited path              |
| Shape Layout (1-D)     | `ConLineRouteExt`                   | `0`         | static: `1`; mind map: `2`; else `0`                                     |
| Shape Layout (1-D)     | `WalkPreference`                    | `0`         | OrgChartNS / FlowchartNS / TreeNS: `1`; else `0`                         |
| Shape Layout (1-D)     | `ConLineJumpCode/Style/DirX/DirY`   | `0`         | backbone: `2`; spurs: `1`; else `0`                                       |
| 1-D Endpoints          | `BeginX/Y`, `EndX/Y`                | literal     | written by `Cell.GlueTo(...)`                                            |
| 1-D Endpoints          | `BegTrigger`, `EndTrigger`          | `_XFTRIGGER`| auto-written by `GlueTo`; rebuilds endpoint on target move               |
| Line Format (1-D)      | `BeginArrow`, `EndArrow`            | `0`         | per edge attribute (`0=none`, `4=filled`, `13=indented`)                 |
| Line Format (1-D)      | `BeginArrowSize`, `EndArrowSize`    | `2`         | rarely overridden                                                         |
| Line Format (1-D)      | `LineWeight`, `LineColor`, `LinePattern` | theme  | inherited from theme; `LinePattern` dashed for informational edges       |
| Connections (target)   | `Connections.X<row>/Y<row>`         | n/a         | static-glue endpoints reference these by name                             |
| Connections (target)   | `Connections.DirX<row>/DirY<row>`   | `0`         | outward unit vector used by AutoConnect side selection                   |
| Connections (target)   | `Connections.Type<row>`             | `0`         | `0=inward`, `1=outward`, `2=both`; `1` required for AutoConnect arrow    |
| User-defined (target)  | `User.msvShapeCategories`           | n/a         | tag set: `"FlowchartShape"`, `"NetworkDevice"`, `"Bus"`, etc.            |
| User-defined (target)  | `User.msvConnectionPointCount`      | derived     | linter uses this to detect runtime-created rows (§10.5)                  |



---

## 15. Quick decision flowchart

```
Is the diagram physical (rack / floor plan / P&ID / electrical / wiring / Gantt)?
│
├── YES → Static glue.
│        │
│        ├── Endpoint formula: PAR(PNT(Sheet.N!Connections.X<row>, …))
│        ├── ShapeRouteStyle: 31 (None) or 1 (RightAngle)
│        ├── ConFixedCode: 6 (never re-route, never split)
│        ├── ConLineRouteExt: 1 (straight)
│        ├── DynamicConnectorRouteStyle on page: 31 or 1
│        ├── PlaceStyle on page: 0 (no auto-placement)
│        ├── ResizePage on page: FALSE (call ResizeToFitContents instead)
│        └── Skip Page.Layout(); call ResizeToFitContents() only.
│
└── NO  → Dynamic glue (org chart / flowchart / tree / network / mind map / state / cloud / wireframe / …).
         │
         ├── Endpoint formula: PNT(Sheet.N!PinX, Sheet.N!PinY)
         ├── ShapeRouteStyle: 0 (inherit)
         ├── ConFixedCode: 0 (router controls)
         ├── DynamicConnectorRouteStyle on page: from §4.3 family table
         ├── PlaceStyle on page: from §4.3 family table
         ├── AvenueSizeX/Y, BlockSizeX/Y: from §5 master table
         ├── ResizePage on page: TRUE
         └── Call Page.Layout() then ResizeToFitContents().

Mixed-glue family (cross-functional flowchart, floor plan with furniture,
class diagram with inheritance + association)?
         │
         └── Apply dynamic policy first, then loop over edges marked
             "anchor=true" and overwrite their cells with the static
             policy. Page.Layout() routes only the dynamic ones because
             ConFixedCode=6 freezes the static set.
```

---

## 16. Cross-references

- `shapesheet-quick-ref.md` — full ShapeSheet cell taxonomy and
  `Cell.FormulaForceU` semantics.
- `vsdx-format-quick-ref.md` — OPC layout, `pages/page<n>.xml`,
  `<Connect>` element schema for direct XML authoring of routing cells.
- `diagram-types.md` — per-template defaults, the canonical "family"
  enumeration the runtime keys against.
- `automation-decision-matrix.md` — when to call `Page.Layout()` vs
  `LayoutIncremental` vs `LayoutChangeDirection`.
- `theme-and-data-graphics.md` — line weight / color / pattern rules
  that interact with §14.4.
- `troubleshooting.md` — symptom → cell triage table that consumes
  §12.1.
- `com-quick-ref.md` — `Cell.GlueTo` / `GlueToPos` / `Unglue`,
  `Connect` collection enumerations, `pythoncom` apartment rules.

---

## Sources

- `research/18-connectors-routing.md` — full inventory of connector
  masters, glue API surface (`Cell.GlueTo`, `Cell.GlueToPos`, `Connect`
  collection, `FromPart` / `ToPart` enums), the eighteen documented
  `VisCellVals` route-style constants, the six line-jump cells,
  AutoConnect / `DropConnected` API, and ShapeSheet reference for every
  per-connector and page-level cell touched in this document.
- `research/19-auto-layout.md` — `Page.Layout()` /
  `LayoutIncremental` / `LayoutChangeDirection` semantics, the Page
  Layout ShapeSheet section (`PlaceStyle`, `RouteStyle`,
  `AvenueSizeX/Y`, `BlockSizeX/Y`, `LineJumpStyle`, `LineJumpCode`,
  `LineToLineX/Y`, `LineToNodeX/Y`, `ResizePage`, `PlowCode`,
  `DynamicsOff`), the `visPLOPlace*` and `visLORoute*` enumeration
  tables (with the `RouteStyle = 2` vs `DynamicConnectorRouteStyle = 8`
  alias caveat), `ContainerProperties.ResizeAsNeeded` interaction with
  `Layout()`, and `FixedCode` bitmask for excluding shapes from layout.

