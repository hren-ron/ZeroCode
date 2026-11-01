import json
import logging
from typing import Any

from zerocode.llm.client import LLMClient
from zerocode.tools.guard import ToolCallGuard
from zerocode.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)

RECOVERABLE_TOOL_ERRORS = (
    ValueError,
    TypeError,
    KeyError,
    FileNotFoundError,
    PermissionError,
    OSError,
)

class Agent:

    def __init__(
        self,
        llm_client: LLMClient,
        tool_registry: ToolRegistry,
        max_iterations: int = 10,
        max_tool_failures: int = 2,
    ) -> None:

        if max_iterations <= 0:
            raise ValueError(
                "max_iterations must be greater than zero"
            )

        if max_tool_failures <= 0:
            raise ValueError(
                "max_tool_failures must be greater than zero"
            )

        self.llm_client = llm_client
        self.tool_registry = tool_registry
        self.max_iterations = max_iterations
        self.max_tool_failures = max_tool_failures


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

        guard = ToolCallGuard(max_failures=self.max_tool_failures)

        for iteration in range(self.max_iterations):
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

                tool_name = tool_call.function.name
                fingerprint = guard.fingerprint(tool_name, tool_call.function.arguments)

                if guard.is_blocked(fingerprint):
                    logger.warning(
                        "Tool call blocked after repeated failures, tool=%s",
                        tool_name,
                    )

                    tool_result = {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": (
                            "Tool call blocked: this exact tool call "
                            "has failed too many times. "
                            "Please change the arguments or use another approach."
                        ),
                    }
                else:


                    try:
                        tool_result = self.execute_tool_call(tool_call)

                    except RECOVERABLE_TOOL_ERRORS as exc:
                        logger.exception("Tool execution failed, tool_call_id=%s",tool_call.id)

                        # 关键：记录工具执行失败
                        guard.record_failure(fingerprint)

                        tool_result = {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": (
                                f"Tool execution failed: "
                                f"{type(exc).__name__}: {exc}"
                            ),
                        }
                messages.append(tool_result)

        raise RuntimeError(
            f"Agent exceeded maximum iterations: {self.max_iterations}"
        )

