# Visio COM Quick Reference

> One-line lookup tables for the ~80 most-used members of the Visio Automation
> object model. Covers `Application`, `Document`, `Page`, `Master`, `Shape`,
> `Shapes`, `Selection`, `Cell`, `Window`, `Connect`, and `Event` plus the
> top constants you need to call them. Every entry names the exact API,
> ProgID, ShapeSheet cell, or `vis*` enum value -- no vague descriptions.
>
> Bindings: VBA / VSTO PIA `Microsoft.Office.Interop.Visio` /
> Python `win32com.client` / PowerShell `New-Object -ComObject`.

---

## 0. ProgIDs, CLSIDs, typelib

| Symbol | Value |
|---|---|
| ProgID (visible) | `Visio.Application` |
| ProgID (headless) | `Visio.InvisibleApp` |
| ProgID (document factory) | `Visio.Drawing` |
| CLSID `Visio.Application` | `{00021A20-0000-0000-C000-000000000046}` |
| CLSID `Visio.InvisibleApp` | `{00021A24-0000-0000-C000-000000000046}` |
| CLSID `Visio.Drawing` | `{00021A21-0000-0000-C000-000000000046}` |
| Typelib GUID | `{00021A98-0000-0000-C000-000000000046}` |
| Typelib (Visio 2019/2021/365) | major `4`, minor `12` |
| Typelib (Visio 2010/2013/2016) | major `4`, minor `0` |
| PIA assembly | `Microsoft.Office.Interop.Visio.dll` |
| PIA strong name | `PublicKeyToken=71e9bce111e9429c` |
| PIA version (2013) | `15.0.0.0` |
| PIA version (2016+) | `16.0.0.0` |
| Apartment | STA (`ThreadingModel=Apartment`) |
| Ribbon ID (drawing window) | `Microsoft.Visio.Drawing` |
| Ribbon ID (print preview) | `Microsoft.Visio.Print.Preview` |

---

## 1. Application object -- top members

The Visio `Application` is the root entry point obtained from
`new Visio.Application()`, `CreateObject("Visio.Application")`,
`Dispatch("Visio.InvisibleApp")`, `New-Object -ComObject Visio.InvisibleApp`,
or VSTO `Globals.ThisAddIn.Application`.

| # | Member | Returns | Use |
|---|---|---|---|
| 1 | `Application.Documents` | `Documents` collection | Root of every open document; iterate, `Add`, `Open`, `OpenEx`. |
| 2 | `Application.ActiveDocument` | `Document` | Document currently in the foreground window; `Nothing` if none. |
| 3 | `Application.ActivePage` | `Page` | Page of the active window; `Nothing` for stencil-only sessions. |
| 4 | `Application.ActiveWindow` | `Window` | Foreground window; provides `Selection` and zoom control. |
| 5 | `Application.Windows` | `Windows` collection | All open windows (drawing, stencil, anchor bar, ShapeSheet). |
| 6 | `Application.Visible` | `Boolean` | `True` to show the main window; default `False` on `InvisibleApp`. |
| 7 | `Application.Quit` | method | Shuts down Visio; pair with `Marshal.ReleaseComObject` in OOP code. |
| 8 | `Application.AlertResponse` | `Long` | Set to `7` (No) before `Quit` to suppress save prompts in batch jobs. |
| 9 | `Application.ScreenUpdating` | `Long` | `0` to suspend redraw, `-1` to resume; speeds up batch builds. |
| 10 | `Application.EventsEnabled` | `Long` | `0` to suspend event firing during a batch, `-1` to restore. |
| 11 | `Application.UndoEnabled` | `Boolean` | `False` to skip undo recording (memory + speed win). |
| 12 | `Application.DeferRecalc` | `Long` | `1` to defer ShapeSheet recalc until reset to `0`. |
| 13 | `Application.BeginUndoScope(name)` | `Long` | Opens a named transaction; returns scopeID for `EndUndoScope`. |
| 14 | `Application.EndUndoScope(scopeID, fCommit)` | method | Commits (`True`) or rolls back (`False`) the undo transaction. |
| 15 | `Application.Settings` | `Settings` | Per-user export/print defaults (e.g. PNG DPI, PDF intent). |
| 16 | `Application.Addons` | `Addons` collection | Visio add-on (`.vsl`/COM) registry; call `Addons("Name").Run`. |
| 17 | `Application.EventList.AddAdvise(code, sink, "", desc)` | `Event` | Programmatic event subscription; `code` is `VisEventCodes` value. |
| 18 | `Application.SelectionChanged += handler` | event | PIA delegate event; fires on every selection change. |
| 19 | `Application.ShapeAdded += handler` | event | Fires when any `Page.Shapes.Add`/`Drop` succeeds. |
| 20 | `Application.BeforeDocumentClose += handler` | event | Last chance to read a `Document` before teardown. |

Application call patterns:

```vb
' VBA: silent batch wrapper
Application.AlertResponse = 7
Application.ScreenUpdating = False
Application.EventsEnabled = False
Application.DeferRecalc = 1
' ... bulk Drop / SetFormulas ...
Application.DeferRecalc = 0
Application.EventsEnabled = True
Application.ScreenUpdating = True
```

```python
# pywin32: undo scope around a batch edit
scope = app.BeginUndoScope("AutoLayout")
try:
    page.Layout()
    app.EndUndoScope(scope, True)
except Exception:
    app.EndUndoScope(scope, False)
    raise
```

---

## 2. Documents collection and Document object

`Documents` is `Application.Documents`. Each child is a `Document` (drawing,
stencil, template). Stencils opened with `visOpenRO + visOpenDocked` are
treated as masters libraries; macro-enabled documents (`.vsdm`/`.vstm`) need
`visOpenMacrosDisabled` for hardened batch jobs.

