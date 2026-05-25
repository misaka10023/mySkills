# Verification

## Verification Matrix

| Change Type | Minimum Useful Proof |
| --- | --- |
| Documentation | Read raw/rendered Markdown; validate commands if executable |
| Unit logic | Focused unit test; add regression test for new behavior |
| Parser/transform | Valid, invalid, empty, boundary, and real sample inputs |
| CLI/script | Minimal sample run; verify exit code and output |
| API/backend | Focused service/route test or local request; check schema and error path |
| Frontend/UI | Run app or component; check screenshot, console, responsive layout, loading and error states. Verify as a user would — click through the flow, not just component renders. |
| Build/tooling | Smallest lint/type/build command touching the changed surface |
| Data migration | Dry run or sample run; verify counts and representative records |
| Security/auth | Authorization, validation, secret handling, logging, dependency exposure |

## End-to-End Preference

Unit tests confirm code logic. They do not confirm the feature works. Prefer a verification path that exercises the change as a consumer or user would experience it — an HTTP request, a CLI invocation, a browser interaction. If the host platform provides browser automation, screenshot tools, or observable runtime output, use them to close the gap between "the code looks right" and "the feature actually works."

## Self-Evaluation Is Unreliable

When asked to evaluate their own work, agents reliably skew positive. For quality-critical changes:

- Verify through a distinct pass: re-read the diff with fresh eyes after a pause.
- If the host supports subagents, have a separate agent verify the change against its acceptance criteria.
- Prefer mechanical checks (type checker, linter, test suite) over human-style review alone.
- If verification is blocked, name the concrete blocker and the strongest substitute evidence used.

## If Verification Fails

1. Preserve the failing output.
2. Stop broad editing.
3. Update the cause chain with new evidence.
4. Fix the next root cause.
5. Re-run the same proof.

## If Verification Cannot Run

State the concrete blocker:

- missing dependency,
- unavailable service,
- sandbox or network restriction,
- absent test suite,
- unsafe side effect,
- missing credentials,
- unsupported host tool.

Then state the strongest substitute evidence used.
