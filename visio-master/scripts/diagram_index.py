"""diagram_index.py — visio-master diagram catalog CLI.

Single source of truth utility for the visio-master builder. It loads
``visio-master/templates/diagrams/diagrams_index.json`` (produced in
Phase 5) and exposes three subcommands so codegen, docs, and scaffolds
can consult one canonical catalog.

Subcommands
-----------
- ``list``                            print every diagram (id, family, template, validation set)
- ``query <id>``                      print the full record for a single diagram id
- ``scaffold <id> <project_path>``    create a starter project for a diagram

Usage
-----
    python diagram_index.py list
    python diagram_index.py list --family flowchart --json
    python diagram_index.py query bpmn-2-0
    python diagram_index.py query bpmn-2-0 --field key_masters
    python diagram_index.py scaffold uml-class ./out/my-class-diagram

Optional dependencies
---------------------
``pywin32`` (``import win32com.client``) and ``vsdx`` are imported lazily
and only used by scaffold templates that mention them. They are NEVER
required at parse time. If absent, the scaffold writes a TODO note and
prints a friendly hint instead of crashing.

Exit codes
----------
0 success; 1 user error (bad id, missing file, bad arguments);
2 environment error (broken JSON, COM error during scaffold probe).
"""
from __future__ import annotations

import argparse
import json
import string
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

# --------------------------------------------------------------------------- #
# Optional imports — never fail at parse time.                                #
# --------------------------------------------------------------------------- #
try:  # pragma: no cover - environment-dependent
    import win32com.client  # type: ignore[import-not-found]  # noqa: F401
    import pywintypes  # type: ignore[import-not-found]
    _HAVE_PYWIN32 = True
    _COM_ERROR: type[BaseException] = pywintypes.com_error  # type: ignore[attr-defined]
except Exception:  # pragma: no cover - tested only on win-less hosts
    _HAVE_PYWIN32 = False

    class _ComErrorSentinel(Exception):
        """Stand-in so ``except _COM_ERROR`` clauses always parse."""

    _COM_ERROR = _ComErrorSentinel

try:  # pragma: no cover - environment-dependent
    import vsdx  # type: ignore[import-not-found]  # noqa: F401
    _HAVE_VSDX = True
except Exception:  # pragma: no cover
    _HAVE_VSDX = False


# --------------------------------------------------------------------------- #
# Paths & schema constants                                                    #
# --------------------------------------------------------------------------- #
_THIS = Path(__file__).resolve()
_VM_ROOT = _THIS.parent.parent  # visio-master/
_INDEX_PATH = _VM_ROOT / "templates" / "diagrams" / "diagrams_index.json"

_SCHEMA_KEYS: tuple[str, ...] = (
    "id",
    "display_name",
    "family",
    "template",
    "workspace_id",
    "built_in_stencil_enum",
    "primary_stencils",
    "canvas",
    "route_style",
    "place_style",
    "theme",
    "validation_rule_set",
    "key_masters",
    "key_user_cells",
    "add_ons",
    "description",
)


@dataclass(frozen=True)
class IndexLoadResult:
    """Container for the loaded index plus the path it came from."""

    path: Path
    diagrams: list[dict[str, Any]]
    schema_version: str | None


# --------------------------------------------------------------------------- #
# Loading & lookups                                                           #
# --------------------------------------------------------------------------- #
def _resolve_index_path(explicit: Path | None) -> Path:
    """Return the explicit path if given, otherwise the bundled default."""
    return Path(explicit).resolve() if explicit else _INDEX_PATH


def load_index(path: Path | None = None) -> IndexLoadResult:
    """Load and lightly validate the diagrams index.

    Raises ``FileNotFoundError`` if missing and ``ValueError`` if the file
    parses but does not look like the expected schema.
    """
    target = _resolve_index_path(path)
    if not target.exists():
        raise FileNotFoundError(
            f"diagrams_index.json not found at {target} "
            "(expected to be produced in Phase 5)"
        )
    try:
        raw = json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{target} is not valid JSON: {exc}") from exc

    # Accept both {schema_version, diagrams: [...]} and a bare list.
    diagrams: list[dict[str, Any]]
    schema_version: str | None
    if isinstance(raw, dict) and "diagrams" in raw:
        diagrams = list(raw.get("diagrams") or [])
        schema_version = raw.get("schema_version")
    elif isinstance(raw, list):
        diagrams = list(raw)
        schema_version = None
    else:
        raise ValueError(
            f"{target} root must be a list or an object with a 'diagrams' key"
        )

    for i, entry in enumerate(diagrams):
        if not isinstance(entry, dict):
            raise ValueError(f"diagrams[{i}] must be a JSON object, got {type(entry).__name__}")
        if "id" not in entry:
            raise ValueError(f"diagrams[{i}] is missing the required 'id' key")
    return IndexLoadResult(path=target, diagrams=diagrams, schema_version=schema_version)


