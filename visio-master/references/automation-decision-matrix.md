# Visio Automation Decision Matrix

> Picking the right automation path for a Visio task. Six runtimes, one
> decision tree, one capability matrix. Every path is named by the exact
> ProgID, package, or namespace; every constraint is named by the exact
> SKU, registry key, or HRESULT. Read this before writing any Visio
> automation code.
>
> Paths covered: **VBA** (in-process VBA host), **pywin32 COM** (Python
> via `win32com.client`), **vsdx** (PyPI `vsdx`, pure-Python OPC), **OPC
> zip+lxml** (raw `zipfile`/`lxml` against `[Content_Types].xml` and the
> `_rels` graph), **VSTO** (`Microsoft.Office.Tools.Visio.AddIn`,
> `Microsoft.Office.Interop.Visio.dll` PIA), **Office.js**
> (`Visio.run` / `Visio.EmbeddedSession`, requirement set `Visio 1.1`).

---

## 0. TL;DR cheat sheet

| Path | Runtime location | Visio install required | Cross-platform | License floor | One-line use |
|------|------------------|------------------------|---------------:|---------------|--------------|
| **VBA** | inside `VISIO.EXE` (32 / 64-bit) | yes (Std/Pro/Plan 2 desktop) | no (Win) | Visio Standard | UI-bound macros, ribbon buttons, in-document automation, `.vsdm` |
| **pywin32 COM** | external `python.exe` driving `Visio.InvisibleApp` | yes (Std/Pro/Plan 2 desktop) | no (Win) | Visio Standard | scripted batch generation, ETL pipelines, scheduled jobs |
| **vsdx (PyPI)** | external `python.exe`, no Visio process | **no** | **yes** (Win/macOS/Linux/CI) | none | templated `.vsdx` mutation, Jinja2 rendering, headless containers |
| **OPC zip+lxml** | external `python.exe`/`pwsh`/anything | **no** | **yes** | none | surgical XML edits to parts the high-level libs do not model |
| **.NET VSTO** | hosted in `VISIO.EXE` AppDomain | yes (Std/Pro/Plan 2 desktop) | no (Win) | Visio Standard | shipping a packaged add-in (.vsto / MSI / ClickOnce) |
| **Office.js** | browser tab against Visio for the Web | **no** (web entitlement) | **yes** (browser) | Visio Plan 1 / Web App | viewer-augmentation add-ins, overlays, highlight-on-data |

The single-sentence selector: **mutate the file** -> `vsdx` or OPC;
**drive the engine** -> VBA / pywin32 / VSTO; **augment the viewer** ->
Office.js; **ship a product** -> VSTO (desktop) or Office.js (web).

---

## 1. The six paths in one decision tree

```
START
  |
  +--Q1. Do you need to RENDER (PDF, PNG, SVG, EMF) or run LAYOUT/ROUTING/VALIDATION?
  |     YES -> only the engine knows how to do this.
  |          +-- inside Visio (user clicks button)? -------------- VBA  or  VSTO
  |          +-- outside (script / scheduler / batch)? ---------- pywin32 COM
  |          +-- inside browser (no engine available)? ---------- NOT POSSIBLE; round-trip via Graph
  |     NO -> continue.
  |
  +--Q2. Is Visio Desktop installed on the host that runs the code?
  |     NO  -> only the file or the web surface is reachable.
  |          +-- need to mutate XML cells / text / pages? ------- vsdx
  |          +-- need OPC parts vsdx does not model? ------------ OPC zip+lxml
  |          +-- need to interact with a live web rendering? ---- Office.js (read-mostly)
  |     YES -> continue.
  |
  +--Q3. What is the deployment target of the code?
  |     +-- end-user button inside Visio (one user) ---------- VBA in `.vsdm`
  |     +-- packaged installer for many users -----------------  VSTO
  |     +-- automation script on operator desktop ------------- pywin32 COM (or PowerShell COM)
  |     +-- nightly batch on a server -------------------------- pywin32 COM with caveats (KB257757)
  |
  +--Q4. Is the source format `.vsdm` / `.vstm` / `.vssm` (macros)?
        YES -> Visio for the Web refuses to open it.
              +-- macros required for the workflow -> desktop only.
              +-- macros optional -> emit `.vsdx`, lift logic to web add-in or backend.
        NO  -> all paths are technically open; pick by Q3.
```

