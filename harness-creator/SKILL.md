---
name: harness-creator
description: Design, create, review, or improve production-grade agent harnesses and evaluation harnesses. Use whenever a user is building or hardening a Codex, Claude Code, MCP, browser, computer-use, coding, long-running, security, tool-use, multi-agent, or self-improving agent workflow; needs task or trace schemas, tool contracts, permission policies, graders, eval suites, resumable state, runbooks, or runtime architecture; wants to turn a human process into an agent-executable workflow; or reports that an agent is unreliable, unsafe, hard to evaluate, or unable to resume across sessions. Also use for reviewing an existing harness even when the user does not call it a harness.
---

# Harness Creator

Turn an agent idea or unreliable workflow into the smallest runnable system that is observable, safe, resumable when necessary, and verified by environment evidence. Package every newly created harness as a reusable skill so its trigger, workflow, resources, and checks travel together. Treat the prompt as one component of the harness, not the harness itself.

## Working Principle

Design feedback systems, not prompt piles. Add a harness component only when it addresses a concrete failure mode, and prefer a deterministic workflow or ordinary script when dynamic agent decisions are unnecessary.

## Route The Request

First identify both the requested operation and harness type.

### Operation

| Request | Action |
| --- | --- |
| Create or design | Inspect the target environment, define success and failure modes, then produce the minimum runnable artifact set. |
| Review or audit | Trace each existing component to a failure mode, find missing controls and unverifiable claims, then report findings before proposing changes. |
| Improve or debug | Start from observed failures or traces, form a cause chain, change the narrowest harness boundary, and add a regression eval. |
| Explain or advise | Give a decision with tradeoffs. Create files only when the user asks for implementation. |

### Harness Type

Classify one primary type and any secondary concerns:

- `coding`: repository modification, testing, review, CI, or patch delivery.
- `long_running`: work continues across context windows or sessions.
- `evaluation`: model, prompt, tool, or agent behavior must be measured.
- `tooling`: tool choice, schemas, responses, or recovery behavior need improvement.
- `browser` or `computer_use`: the agent acts through websites, desktop apps, screenshots, keyboard, or mouse.
- `security`: the agent finds, validates, fixes, or audits vulnerabilities.
- `self_improving`: production evidence and expert corrections become bounded improvement tasks and regression evals.
- `multi_agent`: work is genuinely decomposable and benefits from orchestrator-worker coordination.

If a fixed workflow, one tool call, a script, or ordinary documentation solves the problem, recommend or build that smaller solution instead.

### Packaging Target

For every create or design request, produce a project-local skill package. A standalone runtime, service, library, or repository-native integration may own execution, but the harness must still include a thin skill entrypoint that makes the workflow discoverable and invokes the existing implementation without duplicating it.

Use one canonical project-local installation for both Codex and Claude Code:

```text
.agents/skills/<skill-name>/   # canonical skill content
.claude/skills                 # directory link to .agents/skills
```

Never maintain separate Codex and Claude copies. Keep all essential behavior in portable `SKILL.md`, `scripts/`, `references/`, and `assets/` content. Treat `agents/openai.yaml` as optional Codex-facing display metadata; the harness must remain functional when a host ignores it.

For review-only requests, preserve the established package shape and report a missing skill entrypoint as a finding. For debug or improve implementations, add or repair the thin skill entrypoint as part of the scoped change.

## Load References Progressively

| Need | Read |
| --- | --- |
| Create or install a skill-packaged harness, repository artifacts, or concrete schemas | `references/templates.md` |
| Explain design rationale, compare established patterns, or provide citations | `references/research-sources.md` |

Do not load either reference when the current repository already provides authoritative templates or contracts.

## Operating Workflow

### 1. Inspect The Real Environment

- Read project instructions, existing harness files, tools, tests, evals, traces, schemas, and runtime configuration.
- Identify the model/runtime, execution environment, trust boundaries, and the human or system consuming the result.
- Verify version-sensitive APIs against primary sources when they affect the design.
- Preserve project conventions and unrelated user changes.

For an existing harness, reconstruct the actual loop from code and traces rather than trusting architecture prose.

### 2. Define The Contract

Write a concise goal, non-goals, inputs, outputs, constraints, and stop conditions. Define completion as an observable environment outcome; an agent's final message is not proof.

Clarify only decisions that materially alter architecture, permissions, destructive behavior, or evaluation semantics. Otherwise state reasonable assumptions and proceed.

### 3. Build A Failure-Control Map

List likely failures before selecting components. Typical failures include ambiguous tasks, missing context, noisy or overlapping tools, lost state, premature completion, unsafe permissions, weak graders, unreproducible environments, absent traces, and benchmark overfitting.

Use this structure:

