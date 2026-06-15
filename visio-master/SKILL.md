---
name: visio-master
description: >
  Visio diagram generation system. Converts source documents (PDF/DOCX/XLSX/CSV/Markdown/conversation)
  into Visio .vsdx files (flowcharts, BPMN, UML, ERD, network/cloud architecture, org charts, floor plans,
  business diagrams, Gantt/timeline) through Architect → Drafter → Stylist multi-role pipeline. Use when
  user asks to "create a Visio diagram", "make a flowchart", "draw a BPMN", "做流程图", "做 Visio",
  or mentions "visio-master".
license: MIT
compatibility: >
  Primary: Windows + Visio 2019/2021/Plan 2 (COM automation via pywin32). Fallback: cross-platform
  headless via vsdx Python lib (limited features — no theme application, no Page.Layout, no Validate).
platforms: [windows, macos-fallback, linux-fallback]
---

# Visio Master Skill

> Visio diagram generation system. Converts source documents into a hand-authored multi-page `.vsdx`
> drawing through a strict Architect → Drafter → Stylist pipeline. Cross-page connector consistency,
> stencil-set discipline, and theme variant fidelity all live in `diagram_lock.md` — re-read per page,
> never invented from memory.

**Core Pipeline**: `Source Document → Init Project → [Template] → Architect → [Stencil Resolver] → Drafter → Stylist → Validate → Export`

> [!CAUTION]
> ## 🚨 Global Execution Discipline (MANDATORY)
>
> **This workflow is a strict serial pipeline. The following rules have the highest priority — violating any one of them constitutes execution failure:**
>
> 1. **SERIAL EXECUTION** — Steps MUST be executed in order; the output of each step is the input for the next. Non-BLOCKING adjacent steps may proceed continuously once prerequisites are met, without waiting for the user to say "continue".
> 2. **BLOCKING = HARD STOP** — Steps marked ⛔ BLOCKING require a full stop; the AI MUST wait for an explicit user response before proceeding and MUST NOT make any decisions on behalf of the user. The Eight Confirmations in Step 4 are the canonical BLOCKING point — once `[DIAGRAM_LOCK_CONFIRMED]` has been emitted in this conversation, every subsequent non-BLOCKING step proceeds automatically without further prompts.
> 3. **NO CROSS-PHASE BUNDLING** — Cross-phase bundling is FORBIDDEN. Architect's Eight Confirmations and Drafter's `pages/*.vsdx-page.xml` MUST never appear in the same response. Each phase emits only its own outputs; pre-authoring downstream artefacts during an earlier phase poisons Drafter's per-page lock re-read because the agent's working memory diverges from the lock's declared values.
> 4. **GATE BEFORE ENTRY** — Each Step has prerequisites (🚧 GATE) listed at the top; these MUST be verified before starting that Step. Self-verifiable gates (file presence, command exit code) do not pause for the user; ⛔ BLOCKING gates do.
> 5. **NO SPECULATIVE EXECUTION** — "Pre-preparing" content for subsequent Steps is FORBIDDEN. Writing page-XML during the Architect phase, applying themes during the Drafter phase, or running `finalize_vsdx.py` mid-Drafter are all violations. Phase outputs are the only commitment; everything authored before its phase is invisible to later phases.
> 6. **NO SUB-AGENT VSDX GENERATION** — Drafter Step 6 page authorship is context-dependent and MUST be completed by the current main agent end-to-end. Delegating Visio Page generation to sub-agents is FORBIDDEN — cross-page visual consistency lives in the agent's working memory of pages already authored, and sub-agents sever that memory.
> 7. **SEQUENTIAL PAGE GENERATION ONLY** — In Drafter Step 6, after the global design context is confirmed, Visio Pages MUST be generated sequentially page by page in one continuous pass. Grouped page batches (for example, 5 pages at a time) are FORBIDDEN. Each page is one Drafter turn.
> 8. **DIAGRAM_LOCK RE-READ PER PAGE** — Before generating each Visio Page, Drafter MUST `read_file <project_path>/diagram_lock.md`. All colors / fonts / stencils / images / connector routing MUST come from this file — no values from memory or invented on the fly. Drafter MUST also look up the current page's `page_rhythm` (`anchor` / `dense` / `breathing`), `page_layouts` (which template fragment to inherit, if any), and `page_diagrams` (which structural diagram template to adapt, if any). Empty / absent entries are intentional Architect signals — see `references/drafter.md` §2.4-§2.5. This rule exists to resist context-compression drift on long drawings and to break the uniform "every page is a card grid" default.
> 9. **VSDX MUST BE HAND-CONSTRUCTED, NOT BLINDLY SCRIPT-GENERATED** — Every `pages/<NN>_<page_name>.vsdx-page.xml` fragment is authored by the main agent directly, one page at a time (see rules 6 and 7). Writing or running a Python / Node / shell script that emits page-XML files in batch — looping over pages, templating from data, or producing them via a generator — is FORBIDDEN, including under "save tokens", "quick draft", or "user is in a hurry" pretexts. Cross-page connector consistency, stencil inventory adherence, and per-page rhythm discipline all depend on per-page authoring with full upstream context, which a generator script cannot reproduce. `scripts/vsdx_build.py` exists for **post-authoring** mutations (text fills, master drops into an existing template, connector glue repair) — not for batch page emission.

> [!IMPORTANT]
> ## 🌐 Language & Communication Rule
>
> - **Response language**: match the user's input and source materials. Explicit user override (e.g., "请用英文回答" / "please answer in English") takes precedence.
> - **Template format**: `diagram_spec.md` MUST follow its original English 11-section template structure (section headings, field names) regardless of conversation language. Content values may be in the user's language.
> - **`diagram_lock.md`** is vocabulary-closed. Section names (`## canvas`, `## colors`, `## stencils`, `## page_rhythm`, etc.) and field keys (`canvas.format`, `colors.primary`, `stencils.set`, …) are fixed English atoms. Values may be localised; keys never are.
> - **ShapeSheet `Comment` cells** default to the user's language; in mixed-language drawings, Stylist locks one language per drawing via `diagram_lock.text.language`.

> [!IMPORTANT]
> ## 🔌 Compatibility With Generic Coding Skills
>
> - `visio-master` is a repository-specific workflow, not a general application scaffold.
> - Do NOT create `.worktrees/`, `tests/`, branch workflows, or generic engineering structure by default. Project skeletons live under `<workspace>/projects/<project_id>/` per `project_manager.py init`; nothing else is needed.
> - On conflict with a generic coding skill, follow this skill unless the user explicitly says otherwise.
> - The `vsdx` Python library and `pywin32` are pinned dependencies — do not substitute alternatives (`python-vsdx`, `aspose.diagram`, etc.) without an explicit user request and an audit-stencil-licensing pass.

---

## Main Pipeline Scripts

