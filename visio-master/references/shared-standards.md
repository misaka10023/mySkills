# Shared Technical Standards

Cross-role hard standards every visio-master role consults before writing or
editing a `.vsdx` artefact. These are the constraints that, if violated, either
break the file at OPC level, render incorrectly in Microsoft Visio, lock the
runtime through a COM threading bug, or destroy round-trip fidelity through the
`vsdx_export.py` pipeline. Architect, Drafter, and Stylist all read this file
once per project; `vsdx_quality_checker.py` enforces a static subset of the
rules listed below at lint time.

> Where a value is a closed enumeration (e.g. ContentType strings,
> `VisCellVals` route style ids), the enum given here is canonical — anything
> outside the enum produces a "needs to be repaired" dialog when Visio opens
> the file. The XML schema accepts a wider grammar than the runtime; do not
> trust XSD validation alone.

---

## 1. File naming, units, and canvas geometry

### 1.1 File and part naming

| Surface | Naming rule | Example | Why |
|---------|-------------|---------|-----|
| Final drawing | `<project>_<YYYYMMDD-HHMM>.vsdx` | `network_topology_20260614-1530.vsdx` | Matches `ppt-master`'s timestamp suffix; resists overwrites in `exports/`. |
| Per-page authoring fragment | `<NN>_<page_name>.vsdx-page.xml` | `03_data_ingest.vsdx-page.xml` | `NN` is two-digit zero-padded; page name lower-snake. Drafter writes one fragment per page. |
| Stencil master fragment | `<shape>.vssx-master.xml` | `decision.vssx-master.xml` | Browser-preview sibling lives next to it as `<shape>.svg`. |
| Theme bundle | `<theme_id>/theme.xml` | `dark-tech/theme.xml` | DrawingML root `a:theme`; lazy-loaded by Stylist. |
| ZIP part path inside `.vsdx` | UTF-8, forward-slash separated | `visio/pages/page1.xml` | OPC mandates forward slashes; Windows paths break readers. |
| Relationship Id | `rIdN` (sequential, unique within the rels part) | `rId1`, `rId2`, … | Visio writes them in document order; readers do not rely on order, but stable ids keep diffs small. |

`.vsdm`, `.vstx`, `.vstm`, `.vssx`, `.vssm` use the same OPC framing as
`.vsdx` but require matching `Override` content types in
`[Content_Types].xml` (see §3.2). Renaming the extension without rewriting
`[Content_Types].xml` and adjusting the package-level relationship to
`document.xml` corrupts the file.

### 1.2 Units — millimetre is the project default

visio-master locks its working unit to **mm** by default, even on US letter
canvases. Every `Width`, `Height`, `PinX`, `PinY`, `BeginX`, `EndX`, page
margin, spacing parameter, and ConnectorAvenue value is authored in mm and
converted at export only when the page format demands inches.

| Quantity | Authoring unit | Visio cell unit string (`U=` attribute) | Notes |
|----------|---------------|-----------------------------------------|-------|
| Page extent (`PageWidth`, `PageHeight`) | mm | `MM` for ISO, `IN` for US Letter / Tabloid | The page unit follows `canvas.format`; do not mix. |
| Shape geometry (`Width`, `Height`, `PinX`, `PinY`) | mm | inherits from page unless overridden | Visio treats a unitless number as page-default unit. |
| Connector endpoints (`BeginX`, `BeginY`, `EndX`, `EndY`) | mm | inherits | Always express in the same unit as the page. |
| Line widths and stroke weights (`LineWeight`) | **points** | `PT` | Always pt — never mm — because typographic conventions and Visio's UI both round-trip in pt. |
| Font size (`Char.Size`) | points | `PT` | Same reasoning. |
| Angles (`Angle`) | degrees | `DEG` | Visio internally stores radians; emit `DEG` and let the recalc engine convert. |
| Drawing scale (`PageScale` / `DrawingScale`) | unit-tagged literal | `IN_F` (inch fixed), `MM_F`, etc. | A scale of "1 mm = 100 mm" is `PageScale=1 mm`, `DrawingScale=100 mm`. |
| Time-style cells (`Misc.Comment` does not apply) | n/a | n/a | No time cells in geometry; date helpers live in text fields. |

**Cross-unit hazard** — Visio silently accepts mixed units. A shape with
`Width=100 mm` on a page declared `PageWidth=8.5 in` is a 100 mm shape on an
8.5 inch page (correct). A shape with `Width=100` on the same page is a
100-inch shape (wrong by a factor of 25.4). The quality checker flags any
naked numeric coordinate in a `Cell` element whose `U=` attribute is missing.

### 1.3 Canvas catalogue

| Format id | Width | Height | Unit | Orientation | Use |
|-----------|-------|--------|------|-------------|-----|
| `a4-landscape` | 297 | 210 | mm | landscape | Default for diagrams in EU/CN/JP organisations. |
| `a4-portrait` | 210 | 297 | mm | portrait | Long flowcharts, swim lanes top-to-bottom. |
| `a3-landscape` | 420 | 297 | mm | landscape | Detailed network maps, BPMN. |
| `a3-portrait` | 297 | 420 | mm | portrait | Org charts, hierarchy trees. |
| `letter-landscape` | 11 | 8.5 | in | landscape | US-default presentations. |
| `letter-portrait` | 8.5 | 11 | in | portrait | US-default printouts. |
| `tabloid` | 17 | 11 | in | landscape | US large-format dashboards. |
| `custom` | author-supplied | author-supplied | mm or in | author-supplied | Anything else; `canvas.units` must be declared. |

Default DPI for all formats is `96` (screen) — raise to `150` for
print-bound drawings via `canvas.dpi: 150`. The DPI is metadata only; Visio's
internal raster is vector-first.

### 1.4 ISO-A vs US-Letter selection table

| Audience / region | Recommended format | Reason |
|-------------------|--------------------|-------|
| EU, CN, JP, AU enterprise | `a4-landscape` (default) | ISO 216 paper is the office norm. |
| Engineering / architecture print | `a3-landscape` or `a3-portrait` | Leaves space for title block, dimension callouts. |
| US enterprise | `letter-landscape` | US-Letter is the office norm. |
| US engineering print | `tabloid` | ANSI B is the closest analogue to A3. |
| Public web / SharePoint preview | `a4-landscape` | Web preview crops to fit; ISO ratio looks identical at thumbnail scale. |
| Mixed audience | `a4-landscape` with `--export-pdf` | PDF is unit-neutral on screen. |

Architect's confirmation 1 picks one of these; Stylist does not override.
Mid-project format change requires `update_diagram_lock.py --canvas <new>` so
that every page's `PageWidth` / `PageHeight` cells are rewritten atomically.

---

## 2. Namespace versions — every URI that must match exactly

VSDX is an OPC package; the package frame uses ECMA-376 namespaces, the
Visio body uses Microsoft's `2012/main` namespace, the theme uses DrawingML
2006. A wrong namespace is silent: Visio repairs the file (data loss) or
rejects it.

| Surface | XML element | Namespace URI | Prefix |
|---------|-------------|---------------|--------|
| OPC content-types | `Types` | `http://schemas.openxmlformats.org/package/2006/content-types` | (default) |
| OPC relationships | `Relationships`, `Relationship` | `http://schemas.openxmlformats.org/package/2006/relationships` | (default) |
| Visio document body | `VisioDocument`, `Pages`, `Page`, `Shape`, `Cell`, `Section`, `Row` | `http://schemas.microsoft.com/office/visio/2012/main` | (default), often `v:` |
| Office relationships referenced inline | `Rel/@r:id` | `http://schemas.openxmlformats.org/officeDocument/2006/relationships` | `r:` |
| Theme | `a:theme`, `a:clrScheme`, `a:fontScheme`, `a:fmtScheme` | `http://schemas.openxmlformats.org/drawingml/2006/main` | `a:` |
| Dublin Core (in `core.xml`) | `dc:title`, `dc:creator` | `http://purl.org/dc/elements/1.1/` | `dc:` |
| Dublin Core terms (in `core.xml`) | `dcterms:created`, `dcterms:modified` | `http://purl.org/dc/terms/` | `dcterms:` |
| Core properties root | `cp:coreProperties` | `http://schemas.openxmlformats.org/package/2006/metadata/core-properties` | `cp:` |
| Extended properties (`app.xml`) | `Properties` | `http://schemas.openxmlformats.org/officeDocument/2006/extended-properties` | (default) |
| Custom properties (`custom.xml`) | `Properties`, `property` | `http://schemas.openxmlformats.org/officeDocument/2006/custom-properties` | (default) |
| Variant types (used in `app.xml` / `custom.xml`) | `vt:lpstr`, `vt:i4`, `vt:bool` | `http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes` | `vt:` |

### 2.1 Relationship Type URIs (closed enum used in `.rels` files)

