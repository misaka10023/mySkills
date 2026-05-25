# Agent Operations And Delivery

## Context Management

- Keep searches narrow.
- Summarize large findings instead of loading every file.
- Load reference files only when their route applies.
- If repeated failed attempts pollute the session, summarize durable facts and restart from a cleaner context when supported.

## Isolation

When the host platform supports sandboxed or worktree-isolated execution:

- Make each change in an isolated environment so verification does not depend on dirty local state.
- Tear down the environment once the change is verified and merged.
- If the host does not support isolation, explicitly note dirty-worktree assumptions in verification results.

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

## Anti-Entropy

Codebases accumulate drift — duplicated patterns, stale docs, inconsistent conventions. Over time this degrades agent performance because agents replicate what they see, including uneven patterns.

- When noticing a recurring anti-pattern, encode it as a mechanical check (lint rule, CI check) rather than fixing instances one-by-one.
- If the host supports background or scheduled tasks, periodic "doc-gardening" or cleanup passes that scan for drift and open targeted fixes compound in value.
- Capture human taste once, then enforce it continuously on every line of code.

## Final Response

Keep final responses compact:

- changed files or behavior,
- verification run,
- commit hash if created,
- relevant blockers or residual risk.

Avoid long process narration unless requested.
