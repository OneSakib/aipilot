import litellm

from aipilot.llm.registry import ModelSpec

litellm.drop_params = True
litellm.suppress_debug_info = True

REQUEST_TIMEOUT = 180


class ModelCallError(Exception):
    pass


def normalize(message) -> dict:
    result = {"role": "assistant", "content": message.content or ""}
    calls = getattr(message, "tool_calls", None)
    if calls:
        result["tool_calls"] = [
            {
                "id": call.id,
                "type": "function",
                "function": {
                    "name": call.function.name,
                    "arguments": call.function.arguments or "{}",
                },
            }
            for call in calls
        ]
    return result


async def call_model(spec: ModelSpec, messages: list[dict], tools: list[dict] | None) -> dict:
    options = {"model": spec.name, "messages": messages, "timeout": REQUEST_TIMEOUT}
    if tools:
        options["tools"] = tools
    response = await litellm.acompletion(**options)
    return normalize(response.choices[0].message)


async def complete(
    candidates: list[ModelSpec],
    messages: list[dict],
    tools: list[dict] | None = None,
) -> tuple[ModelSpec, dict]:
    failures = []
    for spec in candidates:
        try:
            return spec, await call_model(spec, messages, tools)
        except Exception as error:
            failures.append(f"{spec.id}: {error}")
    raise ModelCallError(" | ".join(failures))
