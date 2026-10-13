from dataclasses import dataclass

from aipilot.llm.registry import ModelRegistry, ModelSpec
from aipilot.router.classifier import classify_request
from aipilot.router.follow_up import is_follow_up

WORK_KINDS = ("coding", "design", "complex")


@dataclass(frozen=True)
class Route:
    kind: str
    model: ModelSpec


class Router:
    def __init__(self, registry: ModelRegistry):
        self.registry = registry

    async def route(self, request: str, previous_kind: str | None = None) -> Route:
        kind = await classify_request(self.registry, request)
        if kind == "chat" and previous_kind in WORK_KINDS and is_follow_up(request):
            kind = previous_kind
        return Route(kind, self.registry.candidates(kind)[0])
