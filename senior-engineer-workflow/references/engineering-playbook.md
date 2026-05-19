# Engineering Playbook

Use this reference when a task needs deeper execution detail than the main skill body.

## Debugging Checklist

1. Capture the exact failing command, route, UI action, input, or test.
2. Confirm whether the failure is deterministic, intermittent, environment-specific, or data-specific.
3. Identify the first bad boundary: input, validation, transform, persistence, network, render, cache, permission, or external service.
4. Compare with a known-good path.
5. Form one hypothesis at a time and verify it with the smallest command, test, log, or code read.
6. Fix the root cause and remove temporary probes unless they are useful diagnostics.
7. Add regression coverage when possible.
8. Re-run the failing proof and one adjacent proof.

## Accuracy Checklist

- Local code/config beats memory.
- Official docs beat blog posts for API behavior.
- Lockfiles and installed versions beat general docs for version-specific behavior.
- Runtime output beats static assumptions.
- User requirements beat inferred product preferences.
- If data is time-sensitive, verify it online or with the relevant live tool.
- If a conclusion is inferred, label it as inference.

## Implementation Checklist

- Read nearby code before editing.
- Reuse local patterns and helpers.
- Keep contract changes explicit.
- Prefer typed/structured interfaces when available.
- Validate inputs at trust boundaries.
- Preserve backward compatibility unless intentionally changing it.
- Avoid hidden global state and broad side effects.
- Keep comments sparse and focused on non-obvious invariants.

## Verification Matrix

| Change Type | Minimum Useful Verification |
| --- | --- |
| Documentation | Read rendered or raw Markdown; validate examples if executable |
| Unit logic | Run focused unit tests; add missing regression tests |
| Parser/transform | Test valid, invalid, empty, boundary, and real sample inputs |
| API/backend | Run route/service tests or local request; check schemas |
| Frontend/UI | Run app or component test; check screenshot/console/responsive states |
| Build/tooling | Run focused lint/type/build command |
| Data migration | Dry run or sample run; verify counts and representative records |
| Security/auth | Check authorization, input validation, secret handling, logs |

## Failure Response

When verification fails:

1. Stop broad editing.
2. Preserve the failing output.
3. Update the cause chain with the new evidence.
4. Fix the next root cause, not every visible symptom.
5. Re-run the same proof.

If three fixes cascade into new failures, reassess architecture, ownership boundaries, or test assumptions before continuing.
