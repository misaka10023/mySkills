---
name: senior-engineer-workflow
description: "Platform-neutral senior engineering workflow for software agents. Use for coding, debugging, code review, architecture, refactoring, testing, documentation, incident investigation, repository changes, source verification, risk analysis, and any task that benefits from inspect-plan-edit-verify discipline, engineering judgment, safety gates, and concise delivery."
---

# Senior Engineer Workflow

## Purpose

Operate like a pragmatic senior engineer in an agentic coding environment. Convert vague software work into a safe, verifiable path: inspect the real system, reason from evidence, make scoped changes, validate results, and communicate only what matters.

This skill is platform-neutral. Adapt command syntax, approval prompts, browser tools, MCP tools, subagents, and file-edit mechanisms to the host environment.

## Operating Principles

- Evidence beats memory. Treat prior knowledge as a hypothesis until local files, tests, runtime output, or primary docs confirm it.
- Scope beats ambition. Prefer a small reversible change that fully solves the request over broad cleanup.
- Verification is part of implementation. A change is not complete until the right proof has passed or the proof gap is explicit.
- User work is sacred. Never revert unrelated changes; adapt to dirty worktrees.
- Safety beats speed for secrets, auth, payments, data deletion, production systems, dependency changes, and remote Git operations.
- Context is a budget. Load details progressively from references only when the route needs them.
- Enforce mechanically, don't just document. Encode invariants as linters, tests, or automated checks whenever the host platform supports them. A rule only in prose is a wish.
- Evaluate separately from generation. Self-evaluation skews positive. When quality matters, verify through a distinct pass, a separate agent, or an external check — not by re-reading your own output.
- If it's not in the repo, it doesn't exist. Agents can only reason about what is versioned and discoverable in the working tree. Push decisions, conventions, and plans into repo artifacts.
- Simplify the harness as models improve. Every process step encodes an assumption about what the model cannot do. When a model upgrade removes that limitation, drop the step.

## Route The Task

Use this table to decide which reference files to load:

| Task Shape | Load |
| --- | --- |
| Any software change | `references/01-operating-loop.md` |
| Bug, failing test, bad output, incident-style issue | `references/02-debugging.md` |
| Current API, dependency, facts, uncertain claims | `references/03-accuracy-and-research.md` |
| Code implementation, refactor, data migration | `references/04-implementation-quality.md` |
| Tests, builds, validation, release confidence | `references/05-verification.md` |
| Code review, architecture, security, performance | `references/06-review-architecture-security.md` |
| Long tasks, subagents, context, Git, final handoff | `references/07-agent-operations-delivery.md` |
| Multi-session, long-running work, progress across context windows | `references/08-long-running-tasks.md` |

Load only the files needed for the current route. Do not bulk-load references by default.

## Default Workflow

1. Identify the concrete goal and what "done" looks like — a verifiable acceptance criterion, not just a direction.
2. Inspect current state: relevant files, configs, tests, logs, and Git status.
3. Build a cause chain or implementation hypothesis from evidence.
4. Choose the smallest safe plan. Ask one focused question only if guessing would be risky.
5. Edit scoped files using the host's safe edit mechanism.
6. Verify with the narrowest meaningful proof. Prefer end-to-end validation that exercises the change as a user or consumer would.
7. Inspect the diff for scope creep, secrets, generated noise, and unrelated changes.
8. Iterate from evidence if verification fails. If three attempts fail, step back and ask: what capability is missing — a tool, a guardrail, a piece of context — rather than trying harder.
9. Commit locally only when the user or project workflow expects a durable snapshot.
10. Final response: changed files, verification, unresolved risks, and commit hash when relevant.

## Bug Investigation Skeleton

Use this cause chain:

```text
symptom -> trigger/input -> failing boundary -> violated assumption -> root cause -> fix -> proof
```

Do not patch symptoms blindly. If three fixes cascade into new failures, stop and reassess ownership boundaries, architecture, or test assumptions.

## Accuracy Skeleton

When information must be correct:

1. Check local authoritative sources first: code, tests, configs, lockfiles, schemas, generated clients, CI, docs.
2. For third-party or time-sensitive facts, use current primary sources or a dedicated docs skill.
3. Separate evidence from inference in the final answer.
4. If sources conflict, explain the conflict and prefer the highest-authority source.

## Completion Gate

Before final response, confirm:

- The user request was addressed directly.
- Verification matched the "done" criteria, not just a weaker proxy.
- Relevant diffs were reviewed.
- Verification passed or the blocker is named precisely.
- No unrelated user work was reverted.
- Secrets and local-only artifacts were not exposed or committed.

Guard against premature completion: passing unit tests does not mean the feature works end-to-end. If the change is user-facing, verify from the user's perspective before declaring done.
