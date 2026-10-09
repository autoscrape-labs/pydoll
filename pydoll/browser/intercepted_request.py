from __future__ import annotations

from typing import TYPE_CHECKING

from pydoll.protocol.types import Header

if TYPE_CHECKING:
    from typing import Awaitable, Callable


class InterceptedRequest:
    """Protocol-agnostic intercepted network request.

    Provides a clean interface for inspecting and controlling
    intercepted requests, regardless of the underlying protocol.
    """

    def __init__(
        self,
        request_id: str,
        url: str,
        method: str,
        headers: list[Header],
        body: bytes | None,
        continue_fn: Callable[..., Awaitable[None]],
        fail_fn: Callable[..., Awaitable[None]],
        respond_fn: Callable[..., Awaitable[None]],
    ):
        self.request_id = request_id
        self.url = url
        self.method = method
        self.headers = headers
        self.body = body
        self._continue_fn = continue_fn
        self._fail_fn = fail_fn
        self._respond_fn = respond_fn

    async def continue_(
        self,
        url: str | None = None,
        method: str | None = None,
        headers: list[Header] | None = None,
    ):
        """Continue the request, optionally modifying it."""
        await self._continue_fn(
            request_id=self.request_id,
            url=url,
            method=method,
            headers=headers,
        )

    async def fail(self):
        """Fail the request with a network error."""
        await self._fail_fn(request_id=self.request_id)

    async def respond(
        self,
        status: int = 200,
        headers: list[Header] | None = None,
        body: str | None = None,
    ):
        """Respond to the request with a custom response."""
        await self._respond_fn(
            request_id=self.request_id,
            status=status,
            headers=headers,
            body=body,
        )
