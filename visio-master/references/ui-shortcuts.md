# Visio UI Shortcuts and Ribbon Paths

Hand-tuning reference for diagrams produced by visio-master and reopened in
Microsoft Visio Desktop (2019 / 2021 / LTSC / Microsoft 365). Every binding
in this file maps a keyboard shortcut, a ribbon path (`Tab > Group > Control`),
and the canonical `idMso` (Microsoft Office control identifier) — the same
identifier you pass to `Application.CommandBars.ExecuteMso(idMso)` from VBA,
PowerShell, pywin32, or VSTO. When a shortcut differs across en-US layouts and
localized layouts, the value in this file is the en-US one — KeyTips
(`Alt`-letter overlays) remain stable across locales because they are derived
from the localized ribbon labels.

> Conventions:
> - Ribbon paths use the en-US labels from the default ribbon. Custom or
>   contextual tabs are called out explicitly.
> - All `idMso` values target Visio Desktop. The Visio for the Web ribbon is
>   a different surface and most of these idMso values are absent there.
> - The ShapeSheet column references cells from
>   `references/shapesheet-quick-ref.md`. Open the ShapeSheet via the
>   Developer tab (see §11) to verify a hand-tuning matches the diagram
>   produced by the builder.
> - "Selection" means the current `ActiveWindow.Selection`; some controls
>   are disabled when selection is empty (`GetEnabledMso` returns `False`).

---

## 1. KeyTips and ribbon entry points

Press `Alt` once to surface KeyTips — the single-letter overlays that walk you
to any ribbon control without the mouse. The top-level letters are stable:

| KeyTip   | Tab / target                                  | Tab idMso         |
|----------|-----------------------------------------------|-------------------|
| `Alt+F`  | File (Backstage)                              | `TabBackstage`    |
| `Alt+H`  | Home                                          | `TabHome`         |
| `Alt+N`  | Insert                                        | `TabInsert`       |
| `Alt+G`  | Design                                        | `TabDesignVisio`  |
| `Alt+A`  | Data                                          | `TabExternalData` |
| `Alt+P`  | Process                                       | `TabProcess`      |
| `Alt+R`  | Review                                        | `TabReview`       |
| `Alt+W`  | View                                          | `TabView`         |
| `Alt+L`  | Developer (when enabled, see §11)             | `TabDeveloper`    |
| `Alt+Q`  | Tell Me / Search                              | `TellMe`          |
| `Alt+1`…`Alt+9`, `Alt+0` | Quick Access Toolbar slots 1..10  | n/a (see §13)     |
| `F10` then arrow keys | Walk the ribbon without the mouse | n/a               |
| `Esc`    | Cancel KeyTips overlay / close menu           | `Cancel`          |

After the first `Alt+<tab>` chord, every group exposes its own KeyTip. From
the Home tab (`Alt+H`), examples: `FF` for Find, `RA` for Replace, `1` for
Pointer, `3` for Connector, `G` for Group menu.

---

## 2. File and application

`File > <command>` lives in the Backstage view (`TabBackstage`); none of these
have an `idMso`-addressable group container, but each leaf command does.

| Shortcut          | Action                          | Ribbon path                         | idMso / API                                  |
|-------------------|---------------------------------|-------------------------------------|----------------------------------------------|
| `Ctrl+N`          | New blank drawing               | File > New > Blank Drawing          | `FileNewDefault`                             |
| `Ctrl+O`          | Open                            | File > Open                         | `FileOpen` (Backstage `TabRecent`)           |
| `Ctrl+S`          | Save                            | File > Save                         | `FileSave`                                   |
| `F12`             | Save As (file picker)           | File > Save As                      | `FileSaveAs`                                 |
| `Ctrl+P`          | Print pane                      | File > Print                        | `FilePrint` (Backstage `TabPrint`)           |
| `Ctrl+W` / `Ctrl+F4` | Close active drawing         | File > Close                        | `FileClose`                                  |
| `Alt+F4`          | Quit Visio                      | File > Exit (older builds)          | `FileExit`                                   |
| `Ctrl+Z`          | Undo                            | Quick Access Toolbar                | `Undo` / `Application.Undo`                  |
| `Ctrl+Y` / `F4`   | Redo / Repeat                   | Quick Access Toolbar                | `Redo`                                       |
| `Ctrl+F1`         | Collapse / expand the ribbon    | n/a                                 | `MinimizeRibbon`                             |
| `F1`              | Help (online docs)              | n/a                                 | `Help`                                       |
| `Esc`             | Cancel command, deselect, exit text edit | n/a                        | `Cancel`                                     |
| `Alt+F`, then `T` | Options dialog                  | File > Options                      | `ApplicationOptionsDialog`                   |
| `Alt+F`, then `I` | Info pane (document properties) | File > Info                         | `TabInfo` (Backstage)                        |
| `Alt+F`, then `D` | Account                         | File > Account                      | `TabAccount`                                 |

Format-specific saves from the Save As dialog (these are file-type filters,
not separate idMso values):

| Format             | Extension | Notes                                                     |
|--------------------|-----------|-----------------------------------------------------------|
| Visio Drawing      | `.vsdx`   | OPC ZIP, no macros — produced by visio-master.            |
| Visio Macro-Enabled| `.vsdm`   | Same OPC layout plus `vbaProject.bin`.                    |
| Visio Template     | `.vstx`   | Reused as the basis for `New from Template`.              |
| Visio Stencil      | `.vssx`   | Master library; visio-master writes one per palette.      |
| PDF                | `.pdf`    | `File > Export > Create PDF/XPS` (`PublishAsPDFXPS`).     |
| PNG / JPG / SVG    | varies    | `File > Export > Change File Type` (`SaveAsOtherFormats`).|
| AutoCAD            | `.dwg`/`.dxf`| Pro/Plan 2 only.                                       |

Recovery and autosave commands:

| Shortcut       | Action                                                        | idMso                                |
|----------------|---------------------------------------------------------------|--------------------------------------|
| (UI only)      | File > Info > Manage Document > Recover Unsaved Drawings      | `RecoverDraftFiles`                  |
| (UI only)      | File > Options > Save > AutoRecover interval                  | `ApplicationOptionsDialog`           |
| `Ctrl+Shift+S` | Save a copy (some builds; otherwise behaves as `Save As`)     | `FileSaveACopy`                      |

---

## 3. Navigation — pages, windows, zoom, panning

### 3.1 Page navigation

The page tab strip lives at the bottom of the drawing window. Right-click any
tab for `Insert Page`, `Rename`, `Delete`, `Reorder`. The same actions are
exposed under `Insert > Pages` and via these shortcuts:

| Shortcut          | Action                              | Ribbon path                           | idMso                            |
|-------------------|-------------------------------------|---------------------------------------|----------------------------------|
| `Ctrl+Page Down`  | Next page                           | n/a                                   | `ViewNextPage`                   |
| `Ctrl+Page Up`    | Previous page                       | n/a                                   | `ViewPreviousPage`               |
| (UI)              | Insert blank page after current     | Insert > Pages > Blank Page           | `PageNewBlankVisio`              |
| (UI)              | Insert background page              | Insert > Pages > Background           | `BackgroundPageMenuVisio`        |
| (UI)              | Reorder pages                       | Right-click page tab > Reorder        | `PageReorderDialog`              |
| (UI)              | Rename page                         | Right-click page tab > Rename, or F2 on tab | `PageRename`               |
| (UI)              | Delete page                         | Right-click page tab > Delete         | `PageDelete`                     |
| `Ctrl+Shift+P` *  | Go to page (legacy `GoTo` dialog)   | Home > Editing > Go To Page           | `GoToPageMenuVisio`              |

`*` `Ctrl+Shift+P` is overloaded with `Pencil Tool` and `Format Painter`
depending on focus. Use the ribbon path when the chord is ambiguous.

The `ShowDevPagesAsTabs` setting (under `Tools > Options > Advanced` in older
builds, or `Settings.ShowDeveloperPageTabs = True`) makes background and
markup pages visible alongside foreground pages on the tab strip.

### 3.2 Window management

| Shortcut                           | Action                                 | Ribbon path                  | idMso                            |
|------------------------------------|----------------------------------------|------------------------------|----------------------------------|
| `Ctrl+Tab` / `Ctrl+F6`             | Cycle to next open document window     | View > Window > Switch Windows | `WindowSwitchWindowsMenu`      |
| `Ctrl+Shift+Tab` / `Ctrl+Shift+F6` | Cycle to previous open document window | View > Window > Switch Windows | `WindowSwitchWindowsMenu`      |
| (UI)                               | New view of the current document       | View > Window > New Window   | `WindowNew`                      |
| (UI)                               | Tile / cascade open documents          | View > Window > Arrange All / Cascade | `WindowArrangeAll`, `WindowCascade` |
| (UI)                               | View Side by Side                      | View > Window > View Side by Side | `WindowViewSideBySide`      |
| (UI)                               | Synchronous Scrolling toggle           | View > Window > Synchronous Scrolling | `WindowSynchronousScrolling` |

### 3.3 Zoom and pan

