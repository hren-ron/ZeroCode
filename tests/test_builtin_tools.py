
from pathlib import Path

import pytest

from zerocode.tools.builtin import register_builtin_tools
from zerocode.tools.registry import ToolRegistry
from zerocode.workspace import Workspace


@pytest.fixture
def registry_and_workspace(
    tmp_path: Path,
) -> tuple[ToolRegistry, Workspace]:
    registry = ToolRegistry()
    workspace = Workspace(tmp_path)

    register_builtin_tools(registry, workspace)

    return registry, workspace


def test_read_file_is_registered(
    registry_and_workspace: tuple[ToolRegistry, Workspace],
) -> None:
    registry, _ = registry_and_workspace

    tool = registry.get("read_file")

    assert tool.name == "read_file"
    assert tool.schema is not None


def test_execute_read_file_through_registry(
    tmp_path: Path,
    registry_and_workspace: tuple[ToolRegistry, Workspace],
) -> None:
    registry, _ = registry_and_workspace

    file_path = tmp_path / "README.md"
    file_path.write_text("# ZeroCode", encoding="utf-8")

    result = registry.execute(
        "read_file",
        {"path": "README.md"},
    )

    assert result == "# ZeroCode"


def test_invalid_arguments_do_not_execute_handler(
    registry_and_workspace: tuple[ToolRegistry, Workspace],
) -> None:
    registry, _ = registry_and_workspace

    with pytest.raises(ValueError, match="Missing required parameter"):
        registry.execute("read_file", {})


def test_path_traversal_is_rejected(
    tmp_path: Path,
    registry_and_workspace: tuple[ToolRegistry, Workspace],
) -> None:
    registry, _ = registry_and_workspace

    outside_file = tmp_path.parent / "outside.txt"
    outside_file.write_text("secret", encoding="utf-8")

    try:
        with pytest.raises(PermissionError):
            registry.execute(
                "read_file",
                {"path": "../outside.txt"},
            )
    finally:
        outside_file.unlink(missing_ok=True)