The first hard dependency is always **the rendering engine**: PDF /
PNG / SVG / EMF, `Page.Layout()`, `Page.LayoutIncremental`, BPMN
`Document.Validation`, AutoCAD overlay, theme application, and the
ShapeSheet recalc loop are all bound to the `vmrendr.dll` /
`visio.exe` engine and are unreachable from `vsdx`, OPC, or
Office.js. Everything else is a question of *who triggers the engine*.

---

## 2. Path-by-path reference cards

Each card answers six questions in the same order:

1. What ProgID / package / namespace does the path use?
2. What does the host need installed?
3. What constants and APIs are the headline entry points?
4. What can it do (capability axis)?
5. What can it not do (gap axis)?
6. What pitfalls bite teams every time?

### 2.1 Path A -- VBA macros inside `VISIO.EXE`

| Field | Value |
|-------|-------|
| Host | `VISIO.EXE` (Win32 desktop) |
| Activation | `Alt+F11` -> VBE; macros stored in document part `visio/vbaProject.bin` (CFB stream) |
| Storable in | `.vsdm`, `.vssm`, `.vstm` (macros) -- not `.vsdx`, `.vssx`, `.vstx` |
| Type lib | `Visio.Application` 1.0 referenced automatically inside Visio VBA |
| Primary scope | `ThisDocument` (built-in class), Standard modules, Class modules, UserForms |
| Min SKU | Visio Standard 2024 desktop, Visio Pro/Plan 2 desktop |
| Trust path | `HKCU\Software\Microsoft\Office\<ver>\Visio\Security\VBAWarnings` |

**Headline entry points.**

```vba
' Inside ThisDocument:
Private Sub Document_DocumentOpened(ByVal doc As IVDocument)
    Application.AlertResponse  = 7      ' visAlertResponseNo
    Application.ScreenUpdating = False
    Application.EventsEnabled  = False
End Sub
```

```vba
ActivePage.Drop(Documents.OpenEx("...vssx", visOpenRO + visOpenDocked + visOpenHidden) _
    .Masters.ItemU("Process"), 4#, 6#)
shape.CellsU("PinX").FormulaU = "=4 in"
shape.CellsSRC(visSectionObject, visRowXFormOut, visXFormPinX).ResultIU
ActiveDocument.SaveAsEx "out.vsdm", visSaveAsWS + visSaveAsListInMRU
ActivePage.Export "out.png"
ActiveDocument.ExportAsFixedFormat 1, "out.pdf", 1, 0, 1, 1, False, True, 300, ""
```

**Capability axis (yes / no).**

| Capability | VBA |
|------------|:---:|
| Open / save `.vsdx` / `.vsdm` / `.vssx` / `.vstx` | yes |
| Drop master from stencil (`Page.Drop`, `DropMany`, `DropConnected`) | yes |
| Read / write any ShapeSheet cell (`Cells`, `CellsU`, `CellsSRC`, `Section`, `Row`) | yes |
| Connectors (`Shape.AutoConnect`, `Cell.GlueTo`, `GlueToPos`) | yes |
| Auto-layout / route (`Page.Layout`, `LayoutIncremental`) | yes |
| Themes / variants (`Document.Themes`) | yes |
| Validation rules (Pro/Plan 2 only -- `Document.Validation.RuleSets`) | yes (Pro) |
| Render to PDF / XPS (`Document.ExportAsFixedFormat`) | yes |
| Render to PNG / JPG / SVG / EMF (`Page.Export`) | yes |
| Receive events (`Document_*` on `ThisDocument`, `EventList.AddAdvise`) | yes |
| Cross-platform (Linux / macOS / browser) | **no** |
| Run server-side under `SYSTEM` / non-interactive | not supported (KB257757) |
| Ship as a packaged add-in across many users | **no** -- per-document VBA |

**Pitfalls.**

- **`.vsdx` strips macros silently** when called from VBA's `SaveAs` --
  always use `.vsdm` extension and `Document.SaveAsEx(path,
  visSaveAsWS)` to preserve the `vbaProject.bin` part.
- `BeforeShapeDelete`, `ShapesDeleted`, `ShapeBeforeTextEdit`,
  `ShapeExitedTextEdit` are **not** in the default `Document` event
  set; subscribe via `EventList.AddAdvise visEvtCodeShapeDelete,
  sink, "", ""` (codes `&H0321`, `&H0323`, `&H0324`).