| Shortcut                         | Action                                        | Ribbon path / pane                  | idMso                       |
|----------------------------------|-----------------------------------------------|-------------------------------------|-----------------------------|
| `Ctrl+Shift+W`                   | Fit drawing to window                         | View > Zoom > Fit to Window         | `ZoomFitToWindow` / `ZoomCurrentPage` |
| `Ctrl+Shift+I` (some builds)     | Zoom to 100%                                  | View > Zoom > 100%                  | `Zoom100`                   |
| `Ctrl+wheel up` / `Ctrl+wheel down` | Zoom in / out at cursor                    | n/a                                 | `ZoomIn` / `ZoomOut`        |
| `Alt+F6` / `Alt+Shift+F6`        | Zoom in / out a step                          | n/a                                 | `ZoomIn` / `ZoomOut`        |
| `Ctrl+Shift+drag` (right button) | Marquee zoom to rectangle                     | n/a                                 | n/a (mouse only)            |
| `Shift+drag` (right button)      | Pan canvas                                    | n/a                                 | n/a (mouse only)            |
| (UI)                             | Zoom dialog                                   | View > Zoom > Zoom (dialog launcher)| `ZoomDialog`                |
| (UI)                             | Page Width                                    | View > Zoom > Page Width            | `ZoomPageWidth`             |
| (UI)                             | Pan & Zoom window                             | View > Show > Task Panes > Pan & Zoom | `PanAndZoomWindowVisio`   |

### 3.4 Visual aids and snapping

| Action                                  | Ribbon path                          | idMso                          |
|-----------------------------------------|--------------------------------------|--------------------------------|
| Toggle ruler                            | View > Show > Ruler                  | `ViewRulerVisio`               |
| Toggle grid                             | View > Show > Grid                   | `ViewGridLinesVisio`           |
| Toggle guides                           | View > Show > Guides                 | `ViewGuidesVisio`              |
| Toggle page breaks                      | View > Show > Page Breaks            | `ViewPageBreaks`               |
| Toggle connection points                | View > Show > Connection Points      | `ViewConnectionPointsVisio`    |
| AutoConnect arrows on hover             | View > Visual Aids > AutoConnect     | `AutoConnectToggle`            |
| Dynamic Grid (smart guides while drag)  | View > Visual Aids > Dynamic Grid    | `DynamicGridToggle`            |
| Snap & Glue dialog (master toggle)      | View > Visual Aids > dialog launcher | `SnapAndGlueDialog`            |
| Snap toggle                             | View > Visual Aids > Snap            | `SnapToggle`                   |
| Glue toggle                             | View > Visual Aids > Glue            | `GlueToggle`                   |

The Snap & Glue dialog backs onto `Document.SnapEnabled`, `Document.SnapExtensions`,
and the per-window `Window.SnapAngles`. Hand-tuning a connector route after
opening a `vsdx_export.py` artefact almost always wants `SnapToggle` on and
`Dynamic Grid` on so that endpoints lock to existing connection points.

---

## 4. Drawing tools

The pointer / connector / text / rectangle / ellipse / line / arc / freeform /
pencil tools form a mutually-exclusive radio group on `Home > Tools`
(`GroupToolsVisio`). Programmatically the active tool is exposed by
`ActiveWindow.MouseTool` (or, in some contexts, the `Window.SubType` set via
`Window.SubType = visToolPtr…`); from the ribbon, switch with the table below.

| Shortcut          | Tool                       | Ribbon path                          | idMso                              | Window.MouseTool constant     |
|-------------------|----------------------------|--------------------------------------|------------------------------------|-------------------------------|
| `Ctrl+1`          | Pointer                    | Home > Tools > Pointer Tool          | `PointerToolVisio`                 | `visToolPtrGen` (1)           |
| `Ctrl+2`          | Text                       | Home > Tools > Text                  | `TextToolVisio`                    | `visToolPtrText` (2)          |
| `Ctrl+3`          | Connector                  | Home > Tools > Connector             | `ConnectorToolVisio`               | `visToolPtrConn` (3)          |
| `Ctrl+Shift+1`    | Connection Point           | Developer > Connection Point Tool    | `ConnectionPointToolVisio`         | `visToolPtrConnPoint` (8)     |
| `Ctrl+8`          | Rectangle                  | Home > Tools > Rectangle gallery     | `OvalRectGalleryVisio`             | `visToolPtrRect` (4)          |
| `Ctrl+9`          | Ellipse                    | Home > Tools > Ellipse (within gallery) | `EllipseToolVisio`              | `visToolPtrOval` (5)          |
| `Ctrl+6`          | Line                       | Home > Tools > Line gallery          | `LineToolVisio`                    | `visToolPtrLine` (6)          |
| `Ctrl+7`          | Arc                        | Home > Tools > Arc                   | `ArcToolVisio`                     | `visToolPtrArc` (7)           |
| `Ctrl+5`          | Freeform                   | Home > Tools > Freeform              | `FreeformToolVisio`                | `visToolPtrFreeform` (9)      |
| `Ctrl+4`          | Pencil                     | Home > Tools > Pencil                | `PencilToolVisio`                  | `visToolPtrPencil` (10)       |
| n/a               | Crop Picture (contextual)  | Picture Tools Format > Crop          | `PictureCrop`                      | n/a                           |

When you draw with `Rectangle` / `Ellipse` / `Line`, Visio writes the geometry
into a `Geometry` ShapeSheet section. Hold modifiers while dragging:

| Modifier          | Effect                                                                 |
|-------------------|------------------------------------------------------------------------|
| `Shift+drag`      | Constrain to vertical / horizontal / 45° increments.                    |
| `Ctrl+drag`       | Draw symmetric around the start point (so start is the center).         |
| `Ctrl+Shift+drag` | Constrain + symmetric.                                                  |
| `Alt+drag`        | Disable snap to grid (one-shot).                                        |

### 4.1 Connector behaviour

The Connector tool draws a `Dynamic connector` master between two shapes. The
resulting shape's ShapeSheet has these cells worth knowing for hand tuning:

| Cell                              | Meaning                                                                    |
|-----------------------------------|----------------------------------------------------------------------------|
| `BeginX`, `BeginY`, `EndX`, `EndY`| Endpoint coordinates (page-unit) — usually formula references to glued shape `PinX`/`PinY`. |
| `BegTrigger`, `EndTrigger`        | Glue triggers — `=_XFTRIGGER(<Source>!EventXFMod)` keeps the connector reactive. |
| `ShapeRouteStyle`                 | `0`=center to center, `1`=right-angle, `2`=straight, `16`=tree, `17`=organisation chart, etc. |
| `LineRouteExt`                    | `1` for normal, `2` for curved.                                            |
| `ConFixedCode`                    | `0` allows reroute, `1` locks routing.                                     |
| `ConLineRouteExt`                 | Curved (`2`) vs. straight (`1`) override on the connector.                 |
| `User.visBestConnectorAngle`      | Visio internal — usually leave alone.                                      |

Ribbon path for connector style overrides: `Design > Layout > Connectors`
(`ConnectorStyleGalleryVisio`). The gallery is page-scoped — it rewrites the
default `ConnectorRoutingStyle` cell on the PageSheet.

### 4.2 Connection points

| Shortcut       | Action                                  | Ribbon path                                                    | idMso                            |
|----------------|-----------------------------------------|----------------------------------------------------------------|----------------------------------|
| `Ctrl+Shift+1` | Activate Connection Point Tool          | Developer > Shape Design > Connection Point Tool               | `ConnectionPointToolVisio`       |
| `Ctrl+click`   | Add a new connection point (with tool active) | n/a                                                      | n/a                              |
| `Ctrl+click` on point | Delete an existing connection point  | n/a                                                      | n/a                              |
| (UI)           | Toggle visibility of all connection points | View > Show > Connection Points                            | `ViewConnectionPointsVisio`      |

Each connection point is a `Connections` row (`Section.Connection`) with `X`,
`Y`, `DirX`, `DirY`, `Type` (`0`=inward, `1`=outward, `2`=inward+outward).
`DirX=DirY=0` means the point is non-directional (any side accepts the glue).

---

## 5. Selection, copy, duplicate, delete

| Shortcut          | Action                                                | Ribbon path / idMso                  |
|-------------------|-------------------------------------------------------|--------------------------------------|
| `Ctrl+A`          | Select all shapes on current page                     | Home > Editing > Select > All / `SelectAllVisio` |
| `Esc`             | Deselect / cancel current command                     | `Cancel`                             |
| `Tab`             | Select next shape in Z-order                          | n/a                                  |
| `Shift+Tab`       | Select previous shape in Z-order                      | n/a                                  |
| `Shift+click`     | Add to selection                                      | n/a                                  |
| `Ctrl+click`      | Toggle a shape in/out of selection                    | n/a                                  |
| `Alt+click`       | Subselect a member of a group without entering it     | n/a                                  |
| `Ctrl+drag`       | Duplicate during drag                                 | n/a                                  |
| `Ctrl+D`          | Duplicate selection in place + offset                 | `DuplicateAction` / Home > Clipboard |
| `Ctrl+C`          | Copy                                                  | `Copy`                               |
| `Ctrl+X`          | Cut                                                   | `Cut`                                |
| `Ctrl+V`          | Paste                                                 | `Paste`                              |
| `Ctrl+Alt+V`      | Paste Special                                         | `PasteSpecialDialog`                 |
| `Delete`          | Delete selection                                      | n/a                                  |
| Arrow keys        | Nudge by one grid unit                                | n/a                                  |
| `Shift+arrow`     | Nudge by one pixel (sub-grid)                         | n/a                                  |
| (UI)              | Selection pane (visibility / lock / rename)           | Home > Arrange > Selection Pane / `SelectionTaskPane` |
| (UI)              | Select by Type (text, shapes, connectors, …)          | Home > Editing > Select / `SelectMenuVisio`          |

### 5.1 Find, replace, go to

