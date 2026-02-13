"""HAR network recorder for capturing and replaying browser network traffic.

This module provides the internal recording engine (HarRecorder) and the
user-facing recording object (HarCapture) that together enable HAR 1.2
capture and export from browser sessions.
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
from datetime import datetime, timezone
from importlib.metadata import version as _pkg_version
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, cast
from urllib.parse import parse_qs, urlparse

from pydoll.commands.network_commands import NetworkCommands
from pydoll.protocol.network.events import (
    DataReceivedEvent,
    LoadingFailedEvent,
    LoadingFinishedEvent,
    NetworkEvent,
    RequestWillBeSentEvent,
    RequestWillBeSentExtraInfoEvent,
    ResponseReceivedEvent,
    ResponseReceivedExtraInfoEvent,
)
from pydoll.protocol.network.har_types import (
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
from pydoll.protocol.network.types import ResourceType

if TYPE_CHECKING:
    from pydoll.browser.tab import Tab
    from pydoll.protocol.network.methods import GetResponseBodyResponse
    from pydoll.protocol.network.types import ResourceTiming
    from pydoll.protocol.network.types import Response as CDPResponse

logger = logging.getLogger(__name__)

_PYDOLL_CREATOR_NAME = 'pydoll'
_HTTP_NOT_MODIFIED = 304


def _get_pydoll_version() -> str:
    """Get the installed pydoll version."""
    try:
        return _pkg_version('pydoll')
    except Exception:
        return 'unknown'


class HarRecorder:
    """Internal engine that listens to CDP network events and builds HAR entries.

    This class registers callbacks for 6 CDP Network events, correlates them
    by requestId, and builds HAR 1.2 entries. It is not intended for direct
    use — instead, use ``tab.request.record()`` which wraps this engine.
    """

    def __init__(self, tab: Tab, resource_types: list[ResourceType] | None = None):
        self._tab = tab
        self._resource_types = frozenset(resource_types) if resource_types else None
        self._callback_ids: list[int] = []
        self._pending: dict[str, dict[str, Any]] = {}
        self._entries: list[HarEntry] = []
        self._start_time: datetime | None = None
        self._network_was_enabled: bool = False
        self._body_tasks: list[asyncio.Task] = []
        self._data_received_sizes: dict[str, int] = {}

    async def start(self) -> None:
        """Start recording network traffic.

        Enables network events if not already on, and registers callbacks
        for the 6 CDP events needed to build HAR entries.
        """
        if not self._tab.network_events_enabled:
            await self._tab.enable_network_events()
            self._network_was_enabled = True
            logger.debug('HAR recorder enabled network events')

        self._start_time = datetime.now(tz=timezone.utc)

        _cb = Callable[[dict], Any]
        events_and_handlers: list[tuple[str, _cb]] = [
            (NetworkEvent.REQUEST_WILL_BE_SENT, cast(_cb, self._on_request_will_be_sent)),
            (NetworkEvent.REQUEST_WILL_BE_SENT_EXTRA_INFO, cast(_cb, self._on_request_extra_info)),
            (NetworkEvent.RESPONSE_RECEIVED, cast(_cb, self._on_response_received)),
            (NetworkEvent.RESPONSE_RECEIVED_EXTRA_INFO, cast(_cb, self._on_response_extra_info)),
            (NetworkEvent.DATA_RECEIVED, cast(_cb, self._on_data_received)),
            (NetworkEvent.LOADING_FINISHED, cast(_cb, self._on_loading_finished)),
            (NetworkEvent.LOADING_FAILED, cast(_cb, self._on_loading_failed)),
        ]

        for event_name, handler in events_and_handlers:
            callback_id = await self._tab.on(event_name, handler)
            self._callback_ids.append(callback_id)

        logger.info('HAR recorder started, registered %d callbacks', len(self._callback_ids))

    async def stop(self) -> None:
        """Stop recording and clean up.

        Removes all registered callbacks, waits for pending body fetches,
        flushes pending entries, and optionally disables network events.
        """
        for callback_id in self._callback_ids:
            await self._tab.remove_callback(callback_id)
        self._callback_ids.clear()

        if self._body_tasks:
            await asyncio.gather(*self._body_tasks, return_exceptions=True)
            self._body_tasks.clear()

        self._flush_pending()

        if self._network_was_enabled:
            await self._tab.disable_network_events()
            self._network_was_enabled = False

        logger.info('HAR recorder stopped, captured %d entries', len(self._entries))

    def _on_request_will_be_sent(self, event: RequestWillBeSentEvent) -> None:
        """Handle Network.requestWillBeSent event."""
        params = event['params']
        request_id = params['requestId']
        request_data = params['request']
        resource_type = params.get('type', '')
        redirect_response = params.get('redirectResponse')

        if self._resource_types and resource_type not in self._resource_types:
            return

        if redirect_response and request_id in self._pending:
            self._finalize_redirect_entry(request_id, redirect_response)

        self._pending[request_id] = {
            'url': request_data.get('url', ''),
            'method': request_data.get('method', 'GET'),
            'request_headers': request_data.get('headers', {}),
            'post_data': request_data.get('postData'),
            'wall_time': params['wallTime'],
            'resource_type': params.get('type', ''),
            'timestamp': params['timestamp'],
        }
        logger.debug('HAR: request will be sent: %s %s', request_id, request_data.get('url', ''))

    def _on_request_extra_info(self, event: RequestWillBeSentExtraInfoEvent) -> None:
        """Handle Network.requestWillBeSentExtraInfo event."""
        params = event['params']
        request_id = params['requestId']
        pending = self._pending.get(request_id)
        if not pending:
            return

        extra_headers = params.get('headers', {})
        if extra_headers:
            pending['request_headers_extra'] = extra_headers
        logger.debug('HAR: request extra info: %s', request_id)

    def _on_response_received(self, event: ResponseReceivedEvent) -> None:
        """Handle Network.responseReceived event."""
        params = event['params']
        request_id = params['requestId']
        pending = self._pending.get(request_id)
        if not pending:
            return

        response = params['response']
        pending['status'] = response['status']
        pending['status_text'] = response['statusText']
        pending['response_headers'] = response.get('headers', {})
        pending['mime_type'] = response['mimeType']
        pending['protocol'] = response.get('protocol', '')
        pending['timing'] = response.get('timing')
        pending['remote_ip'] = response.get('remoteIPAddress', '')
        pending['connection_id'] = str(response.get('connectionId', ''))
        pending['encoded_data_length'] = response.get('encodedDataLength', 0)
        pending['response_timestamp'] = params['timestamp']
        logger.debug('HAR: response received: %s status=%s', request_id, response['status'])

    def _on_response_extra_info(self, event: ResponseReceivedExtraInfoEvent) -> None:
        """Handle Network.responseReceivedExtraInfo event."""
        params = event['params']
        request_id = params['requestId']
        pending = self._pending.get(request_id)
        if not pending:
            return

        extra_headers = params.get('headers', {})
        if extra_headers:
            pending['response_headers_extra'] = extra_headers
        status_code = params.get('statusCode')
        if status_code is not None:
            pending['extra_status_code'] = status_code
        logger.debug('HAR: response extra info: %s', request_id)

    def _on_data_received(self, event: DataReceivedEvent) -> None:
        """Handle Network.dataReceived event.

        Accumulates body chunk bytes per requestId for accurate bodySize.
        """
        params = event['params']
        request_id = params['requestId']
        chunk_size = params['encodedDataLength']
        self._data_received_sizes[request_id] = (
            self._data_received_sizes.get(request_id, 0) + chunk_size
        )

    def _on_loading_finished(self, event: LoadingFinishedEvent) -> None:
        """Handle Network.loadingFinished event."""
        params = event['params']
        request_id = params['requestId']
        pending = self._pending.get(request_id)
        if not pending:
            return

        pending['transfer_size'] = params['encodedDataLength']
        pending['finished_timestamp'] = params['timestamp']
        pending['body_bytes'] = self._data_received_sizes.pop(request_id, -1)

        task = asyncio.create_task(self._finalize_entry(request_id))
        self._body_tasks.append(task)
        task.add_done_callback(
            lambda t: self._body_tasks.remove(t) if t in self._body_tasks else None
        )
        logger.debug('HAR: loading finished: %s', request_id)

    def _on_loading_failed(self, event: LoadingFailedEvent) -> None:
        """Handle Network.loadingFailed event."""
        params = event['params']
        request_id = params['requestId']
        pending = self._pending.pop(request_id, None)
        if not pending:
            return

        self._data_received_sizes.pop(request_id, None)
        pending.setdefault('status', 0)
        pending.setdefault('status_text', params.get('errorText', 'Failed'))
        pending['error_text'] = params['errorText']
        pending['canceled'] = params.get('canceled', False)

        entry = self._build_entry(pending)
        self._entries.append(entry)
        logger.debug('HAR: loading failed: %s error=%s', request_id, params.get('errorText'))

    async def _finalize_entry(self, request_id: str) -> None:
        """Fetch response body and build the final HAR entry."""
        pending = self._pending.pop(request_id, None)
        if not pending:
            return

        body, base64_encoded = await self._fetch_response_body(request_id)
        pending['response_body'] = body
        pending['response_body_base64'] = base64_encoded

        entry = self._build_entry(pending)
        self._entries.append(entry)

    def _finalize_redirect_entry(self, request_id: str, redirect_response: CDPResponse) -> None:
        """Finalize a redirect entry before starting a new pending entry."""
        pending = self._pending.pop(request_id, None)
        if not pending:
            return
        pending['body_bytes'] = self._data_received_sizes.pop(request_id, -1)

        pending['status'] = redirect_response.get('status', 302)
        pending['status_text'] = redirect_response.get('statusText', '')
        pending['response_headers'] = redirect_response.get('headers', {})
        pending['mime_type'] = redirect_response.get('mimeType', '')
        pending['protocol'] = redirect_response.get('protocol', '')
        pending['timing'] = redirect_response.get('timing')

        entry = self._build_entry(pending)
        self._entries.append(entry)
        logger.debug(
            'HAR: redirect finalized: %s → %s', request_id, redirect_response.get('status')
        )

    def _flush_pending(self) -> None:
        """Convert remaining pending entries (requests with no response) into HAR entries."""
        for request_id in list(self._pending.keys()):
            pending = self._pending.pop(request_id)
            pending.setdefault('status', 0)
            pending.setdefault('status_text', '(pending)')
            entry = self._build_entry(pending)
            self._entries.append(entry)
        logger.debug('HAR: flushed pending entries')

    async def _fetch_response_body(self, request_id: str) -> tuple[str, bool]:
        """Fetch the response body via Network.getResponseBody.

        Returns:
            Tuple of (body_text, is_base64_encoded). Returns ('', False) on failure.
        """
        try:
            command = NetworkCommands.get_response_body(request_id)
            response: GetResponseBodyResponse = await self._tab._execute_command(command)
            body_result = response['result']
            return body_result['body'], body_result['base64Encoded']
        except Exception:
            logger.debug('HAR: failed to fetch response body for %s', request_id)
            return '', False

    def _build_entry(self, pending: dict[str, Any]) -> HarEntry:
        """Build a HAR entry from accumulated pending data."""
        req_hdrs = pending.get('request_headers_extra') or pending.get('request_headers', {})
        resp_hdrs = pending.get('response_headers_extra') or pending.get('response_headers', {})
        url = pending.get('url', '')
        protocol = self._normalize_http_version(pending.get('protocol', ''))
        post_data_text = pending.get('post_data')

        har_request = self._build_har_request(url, pending, req_hdrs, protocol, post_data_text)
        har_response = self._build_har_response(pending, resp_hdrs, protocol)

        response_ts: float = pending.get('response_timestamp', 0)
        finished_ts: float = pending.get('finished_timestamp', 0)
        receive_ms: float | None = None
        if response_ts and finished_ts and finished_ts > response_ts:
            receive_ms = (finished_ts - response_ts) * 1000

        har_timings = self._build_har_timings(pending.get('timing'), receive_ms)
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
        req_cookies = self._parse_request_cookies(headers)
        har_request = HarRequest(
            method=pending.get('method', 'GET'),
            url=url,
            httpVersion=protocol,
            cookies=req_cookies,
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

        # bodySize from dataReceived chunks (actual body bytes, no header overhead)
        # For 304 (cache hit), bodySize must be 0 per HAR spec
        # When body_bytes is 0 but content exists (e.g. file:// protocol),
        # fall back to content_size for consistency with content.size/text.
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
        resp_cookies = self._parse_response_cookies(headers)
        return HarResponse(
            status=status,
            statusText=pending.get('status_text', ''),
            httpVersion=protocol,
            cookies=resp_cookies,
            headers=self._headers_dict_to_list(headers),
            content=har_content,
            redirectURL=redirect,
            headersSize=-1,
            bodySize=body_size,
        )

    @staticmethod
    def _build_har_timings(
        timing: ResourceTiming | None,
        receive_ms: float | None = None,
    ) -> HarTimings:
        """Convert CDP ResourceTiming to HAR timings (in milliseconds).

        Args:
            timing: CDP ResourceTiming from responseReceived.
            receive_ms: Calculated receive time from monotonic timestamps
                (loadingFinished.timestamp - responseReceived.timestamp).
                When provided, overrides the header-based calculation.
        """
        rcv = round(receive_ms, 3) if receive_ms is not None else 0
        if not timing:
            return HarTimings(
                blocked=-1,
                dns=-1,
                connect=-1,
                ssl=-1,
                send=0,
                wait=0,
                receive=rcv,
            )

        dns_s: float = timing.get('dnsStart', -1)
        dns_e: float = timing.get('dnsEnd', -1)
        con_s: float = timing.get('connectStart', -1)
        con_e: float = timing.get('connectEnd', -1)
        ssl_s: float = timing.get('sslStart', -1)
        ssl_e: float = timing.get('sslEnd', -1)
        snd_s: float = timing.get('sendStart', 0)
        snd_e: float = timing.get('sendEnd', 0)
        rh_s: float = timing.get('receiveHeadersStart', 0)

        def _phase(s: float, e: float) -> float:
            return round(max(e - s, 0), 3) if s >= 0 and e >= 0 else -1

        first = dns_s if dns_s >= 0 else (con_s if con_s >= 0 else snd_s)
        return HarTimings(
            blocked=round(max(first, 0), 3),
            dns=_phase(dns_s, dns_e),
            connect=_phase(con_s, con_e),
            ssl=_phase(ssl_s, ssl_e),
            send=round(max(snd_e - snd_s, 0), 3),
            wait=round(max(rh_s - snd_e, 0), 3),
            receive=rcv,
        )

    @staticmethod
    def _normalize_http_version(protocol: str) -> str:
        """Normalize CDP protocol string to HAR httpVersion format.

        CDP reports protocols like 'h2', 'h3', 'http/1.0', 'http/1.1',
        or non-HTTP strings like 'file'. HAR viewers expect uppercase
        HTTP versions (e.g. 'HTTP/1.1', 'h2', 'h3').
        """
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
        """Convert a CDP headers dict to a HAR headers list."""
        return [HarHeader(name=name, value=value) for name, value in headers.items()]

    @staticmethod
    def _parse_query_string(url: str) -> list[HarQueryParam]:
        """Parse URL query string into HAR query param list."""
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
        """Convert a CDP wallTime (seconds since epoch) to ISO 8601 string."""
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
            attrs = stripped_line.split(';')[1:]
            for raw_attr in attrs:
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
    """User-facing object returned by ``tab.request.record()`` context manager.

    Provides access to recorded HAR entries and methods to export the
    recording as a HAR 1.2 file.
    """

    def __init__(self, recorder: HarRecorder):
        self._recorder = recorder

    @property
    def entries(self) -> list[HarEntry]:
        """Return a sorted copy of the recorded HAR entries."""
        return sorted(self._recorder._entries, key=lambda e: e['startedDateTime'])

    def to_dict(self) -> Har:
        """Build a full HAR 1.2 dictionary from the recorded entries.

        Returns:
            A complete HAR 1.2 dict ready for JSON serialization.
        """
        return Har(
            log=HarLog(
                version='1.2',
                creator=HarCreator(
                    name=_PYDOLL_CREATOR_NAME,
                    version=_get_pydoll_version(),
                ),
                pages=[],
                entries=sorted(
                    self._recorder._entries,
                    key=lambda e: e['startedDateTime'],
                ),
            )
        )

    def save(self, path: str | Path) -> None:
        """Save the recording as a HAR 1.2 JSON file.

        Args:
            path: File path to write the HAR file to.
        """
        har_dict = self.to_dict()
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(har_dict, f, indent=2, ensure_ascii=False)
        logger.info('HAR recording saved to %s (%d entries)', path, len(self._recorder._entries))
