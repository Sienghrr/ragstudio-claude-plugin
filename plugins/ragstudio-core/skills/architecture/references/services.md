# RAGStudio services, repos and internal APIs

Kubernetes namespace `ragstudio`. Service DNS = `http://<service-name>:8080` (Spring) / `:8000` (Python).
No Eureka: the Kubernetes Service name is the address.

| Service | Repo | Stack | DB | Port |
|---|---|---|---|---|
| config-server | ragstudio-config-server | Spring Cloud Config | - | 8888 |
| edge gateway | not ours: run by DevOps | DevOps choice (Ingress or API gateway) | - | 443 |
| account-service | ragstudio-account-service | Spring Boot MVC | account_db | 8080 |
| chatbot-service | ragstudio-chatbot-service | Spring Boot MVC | chatbot_db | 8080 |
| knowledge-service | ragstudio-knowledge-service | Spring Boot MVC | knowledge_db + MinIO | 8080 |
| chat-service | ragstudio-chat-service | Spring Boot WebFlux | chat_db + Redis | 8080 |
| analytics-notification-service | ragstudio-analytics-notification-service | Spring Boot MVC, two modules: `analytics`, `notification` | analytics_notification_db (schemas `analytics`, `notification`) + Redis | 8080 |
| ai-ingestion-worker | ragstudio-ai-service (deployment 1) | Python 3.12, aio-pika worker + FastAPI health | ai_db (pgvector, owner) | 8000 |
| ai-rag-service | ragstudio-ai-service (deployment 2) | Python 3.12, FastAPI | ai_db (read only) | 8000 |
| (config) | ragstudio-config | YAML | - | - |

9 repos, 7 codebases, 8 Kubernetes Deployments, plus the edge gateway that DevOps runs. `ragstudio-ai-service` builds ONE image started two ways:
`python -m app.ingestion.worker` (ai-ingestion-worker) and `uvicorn app.rag.main:app` (ai-rag-service).
Each deployment keeps its own name for config files, queues and logs, so the two can scale and fail separately.
`analytics-notification-service` is one process; the modules never touch each other's schema and have separate queues.
| (tooling) | ragstudio-claude-plugin | Claude Code plugins | - | - |

External: Keycloak (realm `ragstudio`, roles USER/ADMIN, TOTP, Google/GitHub IdPs), PostgreSQL 16 + pgvector,
Redis 7, MinIO, RabbitMQ 3.13, Ollama (local models, no API keys).

## Edge gateway routes (contract with DevOps)

DevOps owns the gateway. This table is what we ask of it; changes go to DevOps as a request.
Every service still validates the Keycloak JWT and roles itself, so a misrouted request is refused, not served.
The gateway must never expose `/internal/**`, and must pass `Origin` and `X-Telegram-Bot-Api-Secret-Token` through unchanged.

| Path | Auth | Target |
|---|---|---|
| /api/account/** | JWT USER or ADMIN | account-service |
| /api/admin/users/**, /api/admin/audit-logs/** | JWT ADMIN | account-service |
| /api/chatbots/**, /api/models/** (read) | JWT USER | chatbot-service |
| /api/admin/chatbots/**, /api/admin/models/**, /api/admin/appeals/** | JWT ADMIN | chatbot-service |
| /api/knowledge/** | JWT USER | knowledge-service |
| /api/chat/playground/**, /api/chat/reports/** | JWT USER | chat-service |
| /api/admin/moderation/** | JWT ADMIN | chat-service (reports) + chatbot-service (actions) |
| /api/analytics/**, /api/admin/analytics/** | JWT USER / ADMIN | analytics-notification-service (analytics module) |
| /api/notifications/** | JWT USER or ADMIN | analytics-notification-service (notification module) |
| /public/chat/** (public link, widget) | none, rate-limited | chat-service |
| /public/sources/** (Document Viewer) | signed citation token | knowledge-service |
| /telegram/webhook/{channelId} | X-Telegram-Bot-Api-Secret-Token = channels.webhook_secret | chat-service |

## Internal APIs (cluster-only, never exposed by the edge gateway)

Prefix `/internal/**`. Caller sends a Keycloak client-credentials token (one client per service);
receiver checks the `service` role. All return JSON; errors are RFC 9457 ProblemDetail.

| Owner | Endpoint | Callers | Returns |
|---|---|---|---|
| account | GET /internal/users/{userId}/quota | chatbot, knowledge | maxBots, botCount, maxStorageBytes, storageUsedBytes, status |
| account | GET /internal/users/by-keycloak/{keycloakId} | all services | userId, role, status |
| chatbot | GET /internal/chatbots/{chatbotId}/runtime | chat, knowledge | status, ownerId, ownerOffline, config (all chatbot_configs fields), chatModelKey, fallbackModelKey, embeddingModelKey, contextWindow, activeIndexVersion, starterQuestions |
| chatbot | GET /internal/channels/resolve?publicToken= or ?channelId= | chat | chatbotId, channelType, enabled, expiresAt, allowedDomains, telegramToken (decrypted, chat-service only) |
| knowledge | GET /internal/documents/{documentId}/source-url | chat | presigned MinIO URL (5 min), only when source_visibility = FULL_DOCUMENT |
| ai-rag | POST /v1/answer (SSE) | chat | streamed tokens, then a final event: citations[], retrievedChunks[] (playground only), unanswered, usedFallback, modelId, promptTokens, completionTokens |
| ai-rag | GET /v1/health/ollama | analytics module (admin monitoring) | up/down, loaded models |

chat-service caches `/runtime` and `/channels/resolve` in Redis (key `rt:{chatbotId}`, `ch:{token}`),
evicted on `chatbot.status-changed`, `chatbot.config-changed`, `chatbot.deleted`, `account.user.status-changed`.

## Synchronous call rule

Only the calls above are allowed. Anything else between services goes through events.
A new internal endpoint is a contract change: update this file first (PR to ragstudio-claude-plugin).
