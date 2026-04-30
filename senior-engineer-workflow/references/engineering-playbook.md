# Engineering Playbook

## Request Handling

1. Treat the newest user message as authoritative.
2. Determine whether the user wants code changes, investigation, documentation, review, or an explanation.
3. If the task is actionable, proceed with local inspection and implementation.
4. Ask only when missing information makes the next step risky or impossible.

## Repository Inspection

Run targeted context gathering before edits:

```powershell
rg --files
rg "pattern"
git status --short
Get-Content -Path path\to\file.py -TotalCount 120
```

Check local instructions and configs first:

- `AGENTS.md` or other host-specific instruction files
- package or tool configs such as `pyproject.toml`, `package.json`, `pytest.ini`

## Bug Investigation

Use this sequence:

1. Locate the affected files or data.
2. Reproduce or inspect the failing case.
3. Compare normal vs abnormal behavior.
4. Identify the smallest likely cause.
5. Verify the cause with a focused command or one representative sample.
6. Patch the smallest surface.
7. Re-run the verification.

Describe debugging with direct cause chains:

`bad input shape -> parser assumes field exists -> exception -> guard missing field`

## Code Change Workflow

1. Read the relevant implementation and nearby helpers.
2. Reuse existing patterns, helpers, naming, and error handling.
3. Keep changes local to the requested behavior.
4. Add comments only where the code would otherwise be hard to parse.
5. Prefer structured parsers/APIs over ad hoc string manipulation when available.
6. Use `apply_patch` for manual edits.
7. Avoid unrelated formatting churn.

## Verification Workflow

Choose the narrowest proof that matters:

- Unit or parser change: run the specific test or script.
- CLI/script change: run the command on a minimal sample.
- Web/API scraper change: fetch or render one representative item first.
- Batch rewrite: verify counts and sample records before and after.
- Frontend change: run the dev server and inspect screenshots when visual correctness matters.

If a command fails because of sandbox or network restrictions and the command is necessary, follow the host environment's approval or escalation process.

## Batch Or File Rewrite Safety

Before overwriting important output:

1. Parse record boundaries.
2. Count source records.
3. Verify one target record can be transformed correctly.
4. Write to a new file or create a backup when loss is possible.
5. Replace only the affected ranges.
6. Count output records again.
7. Search for residual failure markers.

For encrypted scraper output, a safe flow is:

1. Identify the first encrypted chapter.
2. Confirm previous chapters are plain text.
3. Fetch or render one encrypted chapter.
4. Confirm decoded text is readable Chinese and not Base64.
5. Integrate the decoder.
6. Rewrite only encrypted chapter bodies.
7. Verify first and last rewritten chapters.

## Git Workflow

1. Run `git status --short`.
2. Ignore unrelated untracked or modified files.
3. Stage only files changed for the task.
4. Commit durable project changes once per turn when appropriate.
5. Use Conventional Commit style.
6. Never contact remotes unless explicitly requested.

Do not commit:

- `.env`, `.env.*`
- `cookies.json`
- `.chat_history`
- `.venv/`
- `node_modules/`
- generated output files
- screenshots containing private data
- resume ID files

## Review Workflow

For code review requests:

1. Start with findings.
2. Order by severity.
3. Include file and line references.
4. Focus on bugs, regressions, security, data loss, and missing tests.
5. Add open questions only after findings.
6. Keep summaries secondary.

If there are no findings, say that directly and mention residual test risk.
