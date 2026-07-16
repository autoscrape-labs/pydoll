"""Shared base for the browser-backed HTTP client (CDP and BiDi).

Both backends make requests the same way: run the page's ``fetch()`` for the
status/body, and capture request/response headers and Set-Cookie from the
protocol's network events (the parts JS ``fetch()`` cannot read). This base owns
the protocol-agnostic surface — the public API, URL/option building, cookie
parsing and Response assembly — and delegates the protocol-specific bits (running
the fetch, subscribing to network events, extracting headers/cookies) to hooks
implemented by the CDP and BiDi subclasses.
"""

from __future__ import annotations

import json as jsonlib
import logging
from abc import ABC, abstractmethod
from typing import Any, Generic, Optional, TypeVar, Union
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from pydoll.browser.requests.response import Response
from pydoll.exceptions import HTTPError
from pydoll.protocol.types import Header, ResponseCookie

logger = logging.getLogger(__name__)

T_Tab = TypeVar('T_Tab')


class BaseRequest(ABC, Generic[T_Tab]):
    """Protocol-agnostic HTTP client executed in the browser's fetch context.

    Requests inherit the browser's session state (cookies, auth, CORS). Subclasses
    bind it to a concrete tab and supply the protocol-specific hooks.
    """

    def __init__(self, tab: T_Tab):
        """Initialize the request helper bound to a tab.

        Args:
            tab: The tab whose JavaScript context and session state are used.
        """
        self.tab = tab
        self._callback_ids: list[int] = []
        logger.debug('Request helper initialized for tab')

    async def request(
        self,
        method: str,
        url: str,
        params: Optional[dict[str, str]] = None,
        data: Optional[Union[dict, list, tuple, str, bytes]] = None,
        json: Optional[dict[str, Any]] = None,
        headers: Optional[list[Header]] = None,
        **kwargs,
    ) -> Response:
        """Execute an HTTP request in the browser's JavaScript context.

        Uses the browser's fetch API, inheriting all session state (cookies,
        authentication, security context).

        Args:
            method: HTTP method (GET, POST, ...). Case insensitive.
            url: Target URL, relative or absolute.
            params: Query parameters merged into the URL.
            data: Request body. dict/list/tuple is form-urlencoded; str/bytes is
                sent as-is. Mutually exclusive with json.
            json: Body serialized as JSON (sets Content-Type). Mutually exclusive
                with data.
            headers: Extra headers ADDED to the browser's automatic headers.
            **kwargs: Extra fetch options (credentials, mode, cache, ...).

        Returns:
            Response with status, headers, content and cookies.

        Raises:
            HTTPError: If the request fails or a network error occurs.
        """
        final_url = self._build_url_with_params(url, params)
        options = self._build_request_options(method, headers, json, data, **kwargs)
        logger.info(f'Executing request: method={method.upper()}, url={final_url}')
        try:
            await self._register_callbacks()
            value = await self._execute_fetch_request(final_url, options)
            if 'error' in value:
                raise HTTPError(f'Fetch error: {value["error"]}')
            await self._await_metadata(final_url)
            received_headers = self._extract_received_headers()
            sent_headers = self._extract_sent_headers()
            cookies = self._extract_set_cookies()
            return self._build_response(value, received_headers, sent_headers, cookies)
        except HTTPError:
            raise
        except Exception as exc:
            logger.error(f'Request failed: {exc}')
            raise HTTPError(f'Request failed: {str(exc)}') from exc
        finally:
            await self._clear_callbacks()

    async def get(
        self, url: str, params: Optional[dict[str, str]] = None, **kwargs
    ) -> Response:
        """Execute a GET request."""
        return await self.request('GET', url, params=params, **kwargs)

    async def post(
        self,
        url: str,
        data: Optional[Union[dict, list, tuple, str, bytes]] = None,
        json: Optional[dict[str, Any]] = None,
        **kwargs,
    ) -> Response:
        """Execute a POST request."""
        return await self.request('POST', url, data=data, json=json, **kwargs)

    async def put(
        self,
        url: str,
        data: Optional[Union[dict, list, tuple, str, bytes]] = None,
        json: Optional[dict[str, Any]] = None,
        **kwargs,
    ) -> Response:
        """Execute a PUT request."""
        return await self.request('PUT', url, data=data, json=json, **kwargs)

    async def patch(
        self,
        url: str,
        data: Optional[Union[dict, list, tuple, str, bytes]] = None,
        json: Optional[dict[str, Any]] = None,
        **kwargs,
    ) -> Response:
        """Execute a PATCH request."""
        return await self.request('PATCH', url, data=data, json=json, **kwargs)

    async def delete(self, url: str, **kwargs) -> Response:
        """Execute a DELETE request."""
        return await self.request('DELETE', url, **kwargs)

    async def head(self, url: str, **kwargs) -> Response:
        """Execute a HEAD request."""
        return await self.request('HEAD', url, **kwargs)

    async def options(self, url: str, **kwargs) -> Response:
        """Execute an OPTIONS request."""
        return await self.request('OPTIONS', url, **kwargs)

    @abstractmethod
    async def _execute_fetch_request(
        self, url: str, options: dict[str, Any]
    ) -> dict[str, Any]:
        """Run the page's fetch and return the result value dict.

        The dict carries ``status``, ``ok``, ``url``, ``content`` (list of byte
        ints), ``text``, ``json`` — or ``error`` if the fetch failed.
        """

    @abstractmethod
    async def _register_callbacks(self) -> None:
        """Subscribe to the network events that carry request/response metadata."""

    @abstractmethod
    async def _clear_callbacks(self) -> None:
        """Remove this request's network listeners and reset captured state."""

    @abstractmethod
    def _extract_received_headers(self) -> list[Header]:
        """Headers received from the server (from captured response events)."""

    @abstractmethod
    def _extract_sent_headers(self) -> list[Header]:
        """Headers actually sent (from captured request events)."""

    @abstractmethod
    def _extract_set_cookies(self) -> list[ResponseCookie]:
        """Cookies parsed from Set-Cookie in the captured response events."""

    async def _await_metadata(self, url: str) -> None:
        """Give network events time to arrive before extraction (no-op by default)."""

    @staticmethod
    def _build_url_with_params(url: str, params: Optional[dict[str, str]]) -> str:
        """Build final URL with query parameters."""
        if not params:
            return url
        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        for key, value in params.items():
            query[key] = [value]
        return urlunparse(parsed._replace(query=urlencode(query, doseq=True)))

    def _build_request_options(
        self,
        method: str,
        headers: Optional[list[Header]],
        json: Optional[dict[str, Any]],
        data: Optional[Union[dict, list, tuple, str, bytes]],
        **kwargs,
    ) -> dict[str, Any]:
        """Build the fetch options dictionary."""
        headers_dict = self._convert_header_entries_to_dict(headers) if headers else {}
        options = {'method': method.upper(), 'headers': headers_dict, **kwargs}
        self._add_request_body(options, json, data)
        return options

    def _add_request_body(
        self,
        options: dict[str, Any],
        json: Optional[dict[str, Any]],
        data: Optional[Union[dict, list, tuple, str, bytes]],
    ) -> None:
        """Add request body and the appropriate Content-Type header."""
        if json is not None:
            self._handle_json_options(options, json)
        elif data is not None:
            self._handle_data_options(options, data)

    @staticmethod
    def _handle_json_options(options: dict[str, Any], json: Optional[dict[str, Any]]) -> None:
        """Set a JSON body and Content-Type."""
        options['body'] = jsonlib.dumps(json)
        options['headers'].setdefault('Content-Type', 'application/json')

    @staticmethod
    def _handle_data_options(
        options: dict[str, Any], data: Optional[Union[dict, list, tuple, str, bytes]]
    ) -> None:
        """Set a form-encoded or raw body."""
        if isinstance(data, (dict, list, tuple)):
            options['body'] = urlencode(data, doseq=True)
            options['headers'].setdefault('Content-Type', 'application/x-www-form-urlencoded')
        else:
            options['body'] = data

    @staticmethod
    def _convert_header_entries_to_dict(headers: list[Header]) -> dict[str, str]:
        """Convert Header entries to a plain dict for the fetch API."""
        return {header['name']: header['value'] for header in headers}

    @staticmethod
    def _convert_dict_to_header_entries(headers_dict: dict) -> list[Header]:
        """Convert a header dictionary to a list of Header entries."""
        return [Header(name=name, value=value) for name, value in headers_dict.items()]

    @classmethod
    def _parse_set_cookie_header(cls, set_cookie_header: str) -> list[ResponseCookie]:
        """Parse a Set-Cookie header value (single or newline-joined) into cookies."""
        cookies = []
        for line in set_cookie_header.split('\n'):
            cookie = cls._parse_cookie_line(line)
            if cookie:
                cookies.append(cookie)
        return cookies

    @staticmethod
    def _parse_cookie_line(line: str) -> Optional[ResponseCookie]:
        """Parse one Set-Cookie line to (name, value), ignoring attributes."""
        if '=' not in line:
            return None
        name = line.split('=', 1)[0].strip()
        value = line.split('=', 1)[1].split(';', 1)[0].strip()
        if not name:
            return None
        return ResponseCookie(name=name, value=value)

    @staticmethod
    def _add_unique_cookies(
        cookies: list[ResponseCookie], new_cookies: list[ResponseCookie]
    ) -> None:
        """Append cookies, skipping duplicates."""
        for cookie in new_cookies:
            if cookie not in cookies:
                cookies.append(cookie)

    @staticmethod
    def _build_response(
        value: dict[str, Any],
        response_headers: list[Header],
        request_headers: list[Header],
        cookies: list[ResponseCookie],
    ) -> Response:
        """Assemble a Response from the fetch result value and captured metadata."""
        return Response(
            status_code=value['status'],
            content=bytes(value.get('content', b'')),
            text=value['text'],
            json=value['json'],
            response_headers=response_headers,
            request_headers=request_headers,
            cookies=cookies,
            url=value['url'],
        )
