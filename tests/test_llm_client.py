
from unittest.mock import MagicMock, patch

import pytest

from zerocode.llm.client import LLMClient


def test_init_uses_configured_model_and_base_url():
    """The client should use the configured model and API endpoint."""
    model = "qwen2.5-coder:14b"
    base_url = "http://localhost:11434/v1"

    with patch("zerocode.llm.client.OpenAI") as mock_openai:
        llm = LLMClient(model=model, base_url=base_url)

    assert llm.model == model
    mock_openai.assert_called_once_with(
        base_url=base_url,
        api_key="ollama",
    )


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
