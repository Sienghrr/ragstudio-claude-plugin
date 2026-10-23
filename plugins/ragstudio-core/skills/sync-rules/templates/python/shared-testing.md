---
paths:
  - "tests/**"
  - "conftest.py"
---

# Testing rules (shared, synced from ragstudio-claude-plugin; do not edit here)

- pytest + pytest-asyncio (`asyncio_mode = "auto"`), httpx `AsyncClient` with `ASGITransport` for API tests.
- Integration tests use testcontainers (`pgvector/pgvector:pg16`, `rabbitmq:3.13`); mark them `@pytest.mark.integration`.
- Never call a real Ollama in tests: inject a fake embedding/chat client that returns fixed vectors and text.
- Parser tests keep small fixture files in `tests/fixtures/` (one per type: pdf, docx, md, xlsx, txt, html)
  and assert location fields (page, heading, sheet + rows, lines).
- Retrieval tests assert chatbot isolation (a chunk from another chatbot never comes back) and index_version filtering.
- Run one file yourself: `uv run pytest tests/<file>.py -q`. Delegate the full suite to `ragstudio-python:python-test-runner`.