| Relationship | Type URI | Source → Target |
|--------------|----------|-----------------|
| Office document | `http://schemas.microsoft.com/visio/2010/relationships/document` | `_rels/.rels` → `visio/document.xml` |
| Pages index | `http://schemas.microsoft.com/visio/2010/relationships/pages` | `document.xml.rels` → `pages/pages.xml` |
| Page | `http://schemas.microsoft.com/visio/2010/relationships/page` | `pages.xml.rels` → `pages/page#.xml` |
| Masters index | `http://schemas.microsoft.com/visio/2010/relationships/masters` | `document.xml.rels` → `masters/masters.xml` |
| Master | `http://schemas.microsoft.com/visio/2010/relationships/master` | `masters.xml.rels` → `masters/master#.xml` |
| Theme | `http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme` | `document.xml.rels` → `theme/theme1.xml` |
| Window | `http://schemas.microsoft.com/visio/2010/relationships/windows` | `document.xml.rels` → `window.xml` |
| Connections | `http://schemas.microsoft.com/visio/2010/relationships/connections` | `document.xml.rels` → `connections/connections.xml` |
| RecordSets index | `http://schemas.microsoft.com/visio/2010/relationships/recordSets` | `document.xml.rels` → `datarecordsets/recordsets.xml` |
| RecordSet | `http://schemas.microsoft.com/visio/2010/relationships/recordSet` | `recordsets.xml.rels` → `recordset#.xml` |
| Image | `http://schemas.openxmlformats.org/officeDocument/2006/relationships/image` | `page#.xml.rels` → `media/image#.png` |
| ForeignData | `http://schemas.microsoft.com/visio/2010/relationships/foreignData` | page/master rels → external bin |
| Comments | `http://schemas.microsoft.com/visio/2010/relationships/comments` | `document.xml.rels` → `comments.xml` |
| Solution XML | `http://schemas.microsoft.com/visio/2010/relationships/solutionXML` | (rare) extension parts |
| VBA project | `http://schemas.microsoft.com/office/2006/relationships/vbaProject` | `.vsdm`/`.vstm`/`.vssm` only |
| Core properties | `http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties` | `_rels/.rels` → `docProps/core.xml` |
| Extended (app) properties | `http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties` | `_rels/.rels` → `docProps/app.xml` |
| Custom properties | `http://schemas.openxmlformats.org/officeDocument/2006/relationships/custom-properties` | `_rels/.rels` → `docProps/custom.xml` |
| Thumbnail | `http://schemas.openxmlformats.org/package/2006/relationships/metadata/thumbnail` | `_rels/.rels` → `docProps/thumbnail.emf` |

> **Versioning trap** — the Visio body namespace is `2012/main`, the
> relationship URIs are `2010/...`, the theme namespace is `2006/main`. The
> three different year stamps reflect when each schema was frozen and are
> *not* interchangeable. Updating a 2012 namespace to 2013 silently breaks
> every consumer; there is no `2013/main`.

### 2.2 ContentType strings (closed enum from `[Content_Types].xml`)

| Part | ContentType |
|------|-------------|
| `visio/document.xml` (`.vsdx`) | `application/vnd.ms-visio.drawing.main+xml` |
| `visio/document.xml` (`.vsdm`) | `application/vnd.ms-visio.drawing.macroEnabled.main+xml` |
| `visio/document.xml` (`.vssx`) | `application/vnd.ms-visio.stencil.main+xml` |
| `visio/document.xml` (`.vssm`) | `application/vnd.ms-visio.stencil.macroEnabled.main+xml` |
| `visio/document.xml` (`.vstx`) | `application/vnd.ms-visio.template.main+xml` |
| `visio/document.xml` (`.vstm`) | `application/vnd.ms-visio.template.macroEnabled.main+xml` |
| `visio/pages/pages.xml` | `application/vnd.ms-visio.pages+xml` |
| `visio/pages/page#.xml` | `application/vnd.ms-visio.page+xml` |
| `visio/masters/masters.xml` | `application/vnd.ms-visio.masters+xml` |
| `visio/masters/master#.xml` | `application/vnd.ms-visio.master+xml` |
| `visio/theme/theme#.xml` | `application/vnd.openxmlformats-officedocument.theme+xml` |
| `visio/window.xml` | `application/vnd.ms-visio.windows+xml` |
| `visio/connections/connections.xml` | `application/vnd.ms-visio.connections+xml` |
| `visio/datarecordsets/recordsets.xml` | `application/vnd.ms-visio.recordsets+xml` |
| `visio/datarecordsets/recordset#.xml` | `application/vnd.ms-visio.recordset+xml` |
| `visio/comments.xml` | `application/vnd.ms-visio.comments+xml` |
| `visio/extensions/extensions.xml` | `application/vnd.ms-visio.extensions+xml` |
| `visio/vbaProject.bin` | `application/vnd.ms-office.vbaProject` |
| `docProps/app.xml` | `application/vnd.openxmlformats-officedocument.extended-properties+xml` |
| `docProps/core.xml` | `application/vnd.openxmlformats-package.core-properties+xml` |
| `docProps/custom.xml` | `application/vnd.openxmlformats-officedocument.custom-properties+xml` |
| `_rels/*.rels` | `application/vnd.openxmlformats-package.relationships+xml` |

`[Content_Types].xml` MUST be the first entry in the ZIP central directory.
`vsdx_export.py`'s `opc_writer.py` enforces this; the fallback `vsdx`-lib
writer enforces it through its own writer.

---

## 3. ShapeSheet cells that must NEVER be hand-overridden

These cells carry inherited or engine-managed formulas. Hand-writing a
literal value into them either breaks recalc dependency tracking, breaks
master inheritance, or is silently overwritten on the next Visio recalc —
appearing to work but failing under round-trip.

### 3.1 Inherited cells (master / style chain)

| Cell (universal name) | Section | Reason it is engine-managed |
|-----------------------|---------|-----------------------------|
| `LineColor`, `LineWeight`, `LinePattern`, `Rounding`, `LineColorTrans`, `LineCap`, `BeginArrow`, `EndArrow`, `BeginArrowSize`, `EndArrowSize` | Line Format | Inherited from the line style; overriding breaks `THEMEGUARD()` propagation. Use `LineStyle = "<style name>"` instead. |
| `FillForegnd`, `FillBkgnd`, `FillPattern`, `ShdwForegnd`, `ShdwPattern`, `FillForegndTrans`, `FillBkgndTrans`, `ShdwForegndTrans` | Fill Format | Same — inherit through `FillStyle`. Hard-coded HEX defeats theme variants and prints wrong on dark themes. |
| `Char.Font`, `Char.Color`, `Char.Style`, `Char.Size`, `Char.Case`, `Char.Pos`, `Char.LangID`, `Char.AsianFont`, `Char.ComplexScriptFont` | Character | Inherited from `TextStyle`; only override per-run via `Characters.CharProps`. |
| `Para.HorzAlign`, `Para.IndFirst`, `Para.IndLeft`, `Para.IndRight`, `Para.SpBefore`, `Para.SpAfter`, `Para.SpLine`, `Para.Bullet*` | Paragraph | Inherited from `TextStyle`; if a per-paragraph override is needed, push into the master, not the instance. |
| `TxtPinX`, `TxtPinY`, `TxtWidth`, `TxtHeight`, `TxtAngle`, `TxtLocPinX`, `TxtLocPinY` | Text Transform | Visio computes these from `Width`/`Height` if cells are absent. Writing literal values pins the text block and breaks shape resize. |
| `Connections.X*`, `Connections.Y*`, `Connections.DirX*`, `Connections.DirY*`, `Connections.Type*` | Connection Pts | The master defines connection points. Adding a literal connection point on a shape *instance* (rather than the master) breaks the master inheritance chain — Visio re-issues the master's points on next recalc and silently drops the override. |

### 3.2 Engine-managed cells (auto-recomputed on recalc)

| Cell | Section | Why hands-off |
|------|---------|---------------|
| `BegTrigger`, `EndTrigger` | Glue Info | Visio writes `_XFTRIGGER(...)` formulae here when an endpoint is glued. Hand-edits are blown away on the next geometric change. |
| `PinX`, `PinY`, `Width`, `Angle` (on 1-D shapes) | XForm | Derived from `BeginX`/`BeginY`/`EndX`/`EndY`. Writing `PinX` directly on a connector causes the next recalc to flip the endpoints. |
| `EventXFMod`, `EventDrop`, `EventDblClick`, `TheText`, `TheData` | Event | Owned by SmartShape masters; Drafter does NOT hook these — Stylist (or a Template_Designer) owns event-cell formulae if any. |
| `LayerMember` (literal index) | Misc | The cell value is a semicolon-delimited list of layer **indices**, not names. Indices are page-local and shift when layers are added/removed. Stylist owns layer assignment via `assemble_containers.py` / `apply_theme.py`. |
| `LangID`, `Calendar` | Misc | Locale-dependent; set once via `diagram_lock.text.language` and propagated by `update_diagram_lock.py`. |
| `RouteStyle`, `AvenueSizeX`, `AvenueSizeY`, `BlockSizeX`, `BlockSizeY`, `LineRouteExt`, `PageLineJumpDirX`, `PageLineJumpDirY`, `LineJumpFactorX`, `LineJumpFactorY`, `LineJumpStyle`, `LineJumpCode` | PageSheet (Page Layout) | Routing is a page-level concern owned by Stylist's `connectors.routing` lock value. Per-shape `ShapeRouteStyle` is the only legal Drafter override. |

