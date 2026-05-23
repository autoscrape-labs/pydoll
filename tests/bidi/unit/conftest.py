"""Unit-test fixtures: an in-memory BiDi connection fake mirroring the real peer.

FakeBiDiConnection stands in for BiDiConnectionHandler for the BiDiTab /
BiDiWebElement methods that merely translate a Python call into a WebDriver BiDi
command and return simple state. It exposes the real handler surface
(execute_command, callback registration, ping, close, network_logs, dialog) plus
set_result/commands_for/last_command for the test to drive it. Event-driven flows
run against real Firefox in the integration suite instead.
"""

from __future__ import annotations

from typing import Awaitable, Callable, Optional

import pytest

from pydoll.browser.firefox.tab import BiDiTab


class FakeBiDiConnection:
    """In-memory stand-in for BiDiConnectionHandler.

    Records every command sent and returns a configurable BiDi success response
    (``{type, id, result}``). Mirrors the public handler interface so a BiDiTab
    cannot tell it apart, while offering set_result/commands_for/last_command.
    """

    def __init__(self) -> None:
        self.commands: list[dict] = []
        self.network_logs: list[dict] = []
        self.dialog: dict = {}
        self._results: dict[str, dict] = {}
        self._callbacks: dict[int, dict] = {}
        self._callback_id = 0
        self._command_id = 0

    def set_result(self, method: str, result: dict) -> None:
        """Configure the result payload returned for a BiDi command method."""
        self._results[method] = result

    def commands_for(self, method: str) -> list[dict]:
        """Every recorded command matching a BiDi method, in arrival order."""
        return [command for command in self.commands if command.get('method') == method]

    def last_command(self, method: Optional[str] = None) -> dict:
        """The most recent recorded command, optionally filtered by method."""
        commands = self.commands_for(method) if method is not None else self.commands
        if not commands:
            raise AssertionError(f'no command recorded for {method!r}')
        return commands[-1]

    async def execute_command(self, command: dict, timeout: int = 60) -> dict:
        """Record the command and return its configured (or empty) success response."""
        self._command_id += 1
        command['id'] = self._command_id
        self.commands.append(command)
        return {
            'type': 'success',
            'id': self._command_id,
            'result': self._results.get(command.get('method'), {}),
        }

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
def fake_bidi_conn() -> FakeBiDiConnection:
    """A fresh in-memory FakeBiDiConnection per test."""
    return FakeBiDiConnection()


@pytest.fixture
def fake_bidi_tab(fake_bidi_conn) -> BiDiTab:
    """A real BiDiTab backed by an in-memory FakeBiDiConnection (no sockets)."""
    return BiDiTab('fake-context', fake_bidi_conn)
