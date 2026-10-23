# <service-name> data

Database `<db_name>`. Columns follow the ERD; this page records what this service actually created and why.
REF columns hold ids owned by other services and have no foreign key.

## Tables

### `<table>`

<One line: what a row is.>

| Column | Type | Notes |
|---|---|---|
| `<column>` | `<TYPE>` | PK · FK `<table>` · REF `<service>` · CHECK (...) · default ... |

Constraints and indexes: `<uq_... (cols)>`, `<ix_... (cols)>`.

## Migrations

| Version | File | What it changes |
|---|---|---|
| V1 | `V1__init.sql` | <tables created> |
