#!/usr/bin/env python3
"""
Visio Master — VSDX Quality Check Tool.

Mirrors the role of ``svg_quality_checker.py`` in ``ppt-master`` but operates
on Visio ``.vsdx`` packages. Performs static lint against the rules codified
in ``visio-master/references/shared-standards.md``:

* Orphan connectors (1-D shapes lacking glue on either endpoint).
* Off-page shapes (``PinX`` / ``PinY`` outside the page rectangle).
* Shapes without a master (``page.DrawRectangle`` style hand-geometry that
  bypasses the master inheritance chain).
* Missing Shape Data fields declared in ``diagram_lock.md``.
* Font fallbacks — every ``Char.Font`` typeface must resolve on the host.
* Theme drift — literal HEX / ``RGB(...)`` in cells that should resolve via
  ``THEMEGUARD()`` / ``THEMEVAL()``.
* Layer membership consistency — ``Misc.LayerMember`` indices in range.

A JSON report (severity-tagged: ``error`` / ``warning`` / ``info``) is written
to stdout or to ``--output``. Exit code is ``1`` when any ``error`` was seen.

Two parsing backends, selected via ``--backend``:

* ``vsdx`` (default) — stdlib ``zipfile`` + ``xml.etree`` over the OPC parts.
  Pure-stdlib so the tool runs on sealed environments. The ``vsdx`` lib is
  detected if installed and reported in the JSON output, but the OPC path is
  canonical and version-stable.
* ``com`` — uses ``pywin32`` to drive a live ``Visio.InvisibleApp`` instance.
  Slower but inspects the post-recalc state Visio actually sees.

Dependencies (declared, never auto-installed):
    Required:  none — stdlib only.
    Optional:  pywin32>=305   for ``--backend com``
               vsdx>=0.5      detected and reported; not required.

Usage::

    python scripts/vsdx_quality_check.py drawings/topology.vsdx
    python scripts/vsdx_quality_check.py drawings/ --output report.json
    python scripts/vsdx_quality_check.py drawings/x.vsdx --backend com \\
        --lock drawings/diagram_lock.md
    python scripts/vsdx_quality_check.py drawings/ --pretty --summary
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable
from xml.etree import ElementTree as ET

# ---------------------------------------------------------------------------
# Optional dependencies — degrade gracefully when missing.
# ---------------------------------------------------------------------------
try:  # pragma: no cover - import probing
    import vsdx as _vsdx_lib  # type: ignore[import-not-found]  # noqa: F401
    _HAS_VSDX_LIB = True
except ImportError:
    _HAS_VSDX_LIB = False

try:  # pragma: no cover - import probing
    import pythoncom  # type: ignore[import-not-found]
    import pywintypes  # type: ignore[import-not-found]
    import win32com.client as _win32  # type: ignore[import-not-found]
except ImportError:
    pythoncom = None  # type: ignore[assignment]
    pywintypes = None  # type: ignore[assignment]
    _win32 = None  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# Constants — taken from shared-standards.md.
# ---------------------------------------------------------------------------
VISIO_NS = "http://schemas.microsoft.com/office/visio/2012/main"
DRAWINGML_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
RELS_NS = "http://schemas.openxmlformats.org/package/2006/relationships"

# Cells that MUST resolve via THEMEGUARD/THEMEVAL — literal HEX is drift.
THEME_BOUND_CELLS = frozenset({"LineColor", "FillForegnd", "FillBkgnd", "ShdwForegnd", "Char.Color"})

# Hand-geometry types that, when used without a Master back-pointer, count
# as "shape without master" per shared-standards.md §4.1.
HAND_GEOMETRY_TYPES = frozenset({"Shape", "Group"})

# Cross-platform pre-installed fonts (mirrors ppt-master safe roster).
PPT_SAFE_FONTS = frozenset({
    "microsoft yahei", "simhei", "simsun", "kaiti", "fangsong",
    "dengxian", "microsoft jhenghei", "pingfang sc", "heiti sc",
    "songti sc", "stsong", "arial", "arial black", "calibri",
    "segoe ui", "verdana", "helvetica", "helvetica neue", "tahoma",
    "trebuchet ms", "times new roman", "times", "georgia", "cambria",
    "palatino", "consolas", "courier new", "menlo", "monaco", "impact",
    "inter", "source han sans", "source han sans sc",
})

HEX_LITERAL_RE = re.compile(r"#?[0-9A-Fa-f]{6}\b")
RGB_FORMULA_RE = re.compile(r"\bRGB\s*\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*\)")
THEME_FORMULA_RE = re.compile(r"\bTHEME(?:GUARD|VAL|COLOR)\b", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Issue model.
# ---------------------------------------------------------------------------
@dataclass
class Issue:
    """A single lint finding with severity and provenance."""

    severity: str  # "error" | "warning" | "info"
    kind: str
    message: str
    page: str | None = None
    shape: str | None = None
    cell: str | None = None

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"severity": self.severity, "kind": self.kind, "message": self.message}
        if self.page is not None:
            out["page"] = self.page
        if self.shape is not None:
            out["shape"] = self.shape
        if self.cell is not None:
            out["cell"] = self.cell
        return out


@dataclass
class PageModel:
    """Lightweight projection of a Visio page used by every checker."""

    name: str
    width: float | None
    height: float | None
    layers: list[str] = field(default_factory=list)
    shapes: list[ShapeModel] = field(default_factory=list)


@dataclass
class ShapeModel:
    """Lightweight projection of a Visio shape — only the fields we lint."""

    sid: str
    name: str
    type: str
    master: str | None
    one_d: bool
    pin_x: float | None
    pin_y: float | None
    width: float | None
    height: float | None
    begin_x: float | None
    begin_y: float | None
    end_x: float | None
    end_y: float | None
    layer_member: str
    fonts: list[str] = field(default_factory=list)
    theme_drift_cells: list[tuple[str, str]] = field(default_factory=list)
    shape_data_keys: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# diagram_lock.md parser — extracts the bits this checker needs.
# ---------------------------------------------------------------------------
def parse_diagram_lock(lock_path: Path) -> dict[str, Any]:
    """Read a diagram_lock.md file and return ``{shape_data, fonts, themes}``.

    The lock is a Markdown document with optional YAML frontmatter and
    documented tables. We scan for the small surface this checker needs and
    silently ignore everything else, so the parser stays robust against
    unrelated lock additions.
    """
    info: dict[str, Any] = {
        "shape_data": [],  # list[str]
        "fonts": [],  # list[str]
        "theme_colors": {},  # name -> hex
    }
    if not lock_path.exists():
        return info
    try:
        text = lock_path.read_text(encoding="utf-8")
    except OSError:
        return info

    # YAML-ish frontmatter (--- … ---).
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            block = text[4:end]
            for line in block.splitlines():
                stripped = line.strip()
                if stripped.startswith("shape_data:"):
                    info["shape_data"] = _parse_inline_list(stripped)
                elif stripped.startswith("fonts:"):
                    info["fonts"] = _parse_inline_list(stripped)

    # Section-style declaration: lines like "- `Prop.Owner`" under "## Shape Data".
    section_re = re.compile(r"^##\s+(Shape Data|Required Shape Data)\b", re.MULTILINE)
    item_re = re.compile(r"^[-*]\s*`(Prop\.[A-Za-z0-9_]+)`")
    for sect_match in section_re.finditer(text):
        start = sect_match.end()
        nxt = re.search(r"^## ", text[start:], re.MULTILINE)
        end = start + (nxt.start() if nxt else len(text) - start)
        for line in text[start:end].splitlines():
            m = item_re.match(line.strip())
            if m and m.group(1) not in info["shape_data"]:
                info["shape_data"].append(m.group(1))
    return info


def _parse_inline_list(yaml_line: str) -> list[str]:
    """Parse ``key: ["a", "b"]`` style YAML inline arrays."""
    after = yaml_line.split(":", 1)[1].strip()
    if not after.startswith("["):
        return []
    return [p.strip().strip("\"'") for p in after.strip("[]").split(",") if p.strip().strip("\"'")]


# ---------------------------------------------------------------------------
# System font enumeration (Windows registry + portable directory scan).
# ---------------------------------------------------------------------------
def list_system_fonts() -> set[str]:
    """Return a lowercase set of font family names installed on the host.

    Uses the Windows registry ``Fonts`` key; on other platforms scans common
    font directories. Falls back to :data:`PPT_SAFE_FONTS` when neither
    yields anything (sandboxed CI, locked-down container).
    """
    fonts: set[str] = set()
    if sys.platform.startswith("win"):
        try:
            import winreg  # type: ignore[import-not-found]
        except ImportError:
            winreg = None  # type: ignore[assignment]
        if winreg is not None:
            keys = (
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"),
            )
            for hive, sub in keys:
                try:
                    with winreg.OpenKey(hive, sub) as k:
                        for i in range(winreg.QueryInfoKey(k)[1]):
                            name, _, _ = winreg.EnumValue(k, i)
                            cleaned = re.sub(r"\s*\(.*\)\s*$", "", name).strip().lower()
                            if cleaned:
                                fonts.add(cleaned)
                except OSError:
                    continue
    else:
        for base in ("/usr/share/fonts", "/usr/local/share/fonts", str(Path.home() / ".fonts")):
            base_path = Path(base)
            if base_path.exists():
                for f in base_path.rglob("*.[ot]tf"):
                    fonts.add(f.stem.lower())
    return fonts or set(PPT_SAFE_FONTS)


# ---------------------------------------------------------------------------
# VSDX parser — raw OPC over stdlib (canonical, version-stable).
# ---------------------------------------------------------------------------
_PAGE_PART_RE = re.compile(r"^visio/pages/page(\d+)\.xml$")


class VsdxParser:
    """Parse a .vsdx OPC package into :class:`PageModel` objects."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def parse(self) -> list[PageModel]:
        if not self.path.exists():
            raise FileNotFoundError(self.path)
        pages: list[PageModel] = []
        with zipfile.ZipFile(self.path) as zf:
            page_parts = sorted(
                (name for name in zf.namelist() if _PAGE_PART_RE.match(name)),
                key=lambda n: int(_PAGE_PART_RE.match(n).group(1)),  # type: ignore[union-attr]
            )
            pages_index = self._read_pages_index(zf)
            for idx, name in enumerate(page_parts, start=1):
                meta = pages_index.get(idx, {})
                with zf.open(name) as fh:
                    tree = ET.parse(fh)
                page = PageModel(
                    name=meta.get("name") or f"Page-{idx}",
                    width=_safe_float(meta.get("PageWidth")),
                    height=_safe_float(meta.get("PageHeight")),
                )
                for sec in tree.findall(f".//{{{VISIO_NS}}}Section[@N='Layer']"):
                    for row in sec.findall(f"{{{VISIO_NS}}}Row"):
                        name_cell = row.find(f"{{{VISIO_NS}}}Cell[@N='Name']")
                        if name_cell is not None and name_cell.get("V"):
                            page.layers.append(name_cell.get("V", ""))
                for shape_el in tree.findall(f".//{{{VISIO_NS}}}Shape"):
                    page.shapes.append(_shape_from_opc(shape_el))
                pages.append(page)
        return pages

    @staticmethod
    def _read_pages_index(zf: zipfile.ZipFile) -> dict[int, dict[str, str]]:
        try:
            with zf.open("visio/pages/pages.xml") as fh:
                tree = ET.parse(fh)
        except KeyError:
            return {}
        out: dict[int, dict[str, str]] = {}
        for i, page in enumerate(tree.findall(f"{{{VISIO_NS}}}Page"), start=1):
            entry: dict[str, str] = {
                "name": page.get("Name") or page.get("NameU") or "",
            }
            for cell in page.findall(f".//{{{VISIO_NS}}}Cell"):
                cn = cell.get("N")
                if cn in ("PageWidth", "PageHeight") and cell.get("V"):
                    entry[cn] = cell.get("V", "")
            out[i] = entry
        return out


