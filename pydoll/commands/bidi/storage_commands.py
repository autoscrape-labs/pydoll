from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from pydoll.protocol.bidi.base import Command
from pydoll.protocol.bidi.storage.methods import (
    DeleteCookiesParameters,
    GetCookiesParameters,
    SetCookieParameters,
    StorageMethod,
)
from pydoll.protocol.bidi.storage.types import (
    CookieFilter,
    PartialCookie,
    PartitionDescriptor,
)

if TYPE_CHECKING:
    from pydoll.protocol.bidi.storage.methods import (
        DeleteCookiesCommand,
        GetCookiesCommand,
        SetCookieCommand,
    )


class StorageCommands:
    """Command builders for the BiDi storage module."""

    @staticmethod
    def get_cookies(
        filter: Optional[CookieFilter] = None,
        partition: Optional[PartitionDescriptor] = None,
    ) -> GetCookiesCommand:
        """Generates a command to get cookies."""
        params = GetCookiesParameters()
        if filter is not None:
            params['filter'] = filter
        if partition is not None:
            params['partition'] = partition
        return Command(method=StorageMethod.GET_COOKIES, params=params)

    @staticmethod
    def set_cookie(
        cookie: PartialCookie,
        partition: Optional[PartitionDescriptor] = None,
    ) -> SetCookieCommand:
        """Generates a command to set a cookie."""
        params = SetCookieParameters(cookie=cookie)
        if partition is not None:
            params['partition'] = partition
        return Command(method=StorageMethod.SET_COOKIE, params=params)

    @staticmethod
    def delete_cookies(
        filter: Optional[CookieFilter] = None,
        partition: Optional[PartitionDescriptor] = None,
    ) -> DeleteCookiesCommand:
        """Generates a command to delete cookies."""
        params = DeleteCookiesParameters()
        if filter is not None:
            params['filter'] = filter
        if partition is not None:
            params['partition'] = partition
        return Command(method=StorageMethod.DELETE_COOKIES, params=params)
