# Accuracy And Research

## Source Hierarchy

Prefer sources in this order:

1. Explicit user instruction for the current turn.
2. Project instruction files and repository docs.
3. Local code, tests, configs, schemas, lockfiles, generated clients, and CI.
4. Runtime output from commands, tests, logs, or local requests.
5. Official/current documentation for third-party APIs.
6. Reputable secondary sources.
7. Memory or general knowledge.

## Verification Rules

- Use current documentation for version-sensitive APIs, SDK behavior, config, migrations, package names, pricing, legal rules, schedules, or time-sensitive facts.
- Determine installed versions from lockfiles or package metadata before applying docs when possible.
- Cite exact evidence in working notes and final answers when it affects the decision.
- Label inference explicitly when evidence is indirect.
- If sources conflict, state which source wins and why.
- If high confidence is impossible, provide the safest next check instead of pretending certainty.

## Query Strategy

- Start from the exact library/framework/product name and version.
- Prefer primary docs, source repositories, release notes, and type definitions.
- Search error messages verbatim only after checking local code and versions.
- For broad topics, narrow by API, option name, framework version, or migration step.
- Avoid copying long external text into the answer; summarize and link sources.

## Agent Legibility

From the agent's perspective, anything it cannot access in-context while running effectively does not exist. Knowledge that lives only in chat threads, external documents, or people's heads is invisible.

- Push architectural decisions, conventions, plans, and design rationale into version-controlled repo artifacts (Markdown, schemas, config files).
- Treat AGENTS.md / CLAUDE.md / project instruction files as a table of contents — a map that points to deeper sources of truth, not an encyclopedia.
- Prefer dependencies and abstractions that can be fully reasoned about from repo-local information. Technologies that are stable, composable, and well-represented in training data give agents more leverage.

## Anti-Patterns

- Implementing from remembered APIs when docs are current and available.
- Treating Stack Overflow or blog posts as authoritative for modern framework behavior.
- Ignoring local lockfile versions.
- Reporting a guess as a fact.
- Searching the web before reading the project code that controls the behavior.
- Keeping design decisions only in chat threads or external documents that future agent sessions cannot discover.