| Shortcut          | Action                          | Ribbon path                          | idMso                              |
|-------------------|---------------------------------|--------------------------------------|------------------------------------|
| `Ctrl+F`          | Find                            | Home > Editing > Find                | `FindMenuVisio` / `EditFindMenu`   |
| `Ctrl+H`          | Replace                         | Home > Editing > Replace             | `ReplaceDialogVisio` / `EditReplaceMenu` |
| `F4`              | Find Next (after first Find)    | n/a                                  | `FindNextVisio`                    |
| `Ctrl+G`          | Group selection (and, in some legacy builds, Go To) | Home > Arrange > Group | `ObjectGroupMenu`                |

`Find` searches `Shape.Text`, `Shape.Name`, shape data, user-defined cells,
and field codes — pick the targets in the dialog. Hand-tuning idiom: tag every
shape that needs review with `User.review = "TODO"`, then `Find` for `TODO`
in `User-defined cells` to walk them.

---

## 6. Alignment, distribution, ordering, grouping

The Home tab's Arrange group (`GroupArrangeVisio`) hosts every alignment,
distribution, position, rotate, and Z-order command. The `F8` shortcut opens
the master *Align Shapes* dialog (`AlignShapesDialog`) which lets you choose
horizontal alignment, vertical alignment, and "Create a guide and glue shapes
to it" in one operation.

### 6.1 Alignment shortcuts

| Shortcut          | Action                              | Ribbon path                          | idMso                                |
|-------------------|-------------------------------------|--------------------------------------|--------------------------------------|
| `F8`              | Align Shapes dialog                 | Home > Arrange > Align (gallery launcher) | `AlignShapesDialog`              |
| (gallery row 1)   | Align Left edges                    | Home > Arrange > Align > Align Left  | `ObjectsAlignLeft`                   |
| (gallery row 1)   | Align Center (horizontal)           | Home > Arrange > Align > Align Center| `ObjectsAlignCenterHorizontal`       |
| (gallery row 1)   | Align Right edges                   | Home > Arrange > Align > Align Right | `ObjectsAlignRight`                  |
| (gallery row 2)   | Align Top edges                     | Home > Arrange > Align > Align Top   | `ObjectsAlignTop`                    |
| (gallery row 2)   | Align Middle (vertical)             | Home > Arrange > Align > Align Middle| `ObjectsAlignMiddleVertical`         |
| (gallery row 2)   | Align Bottom edges                  | Home > Arrange > Align > Align Bottom| `ObjectsAlignBottom`                 |
| (UI)              | Align to Guide (with guide selected primary) | Drag onto guide; or Align Shapes > "Create guide and glue" | n/a |

### 6.2 Distribution

| Action                              | Ribbon path                                   | idMso                              |
|-------------------------------------|-----------------------------------------------|------------------------------------|
| Distribute Shapes dialog            | Home > Arrange > Position > More Distribute   | `DistributeShapesDialog`           |
| Distribute Horizontally (equal gaps)| Home > Arrange > Position > Distribute Horizontally | `ObjectsDistributeHorizontally` |
| Distribute Vertically (equal gaps)  | Home > Arrange > Position > Distribute Vertically   | `ObjectsDistributeVertically`   |
| Auto-Align & Space                  | Home > Arrange > Position > Auto Align & Space (`F8` legacy) | `AutoAlignAndSpaceVisio`|
| Position gallery                    | Home > Arrange > Position                     | `PositionShapesGalleryVisio`       |
| Re-Layout Page                      | Design > Layout > Re-Layout Page              | `ReLayoutPageGalleryVisio`         |

Distributing requires three or more selected shapes — the first and last
selection define the bounding extents and the middle members get evenly
spaced. The PageSheet `LayoutAndRouteOn` cell governs whether
`Re-Layout Page` is applied automatically when shapes are moved.

### 6.3 Z-order

| Shortcut                | Action                | Ribbon path                                | idMso                            |
|-------------------------|-----------------------|--------------------------------------------|----------------------------------|
| `Ctrl+Shift+F`          | Bring to Front        | Home > Arrange > Bring to Front            | `ObjectBringToFront`             |
| `Ctrl+Shift+B`          | Send to Back          | Home > Arrange > Send to Back              | `ObjectSendToBack`               |
| `Ctrl+]`                | Bring Forward (one)   | Home > Arrange > Bring to Front > Bring Forward | `ObjectBringForward`        |
| `Ctrl+[`                | Send Backward (one)   | Home > Arrange > Send to Back > Send Backward | `ObjectSendBackward`           |
| `Ctrl+Shift+Home`       | Bring to Front (alt)  | Home > Arrange > Bring to Front            | `ObjectBringToFront`             |
| `Ctrl+Shift+End`        | Send to Back (alt)    | Home > Arrange > Send to Back              | `ObjectSendToBack`               |

### 6.4 Grouping

| Shortcut          | Action                              | Ribbon path                          | idMso                              |
|-------------------|-------------------------------------|--------------------------------------|------------------------------------|
| `Ctrl+G`          | Group selection                     | Home > Arrange > Group               | `ObjectGroupMenu`                  |
| `Ctrl+Shift+U`    | Ungroup                             | Home > Arrange > Group > Ungroup     | `ObjectsUngroup`                   |
| (UI)              | Add to Group                        | Home > Arrange > Group > Add to Group| `ObjectsAddToGroup`                |
| (UI)              | Remove from Group                   | Home > Arrange > Group > Remove from Group | `ObjectsRemoveFromGroup`     |
| (UI)              | Convert to Group                    | Developer > Group > Convert to Group | `ObjectsConvertToGroup`            |

Groups expose `GroupBehavior` cells: `IsDropTarget` (`SnapTo` group as drop
target), `DontMoveChildren`, `IsSnapTarget`, `IsTextEditTarget`. Hand-tune
under `Developer > Shape Design > Behavior` (`BehaviorDialog`).

### 6.5 Rotate and flip

| Shortcut    | Action                              | Ribbon path                                              | idMso                          |
|-------------|-------------------------------------|----------------------------------------------------------|--------------------------------|
| `Ctrl+L`    | Rotate Left 90° (legacy)            | Home > Arrange > Position > Rotate Shapes > Rotate Left  | `ObjectRotateLeft`             |
| `Ctrl+R`    | Rotate Right 90° (legacy)           | Home > Arrange > Position > Rotate Shapes > Rotate Right | `ObjectRotateRight`            |
| `Ctrl+J`    | Flip Vertical                       | Home > Arrange > Position > Rotate Shapes > Flip Vertical| `ObjectFlipVertical`           |
| (UI)        | Flip Horizontal                     | Home > Arrange > Position > Rotate Shapes > Flip Horizontal | `ObjectFlipHorizontal`      |
| (drag)      | Free rotate via the rotation handle | n/a                                                      | n/a                            |
| `Ctrl+L`/`Ctrl+R` (in text edit) | Align paragraph left / right | n/a                                          | n/a                            |

`Ctrl+L` and `Ctrl+R` collide with paragraph alignment when the text edit
cursor is active inside a shape. If the chord does not behave as expected,
press `Esc` first to leave text edit mode.

---

## 7. Text and formatting

### 7.1 Character formatting

| Shortcut          | Action                          | Ribbon path                          | idMso                            | ShapeSheet cell    |
|-------------------|---------------------------------|--------------------------------------|----------------------------------|--------------------|
| `Ctrl+B`          | Bold                            | Home > Font > Bold                   | `Bold`                           | `Char.Style` bit 1 |
| `Ctrl+I`          | Italic                          | Home > Font > Italic                 | `Italic`                         | `Char.Style` bit 2 |
| `Ctrl+U`          | Underline                       | Home > Font > Underline              | `Underline`                      | `Char.Style` bit 4 |
| `Ctrl+Shift+D`    | Double underline                | Home > Font > Underline gallery > Double | `UnderlineDouble`             | `Char.Style`       |
| `Ctrl+Shift+A`    | All Caps toggle                 | Home > Font > Change Case            | `AllCaps`                        | `Char.Case`        |
| `Ctrl+Shift+K`    | Small Caps                      | Home > Font > Change Case            | `SmallCaps`                      | `Char.Case`        |
| `Ctrl+=`          | Subscript                       | Home > Font > Subscript              | `Subscript`                      | `Char.Pos`         |
| `Ctrl+Shift++`    | Superscript                     | Home > Font > Superscript            | `Superscript`                    | `Char.Pos`         |
| `Ctrl+Shift+>`    | Increase font size              | Home > Font > Grow Font              | `FontSizeIncrease`               | `Char.Size`        |
| `Ctrl+Shift+<`    | Decrease font size              | Home > Font > Shrink Font            | `FontSizeDecrease`               | `Char.Size`        |
| `Ctrl+Spacebar`   | Reset character formatting      | Home > Font > Clear Formatting       | `ClearFormatting`                | resets `Char.*`    |
| `Ctrl+Q`          | Reset paragraph formatting      | Home > Paragraph (dialog launcher)   | `ResetParaFormatting`            | resets `Para.*`    |
| `F11`             | Open Character / Text dialog    | Home > Font (dialog launcher)        | `FormatTextDialog`               | `Char.*`           |
| (UI)              | Font name                       | Home > Font > Font name combo        | `FontFont`                       | `Char.Font`        |
| (UI)              | Font color                      | Home > Font > Font Color (split button) | `FontColorPicker`             | `Char.Color`       |
| (UI)              | Text highlight color            | Home > Font > Text Highlight Color   | `TextHighlightColorPicker`       | `Char.HighlightColor` |

### 7.2 Paragraph and alignment (in text edit mode)

`F2` enters text-edit mode on the selected shape; `Esc` exits.

