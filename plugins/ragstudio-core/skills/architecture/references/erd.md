# RAGStudio ERD (source: RAG_Studio_ERD.png)

Conventions for every table:
- PK UUID unless noted. Timestamps are TIMESTAMPTZ (UTC).
- FK = foreign key inside the same service database (enforce it).
- REF = id of a row owned by ANOTHER service. Store the UUID, never add a FK constraint, never join across databases.
- ENUM = VARCHAR + CHECK constraint with the allowed values below, mapped with @Enumerated(STRING) / Python StrEnum.

## account-service (account_db)

users
  user_id UUID PK
  email VARCHAR(255) UNIQUE
  keycloak_id VARCHAR(36) UNIQUE
  full_name VARCHAR(100)
  avatar_key VARCHAR(500)
  language VARCHAR(5)
  timezone VARCHAR(50)
  role ENUM(USER, ADMIN)
  signup_method ENUM(EMAIL, GOOGLE, GITHUB)
  status ENUM(UNVERIFIED, ACTIVE, SUSPENDED, PENDING_DELETION)
  max_bots INTEGER
  max_storage_bytes BIGINT
  bot_count INTEGER                -- updated from chatbot events; nightly correction job
  storage_used_bytes BIGINT        -- updated from knowledge events
  suspended_reason TEXT
  suspended_at TIMESTAMPTZ
  deletion_requested_at TIMESTAMPTZ
  tos_accepted_at TIMESTAMPTZ
  last_login_at TIMESTAMPTZ
  created_at, updated_at TIMESTAMPTZ

audit_logs (read-only after insert)
  audit_log_id UUID PK
  action ENUM(SUSPEND_USER, REACTIVATE_USER, RESET_MFA, FORCE_LOGOUT, SET_QUOTA,
              FORCE_DISABLE_CHATBOT, REENABLE_CHATBOT, APPROVE_APPEAL, REJECT_APPEAL,
              ADD_MODEL, REMOVE_MODEL, ENABLE_MODEL, DISABLE_MODEL, SET_DEFAULT_MODEL, SET_FALLBACK_MODEL)
  reason TEXT
  details JSONB
  created_at TIMESTAMPTZ
  admin_id UUID FK users
  target_user_id UUID FK users (nullable)
  target_chatbot_id UUID REF chatbot-service
  target_appeal_id UUID REF chatbot-service
  target_model_id UUID REF chatbot-service

platform_settings
  setting_key VARCHAR(40) PK       -- rows: bots (max 5, default 5), storage_bytes (max 5 GB, default 5 GB)
  min_value, max_value, default_value NUMERIC   -- CHECK (min_value <= default_value <= max_value)
  updated_at TIMESTAMPTZ
  updated_by UUID REF users (admin)
  Default quota is copied into users.max_bots / max_storage_bytes when an account is created.

## analytics-notification-service, notification module (analytics_notification_db, schema `notification`)

device_tokens
  device_token_id UUID PK
  token VARCHAR(500) UNIQUE        -- re-registration updates the row
  platform ENUM(IOS, ANDROID)
  role ENUM(OWNER, ADMIN)
  created_at, last_used_at TIMESTAMPTZ
  user_id UUID REF account

notification_preferences          -- UNIQUE (user_id, alert_type)
  notification_pref_id UUID PK
  alert_type ENUM(KB_PROCESSING_FAILED, URL_SCRAPE_FAILED, LLM_REQUEST_FAILED, STORAGE_80,
                  REPORT_INACCURATE, REPORT_UNHELPFUL, HIGH_SYSTEM_ERROR_RATE, API_RESPONSE_ERROR,
                  NEW_APPEAL, USER_REPORT)   -- always-on alerts are not stored
  enabled BOOLEAN
  updated_at TIMESTAMPTZ
  user_id UUID REF account

## chatbot-service (chatbot_db)

chatbots
  chatbot_id UUID PK
  name VARCHAR(50)
  description VARCHAR(200)
  status ENUM(DRAFT, PENDING, ACTIVE, PAUSED, DISABLED)
  owner_offline BOOLEAN            -- true while owner SUSPENDED or PENDING_DELETION
  message_count INTEGER            -- from chat events
  ready_document_count INTEGER     -- from knowledge events
  disabled_reason TEXT
  disabled_at, published_at, deleted_at, created_at, updated_at TIMESTAMPTZ
  user_id UUID REF account (owner)

