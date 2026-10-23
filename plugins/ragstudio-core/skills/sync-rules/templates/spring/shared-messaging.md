---
paths:
  - "src/main/java/**/infrastructure/messaging/**"
  - "src/main/java/**/*Event.java"
  - "src/main/java/**/*Listener.java"
  - "src/main/java/**/*Publisher.java"
---

# RabbitMQ rules (shared, synced from ragstudio-claude-plugin; do not edit here)

- Event names, payloads, producers and consumers come from the catalog (architecture skill, `references/events.md`).
  A routing key or field that is not in the catalog is a contract change: stop and use the `ragstudio-core:new-event` skill.
- One topic exchange `ragstudio.events`. Routing key = event name.
- Queues: `<spring.application.name>.<routing-key>`, durable, with DLQ `<queue>.dlq`; 3 retries with backoff, then DLQ.
  analytics-notification-service adds the module: `<app-name>.analytics.<key>` / `<app-name>.notification.<key>`.
- Envelope record `EventEnvelope<T>(UUID eventId, String type, int version, Instant occurredAt, String producer, T payload)`;
  JSON via `Jackson2JsonMessageConverter`, `FAIL_ON_UNKNOWN_PROPERTIES = false`.
- Publish after commit: application code raises a Spring `ApplicationEvent`; an
  `@TransactionalEventListener(phase = AFTER_COMMIT)` publisher sends it to RabbitMQ.
- Consumers are idempotent: apply state only if it changes something (status already applied, row already deleted)
  and log `eventId` at INFO.
- Never put secrets, raw documents or guest message text in a payload.
- Patterns: `ragstudio-spring:spring-messaging` skill.
