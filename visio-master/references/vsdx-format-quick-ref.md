# VSDX Format Quick Reference

> One-screen lookup for the OPC anatomy of a `.vsdx` package: every part
> Visio writes, its content-type string, its relationship type URI, and a
> minimum-viable XML body. The second half is a set of safe-edit checklists
> keyed to the failure modes that produce "the file is corrupt and cannot
> be opened" or silent stale-cache bugs (`<RecalcDocument/>` omission,
> `[Content_Types].xml` drift, orphan rels). Every cell, attribute,
> content-type and rel URI is named exactly so you can grep for it.
>
> Scope: Visio 2013+ (`http://schemas.microsoft.com/office/visio/2012/main`).
> Legacy `.vdx`/`.vsd`/`.vss`/`.vst` are out of scope -- they are not OPC.

---

## 0. Ten-second mental model

1. `.vsdx` is a ZIP whose first central-directory entry is `[Content_Types].xml`.
2. Package rels (`_rels/.rels`) carries one `Relationship` of type
   `…/visio/2010/relationships/document` whose `Target` is `visio/document.xml`.
3. From `document.xml` you walk to every other Visio part via
   `visio/_rels/document.xml.rels` (pages, masters, theme, window,
   connections, recordsets, vbaProject, …).
4. Indices `pages/pages.xml` and `masters/masters.xml` hold one row per
   page/master; each row carries an inline `<Rel r:id="rIdN"/>` that cites
   an `Id` in the adjacent `_rels/<index>.xml.rels`.
5. After any structural edit, append `<RecalcDocument/>` directly inside
   `<VisioDocument>` so Visio rebuilds cached `V=` values from `F=` formulas.

Break any of those five contracts and Visio either refuses to open the
file or opens it with stale geometry/text/colour. Sections 6--8 are the
debug surface.

---

## 1. Top-level archive layout

```
<archive root>
├── [Content_Types].xml                      ← OPC, MUST be first ZIP entry
├── _rels/
│   └── .rels                                ← package-level relationships
├── docProps/
│   ├── app.xml                              ← extended-properties
│   ├── core.xml                             ← Dublin Core core-properties
│   ├── custom.xml                           ← user-defined properties (opt)
│   └── thumbnail.emf                        ← preview EMF/PNG/JPG (opt)
├── customXml/                               ← CustomXmlPart payloads (opt)
│   ├── item1.xml
│   ├── itemProps1.xml
│   └── _rels/item1.xml.rels
└── visio/
    ├── document.xml                         ← root Visio part (VisioDocument)
    ├── _rels/document.xml.rels              ← rels from document → siblings
    ├── pages/
    │   ├── pages.xml                        ← Pages index (root: Pages)
    │   ├── _rels/pages.xml.rels             ← Id → page#.xml mapping
    │   ├── _rels/page1.xml.rels             ← per-page rels (Image, ForeignData)
    │   └── page1.xml                        ← PageContents
    ├── masters/
    │   ├── masters.xml                      ← Masters index
    │   ├── _rels/masters.xml.rels           ← Id → master#.xml mapping
    │   ├── _rels/master1.xml.rels           ← per-master rels (Image)
    │   └── master1.xml                      ← MasterContents
    ├── theme/
    │   └── theme1.xml                       ← DrawingML <a:theme>
    ├── window.xml                           ← UI window state (Windows)
    ├── connections/connections.xml          ← DataConnections (opt)
    ├── datarecordsets/
    │   ├── recordsets.xml                   ← DataRecordSets index (opt)
    │   ├── _rels/recordsets.xml.rels
    │   └── recordset1.xml                   ← DataRowSet
    ├── extensions/                          ← solution-specific (opt)
    │   ├── extensions.xml
    │   ├── datarefreshconfig.xml
    │   ├── datavalidationrules.xml
    │   ├── datavalidationproperties.xml
    │   └── svgFilters.xml
    ├── comments.xml                         ← Comments (opt)
    ├── embeddings/oleObject1.bin            ← OLE objects (opt)
    ├── media/image1.png                     ← raster/EMF assets (opt)
    └── vbaProject.bin                       ← only in .vsdm/.vstm/.vssm
```

`[MS-VSDX] §2.3.1` lists the "web drawing" subset (App, Comments, Connections,
Content Type, Core, Custom, Document, Extensions, Image, Master, Masters,
Page, Pages, Recordsets, Rels, Theme). Desktop Visio additionally writes
Window, Solution, vbaProject, vbaData and customXml.

---

## 2. Per-part quick reference

Each subsection below states: the canonical part path, the OPC content-type
string for `[Content_Types].xml`, the relationship `Type` URI used to link
*to* that part, the part's root element + namespace, and a minimum-viable XML
body. Optional cells/attributes are noted inline.

### 2.1 `[Content_Types].xml`

| Property | Value |
| --- | --- |
| Mandatory | yes |
| Path | `/[Content_Types].xml` (always at archive root, must be first ZIP entry) |
| Content type (self) | n/a (special OPC part, never declared in itself) |
| Root element | `Types` |
| Namespace | `http://schemas.openxmlformats.org/package/2006/content-types` |

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml"  ContentType="application/xml"/>
  <Default Extension="emf"  ContentType="image/x-emf"/>
  <Override PartName="/visio/document.xml"     ContentType="application/vnd.ms-visio.drawing.main+xml"/>
  <Override PartName="/visio/pages/pages.xml"  ContentType="application/vnd.ms-visio.pages+xml"/>
  <Override PartName="/visio/pages/page1.xml"  ContentType="application/vnd.ms-visio.page+xml"/>
  <Override PartName="/visio/window.xml"       ContentType="application/vnd.ms-visio.windows+xml"/>
  <Override PartName="/docProps/app.xml"       ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
  <Override PartName="/docProps/core.xml"      ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
</Types>
```

Rules:
- `<Default>` matches by extension in lower-case; `<Override>` wins for the
  exact `PartName`.
- Every Visio XML part (document, pages, page, masters, master, theme,
  window, connections, recordsets, recordset, comments, extensions) needs an
  `<Override>` because the generic `application/xml` default would otherwise
  apply.
- `PartName` always begins with `/` and uses forward slashes regardless of
  host OS.

### 2.2 `_rels/.rels` (package relationships)

| Property | Value |
| --- | --- |
| Mandatory | yes |
| Path | `/_rels/.rels` |
| Content type | `application/vnd.openxmlformats-package.relationships+xml` |
| Declared via `<Default Extension="rels"/>` | yes (no `<Override>` needed) |
| Root element | `Relationships` |
| Namespace | `http://schemas.openxmlformats.org/package/2006/relationships` |

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1"
    Type="http://schemas.microsoft.com/visio/2010/relationships/document"
    Target="visio/document.xml"/>
  <Relationship Id="rId2"
    Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties"
    Target="docProps/core.xml"/>
  <Relationship Id="rId3"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties"
    Target="docProps/app.xml"/>
  <Relationship Id="rId4"
    Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/thumbnail"
    Target="docProps/thumbnail.emf"/>
</Relationships>
```

Each `Relationship` has `Id` (unique within the rels part), `Type` (URI),
`Target` (relative URI from the rels part's owner), and optional
`TargetMode="Internal|External"` (default `Internal`).

### 2.3 `docProps/core.xml`

| Property | Value |
| --- | --- |
| Mandatory | recommended (Office sets it on save) |
| Content type | `application/vnd.openxmlformats-package.core-properties+xml` |
| Rel URI (from package) | `http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties` |
| Root element | `cp:coreProperties` |
| Namespaces | `cp`, `dc`, `dcterms`, `dcmitype`, `xsi` (see below) |

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties
    xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
    xmlns:dc="http://purl.org/dc/elements/1.1/"
    xmlns:dcterms="http://purl.org/dc/terms/"
    xmlns:dcmitype="http://purl.org/dc/dcmitype/"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>Process Map</dc:title>
  <dc:creator>misaka10023</dc:creator>
  <cp:lastModifiedBy>misaka10023</cp:lastModifiedBy>
  <cp:revision>1</cp:revision>
  <dcterms:created  xsi:type="dcterms:W3CDTF">2026-06-14T10:00:00Z</dcterms:created>
  <dcterms:modified xsi:type="dcterms:W3CDTF">2026-06-14T11:30:42Z</dcterms:modified>
</cp:coreProperties>
```

