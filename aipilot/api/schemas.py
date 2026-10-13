from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    thread_id: str | None = None
    project: str = "."
    auto_approve: bool = False


class ChatResponse(BaseModel):
    thread_id: str
    kind: str
    model: str
    answer: str
    events: list[dict]


class ModelInfo(BaseModel):
    id: str
    name: str
    available: bool
