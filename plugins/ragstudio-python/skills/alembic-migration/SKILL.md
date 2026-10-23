---
name: alembic-migration
description: Write an Alembic migration for ai_db (document_chunks with pgvector and tsvector) that matches the ERD, including vector, GIN and B-tree indexes. Use in ragstudio-ai-service for any change to the document_chunks table.
argument-hint: "<what changes>"
---

# Alembic migration: $ARGUMENTS

Migrations live in `migrations/` of ragstudio-ai-service and run as a Kubernetes Job before the ai-ingestion-worker deployment rolls out.
The rag side (`app/rag/`) only reads; if a change seems to need a new column for answering, confirm with the user first.

1. Grep `^document_chunks` in the architecture skill's `references/erd.md`. A column it lacks needs the user's OK.
2. Create the revision: `uv run alembic revision -m "<snake_description>"`, then fill `upgrade()` and `downgrade()`.
   Never edit a revision that is on `main`.
3. First revision pattern:

```python
def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "document_chunks",
        sa.Column("chunk_id", sa.Uuid(), primary_key=True),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(1024), nullable=False),
        sa.Column("content_tsv", postgresql.TSVECTOR(), nullable=False),
        sa.Column("index_version", sa.Integer(), nullable=False),
        sa.Column("page_number", sa.Integer()),
        sa.Column("section_title", sa.String(255)),
        sa.Column("sheet_name", sa.String(100)),
        sa.Column("row_start", sa.Integer()), sa.Column("row_end", sa.Integer()),
        sa.Column("line_start", sa.Integer()), sa.Column("line_end", sa.Integer()),
        sa.Column("document_id", sa.Uuid(), nullable=False),   # REF knowledge-service: no FK
        sa.Column("chatbot_id", sa.Uuid(), nullable=False),    # REF chatbot-service: no FK
        sa.UniqueConstraint("document_id", "index_version", "chunk_index", name="uq_chunks_doc_version_index"),
    )
    op.create_index("ix_chunks_chatbot_version", "document_chunks", ["chatbot_id", "index_version"])
    op.create_index("ix_chunks_document", "document_chunks", ["document_id"])
    op.execute("CREATE INDEX ix_chunks_tsv ON document_chunks USING gin (content_tsv)")
    op.execute("CREATE INDEX ix_chunks_embedding ON document_chunks USING hnsw (embedding vector_cosine_ops)")
    op.execute("GRANT SELECT ON document_chunks TO rag_reader")  # ai-rag-service role


def downgrade() -> None:
    op.drop_table("document_chunks")
```

4. Large-table changes: build indexes with `CREATE INDEX CONCURRENTLY` inside `with op.get_context().autocommit_block():`.
5. Check with the integration tests: `uv run pytest -m integration tests/db -q` (Testcontainers `pgvector/pgvector:pg16`).
