#!/usr/bin/env python3
"""Visio Master - VSDX Post-processing Tool.

Analogue of ppt-master's ``finalize_svg.py`` for the Visio pipeline. Reads
``.vsdx`` files emitted into a project's ``vsdx_output/`` and produces
finalised copies under ``vsdx_final/``. Four passes run by default, each
gated by a CLI flag:

    1. glue-fix       Ensure every 1-D connector has explicit glue on
                      both endpoints. ``visConnectFromError`` rows or
                      missing ``Connect`` entries are flagged; with
                      ``--repair-glue`` the closest 2-D shape is re-glued
                      via ``Cell.GlueTo``.
    2. layout         Re-run ``Page.Layout()`` when the ShapeSheet cell
                      ``User.vm_layout_dirty`` is non-zero (Drafter sets
                      that flag whenever connectors are placed by hand
                      without going through the autorouter).
    3. compress       Delete masters in the Document Stencil that no
                      shape references — the standard "drop unused
                      masters" hygiene pass.
    4. verify-lock    Compare the theme name, font scheme, and color
                      scheme inside ``visio/theme/theme1.xml`` against
                      the project's ``diagram_lock.md`` colours / fonts /
                      theme name.

A JSON summary is emitted on stdout (and optionally to ``--summary-path``)
describing what was inspected, changed, and flagged. Exit code 0 on full
parity, 2 when any file failed or any lock check found a discrepancy.

Usage:
    python scripts/finalize_vsdx.py projects/my_project
    python scripts/finalize_vsdx.py projects/my_project --no-layout
    python scripts/finalize_vsdx.py projects/my_project --repair-glue
    python scripts/finalize_vsdx.py projects/my_project \\
        --no-glue-fix --no-layout --no-compress       # verify only

Optional dependencies (declare in pyproject.toml; this script never installs):
    pywin32   Steps 1-3 require COM with Visio Desktop. Without it the
              steps degrade to detect-only or skip with a friendly note.
    vsdx      Read-only fallback enumeration. Optional, never required.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

# --- optional COM imports — every code path guards them -------------------

try:  # pragma: no cover - environment dependent
    import pythoncom  # type: ignore[import-not-found]
    import win32com.client as win32  # type: ignore[import-not-found]
    from pywintypes import com_error as _com_error  # type: ignore[import-not-found]

    _HAS_PYWIN32 = True
except ImportError:  # pragma: no cover
    pythoncom = None  # type: ignore[assignment]
    win32 = None  # type: ignore[assignment]
    _com_error = Exception  # type: ignore[assignment,misc]
    _HAS_PYWIN32 = False

try:  # pragma: no cover
    import vsdx  # type: ignore[import-not-found]  # noqa: F401

    _HAS_VSDX = True
except ImportError:  # pragma: no cover
    _HAS_VSDX = False

# --- constants ------------------------------------------------------------
# Hard-coded so we don't depend on makepy gen_py stubs.
VIS_BEGIN: int = 9                    # VisFromParts.visBegin
VIS_END: int = 12                     # VisFromParts.visEnd
VIS_CONNECT_FROM_ERROR: int = -1      # VisFromParts.visConnectFromError
VIS_OPEN_MACROS_DISABLED: int = 1024  # Documents.OpenEx flag
VIS_ALERT_RESPONSE_NO: int = 7        # Application.AlertResponse

NS_DRAWINGML: str = "http://schemas.openxmlformats.org/drawingml/2006/main"
NS_VISIO_MAIN: str = "http://schemas.microsoft.com/office/visio/2012/main"

_CONNECTOR_MASTER_NAMEUS: frozenset[str] = frozenset({
    "Dynamic connector", "Curved connector", "Straight connector",
})
_LAYOUT_DIRTY_CELL: str = "User.vm_layout_dirty"

# DrawingML clrScheme tag -> diagram_lock.colors key.
_COLOR_SLOTS: dict[str, str] = {
    "dk1": "text", "lt1": "bg",
    "dk2": "text_secondary", "lt2": "surface",
    "accent1": "primary", "accent2": "accent",
    "accent3": "secondary_accent",
    "hlink": "link", "folHlink": "link_visited",
}


# --- result aggregation ---------------------------------------------------


@dataclass
class StepResult:
    name: str
    enabled: bool = True
    ran: bool = False
    skipped_reason: str | None = None
    inspected: int = 0
    changed: int = 0
    issues: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class FileSummary:
    source: str
    output: str
    success: bool = True
    error: str | None = None
    steps: list[StepResult] = field(default_factory=list)


# --- small utilities ------------------------------------------------------


def safe_print(text: str, *, quiet: bool = False) -> None:
    """Print text while tolerating Windows console encoding limits."""
    if quiet:
        return
    try:
        print(text)
    except UnicodeEncodeError:  # pragma: no cover - terminal dependent
        print(text.encode("ascii", "replace").decode("ascii"))


def _endpoint_is_glued(formula: str) -> bool:
    """Heuristic: formula references another sheet via PNT(...) family."""
    if not formula:
        return False
    f = formula.strip().upper()
    return "SHEET." in f and "PNT(" in f


def _normalise_hex(value: str) -> str:
    """Reduce ``#1d1d1f`` / ``1D1D1FFF`` to upper-case 6-hex."""
    s = value.strip().lstrip("#").upper()
    return s[:6] if len(s) == 8 else s  # strip optional alpha