| Shortcut          | Action                                  | Ribbon path                                | idMso                            | ShapeSheet cell      |
|-------------------|-----------------------------------------|--------------------------------------------|----------------------------------|----------------------|
| `Ctrl+L`          | Align paragraph left                    | Home > Paragraph > Align Left              | `AlignLeft`                      | `Para.HorzAlign=0`   |
| `Ctrl+E`          | Align paragraph center                  | Home > Paragraph > Center                  | `AlignCenter`                    | `Para.HorzAlign=1`   |
| `Ctrl+R`          | Align paragraph right                   | Home > Paragraph > Align Right             | `AlignRight`                     | `Para.HorzAlign=2`   |
| `Ctrl+J`          | Justify                                 | Home > Paragraph > Justify                 | `AlignJustify`                   | `Para.HorzAlign=3`   |
| `Tab`             | Increase indent                         | Home > Paragraph > Increase Indent         | `IndentIncreaseVisio`            | `Para.IndLeft`       |
| `Shift+Tab`       | Decrease indent                         | Home > Paragraph > Decrease Indent         | `IndentDecreaseVisio`            | `Para.IndLeft`       |
| (UI)              | Bullets gallery                         | Home > Paragraph > Bullets                 | `BulletsGalleryVisio`            | `Para.Bullet`        |
| (UI)              | Numbering gallery                       | Home > Paragraph > Numbering               | `NumberingGalleryVisio`          | `Para.Bullet`        |
| (UI)              | Align Top (vertical alignment)          | Home > Paragraph > Top                     | `AlignTopVisio`                  | `TextBlock.VerticalAlign=0` |
| (UI)              | Align Middle                            | Home > Paragraph > Middle                  | `AlignMiddleVisio`               | `TextBlock.VerticalAlign=1` |
| (UI)              | Align Bottom                            | Home > Paragraph > Bottom                  | `AlignBottomVisio`               | `TextBlock.VerticalAlign=2` |
| (UI)              | LTR / RTL paragraph direction           | Home > Paragraph > LTR / RTL               | `ParagraphDirectionLTR` / `ParagraphDirectionRTL` | `Para.Flags` |
| (UI)              | Paragraph dialog                        | Home > Paragraph (dialog launcher)         | `ParagraphDialogVisio`           | `Para.*`             |

### 7.3 Text editing inside a text block

| Shortcut                  | Action                                              |
|---------------------------|-----------------------------------------------------|
| `F2`                      | Enter / exit text edit mode on selected shape       |
| `Esc`                     | Exit text edit, return to shape select              |
| `Enter`                   | New paragraph                                       |
| `Shift+Enter`             | Soft line break inside paragraph                    |
| `Ctrl+Enter`              | New paragraph (also commits formula in ShapeSheet)  |
| `Ctrl+Tab`                | Insert literal Tab character                        |
| `Ctrl+Left` / `Ctrl+Right`| Cursor by word                                      |
| `Ctrl+Up` / `Ctrl+Down`   | Cursor by paragraph                                 |
| `Home` / `End`            | Beginning / end of line                             |
| `Ctrl+Home` / `Ctrl+End`  | Beginning / end of text block                       |
| `Shift+arrow`             | Extend selection by character / line                |
| `Ctrl+Shift+arrow`        | Extend selection by word / paragraph                |

### 7.4 Quick styles, fill, line, effects

| Action                              | Ribbon path                                          | idMso                                |
|-------------------------------------|------------------------------------------------------|--------------------------------------|
| Quick Styles gallery                | Home > Shape Styles > Quick Styles                   | `QuickShapeStyleGalleryVisio`        |
| Fill color picker                   | Home > Shape Styles > Fill                           | `ShapeFillColorPickerVisio`          |
| Line color picker                   | Home > Shape Styles > Line                           | `ShapeOutlineColorPickerVisio`       |
| Effects gallery (shadow / glow / …) | Home > Shape Styles > Effects                        | `ShapeEffectsGalleryVisio`           |
| Theme effects gallery               | Home > Shape Styles (gallery launcher)               | `ShapeStylesThemeEffectsGalleryVisio`|
| Format Shape pane                   | Home > Shape Styles (dialog launcher)                | `FormatShapeDialog`                  |

The pane covers Fill, Line, Shadow, Reflection, Glow, Soft Edges, 3-D Format,
3-D Rotation, Picture corrections, and binds to ShapeSheet sections
`Fill Format`, `Line Format`, `Shadow`, `3D Properties`, `Reflection`,
`Glow`, `SoftEdge`. See `references/theme-and-data-graphics.md`.

---

## 8. ShapeSheet — opening, navigating, editing

The ShapeSheet is the per-shape spreadsheet that backs every formula in a
Visio diagram. visio-master writes ShapeSheet content directly into the
`<Cell>` and `<Row>` elements of `pages/page*.xml`; opening the same shape's
ShapeSheet in Visio reflects exactly the cells you authored.

### 8.1 Opening a ShapeSheet

| Shortcut       | Action                                                    | Ribbon path                                          | idMso                            |
|----------------|-----------------------------------------------------------|------------------------------------------------------|----------------------------------|
| n/a (custom)   | Show ShapeSheet for selected shape                        | Developer > Show ShapeSheet                          | `ShowShapeSheet`                 |
| n/a            | Show ShapeSheet for the page                              | Developer > Show ShapeSheet > Show Page ShapeSheet   | `ShowPageShapeSheet`             |
| n/a            | Show ShapeSheet for the document                          | Developer > Show ShapeSheet > Show Document ShapeSheet | `ShowDocumentShapeSheet`       |
| n/a            | Show Master Document Stencil                              | Developer > Show Document Stencil                    | `ShowDocumentStencil`            |
| n/a            | Open Drawing Explorer (tree of pages, masters, styles)    | Developer > Show > Drawing Explorer                  | `DrawingExplorerWindow`          |

If `ShowShapeSheet` is greyed out, the Developer tab is not enabled — see
§11. From COM:

```vba
' VBA — open ShapeSheet for the first selected shape
Sub OpenSelectedShapeSheet()
    On Error GoTo NoSelection
    Dim shp As Visio.Shape
    Set shp = ActiveWindow.Selection.PrimaryItem
    shp.OpenSheetWindow.Activate    ' returns the ShapeSheet Window
    Exit Sub
NoSelection:
    MsgBox "Select a shape first.", vbInformation
End Sub
```

```python
# Python (pywin32) — open ShapeSheet from outside Visio
import pythoncom, win32com.client as w32

pythoncom.CoInitialize()
try:
    app = w32.GetActiveObject("Visio.Application")
    sel = app.ActiveWindow.Selection
    if sel.Count:
        sel.PrimaryItem.OpenSheetWindow().Activate()
finally:
    pythoncom.CoUninitialize()
```

### 8.2 Navigating cells

