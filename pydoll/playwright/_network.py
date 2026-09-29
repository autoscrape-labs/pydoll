"""Request, Response and Route objects built from Network and Fetch events."""

from __future__ import annotations

import asyncio
import base64
import inspect
import json
import logging
import mimetypes
import re
from json import dumps as json_dumps
from pathlib import Path
from typing import TYPE_CHECKING, Any, Awaitable, Callable, cast
from urllib.parse import parse_qs

from pydoll.commands import NetworkCommands
from pydoll.playwright._errors import Error
from pydoll.playwright._events import Deadline
from pydoll.playwright._glob import URLMatch, URLMatcher
from pydoll.protocol.network.types import ErrorReason

if TYPE_CHECKING:
    from pydoll.playwright._frame import Frame
    from pydoll.playwright._page import Page

logger = logging.getLogger(__name__)

RouteHandler = Callable[['Route'], Any] | Callable[['Route', 'Request'], Any]

_ERROR_REASONS = {
    'aborted': ErrorReason.ABORTED,
    'accessdenied': ErrorReason.ACCESS_DENIED,
    'addressunreachable': ErrorReason.ADDRESS_UNREACHABLE,
    'blockedbyclient': ErrorReason.BLOCKED_BY_CLIENT,
    'blockedbyresponse': ErrorReason.BLOCKED_BY_RESPONSE,
    'connectionaborted': ErrorReason.CONNECTION_ABORTED,
    'connectionclosed': ErrorReason.CONNECTION_CLOSED,
    'connectionfailed': ErrorReason.CONNECTION_FAILED,
    'connectionrefused': ErrorReason.CONNECTION_REFUSED,
    'connectionreset': ErrorReason.CONNECTION_RESET,
    'internetdisconnected': ErrorReason.INTERNET_DISCONNECTED,
    'namenotresolved': ErrorReason.NAME_NOT_RESOLVED,
    'timedout': ErrorReason.TIMED_OUT,
    'failed': ErrorReason.FAILED,
}


class Request:
    """One HTTP request issued by the page."""

    def __init__(
        self,
        page: Page,
        request_id: str,
        params: dict[str, Any],
        redirected_from: Request | None = None,
    ) -> None:
        self._page = page
        self._request_id = request_id
        raw = params.get('request', {})
        self._url: str = raw.get('url', '') + raw.get('urlFragment', '')
        self._method: str = raw.get('method', 'GET')
        self._headers: dict[str, str] = {
            key.lower(): value for key, value in raw.get('headers', {}).items()
        }
        self._extra_headers: dict[str, str] = {}
        self._post_data: str | None = raw.get('postData')
        self._resource_type: str = (params.get('type') or 'other').lower()
        self._frame_id: str | None = params.get('frameId')
        self._loader_id: str = params.get('loaderId', '')
        self._is_navigation = bool(params.get('loaderId')) and params.get('loaderId') == request_id
        self._timing: dict[str, Any] = {
            'startTime': params.get('wallTime', 0) * 1000 if params.get('wallTime') else 0
        }
        self._redirected_from = redirected_from
        self._redirected_to: Request | None = None
        self._response: Response | None = None
        self._failure: str | None = None
        self._response_future: asyncio.Future[Response | None] = page._loop.create_future()
        self._finished_future: asyncio.Future[str | None] = page._loop.create_future()
        if redirected_from is not None:
            redirected_from._redirected_to = self

    def __repr__(self) -> str:
        return f'<Request url={self._url!r} method={self._method!r}>'

    @property
    def url(self) -> str:
        return self._url

    @property
    def resource_type(self) -> str:
        return self._resource_type

    @property
    def method(self) -> str:
        return self._method

    @property
    def post_data(self) -> str | None:
        return self._post_data

    @property
    def post_data_json(self) -> Any:
        if self._post_data is None:
            return None
        content_type = self._headers.get('content-type', '')
        if 'application/x-www-form-urlencoded' in content_type:
            return {
                key: values[0] if len(values) == 1 else values
                for key, values in parse_qs(self._post_data).items()
            }
        return json.loads(self._post_data)

    @property
    def post_data_buffer(self) -> bytes | None:
        return self._post_data.encode() if self._post_data is not None else None

    @property
    def headers(self) -> dict[str, str]:
        return dict(self._headers)

    def _full_headers(self) -> dict[str, str]:
        """The headers Chrome actually sent, once ``requestWillBeSentExtraInfo`` told us."""
        return {**self._headers, **self._extra_headers}

    async def all_headers(self) -> dict[str, str]:
        return self._full_headers()

    async def headers_array(self) -> list[dict[str, str]]:
        return [{'name': name, 'value': value} for name, value in self._full_headers().items()]

    async def header_value(self, name: str) -> str | None:
        return self._full_headers().get(name.lower())

    @property
    def frame(self) -> Frame:
        return self._page._frame_for_id(self._frame_id or '')

    @property
    def service_worker(self) -> None:
        return None

    @property
    def redirected_from(self) -> Request | None:
        return self._redirected_from

    @property
    def redirected_to(self) -> Request | None:
        return self._redirected_to

    @property
    def failure(self) -> str | None:
        return self._failure

    @property
    def timing(self) -> dict[str, Any]:
        return dict(self._timing)

    def is_navigation_request(self) -> bool:
        return self._is_navigation

    async def response(self) -> Response | None:
        return await self._response_future

    async def sizes(self) -> dict[str, int]:
        response = self._response
        body = len(await response.body()) if response else 0
        return {
            'requestBodySize': len(self._post_data or ''),
            'requestHeadersSize': sum(len(k) + len(v) + 4 for k, v in self._headers.items()),
            'responseBodySize': body,
            'responseHeadersSize': sum(
                len(k) + len(v) + 4 for k, v in (response._headers.items() if response else [])
            ),
        }