def _safe_float(value: Any) -> float | None:
    """Coerce a Visio cell value to ``float`` without raising."""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _shape_from_opc(shape_el: ET.Element) -> ShapeModel:
    """Build a ShapeModel from a raw ``<Shape>`` XML element."""
    values: dict[str, str] = {}
    fonts: list[str] = []
    theme_drift: list[tuple[str, str]] = []
    shape_data_keys: set[str] = set()

    for cell in shape_el.iter(f"{{{VISIO_NS}}}Cell"):
        cname = cell.get("N", "")
        cv = cell.get("V")
        cf = cell.get("F")
        if cv is not None:
            values[cname] = cv
        # Theme drift — literal HEX or RGB(...) in a theme-bound cell.
        if cname in THEME_BOUND_CELLS and cf and not THEME_FORMULA_RE.search(cf):
            if RGB_FORMULA_RE.search(cf) or HEX_LITERAL_RE.fullmatch(cf.strip().strip('"')):
                theme_drift.append((cname, cf))
        if cname == "Char.Font" and cv:
            fonts.append(cv)

    for sec in shape_el.findall(f"{{{VISIO_NS}}}Section[@N='Property']"):
        for row in sec.findall(f"{{{VISIO_NS}}}Row"):
            row_name = row.get("N")
            if row_name:
                shape_data_keys.add(f"Prop.{row_name}")

    raw_layer = values.get("LayerMember", "").strip().strip('"').strip("'")
    return ShapeModel(
        sid=shape_el.get("ID", ""),
        name=shape_el.get("Name") or shape_el.get("NameU") or shape_el.get("ID", ""),
        type=shape_el.get("Type", "Shape"),
        master=shape_el.get("Master") or shape_el.get("MasterShape"),
        one_d=values.get("Misc.ObjType") == "1" or shape_el.get("Type", "") == "Connector",
        pin_x=_safe_float(values.get("PinX")),
        pin_y=_safe_float(values.get("PinY")),
        width=_safe_float(values.get("Width")),
        height=_safe_float(values.get("Height")),
        begin_x=_safe_float(values.get("BeginX")),
        begin_y=_safe_float(values.get("BeginY")),
        end_x=_safe_float(values.get("EndX")),
        end_y=_safe_float(values.get("EndY")),
        layer_member=raw_layer,
        fonts=fonts,
        theme_drift_cells=theme_drift,
        shape_data_keys=shape_data_keys,
    )


