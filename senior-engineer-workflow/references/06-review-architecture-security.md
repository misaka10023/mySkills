# Review, Architecture, Security

## Code Review

Lead with findings. For each finding include:

- severity: Critical, High, Medium, Low,
- file and line,
- failure mode,
- evidence,
- fix direction.

Prioritize correctness, data loss, security, compatibility, performance cliffs, accessibility, missing tests, deployment risk, and maintainability. If there are no findings, say so and name residual test risk.

## Architecture

Gather:

- functional requirements,
- scale and latency constraints,
- data model and ownership,
- failure modes,
- migration path,
- compatibility requirements,
- observability and operations,
- security and compliance constraints,
- team ownership and maintenance cost.

Compare two or three options. Recommend one and explain tradeoffs. Prefer boring, observable, reversible designs.

Use ADR shape when useful:

```text
Context:
Decision:
Consequences:
Alternatives:
Rollback:
```

## Security

Check:

- authentication and authorization,
- input validation and output encoding,
- injection and unsafe deserialization,
- secrets in code, logs, commits, screenshots, and chat history,
- dependency and supply-chain risk,
- rate limits and abuse cases,
- privacy and data retention,
- least privilege for tools and credentials.

Security-sensitive changes require narrower edits, stronger verification, and explicit unresolved risks.

## Mechanical Enforcement

Documentation alone does not keep a codebase coherent. Prefer encoding rules so they fail the build:

- Custom lint rules that reject known anti-patterns.
- Structural tests that verify dependency direction, layer boundaries, and naming conventions.
- CI checks that validate documentation freshness and cross-links.
- Error messages written to inject remediation instructions into agent context.

A rule that only lives in prose is a wish. A rule enforced by a linter is a guarantee.