chatbot_configs                    -- PK (chatbot_id) = 1:1 with chatbots
  chatbot_id UUID PK, FK chatbots
  on_system_fallback BOOLEAN       -- set when its chat model is disabled/removed by admin
  system_instructions TEXT
  tone ENUM(PROFESSIONAL, FRIENDLY, CASUAL, FORMAL, CUSTOM)
  custom_tone VARCHAR(300)
  answer_length ENUM(CONCISE, DETAILED)
  formatting ENUM(RICH_TEXT, PLAIN_TEXT)
  language ENUM(AUTO, KM, EN, KO)  -- default AUTO
  temperature NUMERIC(3,2)         -- 0-1, default 0.4
  max_response_tokens INTEGER      -- 256-4096, default 1024
  top_k INTEGER                    -- 1-20, default 5
  search_mode ENUM(SEMANTIC, KEYWORD, HYBRID)   -- default HYBRID
  max_context_tokens INTEGER       -- 1000-8000, default 4000, <= model context window - max_response_tokens
  chunk_size INTEGER               -- 200-1000, default 500
  chunk_overlap INTEGER            -- 0-200, default 50
  source_visibility ENUM(FULL_DOCUMENT, NAME_ONLY, HIDDEN)   -- default NAME_ONLY
  active_index_version INTEGER     -- the index version RAG answers from
  reindex_status ENUM(IDLE, QUEUED, PROCESSING, READY, FAILED)
  updated_at TIMESTAMPTZ
  primary_model_id UUID FK llm_models
  embedding_model_id UUID FK llm_models   -- locked after creation

starter_questions                  -- max 4 per chatbot
  starter_question_id UUID PK
  text VARCHAR(200)
  position INTEGER
  chatbot_id UUID FK chatbots

llm_models
  model_id UUID PK
  model_key VARCHAR(100) UNIQUE    -- Ollama model id
  name VARCHAR(100)
  type ENUM(CHAT, EMBEDDING)
  dimensions INTEGER               -- CHECK dimensions = 1024 when type = EMBEDDING
  context_window INTEGER
  enabled BOOLEAN
  is_default_chat BOOLEAN          -- UNIQUE partial WHERE is_default_chat
  is_default_embedding BOOLEAN     -- UNIQUE partial WHERE is_default_embedding
  is_system_fallback BOOLEAN       -- UNIQUE partial WHERE is_system_fallback; chat only; != default chat
  created_at, updated_at TIMESTAMPTZ

setting_limits                     -- 7 rows: temperature, max_response_tokens, top_k, max_context_tokens, chunk_size, chunk_overlap, search_mode
  setting_key VARCHAR(40) PK
  min_value, max_value, default_value NUMERIC   -- CHECK (min <= default <= max); choice settings use allowed_values
  allowed_values JSONB
  updated_at TIMESTAMPTZ
  updated_by UUID REF account

appeals                            -- UNIQUE partial (chatbot_id) WHERE status = PENDING
  appeal_id UUID PK
  message VARCHAR(500)
  status ENUM(PENDING, APPROVED, REJECTED)
  decision_reason TEXT
  created_at, decided_at TIMESTAMPTZ
  chatbot_id UUID FK chatbots
  user_id UUID REF account (owner)
  decided_by UUID REF account (admin)

channels                           -- UNIQUE (public_token); UNIQUE (chatbot_id, type)
  channel_id UUID PK
  type ENUM(PUBLIC_LINK, WIDGET, TELEGRAM)
  enabled BOOLEAN
  public_token VARCHAR(64) UNIQUE
  webhook_secret VARCHAR(128)
  expires_at TIMESTAMPTZ
  telegram_bot_id BIGINT
  telegram_token_enc TEXT          -- encrypted at rest, key from Kubernetes Secret
  telegram_bot_username VARCHAR(100)
  error_reason TEXT
  connected_at, created_at, updated_at TIMESTAMPTZ
  chatbot_id UUID FK chatbots

channel_allowed_domains
  allowed_domain_id UUID PK
  domain VARCHAR(253)
  channel_id UUID FK channels

## knowledge-service (knowledge_db + MinIO)

documents                          -- UNIQUE (chatbot_id, content_hash); UNIQUE partial (chatbot_id, source_url) WHERE type = WEB; recommended UNIQUE (chatbot_id, name)
  document_id UUID PK
  name VARCHAR(255)
  type ENUM(PDF, DOCX, TXT, MD, XLSX, WEB)
  source_url VARCHAR(2000)
  storage_key VARCHAR(500)         -- MinIO object key
  size_bytes BIGINT
  content_hash CHAR(64)            -- SHA-256
  status ENUM(QUEUED, PROCESSING, READY, FAILED)
  indexed_version INTEGER          -- version being built; status stays on the active index during re-index
  failed_reason TEXT
  chunk_count INTEGER
  last_crawled_at, created_at, updated_at TIMESTAMPTZ
  user_id UUID REF account
  chatbot_id UUID REF chatbot