# --- step 1: glue-fix -----------------------------------------------------


def _is_connector(shape: Any) -> bool:
    """Treat any 1-D shape as a connector candidate."""
    try:
        if not bool(shape.OneD):
            return False
        master = shape.Master
        if master is not None:
            name_u = str(master.NameU)
            return name_u in _CONNECTOR_MASTER_NAMEUS or name_u.lower().endswith("connector")
    except _com_error:
        return False
    return True


def _attempt_repair_endpoint(conn: Any, cell_name: str, page: Any, *, quiet: bool) -> bool:
    """Re-glue ``cell_name`` to the closest 2-D shape via ``Cell.GlueTo``."""
    try:
        x = float(conn.Cells(cell_name).Result("in"))
        y = float(conn.Cells(cell_name.replace("X", "Y")).Result("in"))
    except _com_error as exc:
        safe_print(f"   [WARN] {cell_name}: cannot read coords ({exc})", quiet=quiet)
        return False

    target, best = None, float("inf")
    try:
        cid = int(conn.ID)
        for s in page.Shapes:
            try:
                if int(s.ID) == cid or bool(s.OneD):
                    continue
                sx = float(s.Cells("PinX").Result("in"))
                sy = float(s.Cells("PinY").Result("in"))
                d = (sx - x) ** 2 + (sy - y) ** 2
                if d < best:
                    best, target = d, s
            except _com_error:
                continue
    except _com_error:
        return False

    if target is None:
        return False
    try:
        conn.Cells(cell_name).GlueTo(target.Cells("PinX"))
        return True
    except _com_error as exc:
        safe_print(f"   [WARN] GlueTo failed for {cell_name}: {exc}", quiet=quiet)
        return False


def step_glue_fix(page: Any, *, repair: bool, quiet: bool) -> StepResult:
    """Inspect and optionally repair connector glue on a single page."""
    result = StepResult(name="glue_fix", ran=True)
    try:
        connectors = [s for s in page.Shapes if _is_connector(s)]
    except _com_error as exc:
        result.skipped_reason = f"page.Shapes unavailable: {exc}"
        return result
    result.inspected = len(connectors)

    # Index Page.Connects by (shape_id, part).
    connect_index: set[tuple[int, int]] = set()
    try:
        for cn in page.Connects:
            connect_index.add((int(cn.FromSheet.ID), int(cn.FromPart)))
    except _com_error as exc:
        result.issues.append(f"Page.Connects iteration failed: {exc}")

    for conn in connectors:
        try:
            sid, name = int(conn.ID), str(conn.NameU)
        except _com_error:
            continue
        for vis_part, cell_name in ((VIS_BEGIN, "BeginX"), (VIS_END, "EndX")):
            try:
                formula = str(conn.Cells(cell_name).FormulaU)
            except _com_error as exc:
                result.issues.append(f"{name}.{cell_name}: unreadable ({exc})")
                continue
            ok = (sid, vis_part) in connect_index and _endpoint_is_glued(formula)
            if (sid, VIS_CONNECT_FROM_ERROR) in connect_index or not ok:
                msg = f"{name}.{cell_name} orphan (formula={formula!r})"
                if repair and _attempt_repair_endpoint(conn, cell_name, page, quiet=quiet):
                    result.changed += 1
                    safe_print(f"   [OK] re-glued {name}.{cell_name}", quiet=quiet)
                else:
                    result.issues.append(msg)
    return result


# --- step 2: layout -------------------------------------------------------


