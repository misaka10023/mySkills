# diagram-types — Catalog of Supported Visio Diagram Types

> Runtime reference for the visio-master builder. Every entry pins a stable
> `id`, the locale-invariant template short name (`Documents.AddEx`
> argument), the docked stencil files (`Document.OpenEx` arguments),
> the canonical paper / drawing-scale defaults, the layout algorithm
> Visio's `Page.PageSheet.RouteStyle` / `PlaceStyle` cells default to,
> the theme variant the template loads, the `Document.Validation.RuleSets`
> entry (when present), and a one-line semantic description. Mirror the
> ppt-master `charts_index.json` shape: one row per diagram, parameters
> in tables, code-grade naming throughout.

---

## 0. Schema

Each diagram entry exposes the following keys. Builders should treat them
as read-only constants; they map directly to the Visio object model.

| Key                    | Type     | Source surface                                                                  |
|------------------------|----------|---------------------------------------------------------------------------------|
| `id`                   | string   | builder-local kebab-case identifier; stable across releases                     |
| `display_name`         | string   | en-US label shown in Visio's File → New gallery                                 |
| `template`             | string   | `_M.VSTX` / `_U.VSTX` short name resolved via `Application.TemplatePaths`       |
| `workspace_id`         | string   | `Document.Template` / workspace XML tag (`Microsoft.Visio.<Family>Template`)    |
| `built_in_stencil_enum`| int      | `VisBuiltInStencilTypes` constant for `Application.GetBuiltInStencilFile`       |
| `primary_stencils`     | string[] | docked `_M.VSSX` / `_U.VSSX` files the template auto-loads                      |
| `canvas`               | object   | `{paper, orientation, scale, units}` baked into `Page.PageSheet`                |
| `route_style`          | int      | `Page.PageSheet.RouteStyle` default (`VisCellVals` enum)                        |
| `place_style`          | int      | `Page.PageSheet.PlaceStyle` default                                             |
| `theme`                | object   | `{base, variant}` consumed by `Document.SetTheme` / `SetThemeVariant`           |
| `validation_rule_set`  | string   | `Document.Validation.RuleSets.ItemU(...)` name, or `null`                       |
| `key_masters`          | string[] | top-of-mind `Master.NameU` identifiers used by codegen factories                |
| `key_user_cells`       | string[] | polymorphism / data cells (`User.<…>` / `Prop.<…>`) the builder must populate  |
| `add_ons`              | string[] | `Application.Addons.ItemU(...)` names that fire on `EventDrop` / `EventXFMod`   |
| `description`          | string   | one-line semantic description                                                    |

`canvas.paper` values: `A0=841×1189 mm`, `A1=594×841 mm`, `A2=420×594 mm`,
`A3=297×420 mm`, `A4=210×297 mm`, `Letter=8.5×11 in`, `Tabloid=11×17 in`,
`ANSI B=11×17 in`, `ANSI C=17×22 in`, `ANSI D=22×34 in`,
`ANSI E=34×44 in`. `canvas.units`: `mm` / `in` / `ft`.

`route_style` integer constants from `VisCellVals`:

| Value | Constant                       | Meaning                                  |
|-------|--------------------------------|------------------------------------------|
| `0`   | `visLORouteRightAngle`         | orthogonal, no auto-route                |
| `1`   | `visLORouteStraight`           | direct line                              |
| `2`   | `visLORouteCenterToCenter`     | centre-of-shape to centre-of-shape       |
| `3`   | `visLORouteNetwork`            | network routing                          |
| `4`   | `visLORouteFlowchartNS`        | flowchart, north-to-south                |
| `5`   | `visLORouteFlowchartSN`        | flowchart, south-to-north                |
| `6`   | `visLORouteFlowchartWE`        | flowchart, west-to-east                  |
| `7`   | `visLORouteFlowchartEW`        | flowchart, east-to-west                  |
| `8`   | `visLORouteRadial` (Mind Map)  | radial / tree                            |
| `9`   | `visLORouteOrgNS`              | org chart top-down                       |
| `10`  | `visLORouteOrgSN`              | org chart bottom-up                      |

`place_style` integer constants:

| Value | Constant                | Meaning                          |
|-------|-------------------------|----------------------------------|
| `0`   | `visPLOPlaceDefault`    | inherit                           |
| `1`   | `visPLOPlaceCompactDR`  | compact down-then-right          |
| `2`   | `visPLOPlaceCompactRD`  | compact right-then-down          |
| `3`   | `visPLOPlaceTopToBottom`| top-to-bottom hierarchic         |
| `4`   | `visPLOPlaceLeftToRight`| left-to-right hierarchic         |
| `5`   | `visPLOPlaceCircular`   | radial cluster                   |

---

## 1. Master Index

Quick lookup — id → family → template → built-in enum → validation set.

