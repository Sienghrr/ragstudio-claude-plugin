---
name: pr-ready
description: Prepare the current branch for a pull request - run tests and review through subagents in parallel, check contracts, then draft the PR title and description.
disable-model-invocation: true
argument-hint: "[base branch, default main]"
---

# Get this branch PR-ready

Base branch: `$ARGUMENTS` (use `main` if empty).

Current state:
!`git status --short 2>/dev/null | head -40 || true`

Changed files vs main (if the base is another branch, run `git diff --stat <base>...HEAD` yourself):
!`git diff --stat main...HEAD 2>/dev/null | tail -40; true`

## Steps

1. Work out the stack from the repo: `gradlew` present means Spring, `pyproject.toml` means Python.
2. In ONE message, start these subagents in parallel (do not run the suites yourself):
   - Spring: `ragstudio-spring:spring-test-runner` (full suite) and `ragstudio-spring:spring-reviewer` (diff vs base).
   - Python: `ragstudio-python:python-test-runner` (full suite) and `ragstudio-python:python-reviewer` (diff vs base).
   - Also `ragstudio-core:contract-checker` when the diff touches events, listeners, publishers,
     `/internal/**` controllers or clients, or migrations.
   - Also `ragstudio-core:doc-writer` on the whole branch (`main...HEAD`), so README, docs/ and CHANGELOG match it.
3. Fix only blocking findings (failing tests, compile errors, contract mismatches, HIGH review items).
   List MEDIUM and LOW items for the user instead of fixing them unasked.
4. Re-run only the test classes that failed (directly, with `--tests` or `-k`), not the whole suite.
5. Reply with:
   - A PR title (`<type>(<service>): <summary>`, type = feat, fix, refactor, test, chore, docs).
   - A PR body in Markdown: Summary (3 bullets max), Contracts touched (events / internal APIs / migrations, or "none"),
     Docs updated (files from the doc-writer), Testing (what ran, result), Follow-ups (unfixed review items).
6. Do not commit, push or open the PR unless the user asks.
