---
paths:
  - "src/main/java/**/api/**"
  - "src/main/java/**/*Controller.java"
---

# REST API rules (shared, synced from ragstudio-claude-plugin; do not edit here)

- Paths: public `/api/<area>/**` (the DevOps edge gateway forwards paths unchanged), admin `/api/admin/<area>/**`,
  cluster-only `/internal/**`. `/internal/**` endpoints must also appear in the architecture skill's internal API table.
- Every service is an OAuth2 resource server and validates the Keycloak JWT itself. Never trust identity from a header
  the gateway might add; the gateway is DevOps-owned and not part of our security boundary.
- Controllers are thin: validate, call one application service method, map the result. No repositories in controllers.
- Request and response bodies are Java records in `api/dto`, suffixed `Request` / `Response`. Never return JPA entities.
- Validate with Jakarta annotations (`@Valid`, `@NotBlank`, `@Size(max = 50)`) using the limits from the business rules.
- Errors: throw domain exceptions; one `@RestControllerAdvice` maps them to `ProblemDetail` (RFC 9457) with
  `type`, `title`, `status`, `detail` and an `errorCode` property (UPPER_SNAKE). Never expose stack traces.
- Auth: the caller's id is the JWT `sub` (Keycloak id), resolved to `userId` once in a `CurrentUser` argument resolver.
  Use `@PreAuthorize("hasRole('ADMIN')")` on admin endpoints. Every owner endpoint checks ownership in the service layer.
- Lists: `?page=0&size=20&sort=name,asc` and return `{items, page, size, totalItems}`; max size 100.
- Time: `Instant` in UTC, ISO-8601 in JSON. Ids: `UUID`.
- Every endpoint gets a `@WebMvcTest` (or `@WebFluxTest`) covering 200, 400 and 403/404.
