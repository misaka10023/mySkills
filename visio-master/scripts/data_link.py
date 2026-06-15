"""data_link.py - Visio DataRecordset wiring CLI.

Manages the data-linking layer of a Visio drawing: creates DataRecordsets
against Excel workbooks, CSV files, or SQL Server, refreshes them, and
attaches existing Data Graphics to linked shapes. Every successful
operation is recorded in a JSON manifest at ``<project>/data_link.json``
so the configuration can be inspected, version-controlled, and re-applied.

DataRecordsets are a COM-only feature (research/21 sec. 12); this module
hard-fails with a friendly error when Visio + pywin32 are not available.

Dependencies (declare in your environment, do NOT auto-install):
    - Python 3.10+
    - pywin32 >= 305       (required at runtime; optional at import)
    - vsdx     >= 0.5      (optional; offline manifest checks only)
    - Microsoft Visio Plan 2 / Professional / Pro for Microsoft 365

Usage:
    python data_link.py link-excel <vsdx> --workbook <xlsx> --sheet Sheet1 \\
        --primary-key PartNumber --name inventory
    python data_link.py link-csv   <vsdx> --csv <csv> --primary-key SKU --name stock
    python data_link.py link-sql   <vsdx> --server tcp:db01,1433 --database INV \\
        --query "SELECT * FROM dbo.Inventory" --primary-key PartNumber --name sql_inv
    python data_link.py refresh    <vsdx> [--recordset NAME]
    python data_link.py attach-graphic <vsdx> --recordset inventory \\
        --graphic "Inventory DG"
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

# Optional imports: pywin32 required at runtime, optional at import time so
# `--help` works on non-Windows hosts.
try:
    import pythoncom  # type: ignore[import-not-found]
    import pywintypes  # type: ignore[import-not-found]
    import win32com.client as wc  # type: ignore[import-not-found]

    _PYWIN32_AVAILABLE = True
    _PYWIN32_ERROR: str | None = None
except ImportError as exc:  # pragma: no cover - environment-dependent
    pythoncom = None  # type: ignore[assignment]
    pywintypes = None  # type: ignore[assignment]
    wc = None  # type: ignore[assignment]
    _PYWIN32_AVAILABLE = False
    _PYWIN32_ERROR = str(exc)

try:
    import vsdx  # type: ignore[import-not-found]  # noqa: F401  (offline checks)

    _VSDX_AVAILABLE = True
except ImportError:
    vsdx = None  # type: ignore[assignment]
    _VSDX_AVAILABLE = False


# Visio constants (hard-coded; stable across Visio 2010-2024).
# Source: research/21-data-linking-graphics.md sec. 4.1, 4.4
VIS_TYPELIB_GUID = "{00021A98-0000-0000-C000-000000000046}"

# VisDataRecordsetAddOptions
VIS_DR_NO_EXTERNAL_DATA_UI = 1
VIS_DR_NO_ADV_CONFIG = 2
VIS_DR_DELAY_QUERY = 16
VIS_DR_NO_AUTO_DISPLAY_DATA = 64

# VisRefreshSettings
VIS_REFRESH_ON_FILE_OPEN = 1
VIS_REFRESH_LINKED_SHAPES = 2
VIS_REFRESH_AUTOMATIC = 128

# VisDataRowIDSubset
VIS_ROW_SUBSET_ALL = 0

# Document.OpenEx flags
VIS_OPEN_RW = 0
VIS_OPEN_RO = 2

# Default refresh bitmask written when a recordset is created here.
DEFAULT_REFRESH_SETTINGS = (
    VIS_REFRESH_ON_FILE_OPEN | VIS_REFRESH_LINKED_SHAPES
)


# Manifest dataclasses
@dataclass
class RecordsetEntry:
    """One row in the manifest's ``recordsets`` list."""

    name: str
    kind: str  # "excel" | "csv" | "sql"
    connection: str
    command: str
    primary_key: str | None = None
    refresh_settings: int = DEFAULT_REFRESH_SETTINGS
    refresh_interval_minutes: int = 0
    id: int | None = None
    last_refreshed: str | None = None
    notes: str | None = None


@dataclass
class GraphicEntry:
    """One row in the manifest's ``graphics`` list."""

    recordset: str
    graphic: str
    shapes_updated: int = 0
    applied_at: str | None = None


