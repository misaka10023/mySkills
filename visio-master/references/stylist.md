# Stylist — Theme, Data Graphics, Layers, Containers & Page Setup Reference

> The Stylist is the third role in the visio-master pipeline:
> **Architect → Drafter → Stylist**. It is the persona the same agent steps
> into after Drafter has placed every shape and routed every connector to
> `vsdx_output/<page>.vsdx`. Stylist's mandate is the narrow band of
> *theme + data graphics + layers + containers + background page + print
> setup* — visual coherence and operational concerns — without changing
> structure, content, or shape topology.
>
> Stylist NEVER introduces new colors, fonts, stencils, or shapes that
> are not already in [[diagram_lock]]. Every cell Stylist writes resolves
> against a value Architect already locked. Drift detection is hard-wired
> into the validation gate at §6.

---

## 1. Mandate & Boundaries

### 1.1 Role identity

| Attribute | Value |
|---|---|
| Reference file | `visio-master/references/stylist.md` |
| Step in pipeline | Step 7 — between Drafter Step 6 and final export |
| Inputs | `<project>/diagram_lock.md` (re-read per page), `<project>/vsdx_output/*.vsdx`, `<project>/data_links/*.{csv,xlsx,sql}` (optional), `templates/themes/<theme.id>/theme.xml` |
| Outputs | `<project>/vsdx_output/*.vsdx` mutated in-place; `<project>/data_link.json` (audit trail when DG enabled) |
| Hand-off to | Step 7 finalisation (`finalize_vsdx.py` → `vsdx_quality_check.py --post-stylist` → `vsdx_export.py`) |
| Quality gate | `vsdx_quality_check.py --post-stylist` exit 0 before export |

The role-switch marker every Stylist turn opens with:

```
## [Role Switch: Stylist]
📖 Reading role definition: ${SKILL_DIR}/references/stylist.md
📋 Current task: <theme apply | layer setup | container compose | data graphic bind | page setup>
🔁 Re-reading: <project_path>/diagram_lock.md (P<NN> entry, when per-page)
```

The marker is load-bearing: it pins the agent on this reference and creates
an audit trail the orchestrator scans for sub-phase outputs.

### 1.2 What Stylist owns

| Concern | Lock fields | Visio surface |
|---|---|---|
| Theme + variant | `theme.id`, `theme.variant`, `theme.embellishment_level`, `theme.color_overrides.*`, `colors.*` | `theme/theme1.xml`; `<DocumentSheet>` cells `ThemeIndex`, `VariantThemeIndex`, `VariantEmbellishmentIdx`; `<ColorEntry/>`; per-shape `THEMEGUARD()` rewrites |
| Layer setup | `layer_assignments.<name>.{print,visible,lock,snap,glue,active,color}` + per-page `pages.<NN>.layers[]` | `<Section N="Layer">` rows; `<Cell N="LayerMember">` rewrites |
| Container composition | `containers.<id>.{master,page,members,heading,resize,lock_membership,margin}` | `Page.DropContainer`; `User.msvStructureType="Container"`; `User.msvSDContainer*` |
| List composition | `lists.<id>.{master,page,members,direction,alignment,spacing}` | `Page.DropList`; `User.msvStructureType="List"`; `User.msvSDList*` |
| Data graphic binding | `data_links.{enabled,sources,bindings}`, `data_graphics[]`, `page_data_links.P<NN>` | `<DataRecordsets>`; per-shape `LinkedDataRecordsetID`; `<Section N="Property">`; `Shape.DataGraphic` |
| Background + Print setup | `canvas.background_page`, `print_setup.{paper_kind,fit_on_pages,centered_h,centered_v,scale,margins,grid,background}` | `<PageSheet>` cells `Background`, `BackPage`; Print Properties cells |

### 1.3 Forbidden — defer to Architect re-cycle

| Concern | Owner | Why Stylist defers |
|---|---|---|
| Add / delete `<Shape>` elements | Drafter | Topology is committed when Drafter signs off |
| Rewrite `<Connect>` rows or connector glue formulas | Drafter (see [[connector-routing]] and [[drafter]] §5) | Glue change desyncs `<Connects>` from cell formulas |
| Edit `<Text>` content | Drafter (content); Architect (copy edits via lock) | Stylist re-styles via theme; never rewrites the literal run |
| Swap stencil family / master `NameU` | Architect Eight Confirmations re-cycle | `stencils.set` collision breaks every `Master="@<NameU>"` placeholder |
| Hand-edit `diagram_lock.md` | Architect via `update_diagram_lock.py` | Hand-edits desync lock and page-XML; the script propagates atomically |
| Change canvas (`PageWidth`, `PageHeight`, `DrawingScale`) | Architect Confirmation 1 | Resizing post-Drafter shifts every coordinate |
| Introduce colors / fonts / images outside `colors.*` / `typography.*` / `images.*` | Architect via `update_diagram_lock.py` | Stylist applies, never invents — drift triggers post-Stylist errors |
| Run `Page.LayoutIncremental()` | `finalize_vsdx.py --layout` (Step 7) | Reflow is a deterministic post-pass; running it from Stylist masks DG-positioning bugs |

### 1.4 Discipline rules cited

Stylist inherits the Global Execution Discipline from `SKILL.md` and
`_BLUEPRINT.md §7.1`:

- **SERIAL EXECUTION** — the five sub-phases (§3.1 → §3.5) run in order.
- **NO CROSS-PHASE BUNDLING** — Stylist outputs only Stylist surface.
- **NO SPECULATIVE EXECUTION** — finalisation passes run after the
  corresponding sub-phase signs off, never inside it.
- **DIAGRAM_LOCK RE-READ PER PAGE** — same as [[drafter]] §2.1; see §4.
- **Sequential COM session** — `com_helper.py` enforces a process-wide
  lock; sub-agent / parallel COM is forbidden.

---

## 2. Pre-flight gate

Before the first Stylist turn, every check below MUST pass. Failures
abort with a `warning:` line; partial gates are forbidden.

