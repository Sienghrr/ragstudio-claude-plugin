"""Stop hook: lint the Python files changed in this session with Ruff before Claude finishes.

Skips when no .py file changed or the same changes already passed. On findings, exits 2 with at most
30 concise lines so Claude fixes them. Respects stop_hook_active to avoid loops.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys


def git(root: str, *args: str) -> str:
    r = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, timeout=15)
    return r.stdout if r.returncode == 0 else ""


def main() -> int:
    data = json.load(sys.stdin)
    if data.get("stop_hook_active"):
        return 0
    root = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd()
    changed = [l[3:].strip() for l in git(root, "status", "--porcelain", "--untracked-files=all").splitlines() if len(l) > 3]
    files = [c for c in changed if c.endswith(".py") and os.path.isfile(os.path.join(root, c))]
    if not files:
        return 0

    h = hashlib.sha1()
    for f in sorted(files):
        h.update(f.encode())
        h.update(str(os.path.getmtime(os.path.join(root, f))).encode())
    base = os.environ.get("CLAUDE_PLUGIN_DATA") or os.path.join(os.path.expanduser("~"), ".cache", "ragstudio-claude")
    os.makedirs(base, exist_ok=True)
    cf = os.path.join(base, "ruff-" + hashlib.sha1(root.encode()).hexdigest()[:16])
    if os.path.exists(cf) and open(cf).read().strip() == h.hexdigest():
        return 0

    if shutil.which("uv") and os.path.exists(os.path.join(root, "pyproject.toml")):
        ruff = ["uv", "run", "--quiet", "ruff"]
    elif shutil.which("ruff"):
        ruff = ["ruff"]
    else:
        return 0
    r = subprocess.run([*ruff, "check", "--output-format", "concise", *files],
                       cwd=root, capture_output=True, text=True, timeout=100)
    if r.returncode == 0:
        with open(cf, "w") as f:
            f.write(h.hexdigest())
        return 0
    lines = [l for l in r.stdout.splitlines() if l.strip() and not l.startswith("Found ")]
    sys.stderr.write("Ruff found problems in files you changed. Fix them before finishing:\n" + "\n".join(lines[:30]) + "\n")
    return 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
