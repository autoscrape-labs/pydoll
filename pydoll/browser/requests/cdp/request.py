"""CDP-backed HTTP client: runs the page's fetch and captures request/response
metadata from CDP Network events (including the Set-Cookie that JS cannot read).
"""

from __future__ import annotations

import json as jsonlib
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any, Callable, Union, cast

from pydoll.browser.requests.base import BaseRequest
from pydoll.browser.requests.cdp.har_recorder import HarCapture, HarRecorder
from pydoll.commands.cdp.runtime_commands import RuntimeCommands
from pydoll.constants import Scripts
from pydoll.protocol.cdp.network.events import (
    NetworkEvent,
    RequestWillBeSentEvent,
    RequestWillBeSentExtraInfoEvent,
    ResponseReceivedEvent,
    ResponseReceivedExtraInfoEvent,
    ResponseReceivedExtraInfoEventParams,
)
from pydoll.protocol.cdp.network.types import ResourceType
from pydoll.protocol.types import Header, ResponseCookie

logger = logging.getLogger(__name__)

RequestReceivedEvent = Union[
    ResponseReceivedEvent,
    ResponseReceivedExtraInfoEvent,
]
RequestSentEvent = Union[
    RequestWillBeSentEvent,
    RequestWillBeSentExtraInfoEvent,
]

if TYPE_CHECKING:
    from pydoll.browser.chromium.tab import Tab
    from pydoll.protocol.cdp.network.events import (
        RequestWillBeSentEventParams,
        RequestWillBeSentExtraInfoEventParams,
        ResponseReceivedEventParams,
    )

    RequestReceivedEventParams = Union[
        ResponseReceivedEventParams,
        ResponseReceivedExtraInfoEventParams,
    ]
    RequestSentEventParams = Union[
        RequestWillBeSentEventParams,
        RequestWillBeSentExtraInfoEventParams,
    ]


