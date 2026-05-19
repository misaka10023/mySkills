# Verification

## Verification Matrix

| Change Type | Minimum Useful Proof |
| --- | --- |
| Documentation | Read raw/rendered Markdown; validate commands if executable |
| Unit logic | Focused unit test; add regression test for new behavior |
| Parser/transform | Valid, invalid, empty, boundary, and real sample inputs |
| CLI/script | Minimal sample run; verify exit code and output |
| API/backend | Focused service/route test or local request; check schema and error path |
| Frontend/UI | Run app or component; check screenshot, console, responsive layout, loading and error states |
| Build/tooling | Smallest lint/type/build command touching the changed surface |
| Data migration | Dry run or sample run; verify counts and representative records |
| Security/auth | Authorization, validation, secret handling, logging, dependency exposure |

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
