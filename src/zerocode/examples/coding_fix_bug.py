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
    You are working on an existing Python project.

    Your task is to find and fix an existing bug.

    Target files:
    - examples/buggy_calculator.py
    - tests/test_buggy_calculator.py

    Requirements:

    1. Read both the implementation and its tests.
    2. Run the tests using:
       python -m pytest tests/test_buggy_calculator.py -q
    3. Inspect the test failure output carefully.
    4. Identify the root cause of the failure.
    5. Fix the bug in the implementation.
    6. Do not modify the test file to make tests pass.
    7. Run the same test command again after modifying the code.
    8. If tests still fail, analyze the new output and continue fixing.
    9. Stop only after all target tests pass.

    Constraints:
    - Do not modify unrelated files.
    - Use read_file to inspect source code.
    - Use write_file to modify the implementation.
    - Use run_command to execute tests.
    - Do not claim success without observing a successful test result.

    At the end, summarize:
    - The root cause.
    - The code changes.
    - The test execution results.
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