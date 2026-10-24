
"""
local-code-agent: 最小 Agent 实现

功能：
1. 从项目根目录加载 .env 配置
2. 初始化 OpenAI 兼容客户端
3. 向大模型发送消息
4. 输出模型回复
5. 处理常见异常
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import (
    OpenAI,
    APIConnectionError,
    APIStatusError,
    AuthenticationError,
    RateLimitError,
)


# 项目根目录：假设文件位于 src/code_agent/agent.py
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# 加载项目根目录下的 .env
load_dotenv(PROJECT_ROOT / ".env")


class Agent:
    """最小化的 Code Agent。"""

    def __init__(self):
        self.api_key = os.getenv("BAILIAN_API_KEY")
        self.base_url = os.getenv("BAILIAN_BASE_URL")
        self.workspace_id = os.getenv("BAILIAN_WORKSPACEID")
        self.model = os.getenv("BAILIAN_MODEL_NAME")

        self._validate_config()

        # 动态替换 WorkspaceId
        self.base_url = self.base_url.replace(
            "{WorkspaceId}",
            self.workspace_id,
        )

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=60.0,
            max_retries=2,
        )

    def _validate_config(self):
        """检查必要的环境变量。"""
        missing = []

        if not self.api_key:
            missing.append("LLM_API_KEY")

        if not self.base_url:
            missing.append("LLM_BASE_URL")

        if not self.workspace_id:
            missing.append("LLM_WORKSPACE_ID")

        if not self.model:
            missing.append("LLM_MODEL_NAME")

        if missing:
            raise ValueError(
                f"缺少必要的环境变量：{', '.join(missing)}。"
                f"请检查项目根目录下的 .env 文件。"
            )

    def chat(self, user_input: str) -> str:
        """
        发送用户消息并获取模型回复。

        Args:
            user_input: 用户输入的文本。

        Returns:
            模型返回的文本。
        """
        if not user_input or not user_input.strip():
            raise ValueError("用户输入不能为空。")

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是一个专业的软件工程与 Python 编程助手。"
                        "请清晰、准确地回答问题。"
                        "涉及代码时，优先提供可运行的代码和必要的解释。"
                    ),
                },
                {
                    "role": "user",
                    "content": user_input.strip(),
                },
            ],
        )

        content = response.choices[0].message.content

        if not content:
            return "模型没有返回文本内容。"

        return content.strip()


def main():
    """命令行入口。"""
    try:
        agent = Agent()
        print(f"Code Agent 已启动，当前模型：{agent.model}")
        print("输入 exit 或 quit 退出。\n")

        while True:
            try:
                user_input = input("You > ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n再见！")
                break

            if user_input.lower() in {"exit", "quit"}:
                print("再见！")
                break

            if not user_input:
                continue

            try:
                answer = agent.chat(user_input)
                print(f"\nAgent > {answer}\n")
            except AuthenticationError:
                print("认证失败：请检查 .env 中的 LLM_API_KEY。")
            except RateLimitError:
                print("请求频率或额度受限，请检查服务商的限制。")
            except APIConnectionError:
                print("连接失败：请检查网络、代理和 LLM_BASE_URL。")
            except APIStatusError as exc:
                print(f"模型 API 返回错误：HTTP {exc.status_code}")
            except Exception as exc:
                print(f"处理请求时发生错误：{type(exc).__name__}: {exc}")

    except ValueError as exc:
        print(f"配置错误：{exc}")
        sys.exit(1)
    except Exception as exc:
        print(f"Agent 初始化失败：{type(exc).__name__}: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()