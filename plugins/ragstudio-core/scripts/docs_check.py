"""Stop hook: keeps the docs in step with the code, automatically.

When Claude is about to finish and source files changed but no doc file did, it blocks the stop ONCE for that set of
changes and asks Claude to run the doc-writer agent. It never nags twice for the same changes, never loops
(stop_hook_active), and stays silent in repos without code or when docs were already touched.

Turn it off for yourself: set RAGSTUDIO_AUTO_DOCS=0 in the "env" of .claude/settings.local.json.
"""
import hashlib
import json
import os
import subprocess
import sys

SOURCE_PREFIXES = ("src/main/", "app/", "migrations/")
DOC_FILES = ("README.md", "CHANGELOG.md")
DOC_PREFIX = "docs/"


def git(root: str, *args: str) -> str:
    r = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, timeout=15)
    return r.stdout if r.returncode == 0 else ""


def main() -> int:
    data = json.load(sys.stdin)
    if data.get("stop_hook_active"):
        return 0
    if os.environ.get("RAGSTUDIO_AUTO_DOCS", "1").lower() in ("0", "false", "off", "no"):
        return 0
    root = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd()
    if not (os.path.exists(os.path.join(root, "gradlew")) or os.path.exists(os.path.join(root, "pyproject.toml"))):
        return 0

    changed = []
    for line in git(root, "status", "--porcelain", "--untracked-files=all").splitlines():
        if len(line) > 3:
            path = line[3:].strip().split(" -> ")[-1].strip('"')
            changed.append(path)
    source = [c for c in changed if c.startswith(SOURCE_PREFIXES) and os.path.isfile(os.path.join(root, c))]
    docs = [c for c in changed if c in DOC_FILES or c.startswith(DOC_PREFIX)]
    if not source:
        return 0

    h = hashlib.sha1()
    for f in sorted(source):
        h.update(f.encode())
        h.update(str(os.path.getmtime(os.path.join(root, f))).encode())
    fingerprint = h.hexdigest()
    base = os.environ.get("CLAUDE_PLUGIN_DATA") or os.path.join(os.path.expanduser("~"), ".cache", "ragstudio-claude")
    os.makedirs(base, exist_ok=True)
    cf = os.path.join(base, "docs-" + hashlib.sha1(root.encode()).hexdigest()[:16])
    seen = open(cf).read().strip() if os.path.exists(cf) else ""
    with open(cf, "w") as f:
        f.write(fingerprint)
    if docs or seen == fingerprint:
        return 0

    shown = "\n".join(f"  {s}" for s in source[:10])
    more = f"\n  ... and {len(source) - 10} more" if len(source) > 10 else ""
    sys.stderr.write(
        "Code changed but the docs did not:\n" + shown + more + "\n"
        "Before finishing, run the `ragstudio-core:doc-writer` agent on these changes "
        "(README.md, docs/api.md, docs/events.md, docs/data.md, CHANGELOG.md as needed) and relay its summary in one or two lines. "
        "If the change is only a refactor, tests or formatting, say 'No doc change needed' and finish.\n"
    )
    return 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