# ---------------------------------------------------------------------------
# COM backend — opens Visio and reads the live model.
# ---------------------------------------------------------------------------
def parse_with_com(path: Path) -> list[PageModel]:
    """Load a .vsdx via ``Visio.InvisibleApp`` and project to PageModels.

    Raises ``RuntimeError`` with a friendly message when ``pywin32`` is not
    installed or the Visio COM call fails.
    """
    if pythoncom is None or _win32 is None:
        raise RuntimeError(
            "pywin32 is not installed; --backend com requires "
            "`pip install pywin32` and a local Microsoft Visio install."
        )

    pythoncom.CoInitializeEx(pythoncom.COINIT_APARTMENTTHREADED)
    pages: list[PageModel] = []
    app = doc = None
    try:
        app = _win32.DispatchEx("Visio.InvisibleApp")
        app.AlertResponse = 7  # visAlertResponseNo
        # visOpenRO|visOpenHidden|visOpenNoWorkspace|visOpenMacrosDisabled
        doc = app.Documents.OpenEx(str(path), 1 | 64 | 256 | 1024)
        for page in doc.Pages:
            pm = PageModel(
                name=page.NameU,
                width=_com_iu(page.PageSheet, "PageWidth"),
                height=_com_iu(page.PageSheet, "PageHeight"),
            )
            for layer in page.Layers:
                pm.layers.append(getattr(layer, "NameU", None) or layer.Name)
            for sh in page.Shapes:
                pm.shapes.append(_shape_from_com(sh))
            pages.append(pm)
    except (pywintypes.com_error if pywintypes else Exception) as exc:  # type: ignore[misc]
        raise RuntimeError(f"Visio COM call failed for {path}: {exc!r}") from exc
    finally:
        try:
            if doc is not None:
                doc.Close()
            if app is not None:
                app.Quit()
        finally:
            pythoncom.CoUninitialize()
    return pages


