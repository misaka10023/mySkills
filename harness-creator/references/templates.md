# Harness Templates

Use these templates when creating repository artifacts. Adapt paths and sections to the project; do not create unused files.

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