class Response:
    """The response to a request, with lazy body access."""

    def __init__(self, page: Page, request: Request, params: dict[str, Any]) -> None:
        self._page = page
        self._request = request
        raw = params.get('response', {})
        self._url: str = raw.get('url', request.url)
        self._status: int = int(raw.get('status', 0))
        self._status_text: str = raw.get('statusText', '')
        self._headers: dict[str, str] = {
            key.lower(): value for key, value in raw.get('headers', {}).items()
        }
        self._extra_headers: dict[str, str] = {}
        self._remote_address = {
            'ipAddress': raw.get('remoteIPAddress'),
            'port': raw.get('remotePort'),
        }
        self._from_service_worker = bool(raw.get('fromServiceWorker'))
        self._security_details = raw.get('securityDetails')
        self._protocol = raw.get('protocol', '')
        self._frame_id = params.get('frameId')
        self._body: bytes | None = None
        request._response = self
        if not request._response_future.done():
            request._response_future.set_result(self)

    def __repr__(self) -> str:
        return f'<Response url={self._url!r} status={self._status}>'

    @property
    def url(self) -> str:
        return self._url

    @property
    def ok(self) -> bool:
        return self._status == 0 or 200 <= self._status <= 299  # noqa: PLR2004

    @property
    def status(self) -> int:
        return self._status

    @property
    def status_text(self) -> str:
        return self._status_text

    @property
    def headers(self) -> dict[str, str]:
        return dict(self._headers)

    def _full_headers(self) -> dict[str, str]:
        """The raw response headers, once ``responseReceivedExtraInfo`` told us."""
        return {**self._headers, **self._extra_headers}

    async def all_headers(self) -> dict[str, str]:
        return self._full_headers()

    async def headers_array(self) -> list[dict[str, str]]:
        return [
            {'name': name, 'value': value}
            for name, joined in self._full_headers().items()
            for value in joined.split('\n')
        ]

    async def header_value(self, name: str) -> str | None:
        return self._full_headers().get(name.lower())

    async def header_values(self, name: str) -> list[str]:
        value = self._full_headers().get(name.lower())
        return [] if value is None else value.split('\n')

    @property
    def from_service_worker(self) -> bool:
        return self._from_service_worker

    @property
    def request(self) -> Request:
        return self._request

    @property
    def frame(self) -> Frame:
        return self._page._frame_for_id(self._frame_id or '')

    async def server_addr(self) -> dict[str, Any] | None:
        return self._remote_address if self._remote_address.get('ipAddress') else None

    async def security_details(self) -> dict[str, Any] | None:
        return self._security_details

    async def http_version(self) -> str:
        return self._protocol or 'HTTP/1.1'

    async def finished(self) -> str | None:
        return await self._request._finished_future

    async def body(self) -> bytes:
        if self._body is None:
            deadline = Deadline(self._page._timeout(None))
            remaining = deadline.remaining_seconds()
            try:
                await asyncio.wait_for(asyncio.shield(self._request._finished_future), remaining)
            except asyncio.TimeoutError:
                raise deadline.error(
                    'waiting for the response to finish (the page must consume the body first)'
                ) from None
            response = await self._page._send(
                NetworkCommands.get_response_body(self._request._request_id)
            )
            result = response['result']
            if result.get('base64Encoded'):
                self._body = base64.b64decode(result.get('body', ''))
            else:
                self._body = result.get('body', '').encode('utf-8')
        return self._body

    async def text(self) -> str:
        return (await self.body()).decode('utf-8', errors='replace')

    async def json(self) -> Any:
        text = await self.text()
        try:
            return json.loads(text)
        except ValueError as error:
            raise Error(f'Response body is not valid JSON: {error}') from error


