# Research Sources For Harness Design

Use this reference when the user asks why the harness should be shaped a certain way, or when you need citations while designing a harness.

## OpenAI Official Sources

- [Unrolling the Codex agent loop](https://openai.com/index/unrolling-the-codex-agent-loop/)
  - Codex harness executes the loop: user input -> model call -> tool call -> observation -> repeated model call -> final response or environment change.
  - Implication: define loop, tool result handling, termination, and context management.

- [Unlocking the Codex harness: how we built the App Server](https://openai.com/index/unlocking-the-codex-harness/)
  - The Codex harness includes thread lifecycle, persistence, config, auth, tool execution, extensions, and rich client events.
  - `item`, `turn`, and `thread` are useful protocol concepts.
  - Implication: separate core runtime from clients; design event and trace schemas.

- [Harness engineering: leveraging Codex in an agent-first world](https://openai.com/index/harness-engineering/)
  - Agent-first engineering shifts humans from direct coding to steering, environment design, feedback loops, and repository artifacts.
  - Implication: put decisions, constraints, docs, checks, and runbooks in the repo.

- [Building a safe, effective sandbox to enable Codex on Windows](https://openai.com/index/building-codex-windows-sandbox/)
  - Agent usefulness requires file, shell, and test execution; safety requires OS-enforced read/write/network/process boundaries.
  - Implication: define permission policy and approval gates.

- [Running Codex safely at OpenAI](https://openai.com/index/running-codex-safely/)
  - Safety needs telemetry: requests, tool behavior, approvals, tool results, and policy blocks.
  - Implication: trace and audit data are first-class harness outputs.

- [Daybreak](https://openai.com/daybreak/) and [Codex Security Help Center](https://help.openai.com/en/articles/20001107)
  - Security harnesses should validate vulnerabilities, reason about attack paths, generate patches, and keep audit evidence.
  - Implication: encode domain workflow and verification, not just advice.

- [Introducing SWE-bench Verified](https://openai.com/index/introducing-swe-bench-verified/)
  - Eval quality matters: tasks can be underspecified and tests can reject valid solutions.
  - Implication: review benchmark quality and record scaffold/harness versions.

- [Introducing upgrades to Codex](https://openai.com/index/introducing-upgrades-to-codex/)
  - Agentic coding workflows use rich context, todos, MCP, approvals, diff display, and session compacting.
  - Implication: progress tracking and approval state are harness primitives.

- [Building self-improving tax agents with Codex](https://openai.com/index/building-self-improving-tax-agents-with-codex/)
  - Production evidence becomes actionable findings, targeted evals, and bounded tasks.
  - Implication: separate read-only evidence from writable worktree and use expert-reviewed improvement loops.

## Anthropic Official Sources

- [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)
  - Start simple. Use workflows for predefined paths and agents only when dynamic decisions are needed.
  - Implication: justify harness complexity.

- [Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
  - Long tasks need initializer/coding-agent separation, progress logs, and clean-state checkpoints.
  - Implication: design resumable state and handoff artifacts.

- [Harness design for long-running application development](https://www.anthropic.com/engineering/harness-design-long-running-apps)
  - Planner/generator/evaluator structures can help but should be ablated; components encode assumptions about model limits.
  - Implication: avoid permanent complexity without measurement.

- [Scaling Managed Agents: Decoupling the brain from the hands](https://www.anthropic.com/engineering/managed-agents)
  - Separate session, harness, and sandbox behind stable interfaces.
  - Implication: keep state, runtime loop, and execution environment replaceable.

- [Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
  - Defines task, trial, grader, trace, outcome, evaluation harness, and agent harness.
  - Implication: generated harnesses need eval plans and outcome-based graders.

- [Building agents with the Claude Agent SDK](https://claude.com/blog/building-agents-with-the-claude-agent-sdk)
  - Agent loop: gather context -> take action -> verify work -> repeat.
  - Implication: define the agent's "computer" and verification loop.

- [Writing effective tools for agents - with agents](https://www.anthropic.com/engineering/writing-tools-for-agents)
  - Tools are contracts between deterministic systems and non-deterministic agents.
  - Implication: design agent-friendly tools and tool evals.

- [How we built our multi-agent research system](https://www.anthropic.com/engineering/built-multi-agent-research-system)
  - Multi-agent systems help broad parallel research but cost much more; delegation contracts and traces matter.
  - Implication: use multi-agent only for suitable decomposable tasks.

- [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
  - Context engineering manages the runtime context, not just prompts.
  - Implication: design context selection, persistence, compression, isolation, and provenance.

## Research Infrastructure And Papers

- [Lessons from the Trenches on Reproducible Evaluation of Language Models](https://arxiv.org/abs/2405.14782) and [LM Evaluation Harness docs](https://lm-evaluation-harness.readthedocs.io/)
  - Make eval variables explicit: model, prompt, task, decoding, metrics, environment, and outputs.

- [Holistic Evaluation of Language Models](https://arxiv.org/abs/2211.09110)
  - Evaluate across multiple dimensions, not only accuracy.

- [SWE-bench](https://arxiv.org/abs/2310.06770)
  - Real GitHub issue resolution requires repo snapshots, patch generation, and test-based outcome grading.

- [SWE-agent](https://arxiv.org/abs/2405.15793)
  - Agent-computer interfaces materially affect coding-agent performance.

- [AgentBench](https://arxiv.org/abs/2308.03688)
  - Agent evals should involve interactive environments and long-horizon decision making.

- [WebArena](https://arxiv.org/abs/2307.13854)
  - Browser harnesses need controlled environments and functional completion checks.

- [OSWorld](https://arxiv.org/abs/2404.07972)
  - Computer-use harnesses need environment reset and execution-based graders.

- [Tau-bench](https://arxiv.org/abs/2406.12045)
  - Business agents need user, tool, and policy modeling.

- [MLAgentBench](https://arxiv.org/abs/2310.03302)
  - Research-agent harnesses need experiment artifacts, logs, metrics, and budget controls.

