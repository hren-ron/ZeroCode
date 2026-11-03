import logging
from typing import Any

import httpx
from openai import OpenAI


logger = logging.getLogger(__name__)

class LLMClient:


    def __init__(
        self,
        model: str="qwen2.5-coder:14b",
        base_url: str="http://localhost:11434/v1",
        api_key: str="ollama",
    ):

        self.model = model

        http_client = httpx.Client(
            trust_env=False,
            timeout=httpx.Timeout(180.0),
        )

        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key,
            http_client=http_client,
        )

    def chat(self, user_input: str):


        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{
                    "role": "user",
                    "content": user_input,
                }],
                stream=False,
            )

            content = response.choices[0].message.content

            return content or ""

        except Exception:
            logger.exception("Model request failed, model=%s", self.model)
            raise


    def chat_with_tools(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None=None) -> Any:

        logger.info("Starting model request with tools, model=%s",self.model)

        try:
            request_params: dict[str, Any] = {
                "model": self.model,
                "messages": messages,
                "stream": False,
            }

            if tools:
                request_params["tools"] = tools
                request_params["tool_choice"] = "auto"

            response = self.client.chat.completions.create(**request_params)

            message = response.choices[0].message

            logger.info("Model request completed, model=%s, tool_calls=%s",self.model, len(message.tool_calls or []))

            return message

        except Exception:

            logger.exception("Model request with tools failed, model=%s",self.model)

            raise