| Check | How to verify | On failure |
|---|---|---|
| Drafter Phase Complete checkpoint emitted | Marker `[DRAFTER_PHASE_COMPLETE]` present | Bounce back to Drafter |
| `vsdx_quality_check.py` against `pages/` exits 0 | `python3 ${SKILL_DIR}/scripts/vsdx_quality_check.py <project>/pages/` | Bounce back to Drafter |
| `diagram_lock.md` unchanged since Drafter signed off | `git diff` empty, OR fingerprint matches recorded SHA-256 | Run `update_diagram_lock.py`, then re-run Drafter for affected pages |
| `comments/total.md` exists | File present and non-empty | Acceptable; surface `warning: comments missing — finalize will skip Comment-cell injection` |
| Locked theme bundle exists | `${SKILL_DIR}/templates/themes/<theme.id>/theme.xml` parses cleanly | Architect re-cycle to swap `theme.id` |
| Locked stencil set exists | `${SKILL_DIR}/templates/stencils/<stencils.set>/README.md` exists | Architect re-cycle |
| `vsdx_output/<draft>.vsdx` assembled | Page-XML fragments combined into a draft | Run the assembly step first |
| COM session reachable (when `--method com`) | `python3 ${SKILL_DIR}/scripts/com_helper.py ping` exit 0 | Fall back to `--method vsdx`; data linking and `DropContainer` skip with warnings |
| Backup created | `<project>/vsdx_output/.stylist-backup/<draft>.vsdx` byte-identical to pre-Stylist | Stylist refuses to mutate without rollback target |

Pre-flight verification snippet:

```python
"""Run Stylist pre-flight; return list of failures."""
import hashlib, shutil, subprocess, sys
from pathlib import Path


def stylist_preflight(project_path, skill_dir):
    project = Path(project_path)
    skill = Path(skill_dir)
    failures = []

    lock = project / "diagram_lock.md"
    if not lock.exists():
        return [f"diagram_lock.md missing under {project}"]

    pages_dir = project / "pages"
    if not pages_dir.exists() or not any(pages_dir.glob("*.vsdx-page.xml")):
        failures.append("Drafter pages missing under pages/")

    rc = subprocess.run(
        [sys.executable,
         str(skill / "scripts" / "vsdx_quality_check.py"),
         str(pages_dir)],
        capture_output=True, check=False).returncode
    if rc not in (0, 1):
        failures.append(f"vsdx_quality_check.py exits {rc}")

    draft = project / "vsdx_output"
    if not draft.exists() or not any(draft.glob("*.vsdx")):
        failures.append("vsdx_output/<draft>.vsdx missing")

    backup_dir = draft / ".stylist-backup"
    if not backup_dir.exists():
        backup_dir.mkdir(parents=True, exist_ok=True)
        for vsdx in draft.glob("*.vsdx"):
            shutil.copy2(vsdx, backup_dir / vsdx.name)

    fp_file = project / ".stylist" / "lock-fingerprint.txt"
    fp_file.parent.mkdir(parents=True, exist_ok=True)
    fp_file.write_text(hashlib.sha256(lock.read_bytes()).hexdigest(),
                       encoding="utf-8")
    return failures
```

---
## 3. Five sub-phases

Stylist runs five sub-phases in serial order. Each emits its own role-switch
marker (`📋 Current task: <sub-phase>`) and re-reads `diagram_lock.md` per
page where applicable. Combining sub-phases in one shell invocation is
forbidden.

### 3.1 Theme + Variant application

Foundation pass — deck-wide. Mandatory order: **theme → variant → 4-color
override → embellishment → recalc → THEMEGUARD rewrite**. Each step reads
state written by the prior one (see [[theme-and-data-graphics]] §2.1).

#### Theme application matrix — COM vs fallback

| Capability | COM (`--method com`) | XML fallback (`--method vsdx`) |
|---|---|---|
| Built-in theme bundle | `Document.SetTheme("Facet")` | Replace `visio/theme/theme1.xml` with bundle copy |
| Custom brand theme | Open in invisible Visio, `SetTheme(<custom>)` | Patch `theme1.xml` per [[theme-and-data-graphics]] §3 |
| Variant rotation | `SetThemeVariant(idx)` | Set `<DocumentSheet>/<Cell N="VariantThemeIndex">` |
| 4-color accent override | `Document.Colors.Item(1..4).RGB` | Append `<ColorEntry IX='0..3' RGB='RRGGBB'/>` |
| Embellishment level (0..3) | `DocumentSheet.CellsU("VariantEmbellishmentIdx").FormulaU` | Direct cell write |
| `THEMEGUARD()` rewrite | Walk `Page.Shapes` → set `FillForegnd.FormulaU` | Walk `<Shape>` in page-XML; rewrite `<Cell N="FillForegnd">` |
| Verify | `assert PageSheet.CellsU("ThemeIndex").ResultIU != 0` | Re-read `theme1.xml`; assert `<a:theme name="...">` matches |
| Failure mode | Silent no-op when name unknown — verify by cell read-back | XML write-write race when Visio is open — close before patching |

#### Apply theme — COM path

```python
"""Apply theme via Visio COM. Process-wide lock enforced by com_helper."""
import contextlib, pythoncom, win32com.client as win32

VIS_CMD_RECALC_DOCUMENT = 1312


@contextlib.contextmanager
def visio_session(visible=False):
    pythoncom.CoInitialize()
    app = None
    try:
        app = win32.gencache.EnsureDispatch("Visio.InvisibleApp")
        app.Visible = visible
        app.AlertResponse = 7
        yield app
    finally:
        if app is not None:
            try: app.Quit()
            except Exception: pass
        pythoncom.CoUninitialize()


def apply_theme_com(vsdx_path, theme_id, variant=1, embellishment=0,
                    color_overrides=None):
    with visio_session() as app:
        doc = app.Documents.Open(vsdx_path)
        try:
            doc.SetTheme(theme_id)
            assert doc.PageSheet.CellsU("ThemeIndex").ResultIU != 0, \
                f"SetTheme silently failed for {theme_id!r}"
            doc.SetThemeVariant(variant)
            for slot, (r, g, b) in (color_overrides or {}).items():
                c = doc.Colors.Item(slot)
                c.Red, c.Green, c.Blue = r, g, b
            doc.PageSheet.CellsU("VariantEmbellishmentIdx").FormulaU = \
                str(embellishment)
            app.DoCmd(VIS_CMD_RECALC_DOCUMENT)
            doc.Save()
        finally:
            doc.Close()
```

