# Long-Running Tasks

Tasks spanning multiple context windows or sessions need explicit state management. A fresh session starts with no memory of prior work — plan for that.

## Environment Setup (First Session)

When starting a task that will span multiple sessions, invest the first session in scaffolding:

1. **Progress file.** Create a structured tracker (JSON preferred — models are less likely to inappropriately rewrite JSON than Markdown) listing features or sub-tasks, each with a status. Mark every item as incomplete initially.
2. **Setup script.** Write a script (`init.sh` or equivalent) that starts the development environment, runs dependencies, and boots any required services. Future sessions read this first.
3. **Initial commit.** Commit the scaffold so future sessions can see the baseline state.
4. **Map the terrain.** Write a short doc identifying key entry points, relevant directories, and how to run verification. Future sessions read this to orient quickly.

## Session Start Ritual

Every new session, before doing any work:

1. Confirm the working directory (`pwd` or equivalent).
2. Read the progress file and recent git log to understand current state.
3. Run the setup script and verify the environment boots cleanly.
4. Run a basic end-to-end smoke test to catch undocumented breakage from the previous session.
5. Pick a single incomplete item from the progress file to work on.

## Incremental Progress

Work on one item at a time. When the item is complete:

- Verify it end-to-end (not just unit-level).
- Mark it as done in the progress file.
- Commit with a descriptive message.
- Write a brief progress note summarizing what was done, what the next item is, and any caveats for the next session.

This ensures every session leaves the environment in a clean, mergeable state — no half-finished features, no undocumented bugs.

## Structured Handoffs

When one session ends and another will continue:

- The progress file and git history are the handoff. Both must be current.
- If a decision was made that affects future work, record it in a repo file — do not assume the next session will infer it from code.
- JSON is preferred for tracking state. Models are less likely to tamper with JSON structure than with free-text Markdown.

## When To Reset Context

Long sessions accumulate noise. Decide between:

- **Compaction:** Summarize in-place and continue. Preserves continuity but can carry forward stale assumptions. Good for ongoing work with no major direction changes.
- **Context reset:** End the session, write a clean handoff, and start a fresh session. The fresh session reads the handoff artifacts and continues. Good when the model shows "context anxiety" (rushing to finish, losing focus) or when changing direction.

Prefer a reset when the task exceeds a few hours of active work or when the model's behavior degrades noticeably.

## Multi-Agent Patterns

For complex long-running tasks, consider splitting responsibilities:

- **Planner:** Takes a high-level goal and expands it into a structured breakdown with acceptance criteria. Stays at product/architecture level; avoids over-specifying implementation.
- **Builder:** Implements one item at a time against the plan. Self-verifies before handing off.
- **Evaluator:** Verifies the builder's work independently — exercises the running application, checks against acceptance criteria, reports specific gaps.

The evaluator is the highest-leverage addition. Agents reliably skew positive grading their own work. A separate evaluation pass catches issues that self-review misses. Tune the evaluator to be skeptical; it is far easier to make a separate agent critical than to make a builder critical of its own output.

Before each work item, the builder and evaluator negotiate what "done" means in concrete, testable terms. This contract prevents scope drift and gives the evaluator a clear standard to grade against.

## Model Upgrades

When the underlying model improves:

- Re-examine each harness component. Every split (planner/builder/evaluator), every tracking file, every structured handoff encodes an assumption about what the previous model could not do reliably.
- Remove components whose assumptions no longer hold. A step that was load-bearing for one model is dead weight if the next model handles it natively.
- The goal is the simplest harness that produces reliable results — not the most elaborate one.