| Shortcut          | Action                                                 |
|-------------------|--------------------------------------------------------|
| `Tab`             | Move to next cell in row                               |
| `Shift+Tab`       | Move to previous cell in row                           |
| `Enter`           | Commit and move to cell below                          |
| `Ctrl+Enter`      | Commit formula and stay in cell                        |
| `Esc`             | Discard formula edit                                   |
| `F2`              | Edit current cell formula                              |
| `F3`              | Insert Function dialog                                 |
| `F4`              | Cycle reference style (relative / absolute, e.g. `Width` ↔ `=Width!Width`) |
| `F5`              | Recalculate page (`Document.Recalc`)                   |
| `F9`              | Recalculate selected formula                           |
| `Ctrl+`` (back-tick) | Toggle Values / Formulas view                       |
| `Ctrl+Home`       | First cell in current section                          |
| `Ctrl+End`        | Last filled cell in section                            |
| `Ctrl+Shift+E`    | Show / hide all sections (Sections dialog)             |
| `Ctrl+Shift+F`    | Insert Field (in cell formula)                         |
| `Ctrl+Delete`     | Delete current row                                     |
| Right-click cell  | Context menu — Insert Section / Insert Row / Edit Formula |

### 8.3 ShapeSheet ribbon controls

The ShapeSheet window has its own ribbon when active. The most common
controls and their idMso values:

| Action                              | Ribbon path                                       | idMso                                  |
|-------------------------------------|---------------------------------------------------|----------------------------------------|
| Insert section                      | ShapeSheet Tools Design > Sections > Insert       | `ShapeSheetSectionsDialog`             |
| Show sections (Geometry, User-defined, …) | ShapeSheet Tools Design > Sections > View Sections | `ShapeSheetShowSectionsDialog`     |
| Insert row                          | ShapeSheet Tools Design > Rows > Insert           | `InsertRowVisio`                       |
| Insert row before / after           | ShapeSheet Tools Design > Rows                    | `InsertRowBeforeVisio` / `InsertRowAfterVisio` |
| Delete row                          | ShapeSheet Tools Design > Rows > Delete           | `DeleteRowVisio`                       |
| Toggle edit mode                    | ShapeSheet Tools Design > View > Edit Formulas    | `ShapeSheetEditFormulasToggle`         |
| Toggle Values / Formulas            | ShapeSheet Tools Design > View > Formulas         | `ShapeSheetViewFormulasToggle`         |
| Function List pane                  | ShapeSheet Tools Design > View > Function List    | `ShapeSheetFunctionListVisio`          |
| Open `Window > Tile`                | View > Window > Arrange All                       | `WindowArrangeAll`                     |

### 8.4 Sections you commonly insert by hand

| Section                       | Add via                                          | ShapeSheet section name      |
|-------------------------------|--------------------------------------------------|------------------------------|
| Shape Data (custom properties)| `Insert Section` > Shape Data                    | `Property` (`Section.Prop`)  |
| User-defined cells            | `Insert Section` > User-defined cells            | `User` (`Section.User`)      |
| Actions (right-click menu)    | `Insert Section` > Actions                       | `Actions` (`Section.Action`) |
| Connection points             | `Insert Section` > Connection Points             | `Connections` (`Section.Connection`) |
| Controls (yellow handles)     | `Insert Section` > Controls                      | `Controls` (`Section.Control`) |
| Geometry                      | `Insert Section` > Geometry                      | `Geometry` (`Section.FirstComponent`+) |
| Hyperlinks                    | `Insert Section` > Hyperlinks                    | `Hyperlinks` (`Section.Hyperlink`) |
| Layer Membership              | `Insert Section` > Layer Membership              | `LayerMembership`            |

When `vsdx_export.py` produces a shape with `User.review = "TODO"` cells,
hand-tuning workflow:

1. `F8` Pointer Tool, click the shape.
2. `Alt+L`, then `S` for Show ShapeSheet (`ShowShapeSheet`).
3. `Ctrl+End` jumps to last User-defined cell.
4. Edit, `Ctrl+Enter` to commit, close ShapeSheet window.
5. `F5` to recalculate page if formulas reference page-scope cells.

---

## 9. Layers

Layers in Visio are page-scoped. They control visibility, print, lock, snap,
glue, color override, and active-layer assignment for new shapes. visio-master
emits one `Layer` row per logical group on `PageSheet.Layers`; each shape
references those layers via the `LayerMember` cell (a comma-separated list of
zero-based layer indexes).

### 9.1 Opening the Layer Properties dialog

| Path / chord                          | Action                                              | idMso                              |
|---------------------------------------|-----------------------------------------------------|------------------------------------|
| Home > Editing > Layers > Layer Properties | Opens the dialog with all layers on the current page | `LayerPropertiesDialog`         |
| Home > Editing > Layers > Active Layer | Picks the active layer for new shapes              | `LayerSelectActiveVisio`           |
| Home > Editing > Layers > Assign to Layer | Assigns selected shapes to one or more layers   | `LayerAssignDialog` / `AssignToLayerVisio` |
| (Right-click selected shapes)         | Format > Layer                                      | `AssignToLayerVisio`               |
| (UI)                                  | Add layer                                           | `LayerAddDialog`                   |
| (UI)                                  | Remove layer                                        | `LayerRemoveAction`                |
| (UI)                                  | Re-order layers (changes paint order)               | dialog only                        |

There is no built-in keyboard shortcut for the Layer Properties dialog.
Pinning it to QAT slot 1 (`Alt+1`) is the standard hand-tuning workflow.

### 9.2 Layer Properties columns

| Column                  | Cell name (Layers row)            | Notes                                                   |
|-------------------------|-----------------------------------|---------------------------------------------------------|
| Name                    | `Name`                            | UTF-8; uniqueness enforced per page.                    |
| `#`                     | (computed)                        | Number of shapes assigned.                              |
| Visible                 | `Visible`                         | `0` / `1` — hides the layer from view.                  |
| Print                   | `Print`                           | `0` / `1` — strips the layer from print output.         |
| Active                  | `Active`                          | At most one active layer per page; new shapes go here.  |
| Lock                    | `Lock`                            | Selection-disabled; cannot be moved.                    |
| Snap                    | `Snap`                            | Honors snap targets on this layer.                      |
| Glue                    | `Glue`                            | Connectors can glue to its shapes.                      |
| Color                   | `Color`                           | Overrides shape line color when set.                    |
| Color (column header)   | n/a                               | Click cycles 1..24 of the page palette + 0 (no override).|

### 9.3 Layer-membership tuning workflow

1. Select shapes in the canvas (`Ctrl+click`, `Shift+click`, or `Tab`).
2. Right-click > `Format > Layer`, or `Home > Editing > Layers > Assign to Layer`.
3. Tick layers in the dialog. The shapes' `LayerMember` cell is updated to a
   comma-separated index list (empty = no layer).
4. To change layer visibility, open `Layer Properties`, untick `Visible`.
5. Use `View > Show > Page Breaks` (`ViewPageBreaks`) to verify what prints
   when `Print` is unchecked on a layer.

If you produced layers via visio-master (`canvas.layers: [...]`), the layer
ordering is preserved in `PageSheet.Layers` rows. Hand-edits via the dialog
write back to the same rows. Round-trip-safe.

### 9.4 Layer cells in shapes

| Cell                | Purpose                                                       |
|---------------------|---------------------------------------------------------------|
| `LayerMember`       | Comma-separated layer indexes, e.g. `"0;2"` (layer 0 + 2).    |
| (PageSheet row)     | One `Layers` row per layer; rows are zero-indexed.            |
| `Document.LayerColor` | Per-document palette (24 entries plus index 0 = transparent). |

```vba
' VBA — assign selected shape(s) to a named layer
Sub AssignSelectionToLayer(layerName As String)
    Dim shp As Visio.Shape
    Dim lyr As Visio.Layer
    On Error GoTo NoLayer
    Set lyr = ActivePage.Layers(layerName)
    For Each shp In ActiveWindow.Selection
        lyr.Add shp, 0  ' 0 = preserve existing layer membership
    Next
    Exit Sub
NoLayer:
    MsgBox "Layer '" & layerName & "' not found on " & ActivePage.Name
End Sub
```

---

## 10. Validation — Process tab

The Process tab (`TabProcess`) hosts Visio's diagram validation engine. Rule
sets ship with templates (Basic Flowchart, Cross-Functional Flowchart, BPMN,
SharePoint Workflow). visio-master emits validation rules into
`document.xml`'s `ValidationRuleSets` and surfaces them in the Issues window.

### 10.1 Validation commands

| Action                              | Ribbon path                                       | idMso                              |
|-------------------------------------|---------------------------------------------------|------------------------------------|
| Run validation now                  | Process > Diagram Validation > Check Diagram      | `ValidateDiagram`                  |
| Toggle Issues window                | Process > Diagram Validation > Issues Window      | `ValidationIssuesWindow`           |
| Choose rule sets to run             | Process > Diagram Validation > Rules to Check     | `ValidationRulesetMenu`            |
| Validate workflow (SP 2010, legacy) | Process > SharePoint Workflow > Check Diagram     | `ValidateSharePointWorkflowDiagram`|

There is no default keyboard shortcut for `ValidateDiagram`. Pin to QAT slot
2 (`Alt+2`) for a one-chord validation pass.

### 10.2 Issues window

| Column          | Source                                     | Editable? |
|-----------------|--------------------------------------------|-----------|
| Issue           | `ValidationIssue.Description`              | No        |
| Category        | `ValidationIssue.RuleSet.Name`             | No        |
| Rule            | `ValidationIssue.Rule.Name`                | No        |
| Page / Shape    | `ValidationIssue.TargetPage` / `TargetShape` | No (link)|
| Ignore          | `ValidationIssue.Ignored = True`           | Toggle    |

Right-click an issue to:

- `Show Page` — jump to the offending shape.
- `Ignore This Issue` — mark `Ignored=True` on the issue.
- `Reset Ignored Issues` — re-validate ignored items.

### 10.3 Subprocess commands

| Action                              | Ribbon path                                            | idMso                              |
|-------------------------------------|--------------------------------------------------------|------------------------------------|
| Create subprocess from selection    | Process > Subprocess > Create from Selection           | `SubprocessCreateFromSelection`    |
| Link selection to existing subprocess | Process > Subprocess > Link to Existing             | `SubprocessLinkToExisting`         |
| Create new (blank) subprocess       | Process > Subprocess > Create New                      | `SubprocessCreateNew`              |

The subprocess shape acquires a `User.SubProcessID` cell pointing to the
target page name. visio-master uses the same convention.

### 10.4 Programmatic validation

```vba
' VBA — run all enabled rule sets, dump issues to Immediate window
Sub ValidateAll()
    Dim doc As Document, rs As ValidationRuleSet, iss As ValidationIssue
    Set doc = ActiveDocument
    For Each rs In doc.Validation.RuleSets
        rs.Enabled = True
    Next
    doc.Validation.Validate
    Debug.Print "Issues: " & doc.Validation.Issues.Count
    For Each iss In doc.Validation.Issues
        Debug.Print iss.Description & " on " & iss.TargetShape.NameU
    Next
End Sub
```

```python
# Python — summarize issues from outside Visio
import pythoncom, win32com.client as w32

pythoncom.CoInitialize()
try:
    app = w32.GetActiveObject("Visio.Application")
    doc = app.ActiveDocument
    for rs in doc.Validation.RuleSets:
        rs.Enabled = True
    doc.Validation.Validate()
    for iss in doc.Validation.Issues:
        print(f"{iss.RuleSet.Name}/{iss.Rule.Name}: "
              f"{iss.Description} -> {iss.TargetShape.NameU}")
finally:
    pythoncom.CoUninitialize()
```

---

## 11. Developer tab — enable, ShapeSheet, VBA, add-ins

### 11.1 Enabling Developer mode

The Developer tab is hidden by default. Enable via any of:

1. **UI**: `File > Options > Customize Ribbon > Main Tabs > Developer` (tick).
2. **Settings property**: `Application.Settings.RunInDeveloperMode = True` (VBA).
3. **Registry** (per-user, persistent):

   ```
   [HKEY_CURRENT_USER\Software\Microsoft\Office\16.0\Visio\Application]
   "ShowDeveloperTab"=dword:00000001
   "RunInDeveloperMode"=dword:00000001
   ```

   `16.0` is the version key for Visio 2016 / 2019 / 2021 / LTSC / Microsoft 365.
4. **Group Policy**: `User Configuration > Administrative Templates > Microsoft
   Visio 16 > Visio Options > General > Show Developer tab in the Ribbon`.