#### Apply theme — vsdx fallback

```python
"""Patch theme1.xml + DocumentSheet variant cells. No Visio install needed."""
import shutil, zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
NS = "http://schemas.microsoft.com/office/visio/2012/main"
ET.register_namespace("a", A_NS)
ET.register_namespace("", NS)


def apply_theme_vsdx(vsdx_path, bundle_theme_xml, variant_idx,
                     embellishment_idx):
    src = Path(vsdx_path)
    shutil.copy2(src, src.with_suffix(".vsdx.stylist-backup"))
    bundle_bytes = Path(bundle_theme_xml).read_bytes()
    tmp = src.with_suffix(".vsdx.tmp")
    with zipfile.ZipFile(src, "r") as zin, \
         zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "visio/theme/theme1.xml":
                data = bundle_bytes
            elif item.filename == "visio/document.xml":
                data = _patch_doc(data, variant_idx, embellishment_idx)
            zout.writestr(item, data)
    tmp.replace(src)


def _patch_doc(xml_bytes, variant_idx, embellishment_idx):
    root = ET.fromstring(xml_bytes)
    docsheet = root.find(f"{{{NS}}}DocumentSheet")
    if docsheet is None:
        return xml_bytes
    for name, value in (("VariantThemeIndex", str(variant_idx)),
                        ("VariantEmbellishmentIdx", str(embellishment_idx))):
        for cell in docsheet.findall(f"{{{NS}}}Cell"):
            if cell.get("N") == name:
                cell.set("V", value)
                break
        else:
            new = ET.SubElement(docsheet, f"{{{NS}}}Cell")
            new.set("N", name); new.set("V", value)
    return ET.tostring(root, xml_declaration=True, encoding="UTF-8")
```

#### Verify

```python
"""Read theme1.xml back; assert name + accent slots match lock."""
import zipfile
from xml.etree import ElementTree as ET

A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"


def verify_theme(vsdx_path, expected_name, expected_accents):
    with zipfile.ZipFile(vsdx_path, "r") as z:
        try: data = z.read("visio/theme/theme1.xml")
        except KeyError: return False, "theme1.xml missing"
    root = ET.fromstring(data)
    if root.get("name", "").lower() != expected_name.lower():
        return False, f"theme name mismatch: {root.get('name')}"
    scheme = root.find(f".//{{{A_NS}}}clrScheme")
    for slot, expected_hex in expected_accents.items():
        node = scheme.find(f"{{{A_NS}}}{slot}/{{{A_NS}}}srgbClr")
        if node is None or node.get("val", "").upper() != expected_hex.upper():
            return False, f"slot {slot} mismatch"
    return True, "ok"
```

### 3.2 Layer setup

Layers live on the `<PageSheet>` as `<Section N="Layer">` rows; per-shape
membership is the `<Cell N="LayerMember">` cell with a semicolon-delimited
list of layer indices. Stylist creates the rows declared in the lock and
rewrites every shape's `LayerMember` to point at the right indices on
the right page.

#### Layer flag table

| Cell name | Constant | Default | Meaning |
|---|---|---|---|
| `Visible` | `visLayerVisible` (7) | `1` | Render at draw time; `0` hides without removing |
| `Print` | `visLayerPrint` (8) | `1` | Include in print; `0` for screen-only overlays |
| `Active` | `visLayerActive` (9) | `0` | Default-active for newly dropped shapes |
| `Lock` | `visLayerLock` (10) | `0` | Members cannot be selected / edited |
| `Snap` | `visLayerSnap` (11) | `1` | Members are snap targets for other shapes |
| `Glue` | `visLayerGlue` (12) | `1` | Members are glue targets for connectors |
| `Color` | `visLayerColor` (0) | `0` (none) | Layer-wide tint |
| `ColorTrans` | `visLayerColorTrans` (n/a) | `0` | Alpha on `Color` (0 opaque, 1 transparent) |
| `NameUniv` | `visLayerNameUniv` (13) | NameU | Universal English name; localisation-invariant |

#### Create a layer — COM

```python
"""Get-or-create a layer; set flags; assign shapes."""
VIS_LAYER_VISIBLE   = 7
VIS_LAYER_PRINT     = 8
VIS_LAYER_ACTIVE    = 9
VIS_LAYER_LOCK      = 10
VIS_LAYER_SNAP      = 11
VIS_LAYER_GLUE      = 12
VIS_LAYER_NAME_UNIV = 13


def ensure_layer(page, name_u, flags):
    layers = page.Layers
    layer = next((layers.Item(i) for i in range(1, layers.Count + 1)
                  if layers.Item(i).NameU == name_u), None)
    if layer is None:
        layer = layers.Add(name_u)
        layer.CellsC(VIS_LAYER_NAME_UNIV).FormulaU = f'"{name_u}"'
    cell_map = {"visible": VIS_LAYER_VISIBLE, "print": VIS_LAYER_PRINT,
                "active": VIS_LAYER_ACTIVE, "lock": VIS_LAYER_LOCK,
                "snap": VIS_LAYER_SNAP, "glue": VIS_LAYER_GLUE}
    for key, idx in cell_map.items():
        if key in flags:
            layer.CellsC(idx).FormulaU = str(int(flags[key]))
    return layer


def assign_shape_to_layers(shape, layer_indices):
    formula = ";".join(str(i) for i in layer_indices)
    shape.CellsU("LayerMember").FormulaU = f'"{formula}"'
```

#### Algorithm per page

For each `P<NN>`:

1. Re-read `diagram_lock.md` (per-page discipline; see §4).
2. Look up `pages.<NN>.layers` — the layer names this page hosts.
3. For each layer, call `ensure_layer` to create the row and apply flags
   from `layer_assignments.<layer>.*`.
4. Walk every `<Shape>` on the page. The default heuristic uses master
   `NameU` → layer mapping from `templates/stencils/<set>/README.md`
   (e.g. flowchart `Process` masters land on `flow`; lane title shapes
   land on `swim_lane_titles`). Lock-declared
   `pages.<NN>.layer_overrides.<shape_id>` wins over the heuristic.