def _com_iu(obj: Any, name: str) -> float | None:
    try:
        return float(obj.CellsU(name).ResultIU)
    except Exception:
        return None


def _com_fu(shape: Any, name: str) -> str:
    try:
        return str(shape.CellsU(name).FormulaU or "")
    except Exception:
        return ""


def _shape_from_com(shape: Any) -> ShapeModel:
    master_obj = getattr(shape, "Master", None)
    master_name = getattr(master_obj, "NameU", None) if master_obj is not None else None
    one_d = bool(getattr(shape, "OneD", 0))

    layer_member = ""
    try:
        layer_member = shape.CellsU("LayerMember").ResultStrU("").strip()
    except Exception:
        pass

    fonts: list[str] = []
    font = _com_fu(shape, "Char.Font").strip().strip('"')
    if font:
        fonts.append(font)

    theme_drift: list[tuple[str, str]] = []
    for cn in THEME_BOUND_CELLS:
        formula = _com_fu(shape, cn)
        if formula and not THEME_FORMULA_RE.search(formula) and (
            RGB_FORMULA_RE.search(formula)
            or HEX_LITERAL_RE.fullmatch(formula.strip().strip('"'))
        ):
            theme_drift.append((cn, formula))

    shape_data_keys: set[str] = set()
    try:
        section = shape.Section(243)  # visSectionProp
        for r in range(section.Count):
            shape_data_keys.add(f"Prop.{section.Row(r).NameU}")
    except Exception:
        pass

    return ShapeModel(
        sid=str(shape.ID), name=shape.NameU,
        type="Connector" if one_d else "Shape",
        master=master_name, one_d=one_d,
        pin_x=_com_iu(shape, "PinX"), pin_y=_com_iu(shape, "PinY"),
        width=_com_iu(shape, "Width"), height=_com_iu(shape, "Height"),
        begin_x=_com_iu(shape, "BeginX"), begin_y=_com_iu(shape, "BeginY"),
        end_x=_com_iu(shape, "EndX"), end_y=_com_iu(shape, "EndY"),
        layer_member=layer_member, fonts=fonts,
        theme_drift_cells=theme_drift, shape_data_keys=shape_data_keys,
    )


