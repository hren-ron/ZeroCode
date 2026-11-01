import json
import logging
from typing import Any

from click import argument

from zerocode.llm.client import LLMClient
from zerocode.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)

class Agent:

    def __init__(
        self,
        llm_client: LLMClient,
        tool_registry: ToolRegistry,
    ) -> None:
        self.llm_client = llm_client
        self.tool_registry = tool_registry


    def execute_tool_call(self, tool_call: Any) -> dict[str, str]:

        tool_call_id = tool_call.id
        function = tool_call.function

        tool_name = function.name
        arguments = json.loads(function.arguments)

        if not isinstance(arguments, dict):
            raise ValueError("Tool arguments must be a JSON object")

        logger.info(
            "Executing tool call, tool=%s, call_id=%s",
            tool_name,
            tool_call_id,
        )

        result = self.tool_registry.execute(tool_name, arguments)

        return {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": str(result)
        }


    def run(self, user_input: str) -> str:

        messages = [
            {
                "role": "system",
                "content": "You are a helpful coding assistant. "
                           "Use available tools when necessary.",
            },
            {
                "role": "user",
                "content": user_input,
            },
        ]

        tools = self.tool_registry.to_openai_tools()

        while True:
            response = self.llm_client.chat_with_tools(
                messages=messages,
                tools=tools
            )

            # 将模型返回的消息加入上下文
            messages.append(response.model_dump(exclude_none=True))

            # 如果没有工具调用，说明模型已经生成最终回答
            if not response.tool_calls:
                return response.content or ""

            # 执行模型请求的工具
            for tool_call in response.tool_calls:
                tool_result = self.execute_tool_call(tool_call)
                messages.append(tool_result)

