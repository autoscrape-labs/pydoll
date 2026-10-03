from __future__ import annotations

from typing_extensions import TypedDict

from pydoll.protocol.base import Command, EmptyResponse, Response


class PerformActionsParams(TypedDict):
    context: str
    actions: list[dict]


class SetFilesParams(TypedDict):
    context: str
    element: dict
    files: list[str]


PerformActionsResponse = Response[EmptyResponse]
PerformActionsCommand = Command[PerformActionsParams, PerformActionsResponse]

SetFilesResponse = Response[EmptyResponse]
SetFilesCommand = Command[SetFilesParams, SetFilesResponse]


class InputEvent:
    FILE_DIALOG_OPENED = 'input.fileDialogOpened'


def perform_actions(context: str, actions: list[dict]) -> PerformActionsCommand:
    return Command(
        method='input.performActions',
        params=PerformActionsParams(context=context, actions=actions),
    )


def set_files(context: str, shared_id: str, files: list[str]) -> SetFilesCommand:
    return Command(
        method='input.setFiles',
        params=SetFilesParams(context=context, element={'sharedId': shared_id}, files=files),
    )
