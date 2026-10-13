---
name: python-backend
description: Python backend services with FastAPI, Django, Celery and LangGraph
triggers: [python, fastapi, django, celery, flask, pydantic, sqlalchemy, backend, api, endpoint, langgraph, langchain, rag, redis, postgres]
---
- Group code by feature or layer: `api/` for routes, `services/` for business logic, `models/` for data, `schemas/` for request and response types.
- Keep route handlers thin. Validate input with Pydantic and delegate work to services.
- Use `async def` for I/O-bound FastAPI routes. Move CPU-heavy or slow work to Celery tasks.
- Read configuration from environment variables through one settings module.
- Add type hints everywhere. Prefer dataclasses or Pydantic models over loose dicts.
- Raise specific exceptions in services and map them to HTTP errors in one place.
- Write pytest tests next to the feature, using fixtures for the app client and database.