5. Write `LayerMember` per shape.
6. Verify: every shape's indices resolve to existing layer rows.

### 3.3 Container & List composition

Containers and Lists are structured groupings (process domains, swim
lanes, BPMN pools, ranked queues). Stylist drops them around members
Drafter has already placed; member geometry is unchanged.

#### Container resize-mode table

| Value | Constant | Behaviour | Use when |
|---|---|---|---|
| `0` | `visContainerResizeNone` | Never resizes; members may overflow | Fixed-size domain frames where overflow is the visual signal |
| `1` | `visContainerResizeAsNeeded` | Grows to fit; never shrinks below initial drop | Default for swim lanes, BPMN pools, process domains |
| `2` | `visContainerResizeAlways` | Both grows and shrinks to track members exactly | Cluster boundaries; tight ERD entity groups |

Stylist's default is `1` unless the lock overrides. `lock_membership = 1`
prevents the user dragging members out (`User.msvSDContainerLocked = 1`).

#### Heading style

| Constant | Value | Visual |
|---|---|---|
| `visContainerHeadingNone` | 0 | No title bar |
| `visContainerHeadingBar` | 1 | Title bar across top |
| `visContainerHeadingTab` | 2 | Tab on top-left |
| `visContainerHeadingCorner` | 3 | Corner banner |

#### Drop a container — COM

```python
"""Drop a container around member shapes; configure properties."""
VIS_BUILTIN_CONTAINERS = 2
VIS_OPEN_DOCKED        = 0x40
VIS_OPEN_HIDDEN        = 0x80


def drop_container(page, master_name_u, member_ids, heading_text,
                   heading_style=1, resize=1, lock_membership=0,
                   margin=0.125):
    app = page.Application
    path = app.GetBuiltInStencilFile(VIS_BUILTIN_CONTAINERS, 0)
    sten = app.Documents.OpenEx(path, VIS_OPEN_DOCKED | VIS_OPEN_HIDDEN)
    master = sten.Masters.ItemU(master_name_u)
    sel = page.CreateSelection(0, 0)
    for sid in member_ids:
        sel.Select(page.Shapes.ItemFromID(sid), 2)
    container = page.DropContainer(master, sel)
    container.Text = heading_text
    container.ContainerProperties.HeadingStyle = heading_style
    container.ContainerProperties.ResizeAsNeeded = resize
    container.ContainerProperties.LockMembership = lock_membership
    container.CellsU("User.msvSDContainerMargin").FormulaU = str(margin)
    return container


def drop_list(page, master_name_u, member_ids_in_order, direction=0,
              alignment=1, spacing=0.125):
    app = page.Application
    path = app.GetBuiltInStencilFile(VIS_BUILTIN_CONTAINERS, 0)
    sten = app.Documents.OpenEx(path, VIS_OPEN_DOCKED | VIS_OPEN_HIDDEN)
    master = sten.Masters.ItemU(master_name_u)
    list_shape = page.DropList(master, None, False)
    list_shape.CellsU("User.msvSDListDirection").FormulaU = str(direction)
    list_shape.CellsU("User.msvSDListAlignment").FormulaU = str(alignment)
    list_shape.CellsU("User.msvSDListSpacing").FormulaU = str(spacing)
    for pos, sid in enumerate(member_ids_in_order, start=1):
        list_shape.ContainerProperties.InsertListMember(
            page.Shapes.ItemFromID(sid), pos)
    return list_shape
```

#### Container vs List discipline

| Question | Container | List |
|---|---|---|
| Does order matter? | No — members are a set | Yes — `User.msvSDListDirection` axis |
| Drop accepts members at drop time | Yes — `DropContainer(master, selection)` | No — drop empty; `InsertListMember(member, pos)` |
| Reorder | n/a | `InsertListMember(member, k)` shifts members `k..count` |
| Use case | BPMN pool, swim lane, process domain, network cluster | Priority queue, ordered phase markers |

### 3.4 Data graphics binding

Mandatory order: **associate → apply → refresh** ([[theme-and-data-graphics]]
§4). COM-only — the fallback path skips with a `warning:` line.

#### Data-graphic binding sequence

| # | Stage | Per-page steps | Verifies |
|---|---|---|---|
| 1 | **Associate** | `Document.DataRecordsets.Add(connStr, cmdStr, 0, name)`; `SetPrimaryKey(0, key)`; for each shape whose master matches a `bindings[].shape_class`, `Shape.LinkToData(rs.ID, row_id, fAutoText=True, fAutoData=True)`. The `fAutoData=True` flag makes Visio create the `Prop.<column>` rows. | `Shape.LinkedDataRecordsetID == rs.ID`; `Shape.CellsU("Prop.<col>").FormulaU != ""` |
| 2 | **Apply** | `dg = Document.DataGraphics.Add()`; for each `items[]` entry, `dg.DataGraphicItems.Add(<kind>)` and set `DataField`. Walk every linked shape: `shape.DataGraphic = dg`. | `Shape.DataGraphic.ID == dg.ID` |
| 3 | **Refresh** | `rs.Refresh()` to re-pull and trigger `EventDataChange`. | `rs.LastRefreshed > previous` |

Item type constants: `visDGItemTypeText=1`, `visDGItemTypeBar=2`,
`visDGItemTypeIconSet=3`, `visDGItemTypeColorByValue=4`.

Before applying a DG, Stylist verifies the target shape carries the
`Prop.<DataField>` rows the DG references; missing rows → `data_graphic_bind_error`
and rollback that shape's DG assignment.

#### Bind data graphic — COM

