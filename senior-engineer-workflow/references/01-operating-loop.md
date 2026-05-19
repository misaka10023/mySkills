# Operating Loop

## Intake

1. Parse the newest user request as authoritative.
2. Classify the task: change, bug, review, architecture, research, explanation, or operational support.
3. Identify success criteria. If absent, infer a conservative criterion from local context.
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
