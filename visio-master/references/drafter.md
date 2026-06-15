# Drafter — Per-Page Visio Authorship Reference

> The Drafter is the Visio analogue of `ppt-master`'s Executor. It is the role
> the same agent steps into after Architect has emitted `diagram_spec.md` and
> `diagram_lock.md`. Drafter authors **one Visio Page fragment per output
> page, hand-written, sequentially, in one continuous main-agent context**.
> Theme application, data-graphics binding, container/list refit, and layer
> organisation are NOT Drafter's concern — those belong to Stylist (Step 6.5).
>
> Read this file in full before authoring the first page of any drawing.
> Re-read sections 2 and 7 (per-page lock discipline + banned techniques)
> when context budget is tight.

---

## 1. Role Identity

| Attribute | Value |
|---|---|
| Reference file | `visio-master/references/drafter.md` (this file) |
| Step in pipeline | Step 6 — Drafter Phase (between Architect's lock and Stylist's theme pass) |
| Inputs | `<project>/diagram_spec.md` §IX, `<project>/diagram_lock.md` (re-read per page), `templates/page-layouts/<basename>.vsdx-page.xml`, `templates/diagram-templates/<diagram>.vsdx-page.xml`, `templates/stencils/<set>/` masters |
| Outputs | `<project>/pages/<NN>_<page_name>.vsdx-page.xml`, optional `<NN>_<page_name>.shapesheet-notes.md` |
| Forbidden inputs | Memory of prior pages' colors / fonts / stencil names (always re-read the lock); ad-hoc HEX values invented at draft time |
| Hand-off to | Stylist Phase 6.5 (`stylist.md`) for theme application, layer assignment, container refit, data-graphics binding |
| Quality gate | `vsdx_quality_checker.py <project_path>` MUST report 0 errors before Stylist starts |

The Drafter persona is mode-conditioned. The marker block opening every Drafter
turn looks like:

```
## [Role Switch: Drafter]
📖 Reading role definition: references/drafter.md
📋 Current task: Author Visio Page <NN>_<page_name>
```

The marker is load-bearing — it both pins the agent on this reference and
creates an audit trail. Switch markers also separate Drafter output from
Architect's preceding `diagram_lock.md` so post-processing scripts can find
the page-fragment boundaries.

### 1.1 What Drafter does NOT do

Drafter is a **page authorship** role. It does not:

| Concern | Owner |
|---|---|
| Theme XML emission, color variant resolution | Stylist (`apply_theme.py`) |
| Layer creation on the PageSheet | Stylist (writes `Layers` section) |
| Data Graphic binding (`User.msvCalloutType`, etc.) | Stylist (after final shape inventory) |
| Container refit / List ordering recomputation | Stylist (`assemble_containers.py`) |
| Master / stencil resolution into the document stencil | `finalize_vsdx.py` (`embed_masters.py`) |
| OPC zip composition | `vsdx_export.py` |

Drafter declares semantic intent (which master is dropped, which shape glues to
which) and writes the canonical ShapeSheet cells; downstream scripts and Stylist
turn that intent into a working `.vsdx`.

### 1.2 Output file shape

Each page is a single XML fragment named `<NN>_<page_name>.vsdx-page.xml`
where `<NN>` is two digits starting at `01` and `<page_name>` matches
`diagram_spec.md §IX` for that page. The fragment is a `<Page>` element
containing exactly one `<PageSheet>` and exactly one `<Shapes>` child, plus
an optional `<Connects>` child:

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Page xmlns="http://schemas.microsoft.com/office/visio/2012/main"
      ID="<NN>" NameU="<page_name>">
  <PageSheet>
    <!-- Page-level cells: PageWidth, PageHeight, DrawingScale,
         DynamicConnectorRouteStyle, LineJumpStyle, ResizePage, ... -->
  </PageSheet>
  <Shapes>
    <!-- One <Shape> per top-level shape; nested <Shapes> for groups -->
  </Shapes>
  <Connects>
    <!-- One <Connect> per glued connector endpoint -->
  </Connects>
</Page>
```

The fragment is **not a complete `.vsdx` part** — `finalize_vsdx.py` later
wraps it in the OPC namespace declarations and merges with the document-wide
`pages.xml`. Drafter only authors the inner content. Element ordering inside
`<Shape>` is `<Cell>*` then `<Section>*` then nested `<Shapes>` (per the
Visio 2012 schema); writing them out of order produces files Visio refuses
to open.

---

## 2. Per-Page `diagram_lock.md` Re-Read Discipline

> Long drawings drift off the declared palette / stencil / typography mid-deck
> due to context compression. `diagram_lock.md` is the canonical execution
> reference — re-read it per page to bypass model memory. This is the single
> mechanism that resists compression on long drawings (rule 8 of the Global
> Execution Discipline in `_BLUEPRINT.md` §7.1).

### 2.1 The hard rule

**Before authoring each Visio Page**, Drafter MUST execute:

```
read_file <project_path>/diagram_lock.md
```

Use only values from this file. Not from memory, not from a sibling page that
"obviously matches", not from a half-remembered HEX. If context was
auto-compacted between pages, also re-read `<project_path>/diagram_spec.md` for
the current page's §IX brief.

The lock has the closed-vocabulary section list:

| Section | Drafter consults for |
|---|---|
| `## canvas` | `format`, `units`, `width`, `height`, `dpi` → emitted into PageSheet `PageWidth` / `PageHeight` cells; drawing scale baseline |
| `## mode` | Narrative skeleton (`pyramid` / `narrative` / `instructional` / `showcase` / `briefing` / `custom`) — affects shape ordering and label register, not geometry |
| `## visual_style` | Aesthetic posture name; opens the matching overlay file at `references/visual-styles/<name>.md` |
| `## colors` | Every fill, stroke, text color HEX — ONLY values from this section may appear in `<Cell N="FillForegnd">`, `<Cell N="LineColor">`, `<Cell N="Char.Color">`. No invented HEX. |
| `## typography` | `font_family`, plus role overrides `title_family` / `body_family` / `emphasis_family` / `code_family`; sizes follow the body-anchored ramp |
| `## stencils` | `set` (one primary), `brand_set` (optional), `inventory` (allowed master names), `connector_style`, `connector_default_routing` |
| `## images` | Approved image filenames; no invented references |
| `## page_rhythm` | Per-page tag (`anchor` / `dense` / `breathing`) governing density discipline (§5.1) |
| `## page_layouts` | Per-page basename mapping to a `templates/page-layouts/<basename>.vsdx-page.xml` template |
| `## page_diagrams` | Per-page diagram-template mapping to `templates/diagram-templates/<diagram>.vsdx-page.xml` |
| `## page_data_links` | Per-page data binding (Drafter passes through; Stylist consumes) |
| `## layout` | `algorithm`, `spacing` — drives `PageSheet.PlaceStyle` and spacing cells |
| `## connectors` | `routing`, `label_position`, `line_end_default` — drives `PageSheet.DynamicConnectorRouteStyle` and per-connector arrow cells |
| `## forbidden` | Patterns the user explicitly banned for this drawing (in addition to §7 banned techniques) |

### 2.2 What "use only values from the lock" means in practice

| Cell to emit | Source field |
|---|---|
| `<Cell N="FillForegnd" V="#1A73E8"/>` on a process shape | `colors.primary` (verbatim HEX) |
| `<Cell N="LineColor" V="#37474F"/>` on a connector | `colors.border` |
| `<Cell N="Char.Color" V="#212121"/>` on shape text | `colors.text` |
| `<Cell N="Char.Font" V="14"/>` paired with font index | Drafter resolves `typography.body_family` to a font index in `<Document>/<DocumentSettings>` written by Stylist; Drafter uses index 14 (or whatever index Architect declared in `typography.font_index`) |
| `<Cell N="Char.Size" V="0.166666"/>` on body text | `typography.body` (12pt → 0.1667 in) |
| `<Cell N="PageWidth" V="11"/>` | `canvas.width` (in `canvas.units`) |
| `<Shape Master="..."/>` reference | `stencils.inventory` master `NameU` |

If the lock does not contain the value, Drafter MUST surface a `warning:` line
and either request lock extension or skip the page until Architect updates the
lock via `update_diagram_lock.py`. Inventing a HEX, a font, or a master name
is a workflow failure even if the result "looks fine".

### 2.3 Per-page `page_rhythm` lookup

Before drawing each page, look up the entry in `page_rhythm` (key format
`P<NN>` matching the page index in §IX of `diagram_spec.md`):

