# Template Resources

The `templates/` directory groups every bundled asset Architect, Drafter,
and Stylist consume during a visio-master build. Four sub-libraries plus
two specification skeletons live here. They are governed by the same
**JSON-as-truth, README-as-prose** discipline ppt-master uses:
machine-readable index files (`*_index.json`) drive discovery; READMEs
explain the conventions, selection rules, and authoring discipline.

The libraries:

| Sub-library            | Purpose                                                 | Index file                                       |
|------------------------|---------------------------------------------------------|--------------------------------------------------|
| `page-layouts/`        | Pre-built page-roster templates (cover / section / …)   | `page-layouts/page-layouts_index.json`           |
| `themes/`              | Visio Theme XML bundles (`<Theme>` + colour variants)   | `themes/themes_index.json`                       |
| `diagram-templates/`   | Per-diagram-type Visio Page seeds (`*.vsdx-page.xml`)   | `diagram-templates/diagrams_index.json`          |
| `stencils/`            | Master shape catalog exploded from `.vssx`              | (per-set `README.md` entries)                    |

The skeletons:

| Skeleton                          | Architect emits                       | Mirror in ppt-master                |
|-----------------------------------|---------------------------------------|-------------------------------------|
| `diagram_spec_reference.md`       | `<project>/diagram_spec.md`           | `design_spec_reference.md`          |
| `diagram_lock_reference.md`       | `<project>/diagram_lock.md`           | `spec_lock_reference.md`            |

---

## Diagram Specification & Lock References

Two skeleton documents pin the contract between Architect and the rest
of the pipeline.

1. **`diagram_spec_reference.md`** — 11-section narrative reference
   covering Project Information, Visual Specifications, Mode & Visual
   Style, Color Scheme, Typography, Stencil Inventory, Image Resource
   List, Layout & Connectors, Page Rhythm, Page Layouts, Page Diagrams,
   Page Data Links, and Forbidden patterns. Architect copies the
   structure into `<project>/diagram_spec.md` and fills it after the
   Eight Confirmations bundle is accepted by the user. Free-form prose
   is welcome — this file is the human-readable narrative.
2. **`diagram_lock_reference.md`** — parseable execution contract
   Drafter re-reads before every Visio Page (rule 8 of the Global
   Execution Discipline; see `_BLUEPRINT.md` §7.1). Only `## section`
   headings and `- key: value` data lines are emitted at runtime; the
   skeleton's blockquote guidance is author-time only and must not
   appear in the runtime lock. Sections are vocabulary-closed
   (`canvas`, `mode`, `visual_style`, `colors`, `typography`,
   `stencils`, `images`, `page_rhythm`, `page_layouts`,
   `page_diagrams`, `page_data_links`, `forbidden`).

[View Diagram Spec Reference](./diagram_spec_reference.md) ·
[View Diagram Lock Reference](./diagram_lock_reference.md)

The Eight Confirmations populate both files in lock-step:

| #  | Confirmation                  | Spec section                    | Lock fields                                                                       |
|----|-------------------------------|---------------------------------|-----------------------------------------------------------------------------------|
| 1  | Page format / units           | §II Visual Specifications       | `canvas.format` / `canvas.units` / `canvas.width` / `canvas.height` / `canvas.dpi`|
| 2  | Diagram type / page count     | §I Project Information          | `page_count` / `primary_diagram_type` / `page_diagrams.P<NN>`                     |
| 3  | Audience                      | §I Project Information          | (narrative only — drives §4 mode + §5 theme variant)                              |
| 4  | Style objective (mode + style)| §III Mode & Visual Style        | `mode` / `visual_style` (+ optional `*_behavior` paragraphs)                      |
| 5  | Theme / color                 | §IV Color Scheme                | `theme` / `colors.primary` / `colors.accent` / `colors.text` / …                  |
| 6  | Stencil set                   | §V Stencil Inventory            | `stencils.set` / `stencils.brand_set` / `stencils.inventory` / `stencils.connector_style` |
| 7  | Layout & connector routing    | §VI Layout & Connectors         | `layout.algorithm` / `layout.spacing` / `connectors.*` / `page_rhythm.P<NN>`      |
| 8  | Data linking                  | §VII Data Linking               | `data_links.enabled` / `data_links.sources[]` / `data_links.bindings[]` / `data_graphics[]` |

