import pytest
from langgraph.checkpoint.memory import MemorySaver

from aipilot.agent.factory import create_agent
from aipilot.agent.runner import run_agent
from aipilot.tools.approval import approve_all, deny_all
from tests.fake_llm import FakeLLM, text_reply, tool_reply


async def collect(graph, message, thread_id="t1"):
    return [event async for event in run_agent(graph, message, thread_id)]


@pytest.fixture
def workspace(tmp_path):
    (tmp_path / "AGENT.md").write_text("Use snake_case.", encoding="utf-8")
    return tmp_path


async def test_coding_task_routes_writes_file_and_answers(workspace, monkeypatch):
    llm = FakeLLM(
        [
            text_reply("coding"),
            tool_reply("c1", "write_file", '{"path": "app/main.py", "content": "print(1)\\n"}'),
            tool_reply("c2", "run_command", '{"command": "python app/main.py"}'),
            text_reply("Created app/main.py and ran it."),
        ]
    )
    monkeypatch.setattr("aipilot.llm.client.litellm.acompletion", llm.acompletion)
    graph = create_agent(workspace, approve_all, MemorySaver())

    events = await collect(graph, "fix the python bug in main script")

    kinds = [event["type"] for event in events]
    assert kinds == ["routed", "knowledge", "tool_call", "tool_result", "tool_call", "tool_result", "answer"]
    assert events[0]["kind"] == "coding" and events[0]["model"] == "claude-sonnet"
    assert "debugging" in events[1]["skills"] and "python-backend" in events[1]["skills"]
    assert (workspace / "app" / "main.py").read_text() == "print(1)\n"
    assert "exit code 0" in events[5]["output"]
    assert events[-1]["text"] == "Created app/main.py and ran it."
    assert llm.calls[0]["model"].startswith("groq/")
    assert llm.calls[1]["model"] == "anthropic/claude-sonnet-5-5"
    assert "Use snake_case." in llm.calls[1]["messages"][0]["content"]


async def test_chat_request_uses_cheap_model(workspace, monkeypatch):
    llm = FakeLLM([text_reply("chat"), text_reply("Hello!")])
    monkeypatch.setattr("aipilot.llm.client.litellm.acompletion", llm.acompletion)
    graph = create_agent(workspace, approve_all, MemorySaver())

    events = await collect(graph, "hi there")

    assert events[0]["kind"] == "chat" and events[0]["model"] == "groq-llama"
    assert events[-1] == {"type": "answer", "text": "Hello!", "model": "groq-llama"}


async def test_complex_task_runs_planner_first(workspace, monkeypatch):
    llm = FakeLLM([text_reply("complex"), text_reply("1. Scaffold"), text_reply("Done")])
    monkeypatch.setattr("aipilot.llm.client.litellm.acompletion", llm.acompletion)
    graph = create_agent(workspace, approve_all, MemorySaver())

    events = await collect(graph, "build the whole project from scratch")

    assert [event["type"] for event in events] == ["routed", "knowledge", "plan", "answer"]
    assert "1. Scaffold" in llm.calls[2]["messages"][0]["content"]


async def test_denied_write_does_not_touch_disk(workspace, monkeypatch):
    llm = FakeLLM(
        [
            text_reply("coding"),
            tool_reply("c1", "write_file", '{"path": "x.py", "content": "1"}'),
            text_reply("Could not write."),
        ]
    )
    monkeypatch.setattr("aipilot.llm.client.litellm.acompletion", llm.acompletion)
    graph = create_agent(workspace, deny_all, MemorySaver())

    events = await collect(graph, "write a python file")

    assert not (workspace / "x.py").exists()
    assert events[3]["output"].startswith("Denied")


async def test_follow_up_keeps_coding_route_and_history(workspace, monkeypatch):
    llm = FakeLLM(
        [text_reply("coding"), text_reply("First answer"), text_reply("chat"), text_reply("Second answer")]
    )
    monkeypatch.setattr("aipilot.llm.client.litellm.acompletion", llm.acompletion)
    graph = create_agent(workspace, approve_all, MemorySaver())

    await collect(graph, "fix the python bug")
    events = await collect(graph, "yes do it")

    assert events[0]["kind"] == "coding"
    sent = llm.calls[3]["messages"]
    assert [message["role"] for message in sent] == ["system", "user", "assistant", "user"]


async def test_falls_back_to_next_model_on_failure(workspace, monkeypatch):
    class FlakyLLM(FakeLLM):
        async def acompletion(self, **options):
            if options["model"] == "anthropic/claude-sonnet-5-5":
                raise RuntimeError("rate limited")
            return await super().acompletion(**options)

    llm = FlakyLLM([text_reply("coding")])
    monkeypatch.setattr("aipilot.llm.client.litellm.acompletion", llm.acompletion)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    graph = create_agent(workspace, approve_all, MemorySaver())
    llm.replies.append(text_reply("From GPT"))

    events = await collect(graph, "fix the python bug")

    assert events[-1]["model"] == "gpt-5"


async def test_missing_keys_reports_error(workspace, monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY")
    monkeypatch.delenv("ANTHROPIC_API_KEY")
    graph = create_agent(workspace, approve_all, MemorySaver())

    events = await collect(graph, "hello")

    assert events[-1]["type"] == "error"
    assert "API key" in events[-1]["message"]
