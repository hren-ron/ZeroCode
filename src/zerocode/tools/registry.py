import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from zerocode.tools.schema import ToolSchema

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    handler: Callable[..., Any]
    schema: ToolSchema


class ToolRegistry:

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(
        self,
        name: str,
        description: str,
        handler: Callable[..., Any],
        schema: ToolSchema,
    ) -> None:

        if not name.strip():
            raise ValueError("Tool name must not be empty")

        if name in self._tools:
            raise ValueError(f"Tool already registered: {name}")

        if not isinstance(schema, ToolSchema):
            raise TypeError("schema must be a ToolSchema instance")

        self._tools[name] = Tool(
            name=name,
            description=description,
            handler=handler,
            schema=schema,
        )

        logger.info("Tool registered, name=%s", name)

    def get(self, name: str) -> Tool:
        try:
            return self._tools[name]
        except KeyError:
            logger.warning("Tool not found, name=%s", name)
            raise KeyError(f"Tool not found: {name}") from None

    def list_tools(self) -> list[Tool]:
        return list(self._tools.values())

    def execute(self, name: str, arguments: dict[str, Any]) -> Any:

        logger.info(
            "Starting tool execution, name=%s",
            name,
        )

        tool = self.get(name)

        if not isinstance(arguments, dict):
            logger.warning(
                "Invalid tool arguments, name=%s, type=%s",
                name,
                type(arguments).__name__,
            )

            raise TypeError("Tool arguments must be a dictionary")

        try:
            # 验证参数是否符合 Schema。
            tool.schema.validate(arguments)

            # 校验通过后，才执行 handler。
            result = tool.handler(**arguments)

            logger.info(
                "Tool execution completed, name=%s",
                name,
            )

            return result

        except Exception:
            logger.exception(
                "Tool execution failed, name=%s",
                name,
            )
            raise