| # | Member | Returns | Use |
|---|---|---|---|
| 21 | `Documents.Add(template)` | `Document` | New drawing; pass `""` for blank or path to `.vstx`/`.vst`. |
| 22 | `Documents.Open(path)` | `Document` | Open for editing; honors macro auto-run. |
| 23 | `Documents.OpenEx(path, flags)` | `Document` | Flag-controlled open; bitwise OR of `visOpen*` constants. |
| 24 | `Documents.AddEx(template, measSys, flags)` | `Document` | New doc with measurement system + open flags. |
| 25 | `Document.Pages` | `Pages` | Page collection of this document. |
| 26 | `Document.Masters` | `Masters` | Master collection (Document Stencil for drawings). |
| 27 | `Document.Styles` | `Styles` | Named styles (`Normal`, `Connector`, custom). |
| 28 | `Document.SaveAs(path)` | method | Save under new path; format inferred from extension. |
| 29 | `Document.SaveAsEx(path, flags)` | method | `visSaveAsWS` to include workspace, `visSaveAsListInMRU` for recents. |
| 30 | `Document.ExportAsFixedFormat(fmt, path, intent, range, from, to, ...)` | method | PDF/XPS export (`visFixedFormatPDF=1`, `visFixedFormatXPS=2`). |
| 31 | `Document.Close` | method | Close without prompting if `Saved=True` or `AlertResponse=7`. |
| 32 | `Document.Saved` | `Boolean` | Set `True` to suppress Save prompt at close. |
| 33 | `Document.DocumentSheet` | `Shape` | The document-level ShapeSheet (cells like `EventDocOpen`). |

### 2.1 `Documents.OpenEx` flags (`VisOpenSaveArgs`)

| Constant | Value | Effect |
|---|---|---|
| `visOpenRW` | `0` | Read/write (default). |
| `visOpenRO` | `2` | Read-only; required for stencils used as masters source. |
| `visOpenCopy` | `4` | Open as untitled copy (Document1-style); `SaveAs` mandatory. |
| `visOpenMinimized` | `16` | Open minimized in MDI. |
| `visOpenHidden` | `64` | No visible window; common for headless template loads. |
| `visOpenMacrosDisabled` | `128` | Skip auto-run macros; mandatory for untrusted input. |
| `visOpenNoWorkspace` | `256` | Ignore stored workspace (windows / zoom). |
| `visOpenDocked` | `512` | Open as docked stencil. |

### 2.2 `Document.SaveAs` format inference by extension

| Extension | Format | Macros |
|---|---|---|
| `.vsdx` | OPC drawing | stripped |
| `.vsdm` | OPC drawing macro-enabled | preserved |
| `.vstx` | OPC template | stripped |
| `.vstm` | OPC template macro-enabled | preserved |
| `.vssx` | OPC stencil | stripped |
| `.vssm` | OPC stencil macro-enabled | preserved |
| `.vsd` | Visio 2003-2010 binary | per source |
| `.vdx` | XML drawing (2010) | n/a |
| `.svg` | Scalable Vector Graphics | n/a |

### 2.3 `ExportAsFixedFormat` positional arguments

```
Document.ExportAsFixedFormat(
    FixedFormat,           ' visFixedFormatPDF=1 / visFixedFormatXPS=2
    OutputFileName,
    Intent,                ' visDocExIntentPrint=1 / visDocExIntentScreen=2
    PrintRange,            ' visPrintAll=0, visPrintCurrentPage=1, visPrintFromTo=2
    FromPage, ToPage,
    ColorAsBlack,          ' Boolean
    IncludeBackground,     ' Boolean
    IncludeDocumentProperties,
    IncludeStructureTags,  ' PDF/UA tags
    IsoCompliant,          ' PDF/A-1b
    MarkupID, OpenAfterExport)
```

---

## 3. Pages collection and Page object

`Page` represents one drawing surface inside a `Document`. Page geometry,
layout, and routing parameters live on the `PageSheet` (the page-level
ShapeSheet). All drop and shape-creation methods are on `Page`.

| # | Member | Returns | Use |
|---|---|---|---|
| 34 | `Pages.Item(index)` | `Page` | 1-based index access. |
| 35 | `Pages.ItemU(name)` | `Page` | Lookup by universal (locale-invariant) name. |
| 36 | `Pages.Add` | `Page` | Append a foreground page using current page settings. |
| 37 | `Page.Shapes` | `Shapes` | Top-level shapes on this page. |
| 38 | `Page.PageSheet` | `Shape` | Page-level ShapeSheet (cells `PageWidth`, `PageHeight`, `PageScale`, `PlaceStyle`, `RouteStyle`, `AvenueSizeX`). |
| 39 | `Page.NameU` | `String` | Universal (locale-invariant) page name. |
| 40 | `Page.Background` | `Boolean` | `True` for background pages. |
| 41 | `Page.Drop(master, x, y)` | `Shape` | Place one master at `(x,y)` in page units. |
| 42 | `Page.DropMany(mastersArr, xyArr)` | `Long()` | Batch drop; returns ShapeIDs (`Page.Shapes.ItemFromID`). |
| 43 | `Page.DropConnected(master, srcShape, dir, connector)` | `Shape` | Drops + glues; `dir` is `visAutoConnectDir*`. |
| 44 | `Page.DrawRectangle(x1, y1, x2, y2)` | `Shape` | Primitive rectangle, returns the new 2-D shape. |
| 45 | `Page.DrawLine(x1, y1, x2, y2)` | `Shape` | Primitive 1-D line shape. |
| 46 | `Page.DrawOval(x1, y1, x2, y2)` | `Shape` | Primitive ellipse. |
| 47 | `Page.Layout` | method | Auto-route + reposition using `PlaceStyle`/`RouteStyle` from PageSheet. |
| 48 | `Page.LayoutIncremental(flags, scope)` | method | Animated relayout; scope is a `Selection` or `visLayoutIncrementalAllShapes`. |
| 49 | `Page.ResizeToFitContents` | method | Shrinks page to bounding rectangle of shapes plus margin. |
| 50 | `Page.Export(filename)` | method | Raster/vector export (`.png`, `.svg`, `.emf`, `.jpg`, `.gif`, `.bmp`, `.tif`, `.wmf`). |

### 3.1 PageSheet cells you set most often

| Cell | Section | Purpose |
|---|---|---|
| `PageWidth` | Page Properties | Width in IU/inches; e.g. `"11 in"`. |
| `PageHeight` | Page Properties | Height; e.g. `"8.5 in"`. |
| `PageScale` | Page Properties | World units per drawing unit (e.g. `"1 in"`). |
| `DrawingScale` | Page Properties | Logical drawing scale; pairs with `PageScale`. |
| `DrawingSizeType` | Page Properties | `0`=same as printer, `3`=fit to drawing, `4`=custom. |
| `PrintPageOrientation` | Print Properties | `1`=portrait, `2`=landscape. |
| `PlaceStyle` | Page Layout | `0`=as drawn, `1`=top-to-bottom, `2`=left-to-right, etc. |
| `RouteStyle` | Page Layout | `5`=flowchart NS, `6`=tree NS, `9`=org chart, `0`=right-angle. |
| `AvenueSizeX` | Page Layout | Horizontal channel between auto-laid-out shapes. |
| `AvenueSizeY` | Page Layout | Vertical channel. |
| `LineRouteExt` | Page Layout | Connector extension style; `1`=square, `2`=curved. |

