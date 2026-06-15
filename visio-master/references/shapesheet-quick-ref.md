# ShapeSheet Quick Reference

> Dense runtime lookup for the Visio ShapeSheet. Contents: section index map,
> per-section cell catalog with default formulas, formula-language anatomy,
> and a one-row-per-function alphabet covering every formula built-in the
> Visio recalc engine exposes. Deep prose and source citations live in
> `research/02-shapesheet-cells-functions.md` and
> `research/26-custom-shape-development.md`.

Conventions used throughout this file:

- `cellref` — bare cell name, no quotes (`PinX`, `User.flag`, `Geometry1.X3`).
- `text` — quoted string literal (`"hello"`).
- `expr` — any expression (numeric, boolean, point, string).
- `geom` — symbolic path handle (`Geometry1.Path`); never expand by hand.
- `point` — Visio point built with `PNT(x,y)` or returned by `LOCTOPAR`,
  `LOCTOLOC`, `POINTALONGPATH`.
- Section / row / cell numeric ids come from `VisSectionIndices`,
  `VisRowIndices`, `VisCellIndices`. Prefer enum constants in code; integer
  literals listed here exist for OPC / VSDX serialization debugging only.

---

## 1. Section Index Map

Numeric ids from `VisSectionIndices`. `visSectionObject` (`1`) is a virtual
"object" container that gathers every fixed-row section the shape carries
inline (Shape Transform, 1-D Endpoints, Line / Fill / Text formats, Misc,
Glue Info, Protection, Events, Layer Membership, Foreign Image, Group
Properties). Probe with `Shape.SectionExists(section, fExistsLocally)`; add
with `Shape.AddSection(section)`; drop with `Shape.DeleteSection(section)`.

| # | Constant | Section name | Row schema | Owner |
|---|---|---|---|---|
| 1 | `visSectionObject` | Shape Transform, 1-D Endpoints, Line/Fill/Text Format, Glue Info, Misc, Protection, Events, Layer Membership, Foreign Image, Group Properties | fixed rows | Shape, Page, Master, Document, Style |
| 3 | `visSectionCharacter` | Character | dynamic rows, `Char.<col>[i]` | Shape |
| 4 | `visSectionParagraph` | Paragraph | dynamic | Shape |
| 5 | `visSectionTab` | Tabs | dynamic | Shape |
| 6 | `visSectionScratch` | Scratch | dynamic, columns A..F | Shape |
| 7 | `visSectionConnectionPts` | Connection Points | dynamic, optionally named | Shape |
| 8 | `visSectionAction` | Actions (right-click menu) | dynamic, named | Shape |
| 9 | `visSectionSmartTag` | Smart Tags | dynamic, named | Shape |
| 10..137 | `visSectionFirstComponent + i` | Geometry[i], i=0..127 | header row + vertex rows | Shape |
| 138 | `visSectionControls` | Controls (yellow handles) | dynamic, named | Shape |
| 139 | `visSectionLayer` | Layers | dynamic | Page |
| 140 | `visSectionField` | Text Fields | dynamic | Shape |
| 141 | `visSectionForeignImage` | Foreign Image Info | fixed | Shape |
| 142 | `visSectionHyperlink` | Hyperlinks | dynamic, named | Shape |
| 143 | `visSectionReviewer` | Reviewer | dynamic | Document |
| 144 | `visSectionAnnotation` | Annotations | dynamic | Page |
| 240 | `visSectionProp` | Shape Data / custom properties | dynamic, named | Shape |
| 242 | `visSectionUser` | User-defined Cells | dynamic, named | Shape |
| 243 | `visSectionConnectionABCD` | Legacy connection columns | rare | Shape |

### 1.1 Section discovery one-liner

```powershell
0..255 | ? { try { $shape.SectionExists($_, $false) } catch { $false } }
```

```python
present = [s for s in range(256) if shape.SectionExists(s, False)]
```

```vba
Dim s As Integer
For s = 0 To 255
    If shape.SectionExists(s, False) Then Debug.Print s
Next s
```

---

## 2. Cell Address Forms

| Form | Example | When |
|---|---|---|
| Same-shape, named | `Width`, `User.flag`, `Geometry1.X3`, `Scratch.A1`, `Char.Color[0]`, `Actions.Menu[2]` | Default in formulas |
| Cross-shape by id | `Sheet.5!PinX` | Reference another shape by its numeric `Shape.ID` |
| Cross-shape by name | `Sheet.Connector1!Width` | Use after `Shape.NameU` is set |
| Page sheet | `ThePage!PageWidth` | Page-level cells from any shape |
| Document sheet | `TheDoc!User.gridSize` | Doc-level user cells |
| Section short form | `Geom1.X3` | Engine accepts it; canonicalises on read to `Geometry1.X3` |
| By API integer triple | `Shape.CellsSRC(section, row, cell)` | Fastest path; no string parse |
| By universal name | `Shape.CellsU("PinX")` | Locale-independent; preferred over `.Cells` |

Cell read/write properties:

| Property | Read | Write | Notes |
|---|---|---|---|
| `Cell.Formula` / `FormulaU` | source text | source text | `U` suffix = universal English |
| `Cell.FormulaForce` / `FormulaForceU` | — | bypasses `IsInherited` / `Locks` | Use for force-overwrite tools |
| `Cell.Result(unit)` / `ResultIU` | numeric | — | `ResultIU` = internal units |
| `Cell.ResultStr(unit)` / `ResultStrU` | text | — | Formatted by Visio |
| `Cell.Section`, `Cell.Row`, `Cell.Column` | identity ints | — | Reflective |
| `Cell.RowName` / `RowNameU` | row label | row label | Named rows only |
| `Cell.IsConstant` | bool | — | Optimisation hint |
| `Cell.IsInherited` | bool | — | TRUE if inherited from master |
| `Cell.Dependents`, `Cell.Precedents` | `Cell[]` | — | Throws E_FAIL when empty |

---

## 3. Shape Transform — fixed cells (`visSectionObject`)

Locates, sizes, orients a 2-D shape. Length cells default to internal units
(inches); the recalc engine applies `Page.DrawingScale`.

| Cell | `visCellIndices` | Default formula | Purpose |
|---|---|---|---|
| `PinX` | `visXFormPinX` | `Width*0.5` | X of pin in parent coords |
| `PinY` | `visXFormPinY` | `Height*0.5` | Y of pin in parent coords |
| `Width` | `visXFormWidth` | shape-defined | Logical width |
| `Height` | `visXFormHeight` | shape-defined | Logical height |
| `LocPinX` | `visXFormLocPinX` | `Width*0.5` | X of pin in local coords |
| `LocPinY` | `visXFormLocPinY` | `Height*0.5` | Y of pin in local coords |
| `Angle` | `visXFormAngle` | `0 deg` | Rotation around the pin |
| `FlipX` | `visXFormFlipX` | `FALSE` | Mirror across local Y axis |
| `FlipY` | `visXFormFlipY` | `FALSE` | Mirror across local X axis |
| `ResizeMode` | `visXFormResizeMode` | `0` | 0=use group, 1=reposition, 2=scale w/ group |

