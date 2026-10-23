---
paths:
  - "app/ingestion/messaging/**"
---

# RabbitMQ rules (shared, synced from ragstudio-claude-plugin; do not edit here)

- Event names and payloads come from the catalog (architecture skill, `references/events.md`).
  Anything not in the catalog is a contract change: stop and use the `ragstudio-core:new-event` skill.
- Library: `aio-pika` with `connect_robust`. Exchange `ragstudio.events` (topic, durable).
- Queues: `ai-ingestion-worker.<routing-key>`, durable, DLQ `<queue>.dlq`. Only `app/ingestion/` consumes or publishes;
  `app/rag/` never touches RabbitMQ.
- `prefetch_count` = worker concurrency (default 4). Ack only after the work and its DB commit succeed;
  on failure, reject without requeue after 3 attempts so it lands in the DLQ.
- Envelope is a Pydantic model `EventEnvelope[T]` (eventId, type, version, occurredAt, producer, payload) with `extra="ignore"`.
- Handlers are idempotent: re-processing the same document and index version replaces its chunks, never duplicates them.
- Publish status events only after the DB commit.
- Patterns: `ragstudio-python:python-messaging` skill.