### 3.2 `visAutoConnectDir*` for `DropConnected` / `AutoConnect`

| Constant | Value | Direction |
|---|---|---|
| `visAutoConnectDirNone` | `0` | Glue without moving (use existing positions). |
| `visAutoConnectDirRight` | `1` | Place new shape to the right of source. |
| `visAutoConnectDirDown` | `2` | Place below. |
| `visAutoConnectDirLeft` | `3` | Place to left. |
| `visAutoConnectDirUp` | `4` | Place above. |

### 3.3 Layout style values for `RouteStyle` / `PlaceStyle`

| `PlaceStyle` | Meaning |
|---|---|
| `0` | As-drawn (no auto place). |
| `1` | Top-to-bottom flowchart. |
| `2` | Left-to-right flowchart. |
| `3` | Bottom-to-top. |
| `4` | Right-to-left. |
| `7` | Compact down. |
| `8` | Circular. |

| `RouteStyle` | Meaning |
|---|---|
| `0` | Right-angle. |
| `1` | Straight. |
| `2` | Center-to-center. |
| `5` | Flowchart NS. |
| `6` | Tree NS. |
| `9` | Org chart. |

```python
# Drop + auto-route + fit
ps = page.PageSheet
ps.Cells("PlaceStyle").FormulaU = "1"
ps.Cells("RouteStyle").FormulaU = "5"
shape_a = page.Drop(master_proc, 4.0, 8.0)
shape_b = page.Drop(master_proc, 4.0, 6.0)
shape_a.AutoConnect(shape_b, 0, None)
page.Layout()
page.ResizeToFitContents()
```

---

## 4. Masters collection and Master object

A `Master` is a reusable shape definition stored in a stencil document. The
`Document.Masters` collection holds the **Document Stencil** (per-drawing
local masters auto-cloned on first `Drop`); a separately opened `.vssx` is a
`Document` whose `Masters` collection is queried by name to source new
drops.

| # | Member | Returns | Use |
|---|---|---|---|
| 51 | `Masters.Item(index)` | `Master` | 1-based access (locale-localized name). |
| 52 | `Masters.ItemU(name)` | `Master` | Locale-invariant universal-name lookup; preferred. |
| 53 | `Masters.ItemFromID(id)` | `Master` | Lookup by integer master ID (stable per document). |
| 54 | `Master.NameU` | `String` | Universal name; the value to use in `ItemU`. |
| 55 | `Master.BaseID` | `String` | GUID identifying the master across documents (stable). |
| 56 | `Master.UniqueID(flags)` | `String` | Per-instance GUID; pass `visGetOrMakeUniqueID=1` to mint if missing. |
| 57 | `Master.MatchByName` | `Boolean` | If `True`, re-dropping reuses an existing local master with the same name. |
| 58 | `Master.Open` | `Document` | Returns the master's editable document for `Master.Shapes` traversal. |
| 59 | `Master.Drop` (via Page) | `Shape` | Convention: call `Page.Drop(master, x, y)` -- master itself does not drop. |

```python
# Open a stencil read-only/hidden, get master by universal name
stencil = app.Documents.OpenEx(
    r"C:\Program Files\Microsoft Office\root\Office16\Visio Content\1033\BASFLO_M.VSSX",
    2 + 64 + 512)              # visOpenRO + visOpenHidden + visOpenDocked
proc = stencil.Masters.ItemU("Process")
shape = page.Drop(proc, 4.0, 6.0)
print(shape.Master.BaseID)     # GUID e.g. "{8F4C0F6A-...}"
```

---

## 5. Shape object -- core members

`Shape` is the workhorse of the object model. Every dropped instance, every
drawn primitive, every group, sub-shape, and connector is a `Shape`. The
`Cell` interface for ShapeSheet access is reached through `Shape.Cells`,
`Shape.CellsU`, `Shape.CellsSRC`.

| # | Member | Returns | Use |
|---|---|---|---|
| 60 | `Shape.NameU` | `String` | Universal (locale-invariant) shape name. |
| 61 | `Shape.Text` | `String` | Read/write shape's primary text run. |
| 62 | `Shape.Master` | `Master` | Source master, or `Nothing` after `ConvertToGroup`. |
| 63 | `Shape.OneD` | `Boolean` | `True` if the shape carries a `1-D Endpoints` section. |
| 64 | `Shape.Cells(name)` | `Cell` | Localized cell by name (avoid for portable code). |
| 65 | `Shape.CellsU(name)` | `Cell` | Universal cell name; e.g. `"PinX"`, `"Char.Color"`, `"Geometry1.X1"`. |
| 66 | `Shape.CellsSRC(section, row, col)` | `Cell` | Fastest path; integer triple from `VisSectionIndices`/`VisRowIndices`/`VisCellIndices`. |
| 67 | `Shape.CellExistsU(name, fLocal)` | `Long` | Probe before access; non-zero means present. |
| 68 | `Shape.SetFormulas(SIDSRC, formulas, flags)` | `Long` | Batch write formulas in one COM round-trip + one undo step. |
| 69 | `Shape.SetResults(SIDSRC, units, results, flags)` | `Long` | Batch write evaluated values with units. |
| 70 | `Shape.AutoConnect(target, dir, connector)` | method | Draw + glue connector A->B; pass `dir = 0` to keep positions. |
| 71 | `Shape.ConvertToGroup` | method | Severs the master link; embeds local geometry. |
| 72 | `Shape.Shapes` | `Shapes` | Sub-shapes (groups only); empty for primitives. |
| 73 | `Shape.Connects` | `Connects` | The 1-D shape's glue endpoints (begin / end). |
| 74 | `Shape.Delete` | method | Removes the shape from the page. |
| 75 | `Shape.Duplicate` | `Shape` | Clones the shape on the same page. |
| 76 | `Shape.AddSection(section)` | `Long` | Add a ShapeSheet section (`visSectionUser`, `visSectionScratch`...). |
| 77 | `Shape.AddRow(section, row, tag)` | `Long` | Add a row to a dynamic section; `tag` from `VisRowTags`. |
| 78 | `Shape.AddNamedRow(section, name, tag)` | `Long` | Named row insert (e.g. `"flag"` in `User`). |

