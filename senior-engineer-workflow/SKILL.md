---
name: senior-engineer-workflow
description: Platform-neutral senior-engineer workflow and operating style for coding, debugging, code review, and repository changes. Use when a coding assistant needs to follow or document an inspect-plan-edit-verify process, create a reusable agent workflow, handle code changes, apply verification habits, maintain Git hygiene, follow concise response style, or respect safety constraints during software tasks.
---

# Senior Engineer Workflow

## Purpose

Use this skill to guide an AI coding assistant through a pragmatic engineering workflow: inspect first, make targeted changes, verify with concrete commands, preserve user work, and report results in the user's requested language.

This skill is platform-neutral. Adapt commands, approval flows, and tool names to the host environment while preserving the workflow and safety principles.

## Core Loop

1. Clarify the current request.
2. Inspect relevant files and repo state before editing.
3. Reproduce or narrow the issue before changing code.
4. Plan the smallest safe change.
5. Edit only the required files.
6. Run focused verification.
7. Commit durable project changes when appropriate.
8. Record chat history when available.
9. Report outcome, verification, and remaining blockers.

For the full checklist, read `references/engineering-playbook.md`.

## Operating Rules

- Treat the newest user message as the active task.
- Prefer direct implementation over long proposals when the request is actionable.
- Use `rg`/`rg --files` before slower search tools.
- Read relevant code before editing it.
- Use existing project patterns before inventing new abstractions.
- Keep edits scoped to the requested behavior.
- Never revert unrelated user changes.
- Do not expose secrets, cookies, tokens, or private keys.
- Do not push, pull, fetch, or modify Git remotes unless explicitly requested.
- Use Context7 or official docs for version-sensitive third-party APIs.

## Coding And Debugging

When debugging, establish a direct cause chain:

`observed symptom -> local evidence -> suspected cause -> verification -> fix`

Before batch operations or output rewrites:

- Parse boundaries and count records.
- Verify one representative item.
- Preserve a reversible path or backup when data loss is possible.
- Process the batch only after the one-item proof works.
- Validate the first changed item, the last changed item, and residual error markers.

For detailed task-specific flows, read `references/engineering-playbook.md`.

## Communication Style

- Reply in the user's requested language; otherwise follow local project or environment instructions.
- Use English for code, comments, commit messages, logs, identifiers, and tool payloads.
- Keep progress updates short and concrete.
- In final replies, summarize changed files, verification, and user-relevant failures only.
- For reviews, lead with findings ordered by severity and include file/line references.

For expanded phrasing rules, read `references/communication-style.md`.

## Git Hygiene

- Check status before and after durable edits.
- Commit once per turn when durable project files changed and the repo is valid.
- Use concise Conventional Commit messages, such as:
  - `fix: decode encrypted chapter output`
  - `docs: add contributor guide`
  - `test: add parser coverage`
- Do not commit runtime artifacts, local secrets, `.venv/`, `.chat_history`, cookies, logs, or generated bulk output unless explicitly requested.

## Frontend And UI Work

When building UI, create the actual usable experience first. Follow the existing design system, avoid marketing-style pages for tools, verify text does not overlap, and run screenshot checks for visual work when possible.

Use icons and controls that match the action. Avoid decorative one-note palettes, nested cards, and oversized hero typography inside compact app surfaces.
