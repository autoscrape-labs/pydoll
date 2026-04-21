"""HAR network replayer for mocked browser network traffic.

This module provides the HarReplayer class, which intercepts network requests
using the Chrome DevTools Protocol (CDP) Fetch domain.

All requests whose URL *and* method match an entry in the loaded HAR file are
fulfilled immediately from the recorded response, without hitting the network.
Requests that have no match in the HAR are forwarded to the real network.
"""

from __future__ import annotations

import base64
import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from pydoll.commands.page_commands import PageCommands
from pydoll.commands.runtime_commands import RuntimeCommands
from pydoll.protocol.fetch.events import FetchEvent

if TYPE_CHECKING:
    from pydoll.browser.tab import Tab
    from pydoll.protocol.network.har_types import Har, HarEntry

logger = logging.getLogger(__name__)


_FETCH_MOCK_TEMPLATE = r"""
(function() {{
  const __harIndex__ = {har_index_json};
  const _realFetch = window.fetch.bind(window);

  function __key__(method, url) {{
    return method.toUpperCase() + ' ' + url;
  }}

  window.fetch = async function(resource, init) {{
    const url  = (resource instanceof Request) ? resource.url  : String(resource);
    const meth = (init && init.method ? init.method : (
                  resource instanceof Request ? resource.method : 'GET'
                 )).toUpperCase();
    const entry = __harIndex__[__key__(meth, url)];
    if (entry) {{
      const resp  = entry.response || {{}};
      const cont  = resp.content || {{}};
      let bodyStr = cont.text || '';

      if (cont.encoding === 'base64') {{
        try {{ bodyStr = atob(bodyStr); }} catch(e) {{}}
      }}

      const headers = {{}};
      if (Array.isArray(resp.headers)) {{
        for (const h of resp.headers) {{
          headers[h.name] = h.value;
        }}
      }}
      if (!headers['Content-Type'] && cont.mimeType) {{
        headers['Content-Type'] = cont.mimeType;
      }}

      const blob = new Blob([bodyStr], {{ type: cont.mimeType || 'text/plain' }});
      const fakeResp = new Response(blob, {{
        status    : resp.status     || 200,
        statusText: resp.statusText || 'OK',
        headers   : headers,
      }});
      try {{ Object.defineProperty(fakeResp, 'url', {{ value: url }}); }} catch(_) {{}}
      return fakeResp;
    }}

    return _realFetch(resource, init);
  }};
}})();
"""


