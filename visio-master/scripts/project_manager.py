#!/usr/bin/env python3
"""Visio Master project management helpers.

CLI utility for the visio-master skill. Mirrors `ppt-master/scripts/project_manager.py`
but is retargeted to Visio drawings (`.vsdx`) and the visio-master pipeline (Architect /
Drafter / Stylist).

Usage:
    python project_manager.py init <project_name> [--format a3-landscape] [--dir <path>]
    python project_manager.py import-sources <project_path> <src1> [<src2> ...] [--move | --copy]
    python project_manager.py validate <project_path>
    python project_manager.py list-pages <vsdx_file>

Subcommands
-----------
init             Create a new project under <base>/<name>_<format>_<YYYYMMDD>/ with the
                 canonical directory tree (sources/, images/, templates/, vsdx_output/,
                 exports/, backup/, notes/, pages/, comments/, data_links/) plus skeleton
                 `diagram_spec.md` and `diagram_lock.md` files.
import-sources  Copy or move source files into <project>/sources/. Recognises
                 PDF / DOCX / XLSX / CSV / TXT / MD / .vsdx examples; unknown
                 suffixes are archived as-is with a note.
validate         Check that the project directory has the expected structure and
                 required files (diagram_spec.md, diagram_lock.md). Emits a JSON
                 summary on success and a non-zero exit on hard errors.
list-pages       Open an existing `.vsdx` and list its pages. Uses the optional
                 `vsdx` library when available; degrades gracefully (printing a
                 helpful message) when the library is missing or the file cannot
                 be parsed.

Optional dependencies (NOT installed by this script):
    vsdx        — read-side .vsdx parsing for `list-pages`. https://pypi.org/project/vsdx/
    pywin32     — only consulted as a final fallback for `list-pages` on Windows.
                  Imported lazily; no hard requirement.

The `init`, `import-sources`, and `validate` subcommands have no third-party
dependencies (Python 3.10+ standard library only).

Examples:
    python project_manager.py init my_runbook --format a4-landscape
    python project_manager.py import-sources ./projects/my_runbook_a4-landscape_20260614 \
        spec.pdf data.xlsx notes.md --copy
    python project_manager.py validate ./projects/my_runbook_a4-landscape_20260614
    python project_manager.py list-pages ./projects/my_runbook_a4-landscape_20260614/exports/runbook.vsdx
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterable, Sequence

# ---------------------------------------------------------------------------
# Constants & canvas catalogue (subset of references/canvas-formats.md)
# ---------------------------------------------------------------------------

SOURCE_DIRNAME = "sources"
IMAGES_DIRNAME = "images"
TEMPLATES_DIRNAME = "templates"
VSDX_OUTPUT_DIRNAME = "vsdx_output"
EXPORTS_DIRNAME = "exports"
BACKUP_DIRNAME = "backup"
NOTES_DIRNAME = "notes"
PAGES_DIRNAME = "pages"
COMMENTS_DIRNAME = "comments"
DATA_LINKS_DIRNAME = "data_links"

REQUIRED_DIRS: tuple[str, ...] = (
    SOURCE_DIRNAME,
    IMAGES_DIRNAME,
    TEMPLATES_DIRNAME,
    VSDX_OUTPUT_DIRNAME,
    EXPORTS_DIRNAME,
    BACKUP_DIRNAME,
    NOTES_DIRNAME,
    PAGES_DIRNAME,
    COMMENTS_DIRNAME,
    DATA_LINKS_DIRNAME,
)

REQUIRED_FILES: tuple[str, ...] = (
    "diagram_spec.md",
    "diagram_lock.md",
    "README.md",
)

# Recognised source suffixes — drives import-sources classification.
PDF_SUFFIXES: frozenset[str] = frozenset({".pdf"})
DOC_SUFFIXES: frozenset[str] = frozenset(
    {".docx", ".doc", ".odt", ".rtf", ".html", ".htm", ".epub"}
)
EXCEL_SUFFIXES: frozenset[str] = frozenset({".xlsx", ".xlsm", ".xls"})
TABLE_TEXT_SUFFIXES: frozenset[str] = frozenset({".csv", ".tsv"})
TEXT_SUFFIXES: frozenset[str] = frozenset({".txt"})
MARKDOWN_SUFFIXES: frozenset[str] = frozenset({".md", ".markdown"})
VSDX_SUFFIXES: frozenset[str] = frozenset({".vsdx", ".vsd", ".vssx", ".vstx", ".vsdm"})
IMAGE_SUFFIXES: frozenset[str] = frozenset(
    {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tiff", ".tif", ".svg", ".emf", ".wmf"}
)


@dataclass(frozen=True)
class CanvasFormat:
    """Canvas catalog entry. Width/height are in `units`."""

    name: str
    width: float
    height: float
    units: str  # one of: "in", "mm"
    orientation: str  # "landscape" | "portrait"
    notes: str = ""

    @property
    def dimensions(self) -> str:
        return f"{self.width} × {self.height} {self.units}"


# Subset of references/canvas-formats.md sufficient for the canonical defaults.
CANVAS_FORMATS: dict[str, CanvasFormat] = {
    # ISO A-series (metric default).
    "a0-landscape": CanvasFormat("A0 landscape", 1189, 841, "mm", "landscape", "wall poster"),
    "a0-portrait": CanvasFormat("A0 portrait", 841, 1189, "mm", "portrait"),
    "a1-landscape": CanvasFormat("A1 landscape", 841, 594, "mm", "landscape", "P&ID, large network"),
    "a1-portrait": CanvasFormat("A1 portrait", 594, 841, "mm", "portrait"),
    "a2-landscape": CanvasFormat("A2 landscape", 594, 420, "mm", "landscape"),
    "a2-portrait": CanvasFormat("A2 portrait", 420, 594, "mm", "portrait"),
    "a3-landscape": CanvasFormat("A3 landscape", 420, 297, "mm", "landscape", "swim-lane / BPMN"),
    "a3-portrait": CanvasFormat("A3 portrait", 297, 420, "mm", "portrait"),
    "a4-landscape": CanvasFormat("A4 landscape", 297, 210, "mm", "landscape", "single-page summary"),
    "a4-portrait": CanvasFormat("A4 portrait", 210, 297, "mm", "portrait", "runbooks / inserts"),
    "a5-landscape": CanvasFormat("A5 landscape", 210, 148, "mm", "landscape"),
    "a5-portrait": CanvasFormat("A5 portrait", 148, 210, "mm", "portrait"),
    # ANSI / US-customary.
    "letter-landscape": CanvasFormat("Letter landscape", 11.0, 8.5, "in", "landscape", "calendar / workflow"),
    "letter-portrait": CanvasFormat("Letter portrait", 8.5, 11.0, "in", "portrait", "basic flowchart (US)"),
    "legal-landscape": CanvasFormat("Legal landscape", 14.0, 8.5, "in", "landscape"),
    "legal-portrait": CanvasFormat("Legal portrait", 8.5, 14.0, "in", "portrait"),
    "tabloid-landscape": CanvasFormat("Tabloid landscape", 17.0, 11.0, "in", "landscape", "swim-lane / BPMN (US)"),
    "tabloid-portrait": CanvasFormat("Tabloid portrait", 11.0, 17.0, "in", "portrait"),
    "ansi-c-landscape": CanvasFormat("ANSI C landscape", 22.0, 17.0, "in", "landscape"),
    "ansi-d-landscape": CanvasFormat("ANSI D landscape", 34.0, 22.0, "in", "landscape", "floor plan"),
    "ansi-e-landscape": CanvasFormat("ANSI E landscape", 44.0, 34.0, "in", "landscape", "PFD / P&ID / site plan"),
    # Architectural.
    "arch-d-landscape": CanvasFormat("Arch D landscape", 36.0, 24.0, "in", "landscape", "floor plan"),
    "arch-e-landscape": CanvasFormat("Arch E landscape", 48.0, 36.0, "in", "landscape", "site plan"),
}

# Common alias map: short user-facing names → canonical canvas IDs.
CANVAS_ALIASES: dict[str, str] = {
    "letter": "letter-landscape",
    "a4": "a4-landscape",
    "a3": "a3-landscape",
    "a1": "a1-landscape",
    "a0": "a0-landscape",
    "tabloid": "tabloid-landscape",
    "ansi-d": "ansi-d-landscape",
    "ansi-e": "ansi-e-landscape",
    "arch-d": "arch-d-landscape",
    "arch-e": "arch-e-landscape",
}


def normalize_canvas_format(value: str) -> str:
    """Resolve user-supplied canvas tokens to a canonical canvas id."""
    key = value.strip().lower()
    if key in CANVAS_FORMATS:
        return key
    return CANVAS_ALIASES.get(key, key)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ensure_unique_path(path: Path) -> Path:
    """Return `path` if free, otherwise append `_2`, `_3`, ... before the suffix."""
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    counter = 2
    while True:
        candidate = path.with_name(f"{stem}_{counter}{suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def _emit(summary: dict[str, object]) -> None:
    """Print a JSON-ish summary to stdout (single-line, ASCII-safe)."""
    print(json.dumps(summary, ensure_ascii=False, indent=2, default=str))


def _classify_suffix(suffix: str) -> str:
    """Classify a file suffix into a coarse content kind for the import summary."""
    suffix = suffix.lower()
    if suffix in PDF_SUFFIXES:
        return "pdf"
    if suffix in DOC_SUFFIXES:
        return "document"
    if suffix in EXCEL_SUFFIXES:
        return "spreadsheet"
    if suffix in TABLE_TEXT_SUFFIXES:
        return "table"
    if suffix in TEXT_SUFFIXES:
        return "text"
    if suffix in MARKDOWN_SUFFIXES:
        return "markdown"
    if suffix in VSDX_SUFFIXES:
        return "vsdx"
    if suffix in IMAGE_SUFFIXES:
        return "image"
    return "other"


# ---------------------------------------------------------------------------
# Skeleton authoring
# ---------------------------------------------------------------------------


def _diagram_spec_skeleton(project_name: str, canvas_id: str, canvas: CanvasFormat) -> str:
    """Render the `diagram_spec.md` skeleton (Architect's narrative, 11 sections)."""
    today = datetime.now().strftime("%Y-%m-%d")
    return (
        f"# Diagram Specification — {project_name}\n\n"
        f"> Architect-authored narrative. Edit through the Architect role only.\n"
        f"> Canonical execution contract lives in `diagram_lock.md` (parseable).\n\n"
        f"- Canvas format: `{canvas_id}` ({canvas.dimensions}, {canvas.orientation})\n"
        f"- Created: {today}\n\n"
        "## I. Project Information\n\n"
        "- Audience: TBD\n"
        "- Use case: TBD\n"
        "- Presentation mode: TBD\n"
        "- Page count: TBD\n"
        "- Primary diagram type: TBD\n\n"
        "## II. Communication Mode\n\n"
        "- Mode: TBD (`pyramid` / `narrative` / `instructional` / `showcase` / `briefing` / `custom`)\n\n"
        "## III. Visual Style\n\n"
        "- Visual style: TBD (e.g. `engineering-blueprint`, `executive-clean`, `bpmn-strict`)\n\n"
        "## IV. Color Palette\n\n"
        "- primary: TBD\n"
        "- accent: TBD\n"
        "- text: TBD\n\n"
        "## V. Typography\n\n"
        "- title: TBD\n"
        "- body: TBD\n\n"
        "## VI. Stencils\n\n"
        "- Primary stencil set: TBD\n"
        "- Connector style: TBD\n\n"
        "## VII. Layout & Connector Routing\n\n"
        "- Layout algorithm: TBD\n"
        "- Connector routing: TBD\n\n"
        "## VIII. Image Acquisition\n\n"
        "- Acquire via: TBD (`ai` / `web` / `user` / `placeholder` / `formula`)\n\n"
        "## IX. Content Outline (per-page briefs)\n\n"
        "- P01: TBD\n\n"
        "## X. Data Linking (optional)\n\n"
        "- Enabled: false\n\n"
        "## XI. Forbidden Patterns\n\n"
        "- (carried into `diagram_lock.md ## forbidden`)\n"
    )


def _diagram_lock_skeleton(project_name: str, canvas_id: str, canvas: CanvasFormat) -> str:
    """Render the `diagram_lock.md` parseable contract skeleton."""
    return (
        f"# Diagram Lock — {project_name}\n\n"
        "> Parseable execution contract. Drafter re-reads this file before authoring\n"
        "> every Visio Page. Hand-edits after pages exist are forbidden — propagate\n"
        "> changes through `scripts/update_diagram_lock.py` instead.\n\n"
        "## canvas\n\n"
        f"- format: {canvas_id}\n"
        f"- units: {canvas.units}\n"
        f"- width: {canvas.width}\n"
        f"- height: {canvas.height}\n"
        f"- orientation: {canvas.orientation}\n"
        "- dpi: 96\n"
        "- page_scale: 1:1\n\n"
        "## diagram_type\n\n"
        "- primary_diagram_type: TBD\n"
        "- template_basename: TBD\n\n"
        "## mode\n\n"
        "- value: TBD\n\n"
        "## visual_style\n\n"
        "- value: TBD\n\n"
        "## theme\n\n"
        "- id: TBD\n\n"
        "## colors\n\n"
        "- primary: TBD\n"
        "- accent: TBD\n"
        "- text: TBD\n\n"
        "## typography\n\n"
        "- title: TBD\n"
        "- body: TBD\n\n"
        "## stencils\n\n"
        "- set: TBD\n"
        "- connector_style: right-angle\n"
        "- connector_default_routing: flowchart\n\n"
        "## images\n\n"
        "- acquire_via: placeholder\n\n"
        "## layout\n\n"
        "- algorithm: TBD\n"
        "- spacing: normal\n\n"
        "## connectors\n\n"
        "- routing: flowchart\n"
        "- label_position: mid-line\n\n"
        "## page_rhythm\n\n"
        "- P01: anchor\n\n"
        "## page_layouts\n\n"
        "- P01: TBD\n\n"
        "## page_diagrams\n\n"
        "- P01: TBD\n\n"
        "## page_data_links\n\n"
        "- enabled: false\n\n"
        "## forbidden\n\n"
        "- (list patterns Drafter must not emit)\n"
    )


def _readme_skeleton(project_name: str, canvas_id: str, canvas: CanvasFormat) -> str:
    """Render the project-level README pointing at the canonical layout."""
    return (
        f"# {project_name}\n\n"
        f"- Canvas: `{canvas_id}` ({canvas.dimensions}, {canvas.orientation})\n"
        f"- Created: {datetime.now().strftime('%Y-%m-%d')}\n\n"
        "## Directories\n\n"
        "- `sources/`         source materials (PDF / DOCX / XLSX / CSV / TXT / MD / .vsdx examples)\n"
        "- `images/`          referenced image assets (project-wide pool)\n"
        "- `templates/`       project-local copies of page-layouts / themes / stencils\n"
        "- `pages/`           Drafter output: `<NN>_<page_name>.vsdx-page.xml`\n"
        "- `comments/`        per-page commentary (analogue of speaker notes)\n"
        "- `notes/`           working notes / per-step logs\n"
        "- `data_links/`      optional CSV / XLSX bound to shapes by Stylist\n"
        "- `vsdx_output/`     intermediate VSDX builds\n"
        "- `exports/`         final `.vsdx` (and optional PDF) deliverables\n"
        "- `backup/`          timestamped archives of `pages/` before update_diagram_lock.py runs\n\n"
        "## Canonical files\n\n"
        "- `diagram_spec.md`  Architect's narrative specification (11 sections)\n"
        "- `diagram_lock.md`  Drafter's parseable execution contract\n"
    )


# ---------------------------------------------------------------------------
# ProjectManager
# ---------------------------------------------------------------------------


@dataclass
class ImportSummary:
    """Outcome of `import-sources`. Lists are file paths or short notes."""

    archived: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    classified: dict[str, list[str]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "archived": self.archived,
            "skipped": self.skipped,
            "notes": self.notes,
            "classified": self.classified,
        }


class ProjectManager:
    """Create, populate, and validate visio-master project folders."""

    def __init__(self, base_dir: str | Path | None = None) -> None:
        self.base_dir: Path = (
            Path(base_dir) if base_dir is not None else Path.cwd() / "projects"
        )

    # -- init --------------------------------------------------------------

    def init_project(
        self,
        project_name: str,
        canvas_format: str = "a3-landscape",
        base_dir: str | Path | None = None,
    ) -> Path:
        """Create a new project directory with the canonical layout."""
        base_path = Path(base_dir) if base_dir is not None else self.base_dir

        normalized = normalize_canvas_format(canvas_format)
        if normalized not in CANVAS_FORMATS:
            available = ", ".join(sorted(CANVAS_FORMATS))
            raise ValueError(
                f"Unsupported canvas format: {canvas_format!r} "
                f"(available: {available}; common aliases: a3, a4, letter, tabloid)"
            )
        canvas = CANVAS_FORMATS[normalized]

        date_str = datetime.now().strftime("%Y%m%d")
        project_dir_name = f"{project_name}_{normalized}_{date_str}"
        project_path = base_path / project_dir_name

        if project_path.exists():
            raise FileExistsError(f"Project directory already exists: {project_path}")

        for rel in REQUIRED_DIRS:
            (project_path / rel).mkdir(parents=True, exist_ok=True)

        (project_path / "diagram_spec.md").write_text(
            _diagram_spec_skeleton(project_name, normalized, canvas), encoding="utf-8"
        )
        (project_path / "diagram_lock.md").write_text(
            _diagram_lock_skeleton(project_name, normalized, canvas), encoding="utf-8"
        )
        (project_path / "README.md").write_text(
            _readme_skeleton(project_name, normalized, canvas), encoding="utf-8"
        )

        return project_path

    # -- import-sources ----------------------------------------------------

    def import_sources(
        self,
        project_path: str | Path,
        source_items: Sequence[str],
        move: bool = False,
        copy: bool = False,
    ) -> ImportSummary:
        """Move or copy source files into `<project>/sources/` with classification."""
        if move and copy:
            raise ValueError("--move and --copy are mutually exclusive")
        project_dir = Path(project_path)
        if not project_dir.exists() or not project_dir.is_dir():
            raise FileNotFoundError(f"Project directory not found: {project_dir}")
        if not source_items:
            raise ValueError("At least one source path is required")

        sources_dir = project_dir / SOURCE_DIRNAME
        sources_dir.mkdir(parents=True, exist_ok=True)

        # Default behaviour: copy. `--move` flips that.
        effective_move = bool(move)
        summary = ImportSummary()

        for raw_item in source_items:
            source_path = Path(raw_item).expanduser()
            if not source_path.exists():
                summary.skipped.append(f"{raw_item}: path not found")
                continue
            if source_path.is_dir():
                summary.skipped.append(f"{raw_item}: directories are not supported")
                continue

            destination = _ensure_unique_path(sources_dir / source_path.name)
            try:
                if effective_move:
                    shutil.move(str(source_path), str(destination))
                else:
                    shutil.copy2(source_path, destination)
            except (OSError, shutil.Error) as exc:
                summary.skipped.append(f"{raw_item}: import failed ({exc})")
                continue

            kind = _classify_suffix(destination.suffix)
            summary.archived.append(str(destination))
            summary.classified.setdefault(kind, []).append(str(destination))

            if kind == "other":
                summary.notes.append(
                    f"{destination.name}: archived as-is; suffix not recognised "
                    "(no automatic Markdown conversion)"
                )
            elif kind == "vsdx":
                summary.notes.append(
                    f"{destination.name}: archived as a Visio reference; "
                    "Drafter must NOT copy proprietary stencil masters without an "
                    "audit-stencil-licensing pass"
                )

        return summary

    # -- validate ----------------------------------------------------------

    def validate_project(
        self, project_path: str | Path
    ) -> tuple[bool, list[str], list[str]]:
        """Return (is_valid, errors, warnings) for the project structure."""
        errors: list[str] = []
        warnings: list[str] = []
        project_dir = Path(project_path)

        if not project_dir.exists():
            errors.append(f"Project directory not found: {project_dir}")
            return False, errors, warnings
        if not project_dir.is_dir():
            errors.append(f"Project path is not a directory: {project_dir}")
            return False, errors, warnings

        for rel in REQUIRED_DIRS:
            sub = project_dir / rel
            if not sub.exists():
                errors.append(f"Missing required directory: {rel}/")
            elif not sub.is_dir():
                errors.append(f"Required path is not a directory: {rel}/")

        for rel in REQUIRED_FILES:
            file_path = project_dir / rel
            if not file_path.exists():
                errors.append(f"Missing required file: {rel}")
            elif file_path.stat().st_size == 0:
                warnings.append(f"Required file is empty: {rel}")

        # Soft warnings: empty sources/, no pages yet, etc.
        sources_dir = project_dir / SOURCE_DIRNAME
        if sources_dir.is_dir():
            if not any(sources_dir.iterdir()):
                warnings.append("sources/ is empty (run import-sources or drop files in)")

        pages_dir = project_dir / PAGES_DIRNAME
        if pages_dir.is_dir():
            if not any(pages_dir.glob("*.vsdx-page.xml")):
                warnings.append(
                    "pages/ has no `*.vsdx-page.xml` yet (Drafter has not run)"
                )

        # Lock-vs-spec: confirm both reference the same canvas if both readable.
        lock_path = project_dir / "diagram_lock.md"
        spec_path = project_dir / "diagram_spec.md"
        if lock_path.is_file() and spec_path.is_file():
            try:
                lock_canvas = _grep_first_field(lock_path, "format")
                spec_canvas = _grep_first_field(spec_path, "Canvas format")
                if lock_canvas and spec_canvas and lock_canvas not in spec_canvas:
                    warnings.append(
                        f"diagram_lock canvas ({lock_canvas}) does not appear in diagram_spec ({spec_canvas})"
                    )
            except OSError as exc:
                warnings.append(f"could not cross-check spec/lock: {exc}")

        is_valid = not errors
        return is_valid, errors, warnings

    # -- list-pages --------------------------------------------------------

    def list_pages(self, vsdx_file: str | Path) -> dict[str, object]:
        """List pages in a `.vsdx`. Uses `vsdx` library if present; falls back gracefully."""
        target = Path(vsdx_file)
        if not target.exists():
            raise FileNotFoundError(f"VSDX file not found: {target}")
        if target.is_dir():
            raise IsADirectoryError(f"Expected a .vsdx file, got directory: {target}")

        suffix = target.suffix.lower()
        if suffix not in VSDX_SUFFIXES:
            return {
                "file": str(target),
                "backend": "none",
                "pages": [],
                "error": (
                    f"Unsupported file suffix: {suffix!r}. "
                    f"Expected one of: {', '.join(sorted(VSDX_SUFFIXES))}"
                ),
            }

        # Primary path: vsdx library.
        try:
            import vsdx  # type: ignore[import-not-found]
        except ImportError:
            vsdx = None  # type: ignore[assignment]

        if vsdx is not None:
            try:
                with vsdx.VisioFile(str(target)) as doc:  # type: ignore[attr-defined]
                    pages: list[dict[str, object]] = []
                    for index, page in enumerate(getattr(doc, "pages", []) or [], start=1):
                        pages.append(
                            {
                                "index": index,
                                "name": getattr(page, "name", f"Page-{index}"),
                                "page_id": getattr(page, "page_id", None)
                                or getattr(page, "ID", None),
                            }
                        )
                return {
                    "file": str(target),
                    "backend": "vsdx",
                    "page_count": len(pages),
                    "pages": pages,
                }
            except FileNotFoundError as exc:
                return {
                    "file": str(target),
                    "backend": "vsdx",
                    "pages": [],
                    "error": f"FileNotFoundError: {exc}",
                }
            except KeyError as exc:
                return {
                    "file": str(target),
                    "backend": "vsdx",
                    "pages": [],
                    "error": f"KeyError parsing VSDX OPC parts: {exc}",
                }
            except Exception as exc:  # vsdx lib raises a wide variety of errors
                return {
                    "file": str(target),
                    "backend": "vsdx",
                    "pages": [],
                    "error": f"vsdx parse failed ({type(exc).__name__}): {exc}",
                }

        # Fallback path: pywin32 COM (Windows + Visio install only).
        com_pages = _list_pages_via_com(target)
        if com_pages is not None:
            return com_pages

        return {
            "file": str(target),
            "backend": "none",
            "pages": [],
            "error": (
                "Neither `vsdx` nor a Visio COM session is available. "
                "Install `vsdx` (pip install vsdx) or run on a Windows host with Visio + pywin32."
            ),
        }


def _grep_first_field(path: Path, key: str) -> str | None:
    """Return the first `- key: value` or `Canvas format: …` value seen in `path`."""
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            for prefix in (f"- {key}:", f"{key}:"):
                if stripped.startswith(prefix):
                    return stripped[len(prefix):].strip(" `\"'")
    except FileNotFoundError:
        return None
    return None


def _list_pages_via_com(target: Path) -> dict[str, object] | None:
    """Optional Windows-only fallback: open the file via Visio COM and list pages.

    Returns None if pywin32 / COM are unavailable so the caller can present a
    consolidated friendly error.
    """
    try:
        import pywintypes  # type: ignore[import-not-found]
        import win32com.client  # type: ignore[import-not-found]
    except ImportError:
        return None

    visio = None
    document = None
    try:
        visio = win32com.client.DispatchEx("Visio.InvisibleApp")
        visio.AlertResponse = 7  # vbNo — suppress prompts
        document = visio.Documents.OpenEx(str(target), 0x10)  # visOpenRO
        pages = []
        for index, page in enumerate(document.Pages, start=1):
            pages.append(
                {
                    "index": index,
                    "name": page.Name,
                    "page_id": page.ID,
                    "background": bool(getattr(page, "Background", False)),
                }
            )
        return {
            "file": str(target),
            "backend": "pywin32-com",
            "page_count": len(pages),
            "pages": pages,
        }
    except pywintypes.com_error as exc:  # type: ignore[attr-defined]
        return {
            "file": str(target),
            "backend": "pywin32-com",
            "pages": [],
            "error": f"COM error: {exc}",
        }
    except FileNotFoundError as exc:
        return {
            "file": str(target),
            "backend": "pywin32-com",
            "pages": [],
            "error": f"FileNotFoundError: {exc}",
        }
    finally:
        try:
            if document is not None:
                document.Close()
        except Exception:  # pragma: no cover - best-effort cleanup
            pass
        try:
            if visio is not None:
                visio.Quit()
        except Exception:  # pragma: no cover - best-effort cleanup
            pass


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    """Build the argparse CLI surface with subcommands."""
    parser = argparse.ArgumentParser(
        prog="project_manager.py",
        description="Visio Master project management (init / import-sources / validate / list-pages).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True, metavar="<command>")

    # init
    p_init = sub.add_parser("init", help="Create a new visio-master project")
    p_init.add_argument("project_name", help="Logical project name (filesystem-friendly)")
    p_init.add_argument(
        "--format",
        dest="canvas_format",
        default="a3-landscape",
        help="Canvas format id (default: a3-landscape). Aliases: a3, a4, letter, tabloid",
    )
    p_init.add_argument(
        "--dir",
        dest="base_dir",
        default=None,
        help="Base directory for the project (default: ./projects)",
    )

    # import-sources
    p_imp = sub.add_parser("import-sources", help="Copy/move source files into <project>/sources/")
    p_imp.add_argument("project_path", help="Path to an existing project directory")
    p_imp.add_argument("sources", nargs="+", help="One or more source file paths")
    grp = p_imp.add_mutually_exclusive_group()
    grp.add_argument("--move", action="store_true", help="Move sources instead of copying")
    grp.add_argument("--copy", action="store_true", help="Copy sources (default)")

    # validate
    p_val = sub.add_parser("validate", help="Validate project structure and required files")
    p_val.add_argument("project_path", help="Path to the project directory")

    # list-pages
    p_lp = sub.add_parser("list-pages", help="List pages inside a .vsdx file")
    p_lp.add_argument("vsdx_file", help="Path to a `.vsdx` (or compatible) file")

    return parser


def _cmd_init(args: argparse.Namespace) -> int:
    manager = ProjectManager(base_dir=args.base_dir)
    try:
        project_path = manager.init_project(
            args.project_name,
            canvas_format=args.canvas_format,
            base_dir=args.base_dir,
        )
    except (FileExistsError, ValueError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    summary = {
        "command": "init",
        "status": "ok",
        "project_path": str(project_path),
        "canvas_format": normalize_canvas_format(args.canvas_format),
        "directories": list(REQUIRED_DIRS),
        "files": list(REQUIRED_FILES),
        "next_steps": [
            "Drop source files into sources/ (or use import-sources)",
            "Architect: read references/architect.md, then author diagram_spec.md & diagram_lock.md",
            "Drafter: emit pages/<NN>_*.vsdx-page.xml after Architect's lock is complete",
        ],
    }
    _emit(summary)
    return 0


def _cmd_import_sources(args: argparse.Namespace) -> int:
    manager = ProjectManager()
    try:
        result = manager.import_sources(
            args.project_path,
            args.sources,
            move=args.move,
            copy=args.copy,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    summary = {
        "command": "import-sources",
        "status": "ok",
        "project_path": str(Path(args.project_path)),
        "mode": "move" if args.move else "copy",
        **result.to_dict(),
    }
    _emit(summary)
    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    manager = ProjectManager()
    try:
        is_valid, errors, warnings = manager.validate_project(args.project_path)
    except FileNotFoundError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2
    summary = {
        "command": "validate",
        "status": "ok" if is_valid else "invalid",
        "project_path": str(Path(args.project_path)),
        "errors": errors,
        "warnings": warnings,
    }
    _emit(summary)
    return 0 if is_valid else 2


def _cmd_list_pages(args: argparse.Namespace) -> int:
    manager = ProjectManager()
    try:
        result = manager.list_pages(args.vsdx_file)
    except (FileNotFoundError, IsADirectoryError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    payload = {"command": "list-pages", "status": "ok", **result}
    _emit(payload)
    # Soft non-zero exit when no pages were extracted but the file existed.
    if not result.get("pages") and result.get("error"):
        return 3
    return 0


_DISPATCH = {
    "init": _cmd_init,
    "import-sources": _cmd_import_sources,
    "validate": _cmd_validate,
    "list-pages": _cmd_list_pages,
}


def main(argv: Iterable[str] | None = None) -> int:
    """CLI entry point."""
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    handler = _DISPATCH.get(args.command)
    if handler is None:  # pragma: no cover - argparse already enforces this
        parser.error(f"Unknown command: {args.command}")
    try:
        return handler(args)
    except KeyboardInterrupt:  # pragma: no cover - user interrupt
        print("[ERROR] Interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