5. **Ribbon XML override** in a custom add-in:

   ```xml
   <customUI xmlns="http://schemas.microsoft.com/office/2009/07/customui">
     <ribbon>
       <tabs><tab idMso="TabDeveloper" visible="true"/></tabs>
     </ribbon>
   </customUI>
   ```

### 11.2 Developer ribbon controls

Code group: `VisualBasic` (`Alt+F11`), `MacroPlay` (`Alt+F8`), `MacroRecord`,
`MacroSecurity`, `ComAddInsDialog`, `AddInManager`, `RunAddon`. See §15.1
for shortcuts.

| Group              | Action                              | Shortcut       | idMso                              |
|--------------------|-------------------------------------|----------------|------------------------------------|
| Shape Design       | Behavior dialog                     | n/a            | `BehaviorDialog`                   |
| Shape Design       | Protection dialog                   | n/a            | `ProtectionDialog`                 |
| Shape Design       | Connection Point Tool               | `Ctrl+Shift+1` | `ConnectionPointToolVisio`         |
| Shape Design       | Operations menu                     | n/a            | `ShapeOperationsMenu`              |
| Shape Design       | Union                               | n/a            | `ShapeOperationsUnion`             |
| Shape Design       | Combine                             | n/a            | `ShapeOperationsCombine`           |
| Shape Design       | Fragment                            | n/a            | `ShapeOperationsFragment`          |
| Shape Design       | Intersect                           | n/a            | `ShapeOperationsIntersect`         |
| Shape Design       | Subtract                            | n/a            | `ShapeOperationsSubtract`          |
| Shape Design       | Trim                                | n/a            | `ShapeOperationsTrim`              |
| Shape Design       | Join                                | n/a            | `ShapeOperationsJoin`              |
| Shape Design       | Offset                              | n/a            | `ShapeOperationsOffset`            |
| Shape Design       | Fit Curve                           | n/a            | `ShapeOperationsFitCurve`          |
| Shape Design       | Reverse Ends                        | n/a            | `ShapeOperationsReverseEnds`       |
| Shape Design       | Update Alignment Box                | n/a            | `ShapeOperationsUpdateAlignmentBox`|
| ShapeSheet         | Show ShapeSheet                     | n/a            | `ShowShapeSheet`                   |
| ShapeSheet         | Show Document Stencil               | n/a            | `ShowDocumentStencil`              |
| ShapeSheet         | Drawing Explorer                    | n/a            | `DrawingExplorerWindow`            |
| Add-Ins            | My Add-ins                          | n/a            | `OfficeAddInsManageMyAddIns`       |
| Add-Ins            | Get Add-ins (Office Store)          | n/a            | `StoreSeekAndStartAddIns`          |

### 11.3 Behavior, Protection, Layer dialogs

Behavior dialog (`BehaviorDialog`) tabs and the cells they edit:
`Interaction style` (`LineJump`, `IsTextEditTarget`),
`Selection` (cells in `Section.Protection`),
`Group` (`IsDropTarget`, `DontMoveChildren`, `IsSnapTarget`),
`Double-click` (`EventDblClick`),
`Placement` (`LayoutAndRouteOn`, `ShapePlowCode`, `ShapePermeable*`),
`Resize behavior` (`Resize`).

Protection dialog (`ProtectionDialog`) flips `LockMoveX`, `LockMoveY`,
`LockHeight`, `LockWidth`, `LockAspect`, `LockBegin`, `LockEnd`,
`LockRotate`, `LockGroup`, `LockTextEdit`, `LockFormat`, `LockSelect`,
`LockDelete`, `LockCalcWH`, `LockCrop`, `LockCustProp`, `LockThemeColors`,
`LockThemeEffects`, `LockThemeFonts`, `LockVtxEdit` cells in
`Section.Protection`.

---

## 12. Insert, Design, Data, Review (quick lookup)

### 12.1 Insert tab — `TabInsert`

| Action                              | Shortcut       | Ribbon path                                      | idMso                                |
|-------------------------------------|----------------|--------------------------------------------------|--------------------------------------|
| Insert blank page                   | n/a            | Insert > Pages > Blank Page                      | `PageNewBlankVisio`                  |
| Insert background page              | n/a            | Insert > Pages > Background                      | `BackgroundPageMenuVisio`            |
| Insert picture from file            | n/a            | Insert > Illustrations > Pictures                | `PictureInsertFromFile`              |
| Insert online picture               | n/a            | Insert > Illustrations > Online Pictures         | `PictureInsertFromOnlineSource`      |
| Insert chart                        | n/a            | Insert > Illustrations > Chart                   | `ChartInsert`                        |
| Insert CAD drawing                  | n/a            | Insert > Illustrations > CAD Drawing             | `CADInsertDrawing`                   |
| Open Shapes pane                    | `Alt+F1`       | Insert > Shapes (or View > Show > Task Panes)    | `ShapeWindow`                        |
| Insert container                    | n/a            | Insert > Diagram Parts > Container               | `ContainerInsertGalleryVisio`        |
| Insert callout                      | n/a            | Insert > Diagram Parts > Callout                 | `CalloutGalleryVisio`                |
| Insert connector                    | `Ctrl+3`       | Insert > Diagram Parts > Connector               | `ConnectorToolVisio`                 |
| Insert hyperlink                    | `Ctrl+K`       | Insert > Links > Hyperlink                       | `HyperlinkInsert`                    |
| Insert text box                     | n/a            | Insert > Text > Text Box                         | `TextBoxInsertGalleryVisio`          |
| Insert header & footer              | n/a            | Insert > Text > Header & Footer                  | `HeaderFooterInsert`                 |
| Insert object (OLE)                 | n/a            | Insert > Text > Object                           | `CreateObject`                       |
| Insert field code                   | `Ctrl+F9`      | Insert > Text > Field                            | `InsertFieldDialog`                  |
| Insert symbol                       | n/a            | Insert > Text > Symbol                           | `SymbolInsert`                       |
| Insert equation                     | `Alt+=`        | Insert > Text > Equation                         | `EquationInsertNew`                  |

### 12.2 Design tab — `TabDesignVisio`

| Action                              | Shortcut    | Ribbon path                                          | idMso                              |
|-------------------------------------|-------------|------------------------------------------------------|------------------------------------|
| Page Setup dialog                   | `Shift+F5`  | Design > Page Setup (dialog launcher)                | `PageSetupDialog`                  |
| Orientation                         | n/a         | Design > Page Setup > Orientation                    | `PageOrientationGallery`           |
| Page size gallery                   | n/a         | Design > Page Setup > Size                           | `PageSizeGalleryVisio`             |
| Auto-Size page                      | n/a         | Design > Page Setup > Auto Size                      | `PageAutoSize`                     |
| Themes gallery                      | n/a         | Design > Themes                                      | `ThemesGalleryVisio`               |
| New theme                           | n/a         | Design > Themes > New Theme                          | `ThemeNew`                         |
| Variants gallery                    | n/a         | Design > Variants                                    | `VariantsGalleryVisio`             |
| Theme colors gallery                | n/a         | Design > Variants > Colors                           | `ThemeColorsGalleryVisio`          |
| Theme effects gallery               | n/a         | Design > Variants > Effects                          | `ThemeEffectsGalleryVisio`         |
| Connector variants                  | n/a         | Design > Variants > Connectors                       | `ConnectorVariantGalleryVisio`     |
| Embellishments                      | n/a         | Design > Variants > Embellishments                   | `EmbellishmentsGalleryVisio`       |
| Backgrounds gallery                 | n/a         | Design > Backgrounds > Backgrounds                   | `BackgroundsGalleryVisio`          |
| Borders & titles                    | n/a         | Design > Backgrounds > Borders & Titles              | `BorderTitleGalleryVisio`          |
| Connector style                     | n/a         | Design > Layout > Connectors                         | `ConnectorStyleGalleryVisio`       |
| Re-Layout Page                      | n/a         | Design > Layout > Re-Layout Page                     | `ReLayoutPageGalleryVisio`         |

The Page Setup dialog edits `PageSheet` cells: `PageWidth`, `PageHeight`,
`PrintPageOrientation`, `DrawingScaleType`, `PageScale`, `DrawingScale`,
`ShdwOffsetX`, `ShdwOffsetY`. Hand-tuning page extents from the dialog
preserves any formula-based `PageWidth = =Sheet.5!PageWidth` you wrote
through visio-master.

### 12.3 Data tab — `TabExternalData`

The Data tab is Pro/Plan 2 only. Most controls are absent on Visio Standard
and Visio for the Web.

| Action                              | Shortcut     | Ribbon path                                          | idMso                              |
|-------------------------------------|--------------|------------------------------------------------------|------------------------------------|
| Custom Import (data wizard)         | n/a          | Data > External Data > Custom Import                 | `LinkDataToShapesVisio`            |
| Quick Import (Excel)                | n/a          | Data > External Data > Quick Import                  | `QuickImportVisio`                 |
| External Data window toggle         | n/a          | Data > External Data > External Data                 | `ExternalDataWindowToggle`         |
| Refresh All                         | `F5`         | Data > External Data > Refresh All                   | `RefreshAllVisio`                  |
| Refresh Data (selection)            | n/a          | Data > External Data > Refresh Data                  | `RefreshDataVisio`                 |
| Configure Refresh                   | n/a          | Data > External Data > Configure Refresh             | `ConfigureRefreshVisio`            |
| Toggle Shape Data window            | `Ctrl+Shift+D` * | Data > Shape Data > Shape Data                   | `CustomPropertiesWindow`           |
| Define Shape Data                   | n/a          | Data > Shape Data > Define Shape Data                | `CustomPropertiesDialog`           |
| Shape Data Sets                     | n/a          | Data > Shape Data > Shape Data Sets                  | `ShapeDataSetsTaskpane`            |
| Data Graphics gallery               | n/a          | Data > Display Data > Data Graphics                  | `DataGraphicsGalleryVisio`         |
| Edit / new data graphic             | n/a          | Data > Display Data > New / Edit Data Graphic        | `DataGraphicEdit`                  |
| Insert legend                       | n/a          | Data > Display Data > Insert Legend                  | `DataGraphicLegendInsert`          |
| Apply After Linking                 | n/a          | Data > Display Data > Apply After Linking            | `DataGraphicApplyAfterLinking`     |
| Reports                             | n/a          | Data > Advanced Data > Reports                       | `ReportRunDialog`                  |