Updates to a lock after pages exist must flow through
`scripts/update_diagram_lock.py` — hand-editing leaves emitted
Visio Pages and lock out of sync. See `references/architect.md` for the
Eight-Confirmations script and `references/drafter-base.md` for the
per-page re-read protocol.

---

## Page Layout Templates

The `page-layouts/` directory contains pre-built page-roster templates
organised by design style. A page-layout is structurally a small set of
`*.vsdx-page.xml` page fragments wrapped with a `diagram_spec.md`
narrative; Drafter copies a roster, instantiates each fragment as a
Visio Page, and edits text in place.

| Roster id        | Posture                                                          | Page count |
|------------------|------------------------------------------------------------------|-----------:|
| `general`        | Versatile modern style, clean and flexible                       | 5          |
| `engineering`    | Engineering-blueprint roster — cyan/navy line work, hairline grids, monospace labels | 3 |
| `executive`      | Executive-clean roster — soft fills, generous whitespace, sans-serif labels | 3   |

Each roster ships:

```
templates/page-layouts/<id>/
├── diagram_spec.md
└── 0N_<page_role>.vsdx-page.xml
```

The `<page_role>` slug is one of `cover`, `section`, `content_left_text`,
`content_diagram_focus`, `summary`, `block_diagram`, `sequence`,
`executive_summary`, `one_page_strategy`. Drafter resolves
`diagram_lock.page_layouts.P<NN>` to a `<page_role>` basename and reads
that fragment once during the Step 6 batch read.

- **Human browsing**: [page-layouts/README.md](./page-layouts/README.md)
- **Slim lookup (discovery only)**:
  [page-layouts/page-layouts_index.json](./page-layouts/page-layouts_index.json)
  — answers "what page-layouts exist?". The Strategist Step 3 trigger
  is an explicit directory path supplied by the user; bare names from
  this index never trigger by themselves.
- **Authoring workflow**:
  [`../workflows/create-page-layout.md`](../workflows/create-page-layout.md)

---

## Theme Bundles

The `themes/` directory holds Visio Theme XML payloads — the `<Theme>`
block shipped inside a finished `.vsdx`'s `document.xml`, plus the
colour, font, and effect variant subfiles applied by
`Document.SetTheme(<base>)` and `Document.SetThemeVariant(1..4)`.
Themes are aesthetic-only: they never carry page geometry, shape
inventory, or connector routing.

`Document.SetTheme(<base>)` accepts one of: `Office`, `Slate`, `Whisp`,
`Linear`, `Integral`, `Daybreak`, `Parallel`, `Sequence`. Each base
exposes four colour variants (1..4) selected via
`Document.SetThemeVariant(<idx>)`. visio-master ships custom bundles
that pin a base + variant + (optional) overlay so a drawing can recall
the exact aesthetic across edits.

| Bundle id          | Base theme | Default variant | Posture                                                                |
|--------------------|------------|-----------------|------------------------------------------------------------------------|
| `visio-stock`      | `Office`   | `1` (blue)      | Re-creation of Visio's default — the safe fallback for any diagram type|
| `dark-tech`        | `Slate`    | `2`             | Dark canvas, luminous accents, glow effects on shapes and connectors   |
| `swiss-minimal`    | `Linear`   | `1`             | Hairline grids, monochrome with one accent, no shadows                 |

Each bundle directory carries:

```
templates/themes/<id>/
├── diagram_spec.md          # narrative description of the theme's intent
├── theme.xml                # Visio <Theme> + variant blocks
├── colors/                  # optional colour-only overlays
├── fonts/                   # optional font-scheme overlays
└── effects/                 # optional effect-scheme overlays
```