Examples:

```text
PinX     = ThePage!PageWidth * 0.25
PinY     = ThePage!PageHeight * 0.5
Width    = GUARD(2 in)
Height   = GUARD(Width)                        # square aspect
Angle    = ATAN2(EndX-BeginX, EndY-BeginY)     # only on 1-D-derived shapes
LocPinX  = Width*0.5
LocPinY  = Height*0.5
```

---

## 4. 1-D Endpoints — only on 1-D shapes (`visSectionObject`)

Present when `Misc.ObjType=1` (`vis1DObj`). The engine derives `PinX`,
`PinY`, `Width`, `Angle` from these four cells; never write `PinX` directly
on a 1-D shape.

| Cell | Index | Meaning | Default |
|---|---|---|---|
| `BeginX` | `vis1DBeginX` | Tail X in parent coords | drag-derived |
| `BeginY` | `vis1DBeginY` | Tail Y | drag-derived |
| `EndX` | `vis1DEndX` | Head X | drag-derived |
| `EndY` | `vis1DEndY` | Head Y | drag-derived |

Examples:

```text
BeginX = PNTX(LOCTOPAR(PNT(0,0), Sheet.7!,ThePage!))
EndX   = PNTX(LOCTOPAR(PNT(Sheet.7!Width, Sheet.7!Height*0.5),
              Sheet.7!,ThePage!))
```

---

## 5. Geometry[i] — `visSectionFirstComponent + i`, dynamic rows

A shape may carry up to 128 `Geometry` sections. Header row 0 (type
`visTagComponent`) controls fill/stroke/visibility; subsequent vertex rows
draw the path.

### 5.1 Geometry header (row 0)

| Cell | `visCellIndices` | Type | Purpose |
|---|---|---|---|
| `NoFill` | `visCompNoFill` | bool | Skip fill |
| `NoLine` | `visCompNoLine` | bool | Skip stroke |
| `NoShow` | `visCompNoShow` | bool | Hide path entirely |
| `NoSnap` | `visCompNoSnap` | bool | Disable vertex snap |
| `NoQuickDrag` | `visCompNoQuickDrag` | bool | Skip during fast-drag preview |

```text
Geometry1.NoFill     = FALSE
Geometry1.NoLine     = FALSE
Geometry1.NoShow     = NOT(User.ShowDecorator)
```

### 5.2 Vertex row tags (`VisRowTags`)

| Tag | Constant | Value | Columns (X,Y,A,B,C,D,E,F) |
|---|---|---|---|
| `MoveTo` | `visTagMoveTo` | 1 | X, Y |
| `LineTo` | `visTagLineTo` | 2 | X, Y |
| `ArcTo` | `visTagArcTo` | 3 | X, Y, A=bow |
| `InfiniteLine` | `visTagInfiniteLine` | 4 | X, Y, A, B |
| `EllipticalArcTo` | `visTagEllipticalArcTo` | 5 | X, Y, A=ctrl X, B=ctrl Y, C=angle, D=ratio |
| `Ellipse` | `visTagEllipse` | 6 | X, Y, A, B, C, D |
| `NURBSTo` | `visTagNURBSTo` | 7 | X, Y, A=knotLast, B=weightLast, C=knotPrev, D=weightPrev, E=knots, F=weights |
| `PolylineTo` | `visTagPolylineTo` | 8 | X, Y, A=`POLYLINE(...)` |
| `SplineStart` | `visTagSplineBeg` | 9 | X, Y, A=knot, B=knotLast, C=degree |
| `SplineKnot` | `visTagSplineSpan` | 10 | X, Y, A=knot |
| `RelMoveTo` | `visTagRelMoveTo` | 11 | X, Y (uses `Width*` / `Height*` form) |
| `RelLineTo` | `visTagRelLineTo` | 12 | X, Y |
| `RelEllipticalArcTo` / `RelArcTo` / `RelEllipse` | `visTagLoc*` | 13..14 | as base + Rel scaling |

Examples:

```text
# Triangle: MoveTo, LineTo, LineTo, LineTo (close)
Geometry1.X1 = 0          Geometry1.Y1 = 0          # MoveTo
Geometry1.X2 = Width      Geometry1.Y2 = 0          # LineTo
Geometry1.X3 = Width*0.5  Geometry1.Y3 = Height     # LineTo
Geometry1.X4 = Geometry1.X1
Geometry1.Y4 = Geometry1.Y1                          # close

# Rounded corner via ArcTo (positive bow = arc bulges outward)
Geometry1.X5 = Width*0.75 Geometry1.Y5 = Height*0.5
Geometry1.A5 = 0.1 in                                # bow

# Quarter circle via EllipticalArcTo
Geometry1.X6 = Width      Geometry1.Y6 = Height
Geometry1.A6 = Width*0.5  Geometry1.B6 = Height
Geometry1.C6 = 0 deg      Geometry1.D6 = 1
```

---

## 6. Connection Points (`visSectionConnectionPts`, section 7)

Each row exposes one glue target. Address as `Connections.X1`,
`Connections.<RowName>.X` after `Section(7).Row(i).NameU = "Top"`.

| Cell | Index | Default | Purpose |
|---|---|---|---|
| `X` | `visCnnctX` (0) | `Width*0.5` | Anchor X |
| `Y` | `visCnnctY` (1) | `Height*0.5` | Anchor Y |
| `DirX` | `visCnnctDirX` (2) | `0` | Outward X vector |
| `DirY` | `visCnnctDirY` (3) | `0` | Outward Y vector |
| `Type` | `visCnnctType` (4) | `0` | 0=Inward, 1=Outward, 2=InwardOutward |
| `AutoGen` | `visCnnctAutoGen` (5) | `FALSE` | Engine-auto-generated marker |
| `Name` | `visCnnctName` | `""` | Optional row label |

Type values from `VisCellVals`:

| Value | Constant | Meaning |
|---|---|---|
| 0 | `visCnnctTypeInward` | 1-D endpoint glues *to* this point |
| 1 | `visCnnctTypeOutward` | This shape's connector source endpoint |
| 2 | `visCnnctTypeInwardOutward` | Bidirectional; `DirX/DirY` set router preference |

Parametric four-cardinal pattern:

```text
Connections.Top.X    = Width*0.5      Connections.Top.Y    = Height
Connections.Top.DirX = 0              Connections.Top.DirY = 1
Connections.Top.Type = 2

Connections.Right.X    = Width        Connections.Right.Y    = Height*0.5
Connections.Right.DirX = 1            Connections.Right.DirY = 0
Connections.Right.Type = 2

Connections.Bottom.X = Width*0.5      Connections.Bottom.Y = 0
Connections.Bottom.DirX = 0           Connections.Bottom.DirY = -1
Connections.Bottom.Type = 2

Connections.Left.X = 0                Connections.Left.Y = Height*0.5
Connections.Left.DirX = -1            Connections.Left.DirY = 0
Connections.Left.Type = 2
```