```python
"""Run associate -> apply -> refresh on a page; verify each step."""
VIS_DG_ITEM_TEXT, VIS_DG_ITEM_BAR = 1, 2
VIS_DG_ITEM_ICON, VIS_DG_ITEM_COLOR = 3, 4
VIS_REFRESH_ON_FILE_OPEN, VIS_REFRESH_LINKED = 1, 2
VIS_REFRESH_ADD_NEW_ROWS, VIS_REFRESH_AUTOMATIC = 32, 128


def bind_data_graphic(doc, page, lock_source, lock_dg, lock_bindings,
                      data_links_dir):
    if lock_source["kind"] == "xlsx":
        path = f"{data_links_dir}/{lock_source['path'].split('/')[-1]}"
        conn = ("Provider=Microsoft.ACE.OLEDB.16.0;"
                f"Data Source={path};"
                'Extended Properties="Excel 12.0 Xml;HDR=YES;IMEX=1"')
        cmd = f"SELECT * FROM [{lock_source['sheet']}$]"
    else:
        raise NotImplementedError(lock_source["kind"])

    rs = doc.DataRecordsets.Add(conn, cmd, 0, lock_source["id"])
    rs.SetPrimaryKey(0, lock_source["primary_key"])
    rs.RefreshSettings = (VIS_REFRESH_ON_FILE_OPEN | VIS_REFRESH_LINKED
                          | VIS_REFRESH_ADD_NEW_ROWS)

    binding_by_class = {b["shape_class"]: b for b in lock_bindings}
    row_ids = list(rs.DataRowIDs(0))
    for shp in page.Shapes:
        master = shp.Master.NameU if shp.Master else ""
        binding = binding_by_class.get(master.lower().replace(" ", "_"))
        if binding is None:
            continue
        try:
            key = shp.CellsU(f"Prop.{lock_source['primary_key']}").ResultStr("")
        except Exception:
            continue
        for rid in row_ids:
            if rs.GetRowData(rid)[0] == key:
                shp.LinkToData(rs.ID, rid, True, True)
                break

    item_kind = {"text": VIS_DG_ITEM_TEXT, "bar": VIS_DG_ITEM_BAR,
                 "icon": VIS_DG_ITEM_ICON, "color": VIS_DG_ITEM_COLOR}
    dg = doc.DataGraphics.Add()
    dg.NameU = lock_dg["id"]
    for item in lock_dg["items"]:
        di = dg.DataGraphicItems.Add(item_kind[item["kind"]])
        di.DataField = item["data_field"]
        if item["kind"] == "icon":
            di.IconSet = item.get("icon_set", 2)
        if item["kind"] == "color":
            di.CellsU("User.msvColorTarget").FormulaU = (
                f'"{item.get("target", "FillForegnd")}"')

    for shp in page.Shapes:
        if shp.LinkedDataRecordsetID == rs.ID:
            shp.DataGraphic = dg

    rs.Refresh()
    return rs, dg
```

#### Fallback behaviour

```
warning: data_links.enabled=true but --method vsdx selected.
         Data graphic binding skipped. Re-run with --method com on a
         host with Visio installed to apply.
```

The lock's `data_graphics[]` definitions remain in `data_link.json` for
re-application. The drawing renders correctly without DG decoration; a
subsequent `--method com` Stylist pass binds.

### 3.5 Background page + Print/Page setup

Final sub-phase. Assigns the background page (when locked) and writes
Print Properties cells. Touches only `<PageSheet>`.

#### Background page assignment

A Background page has `<PageSheet>/<Cell N="Background" V="1"/>`. Foreground
pages reference it by writing the background's `NameU` into their
`<Cell N="BackPage">`. Stylist:

1. Looks up `canvas.background_page`. Blank → skip.
2. Verifies a page with that NameU exists and is marked Background.
3. For every foreground page, sets `BackPage` to the resolved name.

```python
def assign_background(doc, background_page_name_u):
    bg = next((p for p in doc.Pages if p.NameU == background_page_name_u),
              None)
    if bg is None or bg.PageSheet.CellsU("Background").ResultIU != 1:
        raise RuntimeError(f"background page {background_page_name_u!r} "
                           "missing or not marked Background")
    for p in doc.Pages:
        if p.PageSheet.CellsU("Background").ResultIU == 1:
            continue
        p.PageSheet.CellsU("BackPage").FormulaU = f'"{background_page_name_u}"'
```

#### Print Properties cell mapping

| Cell name | Lock field | Type | Notes |
|---|---|---|---|
| `PaperKind` | `print_setup.paper_kind` | DMPAPER int | 1 Letter, 8 A3, 9 A4, 25 ANSI D, 0 custom |
| `PaperSize` | `print_setup.paper_size` | DMPAPERSIZE int | `0` = same as `PaperKind` |
| `PrintFitOnPages` | `print_setup.print_fit_on_pages` | bool 0/1 | `1` scales to fit `PrintOnPagesX/Y`; ignores `PrintScale` |
| `PrintOnPagesX/Y` | `print_setup.print_on_pages_{x,y}` | int | Tile dimensions when `fit=0` |
| `PrintCenteredH/V` | `print_setup.print_centered_{h,v}` | bool 0/1 | Centre on print page |
| `PrintScale` | `print_setup.print_scale` | float | Used only when `PrintFitOnPages=0` |
| `PrintGrid` | `print_setup.print_grid` | bool 0/1 | Print background grid |
| `PrintBackground` | `print_setup.print_background` | bool 0/1 | Include assigned Background page in print |
| `PageLeftMargin..PageBottomMargin` | `print_setup.page_*_margin` | length | In `canvas.units` |

Apply (idempotent across COM and fallback):

```python
PRINT_CELLS = (
    ("PaperKind", "paper_kind"),
    ("PaperSize", "paper_size"),
    ("PrintFitOnPages", "print_fit_on_pages"),
    ("PrintOnPagesX", "print_on_pages_x"),
    ("PrintOnPagesY", "print_on_pages_y"),
    ("PrintCenteredH", "print_centered_h"),
    ("PrintCenteredV", "print_centered_v"),
    ("PrintScale", "print_scale"),
    ("PrintGrid", "print_grid"),
    ("PrintBackground", "print_background"),
    ("PageLeftMargin", "page_left_margin"),
    ("PageRightMargin", "page_right_margin"),
    ("PageTopMargin", "page_top_margin"),
    ("PageBottomMargin", "page_bottom_margin"),
)


def apply_print_setup_com(page, print_setup):
    for cell_name, lock_key in PRINT_CELLS:
        if lock_key in print_setup:
            page.PageSheet.CellsU(cell_name).FormulaU = str(print_setup[lock_key])
```

