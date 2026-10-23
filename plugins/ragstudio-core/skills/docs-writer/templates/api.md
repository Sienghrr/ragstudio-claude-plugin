# <service-name> API

Base path through the edge gateway: `/api/<area>`. All endpoints need a Keycloak JWT unless marked otherwise.
Errors use RFC 9457 problem JSON with an `errorCode`.

## Public

### `POST /api/<area>/<path>`

<One line: what it does.>

- **Auth:** USER (owner of the resource) · ADMIN · none
- **Request body**

| Field | Type | Required | Rules |
|---|---|---|---|
| `name` | string | yes | 1-50 characters |

- **Response** `201 Created`

```json
{ "id": "3f2a9c1e-5b7d-4e8a-9c21-7d4e5f6a8b90", "name": "Support bot", "status": "DRAFT" }
```

- **Errors**

| Status | errorCode | When |
|---|---|---|
| 400 | `VALIDATION_FAILED` | A field breaks its rule |
| 422 | `QUOTA_EXCEEDED` | The user already has the maximum number of bots |

## Admin

<Same shape, under /api/admin/...>

## Internal

<Endpoints under /internal/**: caller services, request, response. Cluster-only, never routed by the edge gateway.>
