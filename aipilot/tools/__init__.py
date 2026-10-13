from pathlib import Path

from aipilot.config import Settings
from aipilot.tools.base import Approver, ToolBox
from aipilot.tools.files import file_tools
from aipilot.tools.search import search_tools
from aipilot.tools.shell import shell_tools
from aipilot.tools.workspace import Workspace


def build_toolbox(workspace_root: Path, approve: Approver, settings: Settings) -> ToolBox:
    workspace = Workspace(workspace_root)
    tools = [
        *file_tools(workspace),
        *search_tools(workspace),
        *shell_tools(workspace, settings.command_timeout),
    ]
    return ToolBox(tools, approve, settings.max_output_chars)
