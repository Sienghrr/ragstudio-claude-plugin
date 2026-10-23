---
name: spring-messaging
description: RabbitMQ publisher and consumer patterns for RAGStudio Spring services - shared envelope, after-commit publishing, per-service queues with DLQ, idempotent listeners, and tests. Use when publishing or consuming any catalogued event.
---

# RabbitMQ in a RAGStudio Spring service

Check the event in the catalog first (architecture skill, `references/events.md`). Package `infrastructure/messaging`.

## Shared pieces (create once per service)

```java
public record EventEnvelope<T>(UUID eventId, String type, int version, Instant occurredAt, String producer, T payload) {
  public static <T> EventEnvelope<T> of(String type, String producer, T payload) {
    return new EventEnvelope<>(UUID.randomUUID(), type, 1, Instant.now(), producer, payload);
  }
}

@Configuration
class RabbitConfig {
  static final String EXCHANGE = "ragstudio.events";
  @Bean TopicExchange events() { return new TopicExchange(EXCHANGE, true, false); }
  @Bean MessageConverter json(ObjectMapper om) {
    return new Jackson2JsonMessageConverter(om.copy().configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false));
  }
}
```

Retry and DLQ in config (`ragstudio-config/<service>.yml`, not in the repo):
`spring.rabbitmq.listener.simple.retry.enabled=true`, `max-attempts=3`, `initial-interval=1s`, `multiplier=3`,
`default-requeue-rejected=false`.

## Publish after commit

```java
// domain/application code raises a plain Spring event inside the transaction
events.publishEvent(new ChatbotStatusChangedPayload(bot.id(), bot.ownerId(), from, to, actor, reason));

@Component
@RequiredArgsConstructor
class ChatbotEventPublisher {
  private final RabbitTemplate rabbit;
  @Value("${spring.application.name}") private String producer;

  @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
  void on(ChatbotStatusChangedPayload p) {
    rabbit.convertAndSend(RabbitConfig.EXCHANGE, "chatbot.status-changed",
        EventEnvelope.of("chatbot.status-changed", producer, p));
  }
}
```

## Consume

```java
@Configuration
class StatusChangedQueue {
  static final String Q = "chat-service.chatbot.status-changed";
  @Bean Queue q() { return QueueBuilder.durable(Q).deadLetterExchange("").deadLetterRoutingKey(Q + ".dlq").build(); }
  @Bean Queue dlq() { return QueueBuilder.durable(Q + ".dlq").build(); }
  @Bean Binding b(TopicExchange events) { return BindingBuilder.bind(q()).to(events).with("chatbot.status-changed"); }
}

@Component
@RequiredArgsConstructor
@Slf4j
class ChatbotStatusChangedListener {
  private final RuntimeCache cache;

  @RabbitListener(queues = StatusChangedQueue.Q)
  void on(EventEnvelope<ChatbotStatusChangedPayload> e) {
    log.info("event {} {}", e.type(), e.eventId());
    cache.evict(e.payload().chatbotId()); // idempotent: evicting twice is harmless
  }
}
```

Idempotency options, pick the simplest that fits: the state change is naturally repeatable (evict, set status to X);
a conditional update (`UPDATE ... WHERE status <> :to`); or an upsert keyed by the business id.

## Tests

- Publisher: `@SpringBootTest` + Testcontainers RabbitMQ, commit a change, receive from a temp queue bound to the key,
  assert routing key and payload JSON.
- Listener: call the listener method directly with an envelope twice; assert the state once.
