# Canvas Format Specification

> See `shared-standards.md` for ShapeSheet authoring rules; see
> `visio-pages-xml.md` for the XML fragment Drafter actually emits.
> This file is the catalog Architect (`references/architect.md`)
> consults when filling the `## canvas` block of `diagram_lock.md`,
> and the table Drafter (`references/drafter-base.md`) reads when
> resolving `canvas.format` to concrete page-sheet cells.

## 0. Scope and load-bearing contract

Visio is a physical-page tool. Every drawing has at least one Page,
every Page carries a `PageSheet`, and every `PageSheet` declares
`PageWidth` / `PageHeight` / `DrawingUnits` / `DrawingScale` /
`PageScale` / `PrintPageOrientation` / `DrawingScaleType` /
`DrawingSizeType`. Picking a "canvas format" in `diagram_lock.md`
is therefore not a single value — it is a tuple that resolves to
those eight cells (plus `PageNumber`, `Background`, `LineJumpStyle`
and `RouteStyle` which are separately governed by
`connectors.md` and `diagram-layout-patterns.md`).

The blueprint's Confirmation 1 (`canvas.format` /
`canvas.units` / `canvas.width` / `canvas.height` / `canvas.dpi`)
locks the values in this file's preset catalog or — when the user
selects `custom` — copies user-supplied numeric values into the
same five fields. Once locked, **no other role rewrites those
cells**:

- Drafter writes `<PageSheet>` once per page, copying the locked
  values verbatim. There is no per-page page-size variation in a
  single drawing — multi-size drawings require multiple
  `<project>/pages/` entries each carrying their own `canvas`
  override block in `page_layouts.P<NN>.canvas`. That override
  is rare; the default rule is one canvas per drawing.
- Stylist applies theme, layers, and data graphics on top of the
  declared canvas; it does NOT change `PageWidth` / `PageHeight`.
- `update_diagram_lock.py` will refuse to mutate `canvas.*` after
  pages have been emitted because the page-sheet cells have
  already been baked into every emitted Visio Page fragment.

The catalog below is therefore consulted **before** any page is
written, and frozen for the life of the drawing.

## 1. Visio's coordinate model in 30 lines

The entire format catalog rests on one rule: `PageWidth`,
`PageHeight`, and every shape's `PinX` / `PinY` / `Width` /
`Height` / `BeginX` / `BeginY` / `EndX` / `EndY` / `LocPinX` /
`LocPinY` are **stored in inches** in the `.vsdx` XML stream
regardless of what unit the user typed. The unit appears only in
two places:

1. The `DrawingUnits` cell on `PageSheet`. Its enum encodes the
   *display* unit a Visio editor will show on rulers and dialogs.
2. Each cell's `FormulaU` (universal formula) preserves the
   user-typed string — `"297 mm"` or `"11.69 in"` — but the
   sibling `Result` / `ResultIU` reads back inches. Drafter writes
   `FormulaU` so editors render the human form; the parser writes
   `Result` for diagnostic reads.

The `DrawingUnits` enum (from `Visio.VisCellVals` /
`VisUnitCodes`):

| Constant     | Integer | Meaning              |
|--------------|--------:|----------------------|
| `visInches`  |    `0`  | inch                 |
| `visFeet`    |    `1`  | foot                 |
| `visMM`      |   `20`  | millimetre           |
| `visCM`      |   `21`  | centimetre           |
| `visM`       |   `22`  | metre                |
| `visKM`      |   `23`  | kilometre            |
| `visMiles`   |    `2`  | mile                 |
| `visYards`   |    `3`  | yard                 |
| `visPoints`  |   `30`  | typographic point    |
| `visPicas`   |   `31`  | pica (12 pt)         |
| `visDidots`  |   `32`  | didot                |
| `visCiceros` |   `33`  | cicero (12 didots)   |
| `visDate`    |   `40`  | (calendar templates) |
| `visAngular` |   `50`  | (radial layouts)     |

`DrawingScaleType` is a separate enum that picks the scale family
(no-scale / architectural / civil / metric / mechanical / custom).
It cooperates with `DrawingScale` and `PageScale` to produce the
ratio shown on engineering plates. For non-engineering presets
(business diagrams, network maps, BPMN), `DrawingScaleType = 0`
(no scale), `DrawingScale = 1 in`, `PageScale = 1 in` — the page
is its own ruler.

| `DrawingScaleType` | Value | Family                                   |
|--------------------|------:|------------------------------------------|
| `visNoScale`       |   `0` | logical 1:1 (default for diagrams)       |
| `visArchitectural` |   `1` | `1/4" = 1'-0"` and friends               |
| `visCivilEng`      |   `2` | `1" = 10'`, `1" = 20'` and friends       |
| `visCustomScale`   |   `3` | user-supplied                            |
| `visMetric`        |   `4` | `1:50`, `1:100`, `1:200`                 |
| `visMechanicalEng` |   `5` | mechanical drawing scales                |

`DrawingSizeType` controls how the page bounds relate to print
output:

| `DrawingSizeType`  | Value | Effect                                              |
|--------------------|------:|-----------------------------------------------------|
| `visSizeSame`      |   `0` | same as printer paper                               |
| `visSizeFitToPages`|   `1` | shrink/grow to fit a printer-page integer count    |
| `visSizeStandard`  |   `2` | named paper size (Letter, Tabloid, A0..A6, etc.)    |
| `visSizeCustom`    |   `3` | freeform `PageWidth` / `PageHeight`                 |
| `visSizePrintFitOnPages` | `4` | shrink to fit one printer sheet               |

Most of the presets below resolve to either `visSizeStandard` (the
named paper sizes) or `visSizeCustom` (the bespoke ones).

## 2. Format catalog — quick reference

The `canvas.format` value Architect writes into `diagram_lock.md`
must be one of these IDs, or `custom`. Width/height columns give
the **page area**, not the printable area; margins are listed
separately in §6. The `DSU` column is the `DrawingScaleType` enum
value, the `DST` column is `DrawingSizeType`, and the `Units` column
gives the recommended display unit (which sets `DrawingUnits`).

### 2.1 ISO A-series (metric, sqrt(2) aspect ratio)

| ID                | Paper | Width × Height        | Width × Height (in) | Units | DSU | DST | Best fit                                     |
|-------------------|-------|-----------------------|---------------------|-------|----:|----:|----------------------------------------------|
| `a0-landscape`    | A0    | 1189 × 841 mm         | 46.81 × 33.11 in    | `mm`  | `0` | `2` | wall posters, factory layout, mega-network    |
| `a0-portrait`     | A0    | 841 × 1189 mm         | 33.11 × 46.81 in    | `mm`  | `0` | `2` | architectural plans (portrait)                |
| `a1-landscape`    | A1    | 841 × 594 mm          | 33.11 × 23.39 in    | `mm`  | `0` | `2` | floor plans, P&ID, large network maps         |
| `a1-portrait`     | A1    | 594 × 841 mm          | 23.39 × 33.11 in    | `mm`  | `0` | `2` | tall org charts, deep flows                   |
| `a2-landscape`    | A2    | 594 × 420 mm          | 23.39 × 16.54 in    | `mm`  | `0` | `2` | data-center rack rooms, mid-size topology     |
| `a2-portrait`     | A2    | 420 × 594 mm          | 16.54 × 23.39 in    | `mm`  | `0` | `2` | technical posters                              |
| `a3-landscape`    | A3    | 420 × 297 mm          | 16.54 × 11.69 in    | `mm`  | `0` | `2` | swim-lane, BPMN, network, AWS/Azure default   |
| `a3-portrait`     | A3    | 297 × 420 mm          | 11.69 × 16.54 in    | `mm`  | `0` | `2` | mind map portrait, vertical timelines         |
| `a4-landscape`    | A4    | 297 × 210 mm          | 11.69 × 8.27 in     | `mm`  | `0` | `2` | flowchart, single-page summary                |
| `a4-portrait`     | A4    | 210 × 297 mm          | 8.27 × 11.69 in     | `mm`  | `0` | `2` | runbooks, A4 print-ready, document inserts    |
| `a5-landscape`    | A5    | 210 × 148 mm          | 8.27 × 5.83 in      | `mm`  | `0` | `2` | handout cards, micro flow                     |
| `a5-portrait`     | A5    | 148 × 210 mm          | 5.83 × 8.27 in      | `mm`  | `0` | `2` | bookmark-style ref cards                      |
| `a6-landscape`    | A6    | 148 × 105 mm          | 5.83 × 4.13 in      | `mm`  | `0` | `2` | sticker-card decision aids                    |
| `a6-portrait`     | A6    | 105 × 148 mm          | 4.13 × 5.83 in      | `mm`  | `0` | `2` | tear-off pocket guides                        |

The `sqrt(2)` aspect (1:1.414) is exact only at the limit; ISO 216
defines each step with rounding to whole mm so successive halvings
remain a true halving. Visio reproduces the canonical sizes
exactly; the inch column is a derived display value, never written
back into the lock.

### 2.2 ISO B-series (intermediate paper sizes)

| ID            | Paper | Width × Height       | Units | Best fit                                        |
|---------------|-------|----------------------|-------|-------------------------------------------------|
| `b0-landscape`| B0    | 1414 × 1000 mm       | `mm`  | trade-show banner, oversize topology            |
| `b1-landscape`| B1    | 1000 × 707 mm        | `mm`  | conference posters, master-plan summary         |
| `b2-landscape`| B2    | 707 × 500 mm         | `mm`  | engineering shop drawings                       |
| `b3-landscape`| B3    | 500 × 353 mm         | `mm`  | mid-format flowcharts, dense process maps       |
| `b4-landscape`| B4    | 353 × 250 mm         | `mm`  | between A3 and A4 — used for Asian print specs  |
| `b5-landscape`| B5    | 250 × 176 mm         | `mm`  | trade book page, spec sheets                    |
| `b6-landscape`| B6    | 176 × 125 mm         | `mm`  | small-format reference                          |

