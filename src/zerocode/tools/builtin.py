from zerocode.tools.list_files import ListFilesTool
from zerocode.tools.read_file import ReadFileTool
from zerocode.tools.registry import ToolRegistry
from zerocode.tools.schema import ToolSchema, ToolParameter
from zerocode.workspace import Workspace


def register_builtin_tools(
        registry: ToolRegistry,
        workspace: Workspace,
) -> None:
    """Register built-in tools for the given workspace."""

    read_file_tool = ReadFileTool(workspace)

    read_file_schema = ToolSchema(
        parameters=(
            ToolParameter(
                name="path",
                type="string",
                description="Path to a text file inside the workspace",
            ),
            ToolParameter(
                name="encoding",
                type="string",
                description="Text encoding; defaults to utf-8",
                required=False,
            ),
        )
    )

    registry.register(
        name="read_file",
        description="Read a text file from the workspace",
        handler=read_file_tool.execute,
        schema=read_file_schema,
    )

    list_files_tool = ListFilesTool(workspace)

    registry.register(
        name="list_files",
        description="List files and directories inside the workspace.",
        handler=list_files_tool.execute,
        schema=ToolSchema(
            parameters=(
                ToolParameter(
                    name="path",
                    type="string",
                    description="Directory path relative to the workspace root.",
                    required=False,
                ),
                ToolParameter(
                    name="recursive",
                    type="boolean",
                    description="Whether to list files recursively.",
                    required=False,
                ),
                ToolParameter(
                    name="max_entries",
                    type="integer",
                    description="Maximum number of entries to return.",
                    required=False,
                ),
            )
        ),
    )

