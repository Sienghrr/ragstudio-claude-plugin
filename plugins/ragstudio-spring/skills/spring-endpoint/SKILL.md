---
name: spring-endpoint
description: Add or change a REST endpoint in a RAGStudio Spring service - DTO records, validation, ownership and role checks, ProblemDetail errors, and a slice test. Use for any new controller method, admin endpoint or /internal endpoint.
argument-hint: "<METHOD /path> <what it does>"
---

# New endpoint: $ARGUMENTS

1. Decide the path family: `/api/<area>/**` (owner), `/api/admin/<area>/**` (ADMIN), `/internal/**` (service-to-service,
   must match the architecture skill's internal API table). Check the business rules for limits and messages.
2. Create or extend, in this order, only the files the change needs:
   - `api/dto/<Name>Request.java`, `<Name>Response.java` (records)
   - `application/<Area>Service.java` method (transaction, ownership check, domain logic)
   - `api/<Area>Controller.java` method
   - test `api/<Area>ControllerTest.java`
3. Patterns (package `com.ragstudio.<service>`):

```java
public record CreateChatbotRequest(
    @NotBlank @Size(max = 50) String name,
    @Size(max = 200) String description,
    UUID chatModelId,
    @NotNull UUID embeddingModelId) {}

@RestController
@RequestMapping("/api/chatbots")
@RequiredArgsConstructor
class ChatbotController {
  private final ChatbotService service;

  @PostMapping
  @ResponseStatus(HttpStatus.CREATED)
  ChatbotResponse create(@CurrentUser UserRef user, @Valid @RequestBody CreateChatbotRequest req) {
    return service.create(user.userId(), req);
  }
}

// application layer: ownership + domain errors
@Transactional
public ChatbotResponse pause(UUID userId, UUID chatbotId) {
  Chatbot bot = repo.findById(chatbotId).filter(b -> b.ownedBy(userId))
      .orElseThrow(() -> new NotFoundException("CHATBOT_NOT_FOUND", chatbotId));
  bot.pause(); // throws InvalidTransitionException("INVALID_STATUS_TRANSITION") when not ACTIVE
  events.publishEvent(ChatbotStatusChanged.of(bot, Actor.OWNER, null));
  return mapper.toResponse(bot);
}
```

Error mapping (one `@RestControllerAdvice` per service, already present after the first endpoint):
`NotFoundException` -> 404, `InvalidTransitionException` / `ConflictException` -> 409,
`QuotaExceededException` -> 422, `ForbiddenException` -> 403, validation -> 400 with field errors.
Return a 404, not a 403, when a user asks for another user's resource.

4. Test with `@WebMvcTest(<Area>Controller.class)` + `@MockitoBean` for the service: one happy path, one
   validation failure (400), one forbidden or not-found case. Security: `@WithMockUser(roles = "ADMIN")` or a JWT post-processor.
5. Run only the new test class: `./gradlew test --tests '*<Area>ControllerTest'`.
