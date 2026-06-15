# `templates/diagrams/` — Diagram Recipe Library

> Per-diagram-type build recipes for the visio-master builder. One
> directory per diagram, each holding a small `recipe.json`
> (masters-to-drop, connector defaults, layout cells) and an optional
> `starter.vsdx` blank document. The flat `diagrams_index.json` next
> to this README is the single source of truth that the builder, the
> `diagram_index.py` CLI, and downstream codegen read first.

---

## 1. What lives here

```
visio-master/templates/diagrams/
├── README.md                       # this file (catalog prose)
├── diagrams_index.json             # flat list — 59 diagram entries
├── basic-flowchart/
│   ├── recipe.json                 # masters, connector, layout
│   └── starter.vsdx                # optional blank A4 page
├── cross-functional-flowchart/
│   ├── recipe.json
│   └── starter.vsdx
├── bpmn-2-0/
│   ├── recipe.json
│   └── starter.vsdx
├── org-chart/
│   └── recipe.json                 # COM-only; no starter
├── uml-class/
│   ├── recipe.json
│   └── starter.vsdx
├── … (one folder per diagram id, 59 total)
└── _shared/
    ├── connectors.json             # global Dynamic-connector defaults
    └── canvas-presets.json         # paper × scale × units presets
```

The folder names are exactly the `id` field from `diagrams_index.json`
(kebab-case, stable across releases). Builders look up a diagram by
`id`, resolve `templates/diagrams/<id>/recipe.json`, and apply it on
top of the resolved Visio template.

---

## 2. Two layers of metadata

| Layer | File | Purpose | Audience |
| --- | --- | --- | --- |
| Catalog | `diagrams_index.json` | Flat list of all 59 diagrams with id, family, template short-name, built-in stencil enum, primary stencils, canvas, route/place style, theme, validation rule set, key masters, key user cells, add-ons, description. Schema mirrors `references/diagram-types.md`. | `scripts/diagram_index.py`, codegen, docs site, scaffolders |
| Recipe | `<id>/recipe.json` | Concrete build steps: which masters to drop where, which connector master to use, which page-sheet cells to set, how to invoke the family add-on. | `scripts/vsdx_build.py`, scaffold `build.py` |

The catalog answers "what diagrams exist?" The recipe answers "given
diagram X, how do I produce a starter page?" Keeping the two layers
separate lets us version recipes without touching the index, and lets
documentation generators consume the index without parsing 59 recipes.

---

## 3. `diagrams_index.json` schema

Top-level shape:

```json
{
  "schema_version": "1.0",
  "diagrams": [
    { "id": "basic-flowchart", "family": "flowchart", ... },
    { "id": "bpmn-2-0",        "family": "flowchart", ... }
  ]
}
```

A bare list is also accepted by `diagram_index.py.load_index()` for
backward compatibility, but new code emits the wrapped form so the
schema version is discoverable.

Per-entry keys (all required unless marked optional). See
`references/diagram-types.md §0` for the canonical spec.

| Key | Type | Description |
| --- | --- | --- |
| `id` | string | Kebab-case stable id, also the recipe folder name. |
| `display_name` | string | en-US label shown in Visio's File → New gallery. |
| `family` | string | One of `flowchart`, `brainstorm`, `org`, `network`, `network/cloud`, `software`, `software/db`, `engineering`, `floorplan`, `schedule`, `business`. |
| `template` | string \| null | `_M.VSTX` short name passed to `Documents.AddEx`. `null` when no MS-shipped template exists (community stencil only). |
| `workspace_id` | string \| null | `Microsoft.Visio.<Family>Template` workspace tag. |
| `built_in_stencil_enum` | int \| null | `VisBuiltInStencilTypes` constant for `Application.GetBuiltInStencilFile`. |
| `primary_stencils` | string[] | Docked `_M.VSSX` files the template auto-loads. |
| `canvas` | object | `{paper, orientation, scale, units}`; see §3.1 below. |
| `route_style` | int | `Page.PageSheet.RouteStyle` default (0..10). |
| `place_style` | int | `Page.PageSheet.PlaceStyle` default (0..5). |
| `theme` | object | `{base, variant}`; `base` is one of `Office`, `Slate`, `Whisp`, `Linear`, `Integral`, `Daybreak`, `Parallel`, `Sequence`, `Azure`. `variant` is 1..4. |
| `validation_rule_set` | string \| null | `Document.Validation.RuleSets.ItemU(<name>)` name. |
| `key_masters` | string[] | Top-of-mind `Master.NameU` identifiers used by codegen factories. |
| `key_user_cells` | string[] | Polymorphism / data cells the builder must populate. |
| `add_ons` | string[] | `Application.Addons.ItemU(<name>)` entries that fire on `EventDrop` / `EventXFMod`. |
| `description` | string | One-line semantic description. |

