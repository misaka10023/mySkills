# Stencil Library Index

> Index of stencil families that visio-master can discover and drive against
> a local Microsoft Visio Plan 2 / Visio 2024 / Visio 2021 / Visio 2019
> installation. **visio-master does not copy or bundle stencils.** It
> resolves them on demand from the user's Visio install directory, the
> user's `My Shapes` folder, or the running `Visio.Application` instance via
> `Application.GetBuiltInStencilFile` and `Application.TemplatePaths`. Every
> filename below is verified against shipping Visio editions (research notes
> 04, 12, 15); cloud-vendor stencils (Azure, AWS, GCP) are out-of-box
> downloads that visio-master locates but never redistributes.

---

## 1. Discovery model

visio-master treats stencils as **runtime references**, not assets. The
resolution order, in priority:

1. **Already-open `Document`s in the current Visio process.** Walk
   `Application.Documents` and match `Document.Type == visTypeStencil (2)`
   on `Document.Name` or `Document.Path`.
2. **`Application.GetBuiltInStencilFile(builtIn, measureSystem)`.** Returns
   the absolute path Visio itself would use for a built-in stencil at the
   active LCID, falling back to `1033` when a localized copy is missing.
3. **`Application.TemplatePaths`** (semicolon-delimited). Probe each
   directory for a bare filename match like `BASNET_M.VSSX`.
4. **`Application.MyShapesPath`** for user-installed third-party stencils
   (Azure / AWS / Cisco / community GCP).
5. **OS-conventional install paths** (see section 2) when no `Visio.Application`
   is reachable (e.g. headless inspection of a stencil `.vssx` via OPC
   parsing without launching Visio).

`Documents.OpenEx(path, visOpenRO + visOpenDocked)` is the canonical open
call; visio-master always opens stencils read-only and never writes back
into the user's install tree.

---

## 2. Built-in path conventions per OS

Microsoft Visio 16.0 (Visio 2016 through Visio Plan 2) ships built-in
stencils under a versioned **Office root** plus a **Visio Content** folder
keyed by **LCID**.

### 2.1 Windows (Click-to-Run, the only modern Visio target)

