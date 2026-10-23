"""PreToolUse guard: keeps noise and secrets out of Claude's context.

Denies (with a reason Claude can act on):
  - Read/Grep/Glob inside build output, virtualenvs, caches and dependency folders
  - Read of secrets (.env, keystores, private keys) and of lock files
  - Read of a large file without offset/limit (asks for Grep or a slice instead)
  - Bash commands that dump those same files (cat/head/tail/less on them)
  - Edit/Write that puts a literal secret into a config file (use ${ENV_VAR} instead)

Everything else passes untouched. Any internal error lets the call through (fail open).
"""
import json
import os
import re
import sys

NOISE_DIRS = (
    "build", "target", "out", ".gradle", "bin/main", "bin/test", ".venv", "venv",
    "node_modules", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    ".idea", "htmlcov", "dist", ".git",
)
LOCK_FILES = ("uv.lock", "poetry.lock", "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "gradle.lockfile")
SECRET_FILE = re.compile(r"(^|/)(\.env(\..+)?|.*\.(pem|key|p12|jks|keystore|pfx)|id_rsa.*|credentials\.json)$")
SECRET_FILE_ALLOW = re.compile(r"\.env\.(example|sample|template)$")
BINARY_EXT = (".jar", ".class", ".war", ".zip", ".tar", ".gz", ".png", ".jpg", ".jpeg", ".gif", ".pdf", ".pyc", ".so", ".dll")
MAX_READ_BYTES = 256 * 1024  # larger files need offset/limit or Grep
CONFIG_EXT = (".yml", ".yaml", ".properties", ".toml", ".env", ".conf", ".ini")
SECRET_ASSIGN = re.compile(
    r"(?im)^\s*[\w.\-]*(password|passwd|secret|client[-_]?secret|api[-_]?key|access[-_]?key|private[-_]?key|token)"
    r"[\w.\-]*\s*[:=]\s*['\"]?(?!\$\{|\$\(|<|['\"]?\s*$)([^\s'\"#]{8,})"
)
DUMP_CMD = re.compile(r"(^|[\s;&|(])(cat|less|more|head|tail|bat|strings|xxd)\s+([^;&|]+)")


def norm(path: str) -> str:
    if not path:
        return ""
    p = path.replace("\\", "/")
    root = (os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()).replace("\\", "/").rstrip("/")
    if p.startswith(root + "/"):
        p = p[len(root) + 1:]
    while p.startswith("./"):
        p = p[2:]
    return p


def in_noise_dir(rel: str) -> str:
    parts = "/" + rel.strip("/") + "/"
    for d in NOISE_DIRS:
        if f"/{d}/" in parts:
            return d
    return ""


def deny(reason: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))
    sys.exit(0)


def check_path(rel: str, raw: str, tool: str, tool_input: dict) -> None:
    if not rel:
        return
    d = in_noise_dir(rel)
    if d:
        deny(f"'{rel}' is inside '{d}/' (generated or dependency files). Work from source files instead; "
             "for test results ask the test-runner agent.")
    if SECRET_FILE.search(rel) and not SECRET_FILE_ALLOW.search(rel):
        deny(f"'{rel}' may contain secrets and is blocked. Use the .env.example file or ask the user for the key name.")
    if tool != "Read":
        return
    name = rel.rsplit("/", 1)[-1]
    if name in LOCK_FILES:
        deny(f"'{name}' is a lock file. Use Grep for the one package you need.")
    if rel.lower().endswith(BINARY_EXT) and not rel.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".pdf")):
        deny(f"'{rel}' is a binary artifact; it cannot help here.")
    if tool_input.get("offset") or tool_input.get("limit") or tool_input.get("pages"):
        return
    try:
        size = os.path.getsize(raw)
    except OSError:
        return
    if size > MAX_READ_BYTES and not rel.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".pdf")):
        deny(f"'{rel}' is {size // 1024} KB. Grep for what you need, or Read with offset/limit (about 200 lines at a time).")


def check_bash(cmd: str) -> None:
    for m in DUMP_CMD.finditer(cmd):
        for arg in m.group(3).split():
            if arg.startswith("-"):
                continue
            rel = norm(arg.strip("'\""))
            d = in_noise_dir(rel)
            if d:
                deny(f"Dumping files from '{d}/' floods the context. Use Grep with a pattern, "
                     "or the test-runner agent for test output.")
            if SECRET_FILE.search(rel) and not SECRET_FILE_ALLOW.search(rel):
                deny(f"'{rel}' may contain secrets and is blocked.")
            if rel.rsplit("/", 1)[-1] in LOCK_FILES:
                deny(f"'{rel}' is a lock file. Grep it for the package you need.")


def check_write(rel: str, tool_input: dict) -> None:
    if not rel.lower().endswith(CONFIG_EXT) and ".env" not in rel:
        return
    if "/test/" in f"/{rel}" or "local" in rel.rsplit("/", 1)[-1]:
        return  # test fixtures and local dev profiles may hold throwaway values
    text = tool_input.get("content") or tool_input.get("new_string") or ""
    m = SECRET_ASSIGN.search(text)
    if m:
        deny(f"This edit puts a literal value for '{m.group(1)}' in '{rel}'. Secrets live in Kubernetes Secrets; "
             "reference them as ${ENV_VAR_NAME} and tell the user which variable to create.")


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return
    tool = data.get("tool_name", "")
    ti = data.get("tool_input") or {}
    try:
        if tool == "Read":
            raw = ti.get("file_path", "")
            check_path(norm(raw), raw, tool, ti)
        elif tool in ("Grep", "Glob"):
            raw = ti.get("path", "")
            check_path(norm(raw), raw, tool, ti)
        elif tool == "Bash":
            check_bash(ti.get("command", ""))
        elif tool in ("Edit", "Write"):
            raw = ti.get("file_path", "")
            rel = norm(raw)
            if SECRET_FILE.search(rel) and not SECRET_FILE_ALLOW.search(rel):
                deny(f"'{rel}' is a secrets file and must not be written by Claude.")
            check_write(rel, ti)
    except SystemExit:
        raise
    except Exception:
        return


if __name__ == "__main__":
    main()
