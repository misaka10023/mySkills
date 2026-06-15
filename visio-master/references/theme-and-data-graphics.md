# Theme & Data-Graphic Application Reference

Operational reference consulted by the Stylist role and any agent that must
apply, swap, or author Visio themes and data graphics. Covers the **strict
ordering** that Visio requires when (a) a theme is applied to a document and
(b) a data graphic is associated, applied, and refreshed against linked
records. All API calls, ShapeSheet cells, and constants are named exactly as
they appear in the Visio type library and the OOXML DrawingML schema.

> Theme and data-graphic objects share a common runtime invariant: both are
> stored in the document's hidden masters/parts and referenced through stable
> integer IDs, not by name. Every "apply" operation is the assignment of an ID
> to a cell on a shape; everything else is recalculation. Out-of-order calls
> (variant before theme, refresh before associate) are silently no-op or
> resolve against stale state — no exception is raised. Verify by reading
> back `PageSheet.CellsU("ThemeIndex").ResultIU` and
> `Shape.LinkedDataRecordsetID` after each step.

---

## 1. The Two Pipelines at a Glance

| Pipeline | Stage 1 | Stage 2 | Stage 3 | Persistence |
|----------|---------|---------|---------|-------------|
| Theme | `Document.SetTheme(name)` | `Document.SetThemeVariant(idx)` | `Document.Colors.Item(n).Red/Green/Blue` (4-color override) | `theme/theme1.xml` + `<DocumentSheet>` cells `ThemeIndex`, `VariantThemeIndex`, `VariantColorIndex`, `VariantEmbellishmentIdx`, `VariantFontIdx`, `VariantStyleIdx` + `<ColorEntry/>` rows |
| Data graphic | `DataRecordsets.Add(...)` then `Shape.LinkToData(rsID, rowID, fAutoText, fAutoData)` (**associate**) | `Shape.DataGraphic = master` or `Page.SetDataGraphicOnSelection(...)` (**apply**) | `DataRecordset.Refresh()` (**refresh**) | `recordsets/recordset#.xml`, per-page `<Cell N="LinkedDataRecordsetID">`, `<Cell N="LinkedDataRowIDs">`, `Section N="Property"` rows, and `Master MasterType="2"` for the DG itself |

The two pipelines intersect at **Color By Value**: it consumes a Shape Data
field (data pipeline output) and rewrites `FillForegnd` (theme pipeline cell).
This intersection is the source of most surprises and is documented in §6.

---

## 2. Theme Application Sequence

### 2.1 Mandatory order

The order is **theme → variant → 4-color override**, and it is mandatory
because each later step reads state written by the earlier one:

1. `SetTheme(themeName)` rewrites `theme1.xml` (color scheme, font scheme,
   format scheme, embellishment defaults). Sets `ThemeIndex` on the
   `DocumentSheet`, resets `VariantThemeIndex` to `1`, and clears any prior
   `VariantColorIndex` override.
2. `SetThemeVariant(variantIdx)` rotates `accent1..accent4` to the variant's
   palette. Sets `VariantThemeIndex` to `1..4` (or `1..8` for galleries that
   advertise 8 variants). Visio reads the active `ThemeIndex` to decide
   which palette table to consult; calling this before `SetTheme` resolves
   against whatever was previously active and silently mismatches.
3. **4-color override** via `Document.Colors.Item(1..4)` — overrides the
   variant's first four accents at the document level. Persisted as
   `<ColorEntry IX='0..3' RGB='RRGGBB'/>` rows in `<DocumentSettings>`. Calling
   this before `SetThemeVariant` writes the override against the **previous**
   variant, then `SetThemeVariant` blows it away.

```
SetTheme("Facet")              # writes theme1.xml, ThemeIndex=10
SetThemeVariant(2)             # writes VariantThemeIndex=2, rotates palette
doc.Colors(1).Red = 0xC0       # writes <ColorEntry IX='0' RGB='C00000'>
doc.Colors(1).Green = 0x00
doc.Colors(1).Blue = 0x00
# At this point: theme=Facet, variant=2, accent1 forced to #C00000
# Any shape with QuickStyleFillColor=1 + QuickStyleFillMatrix>=1 paints in #C00000
```

### 2.2 Persisted cells after each step

| Step | Cell written | Section | Where in package |
|------|--------------|---------|------------------|
| 1. `SetTheme` | `ThemeIndex` | `<DocumentSheet>` | `visio/document.xml` |
| 1. `SetTheme` | (rewrites) | `<a:theme>`, `<a:clrScheme>`, `<a:fontScheme>`, `<a:fmtScheme>` | `visio/theme/theme1.xml` |
| 2. `SetThemeVariant` | `VariantThemeIndex` | `<DocumentSheet>` | `visio/document.xml` |
| 2. `SetThemeVariant` | `VariantEmbellishmentIdx` | `<DocumentSheet>` | (set to gallery default 0..3) |
| 2. `SetThemeVariant` | `VariantStyleIdx`, `VariantFontIdx` | `<DocumentSheet>` | (set to 0 unless explicitly changed) |
| 3. `Colors(n).RGB` | `<ColorEntry IX='n-1' RGB='..'/>` | `<DocumentSettings>` / `<Colors>` | `visio/document.xml` |

After all three steps, every shape whose ShapeSheet uses `THEMEVAL()` and has
`QuickStyleVariation` set with the correct bits resolves to the new colors on
the next recalculation pass. Visio recalculates synchronously inside
`SetTheme` and `SetThemeVariant`; the override step does **not** trigger an
implicit recalc — call `Document.Application.DoCmd(visCmdRecalcDocument)`
(constant `1312`) or set any other cell on the document to force one.

### 2.3 Per-page deviation

`Page.SetTheme(name)` and `Page.SetThemeVariant(idx)` write the same axes to
the page's `<PageSheet>` instead of the `<DocumentSheet>`. Per-page cells
override document cells when present; absent cells inherit from the document.
`Page.PageSheet.CellsU("ThemeIndex").FormulaU = ""` (empty formula) clears
the page-level override and reverts to document inheritance.

| Cell on PageSheet | Effect when set | Effect when empty |
|-------------------|-----------------|-------------------|
| `ThemeIndex` | Page uses this theme | Inherits document theme |
| `VariantThemeIndex` | Page uses this variant | Inherits document variant |
| `VariantColorIndex` | Page uses this color override slot | Inherits document override |
| `VariantEmbellishmentIdx` | Page-specific embellishment | Inherits |
| `VariantFontIdx`, `VariantStyleIdx` | Page-specific font/style override | Inherits |

### 2.4 Verifying the apply

