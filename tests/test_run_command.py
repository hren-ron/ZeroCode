
import pytest

from zerocode.workspace import Workspace
from zerocode.tools.run_command import RunCommandTool


@pytest.fixture
def run_command_tool(tmp_path):
    workspace = Workspace(tmp_path)
    return RunCommandTool(workspace)


def test_run_command_success(run_command_tool):
    result = run_command_tool.execute(
        ["python", "-c", "print('Hello ZeroCode')"]
    )

    assert "Exit code: 0" in result
    assert "Hello ZeroCode" in result


def test_run_command_failure(run_command_tool):
    result = run_command_tool.execute(
        ["python", "-c", "raise ValueError('test error')"]
    )

    assert "Exit code: 1" in result
    assert "ValueError" in result
    assert "test error" in result


def test_run_command_timeout(tmp_path):
    workspace = Workspace(tmp_path)
    tool = RunCommandTool(workspace, timeout=1)

    result = tool.execute(
        ["python", "-c", "import time; time.sleep(3)"]
    )

    assert "Exit code: 124" in result
    assert "timed out" in result.lower()


def test_run_command_rejects_empty_command(run_command_tool):
    with pytest.raises(ValueError):
        run_command_tool.execute([])


@pytest.mark.parametrize(
    "command",
    [
        [""],
        ["python", ""],
        ["python", 123],
    ],
)
def test_run_command_rejects_invalid_arguments(
    run_command_tool,
    command,
):
    with pytest.raises(ValueError):
        run_command_tool.execute(command)


def test_run_command_rejects_invalid_command_type(run_command_tool):
    with pytest.raises(ValueError):
        run_command_tool.execute("python main.py")