Common children: `dc:title`, `dc:subject`, `dc:creator`, `cp:keywords`,
`dc:description`, `cp:lastModifiedBy`, `cp:revision`, `dcterms:created`,
`dcterms:modified`, `cp:category`, `cp:contentStatus`. The `xsi:type=
"dcterms:W3CDTF"` annotation is required by ISO/IEC 29500-2 on the date
fields.

### 2.4 `docProps/app.xml`

| Property | Value |
| --- | --- |
| Mandatory | recommended (controls File Explorer preview and Office search) |
| Content type | `application/vnd.openxmlformats-officedocument.extended-properties+xml` |
| Rel URI | `http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties` |
| Root element | `Properties` |
| Namespace (default) | `http://schemas.openxmlformats.org/officeDocument/2006/extended-properties` |
| Namespace (`vt`) | `http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes` |

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
            xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Template>BASFLO_M.VSTX</Template>
  <Application>Microsoft Visio</Application>
  <ScaleCrop>false</ScaleCrop>
  <HeadingPairs>
    <vt:vector size="2" baseType="variant">
      <vt:variant><vt:lpstr>Pages</vt:lpstr></vt:variant>
      <vt:variant><vt:i4>1</vt:i4></vt:variant>
    </vt:vector>
  </HeadingPairs>
  <TitlesOfParts>
    <vt:vector size="1" baseType="lpstr">
      <vt:lpstr>Page-1</vt:lpstr>
    </vt:vector>
  </TitlesOfParts>
  <LinksUpToDate>false</LinksUpToDate>
  <SharedDoc>false</SharedDoc>
  <HyperlinksChanged>false</HyperlinksChanged>
  <AppVersion>16.0300</AppVersion>
</Properties>
```

`HeadingPairs/vt:i4` MUST equal the count of pages in `TitlesOfParts`. When
you add or remove a page, update **both** the `vt:vector size=` attribute and
the integer count. File Explorer's preview pane silently fails if these
disagree.

### 2.5 `docProps/custom.xml` (optional)

| Content type | `application/vnd.openxmlformats-officedocument.custom-properties+xml` |
| --- | --- |
| Rel URI | `http://schemas.openxmlformats.org/officeDocument/2006/relationships/custom-properties` |
| Root | `Properties` (different namespace from `app.xml`) |
| Namespace | `http://schemas.openxmlformats.org/officeDocument/2006/custom-properties` |

```xml
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/custom-properties"
            xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <property fmtid="{D5CDD505-2E9C-101B-9397-08002B2CF9AE}" pid="2" name="ProjectId">
    <vt:lpwstr>P-2026-014</vt:lpwstr>
  </property>
  <property fmtid="{D5CDD505-2E9C-101B-9397-08002B2CF9AE}" pid="3" name="Reviewed">
    <vt:bool>true</vt:bool>
  </property>
</Properties>
```

`fmtid` is fixed at `{D5CDD505-2E9C-101B-9397-08002B2CF9AE}`; `pid` starts at
2 and increments. `vt:` payload types: `lpwstr`, `i4`, `r8`, `bool`,
`filetime`.

### 2.6 `visio/document.xml`

| Property | Value |
| --- | --- |
| Mandatory | yes (the `officeDocument` rel target) |
| Content type (`.vsdx`) | `application/vnd.ms-visio.drawing.main+xml` |
| Content type (`.vsdm`) | `application/vnd.ms-visio.drawing.macroEnabled.main+xml` |
| Content type (`.vstx`) | `application/vnd.ms-visio.template.main+xml` |
| Content type (`.vstm`) | `application/vnd.ms-visio.template.macroEnabled.main+xml` |
| Content type (`.vssx`) | `application/vnd.ms-visio.stencil.main+xml` |
| Content type (`.vssm`) | `application/vnd.ms-visio.stencil.macroEnabled.main+xml` |
| Rel URI from package | `http://schemas.microsoft.com/visio/2010/relationships/document` |
| Root element | `VisioDocument` |
| Namespace (default) | `http://schemas.microsoft.com/office/visio/2012/main` |
| Namespace (`r`) | `http://schemas.openxmlformats.org/officeDocument/2006/relationships` |

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<VisioDocument xmlns="http://schemas.microsoft.com/office/visio/2012/main"
               xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
               key="..." metric="0" DocLangID="1033">
  <DocumentSettings TopPage="0" DefaultTextStyle="3"
                    DefaultLineStyle="3" DefaultFillStyle="3"
                    DefaultGuideStyle="4">
    <GlyphSettingsEntry IX="0">Arial</GlyphSettingsEntry>
  </DocumentSettings>
  <Colors>
    <ColorEntry IX="0" RGB="#000000"/>
    <ColorEntry IX="1" RGB="#FFFFFF"/>
  </Colors>
  <FaceNames>
    <FaceName ID="1" Name="Arial"/>
  </FaceNames>
  <StyleSheets>
    <StyleSheet ID="0" NameU="No Style" Name="No Style"/>
    <StyleSheet ID="3" NameU="Normal" Name="Normal" LineStyle="0" FillStyle="0" TextStyle="0"/>
  </StyleSheets>
  <DocumentSheet NameU="TheDoc" Name="TheDoc"
                 LineStyle="3" FillStyle="3" TextStyle="3">
    <Cell N="OutputFormat" V="0"/>
    <Cell N="LockPreview"  V="0"/>
    <Cell N="DocLangID"    V="1033"/>
  </DocumentSheet>
  <EventList/>
  <RecalcDocument/>
</VisioDocument>
```

Key cells on `DocumentSettings`:

| Cell | Meaning |
| --- | --- |
| `TopPage` | Zero-based index of the page Visio opens to. |
| `DefaultTextStyle` / `DefaultLineStyle` / `DefaultFillStyle` / `DefaultGuideStyle` | StyleSheet IDs for new shapes' text, line, fill, guides. |
| `DynamicGridEnabled` / `ProtectStyles` / `SnapEnabled` / `GlueEnabled` | Boolean (`0`/`1`). |
| `SnapAngles` | List of angles for rotation snap. |

The empty `<RecalcDocument/>` tells Visio "rebuild every cached `V=` from
`F=` on next open". Always stamp it after any cell mutation.

### 2.7 `visio/_rels/document.xml.rels`

| Property | Value |
| --- | --- |
| Path | `/visio/_rels/document.xml.rels` |
| Content type | covered by `<Default Extension="rels"/>` |
| Root | `Relationships` |

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.microsoft.com/visio/2010/relationships/masters"     Target="masters/masters.xml"/>
  <Relationship Id="rId2" Type="http://schemas.microsoft.com/visio/2010/relationships/pages"       Target="pages/pages.xml"/>
  <Relationship Id="rId3" Type="http://schemas.microsoft.com/visio/2010/relationships/windows"     Target="window.xml"/>
  <Relationship Id="rId4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="theme/theme1.xml"/>
  <Relationship Id="rId5" Type="http://schemas.microsoft.com/visio/2010/relationships/connections" Target="connections/connections.xml"/>
  <Relationship Id="rId6" Type="http://schemas.microsoft.com/visio/2010/relationships/recordSets"  Target="datarecordsets/recordsets.xml"/>
  <Relationship Id="rId7" Type="http://schemas.microsoft.com/office/2006/relationships/vbaProject" Target="vbaProject.bin"/>
</Relationships>
```

`rId7` (vbaProject) is present **only** in `.vsdm`/`.vstm`/`.vssm`. `Target`
URIs are relative to the rels file's owner part (i.e. relative to
`visio/document.xml`), so `Target="pages/pages.xml"` resolves to
`/visio/pages/pages.xml`.

### 2.8 `visio/pages/pages.xml`