### 3.1 `canvas` sub-schema

```json
{
  "paper":       "A3",
  "orientation": "landscape",
  "scale":       "1:1",
  "units":       "mm"
}
```

| Field | Allowed values |
| --- | --- |
| `paper` | `A0`, `A1`, `A2`, `A3`, `A4`, `Letter`, `Tabloid`, `ANSI B`, `ANSI C`, `ANSI D`, `ANSI E` |
| `orientation` | `portrait`, `landscape` |
| `scale` | `1:1`, `1:50`, `1:200`, `1 in : 1 ft`, `1 in : 20 ft`, `1/4 in : 1 ft`, `1 ft`, free-form scale string consumed by `DrawingScale` |
| `units` | `mm`, `in`, `ft` |

US-locale equivalents (`Letter`, `Tabloid`, `ANSI B/C/D/E`) are
documented in `references/diagram-types.md` and resolved from
`canvas-presets.json` when `Application.MeasurementSystem ==
visMSUS=2`.

---

## 4. `recipe.json` schema

Each diagram folder ships exactly one `recipe.json`. The schema is
intentionally narrow so simple diagrams stay simple; the build CLI
reads only the keys it needs and ignores extras.

```json
{
  "id": "basic-flowchart",
  "version": "1.0",
  "extends": "_shared/connectors.json",
  "page_cells": {
    "RouteStyle":     "4",
    "PlaceStyle":     "1",
    "LineJumpStyle":  "1",
    "AvenueSizeX":    "0.375 in",
    "AvenueSizeY":    "0.375 in"
  },
  "stencils": [
    "BASFLO_M.VSSX",
    "CONNEC_M.VSSX"
  ],
  "drops": [
    { "id": "n1", "master": "Terminator",       "x": "1.0 in", "y": "10.0 in", "text": "Start" },
    { "id": "n2", "master": "Process",          "x": "1.0 in", "y":  "8.5 in", "text": "Step 1" },
    { "id": "n3", "master": "Decision",         "x": "1.0 in", "y":  "7.0 in", "text": "OK?"   },
    { "id": "n4", "master": "Process",          "x": "3.0 in", "y":  "7.0 in", "text": "Retry" },
    { "id": "n5", "master": "Terminator",       "x": "1.0 in", "y":  "5.5 in", "text": "End"   }
  ],
  "connectors": [
    { "from": "n1", "to": "n2", "master": "Dynamic connector" },
    { "from": "n2", "to": "n3", "master": "Dynamic connector" },
    { "from": "n3", "to": "n4", "master": "Dynamic connector", "label": "No"  },
    { "from": "n3", "to": "n5", "master": "Dynamic connector", "label": "Yes" }
  ],
  "addons": [
    { "name": "Layout", "args": "" }
  ],
  "validation": {
    "rule_set": "Flowchart",
    "enabled":  true
  },
  "starter": "starter.vsdx"
}
```

Top-level keys:

| Key | Required | Description |
| --- | --- | --- |
| `id` | yes | Must equal the parent folder name and the catalog `id`. |
| `version` | yes | Recipe schema version. Bump on breaking change. |
| `extends` | no | Relative path to a recipe fragment merged before local keys (typical: `_shared/connectors.json`). |
| `page_cells` | no | Map of `Page.PageSheet` cell name → `FormulaU` string. Builder writes via `CellsU(name).FormulaU = value`. |
| `stencils` | yes | Stencil short-names docked before any drop. Resolved against `Application.TemplatePaths`, then `templates/stencils/`. |
| `drops` | yes | Ordered list of master drops; coordinates are page-space strings honoured by `Page.Drop`. `text`, if present, is written via `Shape.Text`; for UML/BPMN use `props` instead so polymorphism is preserved. |
| `connectors` | no | List of edges. `master` defaults to `Dynamic connector` when omitted. `label` populates `Shape.Text` on the connector midpoint. |
| `addons` | no | Visio add-ons to invoke via `Application.Addons.ItemU(name).Run(args)` after the page is drawn. |
| `validation` | no | Activates the named `RuleSet` and runs `Document.Validation.ValidateAll()`. |
| `starter` | no | Sibling `.vsdx` filename. When present, the builder opens this instead of `Documents.AddEx(template, …)` and skips the `stencils` dock step. |

