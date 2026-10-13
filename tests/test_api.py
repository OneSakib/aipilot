import json

from fastapi.testclient import TestClient

from aipilot.api.app import create_app
from aipilot.config import get_settings
from tests.fake_llm import FakeLLM, text_reply, tool_reply


def make_client(monkeypatch, tmp_path, llm):
    monkeypatch.setenv("AIPILOT_WORKSPACE", str(tmp_path))
    get_settings.cache_clear()
    monkeypatch.setattr("aipilot.llm.client.litellm.acompletion", llm.acompletion)
    return TestClient(create_app())


def test_models_and_health(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path, FakeLLM([]))
    assert client.get("/health").json()["status"] == "ok"
    models = {item["id"]: item["available"] for item in client.get("/v1/models").json()}
    assert models["claude-sonnet"] is True and models["gpt-5"] is False


def test_chat_returns_answer_and_respects_approval(monkeypatch, tmp_path):
    llm = FakeLLM(
        [
            text_reply("coding"),
            tool_reply("c1", "write_file", '{"path": "a.py", "content": "1"}'),
            text_reply("Blocked as expected."),
        ]
    )
    client = make_client(monkeypatch, tmp_path, llm)

    response = client.post("/v1/chat", json={"message": "fix python code"})

    body = response.json()
    assert response.status_code == 200
    assert body["kind"] == "coding" and body["answer"] == "Blocked as expected."
    assert not (tmp_path / "a.py").exists()


def test_chat_with_auto_approve_writes_file(monkeypatch, tmp_path):
    llm = FakeLLM(
        [
            text_reply("coding"),
            tool_reply("c1", "write_file", '{"path": "a.py", "content": "1"}'),
            text_reply("Written."),
        ]
    )
    client = make_client(monkeypatch, tmp_path, llm)

    response = client.post("/v1/chat", json={"message": "fix python code", "auto_approve": True})

    assert response.status_code == 200
    assert (tmp_path / "a.py").read_text() == "1"


def test_stream_emits_sse_events(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path, FakeLLM([text_reply("chat"), text_reply("Hi")]))

    response = client.post("/v1/chat/stream", json={"message": "hello"})

    events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith("data: ")]
    assert [event["type"] for event in events] == ["session", "routed", "knowledge", "answer"]


def test_rejects_project_outside_workspace(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path, FakeLLM([]))
    response = client.post("/v1/chat", json={"message": "hi", "project": "../.."})
    assert response.status_code == 400
