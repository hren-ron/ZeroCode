import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class Workspace:
    """Manage the project root and validate file paths."""

    def __init__(self, root: str | Path) -> None:

        root_path = Path(root).expanduser().resolve(strict=True)

        if not root_path.is_dir():
            raise NotADirectoryError(
                f"Workspace root is not a directory: {root_path}"
            )

        self.root = root_path
        logger.info("Workspace initialized, root=%s", self.root)

    def resolve_path(self, path: str|Path) -> Path:
        """Resolve a path and ensure it stays inside the workspace."""

        relative_or_absolute = Path(path).expanduser()

        if not relative_or_absolute.is_absolute():
            candidate = self.root / relative_or_absolute
        else:
            candidate = relative_or_absolute

        # Resolve '..' and existing symlinks before checking containment.
        resolved = candidate.resolve(strict=False)

        try:
            resolved.relative_to(self.root)
        except ValueError:
            logger.warning("Workspace path access denied")
            raise PermissionError(
                "Path is outside the workspace"
            ) from None

        logger.debug("Workspace path resolved")
        return resolved