"""Shared Visio COM (pywin32) helper module for visio-master.

Centralises the small surface of Visio Automation calls used across the
visio-master script suite. Every public helper either succeeds and returns
a typed result, or raises :class:`VisioCOMError` with a human-readable
diagnostic translated from :class:`pywintypes.com_error`.

The module is import-safe on non-Windows hosts and on machines without
``pywin32`` installed; ``COM_AVAILABLE`` reports whether COM helpers can
actually run.

Usage example::

    from com_helper import VisioCOM

    with VisioCOM(visible=False) as visio:
        doc = visio.open_document(None)               # blank drawing
        page = doc.Pages.Item(1)
        master = visio.ensure_master(doc, "Process",
                                     stencil="BASFLO_M.VSSX")
        shape = visio.drop_master_at(page, master, x=4.0, y=6.0)
        visio.set_shape_text(shape, "Ingest")
        visio.batch_set_formulas(shape, {
            "PinX": "4 in", "PinY": "6 in",
            "Width": "2 in", "Height": "1 in",
        })
        visio.save_document(doc, r"C:\\out\\demo.vsdx")

CLI::

    python com_helper.py selftest             # capability JSON, no Visio
    python com_helper.py ping --visible 0     # spawn InvisibleApp, quit

Dependencies (declare-only; do NOT pip install from this script)
- pywin32              Windows-only; required for COM helpers.
- Microsoft Visio 2016+ (optional at import; required at call time).

Conforms to ``visio-master/references/shared-standards.md`` §4-§6 and
``com-quick-ref.md`` §1-§9.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Mapping, Optional, Sequence, Tuple

# Optional pywin32 import; module stays import-safe on non-Windows hosts.
COM_AVAILABLE: bool = False
COM_IMPORT_ERROR: Optional[str] = None

try:  # pragma: no cover - platform-dependent
    import pythoncom  # type: ignore[import-not-found]
    import pywintypes  # type: ignore[import-not-found]
    import win32com.client as win32  # type: ignore[import-not-found]
    COM_AVAILABLE = True
except Exception as _imp_exc:  # pragma: no cover
    pythoncom = None  # type: ignore[assignment]
    pywintypes = None  # type: ignore[assignment]
    win32 = None  # type: ignore[assignment]
    COM_IMPORT_ERROR = f"{type(_imp_exc).__name__}: {_imp_exc}"

LOG = logging.getLogger("visio_master.com_helper")
LOG.setLevel(os.environ.get("VISIO_MASTER_LOGLEVEL", "INFO").upper())

# Visio 16.0 type-library identity (stable 2010 -> 2024; minor 12 = 2019+).
TYPELIB_GUID: str = "{00021A98-0000-0000-C000-000000000046}"
TYPELIB_LCID: int = 0
TYPELIB_MAJOR: int = 4
TYPELIB_MINOR: int = 12
PROGID_INVISIBLE: str = "Visio.InvisibleApp"
PROGID_VISIBLE: str = "Visio.Application"


class VisConst:
    """Hard-coded ``vis*`` constants -- sealed-environment fallback."""
    visOpenRW, visOpenRO, visOpenCopy = 0, 2, 4
    visOpenMinimized, visOpenHidden = 16, 64
    visOpenMacrosDisabled, visOpenNoWorkspace, visOpenDocked = 128, 256, 512
    visSaveAsWS, visSaveAsListInMRU = 1, 4
    visFixedFormatPDF, visFixedFormatXPS = 1, 2
    visDocExIntentPrint, visDocExIntentScreen = 1, 2
    visPrintAll, visPrintCurrentPage, visPrintFromTo = 0, 1, 2
    visAutoConnectDirNone = 0
    visAutoConnectDirRight, visAutoConnectDirDown = 1, 2
    visAutoConnectDirLeft, visAutoConnectDirUp = 3, 4
    visAlertResponseNo = 7
    visMSDefault, visMSUS, visMSMetric = 0, 1, 2


class VisioCOMError(RuntimeError):
    """Friendly wrapper around :class:`pywintypes.com_error` and friends."""

    def __init__(self, message: str, *, hresult: Optional[int] = None,
                 source: Optional[str] = None,
                 description: Optional[str] = None,
                 cause: Optional[BaseException] = None) -> None:
        super().__init__(message)
        self.hresult, self.source, self.description = hresult, source, description
        self.__cause__ = cause

    def to_dict(self) -> dict[str, Any]:
        h = (f"0x{self.hresult & 0xFFFFFFFF:08X}"
             if self.hresult is not None else None)
        return {"message": str(self), "hresult_hex": h,
                "source": self.source, "description": self.description}


_HRESULT_HINTS: dict[int, str] = {
    0x80040154: "Visio not registered for this bitness; install Visio 2016+ "
                "or match Python bitness to Office.",
    0x80020003: "Method/property not found; stale gen_py cache or wrong cell name.",
    0x80020005: "Type mismatch; check Master vs string and float vs int.",
    0x80020009: "Visio raised an exception; see description.",
    0x800401F0: "COM not initialised on this thread.",
    0x80010001: "Visio busy; retry with backoff.",
    0x8001010A: "RPC_E_SERVERCALL_RETRYLATER; set AlertResponse=7 + back off.",
    0x8001010E: "Cross-thread COM call; Visio proxies are STA-bound.",
    0x80010106: "RPC_E_CHANGED_MODE; mixed STA/MTA on the same thread.",
    0x80010108: "Stale proxy; Visio quit unexpectedly.",
    0x800AC472: ".vsdx is open in another process.",
    0x8004D10D: "Master not found in stencil; verify NameU spelling.",
}


def _format_com_error(exc: BaseException, ctx: str) -> VisioCOMError:
    """Translate any exception (typically ``com_error``) into VisioCOMError."""
    hresult: Optional[int] = None
    source: Optional[str] = None
    description: Optional[str] = None
    args = getattr(exc, "args", ())
    if isinstance(args, tuple):
        if len(args) >= 1:
            try:
                hresult = int(args[0])
            except (TypeError, ValueError):
                hresult = None
        if len(args) >= 2 and isinstance(args[1], str):
            source = args[1]
        if len(args) >= 3 and isinstance(args[2], tuple):
            ei = args[2]
            if len(ei) >= 2 and isinstance(ei[1], str):
                source = source or ei[1]
            if len(ei) >= 3 and isinstance(ei[2], str):
                description = ei[2]
    hint = _HRESULT_HINTS.get(hresult & 0xFFFFFFFF, "") if hresult else ""
    parts = [ctx]
    if hresult is not None:
        parts.append(f"HRESULT=0x{hresult & 0xFFFFFFFF:08X}")
    if description:
        parts.append(f"detail={description!r}")
    if hint:
        parts.append(f"hint={hint}")
    return VisioCOMError(" | ".join(parts), hresult=hresult, source=source,
                         description=description, cause=exc)


def require_com() -> None:
    """Raise VisioCOMError if pywin32 is unavailable on this host."""
    if not COM_AVAILABLE:
        raise VisioCOMError(
            "pywin32 is not importable on this host; COM helpers disabled. "
            f"Original import error: {COM_IMPORT_ERROR}")


_MAKEPY_LOCK = threading.Lock()
_MAKEPY_DONE: bool = False
_MAKEPY_ERROR: Optional[str] = None


def ensure_makepy(quiet: bool = True) -> bool:
    """Idempotently emit Visio type-library stubs via gencache.EnsureModule.

    Returns True on success, False otherwise (failure does NOT raise; callers
    can still try late binding and fall back to :class:`VisConst`).
    """
    global _MAKEPY_DONE, _MAKEPY_ERROR
    if not COM_AVAILABLE:
        return False
    with _MAKEPY_LOCK:
        if _MAKEPY_DONE:
            return _MAKEPY_ERROR is None
        try:
            win32.gencache.EnsureModule(
                TYPELIB_GUID, TYPELIB_LCID, TYPELIB_MAJOR, TYPELIB_MINOR)
            _MAKEPY_DONE, _MAKEPY_ERROR = True, None
            if not quiet:
                LOG.info("makepy OK %s %d.%d",
                         TYPELIB_GUID, TYPELIB_MAJOR, TYPELIB_MINOR)
            return True
        except Exception as exc:  # pragma: no cover
            _MAKEPY_DONE, _MAKEPY_ERROR = True, f"{type(exc).__name__}: {exc}"
            if not quiet:
                LOG.warning("makepy bootstrap failed: %s", _MAKEPY_ERROR)
            return False


if COM_AVAILABLE:
    try:
        ensure_makepy(quiet=True)
    except Exception:  # pragma: no cover
        pass


@dataclass(frozen=True)
class VisCellSRC:
    """A ShapeSheet cell address as a (Section, Row, Column) integer triple."""
    section: int
    row: int
    column: int

    def as_tuple(self) -> Tuple[int, int, int]:
        return self.section, self.row, self.column


# Universal -> SRC mapping for cells written most often (visSectionObject = 1).
_CELL_SRC_TABLE: dict[str, Tuple[int, int, int]] = {
    "PinX": (1, 1, 0), "PinY": (1, 1, 1),
    "Width": (1, 1, 2), "Height": (1, 1, 3),
    "LocPinX": (1, 1, 4), "LocPinY": (1, 1, 5),
    "Angle": (1, 1, 6), "FlipX": (1, 1, 7), "FlipY": (1, 1, 8),
    "BeginX": (1, 2, 0), "BeginY": (1, 2, 1),
    "EndX": (1, 2, 2), "EndY": (1, 2, 3),
}


def cell_src(name: str) -> VisCellSRC:
    """Look up a universal cell name in the static SRC table.

    Raises ``KeyError`` if the name is not in the static table (callers should
    fall back to ``Shape.CellsU(name).FormulaU = ...`` for unmapped cells).
    """
    triple = _CELL_SRC_TABLE.get(name)
    if triple is None:
        raise KeyError(f"unknown universal cell name: {name!r}")
    return VisCellSRC(*triple)


def _flatten_srcs(addrs: Sequence[VisCellSRC]) -> list[int]:
    """Flatten ``[(s,r,c), ...]`` into the int array Visio expects."""
    out: list[int] = []
    for a in addrs:
        out.extend((a.section, a.row, a.column))
    return out


# Process-wide lock; Visio is STA, two InvisibleApps race on stencil locks.
_VISIO_LOCK = threading.Lock()


class VisioCOM:
    """Context manager that owns a hidden Visio process.

    Holds the ``Application`` proxy; callers hold their own document / page /
    shape proxies.
    """

    def __init__(self, *, visible: bool = False, screen_updating: bool = False,
                 events_enabled: bool = False, undo_enabled: bool = False,
                 defer_recalc: bool = True,
                 alert_response: int = VisConst.visAlertResponseNo,
                 suppress_autosave: bool = True) -> None:
        self._visible = visible
        self._screen_updating = screen_updating
        self._events_enabled = events_enabled
        self._undo_enabled = undo_enabled
        self._defer_recalc = defer_recalc
        self._alert_response = alert_response
        self._suppress_autosave = suppress_autosave
        self.app: Any = None
        self._lock_held: bool = False
        self._com_initialised: bool = False

    def __enter__(self) -> "VisioCOM":
        require_com()
        _VISIO_LOCK.acquire()
        self._lock_held = True
        try:
            pythoncom.CoInitializeEx(pythoncom.COINIT_APARTMENTTHREADED)
            self._com_initialised = True
            ensure_makepy(quiet=True)
            progid = PROGID_VISIBLE if self._visible else PROGID_INVISIBLE
            try:
                self.app = win32.DispatchEx(progid)
            except Exception as exc:
                raise _format_com_error(exc, f"DispatchEx({progid})") from exc
            self._configure_app()
            return self
        except BaseException:
            self._teardown_safely()
            raise

    def __exit__(self, exc_type, exc, tb) -> None:
        self._teardown_safely()

    def set_visible(self, visible: bool) -> None:
        """Show or hide Visio's main window mid-session (debugging aid)."""
        require_com()
        if self.app is None:
            raise VisioCOMError("Visio app not initialised")
        try:
            self.app.Visible = bool(visible)
            self._visible = bool(visible)
        except Exception as exc:
            raise _format_com_error(exc, "set_visible") from exc

    def _configure_app(self) -> None:
        try:
            self.app.AlertResponse = self._alert_response
            self.app.ScreenUpdating = 0 if not self._screen_updating else -1
            self.app.EventsEnabled = 0 if not self._events_enabled else -1
            self.app.UndoEnabled = bool(self._undo_enabled)
            self.app.DeferRecalc = 1 if self._defer_recalc else 0
            if self._suppress_autosave:
                try:
                    self.app.AutoRecoverInterval = 0
                except Exception:
                    pass
            if self._visible:
                self.app.Visible = True
        except Exception as exc:
            raise _format_com_error(exc, "configure_app") from exc

    def _teardown_safely(self) -> None:
        try:
            if self.app is not None:
                try:
                    self.app.AlertResponse = self._alert_response
                except Exception:
                    pass
                try:
                    self.app.Quit()
                except Exception as exc:
                    LOG.debug("app.Quit() raised: %s", exc)
                self.app = None
        finally:
            try:
                if self._com_initialised and pythoncom is not None:
                    pythoncom.CoUninitialize()
            except Exception as exc:  # pragma: no cover
                LOG.debug("CoUninitialize raised: %s", exc)
            finally:
                self._com_initialised = False
                if self._lock_held:
                    _VISIO_LOCK.release()
                    self._lock_held = False


    def open_document(self, path: Optional[Path | str], *,
                      readonly: bool = False, hidden: bool = True,
                      macros_disabled: bool = True, no_workspace: bool = True,
                      copy: bool = False, as_stencil: bool = False) -> Any:
        """Open or create a Visio document.

        ``path=None`` creates a blank drawing.  ``as_stencil=True`` opens a
        ``.vssx`` RO/Hidden/Docked (the only legal way to harvest masters).
        """
        require_com()
        if self.app is None:
            raise VisioCOMError("Visio app not initialised")
        if path is None:
            try:
                return self.app.Documents.Add("")
            except Exception as exc:
                raise _format_com_error(exc, "Documents.Add") from exc
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Visio document not found: {p}")
        if as_stencil:
            flags = (VisConst.visOpenRO | VisConst.visOpenHidden
                     | VisConst.visOpenDocked
                     | VisConst.visOpenMacrosDisabled)
        else:
            flags = 0
            if readonly:
                flags |= VisConst.visOpenRO
            if hidden:
                flags |= VisConst.visOpenHidden
            if macros_disabled:
                flags |= VisConst.visOpenMacrosDisabled
            if no_workspace:
                flags |= VisConst.visOpenNoWorkspace
            if copy:
                flags |= VisConst.visOpenCopy
        try:
            return self.app.Documents.OpenEx(str(p), flags)
        except Exception as exc:
            raise _format_com_error(exc, f"Documents.OpenEx({p!s})") from exc

    def save_document(self, doc: Any,
                      path: Optional[Path | str] = None) -> Path:
        """``SaveAs(path)`` (path given) or ``Save()`` (in-place)."""
        require_com()
        if doc is None:
            raise VisioCOMError("save_document: doc is None")
        try:
            if path is None:
                doc.Save()
                return Path(doc.FullName)
            target = Path(path)
            target.parent.mkdir(parents=True, exist_ok=True)
            doc.SaveAs(str(target))
            return target
        except Exception as exc:
            raise _format_com_error(
                exc, f"save_document(path={path!r})") from exc

    def close_document(self, doc: Any, *, force_clean: bool = True) -> None:
        """Close ``doc`` without prompting (sets ``Saved=True`` first)."""
        require_com()
        if doc is None:
            return
        try:
            if force_clean:
                try:
                    doc.Saved = True
                except Exception:
                    pass
            doc.Close()
        except Exception as exc:
            raise _format_com_error(exc, "close_document") from exc


    @contextmanager
    def undo_scope(self, name: str) -> Iterator[int]:
        """``BeginUndoScope`` / ``EndUndoScope`` wrapper.

        Commits on clean exit, rolls back on exception.
        """
        require_com()
        if self.app is None:
            raise VisioCOMError("undo_scope: app not initialised")
        try:
            scope_id = int(self.app.BeginUndoScope(name))
        except Exception as exc:
            raise _format_com_error(exc, f"BeginUndoScope({name!r})") from exc
        commit = True
        try:
            yield scope_id
        except BaseException:
            commit = False
            raise
        finally:
            try:
                self.app.EndUndoScope(scope_id, commit)
            except Exception as exc:
                LOG.warning("EndUndoScope(%s, %s) failed: %s",
                            scope_id, commit, exc)


    def batch_set_formulas(self, shape: Any, cells: Mapping[str, str],
                           *, flags: int = 0) -> int:
        """Batch-write formulas: one COM round-trip + one undo step.

        Names not in the static SRC table fall back to per-cell
        ``CellsU(name).FormulaU = formula``.
        """
        require_com()
        if shape is None:
            raise VisioCOMError("batch_set_formulas: shape is None")
        if not cells:
            return 0
        srcs: list[VisCellSRC] = []
        formulas: list[str] = []
        for name, formula in cells.items():
            try:
                srcs.append(cell_src(name))
                formulas.append(str(formula))
            except KeyError:
                try:
                    shape.CellsU(name).FormulaU = str(formula)
                except Exception as exc:
                    raise _format_com_error(
                        exc, f"CellsU({name!r}).FormulaU") from exc
        if not srcs:
            return 0
        try:
            return int(shape.SetFormulas(_flatten_srcs(srcs),
                                         list(formulas), flags))
        except Exception as exc:
            raise _format_com_error(
                exc, f"SetFormulas(n={len(formulas)})") from exc

    def batch_set_results(self, shape: Any,
                          cells: Mapping[str, Tuple[float, str]],
                          *, flags: int = 0) -> int:
        """Batch-write evaluated results with units.

        ``cells`` maps universal cell names to ``(value, unit)`` tuples; ``unit``
        is a Visio unit string such as ``"in"`` / ``"mm"`` / ``"deg"``.
        """
        require_com()
        if shape is None:
            raise VisioCOMError("batch_set_results: shape is None")
        if not cells:
            return 0
        srcs: list[VisCellSRC] = []
        units: list[str] = []
        results: list[float] = []
        for name, (value, unit) in cells.items():
            try:
                srcs.append(cell_src(name))
                units.append(str(unit))
                results.append(float(value))
            except KeyError:
                try:
                    shape.CellsU(name).Result[str(unit)] = float(value)
                except Exception as exc:
                    raise _format_com_error(
                        exc, f"CellsU({name!r}).Result[{unit!r}]") from exc
        if not srcs:
            return 0
        try:
            return int(shape.SetResults(_flatten_srcs(srcs),
                                        list(units), list(results), flags))
        except Exception as exc:
            raise _format_com_error(
                exc, f"SetResults(n={len(results)})") from exc


    def ensure_master(self, doc: Any, master_name: str, *,
                      stencil: Optional[Path | str | Any] = None) -> Any:
        """Resolve a master by ``NameU``; opens a stencil if needed.

        ``stencil`` may be ``None`` (look in document stencil), a path to a
        ``.vssx`` file, or an already-open stencil ``Document`` proxy.
        """
        require_com()
        if doc is None:
            raise VisioCOMError("ensure_master: doc is None")
        if not master_name:
            raise VisioCOMError("ensure_master: empty master_name")

        def _lookup(masters: Any) -> Any:
            try:
                return masters.ItemU(master_name)
            except Exception as exc:
                raise KeyError(master_name) from exc

        try:
            return _lookup(doc.Masters)
        except KeyError:
            pass
        if stencil is None:
            raise KeyError(
                f"master {master_name!r} not in document stencil and "
                "no external stencil supplied")
        if isinstance(stencil, (str, Path)):
            stencil_doc = self.open_document(stencil, as_stencil=True)
        else:
            stencil_doc = stencil
        try:
            return _lookup(stencil_doc.Masters)
        except KeyError as exc:
            raise KeyError(
                f"master {master_name!r} not found in stencil "
                f"{getattr(stencil_doc, 'Name', stencil)!r}") from exc

    def drop_master_at(self, page: Any, master: Any,
                       x: float, y: float) -> Any:
        """``page.Drop(master, x, y)`` with friendly errors."""
        require_com()
        if page is None or master is None:
            raise VisioCOMError("drop_master_at: page or master is None")
        try:
            return page.Drop(master, float(x), float(y))
        except Exception as exc:
            raise _format_com_error(
                exc,
                f"Page.Drop({getattr(master, 'NameU', master)!r}, {x}, {y})"
            ) from exc


    def connect_shapes(self, page: Any, from_shape: Any, to_shape: Any, *,
                       connector_master: Optional[Any] = None,
                       direction: int = VisConst.visAutoConnectDirNone) -> Any:
        """Glue ``from_shape`` -> ``to_shape`` via ``AutoConnect``.

        Returns the newly-created connector shape (last 1-D shape on the
        page) or ``None`` if it cannot be resolved.
        """
        require_com()
        if from_shape is None or to_shape is None:
            raise VisioCOMError("connect_shapes: from/to shape is None")
        try:
            from_shape.AutoConnect(to_shape, int(direction), connector_master)
        except Exception as exc:
            raise _format_com_error(exc, "AutoConnect") from exc
        try:
            shapes = page.Shapes
            for i in range(shapes.Count, 0, -1):
                s = shapes.Item(i)
                try:
                    if bool(s.OneD):
                        return s
                except Exception:
                    continue
        except Exception:
            return None
        return None

    def set_shape_text(self, shape: Any, text: str) -> None:
        """Write ``shape.Text``; empty string clears the text run."""
        require_com()
        if shape is None:
            raise VisioCOMError("set_shape_text: shape is None")
        try:
            shape.Text = "" if text is None else str(text)
        except Exception as exc:
            raise _format_com_error(exc, "set_shape_text") from exc


    def get_or_create_layer(self, page: Any, name: str, *,
                            visible: bool = True,
                            printable: bool = True) -> Any:
        """Return the page-layer named ``name``, creating it if absent."""
        require_com()
        if page is None:
            raise VisioCOMError("get_or_create_layer: page is None")
        if not name:
            raise VisioCOMError("get_or_create_layer: empty name")
        try:
            layers = page.Layers
            for i in range(1, layers.Count + 1):
                lyr = layers.Item(i)
                try:
                    if str(lyr.Name) == name or str(lyr.NameU) == name:
                        return lyr
                except Exception:
                    continue
            lyr = layers.Add(name)
            try:
                # CellsC indices: 0=Color, 4=Visible, 5=Print, 6=Active.
                if hasattr(lyr, "CellsC"):
                    lyr.CellsC(4).FormulaU = "1" if visible else "0"
                    lyr.CellsC(5).FormulaU = "1" if printable else "0"
            except Exception:
                LOG.debug("layer flags not applied: %r", name)
            return lyr
        except Exception as exc:
            raise _format_com_error(
                exc, f"get_or_create_layer({name!r})") from exc


    def apply_theme(self, doc: Any, theme_name: str, *,
                    variant_index: Optional[int] = None) -> None:
        """Apply a built-in Visio theme by ``NameU``.

        Silently no-ops on Visio editions without ``Document.Themes``.
        """
        require_com()
        if doc is None:
            raise VisioCOMError("apply_theme: doc is None")
        try:
            themes = doc.Themes
        except Exception:
            LOG.warning("apply_theme: doc.Themes unavailable; skipping")
            return
        if themes is None:
            return
        try:
            theme = themes.ItemU(theme_name)
        except Exception as exc:
            raise _format_com_error(
                exc, f"Themes.ItemU({theme_name!r})") from exc
        try:
            theme.Apply()
        except Exception as exc:
            raise _format_com_error(
                exc, f"Themes.{theme_name!r}.Apply") from exc
        if variant_index is not None:
            try:
                doc.ThemeVariants.Item(int(variant_index) + 1).Apply()
            except Exception as exc:
                LOG.warning("variant %d not applied: %s", variant_index, exc)

    def export_page(self, page: Any, out_path: Path | str) -> Path:
        """``page.Export(out_path)``; format inferred from extension.

        Visio supports ``.png .svg .emf .jpg .gif .bmp .tif .wmf``.  Parent
        directory is created if missing.
        """
        require_com()
        if page is None:
            raise VisioCOMError("export_page: page is None")
        target = Path(out_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            page.Export(str(target))
            return target
        except Exception as exc:
            raise _format_com_error(
                exc, f"Page.Export({target!s})") from exc


def _capability_report() -> dict[str, Any]:
    """Inspect the runtime environment without spawning Visio."""
    report: dict[str, Any] = {
        "os": sys.platform, "python": sys.version.split()[0],
        "com_available": COM_AVAILABLE, "com_import_error": COM_IMPORT_ERROR,
        "makepy_done": _MAKEPY_DONE, "makepy_error": _MAKEPY_ERROR,
        "typelib": {"guid": TYPELIB_GUID,
                    "major": TYPELIB_MAJOR, "minor": TYPELIB_MINOR},
    }
    if COM_AVAILABLE:
        report["pywin32"] = {
            "win32com": getattr(win32, "__file__", "?"),
            "pythoncom": getattr(pythoncom, "__file__", "?"),
        }
    return report


def _cmd_selftest(_args: argparse.Namespace) -> int:
    report = _capability_report()
    report["status"] = "ok" if COM_AVAILABLE else "degraded"
    print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


def _cmd_ping(args: argparse.Namespace) -> int:
    """Spawn an InvisibleApp, query Version, exit cleanly."""
    if not COM_AVAILABLE:
        print(json.dumps({"status": "skipped",
                          "reason": "pywin32 unavailable",
                          "import_error": COM_IMPORT_ERROR}, indent=2))
        return 2
    visible = bool(int(args.visible)) if args.visible is not None else False
    try:
        with VisioCOM(visible=visible) as visio:
            result: dict[str, Any] = {"status": "ok", "visible": visible,
                                      "app": {}}
            for attr in ("Version", "Build", "Language"):
                try:
                    val = getattr(visio.app, attr)
                    result["app"][attr.lower()] = (
                        int(val) if attr == "Language" else str(val))
                except Exception:
                    pass
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return 0
    except VisioCOMError as exc:
        print(json.dumps({"status": "failed", **exc.to_dict()}, indent=2))
        return 1
    except FileNotFoundError as exc:
        print(json.dumps({"status": "failed", "error": "FileNotFoundError",
                          "message": str(exc)}, indent=2))
        return 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="com_helper",
        description="visio-master shared Visio COM helper "
                    "(diagnostic CLI; importable as a module).")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("selftest",
                       help="report capability JSON without launching Visio")
    p.set_defaults(func=_cmd_selftest)
    p = sub.add_parser("ping",
                       help="launch InvisibleApp, print Version, quit")
    p.add_argument("--visible", default="0",
                   help="1 to show the main window (debug only)")
    p.set_defaults(func=_cmd_ping)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
