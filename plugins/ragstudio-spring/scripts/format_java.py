"""PostToolUse hook: formats the Java file Claude just edited with Spotless, so Claude never spends turns on formatting.

Runs only for .java files in a Gradle project whose build.gradle.kts applies Spotless.
Silent on success and on failure (formatting must never block work).
"""
import json
import os
import subprocess
import sys


def main() -> None:
    data = json.load(sys.stdin)
    path = (data.get("tool_input") or {}).get("file_path", "")
    if not path.endswith(".java"):
        return
    root = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd()
    gradlew = os.path.join(root, "gradlew.bat" if os.name == "nt" else "gradlew")
    build = os.path.join(root, "build.gradle.kts")
    if not (os.path.exists(gradlew) and os.path.exists(build)):
        return
    with open(build, encoding="utf-8", errors="ignore") as f:
        if "spotless" not in f.read():
            return
    subprocess.run(
        [gradlew, "spotlessApply", f"-PspotlessIdeHook={os.path.abspath(path)}", "-q"],
        cwd=root, capture_output=True, timeout=80,
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
