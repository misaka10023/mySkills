# visio-master

> A multi-role authorship pipeline that converts source documents
> (PDF / DOCX / URL / Markdown / direct prose) into hand-authored
> Microsoft Visio drawings (`.vsdx`). Each Visio Page is written one
> at a time by the host LLM agent so that cross-page visual
> consistency lives in working memory, the same way `ppt-master`
> hand-authors SVG slides for PowerPoint.

`visio-master` is the Visio sibling of the
[`ppt-master`](../../.agents/skills/ppt-master/) skill. The two share
the same disciplines: Eight Confirmations as a single BLOCKING gate,
a parseable lock file (`diagram_lock.md`) re-read per page, sequential
hand-authored pages with no script-driven batch generation, and a
serial post-processing pipeline.

For the full execution pipeline, read [`SKILL.md`](./SKILL.md).
This README only covers what the skill is, what it needs, and how to
install it.

---

## 1. What it does

Given a source — a PDF, DOCX, web page, Markdown file, or a topic the
user describes in conversation — `visio-master`:

1. Ingests the source and normalises it to Markdown.
2. Plans the drawing as the **Architect** role: canvas size, diagram
   types, audience, communication mode, visual style, theme / color
   palette, stencil set, layout / connector routing, and optional
   data linking. The plan is presented to the user as the
   **Eight Confirmations** bundle. Architect commits the agreed plan
   to a human-readable `diagram_spec.md` and a parseable
   `diagram_lock.md`.
3. Authors one Visio Page at a time as the **Drafter** role,
   re-reading `diagram_lock.md` before every page to resist context
   drift on long drawings. Pages land in
   `<project>/pages/<NN>_<name>.vsdx-page.xml`.
4. Applies theme, layers, container/list discipline, and optional
   data-graphics binding as the **Stylist** role.
5. Lints the drawing with `vsdx_quality_checker.py`, then runs the
   three-step post-processing pipeline
   (`total_md_split.py` → `finalize_vsdx.py` → `vsdx_export.py`) to
   produce the final `.vsdx`.

The export script prefers the **Visio COM** path (via `pywin32`)
when a local Visio install is available, and falls back to a pure-
Python OPC/XML writer (`vsdx` + `lxml`) otherwise. An optional
`aspose.diagram` path is supported for sites with a license.

Supported diagram families include process flows, swim lanes, BPMN
2.0, flowcharts, org charts, network topologies (on-prem / Azure /
AWS), entity-relationship diagrams, UML, state machines, mind maps,
Venn / quadrant / matrix layouts, and `mixed` decks declared per
page.

---

## 2. Prerequisites

### 2.1 Required

- **Python** 3.10 or newer.
- **Git** (the skill is consumed as a git-tracked directory).
- A Claude Code or Codex CLI environment that supports skill
  installation. See section 3 for installation.

### 2.2 Recommended

- **Microsoft Visio** (Standard or Professional) on Windows.
  When installed, `vsdx_export.py` automatically uses the COM path
  for highest fidelity. Without Visio the skill still works through
  the pure-Python fallback, with the documented limitations
  (Container / List boundary recomputation is approximated; connector
  routing is straight-line unless an external routing engine is
  configured).
- **LibreOffice Draw** (`soffice`) for headless preview rendering on
  non-Windows hosts.
- **Node.js** 18+ if you opt into `dagre` / `elkjs` connector routing
  in fallback mode.

### 2.3 Optional credentials

Image-generation and image-search workflows read API keys from a
project-local `.env`. Copy `.env.example` and populate the keys you
intend to use. See [`docs/faq.md`](./docs/faq.md) for the full list.

---

## 3. Installation

The skill ships as a directory. The user's global instructions
require project-local skills to live in `.agents/skills/` with
`.claude/skills/` exposed as a symbolic link, so installation is the
same physical layout for both Claude Code and Codex CLI; only the
discovery path differs.

### 3.1 Layout convention

```
<repo-root>/
├── .agents/
│   └── skills/
│       └── visio-master/        <-- the skill's real home
└── .claude/
    └── skills/  -> ../.agents/skills   <-- symlink (Claude Code reads here)
```