| Property | Value |
| --- | --- |
| Mandatory | yes for `.vsdx`/`.vsdm`/`.vstx`/`.vstm`; optional for `.vssx`/`.vssm` |
| Content type | `application/vnd.ms-visio.pages+xml` |
| Rel URI from `document.xml` | `http://schemas.microsoft.com/visio/2010/relationships/pages` |
| Root | `Pages` |
| Namespace | `http://schemas.microsoft.com/office/visio/2012/main` |
| `r` prefix | `http://schemas.openxmlformats.org/officeDocument/2006/relationships` |

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Pages xmlns="http://schemas.microsoft.com/office/visio/2012/main"
       xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <Page ID="0" NameU="Page-1" Name="Page-1"
        ViewScale="1" ViewCenterX="4.25" ViewCenterY="5.5">
    <PageSheet LineStyle="0" FillStyle="0" TextStyle="0">
      <Cell N="PageWidth"          V="8.5" U="IN"/>
      <Cell N="PageHeight"         V="11"  U="IN"/>
      <Cell N="ShdwOffsetX"        V="0.125"/>
      <Cell N="ShdwOffsetY"        V="-0.125"/>
      <Cell N="PageScale"          V="1" U="IN_F"/>
      <Cell N="DrawingScale"       V="1" U="IN_F"/>
      <Cell N="DrawingSizeType"    V="0"/>
      <Cell N="DrawingScaleType"   V="0"/>
      <Cell N="UIVisibility"       V="0"/>
      <Cell N="PrintPageOrientation" V="2"/>
    </PageSheet>
    <Rel r:id="rId1"/>
  </Page>
</Pages>
```

`<Rel r:id="rId1"/>` cites the `Id` of a `<Relationship>` in
`visio/pages/_rels/pages.xml.rels`. The two are joined by `Id` only -- not by
position.

| PageSheet cell | Default | Notes |
| --- | --- | --- |
| `PageWidth` / `PageHeight` | `8.5` / `11` (IN) or `21cm` / `29.7cm` | Logical page extent. |
| `ShdwOffsetX` / `ShdwOffsetY` | `0.125` / `-0.125` | Default shadow offset. |
| `PageScale` / `DrawingScale` | `1` / `1` | Numerator / denominator. |
| `DrawingSizeType` | `0` | `0`=printer paper, `1`=fit to drawing. |
| `DrawingScaleType` | `0` | `0`=no scale, `1`=arch, `2`=civil, `3`=metric. |
| `PrintPageOrientation` | `2` | `1`=portrait, `2`=landscape. |
| `UIVisibility` | `0` | `0`=visible, `1`=hidden background. |

Background pages set `Background="1"` on the `<Page>` row plus
`UIVisibility=1` on the PageSheet, and the foreground page's PageSheet adds
`<Cell N="BackPage" V="<bg page ID>"/>`.

### 2.9 `visio/pages/_rels/pages.xml.rels`

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.microsoft.com/visio/2010/relationships/page" Target="page1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.microsoft.com/visio/2010/relationships/page" Target="page2.xml"/>
</Relationships>
```

One row per page. The `Id` here is what `<Page><Rel r:id="…"/></Page>`
references back in `pages.xml`.

### 2.10 `visio/pages/page#.xml`

| Property | Value |
| --- | --- |
| Content type | `application/vnd.ms-visio.page+xml` |
| Rel URI from `pages.xml` | `http://schemas.microsoft.com/visio/2010/relationships/page` |
| Root | `PageContents` |
| Namespace | `http://schemas.microsoft.com/office/visio/2012/main` |

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<PageContents xmlns="http://schemas.microsoft.com/office/visio/2012/main"
              xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <Shapes>
    <Shape ID="1" NameU="Process" Name="Process.1" Type="Shape" Master="2"
           LineStyle="3" FillStyle="3" TextStyle="3">
      <Cell N="PinX"   V="2"   F="Inh"/>
      <Cell N="PinY"   V="9"   F="Inh"/>
      <Cell N="Width"  V="1.5" F="Inh"/>
      <Cell N="Height" V="0.75" F="Inh"/>
      <Cell N="LocPinX" F="Width*0.5"/>
      <Cell N="LocPinY" F="Height*0.5"/>
      <Cell N="Angle"  V="0"/>
      <Section N="Geometry" IX="0">
        <Cell N="NoFill" V="0"/>
        <Cell N="NoLine" V="0"/>
        <Row T="MoveTo" IX="1"><Cell N="X" V="0"/><Cell N="Y" V="0"/></Row>
        <Row T="LineTo" IX="2"><Cell N="X" F="Width"/><Cell N="Y" V="0"/></Row>
        <Row T="LineTo" IX="3"><Cell N="X" F="Width"/><Cell N="Y" F="Height"/></Row>
        <Row T="LineTo" IX="4"><Cell N="X" V="0"/><Cell N="Y" F="Height"/></Row>
        <Row T="LineTo" IX="5"><Cell N="X" V="0"/><Cell N="Y" V="0"/></Row>
      </Section>
      <Text>Start</Text>
    </Shape>
  </Shapes>
  <Connects>
    <Connect FromSheet="2" FromCell="BeginX" FromPart="9"
             ToSheet="1"   ToCell="PinX"     ToPart="3"/>
  </Connects>
</PageContents>
```

`<Shape>` attribute cheat-sheet:

| Attribute | Meaning |
| --- | --- |
| `ID` | Unique within the page. |
| `NameU` / `Name` | Universal vs. localized. |
| `Type` | `Shape` \| `Group` \| `Foreign` \| `Guide`. |
| `Master` | `Master/@ID` from `masters.xml`. |
| `MasterShape` | Sub-shape ID inside a master. |
| `LineStyle`/`FillStyle`/`TextStyle` | StyleSheet IDs. |
| `UniqueID` | Stable GUID across copy/paste. |

Cell grammar: every cell is `<Cell N="…" V="…" F="…" U="…" E="…"/>`.
`N` cell name; `V` cached value; `F` formula (special: `Inh` = inherit
master, `No Formula`); `U` unit (`IN`, `MM`, `IN_F`, `DEG`, `DA`, …);
`E` error code if formula failed.

Sections: `<Section N="…">` with rows keyed by `IX="0"` or `N="RowName"`.
Indexed sections (`Geometry`, `Connection`, `Character`, `Paragraph`, `Tabs`,
`Field`, `Annotation`, `Scratch`, `Layer`, `Control`, `Reviewer`) use `IX`.
Named sections (`User`, `Property` aka `Prop`, `Action`, `Hyperlink`,
`SmartTag`) use `N`.

`<Connects>` glue rows: `FromSheet` connector `Shape/@ID`; `FromCell`
`BeginX` (start) or `EndX` (end); `FromPart` `9`=begin, `12`=end;
`ToSheet` target `Shape/@ID`; `ToCell` `PinX` (dynamic glue) or
`Connections.X1` (static); `ToPart` `3`=whole shape (dynamic),
`100+i`=i-th connection point.

### 2.11 `visio/pages/_rels/page#.xml.rels` (only when the page references binaries)

Created on demand when a page hosts an embedded image, EMF, or OLE blob.

```xml
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"
    Target="../media/image1.png"/>
  <Relationship Id="rId2"
    Type="http://schemas.microsoft.com/visio/2010/relationships/foreignData"
    Target="../media/image2.emf"/>
  <Relationship Id="rId3"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/oleObject"
    Target="../embeddings/oleObject1.bin"/>
</Relationships>
```

The `Shape` cites the binary via `<ForeignData ForeignType="Bitmap" CompressionType="..." ...><Rel r:id="rId1"/></ForeignData>` inside the shape body.

### 2.12 `visio/masters/masters.xml`

| Property | Value |
| --- | --- |
| Mandatory | yes when `<Master>` rows exist |
| Content type | `application/vnd.ms-visio.masters+xml` |
| Rel URI from `document.xml` | `http://schemas.microsoft.com/visio/2010/relationships/masters` |
| Root | `Masters` |

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Masters xmlns="http://schemas.microsoft.com/office/visio/2012/main"
         xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <Master ID="2" NameU="Process" Name="Process"
          BaseID="{ABCDEFAB-1111-2222-3333-444444444444}"
          UniqueID="{12345678-1111-2222-3333-555555555555}"
          Hidden="0" MatchByName="0" PatternFlags="0"
          IconUpdate="1" IconSize="1" AlignName="2">
    <PageSheet>
      <Cell N="PageWidth"  V="1.5"  U="IN"/>
      <Cell N="PageHeight" V="1"    U="IN"/>
    </PageSheet>
    <Icon>iVBORw0KGgoAAAANSUhEUgAAAAQ...==</Icon>
    <Rel r:id="rId2"/>
  </Master>
  <MasterShortcut ID="0" NameU="Start/End" Name="Start/End"
                  BaseID="{...}" UniqueID="{...}"
                  IconSize="1" PatternFlags="0" Prompt=""
                  IconUpdate="1" AlignName="2"/>