| Tag | Layout discipline |
|---|---|
| `anchor` | Structural page (cover / chapter / TOC / ending). Inherit a `page-layouts/<basename>.vsdx-page.xml` template **verbatim**; hand-edits are minimal — page title, subtitle, version stamp, footer text. Geometry of frame elements is not Drafter's to alter. |
| `dense` | Information-heavy diagram page. Multi-region layouts, swim-lane bands, full network topology with annotations, BPMN with parallel gateways, ERD with many entities — all permitted. This is the baseline for technical drawings. |
| `breathing` | Single-concept hero page. Focal callout, big statement, single-shape display, transition page. Avoid multi-region grids (no 2×2 quadrants, no 3-card swim, no KPI dashboards). Use one strong visual, supported by whitespace and one helper element. |

Missing `page_rhythm` section → emit
`warning: diagram_lock.md missing page_rhythm — defaulting all pages to dense`
once per drawing, fall back to `dense` for every page.

Tag missing for current page → emit
`warning: diagram_lock.md page_rhythm tag not found for P<NN> — falling back to dense`
once per drawing aggregated, fall back to `dense`. Do not invent a tag.

### 2.4 Per-page `page_layouts` lookup

| Lock state | Drafter behaviour |
|---|---|
| Entry present (e.g. `P04: 03a_content_diagram_focus`) → inherit the corresponding XML fragment already in context from §3.0 batch read. The basename **must match** an actual file in `templates/page-layouts/<chosen>/`; if it doesn't, emit `warning: page_layouts P<NN> references missing file <basename>.vsdx-page.xml — falling back to free design` and proceed. |
| No entry for this page → free design. **Not an error** — Architect intentionally left this page free. |
| Whole section absent → see §3 fallback (legacy page-type matching). |

Do NOT invent a layout entry, and do NOT assume a template just because
`templates/page-layouts/` exists. If `page_layouts` is present but silent for
this page, that silence is the instruction.

### 2.5 Per-page `page_diagrams` lookup

| Lock state | Drafter behaviour |
|---|---|
| Entry present (e.g. `P09: bpmn_basic`) → adapt the corresponding diagram template (already loaded). Apply project colors / typography / connector style; do not copy verbatim. Cross-reference `templates/diagram-templates/diagrams_index.json` for the diagram's purpose summary. |
| No entry for this page → either no central diagram on this page, or a diagram that didn't match the catalog (Architect's `no-template-match` fallback). Design the visualization from scratch using `diagram_spec.md §VII Visualization Reference`. |
| Whole section absent → no diagram-template pages in this drawing. |

---

## 3. Pre-Generation Batch Read

> Cached prompt prefix economics. Read every distinct template / diagram /
> stencil-master file ONCE up front; per-page `diagram_lock.md` re-reads
> append below the prefix and benefit from cache. Scattered on-demand reads
> of layout / diagram XML invalidate downstream cache and sit in the
> compression-vulnerable mid-context region.

### 3.0 What to batch-read before page 1

Read each of the following exactly once before authoring the first page:

| Source list | Read path |
|---|---|
| Architect's lock (already authored) | `<project>/diagram_lock.md` |
| Architect's narrative (for §IX page roster) | `<project>/diagram_spec.md` |
| Every distinct `page_layouts` basename | `templates/page-layouts/<chosen>/<basename>.vsdx-page.xml` |
| Every distinct `page_diagrams` template | `templates/diagram-templates/<diagram>.vsdx-page.xml` |
| Stencil set master inventory | `templates/stencils/<stencils.set>/README.md` (catalog of allowed `NameU` values + connection-point conventions) |
| Brand stencil README, if `stencils.brand_set` is set | `templates/stencils/<brand_set>/README.md` |
| Locked visual-style overlay | `references/visual-styles/<visual_style>.md` |
| Locked mode overlay | `references/modes/<mode>.md` |
| Connector authoring guide | `references/connectors.md` |
| Visio Pages XML authoring guide | `references/visio-pages-xml.md` |
| Shared technical constraints | `references/shared-standards.md` |

**Default — read each file once; re-read only on the mid-deck exception
below**. The exception: user adds a page mid-drawing that introduces a new
basename / diagram / stencil set absent from the original batch — read the
new file once, continue.

`diagram_lock.md` is the **only** file re-read per page (§2.1).

### 3.1 Resolution order per page

When deciding which template a page inherits, Drafter consults the lock in
this strict order:

1. `diagram_lock.page_layouts` has `P<NN>: <basename>` → inherit that page-
   layout fragment (already in context from §3.0).
2. `page_layouts` exists but **no entry** for this page → free design, no
   layout inheritance. Still apply `page_diagrams` if set.
3. `diagram_lock.page_diagrams` has `P<NN>: <diagram>` → adapt that diagram
   template.
4. Neither section names this page → free design from scratch using
   `diagram_spec.md §VII` for visualization guidance.

### 3.2 Page-Template Mapping Declaration (Required Output)

Before generating each page, output which template is being used:

```
📝 **Page-layout mapping**: `templates/page-layouts/general/03b_content_diagram_focus.vsdx-page.xml` (or "None (free design)")
📝 **Diagram-template mapping**: `templates/diagram-templates/bpmn_basic.vsdx-page.xml` (or "None (free design)")
🎯 **Adherence rules / layout strategy**: [specific description per the rhythm tag]
```

This pair of declarations creates a bookmark for `vsdx_quality_checker.py`
and makes review easy: a reader can match the declared inheritance against
the emitted XML.

---

## 4. Shape-Drop Pattern

The Visio analogue of "drop a master onto the page". Drafter declares the
intent in XML; `finalize_vsdx.py` resolves the master into the document
stencil, allocates a `BaseID` / `UniqueID`, and writes the binary `.vsdx`.

### 4.1 Anatomy of a shape drop in Visio Pages XML

Every dropped instance is a `<Shape>` element with:

| Attribute | Required | Meaning |
|---|---|---|
| `ID` | yes | 1-based unique integer per page; never reused after delete |
| `NameU` | yes | Universal (locale-invariant) name; default = master `NameU` + numeric suffix on collision |
| `Name` | optional | Localised display name (defaults to `NameU` if absent) |
| `Type` | yes | `"Shape"` for normal instance, `"Group"` for groups, `"Foreign"` for OLE/image, `"Guide"` for guides |
| `Master` | conditional | The master index in `<MasterContents>`; required when the instance derives from a master. Inheritance walks instance → master → style. |
| `LineStyle` | optional | Style index for line formatting (Stylist may add) |
| `FillStyle` | optional | Style index for fill |
| `TextStyle` | optional | Style index for text |

The minimal 2-D drop:

```xml
<Shape ID="5" NameU="Process.5" Type="Shape" Master="2">
  <Cell N="PinX" V="2.5"/>
  <Cell N="PinY" V="6.0"/>
  <Cell N="Width" V="1.5"/>
  <Cell N="Height" V="0.75"/>
  <Cell N="LocPinX" F="Width*0.5"/>
  <Cell N="LocPinY" F="Height*0.5"/>
  <Text>Validate Order</Text>
</Shape>
```

Cell ordering inside `<Shape>`: `<Cell>*` first, then `<Section>*` (Geometry,
Connections, User, Prop, Actions, Controls), then `<Text>` last. Visio's
schema validator rejects shapes where `<Text>` precedes `<Cell>`.

### 4.2 The seven cell discipline for every 2-D shape

A 2-D shape MUST carry these seven Shape Transform cells. Omitting any one
causes Visio to compute a default that contradicts the layout:

| Cell | Universal name | Source |
|---|---|---|
| Pin X | `PinX` | Coordinate in `canvas.units` from page origin |
| Pin Y | `PinY` | Same |
| Width | `Width` | Logical width in `canvas.units` |
| Height | `Height` | Logical height |
| Local Pin X | `LocPinX` | Default formula `Width*0.5` (centre); `0` for top-left anchored |
| Local Pin Y | `LocPinY` | Default formula `Height*0.5` |
| Angle | `Angle` | `0 deg` for axis-aligned shapes; never omit even when zero |

Coordinate origin: Visio's page origin is at the **bottom-left corner**, Y
increases upward. This is the inverse of SVG. A shape at `PinX=2, PinY=8` on
a Letter page (8.5" × 11" landscape with `canvas.format=letter-landscape`,
PageWidth=11", PageHeight=8.5") sits two inches from the left, eight inches
from the bottom — i.e. near the top.

### 4.3 The seven cell discipline for every 1-D shape (connector)

A 1-D shape (connector) carries the four endpoint cells plus three derived
cells which Visio computes by default formulas — emit them anyway because
the recalc engine sometimes misses them on a fresh fragment:

| Cell | Default formula | Notes |
|---|---|---|
| `BeginX` | (literal coord) or `PNT(Sheet.<id>!PinX, Sheet.<id>!PinY)` for dynamic glue | Tail X |
| `BeginY` | same | Tail Y |
| `EndX` | (literal coord) or `PNT(Sheet.<id>!PinX, Sheet.<id>!PinY)` | Head X |
| `EndY` | same | Head Y |
| `PinX` | `F="(BeginX+EndX)/2"` | Midpoint, derived |
| `PinY` | `F="(BeginY+EndY)/2"` | Derived |
| `Width` | `F="SQRT((EndX-BeginX)^2+(EndY-BeginY)^2)"` | Length, derived |
| `Angle` | `F="ATAN2(EndY-BeginY,EndX-BeginX)"` | Derived |

A connector with `Type="Shape"` plus the `1-D Endpoints` section is what
Visio recognises as a connector. The `<Cell N="...">` attribute `V` is the
evaluated value (used when no formula) and `F` is the formula (preferred
for derived cells).

### 4.4 Master inventory verification

Before emitting `Master="<index>"`, confirm the master is in
`diagram_lock.stencils.inventory`. The inventory lists `NameU` values; the
index referenced in the page-XML maps via `<MasterContents>` (resolved by
`embed_masters.py` post-Drafter). For now, Drafter writes a placeholder
attribute `Master="@<NameU>"` — `embed_masters.py` rewrites these to integer
indices once it knows the document stencil contents.

Example placeholder form Drafter emits:

```xml
<Shape ID="5" NameU="Process.5" Type="Shape" Master="@Process">
```

`embed_masters.py` resolves `@Process` to `Master="2"` (or whatever the
local-stencil index becomes after the master is ensured).

### 4.5 Allowed master names — verification table

The inventory's `NameU` values are stencil-set-specific. Examples:

| Stencil set (`stencils.set`) | Allowed master `NameU` (subset) |
|---|---|
| `flowchart-basic` | `Process`, `Decision`, `Start/End` (terminator), `Document`, `Data`, `Predefined Process`, `Manual Operation`, `Off-page Reference`, `Connector`, `Dynamic connector` |
| `flowchart-advanced` | All `flowchart-basic` plus `Database`, `Direct Data`, `Display`, `Manual Input`, `Card`, `Internal Storage`, `Sequential Data`, `On-page Reference`, `Magnetic Disk`, `Sort`, `Merge`, `Extract`, `Or`, `Summing Junction` |
| `bpmn-2.0` | `Activity`, `Subprocess`, `Call Activity`, `Task (User)`, `Task (Service)`, `Task (Manual)`, `Start Event`, `Intermediate Event`, `End Event`, `Boundary Event`, `Gateway (Exclusive)`, `Gateway (Parallel)`, `Gateway (Inclusive)`, `Gateway (Event-based)`, `Sequence Flow`, `Message Flow`, `Association`, `Pool`, `Lane`, `Data Object`, `Data Store`, `Group`, `Text Annotation` |
| `network-rack` | `Rack frame`, `Server (1U)`, `Server (2U)`, `Server (4U)`, `Switch`, `Router`, `Firewall`, `Patch panel`, `KVM`, `Console`, `PDU`, `UPS` |
| `network-azure` | Brand-specific subset; consult `templates/stencils/network-azure/README.md` for the inventory |
| `engineering-isa` | ISA-5.1 P&ID symbols; consult set-specific README |
| `org-personas` | `Executive`, `Manager`, `Position`, `Role`, `Consultant`, `Vacancy`, `Assistant`, `Three-position`, `Multiple positions`, `Dotted-line` (1-D) |
| `mindmap-organic` | `Topic`, `Subtopic`, `Branch`, `Leaf`, `Connector (curved)` |

Drafter MUST NOT use a `NameU` that is not in the locked
`stencils.inventory`. Even if the canonical Visio install has the master
available, mixing stencil semantics breaks the visual contract Architect
established.

### 4.6 Coordinate quantisation

All `PinX` / `PinY` / `Width` / `Height` numeric literals are emitted in
the page's declared `canvas.units` (inch or mm). Use a fixed precision:

| Canvas unit | Decimal places | Snap multiple |
|---|---|---|
| `in` | 4 (e.g. `2.1250`) | `0.0625` (1/16") for general layout, `0.125` (1/8") for grid-aligned shapes |
| `mm` | 2 (e.g. `54.00`) | `1.00 mm` for general, `5.00 mm` for grid-aligned |

Mixing inch literals on a millimetre-canvas page is a workflow failure even
though Visio accepts it silently. The quality checker flags shapes whose
units don't match `canvas.units`.

---

## 5. Connector Pattern

> Connectors are 1-D shapes whose endpoints are either *unattached*
> (literal coordinates), *glued to a point* on a target shape (point-to-
> point, "static" glue), or *glued to the whole shape* (shape-to-shape,
> "dynamic" glue). The mode is determined by the formula written into
> `BeginX` / `EndX` — not by a separate property — so connector authoring
> is fundamentally about writing the right formula and the matching
> `<Connect>` rows.

### 5.1 The two glue modes

| Mode | Endpoint formula | Use when |
|---|---|---|
| **Dynamic** (shape-to-shape) | `BeginX = PNT(Sheet.<srcID>!PinX, Sheet.<srcID>!PinY)` | The diagram should let the auto-router choose the cleanest entry side. Default for org charts, trees, flowcharts where shapes may move. |
| **Static** (point-to-point) | `BeginX = PAR(PNT(Sheet.<srcID>!Connections.X1, Sheet.<srcID>!Connections.Y1))` | The diagram pins endpoints to specific connection points (P&ID, electrical schematics, fixed engineering diagrams). |

`stencils.connector_default_routing` in the lock determines which mode
Drafter uses by default:

| `connector_default_routing` | Default mode |
|---|---|
| `flowchart` / `tree` / `network` | Dynamic glue |
| `organic` (mind maps) | Dynamic glue (lets curve routing breathe) |
| any with explicit per-connector override in `connectors.label_position` set to `endpoint-label` | Static glue, glued to the labelled connection point |

### 5.2 Emitting a connector with dynamic glue

Two parts: the `<Shape>` element plus two `<Connect>` rows.

```xml
<!-- Inside <Shapes> -->
<Shape ID="3" NameU="Dynamic connector.3" Type="Shape" Master="@Dynamic connector">
  <Cell N="BeginX" V="3.0" F="PNT(Sheet.1!PinX,Sheet.1!PinY)"/>
  <Cell N="BeginY" V="6.5" F="PNT(Sheet.1!PinX,Sheet.1!PinY)"/>
  <Cell N="EndX"   V="5.0" F="PNT(Sheet.2!PinX,Sheet.2!PinY)"/>
  <Cell N="EndY"   V="6.5" F="PNT(Sheet.2!PinX,Sheet.2!PinY)"/>
  <Cell N="PinX"   F="(BeginX+EndX)/2"/>
  <Cell N="PinY"   F="(BeginY+EndY)/2"/>
  <Cell N="Width"  F="SQRT((EndX-BeginX)^2+(EndY-BeginY)^2)"/>
  <Cell N="Angle"  F="ATAN2(EndY-BeginY,EndX-BeginX)"/>
  <Cell N="ShapeRouteStyle" V="1"/>      <!-- visLORouteRightAngle -->
  <Cell N="EndArrow"        V="4"/>      <!-- filled arrowhead -->
  <Cell N="BeginArrow"      V="0"/>      <!-- no tail arrow -->
</Shape>

<!-- Inside <Connects> at the bottom of <Page> -->
<Connect FromSheet="3" FromCell="BeginX" FromPart="9"
         ToSheet="1"   ToCell="PinX"     ToPart="3"/>
<Connect FromSheet="3" FromCell="EndX"   FromPart="12"
         ToSheet="2"   ToCell="PinX"     ToPart="3"/>
```

### 5.3 The `FromPart` / `ToPart` constants

Drafter MUST emit numeric literals matching the `VisFromParts` / `VisToParts`
enumerations. The quality checker rejects values outside these tables.

| `FromPart` constant | Value | Meaning |
|---|---|---|
| `visBegin` | `9` | Connector start endpoint |
| `visEnd` | `12` | Connector end endpoint |
| `visControlPoint` | `100 + row` | Endpoint glued via a control handle |
| `visConnectFromError` | `-1` | Endpoint formula unresolvable (NEVER emit; this is a runtime sentinel) |

