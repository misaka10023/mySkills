---
name: chat-history-recorder
description: Record every conversation turn into local history files using chat-history-recorder-mcp. Use before final user-facing responses, when a turn must be logged, when the user asks about previous work, or when a stop hook reports that chat history recording is required.
---

# Chat History Recorder

Use this skill when host instructions require conversation logging or when the user asks about prior work.

## Workflow

1. On first use in a session, call `get_config_info()` to inspect logging configuration.
2. Before the final user-facing response, call `record_chat_history` exactly once for the current turn.
3. Fill fields from the live MCP schema:
   - `user_input`: original user request for the turn.
   - `system_output`: 2-6 sentences summarizing actions, decisions, and results.
   - `project_dir`: current project root.
   - `file_operations`: compact summary such as `edited: src/app.py; mcp: context7`.
   - `llm_name`: current model name when available.
4. Do not store raw secrets, tokens, passwords, cookies, private keys, or large raw outputs. Redact sensitive values.
5. If logging fails, retry at most once only when the operation is idempotent or de-duplicated. Otherwise continue.

## Stop Hook Recovery

If a stop hook reports that chat history recording was missed, record the turn immediately with the same field rules, then continue to the final response. Do not create duplicate records for the same turn.
