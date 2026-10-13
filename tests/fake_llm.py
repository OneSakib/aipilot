from types import SimpleNamespace


def text_reply(content: str):
    return SimpleNamespace(content=content, tool_calls=None)


def tool_reply(call_id: str, name: str, arguments: str):
    call = SimpleNamespace(id=call_id, function=SimpleNamespace(name=name, arguments=arguments))
    return SimpleNamespace(content="", tool_calls=[call])


class FakeLLM:
    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []

    async def acompletion(self, **options):
        self.calls.append(options)
        return SimpleNamespace(choices=[SimpleNamespace(message=self.replies.pop(0))])
