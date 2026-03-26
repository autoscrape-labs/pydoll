from enum import Enum

from typing_extensions import NotRequired, TypedDict

from pydoll.protocol.bidi.base import Command, CommandResponse
from pydoll.protocol.bidi.network.types import Cookie
from pydoll.protocol.bidi.storage.types import (
    CookieFilter,
    PartialCookie,
    PartitionDescriptor,
    PartitionKey,
)


class StorageMethod(str, Enum):
    """Storage module method names."""

    GET_COOKIES = 'storage.getCookies'
    SET_COOKIE = 'storage.setCookie'
    DELETE_COOKIES = 'storage.deleteCookies'


class GetCookiesParameters(TypedDict, total=False):
    """Parameters for storage.getCookies command."""

    filter: CookieFilter
    partition: PartitionDescriptor


class GetCookiesResult(TypedDict):
    """Result for storage.getCookies command."""

    cookies: list[Cookie]
    partitionKey: PartitionKey


class SetCookieParameters(TypedDict):
    """Parameters for storage.setCookie command."""

    cookie: PartialCookie
    partition: NotRequired[PartitionDescriptor]


class SetCookieResult(TypedDict):
    """Result for storage.setCookie command."""

    partitionKey: PartitionKey


class DeleteCookiesParameters(TypedDict, total=False):
    """Parameters for storage.deleteCookies command."""

    filter: CookieFilter
    partition: PartitionDescriptor


class DeleteCookiesResult(TypedDict):
    """Result for storage.deleteCookies command."""

    partitionKey: PartitionKey


GetCookiesCommand = Command[GetCookiesParameters, CommandResponse[GetCookiesResult]]
GetCookiesResponse = CommandResponse[GetCookiesResult]

SetCookieCommand = Command[SetCookieParameters, CommandResponse[SetCookieResult]]
SetCookieResponse = CommandResponse[SetCookieResult]

DeleteCookiesCommand = Command[DeleteCookiesParameters, CommandResponse[DeleteCookiesResult]]
DeleteCookiesResponse = CommandResponse[DeleteCookiesResult]
