---
paths:
  - "build.gradle.kts"
  - "settings.gradle.kts"
  - "gradle/**"
  - "Dockerfile"
  - ".github/workflows/**"
---

# Build rules (shared, synced from ragstudio-claude-plugin; do not edit here)

- Gradle Kotlin DSL, Java toolchain 21, Spring Boot 3.5.x, Spring Cloud 2025.0.x BOM. Versions in `gradle/libs.versions.toml`.
- Required plugins: `org.springframework.boot`, `io.spring.dependency-management`, `com.diffplug.spotless`
  (googleJavaFormat; the format-on-edit hook calls `spotlessApply -PspotlessIdeHook=<file>`).
- Every service: `spring-boot-starter-actuator` (health, prometheus), `spring-cloud-starter-config`,
  `spring-boot-starter-oauth2-resource-server` (except config-server).
- Add a dependency only when the task needs it, and say why in the reply. No Lombok on DTOs (use records).
- Dockerfile: multi-stage, `eclipse-temurin:21-jre` runtime, non-root user, layered jar.
- CI (`.github/workflows/ci.yml`): `./gradlew spotlessCheck build`, then build and push the image on `main`.