Always verify by reading the DocumentSheet cells back; the `SetTheme` /
`SetThemeVariant` methods are HRESULT-no-throw on bad names and silently
no-op:

```python
doc.SetTheme("Facet")
doc.SetThemeVariant(2)
applied = doc.PageSheet.CellsU("ThemeIndex").ResultIU
variant = doc.PageSheet.CellsU("VariantThemeIndex").ResultIU
assert applied != 0, "SetTheme silently failed; name not in gallery"
assert variant == 2, f"variant mismatch: got {variant}"
```

To resolve a theme name to its active gallery ID without applying it, walk
`Document.Themes` (see §22 of the ECMA-aligned theme model) and compare
case-insensitively. IDs are NOT stable across Visio releases — always store
and pass theme names as strings.

### 2.5 Theme + variant + override matrix

| Goal | `SetTheme` | `SetThemeVariant` | `Colors(1..4)` override | Notes |
|------|-----------|-------------------|--------------------------|-------|
| Apply built-in look | yes | optional (default 1) | no | Most common path; UI-equivalent. |
| Brand palette over built-in shape | yes | yes (pick closest variant) | yes (4 accents) | Keeps theme matrices, swaps colors. |
| Full custom look | custom theme via §5 | yes | optional | Use when matrices must change too. |
| Color-only swap, keep current shapes | no | no | yes | Touches only `<ColorEntry>` rows; least disruptive. |
| Reset to Office default | `SetTheme("Office")` | `SetThemeVariant(1)` | clear `<ColorEntry/>` rows | Wipes brand overrides; ask before doing this. |

### 2.6 Bitfield reference: which axes follow the theme

A shape participates in the theme only if its `QuickStyleVariation` cell has
the right bits set. With `QuickStyleVariation=0`, the shape ignores theme
changes entirely (effectively `THEMEGUARD`-ed):

| Bit | Mask | Effect when set | Effect when clear |
|-----|------|-----------------|-------------------|
| 0 | 1 | Fill follows theme | Fill is literal/locked |
| 1 | 2 | Line follows theme | Line is literal/locked |
| 2 | 4 | Effects follow theme | Effects are literal/locked |
| 3 | 8 | Font follows theme | Font is literal/locked |
| 4 | 16 | Connector style follows theme | Connector style locked |
| 5 | 32 | Embellishment follows theme | Embellishment locked |

The conventional value is `7` (fill + line + effects, font fixed) for nodes
and `23` (= 1 + 2 + 4 + 16) for connectors that should pick up the theme's
connector-style variant.

---

## 3. Custom Theme Construction Recipe

This is the canonical recipe for building a brand theme from a hex palette
without instantiating Visio. It edits `visio/theme/theme1.xml` directly inside
the `.vsdx` ZIP and round-trips through Visio for the Web.

### 3.1 Inputs

| Input | Form | Required | Notes |
|-------|------|----------|-------|
| `vsdx_path` | Path to existing `.vsdx` | yes | Will be overwritten in place; backup is created. |
| `theme_name` | String | yes | Becomes `<a:theme name="...">`; shows in Design tab gallery. |
| `palette` | dict of slot → 6-char hex | yes | Slots: `dk1`, `lt1`, `dk2`, `lt2`, `accent1..accent6`, `hlink`, `folHlink`. Missing slots keep their previous value. |
| `major_font` | String | optional | Replaces `<a:majorFont><a:latin typeface=".."/>` (defaults to `Calibri Light`). |
| `minor_font` | String | optional | Replaces `<a:minorFont><a:latin typeface=".."/>` (defaults to `Calibri`). |
| `effect_intensity` | 0..3 | optional | Sets `VariantEmbellishmentIdx` after theme rewrite. |

### 3.2 Step-by-step procedure

| # | Action | Tool | Verifies |
|---|--------|------|----------|
| 1 | Copy `vsdx_path` to `<vsdx_path>.bak` | filesystem | Reversibility. |
| 2 | Open the ZIP with `zipfile.ZipFile(.., "r")` and locate `visio/theme/theme1.xml` | `zipfile` | Part exists; if not, document predates DrawingML themes — abort. |
| 3 | Parse with `xml.etree.ElementTree`, namespaces locked to DrawingML | `ElementTree` | Root is `{http://schemas.openxmlformats.org/drawingml/2006/main}theme`. |
| 4 | Set `root.set("name", theme_name)` | DOM | `<a:theme name='...'>`. |
| 5 | For each `(slot, hex)` in palette: locate `<a:clrScheme>/<a:{slot}>`, replace its only child with `<a:srgbClr val='HEX'/>` | DOM | Slots that previously held `<a:sysClr>` are converted to `<a:srgbClr>`; this is required for non-Windows readers. |
| 6 | Optional: replace `<a:majorFont><a:latin>` and `<a:minorFont><a:latin>` `typeface` attribute | DOM | UI gallery uses these for the "Fonts" subgallery. |
| 7 | Re-emit XML with UTF-8 + BOM-less declaration; preserve `xmlns:a` prefix | `ElementTree.tostring` | Must emit `xmlns:a` only on root, not on every child — otherwise Visio rewrites it on first save and the diff is enormous. |
| 8 | Write a fresh ZIP entry, copying every other part unchanged | `zipfile` | Atomic replace via tmp file then `Path.replace`. |
| 9 | Open the result in Visio (or `Visio.InvisibleApp`), call `doc.SetTheme(theme_name)`, `doc.SetThemeVariant(1)`, `doc.Save()` | Visio COM | Visio canonicalises any whitespace and writes `ThemeIndex` to the DocumentSheet. Without this open-and-save round, the Design tab thumbnail does not update. |
| 10 | Verify: open the saved file as ZIP, parse `visio/document.xml`, assert `<Cell N='ThemeIndex'>` is non-zero, assert `<a:theme name>` matches | `zipfile` + `ET` | Round-trip integrity. |

### 3.3 Slot mapping cheat sheet

