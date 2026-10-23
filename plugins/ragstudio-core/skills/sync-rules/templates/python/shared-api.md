---
paths:
  - "app/*/api/**"
  - "app/*/main.py"
---

# FastAPI rules (shared, synced from ragstudio-claude-plugin; do not edit here)

- Routers in `app/rag/api/<area>.py` (RAG API, mounted under `/v1`) or `app/ingestion/api/` (worker health and metrics only).
  Health at `/health/live` and `/health/ready` in both deployments.
- Request/response models are Pydantic v2 models in `app/<side>/api/schemas/`; never return ORM rows or dicts.
- Handlers are thin and `async`: validate, call one function in `app/<side>/services/`, return the schema.
- Errors: raise domain exceptions; one exception handler maps them to RFC 9457 problem JSON
  (`type`, `title`, `status`, `detail`, `errorCode`).
- Auth: endpoints are cluster-internal; verify the caller's Keycloak client-credentials JWT (`service` role)
  in a dependency, except health and metrics.
- Streaming answers use Server-Sent Events (`text/event-stream`): `token` events, then one `final` event with
  citations and usage, then close. Send a heartbeat comment every 15 s.
- Settings come from `app/core/settings.py`: it asks config-server for `ai-ingestion-worker` or `ai-rag-service` (env `APP_NAME`)
  and lets env vars override. No `os.getenv` elsewhere.