`Codex CLI` reads skills directly from `.agents/skills/`. `Claude
Code` reads from `.claude/skills/`. The symlink lets one copy of the
skill serve both CLIs without duplication.

### 3.2 Claude Code (Windows / macOS / Linux)

1. Place the skill at `<repo-root>/.agents/skills/visio-master/`
   (clone, copy, or `git submodule add` — whichever your repo
   policy prefers).
2. Create `.claude/skills/` as a symbolic link pointing to
   `.agents/skills/`.

   **Windows (PowerShell, run as admin or with Developer Mode on):**
   ```powershell
   New-Item -ItemType SymbolicLink -Path ".claude\skills" -Target "..\.agents\skills"
   ```

   **Windows (cmd.exe with `mklink`):**
   ```bat
   mklink /D .claude\skills ..\.agents\skills
   ```

   **macOS / Linux:**
   ```bash
   mkdir -p .claude
   ln -s ../.agents/skills .claude/skills
   ```

3. Install Python dependencies:
   ```bash
   pip install -r .agents/skills/visio-master/requirements.txt
   ```
4. Copy `.env.example` to `.env` next to the skill (or at repo root,
   whichever your project uses) and fill in any keys you need.
5. Restart Claude Code so the skill is picked up. Confirm with
   `/skills` (or your environment's equivalent) that `visio-master`
   appears.

### 3.3 Codex CLI

1. Place the skill at `<repo-root>/.agents/skills/visio-master/`
   exactly as for Claude Code.
2. Skip the symlink step unless you also use Claude Code in the same
   repo. Codex CLI reads `.agents/skills/` directly.
3. Install dependencies:
   ```bash
   pip install -r .agents/skills/visio-master/requirements.txt
   ```
4. Copy `.env.example` to `.env` and populate the keys you need.
5. Invoke through your usual Codex skill-discovery command. The skill
   surfaces as `visio-master` and follows the workflow documented in
   [`SKILL.md`](./SKILL.md).

### 3.4 Verifying the install

A minimal smoke test:

```bash
cd <repo-root>
python .agents/skills/visio-master/scripts/project_manager.py init \
  --project-name smoke-test \
  --canvas a4-landscape
python .agents/skills/visio-master/scripts/vsdx_quality_checker.py smoke-test
```

Expected: the project scaffold is created and the quality checker
exits `0` against the empty project. See [`docs/faq.md`](./docs/faq.md)
for an end-to-end Markdown-to-`.vsdx` example.

---

## 4. Where to go next

- [`SKILL.md`](./SKILL.md) — the canonical pipeline. Start here for
  any actual drawing.
- [`references/`](./references/) — role definitions (Architect,
  Drafter, Stylist, Image_Generator, Image_Searcher,
  Template_Designer), shared standards, the Visio Pages XML
  authoring guide, the canvas catalog, the connector reference, and
  the mode / visual-style preset catalogs.
- [`scripts/`](./scripts/) — entry-point Python scripts. Each accepts
  `--help`. See [`scripts/README.md`](./scripts/README.md) for the
  helper-module map.
- [`templates/`](./templates/) — `diagram_spec_reference.md`,
  `diagram_lock_reference.md`, plus the page-layout / theme /
  diagram-template / stencil libraries.
- [`workflows/`](./workflows/) — standalone workflows callable from
  `SKILL.md` or directly: `topic-research`, `template-fill-vsdx`,
  `create-page-layout`, `create-theme`, `resume-execute`,
  `verify-diagrams`, `customize-data-graphics`, `live-preview`,
  `visual-review`, `import-existing-vsdx`, `export-pdf`,
  `audit-stencil-licensing`.
- [`docs/faq.md`](./docs/faq.md) — known issues, fallback-mode
  limitations, and remediation tips.

---

## 5. License and stencil sourcing

The skill itself follows the host repository's license. Stencils
shipped under `templates/stencils/` are sourced from license-clear
material (Microsoft's published flowchart shapes for the default
`flowchart-basic` set). Importing third-party stencils — Cisco,
Azure, AWS, Lucid, ConceptDraw, and similar — requires running the
[`audit-stencil-licensing.md`](./workflows/audit-stencil-licensing.md)
workflow first. Bare copies from a system stencil directory are not
permitted.