---

## 7. Controls (`visSectionControls`, section 138)

Yellow drag-handles. Each row owns a position and a constraint pair.

| Cell | Index | Purpose |
|---|---|---|
| `X` | `visCtlX` | Live position X |
| `Y` | `visCtlY` | Live position Y |
| `XCon` | `visCtlXCon` | Constraint id (see below) |
| `YCon` | `visCtlYCon` | Constraint id (see below) |
| `XDyn` | `visCtlXDynamics` | Drag-tracking X seed |
| `YDyn` | `visCtlYDynamics` | Drag-tracking Y seed |
| `Tip` | `visCtlTip` | Tooltip string |
| `Glue` | `visCtlGlue` | TRUE: control snaps to other shapes |

Constraint ids:

| Id | Behaviour |
|---|---|
| 0 | Proportional to width/height |
| 1 | Locked horizontal axis |
| 2 | Locked vertical axis |
| 3 | Clamped horizontal in [0, Width] |
| 4 | Clamped vertical in [0, Height] |
| 5 | Clamped both axes |
| 6 | Infinite (no clamp, no proportional) |
| 7 | Fixed (read-only) |

Angle-control wedge pattern:

```text
Controls.X1   = Width*0.75
Controls.Y1   = Height*0.5
Controls.XCon = 0   Controls.YCon = 0
Controls.Tip  = "Drag to set angle"
Angle         = ATAN2(Controls.X1-PinX, Controls.Y1-PinY)
```

---

## 8. User-defined Cells (`visSectionUser`, section 242)

Two cells per row: `Value` and `Prompt`. Row name is the access key.

| Cell | Index | Purpose |
|---|---|---|
| `Value` | `visUserValue` (0) | Expression / state |
| `Prompt` | `visUserPrompt` (1) | Description, shown as ShapeSheet tooltip |

Examples:

```text
User.HalfWidth          = Width*0.5
User.HalfWidth.Prompt   = "Cached half-width to share among formulas"
User.ShowDecorator      = TRUE
User.AccentColor        = THEMEVAL("AccentColor")
User.Stencil            = DOCNAME(TRUE)
```

---

## 9. Shape Data / Prop (`visSectionProp`, section 240)

End-user-facing custom properties. Edited through the *Shape Data* pane.

| Cell | Index | Purpose |
|---|---|---|
| `Value` | `visCustPropsValue` | Stored value |
| `Prompt` | `visCustPropsPrompt` | Tooltip / help |
| `Label` | `visCustPropsLabel` | Display label |
| `Format` | `visCustPropsFormat` | `FORMAT()` picture string |
| `Type` | `visCustPropsType` | 0=String, 1=Fixed list, 2=Number, 3=Bool, 4=Currency, 5=Date, 6=Duration, 7=Variable list |
| `LangID` | `visCustPropsLangID` | Locale id |
| `Calendar` | `visCustPropsCalendar` | Calendar id (for Date) |
| `SortKey` | `visCustPropsSortKey` | Sort order in pane |
| `Invisible` | `visCustPropsInvis` | Hide from pane |
| `Verify` | `visCustPropsVerify` | Validate against type rules on entry |
| `Ask` | `visCustPropsAsk` | Prompt for value on shape drop |

Examples:

```text
Prop.Hostname            = "srv-001"
Prop.Hostname.Label      = "Hostname"
Prop.Hostname.Type       = 0
Prop.Hostname.SortKey    = 1

Prop.PowerWatts          = 250
Prop.PowerWatts.Type     = 2
Prop.PowerWatts.Format   = "0 W"
Prop.PowerWatts.Verify   = TRUE

Prop.Tier                = "T1"
Prop.Tier.Type           = 1                      # fixed list
Prop.Tier.Format         = "T1;T2;T3"
```

---

## 10. Scratch (`visSectionScratch`, section 6)

Six numeric working columns per row (`A`, `B`, `C`, `D`, `E`, `F`). No
built-in names — addressed positionally as `Scratch.A1` through
`Scratch.F8`. Use as a fast scratchpad inside one shape.

```text
Scratch.A1 = SQRT(Width^2 + Height^2)        # diagonal length
Scratch.B1 = ATAN2(Height, Width)            # diagonal angle
Geometry2.X1 = Width*0.5 + Scratch.A1*0.4*COS(Scratch.B1)
```

---

## 11. Actions (`visSectionAction`, section 8)

Right-click menu rows. Action cell formula fires on click.

| Cell | Index | Purpose |
|---|---|---|
| `Action` | `visActionAction` (0) | Formula run on click |
| `Menu` | `visActionMenu` (1) | Caption; `&` flags accelerator |
| `Checked` | `visActionChecked` (2) | Show check mark when TRUE |
| `Disabled` | `visActionDisabled` (3) | Grey out when TRUE |
| `ReadMyCell` | `visActionReadMyCell` (4) | Force re-evaluation for menus |
| `BeginGroup` | `visActionBeginGroup` (5) | Separator above |
| `Invisible` | `visActionInvisible` (6) | Hide from menu |
| `SortKey` | `visActionSortKey` (7) | Numeric ordering |
| `ButtonFace` | `visActionButtonFace` (8) | Built-in icon id |
| `TagName` | `visActionTagName` (9) | Smart-tag link by name |
| `FlyoutChild` | `visActionFlyoutChild` (10) | Mark this as flyout child |

Common `Action` formula bodies:

| Pattern | Effect |
|---|---|
| `SETF(GETREF(User.X), <expr>)` | Write into `User.X` |
| `RUNADDON("AddonName")` | Invoke a registered Visio add-on |
| `RUNADDONWARGS("Name","args")` | Add-on with command-line |
| `CALLTHIS("ThisDocument.OnX","")` | Call a VBA macro on the doc |
| `OPENFILE("C:\\plan.vsdx")` | Open external file |
| `HYPERLINK("RowName")` | Follow Hyperlinks row |
| `DOCMD(commandID)` | Run Visio command id (e.g. 1312) |
| `GOTOPAGE(2)` | Navigate to page index |

Toggle decorator pattern:

```text
Actions.ToggleDeco.Action  = SETF(GETREF(User.ShowDeco), NOT(User.ShowDeco))
Actions.ToggleDeco.Menu    = "Show &decorator"
Actions.ToggleDeco.Checked = User.ShowDeco
```

---

## 12. Smart Tags (`visSectionSmartTag`, section 9)

Floating UI badges. One row per tag. Anchors via formula; click triggers an
`Actions.<RowName>` row of the same name.

| Cell | Index | Purpose |
|---|---|---|
| `X` | `visSmartTagX` (0) | Anchor X |
| `Y` | `visSmartTagY` (1) | Anchor Y |
| `XJustify` | `visSmartTagXJustify` (2) | 0=left, 1=center, 2=right |
| `YJustify` | `visSmartTagYJustify` (3) | 0=top, 1=middle, 2=bottom |
| `DisplayMode` | `visSmartTagDisplayMode` (4) | 0=Mouse over shape, 1=Mouse over tag, 2=Always |
| `ButtonFace` | `visSmartTagButtonFace` (5) | Built-in icon id |
| `Disabled` | `visSmartTagDisabled` (6) | Boolean expression |
| `Description` | `visSmartTagDescription` (7) | Tooltip |
| `TagName` | `visSmartTagTagName` (8) | Identifier for add-ins |

