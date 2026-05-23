"""WebDriver BiDi-backed HTTP client: runs the page's fetch via script.evaluate
and captures request/response metadata from BiDi network events.

Unlike CDP, BiDi exposes Set-Cookie directly in ``response.headers`` (no separate
extra-info event), and header values arrive wrapped as ``{type, value}``.
"""

from __future__ import annotations

import asyncio
import json as jsonlib
import logging
from typing import TYPE_CHECKING, Any

from pydoll.browser.requests.base import BaseRequest
from pydoll.commands.bidi.script_commands import ScriptCommands
from pydoll.constants import Scripts
from pydoll.protocol.bidi.script.types import ContextTarget
from pydoll.protocol.events import Event
from pydoll.protocol.types import Header, ResponseCookie

if TYPE_CHECKING:
    from pydoll.browser.firefox.tab import BiDiTab

logger = logging.getLogger(__name__)

_METADATA_TIMEOUT = 2.0


class BiDiRequest(BaseRequest['BiDiTab']):
    """HTTP client over WebDriver BiDi. See BaseRequest for the public API.

    Runs the fetch with script.evaluate and captures metadata from
    network.beforeRequestSent (sent headers) and network.responseCompleted
    (response headers, including Set-Cookie). Events are matched to the request's
    URL so unrelated page traffic is excluded.
    """

    def __init__(self, tab: BiDiTab):
        """Initialize a request helper bound to a BiDi tab.

        Args:
            tab: The tab providing the JS execution context and session state.
        """
        super().__init__(tab)
        self._requests_sent: list[dict] = []
        self._requests_received: list[dict] = []
        self._target_url = ''

    async def _execute_fetch_request(
        self, url: str, options: dict[str, Any]
    ) -> dict[str, Any]:
        """Run the fetch via script.evaluate, returning the JSON-decoded result value."""
        self._target_url = url
        inner = Scripts.MAKE_REQUEST.format(
            url=jsonlib.dumps(url), options=jsonlib.dumps(options)
        )
        # MAKE_REQUEST is itself an IIFE ending in ';'; strip it so the call can be
        # awaited inside our wrapper and the result serialized to a JSON string
        # (avoids BiDi RemoteValue serialization limits on large response bodies).
        inner = inner.strip().rstrip(';')
        expression = f'(async () => JSON.stringify(await ({inner})))()'
        response = await self.tab._execute_command(
            ScriptCommands.evaluate(
                expression=expression,
                target=ContextTarget(context=self.tab._context_id),
                await_promise=True,
            )
        )
        result = response['result']
        if result['type'] == 'exception':
            return {'error': result['exceptionDetails']['text'], 'status': 0}
        value = self.tab._deserialize_remote_value(result['result'])
        if not isinstance(value, str):
            return {'error': 'unexpected fetch result type', 'status': 0}
        return jsonlib.loads(value)

    async def _register_callbacks(self) -> None:
        """Capture request/response metadata via BiDi network events."""

        def append_sent(event: dict) -> None:
            self._requests_sent.append(event)

        def append_received(event: dict) -> None:
            self._requests_received.append(event)

        self._callback_ids = [
            await self.tab.on(Event.REQUEST_SENT, append_sent),
            await self.tab.on(Event.RESPONSE_COMPLETED, append_received),
        ]

    async def _clear_callbacks(self) -> None:
        """Remove this request's listeners and reset captured state."""
        for callback_id in self._callback_ids:
            await self.tab.remove_callback(callback_id)
        self._callback_ids.clear()
        self._requests_sent.clear()
        self._requests_received.clear()

    async def _await_metadata(self, url: str) -> None:
        """Wait briefly for this request's responseCompleted event to arrive.

        BiDi delivers network events asynchronously over the shared socket, so the
        responseCompleted may land just after the fetch result. Poll until it
        arrives or a short timeout elapses (metadata is best-effort; the body and
        status already come from the fetch result).
        """
        loop = asyncio.get_event_loop()
        deadline = loop.time() + _METADATA_TIMEOUT
        while loop.time() < deadline:
            if any(self._response_url(event) == url for event in self._requests_received):
                return
            await asyncio.sleep(0.05)

    def _extract_sent_headers(self) -> list[Header]:
        """Sent headers from beforeRequestSent events matching the request URL."""
        return self._collect_headers(
            event['params']['request'].get('headers', [])
            for event in self._requests_sent
            if event.get('params', {}).get('request', {}).get('url') == self._target_url
        )

    def _extract_received_headers(self) -> list[Header]:
        """Response headers from responseCompleted events matching the request URL."""
        return self._collect_headers(
            response.get('headers', []) for response in self._matching_responses()
        )

    def _extract_set_cookies(self) -> list[ResponseCookie]:
        """Cookies from Set-Cookie headers in the matching response events."""
        cookies: list[ResponseCookie] = []
        for response in self._matching_responses():
            for header in response.get('headers', []):
                if header.get('name', '').lower() != 'set-cookie':
                    continue
                value = self._header_value(header.get('value'))
                self._add_unique_cookies(cookies, self._parse_set_cookie_header(value))
        return cookies

    def _matching_responses(self) -> list[dict]:
        """Response objects from captured events whose URL matches the request."""
        return [
            event['params']['response']
            for event in self._requests_received
            if self._response_url(event) == self._target_url
        ]

    @classmethod
    def _collect_headers(cls, header_lists) -> list[Header]:
        """De-duplicate BiDi headers (unwrapping their BytesValue) into Header entries."""
        headers: list[Header] = []
        seen = set()
        for header_list in header_lists:
            for header in header_list:
                entry = Header(
                    name=header['name'], value=cls._header_value(header.get('value'))
                )
                identity = (entry['name'], entry['value'])
                if identity not in seen:
                    headers.append(entry)
                    seen.add(identity)
        return headers

    @staticmethod
    def _response_url(event: dict) -> str:
        """The response URL of a network event, or '' when absent."""
        response = event.get('params', {}).get('response') or {}
        return response.get('url', '')

    @staticmethod
    def _header_value(value: object) -> str:
        """Unwrap a BiDi header BytesValue ({type, value}) to a plain string."""
        if isinstance(value, dict):
            return str(value.get('value', ''))
        return str(value) if value is not None else ''
