MAX_MESSAGES = 60


def close_dangling_calls(messages: list[dict]) -> list[dict]:
    answered = {message["tool_call_id"] for message in messages if message["role"] == "tool"}
    repaired = []
    for message in messages:
        repaired.append(message)
        for call in message.get("tool_calls", []):
            if call["id"] not in answered:
                repaired.append(
                    {
                        "role": "tool",
                        "tool_call_id": call["id"],
                        "name": call["function"]["name"],
                        "content": "Interrupted before this tool ran.",
                    }
                )
    return repaired


def trim_history(messages: list[dict]) -> list[dict]:
    if len(messages) <= MAX_MESSAGES:
        return messages
    last_user = max(index for index, message in enumerate(messages) if message["role"] == "user")
    start = len(messages) - MAX_MESSAGES
    while start < last_user and messages[start]["role"] != "user":
        start += 1
    return messages[min(start, last_user) :]
