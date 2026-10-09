"""BiDi HAR recorder: builds HAR entries from WebDriver BiDi network events.

Correlates beforeRequestSent / responseCompleted / fetchError by request id and
retrieves response bodies through a data collector (network.addDataCollector +
network.getData), since BiDi has no getResponseBody. The protocol-agnostic HAR
assembly and HarCapture live in pydoll.browser.requests.har.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from pydoll.browser.requests.har import BaseHarRecorder
from pydoll.commands.bidi.network_commands import NetworkCommands
from pydoll.protocol.bidi.network.types import DataType
from pydoll.protocol.events import Event
from pydoll.protocol.har_types import HarTimings

if TYPE_CHECKING:
    from pydoll.browser.firefox.tab import BiDiTab

logger = logging.getLogger(__name__)

_MAX_COLLECTED_BYTES = 50_000_000


class BiDiHarRecorder(BaseHarRecorder['BiDiTab']):
    """Listens to BiDi network events and builds HAR 1.2 entries.

    Not intended for direct use — ``tab.request.record()`` wraps this engine.
    """

    def __init__(self, tab: BiDiTab, resource_types: list[str] | None = None):
        super().__init__(tab, frozenset(resource_types) if resource_types else None)
        self._collector_id: str | None = None

    async def start(self) -> None:
        """Add a response data collector and subscribe to BiDi network events."""
        response = await self._tab._execute_command(
            NetworkCommands.add_data_collector(
                data_types=[DataType.RESPONSE],
                max_encoded_data_size=_MAX_COLLECTED_BYTES,
            )
        )
        self._collector_id = response['result']['collector']
        self._start_time = datetime.now(tz=timezone.utc)

        self._callback_ids = [
            await self._tab.on(Event.REQUEST_SENT, self._on_before_request_sent),
            await self._tab.on(Event.RESPONSE_COMPLETED, self._on_response_completed),
            await self._tab.on(Event.FETCH_ERROR, self._on_fetch_error),
        ]
        logger.info('BiDi HAR recorder started (collector=%s)', self._collector_id)

    async def _teardown(self) -> None:
        """Remove the data collector created for this recording."""
        if self._collector_id:
            try:
                await self._tab._execute_command(
                    NetworkCommands.remove_data_collector(collector=self._collector_id)
                )
            except Exception:
                logger.debug('BiDi HAR: failed to remove data collector %s', self._collector_id)
            self._collector_id = None

    def _on_before_request_sent(self, event: dict) -> None:
        """Handle network.beforeRequestSent: open a pending entry."""
        params = event['params']
        request = params.get('request', {})
        request_id = request.get('request', '')
        if not request_id:
            return
        self._pending[request_id] = {
            'url': request.get('url', ''),
            'method': request.get('method', 'GET'),
            'request_headers': self._headers_to_dict(request.get('headers', [])),
            'post_data': None,
            'wall_time': params.get('timestamp', 0) / 1000,
            'timing': request.get('timings'),
            'resource_type': request.get('initiatorType') or request.get('destination') or '',
        }

    def _on_response_completed(self, event: dict) -> None:
        """Handle network.responseCompleted: fill the response and finalize."""
        params = event['params']
        request = params.get('request', {})
        request_id = request.get('request', '')
        pending = self._pending.get(request_id)
        if not pending:
            return
        response = params.get('response', {})
        pending['status'] = response.get('status', 0)
        pending['status_text'] = response.get('statusText', '')
        pending['response_headers'] = self._headers_to_dict(response.get('headers', []))
        pending['mime_type'] = response.get('mimeType', '')
        pending['protocol'] = response.get('protocol', '')
        body_size = response.get('bodySize')
        pending['body_bytes'] = body_size if isinstance(body_size, int) else -1
        if request.get('timings'):
            pending['timing'] = request['timings']

        task = asyncio.create_task(self._finalize_entry(request_id))
        self._body_tasks.append(task)
        task.add_done_callback(
            lambda t: self._body_tasks.remove(t) if t in self._body_tasks else None
        )

    def _on_fetch_error(self, event: dict) -> None:
        """Handle network.fetchError: record a failed entry."""
        params = event['params']
        request = params.get('request', {})
        pending = self._pending.pop(request.get('request', ''), None)
        if not pending:
            return
        pending.setdefault('status', 0)
        pending.setdefault('status_text', params.get('errorText', 'Failed'))
        pending['error_text'] = params.get('errorText', '')
        self._entries.append(self._build_entry(pending))

    async def _finalize_entry(self, request_id: str) -> None:
        """Fetch the response body via the collector and build the HAR entry."""
        pending = self._pending.pop(request_id, None)
        if not pending:
            return
        body, is_base64 = await self._fetch_response_body(request_id)
        pending['response_body'] = body
        pending['response_body_base64'] = is_base64
        self._entries.append(self._build_entry(pending))

    async def _fetch_response_body(self, request_id: str) -> tuple[str, bool]:
        """Retrieve the response body via network.getData (('', False) on failure)."""
        if not self._collector_id:
            return '', False
        try:
            data = await self._tab._execute_command(
                NetworkCommands.get_data(
                    data_type=DataType.RESPONSE,
                    request=request_id,
                    collector=self._collector_id,
                )
            )
            bytes_value = data['result']['bytes']
            value = bytes_value.get('value', '')
            return (value if isinstance(value, str) else ''), bytes_value.get('type') == 'base64'
        except Exception:
            logger.debug('BiDi HAR: failed to fetch response body for %s', request_id)
            return '', False

    def _build_har_timings(self, pending: dict[str, Any]) -> HarTimings:  # noqa: PLR6301
        """Convert BiDi FetchTimingInfo (absolute epoch ms) to HAR timings (ms)."""
        timing = pending.get('timing') or {}
        if not timing:
            return HarTimings(blocked=-1, dns=-1, connect=-1, ssl=-1, send=0, wait=0, receive=0)

        def _phase(start_key: str, end_key: str) -> float:
            start = timing.get(start_key, 0)
            end = timing.get(end_key, 0)
            return round(end - start, 3) if start > 0 and end >= start else -1

        blocked = _phase('requestTime', 'fetchStart')
        send = _phase('connectEnd', 'requestStart')
        wait = _phase('requestStart', 'responseStart')
        receive = _phase('responseStart', 'responseEnd')
        return HarTimings(
            blocked=blocked,
            dns=_phase('dnsStart', 'dnsEnd'),
            connect=_phase('connectStart', 'connectEnd'),
            ssl=_phase('tlsStart', 'tlsEnd'),
            send=max(send, 0),
            wait=wait if wait > 0 else 0,
            receive=receive if receive > 0 else 0,
        )

    @staticmethod
    def _headers_to_dict(headers: list[dict]) -> dict[str, str]:
        """Flatten a BiDi header list (unwrapping BytesValue) into a dict.

        Duplicate names are newline-joined so the shared Set-Cookie parser (which
        splits on newlines) sees every cookie.
        """
        result: dict[str, str] = {}
        for header in headers:
            name = header.get('name', '')
            value = header.get('value')
            if isinstance(value, dict):
                value = value.get('value', '')
            value = value if isinstance(value, str) else ''
            result[name] = f'{result[name]}\n{value}' if name in result else value
        return result
