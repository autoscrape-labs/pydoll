from __future__ import annotations

from typing import Optional, TypedDict

from typing_extensions import Required


class WSAddressResolverParams(TypedDict, total=False):
    """Parameters passed to a WebSocket address resolver callback.

    Note that the list is non-exhaustive.

    Attributes:
        host: The hostname of the browser's debugging server.
        port: The port of the browser's debugging server.
        use_secure: Whether to use HTTPS/WSS (``True``) or HTTP/WS (``False``)
            when resolving the WebSocket address.
    """

    host: Required[Optional[str]]
    port: Required[Optional[int]]
    use_secure: Required[bool]