</Masters>
```

| Master attribute | Meaning |
| --- | --- |
| `ID` | Local; cited by `<Shape Master="…"/>`. |
| `BaseID` / `UniqueID` | Lineage GUID (instances bind by this) / this-version GUID. |
| `Hidden` | `0` show in stencil, `1` hide. |
| `MatchByName` | Drives drag-drop dedupe. |
| `PatternFlags` | Bitfield: `1` line pattern, `2` fill pattern, `4` line ends. |
| `IconSize` | `1` 32x32, `2` 16x16, `3` 72x72, `4` custom. |
| `AlignName` | `0` left, `1` right, `2` center. |

`MasterShortcut` rows reference masters that physically live in another
stencil (`.vssx`) by `BaseID`. Visio resolves shortcuts by GUID at
instantiation time.

### 2.13 `visio/masters/_rels/masters.xml.rels`

```xml
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.microsoft.com/visio/2010/relationships/master" Target="master1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.microsoft.com/visio/2010/relationships/master" Target="master2.xml"/>
</Relationships>
```

### 2.14 `visio/masters/master#.xml`

| Property | Value |
| --- | --- |
| Content type | `application/vnd.ms-visio.master+xml` |
| Rel URI from `masters.xml` | `http://schemas.microsoft.com/visio/2010/relationships/master` |
| Root | `MasterContents` |

Structurally identical to `<PageContents>` -- same `<Shapes>` and
`<Connects>` tree. Master shapes typically use `Inh`-friendly formulas
(`F="Width*0.5"`) so instances inherit cleanly. Add a `Section
N="Connection"` whose rows define connection points (`X`, `Y`, `DirX`,
`DirY`, `Type`) for connectors to glue to. Add a `Section N="Property"`
for Shape Data fields, `Section N="User"` for scripting cells.

Master vs. instance: `F="Inh"` means "inherit from master". Sections in
the instance are diffed against the master's; use `<Row Del="1"/>` to
delete an inherited row.

### 2.15 `visio/theme/theme1.xml`

| Property | Value |
| --- | --- |
| Content type | `application/vnd.openxmlformats-officedocument.theme+xml` |
| Rel URI from `document.xml` | `http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme` |
| Root | `a:theme` |
| Namespace (`a`) | `http://schemas.openxmlformats.org/drawingml/2006/main` |
| Namespace (`thm15`, ext) | `http://schemas.microsoft.com/office/thememl/2012/main` |

Standard ECMA-376 DrawingML theme reused across Visio/Word/PowerPoint/Excel.

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Office Theme">
  <a:themeElements>
    <a:clrScheme name="Office">
      <a:dk1><a:sysClr val="windowText" lastClr="000000"/></a:dk1>
      <a:lt1><a:sysClr val="window"     lastClr="FFFFFF"/></a:lt1>
      <a:dk2><a:srgbClr val="44546A"/></a:dk2>
      <a:lt2><a:srgbClr val="E7E6E6"/></a:lt2>
      <a:accent1><a:srgbClr val="5B9BD5"/></a:accent1>
      <a:accent2><a:srgbClr val="ED7D31"/></a:accent2>
      <a:accent3><a:srgbClr val="A5A5A5"/></a:accent3>
      <a:accent4><a:srgbClr val="FFC000"/></a:accent4>
      <a:accent5><a:srgbClr val="4472C4"/></a:accent5>
      <a:accent6><a:srgbClr val="70AD47"/></a:accent6>
      <a:hlink><a:srgbClr val="0563C1"/></a:hlink>
      <a:folHlink><a:srgbClr val="954F72"/></a:folHlink>
    </a:clrScheme>
    <a:fontScheme name="Office">
      <a:majorFont><a:latin typeface="Calibri Light"/><a:ea typeface=""/><a:cs typeface=""/></a:majorFont>
      <a:minorFont><a:latin typeface="Calibri"/>      <a:ea typeface=""/><a:cs typeface=""/></a:minorFont>
    </a:fontScheme>
    <a:fmtScheme name="Office">
      <a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst>
      <a:lnStyleLst><a:ln w="6350" cap="flat" cmpd="sng" algn="ctr"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln></a:lnStyleLst>
      <a:effectStyleLst/>
      <a:bgFillStyleLst/>
    </a:fmtScheme>
  </a:themeElements>
  <a:objectDefaults/>
  <a:extraClrSchemeLst/>
  <a:extLst>
    <a:ext uri="{05A4C25C-085E-4340-85A3-A5531E510DB2}">
      <thm15:themeFamily xmlns:thm15="http://schemas.microsoft.com/office/thememl/2012/main"
                         name="Office Theme" id="{62F939B6-93AF-4DB8-9C6B-D6C7DFDC589F}"
                         vid="{4A3C46E8-61CC-4603-A589-7422A47A8E4A}"/>
    </a:ext>
  </a:extLst>
</a:theme>
```

Visio cells reference theme via `THEMEVAL()` formulas:

| Cell | Typical formula |
| --- | --- |
| `LineColor` | `F="THEMEGUARD(THEMEVAL())"` |
| `FillForegnd` | `F="THEMEGUARD(THEMEVAL())"` |
| `Char.Color` | `F="THEMEGUARD(THEMEVAL())"` |
| `LineColorTrans` / `FillForegndTrans` | derived from theme effect |
| `ThemeIndex` (PageSheet) | `-1` = document default; `0..N` = pin a variant |

Note: `ThemeIndex = -1` means "use document default", **not** "no theme".

### 2.16 `visio/window.xml`

| Property | Value |
| --- | --- |
| Content type | `application/vnd.ms-visio.windows+xml` |
| Rel URI from `document.xml` | `http://schemas.microsoft.com/visio/2010/relationships/windows` |
| Root | `Windows` |
| Mandatory | no -- safe to omit (Visio invents one on next open) |

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Windows xmlns="http://schemas.microsoft.com/office/visio/2012/main"
         ClientWidth="1920" ClientHeight="1080">
  <Window ID="0" WindowType="Drawing" WindowState="1073741824"
          ContainerType="Page" Page="0"
          ViewScale="-1" ViewCenterX="4.25" ViewCenterY="5.5"
          ShowRulers="1" ShowGrid="1" ShowGuides="1"
          ShowConnectionPoints="1" ShowPageBreaks="0"
          GlueSettings="9" SnapSettings="65849"
          DynamicGridEnabled="1" TabSplitterPos="0.5"
          ReadingOrder="0">
    <ShowInTree>0</ShowInTree>
  </Window>
</Windows>
```

`WindowState=1073741824` = `SW_SHOWMAXIMIZED | SW_SHOWNORMAL`.
`ViewScale="-1"` means "fit to window"; positive numbers are literal zoom
(`1.0` = 100%).

### 2.17 `visio/connections/connections.xml` (optional)

| Content type | `application/vnd.ms-visio.connections+xml` |
| --- | --- |
| Rel URI | `http://schemas.microsoft.com/visio/2010/relationships/connections` |
| Root | `DataConnections` |

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<DataConnections xmlns="http://schemas.microsoft.com/office/visio/2012/main"
                 NextID="2">
  <DataConnection ID="1"
    ConnectionString="Provider=Microsoft.ACE.OLEDB.16.0;Data Source=C:\Data\Inventory.xlsx;Extended Properties='Excel 12.0;HDR=YES'"
    Command="SELECT * FROM [Sheet1$]"
    CommandType="3"
    Timeout="0"
    FileName="C:\Data\Inventory.xlsx"
    AlwaysUseConnectionFile="0"/>
</DataConnections>
```

`CommandType` codes: `1` cube name, `2` table/sproc, `3` SQL text, `4`
default, `5` list of values.

### 2.18 `visio/datarecordsets/recordsets.xml` and `recordset#.xml` (optional)

| `recordsets.xml` content type | `application/vnd.ms-visio.recordsets+xml` |
| --- | --- |
| Rel URI from `document.xml` | `http://schemas.microsoft.com/visio/2010/relationships/recordSets` |
| Root | `DataRecordSets` |
| `recordset#.xml` content type | `application/vnd.ms-visio.recordset+xml` |
| Rel URI from `recordsets.xml` | `http://schemas.microsoft.com/visio/2010/relationships/recordSet` |
| `recordset#.xml` root | `DataRowSet` |