### 3.3 Cells Drafter MAY write directly

| Cell | Section | Use |
|------|---------|-----|
| `PinX`, `PinY`, `Width`, `Height`, `LocPinX`, `LocPinY`, `Angle`, `FlipX`, `FlipY` | XForm (2-D) | Geometry placement — the core Drafter authoring surface. |
| `BeginX`, `BeginY`, `EndX`, `EndY` | XForm1D | Connector endpoints; usually populated through `Cell.GlueTo`, but raw `PNT(...)` formulas are acceptable when a static glue target is intended. |
| `User.<name>.Value` / `User.<name>.Prompt` | User-defined | Drafter scratch storage — keep names lower_snake. Reserved prefix: `User.vm_*` (visio-master internal markers, written only by `update_diagram_lock.py`). |
| `Prop.<name>.Value` / `Prop.<name>.Label` / `Prop.<name>.Type` / `Prop.<name>.Format` / `Prop.<name>.Prompt` / `Prop.<name>.SortKey` / `Prop.<name>.Invisible` / `Prop.<name>.Ask` | Shape Data | First-class custom properties. Type values: `0=String`, `1=Fixed list`, `2=Number`, `3=Boolean`, `4=Variable list`, `5=Date`, `7=Currency`. |
| `Comment` | Misc | Free-form designer note. The `pages/<NN>_*.shapesheet-notes.md` Drafter sidecar flows into this cell at finalisation time. |
| `ShapeKeywords` | Misc | Indexed search keywords; populated by Stylist when `diagram_lock.tags` is non-empty. |

### 3.4 Forbidden ShapeSheet patterns (lint errors)

`vsdx_quality_checker.py` raises `error` on any of these:

| Pattern | Why forbidden |
|---------|---------------|
| `INTERSECTX(...)` / `INTERSECTY(...)` in any geometry cell | Brittle; depends on adjacent shape positions and breaks under any layout change. Prefer named connection points + `GlueTo`. |
| Bare `EVAL(<arbitrary string>)` in a Geometry/XForm cell | `EVAL` was deprecated in Visio 2007. Surviving usages exist in third-party stencils only. |
| `LOOKUP(...)` / `INDEX(...)` against `ThePage!User.<extData>` | Data binding is Stylist's job, applied through Data Graphics, not raw lookups in geometry. |
| `RUNADDON("<addonName>")` referencing an unregistered add-on | Saved formula points at code that doesn't exist on the consumer's machine; Visio shows a yellow alert on every recalc. |
| Direct write to `BegTrigger` / `EndTrigger` | Engine cells; see §3.2. |
| `MASTER(...)` reference inside a geometry cell on an instance | Bypasses the master inheritance chain. Use `Master` back-pointer + style inheritance instead. |
| Literal HEX inside `LineColor` / `FillForegnd` / `Char.Color` when a theme variant exists | See §10. |

---

## 4. Banned API patterns

These are COM and library calls that look correct but produce broken `.vsdx` files, COM hangs, or licensing/security regressions. Every entry below is enforced by `vsdx_quality_checker.py` (for static call patterns) or by code review of `scripts/vsdx_export/com_writer.py` (for runtime patterns).

### 4.1 Banned COM patterns

| Banned call | Replacement | Reason |
|-------------|-------------|--------|
| `Dispatch("Visio.Application")` from a service / unattended job | `DispatchEx("Visio.InvisibleApp")` | `Dispatch` reuses an existing instance via the Running Object Table — risks hijacking the user's interactive Visio. `DispatchEx` always spawns a fresh out-of-process server; `InvisibleApp` keeps the main window hidden. |
| `app.Visible = True` in `vsdx_export.py` | leave `False` | A visible app forces UI message-pump cycles and slows export by 5–10×. |
| `app.Quit()` without `app.AlertResponse = 7` first | set `AlertResponse = 7` (= `visAlertResponseNo`) before `Quit` | Otherwise an unsaved-state Quit pops a modal "Save changes?" dialog — invisible app or not — and the script hangs forever. |
| `Marshal.ReleaseComObject(...)` over-released | trust runtime release; only release the top-level `Application` once after `Quit` | Over-releasing a Visio proxy crashes the host process or zombies the Visio worker. |
| `app.Documents.Open(path)` for stencil | `app.Documents.OpenEx(path, visOpenRO \| visOpenHidden \| visOpenDocked \| visOpenMacrosDisabled)` | `Open` writes to the file's MRU list and may leave a lock; `OpenEx` with the bitmask above is read-only, hidden, and non-blocking. |
| `app.Documents.Open(stencil)` followed by `doc.Save()` | open RO; never `Save` a stencil opened for shape harvesting | Save would update the user's stencil with the document's current theme — silent corruption. |
| `pythoncom.PumpMessages()` from a non-main thread | run the pump only on the apartment thread that created the Visio proxy | Cross-thread pumps deliver events to the wrong apartment and produce `RPC_E_WRONG_THREAD` (`0x8001010E`). |
| `gencache.EnsureDispatch("Visio.Application")` followed by `DispatchEx` reusing the gen_py module without `EnsureModule` | call `gencache.EnsureModule("{00021A98-0000-0000-C000-000000000046}", 0, 4, 12)` first, then `DispatchEx("Visio.InvisibleApp")` | Otherwise `win32com.client.constants` is empty for the second instance and `c.visOpenRO` is `AttributeError`. |
| `app.Documents.Add("")` then `doc.SaveAs("...vsdm")` without macro source | Use `.vsdx` extension or attach a `vbaProject.bin` part | A `.vsdm` written without a VBA project is technically valid but Visio's Trust Center treats it as suspicious and prompts on every open. |
| `page.DrawRectangle(...)` for shapes that have a master | `page.Drop(master, x, y)` | Direct geometry skips the master inheritance chain — the resulting shape has no `Master` back-pointer, no master-driven styling, and is invisible to `Page.Layout()` routing categorisation. |
| Concurrent writes from two threads to the same `Application` proxy | serialise through a single STA thread | Visio's COM server is STA — concurrent calls produce `RPC_E_SERVERCALL_RETRYLATER` (`0x8001010A`) under load. |
| `app.Quit()` while documents are still iterating | close every `Document` first, then `Quit` | Iteration during shutdown raises `pywintypes.com_error` with `0x800401FD` (object not connected). |

### 4.2 Banned `vsdx` Python lib patterns

| Banned call | Replacement | Reason |
|-------------|-------------|--------|
| `vsdx.VisioFile.save(path)` over the same input path | `save(out_path)` to a fresh path | The library streams from the input ZIP while writing — overlapping read/write produces a truncated output. |
| Constructing a `Page` directly | `vsdx.Page(visio_file=...)` only inside the library; in our writer use `opc_writer.add_page_part(...)` | The lib's constructor does not register the page in `pages.xml` or `[Content_Types].xml`; the page is invisible to Visio. |
| Mutating `vsdx.shape.Shape.master` after `to_xml()` | clone the shape, swap masters, call `to_xml()` once | The shape caches its serialized XML; a post-serialize master swap leaves the cache stale. |
| Writing UTF-16 BOM in any part | UTF-8 only, BOM optional but discouraged | Visio's parser misreads UTF-16-prefixed parts as garbage and shows the "needs to be repaired" dialog. |
| Hand-rolled `re.sub` on `<Cell ... F="..."/>` formulae | walk the XML with `lxml`; rebuild formulas with the helpers in `scripts/vsdx_export/drawingml_utils.py` | Formulas can contain quoted strings with `>`, `<`, and `&`; regex substitution corrupts them in 1 of every ~30 cases. |

### 4.3 Banned `aspose.diagram` patterns

| Banned call | Replacement | Reason |
|-------------|-------------|--------|
| `Diagram(licenseUnset).save("out.vsdx")` | always set the license object before any save | Aspose injects a watermark ribbon shape into Page 1 when unlicensed; the file passes `vsdx` validation but renders with a banner. |
| `Diagram.save(path, SaveFileFormat.SVG)` for browser preview | use `vsdx_preview/render_page.py` instead | The Aspose SVG export inlines all theme HEX values, defeating §10. |

### 4.4 Banned PowerShell patterns

| Banned | Replacement |
|--------|-------------|
| `New-Object -ComObject Visio.Application` in CI | `New-Object -ComObject Visio.InvisibleApp` |
| `[runtime.interopservices.Marshal]::ReleaseComObject($app)` in a loop until `0` | call once per top-level proxy in `finally` |
| `$visio.Quit()` without `$ErrorActionPreference = 'Stop'` | always set `Stop` so a `com_error` propagates instead of being swallowed |

---

## 5. Python COM threading rules

Visio's COM server is **STA (single-threaded apartment)**. Every call must happen on the apartment that owns the proxy. The four rules below are non-negotiable; `scripts/vsdx_export/com_writer.py` enforces them with a process-wide lock.

### 5.1 Initialisation