`*` `Ctrl+Shift+D` collides with "double underline" in some builds. The
Shape Data window's idMso is the canonical bind.

### 12.4 Review tab — `TabReview`

| Action                              | Shortcut       | Ribbon path                                          | idMso                                |
|-------------------------------------|----------------|------------------------------------------------------|--------------------------------------|
| Spelling                            | `F7`           | Review > Proofing > Spelling                         | `Spelling`                           |
| Thesaurus                           | `Shift+F7`     | Review > Proofing > Thesaurus                        | `Thesaurus`                          |
| Word count                          | n/a            | Review > Proofing > Word Count                       | `WordCount`                          |
| New comment                         | `Ctrl+Alt+M`   | Review > Comments > New Comment                      | `ReviewNewCommentVisio`              |
| Toggle comments pane                | n/a            | Review > Comments > Show Comments                    | `ReviewToggleCommentsPane`           |
| Delete comment                      | n/a            | Review > Comments > Delete                           | `ReviewDeleteCommentVisio`           |
| Previous / Next comment             | n/a            | Review > Comments > Previous / Next                  | `ReviewPreviousCommentVisio` / `ReviewNextCommentVisio` |
| Reply to comment                    | n/a            | Review > Comments > Reply                            | `ReviewReplyCommentVisio`            |
| Resolve comment                     | n/a            | Review > Comments > Resolve                          | `ReviewResolveCommentVisio`          |
| Translate                           | n/a            | Review > Language > Translate                        | `Translate`                          |
| Set proofing language               | n/a            | Review > Language > Set Proofing Language            | `LanguageSetProofingLanguage`        |
| Language preferences                | n/a            | Review > Language > Language Preferences             | `LanguagePreferences2`               |

---

## 13. Quick Access Toolbar (QAT) for hand-tuning

The QAT lives above (or below) the ribbon and exposes any `idMso` as a
single-chord `Alt+<n>` shortcut. Slot 1 is `Alt+1`, slot 9 is `Alt+9`, slot
10 is `Alt+0`; slots 11+ require chord through a KeyTip.

### 13.1 Where the QAT is stored

| Path                                                       | Scope                                  |
|------------------------------------------------------------|----------------------------------------|
| `%LOCALAPPDATA%\Microsoft\Office\Visio.officeUI`           | Per-user QAT and ribbon customizations |
| `%APPDATA%\Microsoft\Visio\Visio.qat`                      | Legacy binary QAT (pre-2010, residual) |
| `<Document>.vsdx > /customUI/customUI14.xml`               | Document-embedded QAT (OPC part)       |

### 13.2 Recommended QAT for visio-master hand-tuning

The default QAT after a fresh install is `Save / Undo / Redo`. Replace it
with the following six-slot layout that maps to the hand-tuning workflow
described elsewhere in this reference:

| Slot | Chord     | idMso                              | Action                                |
|------|-----------|------------------------------------|---------------------------------------|
| 1    | `Alt+1`   | `LayerPropertiesDialog`            | Open Layer Properties                 |
| 2    | `Alt+2`   | `ValidateDiagram`                  | Run validation                        |
| 3    | `Alt+3`   | `ShowShapeSheet`                   | Open ShapeSheet for selected shape    |
| 4    | `Alt+4`   | `DrawingExplorerWindow`            | Open Drawing Explorer                 |
| 5    | `Alt+5`   | `Undo`                             | Undo                                  |
| 6    | `Alt+6`   | `Redo`                             | Redo                                  |
| 7    | `Alt+7`   | `RefreshAllVisio`                  | Refresh data sources                  |
| 8    | `Alt+8`   | `SelectionTaskPane`                | Open Selection Pane                   |
| 9    | `Alt+9`   | `ZoomFitToWindow`                  | Fit page to window                    |
| 10   | `Alt+0`   | `FormatShapeDialog`                | Open Format Shape pane                |

### 13.3 Deploying the QAT XML

```xml
<!-- %LOCALAPPDATA%\Microsoft\Office\Visio.officeUI -->
<mso:customUI xmlns:mso="http://schemas.microsoft.com/office/2009/07/customui">
  <mso:ribbon>
    <mso:qat>
      <mso:sharedControls>
        <mso:control idQ="mso:LayerPropertiesDialog" visible="true"/>
        <mso:control idQ="mso:ValidateDiagram"       visible="true"/>
        <mso:control idQ="mso:ShowShapeSheet"        visible="true"/>
        <mso:control idQ="mso:DrawingExplorerWindow" visible="true"/>
        <mso:control idQ="mso:Undo"                  visible="true"/>
        <mso:control idQ="mso:Redo"                  visible="true"/>
        <mso:control idQ="mso:RefreshAllVisio"       visible="true"/>
        <mso:control idQ="mso:SelectionTaskPane"     visible="true"/>
        <mso:control idQ="mso:ZoomFitToWindow"       visible="true"/>
        <mso:control idQ="mso:FormatShapeDialog"     visible="true"/>
      </mso:sharedControls>
    </mso:qat>
  </mso:ribbon>
</mso:customUI>
```

Restart Visio after writing the file. KeyTip ordering follows the order of
`<sharedControls>` children — list highest-frequency commands first.

### 13.4 Right-click "Add to Quick Access Toolbar"

The simplest path is the right-click menu: right-click any ribbon control and
choose `Add to Quick Access Toolbar`. The XML is rewritten in place and you
do not need to restart Visio. To remove, right-click the QAT button and
choose `Remove from Quick Access Toolbar`.

To position the QAT below the ribbon: right-click QAT > `Show Quick Access
Toolbar Below the Ribbon` (or `position="below"` in `<mso:qat>`).

---

## 14. Hand-tuning recipes (decision-tree quick access)

Concrete mouse-and-keyboard sequences for the common edits a user makes
after opening a visio-master `.vsdx` in Visio Desktop.

### 14.1 Tighten a connector route

Symptom: a dynamic connector takes a 3-bend path through other shapes.

1. `Ctrl+1` (Pointer Tool), click the connector once.
2. `Alt+L`, `S` to open ShapeSheet (Developer > Show ShapeSheet, idMso
   `ShowShapeSheet`).
3. Locate `Shape Layout > ShapeRouteStyle`. Set to `2` (straight) or `1`
   (right-angle) as desired.
4. `Ctrl+Enter` to commit, close ShapeSheet.
5. `F5` to recalculate page.
6. Drag connector midpoint to refine the route — Visio writes the
   waypoints into the connector's `Geometry` section.

### 14.2 Lock a shape's position

1. Select shape with `Ctrl+1`, click.
2. `Alt+L`, `P` (Developer > Shape Design > Protection),
   idMso `ProtectionDialog`.
3. Tick `Width`, `Height`, `X position`, `Y position`, `Rotation`.
4. `Enter` to commit. Cells `LockMoveX=1`, `LockMoveY=1`, `LockWidth=1`,
   `LockHeight=1`, `LockRotate=1` are written.
5. To lift the lock later: `Ctrl+Shift+P` (Pencil tool out) or repeat
   the dialog and untick.

### 14.3 Move a shape onto a new layer

1. `Ctrl+1`, select shapes (`Shift+click` to extend).
2. `Home > Editing > Layers > Assign to Layer` (idMso `AssignToLayerVisio`).
3. Tick the destination layer, untick others, `OK`.
4. To verify: open ShapeSheet for one shape (`ShowShapeSheet`) and inspect
   `LayerMember`. Should be a comma-separated list of zero-based indexes.

### 14.4 Hide a layer for print

`Home > Editing > Layers > Layer Properties`, untick `Print` for the layer.
`Ctrl+P` to verify in Print Preview.

### 14.5 Fix a validation issue

`Alt+P`, `K` runs `ValidateDiagram`; `Alt+P`, `I` opens the Issues window.
Double-click any issue to jump to the offending shape, fix it, re-run.

### 14.6 Replace a theme without losing direct overrides

`Alt+G`, hover a tile in `Design > Themes`, click to apply
(`ThemesGalleryVisio`). Direct `FillForegnd` / `LineColor` overrides survive
because they take precedence over `Theme.AccentN` slots. To reset to theme:
`Home > Shape Styles > Reset` (`QuickShapeStyleGalleryVisio` > `Reset`).

### 14.7 Re-flow a flowchart

`Ctrl+A`, then `Design > Layout > Re-Layout Page` (`ReLayoutPageGalleryVisio`),
choose direction. PageSheet `LineRouteExt`, `PlaceStyle`, `RouteStyle` and
shape `PinX/PinY` are rewritten.

### 14.8 Add custom shape data

Select shape, `Alt+A`, `D` (Data > Shape Data > Define Shape Data,
`CustomPropertiesDialog`). `New`, fill name + type
(`0=String`, `1=FixedList`, `2=Number`, `3=Boolean`, `4=VariableList`,
`5=Date`, `6=Duration`, `7=Currency`). The cell appears as a
`Property.<Label>` row in the ShapeSheet.

### 14.9 Audit shapes with a User cell tag