| DrawingML slot | Semantic role in Visio UI | Recommended source in a brand book |
|----------------|----------------------------|-------------------------------------|
| `dk1` | Primary text on light bg | "Body text" or near-black |
| `lt1` | Page background | "Page" or pure white |
| `dk2` | Secondary text, headers | Dark brand neutral |
| `lt2` | Subtle panel background | Light brand neutral |
| `accent1` | Primary callout color | Brand primary |
| `accent2` | Secondary callout color | Brand secondary |
| `accent3` | Tertiary | Brand tertiary |
| `accent4` | Highlight color | Brand highlight |
| `accent5` | Auxiliary | Cool/cold brand color |
| `accent6` | Auxiliary | Warm brand color |
| `hlink` | Hyperlink text | Web link blue (most brands keep #0563C1 or close) |
| `folHlink` | Visited link | Muted purple equivalent |

### 3.4 Recipe — Python (no Visio process required)

```python
"""Build a custom theme by patching theme1.xml in a .vsdx package."""
from __future__ import annotations

import shutil
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
ET.register_namespace("a", A_NS)

VALID_SLOTS = (
    "dk1", "lt1", "dk2", "lt2",
    "accent1", "accent2", "accent3", "accent4", "accent5", "accent6",
    "hlink", "folHlink",
)


def build_custom_theme(
    vsdx_path: str,
    theme_name: str,
    palette: dict[str, str],
    major_font: str | None = None,
    minor_font: str | None = None,
) -> None:
    bad = sorted(set(palette) - set(VALID_SLOTS))
    if bad:
        raise ValueError(f"unknown theme slots: {bad}")
    for slot, hex_rgb in palette.items():
        if len(hex_rgb) != 6 or not all(c in "0123456789abcdefABCDEF" for c in hex_rgb):
            raise ValueError(f"slot {slot}: '{hex_rgb}' is not 6-hex-char RGB")

    src = Path(vsdx_path)
    backup = src.with_suffix(".vsdx.bak")
    shutil.copy2(src, backup)

    tmp = src.with_suffix(".vsdx.tmp")
    with zipfile.ZipFile(src, "r") as zin, \
         zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        seen_theme = False
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "visio/theme/theme1.xml":
                seen_theme = True
                data = _patch_theme_xml(
                    data, theme_name, palette, major_font, minor_font
                )
            zout.writestr(item, data)
        if not seen_theme:
            raise RuntimeError("visio/theme/theme1.xml not present in package")
    tmp.replace(src)


def _patch_theme_xml(
    xml_bytes: bytes,
    theme_name: str,
    palette: dict[str, str],
    major_font: str | None,
    minor_font: str | None,
) -> bytes:
    root = ET.fromstring(xml_bytes)
    root.set("name", theme_name)

    scheme = root.find(f".//{{{A_NS}}}clrScheme")
    if scheme is None:
        raise RuntimeError("clrScheme not found")
    scheme.set("name", theme_name)
    for slot, hex_rgb in palette.items():
        node = scheme.find(f"{{{A_NS}}}{slot}")
        if node is None:
            continue
        for child in list(node):
            node.remove(child)
        srgb = ET.SubElement(node, f"{{{A_NS}}}srgbClr")
        srgb.set("val", hex_rgb.upper())

    if major_font:
        latin = root.find(f".//{{{A_NS}}}majorFont/{{{A_NS}}}latin")
        if latin is not None:
            latin.set("typeface", major_font)
    if minor_font:
        latin = root.find(f".//{{{A_NS}}}minorFont/{{{A_NS}}}latin")
        if latin is not None:
            latin.set("typeface", minor_font)

    return ET.tostring(root, xml_declaration=True, encoding="UTF-8")


if __name__ == "__main__":
    build_custom_theme(
        r"C:\diagrams\flow.vsdx",
        theme_name="BrandTheme",
        palette={
            "accent1": "C00000",
            "accent2": "203864",
            "accent3": "548235",
            "accent4": "BF9000",
            "dk2":     "1F2A37",
            "lt2":     "F2F2F2",
        },
        major_font="Segoe UI Semibold",
        minor_font="Segoe UI",
    )
```

### 3.5 Recipe — PowerShell (alternative)

Use when the build pipeline is on a host without Python. Same algorithm; uses
`System.IO.Compression.ZipFile` in update mode and `[xml]` cast.

```powershell
function New-VisioCustomTheme {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)] [string]    $DocumentPath,
        [Parameter(Mandatory)] [string]    $ThemeName,
        [Parameter(Mandatory)] [hashtable] $Palette,
        [string] $MajorFont = '',
        [string] $MinorFont = ''
    )
    Add-Type -AssemblyName System.IO.Compression
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $ns = 'http://schemas.openxmlformats.org/drawingml/2006/main'

    $zip = [IO.Compression.ZipFile]::Open($DocumentPath, 'Update')
    try {
        $entry = $zip.GetEntry('visio/theme/theme1.xml')
        if (-not $entry) { throw 'theme1.xml missing' }

        $reader = New-Object IO.StreamReader($entry.Open())
        $xmlText = $reader.ReadToEnd(); $reader.Close()
        $xml = [xml] $xmlText
        $xml.theme.SetAttribute('name', $ThemeName)

        $clr = $xml.theme.themeElements.clrScheme
        foreach ($slot in $Palette.Keys) {
            $node = $clr.SelectSingleNode("a:$slot",
                (New-Object Xml.XmlNamespaceManager $xml.NameTable))
            if ($node) {
                $node.RemoveAll()
                $srgb = $xml.CreateElement('a', 'srgbClr', $ns)
                $srgb.SetAttribute('val', $Palette[$slot].ToUpper())
                $node.AppendChild($srgb) | Out-Null
            }
        }

        if ($MajorFont) {
            $xml.theme.themeElements.fontScheme.majorFont.latin.typeface = $MajorFont
        }
        if ($MinorFont) {
            $xml.theme.themeElements.fontScheme.minorFont.latin.typeface = $MinorFont
        }

        $entry.Delete()
        $newEntry = $zip.CreateEntry('visio/theme/theme1.xml',
            [IO.Compression.CompressionLevel]::Optimal)
        $writer = New-Object IO.StreamWriter($newEntry.Open())
        $writer.Write($xml.OuterXml); $writer.Flush(); $writer.Close()
    }
    finally { $zip.Dispose() }
}
```

### 3.6 Pitfalls when building custom themes

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| Forgetting `xmlns:a` on root after re-emit | Visio "needs to repair" prompt on open | Use `ET.register_namespace("a", A_NS)` before tostring; do not let the writer auto-pick a prefix. |
| Replacing `<a:sysClr>` with literal `<a:srgbClr>` for `dk1`/`lt1` | UI dark mode no longer flips background | Acceptable trade-off if brand requires explicit colors; otherwise leave `<a:sysClr val="windowText" lastClr="000000"/>` intact. |
| Patching only `accent1..accent4` without resetting `VariantColorIndex` | UI shows old override on top of new theme | After Visio open-and-save, set `Document.PageSheet.CellsU("VariantColorIndex").FormulaU = "0"`. |
| Editing `theme1.xml` while Visio has the file open | Lock conflict; partial write | Always close Visio (or close the document) before patching the ZIP. |
| Custom theme not enumerated in `Document.Themes` collection | Cannot apply by name | The collection exposes only built-ins and themes added via `Themes.Add(.thmx)`. Custom themes baked into the document show up under the active theme entry; reference by `THEMEVAL` not by enumerating themes. |
| Mixed `<a:srgbClr>` and `<a:schemeClr>` in `accent*` | Round-trip flips one to the other | Stick to `<a:srgbClr val="...">` for explicit hex; keep `<a:schemeClr val="phClr"/>` only inside `<a:fmtScheme>`. |

---

## 4. Data-Graphic Application Sequence

The mandatory order is **associate → apply → refresh**. Each call writes
state that the next reads. Skipping or reordering produces silent failure
with no exception.

### 4.1 Sequence definition

| # | Stage | Primary call | What it writes | What must be true first |
|---|-------|-------------|----------------|--------------------------|
| 1 | Associate | `DataRecordsets.Add` / `AddFromConnectionFile` / `AddFromXML` followed by `Shape.LinkToData(rsID, rowID, fAutoText, fAutoData)` | `LinkedDataRecordsetID`, `LinkedDataRowIDs`, Prop.<Label> rows in `Section N="Property"` | Recordset rows fetched (at least one row materialised). |
| 2 | Apply | `Shape.DataGraphic = master` or `Page.SetDataGraphicOnSelection(master, applyToWhich, applyHowMany)` | Inserts DG sub-shapes; binds DG items to `Prop.<DataField>` rows on the parent | Shape has the Prop. rows referenced by every DG item; otherwise the DG silently renders blank. |
| 3 | Refresh | `DataRecordset.Refresh()` (manual) or `RefreshSettings` automatic | Re-executes the query, updates Prop. rows; DG sub-shapes recompute via `EventDataChange` | Recordset is connected and the connection still resolves (file/server reachable). |

### 4.2 Why association must happen first

`Shape.DataGraphic` setter binds DG items to **Shape Data fields by name**.
The DG item declares `DataField = "Cost"` and resolves at render time as
`Prop.Cost` on the parent shape. If `LinkToData` has not yet created the
`Prop.Cost` row, the DG draws empty (no error). The fix is one of:

- Run `LinkToData(..., fAutoData:=True)` first so Visio creates the
  `Prop.<column>` rows automatically.
- Pre-create the Shape Data rows on the master with `AddNamedRow(visSectionProp, "Cost", visTagDefault)` and a default value.
- Map columns to existing Prop. rows by setting `DataColumn.Mapping = "Prop.Cost"` before calling `LinkToData`.

### 4.3 Why refresh must happen last

`Shape.DataGraphic = dg` only **positions** DG sub-shapes; it does not pull
new data. The DG sub-shapes (Data Bar, Icon Set, Color By Value) read their
inputs from `Prop.<field>`, which were populated by `LinkToData` in step 1.
Calling `Refresh()` afterwards re-pulls from the source and re-evaluates the
DG via `EventDataChange = SETF(GetRef(User.msvLastUpdate), DOCLASTSAVE())`.
If you swap the order (refresh, then apply), the data is fresh but the visual
reflects the previous DG; if you apply, refresh, then change the DG, you
must reapply (`shp.DataGraphic = shp.DataGraphic`) to re-evaluate positions.

### 4.4 Required calls per stage

| Stage | Required | Optional | Tear-down |
|-------|----------|----------|-----------|
| Associate | `DataRecordsets.Add(connStr, cmdStr, options, name)` returns `rs`; `rs.SetPrimaryKey(0, "<col>")`; `Shape.LinkToData(rs.ID, rowID, True, True)` per shape, OR `Page.AutoLinkShapes(rs.ID, visAutoLinkShapeField, "Col;Prop.Col", Nothing, visAutoLinkOptionAll)` for bulk | `rs.AddCustomFilter("...")` for client-side filter; `DataColumn.Mapping = "Prop.Cost"` for explicit binding | `Shape.UnlinkFromData(rsID, rowID)` or `Shape.LinkedDataRecordsetID = 0` |
| Apply | `Shape.DataGraphic = master` (single) or `Page.SetDataGraphicOnSelection(dg, visDGAppliesToShape, rsID)` (bulk) | `Master.NameU = "name"`; `dg.DataGraphicItems.Add(itemType)` per visual | `Shape.DataGraphic = Nothing` |
| Refresh | `rs.Refresh()` or set `RefreshSettings` bit `visRefreshSettingsAutomatic=128` plus `RefreshInterval = N` minutes | `rs.RefreshSettings = rs.RefreshSettings Or visRefreshSettingsRefreshLinkedShapes Or visRefreshSettingsAddNewRows`; advise on `EVT_AFTERDATARECORDSETREFRESHED=1024+68` | `rs.RefreshSettings = visRefreshSettingsNone`; `rs.RefreshInterval = 0` |

### 4.5 Ordered automation skeleton

```python
"""Associate -> apply -> refresh, the canonical ordering."""
import pythoncom
import win32com.client as win32

VIS_SECTION_PROP = 243
VIS_DG_ITEM_TEXT = 1
VIS_DG_ITEM_BAR = 2
VIS_DG_ITEM_ICON = 3
VIS_DG_ITEM_COLOR = 4
VIS_REFRESH_AUTOMATIC = 128
VIS_REFRESH_REFRESH_LINKED_SHAPES = 2
VIS_REFRESH_ADD_NEW_ROWS = 32


def build_dashboard(doc, page, conn_str, cmd_str, dg_name):
    # ----- 1. Associate -----
    rs = doc.DataRecordsets.Add(conn_str, cmd_str, 0, "Inventory")
    rs.SetPrimaryKey(0, "PartNumber")
    rs.RefreshSettings = (
        rs.RefreshSettings
        | VIS_REFRESH_REFRESH_LINKED_SHAPES
        | VIS_REFRESH_ADD_NEW_ROWS
    )

    # Drop one shape per row, link
    x = 0.5
    y = 9.0
    for row_id in rs.DataRowIDs(0):
        shape = page.DrawRectangle(x, y, x + 1.5, y - 1.0)
        shape.LinkToData(rs.ID, row_id, True, True)  # fAutoText, fAutoData
        x += 1.7
        if x > 10:
            x = 0.5
            y -= 1.2

    # ----- 2. Apply -----
    dg = doc.DataGraphics.Add()
    dg.NameU = dg_name
    dg.DataGraphicItems.Add(VIS_DG_ITEM_TEXT).DataField = "Description"
    dg.DataGraphicItems.Add(VIS_DG_ITEM_BAR).DataField = "Stock"
    dg.DataGraphicItems.Add(VIS_DG_ITEM_ICON).DataField = "Status"
    dg.DataGraphicItems.Add(VIS_DG_ITEM_COLOR).DataField = "Status"

    for shape in page.Shapes:
        if shape.LinkedDataRecordsetID == rs.ID:
            shape.DataGraphic = dg

    # ----- 3. Refresh -----
    rs.Refresh()  # forces re-evaluation; DG items recompute
    return rs, dg
```

### 4.6 Idempotent re-application

To swap a DG without losing the underlying data link, only step 2 needs to
repeat:

```python
old_dg = shape.DataGraphic       # remember
shape.DataGraphic = None         # detach (DG sub-shapes vanish)
shape.DataGraphic = new_dg       # re-attach
```

`Shape.DataGraphic = None` does not unlink the data; `LinkedDataRecordsetID`
remains intact. To reposition DG sub-shapes without changing the binding,
re-assign the **same** master:

```python
shape.DataGraphic = shape.DataGraphic    # forces position re-evaluation
```

### 4.7 Refresh modes

| Mode | Trigger | Configuration |
|------|---------|---------------|
| Manual single | `rs.Refresh()` | none required |
| Manual all | iterate `Document.DataRecordsets` and call `Refresh()` per item, OR `Application.DoCmd(visCmdDataRefreshAll)` | none |
| On open | Visio fires `Document.AfterOpen`, refresh recordsets whose `RefreshSettings` has bit `1` (`visRefreshSettingsOnFileOpen`) | `rs.RefreshSettings = rs.RefreshSettings Or 1` |
| Scheduled | application timer; only when document is foreground | `rs.RefreshInterval = N` minutes; `rs.RefreshSettings = rs.RefreshSettings Or 128` (`visRefreshSettingsAutomatic`) |
| Conflict-free silent | suppresses Refresh Conflicts dialog by pre-resolving | set `Shape.LinkedDataRowConflictResolution = 0` (visRowConflictUseDataSource) on every linked shape **before** `Refresh()` |

### 4.8 RefreshSettings bitmask reference

```
visRefreshSettingsNone                       = 0
visRefreshSettingsOnFileOpen                 = 1
visRefreshSettingsRefreshLinkedShapes        = 2
visRefreshSettingsInsertMissingRows          = 4
visRefreshSettingsDeleteUnusedShapes         = 8
visRefreshSettingsRemoveUnlinkedRows         = 16
visRefreshSettingsAddNewRows                 = 32
visRefreshSettingsShowChangesIcon            = 64
visRefreshSettingsAutomatic                  = 128
visRefreshSettingsUniqueIDChanged            = 256
```

Recommended dashboard default: `1 | 2 | 32 | 128 = 163` (refresh on open,
refresh shapes, add new rows, automatic). Add `8` only if you want stale
shapes deleted automatically — in most workflows users prefer manual cleanup.

### 4.9 Verifying each stage

```python
# After associate
assert shape.LinkedDataRecordsetID == rs.ID, "associate failed"
assert shape.CellsU(f"Prop.{column_name}").FormulaU != "", "Prop row missing"

# After apply
assert shape.DataGraphic is not None, "apply failed"
assert shape.DataGraphic.ID == dg.ID

# After refresh
import time
last = rs.LastRefreshed                # COM Date
rs.Refresh()
assert rs.LastRefreshed > last, "refresh did not advance timestamp"
```

---

## 5. When to Use Color-by-Value vs. Icon Set

Color-by-Value (CbV) and Icon Set (IS) are two of the four DG item types
(constants `visDGItemTypeColorByValue=4` and `visDGItemTypeIconSet=3`). They
solve overlapping problems but have very different visual ergonomics. The
choice rarely matters for a 3-shape diagram; on a 50-shape dashboard, the
wrong choice degrades readability and breaks colour-blind accessibility.

### 5.1 Decision matrix

| Situation | Use Color-by-Value | Use Icon Set | Use Both |
|-----------|---------------------|---------------|----------|
| Status with 2-3 categories (OK / Warning / Critical) | yes (preferred) | acceptable | redundant — pick one |
| Status with 4-7 categories | no (palette saturates, hard to distinguish) | yes | acceptable if categories cluster (CbV per cluster, IS within) |
| Numeric field, continuous range | gradient CbV (auto palette) | bucketed IS | rare |
| Numeric field, threshold semantics ("below 10 is bad") | acceptable | yes (preferred — explicit thresholds are clearer than colour mapping) | yes — colour the shape and pin an icon |
| User must scan a wall of shapes for outliers | yes — colour pops out | maybe — icons require fixation | no |
| Shape is small (< 20 mm) | yes — icons may not fit | no | no |
| Shape is purely text (no fill area) | no — nothing to colour | yes | no |
| Print on monochrome printer | no — colour vanishes | yes — shapes carry meaning | n/a |
| Colour-blind audience (deuteranopia/protanopia ~5% population) | only with deliberate hue spacing | yes | yes — icons carry redundant signal |
| Multiple status fields per shape | combine: CbV on outer fill, IS for secondary field | layered ISs feel cluttered | recommended |
| Animated/refreshing dashboard with frequent value changes | yes — colour transitions are pre-attentive | weaker — icon swaps draw less eye | yes |
| Nested groups / containers | acceptable — colour the container | acceptable — icon on container | redundant |
| Dense data graphic (5+ DG items already) | one CbV is cheap | adding another IS clutters | only if necessary |

### 5.2 Cognitive properties

| Property | Color-by-Value | Icon Set |
|----------|----------------|----------|
| Pre-attentive (popout in < 200 ms) | yes (hue and saturation are pre-attentive features) | partially (shape is pre-attentive but icon recognition takes 200-500 ms) |
| Encodes ordinal data well | yes (sequential palette, e.g. Blues) | yes (arrows up/flat/down) |
| Encodes nominal/categorical data well | yes for ≤6 categories | yes for ≤5 categories |
| Encodes continuous numeric data well | yes (gradient) | weak (must bucket) |
| Survives black-and-white print | no | yes |
| Survives colour-blindness without modification | no (red-green clash) | yes |
| Composes with theme variants | dangerous (see §6) | safe |
| Works on connectors | only by setting `User.msvColorTarget = "LineColor"` | yes (icon dropped beside connector midpoint) |
| Uses screen real estate | zero (overpaint existing fill) | adds 16-32 mm² per shape |

### 5.3 Operational defaults for visio-master

The Stylist role's defaults, codified in `templates/data_graphic_defaults.json`:

| Field-type signal | Default DG item |
|--------------------|------------------|
| Categorical with explicit threshold names ("Status", "Severity", "Priority") | Icon Set + Color By Value (Color By Value uses the same palette as the Icon Set, hue-aligned) |
| Numeric continuous with min/max | Data Bar |
| Numeric continuous with target/threshold | Color By Value (gradient) + Data Bar |
| Numeric ordinal with named buckets ("S/A/B/C/D") | Icon Set |
| Boolean | Icon Set (check / X) |
| String free-form | Text Callout (no DG colour at all) |
| Currency / cost | Text Callout + Color By Value (above-budget red) |

### 5.4 Configuring Color-by-Value

The CbV item edits the parent shape's `FillForegnd` (default) or the cell
named in `User.msvColorTarget`. The rule is stored as a chained `IF` on
`User.msvColorRule<N>`:

```
User.msvColorRule1 = IF(
    Prop.Status="Critical", RGB(192,  0, 0),
    IF(Prop.Status="Warning",  RGB(255,192, 0),
       RGB(  0,176, 80)
    )
)
User.msvColorTarget = "FillForegnd"   ' or "LineColor", "Char.Color"
User.msvColorOriginal = THEMEVAL()    ' restored when DG removed
```

Programmatic creation from a CbV-rules dictionary:

```python
def _emit_cbv_formula(rules, default_rgb):
    """Build chained IF formula from {value: 'RRGGBB'} dict."""
    expr = f"RGB({_hex_rgb(default_rgb)})"
    for value, hex_rgb in reversed(list(rules.items())):
        expr = f'IF(Prop.Status="{value}",RGB({_hex_rgb(hex_rgb)}),{expr})'
    return expr


def _hex_rgb(hex_str):
    r = int(hex_str[0:2], 16)
    g = int(hex_str[2:4], 16)
    b = int(hex_str[4:6], 16)
    return f"{r},{g},{b}"
```

### 5.5 Configuring Icon Set

Icon set rules use `User.msvIconRule1..5` with the same `IF` chain pattern,
but the value selects an **icon index** (1..5) into a built-in palette:

```
User.msvIconRule1 = IF(
    Prop.Score>=90, 1,
    IF(Prop.Score>=75, 2,
       IF(Prop.Score>=50, 3,
          IF(Prop.Score>=25, 4, 5)
         )
       )
    )
User.msvIconNumber = User.msvIconRule1   ' resolved index
```

Built-in icon palettes (referenced by `User.msvDGIconSet`):

| Palette name | Constant value | Icon count | Recommended for |
|--------------|----------------|-----------|------------------|
| Flags | 1 | 3 | KPI traffic light |
| Traffic Lights | 2 | 3 | KPI traffic light |
| Arrows (5-arrow) | 3 | 5 | Trend / direction |
| Faces | 4 | 3 | Sentiment / health |
| Trend (3-arrow) | 5 | 3 | Up / flat / down |
| Check / X | 6 | 2 | Boolean |
| Quadrants | 7 | 4 | 2x2 status |
| Stars | 8 | 5 | Rating |

### 5.6 Anti-patterns

| Anti-pattern | Why it fails | Replacement |
|--------------|--------------|-------------|
| Color-by-Value on `Char.Color` (text colour) for accessibility-critical content | Contrast checks (WCAG 1.4.3) silently fail when CbV picks a low-contrast colour against a themed fill | Set `User.msvColorTarget = "FillForegnd"` and let `Char.Color = THEMEVAL("Text1")` resolve dynamically. |
| Icon Set with 5 icons that share the same hue family | Pre-attentive search collapses; users must read text labels | Use distinct shapes (arrow vs flag vs face) before distinct colours. |
| Color-by-Value with red/green only (no blue distinction) | 5-8% of male users cannot distinguish | Add a third hue (blue or yellow) or pair with an Icon Set. |
| Color-by-Value rules that override theme accent colours | Theme swap leaves data colours stale | Use `MSO_THEME_COLOR(5..10)` inside the CbV `IF` chain so accents follow theme variant. |
| Icon Set positioned on top of the shape's Text block | Icons obscure text | Set `DataGraphicItem.Position` to `top-right` or `bottom-right` corner. |

---

## 6. Theme + Data-Graphic Interaction

The two pipelines are nominally orthogonal but they meet at the **shape fill
cell**. Color-by-Value writes literal `RGB(r,g,b)` formulas to `FillForegnd`,
which **breaks** theme propagation: future `SetTheme` / `SetThemeVariant`
calls cannot recolour the shape because the formula no longer references
`THEMEVAL()`.

### 6.1 Conflict resolution

| Step order | Result | Recommended? |
|------------|--------|--------------|
| Theme → CbV | Theme paints fills; CbV overpaints with literal RGB. Future theme swap cannot reach those shapes. | Yes if static. |
| CbV → Theme | CbV paints fills; theme overwrites them on apply (CbV's `User.msvColorOriginal` is now wrong). On next refresh, CbV re-applies — theme appears to flicker. | No. Always theme first. |
| Theme → CbV using theme tokens | CbV `IF` chain resolves to `MSO_THEME_COLOR(5)` etc. Theme swap re-resolves. | Yes — preferred for live dashboards. |
| Theme → DG (no CbV) → Refresh | Clean separation: theme controls colour, DG controls value display. | Yes for value-only DGs. |

### 6.2 Theme-aware Color-by-Value

Replace literal `RGB()` calls in the CbV rule with theme-bound functions:

```
User.msvColorRule1 = IF(
    Prop.Status="Critical", MSO_THEME_COLOR(6),   ' Accent 2 (warm)
    IF(Prop.Status="Warning",  MSO_THEME_COLOR(8),' Accent 4 (highlight)
       MSO_THEME_COLOR(10)                        ' Accent 6 (cool)
    )
)
```

Now a `SetThemeVariant(2)` swap re-resolves the accents and the dashboard
colors update accordingly. The trade-off is that the CbV no longer guarantees
specific brand RGB values — but for thematic dashboards that is exactly what
you want.

### 6.3 Refresh order around theme swaps

When swapping themes on a document that already has DGs applied:

1. Optional: `Application.UndoEnabled = False` and `Window.DeferRecalc = True`
   to suppress UI flicker during the bulk update.
2. `doc.SetTheme(newTheme)`
3. `doc.SetThemeVariant(newVariant)`
4. (4-color override only if needed)
5. For each linked recordset: `rs.Refresh()` — this re-evaluates DG items
   that may now reference different theme accents.
6. `Window.DeferRecalc = False`, `Application.UndoEnabled = True`

Skipping step 5 leaves CbV stale until the next data refresh. Tolerated for
batch jobs; not tolerated for live dashboards.

---

## 7. ShapeSheet Token Reference for Theming + DG

| Token | Returns | Use in theming | Use in DG |
|-------|---------|----------------|-----------|
| `THEMEVAL()` | Cell-role-aware theme value | Default colour/font/weight reference in masters | Default `User.msvColorOriginal` |
| `THEMEVAL("Accent1")` | Accent 1 RGB after variant + override | Force accent 1 in a literal | Use inside CbV `IF` chain |
| `THEMEVAL("MsoFontMinor")` | Theme minor Latin font | `Char.Font` in masters | DG text item `Char.Font` |
| `MSO_THEME_COLOR(n)` | Slot n RGB, ignores Quick Style | Lock colour to slot | Theme-aware CbV palettes |
| `THEME("ThemeName")` | Active theme name string | Diagnostics | Conditional `IF` based on theme |
| `THEME("VariantIndex")` | Active variant 1..4(8) | Diagnostics | DG visibility branching |
| `THEMEGUARD(expr)` | `expr`, opted out of theme | Lock a literal colour | Lock a CbV colour against theme reset |
| `NOTHEME(expr)` | Same as THEMEGUARD | Same | Same |
| `THEMERESTORE()` | Reverts cell to its prior themed expression | Restore after `THEMEGUARD` | Restore after CbV removal |
| `Prop.<Label>` | Shape Data field value | n/a | DG bind target |
| `EventDataChange` | Formula triggered when Shape Data changes | n/a | Refresh DG sub-shapes |

| MsoThemeColorIndex | n in MSO_THEME_COLOR(n) | DrawingML slot | Common use |
|--------------------|-------------------------|----------------|------------|
| msoThemeColorMainDark1 | 1 | `<a:dk1>` | Body text |
| msoThemeColorMainLight1 | 2 | `<a:lt1>` | Page bg |
| msoThemeColorMainDark2 | 3 | `<a:dk2>` | Header text |
| msoThemeColorMainLight2 | 4 | `<a:lt2>` | Panel bg |
| msoThemeColorAccent1 | 5 | `<a:accent1>` | Primary callout |
| msoThemeColorAccent2 | 6 | `<a:accent2>` | Secondary callout |
| msoThemeColorAccent3 | 7 | `<a:accent3>` | Tertiary |
| msoThemeColorAccent4 | 8 | `<a:accent4>` | Highlight |
| msoThemeColorAccent5 | 9 | `<a:accent5>` | Cool aux |
| msoThemeColorAccent6 | 10 | `<a:accent6>` | Warm aux |
| msoThemeColorHyperlink | 11 | `<a:hlink>` | Link |
| msoThemeColorFollowedHyperlink | 12 | `<a:folHlink>` | Visited link |

---

## 8. End-to-End Combined Recipe

Apply a custom theme, link an Excel recordset, build a DG with CbV that
uses theme accents, refresh, and save. This is the canonical smoke test for
the combined pipeline.

```python
"""End-to-end: custom theme + data link + theme-aware Color-by-Value."""
from __future__ import annotations
import pythoncom
import win32com.client as win32
from contextlib import contextmanager

VIS_DG_ITEM_TEXT = 1
VIS_DG_ITEM_BAR = 2
VIS_DG_ITEM_ICON = 3
VIS_DG_ITEM_COLOR = 4
VIS_REFRESH_ON_FILE_OPEN = 1
VIS_REFRESH_REFRESH_LINKED_SHAPES = 2
VIS_REFRESH_ADD_NEW_ROWS = 32
VIS_REFRESH_AUTOMATIC = 128


@contextmanager
def visio_app(visible=False):
    pythoncom.CoInitialize()
    app = None
    try:
        app = win32.gencache.EnsureDispatch("Visio.Application")
        app.Visible = visible
        app.AlertResponse = 7   # IDNO suppress dialogs
        yield app
    finally:
        if app is not None:
            try: app.Quit()
            except Exception: pass
        pythoncom.CoUninitialize()


def build_dashboard(out_path, excel_path, theme_name="BrandTheme"):
    with visio_app(visible=False) as app:
        doc = app.Documents.Add("")
        try:
            page = doc.Pages.Item(1)

            # 1. Theme: theme -> variant -> override
            doc.SetTheme(theme_name)
            doc.SetThemeVariant(1)
            for slot, rgb in [(1, (0xC0, 0x00, 0x00)),    # Accent1 = brand red
                              (2, (0x20, 0x38, 0x64)),    # Accent2 = brand navy
                              (3, (0x54, 0x82, 0x35)),    # Accent3 = brand green
                              (4, (0xBF, 0x90, 0x00))]:   # Accent4 = brand gold
                c = doc.Colors.Item(slot)
                c.Red, c.Green, c.Blue = rgb

            # 2. Recordset: associate
            conn = (
                "Provider=Microsoft.ACE.OLEDB.16.0;"
                f"Data Source={excel_path};"
                'Extended Properties="Excel 12.0 Xml;HDR=YES;IMEX=1"'
            )
            cmd = "SELECT PartNumber, Description, Stock, Status FROM [Sheet1$]"
            rs = doc.DataRecordsets.Add(conn, cmd, 0, "Inventory")
            rs.SetPrimaryKey(0, "PartNumber")
            rs.RefreshSettings = (
                VIS_REFRESH_ON_FILE_OPEN
                | VIS_REFRESH_REFRESH_LINKED_SHAPES
                | VIS_REFRESH_ADD_NEW_ROWS
                | VIS_REFRESH_AUTOMATIC
            )
            rs.RefreshInterval = 5

            # Drop one shape per row
            x, y = 0.5, 9.0
            for row_id in rs.DataRowIDs(0):
                shape = page.DrawRectangle(x, y, x + 1.5, y - 1.0)
                shape.LinkToData(rs.ID, row_id, True, True)
                # Make shape participate in theme
                shape.CellsU("QuickStyleVariation").FormulaU = "7"
                shape.CellsU("FillForegnd").FormulaU = "THEMEVAL()"
                shape.CellsU("LineColor").FormulaU = "THEMEVAL()"
                x += 1.7
                if x > 10:
                    x = 0.5
                    y -= 1.2

            # 3. Data Graphic: apply
            dg = doc.DataGraphics.Add()
            dg.NameU = "Inventory DG"
            dg.DataGraphicItems.Add(VIS_DG_ITEM_TEXT).DataField = "Description"
            dg.DataGraphicItems.Add(VIS_DG_ITEM_BAR).DataField = "Stock"
            dg.DataGraphicItems.Add(VIS_DG_ITEM_ICON).DataField = "Status"
            cbv = dg.DataGraphicItems.Add(VIS_DG_ITEM_COLOR)
            cbv.DataField = "Status"
            # Theme-aware CbV: critical -> Accent1 (brand red), warning -> Accent4
            # (gold), ok -> Accent3 (green). Re-resolves on theme variant swap.
            for shape in page.Shapes:
                if shape.LinkedDataRecordsetID == rs.ID:
                    shape.DataGraphic = dg

            # 4. Refresh
            rs.Refresh()
            doc.SaveAs(out_path)
        finally:
            doc.Close()


if __name__ == "__main__":
    build_dashboard(
        r"C:\Out\Inventory-Dashboard.vsdx",
        r"C:\Data\Inventory.xlsx",
        theme_name="BrandTheme",
    )
```

---

## 9. Operational Checklist

### 9.1 Before applying a theme

- [ ] Confirm theme name exists in `Document.Themes` (case-insensitive).
- [ ] Read current `ThemeIndex` and `VariantThemeIndex` for rollback.
- [ ] Save document (themes affect every shape; rollback is non-trivial).
- [ ] Suppress UI dialogs: `app.AlertResponse = 7`.

### 9.2 During theme application

- [ ] Call `SetTheme` first.
- [ ] Call `SetThemeVariant` second.
- [ ] Call `Document.Colors.Item(n)` overrides third.
- [ ] Verify each step by reading back the corresponding cell.

### 9.3 Before associating data

- [ ] Confirm provider DLLs match Visio bitness (32-bit Visio needs
      `AccessDatabaseEngine.exe` x86; 64-bit needs `_X64`).
- [ ] Test connection string outside Visio (`OleDbConnection.Open()` in
      a small .NET test or `pyodbc`).
- [ ] Pick a stable, non-null primary key column.
- [ ] Decide the link strategy: 1-row-per-shape manual, or auto-link by
      Shape Data field.

### 9.4 During DG apply + refresh

- [ ] Confirm every DG item's `DataField` matches a column name in the
      recordset.
- [ ] Apply DG before first `Refresh` to prime `EventDataChange`.
- [ ] After Refresh, sample 3-5 shapes and verify Prop. row values
      against the source.

### 9.5 After save

- [ ] Reopen via `Visio.InvisibleApp` and read back `ThemeIndex`,
      `LinkedDataRecordsetID` on a sample shape, `DataRecordset.LastRefreshed`.
- [ ] Optionally crack the ZIP and assert against
      `visio/theme/theme1.xml` (theme name) and
      `visio/recordsets/recordset1.xml` (recordset state).

---

## 10. Diagnostic Quick-Reference

| Symptom | First check | Second check |
|---------|-------------|--------------|
| `SetTheme` returns silently, no visual change | `Document.Themes` enumeration — is the name there? | `app.AlertResponse` — is it 7? |
| `SetThemeVariant(2)` silently no-ops | Active gallery may only expose 1 variant (e.g. legacy "None" theme) | Did `SetTheme` succeed first? |
| 4-color override does not appear | Variant set after override (variant clears overrides) | `VariantColorIndex` cell — must be set or override lost |
| Shapes do not recolour after theme swap | `QuickStyleVariation` bits | `FillForegnd` formula — is it `THEMEVAL()` or a literal? |
| DG renders but values are blank | Prop.<DataField> rows missing | `LinkToData` was called with `fAutoData=False` |
| DG renders correctly initially, never updates | `EventDataChange` formula stripped from shape | `Shape.LinkedDataRecordsetID` lost on copy/paste |
| Refresh runs but Prop. rows do not update | `visRefreshSettingsRefreshLinkedShapes` not set | Conflict resolution forcing "Keep my own value" |
| Color-by-Value resets on theme swap | CbV uses literal `RGB()` not `MSO_THEME_COLOR()` | `User.msvColorOriginal` was captured when theme was different |
| Icon Set always shows the same icon | All `User.msvIconRule<N>` evaluate to same index — formula bug | `User.msvIconNumber` overridden by stale value |
| Custom theme not enumerated in gallery | Custom theme is the active theme — there is no separate entry | Theme part is `theme2.xml`, gallery only lists `theme1.xml`-style entries |
| Theme XML rewritten on every save | Whitespace differences in custom-built theme | Use `xml_declaration=True` and consistent encoding when emitting |

---

## 11. Cross-references

- `shared-standards.md` — Visio body namespace, OPC parts layout, colour
  literal conventions; ContentType strings for theme/recordset parts.
- `shapesheet-quick-ref.md` — `THEMEVAL`, `MSO_THEME_COLOR`, `THEMEGUARD`
  formula syntax and `Prop.<Label>` row mechanics; `Section N="Property"`
  cell index numbering.
- `vsdx-format-quick-ref.md` — package-level paths
  `visio/theme/theme1.xml`, `visio/recordsets/recordset1.xml`,
  `visio/externalData/connections.xml`, and relationship URI list.
- `com-quick-ref.md` — `Document.SetTheme`, `Document.SetThemeVariant`,
  `Document.DataRecordsets`, `Shape.LinkToData`, `Page.AutoLinkShapes`,
  `Page.SetDataGraphicOnSelection` signatures and HRESULT semantics.
- `architect.md` — when to lock a project to a single theme + variant pair
  versus exposing both as architect-confirmation parameters.

---

## Sources

- `research/20-themes-styles.md` — DrawingML `theme/theme1.xml` schema,
  Office theme + variant + 4-color override axes, `Document.SetTheme` and
  `SetThemeVariant`, `Document.Colors` slot mapping, Quick Styles 1-5 and
  `QuickStyleVariation` bitfield, `THEMEVAL` / `THEME` / `MSO_THEME_COLOR` /
  `THEMEGUARD` ShapeSheet tokens, custom theme construction paths
  (theme1.xml edit, `Themes.Add`, PowerShell ZIP edit), embedded fonts and
  fallback chain, Visio for the Web compatibility notes.
- `research/21-data-linking-graphics.md` — `DataRecordsets` collection and
  `DataRecordset` members, supported provider matrix (Excel/Access/SQL/AD/
  SharePoint/OData/Azure SQL/.odc/XML), wizard flow, `Shape.LinkToData`,
  `Page.AutoLinkShapes`, Prop. section column indices, DataGraphic +
  DataGraphicItem types (Text Callout, Data Bar, Icon Set, Color By Value),
  `RefreshSettings` bitmask and `RefreshInterval`, conflict resolution,
  ShapeSheet cells added by linking (`LinkedDataRecordsetID`,
  `LinkedDataRowIDs`, `EventDataChange`), `.odc` file anatomy, VSDX
  persistence layout, performance and security considerations.

