import json
from pathlib import Path

from zerocode.agent import Agent
from zerocode.llm.client import LLMClient
from zerocode.logging.config import configure_logging
from zerocode.tools.builtin import register_builtin_tools
from zerocode.tools.registry import ToolRegistry
from zerocode.workspace import Workspace


def main():

    configure_logging()

    project_root = Path(__file__).resolve().parents[3]
    workspace = Workspace(project_root)

    registry = ToolRegistry()

    register_builtin_tools(workspace=workspace, registry=registry)

    client = LLMClient(
        model="qwen3.6:35b-a3b",
        base_url="http://localhost:11434/v1",
        api_key="ollama",
    )

    task = """
        Analyze the execution flow of Agent.run() in this project.

        Please inspect the actual source code and explain:

        1. How are the initial messages constructed?
        2. How does Agent call the LLM?
        3. How does Agent handle tool_calls?
        4. How are tool results returned to the LLM?
        5. Under what conditions does Agent terminate?
        6. How are tool execution failures handled?

        Do not guess. Base your explanation on the actual source code.
        """

    with Agent(
        client=client,
        registry=registry,
        max_iterations=10,
    ) as agent:
        result = agent.run(task)

    print("\n========== Analysis Result ==========\n")
    print(result)


if __name__ == "__main__":
    main()