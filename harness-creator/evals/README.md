# Harness Creator Smoke Evals

These version 1 fixtures evaluate design and review behavior without modifying a repository.

## Setup

For each case in `evals.json`, provide only the listed files and the prompt to the executor. Run from an isolated output directory or a read-only workspace; the source Skill repository is never the target harness repository.

## Reset

No environment reset is required because every prompt is explicitly read-only. Discard generated responses between trials and reuse the unchanged fixture files.

## Grading

Grade each `expectations` statement against the response and attached fixture. Reject invented files, unsupported execution claims, and citations to paths not present in the fixture. Use separate trials when measuring model variance.

These smoke evals test routing, design controls, evidence use, platform-specific installation guidance, and review quality. They do not prove filesystem installation, link creation, host discovery, or runtime behavior; verify those with isolated integration checks on the target platform.
