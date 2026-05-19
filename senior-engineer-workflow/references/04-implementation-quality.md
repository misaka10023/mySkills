# Implementation Quality

## Change Design

- Preserve public contracts unless the task requires a contract change.
- Reuse local helpers, naming, validation, error handling, and test style.
- Prefer structured parsers and framework APIs over ad hoc text manipulation.
- Keep data ownership and side effects clear.
- Make reversible changes when touching data, migrations, or generated outputs.
- Introduce abstractions only when they reduce real duplication or clarify a repeated concept.

## Code Quality Checks

Before editing, know:

- the entry point,
- the data shape,
- the trust boundary,
- the error handling path,
- the expected tests or verification path.

After editing, check:

- edge cases,
- backward compatibility,
- failure behavior,
- observability/logging impact,
- security and privacy impact,
- performance or concurrency impact.

## Refactoring Rules

- Keep behavior-preserving refactors separate from behavior changes when possible.
- Avoid broad formatting changes.
- Maintain old tests until new tests prove the same behavior.
- Do not rename or move public symbols without checking all consumers.

## Data And Migration Rules

- Count records before and after.
- Validate representative samples, first item, last item, and edge cases.
- Keep a rollback or backup path for destructive transformations.
- Never run broad destructive operations without explicit user approval and a verified target path.
