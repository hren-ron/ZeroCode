
from unittest.mock import MagicMock, patch

import httpx
import pytest

from zerocode.llm.client import LLMClient


def test_init_uses_configured_model_and_base_url():
    """The client should use the configured model and API endpoint."""
    model = "qwen2.5-coder:14b"
    base_url = "http://localhost:11434/v1"

    with patch("zerocode.llm.client.OpenAI") as mock_openai:
        llm = LLMClient(model=model, base_url=base_url)

    assert llm.model == model
    mock_openai.assert_called_once()

    kwargs = mock_openai.call_args.kwargs

    assert kwargs["base_url"] == "http://localhost:11434/v1"
    assert kwargs["api_key"] == "ollama"
    assert isinstance(kwargs["http_client"], httpx.Client)


@patch("zerocode.llm.client.OpenAI")
def test_chat_returns_model_response(mock_openai):
    """The client should return the model's response content."""
    mock_client = MagicMock()
    mock_openai.return_value = mock_client

    mock_client.chat.completions.create.return_value.choices = [
        MagicMock(message=MagicMock(content="Hello from the model"))
    ]

    llm = LLMClient()
    answer = llm.chat("Hello")

    assert answer == "Hello from the model"

    mock_client.chat.completions.create.assert_called_once_with(
        model="qwen2.5-coder:14b",
        messages=[
            {
                "role": "user",
                "content": "Hello",
            }
        ],
        stream=False,
    )


@patch("zerocode.llm.client.OpenAI")
def test_chat_returns_empty_string_when_content_is_none(mock_openai):
    """The client should return an empty string for a None response."""
    mock_client = MagicMock()
    mock_openai.return_value = mock_client

    mock_client.chat.completions.create.return_value.choices = [
        MagicMock(message=MagicMock(content=None))
    ]

    llm = LLMClient()

    assert llm.chat("Hello") == ""


@patch("zerocode.llm.client.logger")
@patch("zerocode.llm.client.OpenAI")
def test_chat_logs_exception_and_reraises_error(
    mock_openai,
    mock_logger,
):
    """The client should log request failures and re-raise the exception."""
    mock_client = MagicMock()
    mock_openai.return_value = mock_client

    error = ConnectionError("Ollama service connection failed")
    mock_client.chat.completions.create.side_effect = error

    llm = LLMClient()

    with pytest.raises(
        ConnectionError,
        match="Ollama service connection failed",
    ) as exc_info:
        llm.chat("Hello")

    assert exc_info.value is error

    mock_logger.exception.assert_called_once_with(
        "Model request failed, model=%s",
        "qwen2.5-coder:14b",
    )


def test_chat_with_tools_returns_tool_calls() -> None:
    mock_client = MagicMock()

    tool_call = MagicMock()
    tool_call.id = "call_123"

    message = MagicMock()
    message.content = None
    message.tool_calls = [tool_call]

    mock_client.chat.completions.create.return_value.choices = [
        MagicMock(message=message)
    ]

    client = LLMClient()
    client.client = mock_client

    messages = [
        {"role": "user", "content": "Read README.md"}
    ]

    tools = [
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Read a file",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"}
                    },
                    "required": ["path"],
                },
            },
        }
    ]

    result = client.chat_with_tools(messages, tools)

    assert result is message
    assert result.tool_calls[0].id == "call_123"

    mock_client.chat.completions.create.assert_called_once()

    kwargs = mock_client.chat.completions.create.call_args.kwargs

    assert kwargs["tools"] == tools
    assert kwargs["tool_choice"] == "auto"
    assert kwargs["stream"] is False


def test_chat_with_tools_without_tools() -> None:
    mock_client = MagicMock()

    message = MagicMock()
    message.content = "Hello"
    message.tool_calls = None

    mock_client.chat.completions.create.return_value.choices = [
        MagicMock(message=message)
    ]

    client = LLMClient()
    client.client = mock_client

    messages = [
        {"role": "user", "content": "Hello"}
    ]

    result = client.chat_with_tools(messages)

    assert result is message

    kwargs = mock_client.chat.completions.create.call_args.kwargs

    assert "tools" not in kwargs
    assert "tool_choice" not in kwargs