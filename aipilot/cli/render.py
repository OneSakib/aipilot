import json

from rich.console import Console
from rich.markdown import Markdown
from rich.markup import escape
from rich.panel import Panel

PREVIEW_CHARS = 90


def format_arguments(arguments: str | dict) -> str:
    data = json.loads(arguments or "{}") if isinstance(arguments, str) else arguments
    parts = []
    for key, value in data.items():
        text = " ".join(str(value).split())
        parts.append(f"{key}={text[:PREVIEW_CHARS]}{'…' if len(text) > PREVIEW_CHARS else ''}")
    return " ".join(parts)


class Renderer:
    def __init__(self, console: Console):
        self.console = console

    def render(self, event: dict) -> None:
        getattr(self, f"_{event['type']}")(event)

    def _routed(self, event: dict) -> None:
        self.console.print(f"[dim]route[/] [cyan]{event['kind']}[/] [dim]→[/] [magenta]{event['model']}[/]")

    def _knowledge(self, event: dict) -> None:
        if event["skills"]:
            self.console.print(f"[dim]skills[/] {escape(', '.join(event['skills']))}")

    def _plan(self, event: dict) -> None:
        self.console.print(Panel(Markdown(event["text"]), title="plan", border_style="blue"))

    def _note(self, event: dict) -> None:
        self.console.print(f"[dim italic]{escape(event['text'])}[/]")

    def _tool_call(self, event: dict) -> None:
        arguments = escape(format_arguments(event["arguments"]))
        self.console.print(f"[yellow]⚙ {event['name']}[/] [dim]{arguments}[/]")

    def _tool_result(self, event: dict) -> None:
        first_line = event["output"].strip().splitlines()[0] if event["output"].strip() else "(no output)"
        style = "red" if first_line.startswith(("Error", "Denied")) else "dim"
        self.console.print(f"  [{style}]↳ {escape(first_line[:PREVIEW_CHARS * 2])}[/]")

    def _answer(self, event: dict) -> None:
        self.console.print()
        self.console.print(Markdown(event["text"]))
        self.console.print(f"[dim]— {event['model']}[/]\n")

    def _error(self, event: dict) -> None:
        self.console.print(f"[bold red]error[/] {escape(event['message'])}")