| Rule | Code | Notes |
|------|------|-------|
| Every thread that touches a Visio proxy MUST initialise COM first | `pythoncom.CoInitializeEx(pythoncom.COINIT_APARTMENTTHREADED)` | `COINIT_APARTMENTTHREADED = 2`. The bare `pythoncom.CoInitialize()` is also acceptable (defaults to STA) but the explicit constant documents intent. |
| Every thread that initialised COM MUST uninitialise before exit | `pythoncom.CoUninitialize()` | Skipping this leaks the apartment and the next `CoInitializeEx` on the same thread raises `0x80010106 RPC_E_CHANGED_MODE`. |
| Wrap init/uninit in `try` / `finally` | `try: ... finally: pythoncom.CoUninitialize()` | A bare exception leaves the apartment dangling for the lifetime of the worker. |
| The Visio proxy is bound to its creating thread | never share `app`, `doc`, `page`, `shape` proxies across threads without marshalling | Cross-thread access raises `0x8001010E RPC_E_WRONG_THREAD`. |

### 5.2 Marshalling across threads (rare; prefer single-threaded design)

| API | Use |
|-----|-----|
| `pythoncom.CoMarshalInterThreadInterfaceInStream(IID_IDispatch, proxy)` | Serialise the proxy on thread A. Returns an `IStream` cookie. |
| `pythoncom.CoGetInterfaceAndReleaseStream(stream, IID_IDispatch)` | Re-hydrate the proxy on thread B. Releases the stream automatically. |
| `comtypes.client.CreateObject(progid, machine=None, interface=...)` with explicit `pythoncom.COINIT_MULTITHREADED` | Only when targeting an out-of-process server explicitly built for MTA — Visio is **not** one of these. |

### 5.3 Process-wide lock pattern (`com_writer.py`)

The fallback path (`vsdx` lib + raw OPC) is process-safe; only the COM path needs the lock. The lock is **per process**, not per thread, because spawning two `Visio.InvisibleApp` instances on one machine doubles the licensing footprint and races on the file lock for built-in stencils.

```python
import threading, pythoncom, win32com.client as win32

_VISIO_LOCK = threading.Lock()

def with_visio(callback):
    """Run `callback(app)` against a fresh InvisibleApp, serialised process-wide."""
    with _VISIO_LOCK:
        pythoncom.CoInitializeEx(pythoncom.COINIT_APARTMENTTHREADED)
        try:
            win32.gencache.EnsureModule(
                "{00021A98-0000-0000-C000-000000000046}", 0, 4, 12)
            app = win32.DispatchEx("Visio.InvisibleApp")
            app.AlertResponse = 7              # visAlertResponseNo
            app.ScreenUpdating = False
            app.EventsEnabled = 0
            app.UndoEnabled = False
            try:
                return callback(app)
            finally:
                app.Quit()
        finally:
            pythoncom.CoUninitialize()
```

### 5.4 Common HRESULTs and what they mean

| HRESULT | Hex | Meaning | Fix |
|---------|-----|---------|-----|
| `CO_E_NOTINITIALIZED` | `0x800401F0` | Thread did not call `CoInitialize` | Wrap entry point in init/uninit. |
| `RPC_E_WRONG_THREAD` | `0x8001010E` | Proxy used on a thread other than its creator | Marshal or refactor to single-threaded. |
| `RPC_E_CHANGED_MODE` | `0x80010106` | `CoInitializeEx` called with a different threading model than the previous init on the same thread | Decide on STA once and stick with it. |
| `RPC_E_SERVERCALL_RETRYLATER` | `0x8001010A` | Visio is busy (modal dialog, Save in progress) | Set `AlertResponse = 7`; back off and retry; serialise calls. |
| `0x800401FD` | — | Object not connected (Document closed mid-iteration) | Iterate over a snapshot of `doc.Pages.Count` before tearing down. |
| `VISIO_E_OBJECT_NOT_FOUND` | `0x80040000` family | Master / page / shape lookup miss | Verify name with `ItemU` (universal name) and `CellExistsU`. |

---

## 6. pywin32 makepy bootstrap

`win32com.client.constants` is empty until `makepy` has emitted the type-library stubs to `%LOCALAPPDATA%\Temp\gen_py\<py_version>\`. Without it, every `c.visOpenRO` becomes `AttributeError`. The bootstrap is a one-time per-machine, per-Visio-version step.

### 6.1 Type library identity

| Visio version | Major.Minor | Typelib GUID | Bitness |
|---------------|-------------|--------------|---------|
| Visio 2010 (14.0) | `4.0` | `{00021A98-0000-0000-C000-000000000046}` | match host (32 / 64) |
| Visio 2013 (15.0) | `4.0` | same | match host |
| Visio 2016 (16.0) | `4.0` | same | match host |
| Visio 2019 / Microsoft 365 (16.0) | `4.12` | same | match host |
| Visio 2021 / 2024 (16.0) | `4.12` | same | match host |

The GUID is stable across all 2010+ releases; only the typelib **minor version** moves. `gencache.EnsureModule(guid, lcid, major, minor)` accepts the highest installed minor and falls back to lower minors automatically — pin to `4, 12` for current builds.

### 6.2 The two bootstrap forms

| Form | Use |
|------|-----|
| CLI: `py -3.12 -m win32com.client.makepy -i "Microsoft Visio 16.0 Type Library"` | Interactive run; prints the GUID/version triple and emits the stub. Run once per developer workstation. |
| Programmatic: `gencache.EnsureModule("{00021A98-0000-0000-C000-000000000046}", 0, 4, 12)` | Production code; emits the stub on first call, no-op thereafter. Always call BEFORE the first `DispatchEx`. |

### 6.3 Canonical bootstrap snippet

```python
import os, pythoncom
import win32com.client as win32

# 1. Initialise COM on this thread.
pythoncom.CoInitializeEx(pythoncom.COINIT_APARTMENTTHREADED)

# 2. Force makepy stubs for the Microsoft Visio 16.0 Type Library.
#    Triple = (typelib GUID, lcid, major, minor).
win32.gencache.EnsureModule(
    "{00021A98-0000-0000-C000-000000000046}", 0, 4, 12)

# 3. Spawn a fresh, hidden, out-of-process Visio.
app = win32.DispatchEx("Visio.InvisibleApp")

# 4. Now constants are populated.
from win32com.client import constants as c
flags = c.visOpenRO | c.visOpenHidden | c.visOpenMacrosDisabled
```

### 6.4 Stub directory invalidation

| Trigger | Action |
|---------|--------|
| Visio upgraded (e.g. 2019 → 2021) | Delete `%LOCALAPPDATA%\Temp\gen_py\<py_version>\` and re-run bootstrap. Stale stubs reference removed enum values and crash on attribute access. |
| Python upgraded (e.g. 3.11 → 3.12) | `gen_py` is per-Python-version; the new interpreter rebuilds automatically on first `EnsureModule`. |
| `pywin32` version mismatch | `pywin32_postinstall -install` rewrites the stub format. Always run after a `pywin32` upgrade. |
| Locked-down build server (no makepy allowed) | Hard-code the constants from §4.1 of the COM ref; do NOT call `gencache`. |

### 6.5 Hard-coded constants fallback (sealed environments)

```python
# Sealed-environment fallback — embed the integer values used in the codebase.
class VisConst:
    visOpenRO              = 1
    visOpenCopy            = 2
    visOpenDocked          = 4
    visOpenHidden          = 64
    visOpenNoWorkspace     = 256
    visOpenMacrosDisabled  = 1024
    visAddStencil          = 8
    visSaveAsWS            = 1
    visSaveAsListInMRU     = 4
    visFixedFormatPDF      = 1
    visDocExIntentPrint    = 1
    visPrintAll            = 0
    visAutoConnectDirRight = 1
    visAutoConnectDirDown  = 2
    visAutoConnectDirLeft  = 3
    visAutoConnectDirUp    = 4
    visMSDefault           = 0
    visMSUS                = 1
    visMSMetric            = 2
    visAlertResponseNo     = 7