### 5.1 Most-used Shape ShapeSheet cells

| Cell | Section | Purpose |
|---|---|---|
| `PinX` | Shape Transform | X of pin in parent coords. |
| `PinY` | Shape Transform | Y of pin. |
| `Width` | Shape Transform | Logical width. |
| `Height` | Shape Transform | Logical height. |
| `Angle` | Shape Transform | Rotation around pin. |
| `LocPinX` | Shape Transform | X of pin in local coords (default `Width*0.5`). |
| `LocPinY` | Shape Transform | Y of pin in local coords (default `Height*0.5`). |
| `FlipX` | Shape Transform | Mirror across local Y axis. |
| `FlipY` | Shape Transform | Mirror across local X axis. |
| `BeginX` | 1-D Endpoints | Tail X (1-D shapes only). |
| `BeginY` | 1-D Endpoints | Tail Y. |
| `EndX` | 1-D Endpoints | Head X. |
| `EndY` | 1-D Endpoints | Head Y. |
| `LineColor` | Line Format | Stroke color expression (`RGB(...)` or palette index). |
| `LineWeight` | Line Format | Stroke weight; e.g. `"0.02 in"`. |
| `LinePattern` | Line Format | `0`=none, `1`=solid, `2`=dashed, ... |
| `FillForegnd` | Fill Format | Fill color. |
| `FillPattern` | Fill Format | `0`=none, `1`=solid, others = pattern indexes. |
| `Char.Color` | Character[i] | Text color for run i. |
| `Char.Size` | Character[i] | Text size; `"10 pt"`. |
| `Char.Font` | Character[i] | Font index (resolved via `Document.Fonts`). |
| `User.<name>` | User-defined Cells | Named scratch values; row added by `AddNamedRow`. |
| `Prop.<name>` | Shape Data | Custom property; `Prop.<name>.Label`, `.Type`, `.Value`. |
| `Geometry1.X1` | Geometry[1] | First vertex X of path 1; row tag `MoveTo` / `LineTo` / etc. |

### 5.2 ShapeSheet section indices (`VisSectionIndices`)

| Constant | Value | Section |
|---|---|---|
| `visSectionObject` | `1` | The shape's "global" section -- holds Shape Transform / 1-D Endpoints. |
| `visSectionUser` | `242` | User-defined cells. |
| `visSectionScratch` | `243` | Scratch cells (`A1..D1` etc.). |
| `visSectionConnectionPts` | `7` | Connection points. |
| `visSectionControls` | `8` | Yellow control handles. |
| `visSectionAction` | `240` | Right-click actions. |
| `visSectionProp` | `243` | Shape Data (synonym in newer SDKs: `visSectionShapeData`). |
| `visSectionHyperlink` | `247` | Hyperlinks. |
| `visSectionFirstComponent` | `10` | First geometry section (`Geometry1`); add `i` for `Geometry(i+1)`. |
| `visSectionCharacter` | `3` | Character runs. |
| `visSectionParagraph` | `4` | Paragraph runs. |

### 5.3 Batch ShapeSheet write (avoid per-cell `FormulaU = ...`)

```vb
' VBA: PinX, PinY, Width, Height in one round-trip
Dim sidsrc(0 To 11) As Integer
Dim formulas(0 To 3) As String
sidsrc(0)=1: sidsrc(1)=1: sidsrc(2)=0     ' XForm/PinX
sidsrc(3)=1: sidsrc(4)=1: sidsrc(5)=1     ' XForm/PinY
sidsrc(6)=1: sidsrc(7)=1: sidsrc(8)=2     ' XForm/Width
sidsrc(9)=1: sidsrc(10)=1: sidsrc(11)=3   ' XForm/Height
formulas(0) = "4 in"
formulas(1) = "6 in"
formulas(2) = "2 in"
formulas(3) = "1 in"
shape.SetFormulas sidsrc, formulas, 0
```

---

## 6. Cell object

A `Cell` is a single ShapeSheet cell. Always prefer the `*U` (universal)
variants in code that may run on a non-English Visio.

| # | Member | Returns | Use |
|---|---|---|---|
| 79 | `Cell.FormulaU` | `String` | Universal-syntax formula source; round-trip safe across locales. |
| 80 | `Cell.Formula` | `String` | Localized formula; `"PinX"` becomes `"BrocheX"` on French Visio. |
| 81 | `Cell.FormulaForceU` | `String` | Bypasses `GUARD()` and inheritance protection on write. |
| 82 | `Cell.ResultIU` | `Double` | Result in **internal units** (inches/radians); fastest read. |
| 83 | `Cell.Result(unit)` | `Double` | Result coerced to a unit string (`"in"`, `"mm"`, `"deg"`, `"pt"`). |
| 84 | `Cell.ResultStrU(unit)` | `String` | Formatted string (`"3.5 in"`); good for round-trip diff. |
| 85 | `Cell.GlueTo(targetCell)` | method | Glue 1-D endpoint cell to a 2-D target; e.g. `BeginX.GlueTo(Pin.PinX)`. |
| 86 | `Cell.GlueToPos(targetShape, xFrac, yFrac)` | method | Glue to a fractional position (0..1) inside `targetShape`. |
| 87 | `Cell.IsConstant` | `Boolean` | `True` if formula is a literal; lets the caller skip recalc dependency. |
| 88 | `Cell.IsInherited` | `Boolean` | `True` if value comes from master; write switches to local override. |
| 89 | `Cell.Dependents` | `Cell()` | Array of cells whose formulas reference this one. |
| 90 | `Cell.Section` / `Row` / `Column` | `Long` | Reflective identity (use to convert back to `CellsSRC` triple). |

### 6.1 Unit suffix vocabulary for `Cell.Result(unit)` / formulas

| Suffix | Meaning |
|---|---|
| `in` / `in.` | Inches. |
| `mm` | Millimetres. |
| `cm` | Centimetres. |
| `m` | Metres. |
| `pt` | Points (1/72 in). |
| `ft` | Feet. |
| `deg` | Degrees. |
| `rad` | Radians. |
| `%` | Percent (literal `0..1` * 100). |
| `du` | Drawing units (page-scaled). |

