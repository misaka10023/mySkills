"""apply_theme.py — Apply an Office theme + variant to a Visio .vsdx.

Two strategies, selected by ``--method``:

* ``com``  — drives Visio.Application via pywin32 and calls
             ``Document.SetTheme`` / ``Document.SetThemeVariant`` (or
             ``Page.*`` overloads when ``--pages`` is given). Highest
             fidelity because Visio rewrites derived ShapeSheet values.
* ``vsdx`` — patches ``visio/theme/theme1.xml`` directly with a vetted
             theme XML payload from ``scripts/assets/themes/`` and updates
             ``VariantThemeIndex`` / ``VariantColorIndex`` cells in
             ``visio/document.xml`` (or in pages.xml ``PageSheet`` rows
             when ``--pages`` is given). No Visio install required.
* ``auto`` — try COM first, fall back to vsdx on failure.

Usage::

    python apply_theme.py apply input.vsdx --theme facet
    python apply_theme.py apply input.vsdx --theme slice --variant 2 \\
        --method vsdx --in-place
    python apply_theme.py apply input.vsdx --theme wisp --pages 1,3-5 \\
        --out themed.vsdx
    python apply_theme.py list-themes
    python apply_theme.py inspect input.vsdx

Bundled themes (case-insensitive): office, facet, ion, slice, wisp, berlin.

Optional dependencies (declared, not installed by this script):
    pywin32 >=305  (only with ``--method com`` / ``auto``)

Lazy-imported; absence prints a friendly error and the vsdx fallback
continues to work without it.

Exit codes: 0 success, 1 runtime failure, 2 usage error.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
import zipfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Optional, Sequence
from xml.etree import ElementTree as ET

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SCRIPT_DIR: Path = Path(__file__).resolve().parent
ASSETS_DIR: Path = SCRIPT_DIR / "assets" / "themes"

NS_A = "http://schemas.openxmlformats.org/drawingml/2006/main"
NS_V = "http://schemas.microsoft.com/office/visio/2012/main"
NS_R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

# Theme registry: user-key -> {file: bundled XML, name: canonical Visio gallery name}.
# The "name" is what Document.SetTheme expects in the COM path.
THEMES: dict[str, dict[str, str]] = {
    "office": {"file": "office.xml", "name": "Office"},
    "facet":  {"file": "facet.xml",  "name": "Facet"},
    "ion":    {"file": "ion.xml",    "name": "Ion"},
    "slice":  {"file": "slice.xml",  "name": "Slice"},
    "wisp":   {"file": "wisp.xml",   "name": "Whisp"},
    "berlin": {"file": "berlin.xml", "name": "Berlin"},
}


def _resolve_theme_key(theme: str) -> str:
    """Normalise a user-provided theme name to a registry key."""
    key = theme.strip().lower()
    if key not in THEMES:
        raise KeyError(
            f"Unknown theme '{theme}'. Available: {', '.join(sorted(THEMES))}"
        )
    return key


# ---------------------------------------------------------------------------
# COM strategy
# ---------------------------------------------------------------------------

def _try_import_pywin32() -> tuple[Any, Any]:
    """Lazy import of pywin32 modules; returns (pythoncom, win32com.client) or (None, None)."""
    try:
        import pythoncom  # type: ignore[import-not-found]
        import win32com.client as win32  # type: ignore[import-not-found]
        return pythoncom, win32
    except ImportError:
        return None, None


@contextmanager
def _visio_app(visible: bool = False) -> Iterator[Any]:
    """Context manager that initialises COM, dispatches Visio, and tears it down."""
    pythoncom, win32 = _try_import_pywin32()
    if win32 is None:
        raise RuntimeError(
            "pywin32 is not installed. Install it (pip install pywin32) "
            "to use the COM path, or rerun with --method vsdx."
        )
    pythoncom.CoInitialize()
    app = None
    try:
        try:
            app = win32.gencache.EnsureDispatch("Visio.Application")
        except Exception:  # gencache failures fall back to late binding
            app = win32.Dispatch("Visio.Application")
        app.Visible = visible
        app.AlertResponse = 7  # IDNO — suppress all dialogs during batch ops
        yield app
    finally:
        if app is not None:
            try:
                app.Quit()
            except Exception:
                pass
        pythoncom.CoUninitialize()


def apply_via_com(
    src: Path,
    dst: Path,
    theme_key: str,
    variant: int,
    pages: Optional[Sequence[int]] = None,
) -> dict[str, Any]:
    """Apply theme via COM; opens dst (copying from src first if dst != src)."""
    if dst.resolve() != src.resolve():
        shutil.copy2(src, dst)

    com_name = THEMES[theme_key]["name"]

    try:
        from pywintypes import com_error  # type: ignore[import-not-found]
    except ImportError:
        com_error = Exception  # type: ignore[assignment,misc]

    with _visio_app(visible=False) as app:
        try:
            doc = app.Documents.Open(str(dst))
        except com_error as exc:  # type: ignore[misc]
            raise RuntimeError(f"Visio COM Open failed: {exc}") from exc

        try:
            if pages:
                applied_pages: list[int] = []
                page_count = int(doc.Pages.Count)
                for idx in pages:
                    if idx < 1 or idx > page_count:
                        continue
                    page = doc.Pages.Item(idx)
                    page.SetTheme(com_name)
                    page.SetThemeVariant(int(variant))
                    applied_pages.append(int(idx))
                doc.Save()
                applied_idx = int(doc.PageSheet.CellsU("ThemeIndex").ResultIU)
                return {
                    "method": "com",
                    "theme": com_name,
                    "variant": variant,
                    "pages": applied_pages,
                    "themeIndex": applied_idx,
                    "output": str(dst),
                }

            doc.SetTheme(com_name)
            doc.SetThemeVariant(int(variant))
            doc.Save()
            applied_idx = int(doc.PageSheet.CellsU("ThemeIndex").ResultIU)
            return {
                "method": "com",
                "theme": com_name,
                "variant": variant,
                "pages": "all",
                "themeIndex": applied_idx,
                "output": str(dst),
            }
        finally:
            try:
                doc.Close()
            except Exception:
                pass


# ---------------------------------------------------------------------------
# VSDX (fallback) strategy
# ---------------------------------------------------------------------------

def _read_theme_payload(theme_key: str) -> bytes:
    """Read the bundled theme XML from scripts/assets/themes/<key>.xml."""
    asset = ASSETS_DIR / THEMES[theme_key]["file"]
    if not asset.is_file():
        raise FileNotFoundError(
            f"Bundled theme XML missing: {asset}. "
            "Ensure scripts/assets/themes/ ships with the package."
        )
    return asset.read_bytes()


def _set_or_create_cell(parent: ET.Element, name: str, value: str) -> None:
    """Idempotent <Cell N="name" V="value"/> upsert under ``parent``."""
    qn_cell = f"{{{NS_V}}}Cell"
    for cell in parent.findall(qn_cell):
        if cell.get("N") == name:
            cell.set("V", value)
            # Drop any stale formula so V wins on next open.
            if "F" in cell.attrib:
                del cell.attrib["F"]
            return
    new_cell = ET.SubElement(parent, qn_cell)
    new_cell.set("N", name)
    new_cell.set("V", value)


def _serialize(root: ET.Element) -> bytes:
    """Serialise an ElementTree root with XML declaration + UTF-8."""
    return ET.tostring(root, xml_declaration=True, encoding="UTF-8")


def _patch_document_xml(xml_bytes: bytes, variant: int) -> bytes:
    """Stamp variant cells on DocumentSheet and append <RecalcDocument/>."""
    ET.register_namespace("", NS_V)
    ET.register_namespace("r", NS_R)
    root = ET.fromstring(xml_bytes)

    docsheet = root.find(f"{{{NS_V}}}DocumentSheet")
    if docsheet is not None:
        _set_or_create_cell(docsheet, "VariantThemeIndex", str(variant))
        _set_or_create_cell(docsheet, "VariantColorIndex", str(variant))
        _set_or_create_cell(docsheet, "VariantEmbellishmentIdx", "0")
        _set_or_create_cell(docsheet, "VariantFontIdx", "0")
        _set_or_create_cell(docsheet, "VariantStyleIdx", "0")

    qn_recalc = f"{{{NS_V}}}RecalcDocument"
    if root.find(qn_recalc) is None:
        ET.SubElement(root, qn_recalc)

    return _serialize(root)


def _patch_pages_xml_full(xml_bytes: bytes, variant: int, pages: Sequence[int]) -> tuple[bytes, list[int]]:
    """Returns (new_pages_xml_bytes, list_of_applied_1based_page_indices)."""
    ET.register_namespace("", NS_V)
    ET.register_namespace("r", NS_R)
    root = ET.fromstring(xml_bytes)

    qn_page = f"{{{NS_V}}}Page"
    qn_pagesheet = f"{{{NS_V}}}PageSheet"

    page_list = list(root.findall(qn_page))
    pages_set = {p - 1 for p in pages if p >= 1}
    applied: list[int] = []

    for idx, page_el in enumerate(page_list):
        if idx not in pages_set:
            continue
        ps = page_el.find(qn_pagesheet)
        if ps is None:
            ps = ET.SubElement(page_el, qn_pagesheet)
        _set_or_create_cell(ps, "VariantThemeIndex", str(variant))
        _set_or_create_cell(ps, "VariantColorIndex", str(variant))
        _set_or_create_cell(ps, "VariantEmbellishmentIdx", "0")
        applied.append(idx + 1)

    return _serialize(root), applied


@contextmanager
def _vsdx_session(src: Path, dst: Path) -> Iterator[Path]:
    """Unzip src into a temp folder, yield it, then rezip to dst."""
    if not src.is_file():
        raise FileNotFoundError(src)
    work = Path(tempfile.mkdtemp(prefix="vsdx_theme_"))
    try:
        with zipfile.ZipFile(src, "r") as zin:
            zin.extractall(work)
        yield work

        # Repack — Content_Types first per OPC convention.
        members = sorted(p for p in work.rglob("*") if p.is_file())
        ct = work / "[Content_Types].xml"
        if ct in members:
            members.remove(ct)
            members.insert(0, ct)

        # Atomic write via sibling temp file (works when dst == src).
        dst.parent.mkdir(parents=True, exist_ok=True)
        tmp_zip = dst.with_name(dst.name + ".__tmp__")
        try:
            with zipfile.ZipFile(tmp_zip, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zout:
                for p in members:
                    zout.write(p, p.relative_to(work).as_posix())
            tmp_zip.replace(dst)
        finally:
            if tmp_zip.exists():
                try:
                    tmp_zip.unlink()
                except OSError:
                    pass
    finally:
        shutil.rmtree(work, ignore_errors=True)


def apply_via_vsdx(
    src: Path,
    dst: Path,
    theme_key: str,
    variant: int,
    pages: Optional[Sequence[int]] = None,
) -> dict[str, Any]:
    """Patch theme1.xml in place; touch document.xml / pages.xml variant cells."""
    payload = _read_theme_payload(theme_key)
    canonical_name = THEMES[theme_key]["name"]

    applied_pages: list[int] | str = []

    with _vsdx_session(src, dst) as work:
        theme_path = work / "visio" / "theme" / "theme1.xml"
        if not theme_path.is_file():
            raise FileNotFoundError(
                f"Document does not contain visio/theme/theme1.xml: {src}"
            )
        theme_path.write_bytes(payload)

        doc_xml_path = work / "visio" / "document.xml"
        if doc_xml_path.is_file():
            doc_xml_path.write_bytes(
                _patch_document_xml(doc_xml_path.read_bytes(), variant)
            )

        if pages:
            pages_xml_path = work / "visio" / "pages" / "pages.xml"
            if pages_xml_path.is_file():
                new_bytes, applied_pages = _patch_pages_xml_full(
                    pages_xml_path.read_bytes(), variant, pages,
                )
                pages_xml_path.write_bytes(new_bytes)
            else:
                applied_pages = []
        else:
            applied_pages = "all"

    return {
        "method": "vsdx",
        "theme": canonical_name,
        "themeKey": theme_key,
        "variant": variant,
        "pages": applied_pages,
        "output": str(dst),
    }


# ---------------------------------------------------------------------------
# Inspect
# ---------------------------------------------------------------------------

def inspect_document(src: Path) -> dict[str, Any]:
    """Return a JSON-serialisable summary of the document's current theme."""
    if not src.is_file():
        raise FileNotFoundError(src)
    info: dict[str, Any] = {"file": str(src)}

    with zipfile.ZipFile(src, "r") as z:
        try:
            theme_bytes = z.read("visio/theme/theme1.xml")
        except KeyError:
            info["theme"] = None
        else:
            try:
                root = ET.fromstring(theme_bytes)
                info["theme"] = root.get("name", "")
                cs = root.find(f".//{{{NS_A}}}clrScheme")
                if cs is not None:
                    info["clrSchemeName"] = cs.get("name", "")
                    accents: dict[str, str] = {}
                    for slot in (
                        "accent1", "accent2", "accent3",
                        "accent4", "accent5", "accent6",
                    ):
                        node = cs.find(f"{{{NS_A}}}{slot}")
                        if node is None:
                            continue
                        srgb = node.find(f"{{{NS_A}}}srgbClr")
                        if srgb is not None and srgb.get("val"):
                            accents[slot] = srgb.get("val", "")
                    info["accents"] = accents
            except ET.ParseError as exc:
                info["theme"] = f"<parse error: {exc}>"

        try:
            dx = z.read("visio/document.xml")
        except KeyError:
            return info
        try:
            droot = ET.fromstring(dx)
            ds = droot.find(f"{{{NS_V}}}DocumentSheet")
            if ds is not None:
                for cell in ds.findall(f"{{{NS_V}}}Cell"):
                    n = cell.get("N", "")
                    if n in (
                        "VariantThemeIndex",
                        "VariantColorIndex",
                        "VariantEmbellishmentIdx",
                        "VariantFontIdx",
                        "VariantStyleIdx",
                        "ThemeIndex",
                    ):
                        info[n] = cell.get("V")
        except ET.ParseError:
            pass

    return info


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_pages(spec: str) -> list[int]:
    """Parse '1,3-5,7' style page lists into a sorted unique list of ints."""
    out: set[int] = set()
    for chunk in spec.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "-" in chunk:
            lo_str, hi_str = chunk.split("-", 1)
            lo, hi = int(lo_str), int(hi_str)
            if lo > hi:
                lo, hi = hi, lo
            out.update(range(lo, hi + 1))
        else:
            out.add(int(chunk))
    return sorted(out)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="apply_theme",
        description="Apply an Office theme + variant to a Visio .vsdx",
    )
    sub = p.add_subparsers(dest="command", required=True)

    apply_p = sub.add_parser("apply", help="Apply a theme and variant")
    apply_p.add_argument("input", type=Path, help="Source .vsdx path")
    apply_p.add_argument(
        "--out", type=Path, default=None,
        help="Output path (default: <input>.themed.vsdx; ignored with --in-place)",
    )
    apply_p.add_argument(
        "--in-place", action="store_true",
        help="Overwrite the input file (mutually exclusive with --out)",
    )
    apply_p.add_argument(
        "--theme", required=True,
        choices=sorted(THEMES.keys()),
        help="Theme name (case-insensitive)",
    )
    apply_p.add_argument(
        "--variant", type=int, default=1, choices=[1, 2, 3, 4],
        help="Variant index 1-4 (default 1)",
    )
    apply_p.add_argument(
        "--pages", default=None,
        help="Comma-separated 1-based page indices, e.g. '1,3-5' (default: all)",
    )
    apply_p.add_argument(
        "--method", choices=["auto", "com", "vsdx"], default="auto",
        help="Apply path: auto (try COM, fall back to vsdx), com only, or vsdx only",
    )

    sub.add_parser("list-themes", help="List bundled theme names")

    inspect_p = sub.add_parser("inspect", help="Show current theme info")
    inspect_p.add_argument("input", type=Path)

    return p


