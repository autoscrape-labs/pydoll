from enum import Enum

from typing_extensions import NotRequired, TypedDict

from pydoll.protocol.bidi.script.types import RemoteValue, Source, StackTrace


class LogLevel(str, Enum):
    """Log entry severity levels."""

    DEBUG = 'debug'
    INFO = 'info'
    WARN = 'warn'
    ERROR = 'error'


class ConsoleLogEntry(TypedDict):
    """Log entry from console API calls."""

    level: LogLevel
    source: Source
    text: str | None
    timestamp: int
    stackTrace: NotRequired[StackTrace]
    type: str  # "console"
    method: str
    args: list[RemoteValue]


class JavascriptLogEntry(TypedDict):
    """Log entry from JavaScript errors."""

    level: LogLevel
    source: Source
    text: str | None
    timestamp: int
    stackTrace: NotRequired[StackTrace]
    type: str  # "javascript"


class GenericLogEntry(TypedDict):
    """Log entry from other sources."""

    level: LogLevel
    source: Source
    text: str | None
    timestamp: int
    stackTrace: NotRequired[StackTrace]
    type: str


LogEntry = ConsoleLogEntry | JavascriptLogEntry | GenericLogEntry
