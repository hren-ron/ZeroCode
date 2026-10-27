
from pathlib import Path

import pytest

from zerocode.tools.read_file import ReadFileTool
from zerocode.workspace import Workspace


@pytest.fixture
def workspace(tmp_path: Path) -> Workspace:
    return Workspace(tmp_path)


@pytest.fixture
def read_file_tool(workspace: Workspace) -> ReadFileTool:
    return ReadFileTool(workspace)


def test_read_file_returns_content(
    tmp_path: Path,
    read_file_tool: ReadFileTool,
) -> None:
    file_path = tmp_path / "README.md"
    file_path.write_text("# ZeroCode", encoding="utf-8")

    result = read_file_tool.execute("README.md")

    assert result == "# ZeroCode"


def test_read_file_supports_relative_subdirectory(
    tmp_path: Path,
    read_file_tool: ReadFileTool,
) -> None:
    source_dir = tmp_path / "src" / "zerocode"
    source_dir.mkdir(parents=True)

    file_path = source_dir / "agent.py"
    file_path.write_text("class Agent:\n    pass\n", encoding="utf-8")

    result = read_file_tool.execute("src/zerocode/agent.py")

    assert result == "class Agent:\n    pass\n"


def test_read_file_rejects_path_outside_workspace(
    tmp_path: Path,
    read_file_tool: ReadFileTool,
) -> None:
    outside_file = tmp_path.parent / "outside.txt"
    outside_file.write_text("secret", encoding="utf-8")

    try:
        with pytest.raises(PermissionError):
            read_file_tool.execute("../outside.txt")
    finally:
        outside_file.unlink(missing_ok=True)


def test_read_file_raises_for_missing_file(
    read_file_tool: ReadFileTool,
) -> None:
    with pytest.raises(FileNotFoundError):
        read_file_tool.execute("missing.txt")


def test_read_file_rejects_directory(
    tmp_path: Path,
    read_file_tool: ReadFileTool,
) -> None:
    (tmp_path / "src").mkdir()

    with pytest.raises(FileNotFoundError):
        read_file_tool.execute("src")


def test_read_file_reports_decoding_error(
    tmp_path: Path,
    read_file_tool: ReadFileTool,
) -> None:
    file_path = tmp_path / "invalid.txt"
    file_path.write_bytes(b"\xff\xfe\xfa")

    with pytest.raises(ValueError, match="Unable to decode"):
        read_file_tool.execute("invalid.txt")
