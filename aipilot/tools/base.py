import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

STRING = {"type": "string"}
INTEGER = {"type": "integer"}

Handler = Callable[..., Awaitable[str]]
Approver = Callable[[str, dict], Awaitable[bool]]


class ToolError(Exception):
    pass


def object_schema(properties: dict[str, dict], required: list[str]) -> dict[str, Any]:
    return {"type": "object", "properties": properties, "required": required}


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    parameters: dict[str, Any]
    handler: Handler
    needs_approval: bool = False

    def schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class ToolBox:
    def __init__(self, tools: list[Tool], approve: Approver, max_output_chars: int):
        self._tools = {tool.name: tool for tool in tools}
        self._approve = approve
        self._max_output_chars = max_output_chars

    def schemas(self) -> list[dict]:
        return [tool.schema() for tool in self._tools.values()]

    async def run(self, name: str, raw_arguments: str | dict) -> str:
        tool = self._tools.get(name)
        if tool is None:
            return f"Error: unknown tool '{name}'"
        try:
            arguments = self._parse(raw_arguments)
        except ValueError as error:
            return f"Error: {error}"
        if tool.needs_approval and not await self._approve(name, arguments):
            return "Denied: the user rejected this action."
        return self._truncate(await self._execute(tool, arguments))

    @staticmethod
    def _parse(raw_arguments: str | dict) -> dict:
        if isinstance(raw_arguments, dict):
            return raw_arguments
        parsed = json.loads(raw_arguments or "{}")
        if not isinstance(parsed, dict):
            raise ValueError("tool arguments must be a JSON object")
        return parsed

    @staticmethod
    async def _execute(tool: Tool, arguments: dict) -> str:
        try:
            return await tool.handler(**arguments)
        except ToolError as error:
            return f"Error: {error}"
        except TypeError as error:
            return f"Error: invalid arguments: {error}"
        except OSError as error:
            return f"Error: {error}"

    def _truncate(self, output: str) -> str:
        if len(output) <= self._max_output_chars:
            return output
        return output[: self._max_output_chars] + "\n... output truncated"
