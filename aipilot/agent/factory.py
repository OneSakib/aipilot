from pathlib import Path

from aipilot.agent.graph import build_graph
from aipilot.agent.nodes import AgentNodes
from aipilot.config import get_settings
from aipilot.knowledge import KnowledgeBase
from aipilot.llm.registry import ModelRegistry
from aipilot.router import Router
from aipilot.tools import build_toolbox
from aipilot.tools.base import Approver


def create_agent(workspace: Path, approve: Approver, checkpointer):
    settings = get_settings()
    workspace = workspace.resolve()
    registry = ModelRegistry.from_file(settings.models_file)
    knowledge = KnowledgeBase(workspace, [settings.skills_dir, workspace / ".aipilot" / "skills"])
    toolbox = build_toolbox(workspace, approve, settings)
    nodes = AgentNodes(Router(registry), registry, knowledge, toolbox, workspace, settings.max_steps)
    return build_graph(nodes, checkpointer)