crawl_jobs
  crawl_job_id UUID PK
  start_url VARCHAR(2000)
  status ENUM(QUEUED, CRAWLING, READY, IMPORTED, FAILED)
  failed_reason TEXT
  pages_found INTEGER
  created_at, last_run_at, finished_at TIMESTAMPTZ
  chatbot_id UUID REF chatbot

crawl_pages                        -- UNIQUE (crawl_job_id, url)
  crawl_page_id UUID PK
  url VARCHAR(2000)
  title VARCHAR(500)
  content TEXT
  status ENUM(FETCHED, FAILED)
  selected BOOLEAN
  crawl_job_id UUID FK crawl_jobs
  document_id UUID FK documents (nullable until imported)

## ragstudio-ai-service (ai_db, PostgreSQL + pgvector) — written by the ai-ingestion-worker deployment, read by ai-rag-service

document_chunks                    -- UNIQUE (document_id, index_version, chunk_index)
  chunk_id UUID PK
  chunk_index INTEGER
  content TEXT
  embedding VECTOR(1024)           -- every enabled embedding model must output 1024 dims
  content_tsv TSVECTOR
  index_version INTEGER
  page_number INTEGER              -- PDF
  section_title VARCHAR(255)       -- DOCX, MD nearest heading
  sheet_name VARCHAR(100)          -- XLSX
  row_start, row_end INTEGER       -- XLSX
  line_start, line_end INTEGER     -- TXT
  document_id UUID REF knowledge
  chatbot_id UUID REF chatbot      -- every query filters by chatbot_id (knowledge base isolation)

## chat-service (chat_db + Redis)

chat_sessions                      -- Playground only; guest context lives in Redis with a TTL
  session_id UUID PK
  started_at, last_active_at, ended_at TIMESTAMPTZ
  user_id UUID REF account
  chatbot_id UUID REF chatbot

messages
  message_id UUID PK
  role ENUM(USER, ASSISTANT)
  content TEXT
  token_count INTEGER
  used_fallback BOOLEAN
  is_unanswered BOOLEAN
  created_at TIMESTAMPTZ
  session_id UUID FK chat_sessions
  model_id UUID REF chatbot (llm_models)

message_sources
  message_source_id UUID PK
  marker_no INTEGER
  document_name VARCHAR(255)
  snippet TEXT
  location_label VARCHAR(255)
  message_id UUID FK messages
  document_id UUID REF knowledge
  chunk_id UUID REF ai

message_reports                    -- UNIQUE (chatbot_id, message_id); Playground answers cannot be reported
  report_id UUID PK
  type ENUM(INACCURATE, UNHELPFUL)
  question TEXT
  answer TEXT
  comment TEXT
  status ENUM(OPEN, RESOLVED, DISMISSED)
  channel_type ENUM(PUBLIC_LINK, WIDGET, TELEGRAM)
  sources JSONB
  message_id VARCHAR(64)           -- the Redis message id
  created_at, resolved_at TIMESTAMPTZ
  chatbot_id UUID REF chatbot

## analytics-notification-service, analytics module (analytics_notification_db, schema `analytics`, + Redis)

daily_chatbot_stats                -- PK (chatbot_id, stat_date, channel_type)
  chatbot_id UUID PK, REF chatbot
  stat_date DATE PK
  channel_type ENUM(PLAYGROUND, PUBLIC_LINK, WIDGET, TELEGRAM) PK
  sessions, messages INTEGER
  tokens BIGINT
  helpful_count, not_helpful_count, unanswered_count, fallback_count INTEGER
  guests INTEGER                   -- unique guests come from a Redis daily set; never sum this column across days
  user_id UUID REF account (owner)

question_stats                     -- PK (chatbot_id, question_hash); rows not asked for 90 days are deleted
  chatbot_id UUID PK, REF chatbot
  question_hash CHAR(64) PK
  question_text VARCHAR(500)
  ask_count, unanswered_count INTEGER
  last_asked_at TIMESTAMPTZ

daily_model_usage                  -- PK (model_id, user_id, stat_date)
  model_id UUID PK, REF chatbot (llm_models)
  user_id UUID PK, REF account
  stat_date DATE PK
  messages INTEGER
  tokens BIGINT

daily_platform_stats               -- PK (stat_date); nightly snapshot for admin trends
  stat_date DATE PK
  new_users, active_users, chatbots, published_chatbots INTEGER
  messages, storage_used_bytes, tokens BIGINT