```text
SmartTags.Edit.X            = Width
SmartTags.Edit.Y            = Height
SmartTags.Edit.XJustify     = 1
SmartTags.Edit.YJustify     = 1
SmartTags.Edit.DisplayMode  = 0
SmartTags.Edit.Description  = "Edit server"
```

---

## 13. Events (`visSectionObject`, fixed cells)

Six well-known event hooks fired by the engine.

| Cell | Index | When fires |
|---|---|---|
| `EventDblClick` | `visEvtCellDblClick` | User double-clicks the shape |
| `EventXFMod` | `visEvtCellXFMod` | `PinX/PinY/Width/Height/Angle` change |
| `EventDrop` | `visEvtCellDrop` | Shape dropped onto a page |
| `EventMultiDrop` | `visEvtCellMultiDrop` | Multiple shapes dropped together |
| `TheData` | `visEvtCellTheData` | Custom data event hook |
| `TheText` | `visEvtCellTheText` | Text changed |

`EventDblClick` formula vocabulary:

| Formula | Effect |
|---|---|
| `DEFAULTEVENT()` | Visio default — open group, edit text |
| `OPENTEXTWIN()` | Open the text editor on the shape |
| `OPENGROUPWIN()` | Open the group window |
| `OPENSHEETWIN()` | Open the ShapeSheet window |
| `RUNADDON("name")` | Run a registered add-on |
| `RUNADDONWARGS("name","args")` | Add-on with arguments |
| `DOCMD(1312)` | Run Visio command id 1312 (`visCmdShapeProperties`) |
| `OPENFILE("C:\\path")` | Launch external file |
| `HYPERLINK("RowName")` | Follow a Hyperlinks row |
| `GOTOPAGE(2)` | Jump to a drawing page |
| `CALLTHIS("Macro","")` | Run VBA in document |

---

## 14. Glue Info (`visSectionObject`)

Glue book-keeping; routing and walking-glue control.

| Cell | Index | Purpose |
|---|---|---|
| `WalkPreference` | `visWalkPreference` | 0=auto, 1=horiz first, 2=vert first |
| `BegTrigger` | `visBegTrigger` | Engine-written when begin endpoint glues |
| `EndTrigger` | `visEndTrigger` | Engine-written when end endpoint glues |
| `GlueType` | `visGlueType` | 0=allow, 1=no glue, 2=walking glue |

---

## 15. Protection (`visSectionObject`)

Boolean lock cells. Setting any to TRUE forbids the matching gesture.

| Cell | Constant | Lock |
|---|---|---|
| `LockMoveX` | `visLockMoveX` | Disallow horizontal move |
| `LockMoveY` | `visLockMoveY` | Disallow vertical move |
| `LockWidth` | `visLockWidth` | Disallow width change |
| `LockHeight` | `visLockHeight` | Disallow height change |
| `LockAspect` | `visLockAspect` | Maintain aspect ratio |
| `LockDelete` | `visLockDelete` | Disallow deletion |
| `LockBegin` | `visLockBegin` | Lock 1-D begin endpoint |
| `LockEnd` | `visLockEnd` | Lock 1-D end endpoint |
| `LockRotate` | `visLockRotate` | Disallow rotation |
| `LockCrop` | `visLockCrop` | Disallow image crop |
| `LockVtxEdit` | `visLockVtxEdit` | Disallow vertex edit |
| `LockTextEdit` | `visLockTextEdit` | Disallow text edit |
| `LockFormat` | `visLockFormat` | Disallow format change |
| `LockGroup` | `visLockGroup` | Disallow grouping |
| `LockCalcWH` | `visLockCalcWH` | Disallow auto width/height calc |
| `LockSelect` | `visLockSelect` | Make shape unselectable |
| `LockCustProp` | `visLockCustProp` | Disallow Shape Data UI edit |
| `LockThemeColors` | `visLockThemeColors` | Disallow theme colour override |
| `LockThemeEffects` | `visLockThemeEffects` | Disallow theme effect override |
| `LockFromGroupFormat` | `visLockFromGroupFormat` | Children ignore group formatting |

---

## 16. Misc (`visSectionObject`)

Catch-all. Highlights:

| Cell | Purpose |
|---|---|
| `ObjType` | 0 default, 1 (1-D), 2 (2-D), 4 group only |
| `NonPrinting` | TRUE hides at print |
| `NoCtlHandles` | Suppress control handles |
| `NoAlignBox` | Hide alignment box |
| `UpdateAlignBox` | Redraw on size change |
| `NoLiveDynamics` | Force ghost dragging |
| `DynFeedback` | 0=none, 1=line, 2=arrow during drag |
| `Calendar` | Calendar id for date cells |
| `LangID` | Locale id for text cells |
| `ShdwShow` | Shadow-show modifier |
| `IsDropSource` | TRUE marks shape as master drop source / container |
| `Comment` | Free-text designer note |
| `ShapeKeywords` | Indexed search keywords |

---

## 17. Group Properties (`visSectionObject`, group only)

Six cells govern group editing. Address as `Cells("SelectMode")`.

| Cell | Values | Effect |
|---|---|---|
| `SelectMode` | 0/1/2 | 0=group only, 1=group then sub-shape, 2=member shapes |
| `DisplayMode` | 0/1/2 | 0=draw group behind, 1=in front, 2=hide group geometry |
| `IsTextEditTarget` | TRUE/FALSE | Typing inside the group routes here |
| `DontMoveChildren` | TRUE/FALSE | Lock children during group move |
| `IsDropSource` | TRUE/FALSE | Container behaviour on drop |
| `LockFromGroupFormat` | TRUE/FALSE | Children ignore group format |

---

## 18. Layer Membership

Shape cell `LayerMember` is a semicolon-separated list of layer indices
(`"0;3;7"`). Layers themselves live in a per-page `Layers` section
(`visSectionLayer`, 139) on the page sheet.

Page-level Layers row cells:

| Cell | Purpose |
|---|---|
| `Name` | Layer name (localised) |
| `NameUniv` | Layer name (universal) |
| `Color` | Override colour |
| `ColorTrans` | Colour transparency |
| `Status` | 0/1/2 layer state bitmask |
| `Visible` | TRUE shows layer |
| `Print` | TRUE prints layer |
| `Active` | TRUE makes drop-target layer |
| `Lock` | TRUE locks shapes on layer |
| `Snap` | TRUE allows snap to layer |
| `Glue` | TRUE allows glue to layer |

---

## 19. Hyperlinks (`visSectionHyperlink`, section 142)