class Request(BaseRequest['Tab']):
    """HTTP client over CDP. See BaseRequest for the public API.

    Captures both phases of network activity via CDP Network events: request
    headers from requestWillBeSent(ExtraInfo) and response headers + Set-Cookie
    from responseReceived(ExtraInfo).
    """

    def __init__(self, tab: Tab):
        """Initialize a request helper bound to a CDP tab.

        Args:
            tab: The tab providing the JS execution context and session state.
        """
        super().__init__(tab)
        self._network_events_enabled = False
        self._requests_sent: list[RequestSentEvent] = []
        self._requests_received: list[RequestReceivedEvent] = []

    @asynccontextmanager
    async def record(
        self,
        resource_types: list[ResourceType] | None = None,
    ) -> AsyncIterator[HarCapture]:
        """Record network traffic as HAR.

        Args:
            resource_types: Resource types to capture (all when None).

        Usage::

            async with tab.request.record() as capture:
                await tab.go_to('https://example.com')
            capture.save('flow.har')

        Yields:
            HarCapture: Object with .save(), .to_dict(), and .entries.
        """
        recorder = HarRecorder(self.tab, resource_types=resource_types)
        capture = HarCapture(recorder)
        await recorder.start()
        try:
            yield capture
        finally:
            await recorder.stop()

    async def _execute_fetch_request(
        self, url: str, options: dict[str, Any]
    ) -> dict[str, Any]:
        """Run the fetch via Runtime.evaluate and return its result value dict."""
        script = Scripts.MAKE_REQUEST.format(
            url=jsonlib.dumps(url), options=jsonlib.dumps(options)
        )
        result = await self.tab._execute_command(
            RuntimeCommands.evaluate(
                expression=script,
                return_by_value=True,
                await_promise=True,
            )
        )
        return result['result']['result']['value']

    async def _register_callbacks(self) -> None:
        """Capture request/response metadata via CDP Network events."""
        if not self.tab._network_events_enabled:
            await self.tab._enable_network_events()
            self._network_events_enabled = True

        def append_received_request(event: dict) -> None:
            self._requests_received.append(cast(RequestReceivedEvent, event))

        def append_sent_request(event: dict) -> None:
            self._requests_sent.append(cast(RequestSentEvent, event))

        self._callback_ids = [
            await self.tab.on(NetworkEvent.REQUEST_WILL_BE_SENT, callback=append_sent_request),
            await self.tab.on(
                NetworkEvent.REQUEST_WILL_BE_SENT_EXTRA_INFO, callback=append_sent_request
            ),
            await self.tab.on(NetworkEvent.RESPONSE_RECEIVED, callback=append_received_request),
            await self.tab.on(
                NetworkEvent.RESPONSE_RECEIVED_EXTRA_INFO, callback=append_received_request
            ),
        ]

    async def _clear_callbacks(self) -> None:
        """Remove this request's listeners and disable network events if we enabled them."""
        for callback_id in self._callback_ids:
            await self.tab.remove_callback(callback_id)
        self._callback_ids.clear()
        if self._network_events_enabled:
            await self.tab._disable_network_events()
            self._network_events_enabled = False

    def _extract_received_headers(self) -> list[Header]:
        """Extract headers from response network events."""
        event_extractors: dict[str, Callable[[Any], list[Header]]] = {
            'response': self._extract_response_received_headers,
            'blockedCookies': self._extract_response_received_extra_info_headers,
        }
        return self._extract_headers_from_events(self._requests_received, event_extractors)

    def _extract_sent_headers(self) -> list[Header]:
        """Extract headers from request network events."""
        event_extractors: dict[str, Callable[[Any], list[Header]]] = {
            'request': self._extract_request_sent_headers,
            'associatedCookies': self._extract_request_sent_extra_info_headers,
        }
        return self._extract_headers_from_events(self._requests_sent, event_extractors)

    @staticmethod
    def _extract_headers_from_events(
        events: Union[list[RequestSentEvent], list[RequestReceivedEvent]],
        event_extractors: dict[str, Callable[[Any], list[Header]]],
    ) -> list[Header]:
        """Extract and de-duplicate headers from network events."""
        headers: list[Header] = []
        seen = set()
        for event in events:
            params = event['params']
            for key, extractor in event_extractors.items():
                if key in params:
                    for header in extractor(params):
                        identity = (header['name'], header['value'])
                        if identity not in seen:
                            headers.append(header)
                            seen.add(identity)
                    break
        return headers

    def _extract_request_sent_headers(
        self, params: RequestWillBeSentEventParams
    ) -> list[Header]:
        """Headers from the main request event."""
        return self._convert_dict_to_header_entries(params['request'].get('headers', {}))

    def _extract_request_sent_extra_info_headers(
        self, params: RequestWillBeSentExtraInfoEventParams
    ) -> list[Header]:
        """Headers from the extra request info event."""
        return self._convert_dict_to_header_entries(params.get('headers', {}))

    def _extract_response_received_headers(
        self, params: ResponseReceivedEventParams
    ) -> list[Header]:
        """Headers from the main response event."""
        return self._convert_dict_to_header_entries(params['response'].get('headers', {}))

    def _extract_response_received_extra_info_headers(
        self, params: ResponseReceivedExtraInfoEventParams
    ) -> list[Header]:
        """Headers from the extra response info event (includes Set-Cookie)."""
        return self._convert_dict_to_header_entries(params.get('headers', {}))

    def _extract_set_cookies(self) -> list[ResponseCookie]:
        """Extract cookies from Set-Cookie headers in response extra-info events."""
        cookies: list[ResponseCookie] = []
        for event in self._filter_response_extra_info_events():
            params = cast(ResponseReceivedExtraInfoEventParams, event['params'])
            headers = self._convert_dict_to_header_entries(params['headers'])
            set_cookie_headers = [
                header['value'] for header in headers if header['name'] == 'Set-Cookie'
            ]
            for set_cookie_header in set_cookie_headers:
                self._add_unique_cookies(cookies, self._parse_set_cookie_header(set_cookie_header))
        return cookies

    def _filter_response_extra_info_events(self) -> list[RequestReceivedEvent]:
        """Response events that carry Set-Cookie information."""
        return [
            event
            for event in self._requests_received
            if event['method'] == NetworkEvent.RESPONSE_RECEIVED_EXTRA_INFO
        ]
