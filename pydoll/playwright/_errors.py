"""Error types matching ``playwright.async_api`` and the mapping from pydoll's."""

from __future__ import annotations

from pydoll.exceptions import (
    CommandExecutionTimeout,
    CommandFailed,
    ConnectionException,
    DownloadTimeout,
    ElementNotFound,
    NavigationError,
    PageLoadTimeout,
    PydollException,
    ScriptException,
    WaitElementTimeout,
)


class Error(Exception):
    """Base error raised by the Playwright-compatible layer."""

    def __init__(self, message: str) -> None:
        self._message = message
        self._name: str | None = None
        self._stack: str | None = None
        super().__init__(message)

    @property
    def message(self) -> str:
        return self._message

    @property
    def name(self) -> str | None:
        return self._name

    @property
    def stack(self) -> str | None:
        return self._stack


class TimeoutError(Error):  # noqa: A001
    """Raised when an action or a wait exceeds its timeout."""


class TargetClosedError(Error):
    """Raised when the page, context or browser was closed."""

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or 'Target page, context or browser has been closed')


def is_target_closed_error(error: Exception) -> bool:
    return isinstance(error, TargetClosedError)


def translate(error: BaseException) -> BaseException:
    """Map a pydoll exception to its Playwright-compatible counterpart."""
    if isinstance(error, (Error, TimeoutError, TargetClosedError)):
        return error
    if isinstance(
        error, (PageLoadTimeout, WaitElementTimeout, DownloadTimeout, CommandExecutionTimeout)
    ):
        return TimeoutError(str(error))
    if isinstance(error, ConnectionException):
        return TargetClosedError(str(error))
    if isinstance(error, CommandFailed):
        if _mentions_closed_target(error):
            return TargetClosedError(str(error))
        return Error(str(error))
    if isinstance(error, (NavigationError, ScriptException, ElementNotFound, PydollException)):
        return Error(str(error))
    return error


def _mentions_closed_target(error: CommandFailed) -> bool:
    text = str(error).lower()
    return (
        'target closed' in text
        or 'session with given id not found' in text
        or 'no such target' in text
    )
