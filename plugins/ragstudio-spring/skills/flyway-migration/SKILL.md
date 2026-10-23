---
name: flyway-migration
description: Write a Flyway migration for a RAGStudio Spring service that matches the ERD exactly - types, enums as CHECK constraints, REF columns without foreign keys, unique and partial indexes. Use for any new table, column, index or constraint.
argument-hint: "<what changes>"
---

# Flyway migration: $ARGUMENTS

1. Grep the table in the architecture skill's `references/erd.md` (e.g. pattern `^channels` with 30 lines after).
   The ERD is the contract: a column it lacks needs the user's OK and a note for the ERD owner.
2. Next version number: `ls src/main/resources/db/migration | sort -V | tail -1`, then add one.
   File: `V<n>__<snake_case_description>.sql`. Never edit an existing file.
3. Conventions (PostgreSQL 16):

```sql
CREATE TABLE channels (
    channel_id            UUID PRIMARY KEY,
    type                  VARCHAR(32)  NOT NULL CHECK (type IN ('PUBLIC_LINK', 'WIDGET', 'TELEGRAM')),
    enabled               BOOLEAN      NOT NULL DEFAULT FALSE,
    public_token          VARCHAR(64)  UNIQUE,
    webhook_secret        VARCHAR(128),
    expires_at            TIMESTAMPTZ,
    telegram_token_enc    TEXT,
    created_at            TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at            TIMESTAMPTZ  NOT NULL DEFAULT now(),
    chatbot_id            UUID         NOT NULL REFERENCES chatbots (chatbot_id) ON DELETE CASCADE,  -- FK: same service
    CONSTRAINT uq_channels_chatbot_type UNIQUE (chatbot_id, type)
);

-- REF column (other service): plain UUID + index, never REFERENCES
CREATE INDEX ix_chatbots_user_id ON chatbots (user_id);

-- partial unique (from the ERD constraints box)
CREATE UNIQUE INDEX uq_appeals_one_pending ON appeals (chatbot_id) WHERE status = 'PENDING';
CREATE UNIQUE INDEX uq_llm_models_default_chat ON llm_models ((true)) WHERE is_default_chat;
```

- NOT NULL unless the ERD or the feature makes the value optional; defaults from the business rules
  (e.g. `temperature NUMERIC(3,2) NOT NULL DEFAULT 0.40`).
- Name constraints and indexes `pk_`, `uq_<table>_<cols>`, `ix_<table>_<cols>`, `ck_<table>_<col>`.
- Seed rows (platform_settings, setting_limits) go in their own `V<n>__seed_<name>.sql` with `ON CONFLICT DO NOTHING`.
- Adding a NOT NULL column to a filled table: add nullable, backfill, then `SET NOT NULL`, in one migration.
4. Update the JPA entity to match, then run `./gradlew test --tests '*RepositoryTest'` (Testcontainers runs the migrations
   and Hibernate `validate` checks the mapping).
