# Visio Master Toolset

This directory contains user-facing scripts for source ingestion, project setup, asset cataloguing, page drafting, styling, finalisation, quality checking, and export across the Visio Master pipeline (`Architect` → `Drafter` → `Stylist`).

## Directory Layout

- Top-level `scripts/`: 11 runnable entry-point scripts (one helper module: `com_helper.py`)
- `scripts/assets/themes/`: bundled DrawingML theme XML payloads consumed by `apply_theme.py` (`office`, `facet`, `ion`, `slice`, `wisp`, `berlin`)

The skill ships every entry point at the top level — there are no provider subdirectories. Cross-script helpers live in `com_helper.py` and are imported by the COM-driven scripts (`apply_theme`, `data_link`, `finalize_vsdx`, `vsdx_export`, `vsdx_quality_check`).

## Quick Start

Typical end-to-end workflow (Architect → Drafter → Stylist → Export):

```bash
# 1. Ingest source materials into Markdown the Architect reads
python3 scripts/source_to_md.py convert <file.pdf> --project <project_path>
python3 scripts/source_to_md.py batch <inputs_dir> --project <project_path>

# 2. Initialise a project skeleton (diagram_spec.md / diagram_lock.md / canonical dirs)
python3 scripts/project_manager.py init <project_name> --format a3-landscape
python3 scripts/project_manager.py import-sources <project_path> <sources...> --copy
python3 scripts/project_manager.py validate <project_path>

# 3. Catalogue assets the Drafter needs (run once per stencil set / diagram release)
python3 scripts/stencil_index.py scan "<visio-content-dir>"
python3 scripts/diagram_index.py list --family flowchart

# 4. Drafter authoring loop (cross-platform vsdx + lxml builder)
python3 scripts/vsdx_build.py inspect <template.vsdx>
python3 scripts/vsdx_build.py copy-page <template.vsdx> <out.vsdx> --src 0 --name P01
python3 scripts/vsdx_build.py set-text <in.vsdx> <out.vsdx> --page 0 --shape-id 5 --text "Ingest"
python3 scripts/vsdx_build.py drop-master <in.vsdx> <out.vsdx> --page 0 --xml shape.xml --x 2.5 --y 4.0
python3 scripts/vsdx_build.py connect <in.vsdx> <out.vsdx> --page 0 --from 5 --to 9 --kind dynamic

# 5. Stylist passes (theme + data linking)
python3 scripts/apply_theme.py apply <project_path>/vsdx_output/diagram.vsdx --theme facet --variant 2
python3 scripts/data_link.py link-excel <vsdx> --workbook <xlsx> --sheet Sheet1 --primary-key SKU --name inventory
python3 scripts/data_link.py attach-graphic <vsdx> --recordset inventory --graphic "Inventory DG"

# 6. Finalisation + quality lint
python3 scripts/finalize_vsdx.py <project_path>
python3 scripts/vsdx_quality_check.py <project_path>/vsdx_final/ --pretty --summary

# 7. Export
python3 scripts/vsdx_export.py pdf <project_path> --vsdx diagram.vsdx
python3 scripts/vsdx_export.py all <project_path> --vsdx diagram.vsdx
```

COM diagnostic (one-time, before any COM-backed step):

```bash
python3 scripts/com_helper.py selftest      # capability JSON, no Visio launch
python3 scripts/com_helper.py ping          # spawn InvisibleApp, print Version, quit
```

## Script Index

| Area | Primary scripts | Documentation |
|------|-----------------|---------------|
| Source ingestion | `source_to_md.py` | this README + `references/architect.md` |
| Project management | `project_manager.py` | this README + `references/architect.md` |
| COM helper (shared) | `com_helper.py` | `references/com-quick-ref.md`, `references/shared-standards.md` |
| Asset cataloguing | `stencil_index.py`, `diagram_index.py` | `references/drafter-base.md`, `templates/stencils/README.md`, `templates/diagrams/README.md` |
| Drafting (cross-platform) | `vsdx_build.py` | `references/visio-pages-xml.md`, `references/connectors.md` |
| Styling | `apply_theme.py`, `data_link.py` | `references/stylist.md`, `references/data-graphics.md` |
| Finalisation | `finalize_vsdx.py` | `references/shared-standards.md` |
| Quality lint | `vsdx_quality_check.py` | `references/shared-standards.md`, `references/visio-review.md` |
| Export | `vsdx_export.py` | `references/shared-standards.md` |

## High-Frequency Commands

Source ingestion:

```bash
python3 scripts/source_to_md.py convert <file.csv|.tsv|.txt|.md|.xlsx|.pdf>
python3 scripts/source_to_md.py convert <file.pdf> -o <project>/sources/spec.md
python3 scripts/source_to_md.py batch <inputs_dir> --project <project_path>
python3 scripts/source_to_md.py inspect <file>
```

Project setup:

```bash
python3 scripts/project_manager.py init <project_name> --format a3-landscape
python3 scripts/project_manager.py init <project_name> --format letter --dir <base_dir>
python3 scripts/project_manager.py import-sources <project_path> <sources...> --copy
python3 scripts/project_manager.py import-sources <project_path> <sources...> --move
python3 scripts/project_manager.py validate <project_path>
python3 scripts/project_manager.py list-pages <vsdx_file>
```

Supported `--format` ids include `a0…a5` (landscape/portrait), `letter`, `legal`, `tabloid`, `ansi-c…ansi-e`, `arch-d`, `arch-e`. Common aliases (`a3`, `a4`, `letter`, `tabloid`, `ansi-d`, `arch-d`) resolve to landscape variants.

Asset cataloguing:

```bash
python3 scripts/stencil_index.py scan "<visio-content-dir>"
python3 scripts/stencil_index.py query <keyword> --limit 10
python3 scripts/stencil_index.py apply <project_path> <stencil_id> [<stencil_id>...]

python3 scripts/diagram_index.py list
python3 scripts/diagram_index.py list --family flowchart --json
python3 scripts/diagram_index.py query <diagram_id>
python3 scripts/diagram_index.py query <diagram_id> --field key_masters
python3 scripts/diagram_index.py scaffold <diagram_id> <project_path>
```

VSDX build (cross-platform; pure `vsdx` + `lxml`, no Visio engine):

```bash
python3 scripts/vsdx_build.py inspect <template.vsdx>
python3 scripts/vsdx_build.py copy-page <in.vsdx> <out.vsdx> --src 0 --name <page_name>
python3 scripts/vsdx_build.py set-text <in.vsdx> <out.vsdx> --page 0 --shape-id <id> --text "<text>"
python3 scripts/vsdx_build.py drop-master <in.vsdx> <out.vsdx> --page 0 --xml <shape.xml> --x 2.5 --y 4.0
python3 scripts/vsdx_build.py connect <in.vsdx> <out.vsdx> --page 0 --from <id> --to <id> --kind dynamic
```

`vsdx_build.py` mutates persisted state only — Visio re-runs theme application, auto-layout, ShapeSheet recompute, and connector auto-routing on next open. Run `apply_theme.py` and `finalize_vsdx.py` afterward for engine-driven passes.

Theme application:

```bash
python3 scripts/apply_theme.py list-themes
python3 scripts/apply_theme.py inspect <input.vsdx>
python3 scripts/apply_theme.py apply <input.vsdx> --theme facet
python3 scripts/apply_theme.py apply <input.vsdx> --theme slice --variant 2 --method vsdx --in-place
python3 scripts/apply_theme.py apply <input.vsdx> --theme wisp --pages 1,3-5 --out themed.vsdx
```

Bundled themes (case-insensitive): `office`, `facet`, `ion`, `slice`, `wisp`, `berlin`. `--method com` requires Visio + pywin32; `--method vsdx` patches `visio/theme/theme1.xml` directly; `--method auto` (default) tries COM first and falls back to `vsdx`.

Data linking (COM-only; requires Visio Plan 2 / Professional):

```bash
python3 scripts/data_link.py link-excel <vsdx> --workbook <xlsx> --sheet Sheet1 \
    --primary-key PartNumber --name inventory
python3 scripts/data_link.py link-csv <vsdx> --csv <csv> --primary-key SKU --name stock
python3 scripts/data_link.py link-sql <vsdx> --server tcp:db01,1433 --database INV \
    --query "SELECT * FROM dbo.Inventory" --primary-key PartNumber --name sql_inv
python3 scripts/data_link.py refresh <vsdx> [--recordset <name>]
python3 scripts/data_link.py attach-graphic <vsdx> --recordset inventory --graphic "Inventory DG"
```

Every successful operation is recorded in `<project>/data_link.json` so the configuration is inspectable, version-controlled, and re-applyable.

Finalisation:

```bash
python3 scripts/finalize_vsdx.py <project_path>
python3 scripts/finalize_vsdx.py <project_path> --repair-glue
python3 scripts/finalize_vsdx.py <project_path> --no-layout
python3 scripts/finalize_vsdx.py <project_path> --no-glue-fix --no-layout --no-compress  # verify only
python3 scripts/finalize_vsdx.py <project_path> --summary-path <out.json>
```