| `ToPart` constant | Value | Meaning |
|---|---|---|
| `visGuideX` | `1` | Glued to a vertical guide line |
| `visGuideIntersect` | `2` | Glued to a guide intersection |
| `visWholeShape` | `3` | Dynamic glue (target = whole shape) — most common |
| `visGuideY` | `4` | Glued to a horizontal guide line |
| `visToAngle` | `7` | Glued at an angle |
| `visConnectionPoint` | `100 + row` | Static glue to connection-point row N (row 0 → 100, row 1 → 101, ...) |

Pairing of `FromCell` and `ToCell`:

| Glue mode | `FromCell` | `ToCell` | `FromPart` (begin) | `ToPart` |
|---|---|---|---|---|
| Dynamic, begin endpoint | `BeginX` | `PinX` | `9` | `3` |
| Dynamic, end endpoint | `EndX` | `PinX` | `12` | `3` |
| Static to row 1, begin | `BeginX` | `Connections.X1` | `9` | `100` |
| Static to row 2, begin | `BeginX` | `Connections.X2` | `9` | `101` |
| Static to row N, end | `EndX` | `Connections.X<N>` | `12` | `99 + N` |

### 5.4 Per-connector routing override

`stencils.connector_style` sets the deck-wide default; per-connector
override happens via the `ShapeRouteStyle` cell on the connector itself.
Constants from `VisCellVals`:

| Constant | Value | Behaviour |
|---|---|---|
| `visLORouteDefault` | `0` | Inherit page-level setting |
| `visLORouteRightAngle` | `1` | 90° corners (canonical flowchart) |
| `visLORouteStraight` | `2` | Straight line, ignore obstacles |
| `visLORouteOrgChartNS` | `4` | Org chart, vertical |
| `visLORouteOrgChartEW` | `5` | Org chart, horizontal |
| `visLORouteOrgChartNSCompact` | `6` | Org chart vertical, compact |
| `visLORouteOrgChartEWCompact` | `7` | Org chart horizontal, compact |
| `visLORouteFlowchartNS` | `8` | Flowchart top-down |
| `visLORouteFlowchartEW` | `9` | Flowchart left-right |
| `visLORouteTreeNS` | `10` | Tree top-down |
| `visLORouteTreeEW` | `11` | Tree left-right |
| `visLORouteNetwork` | `12` | Radial / network |
| `visLORouteCenterToCenter` | `16` | Straight centre-to-centre |
| `visLORouteSimpleNS` | `17` | Simple right-angle vertical |
| `visLORouteSimpleEW` | `18` | Simple right-angle horizontal |
| `visLORouteNone` | `31` | No routing; literal `BeginX`/`EndX` only |

Mapping from the lock's `connectors.routing` term to the constant:

| Lock `connectors.routing` | Page-level cell value (`DynamicConnectorRouteStyle`) |
|---|---|
| `flowchart` | `8` (`visLORouteFlowchartNS`) for vertical decks, `9` for horizontal |
| `network` | `12` (`visLORouteNetwork`) |
| `tree` | `10` for vertical trees, `11` for horizontal |
| `organic` | `16` (`visLORouteCenterToCenter`) — gives the curved-rest routing for organic mind maps |

### 5.5 Connector arrowheads

`BeginArrow` and `EndArrow` reference `VisArrowValues`:

| Constant | Value | Visual |
|---|---|---|
| `visArrowNone` | `0` | No arrow |
| `visArrowOpen` | `1` | Open chevron |
| `visArrowHollow` | `2` | Hollow triangle |
| `visArrowLine` | `3` | Line-only chevron |
| `visArrowFilled` | `4` | Filled triangle (default for `Dynamic connector` arrow variant) |
| `visArrowOpenThin` | `5` | Open thin |
| `visArrowIndentedFilled` | `13` | Indented filled |

Lock-driven default: `connectors.line_end_default` declares the deck-wide
arrow id. Drafter emits the same value on every connector unless the page
brief overrides for a specific edge (e.g. a return arrow on a feedback
loop).

### 5.6 Page-level connector cells

Drafter emits the page-level connector defaults in `<PageSheet>`. These
are inherited by every connector on the page that has its `ShapeRouteStyle = 0`.

```xml
<PageSheet>
  <Cell N="DynamicConnectorRouteStyle" V="8"/>   <!-- flowchart NS -->
  <Cell N="LineJumpStyle"              V="1"/>   <!-- arc jumps -->
  <Cell N="LineJumpFactorX"            V="0.6667"/>
  <Cell N="LineJumpFactorY"            V="0.6667"/>
  <Cell N="LineJumpCode"               V="1"/>   <!-- horizontal jumps -->
  <Cell N="AvenueSizeX"                V="0.375"/>
  <Cell N="AvenueSizeY"                V="0.375"/>
  <Cell N="BlockSizeX"                 V="0.25"/>
  <Cell N="BlockSizeY"                 V="0.25"/>
  <Cell N="ResizePage"                 V="0"/>   <!-- never auto-grow page -->
  <!-- ...rest of page sheet... -->
</PageSheet>
```

### 5.7 Line jumps

When two connectors cross, Visio renders a "jump" on one of them. Six cells
govern the rendering:

| Cell | Where | Values |
|---|---|---|
| `LineJumpStyle` | PageSheet | `0`=none, `1`=arc, `2`=gap, `3`=square, `4`=sides 2, `5`=sides 3 |
| `LineJumpFactorX` | PageSheet | Multiplier on jump width (default `0.66666`) |
| `LineJumpFactorY` | PageSheet | Multiplier on jump height (default `0.66666`) |
| `LineJumpCode` | PageSheet | `0`=none, `1`=horizontal jumps, `2`=vertical jumps, `3`=last-drawn jumps |
| `ConLineJumpStyle` | Connector | Per-connector override; `0` = page default |
| `ConLineJumpCode` | Connector | `0`=page default, `1`=always jump, `2`=never jump, `3`=other connector jumps |

For "backbone bus, branches arc over it" pattern: set the bus connector's
`ConLineJumpCode = 2` (never jumps) and each branch's `ConLineJumpCode = 1`
(always jumps). This is the canonical electrical-schematic look.

---

## 6. Glue Verification

> Connector glue is the most error-prone surface in Visio authoring.
> Drafter MUST verify glue completeness on every connector before declaring
> a page done. The verification has three layers: structural (XML cells
> present), referential (target shape exists on the same page), and
> semantic (the `Connect` row matches the cell formula).

### 6.1 Structural verification — every connector has the eight 1-D cells

For every `<Shape>` whose XML contains a `BeginX` cell, the following eight
cells MUST be present:

```
BeginX, BeginY, EndX, EndY, PinX, PinY, Width, Angle
```

Missing any one is a structural error. The quality checker rejects with
`error: connector <ID> missing 1-D Endpoints cell <name>`.

Quick self-check pattern Drafter applies before emitting:

| Cell | Form |
|---|---|
| `BeginX` | `V="<lit>" F="<formula>"` if glued; `V="<lit>"` if floating |
| `EndX` | same |
| `PinX` | `F="(BeginX+EndX)/2"` |
| `Width` | `F="SQRT((EndX-BeginX)^2+(EndY-BeginY)^2)"` |
| `Angle` | `F="ATAN2(EndY-BeginY,EndX-BeginX)"` |

### 6.2 Referential verification — `<Connect>` rows reference live shapes

For every `<Connect>` row in `<Connects>`:

| Field | Verification |
|---|---|
| `FromSheet` | An `<Shape ID="...">` with that ID exists on the same page |
| `FromCell` | The referenced shape has a `<Cell N="<FromCell>"/>` element |
| `ToSheet` | An `<Shape ID="...">` with that ID exists on the same page |
| `ToCell` | The referenced shape has a `<Cell N="<ToCell>"/>` element OR is a known sentinel cell name (`PinX`, `Connections.X<n>`) |
| `FromPart` | Integer in `{9, 12, 100..199}` |
| `ToPart` | Integer in `{1, 2, 3, 4, 7, 100..199}` |

A connector with cell formulas referencing `Sheet.5!PinX` MUST have a
matching `<Connect FromSheet="<this connector ID>" ToSheet="5" ...>` row.
A connector with formulas but no `<Connect>` row produces a "static-position
connector" — visually identical, but layout engines and `verify-diagrams`
treat it as untracked and may rebuild the formula on the next save.

### 6.3 Semantic verification — formula matches the `<Connect>` row

The connector cell formula and the `<Connect>` row encode the same glue
twice; they must agree:

