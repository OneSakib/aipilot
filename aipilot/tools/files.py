from aipilot.tools.base import INTEGER, STRING, Tool, ToolError, object_schema
from aipilot.tools.workspace import IGNORED_DIRS, Workspace


def file_tools(workspace: Workspace) -> list[Tool]:
    def existing_file(path: str):
        target = workspace.resolve(path)
        if not target.is_file():
            raise ToolError(f"File not found: {path}")
        return target

    async def read_file(path: str, start_line: int = 1, end_line: int | None = None) -> str:
        lines = existing_file(path).read_text(encoding="utf-8", errors="replace").splitlines()
        return "\n".join(lines[max(start_line - 1, 0) : end_line])

    async def write_file(path: str, content: str) -> str:
        target = workspace.resolve(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return f"Wrote {len(content.splitlines())} lines to {path}"

    async def edit_file(path: str, old_text: str, new_text: str) -> str:
        target = existing_file(path)
        source = target.read_text(encoding="utf-8")
        matches = source.count(old_text)
        if matches != 1:
            raise ToolError(f"old_text must match exactly once, found {matches} matches")
        target.write_text(source.replace(old_text, new_text), encoding="utf-8")
        return f"Edited {path}"

    async def list_dir(path: str = ".") -> str:
        target = workspace.resolve(path)
        if not target.is_dir():
            raise ToolError(f"Directory not found: {path}")
        entries = sorted(target.iterdir(), key=lambda entry: (entry.is_file(), entry.name))
        visible = [entry for entry in entries if entry.name not in IGNORED_DIRS]
        return "\n".join(f"{entry.name}/" if entry.is_dir() else entry.name for entry in visible) or "(empty)"

    return [
        Tool(
            "read_file",
            "Read a text file, optionally limited to a 1-based line range.",
            object_schema({"path": STRING, "start_line": INTEGER, "end_line": INTEGER}, ["path"]),
            read_file,
        ),
        Tool(
            "write_file",
            "Create a file or fully overwrite an existing one.",
            object_schema({"path": STRING, "content": STRING}, ["path", "content"]),
            write_file,
            needs_approval=True,
        ),
        Tool(
            "edit_file",
            "Replace one exact, unique occurrence of old_text with new_text in a file.",
            object_schema(
                {"path": STRING, "old_text": STRING, "new_text": STRING},
                ["path", "old_text", "new_text"],
            ),
            edit_file,
            needs_approval=True,
        ),
        Tool(
            "list_dir",
            "List the entries of one directory.",
            object_schema({"path": STRING}, []),
            list_dir,
        ),
    ]