| Cell | Purpose |
|---|---|
| `Address` | URL or path; usually `HYPERLINK("...")` |
| `SubAddress` | Anchor / page name |
| `ExtraInfo` | Query parameters |
| `Description` | Tooltip / display text |
| `Frame` | Target frame for HTML |
| `NewWindow` | TRUE forces new browser window |
| `Default` | Marks the default hyperlink (clicked on F5 / shape) |
| `Invisible` | Hide from right-click menu |
| `SortKey` | Order within menu |

```text
Hyperlinks.Source.Address     = "https://wiki.contoso.local/hosts/" & Prop.Hostname
Hyperlinks.Source.Description = "Asset wiki"
Hyperlinks.Source.Default     = TRUE
```

---

## 20. Formula Language Anatomy

### 20.1 Operators (precedence high to low)

```
unary    +  -  NOT
power    ^
mul      *  /  %
add      +  -
concat   &
compare  =  <  >  <=  >=  <>
and      AND
or       OR
```

`<>` is "not equal". `&` is string concatenation; both operands coerced to
text.

### 20.2 Unit suffixes

A naked number defaults to inches for length cells, degrees for angle cells,
unitless for everything else.

| Suffix | Meaning |
|---|---|
| `in` / `in.` | inches |
| `ft` | feet |
| `mm`, `cm`, `m`, `km` | metric length |
| `pt`, `pica`, `cicero`, `didot` | typographic |
| `deg`, `rad` | angle |
| `%` | percent (= 0.01) |
| `DU` | drawing units (page units) |
| `PT` | page typographic point |
| `e` | scientific exponent (`1.5e-3`) |
| `MM_F`, `IN_F`, `CM_F` | "fixed" scale-aware variants for `DrawingScale` |

### 20.3 Error sentinels

| Token | Cause |
|---|---|
| `#REF!` | Invalid cell reference |
| `#NAME?` | Unknown name / function |
| `#VALUE!` | Type or unit mismatch |
| `#DIV/0!` | Division by zero |
| `#CYCLE!` | Cyclic dependency the engine could not break |
| `#FUNC?` | Unknown or version-incompatible function |
| `#NUM!` | Numeric overflow or out-of-range argument |

`Cell.Result(unit)` returns NaN for any of the above; `Cell.ResultStr(unit)`
returns the sentinel text verbatim.

---

## 21. Function Alphabet — every built-in, one row each

Categorised but flat. Signatures follow the recalc-engine grammar; arguments
in `[brackets]` are optional. Sources: `learn.microsoft.com` ShapeSheet
function pages cited in `research/02-shapesheet-cells-functions.md`.

### 21.1 Math and arithmetic

| Function | Signature | Example |
|---|---|---|
| `ABS` | `ABS(expr)` | `=ABS(EndX-BeginX)` |
| `CEILING` | `CEILING(expr, signif)` | `=CEILING(Width, 0.25 in)` |
| `FLOOR` | `FLOOR(expr, signif)` | `=FLOOR(Width, 0.25 in)` |
| `ROUND` | `ROUND(expr, digits)` | `=ROUND(Angle, 1)` |
| `INT` | `INT(expr)` | `=INT(Width/0.25 in)` |
| `MOD` | `MOD(num, divisor)` | `=MOD(Angle, 360 deg)` |
| `SQRT` | `SQRT(expr)` | `=SQRT(Width^2+Height^2)` |
| `EXP` | `EXP(expr)` | `=EXP(User.k)` |
| `LN` | `LN(expr)` | `=LN(Width)` |
| `LOG10` | `LOG10(expr)` | `=LOG10(Width)` |
| `MAX` | `MAX(a, b, ...)` | `=MAX(Width, Height)` |
| `MIN` | `MIN(a, b, ...)` | `=MIN(Width, Height)` |
| `SUM` | `SUM(a, b, ...)` | `=SUM(User.r1, User.r2)` |
| `RAND` | `RAND()` | `=RAND()*Width` |
| `SIGN` | `SIGN(expr)` | `=SIGN(EndX-BeginX)` |
| `PI` | `PI()` | `=PI()*User.r^2` |

### 21.2 Trigonometry

| Function | Signature | Example |
|---|---|---|
| `SIN` | `SIN(angle)` | `=SIN(Angle)*Width` |
| `COS` | `COS(angle)` | `=COS(Angle)*Width` |
| `TAN` | `TAN(angle)` | `=TAN(Angle)` |
| `ASIN` | `ASIN(expr)` | `=ASIN(Height/Width)` |
| `ACOS` | `ACOS(expr)` | `=ACOS(0.5)` |
| `ATAN` | `ATAN(expr)` | `=ATAN(Height/Width)` |
| `ATAN2` | `ATAN2(x, y)` | `=ATAN2(EndX-BeginX, EndY-BeginY)` (Visio order: x,y) |
| `SINH` | `SINH(expr)` | `=SINH(User.t)` |
| `COSH` | `COSH(expr)` | `=COSH(User.t)` |
| `TANH` | `TANH(expr)` | `=TANH(User.t)` |
| `DEG` | `DEG(expr)` | `=DEG(1.5708 rad)` |
| `RAD` | `RAD(expr)` | `=RAD(90 deg)` |

### 21.3 Logic and comparison

| Function | Signature | Example |
|---|---|---|
| `IF` | `IF(cond, then, else)` | `=IF(Width>2 in, 1, 0)` |
| `AND` | `AND(a, b, ...)` | `=AND(NOT(FlipX), Angle=0 deg)` |
| `OR` | `OR(a, b, ...)` | `=OR(LockMoveX, LockMoveY)` |
| `NOT` | `NOT(expr)` | `=NOT(NoFill)` |
| `TRUE` | `TRUE()` | `=TRUE()` |
| `FALSE` | `FALSE()` | `=FALSE()` |
| `STRSAME` | `STRSAME(a, b, ignoreCase)` | `=STRSAME(User.kind,"hub",TRUE())` |

### 21.4 Lookup, list, and indexing

| Function | Signature | Example |
|---|---|---|
| `LOOKUP` | `LOOKUP(text, list)` | `=LOOKUP(Prop.size,"S;M;L;XL")` |
| `INDEX` | `INDEX(n, list, [listsep], [recordsep])` | `=INDEX(Prop.idx,"red,green,blue", ",")` |
| `USE` | `USE(masterName)` | `=USE("Process")` |
| `LISTSEP` | `LISTSEP()` | `=LISTSEP()` |
| `LISTORDER` | `LISTORDER()` | `=LISTORDER()` |
| `LISTMEMBERCOUNT` | `LISTMEMBERCOUNT()` | `=LISTMEMBERCOUNT()` |
| `LISTSHEETREF` | `LISTSHEETREF(n)` | `=LISTSHEETREF(1)` |
| `CONTAINERSHEETREF` | `CONTAINERSHEETREF(n)` | `=CONTAINERSHEETREF(1)` |
| `CALLOUTTARGETREF` | `CALLOUTTARGETREF()` | `=CALLOUTTARGETREF()` |
| `RELATIONSHIPS` | `RELATIONSHIPS(typ, filter)` | `=RELATIONSHIPS(0,"")` |
| `HASCATEGORY` | `HASCATEGORY(text)` | `=HASCATEGORY("Container")` |