### 6.2 Read/write idioms

```python
# read
pin_x_in = shape.CellsU("PinX").Result("in")
pin_x_iu = shape.CellsU("PinX").ResultIU            # always inches

# write a literal
shape.CellsU("PinX").FormulaU = "4 in"

# write a formula referencing another cell
shape.CellsU("Width").FormulaU = "GUARD(Sheet.5!Width*0.5)"
```

```csharp
// C# (PIA): traversal release etiquette
Visio.Cell cell = null;
try {
    cell = shape.CellsU["PinX"];
    double iu = cell.ResultIU;
} finally {
    if (cell != null) Marshal.ReleaseComObject(cell);
}
```

---

## 7. Selection and Window objects

`Window` is the host of `Selection`. Drawing windows expose the active
`Page`, the zoom, and the user selection. `Selection` is a 1-based collection
of currently-selected shapes plus alignment / grouping operations.

| # | Member | Returns | Use |
|---|---|---|---|
| 91 | `Window.Selection` | `Selection` | Current selection in the window. |
| 92 | `Window.Page` | `Page` | Active page in this window (synonym for `ActivePage` on the foreground window). |
| 93 | `Window.Zoom` | `Double` | Read/write zoom factor (`1.0` = 100%); `-1` triggers Fit Window. |
| 94 | `Selection.Item(i)` / `Selection[i]` | `Shape` | 1-based access. |
| 95 | `Selection.Count` | `Long` | Number of selected shapes. |
| 96 | `Selection.Align(horiz, vert, glueToGuide)` | method | Align bounding boxes; `horiz` = `VisHorizontalAlignTypes`, `vert` = `VisVerticalAlignTypes`, `glueToGuide` `0`/`1`. |
| 97 | `Selection.Distribute(distType, fSpacing)` | method | Even-distribute; `distType` from `VisUIObjectTypes` (`visDistHorzSpace=4`, `visDistVertSpace=8`). |
| 98 | `Selection.Group` | `Shape` | Wrap selection in a new group. |
| 99 | `Selection.Ungroup` | method | Reverse of `Group`; explodes one level. |
| 100 | `Selection.DeleteEx(flags)` | method | Delete with options (`visDeleteNormal=0`, `visDeleteHealConnectors=256`). |

### 7.1 Alignment enums

| `VisHorizontalAlignTypes` | Value |
|---|---|
| `visHorzAlignNone` | `0` |
| `visHorzAlignLeft` | `1` |
| `visHorzAlignCenter` | `2` |
| `visHorzAlignRight` | `3` |

| `VisVerticalAlignTypes` | Value |
|---|---|
| `visVertAlignNone` | `0` |
| `visVertAlignTop` | `1` |
| `visVertAlignMiddle` | `2` |
| `visVertAlignBottom` | `3` |

```csharp
// align selection horizontally + vertically centred
sel.Align(Visio.VisHorizontalAlignTypes.visHorzAlignCenter,
          Visio.VisVerticalAlignTypes.visVertAlignMiddle,
          0); // GlueToGuide = false
```

---

## 8. Connect and EventList

`Connect` describes a glue relationship between a 1-D shape's endpoint cell
and a 2-D shape's connection-point cell. `Page.Connects` and
`Shape.Connects` enumerate them; the values populate the `<Connects>` block
in the `.vsdx` page XML.

| Member | Returns | Use |
|---|---|---|
| `Page.Connects` | `Connects` | All glue relationships on the page. |
| `Connect.FromSheet` | `Shape` | The 1-D connector. |
| `Connect.FromCell` | `Cell` | The endpoint cell on the connector (`BeginX` / `EndX`). |
| `Connect.FromPart` | `Long` | `visBegin=9` or `visEnd=12`. |
| `Connect.ToSheet` | `Shape` | The target 2-D shape. |
| `Connect.ToCell` | `Cell` | Connection-point cell on the target. |
| `Connect.ToPart` | `Long` | `visConnectionPoint=100` etc. |

### 8.1 Event subscription patterns

The PIA exposes events as .NET delegates. The Visio-native form is
`EventList.AddAdvise`, which stores a persistent or transient subscription
on a `Document` or `Application`.

```csharp
// .NET delegate event (preferred for VSTO)
app.SelectionChanged += (Visio.Window w) => Ribbon.Invalidate();
app.ShapeAdded       += (Visio.Shape s)  => Log(s.NameU);
app.BeforeDocumentClose += (Visio.Document d) => Persist(d);
```

```csharp
// EventList.AddAdvise (works across out-of-process boundaries)
short code = (short)(Visio.VisEventCodes.visEvtAdd | Visio.VisEventCodes.visEvtShape);
Visio.Event evt = app.EventList.AddAdvise(code, sink, "", "Shape added");
// later: evt.Delete();
```

### 8.2 `VisEventCodes` -- common values

| Constant | Value | Meaning |
|---|---|---|
| `visEvtAdd` | `0x8000` | Object added (verb). |
| `visEvtMod` | `0x4000` | Modified (verb). |
| `visEvtDel` | `0x2000` | Deleted (verb). |
| `visEvtShape` | `0x0040` | Subject is a shape (category). |
| `visEvtPage` | `0x0020` | Subject is a page. |
| `visEvtDoc` | `0x0010` | Subject is a document. |
| `visEvtCell` | `0x0080` | Subject is a cell. |
| `visEvtSelect` | `0x0008` | Selection changed. |
| `visEvtCodeShapeAdd` | `0x80000040` | Compound: shape added. |
| `visEvtCodeShapeDelete` | `0x20000040` | Compound: shape deleted. |
| `visEvtCodeWinSelChange` | `0x00010001` | Compound: window selection change. |
| `visEvtCodeBeforeDocClose` | `0x00000001` | Before document close. |

Compound codes are the bitwise OR of the verb and category bits; the PIA
exposes the precomputed values as named members of `VisEventCodes`.

---

## 9. Constants quick lookup

### 9.1 `visOpen*` (Documents.OpenEx)

| Constant | Value |
|---|---|
| `visOpenRW` | `0` |
| `visOpenRO` | `2` |
| `visOpenCopy` | `4` |
| `visOpenMinimized` | `16` |
| `visOpenHidden` | `64` |
| `visOpenMacrosDisabled` | `128` |
| `visOpenNoWorkspace` | `256` |
| `visOpenDocked` | `512` |

