from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections import deque
from typing import TYPE_CHECKING, Mapping, Sequence, cast

if TYPE_CHECKING:
    from pydoll.protocol.cdp.network.events import RequestWillBeSentEvent
    from pydoll.protocol.cdp.page.events import JavascriptDialogOpeningEvent

logger = logging.getLogger(__name__)

MAX_NETWORK_LOGS = 10000


class BaseEventTracker(ABC):
    """Tracks protocol-specific built-in events (network logs, dialogs).

    Trackers are fed every event the connection receives, synchronously on the
    read loop, so the state they expose is always as fresh as the socket.
    """

    @property
    @abstractmethod
    def network_logs(self) -> Sequence[Mapping[str, object]]:
        """Snapshot of the most recent network request events."""

    @property
    @abstractmethod
    def dialog(self) -> Mapping[str, object]:
        """Event of the currently open dialog, or an empty mapping when none is open."""

    @abstractmethod
    def track(self, event_data: dict) -> None:
        """Process event for built-in tracking."""


class CDPEventTracker(BaseEventTracker):
    """Tracks CDP network requests and JavaScript dialogs.

    ``network_logs`` keeps the last ``MAX_NETWORK_LOGS`` ``Network.requestWillBeSent``
    events in a bounded deque. ``dialog`` holds the ``Page.javascriptDialogOpening``
    event while a dialog is open and an empty (falsy) event otherwise, which is
    what ``Tab.has_dialog`` tests.
    """

    def __init__(self) -> None:
        self._network_logs: deque[RequestWillBeSentEvent] = deque(maxlen=MAX_NETWORK_LOGS)
        self._dialog: JavascriptDialogOpeningEvent = self._no_dialog()

    @staticmethod
    def _no_dialog() -> JavascriptDialogOpeningEvent:
        return cast('JavascriptDialogOpeningEvent', {})

    @property
    def network_logs(self) -> list[RequestWillBeSentEvent]:
        return list(self._network_logs)

    @property
    def dialog(self) -> JavascriptDialogOpeningEvent:
        return self._dialog

    def track(self, event_data: dict) -> None:
        event_name = event_data.get('method', '')

        if 'Network.requestWillBeSent' in event_name:
            self._network_logs.append(cast('RequestWillBeSentEvent', event_data))

        elif 'Page.javascriptDialogOpening' in event_name and 'params' in event_data:
            self._dialog = cast('JavascriptDialogOpeningEvent', event_data)

        elif 'Page.javascriptDialogClosed' in event_name:
            self._dialog = self._no_dialog()


class BiDiEventTracker(BaseEventTracker):
    """Tracks WebDriver BiDi network requests and user prompts.

    ``network_logs`` keeps the last ``MAX_NETWORK_LOGS`` ``network.beforeRequestSent``
    events; ``dialog`` holds the ``browsingContext.userPromptOpened`` event while a
    prompt is open and an empty dict otherwise.
    """

    def __init__(self) -> None:
        self._network_logs: deque[dict] = deque(maxlen=MAX_NETWORK_LOGS)
        self._dialog: dict = {}

    @property
    def network_logs(self) -> list[dict]:
        return list(self._network_logs)

    @property
    def dialog(self) -> dict:
        return self._dialog

    def track(self, event_data: dict) -> None:
        event_name = event_data.get('method', '')

        if event_name == 'network.beforeRequestSent':
            self._network_logs.append(event_data)

        elif event_name == 'browsingContext.userPromptOpened':
            self._dialog = event_data

        elif event_name == 'browsingContext.userPromptClosed':
            self._dialog = {}