```

These values are stable across Visio 2010 → 2024; they are documented in the type library and in `research/06-python-com-automation.md §2.1`.

---

## 7. VSDX zip integrity (no nested OPC corruption)

A `.vsdx` is an ECMA-376 OPC ZIP archive. A handful of unobvious requirements separate a valid archive from a "Visio cannot open the file because it is corrupt" error:

### 7.1 ZIP framing rules

| Rule | Detail | Failure mode if violated |
|------|--------|--------------------------|
| `[Content_Types].xml` is the FIRST entry in the central directory | Stream the part out before any other; flush before the next entry | Office 2013 and several third-party OPC readers (Aspose, vsdx-py, Apache POI) fail validation. Visio desktop tolerates the violation but the file fails round-trip through any non-Microsoft consumer. |
| Use forward slashes `/` in part names | `visio/pages/page1.xml`, never `visio\pages\page1.xml` | Visio on macOS / OPC validators reject backslashes. Windows-style paths produce a "needs to be repaired" prompt. |
| Use UTF-8 for part names | No Latin-1 or system codepage | Any non-ASCII char in a part name written as Latin-1 produces an unreadable archive on every non-Windows reader. |
| ZIP entry names start with the part name as declared in `[Content_Types].xml` | The `PartName="/visio/pages/page1.xml"` string MUST match the ZIP entry name exactly (sans leading `/`) | Mismatched casing (`Visio/Pages/Page1.xml` vs `visio/pages/page1.xml`) breaks Visio on macOS and on Windows machines whose filesystem is case-sensitive (e.g. WSL2 mounts). |
| Use deflate or store; no encrypted entries | DEFLATE for everything except `vbaProject.bin` (which is already a compound document and stores well) | Encrypted ZIPs produce "this file is in a different format" errors. |
| No directory entries | OPC has no directory parts; do not write `visio/` or `visio/pages/` zero-length entries | Visio parses every entry as a part and rejects the file when `[Content_Types].xml` has no override for `visio/pages/`. |
| No `Zip64` unless the package exceeds 4 GiB | Visio 2016 and earlier cannot read `Zip64`; Visio 2019+ supports it | A `Zip64`-flagged file under 4 GiB is wasted overhead and breaks older consumers. |
| External attributes / Unix file modes are ignored | Set them to `0o644` for hygiene; nothing reads them | No failure; a noise-floor item. |
| One `[Content_Types].xml` per archive at the root | Never under `visio/` or any subdir | Visio looks at the archive root only; nested copies are silently ignored and the override mismatch corrupts the package. |

### 7.2 ContentType / part-name consistency invariants

For every Visio XML part there are FIVE places its identity must agree:

1. The ZIP entry name (`visio/pages/page1.xml`).
2. The `[Content_Types].xml` `<Override PartName=".../visio/pages/page1.xml" ContentType="..."/>`.
3. The relationship in `_rels/<source>.rels` whose `Target` resolves to that part.
4. The relationship `Id` (e.g. `rId1`) cited inside the parent XML body (e.g. `<Rel r:id="rId1"/>` in `pages.xml`).
5. The XML body's root element + namespace match the ContentType's spec.

Any one of the five drifting silently corrupts the file. `scripts/vsdx_export/opc_writer.py` enforces all five via an integrity check before flushing the archive.

### 7.3 No nested OPC ("zip-bomb" anti-pattern)

| Anti-pattern | Consequence |
|--------------|-------------|
| Embedding a `.vsdx` as a binary blob inside another `.vsdx` (e.g. as an OLE object) without re-declaring its parts in the outer `[Content_Types].xml` | Visio cannot resolve the embedded content; the OLE object renders as a grey placeholder. |
| Linking a `.vssx` stencil via a relative path that escapes the package root (`../../external.vssx`) | OPC validators reject path traversal; Visio shows the "needs to be repaired" dialog. |
| Using `image/svg+xml` ContentType for an embedded SVG without escaping the SVG's `&` / `<` / `>` characters at the OPC level | SVG is XML; Visio re-parses the embedded text and chokes on bare entities. |
| Compressing `media/image*.png` with DEFLATE | PNG is already deflated; double-compression bloats the file with no benefit. Set those entries to `STORED`. |

### 7.4 The `<RecalcDocument/>` stamp

After any out-of-process mutation of `document.xml`, write a `<RecalcDocument/>` element into the `DocumentSettings` block (Visio's "force recalc on next open" sentinel). Without it, formulas like `THEMEGUARD()` and `SETATREF()` may evaluate against stale dependency tables.

```xml
<DocumentSettings TopPage="0" DefaultTextStyle="0" DefaultLineStyle="0"
                  DefaultFillStyle="0" DefaultGuideStyle="4">
  <GlueSettings>9</GlueSettings>
  <SnapSettings>295</SnapSettings>
  <SnapExtensions>34</SnapExtensions>
  <SnapAngles/>
  <DynamicGridEnabled>1</DynamicGridEnabled>
  <ProtectStyles>0</ProtectStyles>
  <ProtectShapes>0</ProtectShapes>
  <ProtectMasters>0</ProtectMasters>
  <ProtectBkgnds>0</ProtectBkgnds>
  <RecalcDocument/>      <!-- forces full recalc on next open -->
</DocumentSettings>
```

`opc_writer.py` injects this on every fallback-path save; the COM path doesn't need it because Visio's `SaveAs` already runs a recalc before flushing.

### 7.5 Round-trip checksum invariant

For each part, the round-trip `parse → emit → parse` must produce a byte-identical second emission when run through `lxml` with `pretty_print=False, xml_declaration=True, encoding="UTF-8"`. Any non-determinism (timestamp comments, random `rId` ordering, attribute reordering) breaks `git diff` ergonomics on hand-edited Drafter pages. The fallback writer uses canonical ordering (alphabetical attribute names within each element, `<Cell>` rows in `N=` ascending order).

---

## 8. Maximum page count per document (~32k)

Visio's COM API and the `pages.xml` schema both index pages with a **16-bit signed page id** (`Page.ID`), giving an absolute ceiling of `32_767` foreground pages per document. The practical ceilings are much lower:

| Tier | Page count | Behaviour |
|------|-----------|-----------|
| Soft target | ≤ 200 | Every `vsdx_export.py` path is fully tested; opens in < 5 s on a typical workstation. |
| Tested ceiling | ≤ 2_000 | COM path verified end-to-end; fallback path verified for stencil-light drawings. Open time scales linearly to ~30 s. |
| Performance cliff | 2_000–10_000 | Visio's `pages.xml` parse becomes O(n²) on the page index lookup (legacy code path); avoid via the page-split workflow. `vsdx_export.py` warns when crossing 5_000. |
| Hard limit (Visio app) | 32_767 | Last id Visio's `Page.ID` field can hold (`Int16`). Adding the 32_768th page raises `Pages.Add` with `0x80040006 visObjectNotConnected`. |
| Hard limit (`pages.xml` schema) | 32_767 | Visio's schema enforces this with `xs:int` plus a runtime check. |
| Architect cap (visio-master) | ≤ 500 | Beyond this the diagram should be split into multiple linked drawings. `diagram_lock.page_count` validation in `update_diagram_lock.py` warns above 500 and errors above 2_000. |

### 8.1 Why the soft cap exists

- **Drafter context budget** — ppt-master tops out at ~120 SVG pages in one main-agent session; visio-master's hand-authored Visio Pages have similar context cost. Beyond 200 pages, split-mode authoring is mandatory (see §11 of the blueprint).
- **`vsdx_quality_checker.py` runtime** — the lint walks every shape; per-page ~50 ms × 500 pages = 25 s, still tolerable. Above 2_000 pages it crosses 100 s and hits CI timeout limits.
- **Visio thumbnail server** — `vsdx_preview/render_page.py` renders each page as a PNG. 500 pages × 200 ms = 100 s of rendering on first preview; cached after.
- **Live preview UX** — beyond 50 pages the per-page navigation panel turns into a scroll list; the threshold is editorial, not technical.

### 8.2 Page id collisions

`Page.ID` and `Shape.ID` share the same 16-bit space within a document but are scoped to their parent — page ids never collide with shape ids. Cross-page shape references use `Pages[<NN>]!Sheet.<id>!CellName`; the `<NN>` index is **1-based** and is `Page.Index`, not `Page.ID`. Drafter uses page **names** (universal name `NameU`) for cross-page references — they are stable under page reordering, ids are not.

---

## 9. Connector glue invariants

Connectors are 1-D shapes whose endpoint formulae encode the glue mode. The eight invariants below are enforced by `vsdx_quality_checker.py` and `references/connectors.md`. Violating any of them produces a connector that looks correct in the editor but renders wrong in print, in PDF export, or in the browser preview.

### 9.1 Endpoint cell completeness

| Invariant | Rule |
|-----------|------|
| Every shape with `<Shape ... Type="Connector">` (or `Misc.ObjType = 1`) has populated `BeginX`, `BeginY`, `EndX`, `EndY` cells | Missing any of the four → Visio renders the connector as a 0-length point at `(0,0)`. |
| Every shape with `OneD = TRUE` and a `Master` reference inheriting from `Dynamic connector` writes `BeginX`/`EndX` formulae through `GlueTo` | Hand-written `PNT(...)` formulas without going through `GlueTo` skip the page-level `Connect` collection update, so layout engines miss the connector. |
| `BegTrigger` and `EndTrigger` are owned by Visio; never hand-write | They auto-rebuild on parent-shape moves. Manual values get clobbered. |

### 9.2 Glue mode encoding

| Mode | Formula shape | When |
|------|---------------|------|
| Dynamic (shape-to-shape) | `BeginX = PNT(Sheet.<id>!PinX, Sheet.<id>!PinY)` | Default for org-charts, flowcharts, network diagrams. Auto-router picks the entry side. |
| Static (point-to-point) | `BeginX = PAR(PNT(Sheet.<id>!Connections.X<n>, Sheet.<id>!Connections.Y<n>))` | Engineering schematics, P&ID, electrical — entries are pinned. |
| Unattached | `BeginX = 1.5 in` (literal coordinate) | Floating call-outs only; quality checker warns when more than 5 % of connectors on a page are unattached. |

The quality checker reads the formula and tags each connector's mode; mixing dynamic and static glue on the same page is allowed but flagged in `verify-diagrams.md`.

### 9.3 `Connect` collection consistency

For every glued endpoint there is exactly one entry in the page-level `Page.Connects` collection:

| Property | Constraint |
|----------|------------|
| `FromSheet` | The connector shape (Type="Connector") |
| `FromCell` | `BeginX` (FromPart=`visBegin=9`) or `EndX` (FromPart=`visEnd=12`) — never `BeginY`/`EndY` (the Y cells are derivative) |
| `FromPart` | `9` or `12`; `-1` (`visConnectFromError`) means the formula no longer resolves and the connector is broken |
| `ToSheet` | A 2-D shape on the same page (cross-page glue is forbidden — Visio supports it but no major exporter round-trips it) |
| `ToCell` | `PinX` for dynamic glue, `Connections.X<n>` for static glue, `Width*0.5` formulae for centroid glue |
| `ToPart` | `visConnectionPoint` (100 + row), `visWholeShape` (3), `visGuideX` (1), `visGuideY` (4), `visGuideIntersect` (2), or `visToAngle` (7) |

`vsdx_quality_checker.py` walks `Page.Connects` (in COM mode) or `pages.xml` `<Connect/>` elements (in fallback mode) and asserts:

1. Every connector has exactly two `Connect` rows (one per endpoint), or fewer if explicitly tagged `unattached` in `diagram_lock.page_diagrams.<P##>.connectors`.
2. No `Connect` row references a `ToSheet` that doesn't exist on the page.
3. No `Connect` row has `FromPart = visConnectFromError (-1)`.

