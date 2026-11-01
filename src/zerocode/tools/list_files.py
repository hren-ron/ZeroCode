import logging

from zerocode.workspace import Workspace

logger = logging.getLogger(__name__)

class ListFilesTool:
    """List files and directories inside the workspace."""

    DEFAULT_IGNORES = {
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "node_modules",
        ".idea",
        ".vscode",
    }

    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace

    def execute(
        self,
        path: str = ".",
        recursive: bool = True,
        max_entries: int = 100,
    ) -> list[str]:

        if not isinstance(path, str) or not path.strip():
            raise ValueError("path must be a non-empty string")

        if not isinstance(recursive, bool):
            raise ValueError("recursive must be a boolean")

        if (
            not isinstance(max_entries, int)
            or isinstance(max_entries, bool)
            or max_entries <= 0
        ):
            raise ValueError("max_entries must be a positive integer")

        root = self.workspace.resolve_path(path)

        if not root.exists():
            raise FileNotFoundError(f"Directory not found: {path}")

        if not root.is_dir():
            raise NotADirectoryError(f"Not a directory: {path}")

        logger.info(
            "Listing workspace files, path=%s, recursive=%s",
            path,
            recursive,
        )

        results: list[str] = []

        if recursive:
            candidates = root.rglob("*")
        else:
            candidates = root.iterdir()

        for candidate in candidates:

            relative_path = candidate.relative_to(self.workspace.root)

            # Exclude ignored directories at any depth.
            if any(
                part in self.DEFAULT_IGNORES
                for part in relative_path.parts
            ):
                continue

            # Do not follow directory symlinks outside the workspace.
            if candidate.is_symlink():
                try:
                    candidate.resolve(strict=True).relative_to(self.workspace.root)
                except (ValueError, OSError):
                    continue

            results.append(relative_path.as_posix())

            if len(results) >= max_entries:
                logger.info(
                    "File listing reached maximum entries, count=%s",
                    max_entries,
                )
                break

        logger.info(
            "File listing completed, count=%s",
            len(results),
        )

        return sorted(results)












