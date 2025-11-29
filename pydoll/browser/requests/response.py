from __future__ import annotations

import json as jsonlib
import logging
from typing import TYPE_CHECKING, Any, Optional, Union

from pydoll.exceptions import HTTPError

if TYPE_CHECKING:
    from pydoll.protocol.fetch.types import HeaderEntry
    from pydoll.protocol.network.types import CookieParam

logger = logging.getLogger(__name__)

STATUS_CODE_RANGE_OK = range(200, 400)


class Response:
    """HTTP response object for browser-based fetch requests.

    This class provides a standardized interface for handling HTTP responses
    obtained through the browser's fetch API. It mimics the requests.Response
    interface while preserving all browser-specific metadata including cookies,
    headers, and network timing information.

    Key Features:
    - Compatible with requests.Response API for easy migration
    - Preserves both request and response headers for analysis
    - Automatic cookie extraction from Set-Cookie headers
    - Lazy JSON parsing with caching
    - Browser-context aware (respects CORS, security policies)
    - Content available in multiple formats (text, bytes, JSON)

    The response contains all data captured during the browser's fetch execution,
    including redirects, authentication flows, and any browser-applied transformations.
    """

    def __init__(
        self,
        status_code: int,
        content: bytes = b'',
        text: str = '',
        json: Optional[dict[str, Any]] = None,
        response_headers: Optional[list[HeaderEntry]] = None,
        request_headers: Optional[list[HeaderEntry]] = None,
        cookies: Optional[list[CookieParam]] = None,
        url: str = '',
    ):
        """Initialize a new Response instance with browser fetch results.

        Args:
            status_code: HTTP status code returned by the server (e.g., 200, 404, 500).
            content: Raw response body as bytes. Used for binary data or when
                text encoding is uncertain.
            text: Response body as decoded string. Pre-decoded by browser's fetch API.
            json: Pre-parsed JSON data if response Content-Type was application/json.
                If None, json() method will attempt to parse from text on demand.
            response_headers: Headers received from the server, including Set-Cookie,
                Content-Type, and any custom headers sent by the server.
            request_headers: Headers that were actually sent in the request, including
                browser-generated headers (User-Agent, Accept, etc.) and custom headers.
            cookies: Cookies extracted from Set-Cookie headers during the response.
                These represent new/updated cookies from this specific request.
            url: Final URL after any redirects. May differ from original request URL
                if the server performed redirects during the request.
        """
        self._status_code = status_code
        self._content = content
        self._text = text
        self._json = json
        self._response_headers = response_headers or []
        self._request_headers = request_headers or []
        self._cookies = cookies or []
        self._url = url
        self._ok = status_code in STATUS_CODE_RANGE_OK
        logger.debug(
            f'Response initialized: status={status_code}, url={url}, '
            f'headers={len(self._response_headers)}, cookies={len(self._cookies)}'
        )

    @property
    def ok(self) -> bool:
        """Check if the request was successful (2xx status codes).

        Returns:
            True if status code is in the 200-399 range, False otherwise.

        Note:
            This follows HTTP conventions where 2xx codes indicate success
            and 3xx codes indicate redirection (still considered "ok").
        """
        return self._ok

    @property
    def cookies(self) -> list[CookieParam]:
        """Get cookies that were set by the server during this response.

        Returns:
            List of cookies extracted from Set-Cookie headers. Each cookie
            contains name and value, with cookie attributes (Path, Domain, etc.)
            automatically handled by the browser.

        Note:
            These are only NEW/UPDATED cookies from this response. Existing
            browser cookies are managed automatically by the browser context.
        """
        return self._cookies

    @property
    def request_headers(self) -> list[HeaderEntry]:
        """Get headers that were actually sent in the HTTP request.

        Returns:
            List of headers sent to the server, including both custom headers
            provided by the user and automatic headers added by the browser
            (User-Agent, Accept, Authorization, etc.).

        Note:
            This shows the ACTUAL headers sent, which may differ from what
            was originally specified due to browser modifications.
        """
        return self._request_headers

    @property
    def headers(self) -> list[HeaderEntry]:
        """Get headers received from the server in the HTTP response.

        Returns:
            List of response headers sent by the server, including standard
            headers (Content-Type, Content-Length, etc.) and any custom headers.

        Note:
            Some security-sensitive headers may be filtered by the browser
            and not appear in this list due to CORS policies.
        """
        return self._response_headers

    @property
    def status_code(self) -> int:
        """Get the HTTP status code returned by the server.

        Returns:
            Integer status code (e.g., 200 for OK, 404 for Not Found, 500 for Server Error).
        """
        return self._status_code

    @property
    def text(self) -> str:
        """Get the response content as a decoded string.

        Returns:
            Response body decoded as UTF-8 string. If no text was provided
            during initialization, it will be decoded from the raw content.

        Note:
            Decoding uses 'replace' error handling to avoid crashes on
            invalid UTF-8 sequences.
        """
        if not self._text and self.content:
            self._text = self.content.decode('utf-8', errors='replace')
        return self._text

    @property
    def content(self) -> bytes:
        """Get the raw response content as bytes.

        Returns:
            Unmodified response body as bytes. Useful for binary data
            (images, files, etc.) or when you need to handle encoding manually.
        """
        return self._content

    @property
    def url(self) -> str:
        """Get the final URL of the response after any redirects.

        Returns:
            The final URL that was accessed, which may differ from the
            original request URL if redirects occurred.
        """
        return self._url

    def json(self) -> Union[dict[str, Any], list]:
        """Parse and return the response content as JSON data.

        Attempts to parse the response text as JSON. Uses caching to avoid
        re-parsing the same content multiple times.

        Returns:
            Parsed JSON data as dictionary, list, or other JSON-compatible type.

        Raises:
            ValueError: If the response content is not valid JSON or if parsing fails.

        Note:
            - Uses lazy parsing: JSON is only parsed when first accessed
            - Subsequent calls return cached result for better performance
            - If JSON was pre-parsed during initialization, that result is returned
        """
        if self._json is not None:
            return self._json

        try:
            self._json = jsonlib.loads(self.text)
            return self._json
        except jsonlib.JSONDecodeError as exc:
            logger.debug('Failed to decode response as JSON')
            raise ValueError('Response is not valid JSON') from exc

    def raise_for_status(self) -> None:
        """Raise an HTTPError if the response indicates an HTTP error status.

        Checks the status code and raises an exception for client errors (4xx)
        and server errors (5xx). Successful responses (2xx) and redirects (3xx)
        do not raise an exception.

        Raises:
            HTTPError: If status code is 400 or higher, indicating an error.

        Note:
            This method is compatible with requests.Response.raise_for_status()
            for easy migration from the requests library.
        """
        if self.status_code not in STATUS_CODE_RANGE_OK:
            logger.error(
                f'HTTP error status encountered: status={self.status_code}, url={self._url}'
            )
            raise HTTPError(f'{self.status_code} Client Error: for url {self._url}')