| Formula | `FromPart` | `ToCell` | `ToPart` |
|---|---|---|---|
| `BeginX = PNT(Sheet.5!PinX,Sheet.5!PinY)` | `9` (`visBegin`) | `PinX` | `3` (`visWholeShape`) |
| `EndX = PNT(Sheet.5!PinX,Sheet.5!PinY)` | `12` (`visEnd`) | `PinX` | `3` |
| `BeginX = PAR(PNT(Sheet.5!Connections.X1,Sheet.5!Connections.Y1))` | `9` | `Connections.X1` | `100` (row 0) |
| `EndX = PAR(PNT(Sheet.5!Connections.X2,Sheet.5!Connections.Y2))` | `12` | `Connections.X2` | `101` (row 1) |

Mismatch produces a connector that visually works in Visio (because Visio
trusts the formula and rewrites `<Connect>` on the next save) but breaks
`vsdx_quality_checker.py` and any external tool that reads `<Connects>`.

### 6.4 Glue check Drafter runs after every connector

After emitting every `<Shape>` and `<Connect>` for a connector, Drafter
should mentally walk this checklist:

| Check | Pass criterion |
|---|---|
| Both endpoints have a glue formula | `BeginX`/`EndX` cells contain `F="..."` (formula), not just `V="..."` (literal) — unless the connector is intentionally floating |
| Source shape ID is on the same page | Every `Sheet.<id>` reference resolves to a `<Shape ID="<id>">` in the current page |
| Source shape is 2-D | The referenced shape has `PinX` cell (not `BeginX`) — only 2-D shapes are dynamic-glue targets |
| Static glue references a real connection-point row | If formula contains `Connections.X<N>`, the target shape has a `<Section N="Connection">` with row `<N>` |
| Two `<Connect>` rows per connector | One for begin (`FromPart="9"`), one for end (`FromPart="12"`) |
| `FromCell` matches the cell carrying the formula | If formula is on `BeginX`, `FromCell="BeginX"`; if on `EndX`, `FromCell="EndX"` |
| Arrow direction matches semantic intent | `EndArrow` is on the head end (where the arrow points to) |

### 6.5 Glue verification — structural quick check

`vsdx_quality_checker.py` glue checks (per `_BLUEPRINT.md` §7.3):

- **Glue completeness**: every `<Shape>` that has a `BeginX` cell has both
  `BeginX`/`BeginY` and `EndX`/`EndY` populated.
- **Connect parity**: every connector has 0 (floating), 1 (one-sided), or 2
  `<Connect>` rows; never 3+.
- **Connect target reachability**: every `<Connect ToSheet="N">` resolves
  to a shape `ID="N"` on the same page.
- **Connect cell coherence**: the `FromCell` value matches a cell that
  actually exists on the source connector shape.

### 6.6 Connector authoring failure modes

| Failure | Symptom | Fix |
|---|---|---|
| Forgot the `<Connect>` rows but wrote glue formulas | Visio opens the file but treats the connector as floating; the next interactive save rewrites the formula and discards the glue | Always emit both formula AND `<Connect>` row |
| Wrote the `<Connect>` row but the cell still has a literal `V` only | Visio overwrites with the literal value at next save; glue is lost | Always pair `<Connect>` with formula on the cell |
| `Sheet.5!PinX` references a shape ID that's on a different page | Visio displays `#REF!` in the cell; connector falls back to a literal endpoint | Validate Source/Target IDs against the current page's `<Shape ID>` set |
| Static glue to `Connections.X1` but the target master has no Connections section | Visio creates a default centred connection point and silently glues there; connector lands in the wrong spot | Verify the target master's stencil README lists the connection-point row |

---

## 7. Sequential Page Generation Rule

> Cross-page visual consistency is not a property of any one page; it lives
> in the agent's working memory of the pages already authored. Sub-agents,
> batch loops, and generator scripts all sever that memory. Drafter MUST
> author pages **sequentially, in one continuous main-agent context, one
> page per turn**.

### 7.1 The hard rule (rules 6, 7, 9 of Global Execution Discipline)

| Rule | Forbidden behaviour |
|---|---|
| **Rule 6 — NO SUB-AGENT PAGE GENERATION** | Drafter Step 6 page authorship is context-dependent and MUST be completed by the current main agent end-to-end. Delegating Visio Page generation to sub-agents is forbidden. |
| **Rule 7 — SEQUENTIAL PAGE GENERATION ONLY** | After global design context is confirmed, pages MUST be generated sequentially page by page in one continuous pass. Grouped batches (e.g. "5 at a time") are forbidden. |
| **Rule 9 — PAGES MUST BE HAND-WRITTEN, NOT SCRIPT-GENERATED** | Writing or running a script that produces page-XML files in batch — looping over pages, templating from data, emitting via a generator — is forbidden, including under "save tokens" / "quick draft" / "user is in a hurry" pretexts. |

### 7.2 What "sequential, hand-written" looks like in practice

| Allowed | Forbidden |
|---|---|
| Author page 01, then page 02, then page 03 in three consecutive Drafter turns | Author all pages in one turn by delegating each to a sub-agent |
| Re-read `diagram_lock.md` before each page | Cache the lock once and emit pages from memory |
| Hand-write each `<Shape>` element with attention to the page's narrative beat | Write a Python loop that templates a `<Shape>` for each row in a CSV |
| Reuse a successful pattern by re-typing the same XML fragment (with adjustments per the lock) | Vendor a generator that emits the pattern to many pages in a single run |
| Use a script for **post-processing** (image resize, master resolution) | Use a script for **page authorship** (geometry placement, glue formula generation) |

### 7.3 Generation cadence (recommended)

After the §3.0 batch read, Drafter runs three phases:

| Phase | Output | Purpose |
|---|---|---|
| 1. Visual Construction Phase | All `pages/<NN>_*.vsdx-page.xml` fragments, sequentially | Cross-page visual continuity; per-page lock re-read |
| 2. Quality Check Gate | `python3 scripts/vsdx_quality_checker.py <project_path>` | Lint every page; fix every error before phase 3 |
| 3. Logic Construction Phase | `comments/total.md` (page commentary), Stylist hand-off | Page-by-page commentary that survives into ShapeSheet `Comment` cells / `commentList.xml` |

**MUST NOT** start phase 3 until phase 2 reports zero errors. The checker
runs against the page-XML fragments **before** `finalize_vsdx.py` because
finalize rewrites cells (master resolution, image embedding) and can mask
violations.

### 7.4 Per-page output format declaration

For each page the Drafter authors, the turn opens with the role-switch
marker block, the per-page lock re-read note, and the template-mapping
declaration:

```
## [Role Switch: Drafter]
📖 Reading role definition: references/drafter.md
📋 Current task: Author Visio Page 04_validate_step

🔁 Re-reading: <project_path>/diagram_lock.md (P04 entry)
🔁 Re-reading: <project_path>/diagram_spec.md §IX P04

📝 **Page-layout mapping**: templates/page-layouts/general/03b_content_diagram_focus.vsdx-page.xml
📝 **Diagram-template mapping**: templates/diagram-templates/bpmn_basic.vsdx-page.xml
🎯 **Adherence rules / layout strategy**: dense rhythm, BPMN sequence flow,
   3 activities + 1 gateway + 1 end event; horizontal swim across the page,
   gateway diverges to two branches that reconverge to the end event.
```

The marker block is the **only** way to confirm Drafter has performed the
mandatory per-page re-read; the orchestrator rejects pages that do not
emit the marker.

### 7.5 Resuming after context compression

If the agent's context was auto-compacted between pages:

1. Re-read `_BLUEPRINT.md` §7 (discipline rules).
2. Re-read `references/drafter.md` (this file) — sections 2 and 7 minimum.
3. Re-read `diagram_lock.md` and `diagram_spec.md`.
4. Re-read every distinct `page_layouts` / `page_diagrams` template that
   has not been recently consulted.
5. Continue from the next un-authored page; do NOT regenerate pages already
   on disk under `pages/`.

The `workflows/resume-execute.md` workflow describes this protocol formally.

---

## 8. Validation Gate

> After all pages are written and **before** Stylist phase 6.5 starts,
> Drafter runs `vsdx_quality_checker.py`. Any `error` MUST be fixed before
> Stylist runs. The checker is the analogue of `ppt-master`'s
> `svg_quality_checker.py` and shares its exit-code conventions.

### 8.1 Invocation

```bash
python3 scripts/vsdx_quality_checker.py <project_path>
```

Exit codes:

| Exit code | Meaning | Drafter action |
|---|---|---|
| `0` | Clean — zero errors, zero warnings | Proceed to Stylist (phase 6.5) |
| `1` | Warnings only | Fix when straightforward; otherwise note in commentary and proceed |
| `2` | Errors present | Fix every error; re-run checker; iterate until exit code drops to 0 or 1 |