### 9.2 `visSaveAs*` (Document.SaveAsEx)

| Constant | Value |
|---|---|
| `visSaveAsWS` | `1` (include workspace) |
| `visSaveAsListInMRU` | `2` (add to MRU) |

### 9.3 `visFixedFormat*` and intent

| Constant | Value | Meaning |
|---|---|---|
| `visFixedFormatPDF` | `1` | PDF output. |
| `visFixedFormatXPS` | `2` | XPS output. |
| `visDocExIntentPrint` | `1` | Print quality (smaller, embeds fonts). |
| `visDocExIntentScreen` | `2` | Screen-optimised. |
| `visPrintAll` | `0` | All pages. |
| `visPrintCurrentPage` | `1` | Active page only. |
| `visPrintFromTo` | `2` | Use `FromPage`/`ToPage` arguments. |
| `visPrintSelection` | `3` | Selection only. |

### 9.4 `ext_ConnectMode` (IDTExtensibility2)

| Constant | Value | Meaning |
|---|---|---|
| `ext_cm_AfterStartup` | `0` | Manual connect after host start. |
| `ext_cm_Startup` | `1` | LoadBehavior=3 (auto-load with host). |
| `ext_cm_External` | `2` | Loaded by another add-in. |
| `ext_cm_CommandLine` | `3` | Command-line load. |
| `ext_cm_Solution` | `4` | Part of a solution. |
| `ext_cm_UISetup` | `5` | One-time UI install pass. |

### 9.5 `ext_DisconnectMode`

| Constant | Value | Meaning |
|---|---|---|
| `ext_dm_HostShutdown` | `0` | Host quitting. |
| `ext_dm_UserClosed` | `1` | Unloaded via COM Add-Ins dialog. |

### 9.6 Common HRESULT values

| HRESULT | Symbol | Cause |
|---|---|---|
| `0x80004005` | `E_FAIL` | Generic Visio failure; check `EXCEPINFO[2]`. |
| `0x80020003` | `DISP_E_MEMBERNOTFOUND` | Method/property typo or wrong Visio version. |
| `0x80020005` | `DISP_E_TYPEMISMATCH` | Wrong arg type (e.g. `str` for `Master`). |
| `0x80020009` | `DISP_E_EXCEPTION` | Visio raised `EXCEPINFO`; real message in `excepinfo[2]`. |
| `0x800401F0` | `CO_E_NOTINITIALIZED` | Thread missed `CoInitialize()`. |
| `0x80010001` | `RPC_E_CALL_REJECTED` | Visio busy (modal dialog); retry with backoff. |
| `0x80010108` | `RPC_E_DISCONNECTED` | Stale proxy after `Quit`. |
| `0x800AC472` | (Visio: file in use) | Another process has the .vsdx open. |
| `0x8004D10D` | (Visio: master not found) | Stencil missing the named master. |
| `0x80040154` | `REGDB_E_CLASSNOTREG` | Visio not installed for this bitness. |
| `0x80048026` | (license / activation) | Visio not licensed; fix in Office portal. |
| `0x80004001` | `E_NOTIMPL` | Online Visio surface; method only available on Win32 desktop. |

---

## 10. Lifecycle skeletons by host language

### 10.1 Python (pywin32)

```python
import pythoncom, pywintypes, win32com.client as wc

pythoncom.CoInitialize()
try:
    wc.gencache.EnsureModule("{00021A98-0000-0000-C000-000000000046}", 0, 4, 12)
    app = wc.DispatchEx("Visio.InvisibleApp")
    app.AlertResponse = 7
    app.ScreenUpdating = 0
    try:
        doc = app.Documents.Add("")
        page = doc.Pages.Item(1)
        page.DrawRectangle(1, 1, 4, 3)
        doc.SaveAs(r"C:\out\rect.vsdx")
        doc.Close()
    finally:
        app.Quit()
finally:
    pythoncom.CoUninitialize()
```

### 10.2 PowerShell

```powershell
$ErrorActionPreference = 'Stop'
$visio = New-Object -ComObject Visio.InvisibleApp
try {
    $visio.AlertResponse = 7
    $doc  = $visio.Documents.Add('')
    $page = $doc.Pages.Item(1)
    $page.DrawRectangle(1, 1, 4, 3) | Out-Null
    $doc.SaveAs('C:\out\rect.vsdx')
    $doc.Close()
}
finally {
    if ($visio) {
        $visio.Quit()
        [void][Runtime.InteropServices.Marshal]::ReleaseComObject($visio)
    }
}
```

### 10.3 C# (out-of-process)

```csharp
[STAThread]
static int Main()
{
    Visio.Application app = null;
    try
    {
        app = new Visio.Application { Visible = true };
        var doc  = app.Documents.Add("");
        var page = doc.Pages[1];
        page.DrawRectangle(1, 1, 3, 2).Text = "Hello";
        return 0;
    }
    finally
    {
        if (app != null) { try { app.Quit(); } catch { } Marshal.ReleaseComObject(app); }
    }
}
```

### 10.4 VBA

```vb
Public Sub QuickDraw()
    Dim doc As Visio.Document
    Dim page As Visio.Page
    Set doc = Application.Documents.Add("")
    Set page = doc.Pages.Item(1)
    page.DrawRectangle 1, 1, 4, 3
    doc.SaveAs "C:\out\rect.vsdx"
End Sub
```

### 10.5 VSTO `ThisAddIn`

```csharp
public partial class ThisAddIn
{
    internal Visio.Application VisioApp { get; private set; }

    private void ThisAddIn_Startup(object sender, EventArgs e)
        => VisioApp = (Visio.Application)this.Application;

    private void ThisAddIn_Shutdown(object sender, EventArgs e)
        => VisioApp = null;

    protected override Office.IRibbonExtensibility CreateRibbonExtensibilityObject()
        => new AlignRibbon();
}
```

---

## 11. Threading and apartment cheatsheet

| Host | Apartment | Init call | Notes |
|---|---|---|---|
| VBA | STA (host thread) | implicit | Always main thread; never spawn `Thread`. |
| VSTO | STA | implicit | Use `SynchronizationContext.Current.Post` to marshal back. |
| C# console | STA | `[STAThread]` on `Main` | `CoCreateInstance` returns `CO_E_NOTINITIALIZED` without it. |
| Python | STA | `pythoncom.CoInitialize()` per thread | `CoUninitialize()` before exit. |
| PowerShell | STA when invoked with `-STA` | implicit on STA | `pwsh -sta`; default for Win PowerShell, opt-in for `pwsh`. |

