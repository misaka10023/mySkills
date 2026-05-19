# Debugging Workflow

## Cause Chain

Use this chain throughout:

```text
symptom -> trigger/input -> failing boundary -> violated assumption -> root cause -> fix -> proof
```

## Steps

1. Capture the exact failure: command, stack trace, status code, UI state, wrong output, or failing assertion.
2. Determine scope: one environment, one data shape, one route, one dependency, one browser, one account, or all cases.
3. Reproduce with the smallest available proof. If reproduction is impossible, explain why and use static evidence.
4. Trace boundaries in order: input, validation, parsing, transformation, state, persistence, network, cache, permissions, rendering, output.
5. Compare normal vs abnormal behavior.
6. Form one hypothesis at a time and verify it before editing broadly.
7. Fix the violated assumption or ownership boundary, not only the visible error.
8. Add regression coverage when feasible.
9. Re-run the failing proof and one adjacent proof.

## Common Failure Modes

- Off-by-one and empty input cases.
- Null, missing, or widened schema fields.
- Async race, stale cache, or double submit.
- Timezone and locale assumptions.
- Path, encoding, newline, and shell differences.
- Permission or auth checks applied in one layer but not another.
- Serialization mismatch across API boundaries.
- Test fixture drift from production data shape.
- Hidden dependency on environment variables or current working directory.

## When To Stop And Reframe

Stop tactical patching when:

- three attempted fixes create new failures,
- the root cause crosses unclear ownership boundaries,
- tests conflict with product requirements,
- logs indicate production data or security impact,
- the change requires a broader contract decision.
