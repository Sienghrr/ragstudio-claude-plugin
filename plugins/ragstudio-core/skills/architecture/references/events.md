# RAGStudio event catalog (RabbitMQ)

This file is the single source of truth for events. Change it through a pull request
to ragstudio-claude-plugin BEFORE changing producer or consumer code.

## Transport

- Exchange: `ragstudio.events` (topic, durable).
- Routing key = event name, for example `chatbot.status-changed`.
- Each consumer declares its own durable queue `<consumer>.<event>` bound to that key,
  for example `chat-service.chatbot.status-changed`.
- `analytics-notification-service` has one queue per MODULE: `analytics-notification-service.analytics.<event>` and
  `analytics-notification-service.notification.<event>`, so a failed push is never retried by re-running stats (or the reverse).
  In the table below, consumers `analytics` and `notification` are those two modules.
- Consumer `ai-ingestion` is the ai-ingestion-worker deployment of ragstudio-ai-service (queues `ai-ingestion-worker.<event>`).
- Dead letter: `<queue>.dlq`, 3 retries with backoff, then park.
- Content type `application/json`, UTF-8.

## Envelope (every message)

```json
{
  "eventId": "uuid",
  "type": "chatbot.status-changed",
  "version": 1,
  "occurredAt": "2026-10-23T04:12:00Z",
  "producer": "chatbot-service",
  "payload": { }
}
```

Rules:
- Consumers are idempotent on `eventId` (upsert, or ignore a state that is already applied).
- Producers publish after the DB transaction commits (`@TransactionalEventListener(phase = AFTER_COMMIT)`).
- Adding an optional payload field: same version. Removing or renaming a field: new version,
  publish both versions until every consumer has moved.
- Never put secrets, full documents or guest message text in an event (questionHash only;
  analytics may receive `questionText` truncated to 500 chars for question_stats).

## Events

| Routing key | Producer | Consumers | Payload |
|---|---|---|---|
| account.user.created | account | analytics | userId, signupMethod |
| account.user.status-changed | account | chatbot, chat, analytics, notification | userId, from, to, reason |
| account.user.purged | account | all services | userId |
| account.storage.threshold-reached | account | notification | userId, percent (80 or 100) |
| chatbot.created | chatbot | account, analytics | chatbotId, ownerId |
| chatbot.deleted | chatbot | account, knowledge, chat, ai-ingestion, analytics | chatbotId, ownerId |
| chatbot.status-changed | chatbot | chat, analytics, notification | chatbotId, ownerId, from, to, actor (OWNER, ADMIN, SYSTEM), reason |
| chatbot.config-changed | chatbot | chat | chatbotId, configVersion |
| chatbot.chunking-changed | chatbot | knowledge | chatbotId, chunkSize, chunkOverlap, newIndexVersion |
| chatbot.model-fallback-applied | chatbot | notification | chatbotId, ownerId, disabledModelId, fallbackModelId |
| chatbot.appeal.submitted | chatbot | analytics, notification | appealId, chatbotId, ownerId |
| chatbot.appeal.decided | chatbot | analytics, notification | appealId, chatbotId, ownerId, status, reason |
| knowledge.document.index-requested | knowledge | ai-ingestion | documentId, chatbotId, type, storageKey, sourceUrl, indexVersion, chunkSize, chunkOverlap, embeddingModelKey |
| knowledge.document.deleted | knowledge | ai-ingestion | documentId, chatbotId |
| knowledge.document.ready-count-changed | knowledge | chatbot | chatbotId, readyCount |
| knowledge.reindex.completed | knowledge | chatbot, ai-ingestion | chatbotId, indexVersion, status (READY, FAILED) |
| knowledge.storage.changed | knowledge | account, analytics | userId, usedBytes |
| knowledge.crawl.failed | knowledge | notification | crawlJobId, chatbotId, ownerId, reason |
| ingestion.document.status-changed | ai-ingestion | knowledge, notification | documentId, chatbotId, ownerId, status (PROCESSING, READY, FAILED), reason, chunkCount, indexVersion |
| chat.message.answered | chat | chatbot, analytics | chatbotId, ownerId, channel, modelId, promptTokens, completionTokens, unanswered, usedFallback, questionHash, questionText, guestId, sessionId |
| chat.feedback.submitted | chat | analytics | chatbotId, messageId, channel, helpful |
| chat.report.created | chat | analytics, notification | reportId, chatbotId, ownerId, type |
| chat.llm.failed | chat | notification | chatbotId, ownerId, error (only when chat model AND fallback failed) |
| admin.action.performed | account, chatbot | account (writes audit_logs) | adminId, action, targetUserId, targetChatbotId, targetAppealId, targetModelId, reason, details |

## Flows worth knowing

Re-index after chunk settings change:
1. chatbot-service saves new chunk_size/overlap, sets reindex_status=QUEUED, publishes
   `chatbot.chunking-changed` with newIndexVersion = active_index_version + 1.
2. knowledge-service sets every document's indexed_version, keeps status as is, publishes
   `knowledge.document.index-requested` per document.
3. ai-ingestion-worker writes chunks with the new index_version, publishes `ingestion.document.status-changed`.
4. When every document of the chatbot is READY at newIndexVersion, knowledge-service publishes
   `knowledge.reindex.completed`; chatbot-service sets active_index_version and reindex_status=READY.
5. ai-rag-service always filters `index_version = active_index_version` (sent by chat-service), so
   answers come from the old index until step 4.
6. ai-ingestion-worker also consumes `knowledge.reindex.completed` (status READY) and deletes that
   chatbot's chunks with index_version < indexVersion. On FAILED it deletes the new version's chunks instead.

Account deletion:
1. account-service sets PENDING_DELETION, publishes `account.user.status-changed` (chatbots go offline).
2. Restore within 7 days: status ACTIVE, event again; chatbot-service moves ACTIVE bots to PAUSED.
3. After 7 days: account-service publishes `account.user.purged`; every service deletes that user's rows,
   files (MinIO), chunks and Redis keys.
