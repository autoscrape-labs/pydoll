from enum import Enum

from pydoll.protocol.bidi.base import BiDiEvent
from pydoll.protocol.bidi.log.types import LogEntry


class LogEvent(str, Enum):
    """Log module event names."""

    ENTRY_ADDED = 'log.entryAdded'


EntryAddedEvent = BiDiEvent[LogEntry]
