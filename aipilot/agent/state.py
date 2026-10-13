import operator
from typing import Annotated, TypedDict


class AgentState(TypedDict, total=False):
    messages: Annotated[list[dict], operator.add]
    request: str
    kind: str
    model_id: str
    knowledge: str
    skills: list[str]
    plan: str
    steps: int