### 9.4 Routing invariants

| Cell | Page vs Shape | Default | Constraint |
|------|--------------|---------|------------|
| `RouteStyle` (page-level: `PageLayout.DynamicConnectorRouteStyle`) | Page | `1` (`visLORouteRightAngle`) | Set ONCE per page from `diagram_lock.connectors.routing`; do not vary per-page within one drawing unless `connectors.routing = mixed`. |
| `ShapeRouteStyle` | Shape | `0` (inherit page) | The only legal Drafter override; values come from `VisCellVals` (table below). |
| `ConFixedCode` | Shape | `0` | `0` = router controls; `1` = user reroutes only; `2` = never reroute; `6` = never reroute and never split. |
| `ConLineRouteExt` | Shape | `0` | `0` = default, `1` = straight, `2` = curved. |
| `WalkPreference` | Shape | `0` | `0` = horiz first, `1` = vert first. |
| `ConLineJumpStyle` | Shape | `0` | `0`= page default, `1`=arc, `2`=gap, `3`=square, `4`=sides 2, `5`=none. |
| `ConLineJumpCode` | Shape | `0` | `0`=page default, `1`=always jump, `2`=never jump, `3`=other connector jumps. |
| `LineJumpFactorX` / `LineJumpFactorY` | Page | `2/3` | Multiplier on connector line-weight; do not exceed `2.0`. |

### 9.5 `VisCellVals` route-style enum (closed)

| Constant | Value | Use |
|----------|-------|-----|
| `visLORouteDefault` | `0` | Inherit from page |
| `visLORouteRightAngle` | `1` | Default for flowcharts |
| `visLORouteStraight` | `2` | Engineering schematics |
| `visLORouteOrgChartNS` | `4` | Org charts top-down |
| `visLORouteOrgChartEW` | `5` | Org charts left-to-right |
| `visLORouteOrgChartNSCompact` | `6` | Tight org charts top-down |
| `visLORouteOrgChartEWCompact` | `7` | Tight org charts left-to-right |
| `visLORouteFlowchartNS` | `8` | Flowchart top-down |
| `visLORouteFlowchartEW` | `9` | Flowchart left-to-right |
| `visLORouteTreeNS` | `10` | Tree top-down |
| `visLORouteTreeEW` | `11` | Tree left-to-right |
| `visLORouteNetwork` | `12` | Network meshes |
| `visLORouteCenterToCenter` | `16` | Straight connectors centroid-to-centroid |
| `visLORouteSimpleNS` | `17` | Simple north-south |
| `visLORouteSimpleEW` | `18` | Simple east-west |
| `visLORouteSimpleNSCenter` | `25` | Centred simple NS |
| `visLORouteSimpleEWCenter` | `26` | Centred simple EW |
| `visLORouteSimpleVertTree` | `27` | Vertical tree |
| `visLORouteSimpleHorzTree` | `28` | Horizontal tree |

Anything outside this enum is rejected by Visio with a recalc warning.

### 9.6 Glue against connection points (static glue)

A target connection point is identified by its **row index** in `visSectionConnectionPts` (section `7`). Cells on the row:

| Column | Cell | Default formula |
|--------|------|-----------------|
| 0 | `Connections.X<n>` | `Width*0.5` |
| 1 | `Connections.Y<n>` | `Height*0.5` |
| 2 | `Connections.DirX<n>` | `0` |
| 3 | `Connections.DirY<n>` | `0` |
| 4 | `Connections.Type<n>` | `0` (inward), `1` (outward), `2` (in/out) |
| 5 | `Connections.Name<n>` | optional row label |

Static glue formula: `BeginX = PAR(PNT(Sheet.<id>!Connections.X<n>, Sheet.<id>!Connections.Y<n>))`. The `PAR()` wrapper marks the formula as "auto-glue handled" so Visio won't blow it away on the next recalc.

### 9.7 Glue invariants for the fallback writer

The fallback path (`vsdx` lib + raw OPC) cannot run Visio's routing engine. To preserve correct visuals on first open:

| Step | Detail |
|------|--------|
| Pre-route the connector on author time | `assemble_containers.py` runs a layout pass (default: dagre via Node sidecar; configurable to ELK) and bakes the polyline geometry into a `Geometry1` section of the connector shape. |
| Stamp `<RecalcDocument/>` | Forces Visio to re-evaluate `BeginX`/`EndX` on first open so the cached polyline is replaced by the live route once the user opens the file. |
| Mark `ConFixedCode = 0` (router-controlled) | So Visio rebuilds the route on first edit. |
| Set `Misc.ObjType = 1` (`oneD = True`) | Required for the connector to be recognised as 1-D and eligible for routing. |

### 9.8 Banned glue patterns

| Banned | Reason |
|--------|--------|
| Cross-page glue (`Sheet.<id>` references a shape on another page) | Visio supports it but no exporter round-trips it; OPC validators flag the cross-page reference. |
| Glue to a guide (`ToPart = visGuideX/Y`) without an explicit guide shape on the page | Visio renders an orphaned guide; quality checker errors. |
| Glue to `Width*0.5, Height*0.5` literal expressions | Legal but defeats the `Connect` collection — use `PinX`/`PinY` instead so `Page.Connects` is populated. |
| `GlueTo` from a 2-D shape onto another 2-D shape | Glue is a 1-D-only concept. The COM call silently no-ops; `vsdx_quality_checker.py` errors. |
| Static glue formula without `PAR()` wrapper | Auto-glue marker is missing; Visio recomputes on every recalc and may flip the endpoint. |

---

## 10. Theme tokens must come from `theme1.xml`, not literal hex

Visio honours OOXML's DrawingML theme model. A drawing has one theme part (`visio/theme/theme1.xml`) containing six color slots, two font scheme slots, and three effect lists. Drafter writes shape colors as **theme references** (`THEMEGUARD()` formulae); Stylist writes the actual HEX into `theme1.xml`. Mixing these layers is the source of the most common visio-master bug: a deck-wide color change that fails to update half the shapes because they used inline HEX.

### 10.1 Theme color slots (closed enum)

The DrawingML `a:clrScheme` element has exactly twelve color slots; Visio's `THEMEVAL()` and `THEMECOLOR()` reference them by name or 0-based index.

| `a:clrScheme` child | Index | Visio mnemonic | Lock field |
|---------------------|-------|----------------|------------|
| `a:dk1` | 0 | `text` | `colors.text` |
| `a:lt1` | 1 | `bg` | `colors.bg` |
| `a:dk2` | 2 | `text_secondary` | `colors.text_secondary` |
| `a:lt2` | 3 | `surface` | `colors.surface` |
| `a:accent1` | 4 | `primary` | `colors.primary` |
| `a:accent2` | 5 | `accent` | `colors.accent` |
| `a:accent3` | 6 | `secondary_accent` | `colors.secondary_accent` |
| `a:accent4` | 7 | `accent_3` | `colors.accent_3` (optional) |
| `a:accent5` | 8 | `accent_4` | `colors.accent_4` (optional) |
| `a:accent6` | 9 | `accent_5` | `colors.accent_5` (optional) |
| `a:hlink` | 10 | `link` | `colors.link` |
| `a:folHlink` | 11 | `link_visited` | `colors.link_visited` |

`colors.border`, `colors.grid`, `colors.scrim` from `diagram_lock.colors` are NOT in `a:clrScheme` — they live as Visio-extension theme variables under `<Variation>` and are referenced via `User.theme.<name>` cells on the document sheet. Stylist's `apply_theme.py` writes both layers atomically.

