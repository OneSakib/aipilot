import pytest


@pytest.fixture(autouse=True)
def model_keys(monkeypatch):
    for name in ("GROQ_API_KEY", "ANTHROPIC_API_KEY"):
        monkeypatch.setenv(name, "test-key")
    for name in ("OPENAI_API_KEY", "XAI_API_KEY"):
        monkeypatch.delenv(name, raising=False)
