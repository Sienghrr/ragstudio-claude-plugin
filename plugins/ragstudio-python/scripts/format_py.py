"""PostToolUse hook: runs Ruff format and safe fixes on the Python file Claude just edited. Always silent."""
import json
import os
import shutil
import subprocess
import sys


def ruff_cmd(root: str) -> list:
    if shutil.which("uv") and os.path.exists(os.path.join(root, "pyproject.toml")):
        return ["uv", "run", "--quiet", "ruff"]
    if shutil.which("ruff"):
        return ["ruff"]
    return []


def main() -> None:
    data = json.load(sys.stdin)
    path = (data.get("tool_input") or {}).get("file_path", "")
    if not path.endswith(".py"):
        return
    root = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd()
    ruff = ruff_cmd(root)
    if not ruff:
        return
    subprocess.run([*ruff, "format", "--quiet", path], cwd=root, capture_output=True, timeout=25)
    subprocess.run([*ruff, "check", "--fix", "--quiet", path], cwd=root, capture_output=True, timeout=25)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