### 21.5 Point geometry

| Function | Signature | Example |
|---|---|---|
| `PNT` | `PNT(x, y)` | `=PNT(Width*0.5, Height)` |
| `PNTX` | `PNTX(point)` | `=PNTX(LOCTOPAR(PNT(0,0)))` |
| `PNTY` | `PNTY(point)` | `=PNTY(LOCTOPAR(PNT(0,0)))` |
| `LOCTOPAR` | `LOCTOPAR(p, [transform])` | `=LOCTOPAR(PNT(0,0))` |
| `LOCTOLOC` | `LOCTOLOC(p, fromShape, toShape)` | `=LOCTOLOC(PNT(0,0),Sheet.5,Sheet.7)` |
| `PROJECTPOINT` | `PROJECTPOINT(geom, x, y)` | `=PROJECTPOINT(Geometry1.Path, EventInfo!X, EventInfo!Y)` |
| `BOUNDINGBOX` | `BOUNDINGBOX(geomFlags)` | `=BOUNDINGBOX(0)` |

### 21.6 Path geometry and NURBS

| Function | Signature | Example |
|---|---|---|
| `POINTALONGPATH` | `POINTALONGPATH(geom, t, [offset])` | `=POINTALONGPATH(Geometry1.Path, 0.5)` |
| `ANGLEALONGPATH` | `ANGLEALONGPATH(geom, t)` | `=ANGLEALONGPATH(Geometry1.Path, 0.5)` |
| `DISTTOPATH` | `DISTTOPATH(geom, x, y)` | `=DISTTOPATH(Geometry1.Path, EventInfo!X, EventInfo!Y)` |
| `NURBS` | `NURBS(degree, useTangent, periodic, useWeights, knotsAndWeights...)` | `=NURBS(3, knotLast, FALSE, FALSE, ...)` |
| `POLYLINE` | `POLYLINE(x1, y1, x2, y2, ...)` | `=POLYLINE(0,0,1,0.5,2,0)` |

### 21.7 Date and time

| Function | Signature | Example |
|---|---|---|
| `NOW` | `NOW()` | `="Edited "&NOW()` |
| `TODAY` | `TODAY()` | `=TODAY()` |
| `DATE` | `DATE(y, m, d)` | `=DATE(2026,06,14)` |
| `TIME` | `TIME(h, m, s)` | `=TIME(9,30,0)` |
| `DATETIME` | `DATETIME(y, m, d, h, n, s)` | `=DATETIME(2026,6,14,9,30,0)` |
| `YEAR` | `YEAR(d)` | `=YEAR(NOW())` |
| `MONTH` | `MONTH(d)` | `=MONTH(NOW())` |
| `DAY` | `DAY(d)` | `=DAY(NOW())` |
| `HOUR` | `HOUR(d)` | `=HOUR(NOW())` |
| `MINUTE` | `MINUTE(d)` | `=MINUTE(NOW())` |
| `SECOND` | `SECOND(d)` | `=SECOND(NOW())` |
| `DAYOFYEAR` | `DAYOFYEAR(d)` | `=DAYOFYEAR(NOW())` |
| `WEEKDAY` | `WEEKDAY(d)` | `=WEEKDAY(NOW())` |

### 21.8 Text and string

| Function | Signature | Example |
|---|---|---|
| `LEN` | `LEN(text)` | `=LEN(TheText)` |
| `LEFT` | `LEFT(text, n)` | `=LEFT("VisioMaster",5)` |
| `RIGHT` | `RIGHT(text, n)` | `=RIGHT("VisioMaster",6)` |
| `MID` | `MID(text, start, n)` | `=MID(TheText, 2, 4)` |
| `UPPER` | `UPPER(text)` | `=UPPER(Prop.Tier)` |
| `LOWER` | `LOWER(text)` | `=LOWER(Prop.Hostname)` |
| `PROPER` | `PROPER(text)` | `=PROPER(Prop.Owner)` |
| `TRIM` | `TRIM(text)` | `=TRIM(Prop.Notes)` |
| `REPT` | `REPT(text, n)` | `=REPT("-", 10)` |
| `SUBSTITUTE` | `SUBSTITUTE(text, old, new, [n])` | `=SUBSTITUTE(TheText," ","_")` |
| `STRSEARCH` | `STRSEARCH(haystack, needle, [start])` | `=STRSEARCH(TheText,"=")` |
| `CHAR` | `CHAR(code)` | `=CHAR(10)` |
| `CODE` | `CODE(text)` | `=CODE(TheText)` |
| `CY` | `CY(value)` | `=CY(Prop.Cost)` |
| `STRBUILD` | `STRBUILD(...)` | `=STRBUILD("Total: ", Prop.Cost)` |
| `FORMAT` | `FORMAT(value, picture)` | `=FORMAT(NOW(),"yyyy-MM-dd")` |
| `FORMATEX` | `FORMATEX(value, picture, srcUnit, dstUnit)` | `=FORMATEX(Width,"0.00 in.","in.","in.")` |

### 21.9 Document, page, and master metadata

| Function | Signature | Example |
|---|---|---|
| `DOCNAME` | `DOCNAME([universal])` | `=DOCNAME(TRUE)` |
| `PAGENAME` | `PAGENAME([universal])` | `=PAGENAME(TRUE)` |
| `PAGENUMBER` | `PAGENUMBER()` | `=PAGENUMBER()` |
| `PAGECOUNT` | `PAGECOUNT()` | `=PAGECOUNT()` |
| `BKGPAGENAME` | `BKGPAGENAME()` | `=BKGPAGENAME()` |
| `MASTERNAME` | `MASTERNAME([universal])` | `=MASTERNAME(TRUE)` |
| `STYLE` | `STYLE([universal])` | `=STYLE()` |
| `LINESTYLE` | `LINESTYLE([universal])` | `=LINESTYLE()` |
| `FILLSTYLE` | `FILLSTYLE([universal])` | `=FILLSTYLE()` |
| `TEXTSTYLE` | `TEXTSTYLE([universal])` | `=TEXTSTYLE()` |
| `TYPEPROP` | `TYPEPROP("Prop.x")` | `=TYPEPROP("Prop.Tier")` |

### 21.10 Add-on and command dispatch

