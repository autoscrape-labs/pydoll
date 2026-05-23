"""CDP HAR recorder: builds HAR entries from CDP Network events.

Correlates 7 CDP events by requestId and fetches response bodies via
Network.getResponseBody. The protocol-agnostic HAR assembly and HarCapture live
in pydoll.browser.requests.har.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Callable, cast

from pydoll.browser.requests.har import BaseHarRecorder
from pydoll.commands.cdp.network_commands import NetworkCommands
from pydoll.protocol.cdp.network.events import (
    DataReceivedEvent,
    LoadingFailedEvent,
    LoadingFinishedEvent,
    NetworkEvent,
    RequestWillBeSentEvent,
    RequestWillBeSentExtraInfoEvent,
    ResponseReceivedEvent,
    ResponseReceivedExtraInfoEvent,
)
from pydoll.protocol.cdp.network.types import ResourceType
from pydoll.protocol.har_types import HarTimings

if TYPE_CHECKING:
    from pydoll.browser.chromium.tab import Tab
    from pydoll.protocol.cdp.network.methods import GetResponseBodyResponse
    from pydoll.protocol.cdp.network.types import ResourceTiming
    from pydoll.protocol.cdp.network.types import Response as CDPResponse

logger = logging.getLogger(__name__)


class HarRecorder(BaseHarRecorder['Tab']):
    """Listens to CDP Network events and builds HAR 1.2 entries.

    Not intended for direct use — ``tab.request.record()`` wraps this engine.
    """

    def __init__(self, tab: Tab, resource_types: list[ResourceType] | None = None):
        super().__init__(tab, frozenset(resource_types) if resource_types else None)
        self._network_was_enabled: bool = False
        self._data_received_sizes: dict[str, int] = {}

    async def start(self) -> None:
        """Enable network events (if needed) and register the 7 CDP handlers."""
        if not self._tab._network_events_enabled:
            await self._tab._enable_network_events()
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
            self._callback_ids.append(await self._tab.on(event_name, handler))
        logger.info('HAR recorder started, registered %d callbacks', len(self._callback_ids))

    async def _teardown(self) -> None:
        """Disable network events if this recorder enabled them."""
        if self._network_was_enabled:
            await self._tab._disable_network_events()
            self._network_was_enabled = False

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

    def _on_request_extra_info(self, event: RequestWillBeSentExtraInfoEvent) -> None:
        """Handle Network.requestWillBeSentExtraInfo event."""
        params = event['params']
        pending = self._pending.get(params['requestId'])
        if not pending:
            return
        extra_headers = params.get('headers', {})
        if extra_headers:
            pending['request_headers_extra'] = extra_headers

    def _on_response_received(self, event: ResponseReceivedEvent) -> None:
        """Handle Network.responseReceived event."""
        params = event['params']
        pending = self._pending.get(params['requestId'])
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

    def _on_response_extra_info(self, event: ResponseReceivedExtraInfoEvent) -> None:
        """Handle Network.responseReceivedExtraInfo event."""
        params = event['params']
        pending = self._pending.get(params['requestId'])
        if not pending:
            return
        extra_headers = params.get('headers', {})
        if extra_headers:
            pending['response_headers_extra'] = extra_headers
        status_code = params.get('statusCode')
        if status_code is not None:
            pending['extra_status_code'] = status_code

    def _on_data_received(self, event: DataReceivedEvent) -> None:
        """Accumulate body chunk bytes per requestId for accurate bodySize."""
        params = event['params']
        request_id = params['requestId']
        self._data_received_sizes[request_id] = (
            self._data_received_sizes.get(request_id, 0) + params['encodedDataLength']
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
        self._entries.append(self._build_entry(pending))

    async def _finalize_entry(self, request_id: str) -> None:
        """Fetch the response body and build the final HAR entry."""
        pending = self._pending.pop(request_id, None)
        if not pending:
            return
        body, base64_encoded = await self._fetch_response_body(request_id)
        pending['response_body'] = body
        pending['response_body_base64'] = base64_encoded
        self._entries.append(self._build_entry(pending))

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
        self._entries.append(self._build_entry(pending))

    async def _fetch_response_body(self, request_id: str) -> tuple[str, bool]:
        """Fetch the response body via Network.getResponseBody (('', False) on failure)."""
        try:
            response: GetResponseBodyResponse = await self._tab._execute_command(
                NetworkCommands.get_response_body(request_id)
            )
            body_result = response['result']
            return body_result['body'], body_result['base64Encoded']
        except Exception:
            logger.debug('HAR: failed to fetch response body for %s', request_id)
            return '', False

    def _build_har_timings(self, pending: dict[str, Any]) -> HarTimings:  # noqa: PLR6301
        """Convert CDP ResourceTiming (+ monotonic receive) to HAR timings (ms)."""
        timing: ResourceTiming | None = pending.get('timing')
        response_ts: float = pending.get('response_timestamp', 0)
        finished_ts: float = pending.get('finished_timestamp', 0)
        receive_ms: float | None = None
        if response_ts and finished_ts and finished_ts > response_ts:
            receive_ms = (finished_ts - response_ts) * 1000

        rcv = round(receive_ms, 3) if receive_ms is not None else 0
        if not timing:
            return HarTimings(
                blocked=-1, dns=-1, connect=-1, ssl=-1, send=0, wait=0, receive=rcv
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