Drift detection re-reads each cell after the apply; tolerance ε=1e-6 on
floats. Persistent drift on margins usually means the locked unit doesn't
match `canvas.units` — bounce back to Architect.

---

## 4. Per-page re-read discipline

> Long drawings drift off the declared theme / layer / data state mid-deck
> due to context compression. `diagram_lock.md` is the canonical execution
> reference — Stylist re-reads it once per page before mutating that
> page's state. Same discipline as [[drafter]] §2.1, same reason.

### 4.1 The hard rule

Before mutating each page's theme, layer, container, data-graphic, or
print state, Stylist MUST execute `read_file <project_path>/diagram_lock.md`.
Use only values from this file — not memory, not a sibling page that
"obviously matches".

### 4.2 Per-page re-read schedule

| Sub-phase | Re-read frequency | Why |
|---|---|---|
| §3.1 Theme + variant | Once at sub-phase start (deck-wide); per page only when `theme.color_overrides.<page>` | Theme is deck-wide; per-page overrides are the only per-page state |
| §3.2 Layer setup | Once per page | `pages.<NN>.layers` is per-page |
| §3.3 Containers + Lists | Once per page | Container drops are page-scoped |
| §3.4 Data graphics | Once per page when `page_data_links.P<NN>` is set | Per-page DG assignment may differ |
| §3.5 Background + print | Once per page | Print Properties are per-page |

### 4.3 Per-page marker

Each Stylist turn that mutates a specific page emits:

```
🔁 Re-reading: <project_path>/diagram_lock.md (P<NN> entry)
🎯 Sub-phase: <theme | layer | container | data-graphic | print-setup>
📋 Page: P<NN>_<page_name>
```

The orchestrator's checkpoint scanner uses this marker to confirm Stylist
performed the mandatory re-read.

### 4.4 Resuming after context compression

1. Re-read `_BLUEPRINT.md §7` (discipline rules).
2. Re-read this file — sections 1, 4, and 5.
3. Re-read `diagram_lock.md` and `diagram_spec.md`.
4. Re-read [[theme-and-data-graphics]] (one section relevant to the
   current sub-phase).
5. Inspect `<project>/.stylist/lock-fingerprint.txt` — if changed,
   restart Stylist from §3.1.
6. Continue from the next un-mutated page; do NOT re-apply a sub-phase
   to a page that already received it.

---

## 5. Forbidden adjustments

> Users sometimes ask Stylist for changes that require an Architect
> re-cycle. The redirect language is fixed so the user sees a consistent
> boundary.

### 5.1 The forbidden list

| User asks for | Why Stylist can't | Redirect to |
|---|---|---|
| Change colors beyond `theme.color_overrides.accent1..4` | New colors require Confirmation 5; they propagate into Drafter inline fills | Architect re-cycle: re-confirm `colors.*`; run `update_diagram_lock.py` |
| Change fonts | Drafter wrote `Char.Font` indices already; font swap renders as Calibri fallback | Architect re-cycle: re-confirm `typography.*`; re-run Drafter for affected pages |
| Swap stencil family | Master `NameU` values change; every `<Shape Master="@<NameU>">` Drafter wrote breaks | Architect re-cycle: full Drafter re-run |
| Add a new page | Page authorship is Drafter's surface (Step 6) | Architect: revise `page_count`, `page_rhythm`, `page_layouts`, `page_diagrams`; re-run Drafter for the new page |
| Restructure connectors | Connector glue is Drafter's surface ([[connector-routing]]); Stylist can't rewrite without breaking `<Connect>` row coherence | Architect: revise diagram brief; re-run Drafter |
| Add / remove shapes | Topology is Drafter's; container membership and glue depend on it | Architect: revise page brief; re-run Drafter |
| Per-page theme override when the lock has none | Requires `theme.color_overrides.P<NN>` in lock | Architect: add per-page entry; Stylist re-runs §3.1 |
| Change `canvas.format / width / height / scale` | Canvas is locked at Confirmation 1 | Architect re-cycle: full pipeline restart |
| Add / remove `data_links.sources[]` | Data link config is locked at Confirmation 8; feeds Drafter Prop row creation | Architect: revise `data_links.*`; Stylist re-runs §3.4 |

### 5.2 Redirect language

```
The change you described — <one-sentence summary> — is outside Stylist's
mandate. Stylist applies the theme, layers, containers, data graphics,
and print setup that Architect locked in diagram_lock.md; structural
changes (colors / fonts / stencils / page count / connectors / shape
topology / canvas) require an Architect re-cycle.

To apply the change:
  1. Switch role to Architect (re-run the Eight Confirmations with the
     proposed value).
  2. Run scripts/update_diagram_lock.py to propagate atomically.
  3. <If shape/connector topology changes:> re-run Drafter for the
     affected pages.
  4. Re-run Stylist; the change is then inside Stylist's mandate.

Would you like to switch role to Architect?
```

The `[Role Switch: Stylist]` block stays open and `[Role Switch:
Architect]` opens only on user confirmation. Stylist does NOT silently
improvise.

### 5.3 What Stylist CAN do (sometimes mistaken for forbidden)

- Apply theme variant rotation (1..4) within the locked theme.
- Apply 4-color override (`theme.color_overrides.accent1..accent4`).
- Toggle a layer's `Visible` / `Print` flag per page per the lock.
- Swap container heading style (Bar / Tab / Corner / None).
- Change list direction or alignment.
- Re-apply a data graphic after a refresh (idempotent).
- Toggle `print_grid`, `print_background`, margin values per the lock.

---

## 6. Validation gate

After Stylist signs off, the validator confirms locked state actually
landed in OPC parts. Hard gate — exit 1 blocks export.

### 6.1 Invocation

```bash
python3 ${SKILL_DIR}/scripts/vsdx_quality_check.py <project_path>/vsdx_output/ \
    --lock <project_path>/diagram_lock.md \
    --post-stylist \
    --pretty --summary
```

### 6.2 Post-Stylist check pack

