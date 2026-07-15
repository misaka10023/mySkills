# Stale Schema Agent Fixture

Treat this file as the complete repository snapshot for the evaluation.

## Existing Files

- `tools/run_migration.py` owns migration execution and must remain the runtime source of truth.
- `source/schema.yaml` contains the canonical schema definition.
- `generated/schema.sql` is committed generated output.
- `tests/test_migration.py` checks migration execution but does not compare generated output with the source schema.
- `docs/agent.md` tells the coding agent to run `python tools/run_migration.py` and report completion.

## Observed Failure

The agent reports success after `tests/test_migration.py` passes, even when `generated/schema.sql` was not regenerated after `source/schema.yaml` changed.

## Constraints

- Keep `tools/run_migration.py` as the execution owner; do not copy or move it into another package.
- The harness must be usable from both Codex and Claude Code.
- Do not maintain duplicate workflow instructions or runtime implementations for the two hosts.
- The regression check must be runnable in a clean fixture.