| Failure mode | Observable signal | Harness control | Verification |
| --- | --- | --- | --- |

Do not retain a component that has no failure mode or measurable purpose.

### 4. Design The Minimum Harness

Specify only the boundaries the request needs:

- **Loop:** gather context -> choose a bounded action -> act -> observe -> verify -> record state -> continue, stop, or request approval.
- **Context:** initial inputs, selection rules, provenance, compression, isolation, and durable handoff state.
- **Tools:** narrow purpose, typed inputs, token-bounded outputs, actionable errors, idempotency expectations, and permission level.
- **State:** source of truth, lifecycle, checkpoints, resume behavior, and stale-state handling.
- **Permissions:** read/write/network/process/secret scope, destructive actions, and explicit approval gates.
- **Trace:** task, turn, step, tool call, approval, environment delta, verification, error, and timestamp.
- **Evals:** representative tasks, fixed setup/reset, trials, outcome-based graders, metrics, and regression comparison.
- **Operations:** startup, inspection, recovery, rollback, upgrade, and ablation.

Use multi-agent topology only when parallelism or specialization outweighs coordination cost. Require explicit task ownership, artifact paths, completion contracts, and integration responsibility.

### 5. Produce A Skill-Packaged Harness

Prefer executable or machine-checkable repository artifacts over chat-only recommendations. Read `references/templates.md` before creating a new harness skill.

Install the skill project-locally at `.agents/skills/<skill-name>/`. Maintain `.claude/skills` as a directory link to `.agents/skills` so Codex and Claude Code load the same files.

Before writing, inspect `.agents`, `.agents/skills`, `.agents/skills/<skill-name>`, `.claude`, and `.claude/skills`. Any existing `.agents`, `.agents/skills`, and `.claude` parent must be a real directory inside the project, not a symlink, Junction, or other reparse point. Create absent parents inside the project, then validate them again before continuing. The only permitted directory link in this layout is `.claude/skills`.

- If `.agents/skills/<skill-name>` is absent, create it.
- If it belongs to the same harness and the user asked for an improvement, update it in place.
- If it belongs to another skill or ownership is ambiguous, stop and report the conflict.
- If any parent path is linked, is not a directory, or resolves outside the project, stop before writing and request an explicit location decision.

Then inspect `.claude/skills`:

- If it is the correct directory link, preserve it.
- On POSIX, if it is absent, create a relative symbolic link to `../.agents/skills`.
- On Windows, if it is absent, create a directory Junction whose absolute target is the resolved project-local `.agents/skills` directory. Junctions preserve one source of truth without requiring Developer Mode or administrator privileges.
- If it is a real directory, file, broken link, or points elsewhere, stop and report the conflict. Do not delete, merge, or replace user content without explicit approval.

Treat `.claude/skills` as an ignored local installation artifact on both platforms: do not duplicate its target content and do not commit the link. Verify or recreate it after checkout, and document the install command. This avoids Windows checkouts materializing a committed POSIX symlink as a plain file when Git symlink support is disabled.

Use this package shape selectively:

```text
<skill-name>/
|-- SKILL.md
|-- agents/
|   `-- openai.yaml
|-- scripts/
|-- references/
|-- assets/
`-- evals/
```

- `SKILL.md` is the concise agent-facing entrypoint. Give it valid `name` and trigger-oriented `description` frontmatter, then route the task, state the workflow, point to resources, and define completion.
- `scripts/` contains deterministic or repetitive operations. Prefer invoking existing project code when it already owns the behavior.
- `references/` contains detailed protocols, schemas, domain variants, runbooks, or rationale loaded only when needed.
- `assets/` contains templates and files copied into outputs; do not use it for instructions.
- `evals/` contains `evals.json`, fixed input fixtures, and objective expectations where behavior is machine-verifiable.
- `agents/openai.yaml` contains agent-facing display metadata when the target host uses it.

Keep `SKILL.md` focused and preferably below 500 lines. Put all trigger conditions in the frontmatter description, use relative links, and avoid duplicating detailed content between the entrypoint and references.

Keep platform-specific commands behind explicit platform branches. Do not put essential instructions only in host-specific metadata, slash commands, hooks, MCP configuration, or proprietary agent formats. When the harness requires a host-specific capability, detect it, provide the equivalent route for the other host when feasible, and declare any remaining compatibility gap.

The harness's operational contracts may live inside the skill under `references/` or `assets/`. Put them in shared repository locations such as `docs/harness/` only when humans, CI, runtimes, or other skills must consume them independently.

Choose the smallest useful contract subset; never create empty boilerplate merely to match a standard layout:

