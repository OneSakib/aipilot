from collections.abc import Iterator


def routed(payload: dict) -> Iterator[dict]:
    yield {"type": "routed", "kind": payload["kind"], "model": payload["model_id"]}


def knowledge(payload: dict) -> Iterator[dict]:
    if "skills" in payload:
        yield {"type": "knowledge", "skills": payload["skills"]}


def plan(payload: dict) -> Iterator[dict]:
    yield {"type": "plan", "text": payload["plan"]}


def agent(payload: dict) -> Iterator[dict]:
    message = payload["messages"][0]
    calls = message.get("tool_calls", [])
    if not calls:
        yield {"type": "answer", "text": message["content"], "model": payload["model_id"]}
        return
    if message["content"]:
        yield {"type": "note", "text": message["content"]}
    for call in calls:
        yield {
            "type": "tool_call",
            "name": call["function"]["name"],
            "arguments": call["function"]["arguments"],
        }


def tools(payload: dict) -> Iterator[dict]:
    for message in payload["messages"]:
        yield {"type": "tool_result", "name": message["name"], "output": message["content"]}


HANDLERS = {
    "understand": routed,
    "knowledge": knowledge,
    "plan": plan,
    "agent": agent,
    "tools": tools,
}


def events_from_update(update: dict) -> Iterator[dict]:
    for node, payload in update.items():
        yield from HANDLERS[node](payload or {})