def step_relayout(page: Any, *, force: bool, quiet: bool) -> StepResult:
    """Run ``Page.Layout()`` when ``User.vm_layout_dirty`` is set."""
    result = StepResult(name="layout", ran=True)
    dirty = force
    if not dirty:
        try:
            dirty = float(page.PageSheet.Cells(_LAYOUT_DIRTY_CELL).Result("")) != 0.0
        except _com_error:
            result.skipped_reason = f"{_LAYOUT_DIRTY_CELL} cell missing"
            return result
    if not dirty:
        result.skipped_reason = "layout_dirty=0"
        return result

    try:
        page.Layout()
        try:
            page.PageSheet.Cells(_LAYOUT_DIRTY_CELL).FormulaU = "0"
        except _com_error:
            pass
        result.changed = 1
        safe_print(f"   [OK] Page.Layout() {page.NameU}", quiet=quiet)
    except _com_error as exc:
        result.issues.append(f"Page.Layout() failed: {exc}")
    return result


# --- step 3: compress masters --------------------------------------------


def _walk_shapes(parent: Any):
    """Yield every shape under ``parent``, descending into groups."""
    try:
        for child in parent.Shapes:
            yield child
            try:
                if int(child.Shapes.Count) > 0:
                    yield from _walk_shapes(child)
            except _com_error:
                continue
    except _com_error:
        return


def step_compress_masters(doc: Any, *, quiet: bool) -> StepResult:
    """Delete masters that no shape references."""
    result = StepResult(name="compress_masters", ran=True)
    used_base_ids: set[str] = set()
    used_names: set[str] = set()

    try:
        for page in doc.Pages:
            for shape in _walk_shapes(page):
                try:
                    m = shape.Master
                    if m is None:
                        continue
                    used_base_ids.add(str(m.BaseID))
                    used_names.add(str(m.NameU))
                except _com_error:
                    continue
    except _com_error as exc:
        result.issues.append(f"page enumeration failed: {exc}")
        return result

    try:
        masters = list(doc.Masters)
    except _com_error as exc:
        result.skipped_reason = f"doc.Masters unavailable: {exc}"
        return result
    result.inspected = len(masters)

    to_delete: list[tuple[str, Any]] = []
    for m in masters:
        try:
            if str(m.BaseID) in used_base_ids or str(m.NameU) in used_names:
                continue
            to_delete.append((str(m.NameU), m))
        except _com_error:
            continue

    for name_u, m in reversed(to_delete):
        try:
            m.Delete()
            result.changed += 1
            safe_print(f"   [OK] master removed: {name_u}", quiet=quiet)
        except _com_error as exc:
            result.issues.append(f"master {name_u} delete failed: {exc}")

    result.details["kept"] = result.inspected - result.changed
    return result


# --- step 4: verify diagram_lock.md parity (no COM required) -------------


_LOCK_HEADER_RE: re.Pattern[str] = re.compile(r"^##\s+([A-Za-z0-9_]+)\s*$")
_LOCK_DATA_RE: re.Pattern[str] = re.compile(r"^-\s+([A-Za-z0-9_]+)\s*:\s*(.*?)\s*$")


def parse_diagram_lock(lock_path: Path) -> dict[str, dict[str, str]]:
    """Parse ``diagram_lock.md`` into ``{section: {key: raw_value}}``."""
    sections: dict[str, dict[str, str]] = {}
    if not lock_path.is_file():
        return sections
    current: str | None = None
    for raw in lock_path.read_text(encoding="utf-8").splitlines():
        m = _LOCK_HEADER_RE.match(raw.rstrip())
        if m:
            current = m.group(1)
            sections.setdefault(current, {})
            continue
        if current is None:
            continue
        d = _LOCK_DATA_RE.match(raw.rstrip())
        if d:
            sections[current][d.group(1)] = d.group(2)
    return sections


