# Long-Running Research Workflow Fixture

## Workflow

- A research run lasts three days and a fresh agent takes over each morning.
- Agents read production reports from `evidence/production/`.
- Agents write notes, hypotheses, and proposed experiments under `tasks/<task-id>/`.
- Conversation history is currently the only handoff mechanism.
- An analyst reviews improvement proposals before approved work enters `queue/approved/`.

## Boundaries

- `evidence/production/` is immutable and may contain sensitive customer identifiers.
- Agents must not place raw sensitive values in traces or writable task files.
- Only an analyst may promote a proposal into `queue/approved/`.
- A fresh agent must be able to resume from repository artifacts without prior conversation context.
