# <service-name> events

Exchange `ragstudio.events` (topic). Envelope fields: `eventId`, `type`, `version`, `occurredAt`, `producer`, `payload`.
The contract is the event catalog in `ragstudio-claude-plugin`; this page lists this service's side of it.

## Published

| Routing key | Published when | Payload fields |
|---|---|---|
| `<domain.event>` | <after which action, after commit> | `chatbotId`, `ownerId` |

## Consumed

| Routing key | Queue | What this service does | Idempotency |
|---|---|---|---|
| `<domain.event>` | `<service>.<domain.event>` | <state change> | <why a duplicate is harmless> |

Failed messages retry 3 times, then go to `<queue>.dlq`.