def _extract_theme_facts(vsdx_path: Path) -> dict[str, Any]:
    """Return ``theme_name``, ``colors``, ``major_font``, ``minor_font``."""
    facts: dict[str, Any] = {
        "theme_name": None, "colors": {},
        "major_font": None, "minor_font": None, "found": False,
    }
    try:
        with zipfile.ZipFile(vsdx_path) as zf:
            part = "visio/theme/theme1.xml"
            if part not in zf.namelist():
                return facts
            with zf.open(part) as fp:
                root = ET.parse(fp).getroot()
    except (zipfile.BadZipFile, ET.ParseError, FileNotFoundError, KeyError):
        return facts

    facts["found"] = True
    facts["theme_name"] = root.attrib.get("name")
    ns = {"a": NS_DRAWINGML}

    clr_scheme = root.find("a:themeElements/a:clrScheme", ns)
    if clr_scheme is not None:
        for child in clr_scheme:
            tag = child.tag.split("}", 1)[-1]
            lock_key = _COLOR_SLOTS.get(tag)
            if lock_key is None:
                continue
            srgb = child.find("a:srgbClr", ns)
            if srgb is not None and "val" in srgb.attrib:
                facts["colors"][lock_key] = _normalise_hex(srgb.attrib["val"])
                continue
            sys_clr = child.find("a:sysClr", ns)
            if sys_clr is not None and "lastClr" in sys_clr.attrib:
                facts["colors"][lock_key] = _normalise_hex(sys_clr.attrib["lastClr"])

    font_scheme = root.find("a:themeElements/a:fontScheme", ns)
    if font_scheme is not None:
        major = font_scheme.find("a:majorFont/a:latin", ns)
        minor = font_scheme.find("a:minorFont/a:latin", ns)
        if major is not None:
            facts["major_font"] = major.attrib.get("typeface")
        if minor is not None:
            facts["minor_font"] = minor.attrib.get("typeface")
    return facts


def _first_family_token(stack: str) -> str:
    """Return the leading family from a CSS-style font stack."""
    return stack.split(",", 1)[0].strip().strip("\"'")


def step_verify_lock(vsdx_path: Path, lock_path: Path) -> StepResult:
    """Compare theme1.xml against ``diagram_lock.md``."""
    result = StepResult(name="verify_lock", ran=True)
    if not lock_path.is_file():
        result.skipped_reason = f"diagram_lock.md missing at {lock_path}"
        return result

    lock = parse_diagram_lock(lock_path)
    facts = _extract_theme_facts(vsdx_path)
    if not facts["found"]:
        result.issues.append("visio/theme/theme1.xml not found inside .vsdx")
        return result

    result.inspected = 1
    lock_colors = lock.get("colors", {})
    for key, theme_hex in facts["colors"].items():
        lock_value = lock_colors.get(key)
        if not lock_value:
            continue
        expected = _normalise_hex(lock_value)
        if expected and expected != theme_hex:
            result.issues.append(f"colors.{key}: lock=#{expected} theme=#{theme_hex}")

    typo = lock.get("typography", {})
    expected_major = _first_family_token(typo.get("title_family") or typo.get("font_family", ""))
    expected_minor = _first_family_token(typo.get("body_family") or typo.get("font_family", ""))
    if expected_major and facts["major_font"] and expected_major != facts["major_font"]:
        result.issues.append(
            f"fonts.major: lock={expected_major!r} theme={facts['major_font']!r}"
        )
    if expected_minor and facts["minor_font"] and expected_minor != facts["minor_font"]:
        result.issues.append(
            f"fonts.minor: lock={expected_minor!r} theme={facts['minor_font']!r}"
        )

    theme_section = lock.get("theme", {})
    expected_name = theme_section.get("name") or theme_section.get("theme_name")
    if expected_name and facts["theme_name"] and expected_name != facts["theme_name"]:
        result.issues.append(
            f"theme.name: lock={expected_name!r} theme={facts['theme_name']!r}"
        )

    result.details = {
        "theme_name": facts["theme_name"],
        "major_font": facts["major_font"],
        "minor_font": facts["minor_font"],
        "colors_checked": len(facts["colors"]),
    }
    return result


# --- COM driver ----------------------------------------------------------


def _open_visio() -> Any:
    """Spawn an InvisibleApp instance with safe defaults."""
    if not _HAS_PYWIN32:
        raise RuntimeError("pywin32 not installed")
    try:
        win32.gencache.EnsureModule("{00021A98-0000-0000-C000-000000000046}", 0, 4, 12)
    except Exception:  # pragma: no cover - typelib may be unavailable
        pass
    app = win32.DispatchEx("Visio.InvisibleApp")
    app.AlertResponse = VIS_ALERT_RESPONSE_NO
    app.ScreenUpdating = False
    app.EventsEnabled = 0
    app.UndoEnabled = False
    app.DeferRecalc = True
    return app


