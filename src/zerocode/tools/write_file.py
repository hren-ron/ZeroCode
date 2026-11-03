import logging

from zerocode.workspace import Workspace

logger = logging.getLogger(__name__)

class WriteFileTool:
    """Write text content to a file inside the workspace."""

    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace

    def execute(self, path: str, content: str) -> str:
        """Create or overwrite a workspace file."""

        if not isinstance(path, str) or not path.strip():
            raise ValueError("File path must not be empty")

        if not isinstance(content, str):
            raise TypeError("File content must be a string")

        # 1. Resolve and validate the target path.
        target_path = self.workspace.resolve_path(path)

        # 2. Create parent directories if necessary.
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # 3. Create or overwrite the file.
        try:
            target_path.write_text(
                content,
                encoding="utf-8"
            )
        except OSError:
            logger.exception(
                "Failed to write file, path=%s",
                path,
            )
            raise

        return f"Successfully wrote file: {path}"