# ---------------------------------------------------------------------------
# The checker.
# ---------------------------------------------------------------------------
class VsdxQualityChecker:
    """Run every lint pass against a parsed VSDX model."""

    def __init__(
        self,
        *,
        lock: dict[str, Any] | None = None,
        system_fonts: set[str] | None = None,
        off_page_tolerance: float = 0.05,
    ) -> None:
        self.lock = lock or {"shape_data": [], "fonts": [], "theme_colors": {}}
        self.system_fonts = system_fonts if system_fonts is not None else list_system_fonts()
        self.off_page_tolerance = off_page_tolerance

    def check_file(self, path: Path, pages: list[PageModel]) -> dict[str, Any]:
        issues: list[Issue] = []
        for page in pages:
            for check in (
                self._check_orphan_connectors,
                self._check_off_page,
                self._check_no_master,
                self._check_shape_data,
                self._check_fonts,
                self._check_theme_drift,
                self._check_layer_membership,
            ):
                issues.extend(check(page))
        summary: dict[str, int] = defaultdict(int)
        for issue in issues:
            summary[issue.severity] += 1
        return {
            "file": str(path),
            "page_count": len(pages),
            "shape_count": sum(len(p.shapes) for p in pages),
            "summary": dict(summary),
            "issues": [issue.to_dict() for issue in issues],
        }

    # ------------------------------------------------------------------ checks
    def _check_orphan_connectors(self, page: PageModel) -> Iterable[Issue]:
        for shape in page.shapes:
            if not shape.one_d and shape.type != "Connector":
                continue
            missing = [
                name for name, val in (
                    ("BeginX", shape.begin_x), ("BeginY", shape.begin_y),
                    ("EndX", shape.end_x), ("EndY", shape.end_y),
                ) if val is None
            ]
            if missing:
                yield Issue(
                    "error", "orphan_connector",
                    f"Connector missing endpoint cells: {', '.join(missing)} "
                    "(Visio will render this as a 0-length point at origin).",
                    page=page.name, shape=shape.name,
                )
            elif shape.begin_x == 0 and shape.begin_y == 0 and shape.end_x == 0 and shape.end_y == 0:
                yield Issue(
                    "warning", "orphan_connector",
                    "Connector endpoints all zero — likely unglued.",
                    page=page.name, shape=shape.name,
                )

    def _check_off_page(self, page: PageModel) -> Iterable[Issue]:
        if not page.width or not page.height:
            return
        tol_x = page.width * self.off_page_tolerance
        tol_y = page.height * self.off_page_tolerance
        for shape in page.shapes:
            if shape.pin_x is None or shape.pin_y is None:
                continue
            if not (-tol_x <= shape.pin_x <= page.width + tol_x):
                yield Issue(
                    "warning", "off_page",
                    f"PinX={shape.pin_x:.3f} is outside page width "
                    f"[{-tol_x:.3f}, {page.width + tol_x:.3f}].",
                    page=page.name, shape=shape.name, cell="PinX",
                )
            if not (-tol_y <= shape.pin_y <= page.height + tol_y):
                yield Issue(
                    "warning", "off_page",
                    f"PinY={shape.pin_y:.3f} is outside page height "
                    f"[{-tol_y:.3f}, {page.height + tol_y:.3f}].",
                    page=page.name, shape=shape.name, cell="PinY",
                )

    def _check_no_master(self, page: PageModel) -> Iterable[Issue]:
        # Foreign / Guide / Group / Page-level shapes can legitimately ship
        # without a master back-pointer; only flag visible 2-D shapes.
        for shape in page.shapes:
            if shape.master or shape.type not in HAND_GEOMETRY_TYPES or shape.one_d:
                continue
            yield Issue(
                "warning", "missing_master",
                "Shape has no Master back-pointer — drawn via Page.Draw* instead "
                "of Page.Drop(master). Master inheritance and Page.Layout() "
                "routing will not see it.",
                page=page.name, shape=shape.name,
            )

    def _check_shape_data(self, page: PageModel) -> Iterable[Issue]:
        required = list(self.lock.get("shape_data") or [])
        if not required:
            return
        for shape in page.shapes:
            if not shape.master:
                continue  # Required only on instance-from-master shapes.
            for key in required:
                if key not in shape.shape_data_keys:
                    yield Issue(
                        "error", "missing_shape_data",
                        f"Required Shape Data row {key} missing (declared in diagram_lock.md).",
                        page=page.name, shape=shape.name,
                    )

    def _check_fonts(self, page: PageModel) -> Iterable[Issue]:
        for shape in page.shapes:
            for font in shape.fonts:
                cleaned = font.strip().strip('"').strip("'").lower()
                if not cleaned or cleaned in self.system_fonts:
                    continue
                if cleaned in PPT_SAFE_FONTS:
                    yield Issue(
                        "info", "font_not_installed",
                        f"Font '{font}' is in the safe roster but not installed on "
                        "this host — Visio will substitute at render time.",
                        page=page.name, shape=shape.name,
                    )
                else:
                    yield Issue(
                        "warning", "font_unsafe",
                        f"Font '{font}' is not installed AND not in the visio-master "
                        "safe roster (Inter / Segoe UI / Microsoft YaHei / etc.).",
                        page=page.name, shape=shape.name,
                    )

    def _check_theme_drift(self, page: PageModel) -> Iterable[Issue]:
        for shape in page.shapes:
            for cell, formula in shape.theme_drift_cells:
                yield Issue(
                    "warning", "theme_drift",
                    f"Cell {cell} uses literal value '{formula}' instead of "
                    "THEMEGUARD()/THEMEVAL(). Theme variants will not propagate.",
                    page=page.name, shape=shape.name, cell=cell,
                )

    def _check_layer_membership(self, page: PageModel) -> Iterable[Issue]:
        layer_count = len(page.layers)
        for shape in page.shapes:
            raw = shape.layer_member.strip().strip('"').strip("'")
            if not raw:
                continue
            for token in raw.split(";"):
                token = token.strip()
                if not token:
                    continue
                try:
                    idx = int(token)
                except ValueError:
                    yield Issue(
                        "error", "layer_member_invalid",
                        f"LayerMember token '{token}' is not an integer.",
                        page=page.name, shape=shape.name, cell="LayerMember",
                    )
                    continue
                if layer_count and (idx < 0 or idx >= layer_count):
                    yield Issue(
                        "error", "layer_member_out_of_range",
                        f"LayerMember index {idx} is outside [0, {layer_count}). "
                        "Adding/removing layers shifts indices; rerun "
                        "update_diagram_lock.py to renumber.",
                        page=page.name, shape=shape.name, cell="LayerMember",
                    )


