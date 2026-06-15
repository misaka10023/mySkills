#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stencil index builder, query, and apply tool for the visio-master skill.

Subcommands:
  scan  <stencil_dir>          recursively index .vssx/.vssm/.vss files
  query <keyword>              search the cached index (AND on whitespace)
  apply <project> <id> [<id>]  copy stencils into <project>/templates/

JSON shape: ``{ "stencils": [ { "id", "path", "sha1", "size", "mtime",
"format", "masters": [ { "name", "name_u", "base_id", "unique_id",
"prompt", "icon_size", "align_name", "pattern_flags", "keywords",
"preview_xml" } ] } ] }``

Optional deps (NOT auto-installed):
  * vsdx     - richer master enumeration; falls back to zipfile + ElementTree.
  * pywin32  - opt-in legacy .vss support via ``--use-com`` + Visio COM.

Usage::
    python stencil_index.py scan "C:/.../Visio Content/1033"
    python stencil_index.py query decision --limit 10
    python stencil_index.py apply "D:/work/my-visio-project" basflo_u crossf_u
"""
from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import logging
import re
import shutil
import sys
import time
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence

# --- Optional imports — never let the script die if these are missing -----
try:  # pragma: no cover
    import vsdx as _vsdx  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover
    _vsdx = None
try:  # pragma: no cover
    import pythoncom  # type: ignore[import-not-found]
    import win32com.client as _win32com  # type: ignore[import-not-found]
    from pywintypes import com_error as _com_error  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover
    pythoncom = None
    _win32com = None

    class _com_error(Exception):  # type: ignore[no-redef]
        """Stand-in so ``except`` clauses are valid without pywin32."""


SUPPORTED_SUFFIXES: tuple[str, ...] = (".vssx", ".vssm", ".vss")
DEFAULT_INDEX_PATH: Path = Path("stencil_index.json")
VISIO_NS: str = "http://schemas.microsoft.com/office/visio/2012/main"
RELS_NS: str = "http://schemas.openxmlformats.org/package/2006/relationships"

logger = logging.getLogger("stencil_index")


# --- Data model ------------------------------------------------------------
@dataclasses.dataclass(slots=True)
class MasterRecord:
    """One ``Master`` shape extracted from a stencil."""

    name: str
    name_u: str
    base_id: str = ""
    unique_id: str = ""
    prompt: str = ""
    icon_size: int = 0
    align_name: int = 0
    pattern_flags: int = 0
    keywords: list[str] = dataclasses.field(default_factory=list)
    preview_xml: str = ""

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(slots=True)
class StencilRecord:
    """One stencil file in the catalogue."""

    id: str
    path: str
    sha1: str
    size: int
    mtime: float
    format: str
    masters: list[MasterRecord] = dataclasses.field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "path": self.path, "sha1": self.sha1,
            "size": self.size, "mtime": self.mtime, "format": self.format,
            "masters": [m.to_dict() for m in self.masters],
        }


# --- Index I/O -------------------------------------------------------------
def load_index(index_path: Path) -> dict[str, Any]:
    """Read a previously written index file. Empty skeleton if absent/bad."""
    try:
        with index_path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        return {"stencils": []}
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Could not parse %s: %s - starting fresh", index_path, exc)
        return {"stencils": []}
    if not isinstance(data, dict) or "stencils" not in data:
        logger.warning("Index at %s missing 'stencils' - starting fresh", index_path)
        return {"stencils": []}
    return data


def save_index(index_path: Path, payload: dict[str, Any]) -> None:
    """Persist the catalogue as pretty-printed UTF-8 JSON (atomic write)."""
    index_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = index_path.with_suffix(index_path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
    tmp.replace(index_path)


# --- Helpers ---------------------------------------------------------------
_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(value: str) -> str:
    """Lowercase + collapse non-alphanumerics to ``_``."""
    return _SLUG_RE.sub("_", value.lower()).strip("_")


def make_stencil_id(path: Path, sha1: str) -> str:
    """Stable, human-friendly stencil id."""
    return f"{slugify(path.stem) or 'stencil'}_{sha1[:8]}"


def sha1_of(path: Path, chunk: int = 65536) -> str:
    """SHA-1 of file contents (cheap dedup signal, not for security)."""
    hasher = hashlib.sha1()  # noqa: S324
    with path.open("rb") as fh:
        for buf in iter(lambda: fh.read(chunk), b""):
            hasher.update(buf)
    return hasher.hexdigest()


def split_terms(query: str) -> list[str]:
    """Split a free-form query into lowercase AND-terms."""
    return [t for t in re.split(r"\s+", query.strip().lower()) if t]


def derive_keywords(master: MasterRecord) -> list[str]:
    """Best-effort keyword harvest from name/name_u/prompt."""
    seen: set[str] = set()
    out: list[str] = []
    for source in (master.name, master.name_u, master.prompt):
        if not source:
            continue
        for tok in re.split(r"[\s,;/\\\-_]+", source):
            token = tok.strip().lower()
            if len(token) >= 2 and token not in seen:
                seen.add(token)
                out.append(token)
    return out


def iter_stencil_files(root: Path) -> Iterator[Path]:
    """Yield every supported stencil under ``root`` (recursive)."""
    if not root.exists():
        raise FileNotFoundError(f"Stencil root does not exist: {root}")
    if root.is_file():
        if root.suffix.lower() in SUPPORTED_SUFFIXES:
            yield root
        return
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES:
            yield path


# --- vssx / vssm parsing (no third-party deps required) -------------------
def _ns(tag: str) -> str:
    return f"{{{VISIO_NS}}}{tag}"


def _rels_ns(tag: str) -> str:
    return f"{{{RELS_NS}}}{tag}"


_RELS_ID_ATTRS = (
    f"{{{RELS_NS}}}id",
    "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id",
)


def parse_vssx_zip(path: Path) -> list[MasterRecord]:
    """Parse a ZIP-packaged stencil (``.vssx`` / ``.vssm``)."""
    masters: list[MasterRecord] = []
    try:
        with zipfile.ZipFile(path, "r") as zf:
            try:
                masters_xml = zf.read("visio/masters/masters.xml").decode("utf-8")
            except KeyError:
                logger.warning("%s missing visio/masters/masters.xml", path.name)
                return masters
            try:
                rels_xml = zf.read(
                    "visio/masters/_rels/masters.xml.rels"
                ).decode("utf-8")
            except KeyError:
                rels_xml = ""

            rel_targets = _parse_master_rels(rels_xml)
            for el in ET.fromstring(masters_xml).findall(_ns("Master")):
                rec = _master_from_element(el)
                rel_el = el.find(_ns("Rel"))
                rel_id = ""
                if rel_el is not None:
                    for attr in _RELS_ID_ATTRS:
                        rel_id = rel_el.attrib.get(attr, "")
                        if rel_id:
                            break
                target = rel_targets.get(rel_id, "")
                if target:
                    member = _resolve_member(target)
                    try:
                        rec.preview_xml = zf.read(member).decode("utf-8")
                    except KeyError:
                        logger.debug("%s missing payload %s", path.name, member)
                rec.keywords = derive_keywords(rec)
                masters.append(rec)
    except zipfile.BadZipFile as exc:
        logger.warning("%s is not a valid ZIP: %s", path, exc)
    except ET.ParseError as exc:
        logger.warning("%s: XML parse error: %s", path, exc)
    return masters


def _parse_master_rels(rels_xml: str) -> dict[str, str]:
    """Map ``Id`` -> ``Target`` for ``masters.xml.rels``."""
    if not rels_xml.strip():
        return {}
    try:
        root = ET.fromstring(rels_xml)
    except ET.ParseError:
        return {}
    return {
        rel.attrib["Id"]: rel.attrib["Target"]
        for rel in root.findall(_rels_ns("Relationship"))
        if rel.attrib.get("Id") and rel.attrib.get("Target")
    }


def _resolve_member(target: str) -> str:
    """Resolve an OPC ``Target`` (relative to ``visio/masters/``)."""
    return target.lstrip("/") if target.startswith("/") else f"visio/masters/{target}"


def _master_from_element(el: ET.Element) -> MasterRecord:
    """Build a ``MasterRecord`` from a ``<Master>`` element."""
    g = el.attrib.get
    return MasterRecord(
        name=g("Name", "").strip(),
        name_u=g("NameU", "").strip(),
        base_id=g("BaseID", "").strip(),
        unique_id=g("UniqueID", "").strip(),
        prompt=g("Prompt", "").strip(),
        icon_size=_safe_int(g("IconSize", "0")),
        align_name=_safe_int(g("AlignName", "0")),
        pattern_flags=_safe_int(g("PatternFlags", "0")),
    )


def _safe_int(raw: str) -> int:
    try:
        return int(raw)
    except (TypeError, ValueError):
        return 0


# --- Optional vsdx-backed parsing (richer fidelity if available) ----------
def parse_via_vsdx(path: Path) -> list[MasterRecord] | None:
    """Use the ``vsdx`` package if importable. ``None`` on failure."""
    if _vsdx is None:
        return None
    try:
        with _vsdx.VisioFile(str(path)) as doc:  # type: ignore[attr-defined]
            collected: list[MasterRecord] = []
            for m in getattr(doc, "masters", []) or []:
                rec = MasterRecord(
                    name=getattr(m, "name", "") or "",
                    name_u=getattr(m, "name_u", "")
                    or getattr(m, "unique_name", "")
                    or "",
                    base_id=getattr(m, "base_id", "") or "",
                    unique_id=getattr(m, "unique_id", "") or "",
                    prompt=getattr(m, "prompt", "") or "",
                )
                xml_el = getattr(m, "xml", None)
                if xml_el is not None:
                    try:
                        rec.preview_xml = ET.tostring(xml_el, encoding="unicode")
                    except (TypeError, ET.ParseError):
                        rec.preview_xml = str(xml_el)
                rec.keywords = derive_keywords(rec)
                collected.append(rec)
            return collected
    except (FileNotFoundError, KeyError, AttributeError, OSError) as exc:
        logger.debug("vsdx parse fell back for %s: %s", path, exc)
        return None


# --- Legacy .vss support via Visio COM (opt-in; rare path) ----------------
def parse_via_com(path: Path) -> list[MasterRecord]:
    """Fallback that opens a stencil via Visio COM. Requires pywin32."""
    if _win32com is None or pythoncom is None:
        logger.info("pywin32 unavailable - skipping COM parse for %s", path)
        return []
    pythoncom.CoInitialize()
    app = doc = None
    try:
        app = _win32com.DispatchEx("Visio.InvisibleApp")
        doc = app.Documents.OpenEx(str(path), 2 + 64)  # visOpenRO|visOpenHidden
        collected: list[MasterRecord] = []
        for m in doc.Masters:
            rec = MasterRecord(
                name=str(m.Name or ""),
                name_u=str(m.NameU or ""),
                base_id=str(m.BaseID or ""),
                unique_id=str(m.UniqueID or ""),
                prompt=str(getattr(m, "Prompt", "") or ""),
                icon_size=int(getattr(m, "IconSize", 0) or 0),
                align_name=int(getattr(m, "AlignName", 0) or 0),
                pattern_flags=int(getattr(m, "PatternFlags", 0) or 0),
            )
            rec.keywords = derive_keywords(rec)
            collected.append(rec)
        return collected
    except _com_error as exc:
        logger.warning("COM error on %s: %s", path, exc)
        return []
    finally:
        for obj, action in ((doc, "Close"), (app, "Quit")):
            if obj is None:
                continue
            try:
                getattr(obj, action)()
            except _com_error:
                pass
        try:
            pythoncom.CoUninitialize()
        except Exception:  # pragma: no cover
            pass


# --- Stencil parsing entry point ------------------------------------------
def parse_stencil(path: Path, *, use_com: bool = False) -> list[MasterRecord]:
    """Pick the best available parser for ``path``."""
    suffix = path.suffix.lower()
    if suffix in (".vssx", ".vssm"):
        masters = parse_via_vsdx(path)
        if masters:
            return masters
        return parse_vssx_zip(path)
    if suffix == ".vss":
        if use_com:
            return parse_via_com(path)
        logger.info(
            "%s is a legacy binary stencil; rerun with --use-com to read it",
            path.name,
        )
        return []
    return []


# --- Output helper --------------------------------------------------------
def _emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


# --- Subcommand: scan -----------------------------------------------------
def cmd_scan(args: argparse.Namespace) -> int:
    root = Path(args.stencil_dir).expanduser().resolve()
    index_path = Path(args.index).expanduser().resolve()
    started = time.perf_counter()

    try:
        files = list(iter_stencil_files(root))
    except FileNotFoundError as exc:
        _emit({"status": "error", "error": str(exc)})
        return 2

    stencils: list[StencilRecord] = []
    for path in files:
        try:
            digest = sha1_of(path)
            stat = path.stat()
            masters = parse_stencil(path, use_com=args.use_com)
        except (FileNotFoundError, PermissionError, OSError) as exc:
            logger.warning("skip %s: %s", path, exc)
            continue
        except _com_error as exc:  # type: ignore[misc]
            logger.warning("COM error on %s: %s", path, exc)
            continue
        stencils.append(StencilRecord(
            id=make_stencil_id(path, digest), path=str(path), sha1=digest,
            size=stat.st_size, mtime=stat.st_mtime,
            format=path.suffix.lower().lstrip("."), masters=masters,
        ))

    save_index(index_path, {
        "schema": 1, "generated_at": time.time(), "root": str(root),
        "stencils": [s.to_dict() for s in stencils],
    })
    _emit({
        "status": "ok", "index": str(index_path),
        "stencil_count": len(stencils),
        "master_count": sum(len(s.masters) for s in stencils),
        "elapsed_s": round(time.perf_counter() - started, 3),
    })
    return 0


# --- Subcommand: query ----------------------------------------------------
def _master_matches(master: dict[str, Any], terms: Sequence[str]) -> bool:
    haystack = " ".join([
        str(master.get("name", "")), str(master.get("name_u", "")),
        str(master.get("prompt", "")),
        " ".join(master.get("keywords", []) or []),
    ]).lower()
    return all(term in haystack for term in terms)


def cmd_query(args: argparse.Namespace) -> int:
    data = load_index(Path(args.index).expanduser().resolve())
    terms = split_terms(args.keyword)
    if not terms:
        _emit({"status": "error", "error": "empty keyword"})
        return 2

    hits: list[dict[str, Any]] = []
    remaining = max(int(args.limit), 0) if args.limit else 0
    for stencil in data.get("stencils", []):
        matched = [m for m in stencil.get("masters", []) if _master_matches(m, terms)]
        if not matched:
            continue
        if remaining:
            matched = matched[:remaining]
        hits.append({
            "id": stencil.get("id"), "path": stencil.get("path"),
            "format": stencil.get("format"),
            "matches": [{
                "name": m.get("name"), "name_u": m.get("name_u"),
                "base_id": m.get("base_id"), "prompt": m.get("prompt"),
                "keywords": m.get("keywords", []),
            } for m in matched],
        })
        if remaining:
            remaining -= len(matched)
            if remaining <= 0:
                break

    _emit({
        "status": "ok", "query": args.keyword, "terms": terms,
        "stencil_hits": len(hits),
        "match_count": sum(len(h["matches"]) for h in hits),
        "results": hits,
    })
    return 0


# --- Subcommand: apply ----------------------------------------------------
def _resolve_stencil(data: dict[str, Any], stencil_id: str) -> dict[str, Any] | None:
    needle = stencil_id.lower()
    stencils = data.get("stencils", [])
    for stencil in stencils:
        if str(stencil.get("id", "")).lower() == needle:
            return stencil
    for stencil in stencils:  # tolerate slug-only matches (no sha1 suffix)
        if str(stencil.get("id", "")).lower().startswith(f"{needle}_"):
            return stencil
    return None


def cmd_apply(args: argparse.Namespace) -> int:
    project = Path(args.project_path).expanduser().resolve()
    target_dir = project / "templates"
    if not project.exists():
        _emit({"status": "error", "error": f"project_path missing: {project}"})
        return 2

    data = load_index(Path(args.index).expanduser().resolve())
    target_dir.mkdir(parents=True, exist_ok=True)

    applied: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    missing: list[str] = []

    for sid in args.stencil_ids:
        stencil = _resolve_stencil(data, sid)
        if not stencil:
            missing.append(sid)
            continue
        src = Path(stencil["path"])
        if not src.exists():
            skipped.append({"id": stencil["id"], "reason": "source missing"})
            continue
        dst = target_dir / src.name
        if dst.exists() and not args.force:
            skipped.append({"id": stencil["id"], "reason": "destination exists"})
            continue
        try:
            shutil.copy2(src, dst)
        except (FileNotFoundError, PermissionError, OSError) as exc:
            skipped.append({"id": stencil["id"], "reason": f"copy failed: {exc}"})
            continue
        applied.append({"id": stencil["id"], "src": str(src), "dst": str(dst)})

    _emit({
        "status": "ok" if not missing else "partial",
        "project": str(project),
        "applied": applied, "skipped": skipped, "missing_ids": missing,
    })
    return 0 if not missing else 1


# --- CLI ------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="stencil_index.py",
        description="Build, query, and apply a JSON catalogue of Visio stencils.",
    )
    parser.add_argument("-v", "--verbose", action="count", default=0,
                        help="-v info, -vv debug")
    sub = parser.add_subparsers(dest="command", required=True)
    idx_help = f"JSON catalogue path (default: {DEFAULT_INDEX_PATH})"

    p_scan = sub.add_parser("scan", help="recursively index stencils")
    p_scan.add_argument("stencil_dir", help="directory containing .vssx files")
    p_scan.add_argument("--index", default=str(DEFAULT_INDEX_PATH), help=idx_help)
    p_scan.add_argument("--use-com", action="store_true",
                        help="open legacy .vss via Visio COM (needs pywin32)")
    p_scan.set_defaults(func=cmd_scan)

    p_query = sub.add_parser("query", help="search the cached index")
    p_query.add_argument("keyword", help="space-separated AND terms")
    p_query.add_argument("--index", default=str(DEFAULT_INDEX_PATH), help=idx_help)
    p_query.add_argument("--limit", type=int, default=0,
                         help="cap total master matches (0 = unlimited)")
    p_query.set_defaults(func=cmd_query)

    p_apply = sub.add_parser("apply",
                             help="copy stencils into <project>/templates/")
    p_apply.add_argument("project_path", help="target Visio project root")
    p_apply.add_argument("stencil_ids", nargs="+", help="ids from the catalogue")
    p_apply.add_argument("--index", default=str(DEFAULT_INDEX_PATH), help=idx_help)
    p_apply.add_argument("--force", action="store_true",
                         help="overwrite existing files")
    p_apply.set_defaults(func=cmd_apply)
    return parser


def configure_logging(verbosity: int) -> None:
    level = logging.WARNING if verbosity < 1 else (
        logging.INFO if verbosity == 1 else logging.DEBUG
    )
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    configure_logging(getattr(args, "verbose", 0))
    try:
        return int(args.func(args))
    except KeyboardInterrupt:  # pragma: no cover
        _emit({"status": "error", "error": "interrupted"})
        return 130
    except _com_error as exc:  # type: ignore[misc]
        _emit({"status": "error", "error": f"COM error: {exc}"})
        return 3
    except FileNotFoundError as exc:
        _emit({"status": "error", "error": str(exc)})
        return 2
    except KeyError as exc:
        _emit({"status": "error", "error": f"missing key: {exc}"})
        return 2


if __name__ == "__main__":
    sys.exit(main())