class NetworkManager:
    """Tracks requests of a page from Network events and answers navigation lookups."""

    def __init__(self, page: Page) -> None:
        self._page = page
        self._requests: dict[str, Request] = {}
        self._response_extra_headers: dict[str, dict[str, str]] = {}
        self._in_flight: set[str] = set()
        self._changed = asyncio.Event()

    def _notify(self) -> None:
        self._changed.set()
        self._changed = asyncio.Event()

    def is_idle(self) -> bool:
        return not self._in_flight

    def on_request_will_be_sent(self, params: dict[str, Any]) -> None:
        request_id = params['requestId']
        redirected_from: Request | None = None
        if 'redirectResponse' in params and request_id in self._requests:
            redirected_from = self._requests[request_id]
            Response(
                self._page,
                redirected_from,
                {'response': params['redirectResponse'], 'frameId': params.get('frameId')},
            )
            self._finish(redirected_from, None)
        request = Request(self._page, request_id, params, redirected_from)
        self._requests[request_id] = request
        self._in_flight.add(request_id)
        self._notify()
        self._page.emit('request', request)

    def on_request_will_be_sent_extra_info(self, params: dict[str, Any]) -> None:
        request = self._requests.get(params['requestId'])
        if request is None:
            return
        request._extra_headers = _lower_keys(params.get('headers', {}))

    def on_response_received(self, params: dict[str, Any]) -> None:
        request = self._requests.get(params['requestId'])
        if request is None:
            return
        response = Response(self._page, request, params)
        response._extra_headers = self._response_extra_headers.pop(params['requestId'], {})
        self._notify()
        self._page.emit('response', response)

    def on_response_received_extra_info(self, params: dict[str, Any]) -> None:
        """Attach the raw headers to the response, or hold them until it exists.

        Chrome gives no ordering guarantee between ``responseReceived`` and
        its extra-info companion, so either side may arrive first.
        """
        request = self._requests.get(params['requestId'])
        headers = _lower_keys(params.get('headers', {}))
        if request is not None and request._response is not None:
            request._response._extra_headers = headers
        else:
            self._response_extra_headers[params['requestId']] = headers

    def on_loading_finished(self, params: dict[str, Any]) -> None:
        request = self._requests.get(params['requestId'])
        if request is None:
            return
        self._finish(request, None)
        self._page.emit('requestfinished', request)

    def on_loading_failed(self, params: dict[str, Any]) -> None:
        request = self._requests.get(params['requestId'])
        if request is None:
            return
        request._failure = params.get('errorText', 'net::ERR_FAILED')
        self._finish(request, request._failure)
        self._page.emit('requestfailed', request)

    def _finish(self, request: Request, error: str | None) -> None:
        self._in_flight.discard(request._request_id)
        if not request._response_future.done():
            request._response_future.set_result(None)
        if not request._finished_future.done():
            request._finished_future.set_result(error)
        self._notify()
        self._page._navigation._notify()

    def navigation_failure(self, loader_id: str) -> str | None:
        """The error text of a failed navigation request, if the loader failed."""
        for request in list(self._requests.values()):
            if request._loader_id == loader_id and request._is_navigation and request._failure:
                return request._failure
        return None

    def request_for(self, request_id: str | None) -> Request | None:
        if request_id is None:
            return None
        return self._requests.get(request_id)

    async def navigation_response(self, loader_id: str, deadline: Deadline) -> Response | None:
        """The response of the navigation request that carried ``loader_id``.

        Called once the navigation reached its wait state, so a loader with no
        request behind it (``about:blank``, ``data:`` documents) is a navigation
        without a network round trip and answers ``None`` right away.
        """
        while True:
            navigation = next(
                (
                    request
                    for request in list(self._requests.values())
                    if request._loader_id == loader_id and request._is_navigation
                ),
                None,
            )
            if navigation is None:
                return None
            if navigation._response is not None:
                return navigation._response
            if navigation._failure is not None or navigation._finished_future.done():
                return None
            remaining = deadline.remaining_seconds()
            if remaining is not None and remaining <= 0:
                return None
            try:
                await asyncio.wait_for(
                    self._changed.wait(), timeout=min(remaining, 1.0) if remaining else 1.0
                )
            except asyncio.TimeoutError:
                if remaining is None or remaining <= 1.0:
                    return None