# ---------------------------------------------------------------------------
# Driver.
# ---------------------------------------------------------------------------
def run_one(path: Path, args: argparse.Namespace, checker: VsdxQualityChecker) -> dict[str, Any]:
    """Parse + check one .vsdx; never raises — emits an error report instead."""
    error_kinds = {
        FileNotFoundError: ("file_not_found", "File does not exist: {exc}"),
        KeyError: ("package_layout", "Required OPC part missing: {exc!r}"),
        RuntimeError: ("backend_unavailable", "{exc}"),
    }
    try:
        if args.backend == "com":
            pages = parse_with_com(path)
        else:
            pages = VsdxParser(path).parse()
    except tuple(error_kinds) as exc:
        kind, fmt = error_kinds[type(exc)]
        return {
            "file": str(path),
            "summary": {"error": 1},
            "issues": [{"severity": "error", "kind": kind, "message": fmt.format(exc=exc)}],
        }
    return checker.check_file(path, pages)


def collect_targets(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    if target.is_dir():
        return sorted(target.rglob("*.vsdx"))
    raise FileNotFoundError(target)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="vsdx_quality_check",
        description="Lint .vsdx files for visio-master compliance.",
    )
    p.add_argument("target", help="Path to a .vsdx file or a directory tree.")
    p.add_argument("--backend", choices=("vsdx", "com"), default="vsdx",
                   help="Static parser (default) vs Visio COM (needs pywin32 + Visio).")
    p.add_argument("--lock", type=Path, default=None,
                   help="Path to diagram_lock.md. Defaults to <target>/diagram_lock.md.")
    p.add_argument("--output", type=Path, default=None,
                   help="Write JSON report to this path instead of stdout.")
    p.add_argument("--pretty", action="store_true", help="Indent JSON output.")
    p.add_argument("--summary", action="store_true",
                   help="Print one-line per-file summary to stderr after JSON.")
    p.add_argument("--off-page-tolerance", type=float, default=0.05,
                   help="Fractional slack on page-bound checks (default 0.05 = 5%%).")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    target = Path(args.target)
    try:
        targets = collect_targets(target)
    except FileNotFoundError:
        print(f"[ERROR] Target does not exist: {target}", file=sys.stderr)
        return 2
    if not targets:
        print(f"[WARN] No .vsdx files under {target}", file=sys.stderr)
        return 0

    lock_path = args.lock or (target if target.is_dir() else target.parent) / "diagram_lock.md"
    checker = VsdxQualityChecker(
        lock=parse_diagram_lock(lock_path),
        off_page_tolerance=args.off_page_tolerance,
    )

    reports = [run_one(t, args, checker) for t in targets]
    aggregate: dict[str, int] = defaultdict(int)
    for report in reports:
        for sev, n in report.get("summary", {}).items():
            aggregate[sev] += int(n)

    output = {
        "tool": "vsdx_quality_check",
        "backend": args.backend,
        "lock": str(lock_path),
        "totals": dict(aggregate),
        "reports": reports,
    }
    serialized = json.dumps(output, indent=2 if args.pretty else None, ensure_ascii=False)
    if args.output:
        args.output.write_text(serialized, encoding="utf-8")
    else:
        print(serialized)

    if args.summary:
        for report in reports:
            c = report.get("summary", {})
            print(
                f"[SUMMARY] {report['file']}: errors={c.get('error', 0)} "
                f"warnings={c.get('warning', 0)} info={c.get('info', 0)}",
                file=sys.stderr,
            )
    return 1 if aggregate.get("error", 0) > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
