"""SessionStart hook: gives Claude a few lines of orientation so it does not spend turns running git commands.

Adds: repo name, stack, branch, up to 10 changed files, last 3 commits, and a pointer to a handoff note
if one was written in the last 3 days. Output stays well under 1,500 characters.
"""
import json
import os
import subprocess
import sys
import time


def git(*args: str) -> str:
    try:
        r = subprocess.run(["git", *args], capture_output=True, text=True, timeout=5)
        return r.stdout.strip() if r.returncode == 0 else ""
    except Exception:
        return ""


def main() -> None:
    try:
        json.load(sys.stdin)
    except Exception:
        pass
    root = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    os.chdir(root)
    repo = os.path.basename(root.rstrip("/\\"))
    stack = "spring (gradle)" if os.path.exists("gradlew") else "python (uv)" if os.path.exists("pyproject.toml") else "config/docs"
    lines = [f"Repo: {repo} | stack: {stack}"]

    branch = git("rev-parse", "--abbrev-ref", "HEAD")
    if branch:
        lines.append(f"Branch: {branch}")
        status = [l for l in git("status", "--porcelain").splitlines() if l.strip()]
        if status:
            shown = "\n".join("  " + s for s in status[:10])
            more = f"\n  ... and {len(status) - 10} more" if len(status) > 10 else ""
            lines.append(f"Uncommitted changes ({len(status)}):\n{shown}{more}")
        else:
            lines.append("Working tree clean.")
        log = git("log", "--oneline", "-3")
        if log:
            lines.append("Recent commits:\n" + "\n".join("  " + l for l in log.splitlines()))

    note = os.path.join(root, ".claude", "handoff.md")
    if os.path.exists(note) and time.time() - os.path.getmtime(note) < 3 * 86400:
        age_h = int((time.time() - os.path.getmtime(note)) / 3600)
        lines.append(f"A handoff note from a previous session exists at .claude/handoff.md ({age_h} h old). "
                     "Read it first if the user is continuing earlier work.")

    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "\n".join(lines)}}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)
