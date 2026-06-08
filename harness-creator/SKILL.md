---
name: harness-creator
description: Create, review, or improve agent harnesses and evaluation harnesses. Use this skill whenever the user asks to build a Codex, Claude Code, MCP, browser, computer-use, coding, long-running, security, tool-use, or self-improving harness; asks to make an agent workflow reliable across sessions; asks for task schemas, graders, trace schemas, permission policies, runbooks, eval suites, or agent runtime design; or wants to convert a human process into an agent-executable and verifiable workflow.
---

# Harness Creator

Use this skill to turn an agent idea into a concrete harness: runnable structure, tools, state, permissions, traces, evals, and operating docs. A harness is not just a prompt; it is the system around the model that makes work executable, observable, safe, and verifiable.

## Core Principle

Design feedback systems, not prompt piles. Reliable agents improve through environment feedback: tool results, tests, evals, traces, human approvals, production evidence, and regression checks. Every harness component should exist because it addresses a concrete failure mode.

## Source Model

This skill is based on these evidence-backed patterns:

- OpenAI Codex harness material: agent loop, App Server thread/turn/item model, sandboxing, safety telemetry, SWE-bench Verified, Codex upgrades, and self-improving domain agents.
- Anthropic agent material: building effective agents, long-running harnesses, harness design for long-running apps, managed agents, agent evals, Claude Agent SDK, tool design, multi-agent research, and context engineering.
- Research infrastructure: LM Evaluation Harness, HELM, SWE-bench, SWE-agent, AgentBench, WebArena, OSWorld, Tau-bench, and MLAgentBench.

When the user asks for detailed rationale or citations, read `references/research-sources.md`. When you need concrete output skeletons, read `references/templates.md`.

## When To Build A Harness

Before creating files, classify the request:

- `coding`: repository modification, testing, review, CI, patch delivery.
- `long_running_project`: work must continue across context windows or sessions.
- `evaluation`: model, prompt, tool, or agent behavior must be measured.
- `tool_optimization`: agent needs better tool choice, schemas, responses, or errors.
- `browser_web`: agent acts through websites, SaaS, or browser automation.
- `computer_use`: agent acts through desktop apps, OS state, files, screenshots, keyboard, or mouse.
- `security`: agent finds, validates, fixes, or audits vulnerabilities.
- `self_improving`: production traces and expert corrections become evals and bounded improvement tasks.
- `multi_agent`: task is broad, parallelizable, and benefits from orchestrator/worker split.

If a fixed workflow, single tool call, script, or ordinary documentation solves the task, recommend that instead of an agent harness. Harness complexity must earn its keep.

## Default Workflow

1. Inspect context.
   - Read existing project docs, scripts, tests, config, AGENTS.md, evals, and any provided research notes.
   - If the user cites URLs or version-sensitive APIs, verify against primary sources when available.
   - Preserve existing project conventions and avoid unrelated rewrites.

2. Define success.
   - Write a short goal and non-goals.
   - Define environment outcomes that prove completion. Do not accept an agent's final message as proof.
   - Identify human approval points and destructive actions.

3. Analyze failure modes.
   - List the likely ways this harness could fail: ambiguous task, missing context, noisy tools, lost state, premature completion, weak grader, unsafe permissions, non-reproducible environment, missing trace, or benchmark overfitting.
   - Map each proposed component to a failure mode.

4. Design the harness.
   - Agent loop: gather context -> act -> observe -> verify -> repeat -> stop.
   - Context model: what the agent sees, where durable state lives, how context is compressed or handed off.
   - Tool model: small, high-value, agent-friendly tools with clear names, schemas, concise responses, and actionable errors.
   - Permission model: read scope, write scope, network, secrets, process execution, destructive actions, approvals.
   - Trace model: task, turn, step, tool call, approval, environment delta, verification, error, timestamp.
   - Eval model: tasks, trials, environment setup/reset, graders, metrics, regression comparison.

5. Generate artifacts.
   - Prefer repository files over chat-only plans. Create or update the smallest useful set of files.
   - Use the templates in `references/templates.md` when creating new harness docs.

6. Verify.
   - Run the smallest useful check available: schema parse, smoke eval, test command, lint, or file existence check.
   - If a proof cannot run, state the exact blocker and the next command that should be run.

7. Deliver.
   - Report created files, verification, unresolved risks, and next steps.
   - Keep the result scoped and avoid unrelated refactors.

## Standard Artifact Set

Create these when relevant. Do not create empty boilerplate files that the project will not use.

- `docs/harness/HARNESS.md`: goal, non-goals, loop, context, tools, state, permissions, evals, traces, human gates, failure modes, runbook.
- `docs/harness/task.schema.yaml`: task schema or task template.
- `docs/harness/tools.yaml`: tool manifest with purpose, safety, responses, errors, and eval tasks.
- `docs/harness/permissions.md`: read/write/network/secret/destructive-action policy.
- `docs/harness/trace.schema.json`: minimal trace contract.
- `docs/harness/runbook.md`: start, resume, inspect trace, run eval, handle failure, upgrade, ablate.
- `evals/README.md` and smoke cases: eval suite entrypoint, graders, fixtures, and regression command.
- `tasks/<task-id>/task.yaml`, `PLAN.md`, `RESULTS.md`: for bounded long-running or self-improving tasks.

## Design Rules

- Prefer workflows over agents when the process is predictable.
- Prefer fewer, better tools. Tool overlap creates selection errors.
- Make tool outputs high-signal and token-bounded by default.
- Include actionable tool errors that tell the agent how to recover.
- Keep read-only evidence separate from writable workspace.
- Use environment outcomes for grading whenever possible.
- Treat trace as a product requirement, not debug leftovers.
- For long tasks, write progress and handoff files that a fresh agent can read.
- For multi-agent systems, require an explicit delegation contract and artifact-based subagent outputs.
- For subjective work, define rubrics and evaluator roles; do not pretend subjective quality is fully objective.
- Revisit harness components after model upgrades. Remove components whose assumptions are no longer true.

## Anti-Patterns

- A giant prompt with no tools, state, evals, or trace.
- Asking the agent to finish a huge project in one pass.
- Judging success from a final chat message.
- Exposing raw internal APIs as noisy tools.
- Running evals without environment reset or versioned config.
- Letting agents access secrets or production data without minimization and audit.
- Multi-agent delegation through lossy chat summaries instead of written artifacts.
- Adding harness layers without measuring whether they help.

## If The User Wants A Skill Or Harness Package

If the user asks to create a reusable harness skill or package:

1. Create the project-local draft first.
2. Keep the skill body short and move large references to `references/`.
3. Include trigger conditions in the description field, not only in the body.
4. Add realistic smoke prompts or eval notes when useful.
5. Validate frontmatter and links.
6. Install only after review, using the user's expected skill directory conventions.

