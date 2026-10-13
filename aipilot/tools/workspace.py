import os
from collections.abc import Iterator
from pathlib import Path

from aipilot.tools.base import ToolError

IGNORED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    "dist",
    "build",
    ".next",
    ".idea",
    ".mypy_cache",
    ".pytest_cache",
}


class Workspace:
    def __init__(self, root: Path):
        self.root = root.resolve()

    def resolve(self, relative: str) -> Path:
        target = (self.root / relative).resolve()
        if not target.is_relative_to(self.root):
            raise ToolError(f"Path is outside the workspace: {relative}")
        return target

    def relative(self, path: Path) -> str:
        return path.relative_to(self.root).as_posix()

    def walk(self, start: Path) -> Iterator[Path]:
        if start.is_file():
            yield start
            return
        for folder, dirs, files in os.walk(start):
            dirs[:] = sorted(name for name in dirs if name not in IGNORED_DIRS)
            for name in sorted(files):
                yield Path(folder) / name