- `Cells("Width")` is locale-sensitive -- French Visio rejects
  `PinX` in favor of `BrocheX`. Use `CellsU` / `FormulaU` /
  `NameU` / `ItemU` everywhere to bypass localization.
- Trust Center `VBAWarnings = 4` (Disable all without notification)
  silently kills `Document_DocumentOpened` on protected machines;
  trust the file or the location, do not lower the policy.
- VBA in stencils (`.vssm`) is fine, but documents spawned from a
  `.vstm` template default to `.vsdx` and lose the macros -- save the
  spawn explicitly with `SaveAsEx ".vsdm"`.
- `EventsEnabled = False` only stops Visio-fired events; sinks
  registered through `AddAdvise` may still fire if their queue is
  warm. Call `EventList.Item(i).Delete` to remove them deterministically.

### 2.2 Path B -- Python pywin32 COM

| Field | Value |
|-------|-------|
| Host | external `python.exe` driving an out-of-process Visio server |
| Package | `pywin32` (`win32com.client`, `pythoncom`, `pywintypes`) |
| ProgIDs | `Visio.Application` (visible), **`Visio.InvisibleApp`** (preferred for batch), `Visio.Drawing` |
| Type lib | `{00021A98-0000-0000-C000-000000000046}` major `4`, minor `12` (2019/2021/365) or `4`, `0` (2010-2016) |
| Min SKU | Visio Standard 2024 desktop, Visio Pro/Plan 2 desktop |
| Apartment | STA only -- `pythoncom.CoInitialize()` on every worker thread |

**Headline entry points.**

```python
import pythoncom, pywintypes, win32com.client as wc

pythoncom.CoInitialize()
wc.gencache.EnsureModule("{00021A98-0000-0000-C000-000000000046}", 0, 4, 12)
app = wc.DispatchEx("Visio.InvisibleApp")     # always DispatchEx, not Dispatch
from win32com.client import constants as c

app.AlertResponse  = 7                         # visAlertResponseCancel
app.ScreenUpdating = 0
app.EventsEnabled  = 0
app.DeferRecalc    = 1
app.AutomationSecurity = 3                     # msoAutomationSecurityForceDisable

doc     = app.Documents.OpenEx("in.vsdx",
                               c.visOpenRO + c.visOpenHidden + c.visOpenMacrosDisabled)
stencil = app.Documents.OpenEx("s.vssx", c.visOpenRO + c.visOpenDocked + c.visOpenHidden)
shape   = doc.Pages.Item(1).Drop(stencil.Masters.ItemU("Process"), 4.0, 6.0)
ids     = doc.Pages.Item(1).DropMany((m1, m2, m3), (1.0, 1.0, 3.0, 1.0, 5.0, 1.0))
shape.AutoConnect(other, c.visAutoConnectDirRight, None)
doc.Pages.Item(1).Layout()
doc.SaveAs("out.vsdx")
doc.ExportAsFixedFormat(c.visFixedFormatPDF, "out.pdf",
                        c.visDocExIntentPrint, c.visPrintAll,
                        1, 1, False, True, False, False, True, "", False)
doc.Close(); app.Quit(); pythoncom.CoUninitialize()
```

**Capability axis.**

| Capability | pywin32 COM |
|------------|:-----------:|
| Full Visio object model (Application/Document/Page/Shape/Cells/CellsSRC) | yes |
| Constants by name (`win32com.client.constants.visFixedFormatPDF`) | yes (after `gencache.EnsureDispatch`) |
| Render PDF / XPS / PNG / SVG / EMF | yes |
| `Page.Layout()` auto-routing / theming / validation | yes |
| Receive Visio events from Python (`WithEvents`-style) | yes (via `DispatchWithEvents`) |
| Run inside a service / scheduled task | yes with caveats (see pitfalls) |
| Cross-platform | **no** -- Windows + Visio desktop only |
| Concurrent same-process calls | **no** -- one Visio per worker process |

**Pitfalls.**

- `Dispatch("Visio.Application")` returns the **already-running** user
  session via the Running Object Table; use `DispatchEx("Visio.InvisibleApp")`
  for unattended work. Stealing a user's interactive Visio is the most
  common production accident.