### 8.2 Checks the validator runs (per `_BLUEPRINT.md` §7.3)

| Check class | Specifics |
|---|---|
| **Banned ShapeSheet patterns** | `INTERSECTX` / `INTERSECTY` formulae (rare and brittle), `PROJECT` / `LOOKUP` against external data (Stylist's job, not Drafter's), arbitrary `EVAL` expressions in geometry cells |
| **Coordinate sanity** | Every shape's bounding box (PinX±Width/2, PinY±Height/2) fits inside the declared page bounding box (`PageWidth` × `PageHeight`); shapes whose extent exceeds the page bounds are flagged |
| **Glue completeness** | Every `<Shape>` whose 1-D Endpoints section is present has both `BeginX`/`BeginY` and `EndX`/`EndY` populated; the glue formula references a valid Connection point or `PinX` on the target shape |
| **Theme consistency** | Every fill / line color either references the declared theme via `THEMEGUARD()` or is a HEX from `diagram_lock.colors` |
| **Stencil consistency** | Every `<Shape Master="@<NameU>"/>` placeholder resolves to a master in the locked stencil set; values not in `stencils.inventory` are errors |
| **Layer assignment** | Every shape declares a `LayerMember` cell whose comma-separated layer ids exist in the page's `<Section N="Layer">` rows |
| **Forbidden text patterns** | HTML named entities (`&nbsp;`, `&mdash;`), bare `<`, `>`, `&` in text content, `<style>` / `<script>` in any embedded SVG image |
| **Per-page rhythm coherence** | Pages tagged `breathing` in `diagram_lock.page_rhythm` MUST NOT have more than two parallel containers; pages tagged `anchor` MUST inherit a `page_layouts` template; pages tagged `dense` are unconstrained |
| **Banned-section check** | No page emits `<Section N="DataGraphic">` (Stylist's job) or `<Section N="UserDef" Name="msvCallout*">` populated entries (Stylist's job) |
| **Coordinate unit drift** | All numeric `V=` literals on length cells consistently use the page's `canvas.units` (no inch literals on a millimetre page) |
| **Universal-name discipline** | All `Char.Font` / `Char.Color` / `Para.HorzAlign` and similar cells use universal cell names (English), not localised names |

### 8.3 Per-page verification checklist (manual, before running the checker)

A short pre-check Drafter runs mentally per page:

| Check | Pass criterion |
|---|---|
| `<PageSheet>` present | Exactly one, with `PageWidth`, `PageHeight`, `DrawingScale` cells |
| `<Shapes>` present | Exactly one, containing every top-level shape |
| Every shape has the seven Shape Transform cells | `PinX`, `PinY`, `Width`, `Height`, `LocPinX`, `LocPinY`, `Angle` |
| Every connector has the eight 1-D cells | §6.1 |
| Every connector has its two `<Connect>` rows in `<Connects>` | §6.5 |
| Every shape's `Master="@..."` placeholder is in `stencils.inventory` | §4.5 |
| Every shape's text colors / fills / strokes come from `diagram_lock.colors` | §2.2 |
| Every text font matches `diagram_lock.typography.font_family` (or role override) | §2.2 |
| `page_rhythm` discipline obeyed | `breathing` pages have ≤ 2 parallel containers; `anchor` pages inherit verbatim |
| Page bounding box ≥ shape extents | No shape spills off the page |

### 8.4 Failure remediation

If `vsdx_quality_checker.py` flags a page:

1. Read the offending page's XML and the checker's report.
2. Re-read the relevant `diagram_lock.md` section (`colors` / `stencils` /
   `page_rhythm`).
3. Patch the page-XML in place — do NOT regenerate from scratch unless the
   page violates rhythm discipline structurally.
4. Re-run the checker to confirm the fix.
5. Do NOT advance to Stylist until the checker exits 0 or 1.

If the failure is a **lock drift** (e.g. Drafter used a HEX that was once
in the lock but Architect has since updated it), run
`scripts/update_diagram_lock.py` from Architect's role to propagate the
new value to every existing page atomically — do NOT hand-edit individual
pages.

---

## 9. Banned Techniques

> Banned not because they don't work, but because they break the contract
> Architect set in `diagram_lock.md`, or because they create surface that
> Stylist cannot rewire, or because they bypass the validation gate.

### 9.1 Banned at the workflow level

| Banned | Why | Use instead |
|---|---|---|
| Authoring two pages in one Drafter turn | Bundles cross-page state into one context window; defeats per-page lock re-read | One page per turn, sequentially |
| Delegating page authorship to a sub-agent | Severs the cross-page memory that drives visual consistency | Author all pages in the main agent |
| Writing a Python loop that emits multiple `<Shape>` elements | Removes per-shape attention; produces "AI-generated" lookalike grids | Hand-write each shape in the page-XML |
| Running `finalize_vsdx.py` mid-Drafter | Finalize rewrites masters and resolves images; running it before all pages exist hides drafting errors | Run only in Step 7, after the validation gate passes |
| Editing a page's XML after Stylist has touched it | Drafter writes geometry; Stylist writes theme; back-and-forth produces inconsistent files | If geometry must change post-Stylist, restart from Drafter on that page |
| Hand-editing `diagram_lock.md` to "fix" a per-page need | The lock is Architect's contract; drift is detected by the quality checker | Surface a `warning:` line and request Architect run `update_diagram_lock.py` |
| Importing a page-layout template from outside `templates/page-layouts/` | Bypasses the audit-stencil-licensing workflow; risks shipping unlicensed content | Use only locked templates; new templates go through `create-page-layout.md` |

### 9.2 Banned at the ShapeSheet level

| Banned cell pattern | Why |
|---|---|
| `<Cell N="FillForegnd" V="#XXXXXX"/>` with HEX not in `diagram_lock.colors` | Theme drift; the value is invisible to Stylist's `apply_theme.py` |
| `<Cell N="FillForegnd" F="THEME(...)"/>` written by Drafter | Theme application is Stylist's job; Drafter writes inline color from the lock, Stylist replaces with `THEMEGUARD()` |
| `<Cell N="Char.Font" V="<arbitrary>"/>` with a font index not declared in the lock | Visio renders unknown fonts as Calibri; deck consistency breaks |
| `<Cell N="LayerMember" V="<index>"/>` referencing a layer ID not yet declared on PageSheet | Layer creation is Stylist's job; Drafter writes `LayerMember` only if Architect declared the layer in the lock |
| `<Cell N="..." F="EVAL(...)"/>` for free-form expression evaluation | `EVAL` is a runtime escape hatch that the validator cannot statically check |
| `<Cell N="..." F="INTERSECTX(...)"/>` or `INTERSECTY(...)` | Brittle; results depend on geometry recalc order and break on resize |
| `<Cell N="..." F="PROJECT(...)"/>` or `LOOKUP(...)` against external data | Data binding is Stylist's job (post-Drafter); Drafter ignores `data_links` |
| `<Cell N="...DataGraphic..."/>` populated entries | Data Graphics are Stylist's surface |
| `<Cell N="ResizePage" V="1"/>` on the page sheet | Lets the page auto-grow at layout time; Drafter wants fixed pages so coordinate sanity holds |
| `<Cell N="..." Result="..."/>` attribute | The `Result` attribute is for Visio's own ResultIU caching; emitting it from a fragment causes formula-result drift |

### 9.3 Banned at the connector level

| Banned | Why | Use instead |
|---|---|---|
| Floating connector with no `<Connect>` row but with glue formula | At next save Visio rewrites the formula and the connector becomes literal-coordinate; the intended glue is lost | Always pair formula with a `<Connect>` row |
| `<Connect ... FromPart="-1"/>` (`visConnectFromError`) | Runtime error sentinel; never emit |
| `<Connect ... FromPart="<other>"/>` outside `{9, 12, 100..199}` | Outside the documented enumeration; the validator rejects |
| Mixing `visLORouteCenterToCenter` (16) on the page with right-angle connectors | Page-level center-to-center collapses every right-angle connector; produces spaghetti | Set per-connector overrides; leave page-level to the lock-declared route |
| Emitting `<Cell N="ShapeRouteStyle" V="0"/>` and expecting per-connector behaviour | `0` means inherit page; nothing changes | Use a non-zero `VisCellVals` constant |
| `<Cell N="LineJumpFactorX" V="0"/>` | Visio still draws the jump glyph at zero size — looks like a rendering bug | Use `0.05` for near-invisible micro-jumps |
| Hand-fabricating `BeginX = PNT(Sheet.5!Connections.X3, Sheet.5!Connections.Y3)` without confirming the master has 3+ connection-point rows | Visio creates a default centred connection and silently mis-glues | Confirm via the stencil README |

