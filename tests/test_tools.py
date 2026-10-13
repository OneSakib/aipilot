import pytest

from aipilot.config import get_settings
from aipilot.tools import build_toolbox
from aipilot.tools.approval import approve_all


@pytest.fixture
def toolbox(tmp_path):
    (tmp_path / "a.py").write_text("def hello():\n    return 1\n", encoding="utf-8")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "skip.py").write_text("def hello(): pass", encoding="utf-8")
    return build_toolbox(tmp_path, approve_all, get_settings())


async def test_read_and_edit(toolbox, tmp_path):
    assert (await toolbox.run("read_file", '{"path": "a.py", "start_line": 2}')).strip() == "return 1"
    await toolbox.run("edit_file", {"path": "a.py", "old_text": "return 1", "new_text": "return 2"})
    assert "return 2" in (tmp_path / "a.py").read_text()


async def test_edit_requires_unique_match(toolbox):
    result = await toolbox.run("edit_file", {"path": "a.py", "old_text": "e", "new_text": "x"})
    assert result.startswith("Error: old_text must match exactly once")


async def test_blocks_path_escape(toolbox):
    result = await toolbox.run("read_file", {"path": "../secret.txt"})
    assert "outside the workspace" in result


async def test_search_and_find_skip_ignored_dirs(toolbox):
    assert (await toolbox.run("search_code", {"pattern": "def hello"})).splitlines() == ["a.py:1: def hello():"]
    assert await toolbox.run("find_files", {"pattern": "*.py"}) == "a.py"


async def test_shell_runs_and_blocks(toolbox):
    assert "exit code 0" in await toolbox.run("run_command", {"command": "echo ok"})
    assert "blocked" in await toolbox.run("run_command", {"command": "sudo ls"})


async def test_bad_arguments_return_errors(toolbox):
    assert (await toolbox.run("read_file", "not json")).startswith("Error")
    assert (await toolbox.run("read_file", {"wrong": 1})).startswith("Error: invalid arguments")
    assert (await toolbox.run("nope", {})).startswith("Error: unknown tool")
