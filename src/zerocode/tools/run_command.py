import logging
import subprocess

from zerocode.workspace import Workspace

logger = logging.getLogger(__name__)

class RunCommandTool:
    """Execute a command inside the workspace."""

    def __init__(
        self,
        workspace: Workspace,
        timeout: float = 30.0,
    ) -> None:
        if timeout <= 0:
            raise ValueError("Timeout must be greater than zero")

        self.workspace = workspace

        self.timeout = timeout

    def execute(self, command: list[str]) -> str:
        """Execute a command and return its output."""

        # 1. Validate command arguments.
        if not isinstance(command, list) or not command:
            raise ValueError("Command must be a non-empty list")

        if not all(
            isinstance(arg, str) and arg.strip()
            for arg in command
        ):
            raise ValueError("Command arguments must be non-empty strings")

        # 2. Execute the command in the workspace root.

        try:
            result = subprocess.run(
                command,
                cwd=self.workspace.root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout,
                shell=False,
                check=False,
            )
        except subprocess.TimeoutExpired:

            logger.warning(
                "Command execution timed out, command=%s",
                command[0],
            )

            return (
                f"Command: {' '.join(command)}\n"
                f"Exit code: 124\n"
                f"Error: Command timed out after {self.timeout} seconds."
            )

        except OSError:
            logger.exception(
                "Failed to execute command, command=%s",
                command[0],
            )
            raise

        # 3. Format execution result.
        stdout = result.stdout or "{empty}"
        stderr = result.stderr or "{empty}"

        return (
            f"Command: {' '.join(command)}\n"
            f"Exit code: {result.returncode}\n\n"
            f"STDOUT:\n{stdout}\n\n"
            f"STDERR:\n{stderr}"
        )



