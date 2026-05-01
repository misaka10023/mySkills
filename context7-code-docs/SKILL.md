---
name: context7-code-docs
description: Fetch up-to-date, version-specific documentation with Context7 for code work. Use when the user asks about libraries, frameworks, SDKs, integrations, API references, setup/configuration, code examples, migrations, or when implementing, modifying, debugging, configuring, or reviewing code that depends on third-party or version-sensitive APIs.
---

# Context7 Code Docs

Use this skill before answering or changing code that depends on current third-party documentation. Prefer Context7 over memory for library APIs, framework behavior, setup steps, middleware, migrations, and code examples.

## Trigger Examples

Use Context7 when the user:

- Asks setup or configuration questions, such as framework middleware, auth providers, build tools, or SDK clients.
- Requests code involving libraries, frameworks, SDKs, or integrations.
- Needs API references, method names, options, migration details, or compatibility behavior.
- Mentions specific frameworks or libraries such as React, Vue, Svelte, Next.js, Prisma, Supabase, Tailwind, Express, FastAPI, Django, or similar tools.

## Fetch Workflow

1. Identify the relevant library, framework, SDK, or integration. Determine the version from local files when possible.
2. Resolve the library with Context7 before fetching docs unless the user already provided an exact Context7-compatible ID such as `/org/project` or `/org/project/version`.
3. Select the best match using exact or closest name, official/primary source status, version match, documentation coverage, reputation, and benchmark score when available.
4. Fetch focused docs for the user's specific API, config, middleware, migration, error, or code example. Use `mode="code"` for API usage and examples; use `mode="info"` for conceptual or architectural questions.
5. If the first result is insufficient, fetch the next page, narrow the topic, resolve a more specific library ID, or use a Context7 research/deep mode when the host implementation supports it before falling back.
6. Use only the necessary details in code or explanation. Cite the relevant library version when it matters.
7. Mention Context7 usage in chat history logging when that logging is available.

## Query Guidance

- Be specific: use the user's full request to choose the library and focused topic.
- Preserve version intent: if the user names a version, prefer a version-specific ID or clearly state when only general docs are available.
- Prefer primary packages over community forks unless the user explicitly asks for a fork or wrapper.
- For monorepos or broad products, resolve the smallest relevant package or docs target before fetching.
- For ambiguous library names, make the best documented primary-source choice when the risk is low; ask only when multiple choices would lead to materially different code.

## Fallback

If Context7 is unavailable or does not contain enough detail, proceed with local code and built-in knowledge only when reasonable. Mark version-sensitive details as uncertain, and prefer primary or official sources if another documentation path is available.
