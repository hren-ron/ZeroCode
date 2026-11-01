import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from zerocode.agent import Agent
from zerocode.tools.executor import ToolExecutor, ToolCapacityError


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

def make_tool_call(
    name: str = "read_file",
    arguments: str = '{"path": "README.md"}',
    call_id: str = "call_123",
):
    return SimpleNamespace(
        id=call_id,
        function=SimpleNamespace(
            name=name,
            arguments=arguments,
        ),
    )

def test_execute_tool_call():
    llm_client = Mock()
    tool_registry = Mock()

    tool_registry.execute.return_value = "README content"

    agent = Agent(
        client=llm_client,
        registry=tool_registry,
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
        client=Mock(),
        registry=Mock(),
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
        client=Mock(),
        registry=tool_registry,
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
        client=llm_client,
        registry=tool_registry,
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
            client=Mock(),
            registry=Mock(),
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
        client=llm_client,
        registry=tool_registry,
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

def test_run_recovers_from_tool_execution_error():
    llm_client = Mock()
    tool_registry = Mock()

    tool_call = SimpleNamespace(
        id="call_123",
        function=SimpleNamespace(
            name="read_file",
            arguments='{"path": "missing.md"}',
        ),
    )

    responses = [
        make_response(tool_calls=[tool_call]),
        make_response(content="The file does not exist."),
    ]

    messages_snapshots = []

    def mock_chat_with_tools(*, messages, tools):
        messages_snapshots.append(deepcopy(messages))
        return responses[len(messages_snapshots) - 1]

    llm_client.chat_with_tools.side_effect = mock_chat_with_tools

    tool_registry.execute.side_effect = FileNotFoundError(
        "Target file does not exist"
    )

    agent = Agent(
        client=llm_client,
        registry=tool_registry,
    )

    result = agent.run("Read missing.md")

    assert result == "The file does not exist."

    assert llm_client.chat_with_tools.call_count == 2
    assert tool_registry.execute.call_count == 1

    second_messages = messages_snapshots[1]

    assert second_messages[-1] == {
        "role": "tool",
        "tool_call_id": "call_123",
        "content": (
            "Tool execution failed: "
            "FileNotFoundError: Target file does not exist"
        ),
    }

    def test_run_recovers_from_value_error():
        llm_client = Mock()
        tool_registry = Mock()

        tool_call = SimpleNamespace(
            id="call_123",
            function=SimpleNamespace(
                name="read_file",
                arguments='{"path": "README.md"}',
            ),
        )

        llm_client.chat_with_tools.side_effect = [
            make_response(tool_calls=[tool_call]),
            make_response(content="I corrected the request."),
        ]

        tool_registry.execute.side_effect = ValueError(
            "Invalid file encoding"
        )

        agent = Agent(llm_client, tool_registry)

        result = agent.run("Read README.md")

        assert result == "I corrected the request."
        assert llm_client.chat_with_tools.call_count == 2

    def test_run_propagates_unexpected_tool_error():
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

        tool_registry.execute.side_effect = RuntimeError(
            "Unexpected internal failure"
        )

        agent = Agent(llm_client, tool_registry)

        with pytest.raises(
                RuntimeError,
                match="Unexpected internal failure",
        ):
            agent.run("Read README.md")

        assert llm_client.chat_with_tools.call_count == 1

def test_run_blocks_repeated_failed_tool_calls():
    llm_client = Mock()
    tool_registry = Mock()

    def make_read_call(call_id):
        return SimpleNamespace(
            id=call_id,
            function=SimpleNamespace(
                name="read_file",
                arguments='{"path": "missing.md"}',
            ),
        )

    responses = [
        make_response(tool_calls=[make_read_call("call_001")]),
        make_response(tool_calls=[make_read_call("call_002")]),
        make_response(tool_calls=[make_read_call("call_003")]),
        make_response(content="I cannot find the requested file."),
    ]

    messages_snapshots = []

    def mock_chat_with_tools(*, messages, tools):
        messages_snapshots.append(deepcopy(messages))
        return responses[len(messages_snapshots) - 1]

    llm_client.chat_with_tools.side_effect = mock_chat_with_tools

    tool_registry.execute.side_effect = FileNotFoundError(
        "Target file does not exist"
    )

    agent = Agent(
        client=llm_client,
        registry=tool_registry,
        max_iterations=5,
        max_tool_failures=2,
    )

    result = agent.run("Read missing.md")

    assert result == "I cannot find the requested file."

    # 前两次真正执行，第三次被 Guard 拦截
    assert tool_registry.execute.call_count == 2

    # 三轮工具调用，第四轮模型生成最终回答
    assert llm_client.chat_with_tools.call_count == 4

    third_messages = messages_snapshots[3]

    assert "blocked" in third_messages[-1]["content"].lower()
    assert third_messages[-1]["tool_call_id"] == "call_003"



def test_agent_creates_executor_by_default():
    agent = Agent(
        client=Mock(),
        registry=Mock(),
    )

    assert isinstance(agent.executor, ToolExecutor)
    assert agent._owns_executor is True

    agent.executor.shutdown()

def test_agent_accepts_external_executor():
    executor = ToolExecutor()

    agent = Agent(
        client=Mock(),
        registry=Mock(),
        executor=executor,
    )

    assert agent.executor is executor
    assert agent._owns_executor is False

    executor.shutdown()

def test_agent_close_owned_executor():
    agent = Agent(
        client=Mock(),
        registry=Mock(),
    )

    executor = agent.executor

    agent.close()

    assert executor._shutdown is True

def test_agent_close_external_executor():
    executor = ToolExecutor()

    agent = Agent(
        client=Mock(),
        registry=Mock(),
        executor=executor,
    )

    agent.close()

    assert executor._shutdown is False

    executor.shutdown()

def test_agent_context_manager():
    with Agent(
        client=Mock(),
        registry=Mock(),
    ) as agent:
        executor = agent.executor
        assert executor._shutdown is False

    assert executor._shutdown is True

def test_execute_tool_call_uses_executor():
    # 1. Mock ToolExecutor
    executor = Mock(spec=ToolExecutor)
    executor.execute.return_value = "file content"

    # 2. Mock ToolRegistry
    registry = Mock()
    registry.execute.return_value = "file content"

    # 3. 创建 Agent
    agent = Agent(
        client=Mock(),
        registry=registry,
        executor=executor,
    )

    # 4. 模拟 OpenAI Tool Call
    tool_call = SimpleNamespace(
        id="call_123",
        function=SimpleNamespace(
            name="read_file",
            arguments=json.dumps({
                "path": "README.md",
            }),
        ),
    )

    # 5. 执行工具调用
    result = agent.execute_tool_call(tool_call)

    # 6. 验证 Executor 被调用
    executor.execute.assert_called_once_with(
        registry.execute,
        "read_file",
        {"path": "README.md"},
    )

    # 7. 验证 Registry 没有被直接调用
    registry.execute.assert_not_called()

    # 8. 验证 Tool Message
    assert result["role"] == "tool"
    assert result["tool_call_id"] == "call_123"
    assert result["content"] == "file content"

def test_agent_handles_tool_capacity_error():
    executor = Mock(spec=ToolExecutor)
    executor.execute.side_effect = ToolCapacityError(
        "Tool executor capacity is full"
    )

    registry = Mock()
    registry.to_openai_tools.return_value = []

    client = Mock()

    tool_call = SimpleNamespace(
        id="call_123",
        function=SimpleNamespace(
            name="read_file",
            arguments=json.dumps({"path": "README.md"}),
        ),
    )

    tool_response = SimpleNamespace(
        model_dump=lambda exclude_none=True: {
            "role": "assistant",
            "tool_calls": [],
        },
        tool_calls=[tool_call],
        content=None,
    )

    final_response = SimpleNamespace(
        model_dump=lambda exclude_none=True: {
            "role": "assistant",
            "content": "The tool executor is currently busy.",
        },
        tool_calls=[],
        content="The tool executor is currently busy.",
    )

    client.chat_with_tools.side_effect = [
        tool_response,
        final_response,
    ]

    agent = Agent(
        client=client,
        registry=registry,
        executor=executor,
    )

    result = agent.run("Read README.md")

    assert result == "The tool executor is currently busy."

    executor.execute.assert_called_once()

    # 模型收到工具执行失败的反馈
    second_messages = client.chat_with_tools.call_args_list[1].kwargs["messages"]

    tool_message = [
        message
        for message in second_messages
        if message["role"] == "tool"
    ][0]

    assert "ToolCapacityError" in tool_message["content"]
    assert "capacity is full" in tool_message["content"]

def test_agent_blocks_repeated_failed_tool_call():
    executor = Mock(spec=ToolExecutor)
    executor.execute.side_effect = ToolCapacityError(
        "Tool executor capacity is full"
    )

    registry = Mock()
    registry.to_openai_tools.return_value = []

    client = Mock()

    def make_tool_call(call_id):
        return SimpleNamespace(
            id=call_id,
            function=SimpleNamespace(
                name="read_file",
                arguments=json.dumps({"path": "README.md"}),
            ),
        )

    first_call = make_tool_call("call_1")
    second_call = make_tool_call("call_2")

    def make_response(tool_calls):
        return SimpleNamespace(
            model_dump=lambda exclude_none=True: {
                "role": "assistant",
                "content": None,
            },
            tool_calls=tool_calls,
            content=None,
        )

    final_response = SimpleNamespace(
        model_dump=lambda exclude_none=True: {
            "role": "assistant",
            "content": "I cannot read the file right now.",
        },
        tool_calls=[],
        content="I cannot read the file right now.",
    )

    client.chat_with_tools.side_effect = [
        make_response([first_call]),
        make_response([second_call]),
        final_response,
    ]

    agent = Agent(
        client=client,
        registry=registry,
        executor=executor,
        max_tool_failures=1,
    )

    result = agent.run("Read README.md")

    assert result == "I cannot read the file right now."

    # 第一次执行失败，第二次被 Guard 拦截
    executor.execute.assert_called_once()

    # 检查第二轮模型上下文中的拦截消息
    second_messages = (
        client.chat_with_tools.call_args_list[1].kwargs["messages"]
    )

    blocked_message = [
        message
        for message in second_messages
        if message["role"] == "tool"
    ][0]


    assert "ToolCapacityError" in blocked_message["content"]