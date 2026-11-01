
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from zerocode.agent import Agent


def make_response(content=None, tool_calls=None):
    response = Mock()
    response.content = content
    response.tool_calls = tool_calls or []

    response.model_dump.return_value = {
        "role": "assistant",
        "content": content,
        "tool_calls": tool_calls,
    }

    return response

def test_execute_tool_call():
    llm_client = Mock()
    tool_registry = Mock()

    tool_registry.execute.return_value = "README content"

    agent = Agent(
        llm_client=llm_client,
        tool_registry=tool_registry,
    )

    tool_call = SimpleNamespace(
        id="call_123",
        function=SimpleNamespace(
            name="read_file",
            arguments='{"path": "README.md"}',
        ),
    )

    result = agent.execute_tool_call(tool_call)

    tool_registry.execute.assert_called_once_with(
        "read_file",
        {"path": "README.md"},
    )

    assert result == {
        "role": "tool",
        "tool_call_id": "call_123",
        "content": "README content",
    }

def test_execute_tool_call_rejects_invalid_json():
    agent = Agent(
        llm_client=Mock(),
        tool_registry=Mock(),
    )

    tool_call = SimpleNamespace(
        id="call_123",
        function=SimpleNamespace(
            name="read_file",
            arguments="{invalid json",
        ),
    )

    with pytest.raises(ValueError):
        agent.execute_tool_call(tool_call)

def test_execute_tool_call_rejects_non_object_arguments():
    tool_registry = Mock()

    agent = Agent(
        llm_client=Mock(),
        tool_registry=tool_registry,
    )

    tool_call = SimpleNamespace(
        id="call_123",
        function=SimpleNamespace(
            name="read_file",
            arguments='["README.md"]',
        ),
    )

    with pytest.raises(ValueError):
        agent.execute_tool_call(tool_call)

    tool_registry.execute.assert_not_called()


def test_run_without_tool_calls():
    llm_client = Mock()
    tool_registry = Mock()

    llm_client.chat_with_tools.return_value = make_response(
        content="Hello, I am ZeroCode."
    )

    agent = Agent(llm_client, tool_registry)

    result = agent.run("Introduce yourself")

    assert result == "Hello, I am ZeroCode."
    llm_client.chat_with_tools.assert_called_once()
    tool_registry.execute.assert_not_called()


from copy import deepcopy


def test_run_with_tool_call():
    llm_client = Mock()
    tool_registry = Mock()

    tool_call = SimpleNamespace(
        id="call_123",
        function=SimpleNamespace(
            name="read_file",
            arguments='{"path": "README.md"}',
        ),
    )

    responses = [
        make_response(tool_calls=[tool_call]),
        make_response(content="The project is a coding agent."),
    ]

    messages_snapshots = []

    def mock_chat_with_tools(*, messages, tools):
        messages_snapshots.append(deepcopy(messages))
        return responses[len(messages_snapshots) - 1]

    llm_client.chat_with_tools.side_effect = mock_chat_with_tools
    tool_registry.execute.return_value = "# ZeroCode"

    agent = Agent(llm_client, tool_registry)

    result = agent.run("Summarize README.md")

    assert result == "The project is a coding agent."
    assert len(messages_snapshots) == 2

    tool_registry.execute.assert_called_once_with(
        "read_file",
        {"path": "README.md"},
    )

    second_messages = messages_snapshots[1]

    assert second_messages[-1] == {
        "role": "tool",
        "tool_call_id": "call_123",
        "content": "# ZeroCode",
    }

def test_run_exceeds_max_iterations():
    llm_client = Mock()
    tool_registry = Mock()

    tool_call = SimpleNamespace(
        id="call_123",
        function=SimpleNamespace(
            name="read_file",
            arguments='{"path": "README.md"}',
        ),
    )

    llm_client.chat_with_tools.return_value = make_response(
        tool_calls=[tool_call]
    )

    tool_registry.execute.return_value = "# ZeroCode"

    agent = Agent(
        llm_client=llm_client,
        tool_registry=tool_registry,
        max_iterations=3,
    )

    with pytest.raises(RuntimeError, match="maximum iterations"):
        agent.run("Read README.md")

    assert llm_client.chat_with_tools.call_count == 3
    assert tool_registry.execute.call_count == 3

@pytest.mark.parametrize("max_iterations", [0, -1])
def test_agent_rejects_invalid_max_iterations(max_iterations):
    with pytest.raises(ValueError, match="greater than zero"):
        Agent(
            llm_client=Mock(),
            tool_registry=Mock(),
            max_iterations=max_iterations,
        )

from copy import deepcopy


def test_run_with_multiple_tool_calls():
    llm_client = Mock()
    tool_registry = Mock()

    tool_calls = [
        SimpleNamespace(
            id="call_001",
            function=SimpleNamespace(
                name="read_file",
                arguments='{"path": "README.md"}',
            ),
        ),
        SimpleNamespace(
            id="call_002",
            function=SimpleNamespace(
                name="read_file",
                arguments='{"path": "pyproject.toml"}',
            ),
        ),
    ]

    responses = [
        make_response(tool_calls=tool_calls),
        make_response(content="Project analysis completed."),
    ]

    messages_snapshots = []

    def mock_chat_with_tools(*, messages, tools):
        messages_snapshots.append(deepcopy(messages))
        return responses[len(messages_snapshots) - 1]

    llm_client.chat_with_tools.side_effect = mock_chat_with_tools

    tool_registry.execute.side_effect = [
        "# ZeroCode",
        "[project]",
    ]

    agent = Agent(
        llm_client=llm_client,
        tool_registry=tool_registry,
        max_iterations=3,
    )

    result = agent.run(
        "Read README.md and pyproject.toml"
    )

    assert result == "Project analysis completed."

    assert llm_client.chat_with_tools.call_count == 2
    assert tool_registry.execute.call_count == 2

    tool_registry.execute.assert_any_call(
        "read_file",
        {"path": "README.md"},
    )

    tool_registry.execute.assert_any_call(
        "read_file",
        {"path": "pyproject.toml"},
    )

    second_messages = messages_snapshots[1]

    tool_messages = [
        message
        for message in second_messages
        if message["role"] == "tool"
    ]

    assert tool_messages == [
        {
            "role": "tool",
            "tool_call_id": "call_001",
            "content": "# ZeroCode",
        },
        {
            "role": "tool",
            "tool_call_id": "call_002",
            "content": "[project]",
        },
    ]