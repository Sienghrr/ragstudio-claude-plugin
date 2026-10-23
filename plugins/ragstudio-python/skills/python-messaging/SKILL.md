---
name: python-messaging
description: aio-pika consumer and publisher patterns for RAGStudio Python services - shared envelope model, per-service durable queues with DLQ, prefetch, ack-after-commit, retries, and idempotent handlers. Use when consuming or publishing any catalogued event.
---

# RabbitMQ in a RAGStudio Python service

Check the event in the catalog (architecture skill, `references/events.md`). Code lives in `app/ingestion/messaging/` (the rag side never uses RabbitMQ).

```python
# app/ingestion/messaging/envelope.py
class EventEnvelope(BaseModel, Generic[T]):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    event_id: UUID = Field(alias="eventId")
    type: str
    version: int = 1
    occurred_at: datetime = Field(alias="occurredAt")
    producer: str
    payload: T

    @classmethod
    def new(cls, type_: str, payload: T) -> "EventEnvelope[T]":
        return cls(eventId=uuid4(), type=type_, occurredAt=datetime.now(UTC), producer=SERVICE_NAME, payload=payload)

# app/ingestion/messaging/bus.py
EXCHANGE = "ragstudio.events"

async def bind(channel: aio_pika.abc.AbstractChannel, routing_key: str) -> aio_pika.abc.AbstractQueue:
    exchange = await channel.declare_exchange(EXCHANGE, aio_pika.ExchangeType.TOPIC, durable=True)
    name = f"{SERVICE_NAME}.{routing_key}"
    await channel.declare_queue(f"{name}.dlq", durable=True)
    queue = await channel.declare_queue(name, durable=True, arguments={
        "x-dead-letter-exchange": "", "x-dead-letter-routing-key": f"{name}.dlq"})
    await queue.bind(exchange, routing_key)
    return queue

async def publish(channel, routing_key: str, payload: BaseModel) -> None:
    exchange = await channel.get_exchange(EXCHANGE)
    body = EventEnvelope.new(routing_key, payload).model_dump_json(by_alias=True).encode()
    await exchange.publish(aio_pika.Message(body, content_type="application/json",
                                            delivery_mode=aio_pika.DeliveryMode.PERSISTENT), routing_key)
```

Consumer with retries (attempt count in a header, DLQ after 3):

```python
async def consume(queue, handler, model: type[BaseModel]) -> None:
    async with queue.iterator() as it:
        async for msg in it:
            attempt = int((msg.headers or {}).get("x-attempt", 0))
            try:
                env = EventEnvelope[model].model_validate_json(msg.body)
                await handler(env)          # does the work AND commits
                await msg.ack()
            except Exception:
                log.exception("event failed", extra={"attempt": attempt})
                if attempt >= 2:
                    await msg.reject(requeue=False)          # -> DLQ
                else:
                    await republish_with_attempt(msg, attempt + 1)
                    await msg.ack()
```

- `await channel.set_qos(prefetch_count=settings.worker_concurrency)` before consuming.
- Idempotent indexing: delete chunks for `(document_id, index_version)` then insert, in one transaction.
- Publish `ingestion.document.status-changed` only after that transaction commits.
- Tests: feed `handler` an envelope twice and assert the chunk count is the same; contract test that the published
  JSON uses the catalog's camelCase field names.
