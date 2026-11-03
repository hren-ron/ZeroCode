
import pytest

from zerocode.workspace import Workspace
from zerocode.tools.search_code import SearchCodeTool


@pytest.fixture
def search_tool(tmp_path):
    workspace = Workspace(tmp_path)

    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()

    (tmp_path / "src" / "agent.py").write_text(
        "class Agent:\n"
        "    def execute(self):\n"
        "        pass\n",
        encoding="utf-8",
    )

    (tmp_path / "tests" / "test_agent.py").write_text(
        "def test_agent():\n"
        "    assert True\n",
        encoding="utf-8",
    )

    return SearchCodeTool(workspace)


def test_search_code(search_tool):
    results = search_tool.execute("def execute")

    assert len(results) == 1
    assert "src/agent.py:2:" in results[0]


def test_search_code_case_insensitive(search_tool):
    results = search_tool.execute("CLASS AGENT")

    assert len(results) == 1


def test_search_code_file_pattern(search_tool):
    results = search_tool.execute(
        query="def",
        file_pattern="test_*.py",
    )

    assert len(results) == 1
    assert "tests/test_agent.py" in results[0]


def test_search_code_max_results(search_tool):
    results = search_tool.execute(
        query="def",
        max_results=1,
    )

    assert len(results) == 1


@pytest.mark.parametrize(
    "kwargs",
    [
        {"query": ""},
        {"query": "   "},
        {"query": "Agent", "max_results": 0},
        {"query": "Agent", "max_results": -1},
        {"query": "Agent", "max_results": True},
        {"query": "Agent", "case_sensitive": 1},
    ],
)
def test_search_code_invalid_arguments(search_tool, kwargs):
    with pytest.raises(ValueError):
        search_tool.execute(**kwargs)

def test_search_code_rejects_path_outside_workspace(search_tool):
    with pytest.raises(PermissionError):
        search_tool.execute("Agent", path="../outside")