| Edition / channel | Default `<OfficeRoot>` |
|-------------------|------------------------|
| Visio Plan 2 / Microsoft 365 Apps (64-bit) | `%ProgramFiles%\Microsoft Office\root\Office16\` |
| Visio Plan 2 / Microsoft 365 Apps (32-bit on 64-bit Windows) | `%ProgramFiles(x86)%\Microsoft Office\root\Office16\` |
| Visio 2019 / 2021 / 2024 retail (Click-to-Run) | same as above |
| Visio 2016 MSI (legacy) | `%ProgramFiles%\Microsoft Office\Office16\` (no `root\` segment) |

Inside `<OfficeRoot>` the stencil and template content lives at:

```text
<OfficeRoot>\Visio Content\<LCID>\
```

The `<LCID>` is the numeric Windows locale ID. Visio's loader falls back
to `1033` (en-US) silently when a content file is missing for the active
LCID.

| LCID | Locale | Coverage |
|------|--------|----------|
| 1033 | en-US | Baseline; ships every template and stencil. |
| 2052 | zh-CN | General purpose; Engineering / UML often falls back to 1033. |
| 1036 | fr-FR | French. |
| 1031 | de-DE | German. |
| 1041 | ja-JP | Japanese. |
| 1042 | ko-KR | Korean. |
| 1046 | pt-BR | Brazilian Portuguese. |
| 1049 | ru-RU | Russian. |
| 3082 | es-ES | Spanish (Spain). |

User-installed stencils live in `Application.MyShapesPath`, which defaults
to `%USERPROFILE%\Documents\My Shapes\` (English Windows) or the localized
`Documents` equivalent.

### 2.2 macOS

Visio for Mac does not exist as a native desktop product. macOS users run
**Visio in a browser** (Visio for the web, Visio Plan 1/Plan 2 web tier),
which has no local stencil filesystem. visio-master is a Windows
COM-driven toolchain; on macOS it can only operate against `.vsdx` /
`.vssx` files copied locally and parsed as OPC packages.

### 2.3 Linux

Same as macOS. Visio has no Linux desktop binary. Linux users typically
edit `.vsdx` / `.vssx` files via OPC tooling or LibreOffice Draw import;
visio-master's COM automation paths do not apply.

---

## 3. Filename suffix convention

Visio uses 8.3-style legacy basenames with a measurement-system suffix.
Every shipping stencil and template comes in two flavors:

| Suffix    | Measurement system | Default page |
|-----------|--------------------|--------------|
| `_M.VSSX` | Metric (mm/cm/m)   | A4 / A3 / A1 |
| `_U.VSSX` | US Customary (in/ft) | Letter / Tabloid / ANSI D |

Older binary equivalents `_M.VSS` / `_U.VSS` remain loadable by Visio 16.0
but are no longer shipped; templates are `_M.VSTX` / `_U.VSTX` (and the
binary `.VST` is similarly legacy). Macro-enabled variants append `M`
before the `X` (`.VSSM`, `.VSTM`).

---

## 4. Stencil families bundled with Visio Plan 2

The following are shipped as part of every Visio Plan 2 installation under
`<OfficeRoot>\Visio Content\<LCID>\`. Each row pairs the canonical
universal filename pattern with the template that pre-loads it. Cloud
stencils (Azure, AWS, GCP, Cisco) are listed separately in section 5
because they are **not** part of the in-box content.

### 4.1 Flowchart family

| Stencil filename            | Display name                          | Pre-loaded by template |
|-----------------------------|---------------------------------------|------------------------|
| `BASFLO_M.VSSX` / `BASFLO_U.VSSX` | Basic Flowchart Shapes           | `BASFLO_M.VSTX` / `_U.VSTX` |
| `CONNEC_M.VSSX` / `CONNEC_U.VSSX` | Connectors                       | every flowchart template |
| `CROSSF_M.VSSX` / `CROSSF_U.VSSX` | Cross-Functional Flowchart Shapes | `CROSSF_M.VSTX` / `_U.VSTX` |
| `WORKOB_M.VSSX` / `WORKOB_U.VSSX` | Workflow Objects                 | `WORKFL_M.VSTX` / `_U.VSTX` |
| `WORKST_M.VSSX` / `WORKST_U.VSSX` | Workflow Steps                   | `WORKFL_M.VSTX` / `_U.VSTX` |
| `BPMN_M.VSSX`  / `BPMN_U.VSSX`    | BPMN Basic Shapes                | `BPMN_M.VSTX` / `_U.VSTX` |
| `BPMN2_M.VSSX` / `BPMN2_U.VSSX`   | BPMN Conversation Shapes         | `BPMN_M.VSTX` (Visio 2016+) |

### 4.2 Brainstorming, Org Chart, Mind Map

| Stencil filename             | Display name           | Pre-loaded by template |
|------------------------------|------------------------|------------------------|
| `BRSTRM_M.VSSX` / `_U.VSSX`  | Brainstorming Shapes   | `BRSTRM_M.VSTX` / `_U.VSTX` |
| `LEGEND_M.VSSX` / `_U.VSSX`  | Legend Shapes          | brainstorming, business |
| `ORGCH_M.VSSX`  / `_U.VSSX`  | Org Chart Shapes       | `ORGCH_M.VSTX` / `_U.VSTX` |
| `ORGCHM_M.VSSX` / `_U.VSSX`  | Org Chart Shapes (Multiple) | `ORGCH_M.VSTX` (Pro) |
| `MINDMAP_M.VSSX`             | Mind Map Shapes        | `MINDMAP_M.VSTX` (Visio 2019+; older SKUs reuse `BRSTRM`) |

### 4.3 Network family (in-box)

| Stencil filename               | Display name                       | Pre-loaded by template |
|--------------------------------|------------------------------------|------------------------|
| `NETLOC_M.VSSX`  / `_U.VSSX`   | Network and Peripherals (Basic)    | `NETBAS_M.VSTX` / `_U.VSTX` |
| `COMPC_M.VSSX`   / `_U.VSSX`   | Computers and Monitors             | `NETBAS_M.VSTX`, `NETDET_M.VSTX` |
| `NETPER_M.VSSX`  / `_U.VSSX`   | Network and Peripherals (Detailed) | `NETDET_M.VSTX` / `_U.VSTX` |
| `NETSRV_M.VSSX`  / `_U.VSSX`   | Servers                            | `NETDET_M.VSTX` |
| `RACKMT_M.VSSX`  / `_U.VSSX`   | Rack-mounted Servers (subset)      | `NETDET_M.VSTX` |
| `RACK_M.VSSX`    / `_U.VSSX`   | Rack-mounted Equipment             | `RACK_M.VSTX` / `_U.VSTX` |
| `FREES_M.VSSX`   / `_U.VSSX`   | Free-standing Rack Equipment       | `RACK_M.VSTX` |
| `CABLES_M.VSSX`  / `_U.VSSX`   | Cables and Connectors              | `RACK_M.VSTX` |
| `ACTDIR_M.VSSX`  / `_U.VSSX`   | Active Directory Objects           | shipped; `ACTDIR_M.VSTX` retired post-2010 |

> Note: research/15 also references the legacy **Basic Network Shapes**
> (`BASNET_M.VSSX` / `BASNET_U.VSSX`) and **Detailed Network Shapes**
> (`DETNET_M.VSSX` / `DETNET_U.VSSX`) names that older revisions used.
> Modern Visio Plan 2 ships these masters under the `NETLOC` / `NETPER` /
> `NETSRV` filenames listed above; visio-master probes both name forms
> when discovering by glob.

### 4.4 Software family

| Stencil filename                 | Display name                   | Pre-loaded by template |
|----------------------------------|--------------------------------|------------------------|
| `UMLCLS_M.VSSX`                  | UML Class                      | `UMLCLS_M.VSTX` |
| `UMLSEQ_M.VSSX`                  | UML Sequence                   | `UMLSEQ_M.VSTX` |
| `UMLACT_M.VSSX`                  | UML Activity                   | `UMLACT_M.VSTX` |
| `UMLSM_M.VSSX`                   | UML State Machine              | `UMLSM_M.VSTX` |
| `UMLUSE_M.VSSX`                  | UML Use Case                   | `UMLUSE_M.VSTX` |
| `UMLCMP_M.VSSX`                  | UML Component                  | `UMLCMP_M.VSTX` |
| `UMLDEP_M.VSSX`                  | UML Deployment                 | `UMLDEP_M.VSTX` |
| `DATAFL_M.VSSX` / `_U.VSSX`      | Data Flow Diagram Shapes       | `DATAFL_M.VSTX` / `_U.VSTX` |
| `GANE_M.VSSX`   / `_U.VSSX`      | Gane-Sarson                    | `DATAFL_M.VSTX` (alt notation) |
| `CROWSFOOT_M.VSSX`               | Crow's Foot Database Notation  | `DATABS_M.VSTX` (Visio Pro) |
| `IDEF1X_M.VSSX`                  | IDEF1X                         | `DATABS_M.VSTX` |
| `RELATIONAL_M.VSSX`              | Relational                     | `DATABS_M.VSTX` |
| `OBJECT_M.VSSX`                  | Object Relational              | `DATABS_M.VSTX` |
| `EERD_M.VSSX`                    | Enhanced Entity Relationship   | `DATABS_M.VSTX` |

### 4.5 Engineering family

| Stencil filename                 | Display name                       | Pre-loaded by template |
|----------------------------------|------------------------------------|------------------------|
| `BAELEC_M.VSSX` / `_U.VSSX`      | Fundamental Items                  | `BAELEC_M.VSTX` / `_U.VSTX` |
| `ANALOG_M.VSSX` / `_U.VSSX`      | Analog and Digital Logic           | `BAELEC_M.VSTX`, `LOGIC_M.VSTX` |
| `SWREL_M.VSSX`  / `_U.VSSX`      | Switches and Relays                | `BAELEC_M.VSTX` |
| `TRANSL_M.VSSX` / `_U.VSSX`      | Transmission Paths                 | `BAELEC_M.VSTX` |
| `INTSEM_M.VSSX` / `_U.VSSX`      | Integrated Circuit Components      | `LOGIC_M.VSTX` |
| `TERSOC_M.VSSX` / `_U.VSSX`      | Terminals and Connectors           | `LOGIC_M.VSTX` |
| `EQUI_M.VSSX`   / `_U.VSSX`      | Equipment - General                | `PFD_M.VSTX` / `_U.VSTX` |
| `EQHEAT_M.VSSX` / `_U.VSSX`      | Heat Exchangers                    | `PFD_M.VSTX` |
| `EQTANKS_M.VSSX`/ `_U.VSSX`      | Vessels                            | `PFD_M.VSTX` |
| `EQPUMP_M.VSSX` / `_U.VSSX`      | Pumps                              | `PFD_M.VSTX` |
| `PFDPI_M.VSSX`  / `_U.VSSX`      | Process Annotations                | `PFD_M.VSTX` |
| `PIDEQ_M.VSSX`  / `_U.VSSX`      | Equipment - P&ID                   | `PID_M.VSTX` / `_U.VSTX` |
| `PIDPI_M.VSSX`  / `_U.VSSX`      | Pipelines                          | `PID_M.VSTX` |
| `PIDIN_M.VSSX`  / `_U.VSSX`      | Instruments                        | `PID_M.VSTX` |
| `PIDVA_M.VSSX`  / `_U.VSSX`      | Valves and Fittings                | `PID_M.VSTX` |
| `EQGEN_M.VSSX`  / `_U.VSSX`      | Equipment - General (P&ID)         | `PID_M.VSTX` |
| `HVACEQ_M.VSSX` / `_U.VSSX`      | HVAC Equipment                     | `HVAC_M.VSTX` / `_U.VSTX` |
| `HVACDU_M.VSSX` / `_U.VSSX`      | HVAC Ductwork                      | `HVAC_M.VSTX` |
| `HVACPI_M.VSSX` / `_U.VSSX`      | HVAC Pipes                         | `HVAC_M.VSTX` |
| `HVACCT_M.VSSX` / `_U.VSSX`      | HVAC Controls and Equipment        | `HVAC_M.VSTX` |
| `PLUMB_M.VSSX`  / `_U.VSSX`      | Plumbing                           | `PLUMB_M.VSTX` / `_U.VSTX` |
| `PIPES_M.VSSX`  / `_U.VSSX`      | Pipes 1 / Pipes 2                  | `PLUMB_M.VSTX`, `HVAC_M.VSTX` |
| `BATHRM_M.VSSX` / `_U.VSSX`      | Bathroom                           | `PLUMB_M.VSTX`, `FLRPLN_M.VSTX` |

### 4.6 Maps & Floor Plans family

| Stencil filename                 | Display name                       | Pre-loaded by template |
|----------------------------------|------------------------------------|------------------------|
| `WALL_M.VSSX`   / `_U.VSSX`      | Walls, Shell and Structure         | `FLRPLN_M.VSTX`, `OFFLAY_M.VSTX`, `SITE_M.VSTX` |
| `DOORW_M.VSSX`  / `_U.VSSX`      | Doors and Windows                  | `FLRPLN_M.VSTX` |
| `BUILDC_M.VSSX` / `_U.VSSX`      | Building Core                      | `FLRPLN_M.VSTX`, `ETPLAN_M.VSTX` |
| `DIMARC_M.VSSX` / `_U.VSSX`      | Dimensioning - Architectural       | `FLRPLN_M.VSTX` |
| `SITEAC_M.VSSX` / `_U.VSSX`      | Site Accessories                   | `SITE_M.VSTX` / `_U.VSTX` |
| `GARDEN_M.VSSX` / `_U.VSSX`      | Garden Accessories                 | `SITE_M.VSTX` |
| `IRRIG_M.VSSX`  / `_U.VSSX`      | Irrigation                         | `SITE_M.VSTX` |
| `PLANT_M.VSSX`  / `_U.VSSX`      | Planting                           | `SITE_M.VSTX` |
| `VEHICLE_M.VSSX`/ `_U.VSSX`      | Vehicles                           | `SITE_M.VSTX`, `PLAYOUT_M.VSTX` |
| `OFFEQ_M.VSSX`  / `_U.VSSX`      | Office Equipment                   | `OFFLAY_M.VSTX` / `_U.VSTX` |
| `OFFFUR_M.VSSX` / `_U.VSSX`      | Office Furniture                   | `OFFLAY_M.VSTX` |
| `OFFAC_M.VSSX`  / `_U.VSSX`      | Office Accessories                 | `OFFLAY_M.VSTX` |
| `CUBES_M.VSSX`  / `_U.VSSX`      | Cubicles                           | `OFFLAY_M.VSTX` |
| `PANEL_M.VSSX`  / `_U.VSSX`      | Panel Systems                      | `OFFLAY_M.VSTX` |
| `RCPLAN_M.VSSX` / `_U.VSSX`      | Reflected Ceiling                  | `RCPLAN_M.VSTX` / `_U.VSTX` |
| `ELECT_M.VSSX`  / `_U.VSSX`      | Electrical and Telecom             | `ETPLAN_M.VSTX` / `_U.VSTX` |
| `REGSEC_M.VSSX` / `_U.VSSX`      | Registers, Grills and Diffusers    | `ETPLAN_M.VSTX`, `HVAC_M.VSTX` |
| `PLBASE_M.VSSX` / `_U.VSSX`      | Shop Floor - Storage / Distribution | `PLAYOUT_M.VSTX` / `_U.VSTX` |
| `PLMAC_M.VSSX`  / `_U.VSSX`      | Shop Floor - Machines / Equipment  | `PLAYOUT_M.VSTX` |
| `WAREHS_M.VSSX` / `_U.VSSX`      | Warehouse - Shipping and Receiving | `PLAYOUT_M.VSTX` |
| `SECEQ_M.VSSX`  / `_U.VSSX`      | Alarm and Access Control           | `SECPLN_M.VSTX` / `_U.VSTX` |
| `VIDSUR_M.VSSX` / `_U.VSSX`      | Video Surveillance                 | `SECPLN_M.VSTX` |
| `INITSF_M.VSSX` / `_U.VSSX`      | Initiation and Annunciation        | `SECPLN_M.VSTX` |

### 4.7 Schedule family

| Stencil filename                 | Display name                       | Pre-loaded by template |
|----------------------------------|------------------------------------|------------------------|
| `CALEND_M.VSSX` / `_U.VSSX`      | Calendar Shapes                    | `CALEND_M.VSTX` / `_U.VSTX` |
| `GANTT_M.VSSX`  / `_U.VSSX`      | Gantt Chart Shapes                 | `GANTT_M.VSTX` / `_U.VSTX` |
| `PERT_M.VSSX`   / `_U.VSSX`      | PERT Chart Shapes                  | `PERT_M.VSTX` / `_U.VSTX` |
| `TIMELINE_M.VSSX` / `_U.VSSX`    | Timeline Shapes                    | `TIMELINE_M.VSTX` / `_U.VSTX` |

### 4.8 Business family

| Stencil filename                 | Display name                       | Pre-loaded by template |
|----------------------------------|------------------------------------|------------------------|
| `MARKETC_M.VSSX` / `_U.VSSX`     | Marketing Charts and Diagrams      | `MARKETC_M.VSTX` / `_U.VSTX`, `SWOT_*` |
| `MARKETD_M.VSSX` / `_U.VSSX`     | Marketing Diagrams                 | `MARKETC_M.VSTX`, business templates |
| `TQM_M.VSSX`     / `_U.VSSX`     | TQM Diagram Shapes                 | `TQM_M.VSTX`, `SIXSIG_M.VSTX` |
| `CAUSEEFF_M.VSSX`/ `_U.VSSX`     | Cause and Effect Diagram Shapes    | `CAUSEEFF_M.VSTX`, `SIXSIG_M.VSTX` |
| `ITIL_M.VSSX`    / `_U.VSSX`     | ITIL Shapes                        | `ITIL_M.VSTX` (Visio Pro) |
| `LEAN_M.VSSX`    / `_U.VSSX`     | Lean / Value Stream Mapping        | `LEAN_M.VSTX` / `_U.VSTX` |
| `AUDIT_M.VSSX`   / `_U.VSSX`     | Audit Diagram Shapes               | `AUDIT_M.VSTX` / `_U.VSTX` |
| `EPC_M.VSSX`     / `_U.VSSX`     | EPC Diagram Shapes                 | `EPC_M.VSTX` / `_U.VSTX` |
| `BLOCK_M.VSSX`   / `_U.VSSX`     | Blocks                             | `BLOCK_M.VSTX` / `_U.VSTX` |
| `BLOCKR_M.VSSX`  / `_U.VSSX`     | Blocks Raised                      | `BLOCK_M.VSTX` |
| `BLOCK3D_M.VSSX` / `_U.VSSX`     | Blocks with Perspective            | `BLOCK_M.VSTX` |

### 4.9 Built-in (insert-only) stencils

These three are not docked by any template; the Insert ribbon and the
`Page.DropContainer` / `DropCallout` APIs open them via
`Application.GetBuiltInStencilFile`.

| `VisBuiltInStencilTypes` constant | Value | What it provides |
|-----------------------------------|-------|------------------|
| `visBuiltInStencilContainers`     | 0     | `Container 1` ... `Container 12`, list / hierarchy frames |
| `visBuiltInStencilCallouts`       | 1     | `Text callout`, balloon / line callouts |
| `visBuiltInStencilConnectors`     | 2     | Sidebar connector gallery (Visio 2010+) |

---

## 5. Cloud and vendor stencils (out-of-box downloads)

These are **not** part of the Visio install. visio-master locates them in
`Application.MyShapesPath` (`%USERPROFILE%\Documents\My Shapes\` on
en-US Windows) and never copies them into the project tree. Filename
patterns track the vendor's release cadence.

### 5.1 Microsoft Azure (official, refreshed quarterly)

| Filename glob                                    | Source |
|--------------------------------------------------|--------|
| `Azure_Public_Service_Icons_V*.vssx`             | learn.microsoft.com/azure/architecture/icons |
| `CnAI-YYYY-MM-DD.vssx` (Cloud and AI Symbol Set) | Microsoft Download Center |
| `AZURE_M.VSTX` companion template                | bundled inside the icon set zip |

Master `User.AzureService` and `User.AzureCategory` cells are how to
identify a master without name-matching against the volatile English
display name. Categories: Compute, Networking, Storage, Database,
AI+ML, IoT, Security, Identity, Containers, DevOps, General, Web,
Migrate, Management, Mixed Reality, Intune, Integration, Analytics.

### 5.2 AWS (community-maintained Visio repackaging)

AWS stopped shipping an official `.vssx` in 2022. The community
`aws-icons-for-visio` repository republishes each AWS Architecture Icons
release. Filename glob: `AWS_*.vssx` or `AWS<YEAR>_*.vssx`. Categories
mirror the AWS Console left rail: Analytics, Application Integration,
Compute, Containers, Database, Developer Tools, Internet of Things,
Machine Learning, Management & Governance, Migration & Transfer,
Networking & Content Delivery, Security Identity & Compliance, Storage.

Master `User.AwsService`, `User.AwsCategory`, and `User.IconVersion`
cells are the stable identifiers.

### 5.3 Google Cloud (no official Visio publication)

GCP publishes only SVG/PNG icons. Visio users obtain a `.vssx` via:

| Source | Filename pattern |
|--------|------------------|
| `gcp-icons-for-visio` community project | `GCP_*.vssx` |
| Lucidchart `.vsdx` export | exported per diagram |

Master cells follow the Azure / AWS conventions: `User.GcpService`,
`User.GcpCategory`, `User.IconVersion`, `Prop.GcpProject`,
`Prop.GcpRegion`, `Prop.ResourceId`.

### 5.4 Cisco

Cisco Network Topology Icons distributes `.vss` and `.vssx` per family:

| Stencil                              | Coverage |
|--------------------------------------|----------|
| `Cisco Routers.vssx`                 | ISR, ASR, NCS, CRS, GSR |
| `Cisco Switches and Hubs.vssx`       | Catalyst, Nexus, MDS, Meraki MS |
| `Cisco Wireless.vssx`                | Aironet, WLC, Meraki MR |
| `Cisco Security.vssx`                | ASA, FTD/Firepower, ISE, Duo |
| `Cisco Voice.vssx`                   | CUCM, Unity, IP phones, Webex |
| `Cisco Video.vssx`                   | TelePresence, codecs |
| `Cisco Storage.vssx`                 | MDS SAN, UCS S-series |
| `Cisco UCS and Servers.vssx`         | UCS B / C / X-series |
| `Cisco Optical.vssx`                 | ONS, NCS, ROADM |
| `Cisco WAN.vssx`                     | SD-WAN vEdge / cEdge / vSmart / vBond / vManage |
| `Cisco Buildings and Concepts.vssx`  | Buildings, internet, end users |
| `Cisco Generic.vssx`                 | Generic devices |

Cisco masters use the product code as `Master.NameU` for stable matching
across locales (e.g. `Cisco ASR 1000`, `Catalyst 9300`, `Nexus 9000`).

---

## 6. `VisBuiltInStencilTypes` enumeration

The stable bridge between Visio's loader and a stencil filename is the
`VisBuiltInStencilTypes` enum passed to
`Application.GetBuiltInStencilFile(builtIn, measureSystem)`. The `measureSystem`
argument uses `VisMeasurementSystem` (`visMSDefault = -2`, `visMSUS = 0`,
`visMSMetric = 1`).

| Constant                                       | Value | Resolves to |
|------------------------------------------------|-------|-------------|
| `visBuiltInStencilContainers`                  | 0     | Containers gallery |
| `visBuiltInStencilCallouts`                    | 1     | Callouts gallery |
| `visBuiltInStencilConnectors`                  | 2     | Connectors gallery |
| `visBuiltInStencilFlowchart`                   | 0 *   | `BASFLO_*.VSSX` (note: collides with Containers in some headers; verify per build) |
| `visBuiltInStencilCrossFunctionalFlowchart`    | 1 *   | `CROSSF_*.VSSX` |
| `visBuiltInStencilRack`                        | (build-specific) | `RACK_*.VSSX` |
| `visBuiltInStencilEquipmentPumps_PID`          | (build-specific) | `EQPUMP_*.VSSX` |
| `visBuiltInStencilBrainstorming`               | (build-specific) | `BRSTRM_*.VSSX` |

The enum is documented at `learn.microsoft.com/office/vba/api/visio.visbuiltinstenciltypes`;
the integer values vary slightly between Visio 2013, 2016, and 2019+
header revisions. visio-master should call the enum by name through the
PIA / late-bound `gencache`-loaded constants, not hardcode integers.

---

## 7. Programmatic discovery helpers

### 7.1 PowerShell - enumerate every shipping stencil

```powershell
$root = (Get-ItemProperty `
    'HKLM:\SOFTWARE\Microsoft\Office\ClickToRun\Configuration' `
    -Name InstallationPath -ErrorAction SilentlyContinue
    ).InstallationPath
