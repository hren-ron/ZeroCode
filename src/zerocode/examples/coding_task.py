
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
    Create a simple Python calculator module and its tests.

    Requirements:

    1. Create examples/calculator.py.
    2. Implement an add(a, b) function that returns a + b.
    3. Create tests/test_calculator.py.
    4. Write tests covering:
       - Positive integers.
       - Negative integers.
       - Floating-point numbers.

    Execution requirements:

    1. Inspect the project structure before modifying files.
    2. Use write_file to create the files.
    3. Use run_command to execute the relevant tests.
    4. If tests fail, analyze the error and fix the code.
    5. Run the tests again after fixing.
    6. Do not claim success unless the tests actually pass.

    Do not modify unrelated existing files.
    """

    with Agent(
        client=client,
        registry=registry,
        max_iterations=10,
    ) as agent:
        result = agent.run(task)

    print("\n========== Coding Task Result ==========\n")
    print(result)


if __name__ == "__main__":
    main()
