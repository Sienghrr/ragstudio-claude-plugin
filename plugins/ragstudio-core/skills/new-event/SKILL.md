---
name: new-event
description: Add or change a RabbitMQ event between RAGStudio services - catalog first, then producer and consumer code with the shared envelope, queue naming and idempotency rules. Use when a task needs one service to tell another that something happened.
argument-hint: "<routing.key> [producer] [consumers]"
---

# Add or change an event: $ARGUMENTS

1. Grep `references/events.md` in the `architecture` skill for the routing key.
   - Exists: use its payload exactly. Do not add fields silently.
   - New or changed: draft the catalog row (routing key `<domain>.<entity>.<past-tense-verb>` or
     `<domain>.<thing>-<verb>`, producer, consumers, payload fields with types) and show it to the user.
     Tell them the catalog lives in `ragstudio-claude-plugin` and needs its own pull request.
     Continue only after the user confirms the row.
2. Implement only the side that lives in THIS repo:
   - Spring producer or consumer: follow the `ragstudio-spring:spring-messaging` skill.
   - Python producer or consumer: follow the `ragstudio-python:python-messaging` skill.
3. Producer checklist: envelope fields (eventId, type, version, occurredAt, producer, payload); publish after commit;
   no secrets or full guest text in the payload.
4. Consumer checklist: queue `<service-name>.<routing-key>`, DLQ `<queue>.dlq`, idempotent handling, unknown fields ignored.
5. Add a test: producer test asserts the routing key and payload JSON; consumer test feeds a sample envelope
   and checks the state change, including a duplicate delivery.
6. Finish with a list of the OTHER repos that must change (from the catalog's producer/consumer columns).
