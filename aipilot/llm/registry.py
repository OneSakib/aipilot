import os
from dataclasses import dataclass
from pathlib import Path

import yaml


class NoModelAvailable(Exception):
    pass


@dataclass(frozen=True)
class ModelSpec:
    id: str
    name: str
    key_env: str

    @property
    def available(self) -> bool:
        return bool(os.getenv(self.key_env))


class ModelRegistry:
    def __init__(self, models: dict[str, ModelSpec], routes: dict[str, list[str]]):
        self.models = models
        self.routes = routes

    @classmethod
    def from_file(cls, path: Path) -> "ModelRegistry":
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        models = {
            model_id: ModelSpec(model_id, entry["name"], entry["key_env"])
            for model_id, entry in data["models"].items()
        }
        return cls(models, data["routes"])

    def candidates(self, route: str) -> list[ModelSpec]:
        specs = [self.models[model_id] for model_id in self.routes[route]]
        available = [spec for spec in specs if spec.available]
        if not available:
            keys = ", ".join(sorted({spec.key_env for spec in specs}))
            raise NoModelAvailable(f"No API key found for route '{route}'. Set one of: {keys}")
        return available