| Check | Rule |
|---|---|
| Theme name match | `<a:theme name="...">` in `theme/theme1.xml` matches `lock.theme.id`; `<DocumentSheet>/ThemeIndex` non-zero; `VariantThemeIndex == lock.theme.variant` |
| Theme palette match | For each `lock.theme.color_overrides.accent<n>`, `<a:clrScheme>/<a:accent<n>>/<a:srgbClr val>` matches the locked HEX (case-insensitive) |
| Embellishment level | `VariantEmbellishmentIdx == lock.theme.embellishment_level` |
| THEMEGUARD coverage | Every theme-eligible shape has `FillForegnd` / `LineColor` / `Char.Color` rewritten to a `THEMEGUARD()` formula or a HEX from `lock.colors.*`. Unlocked HEX is an error |
| Layer presence | Every layer named in `lock.pages.<NN>.layers` exists as a Layer row on that page |
| Layer flag match | Each layer's `Visible/Print/Lock/Snap/Glue/Active` cells match `lock.layer_assignments.<layer>.*` |
| Layer assignment | Every shape's `LayerMember` resolves to existing row indices |
| Container drop | For each `lock.containers.<id>`, a `<Shape Type="Group">` with `User.msvStructureType="Container"` exists on the right page; members are inside its bbox |
| List drop | For each `lock.lists.<id>`, a List shape exists with members in lock-declared order; Direction / Alignment / Spacing match |
| DG bound | Every shape that should carry the DG (matched by `bindings.<class>`) has `Shape.DataGraphic == dg`; Prop rows referenced by DG items exist |
| Background page assignment | If `lock.canvas.background_page` is set, every foreground page's `BackPage` references a Background page with that NameU |
| Print setup | Every `<PageSheet>` has the cells in §3.5.3 set to lock values; ε=1e-6 on float comparisons |
| No new shapes / connectors | Pre-Stylist shape ID set ⊆ post-Stylist set, except for new container/list shells declared in lock |
| Lock fingerprint | `sha256(diagram_lock.md)` matches the pre-Stylist fingerprint — mismatch = error |

### 6.3 Failure remediation

| Error | Remediation |
|---|---|
| Theme name mismatch | Verify `templates/themes/<theme.id>/theme.xml` exists; re-run §3.1 |
| Layer missing on page | Re-run §3.2 with explicit `pages.<NN>.layers` |
| Container not found | Restore from `.stylist-backup/`; re-run §3.3; check member IDs |
| DG missing Prop row | Re-run §3.4 with `fAutoData=True`; or pre-create row on master |
| LayerMember references missing index | Re-run §3.2 fully; use `update_diagram_lock.py` if rename intended |
| Lock fingerprint changed | Restart Stylist from pre-flight; lock changes go through Architect |
| Theme inline HEX not in lock | Bounce back to Drafter for that page; re-Stylist after |

---

## 7. Hand-off to Step 7 (Validate + Export)

### 7.1 Checkpoint block (matches `SKILL.md` "✅ Stylist Phase Complete")

```markdown
## ✅ Stylist Phase Complete

- [x] Pre-flight gate passed (Drafter complete; vsdx_quality_check.py exit 0; lock unchanged; backup created)
- [x] §3.1 Theme + Variant applied: theme=<theme.id> variant=<n> embellishment=<level>
- [x] §3.2 Layer setup: <count> layers across <page_count> pages
- [x] §3.3 Containers + Lists composed: <container_count> containers, <list_count> lists
- [x] §3.4 Data graphics bound: <enabled|skipped> (<shape_count> shapes, <recordset_count> recordsets)
- [x] §3.5 Background + print setup applied: bg_page=<name|none>
- [x] vsdx_quality_check.py --post-stylist exit 0
- [x] Lock fingerprint matches pre-Stylist
- [ ] **Next**: Auto-proceed to Step 7 finalisation (total_md_split.py → finalize_vsdx.py → vsdx_export.py)
```

The checkpoint is required output — the orchestrator's gate scanner
rejects the hand-off without it.

### 7.2 What Stylist delivers

| Artifact | Path |
|---|---|
| Themed / layered / container-bound `.vsdx` | `<project>/vsdx_output/<draft>.vsdx` (mutated in-place) |
| Pre-Stylist backup | `<project>/vsdx_output/.stylist-backup/<draft>.vsdx` |
| Data link audit trail | `<project>/data_link.json` (when DG enabled) |
| Lock fingerprint | `<project>/.stylist/lock-fingerprint.txt` |
| Validator report | `<project>/.stylist/post-stylist.json` (when run with `--report`) |

### 7.3 Step 7 finalisation reads Stylist output

| Step 7 sub-step | Reads | Notes |
|---|---|---|
| 7.1 `total_md_split.py` | `comments/total.md` | Independent of Stylist |
| 7.2 `apply_theme.py` | n/a | No-op — Stylist's §3.1 already covered |
| 7.3 `data_link.py` | n/a | No-op — Stylist's §3.4 already covered |
| 7.4 `finalize_vsdx.py` | `vsdx_output/<draft>.vsdx` | Runs `glue-fix`, `layout`, `compress`, `verify-lock` |
| 7.5 `vsdx_quality_check.py --post-finalize` | `vsdx_final/<draft>.vsdx` | Catches drift introduced by `--layout` |
| 7.6 `vsdx_export.py` | `vsdx_final/<draft>.vsdx` | Produces `exports/<file>.vsdx` plus optional PDF / PNG / SVG |

When Stylist runs as a discrete role turn (recommended), `apply_theme.py`
and `data_link.py` are invoked from inside the Stylist turn; Step 7
starts at 7.4. The duplicate listing in `SKILL.md` reflects the script
ordering; this reference reflects the role boundary.

---

## 8. Rollback

If any sub-phase fails, Stylist rolls back to
`vsdx_output/.stylist-backup/` and surfaces the issue rather than
partial-applying. Partial application is the worst outcome — some shapes
themed, others not; some pages with DGs, others without; validator drift
across the whole drawing.

### 8.1 Rollback triggers