| Script | Purpose |
|--------|---------|
| `${SKILL_DIR}/scripts/source_to_md.py` | Source ingestion — converts PDF / DOCX / XLSX / CSV / TXT / Markdown / web URLs into a single `<project>/source.md` Markdown that Architect reads. Subcommands: `convert`, `batch`, `inspect`. |
| `${SKILL_DIR}/scripts/project_manager.py` | Project initialisation and validation. Subcommands: `init` (`--format` accepts `a0..a5`, `letter`, `legal`, `tabloid`, `ansi-c..ansi-e`, `arch-d`, `arch-e`, with landscape/portrait variants), `import-sources` (`--copy` / `--move`), `validate` (project skeleton + lock structure + stencil inventory cross-check), `list-pages` (inspect a `.vsdx`). |
| `${SKILL_DIR}/scripts/com_helper.py` | Shared COM helper. CLI subcommands: `selftest` (capability JSON, no Visio launch), `ping` (spawn `Visio.InvisibleApp`, print Version, quit). Also imported as a library by every COM-driven script (`apply_theme`, `data_link`, `finalize_vsdx`, `vsdx_export`, `vsdx_quality_check`) for `VisioCOM`, `batch_set_formulas`, `ensure_master`, `drop_master_at`, `connect_shapes`, `apply_theme`, `export_page`. Process-wide lock enforces sequential COM sessions. |
| `${SKILL_DIR}/scripts/stencil_index.py` | Stencil cataloguing. Subcommands: `scan` (walk a Visio Content directory, emit JSON inventory), `query` (keyword search across stencil families and master `NameU` values), `apply` (copy resolved stencils into a project's `templates/stencils/`). |
| `${SKILL_DIR}/scripts/diagram_index.py` | Diagram-template lookup. Subcommands: `list` (`--family flowchart` / `network` / `software` / `engineering` / `floorplan` / `schedule` / `business` / `org` / `brainstorm`), `query <id>` (full record or `--field <key>`), `scaffold <id> <project_path>` (write the diagram's default canvas / layout / routing into the project's `diagram_lock.md`). |
| `${SKILL_DIR}/scripts/vsdx_build.py` | Drafter's cross-platform XML mutation surface (pure `vsdx` + `lxml`, no Visio engine). Subcommands: `inspect`, `copy-page`, `set-text`, `drop-master`, `connect`. Mutates persisted state only — Visio re-runs theme application, auto-layout, ShapeSheet recompute, and connector auto-routing on next open. **NOT a batch page generator** (rule 9). |
| `${SKILL_DIR}/scripts/apply_theme.py` | Stylist's theme application. Subcommands: `list-themes`, `inspect`, `apply` with `--theme {office,facet,ion,slice,wisp,berlin}` and `--variant 1..4`. `--method auto` (default) tries COM first, falls back to `vsdx` (direct `visio/theme/theme1.xml` patching). `--in-place` or `--out` controls output location. `--pages 1,3-5` scopes a partial theme. |
| `${SKILL_DIR}/scripts/data_link.py` | Stylist's data linking (COM-only; requires Visio Plan 2 / Professional). Subcommands: `link-excel`, `link-csv`, `link-sql`, `refresh`, `attach-graphic`. Configuration recorded in `<project>/data_link.json` so it's inspectable, version-controlled, and re-applyable. |
| `${SKILL_DIR}/scripts/finalize_vsdx.py` | Stylist's deck-wide finalisation. Four passes (`glue-fix`, `layout`, `compress`, `verify-lock`); each toggleable via `--no-<pass>`. Writes `<project>/vsdx_final/` sibling to the input `vsdx_output/`. Exit 0 = full parity; exit 2 = any file failed or any lock check found a discrepancy. |
| `${SKILL_DIR}/scripts/vsdx_quality_check.py` | Quality-checker / linter. Backends: `vsdx` (default — stdlib `zipfile` + `xml.etree`, no install needed) and `com` (drives a live `Visio.InvisibleApp`, slower but inspects post-recalc state). `--lock <path>` cross-checks colors / stencils / typography against the lock. Exit 1 = errors emitted; warnings and infos are surfaced but do not fail the run. |
| `${SKILL_DIR}/scripts/vsdx_export.py` | Final `.vsdx` / PDF / PNG / SVG export. Subcommands: `pdf`, `png` (with `--from`, `--to`, `--dpi`), `svg` (with `--embed-fonts`), `all`. Outputs land under `<project_path>/exports/`. PDF / PNG / SVG paths require `pywin32` + a Visio install; on environments without them, the script reports document structure but emits a `requires Visio installed` error for the actual render. |

For complete tool documentation, see `${SKILL_DIR}/scripts/README.md`.

> **Windows note**: if a `python3 ...` command fails (common on python.org installs that ship `python.exe` but not `python3.exe`), rerun the same command with `python` instead.

## Template Index

| Index | Path | Purpose |
|-------|------|---------|
| Diagram templates | `${SKILL_DIR}/templates/diagrams/diagrams_index.json` | Catalog of 38+ structural diagram families (basic flowchart, cross-functional, BPMN 2.0, org chart, mind map, brainstorming, UML class/sequence/activity/use-case/state/component/deployment, ERD Crow's Foot, data flow, basic / detailed network, rack, AWS / Azure architecture, basic electrical, P&ID, HVAC, plumbing, floor plan, office layout, Gantt, timeline, calendar, SWOT, Balanced Scorecard, value stream, fishbone, SIPOC, FMEA, Six Sigma, ITIL). Each entry pins `template_short_name`, `primary_stencils`, `default_canvas`, `default_layout`, `default_routing`, `default_theme`, and an optional `validation_rule_set` plus `recipe_path`. |
| Theme bundles | `${SKILL_DIR}/templates/themes/themes_index.json` | Six built-in DrawingML themes recognised by Visio (`office`, `facet`, `ion`, `slice`, `wisp`, `berlin`) plus a `custom_theme_schema_example` for brand themes. Each entry records `primary_color`, `accent_colors[6]`, `major_font` / `minor_font`, `variant_count`, `embellishment_default`, and `recommended_for` use cases. Pass `display_name` to `Document.SetTheme`. |
| Stencil families | `${SKILL_DIR}/templates/stencils/stencils_index.json` | Catalog of Visio stencil families across nine categories (`flowchart`, `brainstorming`, `org_chart`, `network`, `software`, `engineering`, `floor_plan`, `schedule`, `business`). Each entry pins canonical `file` (metric `_M.VSSX`), `builtin_stencil_enum`, optional `template_file`, `companion_stencils`, `use_cases`, and `common_diagram_types`. Master inventories are intentionally lazy — iterate `Document.Masters` at runtime. |

> **Resolution**: stencils resolve at runtime against `%ProgramFiles%\Microsoft Office\root\Office16\Visio Content\<LCID>\` (e.g. `1033` = en-US, `2052` = zh-CN). Use `Application.GetBuiltInStencilFile(stencilType, measurementSystem)` for portable lookup.

## Standalone Workflows

| Workflow | Path | Purpose |
|----------|------|---------|
| `create-flowchart` | `workflows/create-flowchart.md` | Build a Basic or Cross-Functional flowchart `.vsdx` from a source description, end to end. Default entry for procedure / runbook / RACI / audit-trail diagrams. |
| `create-bpmn` | `workflows/create-bpmn.md` | BPMN 2.0 spec-compliant build with pool / lane semantics, `User.Bpmn*` cells, and the `BPMN 2.0 Diagram` validation rule set. |
| `create-orgchart` | `workflows/create-orgchart.md` | Org chart build with `OrgChartAutoSize=TRUE`, `visLORouteOrgNS` routing, dotted-line reporting, multi-tier matrix orgs. |
| `create-uml` | `workflows/create-uml.md` | UML class / sequence / activity / use-case / state / component / deployment from a software model description. |
| `create-erd` | `workflows/create-erd.md` | Database model with Crow's Foot or IDEF1X notation; static glue between entity / attribute boxes. |
| `create-network` | `workflows/create-network.md` | Basic / detailed network topology, rack diagram, on-prem vs Azure / AWS architecture builds. |
| `apply-theme` | `workflows/apply-theme.md` | Stylist-only entry: apply a Visio Theme to an existing `.vsdx` (COM or fallback). Standalone runnable when geometry is already in place. |
| `link-data` | `workflows/link-data.md` | Stylist data-linking workflow: bind shape rows to Excel / CSV / SQL recordsets, attach Data Graphics. COM-only. |
| `import-stencil` | `workflows/import-stencil.md` | Vendor a third-party `.vssx` into `templates/stencils/` after a license audit. Required before any user-supplied stencil is referenced from a lock. |
| `embed-online` | `workflows/embed-online.md` | Export to a Visio for the Web-compatible `.vsdx` and produce embed code for SharePoint / Teams / iframes. |
| `headless-build` | `workflows/headless-build.md` | CI / Linux / macOS build path: pure `vsdx` + `lxml`, no COM. Intentionally narrower (no theme variant resolution, no Page.Layout, no Validate). |
| `batch-export` | `workflows/batch-export.md` | Render multiple existing `.vsdx` files to PDF / PNG / SVG in one COM session. Sequential by design (rule 17 in `_BLUEPRINT.md` §7.2). |

---

## Workflow

### Step 1: Source Content Processing

🚧 **GATE**: User has provided source material (PDF / DOCX / XLSX / CSV / TSV / Markdown / URL / pasted prose / conversation content — any form is acceptable).

> **No source content?** When the user supplies only a topic name without any file or substantive description, stop and ask for source material; visio-master does not run a `topic-research` pre-pass — diagrams are derived from concrete procedures, models, or topologies, not generated from thin air.

When the user provides non-Markdown content, convert immediately:

| User Provides | Command |
|---------------|---------|
| PDF | `python3 ${SKILL_DIR}/scripts/source_to_md.py convert <file.pdf> -o <project_path>/source.md` |
| DOCX / DOC | `python3 ${SKILL_DIR}/scripts/source_to_md.py convert <file.docx> -o <project_path>/source.md` |
| XLSX / XLSM (RACI / step list) | `python3 ${SKILL_DIR}/scripts/source_to_md.py convert <file.xlsx> -o <project_path>/source.md` |
| CSV / TSV | `python3 ${SKILL_DIR}/scripts/source_to_md.py convert <file.csv> -o <project_path>/source.md` |
| Markdown | Read directly; copy to `<project_path>/source.md` if a project workspace is requested |
| Web URL | `python3 ${SKILL_DIR}/scripts/source_to_md.py convert <url> -o <project_path>/source.md` |
| Pasted prose | Write directly to `<project_path>/source.md` after Step 2 mkdir |
| Batch directory | `python3 ${SKILL_DIR}/scripts/source_to_md.py batch <inputs_dir> --project <project_path>` |

> **What to extract from `source.md`** while reading (in working memory, not on disk yet): actors / roles, steps, decisions, inputs / outputs, start / end, off-page references for flowcharts; entities + relations + cardinalities for ERDs; classes + methods + relations for UML; nodes + links + zones for networks; reporting tiers + dotted lines for org charts. The extraction informs Architect's diagram-type recommendation in Step 4 confirmation 2.

**✅ Checkpoint — Confirm source content is ready, proceed to Step 2.**

---

### Step 2: Project Initialization

🚧 **GATE**: Step 1 complete; `<project_path>/source.md` exists OR the user explicitly described requirements in conversation.

```bash
python3 ${SKILL_DIR}/scripts/project_manager.py init <project_id> --format <format> --dir <workspace>
```

Format options: `a4-landscape` (default for one-pager runbooks), `a3-landscape` (default for swim-lane / BPMN / network), `a1-landscape` (large topology / Gantt), `letter` / `tabloid` (US business), `ansi-d` / `ansi-e` (engineering wide), `arch-d` / `arch-e` (architectural), plus portrait variants. Common aliases (`a3`, `a4`, `letter`, `tabloid`, `ansi-d`, `arch-d`) resolve to landscape variants. Full canvas catalog: `references/canvas-formats.md`.

The script creates:

```
<workspace>/<project_id>/
├── source.md            (Step 1 output, or moved here in Step 2)
├── diagram_spec.md      (Architect Step 4 output — empty until then)
├── diagram_lock.md      (Architect Step 4 output — empty until then)
├── pages/               (Drafter Step 6 output)
├── comments/            (Drafter per-page commentary)
├── data_links/          (CSV/XLSX bindings, optional)
├── vsdx_output/         (intermediate Drafter assembly)
├── vsdx_final/          (Stylist + finalize_vsdx output)
└── exports/             (final .vsdx + PDF / PNG / SVG)
```

Import source content (choose based on the situation):

| Situation | Action |
|-----------|--------|
| Has source files (PDF / MD / XLSX / etc.) | `python3 ${SKILL_DIR}/scripts/project_manager.py import-sources <project_path> <source_files...> --move` |
| User provided text directly in conversation | No import needed — content is already in conversation context; subsequent steps reference it directly |

> ⚠️ Use `--move` (not `--copy`) for full-pipeline runs: the source files belong to the project and don't need to live at the original location anymore. Use `--copy` only when the source is shared with another project or sits in a tracked location.

Validate the skeleton before proceeding:

```bash
python3 ${SKILL_DIR}/scripts/project_manager.py validate <project_path>
```

**✅ Checkpoint — Confirm project structure created successfully, `source.md` is in place, validate exit `0`. Proceed to Step 3.**

---

### Step 3: Template Option

🚧 **GATE**: Step 2 complete; project directory structure is ready.

**Default — free design.** Proceed directly to Step 4. Do NOT query `diagrams_index.json` / `themes_index.json` / `stencils_index.json` unless triggered. Do NOT proactively suggest a diagram template based on slug-like words or vague style descriptions.

**Template flow triggers ONLY on explicit signals**:

| User input contains | Step 3 action |
|---|---|
| An explicit `--diagram <id>` flag (e.g. `bpmn_2`, `cross_functional_flowchart`, `aws_architecture`) referencing a row in `templates/diagrams/diagrams_index.json` | Run `python3 ${SKILL_DIR}/scripts/diagram_index.py scaffold <id> <project_path>`. The script copies the diagram's `default_canvas`, `default_layout`, `default_routing`, `default_theme`, `primary_stencils`, and `validation_rule_set` into `diagram_lock.md`. Architect's Eight Confirmations in Step 4 then refine values rather than choosing from scratch. |
| An explicit `--theme <id>` flag matching a row in `themes_index.json` (`office` / `facet` / `ion` / `slice` / `wisp` / `berlin`) | Pin `theme.id` in `diagram_lock.md`; Architect's confirmation 5 (theme & color) treats the choice as locked, only refining accent slots. |
| Anything else — bare diagram names ("用 BPMN"), style descriptions ("Azure 风格"), brand mentions ("招商银行风格"), vague intent ("想用模板"), or silence | Skip Step 3, free design |

There is no slug matching, no name lookup, no fuzzy resolution. A name without an explicit catalog id does not trigger — the user must give an id the AI can resolve via `diagram_index.py query <id>`.

> Style descriptions ("blueprint 风" / "AWS 简约" / "极简风" / etc.) never trigger Step 3. They flow into Architect's Eight Confirmations as a style brief (mode + visual_style + color in confirmations 4-5).
>
> "What diagram types exist?" / "What themes ship?" is out-of-band Q&A — answer by running `diagram_index.py list` / `apply_theme.py list-themes` and showing the result. Listing alone does not advance the pipeline; the user must send a concrete id back to trigger Step 3.

#### Diagram-template scaffold (single-id case)

```bash
python3 ${SKILL_DIR}/scripts/diagram_index.py scaffold <diagram_id> <project_path>
# Example: bpmn_2, basic_flowchart, cross_functional_flowchart, aws_architecture, gantt, swot, …
```

Architect re-reads the scaffolded `diagram_lock.md` at the start of Step 4 and treats the values as defaults — confirmations refine; they don't second-guess.

#### Multi-source fusion

When the user supplies both `--diagram <id>` and `--theme <id>` plus optional `--stencil <id>` flags, Step 3 fuses them: diagram-driven canvas / layout / routing override defaults, theme overrides color slots and font scheme, brand stencil augments inventory but never substitutes for a missing primary set. Conflicts (e.g. diagram default theme = `office`, user override = `wisp`) follow user-wins-over-default precedence.

**✅ Checkpoint — Default path proceeds to Step 4 without user interaction. If the user supplied explicit catalog ids, those have been scaffolded into `<project_path>/diagram_lock.md` before advancing.**

---

### Step 4: Architect Phase (MANDATORY — cannot be skipped)

🚧 **GATE**: Step 3 complete; default free-design path taken, or (if triggered) diagram / theme scaffolded into the project's `diagram_lock.md`.

First, switch role and read the role definition:

```
## [Role Switch: Architect]
📖 Reading role definition: ${SKILL_DIR}/references/architect.md
📋 Current task: Eight Confirmations + diagram_spec.md + diagram_lock.md
```

Mandatory reads before drafting the bundle (per `references/architect.md` §Mandatory Inputs):

```bash
cat <project_path>/source.md                                       # Source material
cat ${SKILL_DIR}/templates/diagram_spec_reference.md               # 11-section narrative skeleton
cat ${SKILL_DIR}/templates/spec_lock_reference.md                  # Parseable contract skeleton
cat ${SKILL_DIR}/templates/diagrams/diagrams_index.json            # 38+ diagram families
cat ${SKILL_DIR}/templates/themes/themes_index.json                # 6 built-in themes + brand schema
cat ${SKILL_DIR}/templates/stencils/stencils_index.json            # Stencil families + masters resolution
cat ${SKILL_DIR}/references/canvas-formats.md                      # Canvas catalog with px/in/mm/pt
cat ${SKILL_DIR}/references/diagram-types.md                       # Per-family decision space
```

> ⚠️ **Mandatory gate**: before writing `diagram_spec.md`, Architect MUST `read_file templates/diagram_spec_reference.md` and follow its full I-XI section structure. Self-check each section is present after writing. See `references/architect.md` §1.

**Eight Confirmations** (full template: `templates/diagram_spec_reference.md`):

⛔ **BLOCKING**: present the Eight Confirmations as a single bundled recommendation set and **wait for explicit user confirmation or modification** before outputting `diagram_spec.md` and `diagram_lock.md`. This is the single core BLOCKING point — once `[DIAGRAM_LOCK_CONFIRMED]` is emitted in this conversation, all subsequent steps proceed automatically.

1. **Page format / units / scale** — `canvas.format`, `canvas.units` (`in` / `mm` / `cm`), `canvas.width`, `canvas.height`, `canvas.dpi`, `canvas.page_scale` (`1:1` for business, `1 in : 1 ft` / `1:50` / `1:100` for engineering / floor plans), `canvas.measurement_system` (`visMSDefault` / `visMSUS` / `visMSMetric`), `canvas.orientation` (`visPLOPortrait` / `visPLOLandscape`).
2. **Diagram type & page count** — `primary_diagram_type` (one of 38+ catalog entries: `basic-flowchart` / `cross-functional-flowchart` / `bpmn-2.0` / `org-chart` / `mind-map` / `uml-class` / `uml-sequence` / `uml-activity` / `uml-state` / `erd-crowsfoot` / `dataflow` / `basic-network` / `detailed-network` / `rack` / `aws-architecture` / `azure-architecture` / `basic-electrical` / `pid` / `hvac` / `floor-plan` / `gantt` / `timeline` / `calendar` / `swot` / `balanced-scorecard` / `value-stream-map` / `fishbone` / `sipoc` / `fmea` / `itil-workflow` / `mixed`), `page_count`, `template_basename` (Visio `.VSTX` short-name resolved by `Application.GetBuiltInStencilFile`), `page_diagrams.P<NN>` per page when `mixed`.
3. **Audience & use case** — `audience` (`executive` / `operations` / `engineering` / `customer` / `auditor` / `mixed` / `public`), `use_case` (`kickoff briefing` / `runbook` / `as-built spec` / `training` / `compliance evidence` / `public-facing diagram`), `presentation_mode` (`print` / `screen` / `whiteboard` / `pdf-email`), `density_default` (`tight` / `normal` / `relaxed`).
4. **Style objective (mode + visual_style)** — Layer 1 `mode` (`pyramid` / `narrative` / `instructional` / `showcase` / `briefing` / `custom`); Layer 2 `visual_style` (`engineering-blueprint` / `executive-clean` / `network-topology` / `swim-lane-formal` / `mindmap-organic` / `bpmn-strict` / `whiteboard-sketch` / `dark-tech` / `swiss-minimal` / `custom`). For `custom` either layer, append a `mode_behavior:` / `visual_style_behavior:` one-paragraph atomic string.
5. **Theme & color palette** — `theme.id` (`office` / `facet` / `ion` / `slice` / `wisp` / `berlin` / brand / `custom`), `theme.variant` (`1`-`4`), `theme.embellishment_level` (`0` none / `1` subtle / `2` moderate / `3` rich), `colors.primary` / `colors.accent` / `colors.secondary_accent` / `colors.text` / `colors.text_secondary` / `colors.bg` / `colors.surface` / `colors.border` / `colors.grid` / `colors.scrim` / `colors.success` / `colors.warning` / `colors.error` (HEX). User / template colors are TRUTH — do not auto-adjust to fit an industry default.
6. **Stencil set** — `stencils.set` (exactly one primary: `flowchart-basic` / `flowchart-advanced` / `bpmn-2.0` / `network-rack` / `network-azure` / `network-aws` / `software-uml` / `org-personas` / `mindmap-organic` / `engineering-isa` / `electrical-iec` / etc.), `stencils.brand_set` (optional product / company logos), `stencils.inventory` (approved master `NameU` values; Drafter may only use these), `stencils.connector_style` (`right-angle` / `straight` / `curved` / `tree`), `stencils.connector_default_routing` (`flowchart` / `network` / `tree` / `organic`).
7. **Layout & connector routing** — `layout.algorithm` (`flowchart-vertical` / `flowchart-horizontal` / `tree-down` / `radial` / `grid` / `swim-lane-horizontal` / `swim-lane-vertical` / `manual`), `layout.spacing` (`tight` / `normal` / `relaxed`), `connectors.routing` (`flowchart` / `network` / `tree` / `organic`), `connectors.label_position` (`mid-line` / `endpoint-label` / `none`), `connectors.line_end_default` (Visio `LineEnd` id from the chosen stencil set), per-page `page_rhythm.P<NN>` (`anchor` / `dense` / `breathing`).
8. **Data linking** — `data_links.enabled` (`true` / `false`; default `false`), `data_links.sources[]` (CSV / XLSX / SQL paths under `<project>/data_links/`), `data_links.bindings[]` (per-shape-class binding rules `<shape_class> ← <source>:<column>`), `data_graphics[]` (per-shape-class data-graphic definitions: icon / color-by-value / data-bar). When `enabled: false`, Drafter ignores binding and Stylist skips data-graphics application. When `true`, Drafter still does NOT touch binding — it lives in Stylist Step 6.5.

**Mandatory — split-mode note** (not a ninth confirmation): after the eight items, append one short line (rendered in the user's language, prefixed with 💡) about generation cadence. Pick the variant by qualitative read: total `page_count`, source-material bulk, complexity of locked stencil set:

| Signal read | Line content |
|---|---|
| Heavy (`page_count > 8` / bulky source / multiple stencil sets / detailed network or rack) | State estimated page count and recommend switching to **split mode** after Step 5 — stop this chat, open a fresh window and input `继续生成 projects/<project_id>` to enter Phase B (Drafter + Stylist + export). The Visio COM session is stateful — separating Architect from Drafter into two windows reduces context pressure and lets the COM path run without competing for budget. No response or "continue" = default continuous mode. |
| Normal (default — `page_count ≤ 8`, single stencil set) | State scale is moderate, default continuous mode generates in one go; if mid-way window switch is desired, input `继续生成 projects/<project_id>` after Step 5 to switch to split mode. |

This line is required output every run — the user must always see the mode choice exists. Whether to act on it is the user's call.

**Output**:

- `<project_path>/diagram_spec.md` — human-readable 11-section narrative (I Project Information → II Canvas → III Visual Theme → IV Typography → V Layout & Connectors → VI Stencils & Icons → VII Diagram Templates → VIII Image Resource List → IX Page Outline → X ShapeSheet Comments → XI Technical Constraints).
- `<project_path>/diagram_lock.md` — machine-readable execution contract; sections `## canvas`, `## mode`, `## visual_style`, `## colors`, `## typography`, `## stencils`, `## images`, `## page_rhythm`, `## page_layouts`, `## page_diagrams`, `## page_data_links`, `## layout`, `## connectors`, `## forbidden`. Drafter re-reads this file before every page (rule 8).
- `[DIAGRAM_LOCK_CONFIRMED]` marker emitted on its own line in the conversation transcript.

**✅ Checkpoint — Phase deliverables complete, auto-proceed to next step**:

```markdown
## ✅ Architect Phase Complete
- [x] Eight Confirmations completed (user confirmed)
- [x] Split-mode note appended below the eight items (heavy or normal variant)
- [x] diagram_spec.md generated (11 sections)
- [x] diagram_lock.md generated (vocabulary-closed sections)
- [x] [DIAGRAM_LOCK_CONFIRMED] emitted
- [ ] **Next**: Auto-proceed to [Stencil Acquisition / Drafter] phase
```

---

### Step 5: Stencil Acquisition Phase (Conditional)

🚧 **GATE**: Step 4 complete; `diagram_lock.md` exists with `## stencils.set` and `## stencils.inventory` populated. `[DIAGRAM_LOCK_CONFIRMED]` emitted.

> **Trigger**: At least one entry in `stencils.set` or `stencils.brand_set` references a stencil family not yet vendored under `${SKILL_DIR}/templates/stencils/<id>/`. If every locked stencil already exists locally, skip to Step 6.

Resolve and validate the locked stencil set:

```bash
python3 ${SKILL_DIR}/scripts/stencil_index.py query <stencil_id>           # confirm catalog entry exists
python3 ${SKILL_DIR}/scripts/stencil_index.py apply <project_path> <stencil_id> [<id>...]   # vendor masters
python3 ${SKILL_DIR}/scripts/project_manager.py validate <project_path> --resolve-stencils   # inventory cross-check
```

The validator does three things:

1. Reads `<project_path>/diagram_lock.md ## stencils.set` and `## stencils.brand_set`.
2. Confirms each set has a corresponding directory `${SKILL_DIR}/templates/stencils/<set>/` with a `README.md` listing the masters.
3. Cross-checks that every `NameU` in `stencils.inventory` actually appears in that README's master inventory.

If a master is missing:

- Architect re-opens the lock and either drops the master or swaps the stencil set. **Do NOT** silently fall back to a master that wasn't locked.
- For third-party stencils (Cisco, Lucid, ConceptDraw, etc.), run `workflows/import-stencil.md` first — it audits licensing before any masters land in the skill's `templates/stencils/`.

> ⚠️ **Stencil licensing**: Many corporate Visio environments ship paid stencils. Auto-importing them is forbidden — bare `cp` from a system stencil directory is a workflow failure. The default sets shipped with the skill (`flowchart-basic`, `bpmn-2.0` for the BPMN spec subset, plus the families enumerated in `stencils_index.json`) are sourced from Microsoft's own license-clear stencils.

**Default — auto-proceed to Step 6.** Only when the user's Step 4 response explicitly opted into split mode, output the Phase A hand-off below and stop this conversation:

```markdown
## ✅ Phase A Complete
- [x] Spec: diagram_spec.md, diagram_lock.md, [DIAGRAM_LOCK_CONFIRMED] emitted
- [x] Stencils resolved: <list>
- [ ] **Next**: open a fresh chat window and input `继续生成 projects/<project_id>` to enter Phase B
```

**✅ Checkpoint — Confirm stencil resolution attempted for every locked set; no missing masters; no licensing flags. Proceed to Step 6.**

---

### Step 6: Drafter Phase

🚧 **GATE**: Step 4 (and Step 5 if triggered) complete; all prerequisite deliverables ready (`diagram_lock.md`, every master `NameU` in `stencils.inventory` resolves, every `page_layouts` / `page_diagrams` template basename exists on disk).

Switch role and read references for this drawing's locked `mode` + `visual_style`:

```
## [Role Switch: Drafter]
📖 Reading role definition: ${SKILL_DIR}/references/drafter.md
📋 Current task: Author Visio Pages 01..<page_count>
```

```bash
cat ${SKILL_DIR}/references/drafter.md                            # REQUIRED: per-page authorship rules
cat ${SKILL_DIR}/references/shared-standards.md                   # REQUIRED: VSDX/Visio technical constraints
cat ${SKILL_DIR}/references/vsdx-format-quick-ref.md              # VSDX OPC parts + page XML schema
cat ${SKILL_DIR}/references/connector-routing.md                  # Connector authoring (glue, RouteStyle, line ends)
cat ${SKILL_DIR}/references/shapesheet-quick-ref.md               # ShapeSheet cell taxonomy
```

> Read `drafter.md` + `shared-standards.md` + the connector / ShapeSheet quick refs as the baseline. For `mode: custom` or `visual_style: custom`, follow `mode_behavior:` / `visual_style_behavior:` from `diagram_lock.md` instead of any preset overlay.

**Design Parameter Confirmation (Mandatory)**: before the first page, output key design parameters from the lock (canvas dimensions, color palette, font plan, body font size, locked stencil set, default `RouteStyle`). See `references/drafter.md` §2.

**Pre-generation Batch Read (Mandatory)**: before the first page, batch-read every distinct `page_layouts` basename, every distinct `page_diagrams` template, every locked stencil README, and the per-mode / per-visual-style overlay files. One read per file — do not re-read these during page generation. See `references/drafter.md` §3.0.

**Per-page `diagram_lock.md` re-read (Mandatory)**: before **each** Visio Page, `read_file <project_path>/diagram_lock.md`. Use only its colors / fonts / stencils / images, plus per-page `page_rhythm` / `page_layouts` / `page_diagrams` lookups (template fragments are already loaded from the batch read above). This resists context-compression drift on long drawings. See `references/drafter.md` §2.1.

> ⚠️ **Main-agent only**: Visio Page generation MUST stay in the current main agent — page design depends on full upstream context. Do NOT delegate to sub-agents (rule 6).
> ⚠️ **Generation rhythm**: generate pages sequentially, one at a time, in the same continuous context. Do NOT batch (rule 7).
> ⚠️ **Hand-authored**: do NOT loop a generator script over `page_count` (rule 9). `vsdx_build.py` is for post-authoring mutations only.

**Per-page output format declaration**: each Drafter turn opens with the role-switch marker, the per-page lock re-read note, and the template-mapping declaration:

```
## [Role Switch: Drafter]
📖 Reading role definition: ${SKILL_DIR}/references/drafter.md
📋 Current task: Author Visio Page <NN>_<page_name>
🔁 Re-reading: <project_path>/diagram_lock.md (P<NN> entry)
🔁 Re-reading: <project_path>/diagram_spec.md §IX P<NN>

📝 **Page-layout mapping**: templates/page-layouts/<layout_id>/<basename>.vsdx-page.xml (or "None (free design)")
📝 **Diagram-template mapping**: templates/diagrams/<diagram_id>.vsdx-page.xml (or "None (free design)")
🎯 **Adherence rules / layout strategy**: <rhythm-tag-specific description>
```

**Visual Construction Phase**: generate Visio Page fragments sequentially, one at a time, in one continuous pass → `<project_path>/pages/<NN>_<page_name>.vsdx-page.xml`. Each page is a `<Page>` element containing `<PageSheet>` + `<Shapes>` + optional `<Connects>`, following the cell ordering rules in `references/drafter.md` §4.1. Connector glue formulas pair with `<Connect>` rows (§5.2-§6.5) — never one without the other.

**Quality Check Gate (Mandatory)** — after all pages, BEFORE Stylist phase:

```bash
python3 ${SKILL_DIR}/scripts/vsdx_quality_check.py <project_path>/pages/
```

- Any `error` (banned ShapeSheet patterns, banned text patterns, glue completeness, stencil consistency, theme consistency drift, coordinate sanity, layer assignment drift, per-page rhythm coherence) MUST be fixed before proceeding — return to Visual Construction, regenerate that page, re-run check.
- `warning` entries: fix when straightforward, otherwise acknowledge and release.
- Exit codes: `0` = clean, `1` = warnings only, `2` = errors. The checker runs against `pages/*.vsdx-page.xml` (page-XML fragments) **before** `finalize_vsdx.py` because finalize rewrites cells and can mask violations.

**Logic Construction Phase**: generate per-page commentary → `<project_path>/comments/total.md`. Page-by-page intent notes that the Drafter writes inline as one Markdown file with `## Page <NN> — <name>` headings. No splitter step is required; downstream Stylist and reviewers consume `total.md` directly.

**✅ Checkpoint — Confirm all Visio Pages and commentary are fully generated and quality-checked. Proceed directly to Step 7**:

```markdown
## ✅ Drafter Phase Complete
- [x] All pages generated to pages/<NN>_<page_name>.vsdx-page.xml
- [x] Every page emitted role-switch marker + lock re-read note
- [x] vsdx_quality_check.py passed (0 errors)
- [x] Per-page commentary generated at comments/total.md
- [x] No data-graphics / theme / layer rows authored (Stylist's surface)
```

> **Diagram audit (opt-in)?** If the user explicitly asked for stricter connector / coordinate verification before themes are applied, re-run `vsdx_quality_check.py --strict` (treats every warning as an error) after the quality-check gate. Skip by default.

---

### Step 7: Stylist + Validate + Export

🚧 **GATE**: Step 6 complete; all `pages/<NN>_*.vsdx-page.xml` exist; `vsdx_quality_check.py` exits `0` or `1`; `comments/total.md` written.

Switch role for the Stylist passes:

```
## [Role Switch: Stylist]
📖 Reading role definition: ${SKILL_DIR}/references/stylist.md
📋 Current task: Theme + Data Graphics + Layer assignment + Container assembly + Validate + Export
```

```bash
cat ${SKILL_DIR}/references/theme-and-data-graphics.md             # Theme XML + Data Graphic items
cat ${SKILL_DIR}/references/automation-decision-matrix.md          # COM vs fallback path selection
cat ${SKILL_DIR}/references/com-quick-ref.md                       # pywin32 idioms + threading
```

> ⚠️ Run the sub-steps **one at a time** — each must complete successfully before the next.
> ❌ **NEVER** combine them into a single code block or shell invocation.

#### Step 7.1 — Validate commentary against pages

```bash
test -s "<project_path>/comments/total.md" \
  && grep -c '^## Page ' "<project_path>/comments/total.md"
```

Confirm `comments/total.md` exists and contains one `## Page <NN> — <name>` heading per Visio Page authored in Step 6. Stylist consumes this file directly — there is no per-page split step. If a page heading is missing, return to Step 6 to backfill before continuing.

#### Step 7.2 — Apply theme

```bash
python3 ${SKILL_DIR}/scripts/apply_theme.py apply <project_path>/vsdx_output/<draft>.vsdx \
    --theme <theme.id from lock> --variant <theme.variant from lock>
```

Method options:

| Flag | Behaviour |
|------|-----------|
| `--method auto` (default) | Try COM (`pywin32` + Visio installed); fall back to `vsdx` (direct `visio/theme/theme1.xml` patching) |
| `--method com` | Force COM; fail loudly when unavailable |
| `--method vsdx` | Force the cross-platform fallback; never touch COM |

The script reads `diagram_lock.md ## theme` and `## colors`, loads the matching bundle from `${SKILL_DIR}/scripts/assets/themes/`, walks every shape on every page, and replaces inline HEX with `THEMEGUARD()` references when the shape's role qualifies. Status callouts (success / warning / error) retain inline HEX.

#### Step 7.3 — Data linking (conditional)

If `diagram_lock.data_links.enabled = true`:

```bash
python3 ${SKILL_DIR}/scripts/data_link.py link-excel <vsdx> \
    --workbook <project_path>/data_links/<file>.xlsx --sheet Sheet1 \
    --primary-key <key> --name <recordset>
python3 ${SKILL_DIR}/scripts/data_link.py attach-graphic <vsdx> \
    --recordset <recordset> --graphic "<DG name>"
```

Subcommands also support `link-csv` (CSV recordsets) and `link-sql` (SQL Server / ODBC). Every successful operation is appended to `<project_path>/data_link.json` so the configuration is inspectable, version-controlled, and re-applyable.

When `enabled: false` (default for flowcharts and most static diagrams), this sub-step is skipped.

#### Step 7.4 — Finalisation

```bash
python3 ${SKILL_DIR}/scripts/finalize_vsdx.py <project_path>
```

Four passes run by default:

| Pass | Toggle | Purpose |
|------|--------|---------|
| `glue-fix` | `--no-glue-fix` | Repair connector glue formulas; pair every formula with its `<Connect>` row |
| `layout` | `--no-layout` | Run `Page.LayoutIncremental` for every page (COM path) or pre-bake `assemble_containers` membership (fallback) |
| `compress` | `--no-compress` | Re-compose the OPC zip with deflate; deduplicate inherited masters |
| `verify-lock` | `--no-verify-lock` | Cross-check every emitted color / font / stencil against `diagram_lock.md` |

Output lands under `<project_path>/vsdx_final/<draft>.vsdx`. Exit `0` = full parity; exit `2` = any file failed or any lock check found a discrepancy.

#### Step 7.5 — Quality check (post-finalize)

```bash
python3 ${SKILL_DIR}/scripts/vsdx_quality_check.py <project_path>/vsdx_final/ \
    --lock <project_path>/diagram_lock.md --pretty --summary
```

Exit code `1` when any `error` was emitted; `warning` and `info` are surfaced but do not fail the run. Errors here typically mean Drafter wrote an unrecognised HEX that `apply_theme.py` couldn't lift, or a connector glue references a shape on the wrong page. Bounce back to Drafter for that page; do NOT hand-edit the lock.

#### Step 7.6 — Export

```bash
# Final .vsdx (always; copies vsdx_final/ to exports/)
python3 ${SKILL_DIR}/scripts/vsdx_export.py all <project_path> --vsdx <draft>.vsdx
# Or explicit single-format:
python3 ${SKILL_DIR}/scripts/vsdx_export.py pdf <project_path> --vsdx <draft>.vsdx
python3 ${SKILL_DIR}/scripts/vsdx_export.py png <project_path> --vsdx <draft>.vsdx --from 1 --to <page_count> --dpi 300
python3 ${SKILL_DIR}/scripts/vsdx_export.py svg <project_path> --vsdx <draft>.vsdx --embed-fonts
```

Outputs land under `<project_path>/exports/`. Rendering paths require `pywin32` + a Visio install; on environments without them, the script reports document structure (page names, page count) but emits a `requires Visio installed` error for the actual render. CI-friendly headless builds use `workflows/headless-build.md` instead.

> ❌ **NEVER** parallelise `vsdx_export.py` against the same Visio process — `com_helper.py` enforces a process-wide lock; bypassing it via concurrent shells produces COM RPC errors.
> ❌ **NEVER** force `--method com` in `apply_theme.py` on a CI host without `pywin32`; the script will error rather than silently fall back.
> ❌ **NEVER** skip `vsdx_quality_check.py` between Drafter and Stylist — the post-Drafter run is the only chance to catch glue / coordinate / stencil drift before theme rewrites mask it.

#### Final verification

```bash
# Quick smoke test — open the .vsdx with the vsdx Python lib
python3 -c "import vsdx; doc = vsdx.VisioFile('<project_path>/exports/<file>.vsdx'); print(f'pages: {len(doc.pages)}'); [print(p.name) for p in doc.pages]"
```

**✅ Checkpoint — Final `.vsdx` exists at `exports/`, opens cleanly, page count matches `diagram_lock.page_count`, no orphan pages.**

---

## Eight Confirmations Reference

The Eight Confirmations are the single ⛔ BLOCKING gate inside Architect Step 4. Each item is a **decision** Architect proposes with concrete values; the user accepts or revises. "I don't know, you decide" is a valid reply — the recommended values stand.

| # | Confirmation | Decision space | Lock target |
|---|--------------|----------------|-------------|
| 1 | **Page format & units** | `canvas.format` (letter / a3 / a1 / engineering / floor-plan / custom), `canvas.units` (`in` / `mm`), `canvas.width`, `canvas.height`, `canvas.dpi`, `canvas.page_scale`, `canvas.measurement_system`, `canvas.orientation` | `## canvas` |
| 2 | **Diagram type & page count** | `primary_diagram_type` (one of 38+ catalog ids), `page_count`, `template_basename`, per-page `page_diagrams.P<NN>` for mixed decks | `## diagram_type`, `## page_diagrams` |
| 3 | **Audience** | `audience`, `use_case`, `presentation_mode`, `density_default` | `diagram_spec.md §I` only (narrative; no Drafter mechanical feed) |
| 4 | **Style objective** | Layer 1 `mode` (rhetorical skeleton); Layer 2 `visual_style` (aesthetic posture). Optional `mode_behavior:` / `visual_style_behavior:` paragraphs for `custom` either layer | `## mode`, `## visual_style` |
| 5 | **Color theme & variant** | `theme.id`, `theme.variant`, `theme.embellishment_level`, plus the full `colors.*` HEX palette (primary / accent / secondary_accent / text / text_secondary / bg / surface / border / grid / scrim / success / warning / error). User / template colors are TRUTH | `## theme`, `## colors` |
| 6 | **Stencil set** | `stencils.set` (one primary), `stencils.brand_set` (optional opt-in), `stencils.inventory` (allowed master `NameU` values), `stencils.connector_style`, `stencils.connector_default_routing` | `## stencils` |
| 7 | **Layout algorithm + connector routing** | `layout.algorithm`, `layout.spacing`, `connectors.routing`, `connectors.label_position`, `connectors.line_end_default`, per-page `page_rhythm.P<NN>` (`anchor` / `dense` / `breathing`) | `## layout`, `## connectors`, `## page_rhythm` |
| 8 | **Data linking policy** | `data_links.enabled`, `data_links.sources[]`, `data_links.bindings[]`, `data_graphics[]`. Default `enabled: false` for static diagrams; `true` only when the user has an explicit data source AND wants color-by-status / icon-set / data-bar Data Graphics | `## page_data_links`, `## data_graphics` |

After confirmation, Architect appends one **split-mode note** (heavy vs normal) — required output, not a ninth confirmation.

---

## Role Switching Protocol

Before switching roles, **MUST first read** the corresponding reference file. Output marker:

```markdown
## [Role Switch: <Role Name>]
📖 Reading role definition: ${SKILL_DIR}/references/<filename>.md
📋 Current task: <brief description>
```

The marker is **load-bearing**: it both pins the agent on the role's reference file and creates an audit trail. The orchestrator and `vsdx_quality_check.py` use the marker boundaries to find phase outputs.

| Role | Reference | Concern |
|------|-----------|---------|
| **Architect** | `references/architect.md` | Eight Confirmations, `diagram_spec.md` narrative, `diagram_lock.md` parseable contract. Pure planning role; never writes page-XML. |
| **Drafter** | `references/drafter.md` | Hand-authors one Visio Page fragment per output page in sequence. Re-reads `diagram_lock.md` before every page. Never writes Theme XML, Data Graphics, or Layer rows. |
| **Stylist** | `references/stylist.md` | Theme application, Data Graphic binding, Layer assignment, Container / List composition. Edits Drafter's pages in place along the narrow theme / data / layer / container axis only. Never introduces new colors / fonts / stencils. |

Switching roles requires the marker block — bare prose ("Now I'll act as Drafter…") is not sufficient. The orchestrator rejects pages emitted without an opening marker.

---

## Reference Resources

| Resource | Path |
|----------|------|
| Architect role definition | `references/architect.md` |
| Drafter role definition | `references/drafter.md` |
| Stylist role definition | `references/stylist.md` |
| Visio Pages XML quick reference | `references/vsdx-format-quick-ref.md` |
| ShapeSheet cell taxonomy | `references/shapesheet-quick-ref.md` |
| Connector routing & line-end discipline | `references/connector-routing.md` |
| Canvas format catalog | `references/canvas-formats.md` |
| Diagram-types decision space | `references/diagram-types.md` |
| Theme + Data Graphics authoring | `references/theme-and-data-graphics.md` |
| Shared technical constraints | `references/shared-standards.md` |
| Automation decision matrix (COM vs fallback) | `references/automation-decision-matrix.md` |
| pywin32 / COM quick reference | `references/com-quick-ref.md` |
| Visio UI shortcuts (for human cross-check) | `references/ui-shortcuts.md` |
| Troubleshooting | `references/troubleshooting.md` |
| Diagram template index | `templates/diagrams/diagrams_index.json` |
| Theme bundle index | `templates/themes/themes_index.json` |
| Stencil family index | `templates/stencils/stencils_index.json` |
| Spec / lock skeletons | `templates/diagram_spec_reference.md`, `templates/spec_lock_reference.md` |

---

## Common Failure Modes (quick lookup)

| Symptom | Likely cause | Fix |
|---|---|---|
| Visio opens the file but a shape is missing geometry | Master placeholder `@<NameU>` not in `stencils.inventory`; `embed_masters.py` left it unresolved | Cross-check inventory; add the master to lock and re-run |
| Connector renders as a literal line, not a glued connector | Glue formula present but `<Connect>` row missing; or formula references a shape not on the page | Add the `<Connect>` row; verify `Sheet.<id>` is on the same page |
| Connector arrow points the wrong direction | `EndArrow` set on the wrong end (e.g. on the begin endpoint) | Move arrow to the end that points to the target |
| Shape appears off-canvas | Coordinate exceeds `PageWidth` / `PageHeight`; or unit drift (mm value on inch page) | Verify `canvas.units`; quantise to grid; re-run `vsdx_quality_check.py` |
| Text shows as Calibri instead of locked font | Font index unresolved in `<DocumentSettings>/<FontList>` | Re-run `apply_theme.py`; confirm font is installed on the export machine |
| Theme application erases inline color | Drafter wrote a HEX that wasn't in `diagram_lock.colors`; `apply_theme.py` flagged and reset | Use only locked HEX; bounce back to Drafter for that page |
| Container does not enclose its members | Member shapes' bounding boxes don't overlap container; `assemble_containers.py` couldn't infer membership | Move members fully inside the container's `Width` / `Height` |
| List members appear in the wrong order | `msvSDListDirection` mismatch with the physical placement | Set direction to `0` (top-to-bottom) and stack by `PinY`, or `1` (left-to-right) and stack by `PinX` |
| Page opens but Visio "repairs" the file with a warning | Almost always cell ordering inside `<Shape>`: `<Text>` precedes `<Cell>`, or `<Section>` precedes `<Cell>` | Re-order to `<Cell>* <Section>* <Text>?` |
| `vsdx_export.py` errors with COM RPC failure | Parallel COM calls or stale `Visio.InvisibleApp` from a previous crashed run | `python3 com_helper.py ping`; reboot if stuck; never parallelise COM |

For the full failure-mode catalog see `references/drafter.md` §11 and `references/troubleshooting.md`.

---

## Notes

- **Local preview**: open the final `.vsdx` in Visio (Windows: `start <project>/exports/<file>.vsdx`; macOS: `open -a Microsoft\ Visio …` requires Visio Plan 2 web client). For Visio Viewer (read-only, free), `start visioviewer://<file>.vsdx` after registering the protocol.
- **Cross-platform fallback preview**: LibreOffice Draw opens `.vsdx` on Linux / macOS — fidelity is medium (themes apply, basic shapes render, connectors mostly route correctly; Data Graphics and complex Containers may not display). Run `soffice --headless --convert-to png <file>.vsdx` for a quick PNG snapshot.
- **Browser preview**: `vsdx` Python lib + Pillow can render a per-page PNG via the `pages[i].render()` extension; commit such helpers under `workflows/embed-online.md` rather than ad-hoc.
- **COM session lifecycle**: every COM-driven script (`apply_theme`, `data_link`, `finalize_vsdx`, `vsdx_export`, `vsdx_quality_check --backend com`) opens a single `Visio.InvisibleApp` and closes it cleanly on exit. The process-wide lock in `com_helper.py` enforces sequential access; do not parallelise.
- **Update lock after pages exist**: hand-editing `diagram_lock.md` after pages are on disk is forbidden. Use the Architect-mediated `update_diagram_lock.py` flow (see `workflows/import-stencil.md` and `references/architect.md`) so changes propagate atomically across pages.
- **Resume after compaction**: if context is auto-compacted between Drafter pages, re-read this `SKILL.md` (Discipline section), `references/drafter.md` §2 + §7, `diagram_lock.md`, `diagram_spec.md`, then continue from the next un-authored page; do NOT regenerate pages already on disk.
- **Stencil licensing**: third-party stencils require an audit pass. Default sets are Microsoft's own license-clear families. See `workflows/import-stencil.md`.
- **Troubleshooting**: on generation issues (page off-canvas, connector glue lost, theme not applying, Data Graphic not rendering), check `references/troubleshooting.md` and `references/drafter.md` §11 for known remediation patterns.