Visio is registered as `ThreadingModel = Apartment`. From an MTA caller, COM
marshals every call across the apartment boundary which deadlocks on
re-entrant callbacks (e.g. `AutoConnect` invoking event handlers).

---

## 12. RCW release etiquette (out-of-process clients)

Every property traversal accumulates an RCW. In OOP automation a leaked RCW
keeps `Visio.exe` alive after `Quit()`. Defensive pattern:

```csharp
Visio.Document doc = null;
Visio.Pages pages = null;
Visio.Page page = null;
Visio.Shape shape = null;
Visio.Cell cell = null;
try {
    doc   = app.ActiveDocument;
    pages = doc.Pages;
    page  = pages[1];
    shape = page.Shapes[3];
    cell  = shape.Cells["PinX"];
    double iu = cell.ResultIU;
}
finally {
    if (cell  != null) Marshal.ReleaseComObject(cell);
    if (shape != null) Marshal.ReleaseComObject(shape);
    if (page  != null) Marshal.ReleaseComObject(page);
    if (pages != null) Marshal.ReleaseComObject(pages);
    if (doc   != null) Marshal.ReleaseComObject(doc);
}
```

VSTO mostly absolves you of this discipline (per-AppDomain RCW tracking).
For OOP clients (Python / PowerShell / standalone .NET), forgetting it
leaks the host.

---

## 13. Universal vs localized identifiers

| Localized | Universal | Returns | Notes |
|---|---|---|---|
| `Cell.Formula` | `Cell.FormulaU` | `String` | Localizes function names (`SUM` -> `SOMME` on French). |
| `Cell.Result(unit)` | `Cell.ResultStrU(unit)` | `String` | Universal returns invariant decimals. |
| `Shape.Name` | `Shape.NameU` | `String` | Universal stable across languages. |
| `Page.Name` | `Page.NameU` | `String` | Same. |
| `Master.Name` | `Master.NameU` | `String` | Same. |
| `Pages.Item(name)` | `Pages.ItemU(name)` | `Page` | Universal lookup. |
| `Masters.Item(name)` | `Masters.ItemU(name)` | `Master` | Universal lookup. |
| `Shape.Cells(name)` | `Shape.CellsU(name)` | `Cell` | Universal cell name (`"PinX"` not `"BrocheX"`). |

**Always prefer the `*U` variants in machine-readable code.**

---

## 14. PIA Type Library version selection

| Visio | Typelib major.minor | PIA version | Notes |
|---|---|---|---|
| 2010 | 4.0 | 14.0.0.0 | `.vsd` default. |
| 2013 | 4.0 | 15.0.0.0 | OPC `.vsdx` default. |
| 2016 | 4.0 | 16.0.0.0 | Same surface as 2019/365. |
| 2019 | 4.12 | 16.0.0.0 | Adds `Document.SecurityCertificate`. |
| 2021 | 4.12 | 16.0.0.0 | Same. |
| Microsoft 365 | 4.12 | 16.0.0.0 | Subscription channel. |
| Visio for the web | n/a | n/a | No COM; use Office.js / Graph API. |

Pass the matching `(major, minor)` to `gencache.EnsureModule`. Mismatch is
silently tolerated -- pywin32 falls back to the latest registered version.

---

## 15. Registry keys touched by add-ins

```
HKCU\Software\Microsoft\Office\Visio\Addins\<ProgId>
    Description    REG_SZ    "Friendly description"
    FriendlyName   REG_SZ    "Display name"
    LoadBehavior   REG_DWORD 0x00000003
    Manifest       REG_SZ    "file:///C:/.../addin.vsto|vstolocal"

HKCU\Software\Microsoft\Office\16.0\Visio\Resiliency\DisabledItems
HKCU\Software\Microsoft\Office\<ver>\Visio\PDFAddin\
```

`LoadBehavior = 3` means *Load at startup, Connected*. After a startup
failure Visio downgrades it to `2` and may move the add-in to
`Resiliency\DisabledItems`.

---

## 16. Performance tips

| Tactic | Effect |
|---|---|
| `DispatchEx("Visio.InvisibleApp")` over `Dispatch` | Never reuse a user's interactive session for batch jobs. |
| Set `ScreenUpdating = 0`, `EventsEnabled = 0`, `UndoEnabled = False`, `DeferRecalc = 1` | Cuts batch build time 5-10x; reset at end. |
| `Page.DropMany(arr, xy)` over a loop of `Drop` | ~5x faster: one COM round-trip. |
| `Shape.SetFormulas` / `SetResults` over `Cells(...).FormulaU = ...` | ~10x faster for >5 cells. |
| Cache `Masters.ItemU(name)` lookups | `ItemU` does a linear scan. |
| Reuse one `InvisibleApp` for many documents | `DispatchEx` cold start is ~2 s. |
| Avoid `for s in page.Shapes` in tight loops | RCW accumulation; materialize `list(page.Shapes)` once. |

---

## 17. Common mistakes and their fixes

| Symptom | Root cause | Fix |
|---|---|---|
| `0x800401F0 CO_E_NOTINITIALIZED` | Worker thread skipped `CoInitialize`. | Wrap the body in `pythoncom.CoInitialize()` / `CoUninitialize()`. |
| `0x80040154 REGDB_E_CLASSNOTREG` | Bitness mismatch between Python and Visio. | Run 64-bit Python with 64-bit Office (or both 32-bit). |
| Add-in disappears, `LoadBehavior` flips to `2` | `OnConnection`/`Startup` threw. | Check Event Viewer; enable `VSTO_LOGALERTS=1`. |
| Ribbon button missing | `GetCustomUI` returned `""` for unexpected RibbonID. | Confirm `RibbonID == "Microsoft.Visio.Drawing"`. |
| `Cell.Result` returns wrong number on French Visio | Used `Formula` / `Result` (localized). | Use `FormulaU` / `ResultIU` everywhere. |
| `0x800AC472` (file in use) | Another Visio process holds the file. | `Get-Process VISIO \| Stop-Process` only after confirming no UI session. |
| `Visio.exe` lingers after `Quit()` | Leaked RCWs in OOP code. | Release every intermediate proxy in `finally`; force `gc.collect()` in Python. |
| `RPC_E_CALL_REJECTED` | Modal dialog open in Visio. | Set `AlertResponse = 7` before risky ops; retry with backoff on this HRESULT. |
| `DISP_E_MEMBERNOTFOUND` | Wrong typelib stubs cached. | Delete `%LOCALAPPDATA%\Temp\gen_py`; rerun `makepy`. |
| Modifications don't propagate | Wrote `Cell.Formula` while `Cell.IsInherited == True`. | Use `FormulaForceU` to override the master inheritance. |
| `DropConnected` skips glue | Passed `null` connector AND target shape too far. | Use `visAutoConnectDirNone = 0` and pre-place shapes within auto-connect threshold (`AvenueSizeX`). |

