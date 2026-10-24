import logging

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
        self.client = OpenAI(base_url=base_url, api_key=api_key)

    def chat(self, user_input: str):

        logger.info("start llm")

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{
                "role": "user",
                "content": user_input,
            }],
            stream=False,
        )

        logger.info("start llm success")

        content = response.choices[0].message.content
        return content or ""
