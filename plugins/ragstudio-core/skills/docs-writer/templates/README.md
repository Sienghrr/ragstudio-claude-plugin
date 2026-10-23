# <repo-name>

<One paragraph: what this service does and who calls it.>

## Responsibilities

- <responsibility, naming the PDF feature it covers>

## Owns

| Table / store | Purpose |
|---|---|
| `<table>` | <one line> |

## Talks to

- Publishes: see [docs/events.md](docs/events.md)
- Consumes: see [docs/events.md](docs/events.md)
- Internal APIs served and called: see [docs/api.md](docs/api.md#internal)

## Run locally

```bash
<command>
```

Needs config-server and the local infrastructure (PostgreSQL, RabbitMQ, Redis, MinIO, Keycloak) running.

## Configuration

Keys live in `ragstudio-config/<service-name>.yml`; secrets come from environment variables.

| Key | Default | Meaning |
|---|---|---|
| `<prefix.key>` | `<value>` | <one line> |

## Testing

```bash
<unit test command>
<integration test command>
```

## Docs

- [API](docs/api.md) · [Events](docs/events.md) · [Data](docs/data.md) · [Changelog](CHANGELOG.md)
