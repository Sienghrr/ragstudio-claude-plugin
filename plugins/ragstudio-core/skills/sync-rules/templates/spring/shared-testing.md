---
paths:
  - "src/test/**"
---

# Testing rules (shared, synced from ragstudio-claude-plugin; do not edit here)

- JUnit 5 + AssertJ + Mockito. Test class name `<ClassUnderTest>Test`; integration tests `<Feature>IT`.
- Integration tests use Testcontainers (`postgres:16`, `rabbitmq:3.13-management`, `redis:7`) via
  `@ServiceConnection`; never point tests at a shared database.
- Slice tests first: `@WebMvcTest`/`@WebFluxTest` for controllers, `@DataJpaTest` for repositories, plain unit tests for domain logic.
- Name tests by behaviour: `publish_rejected_when_no_ready_document()`.
- Status machines and validation limits get table-driven tests (`@ParameterizedTest`) covering every allowed and denied transition.
- Event consumers: test a normal delivery AND a duplicate delivery of the same `eventId`.
- Run one class yourself: `./gradlew test --tests '<Class>'`. Delegate the full suite to `ragstudio-spring:spring-test-runner`.
