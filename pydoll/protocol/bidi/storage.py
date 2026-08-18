from __future__ import annotations

from typing import Optional

from typing_extensions import NotRequired, TypedDict

from pydoll.protocol.base import Command, EmptyResponse, Response


class CookieValue(TypedDict):
    type: str
    value: str


class CookieFilter(TypedDict, total=False):
    name: str
    domain: str
    path: str
    size: int
    httpOnly: bool
    secure: bool
    sameSite: str
    expiry: int


class BrowsingContextPartitionDescriptor(TypedDict):
    type: str
    context: str


class CookieParam(TypedDict):
    """Cookie parameter object for set_cookie / set_cookies."""

    name: str
    value: str
    domain: str
    path: NotRequired[str]
    httpOnly: NotRequired[bool]
    secure: NotRequired[bool]
    sameSite: NotRequired[str]
    expiry: NotRequired[int]


class CookieHeader(TypedDict):
    name: str
    value: CookieValue
    domain: str
    path: NotRequired[str]
    httpOnly: NotRequired[bool]
    secure: NotRequired[bool]
    sameSite: NotRequired[str]
    expiry: NotRequired[int]


class GetCookiesParams(TypedDict):
    filter: NotRequired[CookieFilter]
    partition: NotRequired[BrowsingContextPartitionDescriptor]


class SetCookieParams(TypedDict):
    cookie: CookieHeader
    partition: NotRequired[BrowsingContextPartitionDescriptor]


class DeleteCookiesParams(TypedDict):
    filter: NotRequired[CookieFilter]
    partition: NotRequired[BrowsingContextPartitionDescriptor]


class GetCookiesResult(TypedDict):
    cookies: list[dict]
    partitionKey: dict


class SetCookieResult(TypedDict):
    partitionKey: dict


GetCookiesResponse = Response[GetCookiesResult]
SetCookieResponse = Response[SetCookieResult]
DeleteCookiesResponse = Response[EmptyResponse]

GetCookiesCommand = Command[GetCookiesParams, GetCookiesResponse]
SetCookieCommand = Command[SetCookieParams, SetCookieResponse]
DeleteCookiesCommand = Command[DeleteCookiesParams, DeleteCookiesResponse]


def _context_partition(context: str) -> BrowsingContextPartitionDescriptor:
    return BrowsingContextPartitionDescriptor(type='context', context=context)


def get_cookies(
    context: str,
    filter: Optional[CookieFilter] = None,
) -> GetCookiesCommand:
    params = GetCookiesParams(partition=_context_partition(context))
    if filter is not None:
        params['filter'] = filter
    return Command(method='storage.getCookies', params=params)


def set_cookie(
    context: str,
    name: str,
    value: str,
    domain: str,
    path: str = '/',
    http_only: bool = False,
    secure: bool = False,
    same_site: Optional[str] = None,
    expiry: Optional[int] = None,
) -> SetCookieCommand:
    cookie = CookieHeader(
        name=name,
        value=CookieValue(type='string', value=value),
        domain=domain,
        path=path,
        httpOnly=http_only,
        secure=secure,
    )
    if same_site is not None:
        cookie['sameSite'] = same_site
    if expiry is not None:
        cookie['expiry'] = expiry
    return Command(
        method='storage.setCookie',
        params=SetCookieParams(cookie=cookie, partition=_context_partition(context)),
    )


def delete_cookies(
    context: str,
    filter: Optional[CookieFilter] = None,
) -> DeleteCookiesCommand:
    params = DeleteCookiesParams(partition=_context_partition(context))
    if filter is not None:
        params['filter'] = filter
    return Command(method='storage.deleteCookies', params=params)
