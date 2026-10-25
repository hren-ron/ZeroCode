from zerocode.tools.registry import ToolRegistry


def test_register_tool():
    registry = ToolRegistry()

    def hello(name: str) -> str:
        return f"Hello, {name}"

    registry.register(
        name="hello",
        description="Say hello to a user",
        handler=hello,
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
    )

    registry.register(
        name="goodbye",
        description="Say goodbye",
        handler=goodbye,
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
    )

    with pytest.raises(
        ValueError,
        match="Tool already registered: hello",
    ):
        registry.register(
            name="hello",
            description="Another hello",
            handler=hello,
        )

def test_get_unknown_tool():
    registry = ToolRegistry()

    with pytest.raises(
        KeyError,
        match="Tool not found: hello",
    ):
        registry.get("hello")