After visio-master writes `User.review = "TODO"` cells: `Ctrl+F`, expand
`In:`, tick `User-defined cells`, search `TODO`. `F4` walks the list.
`Ctrl+Shift+F` in the ShapeSheet locates formulas referencing `User.review`.

---

## 15. Macros, automation, and custom shortcuts

### 15.1 Running and recording macros

| Shortcut          | Action                          | Ribbon path                          | idMso                              |
|-------------------|---------------------------------|--------------------------------------|------------------------------------|
| `Alt+F8`          | Macros dialog (Run / Edit / Step Into) | View > Macros > Macros        | `MacroPlay`                        |
| `Alt+F11`         | Visual Basic IDE                | Developer > Code > Visual Basic     | `VisualBasic`                      |
| n/a               | Record Macro (legacy)           | Developer > Code > Record Macro     | `MacroRecord`                      |
| n/a               | Macro security                  | Developer > Code > Macro Security   | `MacroSecurity`                    |

Visio's macro security is per-user under
`HKCU\Software\Microsoft\Office\16.0\Visio\Security\VBAWarnings` (`1`=enable
all, `2`=warn for unsigned, `3`=disable except signed, `4`=disable all).
Default is `2`. visio-master never produces `.vsdm` files; if a user opens
your `.vsdx`, no macro warning appears.

### 15.2 Custom shortcut creation

Visio (unlike Word) does **not** have a *Customize Keyboard* dialog. Three
supported strategies:

1. **QAT slot binding (`Alt+1`..`Alt+0`)** — see §13. Easiest, no code.
2. **VBA `Application.OnKey`** — *not* available in Visio (Visio's VBA
   surfaces no `OnKey` method; Excel-only).
3. **Window event sink (`KeyDown`)** — register a handler for
   `Window.WindowEvents` (`EventCode = visEvtCodeKeyDown`) or
   `Application.KeyDown`, dispatch by `KeyCode` + `KeyButtonState`. This
   requires a VSTO add-in or a pywin32 process running alongside Visio.

```vba
' VBA — KeyDown sink in ThisDocument's class module
Private WithEvents app As Visio.Application
Private Sub Document_DocumentOpened(ByVal doc As IVDocument)
    Set app = Application
End Sub
Private Sub app_KeyDown(ByVal KeyCode As Integer, ByVal KeyButtonState As Integer, _
                       CancelDefault As Boolean)
    Const VK_R = &H52, KEY_CTRL = 2, KEY_SHIFT = 4
    If KeyCode = VK_R And (KeyButtonState And KEY_CTRL) And (KeyButtonState And KEY_SHIFT) Then
        Application.Addons("ValidateDiagram").Run ""
        CancelDefault = True
    End If
End Sub
```

```python
# Python — global KeyDown listener for Visio.Application
import pythoncom, win32com.client as w32

class VisioEvents:
    def OnKeyDown(self, KeyCode, KeyButtonState, CancelDefault):
        # Ctrl(2) + Shift(4) + R(0x52) -> Run validation
        if KeyCode == 0x52 and (KeyButtonState & 6) == 6:
            self._app.Addons("ValidateDiagram").Run("")
            CancelDefault[0] = True
        return CancelDefault

pythoncom.CoInitialize()
try:
    app = w32.DispatchWithEvents("Visio.Application", VisioEvents)
    app._app = app
    pythoncom.PumpMessages()
finally:
    pythoncom.CoUninitialize()
```

```powershell
# PowerShell 5.1+ — transient handler, foreground only
$visio = [Runtime.InteropServices.Marshal]::GetActiveObject('Visio.Application')
Register-ObjectEvent -InputObject $visio -EventName 'KeyDown' -Action {
    param($KeyCode, $KeyButtonState, [ref]$CancelDefault)
    if ($KeyCode -eq 0x52 -and ($KeyButtonState -band 6) -eq 6) {
        $visio.Addons.Item('ValidateDiagram').Run('') | Out-Null
        $CancelDefault.Value = $true
    }
} | Out-Null
```

### 15.3 KeyButtonState bits

`KeyButtonState` is a bitmask:

| Bit value | Meaning              | Constant in `visio.h`     |
|-----------|----------------------|---------------------------|
| `1`       | Left mouse button    | `visKeyLButton`           |
| `2`       | Control              | `visKeyControl`           |
| `4`       | Shift                | `visKeyShift`             |
| `8`       | Right mouse button   | `visKeyRButton`           |
| `16`      | Middle mouse button  | `visKeyMButton`           |
| `32`      | Alt (some builds)    | `visKeyAlt`               |

To require Ctrl+Shift exactly: `state == (visKeyControl | visKeyShift)` and
nothing else; with `(state & visKeyControl) && (state & visKeyShift)` you
also accept Ctrl+Shift+Alt (depends on whether Alt should be allowed).

---

## 16. Failure modes and idMso troubleshooting

| Symptom                                              | Likely cause                                                  | Fix                                                  |
|------------------------------------------------------|---------------------------------------------------------------|------------------------------------------------------|
| `ExecuteMso` raises `0x800A03EC`                     | Control disabled in current context (no selection / wrong tab)| Test `GetEnabledMso(idMso)` first; switch context.   |
| `idMso` not recognized at runtime                    | Control introduced in a later Visio build                     | Confirm Visio version with `Application.Build`.      |
| Keyboard shortcut chord behaves differently          | Locale-specific keymap; KeyTip alphabet differs               | Use `Alt+<KeyTip>` walk instead of raw chord.        |
| QAT changes do not appear after editing `Visio.officeUI` | Visio held the file open                                  | Close Visio, edit, restart.                          |
| `Application.KeyDown` never fires                    | Visio launched as another user (UAC); event sink not attached | Run handler from same user account.                  |
| Developer tab missing after registry edit            | Wrong hive (`HKLM` vs `HKCU`) or wrong version key            | Use `HKCU\...\16.0\Visio\Application`.               |
| Ribbon XML rejected on add-in load                   | Schema namespace mismatch                                     | Use `http://schemas.microsoft.com/office/2009/07/customui`. |
| `ShowShapeSheet` greyed out                          | Developer mode disabled                                       | `Settings.RunInDeveloperMode = True` or registry.    |
| Connector reroute dialog never opens                 | Connector not selected — overlay arrow selected instead       | Click body of connector line (between endpoints).    |
| Fit-to-Window misaligned after open                  | Window pinned to a previous zoom level                        | `Ctrl+Shift+W` or `View > Zoom > Fit to Window`.     |
| Layer Properties dialog disabled                     | Active page is a stencil (master) page                        | Switch to a foreground or background page.           |
| `Validate Diagram` reports nothing on every run      | All rule sets disabled                                        | `Process > Diagram Validation > Rules to Check` > tick rule sets. |
| Theme reset reverts custom fills                     | Direct overrides `LineColor`/`FillForegnd` without `=THEMEVAL()` | Re-author with `=THEMEVAL("FillColor",...)` formulas. |

### 16.1 Inspecting an idMso at runtime

```vba
' VBA — interrogate any idMso in any Office host
Sub InspectIdMso(idMso As String)
    With Application.CommandBars
        Debug.Print "Enabled : " & .GetEnabledMso(idMso)
        Debug.Print "Pressed : " & .GetPressedMso(idMso)
        Debug.Print "Visible : " & .GetVisibleMso(idMso)
        Debug.Print "Label   : " & .GetLabelMso(idMso)
    End With
End Sub
```

For Python, use `app.CommandBars.GetEnabledMso(id)` /
`GetVisibleMso(id)` / `GetLabelMso(id)` — same names, same semantics.

### 16.2 Tab idMso quick reference

Default tabs: `TabBackstage`, `TabHome`, `TabInsert`, `TabDesignVisio`,
`TabExternalData` (Pro/Plan2), `TabProcess`, `TabReview`, `TabView`. Opt-in:
`TabDeveloper` (§11). Contextual (only with matching selection):
`TabSetPictureToolsVisio` (picture), `TabSetContainerToolsFormat`
(container), `TabSetCalloutFormat` (callout), `TabSetWireframeFormat`
(wireframe), `TabSetDrawingToolsFormatVisio` (free-form draw),
`TabPrintPreview` (print preview), `TabHeaderAndFooter` (header/footer edit).

---

## 17. Cross-references

- `references/shapesheet-quick-ref.md` — cells edited from `ShowShapeSheet` /
  `OpenSheetWindow`, including `Char.*`, `Para.*`, `LineColor`, `FillForegnd`,
  `LayerMember`, and the `Section.User` / `Section.Prop` rows.
- `references/com-quick-ref.md` — `Application.CommandBars`, `Window`,
  `Selection`, event sinks driven by ribbon controls.
- `references/connector-routing.md` — `ShapeRouteStyle`, `LineRouteExt`,
  `ConFixedCode`, the Design > Layout > Connectors gallery.
- `references/theme-and-data-graphics.md` — Design tab themes, variants,
  embedded theme XML; Data tab pipeline.
- `references/canvas-formats.md` — Page Setup dialog mapping to PageSheet
  cells (`PageWidth`, `PageHeight`, `PrintPageOrientation`, …).
- `references/vsdx-format-quick-ref.md` — OPC parts written by visio-master,
  including `customUI/customUI14.xml` for embedded ribbon overrides.
- `references/architect.md` — when to lean on visio-master's automation
  vs. hand-tuning post-export.

---

## Sources

1. `research/24-ui-shortcuts-ribbon.md` — internal research log: Visio
   ribbon tabs, group idMso prefixes, KeyTip table, QAT XML schema, custom
   shortcut wiring (VBA / Python / PowerShell / VSTO), failure modes.