class HarReplayer:
    """Engine that intercepts requests via CDP Fetch.requestPaused.

    On :meth:`start`, it enables the Fetch domain (if needed) and registers an
    event callback for ``Fetch.requestPaused``. Matched requests are fulfilled
    using ``Fetch.fulfillRequest`` with the recorded HAR response.

    Usage is normally via ``tab.request.replay(har_path)`` which wraps this
    class in an async context manager.
    """

    def __init__(self, tab: Tab, har_path: str | Path):
        self._tab = tab
        self._har_path = Path(har_path)
        self._entries: list[HarEntry] = []
        self._index: dict[tuple[str, str], HarEntry] = {}
        self._script_identifier: str | None = None
        self._callback_id: int | None = None
        self._fetch_was_enabled: bool = False
        self._is_running = False

    # ------------------------------------------------------------------
    # Public lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Load the HAR file and enable request interception."""
        if self._is_running:
            return

        self._load_har()
        logger.info('HAR replayer: loaded %d entries from %s', len(self._entries), self._har_path)

        await self._install_fetch_shim()

        if not self._tab.fetch_events_enabled:
            await self._tab.enable_fetch_events()
            self._fetch_was_enabled = True

        self._callback_id = await self._tab.on(
            FetchEvent.REQUEST_PAUSED,
            cast(Any, self._on_request_paused),
        )

        self._is_running = True

    async def stop(self) -> None:
        """Stop interception and restore previous Fetch domain state."""
        if not self._is_running:
            return

        if self._callback_id is not None:
            await self._tab.remove_callback(self._callback_id)
            self._callback_id = None

        if self._script_identifier:
            await self._tab._execute_command(
                PageCommands.remove_script_to_evaluate_on_new_document(self._script_identifier)
            )
            self._script_identifier = None

        if self._fetch_was_enabled and self._tab.fetch_events_enabled:
            await self._tab.disable_fetch_events()
            self._fetch_was_enabled = False

        self._is_running = False
        logger.info('HAR replayer stopped')

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_har(self) -> None:
        """Load and parse the HAR file from disk."""
        try:
            with open(self._har_path, 'r', encoding='utf-8') as f:
                har_data: Har = json.load(f)
                self._entries = har_data['log']['entries']
                self._index = {
                    (e['request']['method'].upper(), e['request']['url']): e for e in self._entries
                }
        except Exception as e:
            logger.error('Failed to load HAR file %s: %s', self._har_path, e)
            raise ValueError(f'Invalid HAR file: {e}') from e

    async def _install_fetch_shim(self) -> None:
        """Install a JS-level fetch shim as a fallback for replay."""
        har_index = {f'{m} {u}': e for (m, u), e in self._index.items()}
        script_source = _FETCH_MOCK_TEMPLATE.format(
            har_index_json=json.dumps(har_index, ensure_ascii=False)
        )

        result: dict[str, Any] = await self._tab._execute_command(
            PageCommands.add_script_to_evaluate_on_new_document(
                source=script_source,
                run_immediately=True,
            )
        )
        self._script_identifier = result.get('result', {}).get('identifier')

        eval_result: dict[str, Any] = await self._tab._execute_command(
            RuntimeCommands.evaluate(
                expression=script_source,
                await_promise=True,
                return_by_value=True,
            )
        )
        if eval_result.get('error'):
            raise RuntimeError(f'Failed to inject HAR fetch shim: {eval_result["error"]}')

    async def _on_request_paused(self, event: dict) -> None:
        """Handle Fetch.requestPaused by fulfilling from HAR when possible."""
        try:
            params = event.get('params') or {}
            request_id = params.get('requestId')
            if not request_id:
                return

            request = params.get('request') or {}
            url = request.get('url', '')
            method = str(request.get('method', 'GET')).upper()

            if not url:
                return

            match = self._index.get((method, url))
            if not match:
                await self._tab.continue_request(request_id)
                return

            await self._fulfill_from_match(request_id, match)
        except Exception as exc:
            logger.debug('HAR replayer: failed to replay paused request: %s', exc)
            await self._fallback_continue(event)

    async def _fulfill_from_match(self, request_id: str, match: HarEntry) -> None:
        """Prepare and send fulfillRequest command from a HAR entry."""
        response = match.get('response') or {}
        content = response.get('content') or {}

        # Extract status and body
        status = int(response.get('status') or 200)
        status_text = str(response.get('statusText') or 'OK')
        body_b64 = self._get_base64_body(content)

        # Build headers
        headers = self._get_response_headers(response, content)

        await self._tab.fulfill_request(
            request_id=request_id,
            response_code=status,
            response_headers=cast(Any, headers) if headers else None,
            body=body_b64,
            response_phrase=status_text,
        )

    @staticmethod
    def _get_base64_body(content: Any) -> str:
        """Extract body text and encode as base64."""
        body_text = str(content.get('text') or '')
        if content.get('encoding') == 'base64':
            return body_text
        return base64.b64encode(body_text.encode('utf-8')).decode('ascii')

    @staticmethod
    def _get_response_headers(response: Any, content: Any) -> list[dict[str, str]]:
        """Consolidate headers from HAR response and content type."""
        headers: list[dict[str, str]] = []
        for h in response.get('headers') or []:
            name = h.get('name')
            value = h.get('value')
            if name and value is not None:
                headers.append({'name': str(name), 'value': str(value)})

        if not any(h['name'].lower() == 'content-type' for h in headers):
            mime_type = content.get('mimeType')
            if mime_type:
                headers.append({'name': 'Content-Type', 'value': str(mime_type)})
        return headers

    async def _fallback_continue(self, event: dict) -> None:
        """Ensure the request is continued if fulfillment fails."""
        try:
            params = event.get('params') or {}
            request_id = params.get('requestId')
            if request_id:
                await self._tab.continue_request(request_id)
        except Exception:
            pass