- Every thread that touches a COM object must call
  `pythoncom.CoInitialize()` (STA) before its first call and
  `pythoncom.CoUninitialize()` before exit; otherwise Visio raises
  `CO_E_NOTINITIALIZED 0x800401F0`. `asyncio` event loops live on a
  single thread but block on every Visio call; offload to
  `loop.run_in_executor(None, fn)` with `CoInitialize` inside `fn`.
- `pywintypes.com_error.args` is a 4-tuple `(hresult, source,
  excepinfo, argerror)` where `excepinfo[2]` carries the human Visio
  message. Without parsing it, errors are useless. Common HRESULTs:
  `0x80020009 DISP_E_EXCEPTION`, `0x80010001 RPC_E_CALL_REJECTED`
  (transient -- retry with backoff), `0x80080005
  CO_E_SERVER_EXEC_FAILURE` (no interactive desktop for the SID),
  `0x80040154 REGDB_E_CLASSNOTREG` (Visio not installed or 32/64-bit
  mismatch).
- The bitness of Python and Visio must match. `py -3.12 -c "import
  platform; print(platform.architecture())"` should print `'64bit'`
  if your Visio is 64-bit (the modern default).
- Microsoft KB257757 declares server-side Office automation
  unsupported. It works in practice on Windows Server with Desktop
  Experience plus the
  `C:\Windows\SysWOW64\config\systemprofile\Desktop` workaround, but
  Microsoft will not investigate hangs reported under this topology.
  For SaaS, switch to Graph API or non-engine libraries (`vsdx`,
  Aspose.Diagram).
- Use locale-invariant identifiers everywhere: `FormulaU`, `NameU`,
  `ItemU`, `CellsU`. Non-`U` variants break on French/German/Japanese
  Visio.
- `app.Settings` belongs to the *Application* the document was opened
  in. If you mix Visio instances, the wrong settings can leak. Always
  read `doc.Application.Settings`.

### 2.3 Path C -- `vsdx` Python library (PyPI)

| Field | Value |
|-------|-------|
| Host | external Python; **no Visio process** |
| Package | `vsdx` (PyPI; author Dave Howard, github.com/dave-howard/vsdx) |
| Engine | `lxml` for XPath / XML, `zipfile` for OPC envelope, `Jinja2` for templating |
| Cross-platform | **yes** -- Linux, macOS, Windows, AWS Lambda, GitHub Actions |
| Min SKU | **none** -- pure file manipulation |

**Headline entry points.**

```python
from vsdx import VisioFile

with VisioFile("input.vsdx") as vis:
    for page in vis.pages:
        for s in page.all_shapes:                # recursive walk
            if "DRAFT" in (s.text or ""):
                s.text = s.text.replace("DRAFT", "FINAL")
        # ShapeSheet cells via dict-like API
        for s in page.child_shapes:
            pinx = s.cells.get("PinX")
            if pinx is not None:
                pinx.value = "3.5"
            s.set_cell_value("LineWeight", "0.02")  # upsert that auto-creates the <Cell>

    # Duplicate a page
    vis.copy_page(vis.pages[0], name="Copy")

    # Drop a master onto the page
    m = vis.master_page_per_shape("Rectangle")
    new_shape = vis.pages[0].add_shape(m, x=2.5, y=4.0, width=2.0, height=1.0)

    # Jinja2 template render (placeholders inside shape text + page names)
    vis.jinja_render_vsdx(context={"customer": "Acme", "regions": [...]})

    vis.save_vsdx("output.vsdx")
```

**Capability axis.**

| Capability | `vsdx` |
|------------|:-----:|
| Read / write `.vsdx` (OPC ZIP) | yes |
| Read / write shape text (`Shape.text`) | yes |
| Read / write ShapeSheet cells (`shape.cells["PinX"].value`, `set_cell_value`) | yes (textual) |
| Read / write Shape Data (`shape.data_properties[label].value`) | yes |
| Add shapes from masters already in document (`Page.add_shape`) | yes |
| Duplicate pages (`VisioFile.copy_page`) | yes |
| Iterate connectors via `<Connect>` rows (`page.connects`) | yes |
| Jinja2 templating across text and page names | yes |
| Apply a theme by name | **no** (you can write QuickStyle indices but cannot synthesize a theme) |
| Auto-layout / connector re-routing | **no** |
| Render to PDF / PNG / SVG / EMF | **no** |
| Recompute ShapeSheet formulas | **no** -- Visio recomputes on next open |
| Synthesize a master from scratch (no source stencil) | **no** |
| Run VBA / add-in code | **no** |

