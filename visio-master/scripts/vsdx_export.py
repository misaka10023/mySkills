#!/usr/bin/env python3
"""Visio Master - VSDX Export Tool.

Export Visio drawings (.vsdx) to PDF, PNG, SVG, or all of the above. The
preferred path uses the Visio COM Automation surface via ``pywin32``:

* PDF -- ``Document.ExportAsFixedFormat`` with ``visFixedFormatPDF``.
* PNG -- per-page ``Page.Export`` with ``Application.Settings.PNG*`` knobs.
* SVG -- per-page ``Page.Export`` with ``Application.Settings.SVG*`` knobs.

When pywin32 is unavailable but the ``vsdx`` Python package is installed, the
script can still report document structure (page names, page count) but emits
a clear ``requires Visio installed`` error for actual rendering -- the
``vsdx`` package parses the OPC bundle, it does not render shapes.

Outputs land under ``<project_path>/exports/``.

Usage examples:
    python scripts/vsdx_export.py pdf <project_path> --vsdx diagram.vsdx
    python scripts/vsdx_export.py png <project_path> --vsdx diagram.vsdx \\
        --from 2 --to 5 --dpi 300
    python scripts/vsdx_export.py svg <project_path> --embed-fonts
    python scripts/vsdx_export.py all <project_path> --vsdx diagram.vsdx

Dependencies (declared, not installed):
    pywin32 -- required for rendering; install via
               ``py -m pip install pywin32 && py -m pywin32_postinstall -install``.
    vsdx    -- optional; enables structural fallback (page listing only).

Exit codes: 0 success, 1 recoverable error, 2 environment error.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence

# Optional dependencies.  Lazy guards keep --help working on Linux / CI where
# neither pywin32 nor vsdx is installed.
try:
    import pythoncom  # type: ignore[import-not-found]
    import pywintypes  # type: ignore[import-not-found]
    import win32com.client as w32  # type: ignore[import-not-found]
    _HAS_PYWIN32 = True
except ImportError:  # pragma: no cover - import-time platform guard
    pythoncom = None  # type: ignore[assignment]
    pywintypes = None  # type: ignore[assignment]
    w32 = None  # type: ignore[assignment]
    _HAS_PYWIN32 = False

try:
    import vsdx  # type: ignore[import-not-found]
    _HAS_VSDX = True
except ImportError:  # pragma: no cover - optional dependency
    vsdx = None  # type: ignore[assignment]
    _HAS_VSDX = False


# Visio Automation constants (stable across Visio 2010-2024).  Hard-coded so
# the script runs even if makepy stubs have not been generated.
VIS_OPEN_RO: int = 2
VIS_OPEN_HIDDEN: int = 64
VIS_OPEN_MACROS_DISABLED: int = 128
VIS_OPEN_NO_WORKSPACE: int = 256

VIS_FIXED_FORMAT_PDF: int = 1
VIS_DOC_EX_INTENT_PRINT: int = 1
VIS_DOC_EX_INTENT_SCREEN: int = 2
VIS_DOC_EX_MARKUP_NONE: int = 0

VIS_PRINT_ALL: int = 0
VIS_PRINT_FROM_TO: int = 1

# ApplicationSettings: per-format resolution / size families.
VIS_RES_CUSTOM: int = 3
VIS_SIZE_SOURCE: int = 0

# Page-type discriminator on Page.Type.
VIS_TYPE_FOREGROUND: int = 0

# AlertResponse: 7 == "No" / "Cancel" -> suppresses interactive prompts.
VIS_ALERT_RESPONSE_CANCEL: int = 7


# Data classes for CLI args / report payload.
@dataclass(slots=True)
class ExportRequest:
    """Resolved export parameters after argparse + filesystem discovery."""

    command: str
    project_path: Path
    vsdx_path: Path
    out_dir: Path
    page_from: int | None = None
    page_to: int | None = None
    dpi: int = 200
    intent: str = "print"  # "print" or "screen"
    include_background: bool = True
    embed_fonts: bool = True
    precise_geometry: bool = True


@dataclass(slots=True)
class ExportSummary:
    """Structured outcome printed at the end of a successful run."""

    command: str
    vsdx_path: str
    out_dir: str
    pdf_path: str | None = None
    png_paths: list[str] = field(default_factory=list)
    svg_paths: list[str] = field(default_factory=list)
    pages_exported: int = 0
    elapsed_seconds: float = 0.0
    backend: str = "com"

    def as_dict(self) -> dict[str, Any]:
        return {
            "command": self.command,
            "backend": self.backend,
            "vsdx_path": self.vsdx_path,
            "out_dir": self.out_dir,
            "pdf_path": self.pdf_path,
            "png_paths": list(self.png_paths),
            "svg_paths": list(self.svg_paths),
            "pages_exported": self.pages_exported,
            "elapsed_seconds": round(self.elapsed_seconds, 3),
        }


# Filesystem helpers.
def _resolve_vsdx_path(project_path: Path, vsdx_arg: str | None) -> Path:
    """Locate the source .vsdx file inside the project tree.

    Resolution order:
        1. If ``vsdx_arg`` is an absolute / relative path that exists, use it.
        2. Otherwise treat it as a filename under ``<project_path>``.
        3. Fall back to the first ``*.vsdx`` found in ``<project_path>``.
    """
    if vsdx_arg:
        candidate = Path(vsdx_arg)
        if candidate.is_file():
            return candidate.resolve()
        nested = project_path / vsdx_arg
        if nested.is_file():
            return nested.resolve()
        raise FileNotFoundError(
            f"VSDX file not found: '{vsdx_arg}' (looked at '{candidate}' and "
            f"'{nested}')"
        )
    matches = sorted(project_path.glob("*.vsdx"))
    if not matches:
        raise FileNotFoundError(
            f"No .vsdx file found in '{project_path}'. Pass --vsdx <name>."
        )
    return matches[0].resolve()


def _ensure_out_dir(project_path: Path) -> Path:
    """Create ``<project_path>/exports`` and return the absolute path."""
    out = (project_path / "exports").resolve()
    out.mkdir(parents=True, exist_ok=True)
    return out


def _safe_stem(name: str) -> str:
    """Sanitise a Visio page name for use as a filesystem stem."""
    bad = '<>:"/\\|?*'
    cleaned = "".join("_" if ch in bad else ch for ch in name).strip()
    return cleaned or "page"


# COM helpers.
def _require_pywin32() -> None:
    """Abort with a helpful message when pywin32 is not importable."""
    if not _HAS_PYWIN32:
        raise RuntimeError(
            "Rendering requires pywin32 and a local Visio installation. "
            "Install with: py -m pip install pywin32 && "
            "py -m pywin32_postinstall -install."
        )


def _open_visio_app() -> Any:
    """Spawn a hidden Visio.InvisibleApp instance, ready for headless work."""
    app = w32.DispatchEx("Visio.InvisibleApp")
    app.Visible = False
    app.AlertResponse = VIS_ALERT_RESPONSE_CANCEL
    for attr, value in (("ScreenUpdating", 0), ("EventsEnabled", 0)):
        try:
            setattr(app, attr, value)
        except Exception:  # pragma: no cover - older Visio editions
            pass
    return app


def _open_document(app: Any, vsdx_path: Path) -> Any:
    """Open ``vsdx_path`` read-only / hidden / no-workspace / no-macros."""
    flags = (
        VIS_OPEN_RO | VIS_OPEN_HIDDEN
        | VIS_OPEN_NO_WORKSPACE | VIS_OPEN_MACROS_DISABLED
    )
    return app.Documents.OpenEx(str(vsdx_path), flags)


def _select_page_range(
    doc: Any, page_from: int | None, page_to: int | None
) -> tuple[int, int, int]:
    """Compute (from, to, total) 1-based indices over foreground pages.

    Mirrors Visio's PrintRange / FromPage / ToPage semantics, which count
    only foreground pages (background pages are skipped).
    """
    fg_total = sum(
        1 for p in doc.Pages if int(getattr(p, "Type", 0)) == VIS_TYPE_FOREGROUND
    )
    if fg_total == 0:
        raise RuntimeError("Document contains no foreground pages.")
    lo = 1 if page_from is None else max(1, int(page_from))
    hi = fg_total if page_to is None else min(fg_total, int(page_to))
    if lo > hi:
        raise ValueError(
            f"Empty page range: from={lo} > to={hi} (document has {fg_total} pages)."
        )
    return lo, hi, fg_total


def _foreground_pages(doc: Any) -> list[Any]:
    """Foreground pages in document order (1-based -> list index)."""
    return [
        p for p in doc.Pages
        if int(getattr(p, "Type", VIS_TYPE_FOREGROUND)) == VIS_TYPE_FOREGROUND
    ]


def _format_com_error(exc: Any) -> str:
    """Extract a human-readable description from a pywintypes.com_error."""
    try:
        hresult, source, excepinfo, _argerr = exc.args
    except Exception:
        return str(exc)
    if excepinfo and len(excepinfo) >= 6:
        descr = excepinfo[2] or ""
        scode = excepinfo[5]
        return f"Visio COM error (HRESULT={hresult:#010x}, SCODE={scode}): {descr}"
    return f"Visio COM error (HRESULT={hresult:#010x}, source={source})"


# COM export commands.
def _export_pdf_via_com(req: ExportRequest, summary: ExportSummary) -> None:
    """Invoke ``Document.ExportAsFixedFormat`` for the requested page range."""
    _require_pywin32()
    pythoncom.CoInitialize()
    app = None
    doc = None
    try:
        app = _open_visio_app()
        try:
            doc = _open_document(app, req.vsdx_path)
            lo, hi, total = _select_page_range(doc, req.page_from, req.page_to)
            range_suffix = "" if (lo == 1 and hi == total) else f"_p{lo:02d}-p{hi:02d}"
            pdf_path = req.out_dir / f"{req.vsdx_path.stem}{range_suffix}.pdf"
            print_range = VIS_PRINT_ALL if (lo == 1 and hi == total) else VIS_PRINT_FROM_TO
            intent = (
                VIS_DOC_EX_INTENT_PRINT
                if req.intent == "print"
                else VIS_DOC_EX_INTENT_SCREEN
            )
            doc.ExportAsFixedFormat(
                VIS_FIXED_FORMAT_PDF, str(pdf_path), intent, print_range,
                lo, hi,
                True,                       # IncludeDocumentProperties
                True,                       # IncludeDocumentStructureTags
                VIS_DOC_EX_MARKUP_NONE,
            )
            summary.pdf_path = str(pdf_path)
            summary.pages_exported += (hi - lo + 1)
        finally:
            if doc is not None:
                doc.Close()
    except pywintypes.com_error as exc:  # type: ignore[union-attr]
        raise RuntimeError(_format_com_error(exc)) from exc
    finally:
        if app is not None:
            try:
                app.Quit()
            except Exception:  # pragma: no cover - best-effort teardown
                pass
        pythoncom.CoUninitialize()


def _apply_png_settings(app: Any, dpi: int) -> None:
    """Configure ``Application.Settings`` for crisp custom-DPI PNG output."""
    s = app.Settings
    s.PNGFileResolutionType = VIS_RES_CUSTOM
    s.PNGFileResolutionX = float(dpi)
    s.PNGFileResolutionY = float(dpi)
    s.PNGExportSizeType = VIS_SIZE_SOURCE
    for attr, value in (("PNGExportFilter", 5), ("PNGExportInterlace", False)):
        try:
            setattr(s, attr, value)
        except Exception:  # pragma: no cover - older Visio editions
            pass


def _apply_svg_settings(
    app: Any, embed_fonts: bool, precise_geometry: bool
) -> None:
    """Configure ``Application.Settings`` for SVG export."""
    s = app.Settings
    for attr, value in (
        ("SVGExportEmbedFonts", bool(embed_fonts)),
        ("SVGExportPreciseGeometry", bool(precise_geometry)),
        ("SVGExportStyleAsAttribute", False),  # smaller output via <style> blocks
    ):
        try:
            setattr(s, attr, value)
        except Exception:  # pragma: no cover - older Visio editions
            pass


def _export_per_page_via_com(
    req: ExportRequest, summary: ExportSummary, suffix: str
) -> None:
    """Drive ``Page.Export`` for every page in the selected range.

    ``suffix`` selects the encoder (``.png`` or ``.svg``); Visio infers the
    output format from the destination extension.
    """
    _require_pywin32()
    if suffix not in {".png", ".svg"}:
        raise ValueError(f"Unsupported per-page suffix: {suffix!r}")
    pythoncom.CoInitialize()
    app = None
    doc = None
    try:
        app = _open_visio_app()
        if suffix == ".png":
            _apply_png_settings(app, req.dpi)
        else:
            _apply_svg_settings(app, req.embed_fonts, req.precise_geometry)
        try:
            doc = _open_document(app, req.vsdx_path)
            lo, hi, _total = _select_page_range(doc, req.page_from, req.page_to)
            fg_pages = _foreground_pages(doc)
            sink = summary.png_paths if suffix == ".png" else summary.svg_paths
            for idx in range(lo, hi + 1):
                page = fg_pages[idx - 1]
                stem = _safe_stem(str(page.Name))
                out_path = req.out_dir / f"{req.vsdx_path.stem}_p{idx:02d}_{stem}{suffix}"
                page.Export(str(out_path))
                sink.append(str(out_path))
                summary.pages_exported += 1
        finally:
            if doc is not None:
                doc.Close()
    except pywintypes.com_error as exc:  # type: ignore[union-attr]
        raise RuntimeError(_format_com_error(exc)) from exc
    finally:
        if app is not None:
            try:
                app.Quit()
            except Exception:  # pragma: no cover - best-effort teardown
                pass
        pythoncom.CoUninitialize()


# vsdx-only fallback (structural, never rendering).
def _fallback_inspect(req: ExportRequest, summary: ExportSummary) -> None:
    """List page metadata using the pure-Python vsdx parser.

    Useful for environments without Visio (Linux CI, headless containers).
    Rendering is not supported -- vsdx parses the OPC bundle, it does not
    rasterise or vectorise shapes.
    """
    if not _HAS_VSDX:
        raise RuntimeError(
            "Rendering requires Visio installed (pywin32). The vsdx Python "
            "library is also unavailable, so structural inspection is not "
            "possible either.  Install vsdx for a metadata-only fallback "
            "via: py -m pip install vsdx."
        )
    print(
        "[fallback] Visio not detected; emitting structural metadata only. "
        "PDF / PNG / SVG rendering requires a local Visio installation.",
        file=sys.stderr,
    )
    with vsdx.VisioFile(str(req.vsdx_path)) as vfile:  # type: ignore[union-attr]
        page_names = [getattr(p, "name", f"Page-{i}") for i, p in enumerate(vfile.pages, start=1)]
    metadata_path = req.out_dir / f"{req.vsdx_path.stem}.metadata.json"
    metadata_path.write_text(
        json.dumps(
            {
                "vsdx_path": str(req.vsdx_path),
                "page_count": len(page_names),
                "page_names": page_names,
                "note": (
                    "Rendering requires Visio installed. Install pywin32 and "
                    "Microsoft Visio to produce PDF / PNG / SVG output."
                ),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    summary.backend = "vsdx-fallback"
    summary.pages_exported = len(page_names)


# Command dispatchers.
_PER_PAGE_SUFFIX = {"png": ".png", "svg": ".svg"}


def _dispatch(req: ExportRequest, summary: ExportSummary) -> None:
    """Route ``req.command`` to COM exporters or the vsdx fallback."""
    if not _HAS_PYWIN32:
        _fallback_inspect(req, summary)
        return
    if req.command == "pdf":
        _export_pdf_via_com(req, summary)
    elif req.command in _PER_PAGE_SUFFIX:
        _export_per_page_via_com(req, summary, _PER_PAGE_SUFFIX[req.command])
    elif req.command == "all":
        _export_pdf_via_com(req, summary)
        _export_per_page_via_com(req, summary, ".png")
        _export_per_page_via_com(req, summary, ".svg")
    else:
        raise KeyError(f"Unknown command: {req.command!r}")


# CLI plumbing.
def _add_common_args(sub: argparse.ArgumentParser) -> None:
    sub.add_argument(
        "project_path", type=Path,
        help="Project directory; output goes to <project_path>/exports/.",
    )
    sub.add_argument(
        "--vsdx", type=str, default=None,
        help="VSDX file path or filename under <project_path>. "
             "Defaults to the first *.vsdx in the project directory.",
    )
    sub.add_argument(
        "--from", dest="page_from", type=int, default=None,
        help="1-based first foreground page to export (inclusive).",
    )
    sub.add_argument(
        "--to", dest="page_to", type=int, default=None,
        help="1-based last foreground page to export (inclusive).",
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vsdx_export",
        description=(
            "Export Visio drawings to PDF / PNG / SVG via the Visio COM "
            "Automation surface (pywin32). Falls back to vsdx metadata "
            "inspection when Visio is not installed."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  %(prog)s pdf  ./my-project --vsdx flow.vsdx\n"
            "  %(prog)s png  ./my-project --vsdx flow.vsdx --from 1 --to 3 --dpi 300\n"
            "  %(prog)s svg  ./my-project --embed-fonts\n"
            "  %(prog)s all  ./my-project --vsdx flow.vsdx\n"
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_pdf = sub.add_parser("pdf", help="Export the document (or page range) to a single PDF.")
    _add_common_args(p_pdf)
    p_pdf.add_argument(
        "--intent", choices=("print", "screen"), default="print",
        help="visDocExIntentPrint (vector, archival) or visDocExIntentScreen "
             "(rasterised effects, smaller). Default: print.",
    )

    p_png = sub.add_parser("png", help="Export each page to a PNG file.")
    _add_common_args(p_png)
    p_png.add_argument(
        "--dpi", type=int, default=200,
        help="Custom DPI for PNG export. Default: 200.",
    )

    p_svg = sub.add_parser("svg", help="Export each page to an SVG file.")
    _add_common_args(p_svg)
    p_svg.add_argument(
        "--embed-fonts", dest="embed_fonts", action="store_true", default=True,
        help="Set SVGExportEmbedFonts = True (default).",
    )
    p_svg.add_argument(
        "--no-embed-fonts", dest="embed_fonts", action="store_false",
        help="Set SVGExportEmbedFonts = False; rely on consumer fonts.",
    )
    p_svg.add_argument(
        "--precise-geometry", dest="precise_geometry", action="store_true", default=True,
        help="Set SVGExportPreciseGeometry = True (default).",
    )
    p_svg.add_argument(
        "--no-precise-geometry", dest="precise_geometry", action="store_false",
        help="Allow Visio to flatten curves for smaller files.",
    )

    p_all = sub.add_parser("all", help="Run pdf + png + svg back-to-back.")
    _add_common_args(p_all)
    p_all.add_argument("--dpi", type=int, default=200)
    p_all.add_argument("--intent", choices=("print", "screen"), default="print")
    p_all.add_argument("--embed-fonts", dest="embed_fonts", action="store_true", default=True)
    p_all.add_argument("--no-embed-fonts", dest="embed_fonts", action="store_false")

    return parser


def _build_request(ns: argparse.Namespace) -> ExportRequest:
    project_path: Path = ns.project_path.resolve()
    if not project_path.is_dir():
        raise FileNotFoundError(f"Project path is not a directory: {project_path}")

    vsdx_path = _resolve_vsdx_path(project_path, getattr(ns, "vsdx", None))
    out_dir = _ensure_out_dir(project_path)

    return ExportRequest(
        command=ns.command,
        project_path=project_path,
        vsdx_path=vsdx_path,
        out_dir=out_dir,
        page_from=getattr(ns, "page_from", None),
        page_to=getattr(ns, "page_to", None),
        dpi=int(getattr(ns, "dpi", 200)),
        intent=str(getattr(ns, "intent", "print")),
        embed_fonts=bool(getattr(ns, "embed_fonts", True)),
        precise_geometry=bool(getattr(ns, "precise_geometry", True)),
    )


def _print_summary(summary: ExportSummary) -> None:
    """Emit a JSON-ish single-line report to stdout."""
    payload = summary.as_dict()
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _emit_failure(message: str, *, env_error: bool = False) -> int:
    print(json.dumps({"status": "error", "message": message}, ensure_ascii=False))
    return 2 if env_error else 1


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    ns = parser.parse_args(argv)

    try:
        req = _build_request(ns)
    except FileNotFoundError as exc:
        return _emit_failure(str(exc))
    except (KeyError, ValueError) as exc:
        return _emit_failure(f"Invalid arguments: {exc}")

    summary = ExportSummary(
        command=req.command,
        vsdx_path=str(req.vsdx_path),
        out_dir=str(req.out_dir),
        backend="com" if _HAS_PYWIN32 else ("vsdx-fallback" if _HAS_VSDX else "none"),
    )
    handler_dispatch = _dispatch

    started = time.perf_counter()
    try:
        handler_dispatch(req, summary)
    except FileNotFoundError as exc:
        return _emit_failure(str(exc))
    except KeyError as exc:
        return _emit_failure(f"Missing required object: {exc}")
    except RuntimeError as exc:
        # Both env errors and COM errors raise RuntimeError; classify by text.
        text = str(exc)
        env = (
            "Visio installed" in text
            or "pywin32" in text
            or "vsdx" in text.lower()
        )
        return _emit_failure(text, env_error=env)
    except Exception as exc:  # pragma: no cover - last-resort safety net
        return _emit_failure(f"Unhandled error: {exc!r}")

    summary.elapsed_seconds = time.perf_counter() - started
    _print_summary(summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
