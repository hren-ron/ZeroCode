from zerocode.tools.executor import ToolExecutor, ToolTimeoutError

import time
import pytest

def test_execute_returns_result():
    executor = ToolExecutor(timeout=2)

    try:
        result = executor.execute(
            lambda x: x * 2,
            x=10,
        )

        assert result == 20
    finally:
        executor.shutdown()



def test_execute_timeout():
    executor = ToolExecutor(timeout=0.1)

    try:
        with pytest.raises(ToolTimeoutError):
            executor.execute(time.sleep, 1)
    finally:
        executor.shutdown()


import threading

import pytest

from zerocode.tools.executor import (
    ToolCapacityError,
    ToolExecutor,
)


def test_execute_rejects_when_capacity_is_full():
    executor = ToolExecutor(
        max_workers=1,
        max_queue_size=0,
        timeout=5,
    )

    started = threading.Event()
    release = threading.Event()
    finished = threading.Event()

    def blocking_task():
        started.set()
        release.wait()
        finished.set()
        return "completed"

    result = {}

    def run_task():
        try:
            result["value"] = executor.execute(blocking_task)
        except Exception as exc:
            result["error"] = exc

    thread = threading.Thread(target=run_task)
    thread.start()

    try:
        assert started.wait(timeout=2)

        with pytest.raises(ToolCapacityError):
            executor.execute(lambda: "another task")

    finally:
        release.set()
        thread.join(timeout=2)
        executor.shutdown()

    assert not thread.is_alive()
    assert result["value"] == "completed"
    assert finished.is_set()

def test_execute_allows_queued_tasks():
    executor = ToolExecutor(
        max_workers=1,
        max_queue_size=1,
        timeout=5,
    )

    started = threading.Event()
    release = threading.Event()

    results = {}

    def blocking_task():
        started.set()
        release.wait()
        return "first"

    def run_first():
        results["first"] = executor.execute(blocking_task)

    def run_second():
        results["second"] = executor.execute(
            lambda: "second"
        )

    first_thread = threading.Thread(target=run_first)
    second_thread = threading.Thread(target=run_second)

    first_thread.start()

    try:
        assert started.wait(timeout=2)

        # 第二个任务提交后会进入等待队列
        second_thread.start()

        # 等待第二个任务完成提交并进入执行器
        # 当前版本没有公开提交状态，因此这里先用短暂等待
        time.sleep(0.1)

        # 第三个任务应该因为容量已满而被拒绝
        with pytest.raises(ToolCapacityError):
            executor.execute(lambda: "third")

    finally:
        release.set()
        first_thread.join(timeout=3)
        second_thread.join(timeout=3)
        executor.shutdown()

    assert results["first"] == "first"
    assert results["second"] == "second"
    assert not first_thread.is_alive()
    assert not second_thread.is_alive()

def test_context_manager_returns_executor():
    executor = ToolExecutor()

    with executor as entered_executor:
        assert entered_executor is executor

    executor.shutdown()


def test_context_manager_shutdown_on_exit():
    executor = ToolExecutor()

    with executor as entered_executor:
        assert entered_executor.execute(lambda: "hello") == "hello"

    assert executor._executor._shutdown is True


def test_context_manager_shutdown_on_exception():
    executor = ToolExecutor()

    with pytest.raises(ValueError, match="test error"):
        with executor:
            raise ValueError("test error")

    assert executor._executor._shutdown is True

def test_shutdown_is_idempotent():
    executor = ToolExecutor()

    executor.shutdown()
    executor.shutdown()
    executor.shutdown()

    assert executor._shutdown is True

def test_execute_after_shutdown():
    executor = ToolExecutor()
    executor.shutdown()

    with pytest.raises(RuntimeError):
        executor.execute(lambda: "hello")

def test_execute_after_shutdown_has_clear_error():
    executor = ToolExecutor()
    executor.shutdown()

    with pytest.raises(
        RuntimeError,
        match="Tool executor has been shut down",
    ):
        executor.execute(lambda: "hello")

def test_shutdown_does_not_kill_running_task():
    import threading

    started = threading.Event()
    release = threading.Event()
    finished = threading.Event()

    executor = ToolExecutor(max_workers=1, timeout=5)

    def blocking_task():
        started.set()
        release.wait()
        finished.set()
        return "done"

    results = []

    def run_task():
        results.append(executor.execute(blocking_task))

    worker = threading.Thread(target=run_task)

    try:
        worker.start()
        assert started.wait(timeout=2)

        executor.shutdown()

        assert not finished.is_set()

        with pytest.raises(RuntimeError):
            executor.execute(lambda: "new task")

        release.set()
        worker.join(timeout=2)

        assert not worker.is_alive()
        assert finished.is_set()
        assert results == ["done"]
    finally:
        release.set()
        worker.join(timeout=2)
        executor.shutdown()


def test_execute_preserves_tool_timeout_error():
    executor = ToolExecutor(timeout=5)

    def task():
        raise TimeoutError("internal tool timeout")

    try:
        with pytest.raises(TimeoutError) as exc_info:
            executor.execute(task)

        assert type(exc_info.value) is TimeoutError
        assert not isinstance(
            exc_info.value,
            ToolTimeoutError,
        )
    finally:
        executor.shutdown()