| Function | Signature | Example |
|---|---|---|
| `RUNADDON` | `RUNADDON(addonName)` | `=RUNADDON("FlowShape")` |
| `RUNADDONWARGS` | `RUNADDONWARGS(name, args)` | `=RUNADDONWARGS("ExportFlow","/o:c:\out.svg")` |
| `CALLTHIS` | `CALLTHIS("Module.Sub", [args...])` | `=CALLTHIS("ThisDocument.OnClick","")` |
| `DOCMD` | `DOCMD(commandID)` | `=DOCMD(1312)` |
| `OPENFILE` | `OPENFILE(path, [flags])` | `=OPENFILE("C:\\plan.vsdx")` |
| `OPENPAGE` | `OPENPAGE(name)` | `=OPENPAGE("Detail")` |
| `OPENGROUPWINDOW` | `OPENGROUPWINDOW()` | `=OPENGROUPWINDOW()` |
| `OPENSHEETWINDOW` | `OPENSHEETWINDOW()` | `=OPENSHEETWINDOW()` |
| `OPENTEXTWIN` | `OPENTEXTWIN()` | `=OPENTEXTWIN()` |
| `GOTOPAGE` | `GOTOPAGE(n)` | `=GOTOPAGE(2)` |
| `DEFAULTEVENT` | `DEFAULTEVENT()` | `=DEFAULTEVENT()` |

### 21.11 Dependency control

| Function | Signature | Example |
|---|---|---|
| `GUARD` | `GUARD(expr)` | `=GUARD(Width*0.5)` |
| `SETF` | `SETF(GETREF(target), value)` | `=SETF(GETREF(User.x), 5)` |
| `SETATREF` | `SETATREF(target, [expr], [ignoreSubsequent])` | `=SETATREF(User.r)+0` |
| `SETATREFEXPR` | `SETATREFEXPR(expr)` | `=SETATREFEXPR(User.x*2)` |
| `SETATREFEVAL` | `SETATREFEVAL(expr)` | `=SETATREFEVAL(User.x)` |
| `DEPENDSON` | `DEPENDSON(c1, c2, ...)` | `=ATAN2(EndX-BeginX,EndY-BeginY)+DEPENDSON(EndX,EndY)` |
| `EVALCELL` | `EVALCELL("PinX")` | `=EVALCELL("Sheet.7!Width")` |
| `BOUND` | `BOUND(value, low, high)` | `=BOUND(User.r, 0.1 in, 5 in)` |
| `GETREF` | `GETREF(cell)` | `=GETREF(User.x)` |

### 21.12 Hyperlink and external

| Function | Signature | Example |
|---|---|---|
| `HYPERLINK` | `HYPERLINK(addr, [subaddr], [frame])` | `=HYPERLINK("https://docs.microsoft.com/visio")` |
| `HYPERLINKBASE` | `HYPERLINKBASE()` | `=HYPERLINKBASE()` |

### 21.13 Color and theme

| Function | Signature | Example |
|---|---|---|
| `RGB` | `RGB(r, g, b)` | `=RGB(255,128,0)` |
| `HSL` | `HSL(h, s, l)` | `=HSL(20,200,128)` |
| `THEMEVAL` | `THEMEVAL([cell])` | `=THEMEVAL("AccentColor")` |
| `THEMECOLOR` | `THEMECOLOR(idx)` | `=THEMECOLOR(1)` |
| `THEMEGUARD` | `THEMEGUARD(expr)` | `=THEMEGUARD(THEMEVAL("AccentColor"))` |
| `BLEND` | `BLEND(c1, c2, t)` | `=BLEND(RGB(255,0,0),RGB(0,0,255),0.5)` |
| `DARKEN` | `DARKEN(color, amount)` | `=DARKEN(THEMEVAL("AccentColor"), 0.2)` |
| `LIGHTEN` | `LIGHTEN(color, amount)` | `=LIGHTEN(THEMEVAL("AccentColor"), 0.2)` |
| `FILLBKGND` | `FILLBKGND()` | `=FILLBKGND()` |
| `FILLFOREGND` | `FILLFOREGND()` | `=FILLFOREGND()` |

---

## 22. Recipes — copy/paste patterns

### 22.1 Square aspect lock

```text
Width  = GUARD(Height)
Height = GUARD(Width)        # engine breaks the cycle via SETATREF
```

### 22.2 Bound-clamped scale handle

```text
User.scale = BOUND(Controls.X1 / Width, 0.25, 4)
Width      = GUARD(User.scale * 1 in)
Height     = GUARD(User.scale * 1 in)
```

### 22.3 Smart connector midpoint label

```text
Geometry2.X1 = PNTX(POINTALONGPATH(Geometry1.Path, 0.5))
Geometry2.Y1 = PNTY(POINTALONGPATH(Geometry1.Path, 0.5))
TxtPinX      = PNTX(POINTALONGPATH(Geometry1.Path, 0.5))
TxtPinY      = PNTY(POINTALONGPATH(Geometry1.Path, 0.5))
TxtAngle     = ANGLEALONGPATH(Geometry1.Path, 0.5)
```

### 22.4 Computed connection point that follows a control

```text
Connections.X1    = Controls.X1
Connections.Y1    = Controls.Y1
Connections.DirX1 = COS(ATAN2(Controls.X1-Width*0.5, Controls.Y1-Height*0.5))
Connections.DirY1 = SIN(ATAN2(Controls.X1-Width*0.5, Controls.Y1-Height*0.5))
```

### 22.5 Right-click "Open data source"

```text
Actions.Open.Action = HYPERLINK(User.dataUrl)
Actions.Open.Menu   = "&Open source data"
Actions.Open.Prompt = "Browse to the row that backs this shape"
```

### 22.6 Forced recalc on remote changes

```text
TheText = "Total: " & Sheet.7!User.total & DEPENDSON(Sheet.7!User.total)
```

### 22.7 Toggle decorator visibility

```text
User.ShowDeco            = TRUE
Geometry2.NoShow         = NOT(User.ShowDeco)
Actions.Toggle.Action    = SETF(GETREF(User.ShowDeco), NOT(User.ShowDeco))
Actions.Toggle.Menu      = "Show &decorator"
Actions.Toggle.Checked   = User.ShowDeco
```

### 22.8 Round-trip Shape Data into a child label

```text
# On the parent group:
Prop.Label = "srv-001"
# On the text-only child shape:
TheText    = Sheet.Parent!Prop.Label
EventTextEdit = SETF(GETREF(Sheet.Parent!Prop.Label), TheText)
```

---

## 23. Programmatic Access — minimal recipes

### 23.1 PowerShell — read every formula on a shape

```powershell
function Get-VisioShapeSheet {
    param(
        [Parameter(Mandatory)] [string] $DocumentPath,
        [Parameter(Mandatory)] [int]    $PageIndex,
        [Parameter(Mandatory)] [int]    $ShapeID
    )
    $visio = $null
    try {
        $visio = New-Object -ComObject Visio.InvisibleApp
        $visio.AlertResponse = 7
        $doc   = $visio.Documents.Open($DocumentPath)
        $page  = $doc.Pages.Item($PageIndex)
        $shape = $page.Shapes.ItemFromID($ShapeID)
        0..255 |
            Where-Object { try { $shape.SectionExists($_, $false) } catch { $false } } |
            ForEach-Object {
                $sec = $_
                for ($r = 0; $r -lt $shape.RowCount($sec); $r++) {
                    for ($c = 0; $c -lt $shape.RowsCellCount($sec, $r); $c++) {
                        $cell = $shape.CellsSRC($sec, $r, $c)
                        [pscustomobject]@{
                            Section = $sec; Row = $r; Col = $c
                            Name = $cell.Name; Formula = $cell.FormulaU
                            Value = $cell.ResultStrU('')
                        }
                    }
                }
            }
    } finally {
        if ($doc)   { $doc.Close()  | Out-Null }
        if ($visio) { $visio.Quit() | Out-Null }
        [Runtime.InteropServices.Marshal]::ReleaseComObject($visio) | Out-Null
    }
}
```

