#!/usr/bin/env python3
"""vsdx_build.py — cross-platform .vsdx build helper.

Primary path uses the ``vsdx`` Python package when importable; falls back to
raw OPC + ``lxml`` operating directly on the ZIP container and per-page XML.

Cross-platform constraint: this module does *not* drive the Visio engine.
Theme application, auto-layout (``Page.Layout``), ShapeSheet recompute, and
connector auto-routing are out of scope — those need Microsoft Visio (COM,
Windows-only, see ``vsdx_export.py``) or a manual round-trip through Visio.
The functions here mutate persisted state; Visio re-runs engine logic on
next open.

Public API: ``open_template``, ``copy_page``, ``set_text_by_id``,
``drop_master_xml``, ``connect_xml``, ``save``.

CLI::

    python vsdx_build.py inspect     <template.vsdx>
    python vsdx_build.py copy-page   <template.vsdx> <out.vsdx> --src 0 --name Copy
    python vsdx_build.py set-text    <template.vsdx> <out.vsdx> --page 0 --shape-id 5 --text "Hi"
    python vsdx_build.py drop-master <template.vsdx> <out.vsdx> --page 0 --xml shape.xml --x 2.5 --y 4.0
    python vsdx_build.py connect     <template.vsdx> <out.vsdx> --page 0 --from 5 --to 9 --kind dynamic

Each successful invocation prints a one-line JSON summary on stdout.

Dependencies (declare in ``requirements.txt``; do NOT pip install here):
Python 3.10+, ``lxml`` (required), ``vsdx`` (optional). ``pywin32`` is not
needed by this module.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
import zipfile
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator, Optional, Union

# Optional imports: both vsdx and lxml may be missing on a thin install.

try:
    import vsdx as _vsdx  # type: ignore[import-not-found]
    _VSDX_AVAILABLE = True
except Exception:  # noqa: BLE001
    _vsdx = None
    _VSDX_AVAILABLE = False

try:
    from lxml import etree as _etree  # type: ignore[import-not-found]
    _LXML_AVAILABLE = True
except Exception:  # noqa: BLE001
    _etree = None
    _LXML_AVAILABLE = False

# Visio / OPC namespaces and constants.
NS_V = "http://schemas.microsoft.com/office/visio/2012/main"
NS_R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_PR = "http://schemas.openxmlformats.org/package/2006/relationships"
NS_CT = "http://schemas.openxmlformats.org/package/2006/content-types"
REL_TYPE_PAGE = "http://schemas.microsoft.com/visio/2010/relationships/page"
CT_PAGE = "application/vnd.ms-visio.page+xml"
# Connect FromPart codes (vsdx-format-quick-ref §2.10).
PART_WHOLE_SHAPE, PART_BEGIN, PART_END = 3, 9, 12
CONN_KINDS = {"begin-end", "dynamic", "static"}


class VsdxBuildError(RuntimeError):
    """Raised for build-helper-specific failures (missing deps, bad input)."""


def _require_lxml() -> None:
    if not _LXML_AVAILABLE:
        raise VsdxBuildError(
            "lxml is required; install it via the project's requirements.txt."
        )


# Shape XML emission (shared by both backends).

def _build_cell(name: str, value: Optional[str] = None,
                formula: Optional[str] = None,
                unit: Optional[str] = None) -> Any:
    _require_lxml()
    cell = _etree.Element(f"{{{NS_V}}}Cell")
    cell.set("N", name)
    if value is not None:
        cell.set("V", value)
    if formula is not None:
        cell.set("F", formula)
    if unit is not None:
        cell.set("U", unit)
    return cell


def _next_shape_id(shapes_el: Any) -> int:
    """Allocate a new page-local ``Shape/@ID`` (max existing + 1, default 1)."""
    _require_lxml()
    ids = [int(s.get("ID")) for s in shapes_el.findall(f"{{{NS_V}}}Shape")
           if s.get("ID") and s.get("ID").isdigit()]
    return (max(ids) + 1) if ids else 1


def _wrap_master_drop(master_xml: str, new_id: int, x: float, y: float) -> Any:
    """Parse a master-derived ``<Shape>`` fragment and re-stamp PinX/PinY/ID."""
    _require_lxml()
    fragment = master_xml.strip()
    if not fragment.startswith("<"):
        raise VsdxBuildError("master_xml does not look like an XML fragment")
    if "xmlns" not in fragment.split(">", 1)[0]:
        fragment = fragment.replace("<Shape", f'<Shape xmlns="{NS_V}"', 1)
    try:
        shape = _etree.fromstring(fragment.encode("utf-8"))
    except _etree.XMLSyntaxError as exc:
        raise VsdxBuildError(f"master_xml is not well-formed: {exc}") from exc

    shape.set("ID", str(new_id))
    # Drop any pre-existing PinX/PinY cells, then prepend fresh ones.
    for cell in list(shape):
        if cell.tag == f"{{{NS_V}}}Cell" and cell.get("N") in {"PinX", "PinY"}:
            shape.remove(cell)
    shape.insert(0, _build_cell("PinY", value=str(y)))
    shape.insert(0, _build_cell("PinX", value=str(x)))
    return shape


def _build_connect(from_id: int, to_id: int,
                   conn_kind: str) -> tuple[Any, Any]:
    """Return (begin_connect, end_connect) for the canonical glue pattern."""
    _require_lxml()
    if conn_kind not in CONN_KINDS:
        raise VsdxBuildError(
            f"unknown conn_kind {conn_kind!r}; expected one of "
            f"{sorted(CONN_KINDS)}"
        )

    if conn_kind in ("begin-end", "dynamic"):
        to_cell, to_part = "PinX", PART_WHOLE_SHAPE
    else:  # static — assume Connection.X1 on the target
        to_cell, to_part = "Connections.X1", 100 + 1

    def _row(from_cell: str, from_part: int) -> Any:
        el = _etree.Element(f"{{{NS_V}}}Connect")
        el.set("FromSheet", str(from_id))
        el.set("FromCell", from_cell)
        el.set("FromPart", str(from_part))
        el.set("ToSheet", str(to_id))
        el.set("ToCell", to_cell)
        el.set("ToPart", str(to_part))
        return el

    return _row("BeginX", PART_BEGIN), _row("EndX", PART_END)


# OPC fallback wrappers

@dataclass
class _OpcPage:
    document: "_OpcDocument"
    part_name: str
    page_id: int
    name: str
    rel_id: str
    tree: Any

    @property
    def root(self) -> Any:
        return self.tree.getroot()

    @property
    def shapes_el(self) -> Any:
        ns = f"{{{NS_V}}}"
        el = self.root.find(f"{ns}Shapes")
        return el if el is not None else _etree.SubElement(self.root, f"{ns}Shapes")

    @property
    def connects_el(self) -> Any:
        ns = f"{{{NS_V}}}"
        el = self.root.find(f"{ns}Connects")
        return el if el is not None else _etree.SubElement(self.root, f"{ns}Connects")


@dataclass
class _OpcDocument:
    source_path: Path
    work_dir: Path
    pages_xml_tree: Any
    pages_rels_tree: Any
    content_types_tree: Any
    pages: list[_OpcPage] = field(default_factory=list)
    backend: str = "opc"

    def page_by_index(self, index: int) -> _OpcPage:
        try:
            return self.pages[index]
        except IndexError as exc:
            raise KeyError(
                f"page index {index} out of range (have {len(self.pages)})"
            ) from exc


def _parse_xml(path: Path) -> Any:
    _require_lxml()
    parser = _etree.XMLParser(remove_blank_text=False, strip_cdata=False)
    return _etree.parse(str(path), parser)


def _write_xml(tree: Any, path: Path) -> None:
    tree.write(str(path), xml_declaration=True, encoding="UTF-8", standalone=True)


def _open_opc_document(template_path: Path) -> _OpcDocument:
    _require_lxml()
    if not template_path.is_file():
        raise FileNotFoundError(template_path)

    work = Path(tempfile.mkdtemp(prefix="vsdx_build_"))
    try:
        with zipfile.ZipFile(template_path, "r") as z:
            z.extractall(work)
    except zipfile.BadZipFile as exc:
        shutil.rmtree(work, ignore_errors=True)
        raise VsdxBuildError(
            f"{template_path} is not a valid .vsdx (zip) file: {exc}"
        ) from exc

    pages_xml = work / "visio" / "pages" / "pages.xml"
    pages_rels = work / "visio" / "pages" / "_rels" / "pages.xml.rels"
    ct_xml = work / "[Content_Types].xml"
    if not (pages_xml.is_file() and pages_rels.is_file() and ct_xml.is_file()):
        shutil.rmtree(work, ignore_errors=True)
        raise VsdxBuildError(
            f"{template_path} is missing canonical OPC parts "
            f"(pages.xml / pages.xml.rels / [Content_Types].xml)"
        )

    doc = _OpcDocument(
        source_path=template_path,
        work_dir=work,
        pages_xml_tree=_parse_xml(pages_xml),
        pages_rels_tree=_parse_xml(pages_rels),
        content_types_tree=_parse_xml(ct_xml),
    )

    rel_targets = {r.get("Id"): r.get("Target")
                   for r in doc.pages_rels_tree.getroot().findall(
                       f"{{{NS_PR}}}Relationship")}

    for page_el in doc.pages_xml_tree.getroot().findall(f"{{{NS_V}}}Page"):
        rel_el = page_el.find(f"{{{NS_V}}}Rel")
        if rel_el is None:
            continue
        rel_id = rel_el.get(f"{{{NS_R}}}id")
        target = rel_targets.get(rel_id, "")
        if not target:
            continue
        page_part = (work / "visio" / "pages" / target).resolve()
        if not page_part.is_file():
            continue
        doc.pages.append(_OpcPage(
            document=doc,
            part_name="/" + page_part.relative_to(work).as_posix(),
            page_id=int(page_el.get("ID", "0")),
            name=page_el.get("Name") or page_el.get("NameU") or "",
            rel_id=rel_id,
            tree=_parse_xml(page_part),
        ))
    return doc


def _save_opc_document(doc: _OpcDocument, out_path: Path) -> None:
    _require_lxml()
    _write_xml(doc.pages_xml_tree, doc.work_dir / "visio" / "pages" / "pages.xml")
    _write_xml(doc.pages_rels_tree,
               doc.work_dir / "visio" / "pages" / "_rels" / "pages.xml.rels")
    _write_xml(doc.content_types_tree, doc.work_dir / "[Content_Types].xml")
    for page in doc.pages:
        _write_xml(page.tree, doc.work_dir / page.part_name.lstrip("/"))

    # Stamp <RecalcDocument/> on visio/document.xml so Visio recomputes on
    # next open (vsdx-format-quick-ref §6.1).
    doc_xml = doc.work_dir / "visio" / "document.xml"
    if doc_xml.is_file():
        try:
            tree = _parse_xml(doc_xml)
            qn = f"{{{NS_V}}}RecalcDocument"
            if tree.getroot().find(qn) is None:
                _etree.SubElement(tree.getroot(), qn)
            _write_xml(tree, doc_xml)
        except _etree.XMLSyntaxError:
            pass

    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists():
        out_path.unlink()

    members = sorted(p for p in doc.work_dir.rglob("*") if p.is_file())
    ct = doc.work_dir / "[Content_Types].xml"
    if ct in members:
        members.remove(ct)
        members.insert(0, ct)
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for p in members:
            z.write(p, p.relative_to(doc.work_dir).as_posix())


def _opc_copy_page(doc: _OpcDocument, src_index: int, new_name: str) -> _OpcPage:
    _require_lxml()
    src = doc.page_by_index(src_index)

    new_page_id = (max(p.page_id for p in doc.pages) + 1) if doc.pages else 0

    rel_root = doc.pages_rels_tree.getroot()
    rel_ids = [int(r.get("Id").lstrip("rId"))
               for r in rel_root.findall(f"{{{NS_PR}}}Relationship")
               if r.get("Id", "").startswith("rId")
               and r.get("Id").lstrip("rId").isdigit()]
    new_rel_id = f"rId{(max(rel_ids) + 1) if rel_ids else 1}"

    pages_dir = doc.work_dir / "visio" / "pages"
    existing = {p.name for p in pages_dir.iterdir()
                if p.is_file() and p.name.startswith("page")
                and p.name.endswith(".xml")}
    n = 1
    while f"page{n}.xml" in existing:
        n += 1
    new_part_name = f"page{n}.xml"

    src_part_path = doc.work_dir / src.part_name.lstrip("/")
    new_part_path = pages_dir / new_part_name
    shutil.copyfile(src_part_path, new_part_path)

    rel_el = _etree.SubElement(rel_root, f"{{{NS_PR}}}Relationship")
    rel_el.set("Id", new_rel_id)
    rel_el.set("Type", REL_TYPE_PAGE)
    rel_el.set("Target", new_part_name)

    pages_root = doc.pages_xml_tree.getroot()
    src_page_el = next(
        (p for p in pages_root.findall(f"{{{NS_V}}}Page")
         if int(p.get("ID", "-1")) == src.page_id), None)
    if src_page_el is None:
        raise VsdxBuildError(
            f"source page id {src.page_id} not found in pages.xml")
    new_page_el = _etree.fromstring(_etree.tostring(src_page_el))
    new_page_el.set("ID", str(new_page_id))
    new_page_el.set("NameU", new_name)
    new_page_el.set("Name", new_name)
    rel_child = new_page_el.find(f"{{{NS_V}}}Rel")
    if rel_child is not None:
        rel_child.set(f"{{{NS_R}}}id", new_rel_id)
    pages_root.append(new_page_el)

    ct_root = doc.content_types_tree.getroot()
    override_path = f"/visio/pages/{new_part_name}"
    if not any(o.get("PartName") == override_path
               for o in ct_root.findall(f"{{{NS_CT}}}Override")):
        override = _etree.SubElement(ct_root, f"{{{NS_CT}}}Override")
        override.set("PartName", override_path)
        override.set("ContentType", CT_PAGE)

    new_page = _OpcPage(
        document=doc,
        part_name=override_path,
        page_id=new_page_id,
        name=new_name,
        rel_id=new_rel_id,
        tree=_parse_xml(new_part_path),
    )
    doc.pages.append(new_page)
    return new_page


def _opc_set_text_by_id(page: _OpcPage, shape_id: int, text: str) -> None:
    _require_lxml()
    target = next(
        (s for s in page.shapes_el.findall(f".//{{{NS_V}}}Shape")
         if s.get("ID") and int(s.get("ID")) == shape_id), None)
    if target is None:
        raise KeyError(f"no shape with ID={shape_id} on page {page.name!r}")

    text_el = target.find(f"{{{NS_V}}}Text")
    if text_el is None:
        text_el = _etree.SubElement(target, f"{{{NS_V}}}Text")
    # Strip mid-text formatting runs — set_text_by_id is a literal-text override.
    for child in list(text_el):
        text_el.remove(child)
    text_el.text = text


def _opc_drop_master_xml(page: _OpcPage, master_xml: str,
                         x: float, y: float) -> int:
    _require_lxml()
    shapes = page.shapes_el
    new_id = _next_shape_id(shapes)
    shapes.append(_wrap_master_drop(master_xml, new_id, x, y))
    return new_id


def _opc_connect_xml(page: _OpcPage, from_id: int, to_id: int,
                     conn_kind: str) -> None:
    _require_lxml()
    begin, end = _build_connect(from_id, to_id, conn_kind)
    page.connects_el.append(begin)
    page.connects_el.append(end)


# vsdx primary-path adapters

@dataclass
class _VsdxPage:
    document: "_VsdxDocument"
    page: Any
    index: int

    @property
    def name(self) -> str:
        return getattr(self.page, "name", f"Page-{self.index + 1}")


@dataclass
class _VsdxDocument:
    source_path: Path
    visio_file: Any
    backend: str = "vsdx"


def _open_vsdx_document(template_path: Path) -> _VsdxDocument:
    if not _VSDX_AVAILABLE:
        raise VsdxBuildError("vsdx package not importable")
    if not template_path.is_file():
        raise FileNotFoundError(template_path)
    return _VsdxDocument(source_path=template_path,
                         visio_file=_vsdx.VisioFile(str(template_path)))


def _vsdx_save(doc: _VsdxDocument, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc.visio_file.save_vsdx(str(out_path))


def _vsdx_copy_page(doc: _VsdxDocument, src_index: int,
                    new_name: str) -> _VsdxPage:
    pages = doc.visio_file.pages
    if not 0 <= src_index < len(pages):
        raise KeyError(f"page index {src_index} out of range")
    src = pages[src_index]
    new_page = None
    try:
        new_page = doc.visio_file.copy_page(src, name=new_name)
    except (AttributeError, TypeError):
        if hasattr(src, "copy"):
            try:
                new_page = src.copy(name=new_name)
            except TypeError:
                new_page = src.copy()
                if new_page is not None and hasattr(new_page, "name"):
                    new_page.name = new_name
    if new_page is None:
        raise VsdxBuildError(
            "vsdx package does not expose copy_page or Page.copy on this "
            "version; pin a newer vsdx in requirements.txt or remove vsdx "
            "to force the OPC fallback."
        )
    return _VsdxPage(doc, new_page, len(doc.visio_file.pages) - 1)


def _vsdx_set_text_by_id(page: _VsdxPage, shape_id: int, text: str) -> None:
    target = None
    finder = getattr(page.page, "find_shape_by_id", None)
    if callable(finder):
        target = finder(str(shape_id)) or finder(shape_id)
    if target is None:
        for s in page.page.all_shapes:
            if str(getattr(s, "ID", "")) == str(shape_id):
                target = s
                break
    if target is None:
        raise KeyError(f"no shape with ID={shape_id} on page {page.name!r}")
    target.text = text


def _vsdx_page_xml(page: _VsdxPage) -> Any:
    page_xml = getattr(page.page, "xml", None)
    if page_xml is None:
        raise VsdxBuildError(
            "vsdx Page does not expose .xml on this version. Use the OPC "
            "fallback by uninstalling vsdx, or pin a newer release."
        )
    return page_xml


def _vsdx_drop_master_xml(page: _VsdxPage, master_xml: str,
                          x: float, y: float) -> int:
    _require_lxml()
    page_xml = _vsdx_page_xml(page)
    shapes_el = page_xml.find(f"{{{NS_V}}}Shapes")
    if shapes_el is None:
        shapes_el = _etree.SubElement(page_xml, f"{{{NS_V}}}Shapes")
    new_id = _next_shape_id(shapes_el)
    shapes_el.append(_wrap_master_drop(master_xml, new_id, x, y))
    return new_id


def _vsdx_connect_xml(page: _VsdxPage, from_id: int, to_id: int,
                      conn_kind: str) -> None:
    _require_lxml()
    page_xml = _vsdx_page_xml(page)
    connects = page_xml.find(f"{{{NS_V}}}Connects")
    if connects is None:
        connects = _etree.SubElement(page_xml, f"{{{NS_V}}}Connects")
    begin, end = _build_connect(from_id, to_id, conn_kind)
    connects.append(begin)
    connects.append(end)


# Public API

Document = Union[_VsdxDocument, _OpcDocument]
Page = Union[_VsdxPage, _OpcPage]


def open_template(template_path: Union[str, Path]) -> Document:
    """Open a template ``.vsdx``; return a backend-agnostic Document. Tries
    ``vsdx`` first when importable; falls back to raw OPC + ``lxml`` on
    import failure or vsdx parse error. ``FileNotFoundError`` is propagated.
    """
    path = Path(template_path)
    if _VSDX_AVAILABLE:
        try:
            return _open_vsdx_document(path)
        except FileNotFoundError:
            raise
        except Exception:  # noqa: BLE001 — fall through to OPC
            pass
    return _open_opc_document(path)


def copy_page(doc: Document, src_index: int, new_name: str) -> Page:
    """Clone ``doc.pages[src_index]`` as a new page named ``new_name``. The
    new page is appended; its index is ``len(doc.pages) - 1`` afterwards."""
    if isinstance(doc, _VsdxDocument):
        return _vsdx_copy_page(doc, src_index, new_name)
    if isinstance(doc, _OpcDocument):
        return _opc_copy_page(doc, src_index, new_name)
    raise TypeError(f"unsupported Document type: {type(doc).__name__}")


def set_text_by_id(page: Page, shape_id: int, text: str) -> None:
    """Overwrite text of shape on ``page`` with ``Shape/@ID == shape_id``.
    Raises ``KeyError`` if no such shape exists. Field codes (``<fld/>``)
    are replaced — literal text only."""
    if isinstance(page, _VsdxPage):
        _vsdx_set_text_by_id(page, shape_id, text)
        return
    if isinstance(page, _OpcPage):
        _opc_set_text_by_id(page, shape_id, text)
        return
    raise TypeError(f"unsupported Page type: {type(page).__name__}")


def drop_master_xml(page: Page, master_xml: str, x: float, y: float) -> int:
    """Append a master-derived ``<Shape>`` XML fragment to ``page`` at
    ``(x, y)``. Returns the allocated page-local ``Shape/@ID``. PinX/PinY
    are re-stamped; ID is allocated fresh."""
    if isinstance(page, _VsdxPage):
        return _vsdx_drop_master_xml(page, master_xml, x, y)
    if isinstance(page, _OpcPage):
        return _opc_drop_master_xml(page, master_xml, x, y)
    raise TypeError(f"unsupported Page type: {type(page).__name__}")


def connect_xml(page: Page, from_id: int, to_id: int,
                conn_kind: str = "dynamic") -> None:
    """Author a ``<Connect>`` Begin+End row pair gluing connector
    ``from_id`` to target ``to_id``. ``conn_kind``: ``begin-end`` /
    ``dynamic`` (whole-shape pin) or ``static`` (Connection.X1). This does
    not author the connector shape itself — drop it via ``drop_master_xml``
    first. Connector geometry is recomputed by Visio's routing engine on
    next open (cross-platform constraint)."""
    if isinstance(page, _VsdxPage):
        _vsdx_connect_xml(page, from_id, to_id, conn_kind)
        return
    if isinstance(page, _OpcPage):
        _opc_connect_xml(page, from_id, to_id, conn_kind)
        return
    raise TypeError(f"unsupported Page type: {type(page).__name__}")


def save(doc: Document, out_path: Union[str, Path]) -> Path:
    """Persist ``doc`` to ``out_path``; return the resolved output path."""
    target = Path(out_path)
    if isinstance(doc, _VsdxDocument):
        _vsdx_save(doc, target)
    elif isinstance(doc, _OpcDocument):
        _save_opc_document(doc, target)
    else:
        raise TypeError(f"unsupported Document type: {type(doc).__name__}")
    return target


@contextmanager
def _document_session(template_path: Path) -> Iterator[Document]:
    """Open a template, yield the document, clean up on exit."""
    doc = open_template(template_path)
    try:
        yield doc
    finally:
        if isinstance(doc, _VsdxDocument):
            close = getattr(doc.visio_file, "close_vsdx", None)
            if callable(close):
                try:
                    close()
                except Exception:  # noqa: BLE001
                    pass
        elif isinstance(doc, _OpcDocument):
            shutil.rmtree(doc.work_dir, ignore_errors=True)


# CLI helpers

def _emit_summary(payload: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(payload, ensure_ascii=False))
    sys.stdout.write("\n")
    sys.stdout.flush()


def _resolve_page(doc: Document, page_index: int) -> Page:
    if isinstance(doc, _OpcDocument):
        return doc.page_by_index(page_index)
    if isinstance(doc, _VsdxDocument):
        pages = doc.visio_file.pages
        if not 0 <= page_index < len(pages):
            raise KeyError(f"page index {page_index} out of range "
                           f"(have {len(pages)})")
        return _VsdxPage(doc, pages[page_index], page_index)
    raise TypeError(f"unsupported document: {type(doc).__name__}")


def _doc_summary(doc: Document) -> dict[str, Any]:
    if isinstance(doc, _VsdxDocument):
        return {
            "backend": "vsdx",
            "path": str(doc.source_path),
            "pages": [{"index": i, "name": getattr(p, "name", "")}
                      for i, p in enumerate(doc.visio_file.pages)],
        }
    return {
        "backend": "opc",
        "path": str(doc.source_path),
        "pages": [{"index": i, "id": p.page_id, "name": p.name}
                  for i, p in enumerate(doc.pages)],
    }


# CLI

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vsdx_build.py",
        description="Cross-platform .vsdx build helper "
                    "(vsdx primary, OPC+lxml fallback).",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("inspect", help="Print a JSON summary of the template.")
    p.add_argument("template", type=Path)

    p = sub.add_parser("copy-page", help="Duplicate a page.")
    p.add_argument("template", type=Path)
    p.add_argument("out", type=Path)
    p.add_argument("--src", type=int, default=0)
    p.add_argument("--name", required=True)

    p = sub.add_parser("set-text", help="Overwrite a shape's text by ID.")
    p.add_argument("template", type=Path)
    p.add_argument("out", type=Path)
    p.add_argument("--page", type=int, default=0)
    p.add_argument("--shape-id", type=int, required=True)
    p.add_argument("--text", required=True)

    p = sub.add_parser("drop-master",
                       help="Append a master-derived shape XML to a page.")
    p.add_argument("template", type=Path)
    p.add_argument("out", type=Path)
    p.add_argument("--page", type=int, default=0)
    p.add_argument("--xml", type=Path, required=True,
                   help="Path to a file holding a single <Shape> fragment.")
    p.add_argument("--x", type=float, required=True)
    p.add_argument("--y", type=float, required=True)

    p = sub.add_parser("connect", help="Glue a connector to a target shape.")
    p.add_argument("template", type=Path)
    p.add_argument("out", type=Path)
    p.add_argument("--page", type=int, default=0)
    p.add_argument("--from", dest="from_id", type=int, required=True)
    p.add_argument("--to", dest="to_id", type=int, required=True)
    p.add_argument("--kind", choices=sorted(CONN_KINDS), default="dynamic")

    return parser


def _cmd_inspect(args: argparse.Namespace) -> int:
    with _document_session(args.template) as doc:
        _emit_summary(_doc_summary(doc))
    return 0


def _cmd_copy_page(args: argparse.Namespace) -> int:
    with _document_session(args.template) as doc:
        copy_page(doc, args.src, args.name)
        out = save(doc, args.out)
        _emit_summary({"op": "copy_page", "ok": True, "src": args.src,
                       "name": args.name, "out": str(out),
                       "backend": getattr(doc, "backend", "unknown")})
    return 0


def _cmd_set_text(args: argparse.Namespace) -> int:
    with _document_session(args.template) as doc:
        set_text_by_id(_resolve_page(doc, args.page), args.shape_id, args.text)
        out = save(doc, args.out)
        _emit_summary({"op": "set_text", "ok": True, "page": args.page,
                       "shape_id": args.shape_id, "out": str(out),
                       "backend": getattr(doc, "backend", "unknown")})
    return 0


def _cmd_drop_master(args: argparse.Namespace) -> int:
    xml_str = args.xml.read_text(encoding="utf-8")
    with _document_session(args.template) as doc:
        new_id = drop_master_xml(_resolve_page(doc, args.page),
                                 xml_str, args.x, args.y)
        out = save(doc, args.out)
        _emit_summary({"op": "drop_master", "ok": True, "page": args.page,
                       "shape_id": new_id, "x": args.x, "y": args.y,
                       "out": str(out),
                       "backend": getattr(doc, "backend", "unknown")})
    return 0


def _cmd_connect(args: argparse.Namespace) -> int:
    with _document_session(args.template) as doc:
        connect_xml(_resolve_page(doc, args.page),
                    args.from_id, args.to_id, args.kind)
        out = save(doc, args.out)
        _emit_summary({"op": "connect", "ok": True, "page": args.page,
                       "from": args.from_id, "to": args.to_id,
                       "kind": args.kind, "out": str(out),
                       "backend": getattr(doc, "backend", "unknown")})
    return 0


_DISPATCH = {
    "inspect": _cmd_inspect,
    "copy-page": _cmd_copy_page,
    "set-text": _cmd_set_text,
    "drop-master": _cmd_drop_master,
    "connect": _cmd_connect,
}


def main(argv: Optional[list[str]] = None) -> int:
    if not _LXML_AVAILABLE:
        print("error: lxml is required; install via the project's "
              "requirements.txt.", file=sys.stderr)
        return 2

    args = _build_parser().parse_args(argv)
    handler = _DISPATCH.get(args.cmd)
    if handler is None:
        _build_parser().print_help(sys.stderr)
        return 2

    try:
        return handler(args)
    except FileNotFoundError as exc:
        print(f"error: file not found: {exc}", file=sys.stderr)
        return 2
    except KeyError as exc:
        print(f"error: lookup failed: {exc}", file=sys.stderr)
        return 1
    except VsdxBuildError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except zipfile.BadZipFile as exc:
        print(f"error: not a valid .vsdx zip: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001 — last-resort surface for the CLI
        # pywintypes.com_error never reaches here (no COM in this module),
        # but caught broadly so the CLI never traceback-spews.
        print(f"error: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
