from zerocode.tools.list_files import ListFilesTool
from zerocode.tools.read_file import ReadFileTool
from zerocode.tools.registry import ToolRegistry
from zerocode.tools.run_command import RunCommandTool
from zerocode.tools.schema import ToolSchema, ToolParameter
from zerocode.tools.search_code import SearchCodeTool
from zerocode.tools.write_file import WriteFileTool
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

    search_code_tool = SearchCodeTool(workspace)

    registry.register(
        name="search_code",
        description="Search source code by keyword inside the workspace.",
        handler=search_code_tool.execute,
        schema=ToolSchema(
            parameters=(
                ToolParameter(
                    name="query",
                    type="string",
                    description="Keyword or text to search for.",
                ),
                ToolParameter(
                    name="path",
                    type="string",
                    description="Directory path to search.",
                    required=False,
                ),
                ToolParameter(
                    name="file_pattern",
                    type="string",
                    description="File name pattern, such as *.py.",
                    required=False,
                ),
                ToolParameter(
                    name="case_sensitive",
                    type="boolean",
                    description="Whether the search is case-sensitive.",
                    required=False,
                ),
                ToolParameter(
                    name="max_results",
                    type="integer",
                    description="Maximum number of matching lines to return.",
                    required=False,
                ),
            )
        ),
    )

    write_file_tool = WriteFileTool(workspace)

    registry.register(
        name="write_file",
        description="Create or overwrite a file in the workspace.",
        schema=ToolSchema(
            parameters=(
                ToolParameter(
                    name="path",
                    type="string",
                    description="Relative path of the file to write.",
                ),
                ToolParameter(
                    name="content",
                    type="string",
                    description="Content to write into the file.",
                ),
            )
        ),
        handler=write_file_tool.execute,
    )

    run_command_tool = RunCommandTool(workspace)

    registry.register(
        name="run_command",
        description="Execute a command in the workspace and return its output.",
        schema=ToolSchema(
            parameters=(
                ToolParameter(
                    name="command",
                    type="array",
                    description="Command and arguments, e.g. ['pytest', '-q'].",
                ),
            )
        ),
        handler=run_command_tool.execute,
    )