### 4.1 `drops[]` per-entry shape

| Key | Required | Notes |
| --- | --- | --- |
| `id` | yes | Local handle referenced by `connectors[].from` / `connectors[].to`. |
| `master` | yes | `Master.NameU` resolved from any docked stencil. |
| `x`, `y` | yes | Page-space coordinates. Strings let recipes mix units (`"2 in"`, `"50 mm"`); the builder defers parsing to `CellsU("PinX").FormulaU`. |
| `width`, `height` | no | Override master defaults; unset means use master geometry. |
| `text` | no | Plain `Shape.Text`. Avoid for UML/BPMN/ERD — use `props` so visibility-glyph formulas keep working. |
| `props` | no | Map of `Prop.<name>` → value. Builder writes via `CellsU("Prop." + key).FormulaU`. |
| `user_cells` | no | Map of `User.<name>` → value. Same write path as `props` with the `User.` prefix. |
| `container` | no | Local id of a container drop this shape becomes a member of (`ContainerProperties.AddMember`). |

### 4.2 `connectors[]` per-entry shape

| Key | Required | Notes |
| --- | --- | --- |
| `from` / `to` | yes | Local `drops[].id` values. Builder glues `BeginX` → source `PinX`, `EndX` → target `PinX`. |
| `master` | no | Default `Dynamic connector`. BPMN uses `Sequence flow` / `Message flow`; UML class uses typed connectors (`Generalization`, `Composition`, …). |
| `label` | no | Midpoint text. |
| `route_style` | no | Per-connector override of the page default. |
| `line_pattern` | no | Integer `LinePattern` (e.g. `2` for dashed `Measures`). |
| `props` | no | Connector-level shape data. |

---

## 5. Diagram catalog (59 entries)

All entries below are valid `id` values. Each has a sibling folder
`templates/diagrams/<id>/` containing `recipe.json`. Built-in enum
values come from `VisBuiltInStencilTypes`; rule-set names match
`Document.Validation.RuleSets`. The full row data (key masters, user
cells, add-ons) is in `diagrams_index.json` and mirrored in
`references/diagram-types.md`.

### 5.1 Flowchart family (6)

| id | template | built-in enum | rule set |
| --- | --- | --- | --- |
| `basic-flowchart` | `BASFLO_M` | `visBuiltInStencilFlowchart=0` | `Flowchart` |
| `cross-functional-flowchart` | `CROSSFUNC_M` | `visBuiltInStencilCrossFunctionalFlowchart=1` | `Cross-Functional Flowchart` |
| `workflow-diagram` | `WORKFL_M` | — | — |
| `bpmn-2-0` | `BPMN_M` | `visBuiltInStencilBPMN=26` | `BPMN 2.0 Diagram` |
| `epc` | `EPC_M` | — | — |
| `audit-diagram` | `AUDIT_M` | — | — |

### 5.2 Brainstorming family (2)

| id | template | built-in enum |
| --- | --- | --- |
| `brainstorming` | `BRSTRM_M` | `visBuiltInStencilBrainstorming=14` |
| `mind-map` | `MINDMAP_M` (fallback `BRSTRM_M`) | — |

### 5.3 Org-chart family (1)

| id | template | built-in enum |
| --- | --- | --- |
| `org-chart` | `ORGCH_M` | `visBuiltInStencilOrgChart=11` |

### 5.4 Network / cloud family (8)

| id | template | built-in enum |
| --- | --- | --- |
| `basic-network` | `NETBAS_M` | `visBuiltInStencilBasicNetwork=70` |
| `detailed-network` | `NETDET_M` | — |
| `rack-diagram` | `RACK_M` | `visBuiltInStencilRack=42` |
| `active-directory` | `ACTDIR_M` | — |
| `aws-architecture` | `AWS_M` | — |
| `azure-architecture` | `AZURE_M` | — |
| `gcp-architecture` | — (community `.vssx`) | — |
| `cisco-network` | — (Cisco distribution) | — |

### 5.5 Software family (13)

| id | template | built-in enum |
| --- | --- | --- |
| `uml-class` | `UMLCLS_M` | `visBuiltInStencilUMLClass=7` |
| `uml-sequence` | `UMLSEQ_M` | `visBuiltInStencilUMLSequence=8` |
| `uml-activity` | `UMLACT_M` | `visBuiltInStencilUMLActivity=9` |
| `uml-use-case` | `UMLUSE_M` | `visBuiltInStencilUMLUseCase=10` |
| `uml-state-machine` | `UMLSM_M` | `visBuiltInStencilUMLStatechart=12` |
| `uml-component` | `UMLCMP_M` | `visBuiltInStencilUMLComponent=13` |
| `uml-deployment` | `UMLDEP_M` | `visBuiltInStencilUMLDeployment=14` |
| `uml-object` | `UMLOBJ_M` | — |
| `uml-communication` | `UMLCOMM_M` | — |
| `uml-package` | `UMLPKG_M` | — |
| `uml-profile` | `UMLPROF_M` | — |
| `dfd` | `DATAFL_M` | — |
| `erd` | `DBMOD_M` | — |

