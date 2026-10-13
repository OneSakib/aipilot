from pathlib import Path

from aipilot.agent.history import close_dangling_calls, trim_history
from aipilot.agent.prompts import PLANNER_PROMPT, build_system_prompt
from aipilot.agent.state import AgentState
from aipilot.knowledge import KnowledgeBase
from aipilot.llm.client import complete
from aipilot.llm.registry import ModelRegistry
from aipilot.router import Router
from aipilot.router.follow_up import is_follow_up
from aipilot.tools.base import ToolBox


class AgentNodes:
    def __init__(
        self,
        router: Router,
        registry: ModelRegistry,
        knowledge: KnowledgeBase,
        toolbox: ToolBox,
        workspace: Path,
        max_steps: int,
    ):
        self.router = router
        self.registry = registry
        self.knowledge = knowledge
        self.toolbox = toolbox
        self.workspace = workspace
        self.max_steps = max_steps

    async def understand(self, state: AgentState) -> dict:
        route = await self.router.route(state["request"], state.get("kind"))
        return {"kind": route.kind, "model_id": route.model.id}

    async def load_knowledge(self, state: AgentState) -> dict:
        context, skills = self.knowledge.build_context(state["request"])
        if not skills and is_follow_up(state["request"]) and state.get("knowledge"):
            return {}
        return {"knowledge": context, "skills": skills}

    async def plan(self, state: AgentState) -> dict:
        messages = [
            {"role": "system", "content": f"{PLANNER_PROMPT}\n{state.get('knowledge', '')}"},
            {"role": "user", "content": state["request"]},
        ]
        _, reply = await complete(self.registry.candidates("planning"), messages)
        return {"plan": reply["content"]}

    async def agent(self, state: AgentState) -> dict:
        steps = state.get("steps", 0)
        tools = self.toolbox.schemas() if steps < self.max_steps else None
        system = build_system_prompt(self.workspace, state.get("knowledge", ""), state.get("plan", ""))
        history = trim_history(close_dangling_calls(state["messages"]))
        spec, reply = await complete(
            self.registry.candidates(state["kind"]),
            [{"role": "system", "content": system}, *history],
            tools,
        )
        return {"messages": [reply], "model_id": spec.id, "steps": steps + 1}

    async def tools(self, state: AgentState) -> dict:
        results = []
        for call in state["messages"][-1]["tool_calls"]:
            function = call["function"]
            output = await self.toolbox.run(function["name"], function["arguments"])
            results.append(
                {
                    "role": "tool",
                    "tool_call_id": call["id"],
                    "name": function["name"],
                    "content": output,
                }
            )
        return {"messages": results}
