
import pytest

from zerocode.workspace import Workspace
from zerocode.tools.write_file import WriteFileTool


@pytest.fixture
def write_file_tool(tmp_path):
    """Create a WriteFileTool with a temporary workspace."""
    workspace = Workspace(tmp_path)
    return WriteFileTool(workspace)


def test_write_file_creates_new_file(write_file_tool, tmp_path):
    """Test creating a new file."""
    content = "print('Hello ZeroCode')"

    result = write_file_tool.execute(
        path="src/main.py",
        content=content,
    )

    target = tmp_path / "src" / "main.py"

    assert target.exists()
    assert target.read_text(encoding="utf-8") == content
    assert "Successfully wrote file" in result


def test_write_file_overwrites_existing_file(write_file_tool, tmp_path):
    """Test overwriting an existing file."""
    target = tmp_path / "main.py"
    target.write_text("old content", encoding="utf-8")

    new_content = "new content"

    write_file_tool.execute(
        path="main.py",
        content=new_content,
    )

    assert target.read_text(encoding="utf-8") == new_content


def test_write_file_creates_parent_directories(write_file_tool, tmp_path):
    """Test creating missing parent directories."""
    content = "print('nested')"

    write_file_tool.execute(
        path="src/tools/nested/main.py",
        content=content,
    )

    target = tmp_path / "src" / "tools" / "nested" / "main.py"

    assert target.exists()
    assert target.read_text(encoding="utf-8") == content


def test_write_file_rejects_path_outside_workspace(write_file_tool):
    """Test rejecting paths outside the workspace."""
    with pytest.raises(PermissionError):
        write_file_tool.execute(
            path="../outside.py",
            content="malicious content",
        )


@pytest.mark.parametrize(
    "path",
    [
        "",
        " ",
    ],
)
def test_write_file_rejects_empty_path(write_file_tool, path):
    """Test rejecting empty paths."""
    with pytest.raises(ValueError):
        write_file_tool.execute(
            path=path,
            content="content",
        )


def test_write_file_rejects_non_string_content(write_file_tool):
    """Test rejecting non-string content."""
    with pytest.raises(TypeError):
        write_file_tool.execute(
            path="main.py",
            content=123,
        )
