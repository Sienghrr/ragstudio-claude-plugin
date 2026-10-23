---
name: architecture
description: RAGStudio cross-service facts - which service owns which table, RabbitMQ event names and payloads, internal APIs, gateway routes, and business rules from the feature spec. Use whenever a task touches another service, an event, an internal endpoint, table columns, status transitions or limits, instead of guessing or searching other repos.
---

# RAGStudio architecture reference

Read ONLY the reference file the task needs. Each is self-contained.

| Need | File |
|---|---|
| Table columns, types, enums, constraints, which service owns a table | `references/erd.md` |
| Event names, envelope, payload fields, producers/consumers, re-index and deletion flows | `references/events.md` |
| Repos, ports, gateway routes, internal APIs, cache keys | `references/services.md` |
| Status transitions, limits, messages shown to guests, feature rules | `references/business-rules.md` |

Tips to keep context small:
- Use Grep on a reference file for one table or event instead of reading the whole file,
  e.g. grep `^chatbot_configs` -A 30 in erd.md, or `chatbot.status-changed` in events.md.
- These files are the contract. If the code in this repo disagrees, say so and ask before changing either.
- Never edit these files from a service repo. Contract changes are a pull request to `ragstudio-claude-plugin`.
