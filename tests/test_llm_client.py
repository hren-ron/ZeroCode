
from unittest.mock import MagicMock, patch

from zerocode.llm.client import LLMClient


def test_init_uses_configured_model_and_base_url():
    """验证模型名称和 API 地址配置正确。"""
    llm = LLMClient(
        model="qwen2.5-coder:14b",
        base_url="http://localhost:11434/v1",
    )

    assert llm.model == "qwen2.5-coder:14b"
    assert llm.client.base_url == "http://localhost:11434/v1/"


@patch("zerocode.llm.client.OpenAI")
def test_chat_returns_model_response(mock_openai):
    """验证请求参数正确，并能提取模型回答。"""
    mock_client = MagicMock()
    mock_openai.return_value = mock_client

    mock_client.chat.completions.create.return_value.choices = [
        MagicMock(message=MagicMock(content="这是模型的回答"))
    ]

    llm = LLMClient()
    answer = llm.chat("你好")

    assert answer == "这是模型的回答"

    mock_client.chat.completions.create.assert_called_once_with(
        model="qwen2.5-coder:14b",
        messages=[
            {"role": "user", "content": "你好"}
        ],
        stream=False,
    )


@patch("zerocode.llm.client.OpenAI")
def test_chat_returns_empty_string_when_content_is_none(mock_openai):
    """验证模型返回空内容时的处理。"""
    mock_client = MagicMock()
    mock_openai.return_value = mock_client

    mock_client.chat.completions.create.return_value.choices = [
        MagicMock(message=MagicMock(content=None))
    ]

    llm = LLMClient()
    assert llm.chat("你好") == ""