### 9.4 Banned at the geometry level

| Banned | Why |
|---|---|
| Drawing a shape via `<Section N="Geometry">` rows when a master in `stencils.inventory` already encodes the same shape | Reinventing the master breaks future swaps, theme inheritance, and category-based validation |
| Mixing `MoveTo` / `LineTo` row tags (`visTagMoveTo=1`, `visTagLineTo=2`) with `Rel*` variants in the same section | Half-relative geometry produces shapes that scale weirdly when the user resizes |
| Writing `<Cell N="Geometry1.NoShow" V="1"/>` on the only Geometry section | Hides the shape; if you want a hidden shape use `Misc.NonPrinting` instead |
| Emitting per-shape `<DocumentSheet>` cells | The DocumentSheet is per-document, not per-shape; placing it inside `<Shape>` produces invalid XML |

### 9.5 Banned text patterns

| Pattern | Why | Use instead |
|---|---|---|
| HTML entities (`&nbsp;`, `&mdash;`, `&rdquo;`) | XML treats `&nbsp;` as undefined; Visio renders literal text | Unicode characters: ` `, `—`, `”` |
| Bare `<`, `>`, `&` in `<Text>` content | Breaks XML well-formedness | `&lt;`, `&gt;`, `&amp;` |
| `<style>` or `<script>` blocks inside any embedded SVG | Visio's SVG parser ignores them but the validator rejects | Plain SVG without script |
| Multi-line text relying on `<br/>` | Visio's text engine ignores `<br/>`; line breaks come from `<cp>` paragraph runs | Use `<Section N="Paragraph">` rows for paragraph breaks |
| Mixing locales in a single `<Char>` row (e.g. `Char.Font="Microsoft YaHei"` + `Char.LangID="en-US"`) | Renders as fallback Calibri; deck visually inconsistent | One language per shape; Architect locks `diagram_lock.text.language` |

### 9.6 Banned at the inheritance level

| Banned | Why |
|---|---|
| Writing `<Shape Type="Group">` without a Group Properties section | Group shapes need `SelectMode`, `DisplayMode`, `IsDropTarget` cells; missing them gives unpredictable interactive behaviour |
| Calling `ConvertToGroup` semantics (i.e. baking master inheritance into local cells) at draft time | Breaks future master swaps and theme inheritance |
| Master-shadowing — emitting a master `Master="@Process"` then overriding every cell the master defines | Defeats the purpose of using a master; produces verbose XML; Stylist's `embed_masters.py` may strip overrides |
| Adding a User-defined cell `User.msvStructureType` to a non-container shape | Confuses Visio's structured-diagram engine; the shape may be treated as a container with unpredictable members |

---

## 10. Hand-off to Stylist

> Drafter completes Step 6 with all `pages/<NN>_*.vsdx-page.xml` fragments
> on disk and the validation gate passing. Stylist's responsibilities
> begin at Step 6.5.

### 10.1 What Drafter delivers

| Artifact | Path |
|---|---|
| Per-page Visio Page fragments | `<project>/pages/<NN>_<page_name>.vsdx-page.xml` |
| Optional ShapeSheet authoring notes | `<project>/pages/<NN>_<page_name>.shapesheet-notes.md` |
| Page-by-page commentary | `<project>/comments/total.md` (split later by `total_md_split.py`) |
| Quality-checker report | exit 0 from `vsdx_quality_checker.py` |

### 10.2 What Drafter does NOT touch

| Concern | Stylist owns |
|---|---|
| `<Document>/<Theme>` block | `apply_theme.py` populates with `theme.xml` from the locked theme bundle |
| `THEMEGUARD()` rewriting on shape fills | `apply_theme.py` walks every shape and replaces inline HEX with theme references for shapes whose role qualifies |
| `<Section N="DataGraphic">` rows | Stylist's data-graphics layer |
| `<Section N="Layer">` rows on the PageSheet | Stylist creates layer rows; Drafter only writes shape `LayerMember` |
| Container member resolution | `assemble_containers.py` |
| Master inheritance index resolution | `embed_masters.py` rewrites `Master="@Process"` placeholders |
| Image relationship-ID resolution | `embed_images.py` rewrites `r:id="@<filename>"` placeholders |
| Final OPC zip composition | `vsdx_export.py` |

### 10.3 Stylist→Drafter feedback loop

