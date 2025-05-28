from typing import List, TypedDict

from pydoll.protocol.target.types import TargetInfo


class AttachToTargetResultDict(TypedDict):
    sessionId: str


class CreateBrowserContextResultDict(TypedDict):
    browserContextId: str


class CreateTargetResultDict(TypedDict):
    targetId: str


class GetBrowserContextsResultDict(TypedDict):
    browserContextIds: List[str]


class GetTargetsResultDict(TypedDict):
    targetInfos: List[TargetInfo]


class AttachToBrowserTargetResultDict(TypedDict):
    sessionId: str


class GetTargetInfoResultDict(TypedDict):
    targetInfo: TargetInfo


class AttachToTargetResponse(TypedDict):
    result: AttachToTargetResultDict


class CreateBrowserContextResponse(TypedDict):
    result: CreateBrowserContextResultDict


class CreateTargetResponse(TypedDict):
    result: CreateTargetResultDict


class GetBrowserContextsResponse(TypedDict):
    result: GetBrowserContextsResultDict


class GetTargetsResponse(TypedDict):
    result: GetTargetsResultDict


class AttachToBrowserTargetResponse(TypedDict):
    result: AttachToBrowserTargetResultDict


class GetTargetInfoResponse(TypedDict):
    result: GetTargetInfoResultDict
