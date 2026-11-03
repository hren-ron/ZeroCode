import logging

from zerocode.workspace import Workspace

logger = logging.getLogger(__name__)

class SearchCodeTool:
    """Search source code by keyword inside the workspace."""
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
        query: str,
        path: str=".",
        file_pattern: str = "*",
        case_sensitive: bool = False,
        max_results: int = 10,
    ):
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query must be a non-empty string")

        if not isinstance(path, str) or not path.strip():
            raise ValueError("path must be a non-empty string")

        if not isinstance(file_pattern, str) or not file_pattern.strip():
            raise ValueError("file_pattern must be a non-empty string")

        if not isinstance(case_sensitive, bool):
            raise ValueError("case_sensitive must be a boolean")

        if (
            not isinstance(max_results, int)
            or isinstance(max_results, bool)
            or max_results <= 0
        ):
            raise ValueError("max_results must be a positive integer")

        search_root = self.workspace.resolve_path(path)

        if not search_root.exists():
            raise FileNotFoundError(f"Directory not found: {path}")

        if not search_root.is_dir():
            raise NotADirectoryError(f"Not a directory: {path}")

        logger.info("Searching code, path=%s, query=%s", path, query)


        results: list[str] = []

        search_query = query if case_sensitive else query.casefold()

        for file_path in search_root.rglob(file_pattern):
            relative_path = file_path.relative_to(self.workspace.root)

            if any(part in self.DEFAULT_IGNORES for part in relative_path.parts):
                continue

            if file_path.is_symlink() or not file_path.is_file():
                continue

            try:
                with file_path.open("r", encoding="utf-8") as file:
                    for line_number, line in enumerate(file, start=1):

                        content = line.rstrip("\r\n")

                        searchable_content = content if case_sensitive else content.casefold()

                        if search_query in searchable_content:
                            results.append(
                                f"{relative_path.as_posix()}:{line_number}: {content}"
                            )

                            if len(results) >= max_results:
                                logger.info(
                                    "Search reached maximum results, count=%s",
                                    max_results,
                                )
                                return results
            except UnicodeDecodeError:
                logger.debug("Skipping non-UTF-8 file: %s", relative_path)
                continue
            except OSError:
                logger.warning("Failed to read file: %s", relative_path)
                continue

        logger.info("Code search completed, count=%s", len(results))
        return results







