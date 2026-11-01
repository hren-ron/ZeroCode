from zerocode.tools.registry import ToolRegistry
from zerocode.tools.schema import ToolSchema, ToolParameter

add_schema = ToolSchema(
    parameters=(
        ToolParameter(name="a", type="integer"),
        ToolParameter(name="b", type="integer"),
    )
)

def test_register_tool():
    registry = ToolRegistry()

    def hello(name: str) -> str:
        return f"Hello, {name}"

    registry.register(
        name="hello",
        description="Say hello to a user",
        handler=hello,
        schema=add_schema,
    )

    tool = registry.get("hello")

    assert tool.name == "hello"
    assert tool.description == "Say hello to a user"
    assert tool.handler is hello

def test_list_tools():
    registry = ToolRegistry()

    def hello(name: str) -> str:
        return f"Hello, {name}"

    def goodbye(name: str) -> str:
        return f"Goodbye, {name}"

    registry.register(
        name="hello",
        description="Say hello",
        handler=hello,
        schema=add_schema,
    )

    registry.register(
        name="goodbye",
        description="Say goodbye",
        handler=goodbye,
        schema=add_schema,
    )

    tools = registry.list_tools()

    assert len(tools) == 2
    assert tools[0].name == "hello"
    assert tools[1].name == "goodbye"

import pytest


def test_register_duplicate_tool():
    registry = ToolRegistry()

    def hello() -> str:
        return "hello"

    registry.register(
        name="hello",
        description="Say hello",
        handler=hello,
        schema=add_schema,
    )

    with pytest.raises(
        ValueError,
        match="Tool already registered: hello",
    ):
        registry.register(
            name="hello",
            description="Another hello",
            handler=hello,
            schema=add_schema,
        )

def test_get_unknown_tool():
    registry = ToolRegistry()

    with pytest.raises(
        KeyError,
        match="Tool not found: hello",
    ):
        registry.get("hello")


def test_to_openai_tools_with_single_tool():
    registry = ToolRegistry()

    schema = ToolSchema(
        parameters=(
            ToolParameter(
                name="path",
                type="string",
                description="File path",
            ),
        )
    )

    registry.register(
        name="read_file",
        description="Read a file",
        handler=lambda path: path,
        schema=schema,
    )

    tools = registry.to_openai_tools()

    assert len(tools) == 1
    assert tools[0]["type"] == "function"
    assert tools[0]["function"]["name"] == "read_file"
    assert tools[0]["function"]["description"] == "Read a file"

def test_to_openai_tools_includes_json_schema():
    registry = ToolRegistry()

    schema = ToolSchema(
        parameters=(
            ToolParameter(
                name="path",
                type="string",
                description="File path",
            ),
            ToolParameter(
                name="encoding",
                type="string",
                description="File encoding",
                required=False,
            ),
        )
    )

    registry.register(
        name="read_file",
        description="Read a file",
        handler=lambda path, encoding="utf-8": path,
        schema=schema,
    )

    tools = registry.to_openai_tools()

    parameters = tools[0]["function"]["parameters"]

    assert parameters == schema.to_json_schema()
    assert parameters["type"] == "object"
    assert parameters["required"] == ["path"]
    assert parameters["properties"]["path"]["type"] == "string"
    assert parameters["properties"]["encoding"]["type"] == "string"

def test_to_openai_tools_with_multiple_tools():
    registry = ToolRegistry()

    empty_schema = ToolSchema()

    registry.register(
        name="read_file",
        description="Read a file",
        handler=lambda: "content",
        schema=empty_schema,
    )

    registry.register(
        name="list_files",
        description="List files",
        handler=lambda: [],
        schema=empty_schema,
    )

    tools = registry.to_openai_tools()

    assert len(tools) == 2

    tool_names = [
        tool["function"]["name"]
        for tool in tools
    ]

    assert tool_names == ["read_file", "list_files"]

def test_to_openai_tools_with_empty_registry():
    registry = ToolRegistry()

    tools = registry.to_openai_tools()

    assert tools == []