def _process_with_com(
    dst: Path, *,
    do_glue_fix: bool, do_layout: bool, do_compress: bool,
    repair_glue: bool, force_layout: bool, quiet: bool,
) -> tuple[list[StepResult], str | None]:
    """Run COM-mediated steps against ``dst``. Returns (steps, error)."""
    if not _HAS_PYWIN32:
        return ([], "pywin32 not available; COM steps skipped")

    pythoncom.CoInitializeEx(pythoncom.COINIT_APARTMENTTHREADED)
    app = doc = None
    steps: list[StepResult] = []
    error: str | None = None
    try:
        app = _open_visio()
        doc = app.Documents.OpenEx(str(dst), VIS_OPEN_MACROS_DISABLED)

        if do_glue_fix:
            agg = StepResult(name="glue_fix", ran=True)
            for page in doc.Pages:
                page_res = step_glue_fix(page, repair=repair_glue, quiet=quiet)
                agg.inspected += page_res.inspected
                agg.changed += page_res.changed
                agg.issues.extend(f"{page.NameU}: {m}" for m in page_res.issues)
            steps.append(agg)

        if do_layout:
            agg = StepResult(name="layout", ran=True)
            for page in doc.Pages:
                page_res = step_relayout(page, force=force_layout, quiet=quiet)
                agg.inspected += 1
                agg.changed += page_res.changed
                agg.issues.extend(f"{page.NameU}: {m}" for m in page_res.issues)
            steps.append(agg)

        if do_compress:
            steps.append(step_compress_masters(doc, quiet=quiet))

        app.DeferRecalc = False
        doc.Save()
    except _com_error as exc:
        error = f"COM error: {exc}"
    except FileNotFoundError as exc:
        error = f"File not found: {exc}"
    except KeyError as exc:
        error = f"Missing key: {exc}"
    finally:
        for fn in (
            (lambda: doc.Close()) if doc is not None else (lambda: None),
            (lambda: app.Quit()) if app is not None else (lambda: None),
            pythoncom.CoUninitialize,
        ):
            try:
                fn()
            except Exception:  # noqa: BLE001 - shutdown best-effort
                pass
    return steps, error


# --- fallback: read-only OPC scan ---------------------------------------


def _fallback_glue_fix(vsdx_path: Path) -> StepResult:
    """Detect orphan connector endpoints by reading raw OPC XML."""
    result = StepResult(name="glue_fix", ran=True)
    result.skipped_reason = "pywin32 unavailable - running detect-only"
    try:
        with zipfile.ZipFile(vsdx_path) as zf:
            page_parts = [
                n for n in zf.namelist()
                if n.startswith("visio/pages/page") and n.endswith(".xml")
            ]
            ns = {"v": NS_VISIO_MAIN}
            for part in page_parts:
                with zf.open(part) as fp:
                    root = ET.parse(fp).getroot()
                for shape in root.iter(f"{{{NS_VISIO_MAIN}}}Shape"):
                    has_endpoint = False
                    bad: list[str] = []
                    for cell in shape.findall("v:Cell", ns):
                        n = cell.attrib.get("N", "")
                        if n in {"BeginX", "EndX"}:
                            has_endpoint = True
                            if not _endpoint_is_glued(cell.attrib.get("F", "")):
                                bad.append(n)
                    if has_endpoint and bad:
                        result.inspected += 1
                        sid = shape.attrib.get("ID", "?")
                        result.issues.append(
                            f"{Path(part).name}#shape{sid}: orphan {bad}"
                        )
    except (zipfile.BadZipFile, ET.ParseError, FileNotFoundError, KeyError) as exc:
        result.issues.append(f"OPC scan failed: {exc}")
    return result


# --- top-level driver ---------------------------------------------------


