# ragstudio-claude-plugin

Shared Claude Code setup for the RAGStudio team: one private plugin marketplace with three plugins.
Every service repo's `.claude/settings.json` points here, so teammates are prompted to install the plugins
the first time they open a repo and trust the folder. Update this repo once and everyone gets the change.

| Plugin | Enable in | What it adds |
|---|---|---|
| `ragstudio-core` | every repo | `architecture` and `docs-writer` skills; `contract-checker` and `doc-writer` agents; `/ragstudio-core:pr-ready`, `/ragstudio-core:handoff`, `/ragstudio-core:new-event`, `/ragstudio-core:sync-rules`; read-guard, session-context and auto-docs hooks |
| `ragstudio-spring` | Spring repos | `spring-endpoint`, `spring-messaging`, `flyway-migration` skills; `spring-reviewer`, `spring-test-runner` agents; Spotless format-on-edit and compile-on-stop hooks; `rs-test-java` command |
| `ragstudio-python` | Python repos | `fastapi-endpoint`, `python-messaging`, `alembic-migration` skills; `python-reviewer`, `python-test-runner` agents; Ruff format-on-edit and lint-on-stop hooks; `rs-test-py` command |

Splitting by stack keeps Java skills and agents out of Python sessions and the reverse: only names and
descriptions of enabled components sit in context, and every disabled plugin costs nothing.

## Where the token savings come from

| Mechanism | What it replaces |
|---|---|
| Short `CLAUDE.md` per repo (about 45 lines) | Long always-loaded instructions |
| Path-scoped `.claude/rules/*.md` | Rules that only load when Claude touches matching files (API, persistence, messaging, tests, build) |
| `architecture` skill with 4 reference files | Pasting the 70-page PDF or the ERD image, or Claude searching other repos |
| Test-runner agents on Haiku with `omitClaudeMd` | Thousands of lines of Gradle or pytest output in the main conversation |
| Reviewer and contract-checker agents | Re-reading the whole diff and the contracts in the main conversation |
| `rs-test-java` / `rs-test-py` | Full test logs; they print totals and failures only |
| Format-on-edit hooks | Turns spent fixing formatting or re-running formatters |
| Stop hooks (compile / Ruff) | Turns spent discovering compile errors later; only error lines are returned |
| Read guard hook + deny rules | Reads of `build/`, `.venv/`, lock files, logs, secrets and files over 256 KB |
| SessionStart hook | Git commands at the start of every session |
| Auto-docs Stop hook + `doc-writer` agent | Writing docs in the main conversation; the agent reads only the changed code and edits only affected sections |
| `/ragstudio-core:handoff` | Re-exploring the code after `/clear` or a new session |
| `BASH_MAX_OUTPUT_LENGTH=20000` | 30,000-character command outputs (default) |

## Install (team lead, once)

1. Create a private GitHub repo `<your-org>/ragstudio-claude-plugin` and push this folder as its root.
2. Check it: `claude plugin validate ./plugins/ragstudio-core` (and the other two).
3. From the setup kit, run `./bootstrap.sh <your-org> <folder-with-cloned-repos>`, then commit in each repo.

## Install (each teammate)

1. Make sure you can clone `<your-org>/ragstudio-claude-plugin` (GitHub access to the org).
2. Open any service repo with `claude`, accept the "trust this folder" prompt, then accept the plugin install prompt.
   If it says a plugin is enabled but not installed, run `/plugin`, open the `ragstudio` marketplace and install.
3. Requirements: `bash` (Git Bash on Windows), Python 3.8+ on PATH as `python3` or `python` (hooks are stdlib-only),
   `uv` for Python repos, Spotless applied in Spring repos' `build.gradle.kts`.

## Changing contracts

`plugins/ragstudio-core/skills/architecture/references/` is the single source of truth for table ownership,
events, internal APIs and business rules. Change it here first, by pull request, then change the services.
Bump `version` in the plugin's `.claude-plugin/plugin.json` so auto-update picks it up.

## Changing shared rules

Edit `plugins/ragstudio-core/skills/sync-rules/templates/{spring,python}/shared-*.md`, merge, then in each repo
run `/ragstudio-core:sync-rules` and commit `.claude/rules/`.

## Turning a hook off for yourself

Auto-docs only: add `"env": {"RAGSTUDIO_AUTO_DOCS": "0"}` to your `.claude/settings.local.json`. Run `/ragstudio-core:docs-writer` by hand when you want docs.


Put overrides in `.claude/settings.local.json` (gitignored) or disable a plugin with `/plugin`. Do not edit the
shared settings for a personal preference.
