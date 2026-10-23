---
name: handoff
description: Write a short handoff note to .claude/handoff.md so the next session (yours or a teammate's on the same machine) continues without re-exploring the code. Run before /clear or at the end of a long session.
disable-model-invocation: true
---

# Write the handoff note

Overwrite `.claude/handoff.md` (it is gitignored) with at most 40 lines, in this shape:

```markdown
# Handoff - <one-line goal> (<date>)

## Done
- <what is finished, with file paths>

## In progress
- <what is half done and exactly where it stopped>

## Next
1. <next concrete step>

## Facts learned
- <non-obvious things found while working: a quirk, a command that works, a decision the user made>

## Files that matter
- path/to/File.java - why
```

Rules:
- Facts only from this session. No code blocks longer than 5 lines.
- Paths relative to the repo root.
- After writing, tell the user they can run `/clear`; the SessionStart hook will point the new session at the note.
