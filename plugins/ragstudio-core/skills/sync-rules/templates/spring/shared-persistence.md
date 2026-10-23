---
paths:
  - "src/main/resources/db/migration/**"
  - "src/main/java/**/infrastructure/persistence/**"
  - "src/main/java/**/domain/**"
---

# Persistence rules (shared, synced from ragstudio-claude-plugin; do not edit here)

- Schema changes only through Flyway: `src/main/resources/db/migration/V<n>__<snake_description>.sql`.
  Never edit a migration that exists on `main`; add a new one. Use the `ragstudio-spring:flyway-migration` skill.
- Tables and columns must match the ERD (architecture skill, `references/erd.md`). This service owns only its own tables.
- REF columns (ids from other services) are plain `UUID` columns with an index, never a foreign key.
- ENUM columns: `VARCHAR(32)` + `CHECK (col IN (...))`, mapped with `@Enumerated(EnumType.STRING)`.
- PKs: `UUID` generated in Java (`UUID.randomUUID()` or `@UuidGenerator`), not by the database.
- Timestamps `TIMESTAMPTZ`, mapped to `Instant`; `created_at`/`updated_at` set by `@CreationTimestamp`/`@UpdateTimestamp`.
- `spring.jpa.hibernate.ddl-auto=validate` everywhere. `open-in-view=false`.
- Repositories: Spring Data interfaces in `infrastructure/persistence`. Fetch what the use case needs
  (projections or `@EntityGraph`); watch for N+1 in list endpoints.
- `@Transactional` on application service methods, not on controllers or repositories. Read-only methods use `readOnly = true`.
- Counters updated from events (bot_count, message_count, ready_document_count) use an atomic
  `UPDATE ... SET x = x + :delta` query, never read-modify-write.
