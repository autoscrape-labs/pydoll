from typing import TypedDict


class GetResponseBodyResultDict(TypedDict):
    body: str
    base64encoded: bool


class TakeResponseBodyAsStreamResultDict(TypedDict):
    stream: str


class GetResponseBodyResponse(TypedDict):
    result: GetResponseBodyResultDict


class TakeResponseBodyAsStreamResponse(TypedDict):
    result: TakeResponseBodyAsStreamResultDict
