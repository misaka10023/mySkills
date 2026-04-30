# Repository Guidelines

## Project Structure & Module Organization

This repository stores reusable Codex skills. `README.md` is the collection entry point. Each skill should live in its own top-level directory; the current skill is `codex-workflow/`.

- `codex-workflow/SKILL.md`: primary skill definition, including YAML front matter and operating workflow.
- `codex-workflow/references/`: supporting Markdown guides that are loaded only when needed.
- `codex-workflow/agents/openai.yaml`: agent-facing metadata, display name, and default prompt.

Keep future examples, templates, or assets inside the owning skill directory so each skill remains portable.

## Build, Test, and Development Commands

There is no build system or automated test runner yet. Use focused inspection commands while editing:

```powershell
rg --files
Get-Content -Raw codex-workflow\SKILL.md
git -c safe.directory=D:/Pe/Project/python/mySkills status --short
git -c safe.directory=D:/Pe/Project/python/mySkills diff
```

`rg --files` verifies repository contents. `Get-Content` checks the skill body. The Git commands are useful on this Windows checkout when Git reports dubious ownership.

## Coding Style & Naming Conventions

Use Markdown for skill documentation and YAML for agent metadata. Keep Markdown headings descriptive and concise. Use fenced code blocks with language tags for command examples. YAML files should use two-space indentation and quoted strings only when they improve clarity.

Name skill directories with kebab case, such as `codex-workflow`. Every skill must include a `SKILL.md` file with `name` and `description` front matter. Prefer relative paths when referring to files inside the same skill.

## Testing Guidelines

Validate documentation changes manually until automated tests are added. Confirm that YAML front matter parses visually, referenced files exist, and examples match the current directory layout. After edits, run `rg --files` and inspect changed files with `git diff`.

## Commit & Pull Request Guidelines

Recent history uses short Conventional Commit-style messages, for example `feat:add codex workflow`. Prefer the spaced form going forward, such as `docs: add contributor guide`.

Pull requests should include a concise summary, changed skill directories, validation commands run, and any known gaps. Link related issues when available. Include screenshots only for visual assets or UI-facing documentation.

## Security & Configuration Tips

Do not commit secrets, local tokens, cookies, `.env` files, chat history, or generated runtime artifacts. Do not push, pull, fetch, or modify Git remotes unless explicitly requested by the maintainer.