The B-series sits between successive A sizes (B`n` ≈ geometric mean
of A`n-1` and A`n`) and is rare in business diagramming. visio-master
exposes it for completeness; the recommended default is the A-series.

### 2.3 ANSI / US-customary

| ID                  | Paper           | Width × Height (in) | Width × Height (mm) | Units | DSU | DST | Best fit                              |
|---------------------|-----------------|---------------------|---------------------|-------|----:|----:|---------------------------------------|
| `letter-portrait`   | ANSI A / Letter | 8.5 × 11 in         | 215.9 × 279.4 mm    | `in`  | `0` | `2` | basic flowchart (US default)          |
| `letter-landscape`  | ANSI A / Letter | 11 × 8.5 in         | 279.4 × 215.9 mm    | `in`  | `0` | `2` | calendar, simple workflow             |
| `legal-portrait`    | Legal           | 8.5 × 14 in         | 215.9 × 355.6 mm    | `in`  | `0` | `2` | tall flowchart, contract diagrams     |
| `legal-landscape`   | Legal           | 14 × 8.5 in         | 355.6 × 215.9 mm    | `in`  | `0` | `2` | wide swim-lane (rare)                 |
| `tabloid-landscape` | Tabloid / Ledger / ANSI B | 17 × 11 in | 431.8 × 279.4 mm  | `in`  | `0` | `2` | swim-lane, BPMN (US default)          |
| `tabloid-portrait`  | Tabloid / ANSI B| 11 × 17 in          | 279.4 × 431.8 mm    | `in`  | `0` | `2` | tall org chart, deep flows            |
| `ansi-c-landscape`  | ANSI C          | 22 × 17 in          | 558.8 × 431.8 mm    | `in`  | `0` | `2` | mid-network, factory cell layout      |
| `ansi-d-landscape`  | ANSI D          | 34 × 22 in          | 863.6 × 558.8 mm    | `in`  | `0` | `2` | floor plan, HVAC, Plan 2 default      |
| `ansi-e-landscape`  | ANSI E          | 44 × 34 in          | 1117.6 × 863.6 mm   | `in`  | `0` | `2` | PFD, P&ID, site plan                  |
| `ansi-f-landscape`  | ANSI F          | 40 × 28 in          | 1016 × 711.2 mm     | `in`  | `0` | `2` | (rarely used; legacy aerospace)       |

The ANSI lineage has its own halving rule: ANSI A → B (rotate +
double width), B → C (rotate + double width), and so on. ANSI does
NOT preserve aspect ratio across sizes — odd-numbered steps are
landscape, even are portrait, and the aspect alternates between
1.294 (`sqrt(11/8.5)`-ish) and 1.545 (`14/8.5`). When mixing ANSI
sizes in a portfolio, expect the layout grid to need rebalancing
between the odd and even steps.

### 2.4 Architectural (Arch A..E1) — bigger than ANSI, 4:3 family

| ID                  | Paper   | Width × Height (in) | Width × Height (mm) | Units | DSU | Best fit                                      |
|---------------------|---------|---------------------|---------------------|-------|----:|------------------------------------------------|
| `arch-a-landscape`  | Arch A  | 12 × 9 in           | 304.8 × 228.6 mm    | `in`  | `1` | small detail sheet, sketch elevation           |
| `arch-b-landscape`  | Arch B  | 18 × 12 in          | 457.2 × 304.8 mm    | `in`  | `1` | partial floor plan, room schedule              |
| `arch-c-landscape`  | Arch C  | 24 × 18 in          | 609.6 × 457.2 mm    | `in`  | `1` | small floor plan, RCP                          |
| `arch-d-landscape`  | Arch D  | 36 × 24 in          | 914.4 × 609.6 mm    | `in`  | `1` | full floor plan (US AEC default)               |
| `arch-e-landscape`  | Arch E  | 48 × 36 in          | 1219.2 × 914.4 mm   | `in`  | `1` | large floor plan, site plan, complete set      |
| `arch-e1-landscape` | Arch E1 | 42 × 30 in          | 1066.8 × 762 mm     | `in`  | `1` | between Arch D and Arch E                      |

Architectural sizes preserve a 4:3 (or 3:2 for E1) aspect across
the sequence, which keeps schedules and detail callouts visually
consistent across sheet sizes. The recommended `DrawingScaleType`
is `1` (`visArchitectural`) which forces the scale combo box to the
`1/x" = 1'-0"` family.

### 2.5 Engineering scales — large-format technical drawings

These IDs are aliases for ANSI sizes with the engineering scale
family pre-selected, plus the dedicated `tabloid-engineering` /
`a3-engineering` defaults Visio uses for floor-plan templates.

| ID                          | Base size  | Recommended scale       | DSU | Best fit                                      |
|-----------------------------|------------|--------------------------|----:|------------------------------------------------|
| `engineering-d-landscape`   | ANSI D     | `1/4 in = 1 ft` (1:48)   | `1` | floor plan US default                          |
| `engineering-e-landscape`   | ANSI E     | `1 ft` (1:1 schematic)   | `1` | PFD / P&ID                                     |
| `metric-a1-engineering`     | A1         | `1:50`                   | `4` | floor plan metric default                      |
| `metric-a0-engineering`     | A0         | `1:100`                  | `4` | site plan metric default                       |
| `civil-d-landscape`         | ANSI D     | `1 in = 20 ft` (1:240)   | `2` | site plan US default                           |
| `civil-e-landscape`         | ANSI E     | `1 in = 50 ft` (1:600)   | `2` | regional / land plot                           |

When the user picks one of these, Architect MUST also fill the
`canvas.scale.drawing_scale` and `canvas.scale.page_scale` fields
in `diagram_lock.md` (default values listed in §4); otherwise the
ratio prints differently from what the page-sheet declares.

### 2.6 Whiteboard / poster / tile (custom-formed)

| ID                  | Width × Height       | Units | DST | Best fit                                       |
|---------------------|----------------------|-------|----:|------------------------------------------------|
| `whiteboard-1080p`  | 1920 × 1080 px @ 96 dpi (≈ 20 × 11.25 in) | `in` | `3` | digital whiteboard / TV display |
| `whiteboard-4k`     | 3840 × 2160 px @ 96 dpi (≈ 40 × 22.5 in) | `in` | `3` | 4K kiosk, conference room TV                   |
| `square-poster`     | 24 × 24 in           | `in`  | `3` | center-radial mind map, hub topology           |
| `wide-poster`       | 60 × 24 in           | `in`  | `3` | conference banner, value-stream wall map       |
| `vertical-banner`   | 24 × 60 in           | `in`  | `3` | retractable banner, lobby display              |
| `slide-16x9`        | 13.33 × 7.5 in       | `in`  | `3` | matches PPT 16:9 — for cross-deck embedding    |
| `slide-4x3`         | 10 × 7.5 in          | `in`  | `3` | matches PPT 4:3 — legacy projector slide       |

`whiteboard-1080p` and `slide-*` exist so a Visio Page can be
embedded into a PPTX deck via `vsdx_export.py --embed-png`
without coordinate mismatch.

### 2.7 Custom

The `custom` ID accepts any positive numeric `canvas.width` /
`canvas.height` in `mm` or `in`. When `custom`, Architect MUST
fill all five Confirmation 1 fields (no defaults). Recommended
guard-rails:

- minimum: 50 × 50 mm (smaller fails to render legibly)
- maximum: 5000 × 5000 mm (larger blows the COM export budget)
- aspect ratio: 1:5 to 5:1 (extreme aspects break stencil scaling)

## 3. PageSheet cell mapping

For every preset, Drafter writes the following `<Cell>` rows on
the Page's `<PageSheet>` in `pages/<NN>_<name>.vsdx-page.xml`.
`PinX` and `PinY` of the page are at the geometric centre by
convention; rotated pages set `LocPinX` / `LocPinY` to the same
centre.

| Cell                  | Source field           | Example formula                  |
|-----------------------|------------------------|----------------------------------|
| `PageWidth`           | `canvas.width`         | `=297 mm` (A4 landscape)         |
| `PageHeight`          | `canvas.height`        | `=210 mm`                        |
| `ShdwOffsetX`         | (theme)                | `=THEMEVAL("ShdwOffsetX")`       |
| `ShdwOffsetY`         | (theme)                | `=THEMEVAL("ShdwOffsetY")`       |
| `PageScale`           | `canvas.scale.page_scale`    | `=1 in` for diagrams       |
| `DrawingScale`        | `canvas.scale.drawing_scale` | `=1 in` for diagrams       |
| `DrawingSizeType`     | preset's `DST`         | `=2` (visSizeStandard)           |
| `DrawingScaleType`    | preset's `DSU`         | `=0` (visNoScale)                |
| `InhibitSnap`         | `canvas.snap_to_grid`  | `=0` (default — snap on)         |
| `UIVisibility`        | `canvas.ui`            | `=0`                             |
| `ShdwType`            | (theme)                | `=THEMEVAL("ShdwType")`          |
| `DrawingResizeType`   | `canvas.resize`        | `=0` (no auto resize)            |
| `PageLockReplace`     | (defaults `0`)         | `=0`                             |
| `PageLockDuplicate`   | (defaults `0`)         | `=0`                             |
| `PrintPageOrientation`| `canvas.orientation`   | `=2` (landscape) / `=1` (portrait)|
| `PaperKind`           | derived from preset    | `=9` for A4, `=1` for Letter     |
| `PrintGrid`           | `canvas.print_grid`    | `=0`                             |
| `PaperSource`         | (defaults `7` auto)    | `=7`                             |
| `DrawingUnits`        | `canvas.units` enum    | `=20` (`mm`) or `=0` (`in`)      |
| `Background`          | `canvas.is_background` | `=0` (foreground) / `=1`         |

