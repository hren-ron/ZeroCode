
import pytest

from zerocode.workspace import Workspace
from zerocode.tools.list_files import ListFilesTool


@pytest.fixture
def list_tool(tmp_path):
    workspace = Workspace(tmp_path)

    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()

    (tmp_path / "src" / "agent.py").write_text(
        "class Agent: pass",
        encoding="utf-8",
    )
    (tmp_path / "src" / "client.py").write_text(
        "class Client: pass",
        encoding="utf-8",
    )
    (tmp_path / "tests" / "test_agent.py").write_text(
        "def test_agent(): pass",
        encoding="utf-8",
    )

    return ListFilesTool(workspace)


def test_list_files_recursive(list_tool):
    result = list_tool.execute()

    assert "src/agent.py" in result
    assert "src/client.py" in result
    assert "tests/test_agent.py" in result


def test_list_files_non_recursive(list_tool):
    result = list_tool.execute(recursive=False)

    assert "src" in result
    assert "tests" in result
    assert "src/agent.py" not in result


def test_list_files_max_entries(list_tool):
    result = list_tool.execute(max_entries=2)

    assert len(result) == 2


def test_list_files_excludes_ignored_directories(list_tool, tmp_path):
    ignored = tmp_path / ".venv"
    ignored.mkdir()

    (ignored / "package.py").write_text(
        "print('ignored')",
        encoding="utf-8",
    )

    result = list_tool.execute()

    assert not any(".venv" in path for path in result)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"path": ""},
        {"path": "   "},
        {"max_entries": 0},
        {"max_entries": -1},
        {"max_entries": True},
        {"recursive": 1},
    ],
)
def test_list_files_invalid_arguments(list_tool, kwargs):
    with pytest.raises(ValueError):
        list_tool.execute(**kwargs)


def test_list_files_rejects_path_outside_workspace(
    list_tool,
    tmp_path,
):
    with pytest.raises(PermissionError):
        list_tool.execute("../outside")