```xml
<DataRecordSets xmlns="http://schemas.microsoft.com/office/visio/2012/main"
                NextID="2" ActiveID="1">
  <DataRecordSet ID="1" Name="Inventory" ConnectionID="1"
                 Command="SELECT * FROM [Sheet1$]"
                 PrimaryKey="0xb0;PartNumber"
                 Refresh="1" NextRowID="247" OptionFlags="32">
    <Rel r:id="rId1" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"/>
  </DataRecordSet>
</DataRecordSets>
```

```xml
<DataRowSet xmlns="http://schemas.microsoft.com/office/visio/2012/main">
  <DataColumns>
    <DataColumn Name="PartNumber" Label="Part #" Type="0"/>
    <DataColumn Name="OnHand"     Label="On Hand" Type="1"/>
    <DataColumn Name="UnitCost"   Label="Cost"   Type="6" Format="$#,##0.00"/>
  </DataColumns>
  <DataRow ID="1">
    <Cell N="PartNumber" V="A-100"/>
    <Cell N="OnHand"     V="42"/>
    <Cell N="UnitCost"   V="3.95"/>
  </DataRow>
</DataRowSet>
```

`DataColumn/@Type`: `0`=string, `1`=integer, `2`=double, `3`=bool,
`4`=DateTime, `6`=currency.

### 2.19 `visio/comments.xml` (optional)

| Content type | `application/vnd.ms-visio.comments+xml` |
| --- | --- |
| Rel URI | `http://schemas.microsoft.com/visio/2010/relationships/comments` |
| Root | `Comments` |

```xml
<Comments xmlns="http://schemas.microsoft.com/office/visio/2012/main">
  <Authors>
    <Author ID="0" Name="misaka10023" Initials="MS"/>
  </Authors>
  <CommentList>
    <Comment ID="1" AuthorID="0" Date="2026-06-14T10:00:00Z"
             PageID="0" ShapeID="1">
      <CommentText>Add error handling to this step.</CommentText>
    </Comment>
  </CommentList>
</Comments>
```

### 2.20 `visio/extensions/*.xml` (optional, Visio Pro solutions)

| Path | Content type | Rel type URI |
| --- | --- | --- |
| `visio/extensions/extensions.xml` | `application/vnd.ms-visio.extensions+xml` | `http://schemas.microsoft.com/visio/2010/relationships/extensions` |
| `visio/extensions/datarefreshconfig.xml` | `application/vnd.ms-visio.extensions+xml` | (in extensions.xml) |
| `visio/extensions/datavalidationrules.xml` | `application/vnd.ms-visio.extensions+xml` | (in extensions.xml) |
| `visio/extensions/datavalidationproperties.xml` | `application/vnd.ms-visio.extensions+xml` | (in extensions.xml) |
| `visio/extensions/svgFilters.xml` | `application/vnd.ms-visio.extensions+xml` | (in extensions.xml) |

### 2.21 `visio/vbaProject.bin` (`.vsdm`/`.vstm`/`.vssm` only)

| Content type | `application/vnd.ms-office.vbaProject` |
| --- | --- |
| Rel URI from `document.xml` | `http://schemas.microsoft.com/office/2006/relationships/vbaProject` |
| Format | CFBF (Compound File Binary Format) -- binary, **never** decode as text |

A `.vsdm` differs from a `.vsdx` by exactly four facts:
1. Extension is `.vsdm`.
2. `[Content_Types].xml` `<Override>` for `/visio/document.xml` is
   `application/vnd.ms-visio.drawing.macroEnabled.main+xml`.
3. `[Content_Types].xml` adds `<Override PartName="/visio/vbaProject.bin"
   ContentType="application/vnd.ms-office.vbaProject"/>`.
4. `visio/_rels/document.xml.rels` adds the vbaProject relationship.
5. The literal CFBF blob exists at `/visio/vbaProject.bin`.

Renaming a `.vsdm` to `.vsdx` without removing items 2--5 still loads the VBA.

### 2.22 `visio/media/image#.{png,jpg,emf,wmf,svg}` and `visio/embeddings/oleObject#.bin`

| Asset | Content type (via `<Default>` or `<Override>`) | Rel type URI |
| --- | --- | --- |
| `media/image1.png` | `image/png` | `http://schemas.openxmlformats.org/officeDocument/2006/relationships/image` |
| `media/image1.jpg` | `image/jpeg` | same |
| `media/image1.emf` | `image/x-emf` | same |
| `media/image1.wmf` | `image/x-wmf` | same |
| `media/image1.svg` | `image/svg+xml` | same |
| `embeddings/oleObject1.bin` | `application/vnd.openxmlformats-officedocument.oleObject` (override) | `http://schemas.openxmlformats.org/officeDocument/2006/relationships/oleObject` |

Image references live on the page or master that displays them, in their
respective `_rels/page#.xml.rels` or `_rels/master#.xml.rels`.

---

## 3. Content-types matrix (full)

| PartName | ContentType (`<Override>` value) |
| --- | --- |
| `/visio/document.xml` (`.vsdx`) | `application/vnd.ms-visio.drawing.main+xml` |
| `/visio/document.xml` (`.vsdm`) | `application/vnd.ms-visio.drawing.macroEnabled.main+xml` |
| `/visio/document.xml` (`.vstx`) | `application/vnd.ms-visio.template.main+xml` |
| `/visio/document.xml` (`.vstm`) | `application/vnd.ms-visio.template.macroEnabled.main+xml` |
| `/visio/document.xml` (`.vssx`) | `application/vnd.ms-visio.stencil.main+xml` |
| `/visio/document.xml` (`.vssm`) | `application/vnd.ms-visio.stencil.macroEnabled.main+xml` |
| `/visio/pages/pages.xml` | `application/vnd.ms-visio.pages+xml` |
| `/visio/pages/page#.xml` | `application/vnd.ms-visio.page+xml` |
| `/visio/masters/masters.xml` | `application/vnd.ms-visio.masters+xml` |
| `/visio/masters/master#.xml` | `application/vnd.ms-visio.master+xml` |
| `/visio/theme/theme#.xml` | `application/vnd.openxmlformats-officedocument.theme+xml` |
| `/visio/window.xml` | `application/vnd.ms-visio.windows+xml` |
| `/visio/connections/connections.xml` | `application/vnd.ms-visio.connections+xml` |
| `/visio/datarecordsets/recordsets.xml` | `application/vnd.ms-visio.recordsets+xml` |
| `/visio/datarecordsets/recordset#.xml` | `application/vnd.ms-visio.recordset+xml` |
| `/visio/comments.xml` | `application/vnd.ms-visio.comments+xml` |
| `/visio/extensions/extensions.xml` | `application/vnd.ms-visio.extensions+xml` |
| `/visio/extensions/datarefreshconfig.xml` | `application/vnd.ms-visio.extensions+xml` |
| `/visio/extensions/datavalidationrules.xml` | `application/vnd.ms-visio.extensions+xml` |
| `/visio/extensions/datavalidationproperties.xml` | `application/vnd.ms-visio.extensions+xml` |
| `/visio/extensions/svgFilters.xml` | `application/vnd.ms-visio.extensions+xml` |
| `/visio/vbaProject.bin` | `application/vnd.ms-office.vbaProject` |
| `/visio/embeddings/oleObject#.bin` | `application/vnd.openxmlformats-officedocument.oleObject` |
| `/docProps/app.xml` | `application/vnd.openxmlformats-officedocument.extended-properties+xml` |
| `/docProps/core.xml` | `application/vnd.openxmlformats-package.core-properties+xml` |
| `/docProps/custom.xml` | `application/vnd.openxmlformats-officedocument.custom-properties+xml` |
| `/customXml/item#.xml` | `application/xml` (default; no override) |
| `/customXml/itemProps#.xml` | `application/vnd.openxmlformats-officedocument.customXmlProperties+xml` |

Default extensions Visio uses:

| `<Default Extension="…">` | ContentType |
| --- | --- |
| `rels` | `application/vnd.openxmlformats-package.relationships+xml` |
| `xml` | `application/xml` |
| `png` | `image/png` |
| `jpg` / `jpeg` | `image/jpeg` |
| `emf` | `image/x-emf` |
| `wmf` | `image/x-wmf` |
| `svg` | `image/svg+xml` |
| `bin` | `application/vnd.openxmlformats-officedocument.oleObject` (use override for vbaProject) |