class Route:
    """A paused request that a route handler decides how to serve."""

    def __init__(self, page: Page, params: dict[str, Any], request: Request) -> None:
        self._page = page
        self._interception_id: str = params['requestId']
        self._network_id: str | None = params.get('networkId')
        self._request = request
        self._handled = False
        self._at_response_stage = 'responseStatusCode' in params
        self._fallback_overrides: dict[str, Any] = {}
        self._intercepted: asyncio.Future[APIResponse] | None = None

    @property
    def request(self) -> Request:
        return self._request

    def _mark(self) -> None:
        if self._handled:
            raise Error('Route is already handled!')
        self._handled = True

    async def abort(self, error_code: str | None = None) -> None:
        self._mark()
        reason = _ERROR_REASONS.get((error_code or 'failed').lower(), ErrorReason.FAILED)
        await self._page._guard(lambda: self._page._tab.fail_request(self._interception_id, reason))

    async def continue_(
        self,
        url: str | None = None,
        method: str | None = None,
        headers: dict[str, str] | None = None,
        post_data: str | bytes | dict[str, Any] | None = None,
    ) -> None:
        self._mark()
        overrides = dict(self._fallback_overrides)
        overrides.update({
            k: v
            for k, v in {
                'url': url,
                'method': method,
                'headers': headers,
                'post_data': post_data,
            }.items()
            if v is not None
        })
        await self._continue(overrides)

    async def _continue(self, overrides: dict[str, Any]) -> None:
        if self._at_response_stage:
            await self._page._send({
                'method': 'Fetch.continueResponse',
                'params': {'requestId': self._interception_id},
            })
            return
        post_data = overrides.get('post_data')
        if isinstance(post_data, dict):
            post_data = json.dumps(post_data)
        if isinstance(post_data, str):
            post_data = post_data.encode()
        headers = overrides.get('headers')
        encoded = base64.b64encode(post_data).decode() if post_data is not None else None
        await self._page._guard(
            lambda: self._page._tab.continue_request(
                self._interception_id,
                url=overrides.get('url'),
                method=overrides.get('method'),
                post_data=encoded,
                headers=[{'name': name, 'value': value} for name, value in headers.items()]
                if headers
                else None,
            )
        )

    async def fallback(
        self,
        url: str | None = None,
        method: str | None = None,
        headers: dict[str, str] | None = None,
        post_data: str | bytes | dict[str, Any] | None = None,
    ) -> None:
        for key, value in {
            'url': url,
            'method': method,
            'headers': headers,
            'post_data': post_data,
        }.items():
            if value is not None:
                self._fallback_overrides[key] = value

    async def fulfill(
        self,
        status: int | None = None,
        headers: dict[str, str] | None = None,
        body: str | bytes | None = None,
        json: Any = None,  # noqa: A002
        path: str | Path | None = None,
        content_type: str | None = None,
        response: APIResponse | None = None,
    ) -> None:
        self._mark()
        response_headers: dict[str, str] = {}
        status_code = status or 200
        payload: bytes = b''
        if response is not None:
            status_code = status or response.status
            response_headers.update(response.headers)
            payload = await response.body()
        if json is not None:
            body = json_dumps(json)
            content_type = content_type or 'application/json'
        if path is not None:
            payload = Path(path).read_bytes()
            content_type = (
                content_type or mimetypes.guess_type(str(path))[0] or 'application/octet-stream'
            )
        if body is not None:
            payload = body.encode() if isinstance(body, str) else body
        if headers:
            response_headers.update({key: str(value) for key, value in headers.items()})
        if content_type:
            response_headers['content-type'] = content_type
        response_headers.setdefault('content-length', str(len(payload)))
        await self._page._guard(
            lambda: self._page._tab.fulfill_request(
                self._interception_id,
                response_code=status_code,
                response_headers=[
                    {'name': name, 'value': value} for name, value in response_headers.items()
                ],
                body=base64.b64encode(payload).decode(),
            )
        )

    async def fetch(
        self,
        url: str | None = None,
        method: str | None = None,
        headers: dict[str, str] | None = None,
        post_data: str | bytes | dict[str, Any] | None = None,
        max_redirects: int | None = None,
        max_retries: int | None = None,
        timeout: float | None = None,
    ) -> APIResponse:
        """Let the request reach the network and capture its response for ``fulfill``.

        The request continues with the given overrides and pauses again at the
        response stage, so the handler can inspect or rewrite the body before
        answering the page.
        """
        if self._handled:
            raise Error('Route is already handled!')
        if self._intercepted is not None:
            return await self._intercepted
        overrides = dict(self._fallback_overrides)
        overrides.update({
            key: value
            for key, value in {
                'url': url,
                'method': method,
                'headers': headers,
                'post_data': post_data,
            }.items()
            if value is not None
        })
        self._intercepted = self._page._loop.create_future()
        self._page._router.expect_response_stage(self)
        data = overrides.get('post_data')
        if isinstance(data, dict):
            data = json.dumps(data)
        if isinstance(data, str):
            data = data.encode()
        request_headers = overrides.get('headers')
        encoded = base64.b64encode(data).decode() if data is not None else None
        await self._page._guard(
            lambda: self._page._tab.continue_request(
                self._interception_id,
                url=overrides.get('url'),
                method=overrides.get('method'),
                post_data=encoded,
                headers=[{'name': name, 'value': value} for name, value in request_headers.items()]
                if request_headers
                else None,
                intercept_response=True,
            )
        )
        deadline = Deadline(self._page._timeout(timeout))
        remaining = deadline.remaining_seconds()
        try:
            if remaining is None:
                return await self._intercepted
            return await asyncio.wait_for(asyncio.shield(self._intercepted), timeout=remaining)
        except asyncio.TimeoutError:
            raise deadline.error('waiting for the intercepted response') from None

    async def _resolve_response_stage(self, params: dict[str, Any]) -> None:
        self._interception_id = params['requestId']
        self._at_response_stage = True
        headers = {
            entry['name'].lower(): entry['value'] for entry in params.get('responseHeaders', [])
        }
        body = b''
        try:
            response = await self._page._send({
                'method': 'Fetch.getResponseBody',
                'params': {'requestId': self._interception_id},
            })
            result = response['result']
            raw = result.get('body', '')
            body = base64.b64decode(raw) if result.get('base64Encoded') else raw.encode()
        except Error:
            body = b''
        api_response = APIResponse(
            self._request.url, int(params.get('responseStatusCode', 0)), headers, body
        )
        if self._intercepted is not None and not self._intercepted.done():
            self._intercepted.set_result(api_response)