### 5.6 Engineering family (6)

| id | template | built-in enum | rule set |
| --- | --- | --- | --- |
| `basic-electrical` | `BAELEC_M` | `visBuiltInStencilBasicElectrical=70` | — |
| `logic-gate` | `LOGIC_M` | `visBuiltInStencilLogicGate=80` | — |
| `pfd` | `PFD_M` | — | — |
| `pid` | `PID_M` | — | `Piping and Instrumentation` |
| `hvac` | `HVAC_M` | — | — |
| `plumbing` | `PLMBPL_M` | — | — |

### 5.7 Floor-plan family (8)

| id | template |
| --- | --- |
| `floor-plan` | `FLRPLN_M` |
| `office-layout` | `OFFLAY_M` |
| `home-plan` | `HOMEPLN_M` |
| `site-plan` | `SITPLN_M` |
| `reflected-ceiling-plan` | `RFLPLN_M` |
| `electrical-telecom-plan` | `ELECPL_M` |
| `plant-layout` | `PLAYOUT_M` |
| `security-access-plan` | `SECPLN_M` |

### 5.8 Schedule family (4)

| id | template | built-in enum |
| --- | --- | --- |
| `calendar` | `CALEND_M` | `visBuiltInStencilCalendar=27` |
| `gantt-chart` | `GANTT_M` | `visBuiltInStencilGantt=15` |
| `pert-chart` | `PERT_M` | `visBuiltInStencilPERT=70` |
| `timeline` | `TIMELINE_M` | `visBuiltInStencilTimeline=28` |

### 5.9 Business family (12)

| id | template | built-in enum |
| --- | --- | --- |
| `swot` | `SWOT_M` (or `MARKETC_M`) | — |
| `balanced-scorecard` | `BSC_M` | — |
| `strategy-map` | `STRATEGY_M` | — |
| `marketing-charts` | `MARKETC_M` | `visBuiltInStencilMarketing=66` |
| `itil-diagram` | `ITIL_M` | — |
| `six-sigma` | `SIXSIG_M` | — |
| `cause-effect-fishbone` | `CAUSEEFF_M` | — |
| `value-stream-map` | `LEAN_M` | `visBuiltInStencilLeanShapes=98` |
| `tqm` | `TQM_M` | `visBuiltInStencilTQM=68` |
| `fmea-grid` | sub-template of `SIXSIG_M` | — |
| `sipoc` | sub-template of `SIXSIG_M` | — |
| `functional-block-diagram` | `BLOCK_M` | — |

**Total: 59 diagrams**, matching the `Total: 59 diagram types`
summary in `references/diagram-types.md §15`.

---

## 6. How the builder consumes this folder

```text
build request: id="bpmn-2-0"
  │
  ▼
1. scripts/diagram_index.py  → load diagrams_index.json
                              → find_diagram("bpmn-2-0")
  │
  ▼
2. scripts/vsdx_build.py     → read templates/diagrams/bpmn-2-0/recipe.json
                              → if recipe.starter present:
                                    open templates/diagrams/bpmn-2-0/starter.vsdx
                                else:
                                    Documents.AddEx(catalog.template, …)
                                    Documents.OpenEx(s, visOpenHidden|RO|Docked)
                                       for s in recipe.stencils
  │
  ▼
3.   for cell, formula in recipe.page_cells.items():
        page.PageSheet.CellsU(cell).FormulaU = formula
     for d in recipe.drops:
        s = page.Drop(masters[d.master], parse(d.x), parse(d.y))
        for k, v in (d.props or {}).items():
            s.CellsU("Prop." + k).FormulaU = v
        for k, v in (d.user_cells or {}).items():
            s.CellsU("User." + k).FormulaU = v
     for c in recipe.connectors:
        wire = page.Drop(masters[c.master or "Dynamic connector"], 0, 0)
        wire.CellsU("BeginX").GlueTo(drops[c.from].CellsU("PinX"))
        wire.CellsU("EndX").GlueTo(drops[c.to].CellsU("PinX"))
        if c.label: wire.Text = c.label
     for a in recipe.addons:
        Application.Addons.ItemU(a.name).Run(a.args)
     if recipe.validation and recipe.validation.enabled:
        rs = doc.Validation.RuleSets.ItemU(recipe.validation.rule_set)
        rs.Enabled = True
        doc.Validation.ValidateAll()
  │
  ▼
4. Page.Layout()              # only when recipe.page_cells set RouteStyle/PlaceStyle
  │
  ▼
5. doc.SaveAs(out_path)
```

