import logging

from zerocode.workspace import Workspace

logger = logging.getLogger(__name__)

class ReadFileTool:
    """Read a text file within the configured workspace."""

    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace

    def execute(
            self,
            path: str,
            encoding: str = "utf-8",
    ) -> str:

        logger.info("Starting file read")

        file_path = self.workspace.resolve_path(path)
        if not file_path.is_file():
            logger.warning("File read failed: target is not a file")
            raise FileNotFoundError("Target file does not exist")

        try:
            content = file_path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            logger.warning("File read failed: decoding error")
            raise ValueError(
                f"Unable to decode file using encoding: {encoding}"
            ) from None
        except OSError:
            logger.exception("File read failed due to an OS error")
            raise

        logger.info("File read completed")
        return content