### 10.2 `THEMEGUARD()` and `THEMEVAL()` formulae

| Formula | Use | Example |
|---------|-----|---------|
| `THEMEVAL()` | Resolve to the current theme value for THIS cell. Engine knows which slot to use based on cell name. | `FillForegnd = THEMEVAL()` resolves to the theme's primary fill. |
| `THEMEVAL("<token>")` | Resolve a specific token by name | `FillForegnd = THEMEVAL("AccentColor1")` |
| `THEMEGUARD(<expr>)` | Mark the expression as theme-protected. User-driven theme changes will rewrite the formula; manual edits in the UI go to a `SETATREF` shadow cell. | `FillForegnd = THEMEGUARD(THEMEVAL())` |
| `THEMECOLOR(<index>)` | Return the HEX for slot index `<0..11>` | `Char.Color = THEMECOLOR(0)` (text) |
| `BLEND(c1, c2, t)` | Linear blend; useful for hover/disabled states | `BLEND(THEMECOLOR(4), THEMECOLOR(1), 0.5)` |
| `DARKEN(c, factor)` / `LIGHTEN(c, factor)` | Tint variants for hover / press states | `DARKEN(THEMECOLOR(4), 0.2)` |

### 10.3 The "no literal HEX in geometry" rule

Drafter MUST emit theme references for any color that maps onto a `colors.*` lock token. Inline HEX is permitted ONLY for:

| Allowed inline HEX | Justification |
|---------------------|---------------|
| Colors declared as `colors.exempt[]` in `diagram_lock.md` | Architect explicitly tagged the value as theme-immune. |
| Brand-locked logos/icons whose HEX is part of the brand identity | A red Coca-Cola wordmark is not subject to dark-mode theming. |
| Single-use accent colors used for one specific shape with `Misc.Comment = "theme-immune"` | Quality checker honours the marker on a per-shape basis. |
| Default fallback inside imported third-party stencils | Stylist's `apply_theme.py` rewrites these on import; until rewritten, they pass lint as warnings, not errors. |

`vsdx_quality_checker.py` errors on:

- Any `<Cell N="LineColor" V="..." F="..."/>` whose `F` attribute is a literal `RGB(...)` and the cell's parent shape is NOT in the exempt list.
- Any `<Cell N="FillForegnd" V="..." F="..."/>` whose `F` is `THEMEVAL()` but `theme1.xml` does not define the matching slot.
- Any `<Cell N="Char.Color" V="..." F="..."/>` whose `F` is a literal HEX when `colors.text` is locked.

### 10.4 Theme part XML skeleton

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
         name="visio-stock">
  <a:themeElements>
    <a:clrScheme name="visio-stock">
      <a:dk1>      <a:srgbClr val="1D1D1F"/></a:dk1>
      <a:lt1>      <a:srgbClr val="FFFFFF"/></a:lt1>
      <a:dk2>      <a:srgbClr val="6E6E73"/></a:dk2>
      <a:lt2>      <a:srgbClr val="F5F5F7"/></a:lt2>
      <a:accent1>  <a:srgbClr val="0071E3"/></a:accent1>
      <a:accent2>  <a:srgbClr val="FF9F0A"/></a:accent2>
      <a:accent3>  <a:srgbClr val="30D158"/></a:accent3>
      <a:accent4>  <a:srgbClr val="BF5AF2"/></a:accent4>
      <a:accent5>  <a:srgbClr val="FF375F"/></a:accent5>
      <a:accent6>  <a:srgbClr val="64D2FF"/></a:accent6>
      <a:hlink>    <a:srgbClr val="0071E3"/></a:hlink>
      <a:folHlink> <a:srgbClr val="5856D6"/></a:folHlink>
    </a:clrScheme>
    <a:fontScheme name="visio-stock">
      <a:majorFont>
        <a:latin typeface="Inter"/>
        <a:ea typeface="Microsoft YaHei"/>
        <a:cs typeface=""/>
      </a:majorFont>
      <a:minorFont>
        <a:latin typeface="Inter"/>
        <a:ea typeface="Microsoft YaHei"/>
        <a:cs typeface=""/>
      </a:minorFont>
    </a:fontScheme>
    <a:fmtScheme name="visio-stock">
      <a:fillStyleLst><!-- 3 entries --></a:fillStyleLst>
      <a:lnStyleLst><!-- 3 entries --></a:lnStyleLst>
      <a:effectStyleLst><!-- 3 entries --></a:effectStyleLst>
      <a:bgFillStyleLst><!-- 3 entries --></a:bgFillStyleLst>
    </a:fmtScheme>
  </a:themeElements>
</a:theme>
```

The `a:fillStyleLst`, `a:lnStyleLst`, `a:effectStyleLst`, `a:bgFillStyleLst` each MUST have exactly 3 child entries (subtle / moderate / intense). Visio crashes on theme parts with a different count.

### 10.5 Font fallback in the theme

| Slot | Latin | EA (East Asian) | CS (Complex Script) | Drafter source |
|------|-------|-----------------|---------------------|----------------|
| `a:majorFont` (titles) | `typography.title.latin` | `typography.title.cjk` | `""` | `diagram_lock.typography.title` |
| `a:minorFont` (body) | `typography.body.latin` | `typography.body.cjk` | `""` | `diagram_lock.typography.body` |

Latin and EA must both resolve to **system-installed** font families. visio-master's safe roster is documented in `references/canvas-formats.md §Fonts`; the default safe set is `Inter` / `Segoe UI` / `Microsoft YaHei` / `SimSun` / `Source Han Sans` / `Arial` / `Times New Roman` / `Consolas`. Custom font families require a separate `font/font1.fntdata` part and a custom font-embedding workflow (out-of-scope for visio-master v1).

### 10.6 Color variants

A theme can ship multiple color variants under `a:extLst` → `<thm15:themeFamily/>` extensions. Visio's "Variants" gallery lists them. visio-master's stock themes ship 4 variants (`primary`, `cool`, `warm`, `neutral`); custom themes ship 1+. The active variant is set on the document sheet's `User.themeVariant.Value` cell — `0..3` indices map to the four variants.

### 10.7 Forbidden theme overrides

| Forbidden | Why |
|-----------|-----|
| Naming a theme `theme0.xml` | Microsoft reserves `theme0` for the application-default; Visio rejects it. |
| Multiple `a:clrScheme` children under `a:themeElements` | OOXML requires exactly one. Visio crashes on validation. |
| Empty `a:srgbClr val=""` | Use a 6-digit HEX without `#` (e.g. `1D1D1F`); empty values default to black and break dark themes. |
| `a:sysClr val="windowText"` instead of `a:srgbClr` | System colors don't round-trip through PDF / SVG / browser preview; force explicit HEX. |
| Mixing `a:scrgbClr` (sRGB float) with `a:srgbClr` (hex) | Use `a:srgbClr` only — Visio's color picker writes hex. |

---

## 11. ID and naming hygiene

### 11.1 Visio object IDs

| Surface | ID space | Constraint |
|---------|----------|------------|
| `Shape.ID` | 16-bit unsigned per page | Auto-assigned by Visio; do not write directly in fallback XML. |
| `Shape.NameU` | UTF-8 string | Universal, locale-invariant. Drafter writes `NameU`; never `Name` (which is locale-dependent). |
| `Master.NameU` | UTF-8 string | Same — `NameU` only. |
| `Page.NameU` | UTF-8 string | Cross-page references use this; ids change on reorder. |
| Document `UniqueID` | GUID | Generated by Visio on first save; preserve on round-trip. |
| Relationship `Id` | `rId<n>` | Sequential within a `.rels` part; `<n>` starts at 1. |

### 11.2 Reserved name prefixes

| Prefix | Owner | Reason |
|--------|-------|--------|
| `User.vm_*` | `update_diagram_lock.py` | Internal markers used by diagram_lock propagation. |
| `Prop.vm_*` | Stylist | Data-graphic binding metadata. |
| `Sheet.<id>!` | Visio runtime | Cross-shape reference syntax; never a name on its own. |
| `Theme.*` | Stylist | Theme tokens; only `apply_theme.py` writes these. |

### 11.3 Banned characters in `NameU`

`NameU` strings must match `^[A-Za-z][A-Za-z0-9_.-]{0,63}$` for stable cross-platform behaviour. Specifically forbidden:

