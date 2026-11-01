import logging
from concurrent.futures import (
    ThreadPoolExecutor,
    TimeoutError as FutureTimeoutError,
)
from threading import BoundedSemaphore, Lock
from typing import Any, Callable

logger = logging.getLogger(__name__)

class ToolTimeoutError(TimeoutError):
    """Raised when tool execution exceeds the configured timeout."""

class ToolCapacityError(RuntimeError):
    """Raised when the tool executor has no available capacity."""

class ToolExecutor:
    def __init__(
        self,
        max_workers: int = 4,
        max_queue_size: int = 8,
        timeout: float = 10.0,
    ) -> None:

        if max_workers <= 0:
            raise ValueError("max_workers must be greater than zero")

        if max_queue_size < 0:
            raise ValueError("max_queue_size must not be negative")

        if timeout <= 0:
            raise ValueError("timeout must be greater than zero")

        self.timeout = timeout

        # 增加关闭状态, 让 shutdown() 可以安全地重复调用
        self._shutdown = False

        # 因为可能有多个线程同时调用 shutdown()。如果没有锁，多个线程可能同时判断执行器尚未关闭，
        # 然后重复执行关闭操作。
        self._shutdown_lock = Lock()

        self._executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="zerocode-tool",
        )

        self._capacity = BoundedSemaphore(max_workers + max_queue_size)

    def execute(
        self,
        func: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:

        with self._shutdown_lock:

            self._ensure_not_shutdown()

            # 非阻塞申请容量，避免无限等待
            if not self._capacity.acquire(blocking=False):
                logger.warning("Tool executor capacity is full")
                raise ToolCapacityError(
                    "Tool executor capacity is full"
                )

            try:
                future = self._executor.submit(func, *args, **kwargs)

                # Future 真正完成后释放容量
                future.add_done_callback(lambda _: self._capacity.release())

            except BaseException:

                # 提交失败时归还已经申请的容量
                self._capacity.release()
                raise

        logger.info("Submitting tool execution")

        try:
            result = future.result(timeout=self.timeout)

            logger.info("Tool execution completed")
            return result

        except FutureTimeoutError:

            if future.done():
                raise

            future.cancel()

            logger.warning(
                "Tool execution timed out, timeout=%s",
                self.timeout,
            )

            raise ToolTimeoutError(
                f"Tool execution exceeded {self.timeout} seconds"
            ) from None

    def shutdown(self):

        with self._shutdown_lock:

            if self._shutdown:
                logger.debug("Tool executor is already shut down")
                return

            self._shutdown = True

            self._executor.shutdown(wait=False, cancel_futures=True)

            logger.info("Tool executor shut down")

    def __enter__(self)  -> "ToolExecutor":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.shutdown()

    def _ensure_not_shutdown(self) -> None:
        if self._shutdown:
            raise RuntimeError("Tool executor has been shut down")