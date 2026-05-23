"""Conversion between protocol-agnostic cookies and CDP cookie types.

The public surface (``Tab``/``Browser`` ``get_cookies``/``set_cookies``) speaks the
portable ``pydoll.protocol.types`` cookie types. CDP commands use their own richer
cookie types, so these helpers translate at the boundary. CDP-only fields (``session``,
``priority``, ``partitionKey``, ...) are dropped on the way out; reach for them via the
escape hatch ``execute_protocol_command(NetworkCommands.get_cookies())`` when needed.
"""

from __future__ import annotations

from pydoll.protocol.cdp.network.types import Cookie as CDPCookie
from pydoll.protocol.cdp.network.types import CookieParam as CDPCookieParam
from pydoll.protocol.cdp.network.types import CookieSameSite
from pydoll.protocol.types import Cookie, CookieParam


def to_generic_cookies(cdp_cookies: list[CDPCookie]) -> list[Cookie]:
    """Convert CDP cookies into protocol-agnostic cookies."""
    return [_to_generic_cookie(cookie) for cookie in cdp_cookies]


def _to_generic_cookie(cookie: CDPCookie) -> Cookie:
    result = Cookie(
        name=cookie['name'],
        value=cookie['value'],
        domain=cookie['domain'],
        path=cookie['path'],
        size=cookie['size'],
        httpOnly=cookie['httpOnly'],
        secure=cookie['secure'],
        sameSite=cookie.get('sameSite', ''),
    )
    expires = cookie['expires']
    if expires >= 0:
        result['expiry'] = int(expires)
    return result


def to_cdp_cookie_params(cookies: list[CookieParam]) -> list[CDPCookieParam]:
    """Convert protocol-agnostic cookie params into CDP cookie params."""
    return [_to_cdp_cookie_param(cookie) for cookie in cookies]


def _to_cdp_cookie_param(cookie: CookieParam) -> CDPCookieParam:
    result = CDPCookieParam(name=cookie['name'], value=cookie['value'])
    if 'domain' in cookie:
        result['domain'] = cookie['domain']
    if 'path' in cookie:
        result['path'] = cookie['path']
    if 'secure' in cookie:
        result['secure'] = cookie['secure']
    if 'httpOnly' in cookie:
        result['httpOnly'] = cookie['httpOnly']
    if 'expiry' in cookie:
        result['expires'] = float(cookie['expiry'])
    if 'sameSite' in cookie:
        result['sameSite'] = CookieSameSite(cookie['sameSite'])
    return result