---

## 4. Relationship-type URIs (full)

| Source → Target | `Type` URI |
| --- | --- |
| package → `visio/document.xml` | `http://schemas.microsoft.com/visio/2010/relationships/document` |
| `document.xml` → `pages/pages.xml` | `http://schemas.microsoft.com/visio/2010/relationships/pages` |
| `pages/pages.xml` → `pages/page#.xml` | `http://schemas.microsoft.com/visio/2010/relationships/page` |
| `document.xml` → `masters/masters.xml` | `http://schemas.microsoft.com/visio/2010/relationships/masters` |
| `masters/masters.xml` → `masters/master#.xml` | `http://schemas.microsoft.com/visio/2010/relationships/master` |
| `document.xml` → `theme/theme#.xml` | `http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme` |
| `document.xml` → `window.xml` | `http://schemas.microsoft.com/visio/2010/relationships/windows` |
| `document.xml` → `connections/connections.xml` | `http://schemas.microsoft.com/visio/2010/relationships/connections` |
| `document.xml` → `datarecordsets/recordsets.xml` | `http://schemas.microsoft.com/visio/2010/relationships/recordSets` |
| `recordsets.xml` → `recordset#.xml` | `http://schemas.microsoft.com/visio/2010/relationships/recordSet` |
| page/master → `media/image#.*` | `http://schemas.openxmlformats.org/officeDocument/2006/relationships/image` |
| page/master → external EMF/binary | `http://schemas.microsoft.com/visio/2010/relationships/foreignData` |
| page/master → `embeddings/oleObject#.bin` | `http://schemas.openxmlformats.org/officeDocument/2006/relationships/oleObject` |
| `document.xml` → `comments.xml` | `http://schemas.microsoft.com/visio/2010/relationships/comments` |
| `document.xml` → solution XML | `http://schemas.microsoft.com/visio/2010/relationships/solutionXML` |
| `document.xml` → `extensions/extensions.xml` | `http://schemas.microsoft.com/visio/2010/relationships/extensions` |
| `document.xml` → `vbaProject.bin` | `http://schemas.microsoft.com/office/2006/relationships/vbaProject` |
| package → `docProps/core.xml` | `http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties` |
| package → `docProps/app.xml` | `http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties` |
| package → `docProps/custom.xml` | `http://schemas.openxmlformats.org/officeDocument/2006/relationships/custom-properties` |
| package → `docProps/thumbnail.emf` | `http://schemas.openxmlformats.org/package/2006/relationships/metadata/thumbnail` |
| package → `customXml/item#.xml` | `http://schemas.openxmlformats.org/officeDocument/2006/relationships/customXml` |
| `customXml/item#.xml` → `customXml/itemProps#.xml` | `http://schemas.openxmlformats.org/officeDocument/2006/relationships/customXmlProps` |

`r` prefix used inside Visio XML always resolves to
`http://schemas.openxmlformats.org/officeDocument/2006/relationships`.

---

## 5. Namespace prefix table

| Prefix | URI | Used in |
| --- | --- | --- |
| (default OPC) | `http://schemas.openxmlformats.org/package/2006/content-types` | `[Content_Types].xml` |
| (default rels) | `http://schemas.openxmlformats.org/package/2006/relationships` | every `*.rels` |
| `r` | `http://schemas.openxmlformats.org/officeDocument/2006/relationships` | `<Rel r:id=…/>` inside Visio XML |
| `cp` / `dc` / `dcterms` / `dcmitype` | core-props, Dublin Core, dates, types | `docProps/core.xml` |
| `vt` | `http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes` | `app.xml`, `custom.xml` |
| (default) | `http://schemas.microsoft.com/office/visio/2012/main` | every Visio part |
| `a` | `http://schemas.openxmlformats.org/drawingml/2006/main` | `theme1.xml` |
| `thm15` | `http://schemas.microsoft.com/office/thememl/2012/main` | theme family extension |

VSDX root element is always `VisioDocument` in
`http://schemas.microsoft.com/office/visio/2012/main`. The legacy
`http://schemas.microsoft.com/visio/2003/core` namespace appears only in
`.vdx` (not OPC) -- never inside `.vsdx`.

---

## 6. Safe-edit checklists

These are decision flowcharts. Each lists the parts you MUST touch when
performing one mutation. Skipping a step yields one of: silent corruption
(file opens but with stale visuals), File Explorer preview failure, or
"the file is corrupt and cannot be opened" with no further hint.

### 6.1 General invariants (apply to every edit)

- [ ] `[Content_Types].xml` is the **first** entry in the ZIP central
      directory after rezip.
- [ ] Every part path used in `<Override PartName=…/>` starts with `/` and
      uses forward slashes.
- [ ] Every part you added/removed has a matching `<Override>` (added) or
      no `<Override>` (removed). If the part was covered only by
      `<Default Extension=…/>`, no override is required.
- [ ] Every `Relationship/@Id` is unique within its rels file.
- [ ] Every `<Rel r:id="rIdN"/>` inside Visio XML cites an `Id` defined in
      the **adjacent** `_rels/<owner>.rels`.
- [ ] All XML written without UTF-8 BOM (`UTF8Encoding(false)` in C#,
      `xml_declaration=True, encoding="UTF-8"` in Python ElementTree).
- [ ] Decimal separator is `.` even on `,`-locale OS.
- [ ] `xml:space="preserve"` retained on `<Text>` elements that hold
      leading/trailing whitespace.
- [ ] Binary parts (`.png`, `.emf`, `.bin`, `vbaProject.bin`) copied
      byte-exact, never re-encoded as text.
- [ ] After mutating any `<Cell>`, append `<RecalcDocument/>` directly
      inside `<VisioDocument>` (or `<RecalcPage/>` inside `<PageContents>`
      for a single page).

### 6.2 Adding a new page

- [ ] Allocate `Page/@ID` = max existing `Page/@ID` + 1.
- [ ] Append `<Page ID=…>` row to `visio/pages/pages.xml` with `NameU`,
      `Name`, `ViewScale`, `ViewCenterX/Y`, and an inline `<PageSheet>`
      containing at least `PageWidth` and `PageHeight`.
- [ ] Append `<Rel r:id="rIdN"/>` inside the new `<Page>`. Choose
      `rIdN` = max existing `Id` in `pages.xml.rels` + 1.
- [ ] Append `<Relationship Id="rIdN" Type="…/visio/2010/relationships/page"
      Target="pageN.xml"/>` to `visio/pages/_rels/pages.xml.rels`.
- [ ] Create `visio/pages/pageN.xml` with `<PageContents>` and an empty
      `<Shapes/>` (the `<Shapes>` element may be omitted entirely if the
      page has no shapes, but the root `<PageContents>` must exist).
- [ ] Add `<Override PartName="/visio/pages/pageN.xml"
      ContentType="application/vnd.ms-visio.page+xml"/>` to
      `[Content_Types].xml`.
- [ ] Update `docProps/app.xml`:
  - [ ] increment the `<vt:i4>` count inside `<HeadingPairs>`.
  - [ ] append `<vt:lpstr>PageName</vt:lpstr>` inside `<TitlesOfParts>` and
        update its `vt:vector size=` attribute.
- [ ] Stamp `<RecalcDocument/>` in `visio/document.xml`.

### 6.3 Removing a page

- [ ] Delete the `<Page>` row from `pages.xml`.
- [ ] Delete the matching `<Relationship>` from `pages/_rels/pages.xml.rels`.
- [ ] Delete the `pages/pageN.xml` file.
- [ ] Delete its `pages/_rels/pageN.xml.rels` file (if any).
- [ ] Delete the `<Override PartName="/visio/pages/pageN.xml"/>` in
      `[Content_Types].xml`.
- [ ] If the deleted page was a background page (`Background="1"`), search
      every other page's PageSheet for `<Cell N="BackPage" V="<that ID>"/>`
      and remove or repoint it.
- [ ] Update `docProps/app.xml` `<HeadingPairs>` count and
      `<TitlesOfParts>` vector.
- [ ] Stamp `<RecalcDocument/>` in `document.xml`.

### 6.4 Adding a master