if (-not $root) { $root = "$env:ProgramFiles\Microsoft Office\root" }
$lcid = 1033

$dir = Join-Path $root "Office16\Visio Content\$lcid"
Get-ChildItem $dir -Filter *.vssx -Recurse | ForEach-Object {
    [pscustomobject]@{
        File      = $_.Name
        SizeKB    = [int]($_.Length/1KB)
        Base      = $_.BaseName -replace '_[MU]$',''
        Units     = if ($_.BaseName -match '_M$') { 'Metric' } else { 'US' }
    }
} | Sort-Object Base, Units | Format-Table -AutoSize
```

### 7.2 Python - resolve via the live `Visio.Application`

```python
import os, pythoncom, win32com.client as w

VIS_OPEN_RO     = 2
VIS_OPEN_DOCKED = 512
VIS_TYPE_STENCIL = 2

def open_stencil(visio, name_or_path):
    """Resolve a stencil by short name or absolute path; return Document."""
    # 1. Already open?
    for d in visio.Documents:
        if d.Type == VIS_TYPE_STENCIL and (
                d.Name.upper() == name_or_path.upper()
                or d.FullName.upper() == name_or_path.upper()):
            return d
    # 2. Try GetBuiltInStencilFile when caller passed a known constant.
    if isinstance(name_or_path, int):
        path = visio.GetBuiltInStencilFile(name_or_path, 1)  # metric
        return visio.Documents.OpenEx(path, VIS_OPEN_RO | VIS_OPEN_DOCKED)
    # 3. Bare name -> resolved through TemplatePaths.
    return visio.Documents.OpenEx(name_or_path,
                                  VIS_OPEN_RO | VIS_OPEN_DOCKED)