def finalize_project(
    project_dir: Path, *,
    do_glue_fix: bool, do_layout: bool, do_compress: bool, do_verify_lock: bool,
    repair_glue: bool, force_layout: bool, quiet: bool,
) -> dict[str, Any]:
    """Process every ``.vsdx`` under ``vsdx_output/`` into ``vsdx_final/``."""
    src_dir = project_dir / "vsdx_output"
    dst_dir = project_dir / "vsdx_final"
    lock_path = project_dir / "diagram_lock.md"

    summary: dict[str, Any] = {
        "project": str(project_dir),
        "source_dir": str(src_dir),
        "output_dir": str(dst_dir),
        "lock_path": str(lock_path),
        "pywin32_available": _HAS_PYWIN32,
        "vsdx_lib_available": _HAS_VSDX,
        "files": [],
    }

    if not src_dir.is_dir():
        summary["error"] = f"vsdx_output directory not found: {src_dir}"
        return summary
    vsdx_files = sorted(src_dir.glob("*.vsdx"))
    if not vsdx_files:
        summary["error"] = f"No .vsdx files in {src_dir}"
        return summary

    if dst_dir.exists():
        shutil.rmtree(dst_dir)
    dst_dir.mkdir(parents=True)

    safe_print(f"[DIR] Project: {project_dir.name}", quiet=quiet)
    safe_print(f"[FILE] {len(vsdx_files)} .vsdx file(s)", quiet=quiet)

    for src in vsdx_files:
        dst = dst_dir / src.name
        shutil.copy2(src, dst)
        fs = FileSummary(source=str(src), output=str(dst))
        com_wanted = do_glue_fix or do_layout or do_compress

        if com_wanted and _HAS_PYWIN32:
            steps, error = _process_with_com(
                dst,
                do_glue_fix=do_glue_fix, do_layout=do_layout, do_compress=do_compress,
                repair_glue=repair_glue, force_layout=force_layout, quiet=quiet,
            )
            fs.steps.extend(steps)
            if error:
                fs.success = False
                fs.error = error
        elif com_wanted:
            if do_glue_fix:
                fs.steps.append(_fallback_glue_fix(dst))
            for name, want in (("layout", do_layout), ("compress_masters", do_compress)):
                if want:
                    fs.steps.append(StepResult(
                        name=name, ran=False,
                        skipped_reason="pywin32 unavailable - requires Visio COM",
                    ))

        if do_verify_lock:
            fs.steps.append(step_verify_lock(dst, lock_path))

        # Record disabled-by-flag steps so the summary lists every pass.
        for name, enabled in (
            ("glue_fix", do_glue_fix), ("layout", do_layout),
            ("compress_masters", do_compress), ("verify_lock", do_verify_lock),
        ):
            if not enabled and not any(s.name == name for s in fs.steps):
                fs.steps.append(StepResult(
                    name=name, enabled=False, ran=False, skipped_reason="disabled by flag",
                ))

        summary["files"].append(asdict(fs))
        safe_print(f"   {'[OK]' if fs.success else '[ERROR]'} {src.name}", quiet=quiet)

    return summary


# --- CLI ----------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Visio Master - VSDX post-processing pipeline. Mirrors the four "
            "passes of finalize_svg.py for the .vsdx format."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Steps (all on by default; disable with --no-<step>):
  glue-fix       Repair connectors with orphan endpoints (COM only).
  layout         Re-run Page.Layout() when User.vm_layout_dirty is set.
  compress       Drop unused masters from the Document Stencil.
  verify-lock    Compare theme1.xml against diagram_lock.md.

Examples:
  %(prog)s projects/my_project
  %(prog)s projects/my_project --no-layout --no-compress
  %(prog)s projects/my_project --force-layout --repair-glue
""",
    )
    p.add_argument("project_dir", type=Path, help="Project directory path.")
    p.add_argument("--no-glue-fix", action="store_true", help="Skip step 1.")
    p.add_argument("--no-layout", action="store_true", help="Skip step 2.")
    p.add_argument("--no-compress", action="store_true", help="Skip step 3.")
    p.add_argument("--no-verify-lock", action="store_true", help="Skip step 4.")
    p.add_argument(
        "--repair-glue", action="store_true",
        help="Auto-reglue orphan endpoints to the closest 2-D shape.",
    )
    p.add_argument(
        "--force-layout", action="store_true",
        help="Run Page.Layout() on every page regardless of User.vm_layout_dirty.",
    )
    p.add_argument("-q", "--quiet", action="store_true", help="Suppress progress output.")
    p.add_argument(
        "--summary-path", type=Path, default=None,
        help="Optional path to write the JSON summary (default: stdout).",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns the exit code."""
    args = _build_parser().parse_args(argv)
    project_dir: Path = args.project_dir
    if not project_dir.is_dir():
        safe_print(f"[ERROR] Project directory does not exist: {project_dir}")
        return 1

    summary = finalize_project(
        project_dir,
        do_glue_fix=not args.no_glue_fix,
        do_layout=not args.no_layout,
        do_compress=not args.no_compress,
        do_verify_lock=not args.no_verify_lock,
        repair_glue=args.repair_glue,
        force_layout=args.force_layout,
        quiet=args.quiet,
    )

    payload = json.dumps(summary, indent=2, ensure_ascii=False)
    if args.summary_path is not None:
        args.summary_path.write_text(payload, encoding="utf-8")
    if not args.quiet:
        print(payload)

    failures = 1 if "error" in summary else 0
    for f in summary.get("files", []):
        if not f.get("success", True):
            failures += 1
        for s in f.get("steps", []):
            if s["name"] == "verify_lock" and s.get("issues"):
                failures += 1
    return 0 if failures == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