**Pitfalls.**

- `vsdx` mutates *persisted* state. Anything that depends on engine
  recalculation -- formulas with side-effects, theme application,
  connector geometry after auto-route -- shows up *only after* the
  next Visio open re-runs the engine. For a fully-rendered file in
  CI, hand the `vsdx`-written package to a Windows worker via Path B.
- `shape.text` field codes (`<fld>` page name / file name / data
  fields) return Visio's last-cached value; setting `shape.text =
  "..."` writes a literal but Visio will overwrite it on next open
  if a field code remains. Author template shapes without field
  codes for predictable rendering, or use Jinja2.
- `shape.cells` returns `None` (or raises `KeyError` depending on
  version) for cells inherited from a master without override.
  Always probe with `shape.cells.get("PinX")` and prefer
  `set_cell_value(name, value)` for upsert semantics.
- Concurrency is per-file, not per-thread: a `VisioFile` instance
  owns a temp directory and live `lxml` trees; parallelize at the
  `.vsdx` level (one process per file).
- Saved files are not byte-identical to Visio's output (zip entry
  order, namespace prefixes, compression). They are semantically
  equivalent. Do not gate CI on byte-level diffs.
- Do not write to the same path you opened from inside the `with
  VisioFile(...)` block on Windows -- the temp `ZipFile` may still
  hold an exclusive lock until `close_vsdx()` runs.
- Pin the version (`vsdx==0.5.18`); the API has minor shifts:
  `VisioFile.copy_page` vs `Page.copy`, `find_shape_by_property_label`
  appearance, `jinja_render_vsdx(context=...)` vs `**kwargs`.

### 2.4 Path D -- Direct OPC `zipfile` + `lxml`

| Field | Value |
|-------|-------|
| Host | any Python / Node / .NET / Java; no Visio, no `vsdx` library |
| Engine | `zipfile` (or any OPC reader) + `lxml` for XML mutation |
| Spec | ECMA-376 Part 2 (OPC) + `[MS-VSDX]` Visio Graphics Service File Format |
| Cross-platform | yes |
| Min SKU | none |

**Headline pattern.**

```python
import zipfile, shutil, tempfile, os
from lxml import etree

VIS_NS  = {"v": "http://schemas.microsoft.com/office/visio/2012/main"}
REL_NS  = {"r": "http://schemas.openxmlformats.org/package/2006/relationships"}
CT_NS   = {"ct": "http://schemas.openxmlformats.org/package/2006/content-types"}

shutil.copy("in.vsdx", "out.vsdx")
tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".vsdx").name

with zipfile.ZipFile("out.vsdx", "r") as zin, \
     zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
    for item in zin.infolist():
        data = zin.read(item.filename)
        if item.filename == "visio/pages/page1.xml":
            tree = etree.fromstring(data)
            for cell in tree.findall(".//v:Cell", VIS_NS):
                if cell.get("N") == "PinX":
                    cell.set("V", "3.5")
            data = etree.tostring(tree, xml_declaration=True,
                                  encoding="UTF-8", standalone=True)
        zout.writestr(item, data)
