---
name: kb-memory
description: Store durable, reusable knowledge with the bundled kb-mcp HTTP client script. Use when a stable process, configuration, interface, pitfall, or decision should be saved for future work, or when the user asks to remember reusable project knowledge.
---

# KB Memory

Use this skill for durable reusable knowledge, not routine chat logging. This skill does not require `kb-mcp` to be registered as a global host MCP server; use `scripts/kb_memory_client.py` to configure and call the MCP HTTP endpoint directly.

## Setup

Create the ignored local config file on first use:

```bash
python kb-memory/scripts/kb_memory_client.py init-config
```

The default config path is `kb-memory/config.local.json`. It is local-only and must not be committed. Edit it with the kb-mcp HTTP URL and auth header, or use environment variables:

- `KB_MEMORY_MCP_URL`
- `KB_MEMORY_MCP_AUTHORIZATION`
- `KB_MEMORY_MCP_BEARER_TOKEN`
- `KB_MEMORY_MCP_HEADERS_JSON`
- `KB_MEMORY_CONFIG`

Check configuration without exposing secrets:

```bash
python kb-memory/scripts/kb_memory_client.py doctor
python kb-memory/scripts/kb_memory_client.py doctor --connect
```

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

## Tool Workflow

1. Run `doctor` when configuration is missing, newly created, or suspected to differ across macOS, Linux, and Windows.
2. Run `tools` to inspect the available kb-mcp tool names and schemas before calling a write/update tool.
3. Call the chosen tool with a JSON object:

```bash
python kb-memory/scripts/kb_memory_client.py tools
python kb-memory/scripts/kb_memory_client.py call <tool-name> --arguments-file entry.json
```

Prefer `--arguments-file` or stdin for large entries so shell quoting does not corrupt JSON.

If `kb-mcp` is unavailable, do not block the user. Note the skipped write in chat history when chat history logging is available.