class APIResponse:
    """A fetched response that ``route.fulfill(response=...)`` can replay."""

    def __init__(self, url: str, status: int, headers: dict[str, str], body: bytes) -> None:
        self._url = url
        self._status = status
        self._headers = {key.lower(): value for key, value in headers.items()}
        self._body = body

    @property
    def url(self) -> str:
        return self._url

    @property
    def status(self) -> int:
        return self._status

    @property
    def ok(self) -> bool:
        return 200 <= self._status <= 299  # noqa: PLR2004

    @property
    def headers(self) -> dict[str, str]:
        return dict(self._headers)

    async def body(self) -> bytes:
        return self._body

    async def text(self) -> str:
        return self._body.decode('utf-8', errors='replace')

    async def json(self) -> Any:
        return json.loads(await self.text())


_HANDLER_ARITY_WITH_REQUEST = 2


class RouteEntry:
    """A registered route: matcher, handler and remaining invocations."""

    def __init__(self, matcher: URLMatcher, handler: RouteHandler, times: int | None) -> None:
        self.matcher = matcher
        self.handler = handler
        self.times = times
        self.count = 0

    def matches(self, url: str) -> bool:
        return (self.times is None or self.count < self.times) and self.matcher.matches(url)

    async def handle(self, route: Route) -> bool:
        self.count += 1
        parameters = inspect.signature(self.handler).parameters
        if len(parameters) >= _HANDLER_ARITY_WITH_REQUEST:
            with_request = cast(Callable[[Route, Request], Any], self.handler)
            result = with_request(route, route.request)
        else:
            route_only = cast(Callable[[Route], Any], self.handler)
            result = route_only(route)
        if inspect.isawaitable(result):
            await result
        return route._handled