@dataclass
class Manifest:
    """Top-level manifest persisted to ``data_link.json``."""

    document: str
    updated: str = ""
    recordsets: list[RecordsetEntry] = field(default_factory=list)
    graphics: list[GraphicEntry] = field(default_factory=list)

    def upsert_recordset(self, entry: RecordsetEntry) -> None:
        for i, existing in enumerate(self.recordsets):
            if existing.name == entry.name:
                self.recordsets[i] = entry
                return
        self.recordsets.append(entry)

    def upsert_graphic(self, entry: GraphicEntry) -> None:
        for i, existing in enumerate(self.graphics):
            if (
                existing.recordset == entry.recordset
                and existing.graphic == entry.graphic
            ):
                self.graphics[i] = entry
                return
        self.graphics.append(entry)


# Manifest helpers
def _manifest_path(document: Path) -> Path:
    """Return the manifest path that lives next to the .vsdx file."""

    return document.with_name("data_link.json")


def load_manifest(document: Path) -> Manifest:
    """Load (or create) the manifest associated with ``document``."""

    path = _manifest_path(document)
    if not path.exists():
        return Manifest(document=document.name)

    raw = json.loads(path.read_text(encoding="utf-8"))
    rs = [RecordsetEntry(**r) for r in raw.get("recordsets", [])]
    gr = [GraphicEntry(**g) for g in raw.get("graphics", [])]
    return Manifest(
        document=raw.get("document", document.name),
        updated=raw.get("updated", ""),
        recordsets=rs,
        graphics=gr,
    )


def save_manifest(document: Path, manifest: Manifest) -> Path:
    """Persist ``manifest`` to ``<document>.parent / data_link.json``."""

    manifest.updated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    payload: dict[str, Any] = {
        "document": manifest.document,
        "updated": manifest.updated,
        "recordsets": [asdict(r) for r in manifest.recordsets],
        "graphics": [asdict(g) for g in manifest.graphics],
    }
    path = _manifest_path(document)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return path


# Connection-string builders
def build_excel_connection(workbook: Path, *, has_header: bool = True) -> str:
    """OLEDB string for the ACE provider against a workbook."""

    suffix = workbook.suffix.lower()
    if suffix in {".xlsx", ".xlsm"}:
        ext_props = (
            f'Excel 12.0 {"Macro" if suffix == ".xlsm" else "Xml"};'
            f'HDR={"YES" if has_header else "NO"};IMEX=1'
        )
    elif suffix == ".xls":
        ext_props = f'Excel 8.0;HDR={"YES" if has_header else "NO"}'
    else:
        raise KeyError(f"Unsupported Excel extension: {suffix!r}")

    return (
        "Provider=Microsoft.ACE.OLEDB.16.0;"
        f"Data Source={workbook};"
        f'Extended Properties="{ext_props}"'
    )


def build_csv_connection(csv_path: Path, *, has_header: bool = True) -> str:
    """OLEDB string for the ACE text driver. The folder is the data source."""

    folder = csv_path.parent
    return (
        "Provider=Microsoft.ACE.OLEDB.16.0;"
        f"Data Source={folder};"
        f'Extended Properties="text;HDR={"YES" if has_header else "NO"};FMT=Delimited"'
    )


def build_sql_connection(
    server: str,
    database: str,
    *,
    user: str | None = None,
    password: str | None = None,
    trust_certificate: bool = False,
) -> str:
    """Connection string for the MSOLEDBSQL provider.

    Falls back to Integrated Security when ``user`` is not supplied. Secret
    materials are accepted as parameters but are echoed verbatim into the
    connection string only - we never log them.
    """

    parts = [
        "Provider=MSOLEDBSQL",
        f"Server={server}",
        f"Database={database}",
        "Encrypt=yes",
        f"TrustServerCertificate={'yes' if trust_certificate else 'no'}",
    ]
    if user:
        parts.append(f"User ID={user}")
        if password is not None:
            parts.append(f"Password={password}")
    else:
        parts.append("Integrated Security=SSPI")
    return ";".join(parts) + ";"


# Visio COM bootstrap and helpers
class VisioUnavailable(RuntimeError):
    """Raised when pywin32 / Visio cannot be reached."""


def _require_visio() -> None:
    if not _PYWIN32_AVAILABLE:
        raise VisioUnavailable(
            "pywin32 is not installed. DataRecordsets are a COM-only feature "
            "and require pywin32 plus a local Microsoft Visio installation. "
            f"Import error: {_PYWIN32_ERROR}"
        )


def _format_com_error(exc: "pywintypes.com_error") -> str:  # type: ignore[name-defined]
    """Pull the most useful diagnostic out of a com_error tuple."""

    try:
        hresult, _source, excepinfo, _argerror = exc.args
    except (ValueError, TypeError):
        return str(exc)
    if excepinfo:
        descr = excepinfo[2]
        return f"HRESULT={hresult & 0xFFFFFFFF:#010x} : {descr}"
    return f"HRESULT={hresult & 0xFFFFFFFF:#010x}"


