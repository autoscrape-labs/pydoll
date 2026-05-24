from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from pydoll.protocol.cdp.network.events import RequestWillBeSentEvent

logger = logging.getLogger(__name__)


class BaseEventTracker(ABC):
    """Tracks protocol-specific built-in events (network logs, dialogs)."""

    @property
    @abstractmethod
    def network_logs(self) -> list:
        ...

    @property
    @abstractmethod
    def dialog(self) -> dict:
        ...

    @abstractmethod
    def track(self, event_data: dict) -> None:
        """Process event for built-in tracking."""


class CDPEventTracker(BaseEventTracker):
    """Tracks CDP-specific network and dialog events."""

    def __init__(self) -> None:
        self._network_logs: list[RequestWillBeSentEvent] = []
        self._dialog: dict = {}

    @property
    def network_logs(self) -> list:
        return self._network_logs

    @property
    def dialog(self) -> dict:
        return self._dialog

    def track(self, event_data: dict) -> None:
        event_name = event_data.get('method', '')

        if 'Network.requestWillBeSent' in event_name:
            self._network_logs.append(cast('RequestWillBeSentEvent', event_data))
            self._network_logs = self._network_logs[-10000:]

        elif 'Page.javascriptDialogOpening' in event_name:
            self._dialog = event_data

        elif 'Page.javascriptDialogClosed' in event_name:
            self._dialog = {}


class BiDiEventTracker(BaseEventTracker):
    """Tracks BiDi-specific network and dialog events."""

    def __init__(self) -> None:
        self._network_logs: list[dict] = []
        self._dialog: dict = {}

    @property
    def network_logs(self) -> list:
        return self._network_logs

    @property
    def dialog(self) -> dict:
        return self._dialog

    def track(self, event_data: dict) -> None:
        event_name = event_data.get('method', '')

        if event_name == 'network.beforeRequestSent':
            self._network_logs.append(event_data)
            self._network_logs = self._network_logs[-10000:]

        elif event_name == 'browsingContext.userPromptOpened':
            self._dialog = event_data

        elif event_name == 'browsingContext.userPromptClosed':
            self._dialog = {}