### 23.2 Python (pywin32) — patch cells with `CoInitialize`

```python
"""Patch a Visio shape's ShapeSheet from Python."""
import contextlib
import pythoncom
import win32com.client as win32
from win32com.client import constants as c   # VisSectionIndices etc.

@contextlib.contextmanager
def visio_app(visible: bool = False):
    pythoncom.CoInitialize()
    app = None
    try:
        app = win32.gencache.EnsureDispatch("Visio.InvisibleApp")
        app.AlertResponse = 7
        app.Visible       = visible
        yield app
    finally:
        if app is not None:
            with contextlib.suppress(Exception):
                app.Quit()
        pythoncom.CoUninitialize()

def patch(path: str, shape_id: int) -> None:
    with visio_app() as app:
        doc = app.Documents.Open(path)
        try:
            shape = doc.Pages.Item(1).Shapes.ItemFromID(shape_id)
            shape.CellsU("PinX").FormulaU   = "PageWidth*0.25"
            shape.CellsU("Width").FormulaU  = "1.5 in"
            shape.CellsU("Height").FormulaU = "GUARD(Width*0.75)"
            if not shape.SectionExists(c.visSectionUser, False):
                shape.AddSection(c.visSectionUser)
            shape.AddNamedRow(c.visSectionUser, "scale", 0)
            shape.CellsU("User.scale").FormulaU        = "1.0"
            shape.CellsU("User.scale.Prompt").FormulaU = '"Free scale"'
            doc.Save()
        finally:
            with contextlib.suppress(Exception):
                doc.Close()
```

### 23.3 VBA — emit a triangle Geometry section

```vba
Public Sub EmitTriangle(shape As Visio.Shape)
    Dim sec As Integer: sec = visSectionFirstComponent
    If shape.SectionExists(sec, False) Then shape.DeleteSection sec
    shape.AddSection sec
    shape.CellsSRC(sec, visRowComponent, visCompNoFill).FormulaU = "FALSE"
    shape.CellsSRC(sec, visRowComponent, visCompNoLine).FormulaU = "FALSE"
    shape.AddRow sec, visRowVertex, visTagMoveTo
    shape.CellsSRC(sec, visRowVertex, visX).FormulaU = "0"
    shape.CellsSRC(sec, visRowVertex, visY).FormulaU = "0"
    shape.AddRow sec, visRowVertex + 1, visTagLineTo
    shape.CellsSRC(sec, visRowVertex + 1, visX).FormulaU = "Width*1"
    shape.CellsSRC(sec, visRowVertex + 1, visY).FormulaU = "0"
    shape.AddRow sec, visRowVertex + 2, visTagLineTo
    shape.CellsSRC(sec, visRowVertex + 2, visX).FormulaU = "Width*0.5"
    shape.CellsSRC(sec, visRowVertex + 2, visY).FormulaU = "Height*1"
    shape.AddRow sec, visRowVertex + 3, visTagLineTo
    shape.CellsSRC(sec, visRowVertex + 3, visX).FormulaU = "Geometry1.X1"
    shape.CellsSRC(sec, visRowVertex + 3, visY).FormulaU = "Geometry1.Y1"
End Sub
```

### 23.4 C# (VSTO) — dependency walk

```csharp
public static IEnumerable<string> WalkPrecedents(Visio.Cell cell)
{
    var seen  = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
    var stack = new Stack<Visio.Cell>();
    stack.Push(cell);
    while (stack.Count > 0)
    {
        var current = stack.Pop();
        var id = $"{current.Shape.ID}.{current.Section}.{current.Row}.{current.Column}";
        if (!seen.Add(id)) continue;
        yield return $"{id}\t= {current.FormulaU}";
        try
        {
            Array precedents;
            current.Precedents(out precedents);
            if (precedents == null) continue;
            foreach (Visio.Cell p in precedents) stack.Push(p);
        }
        catch (System.Runtime.InteropServices.COMException) { }
    }
}
```

---

## 24. Recalc, performance, and error handling

| Concern | Rule | Mitigation |
|---|---|---|
| Recalc order | Topological by precedent edges | Use `DEPENDSON` for hidden edges |
| Cycle detection | `#CYCLE!` if engine cannot break with `SETATREF` | Wrap one side in `GUARD` |
| Deep precedent chains | Cost ~`O(N * fanout)` per top-level edit | Cache via `User.*` cells |
| Bulk rewrites | Each formula write triggers recalc | `Document.PauseEvents = True` then `False` |
| Undo grouping | Each `FormulaU = ...` is its own undo step | Wrap in `Application.BeginUndoScope` / `EndUndoScope` |
| Locale safety | `.Cells`/`.Formula` uses localised names | Always use `CellsU` and `FormulaU` |
| Protection bypass | `LockSelect=1` blocks even macro selection in user mode | Set `Document.Mode = visDrawingDocMaster`, or use `FormulaForceU` |
| Master inheritance | `IsInherited=TRUE` until first local write | Use `Cell.FormulaForceU` to force a local override; `Cell.Inherit` (where exposed) restores |

---

## 25. Validation checklist before publishing

1. Open the `.vssx` / `.vsdx`; confirm shapes drop with sane defaults.
2. Verify connection points match `Connections.<Name>` and route correctly.
3. Resize the shape; geometry, controls, and connection points track via
   formulas with no hard-coded coordinates.
4. Right-click; every `Actions.<Row>.Menu` appears with correct accelerator
   and the action runs without `#REF!` / `#NAME?`.
5. Hover; smart tags appear at configured anchors and clicking them fires
   the matched `Actions.<Tag>` row.
6. Double-click; `EventDblClick` formula fires the intended target.
7. `Protection` cells behave as declared (`LockTextEdit`, `LockSelect`,
   `LockMoveX`, `LockMoveY`).
8. Search "Find shape" with each keyword in `Master.Prompt`; the master
   surfaces.
9. `[Content_Types].xml` declares the right content types
   (`vnd.ms-visio.drawing` / `.stencil` / `.template`).
10. No `Cell` element in serialised XML carries a naked numeric coordinate
    without a `U=` unit attribute.

---

## Sources

1. `research/02-shapesheet-cells-functions.md` — section catalog, cell index
   table, full function reference with PowerShell / Python / VBA / C#
   examples.
2. `research/26-custom-shape-development.md` — group editing, Connections,
   Protection, Geometry `NoShow`, SmartTags, Actions, EventDblClick,
   Master.PatternFlags / AlignName / IconUpdate, `.vssx` distribution.

