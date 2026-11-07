from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from pydoll.exceptions import TargetCrashed
from pydoll.protocol.browser.methods import BrowserMethod
from pydoll.protocol.fetch.methods import FetchMethod
from pydoll.protocol.inspector.events import InspectorEvent
from pydoll.protocol.network.methods import NetworkMethod
from pydoll.protocol.page.methods import PageMethod
from pydoll.protocol.storage.methods import StorageMethod
from pydoll.protocol.target.methods import TargetMethod

if TYPE_CHECKING:
    from pydoll.protocol.base import CDPEvent, Command, Response

logger = logging.getLogger(__name__)

COMMANDS_ANSWERED_AFTER_CRASH: frozenset[str] = frozenset({
    *BrowserMethod,
    *FetchMethod,
    *StorageMethod,
    *TargetMethod,
    PageMethod.NAVIGATE,
    PageMethod.RELOAD,
    PageMethod.CLOSE,
    PageMethod.STOP_LOADING,
    PageMethod.BRING_TO_FRONT,
    PageMethod.GET_NAVIGATION_HISTORY,
    PageMethod.NAVIGATE_TO_HISTORY_ENTRY,
    PageMethod.RESET_NAVIGATION_HISTORY,
    NetworkMethod.GET_COOKIES,
    NetworkMethod.SET_COOKIE,
    NetworkMethod.SET_COOKIES,
    NetworkMethod.DELETE_COOKIES,
    NetworkMethod.CLEAR_BROWSER_COOKIES,
})
"""Commands Chrome still answers on a page session after the renderer crashed.

Measured against Chrome: the Browser, Fetch, Storage and Target domains and
the cookie methods are served by the browser process, and the navigation
ones are how a crashed tab recovers. Every other command of a renderer domain
waits for an answer that never comes.
"""


NAVIGATIONS_THAT_RELOAD_A_CRASHED_TARGET: frozenset[str] = frozenset({
    PageMethod.NAVIGATE,
    PageMethod.RELOAD,
    PageMethod.NAVIGATE_TO_HISTORY_ENTRY,
})
"""Commands whose success starts a new renderer in a crashed target."""


class TargetCrashManager:
    """
    Follows whether a connection's target renderer crashed.

    Chrome reports the crash with ``Inspector.targetCrashed`` on the target's
    own session and stops answering every command that needs the renderer,
    until ``Inspector.targetReloadedAfterCrash`` reports that a navigation or
    a reload started a new one.
    """

    def __init__(self) -> None:
        """Initialize with the target alive."""
        self._crashed = False

    @property
    def crashed(self) -> bool:
        """Whether the target's renderer crashed and has not been reloaded since."""
        return self._crashed

    def track(self, event: CDPEvent) -> bool:
        """Update the crash state from an event received on the connection.

        Events of a child session (an attached iframe or worker, carrying a
        ``sessionId``) are about that session's renderer, not the target's.

        Returns:
            True when the event reports that the target just crashed.
        """
        if 'sessionId' in event:
            return False
        method = event.get('method')
        if method == InspectorEvent.TARGET_CRASHED:
            logger.error('Target renderer crashed')
            self._crashed = True
            return True
        if method == InspectorEvent.TARGET_RELOADED_AFTER_CRASH:
            logger.info('Target reloaded after crash')
            self._crashed = False
        return False

    def observe_answer(self, command: Command, response: Response) -> None:
        """Treat a successful navigation of a crashed target as its recovery.

        On the target's own session Chrome reports the recovery with
        ``Inspector.targetReloadedAfterCrash``, but a session opened after the
        crash (the connection dropped meanwhile) never gets that event. A
        navigation Chrome accepted without an error has started a new renderer
        either way.
        """
        if not self._crashed or 'sessionId' in command:
            return
        if command.get('method', '') not in NAVIGATIONS_THAT_RELOAD_A_CRASHED_TARGET:
            return
        result = response.get('result', {})
        if result.get('errorText'):
            return
        logger.info('Navigation started a new renderer for the crashed target')
        self._crashed = False

    def check(self, command: Command) -> None:
        """Refuse a command the crashed renderer would never answer.

        Commands the browser process serves (navigation, closing, cookies and
        the browser-wide domains) still go through, so the tab can recover, and
        so do commands for child sessions, which have renderers of their own.

        Raises:
            TargetCrashed: If the target crashed and the command needs its renderer.
        """
        if not self._crashed or 'sessionId' in command:
            return
        if command.get('method', '') in COMMANDS_ANSWERED_AFTER_CRASH:
            return
        raise TargetCrashed()
