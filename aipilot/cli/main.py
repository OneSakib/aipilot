import asyncio
from pathlib import Path
from typing import Annotated
from uuid import uuid4

import typer
import uvicorn
from langgraph.checkpoint.memory import MemorySaver
from rich.console import Console
from rich.prompt import Confirm
from rich.table import Table

from aipilot.agent.factory import create_agent
from aipilot.agent.runner import run_agent
from aipilot.cli.render import Renderer, format_arguments
from aipilot.config import get_settings
from aipilot.llm.registry import ModelRegistry
from aipilot.tools.base import Approver

app = typer.Typer(add_completion=False, no_args_is_help=True, help="Multi-model AI coding agent.")
console = Console()

WorkspaceOption = Annotated[
    Path,
    typer.Option("--workspace", "-w", exists=True, file_okay=False, resolve_path=True, help="Project folder."),
]
YesOption = Annotated[
    bool,
    typer.Option("--yes", "-y", help="Approve file writes and shell commands automatically."),
]


def make_approver(auto_approve: bool) -> Approver:
    async def approve(name: str, arguments: dict) -> bool:
        if auto_approve:
            return True
        question = f"[yellow]Allow {name}[/] [dim]{format_arguments(arguments)}[/]?"
        return await asyncio.to_thread(Confirm.ask, question, console=console, default=False)

    return approve


def models_table() -> Table:
    registry = ModelRegistry.from_file(get_settings().models_file)
    table = Table(title="Models")
    table.add_column("id")
    table.add_column("litellm name")
    table.add_column("key")
    table.add_column("ready")
    for spec in registry.models.values():
        table.add_row(spec.id, spec.name, spec.key_env, "[green]yes[/]" if spec.available else "[red]no[/]")
    return table


async def stream_turn(graph, renderer: Renderer, message: str, thread_id: str) -> None:
    async for event in run_agent(graph, message, thread_id):
        renderer.render(event)


async def chat_session(workspace: Path, auto_approve: bool) -> None:
    graph = create_agent(workspace, make_approver(auto_approve), MemorySaver())
    renderer = Renderer(console)
    thread_id = uuid4().hex
    console.print(f"[bold]AIPilot[/] in [cyan]{workspace}[/]  [dim]/models  /clear  /exit[/]")
    while True:
        try:
            message = (await asyncio.to_thread(console.input, "[bold green]you ›[/] ")).strip()
        except EOFError:
            break
        if message in ("/exit", "/quit"):
            break
        if message == "/clear":
            thread_id = uuid4().hex
            console.print("[dim]new conversation[/]")
        elif message == "/models":
            console.print(models_table())
        elif message:
            await stream_turn(graph, renderer, message, thread_id)


@app.command()
def chat(workspace: WorkspaceOption = Path("."), yes: YesOption = False) -> None:
    try:
        asyncio.run(chat_session(workspace, yes))
    except KeyboardInterrupt:
        console.print("\n[dim]bye[/]")


@app.command()
def run(prompt: str, workspace: WorkspaceOption = Path("."), yes: YesOption = False) -> None:
    graph = create_agent(workspace, make_approver(yes), MemorySaver())
    asyncio.run(stream_turn(graph, Renderer(console), prompt, uuid4().hex))


@app.command()
def models() -> None:
    console.print(models_table())


@app.command()
def serve(host: str = "127.0.0.1", port: int = 8000) -> None:
    uvicorn.run("aipilot.api.app:create_app", factory=True, host=host, port=port)
