from __future__ import annotations

from typing_extensions import TypedDict

from pydoll.protocol.base import Command, EmptyResponse, Response


class PerformActionsParams(TypedDict):
    context: str
    actions: list[dict]


PerformActionsResponse = Response[EmptyResponse]
PerformActionsCommand = Command[PerformActionsParams, PerformActionsResponse]


def perform_actions(context: str, actions: list[dict]) -> PerformActionsCommand:
    return Command(
        method='input.performActions',
        params=PerformActionsParams(context=context, actions=actions),
    )