os.replace(tmp, "out.vsdx")
```

**Capability axis.**

| Capability | OPC zip+lxml |
|------------|:-----------:|
| Read / write any XML part (pages, masters, themes, recordsets, comments) | yes |
| Patch parts that `vsdx` does not model (`theme/theme1.xml` in detail, `data/recordsets/`, embedded OLE wrappers, custom XML for an add-in) | yes |
| Repair corrupt files part by part | yes |
| Add new parts (new page, new master, new theme) | yes (must update `[Content_Types].xml` + `_rels` graph) |
| Cross-platform, dependency-free (lxml only) | yes |
| High-level API for connectors, glue, master inheritance | **no** -- you implement it |
| Render | **no** |

**Pitfalls.**

- `[Content_Types].xml` must declare every `<Override
  PartName="..." ContentType="..."/>` for each non-default part. The
  Visio content types are documented in `[MS-VSDX]` section 2.1.4 --
  `application/vnd.ms-visio.page+xml`,
  `application/vnd.ms-visio.master+xml`,
  `application/vnd.ms-visio.theme+xml`,
  `application/vnd.ms-visio.windows+xml`,
  `application/vnd.ms-visio.relationships+xml`. Forgetting to add an
  Override on a new part makes Visio refuse to open the file.
- `_rels/*.rels` files own the part-to-part edges. Adding a new page
  means editing `visio/_rels/document.xml.rels` (link `document.xml
  -> pages.xml`) **and** `visio/pages/_rels/pages.xml.rels` (link
  `pages.xml -> pageN.xml`). The `Id` attributes (`rId1`, `rId2`,
  ...) must be unique within their `.rels` file but are otherwise
  free.
- Page IDs are not page indexes. `pages.xml` has `<Page ID="0">` but
  the part filename `pages/page1.xml` has nothing to do with `ID="0"`
  -- the ordinal in `pages.xml` is what determines tab order.
- Shape IDs are page-scoped and referenced from `<Connect
  FromSheet="42" ToSheet="17"/>` rows in the page XML. Renumbering on
  a copy means rewriting every `Connect` element. `vsdx` handles this
  for you; raw OPC does not.
- `xml_declaration=True, encoding="UTF-8", standalone=True` is the
  exact triple Visio writes; deviating in serialization can pass but
  produces ugly diffs in version control.
- Replace `zipfile` entries by rebuilding the zip; `ZipFile.open(...,
  "w")` cannot overwrite an existing entry.
- ZIP file parts in Visio's own files are not byte-deterministic
  (entry order, compression level, mtime). Re-emitting a file
  unchanged will diff -- gate CI on semantic checks (open in
  `vsdx`, compare known fields), not on `sha256`.

### 2.5 Path E -- .NET VSTO add-in

| Field | Value |
|-------|-------|
| Host | `VISIO.EXE` AppDomain (one per add-in via VSTO shim) |
| Loader | `VSTOLoader.dll` (Office shim) + `*.vsto` deployment manifest + registry |
| PIA | `Microsoft.Office.Interop.Visio.dll` (`PublicKeyToken=71e9bce111e9429c`); 15.0.0.0 (2013), 16.0.0.0 (2016+) |
| Base class | `Microsoft.Office.Tools.Visio.AddIn` (VSTO) **or** `Extensibility.IDTExtensibility2` (legacy COM) |
| Target | .NET Framework `net48` (CLR 4); not .NET Core / 5+ |
| Manifest registry | `HKCU\Software\Microsoft\Office\Visio\Addins\<ProgId>` (or `HKLM`) |
| Min SKU | Visio Standard 2024 desktop, Visio Pro/Plan 2 desktop |
| Ribbon ID | `Microsoft.Visio.Drawing` (the only one Visio publishes) |

**Headline entry points.**

```csharp
using Visio = Microsoft.Office.Interop.Visio;
public partial class ThisAddIn       // Microsoft.Office.Tools.Visio.AddIn
{
    private Visio.Application _app;
    private Visio.EApplication_SelectionChangedEventHandler _selChanged;

    private void ThisAddIn_Startup(object sender, EventArgs e)
    {
        _app = (Visio.Application)this.Application;
        _selChanged = OnSelectionChanged;          // ROOT the delegate
        _app.SelectionChanged += _selChanged;
    }

    internal void AlignSelection(Visio.VisHorizontalAlignTypes h,
                                 Visio.VisVerticalAlignTypes v)
    {
        var sel = _app.ActiveWindow.Selection;
        int undo = _app.BeginUndoScope("Align");
        try { sel.Align(h, v, 0); _app.EndUndoScope(undo, true); }
        catch { _app.EndUndoScope(undo, false); throw; }
        finally { Marshal.ReleaseComObject(sel); }
    }
}
```

```xml
<!-- Ribbon.xml -->
<customUI xmlns="http://schemas.microsoft.com/office/2009/07/customui"
          onLoad="OnRibbonLoad">
  <ribbon><tabs>
    <tab id="acmeTab" label="Acme" insertAfterMso="TabHome">
      <group id="g1" label="Align">
        <button id="b1" label="Left" imageMso="AlignLeft"
                onAction="OnAlignLeftClick" size="large"/>
      </group>
    </tab>
  </tabs></ribbon>
</customUI>
```