| id                          | family       | display name                  | template       | built-in enum                                  | validation rule set       |
|-----------------------------|--------------|-------------------------------|----------------|------------------------------------------------|---------------------------|
| `basic-flowchart`           | flowchart    | Basic Flowchart               | `BASFLO_M`     | `visBuiltInStencilFlowchart=0`                 | `Flowchart`               |
| `cross-functional-flowchart`| flowchart    | Cross-Functional Flowchart    | `CROSSFUNC_M`  | `visBuiltInStencilCrossFunctionalFlowchart=1`  | `Cross-Functional Flowchart`|
| `workflow-diagram`          | flowchart    | Workflow Diagram              | `WORKFL_M`     | `null`                                         | `null`                    |
| `bpmn-2-0`                  | flowchart    | BPMN 2.0 Diagram              | `BPMN_M`       | `visBuiltInStencilBPMN=26`                     | `BPMN 2.0 Diagram`        |
| `epc`                       | flowchart    | Event-driven Process Chain    | `EPC_M`        | `null`                                         | `null`                    |
| `audit-diagram`             | flowchart    | Audit Diagram                 | `AUDIT_M`      | `null`                                         | `null`                    |
| `brainstorming`             | brainstorm   | Brainstorming                 | `BRSTRM_M`     | `visBuiltInStencilBrainstorming=14`            | `null`                    |
| `mind-map`                  | brainstorm   | Mind Map                      | `MINDMAP_M`    | `null` (2019+)                                 | `null`                    |
| `org-chart`                 | org          | Org Chart                     | `ORGCH_M`      | `visBuiltInStencilOrgChart=11`                 | `null`                    |
| `basic-network`             | network      | Basic Network Diagram         | `NETBAS_M`     | `visBuiltInStencilBasicNetwork=70`             | `null`                    |
| `detailed-network`          | network      | Detailed Network Diagram      | `NETDET_M`     | `null` (Pro / Plan 2)                          | `null`                    |
| `rack-diagram`              | network      | Rack Diagram                  | `RACK_M`       | `visBuiltInStencilRack=42`                     | `null`                    |
| `active-directory`          | network      | Active Directory Diagram      | `ACTDIR_M`     | `null`                                         | `null`                    |
| `aws-architecture`          | network/cloud| AWS Architecture Diagram      | `AWS_M`        | `null` (third-party `.vssx`)                   | `null`                    |
| `azure-architecture`        | network/cloud| Azure Architecture Diagram    | `AZURE_M`      | `null` (download from MS Symbol Set)           | `null`                    |
| `gcp-architecture`          | network/cloud| GCP Architecture Diagram      | `null`         | `null` (community `.vssx`)                     | `null`                    |
| `cisco-network`             | network/cloud| Cisco Network Diagram         | `null`         | `null` (Cisco distribution)                    | `null`                    |
| `uml-class`                 | software     | UML Class                     | `UMLCLS_M`     | `visBuiltInStencilUMLClass=7`                  | `null` (no model engine)  |
| `uml-sequence`              | software     | UML Sequence                  | `UMLSEQ_M`     | `visBuiltInStencilUMLSequence=8`               | `null`                    |
| `uml-activity`              | software     | UML Activity                  | `UMLACT_M`     | `visBuiltInStencilUMLActivity=9`               | `null`                    |
| `uml-use-case`              | software     | UML Use Case                  | `UMLUSE_M`     | `visBuiltInStencilUMLUseCase=10`               | `null`                    |
| `uml-state-machine`         | software     | UML State Machine             | `UMLSM_M`      | `visBuiltInStencilUMLStatechart=12`            | `null`                    |
| `uml-component`             | software     | UML Component                 | `UMLCMP_M`     | `visBuiltInStencilUMLComponent=13`             | `null`                    |
| `uml-deployment`            | software     | UML Deployment                | `UMLDEP_M`     | `visBuiltInStencilUMLDeployment=14`            | `null`                    |
| `uml-object`                | software     | UML Object                    | `UMLOBJ_M`     | `null`                                         | `null`                    |
| `uml-communication`         | software     | UML Communication             | `UMLCOMM_M`    | `null`                                         | `null`                    |
| `uml-package`               | software     | UML Package                   | `UMLPKG_M`     | `null`                                         | `null`                    |
| `uml-profile`               | software     | UML Profile                   | `UMLPROF_M`    | `null`                                         | `null`                    |
| `dfd`                       | software     | Data Flow Diagram             | `DATAFL_M`     | `null`                                         | `null`                    |
| `erd`                       | software/db  | Database Model (Crow's Foot)  | `DBMOD_M`      | `null` (template removed 2016; stencil ships)  | `null`                    |
| `basic-electrical`          | engineering  | Basic Electrical              | `BAELEC_M`     | `visBuiltInStencilBasicElectrical=70`          | `null`                    |
| `logic-gate`                | engineering  | Logic Gate Diagram            | `LOGIC_M`      | `visBuiltInStencilLogicGate=80`                | `null`                    |
| `pfd`                       | engineering  | Process Flow Diagram          | `PFD_M`        | `null`                                         | `null`                    |
| `pid`                       | engineering  | Piping & Instrumentation      | `PID_M`        | `null`                                         | `Piping and Instrumentation` |
| `hvac`                      | engineering  | HVAC Plan                     | `HVAC_M`       | `null`                                         | `null`                    |
| `plumbing`                  | engineering  | Plumbing & Piping Plan        | `PLMBPL_M`     | `null`                                         | `null`                    |
| `site-plan`                 | floorplan    | Site Plan                     | `SITPLN_M`     | `null`                                         | `null`                    |
| `floor-plan`                | floorplan    | Floor Plan                    | `FLRPLN_M`     | `null`                                         | `null`                    |
| `home-plan`                 | floorplan    | Home Plan                     | `HOMEPLN_M`    | `null`                                         | `null`                    |
| `office-layout`             | floorplan    | Office Layout                 | `OFFLAY_M`     | `null`                                         | `null`                    |
| `reflected-ceiling-plan`    | floorplan    | Reflected Ceiling Plan        | `RFLPLN_M`     | `null`                                         | `null`                    |
| `electrical-telecom-plan`   | floorplan    | Electrical & Telecom Plan     | `ELECPL_M`     | `null`                                         | `null`                    |
| `plant-layout`              | floorplan    | Plant Layout                  | `PLAYOUT_M`    | `null`                                         | `null`                    |
| `security-access-plan`      | floorplan    | Security & Access Plan        | `SECPLN_M`     | `null`                                         | `null`                    |
| `calendar`                  | schedule     | Calendar                      | `CALEND_M`     | `visBuiltInStencilCalendar=27`                 | `null`                    |
| `gantt-chart`               | schedule     | Gantt Chart                   | `GANTT_M`      | `visBuiltInStencilGantt=15`                    | `null`                    |
| `pert-chart`                | schedule     | PERT Chart                    | `PERT_M`       | `visBuiltInStencilPERT=70`                     | `null`                    |
| `timeline`                  | schedule     | Timeline                      | `TIMELINE_M`   | `visBuiltInStencilTimeline=28`                 | `null`                    |
| `swot`                      | business     | SWOT Analysis                 | `SWOT_M`       | `null`                                         | `null`                    |
| `balanced-scorecard`        | business     | Balanced Scorecard            | `BSC_M`        | `null`                                         | `null`                    |
| `strategy-map`              | business     | Strategy Map                  | `STRATEGY_M`   | `null`                                         | `null`                    |
| `marketing-charts`          | business     | Marketing Charts & Diagrams   | `MARKETC_M`    | `visBuiltInStencilMarketing=66`                | `null`                    |
| `itil-diagram`              | business     | ITIL Diagram                  | `ITIL_M`       | `null`                                         | `null`                    |
| `six-sigma`                 | business     | Six Sigma Diagram             | `SIXSIG_M`     | `null`                                         | `null`                    |
| `cause-effect-fishbone`     | business     | Cause & Effect / Fishbone     | `CAUSEEFF_M`   | `null`                                         | `null`                    |
| `value-stream-map`          | business     | Lean / Value Stream Map       | `LEAN_M`       | `visBuiltInStencilLeanShapes=98`               | `null`                    |
| `tqm`                       | business     | Total Quality Management      | `TQM_M`        | `visBuiltInStencilTQM=68`                      | `null`                    |
| `fmea-grid`                 | business     | FMEA Grid                     | `null` (Six Sigma sub-template) | `null`                        | `null`                    |
| `sipoc`                     | business     | SIPOC                         | `null` (Six Sigma sub-template) | `null`                        | `null`                    |
| `functional-block-diagram`  | business     | Functional Block Diagram      | `BLOCK_M`      | `null`                                         | `null`                    |

---

## 2. Flowchart Family

### 2.1 `basic-flowchart` — Basic Flowchart

| field | value |
|-------|-------|
| `id` | `basic-flowchart` |
| `display_name` | Basic Flowchart |
| `template` | `BASFLO_M.VSTX` / `BASFLO_U.VSTX` |
| `workspace_id` | `Microsoft.Visio.BasicFlowchartTemplate` |
| `built_in_stencil_enum` | `visBuiltInStencilFlowchart=0` |
| `primary_stencils` | `BASFLO_M.VSSX` (Basic Flowchart Shapes), `CONNEC_M.VSSX` (Connectors) |
| `canvas` | `{paper:"A4", orientation:"portrait", scale:"1:1", units:"mm"}` (US: Letter) |
| `route_style` | `4` (`visLORouteFlowchartNS`) |
| `place_style` | `1` (`visPLOPlaceCompactDR`) |
| `theme` | `{base:"Office", variant:1}` |
| `validation_rule_set` | `Flowchart` |
| `key_masters` | `Process`, `Decision`, `Document`, `Data`, `Terminator`, `On-page reference`, `Off-page reference`, `Database`, `Direct data`, `Stored data`, `Internal storage`, `Sequential data`, `Manual operation`, `Manual input`, `Preparation`, `Predefined process`, `Annotation`, `Dynamic connector` |
| `key_user_cells` | `User.visAutoConnectDecisionLabels` (Decision), `User.msvShapeCategories="Flowchart"`, page-level `LineJumpStyle`, `LineJumpCode` |
| `add_ons` | `Layout` |
| `description` | ANSI/ISO 5807 procedure diagram with seventeen 2-D masters and a single Dynamic connector. |

### 2.2 `cross-functional-flowchart` — Cross-Functional Flowchart (Swimlane)

| field | value |
|-------|-------|
| `id` | `cross-functional-flowchart` |
| `display_name` | Cross-Functional Flowchart |
| `template` | `CROSSFUNC_M.VSTX` / `CROSSFUNC_U.VSTX` |
| `workspace_id` | `Microsoft.Visio.CrossFunctionalFlowchartTemplate` |
| `built_in_stencil_enum` | `visBuiltInStencilCrossFunctionalFlowchart=1` |
| `primary_stencils` | `CROSSFUNC_M.VSSX` (Cross-Functional Flowchart Shapes), `BASFLO_M.VSSX`, `CONNEC_M.VSSX` |
| `canvas` | `{paper:"A3", orientation:"landscape", scale:"1:1", units:"mm"}` (US: Tabloid) |
| `route_style` | `4` |
| `place_style` | `4` (`visPLOPlaceLeftToRight`) |
| `theme` | `{base:"Office", variant:1}` |
| `validation_rule_set` | `Cross-Functional Flowchart` |
| `key_masters` | `Swimlane list`, `Swimlane`, `Phase`, `Separator`, `Title bar` (+ all `BASFLO_M` masters) |
| `key_user_cells` | `User.msvStructureType="List"` (list container), `User.visSDContainerCategories="Cross-functional flowchart"`, `User.msvSDListAlignment` (`0=horizontal`, `1=vertical`), `User.msvSDListSpacing`, `Prop.Function` (lane label), `Prop.Phase` (phase label) |
| `add_ons` | `Layout` (swimlane list reflows via `ContainerProperties.AddSwimlane(idx)`) |
| `description` | Process responsibility map; lanes added via `Shape.ContainerProperties.AddSwimlane`/`AddPhase`. |

### 2.3 `workflow-diagram` — Workflow Diagram

| field | value |
|-------|-------|
| `id` | `workflow-diagram` |
| `display_name` | Workflow Diagram |
| `template` | `WORKFL_M.VSTX` / `WORKFL_U.VSTX` |
| `workspace_id` | `Microsoft.Visio.WorkflowTemplate` |
| `built_in_stencil_enum` | `null` |
| `primary_stencils` | `WORKOB_M.VSSX` (Workflow Objects), `WORKST_M.VSSX` (Workflow Steps), `BASFLO_M.VSSX`, `CONNEC_M.VSSX` |
| `canvas` | `{paper:"A4", orientation:"landscape", scale:"1:1", units:"mm"}` |
| `route_style` | `4` |
| `place_style` | `1` |
| `theme` | `{base:"Office", variant:2}` |
| `validation_rule_set` | `null` |
| `key_masters` | `Server`, `Database`, `Document`, `Workflow phases`, `Generic Process`, `Generic Decision`, `Person`, `Sound`, `Tablet`, `Phone`, `Email`, `Form` |
| `key_user_cells` | `User.msvShapeCategories="Workflow"`, `Prop.Owner`, `Prop.SLA` |
| `add_ons` | `Layout` |
| `description` | Mixed-actor workflow storyboard for SharePoint Designer / Power Automate flows. |

### 2.4 `bpmn-2-0` — BPMN 2.0 Diagram

| field | value |
|-------|-------|
| `id` | `bpmn-2-0` |
| `display_name` | BPMN 2.0 Diagram |
| `template` | `BPMN_M.VSTX` / `BPMN_U.VSTX` |
| `workspace_id` | `Microsoft.Visio.BPMNTemplate` |
| `built_in_stencil_enum` | `visBuiltInStencilBPMN=26` |
| `primary_stencils` | `BPMN_M.VSSX` (BPMN Basic Shapes), `BPMN2_M.VSSX` (BPMN Conversation Shapes — 2016+) |
| `canvas` | `{paper:"A3", orientation:"landscape", scale:"1:1", units:"mm"}` (US: Tabloid) |
| `route_style` | `4` |
| `place_style` | `4` |
| `theme` | `{base:"Office", variant:1}` |
| `validation_rule_set` | `BPMN 2.0 Diagram` (rules: `MessageFlowMustCrossPools`, `SequenceFlowsCannotCrossPools`, `EventBoundaryMustAttach`, `ExclusiveGatewayHasOneDefault`, `EndEventNoOutgoing`, `StartEventNoIncoming`, `LaneMustBeInPool`, `MessageFlowEndpointMustBeAllowed`) |
| `key_masters` | `Activity`, `Event`, `Gateway`, `Data Object`, `Data Store`, `Pool`, `Lane`, `Sequence flow`, `Message flow`, `Association`, `Default flow`, `Conditional flow`, `Group`, `Text Annotation` |
| `key_user_cells` | `User.BpmnTaskType` (`0..7`), `User.BpmnActivityType` (`0..4`), `User.BpmnIsLoop` (`0..3`), `User.BpmnIsCompensation`, `User.BpmnIsAdHoc`, `User.BpmnIsCallActivity`, `User.BpmnEventType` (`0..3`: Start/Intermediate/End/Boundary), `User.BpmnEventTrigger` (`0..14`: None/Message/Timer/Conditional/Signal/Multiple/ParallelMultiple/Error/Escalation/Cancel/Compensation/Link/Terminate), `User.BpmnEventIsThrowing`, `User.BpmnEventIsInterrupting`, `User.BpmnGatewayType` (`0..6`: XOR/OR/AND/Complex/EventBased/ExclusiveEventBasedInstantiate/ParallelEventBasedInstantiate), `User.BpmnGatewayDirection` (`0..3`), `User.BpmnIsBlackBox` (Pool), `User.BpmnParticipantMultiplicity`, `User.BpmnIsCollection` (Data Object), `User.BpmnIsInput`, `User.BpmnIsOutput`, `User.visBpmnVersion=1` |
| `add_ons` | (none — semantics computed in `Geometry.NoShow` formulas off the User cells) |
| `description` | OMG BPMN 2.0.2 process model with polymorphic Activity/Event/Gateway masters and pool-aware flow validation. |

### 2.5 `epc` — Event-driven Process Chain

| field | value |
|-------|-------|
| `id` | `epc` |
| `template` | `EPC_M.VSTX` / `EPC_U.VSTX` |
| `primary_stencils` | `EPC_M.VSSX`, `BASFLO_M.VSSX`, `CONNEC_M.VSSX` |
| `canvas` | `{paper:"A3", orientation:"landscape", scale:"1:1", units:"mm"}` |
| `route_style` | `4` |
| `key_masters` | `Event` (hexagon), `Function` (rounded rectangle), `Organization unit`, `Information / material`, `Process path`, `XOR`, `OR`, `AND`, `Logical operator` |
| `description` | SAP / ARIS-style event-driven process chain for ERP procedure documentation. |

### 2.6 `audit-diagram` — Audit Diagram

| field | value |
|-------|-------|
| `id` | `audit-diagram` |
| `template` | `AUDIT_M.VSTX` / `AUDIT_U.VSTX` |
| `primary_stencils` | `AUDIT_M.VSSX`, `BASFLO_M.VSSX`, `CONNEC_M.VSSX` |
| `canvas` | `{paper:"A3", orientation:"landscape", scale:"1:1", units:"mm"}` |
| `route_style` | `4` |
| `key_masters` | `Process`, `Decision`, `Document`, `Tape`, `Manual operation`, `Data store`, `Begin/End`, `Off-page reference`, `Auditor's note` |
| `description` | Internal-audit / financial-control flowchart variant of Basic Flowchart. |

---

## 3. Brainstorming / Mind Map Family

### 3.1 `brainstorming` — Brainstorming Diagram

| field | value |
|-------|-------|
| `id` | `brainstorming` |
| `display_name` | Brainstorming |
| `template` | `BRSTRM_M.VSTX` / `BRSTRM_U.VSTX` |
| `workspace_id` | `Microsoft.Visio.BrainstormingTemplate` |
| `built_in_stencil_enum` | `visBuiltInStencilBrainstorming=14` |
| `primary_stencils` | `BRSTRM_M.VSSX`, `LEGEND_M.VSSX` (optional) |
| `canvas` | `{paper:"A3", orientation:"landscape", scale:"1:1", units:"mm"}` |
| `route_style` | `8` (`visLORouteRadial`) |
| `place_style` | `5` (`visPLOPlaceCircular`) |
| `theme` | `{base:"Office", variant:3}` |
| `key_masters` | `Main topic`, `Topic`, `Subtopic`, `Multiple topic`, `Legend`, `Dynamic connector` |
| `key_user_cells` | `User.BrainstormParent` (Master.ID of parent), `User.BrainstormLevel` (`0=main`) |
| `add_ons` | `Microsoft.Office.Visio.Brainstorming.Outliner` (Outline window), legacy `BRSTRM.EXE` |
| `description` | Mind-map / ideation tree managed by the Outline Window dock. |

### 3.2 `mind-map` — Mind Map (2019+)

| field | value |
|-------|-------|
| `id` | `mind-map` |
| `template` | `MINDMAP_M.VSTX` (falls back to `BRSTRM_*.VSTX` on older SKUs) |
| `primary_stencils` | `MINDMAP_M.VSSX` |
| `canvas` | `{paper:"A3", orientation:"landscape", scale:"1:1", units:"mm"}` |
| `route_style` | `8` |
| `place_style` | `5` |
| `theme` | `{base:"Office", variant:3}` |
| `key_masters` | `Central idea`, `Branch`, `Sub-branch`, `Cloud`, `Note`, `Image holder` |
| `key_user_cells` | page-level `Routing.Style=visLORouteRadial`, `AvenueSizeX=0.25 in`, `AvenueSizeY=0.25 in` |
| `description` | Discovery-style mind map with central-idea-and-branch geometry. |

---

## 4. Org Chart Family

### 4.1 `org-chart` — Organization Chart

| field | value |
|-------|-------|
| `id` | `org-chart` |
| `display_name` | Org Chart |
| `template` | `ORGCH_M.VSTX` / `ORGCH_U.VSTX` |
| `workspace_id` | `Microsoft.Visio.OrgChartTemplate` |
| `built_in_stencil_enum` | `visBuiltInStencilOrgChart=11` |
| `primary_stencils` | `ORGCH_M.VSSX`, `ORGCHM_M.VSSX` (Multiple Shapes — Pro), `WORKFL_M.VSSX` (optional) |
| `canvas` | `{paper:"A4", orientation:"landscape", scale:"1:1", units:"mm"}` (auto-fit via `OrgChartAutoSize=TRUE`) |
| `route_style` | `9` (`visLORouteOrgNS`) |
| `place_style` | `3` (`visPLOPlaceTopToBottom`) |
| `theme` | `{base:"Office", variant:1}` |
| `key_masters` | `Executive`, `Manager`, `Position`, `Consultant`, `Vacancy`, `Assistant`, `Staff`, `Team Frame`, `Three positions`, `Multiple shapes`, `Title/Date` |
| `key_user_cells` | `User.visOrgChartShape=TRUE`, `User.OrgChartLevel`, `Prop.Department`, `Prop.Title`, `Prop.Telephone`, `Prop.Email`, `Prop.MasterShape` |
| `add_ons` | `OrgC` (`Application.Addons.ItemU("OrgC")`) — Org Chart Wizard, drives Excel/CSV/AD/Exchange import |
| `description` | Hierarchic reporting chart sourced from HRIS, AD, or Exchange via the Org Chart Wizard. |

---

## 5. Network / Cloud Family

### 5.1 `basic-network` — Basic Network Diagram

| field | value |
|-------|-------|
| `id` | `basic-network` |
| `display_name` | Basic Network Diagram |
| `template` | `NETBAS_M.VSTX` / `NETBAS_U.VSTX` |
| `workspace_id` | `Microsoft.Visio.BasicNetworkTemplate` |
| `built_in_stencil_enum` | `visBuiltInStencilBasicNetwork=70` |
| `primary_stencils` | `BASNET_M.VSSX` (Network and Peripherals), `COMPC_M.VSSX` (Computers and Monitors) |
| `canvas` | `{paper:"A3", orientation:"landscape", scale:"1:1", units:"mm"}` (US: Tabloid) |
| `route_style` | `3` (`visLORouteNetwork`) |
| `place_style` | `0` |
| `theme` | `{base:"Office", variant:2}` |
| `key_masters` | `Computer`, `Server`, `Router`, `Switch`, `Firewall`, `Hub`, `Workstation`, `PC`, `Laptop computer`, `Mainframe`, `Printer`, `Communication link`, `Ethernet`, `Cloud` |
| `key_user_cells` | `Prop.IPAddress`, `Prop.SubnetMask`, `Prop.MACAddress`, `Prop.NumberOfPorts`, `Prop.AssetNumber`, `Prop.SerialNumber`, `Prop.Manufacturer`, `Prop.Location`, `Prop.NetworkName` |
| `add_ons` | `Layout` |
| `description` | LAN/WAN topology overview using the seven canonical network masters plus the bus-style `Ethernet` connector. |

### 5.2 `detailed-network` — Detailed Network Diagram

| field | value |
|-------|-------|
| `id` | `detailed-network` |
| `template` | `NETDET_M.VSTX` / `NETDET_U.VSTX` |
| `primary_stencils` | `BASNET_M.VSSX`, `COMPC_M.VSSX`, `DETNET_M.VSSX` (Detailed peripherals), `NETSRV_M.VSSX` (Servers), `RACKMT_M.VSSX` (Rack-mounted partial) |
| `canvas` | `{paper:"A1", orientation:"landscape", scale:"1:1", units:"mm"}` (US: ANSI D) |
| `route_style` | `3` |
| `key_masters` | `Storage area network`, `Tape array`, `RAID`, `SAN switch`, `Load balancer`, `IDS`, `VPN concentrator`, `Proxy server`, `Telnet`, `Mainframe`, `Cloud`, `File server`, `Mail server`, `Database server`, `Web server`, `Directory server` |
| `key_user_cells` | `User.SubLabel` (rack U-hint), `User.visEquipNumberable=TRUE`, `User.visRackUnitSize`, `User.AntiScale=1` |
| `description` | As-built infrastructure diagram with rack-style front-elevation iconography. |

### 5.3 `rack-diagram` — Rack Diagram

| field | value |
|-------|-------|
| `id` | `rack-diagram` |
| `template` | `RACK_M.VSTX` / `RACK_U.VSTX` |
| `workspace_id` | `Microsoft.Visio.RackDiagramTemplate` |
| `built_in_stencil_enum` | `visBuiltInStencilRack=42` |
| `primary_stencils` | `RACK_M.VSSX`, `RACKACC_M.VSSX` (accessories), `FREES_M.VSSX` (free-standing), `CABLES_M.VSSX` (cables) |
| `canvas` | `{paper:"A3", orientation:"portrait", scale:"1 in : 1 ft", units:"in"}` (US: ANSI B) |
| `route_style` | `0` |
| `place_style` | `3` |
| `theme` | `{base:"Office", variant:2}` |
| `key_masters` | `Rack frame`, `1 U server` … `12 U server`, `1 U patch panel`, `2 U patch panel`, `4 U patch panel`, `1 U switch`, `2 U switch`, `1 U router`, `2 U router`, `1 U firewall`, `2 U firewall`, `1 U KVM switch`, `2 U KVM switch`, `2 U UPS`, `3 U UPS`, `5 U UPS`, `4 U RAID array`, `5 U Tape drive`, `Blank rack unit`, `Numbering` |
| `key_user_cells` | `User.RUSize` (frame total U), `User.RUHeight=1.75 in`, `User.RackNumbering` (`1=bottom-up`, `2=top-down`), `User.EquipmentNumbering`, `User.RUStart` (computed by snap), `User.visEquipNumberable`, `User.msvSDContainerCategories="Rack mounted equipment"`, `Prop.AssetTag`, `Prop.SerialNumber`, `Prop.RackPosition` |
| `add_ons` | `Visio.NetworkShapes.EquipmentNumbering` (auto-number equipment) |
| `description` | Data-center rack elevation; equipment auto-snaps to U slots via list-container membership and `User.RUSize`-driven height math. |

### 5.4 `active-directory` — Active Directory Diagram

| field | value |
|-------|-------|
| `id` | `active-directory` |
| `template` | `ACTDIR_M.VSTX` (legacy; stencil ships in 2016+ Pro/Plan 2) |
| `primary_stencils` | `ACTDIR_M.VSSX` |
| `canvas` | `{paper:"A3", orientation:"landscape", scale:"1:1", units:"mm"}` |
| `route_style` | `9` |
| `key_masters` | `Site`, `Site link`, `Site link bridge`, `Subnet`, `Domain`, `Domain controller`, `Global catalog`, `Organizational unit`, `Container`, `User`, `Group`, `Computer`, `Printer`, `Shared folder`, `Contact`, `Trust`, `Replication`, `FSMO role holder` |
| `key_user_cells` | `Prop.LDAPName`, `Prop.SAMAccountName`, `Prop.UserPrincipalName`, `Prop.GUID`, `Prop.SID`, `Prop.Domain`, `Prop.Site`, `Prop.OS`, `Prop.OSVersion`, `Prop.LastLogon`, `Prop.PasswordLastSet` |
| `description` | Forest / domain / OU topology with LDAP-DN attributes; legacy auto-discovery wizard removed in 2013. |

### 5.5 `aws-architecture` — AWS Architecture Diagram

| field | value |
|-------|-------|
| `id` | `aws-architecture` |
| `template` | `AWS_M.VSTX` (Visio Plan 2; community-redistributed stencil after 2022) |
| `primary_stencils` | `AWS17_*.VSSX` (Compute, Storage, Database, Network, Security, AI/ML, etc.); 2024 re:Invent icon pack |
| `canvas` | `{paper:"A3", orientation:"landscape", scale:"1:1", units:"mm"}` |
| `route_style` | `0` |
| `key_masters` | `EC2`, `S3`, `RDS`, `Lambda`, `VPC`, `Subnet`, `Internet Gateway`, `Route table`, `Region` (container), `Availability Zone` (container), `IAM`, `CloudFront`, `Route 53`, `DynamoDB`, `Aurora`, `EKS`, `ECS`, `Fargate`, `SQS`, `SNS`, `API Gateway`, `Step Functions` |
| `key_user_cells` | `User.AwsService`, `User.AwsCategory`, `User.IconVersion`, `Prop.AwsResourceArn`, `Prop.AwsRegion`, `Prop.AwsAccount`, `User.msvSDContainerCategories="AWS Region"` / `"AWS AZ"` |
| `description` | AWS solution architecture with Region / AZ list containers and service icons. |

### 5.6 `azure-architecture` — Azure Architecture Diagram

| field | value |
|-------|-------|
| `id` | `azure-architecture` |
| `template` | `AZURE_M.VSTX` (Visio Plan 2; quarterly icon refresh) |
| `primary_stencils` | `Azure_Public_Service_Icons_V<n>.vssx` (Compute, Networking, Storage, Database, AI+ML, IoT, Security, Identity, Containers, DevOps, General, Web, Migrate, Management, Analytics, Integration) |
| `canvas` | `{paper:"A3", orientation:"landscape", scale:"1:1", units:"mm"}` |
| `route_style` | `0` |
| `key_masters` | `Virtual machine`, `App Service`, `Function`, `AKS`, `Container Instance`, `SQL Database`, `Cosmos DB`, `Storage account`, `Blob storage`, `Virtual network`, `Subnet`, `Application Gateway`, `Front Door`, `Key Vault`, `Active Directory`, `Resource group` (container), `Subscription` (container), `Region` |
| `key_user_cells` | `User.AzureService`, `User.AzureCategory`, `User.AzureSku`, `User.IconVersion`, `Prop.ResourceId`, `Prop.SubscriptionId`, `Prop.ResourceGroup`, `Prop.Region`, `Prop.Sku` |
| `description` | Azure landing-zone diagram with ARM-aware Subscription/RG/Region containers. |

### 5.7 `gcp-architecture` — GCP Architecture Diagram

| field | value |
|-------|-------|
| `id` | `gcp-architecture` |
| `template` | (no MS-shipped template; community `gcp-icons-for-visio.vssx` or Lucidchart export) |
| `primary_stencils` | community `.vssx` packs |
| `canvas` | `{paper:"A3", orientation:"landscape", scale:"1:1", units:"mm"}` |
| `key_masters` | `Compute Engine`, `App Engine`, `Cloud Run`, `Cloud Functions`, `GKE`, `Cloud Storage`, `Cloud SQL`, `Spanner`, `BigQuery`, `Pub/Sub`, `Vertex AI`, `Cloud Load Balancing`, `VPC`, `IAM`, `Cloud KMS` |
| `key_user_cells` | `User.GcpService`, `User.GcpCategory`, `User.IconVersion`, `Prop.GcpProject`, `Prop.GcpRegion`, `Prop.GcpZone`, `Prop.ResourceId` |
| `description` | Google Cloud architecture using community-distributed icon `.vssx`. |

### 5.8 `cisco-network` — Cisco Network Diagram

| field | value |
|-------|-------|
| `id` | `cisco-network` |
| `template` | (no MS-shipped template; Cisco distribution) |
| `primary_stencils` | `Cisco Routers.vssx`, `Cisco Switches and Hubs.vssx`, `Cisco Wireless.vssx`, `Cisco Security.vssx`, `Cisco UCS and Servers.vssx`, `Cisco WAN.vssx`, `Cisco Buildings and Concepts.vssx`, `Cisco Generic.vssx` |
| `canvas` | `{paper:"A3", orientation:"landscape", scale:"1:1", units:"mm"}` |
| `key_masters` | `Router`, `Cisco ASR 1000`, `Catalyst 9300`, `Nexus 9000`, `ASA 5500`, `Firepower 1000`, `vEdge 100`, `Meraki MR`, `UCS B200 M5` |
| `key_user_cells` | `Prop.CiscoModel`, `Prop.CiscoFamily`, `Prop.CiscoLine`, `Prop.HostName`, `Prop.MgmtIP`, `Prop.IOSVersion`, `Prop.SerialNumber` |
| `description` | Cisco-specific topology using product-code-named masters from the Cisco Network Topology Icons distribution. |

---

## 6. Software Modeling Family (UML 2.5)

> Visio 2016+ ships UML stencils only — no model repository, no reverse
> engineering, no round-tripping. `Prop.Visibility` (`public;protected;
> private;package`), `Prop.IsAbstract`, `Prop.IsStatic` are universal
> across every UML element. Editing a shape's visible text strips the
> formula linkage; always set `Prop.Name`, never `Shape.Text`.

### 6.1 `uml-class` — UML Class

| field | value |
|-------|-------|
| `id` | `uml-class` |
| `template` | `UMLCLS_M.VSTX` |
| `workspace_id` | `Microsoft.Visio.UMLClassTemplate` |
| `built_in_stencil_enum` | `visBuiltInStencilUMLClass=7` |
| `primary_stencils` | `UMLCLS_M.VSSX` |
| `canvas` | `{paper:"A3", orientation:"landscape", scale:"1:1", units:"mm"}` |
| `route_style` | `0` |
| `key_masters` | `Class`, `Abstract class`, `Interface`, `Enumeration`, `Data type`, `Primitive type`, `Signal`, `Package`, `Note`, `Association`, `Directed association`, `Aggregation`, `Composition`, `Generalization`, `Realization`, `Dependency`, `Containment`, `N-ary association` |
| `key_user_cells` | `Prop.Visibility`, `Prop.IsAbstract`, `Prop.IsActive`, `Prop.IsLeaf`, `Prop.Stereotype`, `Prop.Namespace`; member rows: `Prop.IsStatic`, `Prop.IsReadOnly`, `Prop.IsDerived`, `Prop.IsQuery`, `Prop.Type`, `Prop.Multiplicity`, `Prop.DefaultValue`, `Prop.Parameters`, `Prop.ReturnType`; `User.fmtVis` (visibility-glyph rewrite); `User.msvShapeCategories="UML 2.5"` |
| `description` | OOP class model with three list-container compartments (Name / Attributes / Operations); shape-data-driven label rendering. |

### 6.2 `uml-sequence` — UML Sequence

| field | value |
|-------|-------|
| `id` | `uml-sequence` |
| `template` | `UMLSEQ_M.VSTX` |
| `built_in_stencil_enum` | `visBuiltInStencilUMLSequence=8` |
| `primary_stencils` | `UMLSEQ_M.VSSX` |
| `canvas` | `{paper:"A3", orientation:"landscape", scale:"1:1", units:"mm"}` |
| `route_style` | `0` |
| `key_masters` | `Lifeline`, `Actor lifeline`, `Boundary lifeline`, `Control lifeline`, `Entity lifeline`, `Activation`, `Destruction`, `Frame`, `Combined fragment`, `Interaction use`, `State invariant`, `Continuation`, `Gate`, `Message`, `Reply message`, `Asynchronous message`, `Self message`, `Create message`, `Lost message`, `Found message` |
| `key_user_cells` | `Prop.Name`, `Prop.ClassifierName`, `Prop.IsActor`, `User.LifelineLength`, `User.ActivationStart`, `User.ActivationEnd`, `Prop.MessageNumber`, `Prop.Arguments`, `Prop.ReturnValue`, `Prop.Operator` (alt/opt/loop/par/break/ref/seq/strict/neg/assert/critical/ignore/consider), `Prop.Guard`, `Prop.OperandCount`, `Prop.Constraint`, `Prop.FrameKind` |
| `description` | Interaction model with vertical lifelines, list-container Combined fragments, and seven message-arrow styles. |

### 6.3 `uml-activity` — UML Activity

| field | value |
|-------|-------|
| `id` | `uml-activity` |
| `template` | `UMLACT_M.VSTX` |
| `built_in_stencil_enum` | `visBuiltInStencilUMLActivity=9` |
| `primary_stencils` | `UMLACT_M.VSSX` |
| `canvas` | `{paper:"A3", orientation:"landscape", scale:"1:1", units:"mm"}` |
| `route_style` | `4` |
| `key_masters` | `Action`, `Initial node`, `Activity final`, `Flow final`, `Decision`, `Merge`, `Fork`, `Join`, `Object node`, `Send signal`, `Accept event`, `Time event`, `Activity partition` (swimlane), `Expansion region`, `Interruptible region`, `Control flow`, `Object flow`, `Exception handler` |
| `key_user_cells` | `Prop.Name`, `Prop.LocalPrecondition`, `Prop.LocalPostcondition`, `Prop.IsLocallyReentrant`, `Prop.Behavior`; partition reuses `ContainerProperties.AddSwimlane(idx, direction)` |
| `description` | UML activity / control-flow diagram with swimlane partitions and interruptible regions. |

### 6.4 `uml-use-case` — UML Use Case

| field | value |
|-------|-------|
| `id` | `uml-use-case` |
| `template` | `UMLUSE_M.VSTX` |
| `built_in_stencil_enum` | `visBuiltInStencilUMLUseCase=10` |
| `primary_stencils` | `UMLUSE_M.VSSX` |
| `canvas` | `{paper:"A3", orientation:"landscape", scale:"1:1", units:"mm"}` |
| `key_masters` | `Actor`, `Use case`, `Subject` (system boundary container), `Package`, `Association`, `Include` (`«include»`), `Extend` (`«extend»`), `Generalization` |
| `key_user_cells` | `Prop.Name`, `Prop.ExtensionPoint`, `User.msvSDContainerCategories="Use Case Subject"` |
| `description` | Requirements scoping with actors, ellipses, and a subject boundary container. |

### 6.5 `uml-state-machine` — UML State Machine

| field | value |
|-------|-------|
| `id` | `uml-state-machine` |
| `template` | `UMLSM_M.VSTX` |
| `built_in_stencil_enum` | `visBuiltInStencilUMLStatechart=12` |
| `primary_stencils` | `UMLSM_M.VSSX` |
| `canvas` | `{paper:"A3", orientation:"landscape", scale:"1:1", units:"mm"}` |
| `key_masters` | `State`, `Composite state`, `Initial pseudostate`, `Final state`, `Choice`, `Junction`, `Fork`, `Join`, `Shallow history`, `Deep history`, `Entry point`, `Exit point`, `Terminate`, `Region`, `Transition`, `Internal transition`, `Self transition` |
| `key_user_cells` | `Prop.Trigger`, `Prop.Guard`, `Prop.Effect`, `Prop.EntryActivity`, `Prop.ExitActivity`, `Prop.DoActivity`, `Prop.InternalTransitions`; transition `TheText = Prop.Trigger & " [" & Prop.Guard & "] / " & Prop.Effect` |
| `description` | UML state engine with composite states, history pseudostates, and trigger/guard/effect transitions. |

### 6.6 `uml-component` — UML Component

| field | value |
|-------|-------|
| `id` | `uml-component` |
| `template` | `UMLCMP_M.VSTX` |
| `built_in_stencil_enum` | `visBuiltInStencilUMLComponent=13` |
| `primary_stencils` | `UMLCMP_M.VSSX` |
| `canvas` | `{paper:"A3", orientation:"landscape", scale:"1:1", units:"mm"}` |
| `key_masters` | `Component`, `Provided interface` (lollipop), `Required interface` (socket), `Port`, `Assembly connector`, `Delegation connector`, `Artifact`, `Manifestation`, `Dependency`, `Realization` |
| `key_user_cells` | `Prop.Name`, `Prop.IsIndirectlyInstantiated`, `Prop.Stereotype` (`component;subsystem;specification;realization`) |
| `description` | Architectural component contract diagram with provided/required interface ball-and-socket. |

### 6.7 `uml-deployment` — UML Deployment

| field | value |
|-------|-------|
| `id` | `uml-deployment` |
| `template` | `UMLDEP_M.VSTX` |
| `built_in_stencil_enum` | `visBuiltInStencilUMLDeployment=14` |
| `primary_stencils` | `UMLDEP_M.VSSX` |
| `canvas` | `{paper:"A3", orientation:"landscape", scale:"1:1", units:"mm"}` |
| `key_masters` | `Node` (3-D box), `Device`, `Execution environment`, `Artifact`, `Deployment specification`, `Communication path`, `Deployment` (`«deploy»`), `Manifestation` (`«manifest»`), `Dependency` |
| `key_user_cells` | `Prop.Name`, `Prop.Stereotype` |
| `description` | Topology of nodes, devices, and deployed artifacts with `«deploy»`/`«manifest»` connectors. |

### 6.8 Other UML diagrams (`uml-object`, `uml-communication`, `uml-package`, `uml-profile`)

| id | template | primary stencils | key masters |
|----|----------|------------------|-------------|
| `uml-object` | `UMLOBJ_M.VSTX` | `UMLOBJ_M.VSSX` | `Instance specification`, `Slot`, `Link object`, `Composite object`, `Link`, `Dependency` |
| `uml-communication` | `UMLCOMM_M.VSTX` | `UMLCOMM_M.VSSX` | `Lifeline / Object`, `Actor`, `Frame`, `Communication link` (numbered messages `1.`, `1.1`, `2:`) |
| `uml-package` | `UMLPKG_M.VSTX` | `UMLPKG_M.VSSX` | `Package`, `Model`, `Subsystem`, `Containment`, `Dependency («import»)`, `Dependency («access»)`, `Dependency («merge»)` |
| `uml-profile` | `UMLPROF_M.VSTX` | `UMLPROF_M.VSSX` | `Stereotype`, `Metaclass`, `Profile`, `Extension`, `Reference`, `Generalization` |

All inherit the universal `Prop.Visibility` / `Prop.IsAbstract` /
`Prop.IsStatic` / `Prop.Stereotype` cell triple. `uml-object` adds
`Prop.InstanceName` + `Prop.ClassifierName` + `Prop.Feature` /
`Prop.Value`; `uml-communication` carries an ordered `Prop.Messages`
multiline string; `uml-profile.Extension` uses `BeginArrow=4` (filled
black triangle) on the metaclass end.

### 6.9 `dfd` — Data Flow Diagram (Yourdon / Gane-Sarson)

| field | value |
|-------|-------|
| `id` | `dfd` |
| `template` | `DATAFL_M.VSTX` / `DATAFL_U.VSTX` |
| `primary_stencils` | `DATAFL_M.VSSX`, `GANE_M.VSSX` (Gane-Sarson alternate) |
| `canvas` | `{paper:"A3", orientation:"landscape", scale:"1:1", units:"mm"}` |
| `key_masters` | `Process` (numbered circle Yourdon / rounded rectangle Gane), `External entity`, `Data store`, `Data flow`, `State`, `Loop on center`, `Center to center` |
| `description` | Structured-analysis decomposition (level-0/1/...) with Yourdon and Gane-Sarson notations. |

### 6.10 `erd` — Database Model (Crow's Foot)

| field | value |
|-------|-------|
| `id` | `erd` |
| `template` | `DBMOD_M.VSTX` (template removed in 2016 New gallery; stencil still installed; community add-in restores menu entry) |
| `primary_stencils` | `DBMOD_M.VSSX` (Database Model) — also `CROWSFOOT_M.VSSX`, `IDEF1X_M.VSSX`, `RELATIONAL_M.VSSX` on legacy installs |
| `canvas` | `{paper:"A3", orientation:"landscape", scale:"1:1", units:"mm"}` |
| `route_style` | `0` |
| `key_masters` | `Entity`, `View`, `Category`, `Type`, `Relationship`, `Parent to category`, `Category to child`, `Dynamic connector` |
| `key_user_cells` | column rows: `Prop.Name`, `Prop.DataType`, `Prop.IsPK`, `Prop.IsFK`, `Prop.IsRequired`, `Prop.IsUnique`, `Prop.IsIndexed`, `Prop.DefaultValue`, `Prop.Description`, `User.PKFK`; relationship: `Prop.CardinalityChild` (`Zero or one;Exactly one;Zero or more;One or more`), `Prop.CardinalityParent`, `Prop.IsIdentifying`, `Prop.VerbPhraseParentToChild`, `Prop.VerbPhraseChildToParent`, `Prop.ParentEntityName`, `Prop.ChildEntityName`; `LinePattern=1` (identifying) / `2` (non-identifying) |
| `description` | Crow's-Foot ERD with PK/FK gutter glyphs, identifying vs non-identifying relationship line patterns, and verbalization strings. |

---

## 7. Engineering Family

> All Engineering templates default to `DrawingScale != 1` and ship a
> title block per page (`User.titleblock=TRUE`). `RouteStyle=0` because
> process and electrical schematics use orthogonal connectors only.

### 7.1 `basic-electrical` — Basic Electrical Schematic (IEEE 315)

| field | value |
|-------|-------|
| `id` | `basic-electrical` |
| `template` | `BAELEC_M.VSTX` / `BAELEC_U.VSTX` |
| `workspace_id` | `Microsoft.Visio.BasicElectricalTemplate` |
| `built_in_stencil_enum` | `visBuiltInStencilBasicElectrical=70` |
| `primary_stencils` | `ELECFI_M.VSSX` (Fundamental Items), `ELECRC_M.VSSX` (Resistors and Capacitors), `ELECSR_M.VSSX` (Switches and Relays), `ELECTP_M.VSSX` (Transmission Paths), `ELECPS_M.VSSX` (Power Sources), `ELECSE_M.VSSX` (Semiconductors), `ELECTW_M.VSSX` (Transformers), `ELECRE_M.VSSX` (Rotating Equipment), `ELECCA_M.VSSX` (Composite Assemblies), `ELECTC_M.VSSX` (Terminals) |
| `canvas` | `{paper:"A3", orientation:"landscape", scale:"1 in : 1 in", units:"in"}` (US: ANSI B) |
| `route_style` | `0` |
| `theme` | `{base:"Office", variant:1}` |
| `key_masters` | `Resistor`, `Capacitor`, `Inductor`, `Battery`, `Voltage source`, `Current source`, `Diode`, `LED`, `Zener diode`, `NPN transistor`, `PNP transistor`, `MOSFET-N`, `MOSFET-P`, `Op-amp`, `Switch SPST`, `Switch SPDT`, `Relay`, `Ground (earth)`, `Antenna`, `Transformer`, `Fuse`, `Wire`, `Wire, junction`, `Wire, crossover` |
| `key_user_cells` | `Prop.RefDes` (`R`, `C`, `L`, `D`, `Q`, `U`, `J`, `K`, `M`, `T`, `Y`, `S`), `Prop.Value`, `Prop.Tolerance`, `Prop.Power`, `Prop.PartNumber`; `Connections.Row_n` per pin |
| `add_ons` | `ELECTRICAL` (`/cmd=NumberWires`, `/cmd=NetList`, `/cmd=BOM`, `/cmd=ValidateRefDes`) |
| `description` | IEEE Std 315-1975 schematic capture with RefDes per ASME Y14.44 / IEEE 200. |

### 7.2 `logic-gate` — Logic Gate Diagram

| field | value |
|-------|-------|
| `id` | `logic-gate` |
| `template` | `LOGIC_M.VSTX` / `LOGIC_U.VSTX` (subset of Basic Electrical) |
| `built_in_stencil_enum` | `visBuiltInStencilLogicGate=80` |
| `primary_stencils` | `LOGGATE_M.VSSX` (Logic Gates), `INTSEM_M.VSSX` (Integrated Circuit Components), `TERSOC_M.VSSX` (Terminals and Connectors) |
| `canvas` | `{paper:"A3", orientation:"landscape", scale:"1:1", units:"in"}` |
| `key_masters` | `AND`, `OR`, `NAND`, `NOR`, `XOR`, `XNOR`, `Inverter` (`NOT`), `Buffer`, `Tri-state buffer`, `Flip-flop, D`, `Flip-flop, JK`, `Flip-flop, RS`, `Multiplexer`, `Demultiplexer`, `Decoder`, `Encoder`, `Latch`, `Adder` |
| `key_user_cells` | `User.NumInputs` (2..8), `User.Inverted`, `User.HasPreset`, `User.HasClear`, `Prop.RefDes="U?"`, `Prop.PartNumber="74LS08"`; `Connections.Input_1..N`, `Connections.Output` |
| `description` | ANSI/IEEE 91-1984 distinctive-shape combinational and sequential logic. |

### 7.3 `pfd` — Process Flow Diagram

| field | value |
|-------|-------|
| `id` | `pfd` |
| `template` | `PFD_M.VSTX` / `PFD_U.VSTX` |
| `workspace_id` | `Microsoft.Visio.PFDTemplate` |
| `primary_stencils` | `PEEQGN_M.VSSX` (Equipment, General), `PEEQHE_M.VSSX` (Heat Exchangers), `PEEQVS_M.VSSX` (Vessels), `PEEQPM_M.VSSX` (Pumps), `PFDPI_M.VSSX` (Process Annotations) |
| `canvas` | `{paper:"A1", orientation:"landscape", scale:"1 ft", units:"ft"}` (US: ANSI E) |
| `route_style` | `0` |
| `key_masters` | `Vessel`, `Reactor`, `Column / tower`, `Heat exchanger (shell-and-tube)`, `Heat exchanger (plate)`, `Pump (centrifugal)`, `Pump (positive displacement)`, `Compressor`, `Mixer`, `Stream`, `Material balance table` |
| `key_user_cells` | `User.DiagramType="PFD"` (page-level), `Prop.TagNumber`, `Prop.ServiceDescription`, `User.StreamComposition` |
| `add_ons` | `PROCESSENG` (stream tables, BOM, validate connections) |
| `description` | Refinery / chemical-plant macro-flow; parent diagram for downstream P&IDs. |

### 7.4 `pid` — Piping & Instrumentation Diagram (ISA-5.1)

| field | value |
|-------|-------|
| `id` | `pid` |
| `template` | `PID_M.VSTX` / `PID_U.VSTX` |
| `workspace_id` | `Microsoft.Visio.PIDTemplate` |
| `primary_stencils` | `PEEQGN_M.VSSX`, `PEEQHE_M.VSSX`, `PEEQPM_M.VSSX`, `PEEQVS_M.VSSX`, `PEINSM_M.VSSX` (Instruments), `PEPIPS_M.VSSX` (Pipelines), `PEVALV_M.VSSX` (Valves and Fittings) |
| `canvas` | `{paper:"A1", orientation:"landscape", scale:"1 ft / 1 m", units:"ft|m"}` (US: ANSI E) |
| `route_style` | `0` |
| `theme` | `{base:"Office", variant:1}` |
| `validation_rule_set` | `Piping and Instrumentation` (custom — endpoint-glue and tag-uniqueness rules) |
| `key_masters` | `Major pipeline`, `Minor pipeline`, `Capillary`, `Pneumatic signal`, `Electric signal`, `Hydraulic signal`, `Discrete instrument`, `Shared display`, `Computer function`, `Software function`, `Logic function`, `Gate valve`, `Globe valve`, `Ball valve`, `Butterfly valve`, `Check valve`, `Plug valve`, `Diaphragm valve`, `Needle valve`, `Pressure relief`, `Three-way valve`, `Reducer`, `Tee`, `Cross`, `Elbow`, `Flange`, `Vertical vessel`, `Horizontal vessel`, `Centrifugal pump` |
| `key_user_cells` | instrument bubble: `User.MountType` (`0=field`, `1=panel`, `2=aux panel`, `3=DCS`, `4=PLC`), `User.Accessibility` (`0=accessible`, `1=not`), `Prop.TagFirst` (F/L/P/T/A/H/S/Y/Z), `Prop.TagFunctions` (I/R/C/T/E/V/Y/S), `Prop.TagNumber`, `Prop.LoopID`; pipeline: `User.IsPipeline=TRUE`, `User.PipeSpec`, `User.LineNumber`, `User.Service`, `Prop.Diameter`, `Prop.InsulationType`, `Prop.InsulationThickness`, page-level `User.PipeJumps` (`0=none`, `1=arc`, `2=gap`) |
| `add_ons` | `PROCESSENG` (`/cmd=TagComponents`, `/cmd=NumberPipelines`, `/cmd=GenerateBOM`, `/cmd=ValidateConnections`, `/cmd=PipelineList`) |
| `description` | ANSI/ISA-5.1-2009 detailed plant control diagram with two-line ISA tag balloons and pipe-jump rendering. |

### 7.5 `hvac` — HVAC Plan

| field | value |
|-------|-------|
| `id` | `hvac` |
| `template` | `HVAC_M.VSTX` / `HVAC_U.VSTX` |
| `primary_stencils` | `HVACDC_M.VSSX` (Ducts), `HVACEQ_M.VSSX` (Equipment), `HVACCT_M.VSSX` (Controls), `HVCTEQ_M.VSSX` (Controls Equipment), `RGD_M.VSSX` (Registers, Grilles and Diffusers) |
| `canvas` | `{paper:"A1", orientation:"landscape", scale:"1:50", units:"mm"}` (US: ANSI D, `1/4 in : 1 ft`) |
| `route_style` | `0` |
| `key_masters` | `Air handler`, `Rooftop unit`, `Chiller`, `Cooling tower`, `Boiler`, `Furnace`, `Pump, HVAC`, `Fan, centrifugal`, `Fan, axial`, `Heat pump`, `VAV box`, `CAV box`, `Filter, HVAC`, `Duct, rectangular`, `Duct, round`, `Elbow, rectangular`, `Elbow, round`, `Reducer`, `Tee, branch`, `Cross`, `Damper, manual`, `Damper, motorised`, `Volume box`, `Flexible duct`, `Diffuser, ceiling`, `Linear diffuser`, `Return air grille`, `Exhaust register`, `Thermostat`, `Humidistat`, `Sensor, temperature`, `Sensor, pressure`, `Controller, DDC`, `Actuator` |
| `key_user_cells` | duct: `User.DuctWidth`, `User.DuctHeight`, `User.Diameter` (round), `User.DuctType` (`0=Supply`, `1=Return`, `2=Exhaust`, `3=Outside`, `4=Mixed`), `Prop.AirFlow`, `Prop.Velocity=AirFlow/(DuctWidth*DuctHeight)`, `Prop.PressureDrop`; register: `User.NeckSize`, `Prop.Throw`, `Prop.NoiseCriterion`, `Prop.MountType`; `LineColor=IF(User.DuctType=0,RGB(0,128,255),IF(User.DuctType=1,RGB(255,128,0),RGB(0,160,0)))` |
| `add_ons` | `HVAC` (`/cmd=SizeDucts`, `/cmd=BalanceFlow`, `/cmd=RegisterSchedule`, `/cmd=DuctTakeoff`) |
| `description` | ASHRAE/SMACNA mechanical shop drawing with duct sizing, flow balance, and register schedule add-ons. |

### 7.6 `plumbing` — Plumbing & Piping Plan

| field | value |
|-------|-------|
| `id` | `plumbing` |
| `template` | `PLMBPL_M.VSTX` / `PLMBPL_U.VSTX` |
| `primary_stencils` | `PLUMB_M.VSSX` (Plumbing), `PIPES1_M.VSSX` (Pipes 1), `PIPES2_M.VSSX` (Pipes 2), `VALVES1_M.VSSX` (Valves 1), `VALVES2_M.VSSX` (Valves 2), `BATHKIT_M.VSSX` (Bath and Kitchen — shared) |
| `canvas` | `{paper:"A1", orientation:"landscape", scale:"1:50", units:"mm"}` |
| `key_masters` | `Toilet, plumbing`, `Lavatory`, `Bathtub, plumbing`, `Shower, plumbing`, `Sink, kitchen`, `Sink, double`, `Urinal`, `Floor drain`, `Hose bib`, `Water heater`, `Water meter`, `Pipe, supply`, `Pipe, drain`, `Pipe, vent`, `Pipe, gas`, `Pipe, fire sprinkler`, `Pipe, condensate`, `Riser, up`, `Riser, down`, `Cleanout`, `Trap`, `Backflow preventer`, `Mixing valve`, `Reducing valve`, `Solenoid valve`, `Float valve` |
| `key_user_cells` | fixture: `User.FixtureUnits` (DFU), `User.HotWaterDemand` (gpm), `User.ColdWaterDemand`, `Prop.Connections` (`1/2 in;3/4 in;1 in;1-1/4 in;1-1/2 in;2 in`), `Prop.Manufacturer`, `Prop.Model` |
| `description` | Plumbing-fixture and piping-riser diagram with fixture-unit (DFU) and demand totals. |

---

## 8. Floor Plan / Maps Family

> All floor-plan templates set `PageScale != 1`, default to ANSI D / A1
> paper, and turn on architectural ruler ticks via document cell
> `MeasurementUnits = visMeters` (metric) / `visFeetAndInches` (US).
> The `BUILDING PLAN` add-on drives wall trim and door/window cutouts
> via `RUNADDONWARGS("BUILDING PLAN","/cmd=…")` `Events.EventDrop` /
> `Events.EventXFMod` formulas on the `Wall`, `Door`, `Window` masters.

### 8.1 `floor-plan` — Floor Plan

| field | value |
|-------|-------|
| `id` | `floor-plan` |
| `template` | `FLRPLN_M.VSTX` / `FLRPLN_U.VSTX` |
| `workspace_id` | `Microsoft.Visio.FloorPlanTemplate` |
| `primary_stencils` | `WALSTR_M.VSSX` (Walls, Shell and Structure), `DRWIN_M.VSSX` (Doors and Windows), `BLDCOR_M.VSSX` (Building Core), `FURN_M.VSSX` (Furniture), `BATHKIT_M.VSSX` (Bath and Kitchen), `DIMARC_M.VSSX` (Dimensioning — Architectural) |
| `canvas` | `{paper:"A1", orientation:"landscape", scale:"1:50", units:"mm"}` (US: ANSI D, `1/4 in : 1 ft`) |
| `route_style` | `0` |
| `theme` | `{base:"Office", variant:1}` |
| `key_masters` | `Wall`, `Curved wall`, `Cavity wall`, `Space`, `Column`, `Beam`, `Roof`, `Slab`, `Structural shape`, `Pad footing`, `Continuous footing`, `Stair`, `Stair (curved)`, `Ramp`, `Door`, `Door – glass`, `Door – metal`, `Door – revolving`, `Door – sliding`, `Door – overhead`, `Window`, `Window – bay`, `Window – casement`, `Window – sash`, `Skylight`, `Opening`, `Elevator`, `Stairs (multi-story)` |
| `key_user_cells` | wall: `User.WallThickness=GUARD(150 mm)`, `User.AlignmentReference` (`0=centre`, `1=inner`, `2=outer`), `User.AntiScale=1/ThePage!PageScale*ThePage!DrawingScale`, `User.WallBegin=PNT(BeginX,BeginY)`, `User.WallEnd=PNT(EndX,EndY)`, `User.ShowDimension`, `Prop.WallType` (`Interior;Exterior;Foundation;Partition`), `Prop.FireRating`; door/window: `User.HoleWidth=GUARD(Width)`, `User.HoleDepth=GUARD(Width(Wall))`, `User.SwingAngle=GUARD(90 deg)` (Door), `User.SwingDirection=GUARD(1)`, `User.SillHeight=900 mm` (Window), `User.HeadHeight=2400 mm`, `Prop.DoorNumber`, `Prop.WindowNumber`, `Prop.FireRating`, `Prop.Manufacturer`, `Prop.Model`; space: `Prop.Name`, `Prop.RoomNumber`, `Prop.Department`, `Prop.UseType`, `Prop.Area=AREA(Geometry1.Path)`, `Prop.Perimeter=PERIMETER(Geometry1.Path)`, `User.AreaUnits="m²"` |
| `add_ons` | `BUILDING PLAN` (wall trim, cutouts, room numbering, plan reports), `VisRpt` (Door Schedule, Window Schedule, Space Inventory, Furniture Inventory, Wall Lengths) |
| `description` | Architectural plan with smart Wall/Door/Window cutout choreography and AREA/PERIMETER-driven Space rooms. |

### 8.2 `office-layout` — Office Layout

| field | value |
|-------|-------|
| `id` | `office-layout` |
| `template` | `OFFLAY_M.VSTX` / `OFFLAY_U.VSTX` |
| `primary_stencils` | `WALSTR_M.VSSX`, `DRWIN_M.VSSX`, `OFCFRN_M.VSSX` (Office Furniture), `OFCEQP_M.VSSX` (Office Equipment), `OFCACC_M.VSSX` (Office Accessories), `CUBICAL_M.VSSX` (Cubicles), `FURN_M.VSSX` |
| `canvas` | `{paper:"A1", orientation:"landscape", scale:"1:50", units:"mm"}` |
| `key_masters` | `Desk`, `Round table`, `Boat-shaped table`, `Conference table`, `File`, `Lateral file`, `Bookcase`, `Plant`, `Workstation`, `Computer`, `Monitor`, `Printer`, `Copier`, `Fax`, `Phone`, `Projector`, `Whiteboard`, `Telephone`, `Lamp, desk`, `Keyboard`, `Wastepaper basket`, `Plant, small`, `Coffee machine`, `Panel, straight`, `Panel, corner`, `Workstation, L`, `Workstation, U`, `Cubicle, 2-person`, `Bullnose worksurface`, `Privacy screen` |
| `key_user_cells` | furniture: `User.AntiScale`, `Prop.AssetNumber`, `Prop.Manufacturer`, `Prop.Model`, `Prop.SerialNumber`, `Prop.Cost`, `Prop.OwnedBy`, `Prop.Department`, `Prop.SpaceID`; cubicle panels: `User.PanelThickness=50 mm`, `User.PanelHeight=1500 mm`; office equipment: `Prop.PowerLoad`, `Prop.HeatLoad`, `Prop.NetworkPort` |
| `description` | Cubicle / desk / equipment layout with panel-to-panel glue and FM-grade asset metadata. |

### 8.3 `home-plan` — Home Plan

| field | value |
|-------|-------|
| `id` | `home-plan` |
| `template` | `HOMEPLN_M.VSTX` |
| `primary_stencils` | `WALSTR_M.VSSX`, `DRWIN_M.VSSX`, `BATHKIT_M.VSSX`, `CABINETS_M.VSSX`, `APPLIANCES_M.VSSX`, `ELECT_M.VSSX`, `SITACC_M.VSSX` (Garden Accessories), `FURN_M.VSSX` |
| `canvas` | `{paper:"A1", orientation:"landscape", scale:"1:50", units:"mm"}` |
| `key_masters` | `Wall`, `Door`, `Window`, `Toilet`, `Bathtub`, `Shower`, `Sink`, `Refrigerator`, `Range`, `Dishwasher`, `Microwave`, `Cabinet`, `Tree, deciduous`, `Shrub` |
| `description` | Residential floor plan with bathroom, kitchen, and landscaping shapes. |

### 8.4 `site-plan` — Site Plan

| field | value |
|-------|-------|
| `id` | `site-plan` |
| `template` | `SITPLN_M.VSTX` / `SITPLN_U.VSTX` |
| `workspace_id` | `Microsoft.Visio.SitePlanTemplate` |
| `primary_stencils` | `SITACC_M.VSSX` (Site Accessories), `GARDEN_M.VSSX`, `IRRIG_M.VSSX`, `PLANT_M.VSSX`, `VEHICLE_M.VSSX`, `WALSTR_M.VSSX` |
| `canvas` | `{paper:"A0", orientation:"landscape", scale:"1:200", units:"mm"}` (US: ANSI E, `1 in : 20 ft`) |
| `key_masters` | `Tree (deciduous)`, `Tree (evergreen)`, `Shrub`, `Lawn area`, `Walkway`, `Driveway`, `Property line`, `Sprinkler head`, `Bench`, `Lamp post`, `Fence`, `Gate`, `Hedge` |
| `description` | Landscape / civil-survey site plot at 1:200 (or 1 in : 20 ft). |

### 8.5 `reflected-ceiling-plan` — Reflected Ceiling Plan

| field | value |
|-------|-------|
| `id` | `reflected-ceiling-plan` |
| `template` | `RFLPLN_M.VSTX` / `RCPLAN_U.VSTX` |
| `primary_stencils` | `RCPLAN_M.VSSX` (Reflected Ceiling), `WALSTR_M.VSSX`, `ELECT_M.VSSX` |
| `canvas` | `{paper:"A1", orientation:"landscape", scale:"1:50", units:"mm"}` |
| `key_masters` | `Suspended ceiling grid`, `Recessed light`, `Fluorescent fixture`, `Pendant light`, `Sprinkler head`, `Smoke detector`, `Diffuser (HVAC)`, `Speaker`, `Exit sign` |
| `description` | Lighting and ceiling-grid coordination plan; fixtures overlay a backdrop ceiling-grid layer (no auto-cut). |

### 8.6 `electrical-telecom-plan` — Electrical & Telecom Plan

| field | value |
|-------|-------|
| `id` | `electrical-telecom-plan` |
| `template` | `ELECPL_M.VSTX` / `ETPLAN_U.VSTX` |
| `primary_stencils` | `ELECT_M.VSSX` (Electrical and Telecom), `WALSTR_M.VSSX`, `BLDCOR_M.VSSX`, `RGD_M.VSSX` |
| `canvas` | `{paper:"A1", orientation:"landscape", scale:"1:50", units:"mm"}` |
| `key_masters` | `Duplex outlet`, `Quad outlet`, `GFCI outlet`, `Light switch`, `Three-way switch`, `Dimmer`, `Telephone jack`, `Data jack`, `Junction box`, `Circuit breaker panel`, `Cable tray` |
| `description` | Outlet / switch / data-jack layout overlaid on architectural backgrounds. |

### 8.7 `plant-layout` — Plant Layout

| field | value |
|-------|-------|
| `id` | `plant-layout` |
| `template` | `PLAYOUT_M.VSTX` / `PLAYOUT_U.VSTX` |
| `primary_stencils` | `PLBASE_M.VSSX` (Storage and Distribution), `PLMAC_M.VSSX` (Machines and Equipment), `WALSTR_M.VSSX`, `VEHICLE_M.VSSX`, `WAREHS_M.VSSX` (Warehouse — Shipping and Receiving) |
| `canvas` | `{paper:"A1", orientation:"landscape", scale:"1:50", units:"mm"}` |
| `key_masters` | `CNC machine`, `Conveyor`, `Workbench`, `Forklift`, `Pallet rack`, `Storage area`, `Shipping dock`, `Robot arm` |
| `description` | Manufacturing / warehouse facility layout for lean cell design and slotting. |

### 8.8 `security-access-plan` — Security & Access Plan

| field | value |
|-------|-------|
| `id` | `security-access-plan` |
| `template` | `SECPLN_M.VSTX` / `SECPLN_U.VSTX` |
| `primary_stencils` | `SECEQ_M.VSSX` (Alarm and Access Control), `VIDSUR_M.VSSX` (Video Surveillance), `INITSF_M.VSSX` (Initiation and Annunciation), `WALSTR_M.VSSX` |
| `canvas` | `{paper:"A1", orientation:"landscape", scale:"1:50", units:"mm"}` |
| `key_masters` | `Access reader`, `Camera (fixed)`, `Camera (PTZ)`, `Motion detector`, `Glass-break sensor`, `Door contact`, `Smoke detector`, `Heat detector`, `Pull station`, `Strobe`, `Annunciator panel`, `Card reader`, `Keypad`, `Magnetic lock` |
| `description` | CCTV coverage, access-control, and NFPA 72 alarm layout on architectural backgrounds. |

---

## 9. Schedule Family

### 9.1 `calendar` — Calendar

| field | value |
|-------|-------|
| `id` | `calendar` |
| `template` | `CALEND_M.VSTX` / `CALEND_U.VSTX` |
| `workspace_id` | `Microsoft.Visio.CalendarTemplate` |
| `built_in_stencil_enum` | `visBuiltInStencilCalendar=27` |
| `primary_stencils` | `CALEND_M.VSSX` |
| `canvas` | `{paper:"A4", orientation:"landscape", scale:"1:1", units:"mm"}` (US: Letter) |
| `key_masters` | `Month`, `Week`, `Day`, `Multi-day event`, `Appointment`, `Year`, `Small month`, `Title bar`, `Art 1` … `Art 6` |
| `key_user_cells` | `User.Date`, `User.StartDate`; Day-master colour formula `IF(WEEKDAY(User.Date,1)=1, …)`; grid populated via `=DATETIME(User.StartDate)+ROW()-1` |
| `add_ons` | `Microsoft.Office.Visio.CalendarAddOn` (legacy `CALWIZ.EXE`) — generates monthly grid from start date |
| `description` | Editorial / project-milestone calendar grid driven by `WEEKDAY` / `DATETIME` formulas. |

### 9.2 `gantt-chart` — Gantt Chart (data-bound)

| field | value |
|-------|-------|
| `id` | `gantt-chart` |
| `template` | `GANTT_M.VSTX` / `GANTT_U.VSTX` |
| `workspace_id` | `Microsoft.Visio.GanttTemplate` |
| `built_in_stencil_enum` | `visBuiltInStencilGantt=15` |
| `primary_stencils` | `GANTT_M.VSSX` |
| `canvas` | `{paper:"A1", orientation:"landscape", scale:"1:1", units:"mm"}` (US: ANSI D) |
| `route_style` | `0` |
| `theme` | `{base:"Office", variant:1}` |
| `key_masters` | `Task bar`, `Milestone`, `Summary bar`, `Row`, `Column`, `Title`, `Legend`, `Gantt frame` |
| `key_user_cells` | `Prop.Start`, `Prop.Finish`, `Prop.Duration`, `Prop.PercentComplete`, `User.GanttUseDates`; chart-level `Page.GanttChart.BeginDate`, `EndDate`, `MajorUnits`, `MinorUnits`, `DurationUnits` (`VisTimeUnit`: `1=Minute`, `2=Hour`, `3=Day`, `4=Week`, `5=Month`, `6=Quarter`, `7=Year`); link types via `VisGCLinkType`: `0=FS`, `1=SS`, `2=FF`, `3=SF`; predecessor strings `"1FS,3SS+2d"` |
| `add_ons` | (built-in) — `Page.DropGanttChart(start, end, fmt)` returns `Visio.GanttChart`; `Tasks.Add(visTaskBar=1)` / `Tasks.Add(visTaskMilestone=2)` / `Tasks.Add(visTaskSummary=3)`; `Tasks.AddBefore(idx)` / `AddAfter(idx)` / `Item(idx)`; `Tasks.Link(predID, succID, linkType)`; `Task.Outdent()` / `Indent()` / `Delete()` |
| `description` | The only Visio template whose primary edit surface is a top-level COM object (`GanttChart`) rather than the page; tasks carry typed dependencies and predecessor strings. |

### 9.3 `pert-chart` — PERT Chart

| field | value |
|-------|-------|
| `id` | `pert-chart` |
| `template` | `PERT_M.VSTX` / `PERT_U.VSTX` |
| `workspace_id` | `Microsoft.Visio.PERTTemplate` |
| `built_in_stencil_enum` | `visBuiltInStencilPERT=70` |
| `primary_stencils` | `PERT_M.VSSX`, `BASFLO_M.VSSX`, `CONNEC_M.VSSX` |
| `canvas` | `{paper:"A3", orientation:"landscape", scale:"1:1", units:"mm"}` |
| `route_style` | `0` |
| `key_masters` | `PERT 1` (6-cell grid), `PERT 2` (alternate layout), `Summary 1`, `Summarized node`, `Critical edge`, `Non-critical edge` |
| `key_user_cells` | `Prop.TaskName`, `Prop.Duration`, `Prop.EarliestStart`, `Prop.EarliestFinish`, `Prop.LatestStart`, `Prop.LatestFinish`, `Prop.Cost`, `Prop.Resources`, `User.Slack=Prop.LatestStart-Prop.EarliestStart`; critical-edge auto-colour `LineColor=IF(SHEETREF(BeginX)!User.Slack=0, RGB(192,0,0), RGB(89,89,89))` |
| `description` | Activity-on-node network with forward/backward pass and critical-path highlighting. |

### 9.4 `timeline` — Timeline

| field | value |
|-------|-------|
| `id` | `timeline` |
| `template` | `TIMELINE_M.VSTX` / `TIMELINE_U.VSTX` |
| `workspace_id` | `Microsoft.Visio.TimelineTemplate` |
| `built_in_stencil_enum` | `visBuiltInStencilTimeline=28` |
| `primary_stencils` | `TIMELINE_M.VSSX` |
| `canvas` | `{paper:"A3", orientation:"landscape", scale:"1:1", units:"mm"}` |
| `route_style` | `0` |
| `key_masters` | timelines: `Block timeline`, `Line timeline`, `Cylindrical timeline`, `Ruler timeline`, `Divided timeline`, `Expanded timeline`; events: `Diamond milestone`, `Circle milestone`, `Star milestone`, `Triangle milestone`, `Line milestone`, `Cylindrical milestone`, `Pin milestone`, `Today marker`; intervals: `Block interval`, `Cylindrical interval`, `Bracket interval`, `Line interval` |
| `key_user_cells` | timeline: `User.Start`, `User.End`, `User.MajorUnits`, `User.MinorUnits` (`VisTimeUnit` 1..7), `User.Format`, `User.TickMarks` (Ruler), `User.PhaseLabels` (Divided); event: `User.MilestoneDate`, `Prop.Description`, `User.DateFormat` (`12=long`, `15=short`, `16=ISO`, `19=Q1 2026`, `20=Jan 2026`), `User.IsToday=TRUE` (Today marker default `User.MilestoneDate=NOW()`); interval: `User.StartDate`, `User.EndDate`; PinX glue formula `=SHEETREF(Timeline)!Width*((User.MilestoneDate-Timeline.User.Start)/(Timeline.User.End-Timeline.User.Start))+...` |
| `add_ons` | `Timeline` (Visio 2013+ AddOn — re-glues markers to timeline coordinates after date edits) |
| `description` | 1-D dynamic timeline shape with three marker classes (interval / event / today) and date-driven PinX glue. |

---

## 10. Business Family

### 10.1 `swot` — SWOT Analysis

| field | value |
|-------|-------|
| `id` | `swot` |
| `template` | `SWOT_M.VSTX` / `SWOT_U.VSTX` (some SKUs reuse `MARKETC_M.VSTX`) |
| `workspace_id` | `Microsoft.Visio.MarketingTemplate` |
| `primary_stencils` | `MARKETC_M.VSSX`, `MARKETD_M.VSSX`, `LEGEND_M.VSSX` |
| `canvas` | `{paper:"A3", orientation:"landscape", scale:"1:1", units:"mm"}` |
| `key_masters` | `2x2 matrix`, `Quadrant`, `Title bar`, `Description block` |
| `key_user_cells` | `User.QuadrantIndex` (1=top-left, 2=top-right, 3=bottom-left, 4=bottom-right), `User.AxisLabelTop`, `User.AxisLabelLeft`, `Prop.Title`, `Prop.Description`, `Prop.Body` |
| `description` | 2x2 list-container quadrant for Strengths / Weaknesses / Opportunities / Threats. |

### 10.2 `balanced-scorecard` — Balanced Scorecard

| field | value |
|-------|-------|
| `id` | `balanced-scorecard` |
| `template` | `BSC_M.VSTX` (sometimes `STRATEGY_M.VSTX`) |
| `workspace_id` | `Microsoft.Visio.BSCTemplate` |
| `primary_stencils` | `TQM_M.VSSX`, `MARKETD_M.VSSX`, `LEGEND_M.VSSX` |
| `canvas` | `{paper:"A3", orientation:"landscape", scale:"1:1", units:"mm"}` |
| `key_masters` | `Perspective` (Financial / Customer / Internal Process / Learning & Growth), `Objective`, `KPI`, `Initiative`, `Strategy map node`, `Cause-effect arrow` |
| `key_user_cells` | `User.PerspectiveIndex` (1..4), `User.msvSDContainerCategories="BSC"`, `User.RAGStatus` (`R/A/G` driving `FillForegnd`), `Prop.PerspectiveName`, `Prop.Objective`, `Prop.Measure`, `Prop.Target`, `Prop.Initiative`, `Prop.Owner`, `Prop.KPIName`, `Prop.Actual`, `Prop.Variance`, `Prop.DueDate`, `Prop.Status` |
| `description` | Kaplan-Norton four-perspective horizontal list-container stack with traffic-light objective cards. |

### 10.3 `strategy-map` — Strategy Map

| field | value |
|-------|-------|
| `id` | `strategy-map` |
| `template` | `STRATEGY_M.VSTX` / `STRATEGY_U.VSTX` |
| `workspace_id` | `Microsoft.Visio.StrategyMapTemplate` |
| `primary_stencils` | `STRATEGY_M.VSSX`, `MARKETC_M.VSSX`, `MARKETD_M.VSSX`, `BLOCK_M.VSSX`, `CONNEC_M.VSSX` |
| `canvas` | `{paper:"A3", orientation:"landscape", scale:"1:1", units:"mm"}` |
| `route_style` | `4` |
| `place_style` | `3` |
| `key_masters` | `Cause-effect arrow` (drives), `Enables connector`, `Measures connector`, `Strategy map node`, `Perspective` (re-used) |
| `key_user_cells` | `User.LinkType` (`drives`/`enables`/`measures`), `User.IsCausal=TRUE`; line ends: `LineEnd.EndArrow=4` (drives, filled triangle), `LineEnd.EndArrow=2` (enables, open arrow), `LinePattern=2` (measures, dashed) |
| `description` | Balanced Scorecard with typed cause-effect connectors rendering Kaplan-Norton's bottom-up causal chain. |

### 10.4 `marketing-charts` — Marketing Charts & Diagrams

| field | value |
|-------|-------|
| `id` | `marketing-charts` |
| `template` | `MARKETC_M.VSTX` / `MARKETC_U.VSTX` |
| `built_in_stencil_enum` | `visBuiltInStencilMarketing=66` |
| `primary_stencils` | `MARKETC_M.VSSX`, `MARKETD_M.VSSX`, `MARKETC2_M.VSSX` |
| `canvas` | `{paper:"A3", orientation:"landscape", scale:"1:1", units:"mm"}` |
| `key_masters` | `Pie chart`, `Pie slice`, `Bar chart`, `Column chart`, `Line chart`, `Pyramid (4 levels)`, `Funnel`, `Pipeline`, `Cycle`, `Triangle`, `Block arrow`, `Marketing 2x2 matrix`, `Boston box`, `Ansoff matrix`, `4P (price/place/product/promotion)` |
| `description` | Conceptual business graphics for slide-quality charts. |

### 10.5 `itil-diagram` — ITIL Diagram

| field | value |
|-------|-------|
| `id` | `itil-diagram` |
| `template` | `ITIL_M.VSTX` / `ITIL_U.VSTX` |
| `workspace_id` | `Microsoft.Visio.ITILTemplate` |
| `primary_stencils` | `ITIL_M.VSSX`, `BASFLO_M.VSSX`, `CROSSFUNC_M.VSSX`, `CONNEC_M.VSSX` |
| `canvas` | `{paper:"A3", orientation:"landscape", scale:"1:1", units:"mm"}` |
| `route_style` | `4` |
| `key_masters` | `Incident`, `Problem`, `Change`, `Release`, `Service`, `Service Desk`, `Configuration Item`, `Knowledge Article`, `Service Level Agreement`, `Process` (BASFLO, ITIL theme), `Decision` |
| `key_user_cells` | `Prop.IncidentID`, `Prop.Priority`, `Prop.Status`, `Prop.ProblemID`, `Prop.RootCause`, `Prop.WorkaroundExists`, `Prop.ChangeID`, `Prop.ChangeType`, `Prop.RFC`, `Prop.ReleaseID`, `Prop.Window`, `Prop.RollbackPlan`, `Prop.ServiceName`, `Prop.SLAID`, `Prop.OwnerTeam`, `Prop.CIID`, `Prop.CIType`, `Prop.Environment`, `Prop.SLATarget`, `Prop.MetricUnit` |
| `description` | ITIL v3/v4 service-management process diagram themed on a Cross-Functional Flowchart. |

### 10.6 `six-sigma` — Six Sigma Diagram (DMAIC)

| field | value |
|-------|-------|
| `id` | `six-sigma` |
| `template` | `SIXSIG_M.VSTX` / `SIXSIG_U.VSTX` |
| `workspace_id` | `Microsoft.Visio.SixSigmaTemplate` |
| `primary_stencils` | `SSCEDIA_M.VSSX` (Cause-Effect), `SSSIPOC_M.VSSX` (SIPOC), `SSVSM_M.VSSX` (Value Stream Map), `SSFMEA_M.VSSX` (FMEA), `BASFLO_M.VSSX`, `CONNEC_M.VSSX`, `MARKETC_M.VSSX`, `CAUSEEFF_M.VSSX` |
| `canvas` | `{paper:"A3", orientation:"landscape", scale:"1:1", units:"mm"}` |
| `key_masters` | `DMAIC step`, `Define`, `Measure`, `Analyze`, `Improve`, `Control`, `Pareto bar`, `Histogram`, `Scatter plot`, `Control chart`, `Fishbone (Ishikawa)`, `5 Whys`, `SIPOC` (+ all sub-template masters) |
| `description` | DMAIC project storyboard combining Cause-Effect, SIPOC, VSM, and FMEA stencils. |

### 10.7 `cause-effect-fishbone` — Cause & Effect (Fishbone / Ishikawa)

| field | value |
|-------|-------|
| `id` | `cause-effect-fishbone` |
| `template` | `CAUSEEFF_M.VSTX` / `CAUSEEFF_U.VSTX` |
| `workspace_id` | `Microsoft.Visio.CauseEffectTemplate` |
| `primary_stencils` | `CAUSEEFF_M.VSSX` / `SSCEDIA_M.VSSX` |
| `canvas` | `{paper:"A3", orientation:"landscape", scale:"1:1", units:"mm"}` |
| `key_masters` | `Effect` (fish head), `Category 1` … `Category 6` (bones), `Primary cause 1` … `Primary cause 4`, `Spine`, `Fishbone frame` |
| `key_user_cells` | `Prop.Effect`, `Prop.Category`, `Prop.Cause`, `User.BoneAngle=IF(MODULUS(User.CategoryIndex,2)=0, 30 deg, -30 deg)`, `User.SpineConnect`, `User.NumCategories=6`, `User.SpineLength` |
| `description` | Horizontal-spine root-cause analysis with 6M (Methods, Machines, Materials, Manpower, Measurement, Mother Nature) categories. |

### 10.8 `value-stream-map` — Lean / Value Stream Map

| field | value |
|-------|-------|
| `id` | `value-stream-map` |
| `template` | `LEAN_M.VSTX` / `LEAN_U.VSTX` |
| `workspace_id` | `Microsoft.Visio.LeanTemplate` |
| `built_in_stencil_enum` | `visBuiltInStencilLeanShapes=98` |
| `primary_stencils` | `LEAN_M.VSSX`, `BASFLO_M.VSSX`, `CONNEC_M.VSSX` |
| `canvas` | `{paper:"A1", orientation:"landscape", scale:"1:1", units:"mm"}` |
| `key_masters` | `Customer/supplier`, `Process box`, `Data box`, `Inventory triangle`, `Push arrow`, `Pull arrow`, `Supermarket`, `Kanban`, `Kanban post`, `FIFO lane`, `Milk run`, `Buffer or safety stock`, `External shipment`, `Production control`, `Manual info flow`, `Electronic info flow`, `Operator`, `Timeline (VSM)`, `Kaizen burst`, `Go-see scheduling`, `Load levelling` |
| `key_user_cells` | `User.HasDataBox`, `User.IsSupermarket`, `User.IsPush`, `User.IsPull`, `User.IsFIFO`, `Prop.ProcessName`, `Prop.Operators`, `Prop.CycleTime`, `Prop.ChangeoverTime`, `Prop.Uptime`, `Prop.LotSize`, `Prop.WorkTime`, `Prop.KanbanType` (`production;withdrawal;signal`), `Prop.MaxQty`, `Prop.PartType`, `Prop.PartNumber`, `Prop.Frequency`, `Prop.BufferQty`, `User.BufferType` (`buffer`/`safety`), `Prop.Demand`, `Prop.Takt`, `Prop.System` (`MRP`/`ERP`/`Manual`), `Prop.Improvement`, `Prop.Heijunka`; sawtooth totals `User.TotalProcessTime`, `User.TotalLeadTime`, `User.ProcessRatio` |
| `description` | *Learning to See* (Rother/Shook) icon vocabulary plus sawtooth timeline ladder for value-add ratio. |

### 10.9 `tqm` — Total Quality Management

| field | value |
|-------|-------|
| `id` | `tqm` |
| `template` | `TQM_M.VSTX` / `TQM_U.VSTX` |
| `built_in_stencil_enum` | `visBuiltInStencilTQM=68` |
| `primary_stencils` | `TQM_M.VSSX`, `CAUSEEFF_M.VSSX`, `MARKETC_M.VSSX`, `BASFLO_M.VSSX`, `CONNEC_M.VSSX` |
| `canvas` | `{paper:"A3", orientation:"landscape", scale:"1:1", units:"mm"}` |
| `key_masters` | `Process`, `Decision`, `Document`, `Top down hierarchy`, `Process step (numbered)`, `Cause-effect`, `5S`, `PDCA`, `Pareto`, `Control chart`, `Run chart`, `Scatter diagram`, `Histogram`, `Check sheet` |
| `description` | Quality-management initiative documentation; ISO 9001 process maps. |

### 10.10 `fmea-grid` — FMEA Grid

| field | value |
|-------|-------|
| `id` | `fmea-grid` |
| `template` | (sub-template of `SIXSIG_M.VSTX`) |
| `primary_stencils` | `SSFMEA_M.VSSX` |
| `canvas` | `{paper:"A3", orientation:"landscape", scale:"1:1", units:"mm"}` |
| `key_masters` | `FMEA header`, `FMEA row`, `FMEA frame` |
| `key_user_cells` | `Prop.Item`, `Prop.Function`, `Prop.FailureMode`, `Prop.FailureEffect`, `Prop.Severity` (1..10), `Prop.Cause`, `Prop.Occurrence` (1..10), `Prop.Controls`, `Prop.Detection` (1..10), `Prop.RecommendedAction`, `Prop.Owner`, `Prop.TargetDate`, `Prop.ActionTaken`, `User.RPN=Prop.Severity*Prop.Occurrence*Prop.Detection`, `User.RowCount`, `User.AutoNumber`; heat-map `FillForegnd=IF(User.RPN>=200,RGB(192,0,0),IF(User.RPN>=100,RGB(255,192,0),RGB(0,176,80)))` |
| `description` | Failure Mode and Effects Analysis tabular grid with computed Risk Priority Number heat-map. |

### 10.11 `sipoc` — SIPOC

| field | value |
|-------|-------|
| `id` | `sipoc` |
| `template` | (sub-template of `SIXSIG_M.VSTX`) |
| `primary_stencils` | `SSSIPOC_M.VSSX` |
| `canvas` | `{paper:"A3", orientation:"landscape", scale:"1:1", units:"mm"}` |
| `key_masters` | `SIPOC frame`, `SIPOC column`, `SIPOC row`, `SIPOC process step` |
| `key_user_cells` | `User.ColumnCount=5`, `User.msvSDContainerCategories="SIPOC"`, `User.ColumnIndex` (1..5), `Prop.ColumnTitle` (`Suppliers;Inputs;Process;Outputs;Customers`), `Prop.Text`, `Prop.StepNumber`, `Prop.StepName` |
| `description` | Five-column Suppliers-Inputs-Process-Outputs-Customers chart implemented as horizontal list containers. |

### 10.12 `functional-block-diagram` — Functional Block Diagram

| field | value |
|-------|-------|
| `id` | `functional-block-diagram` |
| `template` | `BLOCK_M.VSTX` / `BLOCK_U.VSTX` |
| `primary_stencils` | `BLOCK_M.VSSX` (Blocks), `BLOCKR_M.VSSX` (Blocks Raised), `BLOCK3D_M.VSSX` (Blocks with Perspective), `CONNEC_M.VSSX` |
| `canvas` | `{paper:"A3", orientation:"landscape", scale:"1:1", units:"mm"}` |
| `key_masters` | `Block`, `Block (raised)`, `2-D box`, `1-D single arrow`, `1-D double arrow`, `Open/closed bar`, `Tree (left/right/up/down)`, `Vanishing point` |
| `key_user_cells` | `User.VanishingPointX`, `User.VanishingPointY` (3-D variants) |
| `description` | Conceptual block / signal-processing diagram with optional 3-D perspective math. |

---

## 11. Validation Rule Sets — Inventory

Diagrams that ship a `Document.Validation.RuleSets` entry. Each rule set
is enumerated via `Document.Validation.RuleSets.ItemU(<name>).Rules`;
`Document.Validate(visValidateAll)` executes the active set and writes
markers into `Document.Issues`.

| Rule set                       | Diagram id                  | Representative rules (`NameU` → category)                                                                                                                                                                                                                                                                                |
|--------------------------------|-----------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `Flowchart`                    | `basic-flowchart`           | `EveryShapeMustBeConnected` (Warning), `DecisionMustHaveTwoOutcomes` (Warning), `TerminatorEndpointsOnly` (Error), `OffPageReferenceMustPair` (Warning)                                                                                                                                                                |
| `Cross-Functional Flowchart`   | `cross-functional-flowchart`| `LaneMustHaveTitle`, `ShapesMustBelongToALane` (Warning), `ConnectorsCannotCrossPhases` (Warning)                                                                                                                                                                                                                       |
| `BPMN 2.0 Diagram`             | `bpmn-2-0`                  | `MessageFlowMustCrossPools` (Error), `SequenceFlowsCannotCrossPools` (Error), `EventBoundaryMustAttach` (Error), `ExclusiveGatewayHasOneDefault` (Warning), `EndEventNoOutgoing` (Error), `StartEventNoIncoming` (Error), `LaneMustBeInPool` (Error), `MessageFlowEndpointMustBeAllowed` (Error)                       |
| `Piping and Instrumentation`   | `pid`                       | `EveryPipeEndpointMustBeGlued` (Error), `TagNumbersMustBeUnique` (Error), `LoopIDsMustBeConsistent` (Warning), `InstrumentBubblesMustHaveTagFirst` (Warning)                                                                                                                                                            |

Built-in rule discovery from VBA:

```vba
Public Sub DumpRules(ruleSetName As String)
    Dim rs As Visio.ValidationRuleSet
    Set rs = ActiveDocument.Validation.RuleSets.ItemU(ruleSetName)
    Dim r As Visio.ValidationRule
    For Each r In rs.Rules
        Debug.Print r.NameU, r.Description, r.Category, r.Ignored
    Next r
End Sub
```

---

## 12. Layout Algorithm Defaults — Cross-Reference

`Page.PageSheet.RouteStyle` and `PlaceStyle` per diagram, alongside the
auto-layout `Page.Layout` reflow expectation. `AvenueSizeX` /
`AvenueSizeY` shape the channel spacing; defaults are `0.375 in` for
flowchart, `0.25 in` for radial.

| diagram id                   | RouteStyle (constant)                       | PlaceStyle                       | LineJumpStyle              | Notes                                              |
|------------------------------|---------------------------------------------|----------------------------------|----------------------------|----------------------------------------------------|
| `basic-flowchart`            | `4` `visLORouteFlowchartNS`                 | `1` `visPLOPlaceCompactDR`       | `1` (arc)                  | `LineJumpCode` controls who jumps                  |
| `cross-functional-flowchart` | `4`                                         | `4` `visPLOPlaceLeftToRight`     | `1`                        | per-lane ordering                                  |
| `bpmn-2-0`                   | `4`                                         | `4`                              | `2` (gap)                  | rule set rejects cross-pool sequence flows         |
| `org-chart`                  | `9` `visLORouteOrgNS`                       | `3` `visPLOPlaceTopToBottom`     | `1`                        | `OrgChartAutoSize=TRUE` page-level                 |
| `brainstorming`              | `8` `visLORouteRadial`                      | `5` `visPLOPlaceCircular`        | n/a                        | tree from Main topic outward                       |
| `mind-map`                   | `8`                                         | `5`                              | n/a                        | `AvenueSizeX=AvenueSizeY=0.25 in`                  |
| `basic-network` / `detailed` | `3` `visLORouteNetwork`                     | `0`                              | `1`                        | bus / mesh routing                                 |
| `rack-diagram`               | `0` `visLORouteRightAngle`                  | `3`                              | n/a                        | list-container snap math, no auto-route            |
| `aws/azure/gcp-architecture` | `0`                                         | `0`                              | n/a                        | manual placement; container hierarchy enforces ARM |
| `uml-class`                  | `0`                                         | `0`                              | `1`                        | manual; right-angle Generalization arrows          |
| `uml-sequence`               | `0`                                         | `0`                              | n/a                        | dates handled by Combined fragment list container  |
| `uml-activity`               | `4`                                         | `1`                              | `1`                        | inherits flowchart layout                          |
| `uml-state-machine`          | `0`                                         | `0`                              | `1`                        | manual transition placement                        |
| `dfd`                        | `2` `visLORouteCenterToCenter`              | `0`                              | `1`                        | level-0 / level-1 stacks                           |
| `erd`                        | `0`                                         | `0`                              | `1`                        | manual; entity reflow via `Layout` only            |
| `pfd` / `pid`                | `0`                                         | `0`                              | `2` (gap) / `1` (arc)      | page-level `User.PipeJumps` decides crossings      |
| `basic-electrical` / `logic` | `0`                                         | `0`                              | `1`                        | `Wire, crossover` master draws hop                 |
| `hvac`                       | `0`                                         | `0`                              | n/a                        | duct routing manual; flow balance via add-on       |
| `floor-plan` / `office`      | `0`                                         | `0`                              | n/a                        | walls auto-trim via Building Plan add-on, no auto-route |
| `gantt-chart`                | `0`                                         | `3`                              | n/a                        | `Page.GanttChart` owns layout                      |
| `pert-chart`                 | `0`                                         | `4`                              | `1`                        | critical-edge auto-coloring per Slack=0            |
| `timeline`                   | `0`                                         | `0`                              | n/a                        | PinX glue formulas place markers along timeline    |
| `swot`                       | `0`                                         | `0`                              | n/a                        | 2x2 list container                                 |
| `balanced-scorecard`         | `0`                                         | `3`                              | n/a                        | four horizontal perspective bands                  |
| `strategy-map`               | `4`                                         | `3`                              | `1`                        | typed cause-effect edges                           |
| `value-stream-map`           | `0`                                         | `4`                              | n/a                        | left-to-right process boxes; sawtooth at bottom    |
| `cause-effect-fishbone`      | `0`                                         | `0`                              | n/a                        | `User.BoneAngle` toggles top/bottom bones          |
| `sipoc`                      | `0`                                         | `4`                              | n/a                        | five horizontal list-container columns             |
| `fmea-grid`                  | `0`                                         | `3`                              | n/a                        | tabular grid; row-by-row drop                      |

---

## 13. Theme Variants — Per Family Defaults

Visio document themes are applied with `Document.SetTheme(<name>)` and
`Document.SetThemeVariant(<1..4>)`. The variant index controls the
colour palette only; geometry stays constant.

| family          | base theme    | default variant | rationale                                            |
|-----------------|---------------|-----------------|------------------------------------------------------|
| flowchart       | `Office`      | `1` (blue)      | flowchart shapes default to blue fills                |
| brainstorming   | `Office`      | `3` (green)     | brainstorming shipping palette                        |
| org chart       | `Office`      | `1`             | corporate blue                                        |
| network         | `Office`      | `2` (grey)      | iconographic / vendor-neutral                        |
| cloud (Azure)   | `Azure`       | `1`             | matches Azure Public Symbol Set hue                   |
| cloud (AWS)     | `Office`      | `4` (orange)    | matches AWS service-icon orange                       |
| software (UML)  | `Office`      | `1`             | classic UML black-on-white with blue accents          |
| engineering     | `Office`      | `1`             | engineering reference variants ship neutral palette   |
| floor plan      | `Office`      | `1`             | architectural neutral                                 |
| schedule        | `Office`      | `1`             | Gantt / PERT default blue task bars                   |
| business        | `Office`      | varies          | SWOT/BSC/Strategy use 4 quadrant colours; Lean uses VSM-icon palette |

The default theme for *new* drawings is `Office` variant `1`. Override
with `ActiveDocument.SetTheme "Slate"` (or any of `Whisp`, `Linear`,
`Integral`, `Daybreak`, `Parallel`, `Sequence`, `Office`).

---

## 14. Builder Lookup Patterns

| step                         | API                                                                                                   |
|------------------------------|-------------------------------------------------------------------------------------------------------|
| Resolve template path        | `Application.GetBuiltInTemplateFile(enum, VisMeasurementSystem)`; fallback to `Application.TemplatePaths` walk |
| Mount docked stencil         | `Application.Documents.OpenEx(<.VSSX>, 64 + 2 + 256)` (`visOpenHidden + visOpenRO + visOpenDocked`)    |
| Discover masters             | iterate `Document.Masters` where `Document.Type == visTypeStencil` (`2`); use `Master.NameU` for matching |
| Drop a master                | `Page.Drop(Master, x, y)`, `Page.DropConnected(Master, src, place, conn)`, `Page.DropMany(masters, xy)` |
| Set page layout              | `Page.PageSheet.Cells("RouteStyle"|"PlaceStyle"|"LineJumpStyle"|"AvenueSizeX"|"AvenueSizeY").FormulaU` then `Page.Layout` |
| Add swimlane / phase         | `Shape.ContainerProperties.AddSwimlane(idx)` / `AddPhase(idx)` on a list container                    |
| Add list-row member          | `Shape.ContainerProperties.AddListMember(master, idx)` (UML class compartments, BPMN combined fragment, ERD column rows) |
| Add data field cell          | `Shape.AddNamedRow(visSectionUser=242 / visSectionProp=243, name, visTagDefault=0)`                   |
| Validate                     | `Document.Validation.RuleSets.ItemU(<name>).Enabled = True`; `Document.Validation.ValidateAll`; iterate `Document.Validation.Issues` |
| Apply theme                  | `Document.SetTheme("Office")`; `Document.SetThemeVariant(1..4)`                                        |
| Drop a Gantt chart           | `Page.DropGanttChart(beginDate, endDate, VisGanttChartTimeScale)` returns `GanttChart`                |
| Add tasks                    | `gc.Tasks.Add(visTaskBar=1)` / `visTaskMilestone=2` / `visTaskSummary=3`; `Tasks.AddBefore(idx)` / `AddAfter(idx)` |
| Link tasks                   | `gc.Tasks.Link(predID, succID, VisGCLinkType)` (`0=FS`, `1=SS`, `2=FF`, `3=SF`)                       |
| Force-add a member           | `Shape.ContainerProperties.AddMember(child, visMemberAddNormal=0)` (rack equipment, BPMN pool members) |
| Resolve glue                 | `Shape.Cells("BeginX"|"EndX").GlueTo(target.Cells("PinX"|"Connections.<row>.X"))`                     |
| Discover add-ons             | iterate `Application.Addons`; invoke via `Application.Addons.ItemU(<name>).Run("/cmd=...")` (`BUILDING PLAN`, `PROCESSENG`, `ELECTRICAL`, `HVAC`, `OrgC`, `Layout`, `VisRpt`) |

---

## 15. Diagram-Type Coverage Summary

| family count | diagrams catalogued |
|--------------|---------------------|
| flowchart    | 6 (`basic-flowchart`, `cross-functional-flowchart`, `workflow-diagram`, `bpmn-2-0`, `epc`, `audit-diagram`) |
| brainstorm   | 2 (`brainstorming`, `mind-map`) |
| org chart    | 1 (`org-chart`) |
| network/cloud| 8 (`basic-network`, `detailed-network`, `rack-diagram`, `active-directory`, `aws-architecture`, `azure-architecture`, `gcp-architecture`, `cisco-network`) |
| software     | 12 (`uml-class`, `uml-sequence`, `uml-activity`, `uml-use-case`, `uml-state-machine`, `uml-component`, `uml-deployment`, `uml-object`, `uml-communication`, `uml-package`, `uml-profile`, `dfd`, `erd`) |
| engineering  | 6 (`basic-electrical`, `logic-gate`, `pfd`, `pid`, `hvac`, `plumbing`) |
| floor plan   | 8 (`floor-plan`, `office-layout`, `home-plan`, `site-plan`, `reflected-ceiling-plan`, `electrical-telecom-plan`, `plant-layout`, `security-access-plan`) |
| schedule     | 4 (`calendar`, `gantt-chart`, `pert-chart`, `timeline`) |
| business     | 12 (`swot`, `balanced-scorecard`, `strategy-map`, `marketing-charts`, `itil-diagram`, `six-sigma`, `cause-effect-fishbone`, `value-stream-map`, `tqm`, `fmea-grid`, `sipoc`, `functional-block-diagram`) |

**Total: 59 diagram types**, with explicit `Master.NameU` /
`User.<…>` / `Prop.<…>` / `route_style` / `validation_rule_set`
mappings ready for builder consumption.

---

## Sources

1. `research/12-builtin-templates-catalog.md` — built-in template /
   stencil inventory, `Documents.AddEx` / `OpenEx` flag table,
   `VisBuiltInStencilTypes`, `VisOpenSaveArgs`, `VisMeasurementSystem`
   enums, page-level cell defaults (`DrawingScale`, `PageScale`,
   `RouteStyle`, `LineJumpStyle`, `DynamicsOff`).
2. `research/13-flowchart-bpmn-family.md` — Basic Flowchart /
   Cross-Functional Flowchart / BPMN 2.0 deep reference,
   `ContainerProperties.AddSwimlane` / `AddPhase`, BPMN polymorphism
   via `User.BpmnTaskType` / `User.BpmnEventType` /
   `User.BpmnEventTrigger` / `User.BpmnGatewayType`, validation rule
   names.
3. `research/14-uml-software-family.md` — eleven UML stencils, ERD
   masters, `Prop.Visibility` / `Prop.IsAbstract` / `Prop.IsStatic`
   triple, Crow's Foot cardinalities, the 2013 reverse-engineering
   removal wall.
4. `research/15-network-cloud-family.md` — Basic / Detailed / Rack
   stencils, Active Directory masters, Azure / AWS / GCP / Cisco
   icon-pack inventories, `User.RUSize` / `User.RackNumbering` /
   `User.RUStart` rack math, `EquipmentNumbering` add-on.
5. `research/16-floorplan-engineering-family.md` — Wall / Door /
   Window / Space master cells, `BUILDING PLAN` add-on choreography,
   ISA-5.1 instrument balloon `User.MountType` matrix, IEEE 315
   `Prop.RefDes` conventions, HVAC duct typing, Plumbing fixture
   units.
6. `research/17-business-schedule-family.md` — SWOT / BSC /
   Strategy Map / ITIL / Six Sigma / Lean VSM masters, FMEA `User.RPN`
   computation, `Page.DropGanttChart` and `GanttChart` / `Tasks` /
   `Task` object model, `VisGCLinkType` and `VisTimeUnit` enums,
   Timeline `User.MilestoneDate` PinX glue formulas.