Four passes run by default: `glue-fix`, `layout`, `compress`, `verify-lock`. Each can be turned off with the matching `--no-<pass>` flag. Output lands under `<project>/vsdx_final/` (sibling of the input `vsdx_output/`). Exit code 0 = full parity; exit code 2 = any file failed or any lock check found a discrepancy.

Quality check:

```bash
python3 scripts/vsdx_quality_check.py <project>/vsdx_final/diagram.vsdx
python3 scripts/vsdx_quality_check.py <project>/vsdx_final/ --output report.json
python3 scripts/vsdx_quality_check.py <project>/vsdx_final/x.vsdx --backend com \
    --lock <project>/diagram_lock.md
python3 scripts/vsdx_quality_check.py <project>/vsdx_final/ --pretty --summary
```

Two backends: `vsdx` (default — stdlib `zipfile` + `xml.etree`, no install needed) and `com` (drives a live `Visio.InvisibleApp`, slower but inspects post-recalc state). Exit code `1` when any `error` was emitted; `warning` and `info` are surfaced but do not fail the run.

Export:

```bash
python3 scripts/vsdx_export.py pdf <project_path> --vsdx diagram.vsdx
python3 scripts/vsdx_export.py png <project_path> --vsdx diagram.vsdx --from 2 --to 5 --dpi 300
python3 scripts/vsdx_export.py svg <project_path> --vsdx diagram.vsdx --embed-fonts
python3 scripts/vsdx_export.py all <project_path> --vsdx diagram.vsdx
```

Outputs land under `<project_path>/exports/`. Rendering paths require pywin32 + a Visio install; without them the script reports document structure (page names, page count) but emits a `requires Visio installed` error for the actual render.

COM diagnostics (when COM-backed steps misbehave):

```bash
python3 scripts/com_helper.py selftest      # capability JSON, no Visio launch
python3 scripts/com_helper.py ping          # InvisibleApp + Version + clean Quit
```

`com_helper.py` is also imported by COM-driven scripts as a library — see its module docstring for `VisioCOM`, `batch_set_formulas`, `ensure_master`, `drop_master_at`, `connect_shapes`, `apply_theme`, `export_page`.

## Pipeline Disciplines

Per the visio-master blueprint:

- Phase boundaries are atomic. Each Step 7 command (finalisation, lint, export) runs in its own shell invocation; combining them in a single command breaks the gate-before-entry rule.
- The COM path is fidelity-preferred when Visio is installed. The fallback path (`vsdx_build.py`, `apply_theme.py --method vsdx`, `vsdx_quality_check.py --backend vsdx`) is intentionally narrower — `apply_theme.py --method auto` and similar default modes negotiate the choice automatically.
- A process-wide lock inside `com_helper.py` enforces sequential COM sessions; never parallelise `vsdx_export.py` against the same Visio process.
- `vsdx_build.py` mutates persisted state only; Drafter re-reads `diagram_lock.md` per page and authors XML by hand, never via batch generators.
- `vsdx_quality_check.py` runs against `vsdx_final/`, the post-finalisation output, mirroring ppt-master's pre-finalise checker discipline (the finalised state is the canonical surface to lint).

## Recommendations

- Keep one user-facing entry point per concern at the top level of `scripts/`. Cross-cutting helpers belong in `com_helper.py`.
- Prefer `--method auto` for `apply_theme.py` so the same command runs on Windows-with-Visio and CI hosts.
- Pin stencil and diagram catalogues by checking in the JSON outputs of `stencil_index.py scan` and the bundled `diagrams_index.json`.
- Run `com_helper.py selftest` before any COM-backed step the first time on a new host; the JSON report names the missing piece (pywin32, Visio version, makepy stubs) when something is off.
- Use `vsdx_export.py all` only after `finalize_vsdx.py` and `vsdx_quality_check.py` have signed off — re-rendering after fixes is cheaper than re-issuing assets.

## Related Docs

- [Skill Entry](../SKILL.md)
- [Architect Reference](../references/architect.md)
- [Drafter Reference](../references/drafter-base.md)
- [Stylist Reference](../references/stylist.md)
- [Shared Standards](../references/shared-standards.md)
- [Visio Pages XML Authoring](../references/visio-pages-xml.md)
- [Connectors](../references/connectors.md)
- [Data Graphics](../references/data-graphics.md)
- [COM Quick Reference](../references/com-quick-ref.md)
- [Visio Review Rubric](../references/visio-review.md)

_Last updated: 2026-06-14_
