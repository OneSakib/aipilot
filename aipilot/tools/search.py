import re
from fnmatch import fnmatch

from aipilot.tools.base import STRING, Tool, ToolError, object_schema
from aipilot.tools.workspace import Workspace

MAX_MATCHES = 100
MAX_FILES = 300
MAX_FILE_BYTES = 1_000_000


def search_tools(workspace: Workspace) -> list[Tool]:
    async def search_code(pattern: str, path: str = ".") -> str:
        try:
            regex = re.compile(pattern)
        except re.error as error:
            raise ToolError(f"Invalid regex: {error}")
        matches = []
        for file in workspace.walk(workspace.resolve(path)):
            if file.stat().st_size > MAX_FILE_BYTES:
                continue
            try:
                lines = file.read_text(encoding="utf-8").splitlines()
            except UnicodeDecodeError:
                continue
            for number, line in enumerate(lines, start=1):
                if regex.search(line):
                    matches.append(f"{workspace.relative(file)}:{number}: {line.strip()[:200]}")
                    if len(matches) >= MAX_MATCHES:
                        return "\n".join(matches)
        return "\n".join(matches) or "No matches"

    async def find_files(pattern: str, path: str = ".") -> str:
        found = []
        for file in workspace.walk(workspace.resolve(path)):
            relative = workspace.relative(file)
            if fnmatch(relative, pattern) or fnmatch(file.name, pattern):
                found.append(relative)
                if len(found) >= MAX_FILES:
                    break
        return "\n".join(found) or "No files found"

    return [
        Tool(
            "search_code",
            "Search file contents with a regular expression. Returns path:line: text.",
            object_schema({"pattern": STRING, "path": STRING}, ["pattern"]),
            search_code,
        ),
        Tool(
            "find_files",
            "Find files by glob pattern such as '*.py' or 'src/**/*.tsx'.",
            object_schema({"pattern": STRING, "path": STRING}, ["pattern"]),
            find_files,
        ),
    ]
