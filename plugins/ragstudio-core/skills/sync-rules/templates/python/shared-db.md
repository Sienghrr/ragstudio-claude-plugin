---
paths:
  - "migrations/**"
  - "app/repositories/**"
  - "app/models/**"
  - "app/*/repositories/**"
---

# Database rules (shared, synced from ragstudio-claude-plugin; do not edit here)

- `document_chunks` is the only table in `ai_db`; it must match the ERD (architecture skill, `references/erd.md`).
- Only the ai-ingestion-worker deployment writes the table; Alembic migrations live in `migrations/` and run as a Kubernetes Job
  before that deployment rolls out. Code under `app/rag/` connects with a read-only role and must never write.
- Never edit a migration on `main`; add a new revision. Use the `ragstudio-python:alembic-migration` skill.
- SQLAlchemy 2.0 async (`asyncpg`) with `pgvector.sqlalchemy.Vector(1024)`. Raw SQL only for the hybrid search query,
  kept in `app/repositories/` with bound parameters, never f-strings.
- Every query filters `chatbot_id = :chatbot_id` (knowledge base isolation) and, for answering,
  `index_version = :active_index_version`.
- Indexes: HNSW on `embedding` (`vector_cosine_ops`), GIN on `content_tsv`, B-tree on `(chatbot_id, index_version)` and `document_id`.
- Bulk writes go in batches (about 100 rows) inside one transaction per document.
