"""Shared HAR recording engine (CDP and BiDi).

Both backends correlate network events into per-request ``pending`` dicts and turn
them into HAR 1.2 entries. This base owns the protocol-agnostic part — assembling
HarEntry/HarRequest/HarResponse, cookie/query/header parsing, and the HarCapture
export object — and delegates the protocol-specific bits (event subscription,
response-body retrieval, and timing extraction) to the CDP and BiDi subclasses.
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from importlib.metadata import version as _pkg_version
from pathlib import Path
from typing import Any, Generic, Optional, Protocol, TypeVar
from urllib.parse import parse_qs, urlparse

from pydoll.protocol.har_types import (
    Har,
    HarContent,
    HarCookie,
    HarCreator,
    HarEntry,
    HarHeader,
    HarLog,
    HarPostData,
    HarQueryParam,
    HarRequest,
    HarResponse,
    HarTimings,
)

logger = logging.getLogger(__name__)

_PYDOLL_CREATOR_NAME = 'pydoll'
_HTTP_NOT_MODIFIED = 304


def _get_pydoll_version() -> str:
    """Get the installed pydoll version."""
    try:
        return _pkg_version('pydoll')
    except Exception:
        return 'unknown'


class _HarTab(Protocol):
    """Minimal tab surface the base recorder needs (both backends satisfy it)."""

    async def remove_callback(self, callback_id: int) -> None: ...


T_Tab = TypeVar('T_Tab', bound=_HarTab)


class BaseHarRecorder(ABC, Generic[T_Tab]):
    """Builds HAR 1.2 entries from network events. Subclasses bind the protocol.

    Not used directly — ``tab.request.record()`` wraps a concrete recorder in a
    HarCapture.
    """

    def __init__(self, tab: T_Tab, resource_types: Optional[frozenset[str]] = None):
        self._tab = tab
        self._resource_types = resource_types
        self._callback_ids: list[int] = []
        self._pending: dict[str, dict[str, Any]] = {}
        self._entries: list[HarEntry] = []
        self._start_time: datetime | None = None
        self._body_tasks: list[asyncio.Task] = []

    @abstractmethod
    async def start(self) -> None:
        """Subscribe to the protocol's network events and begin recording."""

    async def stop(self) -> None:
        """Stop recording: remove listeners, await body fetches, flush, tear down."""
        for callback_id in self._callback_ids:
            await self._tab.remove_callback(callback_id)
        self._callback_ids.clear()

        if self._body_tasks:
            await asyncio.gather(*self._body_tasks, return_exceptions=True)
            self._body_tasks.clear()

        self._flush_pending()
        await self._teardown()
        logger.info('HAR recorder stopped, captured %d entries', len(self._entries))

    @abstractmethod
    async def _teardown(self) -> None:
        """Release protocol resources (network events / data collectors)."""

    @abstractmethod
    def _build_har_timings(self, pending: dict[str, Any]) -> HarTimings:
        """Build HAR timings from the protocol's timing data in pending."""

    def _flush_pending(self) -> None:
        """Convert leftover pending requests (no response) into HAR entries."""
        for request_id in list(self._pending.keys()):
            pending = self._pending.pop(request_id)
            pending.setdefault('status', 0)
            pending.setdefault('status_text', '(pending)')
            self._entries.append(self._build_entry(pending))

    def _build_entry(self, pending: dict[str, Any]) -> HarEntry:
        """Build a HAR entry from accumulated pending data."""
        req_hdrs = pending.get('request_headers_extra') or pending.get('request_headers', {})
        resp_hdrs = pending.get('response_headers_extra') or pending.get('response_headers', {})
        url = pending.get('url', '')
        protocol = self._normalize_http_version(pending.get('protocol', ''))
        post_data_text = pending.get('post_data')

        har_request = self._build_har_request(url, pending, req_hdrs, protocol, post_data_text)
        har_response = self._build_har_response(pending, resp_hdrs, protocol)
        har_timings = self._build_har_timings(pending)

        # Sum without ssl — connect already includes it per HAR 1.2 spec
        _phases = (
            har_timings['blocked'],
            har_timings['dns'],
            har_timings['connect'],
            har_timings['send'],
            har_timings['wait'],
            har_timings['receive'],
        )
        total_time = sum(v for v in _phases if v > 0)

        entry = HarEntry(
            startedDateTime=self._wall_time_to_iso(pending.get('wall_time', 0)),
            time=round(total_time, 2),
            request=har_request,
            response=har_response,
            cache={},
            timings=har_timings,
        )

        for key, field in [
            ('remote_ip', 'serverIPAddress'),
            ('connection_id', 'connection'),
            ('resource_type', '_resourceType'),
        ]:
            if pending.get(key, ''):
                entry[field] = pending[key]  # type: ignore[literal-required]

        return entry

    def _build_har_request(
        self,
        url: str,
        pending: dict[str, Any],
        headers: dict[str, str],
        protocol: str,
        post_data_text: str | None,
    ) -> HarRequest:
        """Build the HarRequest portion of an entry."""
        har_request = HarRequest(
            method=pending.get('method', 'GET'),
            url=url,
            httpVersion=protocol,
            cookies=self._parse_request_cookies(headers),
            headers=self._headers_dict_to_list(headers),
            queryString=self._parse_query_string(url),
            headersSize=-1,
            bodySize=len(post_data_text.encode('utf-8')) if post_data_text else 0,
        )
        if post_data_text:
            ct = headers.get('Content-Type', headers.get('content-type', ''))
            har_request['postData'] = HarPostData(mimeType=ct, text=post_data_text)
        return har_request

    def _build_har_response(
        self,
        pending: dict[str, Any],
        headers: dict[str, str],
        protocol: str,
    ) -> HarResponse:
        """Build the HarResponse portion of an entry."""
        body = pending.get('response_body', '')
        is_base64 = pending.get('response_body_base64', False)
        status = pending.get('extra_status_code', pending.get('status', 0))

        if body and is_base64:
            try:
                content_size = len(base64.b64decode(body))
            except Exception:
                content_size = len(body)
        elif body:
            content_size = len(body.encode('utf-8'))
        else:
            content_size = 0

        har_content = HarContent(size=content_size, mimeType=pending.get('mime_type', ''))
        if body:
            har_content['text'] = body
            if is_base64:
                har_content['encoding'] = 'base64'

        body_bytes = pending.get('body_bytes', -1)
        if status == _HTTP_NOT_MODIFIED:
            body_size = 0
        elif body_bytes > 0:
            body_size = body_bytes
        elif content_size > 0:
            body_size = content_size
        else:
            body_size = -1

        redirect = headers.get('Location', headers.get('location', ''))
        return HarResponse(
            status=status,
            statusText=pending.get('status_text', ''),
            httpVersion=protocol,
            cookies=self._parse_response_cookies(headers),
            headers=self._headers_dict_to_list(headers),
            content=har_content,
            redirectURL=redirect,
            headersSize=-1,
            bodySize=body_size,
        )

    @staticmethod
    def _normalize_http_version(protocol: str) -> str:
        """Normalize a protocol string to HAR httpVersion format."""
        if not protocol:
            return ''
        lower = protocol.lower()
        if lower in {'h2', 'h3', 'h2c'}:
            return lower
        if lower.startswith('http/'):
            return protocol.upper()
        return ''

    @staticmethod
    def _headers_dict_to_list(headers: dict[str, str]) -> list[HarHeader]:
        """Convert a headers dict to a HAR headers list."""
        return [HarHeader(name=name, value=value) for name, value in headers.items()]

    @staticmethod
    def _parse_query_string(url: str) -> list[HarQueryParam]:
        """Parse a URL query string into a HAR query param list."""
        parsed = urlparse(url)
        if not parsed.query:
            return []
        params = parse_qs(parsed.query, keep_blank_values=True)
        result: list[HarQueryParam] = []
        for name, values in params.items():
            for value in values:
                result.append(HarQueryParam(name=name, value=value))
        return result

    @staticmethod
    def _wall_time_to_iso(wall_time: float) -> str:
        """Convert an epoch-seconds wall time to an ISO 8601 string."""
        if not wall_time:
            return datetime.now(tz=timezone.utc).isoformat()
        return datetime.fromtimestamp(wall_time, tz=timezone.utc).isoformat()

    @staticmethod
    def _parse_request_cookies(headers: dict[str, str]) -> list[HarCookie]:
        """Parse request cookies from the Cookie header."""
        cookie_header = headers.get('Cookie', headers.get('cookie', ''))
        if not cookie_header:
            return []
        cookies: list[HarCookie] = []
        for raw_pair in cookie_header.split(';'):
            stripped = raw_pair.strip()
            if '=' not in stripped:
                continue
            name, value = stripped.split('=', 1)
            name = name.strip()
            if name:
                cookies.append(HarCookie(name=name, value=value.strip()))
        return cookies

    @staticmethod
    def _parse_response_cookies(headers: dict[str, str]) -> list[HarCookie]:
        """Parse response cookies from Set-Cookie headers."""
        set_cookie = headers.get('Set-Cookie', headers.get('set-cookie', ''))
        if not set_cookie:
            return []
        cookies: list[HarCookie] = []
        for raw_line in set_cookie.split('\n'):
            stripped_line = raw_line.strip()
            if '=' not in stripped_line:
                continue
            name_value = stripped_line.split(';', 1)[0]
            name, value = name_value.split('=', 1)
            name = name.strip()
            if not name:
                continue
            cookie = HarCookie(name=name, value=value.strip())
            for raw_attr in stripped_line.split(';')[1:]:
                attr_lower = raw_attr.strip().lower()
                if attr_lower == 'httponly':
                    cookie['httpOnly'] = True
                elif attr_lower == 'secure':
                    cookie['secure'] = True
                elif attr_lower.startswith('path='):
                    cookie['path'] = attr_lower.split('=', 1)[1]
                elif attr_lower.startswith('domain='):
                    cookie['domain'] = attr_lower.split('=', 1)[1]
            cookies.append(cookie)
        return cookies


class HarCapture:
    """User-facing object returned by ``tab.request.record()``.

    Provides access to recorded HAR entries and export to a HAR 1.2 file.
    """

    def __init__(self, recorder: BaseHarRecorder):
        self._recorder = recorder

    @property
    def entries(self) -> list[HarEntry]:
        """Return a sorted copy of the recorded HAR entries."""
        return sorted(self._recorder._entries, key=lambda e: e['startedDateTime'])

    def to_dict(self) -> Har:
        """Build a full HAR 1.2 dictionary from the recorded entries."""
        return Har(
            log=HarLog(
                version='1.2',
                creator=HarCreator(name=_PYDOLL_CREATOR_NAME, version=_get_pydoll_version()),
                pages=[],
                entries=sorted(self._recorder._entries, key=lambda e: e['startedDateTime']),
            )
        )

    def save(self, path: str | Path) -> None:
        """Save the recording as a HAR 1.2 JSON file."""
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        logger.info('HAR recording saved to %s (%d entries)', path, len(self._recorder._entries))
