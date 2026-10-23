"""Stop hook: before Claude finishes, compile main and test code if Java/Gradle files changed.

- Skips when nothing relevant changed, or when the same changes already compiled (fingerprint cache).
- On failure, exits 2 with ONLY the compiler error lines (max 30), so Claude fixes them before stopping.
- Respects stop_hook_active so it never loops: a second consecutive failure lets Claude stop and report.
"""
import hashlib
import json
import os
import re
import subprocess
import sys

RELEVANT = (".java", ".kts", ".gradle", ".toml")


def git(root: str, *args: str) -> str:
    r = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, timeout=15)
    return r.stdout if r.returncode == 0 else ""


def cache_file(root: str) -> str:
    base = os.environ.get("CLAUDE_PLUGIN_DATA") or os.path.join(os.path.expanduser("~"), ".cache", "ragstudio-claude")
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, "compile-" + hashlib.sha1(root.encode()).hexdigest()[:16])


def main() -> int:
    data = json.load(sys.stdin)
    if data.get("stop_hook_active"):
        return 0
    root = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd()
    gradlew = os.path.join(root, "gradlew.bat" if os.name == "nt" else "gradlew")
    if not os.path.exists(gradlew):
        return 0

    changed = [l[3:].strip() for l in git(root, "status", "--porcelain", "--untracked-files=all").splitlines() if len(l) > 3]
    changed = [c for c in changed if c.endswith(RELEVANT)]
    if not changed:
        return 0

    h = hashlib.sha1(git(root, "diff", "HEAD").encode())
    for c in sorted(changed):
        p = os.path.join(root, c)
        if os.path.isfile(p):
            h.update(c.encode())
            h.update(str(os.path.getmtime(p)).encode())
    fingerprint = h.hexdigest()
    cf = cache_file(root)
    if os.path.exists(cf) and open(cf).read().strip() == fingerprint:
        return 0

    r = subprocess.run([gradlew, "compileJava", "compileTestJava", "-q", "--console=plain"],
                       cwd=root, capture_output=True, text=True, timeout=280)
    if r.returncode == 0:
        with open(cf, "w") as f:
            f.write(fingerprint)
        return 0

    out = (r.stdout + "\n" + r.stderr).splitlines()
    picked = []
    for i, line in enumerate(out):
        if re.search(r"\.java:\d+: error:", line) or line.startswith("e: "):
            picked.extend(out[i:i + 3])
    if not picked:
        picked = [l for l in out if l.strip()][-25:]
    root_slash = root.rstrip("/\\") + os.sep
    msg = "\n".join(l.replace(root_slash, "") for l in picked[:30])
    sys.stderr.write("Compilation failed. Fix these errors before finishing (from ./gradlew compileJava compileTestJava):\n" + msg + "\n")
    return 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except subprocess.TimeoutExpired:
        sys.exit(0)
    except Exception:
        sys.exit(0)