class VisioDocumentSession:
    """Context manager that opens a .vsdx and saves on clean exit."""

    def __init__(self, path: Path, *, read_only: bool = False) -> None:
        self.path = path
        self.read_only = read_only
        self.app: Any = None
        self.doc: Any = None

    def __enter__(self) -> Any:
        _require_visio()
        if not self.path.exists():
            raise FileNotFoundError(f"Drawing not found: {self.path}")

        pythoncom.CoInitialize()
        try:
            wc.gencache.EnsureModule(VIS_TYPELIB_GUID, 0, 4, 12)
        except Exception:
            # makepy may fail on locked-down boxes; late binding still works.
            pass

        self.app = wc.DispatchEx("Visio.InvisibleApp")
        self.app.Visible = False
        self.app.AlertResponse = 7  # default to "No" on any prompt
        try:
            flags = VIS_OPEN_RO if self.read_only else VIS_OPEN_RW
            self.doc = self.app.Documents.OpenEx(str(self.path), flags)
        except pywintypes.com_error as exc:  # type: ignore[union-attr]
            self._teardown()
            raise RuntimeError(
                f"Failed to open {self.path}: {_format_com_error(exc)}"
            ) from exc
        return self.doc

    def __exit__(self, exc_type, exc, tb) -> None:
        try:
            if self.doc is not None and exc is None and not self.read_only:
                try:
                    self.doc.Save()
                except pywintypes.com_error as save_exc:  # type: ignore[union-attr]
                    print(
                        f"warning: Save failed: {_format_com_error(save_exc)}",
                        file=sys.stderr,
                    )
            if self.doc is not None:
                try:
                    self.doc.Close()
                except pywintypes.com_error:  # type: ignore[union-attr]
                    pass
        finally:
            self._teardown()

    def _teardown(self) -> None:
        if self.app is not None:
            try:
                self.app.Quit()
            except Exception:
                pass
            self.app = None
        if pythoncom is not None:
            pythoncom.CoUninitialize()


# Recordset operations
def _add_recordset(doc: Any, entry: RecordsetEntry) -> Any:
    """Create the recordset, set primary key + refresh policy, return COM obj."""

    options = VIS_DR_NO_EXTERNAL_DATA_UI | VIS_DR_NO_AUTO_DISPLAY_DATA
    rs = doc.DataRecordsets.Add(
        entry.connection, entry.command, options, entry.name
    )
    if entry.primary_key:
        rs.SetPrimaryKey(0, entry.primary_key)
    rs.RefreshSettings = entry.refresh_settings
    if entry.refresh_interval_minutes > 0:
        rs.RefreshInterval = entry.refresh_interval_minutes
        rs.RefreshSettings = (
            entry.refresh_settings | VIS_REFRESH_AUTOMATIC
        )
    entry.id = int(rs.ID)
    return rs


def _replace_existing_recordset(doc: Any, name: str) -> None:
    """Drop a same-named recordset to keep the doc idempotent."""

    try:
        rs = doc.DataRecordsets.Item(name)
    except pywintypes.com_error:  # type: ignore[union-attr]
        return
    except Exception:
        return
    try:
        rs.Delete()
    except Exception:
        pass