- Spaces (use `_`)
- Backticks, quotes (`'`, `"`, `` ` ``)
- ShapeSheet operators: `!`, `&`, `+`, `-`, `*`, `/`, `=`, `<`, `>`
- Path separators: `/`, `\`
- Whitespace characters other than space (already banned)
- CJK characters in `NameU` — use the localised `Name` for CJK, and a transliterated ASCII `NameU`.

---

## 12. Text content rules

### 12.1 Character set

| Allowed | Forbidden |
|---------|-----------|
| UTF-8 encoded characters | UTF-16 BOM in any part |
| Raw Unicode (`—`, `→`, `©`, `®`, `«`, `»`, `…`) | HTML named entities (`&mdash;`, `&rarr;`, `&copy;`, `&hellip;`) |
| XML entities for the five reserved chars: `&amp;`, `&lt;`, `&gt;`, `&quot;`, `&apos;` | Bare `&`, `<`, `>` in `<Text/>` element content |
| Numeric character refs `&#160;` | Discouraged — prefer raw Unicode for clarity |

`vsdx_quality_checker.py` errors on any HTML named entity inside a `<Text/>` element. The lint runs against `pages/*.vsdx-page.xml` source-of-truth fragments before finalisation.

### 12.2 Text run encoding

Per-run formatting in Visio is encoded as a sequence of `<cp>...</cp>` (Character Properties) and `<pp>...</pp>` (Paragraph Properties) elements interleaved with text. Each `<cp>` references a row in the `Character` section by index; each `<pp>` references a row in the `Paragraph` section.

```xml
<Text>
  <cp IX="0"/>Header text
  <cp IX="1"/> with accent run
  <cp IX="0"/> back to default.
</Text>
```

The corresponding sections live on the same `<Shape>`:

```xml
<Section N="Character">
  <Row IX="0"><Cell N="Color" V="0" F="THEMEGUARD(THEMECOLOR(0))"/></Row>
  <Row IX="1"><Cell N="Color" V="1" F="THEMEGUARD(THEMECOLOR(4))"/></Row>
</Section>
```

### 12.3 Forbidden text patterns

| Pattern | Why |
|---------|-----|
| Multiple consecutive `<cp/>` with the same `IX` | Wasteful and breaks Visio's text-run merger; the lint warns. |
| Text fields (`<fld/>`) referencing undefined field types | Visio shows `#REF!`; lint errors. |
| `<Text/>` content longer than 32_768 characters | Visio truncates silently; lint warns. |
| Trailing whitespace on every line | Visible in PDF export and breaks alignment; lint warns. |

---

## 13. Image and media constraints

### 13.1 Allowed image formats

| Format | ContentType | Use |
|--------|-------------|-----|
| PNG | `image/png` | Default for raster — lossless, alpha supported. |
| JPEG | `image/jpeg` | Photos only; never for screenshots or diagrams (lossy artifacts). |
| EMF | `image/x-emf` | Vector — preferred for icons that don't have a Visio master. |
| WMF | `image/x-wmf` | Legacy vector; convert to EMF on import. |
| SVG | `image/svg+xml` | Allowed but converted to EMF at finalisation by `embed_images.py` (Visio's SVG renderer is unreliable across versions). |
| GIF | (banned) | No animation support; convert first frame to PNG. |
| BMP | (banned) | Bloats package; convert to PNG. |
| HEIC, AVIF, WEBP | (banned) | Visio 2016/2019 cannot decode; convert to PNG. |

### 13.2 Image part placement

| Part path | When |
|-----------|------|
| `visio/media/image<n>.<ext>` | Page-scoped image; relationship from `pages/_rels/page<n>.xml.rels` |
| `visio/media/master<m>_image<n>.<ext>` | Master-scoped image (used in stencil-derived shapes) |

### 13.3 Image sizing constraints

| Constraint | Threshold | Reason |
|------------|-----------|--------|
| Max dimension | 8_000 × 8_000 px | Visio renderer slows quadratically; fallback path memory-OOMs. |
| Recommended max | 2_000 × 2_000 px (raster) | Balances quality and file size. |
| Min raster DPI for print | 200 dpi at output size | Below 200 dpi prints blurry. |
| Total media weight | ≤ 50 MB per `.vsdx` | Above 50 MB, OneDrive Sync, SharePoint, and email attachments choke. |

`embed_images.py` warns when crossing any threshold.

---

## 14. Layer hygiene

### 14.1 Layer rows on PageSheet

Each page has a `Layer` section on its PageSheet whose rows define the layers visible on that page. Cells per row:

| Cell | Type | Default | Purpose |
|------|------|---------|---------|
| `Layer.Name` | string | `""` | Localised layer name |
| `Layer.NameUniv` | string | `""` | Universal name |
| `Layer.Color` | int | `255` (theme-default) | Layer-specific override color |
| `Layer.ColorTrans` | percent | `0%` | Layer transparency |
| `Layer.Visible` | bool | `TRUE` | Show on page |
| `Layer.Print` | bool | `TRUE` | Include in print/PDF |
| `Layer.Active` | bool | `FALSE` | Default-active layer for new shapes |
| `Layer.Lock` | bool | `FALSE` | Prevent edits |
| `Layer.Snap` | bool | `TRUE` | Snap-target layer |
| `Layer.Glue` | bool | `TRUE` | Glue-target layer |
| `Layer.Status` | int | `0` | Reserved |

### 14.2 Layer assignment on shapes

`Misc.LayerMember = "0;3;7"` — semicolon-delimited 0-based **indices** into the layer table on this page. NOT names — adding/removing layers shifts indices and silently corrupts assignments.

`update_diagram_lock.py` re-renumbers `LayerMember` cells when the layer set changes. Hand-edits that bypass this script produce shapes that vanish from "their" layer when a new layer is added higher in the table.

### 14.3 Standard layer set

visio-master's standard layer set per page (assigned by Stylist, not Drafter):

| Index | Name | Purpose |
|-------|------|---------|
| 0 | `frame` | Page borders, title block, page numbers |
| 1 | `chrome` | Decorative accents, watermarks, dividers |
| 2 | `content` | Primary diagram shapes |
| 3 | `connectors` | All 1-D connector shapes |
| 4 | `annotations` | Callouts, comments, sticky notes |
| 5 | `data-graphics` | Data-graphic overlays (Stylist-applied) |
| 6 | `guides` | Layout guides (always `Visible=FALSE, Print=FALSE`) |

Drafter writes `Misc.LayerMember = "2"` for content shapes and `"3"` for connectors. Stylist may change assignments during the Step 6.5 layer pass.

---

## 15. Source citation summary

| Section | Primary inputs |
|---------|----------------|
| §1 File naming, units, canvas | Blueprint §4 confirmation 1; `research/03-vsdx-file-format.md §1`; `research/02-shapesheet-cells-functions.md §3.2` |
| §2 Namespaces and content types | `research/03-vsdx-file-format.md §2, §3` |
| §3 ShapeSheet hands-off cells | `research/02-shapesheet-cells-functions.md §2`; `research/01-com-object-model.md §6` |
| §4 Banned API patterns | `research/06-python-com-automation.md §1, §3, §6`; `research/01-com-object-model.md §13, §15` |
| §5 Threading | `research/06-python-com-automation.md §1, §11`; `research/01-com-object-model.md §15` |
| §6 makepy bootstrap | `research/06-python-com-automation.md §1.4, §2.1` |
| §7 ZIP integrity | `research/03-vsdx-file-format.md §1.1, §2, §3` |
| §8 Page count | `research/01-com-object-model.md §4`; blueprint §4 confirmation 2 |
| §9 Connector glue | `research/18-connectors-routing.md §1–§5`; `research/01-com-object-model.md §8` |
| §10 Theme tokens | `research/03-vsdx-file-format.md §2`; blueprint §4 confirmation 5 |
| §11 ID hygiene | `research/01-com-object-model.md §3, §4, §5` |
| §12 Text rules | `research/02-shapesheet-cells-functions.md §2.6` |
| §13 Image rules | `research/03-vsdx-file-format.md §2.1` |
| §14 Layer hygiene | `research/01-com-object-model.md §10`; `research/02-shapesheet-cells-functions.md §2.10` |

---

## Sources

Primary research files consulted while authoring this document:

1. `D:/Pe/Project/python/workProject/visio-master—builder/_BLUEPRINT.md` — architectural blueprint, role definitions, Eight Confirmations, file inventory, discipline rules.
2. `D:/Pe/Project/python/workProject/visio-master—builder/research/01-com-object-model.md` — Visio COM object model, `Application` / `InvisibleApp` ProgIDs, threading rules, `Documents.OpenEx` flags, event surface.
3. `D:/Pe/Project/python/workProject/visio-master—builder/research/02-shapesheet-cells-functions.md` — ShapeSheet section taxonomy, cell catalogue, formula language, units, `THEMEGUARD` / `THEMEVAL` / `GUARD` / `SETF` semantics.
4. `D:/Pe/Project/python/workProject/visio-master—builder/research/03-vsdx-file-format.md` — OPC package layout, `[Content_Types].xml`, relationship URIs, namespace versions, ZIP framing rules.
5. `D:/Pe/Project/python/workProject/visio-master—builder/research/06-python-com-automation.md` — pywin32 / `gencache.EnsureDispatch` / `DispatchEx` patterns, makepy bootstrap, threading, error handling.
6. `D:/Pe/Project/python/workProject/visio-master—builder/research/18-connectors-routing.md` — connector master inventory, glue modes, `Connect` collection, `VisCellVals` route style enum, line-jump cells.
7. `D:/Pe/Project/python/workProject/visio-master—builder/research/27-events-add-in-architecture.md` — event model, `EventList` / `AddAdvise` / `WithEvents`, `visEvt*` event codes.

Pattern reference (style only, not content): `D:/Pe/Project/python/workProject/.agents/skills/ppt-master/references/shared-standards.md`.