class Router:
    """Dispatches paused requests to page and context route handlers."""

    def __init__(self, page: Page) -> None:
        self._page = page
        self._awaiting_response: dict[str, Route] = {}

    def expect_response_stage(self, route: Route) -> None:
        self._awaiting_response[route._network_id or route._interception_id] = route

    async def dispatch(self, params: dict[str, Any]) -> None:
        network_id = params.get('networkId')
        if 'responseStatusCode' in params or 'responseErrorReason' in params:
            waiting = self._awaiting_response.pop(network_id or params['requestId'], None)
            if waiting is not None:
                await waiting._resolve_response_stage(params)
                return
            await self._page._send({
                'method': 'Fetch.continueResponse',
                'params': {'requestId': params['requestId']},
            })
            return
        request = self._page._network.request_for(network_id) or Request(
            self._page, network_id or params['requestId'], params
        )
        route = Route(self._page, params, request)
        entries = list(reversed(self._page._routes)) + list(reversed(self._page.context._routes))
        for entry in entries:
            if not entry.matches(request.url):
                continue
            try:
                handled = await entry.handle(route)
            except Exception:
                logger.exception('Route handler for %s raised', request.url)
                handled = route._handled
            if handled:
                return
        if not route._handled:
            route._handled = True
            await route._continue(route._fallback_overrides)


def make_entry(
    url: URLMatch, handler: RouteHandler, times: int | None, base_url: str | None
) -> RouteEntry:
    return RouteEntry(URLMatcher(url, base_url), handler, times)


async def wait_for_matching(
    page: Page,
    event: str,
    matcher: URLMatch | Callable[[Any], bool | Awaitable[bool]],
    deadline: Deadline,
) -> Any:
    future: asyncio.Future[Any] = page._loop.create_future()
    url_matcher: URLMatcher | None = None
    predicate: Callable[[Any], bool | Awaitable[bool]] | None = None
    if isinstance(matcher, (str, re.Pattern)):
        url_matcher = URLMatcher(matcher, page.context._base_url)
    else:
        predicate = matcher

    async def check(item: Any) -> None:
        if future.done():
            return
        try:
            if url_matcher is not None:
                matched = url_matcher.matches(item.url)
            elif predicate is not None:
                outcome = predicate(item)
                matched = await outcome if inspect.isawaitable(outcome) else bool(outcome)
        except Exception as error:
            future.set_exception(error)
            return
        if matched:
            future.set_result(item)

    def listener(item: Any) -> None:
        asyncio.ensure_future(check(item))

    page.on(event, listener)
    try:
        remaining = deadline.remaining_seconds()
        return await (
            asyncio.wait_for(future, timeout=remaining) if remaining is not None else future
        )
    except asyncio.TimeoutError:
        raise deadline.error(f'waiting for {event}') from None
    finally:
        page.remove_listener(event, listener)


def _lower_keys(headers: dict[str, str]) -> dict[str, str]:
    return {key.lower(): value for key, value in headers.items()}
