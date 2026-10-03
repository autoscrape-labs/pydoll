from __future__ import annotations

from typing import Optional

from typing_extensions import NotRequired, TypedDict

from pydoll.protocol.base import Command, EmptyResponse, Response


class CapabilitiesRequest(TypedDict):
    alwaysMatch: NotRequired[dict]


class SessionNewParams(TypedDict):
    capabilities: CapabilitiesRequest


class SessionSubscribeParams(TypedDict):
    events: list[str]
    contexts: NotRequired[list[str]]


class SessionNewResult(TypedDict):
    sessionId: str
    capabilities: dict


SessionNewResponse = Response[SessionNewResult]
SessionSubscribeResponse = Response[EmptyResponse]

SessionNewCommand = Command[SessionNewParams, SessionNewResponse]
SessionSubscribeCommand = Command[SessionSubscribeParams, SessionSubscribeResponse]
SessionUnsubscribeCommand = Command[SessionSubscribeParams, SessionSubscribeResponse]


def new_session(capabilities: Optional[dict] = None) -> SessionNewCommand:
    params = SessionNewParams(capabilities={'alwaysMatch': capabilities or {}})
    return Command(method='session.new', params=params)


def subscribe(events: list[str], contexts: Optional[list[str]] = None) -> SessionSubscribeCommand:
    params = SessionSubscribeParams(events=events)
    if contexts is not None:
        params['contexts'] = contexts
    return Command(method='session.subscribe', params=params)


def unsubscribe(
    events: list[str], contexts: Optional[list[str]] = None
) -> SessionUnsubscribeCommand:
    params = SessionSubscribeParams(events=events)
    if contexts is not None:
        params['contexts'] = contexts
    return Command(method='session.unsubscribe', params=params)
