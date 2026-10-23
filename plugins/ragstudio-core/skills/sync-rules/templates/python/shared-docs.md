---
paths:
  - "README.md"
  - "CHANGELOG.md"
  - "docs/**"
---

# Documentation rules (shared, synced from ragstudio-claude-plugin; do not edit here)

- The doc set is fixed: `README.md`, `docs/api.md`, `docs/events.md`, `docs/data.md`, `CHANGELOG.md`. No other doc files.
- Docs describe the code as it is. Write `TODO(owner): <question>` instead of guessing.
- Edit only the sections a change affects; keep the templates' section order (the `ragstudio-core:docs-writer` skill).
- Event names, payloads and tables must agree with the architecture skill; report disagreements instead of editing around them.
- CHANGELOG lines go under `## [Unreleased]`, one per user-visible change, naming the endpoint, event or table.
- English, short, tables over prose. Fake example data only; never tokens, secrets or real user data.
