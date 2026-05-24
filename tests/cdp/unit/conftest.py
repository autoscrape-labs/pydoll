"""Unit-test fixtures: an in-memory connection fake that mirrors the real API.

FakeConnection stands in for ConnectionHandler for the bulk of Tab/WebElement
methods that merely translate a Python call into a CDP command and return
simple state. It exposes only the real ConnectionHandler surface plus
configuration/inspection helpers; it deliberately cannot inject events. Event
driven flows (callbacks, go_to, dialogs populated by events) are covered against
the real handler and FakeCDPServer in the integration suite instead.
"""

from __future__ import annotations

from typing import Awaitable, Callable, Optional

import pytest

from pydoll.browser.chromium import Chrome
from pydoll.browser.chromium.tab import Tab


class FakeConnection:
    """In-memory stand-in for ConnectionHandler.

    Records every command sent and returns a configurable response. Mirrors the
    public ConnectionHandler interface (execute_command, callback registration,
    ping, close, network_logs and dialog) so a Tab cannot tell it apart, while
    offering set_response/commands_for/last_command for the test to drive it.
    """

    def __init__(self) -> None:
        self.commands: list[dict] = []
        self.network_logs: list[dict] = []
        self.dialog: dict = {}
        self._results: dict[str, dict] = {}
        self._callbacks: dict[int, dict] = {}
        self._callback_id = 0
        self._command_id = 0

    def set_response(self, method: str, result: dict) -> None:
        """Configure the result payload returned for a command method."""
        self._results[method] = result

    def commands_for(self, method: str) -> list[dict]:
        """Every recorded command matching a CDP method, in arrival order."""
        return [command for command in self.commands if command.get('method') == method]

    def last_command(self, method: Optional[str] = None) -> dict:
        """The most recent recorded command, optionally filtered by method."""
        commands = self.commands_for(method) if method is not None else self.commands
        if not commands:
            raise AssertionError(f'no command recorded for {method!r}')
        return commands[-1]

    def callbacks_for(self, event_name: str) -> list:
        """Callbacks currently registered for an event name."""
        return [
            data['callback']
            for data in self._callbacks.values()
            if data['event'] == event_name
        ]

    async def execute_command(self, command: dict, timeout: int = 60) -> dict:
        """Record the command and return its configured (or empty) response."""
        self._command_id += 1
        command['id'] = self._command_id
        self.commands.append(command)
        return {'id': self._command_id, 'result': self._results.get(command.get('method'), {})}

    async def register_callback(
        self,
        event_name: str,
        callback: Callable[[dict], Awaitable[None]],
        temporary: bool = False,
    ) -> int:
        """Record a callback registration and return its id (never fired here)."""
        self._callback_id += 1
        self._callbacks[self._callback_id] = {
            'event': event_name,
            'callback': callback,
            'temporary': temporary,
        }
        return self._callback_id

    async def remove_callback(self, callback_id: int) -> bool:
        """Remove a registered callback by id."""
        return self._callbacks.pop(callback_id, None) is not None

    async def clear_callbacks(self) -> None:
        """Remove every registered callback."""
        self._callbacks.clear()

    async def ping(self) -> bool:
        """A fake connection is always responsive."""
        return True

    async def close(self) -> None:
        """Drop callbacks, mirroring the real handler's cleanup."""
        self._callbacks.clear()


@pytest.fixture
def fake_conn() -> FakeConnection:
    """A fresh in-memory FakeConnection per test."""
    return FakeConnection()


@pytest.fixture
def fake_tab(fake_conn) -> Tab:
    """A real Tab backed by an in-memory FakeConnection (no sockets, no browser).

    The Tab borrows an unstarted Chrome only for its options and tab registry.
    """
    return Tab(browser=Chrome(), target_id='fake-tab', connection_handler=fake_conn)
