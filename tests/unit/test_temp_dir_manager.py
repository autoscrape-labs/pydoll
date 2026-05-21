"""Unit tests for TempDirectoryManager: creation, cleanup, and lock handling.

Uses the injectable temp_dir_factory seam and real directories so assertions are
on observable outcomes: what create returns, that cleanup removes directories
from disk, and whether the error handler swallows, recovers from, or re-raises.
"""

from __future__ import annotations

import os
import tempfile
from types import SimpleNamespace

import pytest

from pydoll.browser.managers import TempDirectoryManager


def test_create_temp_dir_returns_factory_output():
    created = SimpleNamespace(name='/tmp/fake-profile')
    manager = TempDirectoryManager(temp_dir_factory=lambda: created)
    assert manager.create_temp_dir() is created


def test_cleanup_removes_created_directories():
    manager = TempDirectoryManager(
        temp_dir_factory=lambda: SimpleNamespace(name=tempfile.mkdtemp())
    )
    first = manager.create_temp_dir().name
    second = manager.create_temp_dir().name
    assert os.path.isdir(first) and os.path.isdir(second)

    manager.cleanup()

    assert not os.path.exists(first)
    assert not os.path.exists(second)


def test_retry_process_file_runs_the_operation_once_on_success():
    processed = []
    TempDirectoryManager.retry_process_file(processed.append, 'path', retry_times=3)
    assert processed == ['path']


def test_retry_process_file_raises_after_exhausting_retries():
    def always_locked(_path):
        raise PermissionError()

    with pytest.raises(PermissionError):
        TempDirectoryManager.retry_process_file(always_locked, 'path', retry_times=2)


def test_handle_cleanup_error_swallows_oserror():
    manager = TempDirectoryManager()
    manager.handle_cleanup_error(lambda _p: None, '/x', (OSError, OSError('boom'), None))


def test_handle_cleanup_error_reraises_unhandled_permission_error():
    manager = TempDirectoryManager()
    error = PermissionError('locked')
    with pytest.raises(PermissionError):
        manager.handle_cleanup_error(
            lambda _p: None, '/regular/file.txt', (PermissionError, error, None)
        )


def test_handle_cleanup_error_recovers_known_chrome_lock():
    manager = TempDirectoryManager()
    processed = []
    manager.handle_cleanup_error(
        processed.append,
        '/profile/CrashpadMetrics-active.pma',
        (PermissionError, PermissionError(), None),
    )
    assert processed == ['/profile/CrashpadMetrics-active.pma']


def test_handle_cleanup_error_recovers_safe_browsing_lock():
    manager = TempDirectoryManager()
    processed = []
    manager.handle_cleanup_error(
        processed.append,
        '/profile/Safe Browsing/data',
        (PermissionError, PermissionError(), None),
    )
    assert processed == ['/profile/Safe Browsing/data']


def test_handle_cleanup_error_swallows_persistently_locked_chrome_file():
    manager = TempDirectoryManager()

    def always_locked(_path):
        raise PermissionError()

    # A known Chrome lock file that never unlocks is logged and ignored, not raised.
    manager.handle_cleanup_error(
        always_locked,
        '/profile/CrashpadMetrics-active.pma',
        (PermissionError, PermissionError(), None),
    )
