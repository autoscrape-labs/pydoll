from __future__ import annotations

import logging
from enum import Enum
from typing import TYPE_CHECKING

from pydoll.protocol.accessibility.methods import AccessibilityMethod
from pydoll.protocol.dom.methods import DomMethod
from pydoll.protocol.fetch.methods import FetchMethod
from pydoll.protocol.network.methods import NetworkMethod
from pydoll.protocol.page.methods import PageMethod
from pydoll.protocol.runtime.methods import RuntimeMethod

if TYPE_CHECKING:
    from pydoll.protocol.base import Command

logger = logging.getLogger(__name__)

DOMAIN_DISABLE_FOR_ENABLE: dict[str, str] = {
    AccessibilityMethod.ENABLE: AccessibilityMethod.DISABLE,
    DomMethod.ENABLE: DomMethod.DISABLE,
    FetchMethod.ENABLE: FetchMethod.DISABLE,
    NetworkMethod.ENABLE: NetworkMethod.DISABLE,
    PageMethod.ENABLE: PageMethod.DISABLE,
    RuntimeMethod.ENABLE: RuntimeMethod.DISABLE,
}
"""Domain enable commands whose effect a new session has to repeat, with their disable."""

DOMAIN_ENABLE_FOR_DISABLE: dict[str, str] = {
    disable: enable for enable, disable in DOMAIN_DISABLE_FOR_ENABLE.items()
}


class DomainsManager:
    """
    Tracks the CDP domains a connection should have enabled, and which its live session has.

    Domain state belongs to the CDP session, so a new WebSocket starts with
    every domain off while the tab still reports them on. The domains a caller
    enabled (with their parameters, Fetch patterns included) are remembered
    until disabled, and the live session's own set is reset on every new
    connection, so the difference is what has to be enabled again.
    """

    def __init__(self) -> None:
        """Initialize with no domain enabled."""
        self._wanted: dict[str, Command] = {}
        self._live: set[str] = set()

    @property
    def missing(self) -> list[Command]:
        """Enable commands the live session lacks, in the order they were first enabled."""
        return [
            {'method': method, 'params': dict(enable.get('params', {}))}
            for method, enable in self._wanted.items()
            if method not in self._live
        ]

    def record(self, command: Command) -> None:
        """Record a command the browser accepted, if it enables or disables a domain.

        A command for a child session (an attached iframe or worker, sent with
        ``sessionId``) belongs to that session, not to the connection's own.
        """
        if 'sessionId' in command:
            return
        method = self._method_name(command)
        if method in DOMAIN_DISABLE_FOR_ENABLE:
            self._wanted[method] = {'method': method, 'params': dict(command.get('params', {}))}
            self._live.add(method)
        elif method in DOMAIN_ENABLE_FOR_DISABLE:
            self.forget(DOMAIN_ENABLE_FOR_DISABLE[method])

    def mark_live(self, enable_method: str) -> None:
        """Note that the live session was sent the enable, so it no longer counts as missing."""
        self._live.add(enable_method)

    def reject(self, enable: Command) -> None:
        """Stop wanting a domain the new session refused, unless it was enabled again since."""
        method = self._method_name(enable)
        if self._wanted.get(method) == {'method': method, 'params': dict(enable.get('params', {}))}:
            self.forget(method)

    def forget(self, enable_method: str) -> None:
        """Stop wanting a domain on, for example because a new session rejected it."""
        self._wanted.pop(enable_method, None)
        self._live.discard(enable_method)

    def reset_session(self) -> None:
        """Note that the live session is gone, so every wanted domain is missing again."""
        self._live.clear()

    def clear(self) -> None:
        """Forget every domain, wanted and live."""
        self._wanted.clear()
        self._live.clear()

    @staticmethod
    def _method_name(command: Command) -> str:
        """The command's CDP method as a plain string (methods may be enums)."""
        raw_method = command.get('method', '')
        return raw_method.value if isinstance(raw_method, Enum) else raw_method