The same flow runs against the `vsdx` package fallback when Visio
COM is unavailable — `recipe.starter` is opened as a zip, drops are
appended to `pages/page1.xml`, and the file is re-zipped.

---

## 7. Authoring conventions

1. **Recipe folder name = `id` value.** Lower-kebab-case. No
   spaces, no underscores, no version suffixes.
2. **One recipe per id.** Variants (e.g. portrait vs landscape)
   live as `recipe.json` keys, not separate folders.
3. **Coordinates are strings with units.** Builders forward them to
   `CellsU.FormulaU` verbatim, so `"2 in"` and `"50 mm"` both work.
   Avoid bare numbers — the unit is template-default-dependent.
4. **Use `props` / `user_cells`, not `text`, for polymorphic
   shapes.** UML, BPMN, ERD, P&ID rely on `Geometry.NoShow`
   formulas reading `Prop.<…>` / `User.<…>`. Editing `Shape.Text`
   strips the formula linkage (see `references/diagram-types.md
   §6`).
5. **Reference real master names.** `key_masters` in
   `diagrams_index.json` is the authoritative list. CI rejects
   recipes whose `drops[].master` is not present in any
   `primary_stencils` entry of the same diagram.
6. **Connectors default to `Dynamic connector`.** Override with
   `master` only when the diagram requires a typed line (BPMN
   `Sequence flow`, UML `Generalization`, P&ID `Major pipeline`,
   Strategy Map `Cause-effect arrow`).
7. **Starter `.vsdx` files are optional and frozen.** Generate
   them once via the COM build path, then commit them. They exist
   so the file-mode (`vsdx`) fallback can produce a result without
   a running Visio install.
8. **No comments inside `recipe.json`.** It is strict JSON. Put
   prose in this README or in a sibling `NOTES.md`.

---

## 8. Adding a new diagram

```bash
# 1. Add a row to diagrams_index.json (alphabetical within family)
#    fields: id, display_name, family, template, …, description.

# 2. Scaffold a starter project.
python visio-master/scripts/diagram_index.py scaffold \
       <new-id> visio-master/templates/diagrams/<new-id>

# 3. Replace the generated build.py with a recipe.json (same shape
#    as §4). Keep diagram_meta.json as a debugging snapshot.

# 4. Optional: open Visio once, drop the masters by hand, save as
#    starter.vsdx so the file-mode fallback has somewhere to begin.

# 5. Verify.
python visio-master/scripts/diagram_index.py query <new-id>
python visio-master/scripts/vsdx_build.py --diagram <new-id> --out /tmp/x.vsdx
```

CI runs `diagram_index.py list --json | jq '.diagrams | length'` and
fails when the number drifts away from the catalog summary in
`references/diagram-types.md §15`. Bump that summary in the same
commit when the count legitimately changes.

---

## 9. Cross-references

| Concern | Authoritative source |
| --- | --- |
| Per-diagram master / cell / add-on details | `visio-master/references/diagram-types.md` |
| Page-cell semantics (`RouteStyle`, `PlaceStyle`, `LineJumpStyle`) | `visio-master/references/connector-routing.md`, `references/shapesheet-quick-ref.md` |
| Paper / scale / units presets | `visio-master/references/canvas-formats.md`, `_shared/canvas-presets.json` |
| Theme catalog | `visio-master/templates/themes/themes_index.json`, `templates/themes/README.md` |
| Stencil discovery | `visio-master/templates/stencils/`, `scripts/stencil_index.py` |
| Catalog CLI | `visio-master/scripts/diagram_index.py` (`list`, `query`, `scaffold`) |
| Build runner | `visio-master/scripts/vsdx_build.py` |
| Workflow shells | `visio-master/workflows/verify-diagrams.md` |

The Visio object-model cells named in this README (`PageSheet`,
`CellsU`, `Documents.AddEx`, `Documents.OpenEx`, `Page.Drop`,
`Page.Layout`, `Document.Validation.RuleSets`, `Application.Addons`)
are documented in `references/com-quick-ref.md` with full method
signatures.
