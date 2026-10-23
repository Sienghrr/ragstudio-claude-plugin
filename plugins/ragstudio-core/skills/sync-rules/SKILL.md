---
name: sync-rules
description: Copy the team's latest shared path-scoped rules from this plugin into the current repo's .claude/rules folder. Run after the plugin updates.
disable-model-invocation: true
allowed-tools: Bash(ls:*), Bash(cp:*), Bash(diff:*), Bash(mkdir:*)
---

# Sync shared rules into this repo

Templates in this skill: `${CLAUDE_SKILL_DIR}/templates/spring/` and `${CLAUDE_SKILL_DIR}/templates/python/`.

1. Pick the stack: `gradlew` in the repo root means `spring`, `pyproject.toml` means `python`.
   If neither exists, say there are no shared rules for this repo and stop.
2. Run `mkdir -p .claude/rules`, then for each template file show `diff -q` against `.claude/rules/<same name>`.
3. Copy the changed or missing files with `cp`. Only files named `shared-*.md` are managed here;
   never touch other files in `.claude/rules/` (those are this service's own rules).
4. Report which files changed, in one line each. Remind the user to commit `.claude/rules/`.