- [ ] Allocate `Master/@ID` = max existing + 1.
- [ ] Generate fresh `BaseID` and `UniqueID` GUIDs (UUID v4).
- [ ] Append `<Master ID=…>` row to `visio/masters/masters.xml` with the
      `BaseID`, `UniqueID`, `NameU`, `Name`, plus inline `<PageSheet>` and
      `<Rel r:id="rIdN"/>`.
- [ ] Append matching `<Relationship Id="rIdN"
      Type="…/visio/2010/relationships/master" Target="masterN.xml"/>` to
      `masters/_rels/masters.xml.rels`.
- [ ] Create `masters/masterN.xml` with `<MasterContents>` containing
      `<Shapes>`.
- [ ] Add `<Override PartName="/visio/masters/masterN.xml"
      ContentType="application/vnd.ms-visio.master+xml"/>` to
      `[Content_Types].xml`.
- [ ] If this is the first master and `masters/masters.xml` did not exist,
      also add:
  - [ ] `<Override PartName="/visio/masters/masters.xml"
        ContentType="application/vnd.ms-visio.masters+xml"/>` to CT.
  - [ ] `<Relationship>` of type `…/visio/2010/relationships/masters` from
        `document.xml.rels` pointing to `masters/masters.xml`.
- [ ] Stamp `<RecalcDocument/>` in `document.xml`.

### 6.5 Removing a master

- [ ] **First** scan every `pages/page#.xml` for `<Shape Master="<that ID>"/>`
      and either repoint to a different master or delete those instance
      shapes. Visio renders orphaned instances as a red "X" placeholder.
- [ ] Remove the `<Master>` (or `<MasterShortcut>`) row.
- [ ] Remove the matching `<Relationship>` from `masters.xml.rels`.
- [ ] Delete `masters/masterN.xml` and its `_rels/masterN.xml.rels`.
- [ ] Remove the `<Override>` from `[Content_Types].xml`.
- [ ] Stamp `<RecalcDocument/>`.

### 6.6 Adding an embedded raster image to a page

- [ ] Drop the binary into `visio/media/imageN.png` (or `.jpg`/`.emf`/
      `.svg`).
- [ ] If the file extension does not yet have a `<Default>` entry, add one
      (e.g. `<Default Extension="png" ContentType="image/png"/>`). PNG/JPEG
      are usually already declared.
- [ ] Create or extend `visio/pages/_rels/pageN.xml.rels` with
      `<Relationship Id="rIdK"
      Type="…/officeDocument/2006/relationships/image"
      Target="../media/imageN.png"/>`.
- [ ] Inside the page shape, reference the image via
      `<Shape Type="Foreign" …><ForeignData ForeignType="Bitmap"
      CompressionType="PNG" CompressionLevel="0.5" ExtentX="…" ExtentY="…">
      <Rel r:id="rIdK"/></ForeignData></Shape>`.
- [ ] Stamp `<RecalcDocument/>`.

### 6.7 Replacing the document theme

- [ ] Overwrite `visio/theme/theme1.xml` (or add `theme2.xml` and update
      `document.xml.rels`).
- [ ] Verify the theme's `<a:extLst>` carries the `thm15:themeFamily`
      element with a unique GUID `id` and `vid`.
- [ ] If you bumped the theme part name, update `[Content_Types].xml`
      `<Override>` accordingly.
- [ ] Update PageSheet `<Cell N="ThemeIndex" V="-1"/>` if you want pages to
      follow the new default; pin a positive index per page to override.
- [ ] Stamp `<RecalcDocument/>` -- without it, cached colors don't repaint
      until the user toggles the theme manually.

### 6.8 Switching `.vsdx` ↔ `.vsdm` (macros)

To **add** macros (rename `.vsdx` → `.vsdm`):

- [ ] Rename file extension to `.vsdm`.
- [ ] Change `<Override PartName="/visio/document.xml" ContentType=…/>`
      from `…drawing.main+xml` to `…drawing.macroEnabled.main+xml`.
- [ ] Add `<Override PartName="/visio/vbaProject.bin"
      ContentType="application/vnd.ms-office.vbaProject"/>`.
- [ ] Add `<Relationship>` of type
      `http://schemas.microsoft.com/office/2006/relationships/vbaProject`
      to `visio/_rels/document.xml.rels` with `Target="vbaProject.bin"`.
- [ ] Drop the CFBF `vbaProject.bin` blob into `/visio/`.
- [ ] (Optional) Add `vbaData.xml` digital-signature companion + its rels.

To **remove** macros (rename `.vsdm` → `.vsdx`):

- [ ] Reverse all five steps above. Renaming the extension alone leaves
      the macros executable.

### 6.9 Linking a recordset

- [ ] Create or extend `visio/connections/connections.xml` with a
      `<DataConnection ID=…/>`.
- [ ] Add the `<Override PartName="/visio/connections/connections.xml"
      ContentType="application/vnd.ms-visio.connections+xml"/>` if not
      present.
- [ ] Add a rel of type `…/visio/2010/relationships/connections` from
      `document.xml.rels`.
- [ ] Create `visio/datarecordsets/recordsets.xml` (DataRecordSets root)
      and `recordset1.xml` (DataRowSet root).
- [ ] Add their `<Override>` entries to `[Content_Types].xml`
      (`…recordsets+xml` and `…recordset+xml`).
- [ ] Add the `recordSets` rel from `document.xml.rels`.
- [ ] Add the `recordSet` rel from `recordsets.xml.rels`.
- [ ] Stamp `<RecalcDocument/>`.

### 6.10 Other one-line edits

| Edit | Steps |
| --- | --- |
| Rename a page | Set `<Page NameU=… Name=…/>` in `pages.xml`; update matching `<vt:lpstr>` in `app.xml` `<TitlesOfParts>`; stamp `<RecalcDocument/>`. |
| Set start page | Set `DocumentSettings/@TopPage` in `document.xml` to zero-based page index; stamp `<RecalcDocument/>`. |
| Reset zoom | Set `Window/@ViewScale="-1"` in `window.xml`. Or delete `window.xml` plus its `<Override>` in CT and `windows` rel in `document.xml.rels`. |
| Strip background pages | For each `<Page Background="1"/>`: search every other PageSheet for `<Cell N="BackPage" V="<that ID>"/>`, delete or repoint, then apply checklist 6.3. |

---

## 7. ShapeSheet cells most often touched at file level

Reference only -- see `shapesheet-quick-ref.md` for the full cell catalogue,
including units, valid ranges, and formula syntax.

| Group | Cells |
| --- | --- |
| Shape transform | `PinX`, `PinY`, `LocPinX`, `LocPinY`, `Width`, `Height`, `Angle`, `FlipX`, `FlipY`, `ResizeMode`. |
| 1-D endpoints | `BeginX`, `BeginY`, `EndX`, `EndY`. |
| Fill / line / shadow | `FillForegnd`, `FillBkgnd`, `FillPattern`, `FillForegndTrans`, `LineColor`, `LineWeight`, `LinePattern`, `LineCap`, `Rounding`, `BeginArrow`, `EndArrow`, `BeginArrowSize`, `EndArrowSize`, `ShdwForegnd`, `ShdwPattern`, `ShdwOffsetX`, `ShdwOffsetY`, `ShdwType`, `ShdwScaleFactor`. |
| Theme | `ThemeIndex` (PageSheet; `-1` = doc default, NOT "no theme"), `QuickStyleType`, `QuickStyleVariation`, `QuickStyleFillColor`, `QuickStyleLineColor`, `QuickStyleEffectMatrix`, `QuickStyleFontColor`, `QuickStyleShadowColor`, `QuickStyleLineMatrix`, `QuickStyleFillMatrix`. |
| Text | `Char.Color`, `Char.Font`, `Char.Size`, `Char.Style`, `Char.AsianFont`, `Char.ComplexScriptFont`, `Para.HorzAlign` (`0` left, `1` center, `2` right, `3` justify), `VerticalAlign` (`0` top, `1` middle, `2` bottom), `TxtPinX`, `TxtPinY`, `TxtWidth`, `TxtHeight`, `TxtAngle`. |
| Routing (PageSheet) | `RouteStyle` (`0` right-angle, `1` straight, `9` center-to-center), `LineRouteExt`, `LineToLineX/Y`, `LineToNodeX/Y`, `AvenueSizeX/Y`. |

