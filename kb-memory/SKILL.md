---
name: kb-memory
description: Store durable, reusable knowledge with kb-mcp. Use when a stable process, configuration, interface, pitfall, or decision should be saved for future work, or when the user asks to remember reusable project knowledge.
---

# KB Memory

Use this skill for durable reusable knowledge, not routine chat logging.

## Write Criteria

Write to `kb-mcp` only when at least two are true:

- Likely reusable within one month.
- Needed as evidence or future reference.
- Source is traceable.
- Topic is clearly categorizable.
- Documents a stable process, config, interface, pitfall, or decision.

Do not write one-off chat details, temporary state, secrets, credentials, large raw outputs, or fast-expiring information unless dated and versioned.

## Entry Format

Use one topic per entry:

```text
Title:
Key points:
Steps:
Examples:
Tags:
Source:
```

Prefer updating an existing entry over creating near-duplicates. Use 1-3 tags such as `mcp`, `git`, `agent`, `debug`, or the project name.

If `kb-mcp` is unavailable, do not block the user. Note the skipped write in chat history when chat history logging is available.