pythoncom.CoInitialize()
try:
    visio = w.DispatchEx("Visio.Application")
    visio.Visible = False
    st = open_stencil(visio, "BASNET_M.VSSX")
    print(f"Opened {st.Name} from {st.Path}")
finally:
    pythoncom.CoUninitialize()
```

### 7.3 C# - read-only, hidden, no UI

```csharp
using Visio = Microsoft.Office.Interop.Visio;

public static Visio.Document OpenStencilReadOnly(
    Visio.Application app, string nameOrPath)
{
    const short visOpenRO     = 2;
    const short visOpenHidden = 64;
    return app.Documents.OpenEx(nameOrPath,
        (short)(visOpenRO | visOpenHidden));
}
```

---

## 8. Pitfalls

1. **Locale fallback is silent.** A bare `BASNET_M.VSSX` may resolve to
   the `1033` copy even when the active LCID is `2052`. Localized text on
   masters will read English. Probe `Application.GetBuiltInStencilFile`
   with the active LCID first when localization matters.
2. **Click-to-Run sandboxing.** Recent Click-to-Run installs ship Visio
   inside a Win32-app sandbox; reading the `Visio Content` folder
   directly from a non-Visio process can return `Access denied`. Going
   through `Application.GetBuiltInStencilFile` always works.
3. **Hidden vs docked.** `visOpenHidden | visOpenRO` mounts a stencil
   silently for COM access; you still need `visOpenDocked` (= 512) to
   show the user-visible side panel.
4. **`Master.NameU` vs `Master.Name`.** Always match by `NameU` when
   driving discovery from code. Localized `Name` strings differ across
   the LCID matrix in section 2.1.
5. **Cloud stencils are versioned.** Azure / AWS / GCP refresh icons
   independent of Visio. Pin to a known release hash or version string
   (`User.IconVersion`) when reproducibility matters.
6. **`MyShapesPath` is localized.** On a German Windows the default is
   `%USERPROFILE%\Dokumente\Meine Shapes\`. Always read
   `Application.MyShapesPath` rather than concatenating literals.
7. **Office bitness mismatch.** A 32-bit Visio can only be driven by a
   32-bit COM client. visio-master probes `HKLM\SOFTWARE\Microsoft\Office\
   ClickToRun\Configuration\Platform` to detect bitness before launching
   Python / .NET clients.

---

## 9. Cross-references

- `research/04-shapes-masters-stencils.md` - master / stencil object model,
  `Master.NameU`, `Document.Masters`, `OpenEx` flags.
- `research/12-builtin-templates-catalog.md` - exhaustive template list
  with the stencils each one pre-docks; `Documents.AddEx` patterns.
- `research/15-network-cloud-family.md` - Azure / AWS / GCP / Cisco
  families, rack `User.RUSize` math, deprecation history.

---

## 10. Sources

- Microsoft Learn, *Application.GetBuiltInStencilFile*: <https://learn.microsoft.com/en-us/office/vba/api/visio.application.getbuiltinstencilfile>
- Microsoft Learn, *VisBuiltInStencilTypes*: <https://learn.microsoft.com/en-us/office/vba/api/visio.visbuiltinstenciltypes>
- Microsoft Learn, *VisMeasurementSystem*: <https://learn.microsoft.com/en-us/office/vba/api/visio.vismeasurementsystem>
- Microsoft Learn, *Application.TemplatePaths*: <https://learn.microsoft.com/en-us/office/vba/api/visio.application.templatepaths>
- Microsoft Learn, *Application.MyShapesPath*: <https://learn.microsoft.com/en-us/office/vba/api/visio.application.myshapespath>
- Microsoft Learn, *Documents.OpenEx*: <https://learn.microsoft.com/en-us/office/vba/api/visio.documents.openex>
- Microsoft Learn, *Visio file formats / VSSX OPC*: <https://learn.microsoft.com/en-us/office/client-developer/visio/introduction-to-the-visio-file-format-vsdx>
- Microsoft Learn, *Azure architecture icons*: <https://learn.microsoft.com/en-us/azure/architecture/icons/>
- AWS Architecture Icons: <https://aws.amazon.com/architecture/icons/>
- Google Cloud icons for architecture diagrams: <https://cloud.google.com/icons>
- Cisco Network Topology Icons: <https://www.cisco.com/c/en/us/about/brand-center/network-topology-icons.html>