def find_diagram(diagrams: Iterable[dict[str, Any]], diagram_id: str) -> dict[str, Any]:
    """Return the entry whose ``id`` equals ``diagram_id`` or raise ``KeyError``."""
    for entry in diagrams:
        if entry.get("id") == diagram_id:
            return entry
    raise KeyError(diagram_id)


def _suggest_ids(diagrams: Iterable[dict[str, Any]], needle: str, limit: int = 5) -> list[str]:
    """Cheap prefix/substring match used when ``query`` misses."""
    needle = needle.lower()
    hits: list[tuple[int, str]] = []
    for entry in diagrams:
        ident = str(entry.get("id", ""))
        low = ident.lower()
        if low.startswith(needle):
            hits.append((0, ident))
        elif needle in low:
            hits.append((1, ident))
    hits.sort()
    return [h[1] for h in hits[:limit]]


# --------------------------------------------------------------------------- #
# Subcommand: list                                                            #
# --------------------------------------------------------------------------- #
def cmd_list(args: argparse.Namespace) -> int:
    try:
        result = load_index(args.index)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    rows = result.diagrams
    if args.family:
        rows = [d for d in rows if d.get("family") == args.family]

    if args.json:
        payload = {
            "ok": True,
            "index_path": str(result.path),
            "schema_version": result.schema_version,
            "count": len(rows),
            "diagrams": [
                {
                    "id": d.get("id"),
                    "family": d.get("family"),
                    "display_name": d.get("display_name"),
                    "template": d.get("template"),
                    "validation_rule_set": d.get("validation_rule_set"),
                }
                for d in rows
            ],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    # Human-friendly text table.
    if not rows:
        print(f"(no diagrams matched; index has {len(result.diagrams)} total entries)")
        return 0
    widths = {
        "id": max(len("id"), max(len(str(d.get("id", ""))) for d in rows)),
        "family": max(len("family"), max(len(str(d.get("family", "") or "")) for d in rows)),
        "template": max(len("template"), max(len(str(d.get("template", "") or "")) for d in rows)),
    }
    header = f"{'id'.ljust(widths['id'])}  {'family'.ljust(widths['family'])}  {'template'.ljust(widths['template'])}  display_name"
    print(header)
    print("-" * len(header))
    for d in rows:
        ident = str(d.get("id", ""))
        family = str(d.get("family", "") or "-")
        template = str(d.get("template", "") or "-")
        display = str(d.get("display_name", "") or "-")
        print(
            f"{ident.ljust(widths['id'])}  "
            f"{family.ljust(widths['family'])}  "
            f"{template.ljust(widths['template'])}  "
            f"{display}"
        )
    print(f"\n{len(rows)} diagram(s) listed from {result.path}")
    return 0


# --------------------------------------------------------------------------- #
# Subcommand: query                                                           #
# --------------------------------------------------------------------------- #
def cmd_query(args: argparse.Namespace) -> int:
    try:
        result = load_index(args.index)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    try:
        entry = find_diagram(result.diagrams, args.diagram_id)
    except KeyError:
        suggestions = _suggest_ids(result.diagrams, args.diagram_id)
        msg = f"error: diagram id '{args.diagram_id}' not found"
        if suggestions:
            msg += f" (did you mean: {', '.join(suggestions)}?)"
        print(msg, file=sys.stderr)
        return 1

    if args.field:
        if args.field not in entry:
            print(
                f"error: field '{args.field}' not present on diagram '{args.diagram_id}'",
                file=sys.stderr,
            )
            return 1
        value = entry[args.field]
        if isinstance(value, (dict, list)):
            print(json.dumps(value, ensure_ascii=False, indent=2))
        else:
            print(value)
        return 0

    print(json.dumps(entry, ensure_ascii=False, indent=2))
    return 0


# --------------------------------------------------------------------------- #
# Subcommand: scaffold                                                        #
# --------------------------------------------------------------------------- #
_BUILD_PY_TEMPLATE = string.Template('''\
"""build.py — generated scaffold for diagram '$diagram_id'.

Generated by visio-master/scripts/diagram_index.py. Edit freely.

Strategy
--------
1. Open the bundled template short-name '$template' via Visio COM
   (``Documents.AddEx``). When pywin32 is unavailable, fall back to
   composing a .vsdx with the ``vsdx`` package.
2. Dock the primary stencils so masters resolve by NameU.
3. Drop the diagram's key masters (see ``KEY_MASTERS``) and wire them
   with Dynamic connectors using the diagram's ``route_style`` /
   ``place_style`` defaults.
4. Save as ``out/$diagram_id.vsdx`` next to this script.

Required diagram metadata is in ``diagram_meta.json``.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
META = json.loads((HERE / "diagram_meta.json").read_text(encoding="utf-8"))

DIAGRAM_ID = META["id"]
TEMPLATE = META.get("template")
PRIMARY_STENCILS = META.get("primary_stencils") or []
KEY_MASTERS = META.get("key_masters") or []
ROUTE_STYLE = META.get("route_style", 0)
PLACE_STYLE = META.get("place_style", 0)


def build_via_com(out_path: Path) -> int:
    try:
        import win32com.client  # type: ignore[import-not-found]
        import pywintypes  # type: ignore[import-not-found]
    except ImportError:
        print("pywin32 not installed — skipping COM build path.", file=sys.stderr)
        return 1
    try:
        app = win32com.client.DispatchEx("Visio.Application")
        app.Visible = False
        try:
            doc = app.Documents.AddEx(TEMPLATE or "", 0, 0, 0)  # visMSDefault
            page = doc.Pages.Item(1)
            page.PageSheet.CellsU("RouteStyle").FormulaU = str(ROUTE_STYLE)
            page.PageSheet.CellsU("PlaceStyle").FormulaU = str(PLACE_STYLE)
            # TODO: Drop KEY_MASTERS via doc.Masters.ItemU(<name>) and
            # connect them with Dynamic connector. Save the result.
            out_path.parent.mkdir(parents=True, exist_ok=True)
            doc.SaveAs(str(out_path))
            doc.Close()
        finally:
            app.Quit()
    except pywintypes.com_error as exc:  # noqa: BLE001
        print(f"COM error during build: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"ok": True, "path": str(out_path), "via": "com"}))
    return 0


def build_via_vsdx(out_path: Path) -> int:
    try:
        import vsdx  # type: ignore[import-not-found]  # noqa: F401
    except ImportError:
        print("vsdx not installed — cannot use the file-mode fallback.", file=sys.stderr)
        return 1
    # TODO: synthesise an empty .vsdx and inject masters via vsdx APIs.
    print("vsdx fallback is a TODO — see scaffold README for guidance.", file=sys.stderr)
    return 1


def main() -> int:
    out = HERE / "out" / f"{DIAGRAM_ID}.vsdx"
    rc = build_via_com(out)
    if rc == 1:
        rc = build_via_vsdx(out)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
''')

_README_TEMPLATE = string.Template("""\
# $display_name — visio-master scaffold

Generated by `visio-master/scripts/diagram_index.py scaffold $diagram_id`.

| Key | Value |
| --- | --- |
| id | `$diagram_id` |
| family | `$family` |
| template | `$template` |
| workspace_id | `$workspace_id` |
| validation rule set | `$validation_rule_set` |
| route_style | `$route_style` |
| place_style | `$place_style` |

## Files

- `diagram_meta.json` — verbatim copy of the diagram entry from `diagrams_index.json`.
- `build.py` — runnable scaffold. Two execution paths:
  1. **COM** (`pywin32`) — preferred; opens the real Visio template.
  2. **vsdx** (`vsdx` package) — file-mode fallback when Visio is unavailable.
- `out/` — generated `.vsdx` lives here after `python build.py` succeeds.

## Run

```bash
python build.py
```

If neither pywin32 nor vsdx is installed the script prints a hint and
exits non-zero — install at least one, then re-run.

## Key masters

$key_masters_block

## Primary stencils

$primary_stencils_block
""")


def _bullet_list(items: Iterable[str]) -> str:
    items = [str(x) for x in items]
    if not items:
        return "_(none documented in the index)_"
    return "\n".join(f"- `{x}`" for x in items)


def cmd_scaffold(args: argparse.Namespace) -> int:
    try:
        result = load_index(args.index)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    try:
        entry = find_diagram(result.diagrams, args.diagram_id)
    except KeyError:
        suggestions = _suggest_ids(result.diagrams, args.diagram_id)
        msg = f"error: diagram id '{args.diagram_id}' not found"
        if suggestions:
            msg += f" (did you mean: {', '.join(suggestions)}?)"
        print(msg, file=sys.stderr)
        return 1

    project_path = Path(args.project_path).resolve()
    if project_path.exists() and any(project_path.iterdir()) and not args.force:
        print(
            f"error: {project_path} is not empty; pass --force to overwrite",
            file=sys.stderr,
        )
        return 1
    project_path.mkdir(parents=True, exist_ok=True)

    # 1. Verbatim metadata.
    meta_path = project_path / "diagram_meta.json"
    meta_path.write_text(
        json.dumps(entry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    # 2. build.py — runnable scaffold.
    build_py = _BUILD_PY_TEMPLATE.substitute(
        diagram_id=entry.get("id", args.diagram_id),
        template=entry.get("template") or "",
    )
    (project_path / "build.py").write_text(build_py, encoding="utf-8")

    # 3. README.md — human guide.
    readme = _README_TEMPLATE.substitute(
        display_name=entry.get("display_name") or args.diagram_id,
        diagram_id=entry.get("id", args.diagram_id),
        family=entry.get("family") or "-",
        template=entry.get("template") or "-",
        workspace_id=entry.get("workspace_id") or "-",
        validation_rule_set=entry.get("validation_rule_set") or "-",
        route_style=entry.get("route_style", "-"),
        place_style=entry.get("place_style", "-"),
        key_masters_block=_bullet_list(entry.get("key_masters") or []),
        primary_stencils_block=_bullet_list(entry.get("primary_stencils") or []),
    )
    (project_path / "README.md").write_text(readme, encoding="utf-8")

    # 4. Friendly capability probe — never aborts the scaffold.
    notes: list[str] = []
    if not _HAVE_PYWIN32:
        notes.append("pywin32 not detected; COM build path will skip at runtime.")
    if not _HAVE_VSDX:
        notes.append("vsdx not detected; file-mode fallback will skip at runtime.")
    if _HAVE_PYWIN32:
        try:
            # Cheap probe — do not actually instantiate Visio here, just confirm
            # the COM dispatcher loads. Catch the documented com_error type.
            import win32com.client  # type: ignore[import-not-found]  # noqa: F401
        except _COM_ERROR as exc:  # pragma: no cover - environment-dependent
            notes.append(f"pywin32 imported but COM probe raised: {exc}")

    summary = {
        "ok": True,
        "diagram_id": entry.get("id"),
        "project_path": str(project_path),
        "files": [
            str(meta_path.relative_to(project_path)),
            "build.py",
            "README.md",
        ],
        "have_pywin32": _HAVE_PYWIN32,
        "have_vsdx": _HAVE_VSDX,
        "notes": notes,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


# --------------------------------------------------------------------------- #
# CLI plumbing                                                                #
# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="diagram_index",
        description="Query and scaffold from the visio-master diagrams catalog.",
    )
    parser.add_argument(
        "--index",
        type=Path,
        default=None,
        help=(
            "path to diagrams_index.json (default: "
            "visio-master/templates/diagrams/diagrams_index.json)"
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="print every diagram in the catalog")
    p_list.add_argument("--family", help="filter by family (e.g. flowchart, software, network)")
    p_list.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    p_list.set_defaults(func=cmd_list)

    p_query = sub.add_parser("query", help="print one diagram entry by id")
    p_query.add_argument("diagram_id", help="diagram id, e.g. bpmn-2-0")
    p_query.add_argument(
        "--field",
        help="print only this top-level field (e.g. key_masters, canvas)",
    )
    p_query.set_defaults(func=cmd_query)

    p_scaffold = sub.add_parser(
        "scaffold",
        help="create a starter Python project for a given diagram id",
    )
    p_scaffold.add_argument("diagram_id", help="diagram id, e.g. uml-class")
    p_scaffold.add_argument("project_path", help="destination directory for the scaffold")
    p_scaffold.add_argument(
        "--force",
        action="store_true",
        help="allow scaffolding into a non-empty directory",
    )
    p_scaffold.set_defaults(func=cmd_scaffold)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