def _do_apply(args: argparse.Namespace) -> int:
    src: Path = args.input
    if not src.is_file():
        print(f"error: input file not found: {src}", file=sys.stderr)
        return 1
    if args.in_place and args.out is not None:
        print("error: --in-place and --out are mutually exclusive", file=sys.stderr)
        return 2

    if args.in_place:
        dst = src
    elif args.out is not None:
        dst = args.out
    else:
        dst = src.with_suffix(".themed.vsdx")

    try:
        theme_key = _resolve_theme_key(args.theme)
    except KeyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    pages = _parse_pages(args.pages) if args.pages else None

    method = args.method
    summary: Optional[dict[str, Any]] = None
    fallback_notes: list[str] = []

    if method in ("auto", "com"):
        pythoncom, win32 = _try_import_pywin32()
        com_available = win32 is not None
        if not com_available and method == "com":
            print(
                "error: pywin32 is not installed; cannot use --method com",
                file=sys.stderr,
            )
            return 1
        if com_available:
            try:
                summary = apply_via_com(src, dst, theme_key, args.variant, pages)
            except Exception as exc:  # COM/Visio errors are heterogeneous
                if method == "com":
                    print(f"error: COM apply failed: {exc}", file=sys.stderr)
                    return 1
                fallback_notes.append(f"com: {type(exc).__name__}: {exc}")
                summary = None

    if summary is None and method in ("auto", "vsdx"):
        try:
            summary = apply_via_vsdx(src, dst, theme_key, args.variant, pages)
        except (FileNotFoundError, KeyError, zipfile.BadZipFile) as exc:
            print(f"error: vsdx apply failed: {exc}", file=sys.stderr)
            for note in fallback_notes:
                print(f"  prior: {note}", file=sys.stderr)
            return 1

    if summary is None:
        print("error: no apply method succeeded", file=sys.stderr)
        return 1

    if fallback_notes:
        summary["fallback_from"] = fallback_notes

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def _do_list_themes(_args: argparse.Namespace) -> int:
    payload = {
        "themes": [
            {
                "key": k,
                "name": v["name"],
                "asset": str(ASSETS_DIR / v["file"]),
                "available": (ASSETS_DIR / v["file"]).is_file(),
            }
            for k, v in sorted(THEMES.items())
        ],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def _do_inspect(args: argparse.Namespace) -> int:
    try:
        info = inspect_document(args.input)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except zipfile.BadZipFile as exc:
        print(f"error: not a valid .vsdx (bad zip): {exc}", file=sys.stderr)
        return 1
    print(json.dumps(info, ensure_ascii=False, indent=2))
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "apply":
        return _do_apply(args)
    if args.command == "list-themes":
        return _do_list_themes(args)
    if args.command == "inspect":
        return _do_inspect(args)
    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
