

from zerocode.tools.guard import ToolCallGuard


def test_fingerprint_is_deterministic():
    guard = ToolCallGuard()

    first = guard.fingerprint(
        "read_file",
        '{"path": "README.md", "encoding": "utf-8"}',
    )

    second = guard.fingerprint(
        "read_file",
        '{"encoding": "utf-8", "path": "README.md"}',
    )

    assert first == second

def test_fingerprint_differs_for_different_arguments():
    guard = ToolCallGuard()

    first = guard.fingerprint(
        "read_file",
        '{"path": "README.md"}',
    )

    second = guard.fingerprint(
        "read_file",
        '{"path": "missing.md"}',
    )

    assert first != second

def test_guard_blocks_after_max_failures():
    guard = ToolCallGuard(max_failures=2)

    fingerprint = guard.fingerprint(
        "read_file",
        '{"path": "missing.md"}',
    )

    assert not guard.is_blocked(fingerprint)

    guard.record_failure(fingerprint)

    assert not guard.is_blocked(fingerprint)

    guard.record_failure(fingerprint)

    assert guard.is_blocked(fingerprint)

def test_record_success_resets_failure_count():
    guard = ToolCallGuard(max_failures=2)

    fingerprint = guard.fingerprint(
        "read_file",
        '{"path": "README.md"}',
    )

    guard.record_failure(fingerprint)
    guard.record_success(fingerprint)

    assert not guard.is_blocked(fingerprint)

import pytest


@pytest.mark.parametrize("max_failures", [0, -1])
def test_guard_rejects_invalid_max_failures(max_failures):
    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        ToolCallGuard(max_failures=max_failures)