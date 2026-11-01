import hashlib
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

class ToolCallGuard:

    def __init__(self, max_failures: int = 2):
        if max_failures <= 0:
            raise ValueError("max_failures must be greater than zero")

        self.max_failures = max_failures
        self._failures: dict[str, int] = {}

    @staticmethod
    def fingerprint(tool_name: str, arguments: Any):

        try:
            parsed_arguments = json.loads(arguments)

            normalized_arguments = json.dumps(
                parsed_arguments,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            )

        except (TypeError, json.JSONDecodeError):
            normalized_arguments = str(arguments)

        raw = f"{tool_name}:{normalized_arguments}"

        return hashlib.sha256(
            raw.encode("utf-8")
        ).hexdigest()

    def is_blocked(self, fingerprint: str) -> bool:
        return (
            self._failures.get(fingerprint, 0) >= self.max_failures
        )

    def record_failure(self, fingerprint: str) -> None:
        self._failures[fingerprint] = self._failures.get(fingerprint, 0) + 1

        logger.warning(
            "Tool failure recorded, fingerprint=%s, failures=%s",
            fingerprint[:12],
            self._failures[fingerprint],
        )

    def record_success(self, fingerprint: str) -> None:
        self._failures.pop(fingerprint, None)
