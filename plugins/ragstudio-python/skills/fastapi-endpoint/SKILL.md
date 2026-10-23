---
name: fastapi-endpoint
description: Add or change an HTTP endpoint in a RAGStudio Python service - Pydantic v2 schemas, service-token auth dependency, problem+json errors, SSE streaming, and an httpx test. Use for any new route in ragstudio-ai-service (rag API under app/rag/, worker health under app/ingestion/).
argument-hint: "<METHOD /v1/path> <what it does>"
---

# New endpoint: $ARGUMENTS

1. Check the internal API table (architecture skill, `references/services.md`). A route chat-service calls must match it.
2. Files (RAG side): `app/rag/api/schemas/<area>.py`, `app/rag/api/<area>.py` (router), `app/rag/services/<area>.py`,
   `tests/rag/api/test_<area>.py`. Never import from `app/ingestion/` here.
3. Patterns:

```python
# app/rag/api/schemas/answer.py
class AnswerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    chatbot_id: UUID
    question: str = Field(min_length=1, max_length=4000)
    history: list[Turn] = Field(default_factory=list, max_length=20)
    config: RuntimeConfig          # sent by chat-service from chatbot-service /runtime
    playground: bool = False

# app/rag/api/answer.py
router = APIRouter(prefix="/v1", dependencies=[Depends(require_service_token)])

@router.post("/answer")
async def answer(req: AnswerRequest, svc: AnswerService = Depends(get_answer_service)) -> EventSourceResponse:
    return EventSourceResponse(svc.stream(req), ping=15)

# app/rag/services/answer.py yields SSE events
async def stream(self, req: AnswerRequest) -> AsyncIterator[dict]:
    async for token in self._generate(req):
        yield {"event": "token", "data": token}
    yield {"event": "final", "data": result.model_dump_json()}
```

Errors: raise `DomainError(code="CHATBOT_HAS_NO_INDEX", status=409, detail=...)`; the handler in `app/rag/main.py`
returns `application/problem+json`. Never let Ollama exceptions escape raw: map to `LLM_UNAVAILABLE` (503).

4. Test with `httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://t")`, override
   `require_service_token` and the service dependency with fakes, assert status codes and, for SSE, the event order
   (`token`... then one `final`).
5. Run only that file: `uv run pytest tests/rag/api/test_<area>.py -q`.
