import json
from collections.abc import AsyncIterator
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from langgraph.checkpoint.memory import MemorySaver

from aipilot import __version__
from aipilot.agent.factory import create_agent
from aipilot.agent.runner import run_agent
from aipilot.api.schemas import ChatRequest, ChatResponse, ModelInfo
from aipilot.config import get_settings
from aipilot.llm.registry import ModelRegistry
from aipilot.tools.approval import approve_all, deny_all


def sse(event: dict) -> str:
    return f"data: {json.dumps(event)}\n\n"


def create_app() -> FastAPI:
    settings = get_settings()
    checkpointer = MemorySaver()
    app = FastAPI(title="AIPilot", version=__version__)

    def open_session(request: ChatRequest):
        project = (settings.workspace / request.project).resolve()
        if not project.is_relative_to(settings.workspace) or not project.is_dir():
            raise HTTPException(status_code=400, detail="Invalid project path")
        approve = approve_all if request.auto_approve else deny_all
        graph = create_agent(project, approve, checkpointer)
        return graph, request.thread_id or uuid4().hex

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok", "version": __version__}

    @app.get("/v1/models", response_model=list[ModelInfo])
    async def list_models() -> list[ModelInfo]:
        registry = ModelRegistry.from_file(settings.models_file)
        return [
            ModelInfo(id=spec.id, name=spec.name, available=spec.available)
            for spec in registry.models.values()
        ]

    @app.post("/v1/chat", response_model=ChatResponse)
    async def chat(request: ChatRequest) -> ChatResponse:
        graph, thread_id = open_session(request)
        events = [event async for event in run_agent(graph, request.message, thread_id)]
        failure = next((event for event in events if event["type"] == "error"), None)
        if failure:
            raise HTTPException(status_code=502, detail=failure["message"])
        routed = next(event for event in events if event["type"] == "routed")
        answer = next(event for event in reversed(events) if event["type"] == "answer")
        return ChatResponse(
            thread_id=thread_id,
            kind=routed["kind"],
            model=answer["model"],
            answer=answer["text"],
            events=events,
        )

    @app.post("/v1/chat/stream")
    async def chat_stream(request: ChatRequest) -> StreamingResponse:
        graph, thread_id = open_session(request)

        async def stream() -> AsyncIterator[str]:
            yield sse({"type": "session", "thread_id": thread_id})
            async for event in run_agent(graph, request.message, thread_id):
                yield sse(event)

        return StreamingResponse(stream(), media_type="text/event-stream")

    return app