`PaperKind` is the Windows `DEVMODE` enum and matters when the
file is printed through the Windows print spooler. It also
matters when COM export saves to PDF — the produced PDF inherits
the paper-kind hint. The full `VisPaperSizes` enumeration is in
§14.2; the preset → `PaperKind` mapping is in §14.3. Custom
presets (`arch-*`, `whiteboard-*`, `slide-*`, `metric-a*-engineering`,
`a0-*`, `a1-*`, `a2-*`) declare `PaperKind = 0` (`visPaperCustom`)
and emit explicit `PaperWidth` / `PaperHeight` cells; Drafter
picks an unused index in the 256..999 band only when serialising
DMPAPER for legacy print drivers.

### 3.1 Worked example — A4 landscape PageSheet

The full PageSheet block Drafter emits for `a4-landscape` looks
like:

```xml
<PageSheet LineStyle="0" FillStyle="0" TextStyle="0">
  <Cell N="PageWidth" V="11.69291338582677" U="MM" F="297 mm"/>
  <Cell N="PageHeight" V="8.267716535433071" U="MM" F="210 mm"/>
  <Cell N="ShdwOffsetX" V="0.125"/>
  <Cell N="ShdwOffsetY" V="-0.125"/>
  <Cell N="PageScale" V="1" U="MM" F="1 mm"/>
  <Cell N="DrawingScale" V="1" U="MM" F="1 mm"/>
  <Cell N="DrawingSizeType" V="2"/>
  <Cell N="DrawingScaleType" V="0"/>
  <Cell N="InhibitSnap" V="0"/>
  <Cell N="PageLockReplace" V="0"/>
  <Cell N="PageLockDuplicate" V="0"/>
  <Cell N="UIVisibility" V="0"/>
  <Cell N="ShdwType" V="0"/>
  <Cell N="ShdwObliqueAngle" V="0"/>
  <Cell N="ShdwScaleFactor" V="1"/>
  <Cell N="DrawingResizeType" V="1"/>
  <Cell N="PaperKind" V="9"/>
  <Cell N="PrintPageOrientation" V="2"/>
  <Cell N="PaperSource" V="7"/>
  <Cell N="PrintGrid" V="0"/>
  <Cell N="DrawingUnits" V="20"/>
  <Cell N="Background" V="0"/>
</PageSheet>
```

Note that the `V` attribute is always inches (`Result`) while the
`F` attribute carries the locale-stable formula (`FormulaU`). The
inch value 11.69291338582677 is exactly 297 mm divided by 25.4.
Drafter uses six decimal digits; eight is also acceptable but
adds bytes for no parser benefit.

## 4. Default scale and units per preset

Most diagram presets keep the canvas at logical 1:1 — every drawn
inch is one inch on the page. Engineering and floor-plan presets
apply a scale ratio so a 1:50 drawing of a 5 m wall takes
100 mm on the page.

### 4.1 Diagram presets — no scale

| ID                  | DrawingScaleType | DrawingScale | PageScale | Effective ratio |
|---------------------|-----------------:|--------------|-----------|-----------------|
| `a4-*`              | `0`              | `=1 mm`      | `=1 mm`   | 1:1             |
| `a3-*`              | `0`              | `=1 mm`      | `=1 mm`   | 1:1             |
| `letter-*`          | `0`              | `=1 in`      | `=1 in`   | 1:1             |
| `tabloid-*`         | `0`              | `=1 in`      | `=1 in`   | 1:1             |
| `whiteboard-*`      | `0`              | `=1 in`      | `=1 in`   | 1:1             |
| `slide-*`           | `0`              | `=1 in`      | `=1 in`   | 1:1             |

### 4.2 Floor-plan presets — architectural / metric scale

Following `research/16-floorplan-engineering-family.md` §1.3:

| ID                       | DrawingScaleType | DrawingScale  | PageScale   | Effective ratio   |
|--------------------------|-----------------:|---------------|-------------|-------------------|
| `engineering-d-landscape`| `1` arch         | `=0.25 in`    | `=12 in`    | 1:48 (1/4"=1ft)   |
| `arch-d-landscape`       | `1` arch         | `=0.25 in`    | `=12 in`    | 1:48              |
| `arch-e-landscape`       | `1` arch         | `=0.125 in`   | `=12 in`    | 1:96 (1/8"=1ft)   |
| `metric-a1-engineering`  | `4` metric       | `=50 mm`      | `=1000 mm`  | 1:50              |
| `metric-a0-engineering`  | `4` metric       | `=100 mm`     | `=1000 mm`  | 1:100             |

The two scale cells together encode the ratio: `PageScale` is
"how many drawing-units one page-unit represents" and
`DrawingScale` is "how many drawing-units one drawing-unit covers".
The visual ratio is `DrawingScale / PageScale`. For US `1/4" = 1'-0"`,
that is `0.25 in / 12 in = 1/48`. For metric `1:50`, that is
`50 mm / 1000 mm = 1/20`, but Visio internally treats it as the
1:50 scale family because `DrawingScaleType = 4` is set and
ribbon UI parses the ratio from the cells.

### 4.3 Engineering process presets

Following `research/12-builtin-templates-catalog.md` §7:

| ID                       | DrawingScaleType | DrawingScale | PageScale | Effective ratio |
|--------------------------|-----------------:|--------------|-----------|-----------------|
| `engineering-e-landscape`| `0`              | `=1 ft`      | `=1 ft`   | 1:1 schematic   |
| `engineering-d-landscape`| `1`              | `=0.25 in`   | `=12 in`  | 1:48            |

PFDs and P&IDs use `DrawingScale = 1 ft` because they are
schematic — the page is a story, not a measured plan. Pipe
sizes are encoded in `Prop.Diameter` shape data, not in the
geometry.

### 4.4 Civil presets

| ID                  | DrawingScaleType | DrawingScale | PageScale | Effective ratio |
|---------------------|-----------------:|--------------|-----------|-----------------|
| `civil-d-landscape` | `2` civil        | `=1 in`      | `=20 ft`  | 1:240 (1"=20ft) |
| `civil-e-landscape` | `2` civil        | `=1 in`      | `=50 ft`  | 1:600 (1"=50ft) |

`DrawingScaleType = 2` activates the civil-engineering ribbon
preset list (`1"=10'`, `1"=20'`, `1"=30'`, `1"=40'`, `1"=50'`,
`1"=60'`, `1"=80'`, `1"=100'`, `1"=200'`, `1"=400'`).

## 5. Margin guidelines

Margins are **not** stored on the PageSheet — Visio has no
"page margin" cell. Margin discipline lives in the layout
templates (`templates/page-layouts/<id>/`) and in
`diagram-layout-patterns.md`. The values below are the
recommended interior padding from each edge before content
should start. Drafter places title, content, footer, and
page-number anchors using these margins.

### 5.1 Diagram-canvas margins (no-scale presets)

| Preset family              | Top    | Right  | Bottom | Left   | Notes                                 |
|----------------------------|--------|--------|--------|--------|---------------------------------------|
| `letter-*`                 | 0.5 in | 0.5 in | 0.5 in | 0.5 in | symmetric                             |
| `legal-*`                  | 0.5 in | 0.5 in | 0.5 in | 0.5 in | symmetric                             |
| `tabloid-*`                | 0.5 in | 0.5 in | 0.5 in | 0.5 in | symmetric                             |
| `a4-*`                     | 12 mm  | 12 mm  | 12 mm  | 12 mm  | symmetric (≈ 0.47 in)                 |
| `a3-*`                     | 15 mm  | 15 mm  | 15 mm  | 15 mm  | symmetric                             |
| `a2-*`                     | 20 mm  | 20 mm  | 20 mm  | 20 mm  | symmetric                             |
| `a1-*`                     | 25 mm  | 25 mm  | 25 mm  | 25 mm  | symmetric                             |
| `a0-*`                     | 30 mm  | 30 mm  | 30 mm  | 30 mm  | symmetric                             |
| `whiteboard-1080p`         | 0.5 in | 0.5 in | 0.5 in | 0.5 in | TV-safe area; 5% safe zone optional   |
| `whiteboard-4k`            | 1.0 in | 1.0 in | 1.0 in | 1.0 in | TV-safe area at 4K resolution         |
| `slide-16x9`               | 0.5 in | 0.5 in | 0.4 in | 0.5 in | matches ppt-master 16:9 margins        |
| `slide-4x3`                | 0.4 in | 0.4 in | 0.3 in | 0.4 in | matches ppt-master 4:3 margins         |

### 5.2 Engineering / floor-plan margins (with title block)

Engineering canvases reserve a fixed strip on the right edge for
the title block (`User.titleblock = TRUE` on the page; the strip
contains the project name, drawing number, scale, revision,
issue date, and signature blocks). visio-master ships the title
block as a master in `templates/stencils/engineering-title-blocks/`.

| Preset family              | Top    | Right (incl. title block) | Bottom | Left   | Title block size |
|----------------------------|--------|----------------------------|--------|--------|------------------|
| `arch-d-landscape`         | 1.0 in | 6.0 in                     | 1.0 in | 1.0 in | 5 × 22 in        |
| `arch-e-landscape`         | 1.5 in | 8.0 in                     | 1.5 in | 1.5 in | 6.5 × 33 in      |
| `engineering-d-landscape`  | 1.0 in | 6.0 in                     | 1.0 in | 1.0 in | 5 × 20 in        |
| `engineering-e-landscape`  | 1.5 in | 8.0 in                     | 1.5 in | 1.5 in | 6.5 × 31 in      |
| `metric-a1-engineering`    | 25 mm  | 150 mm                     | 25 mm  | 25 mm  | 130 × 540 mm     |
| `metric-a0-engineering`    | 30 mm  | 180 mm                     | 30 mm  | 30 mm  | 155 × 780 mm     |
| `civil-d-landscape`        | 1.0 in | 6.0 in                     | 1.0 in | 1.0 in | 5 × 20 in        |
| `civil-e-landscape`        | 1.5 in | 8.0 in                     | 1.5 in | 1.5 in | 6.5 × 31 in      |

Drafter writes the title-block group at `(PageWidth - margin -
titleblock_width / 2, PageHeight / 2)` so it stays right-aligned
inside the printable area. The block consumes the right margin —
non-title-block content uses the smaller "drawable rectangle":

```
drawable_x = left_margin .. (PageWidth - right_margin)
drawable_y = bottom_margin .. (PageHeight - top_margin)
```

### 5.3 Poster / banner margins

| Preset             | Top    | Right  | Bottom | Left   | Notes                                          |
|--------------------|--------|--------|--------|--------|------------------------------------------------|
| `square-poster`    | 1.0 in | 1.0 in | 1.0 in | 1.0 in | symmetric, leaves room for title and legend    |
| `wide-poster`      | 2.0 in | 2.0 in | 2.0 in | 2.0 in | wider banner needs more breathing room         |
| `vertical-banner`  | 2.0 in | 1.0 in | 2.0 in | 1.0 in | tall side-margin for retractable display       |
| `b0-*`             | 30 mm  | 30 mm  | 30 mm  | 30 mm  | symmetric                                      |
| `b1-*`             | 25 mm  | 25 mm  | 25 mm  | 25 mm  | symmetric                                      |

## 6. Suitable diagram types per preset

The full preset → diagram fit map is consolidated in §7.2 (auto-
recommendation matrix) and §17 (decision tree). The short rule:

- **A4 / Letter** — flowchart, runbook, decision tree, single-cycle.
- **A3 / Tabloid** — swim-lane, BPMN, network, AWS/Azure, UML, ERD,
  mid org chart, mind map (portrait), state machine.
- **A2 / ANSI C** — mid-network, factory cell, partial floor plan.
- **A1 / ANSI D** — floor plan, HVAC, electrical, security plan,
  rack room, large network as-built.
- **A0 / ANSI E** — site plan, full architectural set, PFD, P&ID,
  factory layout, master-plan.
- **Arch D / Arch E** — US-AEC floor plan / site plan with the
  architectural scale family preselected.
- **Engineering E** — schematic PFD/P&ID at `1 ft` page scale.
- **Civil D / Civil E** — civil overlays, plot plans, regional plans.
- **Whiteboard / poster / banner** — collaborative, brainstorming,
  retro, kanban, lean canvas, value-stream wall maps.
- **Slide-16x9 / slide-4x3** — drawings destined for embedding into
  PowerPoint at slide pixel dimensions.

Anti-fits worth flagging during Confirmation 1: never put a full
floor plan on A4 (`coordinate.out-of-bounds` near-certainty);
never put a flowchart on A0 (every shape ends up as a postage
stamp); never put a swim-lane on a vertical banner (lanes need
horizontal travel).

## 7. Default canvas presets visio-master ships

These are the IDs reachable from Architect Confirmation 1 without
custom values. Each is registered in
`templates/page-layouts/page-layouts_index.json` under its preset
name; Architect's recommendation engine picks one of these based
on the source bulk and `primary_diagram_type` from Confirmation 2.

### 7.1 Default presets — full table

| Preset ID              | Width × Height       | Units | DSU | DST | Orient.   | Diagram fit              |
|------------------------|----------------------|-------|----:|----:|-----------|--------------------------|
| `a4-landscape`         | 297 × 210 mm         | `mm`  | `0` | `2` | landscape | flowchart                |
| `a4-portrait`          | 210 × 297 mm         | `mm`  | `0` | `2` | portrait  | runbook                  |
| `a3-landscape`         | 420 × 297 mm         | `mm`  | `0` | `2` | landscape | swim-lane / BPMN         |
| `a3-portrait`          | 297 × 420 mm         | `mm`  | `0` | `2` | portrait  | mind map / org chart     |
| `letter-portrait`      | 8.5 × 11 in          | `in`  | `0` | `2` | portrait  | flowchart (US)           |
| `letter-landscape`     | 11 × 8.5 in          | `in`  | `0` | `2` | landscape | calendar / workflow      |
| `tabloid-landscape`    | 17 × 11 in           | `in`  | `0` | `2` | landscape | swim-lane / BPMN (US)    |
| `tabloid-portrait`     | 11 × 17 in           | `in`  | `0` | `2` | portrait  | tall org chart           |
| `ansi-d-landscape`     | 34 × 22 in           | `in`  | `0` | `2` | landscape | floor plan (US)          |
| `ansi-e-landscape`     | 44 × 34 in           | `in`  | `0` | `2` | landscape | PFD / P&ID               |
| `metric-a1-engineering`| 841 × 594 mm         | `mm`  | `4` | `2` | landscape | floor plan (metric)      |
| `metric-a0-engineering`| 1189 × 841 mm        | `mm`  | `4` | `2` | landscape | site plan (metric)       |
| `arch-d-landscape`     | 36 × 24 in           | `in`  | `1` | `2` | landscape | floor plan (US AEC)      |
| `arch-e-landscape`     | 48 × 36 in           | `in`  | `1` | `2` | landscape | site plan / set sheet    |
| `whiteboard-1080p`     | 1920 × 1080 px       | `in`  | `0` | `3` | landscape | retro / brainstorm       |
| `slide-16x9`           | 13.33 × 7.5 in       | `in`  | `0` | `3` | landscape | slide embed              |

### 7.2 Architect's auto-recommendation matrix

When the user does not state a preference, Architect picks a
canvas from this table by intersecting `primary_diagram_type`
(Confirmation 2) and `audience` (Confirmation 3):

| `primary_diagram_type`      | Default audience: technical | Default audience: executive | Default audience: public |
|-----------------------------|------------------------------|------------------------------|---------------------------|
| `process-flow`              | `a3-landscape`               | `a4-landscape`               | `a4-landscape`            |
| `flowchart`                 | `a4-portrait`                | `a4-landscape`               | `a4-portrait`             |
| `swim-lane`                 | `a3-landscape`               | `a3-landscape`               | `a3-landscape`            |
| `bpmn`                      | `a3-landscape`               | `tabloid-landscape`          | `a3-landscape`            |
| `org-chart`                 | `a3-landscape`               | `a3-portrait`                | `a4-portrait`             |
| `network`                   | `a2-landscape`               | `a3-landscape`               | `a3-landscape`            |
| `topology`                  | `a1-landscape`               | `a2-landscape`               | `a3-landscape`            |
| `erd`                       | `a3-landscape`               | `tabloid-landscape`          | `a4-landscape`            |
| `state-machine`             | `a3-landscape`               | `a3-landscape`               | `a4-landscape`            |
| `mind-map`                  | `a3-portrait`                | `a3-portrait`                | `square-poster`           |
| `venn` / `quadrant`         | `a4-landscape`               | `square-poster`              | `square-poster`           |
| `floor-plan`                | `metric-a1-engineering`      | `metric-a1-engineering`      | `arch-d-landscape`        |
| `pfd` / `pid`               | `engineering-e-landscape`    | `arch-e-landscape`           | `tabloid-landscape`       |
| `mixed` (multi-type)        | `a3-landscape`               | `tabloid-landscape`          | `a3-landscape`            |

The recommendation is a starting point. The user always overrides
during Confirmation 1; the recommendation never auto-locks.

## 8. `diagram_lock.md` `## canvas` block — schema and example

Architect emits one block per drawing. Multi-page drawings declare
the canvas once; per-page overrides go in
`page_layouts.P<NN>.canvas` (rare).

### 8.1 Field reference

| Field                       | Type            | Required | Notes                                                        |
|-----------------------------|-----------------|----------|--------------------------------------------------------------|
| `canvas.format`             | preset ID       | yes      | one of §7.1 IDs or `custom`                                  |
| `canvas.units`              | enum            | yes      | `mm` / `in`                                                  |
| `canvas.width`              | number          | yes      | in `canvas.units`                                            |
| `canvas.height`             | number          | yes      | in `canvas.units`                                            |
| `canvas.orientation`        | enum            | yes      | `landscape` / `portrait`                                     |
| `canvas.dpi`                | integer         | no       | `96` default; `150` for print-bound drawings                 |
| `canvas.scale.type`         | DSU enum        | no       | `no-scale` / `architectural` / `civil` / `metric` / `mechanical` / `custom` |
| `canvas.scale.drawing_scale`| length string   | no       | e.g. `0.25 in` / `50 mm` / `1 ft`                            |
| `canvas.scale.page_scale`   | length string   | no       | e.g. `12 in` / `1000 mm` / `1 ft`                            |
| `canvas.size_type`          | DST enum        | no       | `same` / `fit-to-pages` / `standard` / `custom` / `print-fit-on-pages` |
| `canvas.paper_kind`         | integer         | no       | DMPAPER value when known; helpful for COM round-trip         |
| `canvas.snap_to_grid`       | boolean         | no       | default `true`                                               |
| `canvas.print_grid`         | boolean         | no       | default `false`                                              |
| `canvas.title_block`        | string id       | no       | if non-empty, name of a master from `templates/stencils/engineering-title-blocks/` |
| `canvas.margin.top`         | length string   | no       | else inferred from §5                                        |
| `canvas.margin.right`       | length string   | no       | else inferred                                                |
| `canvas.margin.bottom`      | length string   | no       | else inferred                                                |
| `canvas.margin.left`        | length string   | no       | else inferred                                                |
| `canvas.background_page`    | string          | no       | `NameU` of a Background page; default empty                  |

### 8.2 Worked example — A3 landscape swim-lane

```
## canvas
- format: a3-landscape
- units: mm
- width: 420
- height: 297
- orientation: landscape
- dpi: 96
- scale.type: no-scale
- scale.drawing_scale: 1 mm
- scale.page_scale: 1 mm
- size_type: standard
- paper_kind: 8
- snap_to_grid: true
- print_grid: false
- title_block:
- margin.top: 15 mm
- margin.right: 15 mm
- margin.bottom: 15 mm
- margin.left: 15 mm
- background_page:
```

### 8.3 Worked example — ANSI E P&ID with engineering title block

```
## canvas
- format: engineering-e-landscape
- units: in
- width: 44
- height: 34
- orientation: landscape
- dpi: 150
- scale.type: no-scale
- scale.drawing_scale: 1 ft
- scale.page_scale: 1 ft
- size_type: standard
- paper_kind: 26
- snap_to_grid: true
- print_grid: true
- title_block: pid_ansi_e_isa
- margin.top: 1.5 in
- margin.right: 8.0 in
- margin.bottom: 1.5 in
- margin.left: 1.5 in
- background_page: pid-grid
```

The `pid-grid` background page is shipped with the
`engineering-title-blocks` stencil and renders the major-grid
crosshairs, ruler ticks, and rev-history boxes.

For other presets, Drafter follows the same pattern: copy
`format`, `width`, `height`, `units`, and `paper_kind` from §7
and §14.3; copy margins from §5; copy scale from §4. A custom
whiteboard sets `format: custom`, `paper_kind: 256`, and
`size_type: custom`; an A4 portrait runbook sets
`format: a4-portrait`, `paper_kind: 9`, `size_type: standard`,
and 12 mm symmetric margins.

## 9. Page-orientation switching

Visio's `PrintPageOrientation` cell encodes the orientation as an
enum (`visPLOPortrait = 1`, `visPLOLandscape = 2`). To switch a
preset between portrait and landscape, Architect MUST swap
`PageWidth` and `PageHeight` AND set the orientation cell. Visio
does not auto-flip dimensions when only the cell is changed.

### 9.1 Orientation matrix

| Orientation | `PrintPageOrientation` | Page geometry           |
|-------------|------------------------:|--------------------------|
| Portrait    | `1`                     | `width <= height`        |
| Landscape   | `2`                     | `width >= height`        |
| Default     | `0`                     | inherits printer setting |

Drafter validates the relationship: if `canvas.orientation =
landscape` but `canvas.width < canvas.height`, the
`vsdx_quality_checker.py` raises an `error` (rule
`canvas.orientation.mismatch`).

### 9.2 Code-level switch helper

`scripts/vsdx_finalize/page_size.py` exposes:

```python
from vsdx_finalize.page_size import set_canvas

set_canvas(page_xml,
           preset="a3-landscape",
           orientation="landscape")
```

This rewrites all eight page-sheet cells atomically. Calling it
on a page that already has shapes is dangerous — shapes' `PinX` /
`PinY` may now sit outside the new bounds. The quality checker
catches this with the `coordinate.out-of-bounds` rule.

## 10. Multi-page drawings — same canvas vs mixed canvases

The default rule is one canvas for the whole drawing. When a
drawing legitimately mixes canvases (e.g. an A3-landscape network
overview followed by an A4-portrait runbook checklist), each page
declares its canvas in `page_layouts.P<NN>.canvas`:

```
## page_layouts
- P01: cover.vsdx-page.xml
  canvas:
    format: a3-landscape
    units: mm
    width: 420
    height: 297
- P02: runbook_step_1.vsdx-page.xml
  canvas:
    format: a4-portrait
    units: mm
    width: 210
    height: 297
- P03: runbook_step_2.vsdx-page.xml
  canvas:
    format: a4-portrait
    units: mm
    width: 210
    height: 297
```

Mixing canvases is rare because:

1. Visio renders each page with its own paper size; print-to-PDF
   produces a multi-sized PDF, which most viewers handle but which
   confuses some workflow systems (Bates stamping, redaction).
2. The drawing's printable area changes per page, so headers /
   footers / page numbers must be re-laid-out per canvas.
3. The quality checker's `canvas.consistency` warning fires when
   any two pages declare different canvases without an explicit
   `canvas.mixing_allowed: true` flag at the top of the lock.

Best practice: keep one canvas per drawing. Use the multi-canvas
escape hatch only when content genuinely demands it.

## 11. DPI and pixel mapping

Visio is vector-first; DPI matters only when a bitmap is embedded,
a page is exported to PNG / JPG, or the drawing is sent through
a printer driver that rasterises before output.

`canvas.dpi` is recorded so the preview server
(`vsdx_preview/render_page.py`) uses it as the default render DPI,
and so the `whiteboard-*` / `slide-*` presets carry a stable
pixel ratio. The DPI value lets Drafter compute the inch geometry
that matches the requested pixel canvas: 1920 × 1080 px @ 96 dpi
= 20 × 11.25 in (`whiteboard-1080p`); 1280 × 720 px @ 96 dpi =
13.33 × 7.5 in (`slide-16x9`); 3840 × 2160 px @ 96 dpi = 40 ×
22.5 in (`whiteboard-4k`). All custom-pixel presets declare
`paper_kind: 256` (DMPAPER_USER) and emit explicit `PaperWidth`
/ `PaperHeight` in inches.

## 12. Built-in Visio template alignment

When a user picks one of the visio-master presets, the
corresponding shipping Visio template is the closest equivalent
that COM export targets. The mapping below lets `vsdx_export.py`
seed a new document from the Visio built-in template
(`Documents.AddEx(<short_name>.vstx)`), then overwrite the
canvas cells from the lock.

| Preset / context             | Built-in template (short name)     |
|------------------------------|------------------------------------|
| `a4-portrait` (metric)       | `BASFLO_M.VSTX` (Basic Flowchart)  |
| `letter-portrait` (US)       | `BASFLO_U.VSTX` (Basic Flowchart)  |
| `a3-landscape` swim-lane     | `CROSSF_M.VSTX` (Cross-Functional) |
| `tabloid-landscape` US       | `CROSSF_U.VSTX` (Cross-Functional) |
| `a3-landscape` BPMN          | `BPMN_M.VSTX`                      |
| `a3-landscape` brainstorm    | `BRSTRM_M.VSTX`                    |
| `a3-portrait` mind map       | `MINDMAP_M.VSTX`                   |
| `letter-landscape` org       | `ORGCH_U.VSTX`                     |
| `a3-landscape` network       | `NETBAS_M.VSTX`                    |
| `ansi-d-landscape` network   | `NETDET_U.VSTX`                    |
| `a3-landscape` rack          | `RACK_M.VSTX`                      |
| `a3-landscape` AWS / Azure   | `AWS_M.VSTX` / `AZURE_M.VSTX`      |
| `a3-landscape` UML / ERD     | `UMLCLS_M.VSTX` / `DATABS_M.VSTX`  |
| `arch-d-landscape`           | `FLRPLN_U.VSTX` (Floor Plan US)    |
| `metric-a1-engineering`      | `FLRPLN_M.VSTX` (Floor Plan metric)|
| `arch-e-landscape`           | `SITE_U.VSTX` (Site Plan US)       |
| `engineering-e-landscape`    | `PID_U.VSTX` (P&ID US)             |
| `metric-a0-engineering`      | `SITPLN_M.VSTX` (Site Plan metric) |
| `letter-landscape` Gantt     | `GANTT_U.VSTX`                     |
| `letter-landscape` calendar  | `CALEND_U.VSTX`                    |

Refer to `research/12-builtin-templates-catalog.md` for the full
template defaults (page size, `RouteStyle`, `LineJumpStyle`,
preloaded stencils). The mapping is a hint — `vsdx_export.py` may
bypass the built-in template entirely (the `--no-template` flag)
and write the canvas cells directly. The fallback writer (vsdx
Python library) always uses the direct path because it has no
Visio install to invoke `Documents.AddEx`.

## 13. Validation rules — what `vsdx_quality_checker.py` enforces

The checker runs against `pages/<NN>_*.vsdx-page.xml` and
flags the following canvas-related issues:

| Rule ID                          | Severity | What it checks                                                                                  |
|----------------------------------|----------|--------------------------------------------------------------------------------------------------|
| `canvas.format.unknown`          | error    | `canvas.format` is not in §7.1 and not `custom`                                                  |
| `canvas.dimensions.missing`      | error    | `canvas.width` or `canvas.height` absent                                                        |
| `canvas.dimensions.range`        | error    | width or height outside the 50-5000 mm guard-rail                                                |
| `canvas.units.invalid`           | error    | `canvas.units` is not `mm` or `in`                                                              |
| `canvas.orientation.mismatch`    | error    | landscape declared but width < height (or portrait but width > height)                          |
| `canvas.preset.dimensions.drift` | error    | preset ID does not match the dimensions (e.g. `a4-landscape` with 297 × 297)                    |
| `canvas.scale.missing`           | error    | engineering / floor-plan preset without `scale.drawing_scale` and `scale.page_scale`            |
| `canvas.scale.unit_inconsistent` | error    | scale string units don't match `canvas.units`                                                   |
| `canvas.paperkind.mismatch`      | warning  | `paper_kind` declared but does not match the §3.1 row for the preset                            |
| `canvas.consistency`             | warning  | per-page canvases differ without `canvas.mixing_allowed: true`                                  |
| `coordinate.out-of-bounds`       | error    | any shape's bounding box exceeds the page bounds                                                |
| `coordinate.title_block_overlap` | warning  | non-title-block content sits inside the title-block strip                                       |
| `canvas.dpi.range`               | warning  | DPI < 72 or > 600                                                                               |
| `canvas.background_unknown`      | error    | `background_page` references a page not declared as `Background="1"`                            |

`vsdx_quality_checker.py` exits `0` if no warnings or errors,
`1` if warnings only, `2` if any error. Errors block Step 7
(post-processing) per §7.5 of the blueprint.

## 14. Print and export concerns

The canvas declaration interacts with three orthogonal Visio output
paths: `Document.SaveAs` (extension-driven persisted formats),
`Document.ExportAsFixedFormat` (PDF / XPS), and
`Document.PrintOut` / `Page.Print` (printer spooler). Each is
documented below in terms of which `## canvas` fields it consumes
and which Visio cells it touches.

### 14.1 Print Properties section (page ShapeSheet)

Every page carries a Print Properties section in addition to the
canvas cells from §3. These cells govern margins, scaling, and
sheet-array layout when the page is printed. The Section/Row pair
is `(visSectionObject, visRowPrintProperties)` and the cell
indices are stable across Visio 2013 / 2016 / 2019 / 2021 / 365.

| Cell                | Index constant                              | Type    | Default  | Effect                                                                |
|---------------------|---------------------------------------------|---------|----------|-----------------------------------------------------------------------|
| `PrintFitOnPages`   | `visPrintPropertiesPrintFitOnPages` (`0`)   | Boolean | `FALSE`  | when `TRUE`, scaling honours `PrintOnPagesX/Y` instead of `PrintScale`|
| `PrintOnPagesX`     | `visPrintPropertiesOnPagesX` (`1`)          | Number  | `1`      | sheets across in the printer-sheet array                              |
| `PrintOnPagesY`     | `visPrintPropertiesOnPagesY` (`2`)          | Number  | `1`      | sheets down                                                           |
| `PrintCenteredH`    | `visPrintPropertiesCenterX` (`3`)           | Boolean | `FALSE`  | centre horizontally on each printer sheet                             |
| `PrintCenteredV`    | `visPrintPropertiesCenterY` (`4`)           | Boolean | `FALSE`  | centre vertically                                                     |
| `PrintScale`        | `visPrintPropertiesPrintScale`              | Number  | `1.0`    | active when `PrintFitOnPages = FALSE`; `1.0 = 100%`                   |
| `PageLeftMargin`    | `visPrintPropertiesLeftMargin`              | Length  | (driver) | physical printer margin                                              |
| `PageRightMargin`   | `visPrintPropertiesRightMargin`             | Length  | (driver) |                                                                       |
| `PageTopMargin`     | `visPrintPropertiesTopMargin`               | Length  | (driver) |                                                                       |
| `PageBottomMargin`  | `visPrintPropertiesBottomMargin`            | Length  | (driver) |                                                                       |
| `PaperKind`         | `visPrintPropertiesPaperKind` (`21`)        | Enum    | (preset) | `VisPaperSizes`; `0` = `visPaperCustom` honours W/H below             |
| `PaperWidth`        | `visPrintPropertiesPaperWidth`              | Length  | derived  | effective only when `PaperKind = visPaperCustom (0)`                  |
| `PaperHeight`       | `visPrintPropertiesPaperHeight`             | Length  | derived  |                                                                       |
| `PrintGrid`         | `visPrintPropertiesPrintGrid`               | Boolean | `FALSE`  | overlay the page grid on print output                                 |
| `PrintBackground`   | `visPrintPropertiesPrintBackground`         | Boolean | `TRUE`   | print the assigned background page                                    |
| `PrintFromPage`     | `visPrintPropertiesPrintFromPage`           | Number  | `1`      | default `From` for the Print dialog                                   |
| `PrintToPage`       | `visPrintPropertiesPrintToPage`             | Number  | n        | default `To`                                                          |

The print scaling interaction:

- `PrintFitOnPages = TRUE`, `PrintOnPagesX/Y = 1, 1` — fit single sheet.
- `PrintFitOnPages = TRUE`, `PrintOnPagesX/Y = 2, 1` — 2-wide × 1-tall poster.
- `PrintFitOnPages = FALSE` — render at `PrintScale` and tile.

`PrintCenteredH/V` only matter when the drawing is smaller than the
printer sheet array.

### 14.2 `VisPaperSizes` enumeration

The values written into `Print Properties.PaperKind` and the
PageSheet's `PaperKind` cell come from the Win32 `VisPaperSizes`
enumeration (~120 entries; relevant subset below). When `PaperKind`
is changed, Visio updates `PaperWidth` / `PaperHeight`
automatically; explicit `PaperWidth` / `PaperHeight` values are
honoured only when `PaperKind = visPaperCustom (0)`.

| Constant                  | Value | Sheet                | mm                |
|---------------------------|------:|----------------------|-------------------|
| `visPaperCustom`          |   `0` | Custom (uses W/H)    | n/a               |
| `visPaperLetter`          |   `1` | US Letter            | 215.9 × 279.4     |
| `visPaperTabloid`         |   `3` | US Tabloid (11 × 17) | 279.4 × 431.8     |
| `visPaperLegal`           |   `5` | US Legal             | 215.9 × 355.6     |
| `visPaperA3`              |   `8` | A3                   | 297 × 420         |
| `visPaperA4`              |   `9` | A4                   | 210 × 297         |
| `visPaperA5`              |  `11` | A5                   | 148 × 210         |
| `visPaperB4`              |  `12` | JIS B4               | 257 × 364         |
| `visPaperB5`              |  `13` | JIS B5               | 182 × 257         |
| `visPaper11x17`           |  `17` | 11 × 17              | 279.4 × 431.8     |
| `visPaperCSheet`          |  `24` | C-Size sheet         | 432 × 559         |
| `visPaperDSheet`          |  `25` | D-Size sheet         | 559 × 864         |
| `visPaperESheet`          |  `26` | E-Size sheet         | 864 × 1118        |
| `visPaperISOB4`           |  `42` | ISO B4               | 250 × 353         |

> Caution: `visPaperB4` (`12`) and `visPaperB5` (`13`) refer to
> **JIS B-series** sizes (257 × 364, 182 × 257), not ISO B. Use
> `visPaperISOB4` (`42`) for ISO B4. The visio-master `b*-*`
> presets (§2.2) declare ISO B sizes and therefore set
> `paper_kind: 42` for B4 and `paper_kind: 256` (custom) for the
> B0..B3, B5..B6 sizes that have no canonical Visio constant.

### 14.3 Mapping visio-master presets → `PaperKind` (canonical)

| Preset                    | `PaperKind` constant      | Value |
|---------------------------|---------------------------|------:|
| `letter-portrait`         | `visPaperLetter`          |   `1` |
| `letter-landscape`        | `visPaperLetter`          |   `1` |
| `legal-portrait`          | `visPaperLegal`           |   `5` |
| `tabloid-landscape`       | `visPaperTabloid`         |   `3` |
| `tabloid-portrait`        | `visPaper11x17`           |  `17` |
| `ansi-c-landscape`        | `visPaperCSheet`          |  `24` |
| `ansi-d-landscape`        | `visPaperDSheet`          |  `25` |
| `ansi-e-landscape`        | `visPaperESheet`          |  `26` |
| `a3-*`                    | `visPaperA3`              |   `8` |
| `a4-*`                    | `visPaperA4`              |   `9` |
| `a5-*`                    | `visPaperA5`              |  `11` |
| `b4-*`                    | `visPaperISOB4`           |  `42` |
| All `arch-*`              | `visPaperCustom`          |   `0` |
| `engineering-d-landscape` | `visPaperDSheet`          |  `25` |
| `engineering-e-landscape` | `visPaperESheet`          |  `26` |
| `metric-a1-engineering`   | `visPaperCustom`          |   `0` |
| `metric-a0-engineering`   | `visPaperCustom`          |   `0` |
| All `civil-*`             | `visPaperDSheet`/`ESheet` | `25`/`26` |
| All `whiteboard-*`        | `visPaperCustom`          |   `0` |
| All `slide-*`             | `visPaperCustom`          |   `0` |
| `custom`                  | `visPaperCustom`          |   `0` |

`A0`/`A1`/`A2` and `arch-*` resolve to `visPaperCustom` because
the canonical `VisPaperSizes` enum does not ship a stable A0/A1/A2
constant in every Visio SKU; declaring custom and supplying
`PaperWidth` / `PaperHeight` explicitly is more portable.

### 14.4 `Document.SaveAs` — extension-driven format selection

`Document.SaveAs(FileName)` rewrites the document under a new path.
There is no format argument; Visio inspects the extension and
maps to an internal format ID. An unrecognised extension raises
**error -2032466935 (Bad parameter)**.

| Extension | Internal ID | Friendly name              | Macros | OPC pkg |
|-----------|------------:|----------------------------|--------|---------|
| `.vsdx`   |        `51` | Visio Drawing              | no     | yes     |
| `.vsdm`   |        `52` | Visio Macro-Enabled Draw.  | yes    | yes     |
| `.vstx`   |        `54` | Visio Template             | no     | yes     |
| `.vstm`   |        `55` | Visio Macro-Enabled Tmpl.  | yes    | yes     |
| `.vssx`   |        `60` | Visio Stencil              | no     | yes     |
| `.vssm`   |        `61` | Visio Macro-Enabled Stnl.  | yes    | yes     |

`Document.SaveAsEx(FileName, Flags)` takes a `VisSaveAsFlags`
bitmask in addition: `visSaveAsRO = 1`, `visSaveAsWS = 2`,
`visSaveAsListInMRU = 4`, `visSaveAsCreateLocked = 8`,
`visSaveAsCreateUnlocked = 16`, `visSaveAsCustomDataExp = 64`.
For OPC formats (.vsdx, .vsdm, .vstx, .vstm, .vssx, .vssm) the
Workspace flag (`2`) is silently ignored.

`vsdx_export.py` always saves as `.vsdx` (ID `51`); the
`.vsdm` / `.vstx` / `.vstm` / `.vssx` / `.vssm` paths are
reserved for the `create-page-layout` and `create-theme`
workflows.

### 14.5 `Document.ExportAsFixedFormat` — PDF / XPS

PDF and XPS output go through `Document.ExportAsFixedFormat`
exclusively; this is the only supported path for scripted PDF
generation. The signature is:

```
Document.ExportAsFixedFormat(
    FixedFormat,                  ' VisFixedFormatTypes
    OutputFileName,               ' String
    Intent,                       ' VisDocExIntent
    PrintRange,                   ' VisPrintOutRange
    FromPage, ToPage,             ' Long, 1-based
    IncludeDocumentProperties,    ' Boolean
    IncludeDocumentStructureTags, ' Boolean
    Markup)                       ' VisDocExMarkup
```

Enum values:

| Argument enum         | Constant                      | Value | Meaning                                                  |
|-----------------------|-------------------------------|------:|----------------------------------------------------------|
| `VisFixedFormatTypes` | `visFixedFormatPDF`           |   `1` | PDF output                                               |
| `VisFixedFormatTypes` | `visFixedFormatXPS`           |   `2` | XPS output                                               |
| `VisDocExIntent`      | `visDocExIntentScreen`        |   `0` | smaller, screen-friendly raster for gradients            |
| `VisDocExIntent`      | `visDocExIntentPrint`         |   `1` | vector-preserved output for print / archive              |
| `VisPrintOutRange`    | `visPrintAll`                 |   `0` | every foreground page                                    |
| `VisPrintOutRange`    | `visPrintFromTo`              |   `1` | range from `FromPage` to `ToPage`                        |
| `VisPrintOutRange`    | `visPrintCurrentPage`         |   `2` | the active page only                                     |
| `VisPrintOutRange`    | `visPrintSelection`           |   `3` | the current selection                                    |
| `VisPrintOutRange`    | `visPrintCurrentView`         |   `4` | the current view rectangle                               |
| `VisDocExMarkup`      | `visDocExMarkupNone`          |   `0` | no comment markup                                        |
| `VisDocExMarkup`      | `visDocExMarkupInPlace`       |   `1` | inline comment markers                                   |
| `VisDocExMarkup`      | `visDocExMarkupInMargin`      |   `2` | margin comment list                                      |

Canvas-relevant behaviour:

- `ExportAsFixedFormat` honours `PageWidth` / `PageHeight`
  exactly. The produced PDF / XPS page size matches the canvas
  regardless of `PaperKind`. This is the recommended path for
  custom canvases (`visPaperCustom`) because no driver
  re-rounding occurs.
- `visDocExIntentPrint` preserves vector geometry; choose this
  for archival, pre-press, or accessibility (tagged-PDF) output.
- `visDocExIntentScreen` rasterises gradients and effects for a
  smaller file; choose this for thumbnails or web preview.
- `IncludeDocumentStructureTags = TRUE` produces tagged PDF (the
  PDF/UA prerequisite). Pair with `visDocExIntentPrint` —
  structure tags require the print rendering pipeline.
- Visio does **not** produce PDF/A directly. For PDF/A submission,
  fall back through the print path (§14.7) using a PDF/A-capable
  printer driver.

### 14.6 `Page.Export` — single-page raster / vector

`Page.Export(FileName)` writes one page to a raster or vector
file; the encoder is determined entirely by the destination
extension. Raster paths: `.png`, `.jpg`/`.jpeg`, `.gif`,
`.tif`/`.tiff`, `.bmp`/`.dib`. Vector paths: `.emf`, `.wmf`,
`.svg`, `.pdf` (Visio 2013+), `.dwg`/`.dxf` (CAD converter
required). Bundle: `.htm`/`.html`. Per-format quality knobs live
on `Application.Settings` and persist for the life of the
`Application` object.

For raster formats, the resolution / size pattern (replace `<F>`
with `PNG`, `JPG`, `GIF`, `TIFF`, or `BMP`):

- `<F>FileResolutionType` — `VisExportResolution` enum:
  `visResolutionTypeSourceResolution = 0`,
  `ScreenResolution = 1`, `PrinterResolution = 2`,
  `CustomResolution = 3`.
- `<F>FileResolutionX/Y` — DPI when `Type = 3`.
- `<F>ExportSizeType` — `VisExportSize` enum: `visExportSizeSource
  = 0`, `visExportSizeScreen = 1`, `visExportSizeCustom = 2`.
- `<F>FileSizeX/Y` — pixels when `SizeType = 2`.
- `<F>BackgroundColor` — RGB applied to transparent pixels for
  raster.

The `canvas.dpi` field maps to `PNGFileResolutionType = 3` plus
`PNGFileResolutionX/Y = canvas.dpi`. Set on
`Application.Settings` immediately before each `Export` call.

SVG-specific knobs: `SVGExportEmbedFonts` (`True` embeds glyph
outlines), `SVGExportPreciseGeometry` (`True` emits raw
`Geometry` paths), `SVGExportStyleAsAttribute` (`True` writes
inline style attributes; `False` uses `<style>` blocks). The SVG
viewport is set from the page rectangle: `viewBox = "0 0 W H"`
with `preserveAspectRatio = "xMidYMid meet"`.

### 14.7 `Document.PrintOut` and the spooler path

```
Document.PrintOut(PrintRange, FromPage, ToPage,
                   Copies, Collate, Activate,
                   PrintToFile, PrintFile)
```

`Page.Print()` is shorthand for `PrintOut(visPrintCurrentPage,
ThePage, ThePage, 1, FALSE, FALSE, FALSE, "")`.
`Application.ActivePrinter` is read/write `String`. The print
path requires a logged-on interactive session — running Visio
under `LocalSystem` is unsupported.

The "Microsoft Print to PDF" virtual printer is the canonical
fallback when `ExportAsFixedFormat` is unreachable (e.g. Visio
Standard SKU):

```vb
previousPrinter = Application.ActivePrinter
Application.ActivePrinter = "Microsoft Print to PDF"
' Set Print Properties.PrintFitOnPages, OnPagesX/Y, CenterX/Y
doc.PrintOut visPrintAll, 0, 0, 1, True, True, True, pdfPath
Application.ActivePrinter = previousPrinter
```

`vsdx_export.py` selects this path automatically when
`--force-com` is not set and the SKU lacks
`ExportAsFixedFormat`.

### 14.8 PDF / preview / embed pathway summary

| Use case                                  | Path                                                                  |
|-------------------------------------------|-----------------------------------------------------------------------|
| Web preview / thumbnail                   | `ExportAsFixedFormat` + `visDocExIntentScreen`                        |
| Archival / pre-press                      | `ExportAsFixedFormat` + `visDocExIntentPrint`                         |
| Tagged PDF for accessibility              | `ExportAsFixedFormat` + `visDocExIntentPrint` + `IncludeDocumentStructureTags = TRUE` |
| PDF/A submission                          | "Microsoft Print to PDF" + post-convert with Acrobat                  |
| Visio Standard SKU (no fixed-format)      | "Microsoft Print to PDF" via `Document.PrintOut`                      |
| Live preview server                       | `Page.Export` to PNG at `canvas.dpi` (caps at 96 dpi above 50 MP)     |
| PowerPoint embed                          | `Page.Export` to PNG at slide pixel dimensions                        |

For PowerPoint embeds, declare a canvas whose aspect matches the
slide aspect (`slide-16x9` for ppt169, `slide-4x3` for ppt43);
mismatched aspects cause letter-boxing or pillar-boxing in the
embedded PNG.

For print-bound drawings (`canvas.dpi >= 150`), prefer
`size_type: standard` (`DrawingSizeType = 2`) with a recognised
`paper_kind`. The COM export path passes the paper-kind to the
print spooler verbatim, which gives the most predictable output.

The fallback writer's PDF path uses LibreOffice's `soffice
--headless --convert-to pdf`, which uses `paper_kind` as the
page-size hint and may round to the nearest standard size; the
fallback path warns when `paper_kind: 256` (custom) is declared.

### 14.9 Common export error codes

| HRESULT                              | Cause                                                                                       |
|--------------------------------------|---------------------------------------------------------------------------------------------|
| `-2032466935` (Bad parameter)        | Unrecognised extension on `SaveAs`, or invalid `FixedFormat` on `ExportAsFixedFormat`       |
| `-2032465884` (File access denied)   | Output path locked; close any reader (Acrobat, Edge) before retrying                        |
| `-2032465750` (No active printer)    | `Application.ActivePrinter` blank in headless service; ensure spooler is running            |
| `-2032465719` (Printer driver error) | `PaperKind` mismatch with driver; fall back to `visPaperLetter` or `visPaperA4`             |
| `-2032465647` (Document is read-only)| Trying to `SaveAs` a document opened with `visOpenRO`; reopen with `0`                      |

## 15. Inputs flowing from Confirmation 1 to downstream phases

Every field in `## canvas` flows to one or more downstream
consumers via the lock — there is no side channel.

| Consumer                       | Fields used                          | Purpose                                            |
|--------------------------------|--------------------------------------|----------------------------------------------------|
| Drafter                        | every field                          | writes `<PageSheet>` cells per §3                  |
| Stylist                        | `format` + `units`                   | scales theme strokes / shadows                     |
| `connectors.md` routing        | `units`                              | resolves spacing defaults                          |
| `diagram-layout-patterns.md`   | `format` + `margin.*`                | computes lane / band / grid widths                 |
| `vsdx_export.py` (COM)         | `format` + `paper_kind`              | calls `Documents.AddEx`                            |
| `vsdx_export.py` (fallback)    | `width` / `height` / `units`         | writes raw `pages.xml`                             |
| `vsdx_preview` server          | `width` / `height` / `dpi`           | renders preview PNG                                |
| `vsdx_quality_checker.py`      | every field                          | enforces §13 rules                                 |
| `update_diagram_lock.py`       | (read-only)                          | rejects mutations after pages exist                |

## 16. Anti-patterns

The following are rejected at the Architect or quality-checker
gate:

1. **Custom canvas of 297 × 210 mm** — that is `a4-landscape`.
   Use the named preset; only the named preset triggers
   `vsdx_export.py` COM template seeding.
2. **Canvas in pixels** — Visio is a physical-page tool. Pixel
   canvases are encoded as inches at 96 dpi via the
   `whiteboard-*` / `slide-*` presets; raw pixel values in
   `canvas.width` / `canvas.height` are an error.
3. **Different canvas per page without `mixing_allowed`** —
   warning. If genuinely needed, set `mixing_allowed: true` and
   `default_format: <preset>` at the top of `diagram_lock.md`,
   with per-page overrides under `page_layouts.P<NN>.canvas`.
4. **Set page size after writing shapes** — coordinates do not
   re-fit. If the canvas must change post-Drafter, the affected
   pages re-author from scratch.
5. **Custom DPI of 600 for whiteboard** — the preview server
   degrades above 50 MP. Print at 600 dpi by all means, but record
   the preview DPI separately if it matters.
6. **Use `visSizeSame` for print** — only valid when the printer
   paper exactly matches the canvas. For most office workflows,
   `visSizeStandard` (`2`) is the safe default.
7. **Skip the title block on engineering canvases** — engineering
   deliverables without a title block fail contract review at
   every AEC firm. The right-margin strip in §5.2 is non-negotiable
   for `arch-*` / `engineering-*` / `civil-*` presets.

## 17. Format selection decision tree

Architect's recommendation engine traverses this tree top-down,
returning the first match; the user always overrides during
Confirmation 1.

| Deliverable category                  | Recommended preset                                              |
|---------------------------------------|------------------------------------------------------------------|
| Floor plan (US AEC)                   | `arch-d-landscape`                                               |
| Floor plan (metric)                   | `metric-a1-engineering`                                          |
| Site plan (US)                        | `arch-e-landscape` or `civil-e-landscape`                        |
| Site plan (metric)                    | `metric-a0-engineering`                                          |
| PFD / P&ID (US)                       | `engineering-e-landscape`                                        |
| PFD / P&ID (metric)                   | `metric-a0-engineering`                                          |
| HVAC / Electrical / Security plan     | `metric-a1-engineering` (metric) / `arch-d-landscape` (US)       |
| Flowchart                             | `a4-landscape` (metric) / `letter-portrait` (US)                 |
| Swim-lane / BPMN                      | `a3-landscape` (metric) / `tabloid-landscape` (US)               |
| Org chart                             | `a3-landscape` (wide) / `a3-portrait` (deep)                     |
| Mind map                              | `a3-portrait` or `square-poster`                                 |
| Timeline                              | `wide-poster` or `a3-landscape`                                  |
| Quadrant / Venn / 2x2                 | `a4-landscape` or `square-poster`                                |
| Small network (≤ 30 nodes)            | `a3-landscape`                                                   |
| Mid topology (30–80 nodes)            | `a2-landscape`                                                   |
| Full enterprise topology (> 80 nodes) | `a1-landscape`                                                   |
| Rack diagram                          | `a3-landscape`                                                   |
| AWS / Azure architecture              | `a3-landscape`                                                   |
| Detailed network as-built             | `ansi-d-landscape`                                               |
| UML class / sequence / state          | `a3-landscape`                                                   |
| ERD (small / large)                   | `a3-landscape` / `tabloid-landscape`                             |
| Component / deployment diagram        | `a3-landscape`                                                   |
| Digital whiteboard                    | `whiteboard-1080p`                                               |
| 4K kiosk / facilitator board          | `whiteboard-4k`                                                  |
| Conference banner                     | `wide-poster`                                                    |
| Lobby retractable banner              | `vertical-banner`                                                |
| Hub-and-spoke poster                  | `square-poster`                                                  |
| 16:9 slide embed                      | `slide-16x9`                                                     |
| 4:3 slide embed                       | `slide-4x3`                                                      |

## 18. Canvas-related cells beyond the PageSheet

A handful of supporting cells live on the `DocumentSheet`
(`Document` ShapeSheet) rather than on the PageSheet:

| DocumentSheet cell    | Default      | Effect                                          |
|-----------------------|--------------|-------------------------------------------------|
| `OrgChartAutoSize`    | `FALSE`      | (Org Chart) auto-fit canvas to roster           |
| `MeasurementUnits`    | `4` mm / `0` in | locale-default measurement system            |
| `PageColor`           | `#FFFFFF`    | global page background colour (Stylist-owned)   |
| `PrintMargin.X`/`Y`   | `0.25 in`    | applied at print time, not at draw time         |
| `OutputFormat`        | `2`          | default `Document.ExportAsFixedFormat` target   |
| `AvenueSizeX` / `Y`   | `0.375 in`   | grid spacing for `Layout` add-on (auto-route)   |
| `BlockSizeX` / `Y`    | `0.375 in`   | block size for `Layout` add-on                  |

The `Avenue` and `Block` sizes are read by the auto-layout
subsystem documented in `diagram-layout-patterns.md`. All other
cells are inherited from the chosen built-in template;
visio-master rarely overrides them.

## 19. Round-trip stability

The fields in `## canvas` round-trip cleanly between
`diagram_lock.md` and `pages.xml` IF and ONLY IF:

- `width` / `height` are stored to at least four decimal places
  (the inch value).
- `paper_kind` is one of the canonical DMPAPER values OR
  `256+` for custom.
- `units` is `mm` or `in` only.

`scripts/vsdx_export/opc_writer.py` enforces these constraints
when writing the OPC zip; if any field is malformed, export
aborts with a clear error and points the user back to
Architect.

When reading an existing `.vsdx` (the `import-existing-vsdx`
workflow), `scripts/source_to_md/vsdx_to_md.py` reconstructs the
`## canvas` block by reading the PageSheet's eight key cells. If
the input file uses a `paper_kind` outside the canonical set,
the importer maps to `custom` and records the original
`paper_kind` in a comment so future round-trips preserve it.

## 20. Quick crib

- Defaults to A4 (metric) / Letter (US) for flowcharts.
- Defaults to A3 (metric) / Tabloid (US) for swim-lane, BPMN,
  network, AWS/Azure, UML, ERD.
- Defaults to A1 (metric) / ANSI D (US) for floor plans.
- Defaults to A0 (metric) / ANSI E (US) for site plans, PFDs,
  P&IDs.
- Use `slide-16x9` when the drawing is destined for a PPTX.
- Use `whiteboard-1080p` when the drawing lives on a TV.
- Custom canvases declare `paper_kind: 256` and `size_type:
  custom`.
- Engineering canvases ship a title block; the right-margin
  strip in §5.2 is part of the canvas, not optional.
- Mixed-canvas drawings need explicit `mixing_allowed: true`;
  default is one canvas per drawing.
- The catalog is frozen once the first Visio Page is emitted —
  `update_diagram_lock.py` will not change it.

## Sources

This reference is derived from the following input files:

- `D:/Pe/Project/python/workProject/visio-master—builder/_BLUEPRINT.md`
  — Confirmation 1 field schema (§4 of the blueprint), discipline
  rules around lock immutability (§7.1 rule 8), and the canvas
  preset enumeration.
- `D:/Pe/Project/python/workProject/visio-master—builder/research/12-builtin-templates-catalog.md`
  — built-in Visio template page sizes, `DrawingScale` /
  `DrawingScaleType` / `RouteStyle` defaults per template, the
  short-name table mapped in §12 above, and the
  `GetBuiltInStencilFile` integration notes.
- `D:/Pe/Project/python/workProject/visio-master—builder/research/16-floorplan-engineering-family.md`
  — floor-plan / engineering / civil canvas defaults, the
  `DrawingScaleType` enumeration values, the `1:50` / `1:100` /
  `1/4 in : 1 ft` scale conventions, and the title-block-strip
  recommendation underpinning §5.2.
- `D:/Pe/Project/python/workProject/visio-master—builder/research/23-export-print.md`
  — `Document.SaveAs` extension/ID matrix (§14.4), the
  `Document.ExportAsFixedFormat` signature with
  `VisFixedFormatTypes` / `VisDocExIntent` / `VisPrintOutRange` /
  `VisDocExMarkup` enumerations (§14.5), the Print Properties
  section cells and indices (§14.1), the
  `VisPaperSizes` enumeration values mapped to visio-master
  presets in §14.2 and §14.3, the `Page.Export` resolution /
  size settings in `Application.Settings` (§14.6), the
  `Document.PrintOut` signature and "Microsoft Print to PDF"
  fallback pattern (§14.7), and the export-error HRESULT table
  in §14.9.
