---
name: docs-writer
description: Write or update a RAGStudio service repo's documentation from its code - README.md, docs/api.md, docs/events.md, docs/data.md and CHANGELOG.md - touching only the sections the change affects. Use after implementing or changing endpoints, events, listeners, migrations, configuration keys or behaviour, or when asked to document the service.
argument-hint: "[what changed, or 'all' to rebuild every doc]"
---

# Write the docs: $ARGUMENTS

Prefer running this through the `ragstudio-core:doc-writer` agent so the reading stays out of the main conversation.

## The doc set (English, Markdown, in the repo)

| File | Holds | Update when the diff touches |
|---|---|---|
| `README.md` | Purpose, responsibilities, tables owned, run locally, config keys, docs index | Run commands, config keys (`@ConfigurationProperties`, `@Value`, settings fields), new responsibilities |
| `docs/api.md` | One section per endpoint: auth, request, response, errors | Controllers / routers, request and response DTOs, error mapping |
| `docs/events.md` | Events published and consumed, with queues | Publishers, listeners, queue config |
| `docs/data.md` | Tables owned, key constraints, migration history | Flyway / Alembic migrations, entities |
| `CHANGELOG.md` | One line per user-visible change under `## [Unreleased]` | Every change except pure refactors, tests and formatting |

Templates for a missing file: `${CLAUDE_SKILL_DIR}/templates/<file>` (copy, then fill). Never create other doc files.

## Steps

1. Find what changed: `git diff --name-only HEAD` plus `git status --short` (or `main...HEAD` when asked for a branch).
   Ignore tests, formatting-only edits and files under `docs/` themselves.
2. Map each changed file to the docs in the table. Pure refactor or test-only change: update nothing, say so in one line.
3. For each affected doc, read only the code that defines the facts (the controller method, the DTO record, the listener,
   the migration), with Grep first and Read with offset/limit.
4. Edit only the affected sections with Edit; keep every other line as it is. Keep sections in the template's order;
   endpoints sorted by path then method; events sorted by routing key.
5. CHANGELOG: add lines under `## [Unreleased]` in `### Added`, `### Changed`, `### Fixed` or `### Removed`,
   each naming the endpoint, event or table, e.g. `- POST /api/chatbots/{id}/publish checks the publish checklist`.

## Rules

- Document only what the code shows. If a fact is unclear (an error's meaning, a default), write `TODO(owner): <question>`
  rather than guessing.
- Event names and payloads must match the architecture skill's `references/events.md`; table definitions must match
  `references/erd.md`. If the code disagrees with them, do not "fix" the docs to match either side: report the mismatch.
- Never edit the architecture references from a service repo.
- Examples use realistic fake data (UUIDs like `3f2a9c1e-...`, `owner@example.com`); never real tokens, secrets or user data.
- Short: a section per endpoint is about 15 lines; tables over prose; no marketing words.
- Finish with one line per file changed: `docs/api.md - added POST /api/chatbots/{id}/pause`.