# Shared link helper - applies a RecordsetEntry to a document.
def _apply_link(document: Path, entry: RecordsetEntry, action: str) -> dict[str, Any]:
    """Open the doc, replace any same-named recordset, refresh, persist."""

    manifest = load_manifest(document)
    with VisioDocumentSession(document) as doc:
        _replace_existing_recordset(doc, entry.name)
        rs = _add_recordset(doc, entry)
        try:
            rs.Refresh()
            entry.last_refreshed = datetime.now(timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
        except pywintypes.com_error as exc:  # type: ignore[union-attr]
            entry.notes = (
                f"{entry.notes or ''}; initial refresh failed: "
                f"{_format_com_error(exc)}"
            )

    manifest.upsert_recordset(entry)
    save_manifest(document, manifest)
    return {"action": action, "recordset": asdict(entry)}


# Subcommand: link-excel
def cmd_link_excel(args: argparse.Namespace) -> dict[str, Any]:
    document = Path(args.document)
    workbook = Path(args.workbook)
    if not workbook.exists():
        raise FileNotFoundError(f"Workbook not found: {workbook}")

    sheet = args.sheet or "Sheet1"
    command = args.query or f"SELECT * FROM [{sheet}$]"
    entry = RecordsetEntry(
        name=args.name,
        kind="excel",
        connection=build_excel_connection(workbook, has_header=not args.no_header),
        command=command,
        primary_key=args.primary_key,
        refresh_interval_minutes=args.refresh_interval,
        refresh_settings=DEFAULT_REFRESH_SETTINGS,
        notes=f"workbook={workbook.name}; sheet={sheet}",
    )
    return _apply_link(document, entry, "link-excel")


# Subcommand: link-csv
def cmd_link_csv(args: argparse.Namespace) -> dict[str, Any]:
    document = Path(args.document)
    csv_path = Path(args.csv)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    command = args.query or f"SELECT * FROM [{csv_path.name}]"
    entry = RecordsetEntry(
        name=args.name,
        kind="csv",
        connection=build_csv_connection(csv_path, has_header=not args.no_header),
        command=command,
        primary_key=args.primary_key,
        refresh_interval_minutes=args.refresh_interval,
        refresh_settings=DEFAULT_REFRESH_SETTINGS,
        notes=f"csv={csv_path.name}",
    )
    return _apply_link(document, entry, "link-csv")


# Subcommand: link-sql
def cmd_link_sql(args: argparse.Namespace) -> dict[str, Any]:
    document = Path(args.document)
    if not args.query:
        raise KeyError("--query is required for link-sql")

    entry = RecordsetEntry(
        name=args.name,
        kind="sql",
        connection=build_sql_connection(
            server=args.server,
            database=args.database,
            user=args.user,
            password=args.password,
            trust_certificate=args.trust_certificate,
        ),
        command=args.query,
        primary_key=args.primary_key,
        refresh_interval_minutes=args.refresh_interval,
        refresh_settings=DEFAULT_REFRESH_SETTINGS,
        notes=f"server={args.server}; database={args.database}",
    )
    result = _apply_link(document, entry, "link-sql")

    # Sanitise the manifest entry so passwords do not bleed into Git.
    if args.password:
        manifest = load_manifest(document)
        for stored in manifest.recordsets:
            if stored.name == entry.name:
                stored.connection = stored.connection.replace(
                    f"Password={args.password}", "Password=***REDACTED***"
                )
        save_manifest(document, manifest)
        result["recordset"]["connection"] = result["recordset"]["connection"].replace(
            f"Password={args.password}", "Password=***REDACTED***"
        )
    return result


# Subcommand: refresh
def _iter_recordsets(doc: Any) -> Iterable[Any]:
    count = int(doc.DataRecordsets.Count)
    for i in range(1, count + 1):
        yield doc.DataRecordsets.Item(i)


def cmd_refresh(args: argparse.Namespace) -> dict[str, Any]:
    document = Path(args.document)
    manifest = load_manifest(document)
    refreshed: list[dict[str, Any]] = []

    with VisioDocumentSession(document) as doc:
        for rs in _iter_recordsets(doc):
            name = str(rs.Name)
            if args.recordset and args.recordset != name:
                continue
            try:
                rs.Refresh()
                ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                refreshed.append({"name": name, "status": "ok", "at": ts})
                for entry in manifest.recordsets:
                    if entry.name == name:
                        entry.last_refreshed = ts
                        entry.id = int(rs.ID)
            except pywintypes.com_error as exc:  # type: ignore[union-attr]
                refreshed.append(
                    {
                        "name": name,
                        "status": "error",
                        "detail": _format_com_error(exc),
                    }
                )

    save_manifest(document, manifest)
    return {"action": "refresh", "recordsets": refreshed}


# Subcommand: attach-graphic
def _find_recordset_id(doc: Any, name: str) -> int:
    try:
        rs = doc.DataRecordsets.Item(name)
    except pywintypes.com_error as exc:  # type: ignore[union-attr]
        raise KeyError(
            f"Recordset {name!r} not found in document: "
            f"{_format_com_error(exc)}"
        ) from exc
    return int(rs.ID)


def _find_data_graphic(doc: Any, name: str) -> Any:
    try:
        return doc.DataGraphics.ItemU(name)
    except pywintypes.com_error as exc:  # type: ignore[union-attr]
        raise KeyError(
            f"Data Graphic {name!r} not found in document: "
            f"{_format_com_error(exc)}"
        ) from exc


def cmd_attach_graphic(args: argparse.Namespace) -> dict[str, Any]:
    document = Path(args.document)
    manifest = load_manifest(document)
    updated_count = 0

    with VisioDocumentSession(document) as doc:
        rs_id = _find_recordset_id(doc, args.recordset)
        dg = _find_data_graphic(doc, args.graphic)

        page_count = int(doc.Pages.Count)
        for page_index in range(1, page_count + 1):
            page = doc.Pages.Item(page_index)
            shape_count = int(page.Shapes.Count)
            for shape_index in range(1, shape_count + 1):
                shape = page.Shapes.Item(shape_index)
                try:
                    linked_id = int(shape.LinkedDataRecordsetID)
                except pywintypes.com_error:  # type: ignore[union-attr]
                    continue
                if linked_id != rs_id:
                    continue
                try:
                    shape.DataGraphic = dg
                    updated_count += 1
                except pywintypes.com_error as exc:  # type: ignore[union-attr]
                    print(
                        f"warning: failed to set DG on shape "
                        f"{shape.Name!r}: {_format_com_error(exc)}",
                        file=sys.stderr,
                    )

    entry = GraphicEntry(
        recordset=args.recordset,
        graphic=args.graphic,
        shapes_updated=updated_count,
        applied_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
    manifest.upsert_graphic(entry)
    save_manifest(document, manifest)
    return {"action": "attach-graphic", "graphic": asdict(entry)}


# CLI plumbing
def _add_common_link_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("document", help="Path to the .vsdx drawing")
    p.add_argument("--name", required=True, help="Recordset name (manifest key)")
    p.add_argument(
        "--primary-key",
        help="Column name to mark as primary key (required for refresh)",
    )
    p.add_argument(
        "--refresh-interval",
        type=int,
        default=0,
        help="Schedule refresh every N minutes (0 = on demand only)",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="data_link.py",
        description=(
            "Manage Visio DataRecordsets and Data Graphics. Stores a JSON "
            "manifest at <document>.parent/data_link.json."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_excel = sub.add_parser("link-excel", help="Link an Excel workbook")
    _add_common_link_args(p_excel)
    p_excel.add_argument("--workbook", required=True, help="Path to .xlsx/.xlsm/.xls")
    p_excel.add_argument("--sheet", default="Sheet1", help="Sheet name (no $)")
    p_excel.add_argument("--query", help="Override the SELECT statement")
    p_excel.add_argument("--no-header", action="store_true", help="HDR=NO")
    p_excel.set_defaults(func=cmd_link_excel)

    p_csv = sub.add_parser("link-csv", help="Link a CSV file")
    _add_common_link_args(p_csv)
    p_csv.add_argument("--csv", required=True, help="Path to .csv")
    p_csv.add_argument("--query", help="Override the SELECT statement")
    p_csv.add_argument("--no-header", action="store_true", help="HDR=NO")
    p_csv.set_defaults(func=cmd_link_csv)

    p_sql = sub.add_parser("link-sql", help="Link a SQL Server query")
    _add_common_link_args(p_sql)
    p_sql.add_argument("--server", required=True, help="e.g. tcp:HOST,1433")
    p_sql.add_argument("--database", required=True, help="Database name")
    p_sql.add_argument("--query", required=True, help="SELECT or EXEC ...")
    p_sql.add_argument("--user", help="SQL login (omit for Integrated auth)")
    p_sql.add_argument("--password", help="SQL password")
    p_sql.add_argument(
        "--trust-certificate",
        action="store_true",
        help="Set TrustServerCertificate=yes (only for dev/test)",
    )
    p_sql.set_defaults(func=cmd_link_sql)

    p_refresh = sub.add_parser("refresh", help="Refresh DataRecordsets")
    p_refresh.add_argument("document", help="Path to the .vsdx drawing")
    p_refresh.add_argument(
        "--recordset",
        help="Refresh only this recordset (default: all)",
    )
    p_refresh.set_defaults(func=cmd_refresh)

    p_dg = sub.add_parser(
        "attach-graphic",
        help="Apply an existing Data Graphic master to linked shapes",
    )
    p_dg.add_argument("document", help="Path to the .vsdx drawing")
    p_dg.add_argument(
        "--recordset", required=True, help="Recordset name driving the bind"
    )
    p_dg.add_argument(
        "--graphic",
        required=True,
        help="Universal name of the Data Graphic master in the doc",
    )
    p_dg.set_defaults(func=cmd_attach_graphic)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    # Build the COM-error type tuple lazily so that the import-time absence of
    # pywin32 does not crash this module on non-Windows hosts.
    com_error_types: tuple[type[BaseException], ...]
    if _PYWIN32_AVAILABLE:
        com_error_types = (pywintypes.com_error,)  # type: ignore[union-attr]
    else:
        com_error_types = ()

    try:
        result = args.func(args)
    except VisioUnavailable as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except KeyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except com_error_types as exc:  # type: ignore[misc]
        print(
            f"error: Visio COM call failed: {_format_com_error(exc)}",
            file=sys.stderr,
        )
        return 3

    print(json.dumps({"status": "ok", **result}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
