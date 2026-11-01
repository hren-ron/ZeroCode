import json
import logging
from typing import Any

from zerocode.llm.client import LLMClient
from zerocode.tools.executor import ToolExecutor, ToolCapacityError
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
    ToolCapacityError,
)

class Agent:

    def __init__(
        self,
        client: LLMClient,
        registry: ToolRegistry,
        max_iterations: int = 10,
        max_tool_failures: int = 2,
        executor: ToolExecutor | None=None,
    ) -> None:

        if max_iterations <= 0:
            raise ValueError(
                "max_iterations must be greater than zero"
            )

        if max_tool_failures <= 0:
            raise ValueError(
                "max_tool_failures must be greater than zero"
            )

        self.client = client
        self.registry = registry
        self.max_iterations = max_iterations
        self.max_tool_failures = max_tool_failures

        # 标记 Agent 是否拥有执行器
        self._owns_executor = executor is None

        # 实际执行工具的执行器
        self.executor = executor or ToolExecutor()


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

        result = self.executor.execute(
            self.registry.execute,
            tool_name,
            arguments,
        )

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

        tools = self.registry.to_openai_tools()

        guard = ToolCallGuard(max_failures=self.max_tool_failures)

        for iteration in range(self.max_iterations):
            response = self.client.chat_with_tools(
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

                        guard.record_success(fingerprint)

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

    def close(self) -> None:

        if not self._owns_executor:
            return
        self.executor.shutdown()

    def __enter__(self) -> "Agent":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()


