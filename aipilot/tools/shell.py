import asyncio
import re

from aipilot.tools.base import STRING, Tool, ToolError, object_schema
from aipilot.tools.workspace import Workspace

BLOCKED = re.compile(r"\b(sudo|mkfs|shutdown|reboot)\b|rm\s+-rf\s+/(\s|$)|:\(\)\s*\{")


def shell_tools(workspace: Workspace, timeout: int) -> list[Tool]:
    async def run_command(command: str) -> str:
        if BLOCKED.search(command):
            raise ToolError("Command blocked for safety")
        process = await asyncio.create_subprocess_shell(
            command,
            cwd=workspace.root,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        try:
            output, _ = await asyncio.wait_for(process.communicate(), timeout)
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            raise ToolError(f"Command timed out after {timeout}s")
        return f"exit code {process.returncode}\n{output.decode(errors='replace')}"

    return [
        Tool(
            "run_command",
            "Run a shell command in the project root. Use for tests, installs, builds and git.",
            object_schema({"command": STRING}, ["command"]),
            run_command,
            needs_approval=True,
        ),
    ]