- `docs/harness/HARNESS.md`: goal, loop, boundaries, failure-control map, and operating model.
- `docs/harness/task.schema.yaml`: task inputs, constraints, success criteria, verification, and handoff.
- `docs/harness/tools.yaml`: tool contracts, safety properties, response limits, errors, and eval cases.
- `docs/harness/permissions.md`: trust boundaries and approval policy.
- `docs/harness/trace.schema.json`: stable observability contract with redaction rules.
- `docs/harness/runbook.md`: start, resume, diagnose, recover, upgrade, and ablate.
- `evals/`: smoke tasks, fixtures, graders, configuration, and regression entrypoint.
- `tasks/<task-id>/`: durable plan, progress, results, and handoff for bounded long-running work.

When improving an existing harness, edit its established files and keep the skill as a thin routing and operating layer instead of moving or copying runtime ownership.

### 6. Verify From The Consumer Boundary

Run the narrowest proof that exercises the changed contract:

1. Parse schemas and configuration.
2. Validate skill frontmatter, resource links, and expected directory names.
3. Confirm all install paths resolve inside the project and `.agents/skills/<skill-name>` has no ownership conflict.
4. Confirm `.agents/skills/<skill-name>` is canonical and `.claude/skills` resolves to `.agents/skills`.
5. Check that both Codex and Claude Code can discover the same `SKILL.md` without relying on host-specific metadata.
6. Run deterministic scripts directly with a minimal fixture.
7. Run a tool-contract or runtime smoke test.
8. Run at least one representative skill eval with a clean fixture or documented reset.
9. Confirm required trace events and redaction behavior.
10. Exercise resume or approval behavior when those are central risks.
11. Run `git check-ignore` and `git status`: canonical `.agents/skills/<skill-name>` content must be visible to Git when versioned, while the local `.claude/skills` link must be ignored and reproducible from documented install steps.
12. Review the diff for scope creep, secrets, generated noise, and unverified claims.

If execution is unavailable, distinguish structural validation from behavioral proof and name the exact missing proof.

### 7. Deliver A Decision Record

Report:

- the failure modes addressed and the controls added or changed;
- created or modified artifacts;
- verification run and its result;
- residual risks, assumptions, and the next highest-value eval.

For reviews, lead with findings ordered by severity and cite file locations. For implementations, lead with the working outcome.

## Harness-Specific Controls

Apply these only when the route requires them:

- **Long-running:** durable progress and result files, explicit resume instructions, clean checkpoints, and a fresh-agent smoke test.
- **Browser/computer-use:** stable environment fixtures, screenshot or state evidence, retry bounds, focus/window assumptions, and functional completion graders.
- **Security:** least privilege, secret minimization, sandbox boundaries, audit evidence, exploit validation controls, and human gates for high-impact actions.
- **Self-improving:** read-only production evidence, expert-reviewed findings, bounded writable tasks, held-out evals, rollback, and promotion gates.
- **Multi-agent:** non-overlapping ownership, written artifacts instead of lossy summaries, bounded fan-out, cost limits, and an explicit integrator.
- **Evaluation:** version every relevant variable, separate generation from grading, use repeated trials where nondeterminism matters, and check graders for false positives and false negatives.

## Design Rules

- Prefer fewer, distinct tools; overlapping tools increase selection errors.
- Return high-signal, token-bounded observations and actionable recovery errors.
- Keep read-only evidence separate from writable workspaces.
- Grade environment outcomes whenever possible; use rubric-based judges only for genuinely subjective criteria.
- Treat traces as stable product interfaces and redact sensitive values at capture time.
- Encode resumability in repository artifacts rather than relying on conversation history.
- Record harness, model, prompt, tool, fixture, and grader versions for reproducible evals.
- Re-evaluate components after model or runtime upgrades and remove scaffolding that no longer improves measured outcomes.

## Completion Gate

Before declaring the harness complete, confirm:

- Every material component maps to a documented failure mode.
- The harness has a valid, triggerable `SKILL.md` entrypoint, including when a separate runtime owns execution.
- The canonical installation is project-local under `.agents/skills`, every resolved install path remains inside the project, and `.claude/skills` resolves to that same directory without duplicated content.
- Essential behavior is portable across Codex and Claude Code; host-specific metadata is optional.
- Detailed resources are progressively loaded and owned by the skill or referenced without duplication.
- Success and stop conditions are externally observable.
- Permission escalation and destructive actions have explicit policy.
- State and trace contracts are durable, bounded, and redact secrets.
- At least one realistic smoke path has been exercised, or the behavioral proof gap is explicit.
- Eval setup, grader behavior, and relevant versions are reproducible.
- Canonical Skill files are visible to Git when versioned; the ignored local `.claude/skills` link is reproducible from documented install steps and verified after recreation.
- The result follows the target repository's conventions and contains no unused framework files.
