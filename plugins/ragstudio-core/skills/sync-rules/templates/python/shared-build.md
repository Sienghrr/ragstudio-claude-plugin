---
paths:
  - "pyproject.toml"
  - "Dockerfile"
  - ".github/workflows/**"
---

# Build rules (shared, synced from ragstudio-claude-plugin; do not edit here)

- Python 3.12, uv for everything: `uv add <pkg>`, `uv sync`, `uv run <cmd>`. Never pip install, never edit `uv.lock` by hand.
- Ruff is the formatter and linter (`line-length = 100`, rules `E,F,I,B,UP,ASYNC`); the hooks run it on every edit.
- Type hints on every public function; `mypy --strict` runs in CI only.
- Add a dependency only when the task needs it, and say why in the reply.
- Dockerfile: `python:3.12-slim`, uv in a build stage, non-root user, `uvicorn app.main:app --host 0.0.0.0 --port 8000`.
- CI (`.github/workflows/ci.yml`): `uv sync --frozen`, `uv run ruff check`, `uv run ruff format --check`, `uv run pytest -m "not integration"`,
  then integration tests, then build and push the image on `main`.
