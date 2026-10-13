from collections.abc import AsyncIterator

from aipilot.agent.events import events_from_update

RECURSION_LIMIT = 200


async def run_agent(graph, message: str, thread_id: str) -> AsyncIterator[dict]:
    config = {"configurable": {"thread_id": thread_id}, "recursion_limit": RECURSION_LIMIT}
    state = {
        "messages": [{"role": "user", "content": message}],
        "request": message,
        "plan": "",
        "steps": 0,
    }
    try:
        async for update in graph.astream(state, config, stream_mode="updates"):
            for event in events_from_update(update):
                yield event
    except Exception as error:
        yield {"type": "error", "message": str(error)}
