# AIPilot

Multi-model AI coding agent for the terminal. It classifies each request, routes it to the right model (GPT, Claude, Grok, Groq), loads `AGENT.md` and the matching skills, then works on your project with file, search and shell tools.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

Add at least one API key to `.env`. Routing uses whichever keys exist and falls back down each route automatically.

## Use

```bash
aipilot chat -w ~/my-project
aipilot run "add a /health endpoint and a test" -w ~/my-project --yes
aipilot models
aipilot serve --port 8000
```

Without `--yes`, every file write and shell command asks for approval.

Chat commands: `/models`, `/clear`, `/exit`.

## How a request flows

```
understand -> knowledge -> (plan) -> agent <-> tools -> answer
```

1. understand: a fast model labels the request `chat`, `coding`, `design` or `complex`.
2. knowledge: loads `AGENT.md` plus the best matching skills.
3. plan: only for `complex`, the strongest model writes a step plan.
4. agent and tools: the routed model calls tools until the task is done.

## Layout

| Path | Purpose |
| --- | --- |
| `models.yaml` | Model catalog and routes per task kind. Edit this to change models. |
| `skills/<name>/SKILL.md` | Knowledge packs with `triggers` in the front matter. |
| `AGENT.md` | Project rules the agent always follows. Put one in each project. |
| `aipilot/llm` | Model registry and LiteLLM client with fallback. |
| `aipilot/router` | Request classifier and router. |
| `aipilot/knowledge` | `AGENT.md` and skill loader. |
| `aipilot/tools` | read, write, edit, list, find, search and shell tools. |
| `aipilot/agent` | LangGraph state, nodes, graph, events and runner. |
| `aipilot/api` | FastAPI app with `/v1/chat`, `/v1/chat/stream`, `/v1/models`. |
| `aipilot/cli` | Typer commands and Rich rendering. |
| `tests` | Offline tests with a fake LLM. |

## Customize

- Change a model: edit `name` in `models.yaml`. Names follow LiteLLM format (`provider/model`).
- Change routing: edit the lists under `routes`. The first model with an API key wins.
- Add a skill: create `skills/<name>/SKILL.md` with `name`, `description` and `triggers`. Project-only skills go in `<project>/.aipilot/skills/`.
- Add a tool: create a `Tool` in `aipilot/tools/` and register it in `aipilot/tools/__init__.py`.

## API

```bash
curl -X POST localhost:8000/v1/chat -H "Content-Type: application/json" \
  -d '{"message": "explain this repo", "project": "."}'
```

Set `"auto_approve": true` to let the API write files and run commands. The default denies them. `project` must stay inside `AIPILOT_WORKSPACE`.

## Tests

```bash
pytest
```