If Stylist's theme application surfaces an inconsistency that requires
geometric change (e.g. a shape's bounding box can't accommodate the
theme's font size), Stylist surfaces a `warning:` line and the workflow
returns to Drafter for that page only. Drafter re-reads the lock,
patches the offending page-XML, re-runs the quality checker, hands back
to Stylist. Pages that Drafter has not touched in this round stay as
they were.

This loop is rare. The lock-driven discipline is designed to prevent
it: if `typography.body` is locked at 12pt and shapes are sized to
accommodate 12pt, theme application doesn't shift sizes.

---

## 11. Failure Modes and Diagnostics

### 11.1 Common authoring errors

| Symptom | Likely cause | Fix |
|---|---|---|
| Visio opens the file but a shape is missing geometry | Master placeholder `@<NameU>` was not in `stencils.inventory`; `embed_masters.py` left it unresolved | Cross-check inventory; add the master to lock and re-run |
| Connector renders as a literal line, not a glued connector | Glue formula present but `<Connect>` row missing; or formula references a shape not on the page | Add the `<Connect>` row; verify `Sheet.<id>` is on the same page |
| Connector arrow points the wrong direction | `EndArrow` set on the wrong end (e.g. on the begin endpoint) | Move arrow to the end that points to the target |
| Shape appears off-canvas | Coordinate exceeds `PageWidth` / `PageHeight`; or unit drift (mm value on inch page) | Verify `canvas.units`; quantise to grid |
| Text shows as Calibri instead of locked font | Font index unresolved in `<DocumentSettings>/<FontList>` | Re-run `apply_theme.py`; if persistent, confirm font is installed on the export machine |
| Theme application erases inline color | Drafter wrote a HEX that wasn't in `diagram_lock.colors`; `apply_theme.py` flagged and reset to default | Use only locked HEX |
| Container does not enclose its members | Member shapes' bounding boxes don't overlap container; `assemble_containers.py` couldn't infer membership | Move members fully inside the container's `Width`/`Height` |
| List members appear in the wrong order | `msvSDListDirection` mismatch with the physical placement | Set `msvSDListDirection` to `0` (top-to-bottom) and stack members by `PinY`; or `1` (left-to-right) and stack by `PinX` |
| Page opens but Visio "repairs" the file with a warning | Almost always cell ordering inside `<Shape>`: `<Text>` precedes `<Cell>`, or `<Section>` precedes `<Cell>` | Re-order to `<Cell>* <Section>* <Text>?` |

### 11.2 Logging Drafter intent

Per page, Drafter writes a sibling `.shapesheet-notes.md` file
documenting:

- Which lock fields drove which cells (e.g. `colors.primary → FillForegnd on shapes 1-4`).
- Why a particular master was chosen over alternatives.
- Page-rhythm discipline applied (`anchor` → verbatim inheritance, `breathing` → single-callout layout).
- Any `warning:` lines surfaced during authoring.

The notes file is not strictly required — it's a debugging aid.
`finalize_vsdx.py` copies its contents into ShapeSheet `Comment` cells
on the page sheet (universal cell name `Comment`) so they survive into
the final `.vsdx`.

### 11.3 When to escalate to Architect

Drafter MUST stop and escalate (rather than improvising) when:

- The lock does not contain a needed value (color, font, master, image).
- A `§IX` block's content texture cannot be rendered in the locked
  stencil set (e.g. brief asks for a BPMN gateway but stencil set is
  `flowchart-basic`).
- A page-layout template is named in `page_layouts` but the file is
  missing from `templates/page-layouts/`.
- Two locked rules conflict (e.g. `page_rhythm: anchor` + `page_diagrams:
  bpmn_basic` — `anchor` pages don't get diagrams; one of the two has
  to give).

Escalation surfaces a `warning:` line in the agent output and **does
not** silently proceed with an invented fallback.

---

## 12. Quick Reference Card

> Pin this to the top of the Drafter context for fast lookup.

### 12.1 Per-page checklist

| Step | Action |
|---|---|
| 1 | Re-read `<project>/diagram_lock.md` |
| 2 | Re-read `<project>/diagram_spec.md` §IX P<NN> |
| 3 | Look up `page_rhythm.P<NN>`, `page_layouts.P<NN>`, `page_diagrams.P<NN>` |
| 4 | Output role-switch marker + template-mapping declaration |
| 5 | Author `<PageSheet>` with `PageWidth`, `PageHeight`, `ResizePage=0`, `DynamicConnectorRouteStyle`, `LineJumpStyle`, `AvenueSizeX/Y`, `BlockSizeX/Y` |
| 6 | Author `<Shapes>` with each shape's seven Shape Transform cells |
| 7 | Author connectors with eight 1-D Endpoint cells (§4.3) |
| 8 | Author `<Connects>` with paired `<Connect>` rows (§5.2, §6.1) |
| 9 | Verify glue completeness (§6) |
| 10 | Save to `pages/<NN>_<page_name>.vsdx-page.xml` |
| 11 | After all pages, run `vsdx_quality_checker.py`; iterate to exit 0 |

### 12.2 Cell name → universal value type

| Cell | Type | Source |
|---|---|---|
| `PinX`, `PinY`, `Width`, `Height` | Length | Lock `canvas.units` |
| `LocPinX`, `LocPinY` | Length / formula | Default `Width*0.5`, `Height*0.5` |
| `Angle` | Angle | `0 deg` for axis-aligned |
| `BeginX`, `BeginY`, `EndX`, `EndY` | Length / formula | Connector endpoints |
| `FillForegnd`, `LineColor`, `Char.Color` | Color | Lock `colors.*` HEX |
| `Char.Font` | Font index | Resolved by `apply_theme.py` |
| `Char.Size` | Length (inches) | `<pt>/72` from lock typography |
| `LayerMember` | Index list | Lock `layers.*` IDs |
| `DynamicConnectorRouteStyle` | Constant | `VisCellVals` |
| `LineJumpStyle`, `LineJumpCode` | Constant | `VisCellVals` |
| `PlaceStyle`, `RouteStyle` | Constant | `visPLOPlace*`, `visLORoute*` |

### 12.3 Constants cheat sheet

```
# FromPart (connector endpoint)
visBegin                  = 9
visEnd                    = 12
visConnectFromError       = -1   # NEVER emit

# ToPart (target type)
visGuideX                 = 1
visGuideIntersect         = 2
visWholeShape             = 3    # dynamic glue
visGuideY                 = 4
visToAngle                = 7
visConnectionPoint        = 100  # + row offset

# AutoConnect direction
visAutoConnectDirNone     = 0
visAutoConnectDirRight    = 1
visAutoConnectDirLeft     = 2
visAutoConnectDirUp       = 3
visAutoConnectDirDown     = 4

# RouteStyle / DynamicConnectorRouteStyle (VisCellVals)
visLORouteDefault         = 0
visLORouteRightAngle      = 1
visLORouteStraight        = 2
visLORouteOrgChartNS      = 4
visLORouteOrgChartEW      = 5
visLORouteFlowchartNS     = 8
visLORouteFlowchartEW     = 9
visLORouteTreeNS          = 10
visLORouteTreeEW          = 11
visLORouteNetwork         = 12
visLORouteCenterToCenter  = 16
visLORouteNone            = 31

# PlaceStyle (visPLOPlace*)
visPLOPlaceDefault                    = 0
visPLOPlaceTopToBottom                = 1
visPLOPlaceLeftToRight                = 2
visPLOPlaceBottomToTop                = 3
visPLOPlaceRightToLeft                = 4
visPLOPlaceCircular                   = 5
visPLOPlaceRadial                     = 6
visPLOPlaceHierarchyTopToBottomCenter = 17

# LineJumpStyle
visLOJumpNone   = 0
visLOJumpArc    = 1
visLOJumpGap    = 2
visLOJumpSquare = 3
visLOJumpSides2 = 4

# Arrowheads (VisArrowValues)
visArrowNone           = 0
visArrowOpen           = 1
visArrowHollow         = 2
visArrowLine           = 3
visArrowFilled         = 4
```

### 12.4 ShapeSheet section indices

```
visSectionObject          = 1     # Shape Transform, Line, Fill, Text Block, Misc
visSectionFirstComponent  = 10    # Geometry1, Geometry2, ...
visSectionConnectionPts   = 7     # Connection points
visSectionControls        = 10    # Control handles (note: shares 10 with FirstComponent)
visSectionScratch         = 6     # Scratch.A1..F8
visSectionAction          = 240   # Right-click menu
visSectionUser            = 242   # User-defined cells
visSectionProp            = 243   # Shape Data (custom properties)
visSectionLayer           = 244   # Layer rows (page sheet)
visSectionHyperlink       = 245   # Multiple hyperlinks
```

### 12.5 Pre-flight before declaring a page done

```
✓ <PageSheet> with PageWidth, PageHeight, ResizePage=0, layout cells
✓ Every shape has 7 Shape Transform cells
✓ Every connector has 8 1-D cells
✓ Every connector has 2 <Connect> rows in <Connects>
✓ Every Master="@<NameU>" is in stencils.inventory
✓ Every HEX is from diagram_lock.colors
✓ Every font role uses the locked typography family
✓ page_rhythm discipline applied
✓ No banned ShapeSheet patterns (§9.2)
✓ No banned text patterns (§9.5)
✓ Saved to pages/<NN>_<page_name>.vsdx-page.xml
```

---

## Sources

- `_BLUEPRINT.md` — visio-master architectural blueprint, §1-§7 for the
  pipeline mental model, role roster, eight confirmations, and the
  discipline rules carried over from ppt-master Executor.
- `research/01-com-object-model.md` — Visio COM Application / Document /
  Page / Shape / Cells / Connects object model; the API surface that
  underpins Drafter's XML emission semantics.
- `research/02-shapesheet-cells-functions.md` — full ShapeSheet cell
  taxonomy including Shape Transform, 1-D Endpoints, Geometry, Connection
  Points, Controls, User-defined, Scratch, Actions, Glue Info,
  Protection, Misc; the formula language (`PNT`, `PAR`, `THEMEGUARD`,
  `GUARD`, `SETF`, `BOUND`).
- `research/04-shapes-masters-stencils.md` — 1-D vs 2-D shape
  dimensionality, master inheritance, Document Stencil, the `Drop*`
  family (`Drop`, `DropMany`, `DropConnected`, `DropContainer`,
  `DropIntoList`, `DropCallout`, `DropLegend`, `DropLinked`); the
  `SetFormulas` / `SetResults` batch APIs.
- `research/06-python-com-automation.md` — pywin32 Dispatch /
  DispatchEx / `gencache.EnsureDispatch`; threading rules
  (`pythoncom.CoInitialize`); the COM path that `vsdx_export.py` may
  use during finalize.
- `research/07-python-vsdx-library.md` — `vsdx` Python library; pure-
  Python `.vsdx` authoring without COM; the fallback writer used in
  CI environments.
- `research/18-connectors-routing.md` — connector master inventory,
  static vs dynamic glue, `Cell.GlueTo` / `GlueToPos`, the `Connect`
  collection, `FromPart` / `ToPart` enumerations, `ConRouteStyle` /
  `DynamicConnectorRouteStyle`, line jumps, AutoConnect, line-jump
  cells; the page-XML schema for `<Connect>` elements.
- `research/19-auto-layout.md` — `Page.Layout` /
  `Page.LayoutIncremental`, the Page Layout ShapeSheet section
  (`PlaceStyle`, `RouteStyle`, `AvenueSizeX/Y`, `BlockSizeX/Y`,
  `LineJumpStyle`, `ResizePage`); the `visPLOPlace*` and `visLORoute*`
  enumerations.
- `research/22-containers-layers-pages.md` — Containers, Lists,
  Callouts; `ContainerProperties`; `Page.DropContainer` /
  `DropList` / `DropCallout`; the User-defined cells
  (`User.msvStructureType`, `msvSDContainer*`, `msvSDList*`,
  `msvCalloutTargetShape`); Layers and `LayerMember`;
  background pages.
- `research/25-validation-process.md` — Diagram Validation framework,
  `Document.Validation`, `ValidationRuleSet`, `ValidationRule`
  (`FilterExpression`, `TestExpression`, `Description`, `Category`);
  the model `vsdx_quality_checker.py` extends with static lint rules.
- `research/26-custom-shape-development.md` — SmartShape authoring,
  Group editing semantics, `Connections` / `Protection` / `Geometry` /
  `User` / `Actions` / `Events` / `SmartTags` sections; `EventDblClick`,
  `Master.PatternFlags`, `Master.Prompt`; the conventions a Drafter
  must respect when reusing masters from `templates/stencils/`.

