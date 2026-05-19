# Agent Operations And Delivery

## Context Management

- Keep searches narrow.
- Summarize large findings instead of loading every file.
- Load reference files only when their route applies.
- If repeated failed attempts pollute the session, summarize durable facts and restart from a cleaner context when supported.

## Delegation

Use helper agents only when:

- the host supports them,
- the task is bounded,
- the write set is separate or the task is read-only,
- the main task can continue without waiting.

Do not delegate the immediate blocker. Give helpers explicit scope, expected output, and files they may touch.

## Git And Delivery

- Check status before and after edits.
- Never revert unrelated user changes.
- Stage only task files.
- Commit locally only when requested or when project workflow expects durable snapshots.
- Never push, pull, fetch, or edit remotes unless explicitly requested.
- Do not commit secrets, `.env*`, logs, dependency folders, chat history, private screenshots, or bulk generated output unless explicitly requested.

## Final Response

Keep final responses compact:

- changed files or behavior,
- verification run,
- commit hash if created,
- relevant blockers or residual risk.

Avoid long process narration unless requested.
