
from pathlib import Path

import pytest

from zerocode.workspace import Workspace


def test_workspace_initializes_with_absolute_root(
    tmp_path: Path,
) -> None:
    workspace = Workspace(tmp_path)

    assert workspace.root == tmp_path.resolve()
    assert workspace.root.is_absolute()


def test_workspace_rejects_nonexistent_root(
    tmp_path: Path,
) -> None:
    with pytest.raises(FileNotFoundError):
        Workspace(tmp_path / "missing")


def test_workspace_rejects_file_as_root(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "README.md"
    file_path.write_text("hello", encoding="utf-8")

    with pytest.raises(NotADirectoryError):
        Workspace(file_path)


def test_resolve_relative_path(
    tmp_path: Path,
) -> None:
    workspace = Workspace(tmp_path)

    result = workspace.resolve_path("src/zerocode/agent.py")

    assert result == (
        tmp_path / "src" / "zerocode" / "agent.py"
    ).resolve()


def test_resolve_normalizes_dot_segments(
    tmp_path: Path,
) -> None:
    workspace = Workspace(tmp_path)

    result = workspace.resolve_path("src/../README.md")

    assert result == (tmp_path / "README.md").resolve()


def test_resolve_rejects_parent_directory_traversal(
    tmp_path: Path,
) -> None:
    workspace = Workspace(tmp_path)

    with pytest.raises(PermissionError):
        workspace.resolve_path("../secret.txt")


def test_resolve_rejects_absolute_path_outside_workspace(
    tmp_path: Path,
) -> None:
    workspace = Workspace(tmp_path)
    outside = tmp_path.parent / "secret.txt"

    with pytest.raises(PermissionError):
        workspace.resolve_path(outside)


def test_resolve_allows_path_inside_workspace(
    tmp_path: Path,
) -> None:
    workspace = Workspace(tmp_path)
    file_path = tmp_path / "README.md"
    file_path.write_text("hello", encoding="utf-8")

    assert workspace.resolve_path("README.md") == file_path.resolve()