Closed-enum payload values used as `V=` literals:

| Cell | Values |
| --- | --- |
| `Connections.Type#` | `0` Inward, `1` Outward, `2` Inward+Outward (default). |
| `FillPattern` | `0` none, `1` solid, `2..40` pattern (`25` diagonal stripes, `27` crosshatch). |
| `LinePattern` | `0` none, `1` solid, `2` dashed, `3` dotted, `4` dash-dot, `5+` from `LineStyle`. |
| `BeginArrow`/`EndArrow` | `0` none, `1..45` built-ins (`4` filled triangle, `13` open arrow). |
| `ShdwType` | `0` simple drop, `1` oblique, `2` magnify. |
| `Property` row `Type` | `0` String, `1` Fixed list, `2` Number, `3` Boolean, `4` Variable list, `5` Date, `6` Duration, `7` Currency. |
| `GlueType` | `0` any, `1` walk away, `2` guide. |
| `DataColumn/@Type` | `0` string, `1` integer, `2` double, `3` bool, `4` DateTime, `6` currency. |
| `CommandType` | `1` cube, `2` table/sproc, `3` SQL text, `4` default, `5` value list. |

`Geometry.Row.T` types: `MoveTo`, `LineTo`, `ArcTo`, `EllipticalArcTo`,
`Ellipse`, `InfiniteLine`, `NURBSTo`, `PolylineTo`, `RelMoveTo`,
`RelLineTo`, `RelCubBezTo`, `RelQuadBezTo`, `RelEllipticalArcTo`,
`SplineStart`, `SplineKnot`.

`Connect.FromPart` codes: `0` none, `3` whole shape (dynamic glue,
"Center"), `4` left edge, `5` bottom, `6` right, `7` top, `9` begin
point (1-D), `12` end point (1-D), `100+i` i-th connection-point row.

When you set a literal `V=`, drop the `F=` attribute (or set
`F="No Formula"`) unless the formula should keep recomputing. After
patching, stamp `<RecalcDocument/>`.

---

## 8. Pitfalls and gotchas

| Symptom | Root cause | Fix |
| --- | --- | --- |
| "The file is corrupt and cannot be opened." | Added a part without a matching `<Override>` in `[Content_Types].xml`. | Add the override. |
| Same error, different file. | Added a `<Page>`/`<Master>` row but didn't update the corresponding `*.rels`. | Insert the `<Relationship>` with the matching `Id`. |
| Visio opens but page is blank. | `<PageContents>` exists but the `<Rel r:id=…/>` inside `<Page>` references an `Id` that doesn't exist in `pages.xml.rels`. | Make the IDs match. |
| Color/text changes don't take effect. | Edited `F=` formulas without stamping `<RecalcDocument/>`. | Append `<RecalcDocument/>` inside `<VisioDocument>`. |
| File Explorer preview pane shows nothing. | `docProps/app.xml` `<HeadingPairs>` count disagrees with `<TitlesOfParts>` size. | Make them match. |
| Macros still run after renaming `.vsdm` → `.vsdx`. | Content type for `document.xml` is still the macroEnabled variant **and** `vbaProject.bin` is still in the package. | Switch the Override and delete `vbaProject.bin` and its rels/content-type entry. |
| Diagonal text rendering on first paint. | Wrote XML with UTF-8 BOM. Some Office tools accept it; Visio's preview pipeline does not. | Disable BOM (`UTF8Encoding(false)` / `xml_declaration=True`). |
| `<Text>` losing leading/trailing spaces. | XML serializer stripped whitespace. | Preserve `xml:space="preserve"` on `<Text>`. |
| Numeric cell becoming `1,5` instead of `1.5`. | Ran value through `CultureInfo.CurrentCulture`. | Format with the invariant culture / `.` separator. |
| Visio shows a red "X" in place of a shape. | `<Shape Master="N"/>` references a master that was deleted. | Repoint or delete the orphan instance. |
| Two stencils' shapes share the same lineage after copy/paste. | Duplicated a master without regenerating `BaseID`. | Generate a fresh GUID v4 and assign to `BaseID` and `UniqueID`. |
| Cells edited via XML "stuck" at old values. | Forgot `<RecalcDocument/>` (file-level) or `<RecalcPage/>` (page-level). | Stamp recalc. |
| `pageN.xml` opened standalone shows fine but full file is corrupt. | Path in `Target=` uses `\\` instead of `/`. | Rewrite to forward slashes before computing the URI. |
| ZIP file rejected by SharePoint. | Central-directory CRC32 mismatch from a raw stream rewrite. | Use `ZipArchive`/`zipfile` so CRCs are recomputed. |
| Theme variant index `-1` looks wrong. | `-1` means "document default", not "no theme". | Use `<Cell N="ThemeIndex" V="0"/>` to pin variant 0. |
| Extension switched but icon didn't update. | `[Content_Types].xml` Override still references the old format. | Update Override to the new content-type string. |

---

## 9. Rezip recipe (minimum-viable patch loop, no COM)

1. Copy source `.vsdx` to a working path; never edit in place.
2. Unzip with `zipfile`/`ZipArchive` (UTF-8 names, forward slashes).
3. Patch XML with a namespace-aware parser. Edit `*.rels` alongside
   `*.xml` whenever you add/remove parts; update `[Content_Types].xml`
   overrides.
4. Rezip with `[Content_Types].xml` as the **first** central-directory
   entry; deflate level 6. Use a real ZIP library so CRC32 is recomputed.
5. Stamp `<RecalcDocument/>` inside `<VisioDocument>` (or `<RecalcPage/>`
   inside `<PageContents>` for single-page edits).

Encoding: UTF-8 **without** BOM (`UTF8Encoding(false)` in C#,
`xml_declaration=True, encoding="UTF-8"` in Python ElementTree). Replace
`\\` with `/` before computing OPC URIs. Copy binary parts (`.png`,
`.emf`, `.bin`, `vbaProject.bin`) byte-exact.

To detect the variant, search the `document.xml` Override for
`vnd.ms-visio.{drawing,template,stencil}(.macroEnabled)?.main+xml`. The
`macroEnabled` token flips `vsdx`→`vsdm`, `vstx`→`vstm`, `vssx`→`vssm`.

---

## Sources

1. `research/03-vsdx-file-format.md` -- canonical OPC anatomy, content
   type/rel URI tables, ShapeSheet cell grammar, and safe-edit recipe used
   as the primary source for sections 1--9 of this reference.
2. `research/07-python-vsdx-library.md` -- referenced for the rezip and
   recalc patterns in §9 (when the file was empty at write time, the
   Python recipe was sourced from `03-vsdx-file-format.md` §16).
3. `[MS-VSDX]: Visio Drawing (.vsdx) File Format` --
   <https://learn.microsoft.com/en-us/openspecs/office_file_formats/ms-vsdx/>
4. `[MS-VSDX] §2.3 Document parts` --
   <https://learn.microsoft.com/en-us/openspecs/office_file_formats/ms-vsdx/c1ca7e33-c9ae-4f8b-b2ff-c2fd9c1b5b18>
5. Open Packaging Conventions (ECMA-376 Part 2 / ISO/IEC 29500-2) --
   <https://www.ecma-international.org/publications-and-standards/standards/ecma-376/>
6. Visio file format reference (Visio 2013+) --
   <https://learn.microsoft.com/en-us/office/client-developer/visio/introduction-to-the-visio-file-format-vsdx>
7. ShapeSheet `Cell` element / `Geometry` / `Connection` schema --
   <https://learn.microsoft.com/en-us/office/client-developer/visio/cell-element-row-shapesheetvisio-xml>
8. `RecalcDocument` element reference --
   <https://learn.microsoft.com/en-us/office/client-developer/visio/recalcdocument-element-visiodocument-complextypevisio-xml>
9. DrawingML theme schema (`theme1.xml`) --
   <https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.drawing.theme>
10. `System.IO.Packaging` / OPC packaging in .NET --
    <https://learn.microsoft.com/en-us/dotnet/api/system.io.packaging.package>
11. Office VBA Project (`vbaProject.bin`) reference --
    <https://learn.microsoft.com/en-us/openspecs/office_file_formats/ms-ovba/575462ba-bf67-4190-9fac-c275523c75fc>

