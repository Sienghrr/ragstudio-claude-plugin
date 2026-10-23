#!/usr/bin/env bash
# Runs a hook script with whichever Python 3.8+ is installed (python3 on macOS/Linux, python on Windows Git Bash).
# Fails open: if no Python is found the hook exits 0 and Claude carries on without it.
script="$1"
shift
for py in python3 python; do
  if command -v "$py" >/dev/null 2>&1 && "$py" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' >/dev/null 2>&1; then
    exec "$py" "$script" "$@"
  fi
done
exit 0
