# Harness Templates

Use these templates when creating repository artifacts. Adapt paths and sections to the project; do not create unused files.

## Skill-Packaged Harness

Use a skill as the required agent-facing package for every newly created harness:

```text
.agents/
`-- skills/
    `-- <skill-name>/
        |-- SKILL.md
        |-- agents/
        |   `-- openai.yaml
        |-- scripts/       # deterministic operations, only when needed
        |-- references/    # detailed protocols and schemas loaded on demand
        |-- assets/        # output templates, only when needed
        `-- evals/         # realistic smoke prompts, fixtures, expectations
.claude/
`-- skills                # POSIX symlink or Windows Junction
```

Install once under `.agents/skills`; expose the same directory at `.claude/skills` for Claude Code compatibility. Do not copy the skill into both locations.

Before running either platform command, require every existing `.agents`, `.agents/skills`, and `.claude` parent to be a real directory inside the project, not a symlink, Junction, or other reparse point. Create absent parents inside the project and validate them again before linking. Also verify that `.agents/skills/<skill-name>` is absent or belongs to the harness being updated. The only permitted directory link is `.claude/skills`; stop on a parent-link, file, broken-link, wrong-target, or ownership conflict.

On POSIX systems, create the link from the project root after confirming the destination does not already contain user data:

```bash
mkdir -p .agents/skills .claude
ln -s ../.agents/skills .claude/skills
```

On Windows PowerShell, use a directory Junction after the same conflict and boundary checks. `Junction` accepts an absolute target and does not require Developer Mode or administrator privileges:

```powershell
New-Item -ItemType Directory -Force .agents\skills, .claude | Out-Null
$agentsSkills = (Resolve-Path .agents\skills).Path
New-Item -ItemType Junction -Path .claude\skills -Target $agentsSkills | Out-Null
$link = Get-Item -Force .claude\skills
$linkTarget = [System.IO.Path]::GetFullPath([string]$link.Target)
if ($link.LinkType -ne "Junction" -or
    $linkTarget -ne $agentsSkills) {
  throw "Claude skills junction does not resolve to .agents/skills"
}
```

If `.claude/skills` already exists and is not the expected directory link, stop for explicit migration approval. Do not replace it or fall back to a second copy. Treat the link as an ignored local installation artifact on both platforms; a Windows Junction also stores an absolute target and must be recreated after moving or cloning the repository. Verify that both hosts resolve the same `SKILL.md`, then check `git check-ignore` and `git status`: canonical `.agents/skills` content must remain versionable and `.claude/skills` must remain ignored and reproducible from the install steps.

Start `SKILL.md` with this shape and replace every placeholder:

```markdown
---
name: <skill-name>
description: <What the harness enables and concrete user contexts that should trigger it.>
---

# <Harness Display Name>

State the outcome this harness produces and its central operating principle.

## Route The Task

Classify request variants and point each variant to only the resources it needs.

## Workflow

1. Inspect inputs and authoritative state.
2. Define observable success and safety boundaries.
3. Execute the next bounded action using bundled scripts or existing project tools.
4. Verify environment outcomes.
5. Record durable state and decide whether to continue, stop, or request approval.

## Resources

- Read `references/<topic>.md` when <specific condition>.
- Run `scripts/<operation>` when <specific condition>.
- Use `assets/<template>` when producing <specific artifact>.

## Completion Gate

List externally verifiable conditions for success, safety, state, and reporting.
```

The skill entrypoint should route and govern execution. Keep long schemas, domain detail, citations, and runbooks in `references/`; keep deterministic behavior in `scripts/`; reuse existing runtime code rather than copying it into the skill. Put essential behavior in host-neutral resources, not only in `agents/openai.yaml` or Claude-specific hooks.

## HARNESS.md

```markdown
# <Harness Name>

## Goal

## Non-goals

## Harness Type

## Agent Loop

Describe the loop as:

1. Gather context.
2. Plan the next bounded action.
3. Call tools or modify the environment.
4. Observe results.
5. Verify against environment outcomes.
6. Update trace and state.
7. Stop, ask for approval, or continue.

## Context Model

- Initial context:
- Durable state:
- Handoff artifacts:
- Context compression:
- Context provenance:

## Tools

| Tool | Purpose | Inputs | Output Shape | Failure Mode | Recovery |
| --- | --- | --- | --- | --- | --- |

## State and Memory

## Permissions

- Read scope:
- Write scope:
- Network:
- Secrets:
- Process execution:
- Destructive actions:
- Human approval:

## Trace and Observability

## Verification

## Eval Suite

## Human Gates

## Failure Modes

| Failure Mode | Harness Control | Verification |
| --- | --- | --- |

## Operating Runbook

## Maintenance and Ablation
```

## Task Schema

```yaml
id: example-task-001
title: "Short task title"
goal: "Concrete outcome the agent must produce."
inputs:
  repo_path: "."
  issue: "Problem statement or workflow request."
success_criteria:
  - "Environment outcome that proves success"
constraints:
  write_scope:
    - "src/"
    - "tests/"
  forbidden:
    - "Do not expose secrets"
verification:
  commands:
    - "pytest tests/test_target.py"
trace:
  required_fields:
    - "task_id"
    - "tool_calls"
    - "verification"
handoff:
  update_files:
    - "tasks/example-task-001/RESULTS.md"
```

## Tool Manifest

```yaml
tools:
  - name: "repo_search"
    purpose: "Find code and docs in the repository."
    safe_by_default: true
    requires_approval: false
    inputs:
      query: "Search phrase or regex"
    returns: "Matching paths and short snippets"
    token_controls:
      default_limit: 20
      supports_pagination: true
    actionable_errors:
      - "No matches: try broader terms or inspect known entrypoints."
    eval_tasks:
      - "Find the config loader for a known setting."
```

## Trace Schema

```json
{
  "task_id": "string",
  "turn_id": "string",
  "step_id": "string",
  "actor": "user|agent|tool|human_reviewer",
  "input_summary": "string",
  "context_refs": ["string"],
  "tool_name": "string|null",
  "tool_args_redacted": {},
  "tool_result_summary": "string|null",
  "approval_decision": "allow|deny|not_required|null",
  "environment_delta": "string|null",
  "verification": {
    "status": "pass|fail|blocked|not_run",
    "evidence": "string"
  },
  "errors": ["string"],
  "timestamp": "ISO-8601"
}
```

## Eval README

```markdown
# Harness Eval Suite

## Purpose

## What This Suite Measures

## What This Suite Does Not Measure

## Environment Setup

## Running Smoke Evals

## Running Full Evals

## Grader Contract

## Metrics

- task_success_rate
- regression_pass_rate
- tool_call_count
- token_cost
- latency
- human_intervention_rate
- safety_block_rate

## Adding A New Eval

Each eval must include:

- task input
- fixed environment or fixture
- success criteria
- grader
- expected trace fields
- regression command
```

## Long-Running Progress Log

```markdown
# Progress

## Current State

## Completed

## In Progress

## Blocked

## Verification

## Known Risks

## Next Session Instructions
```