---

## 18. Bitwise idioms

```python
# Open stencil read-only, hidden, docked: 2 | 64 | 512 = 578
flags = c.visOpenRO + c.visOpenHidden + c.visOpenDocked
stencil = app.Documents.OpenEx(path, flags)

# AddAdvise: shape added = visEvtAdd (0x8000) | visEvtShape (0x40) = 0x8040
code = (Visio.VisEventCodes.visEvtAdd | Visio.VisEventCodes.visEvtShape)
evt = app.EventList.AddAdvise(code, sink, "", "Shape added")
```

When constructing event codes manually, be sure of `short` vs `long`:
`AddAdvise` takes a `short` (16-bit) on legacy event codes but the modern
PIA exposes 32-bit compound codes through `VisEventCodes` enum members --
use those constants directly to avoid sign-extension bugs.

---

## 19. Headless-server preflight checklist

| Check | Why |
|---|---|
| Visio installed and activated for the executing user | Per-user license; service account needs `Distributed COM Users`. |
| Bitness of automation runtime matches Office | 64-bit Python / .NET for 64-bit Office. |
| `C:\Windows\SysWOW64\config\systemprofile\Desktop` exists (32-bit on 64-bit OS) | Visio refuses to start when missing. |
| Interactive desktop available | Service account must run with "Interact with desktop" or use a console session. |
| `Application.AlertResponse = 7` set before any `Open`/`SaveAs` | Suppresses modal save / repair / merge prompts. |
| `visOpenMacrosDisabled` (`128`) for untrusted input | Blocks macro auto-run. |
| `Application.AutoRecoverInterval = 0` | Skip autosave on the unattended box. |
| `taskkill /F /IM VISIO.EXE` only after confirming no user session | Orphan cleanup safety. |

---

## Sources

- `research/01-com-object-model.md` -- Visio Object Model containment chain
  (`Application -> Documents -> Document -> Pages -> Page -> Shapes -> Shape ->
  Cells/CellsSRC`), `Visio.Application` vs `Visio.InvisibleApp` ProgID/CLSID
  matrix, `IVApplication` interface, `Documents.OpenEx` flag bitmask
  (`VisOpenSaveArgs`), `Page.Drop` / `DropMany` / `DropConnected`,
  `Shape.CellsU` / `CellsSRC`, `visSection*` indices (`visSectionObject`,
  `visSectionUser=242`, `visSectionProp=243`, `visSectionConnectionPts=7`,
  `visSectionFirstComponent=10`), `Connect` glue model
  (`FromSheet`/`FromCell`/`FromPart`/`ToSheet`/`ToCell`/`ToPart`),
  `Selection.Align`/`Distribute`/`Group`, `Window.Selection`/`Zoom`/
  `WindowState`, `Layer.Add`, `EventList.AddAdvise(code, sink, "", desc)`,
  `VisEventCodes` action/source bit composition (`visEvtAdd=0x0001`,
  `visEvtShape=0x0800`, etc.), STA threading rule.
- `research/06-python-com-automation.md` -- Python pywin32 /
  `win32com.client` reference: `Dispatch` vs `DispatchEx` vs
  `gencache.EnsureDispatch`, typelib GUID
  `{00021A98-0000-0000-C000-000000000046}` (`4, 12` for Visio 2019/2021/M365),
  `win32com.client.constants` namespace, `Documents.OpenEx` flag values
  (`visOpenRO=2`, `visOpenCopy=4`, `visOpenHidden=64`,
  `visOpenMacrosDisabled=128`, `visOpenNoWorkspace=256`,
  `visOpenDocked=512`), `Document.SaveAs` extension matrix,
  `ExportAsFixedFormat` 13-argument positional signature,
  `Page.Drop`/`DropMany`/`DropConnected`/`Layout`/
  `LayoutIncremental`/`ResizeToFitContents`/`Export`, `Shape.AutoConnect`,
  `Shape.SetFormulas` / `SetResults` batch APIs, `Cell.GlueTo` /
  `GlueToPos`, `pythoncom.CoInitialize`, `pywintypes.com_error` 4-tuple,
  performance benchmarks, retry-on-`RPC_E_CALL_REJECTED` pattern.
- `research/08-powershell-automation.md` -- PowerShell `New-Object -ComObject
  Visio.InvisibleApp` patterns, `Application.AlertResponse = 7`,
  `Document.ExportAsFixedFormat` 11-arg PowerShell signature, PageSheet
  print cells (`PrintPageOrientation`, `ScaleToFit`, `PagesX`/`PagesY`,
  `PaperKind`, `PageLeftMargin`), Scheduled Task / Session 0 /
  `SysWOW64\config\systemprofile\Desktop` workarounds,
  `Marshal::ReleaseComObject` discipline.
- `research/09-csharp-vsto-addins.md` -- VSTO `ThisAddIn` lifecycle,
  `IDTExtensibility2` `ext_ConnectMode` / `ext_DisconnectMode`,
  `IRibbonExtensibility`, `Application.SelectionChanged` /
  `ShapeAdded` / `BeforeDocumentClose` delegate events,
  `EApplication_Event` interface, `EventList.AddAdvise(code, sink, "", desc)`,
  `Application.BeginUndoScope` / `EndUndoScope`,
  `Selection.Align(VisHorizontalAlignTypes, VisVerticalAlignTypes,
  glueToGuide)` constants, RCW release etiquette in `finally`, registry
  keys (`HKCU\Software\Microsoft\Office\Visio\Addins\<ProgId>`,
  `LoadBehavior=3`, `Resiliency\DisabledItems`), PIA version matrix
  (`Microsoft.Office.Interop.Visio` 14.0/15.0/16.0).