Sample colour anchors from the shipped bundles (truth lives in each
bundle's `theme.xml` — these illustrate the published palette):

| Bundle           | primary   | accent    | secondary_accent | text      | bg        | grid      | border    |
|------------------|-----------|-----------|------------------|-----------|-----------|-----------|-----------|
| `visio-stock`    | `#1F4E79` | `#2E75B6` | `#5B9BD5`        | `#1F1F1F` | `#FFFFFF` | `#D9D9D9` | `#A6A6A6` |
| `dark-tech`      | `#00BCF2` | `#7FBA00` | `#F25022`        | `#FFFFFF` | `#1B1B1B` | `#3A3A3A` | `#5A5A5A` |
| `swiss-minimal`  | `#000000` | `#E81123` | `#737373`        | `#1F1F1F` | `#FFFFFF` | `#BFBFBF` | `#000000` |

Per-family default theme + variant guidance from
`references/diagram-types.md` §13:

| Diagram family   | Recommended base | Variant     | Rationale                                              |
|------------------|------------------|-------------|--------------------------------------------------------|
| flowchart        | `Office`         | `1` blue    | Flowchart shapes default to blue fills                 |
| brainstorming    | `Office`         | `3` green   | Matches Visio's brainstorming shipping palette         |
| network          | `Office`         | `2` grey    | Iconographic / vendor-neutral                          |
| cloud (Azure)    | `Office`         | `1`         | Matches Azure Public Symbol Set hue                    |
| cloud (AWS)      | `Office`         | `4` orange  | Matches AWS service-icon orange                        |
| engineering      | `Office`         | `1`         | Engineering reference variants ship neutral palette    |
| floor plan       | `Office`         | `1`         | Architectural neutral                                  |
| schedule         | `Office`         | `1`         | Gantt / PERT default blue task bars                    |

- **Human browsing**: [themes/README.md](./themes/README.md)
- **Discovery index**: [themes/themes_index.json](./themes/themes_index.json)
- **Authoring workflow**: [`../workflows/create-theme.md`](../workflows/create-theme.md)

---

## Diagram Templates

The `diagram-templates/` directory contains Visio Page fragments seeded
for each supported diagram type. Drafter copies a template, swaps the
shape inventory for masters declared in
`diagram_lock.stencils.inventory`, and edits text + connector glue per
page. Each fragment is a self-contained `<Page>` element (PageSheet +
Shapes + Connects) ready to slot into the final `pages.xml`.

The starter set covers the highest-frequency diagram types from
`references/diagram-types.md` (the full 59-row catalog):

| File                                        | Diagram id                  | Built-in template seed | Default canvas                | RouteStyle                     |
|---------------------------------------------|-----------------------------|------------------------|-------------------------------|--------------------------------|
| `process_flow_basic.vsdx-page.xml`          | `basic-flowchart`           | `BASFLO_M.VSTX`        | A4 portrait / 1:1             | `4` `visLORouteFlowchartNS`    |
| `process_flow_detailed.vsdx-page.xml`       | `basic-flowchart`           | `BASFLO_M.VSTX`        | A3 landscape / 1:1            | `4`                            |
| `swim_lane_horizontal.vsdx-page.xml`        | `cross-functional-flowchart`| `CROSSFUNC_M.VSTX`     | A3 landscape / 1:1            | `4`                            |
| `swim_lane_vertical.vsdx-page.xml`          | `cross-functional-flowchart`| `CROSSFUNC_M.VSTX`     | A3 portrait / 1:1             | `4`                            |
| `bpmn_basic.vsdx-page.xml`                  | `bpmn-2-0`                  | `BPMN_M.VSTX`          | A3 landscape / 1:1            | `4`                            |
| `network_topology_star.vsdx-page.xml`       | `basic-network`             | `NETBAS_M.VSTX`        | A3 landscape / 1:1            | `3` `visLORouteNetwork`        |
| `network_topology_mesh.vsdx-page.xml`       | `basic-network`             | `NETBAS_M.VSTX`        | A3 landscape / 1:1            | `3`                            |
| `network_rack_diagram.vsdx-page.xml`        | `rack-diagram`              | `RACK_M.VSTX`          | A3 portrait / `1 in : 1 ft`   | `0` `visLORouteRightAngle`     |
| `erd_basic.vsdx-page.xml`                   | `erd`                       | `DBMOD_M.VSTX`         | A3 landscape / 1:1            | `0`                            |
| `uml_class_basic.vsdx-page.xml`             | `uml-class`                 | `UMLCLS_M.VSTX`        | A3 landscape / 1:1            | `0`                            |
| `state_machine.vsdx-page.xml`               | `uml-state-machine`         | `UMLSM_M.VSTX`         | A3 landscape / 1:1            | `0`                            |
| `org_chart_pyramidal.vsdx-page.xml`         | `org-chart`                 | `ORGCH_M.VSTX`         | A4 landscape / auto-fit       | `9` `visLORouteOrgNS`          |
| `org_chart_matrix.vsdx-page.xml`            | `org-chart`                 | `ORGCH_M.VSTX`         | A3 landscape / auto-fit       | `9`                            |
| `mind_map.vsdx-page.xml`                    | `mind-map`                  | `MINDMAP_M.VSTX`       | A3 landscape / 1:1            | `8` `visLORouteRadial`         |
| `venn_three.vsdx-page.xml`                  | (decoration; `MARKETC_M`)   | `MARKETC_M.VSTX`       | A4 landscape / 1:1            | `0`                            |
| `quadrant_2x2.vsdx-page.xml`                | `swot` / 2x2 matrix         | `SWOT_M.VSTX`          | A4 landscape / 1:1            | `0`                            |

Each fragment declares the canonical `Page.PageSheet` cells
(`PageWidth`, `PageHeight`, `DrawingScale`, `PageScale`, `RouteStyle`,
`PlaceStyle`, `LineJumpStyle`, `AvenueSizeX`, `AvenueSizeY`,
`PrintPageOrientation`, `DrawingUnits`) per the row above, plus an
empty `<Shapes/>` slot Drafter populates. The Built-in template seed
column is the locale-invariant `Documents.AddEx` short name used by
`scripts/vsdx_export/com_writer.py` when COM is available; the fallback
writer reads the inline cells directly.

The full diagram-type catalog (59 diagrams across 9 families:
flowchart, brainstorm, org chart, network/cloud, software, engineering,
floor plan, schedule, business) lives in
`references/diagram-types.md`. Expanding the starter set is normal
maintenance through the `create-page-layout` workflow, registered via
`scripts/register_template.py`.

- **Library index (single source of truth)**:
  [diagram-templates/diagrams_index.json](./diagram-templates/diagrams_index.json)
- **Reference catalog**: [`../references/diagram-types.md`](../references/diagram-types.md)
- **Layout-pattern reference**: [`../references/diagram-layout-patterns.md`](../references/diagram-layout-patterns.md)

---

## Stencil Catalog

The `stencils/` directory hosts visio-master's master shape libraries.
Each set is one Visio `.vssx` exploded to per-master XML fragments
(`<shape>.vssx-master.xml`) plus an SVG-export sibling for the live
preview server.

Foundation set shipped with the skill:

| Set                  | Base stencil (Visio shipping)         | Master count | Connector style      | Use                                                |
|----------------------|----------------------------------------|-------------:|----------------------|----------------------------------------------------|
| `flowchart-basic`    | `BASFLO_M.VSSX` + `CONNEC_M.VSSX`      | 5 starter    | `Dynamic connector`  | Process / Decision / Start-End / Data / Document   |

The starter `flowchart-basic` ships five canonical masters:

| Master file                                  | Visio `Master.NameU` | Geometry           | Default `LinePattern` | Default fill          |
|----------------------------------------------|----------------------|--------------------|-----------------------|-----------------------|
| `flowchart-basic/process.vssx-master.xml`    | `Process`            | rounded rectangle  | `1` (solid)           | theme `Accent 1`      |
| `flowchart-basic/decision.vssx-master.xml`   | `Decision`           | rhombus / diamond  | `1`                   | theme `Accent 2`      |
| `flowchart-basic/start_end.vssx-master.xml`  | `Terminator`         | stadium / pill     | `1`                   | theme `Accent 3`      |
| `flowchart-basic/data.vssx-master.xml`       | `Data`               | parallelogram      | `1`                   | theme `Background 2`  |
| `flowchart-basic/document.vssx-master.xml`   | `Document`           | document tail      | `1`                   | theme `Background 2`  |

Each master directory carries:

- `<shape>.vssx-master.xml` — the Visio Master ShapeSheet (Geometry,
  ConnectionPoints, User-defined cells, Prop rows, Action rows)
- `<shape>.svg` — browser-preview sibling rendered at 1× page units for
  the live preview server (`scripts/vsdx_preview/server.py`)

Additional stencil sets are slotted in through the
`audit-stencil-licensing` workflow before being registered. The
following set ids are reserved (placeholder directories shipped empty):

| Set id                     | Source family                                    | Confirmation 6 fit                       |
|----------------------------|--------------------------------------------------|------------------------------------------|
| `flowchart-advanced`       | `BASFLO_M.VSSX` + `CROSSFUNC_M.VSSX`             | dense flowcharts, swim-lane              |
| `bpmn-2.0`                 | `BPMN_M.VSSX` + `BPMN2_M.VSSX`                   | BPMN 2.0 strict                          |
| `network-rack`             | `RACK_M.VSSX` + `RACKACC_M.VSSX` + `CABLES_M.VSSX`| rack diagrams                            |
| `network-azure`            | `Azure_Public_Service_Icons_V<n>.vssx`           | Azure architecture                       |
| `network-aws`              | `AWS17_*.VSSX` (re:Invent 2024)                  | AWS architecture                         |
| `software-uml`             | `UMLCLS_M.VSSX` family                           | UML class / sequence / state etc.        |
| `org-personas`             | `ORGCH_M.VSSX` + `ORGCHM_M.VSSX`                 | org charts                               |
| `mindmap-organic`          | `MINDMAP_M.VSSX` / `BRSTRM_M.VSSX`               | mind maps, brainstorm                    |
| `engineering-isa`          | `PEINSM_M.VSSX` + `PEPIPS_M.VSSX` + `PEVALV_M.VSSX`| ISA-5.1 P&ID                             |
| `electrical-iec`           | `ELECFI_M.VSSX` family                           | IEEE 315 schematics                      |

**Hard rule**: never copy enterprise stencils into this directory by
bare `cp`. Corporate stencil sets (Cisco Network Topology Icons, Lucid,
ConceptDraw, vendor packs) often carry licensing constraints. The
`audit-stencil-licensing` workflow is the only path for adding a new
set; bare imports are blocked at registration time.

**Hard rule** (visio-master discipline 16, see `_BLUEPRINT.md` §7.2):
one primary stencil set per drawing. Mixing `flowchart-basic` and
`bpmn-2.0` produces visual incoherence and breaks user expectation of
stencil semantics. Brand stencils (product / company logos) are the
only exception and are opt-in via `stencils.brand_set` in the lock.

- **Per-set guide**: [stencils/README.md](./stencils/README.md)
- **Audit & registration workflow**: [`../workflows/audit-stencil-licensing.md`](../workflows/audit-stencil-licensing.md)
- **ShapeSheet authoring rules**: [`../references/shared-standards.md`](../references/shared-standards.md)

---

## Cross-References

- [`../references/canvas-formats.md`](../references/canvas-formats.md)
  — canvas catalog Architect picks from at Confirmation 1; resolves
  `canvas.format` to `PageWidth` / `PageHeight` / `DrawingUnits` /
  `DrawingScale` / `PageScale` / `PrintPageOrientation` /
  `DrawingScaleType` / `DrawingSizeType` cells.
- [`../references/diagram-types.md`](../references/diagram-types.md) —
  59-row diagram-type catalog mapping each template to `Master.NameU` /
  `User.<…>` / `Prop.<…>` / `RouteStyle` / `PlaceStyle` /
  `validation_rule_set` / `add_ons`.
- [`../references/visio-pages-xml.md`](../references/visio-pages-xml.md)
  — authoring guide for the `*.vsdx-page.xml` fragment format Drafter
  writes and this directory's diagram templates use.
- [`../references/connectors.md`](../references/connectors.md) —
  connector authorship reference (glue cells, `RouteStyle`,
  line-end choice, label placement).
- [`../references/data-graphics.md`](../references/data-graphics.md) —
  data-graphics authorship for Stylist (icon sets, colour-by-value,
  data bars).
- [`../references/diagram-layout-patterns.md`](../references/diagram-layout-patterns.md)
  — layout patterns library (process flow / swim-lane / org chart /
  network / mindmap pattern catalog).
- [`../references/architect.md`](../references/architect.md) —
  Eight Confirmations script; lock authorship discipline.
- [`../references/drafter-base.md`](../references/drafter-base.md) —
  per-page Visio Page authorship discipline; batch read + lock re-read
  protocol.
- [`../references/stylist.md`](../references/stylist.md) — theme
  application, data-graphics binding, layer organisation, container /
  list shape composition.
