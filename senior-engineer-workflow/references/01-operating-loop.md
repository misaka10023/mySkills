# Operating Loop

## Intake

1. Parse the newest user request as authoritative.
2. Classify the task: change, bug, review, architecture, research, explanation, operational support, or long-running task spanning multiple sessions.
3. Define "done" as a verifiable acceptance criterion. Prefer a concrete check (test passes, output matches, endpoint responds) over a vague direction. When the task is complex, write down the done-condition before starting — it catches scope drift earlier than any prompt change.
4. Ask only when a wrong assumption could cause data loss, security risk, broad rework, or wrong architecture.

## Inspect

Start with cheap targeted evidence:

- File map with fast search.
- Git status and local instructions.
- Relevant implementation, tests, configs, lockfiles, generated clients, schemas, and CI.
- Recent failing command output or logs if provided.

Avoid reading large files in full when a search or line range answers the question.

## Plan

Use the smallest safe plan that can satisfy the request. For non-trivial work, name:

- files or modules likely to change,
- behavior to preserve,
- verification command,
- risk or assumption.

Do not produce a long plan when the next step is obvious inspection or a small edit.

After repeated failures, step back and ask: what capability is missing? A tool the agent cannot access? A guardrail not encoded? A piece of context not in the repo? Fix the harness gap, then retry. Do not retry the same approach with the same constraints.

As the underlying model improves, re-examine the harness. Every process step assumes the model cannot do something. When that assumption becomes stale, remove the step rather than letting scaffolding accumulate.

## Execute

- Edit only targeted files.
- Preserve existing patterns and local abstractions.
- Avoid unrelated formatting churn.
- Keep temporary diagnostics out of final changes unless useful.
- If unexpected user changes appear, treat them as intentional and work around them.

## Review Diff

Before handoff, inspect for:

- unrelated files,
- generated noise,
- secrets or local paths,
- behavior beyond the request,
- missing tests or docs.

## Handoff

Final response should include what changed, how it was verified, unresolved blockers, and commit hash when a commit exists.