| Trigger | Rollback scope |
|---|---|
| §3.1 — `SetTheme` returns silently with `ThemeIndex == 0` | Full sub-phase; bounce to Architect (theme name wrong) |
| §3.1 — Bundle has fewer accent slots than `color_overrides` references | Full sub-phase; bounce to Architect (palette mismatch) |
| §3.2 — `Layers.Add(name)` fails (reserved name) | Per-page; warn; proceed with remaining pages |
| §3.3 — `DropContainer` raises `0x80040120 visStructDiagramFeatureDisabled` | Full sub-phase; ensure structured diagram features enabled |
| §3.3 — Member ID does not resolve to a `<Shape ID>` on the named page | Per-container; warn; skip that container |
| §3.4 — Recordset connection fails (missing file, OLEDB not registered) | Full sub-phase; surface error; theme + layer + container styling remain |
| §3.4 — Prop row missing on shape after `LinkToData(... fAutoData=False)` | Per-shape; re-run with `fAutoData=True` or pre-create the row |
| §3.5 — Background page name does not match a `<Page Background='1'>` | Skip background assignment; warn |
| §3.5 — Print setup cell write rejected (cell name typo) | Per-cell; warn; proceed |

### 8.2 Rollback procedure

```python
"""Rollback Stylist mutations to the pre-Stylist state."""
import shutil
from pathlib import Path


def rollback_stylist(project_path):
    project = Path(project_path)
    draft_dir = project / "vsdx_output"
    backup_dir = draft_dir / ".stylist-backup"
    if not backup_dir.exists():
        raise RuntimeError(
            f"backup directory missing: {backup_dir}. "
            "Cannot roll back Stylist mutations.")
    for backup_file in backup_dir.glob("*.vsdx"):
        shutil.copy2(backup_file, draft_dir / backup_file.name)
    data_link = project / "data_link.json"
    if data_link.exists():
        data_link.unlink()
    print(f"Rolled back Stylist mutations under {draft_dir}")
```

### 8.3 Surfaced output on rollback

```
## ⚠️ Stylist Rollback

Sub-phase: <§3.x — name>
Trigger: <one-line description>

Rollback scope: <full | per-page <NN> | per-container <id> | per-shape <ID>>
Action taken: Restored vsdx_output/<draft>.vsdx from .stylist-backup/

Diagnosis:
  - <bullet pointing to the lock field or COM call>
  - <bullet pointing to suggested remediation>

Next steps:
  1. <Architect re-cycle | re-run with --method <X> | check stencil licensing>
  2. After remediation, re-run Stylist from §3.1.

Stylist phase HALTED. The drawing is in its pre-Stylist state.
```

### 8.4 Idempotency

The sub-phases are designed so rollback + re-run produces the same output:

- §3.1 — `SetTheme(same)` is a no-op when `ThemeIndex` is correct;
  `SetThemeVariant(same)` likewise.
- §3.2 — `ensure_layer(name)` reuses the existing row.
- §3.3 — Re-dropping a container with the same members raises
  `visAlreadyContainerMember`; rollback restores backup before re-run.
- §3.4 — `LinkToData` on already-linked shape is no-op;
  `Shape.DataGraphic = dg` idempotent; `Refresh()` advances
  `LastRefreshed` (same data state).
- §3.5 — Cell writes are no-ops when value matches.

The contract relies on rollback restoring the persistent state.
Without rollback, re-running §3.3 against a drawing with existing
containers raises errors and creates a double-membership graph.

---

## 9. Cross-references

- [[architect]] — Eight Confirmations, lock authorship, `theme.id` /
  `theme.variant` / `colors.*` / `stencils.set`.
- [[drafter]] — per-page authorship, inline-HEX-from-lock discipline,
  validator gate before Stylist.
- [[theme-and-data-graphics]] — full theme application sequence (§2.1),
  custom theme XML recipe (§3), DG association (§4), Color-by-Value vs
  Icon Set (§5), end-to-end pipeline (§8).
- [[connector-routing]] — connector glue formulas and `<Connect>` row
  coherence (Drafter's surface; Stylist must not touch).

---

## Sources

- `_BLUEPRINT.md` — pipeline mental model, role roster, eight
  confirmations, discipline rules, Stylist role definition (§3.3).
- `visio-master/SKILL.md` — pipeline step listing, role-switching
  protocol, common failure modes; Step 7 sub-step ordering 7.1..7.6.
- `visio-master/references/architect.md` — Eight Confirmations
  reference; lock field definitions for `canvas`, `theme`, `colors`,
  `typography`, `stencils`, `layout`, `connectors`, `data_links`.
- `visio-master/references/drafter.md` — per-page lock re-read
  discipline (§2), banned ShapeSheet patterns (§9.2), hand-off-to-
  Stylist contract (§10).
- `visio-master/references/theme-and-data-graphics.md` — theme
  application sequence (§2), custom theme construction recipe (§3), DG
  associate→apply→refresh (§4), Color-by-Value vs Icon Set (§5), theme
  + DG interaction (§6), end-to-end recipe (§8).
- `visio-master/references/connector-routing.md` — connector glue
  modes and routing decisions Drafter owns.
- `visio-master/templates/spec_lock_reference.md` — canonical
  `diagram_lock.md` skeleton with the section vocabulary Stylist reads
  (`theme`, `colors`, `layer_assignments`, `containers`, `lists`,
  `page_data_links`, `data_graphics`, `canvas`, `print_setup`).
- `research/20-themes-styles.md` — DrawingML `theme1.xml` schema,
  `Document.SetTheme` / `SetThemeVariant`, `Document.Colors` slot
  mapping, `THEMEVAL` / `THEMEGUARD` / `MSO_THEME_COLOR` tokens.
- `research/21-data-linking-graphics.md` — `DataRecordsets`,
  `Shape.LinkToData`, `Page.AutoLinkShapes`, DataGraphic /
  DataGraphicItem types, `RefreshSettings`, conflict resolution.
- `research/22-containers-layers-pages.md` — Containers, Lists,
  Callouts; `ContainerProperties`; `Page.DropContainer` / `DropList`;
  User-defined cells `User.msvStructureType`, `msvSDContainer*`,
  `msvSDList*`; Layers and `LayerMember`; background pages.
- `research/23-export-print.md` — `Document.SaveAs`,
  `Document.ExportAsFixedFormat`, `Page.Export`, `Document.PrintOut`,
  Print Properties (`PrintFitOnPages`, `PrintCenteredH/V`, `PaperKind`,
  margins, `PrintBackground`, `PrintGrid`).

