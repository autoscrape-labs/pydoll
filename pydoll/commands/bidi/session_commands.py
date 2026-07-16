from __future__ import annotations

from typing import TYPE_CHECKING

from pydoll.protocol.bidi.base import Command
from pydoll.protocol.bidi.session.methods import (
    NewParameters,
    SessionMethod,
)
from pydoll.protocol.bidi.session.types import (
    CapabilitiesRequest,
    SubscribeParameters,
)

if TYPE_CHECKING:
    from pydoll.protocol.bidi.session.methods import (
        EndCommand,
        NewCommand,
        StatusCommand,
        SubscribeCommand,
        UnsubscribeCommand,
    )
    from pydoll.protocol.bidi.session.types import (
        UnsubscribeByAttributesRequest,
        UnsubscribeByIDRequest,
    )


class SessionCommands:
    """Command builders for the BiDi session module."""

    @staticmethod
    def status() -> StatusCommand:
        """Generates a command to check if the remote end can create new sessions."""
        return Command(method=SessionMethod.STATUS, params={})

    @staticmethod
    def new(
        capabilities: CapabilitiesRequest | None = None,
    ) -> NewCommand:
        """Generates a command to create a new BiDi session."""
        params = NewParameters(
            capabilities=capabilities or CapabilitiesRequest()
        )
        return Command(method=SessionMethod.NEW, params=params)

    @staticmethod
    def end() -> EndCommand:
        """Generates a command to end the current session."""
        return Command(method=SessionMethod.END, params={})

    @staticmethod
    def subscribe(
        events: list[str],
        contexts: list[str] | None = None,
        user_contexts: list[str] | None = None,
    ) -> SubscribeCommand:
        """Generates a command to subscribe to specific events."""
        params = SubscribeParameters(events=events)
        if contexts is not None:
            params['contexts'] = contexts
        if user_contexts is not None:
            params['userContexts'] = user_contexts
        return Command(method=SessionMethod.SUBSCRIBE, params=params)

    @staticmethod
    def unsubscribe_by_id(
        subscriptions: list[str],
    ) -> UnsubscribeCommand:
        """Generates a command to unsubscribe by subscription IDs."""
        params: UnsubscribeByIDRequest = {'subscriptions': subscriptions}
        return Command(method=SessionMethod.UNSUBSCRIBE, params=params)

    @staticmethod
    def unsubscribe_by_events(
        events: list[str],
    ) -> UnsubscribeCommand:
        """Generates a command to unsubscribe by event names."""
        params: UnsubscribeByAttributesRequest = {'events': events}
        return Command(method=SessionMethod.UNSUBSCRIBE, params=params)
