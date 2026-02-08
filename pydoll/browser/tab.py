from __future__ import annotations

import asyncio
import base64 as _b64
import logging
import shutil
import warnings
from contextlib import asynccontextmanager
from functools import partial
from pathlib import Path
from tempfile import mkdtemp
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncGenerator,
    Awaitable,
    Callable,
    Optional,
    TypeAlias,
    Union,
    cast,
    overload,
)

import aiofiles

from pydoll.browser.requests import Request
from pydoll.commands import (
    DomCommands,
    FetchCommands,
    NetworkCommands,
    PageCommands,
    RuntimeCommands,
    StorageCommands,
    TargetCommands,
)
from pydoll.connection import ConnectionHandler
from pydoll.constants import By, PageLoadState
from pydoll.elements.mixins import FindElementsMixin
from pydoll.elements.shadow_root import ShadowRoot
from pydoll.elements.web_element import WebElement
from pydoll.exceptions import (
    CommandExecutionTimeout,
    DownloadTimeout,
    IFrameNotFound,
    InvalidFileExtension,
    InvalidIFrame,
    InvalidScriptWithElement,
    InvalidTabInitialization,
    MissingScreenshotPath,
    NetworkEventsNotEnabled,
    NoDialogPresent,
    NotAnIFrame,
    PageLoadTimeout,
    TopLevelTargetRequired,
    WaitElementTimeout,
    WebSocketConnectionClosed,
)
from pydoll.interactions import KeyboardAPI, ScrollAPI
from pydoll.interactions.iframe import IFrameContext
from pydoll.protocol.browser.types import DownloadBehavior, DownloadProgressState
from pydoll.protocol.dom.types import Node, ShadowRootType
from pydoll.protocol.page.events import PageEvent
from pydoll.protocol.page.types import ScreenshotFormat
from pydoll.protocol.runtime.methods import (
    CallFunctionOnResponse,
    EvaluateResponse,
    SerializationOptions,
)
from pydoll.protocol.runtime.types import CallArgument
from pydoll.protocol.target.types import TargetInfo
from pydoll.utils import (
    decode_base64_to_bytes,
    has_return_outside_function,
)

if TYPE_CHECKING:
    from pydoll.browser.chromium.base import Browser
    from pydoll.protocol.base import EmptyResponse, Response
    from pydoll.protocol.browser.events import (
        DownloadProgressEvent,
        DownloadWillBeginEvent,
    )
    from pydoll.protocol.dom.methods import (
        DescribeNodeResponse,
        GetDocumentResponse,
        ResolveNodeResponse,
    )
    from pydoll.protocol.fetch.types import AuthChallengeResponseType, HeaderEntry, RequestStage
    from pydoll.protocol.network.events import RequestWillBeSentEvent
    from pydoll.protocol.network.methods import GetCookiesResponse as NetworkGetCookiesResponse
    from pydoll.protocol.network.methods import GetResponseBodyResponse
    from pydoll.protocol.network.types import (
        Cookie,
        CookieParam,
        ErrorReason,
        RequestMethod,
        ResourceType,
    )
    from pydoll.protocol.page.events import FileChooserOpenedEvent
    from pydoll.protocol.page.methods import CaptureScreenshotResponse, PrintToPDFResponse
    from pydoll.protocol.runtime.methods import CallFunctionOnResponse, EvaluateResponse
    from pydoll.protocol.storage.methods import GetCookiesResponse as StorageGetCookiesResponse
    from pydoll.protocol.target.methods import AttachToTargetResponse, GetTargetsResponse

logger = logging.getLogger(__name__)

IFrame: TypeAlias = 'Tab'

_CLOUDFLARE_CHALLENGE_DOMAIN = 'challenges.cloudflare.com'
_CLOUDFLARE_IFRAME_SELECTOR = f'iframe[src*="{_CLOUDFLARE_CHALLENGE_DOMAIN}"]'
_CLOUDFLARE_CHECKBOX_SELECTOR = 'span.cb-i'


class Tab(FindElementsMixin):
    """
    Controls a browser tab via Chrome DevTools Protocol.

    Primary interface for web page automation including navigation, DOM manipulation,
    JavaScript execution, event handling, network monitoring, and specialized tasks
    like Cloudflare bypass.
    """

    _READY_STATE_ORDER = (PageLoadState.LOADING, PageLoadState.INTERACTIVE, PageLoadState.COMPLETE)

    def __init__(
        self,
        browser: Browser,
        connection_port: Optional[int] = None,
        target_id: Optional[str] = None,
        browser_context_id: Optional[str] = None,
        ws_address: Optional[str] = None,
    ):
        """
        Initialize tab controller for existing browser tab.

        Args:
            browser: Browser instance that created this tab.
            connection_port: CDP WebSocket port.
            target_id: CDP target identifier for this tab.
            browser_context_id: Optional browser context ID.
            ws_address: Optional WebSocket address for this tab.
        """
        if not any([connection_port, target_id, ws_address]):
            raise InvalidTabInitialization()

        self._browser = browser
        self._connection_port = connection_port
        self._target_id = target_id
        self._ws_address = ws_address
        self._browser_context_id = browser_context_id
        self._connection_handler = self._get_connection_handler()
        self._page_events_enabled = False
        self._network_events_enabled = False
        self._fetch_events_enabled = False
        self._dom_events_enabled = False
        self._runtime_events_enabled = False
        self._intercept_file_chooser_dialog_enabled = False
        self._cloudflare_captcha_callback_id: Optional[int] = None
        self._request: Optional[Request] = None
        self._scroll: Optional[ScrollAPI] = None
        self._keyboard: Optional[KeyboardAPI] = None
        logger.debug(
            (
                f'Tab initialized: target_id={self._target_id}, '
                f'ws_address_set={bool(self._ws_address)}, '
                f'context_id={self._browser_context_id}, port={self._connection_port}'
            )
        )

    @property
    def page_events_enabled(self) -> bool:
        """Whether CDP Page domain events are enabled."""
        return self._page_events_enabled

    @property
    def network_events_enabled(self) -> bool:
        """Whether CDP Network domain events are enabled."""
        return self._network_events_enabled

    @property
    def fetch_events_enabled(self) -> bool:
        """Whether CDP Fetch domain events (request interception) are enabled."""
        return self._fetch_events_enabled

    @property
    def dom_events_enabled(self) -> bool:
        """Whether CDP DOM domain events are enabled."""
        return self._dom_events_enabled

    @property
    def runtime_events_enabled(self) -> bool:
        """Whether CDP Runtime domain events are enabled."""
        return self._runtime_events_enabled

    @property
    def request(self) -> Request:
        """
        Get the request object for making HTTP requests using the browser's fetch API.

        Returns:
            Request: An instance of the Request class for making HTTP requests.
        """
        if self._request is None:
            self._request = Request(self)
        return self._request

    @property
    def scroll(self) -> ScrollAPI:
        """
        Get the scroll API for controlling page scroll behavior.

        Returns:
            ScrollAPI: An instance of the ScrollAPI class for scroll operations.
        """
        if self._scroll is None:
            self._scroll = ScrollAPI(self)
        return self._scroll

    @property
    def keyboard(self) -> KeyboardAPI:
        """
        Get the keyboard API for controlling keyboard input at page level.

        Returns:
            KeyboardAPI: An instance of the KeyboardAPI class for keyboard operations.
        """
        if self._keyboard is None:
            self._keyboard = KeyboardAPI(self)
        return self._keyboard

    @property
    def intercept_file_chooser_dialog_enabled(self) -> bool:
        """Whether file chooser dialog interception is active."""
        return self._intercept_file_chooser_dialog_enabled

    @property
    async def current_url(self) -> str:
        """Get current page URL (reflects redirects and client-side navigation)."""
        response: EvaluateResponse = await self._execute_command(
            RuntimeCommands.evaluate('window.location.href')
        )
        return response['result']['result']['value']

    @property
    async def page_source(self) -> str:
        """Get complete HTML source of current page (live DOM state)."""
        response: EvaluateResponse = await self._execute_command(
            RuntimeCommands.evaluate('document.documentElement.outerHTML')
        )
        return response['result']['result']['value']

    @property
    async def title(self) -> str:
        """Get current page title."""
        response: EvaluateResponse = await self._execute_command(
            RuntimeCommands.evaluate('document.title')
        )
        return response['result']['result'].get('value', '')

    async def enable_page_events(self):
        """Enable CDP Page domain events (load, navigation, dialogs, etc.)."""
        logger.debug('Enabling Page events')
        response = await self._execute_command(PageCommands.enable())
        self._page_events_enabled = True
        logger.debug('Page events enabled')
        return response

    async def enable_network_events(self):
        """Enable CDP Network domain events (requests, responses, etc.)."""
        logger.debug('Enabling Network events')
        response = await self._execute_command(NetworkCommands.enable())
        self._network_events_enabled = True
        logger.debug('Network events enabled')
        return response

    async def enable_fetch_events(
        self,
        handle_auth: bool = False,
        resource_type: Optional[ResourceType] = None,
        request_stage: Optional[RequestStage] = None,
    ):
        """
        Enable CDP Fetch domain for request interception.

        Args:
            handle_auth: Intercept authentication challenges.
            resource_type: Filter by resource type (all if None).
            request_stage: When to intercept (Request/Response).

        Note:
            Intercepted requests must be explicitly continued or timeout.
        """
        logger.debug(
            f'Enabling Fetch events: handle_auth={handle_auth}, resource_type={resource_type}, '
            f'stage={request_stage}'
        )
        response: Response[EmptyResponse] = await self._execute_command(
            FetchCommands.enable(
                handle_auth_requests=handle_auth,
                resource_type=resource_type,
                request_stage=request_stage,
            )
        )
        self._fetch_events_enabled = True
        logger.debug('Fetch events enabled')
        return response

    async def enable_dom_events(self):
        """Enable CDP DOM domain events (document structure changes)."""
        logger.debug('Enabling DOM events')
        response = await self._execute_command(DomCommands.enable())
        self._dom_events_enabled = True
        logger.debug('DOM events enabled')
        return response

    async def enable_runtime_events(self):
        """Enable CDP Runtime domain events."""
        logger.debug('Enabling Runtime events')
        response = await self._execute_command(RuntimeCommands.enable())
        self._runtime_events_enabled = True
        logger.debug('Runtime events enabled')
        return response

    async def enable_intercept_file_chooser_dialog(self):
        """
        Enable file chooser dialog interception for automated uploads.

        Note:
            Use expect_file_chooser context manager for convenience.
        """
        logger.info('Enabling file chooser interception')
        response = await self._execute_command(PageCommands.set_intercept_file_chooser_dialog(True))
        self._intercept_file_chooser_dialog_enabled = True
        logger.debug('File chooser interception enabled')
        return response

    async def enable_auto_solve_cloudflare_captcha(
        self,
        custom_selector: Optional[tuple[By, str]] = None,
        time_before_click: Optional[float] = None,
        time_to_wait_captcha: float = 5,
    ):
        """
        Enable automatic Cloudflare Turnstile captcha bypass.

        Args:
            custom_selector: Deprecated — ignored. Cloudflare Turnstile is now
                detected automatically via shadow root inspection.
            time_before_click: Deprecated — ignored. The checkbox is now
                located via shadow root polling and clicked immediately.
            time_to_wait_captcha: Timeout for captcha detection (default 5s).
        """
        if custom_selector is not None:
            warnings.warn(
                'custom_selector is deprecated and ignored. Cloudflare Turnstile is now '
                'detected automatically via shadow root inspection.',
                DeprecationWarning,
                stacklevel=2,
            )

        if time_before_click is not None:
            warnings.warn(
                'time_before_click is deprecated and ignored. The checkbox is now '
                'located via shadow root polling and clicked immediately.',
                DeprecationWarning,
                stacklevel=2,
            )

        logger.info('Enabling Cloudflare captcha auto-solve')
        if not self.page_events_enabled:
            await self.enable_page_events()

        callback = partial(
            self._bypass_cloudflare,
            time_to_wait_captcha=time_to_wait_captcha,
        )

        self._cloudflare_captcha_callback_id = await self.on(PageEvent.LOAD_EVENT_FIRED, callback)
        logger.debug(
            f'Cloudflare auto-solve callback registered: id={self._cloudflare_captcha_callback_id}'
        )

    async def disable_fetch_events(self):
        """Disable CDP Fetch domain and release paused requests."""
        logger.debug('Disabling Fetch events')
        response = await self._execute_command(FetchCommands.disable())
        self._fetch_events_enabled = False
        logger.debug('Fetch events disabled')
        return response

    async def disable_page_events(self):
        """Disable CDP Page domain events."""
        logger.debug('Disabling Page events')
        response = await self._execute_command(PageCommands.disable())
        self._page_events_enabled = False
        logger.debug('Page events disabled')
        return response

    async def disable_network_events(self):
        """Disable CDP Network domain events."""
        logger.debug('Disabling Network events')
        response = await self._execute_command(NetworkCommands.disable())
        self._network_events_enabled = False
        logger.debug('Network events disabled')
        return response

    async def disable_dom_events(self):
        """Disable CDP DOM domain events."""
        logger.debug('Disabling DOM events')
        response = await self._execute_command(DomCommands.disable())
        self._dom_events_enabled = False
        logger.debug('DOM events disabled')
        return response

    async def disable_runtime_events(self):
        """Disable CDP Runtime domain events."""
        logger.debug('Disabling Runtime events')
        response = await self._execute_command(RuntimeCommands.disable())
        self._runtime_events_enabled = False
        logger.debug('Runtime events disabled')
        return response

    async def disable_intercept_file_chooser_dialog(self):
        """Disable file chooser dialog interception."""
        logger.info('Disabling file chooser interception')
        response = await self._execute_command(
            PageCommands.set_intercept_file_chooser_dialog(False)
        )
        self._intercept_file_chooser_dialog_enabled = False
        logger.debug('File chooser interception disabled')
        return response

    async def disable_auto_solve_cloudflare_captcha(self):
        """Disable automatic Cloudflare Turnstile captcha bypass."""
        logger.info('Disabling Cloudflare captcha auto-solve')
        await self._connection_handler.remove_callback(self._cloudflare_captcha_callback_id)
        self._cloudflare_captcha_callback_id = None

    async def close(self):
        """
        Close this browser tab.

        Note:
            Tab instance becomes invalid after calling this method.
        """
        logger.info(f'Closing tab: target_id={self._target_id}')
        result = await self._execute_command(PageCommands.close())
        self._browser._tabs_opened.pop(self._target_id)
        logger.debug('Tab closed and removed from browser registry')
        return result

    async def get_frame(self, frame: 'WebElement') -> IFrame:
        """
        .. deprecated:: ?.?.?
            Use iframe `WebElement` instances directly; this method will be removed in
            a future version.

        Get Tab object for interacting with iframe content.

        Args:
            frame: Tab representing the iframe tag.

        Returns:
            Tab instance configured for iframe interaction.

        Raises:
            NotAnIFrame: If element is not an iframe.
            InvalidIFrame: If iframe lacks valid src attribute.
            IFrameNotFound: If iframe target not found in browser.
        """
        warnings.warn(
            'Tab.get_frame() is deprecated and will be removed in a future version. '
            'Interact with iframe WebElements directly.',
            DeprecationWarning,
            stacklevel=2,
        )
        logger.debug(f'Resolving iframe: tag={frame.tag_name}')
        if not frame.tag_name == 'iframe':
            raise NotAnIFrame

        frame_url = frame.get_attribute('src')
        logger.debug(f'Iframe src resolved: {frame_url}')
        if not frame_url:
            raise InvalidIFrame('The iframe does not have a valid src attribute')

        targets = await self._browser.get_targets()
        iframe_target = next((target for target in targets if target['url'] == frame_url), None)
        if not iframe_target:
            raise IFrameNotFound('The target for the iframe was not found')

        target_id = iframe_target['targetId']
        if target_id in self._browser._tabs_opened:
            logger.debug(f'Iframe tab already tracked: {target_id}')
            return self._browser._tabs_opened[target_id]

        tab = Tab(
            self._browser,
            target_id=target_id,
            connection_port=self._connection_port,
        )
        self._browser._tabs_opened[target_id] = tab
        logger.debug(f'Iframe tab created and registered: {target_id}')
        return tab

    async def find_shadow_roots(self, deep: bool = False, timeout: float = 0) -> list[ShadowRoot]:
        """
        Find all shadow roots in the page.

        Traverses the entire DOM tree (including iframes and nested shadow DOMs)
        to collect all shadow roots found. This is especially useful when the
        shadow host element selector is unknown or dynamic (e.g., Cloudflare
        challenge pages).

        Args:
            deep: If True, also traverses cross-origin iframes (OOPIFs) to
                discover shadow roots inside them. The returned ShadowRoot
                objects will automatically route CDP commands through the
                correct OOPIF session.
            timeout: Maximum seconds to wait for shadow roots to appear.
                When > 0, repeatedly polls the DOM (every 0.5s) until at least
                one shadow root is found or the timeout expires. Useful when
                shadow hosts are injected asynchronously (e.g., Cloudflare
                Turnstile loading inside an OOPIF).

        Returns:
            List of ShadowRoot instances found in the page.

        Raises:
            WaitElementTimeout: If timeout > 0 and no shadow roots are found
                within the specified duration.
        """
        logger.debug('Finding all shadow roots in page (timeout=%s)', timeout)

        if not timeout:
            return await self._collect_all_shadow_roots(deep)

        start_time = asyncio.get_event_loop().time()
        while True:
            shadow_roots = await self._collect_all_shadow_roots(deep)
            if shadow_roots:
                return shadow_roots

            if asyncio.get_event_loop().time() - start_time > timeout:
                raise WaitElementTimeout(
                    f'Timed out after {timeout}s waiting for shadow roots in page'
                )

            await asyncio.sleep(0.5)

    async def _collect_all_shadow_roots(self, deep: bool) -> list[ShadowRoot]:
        """Collect shadow roots from the main document and optionally OOPIFs."""
        response: GetDocumentResponse = await self._execute_command(
            DomCommands.get_document(depth=-1, pierce=True)
        )
        root_node = response.get('result', {}).get('root', {})

        shadow_root_entries: list[tuple[Node, int | None]] = []
        self._collect_shadow_roots_from_tree(root_node, shadow_root_entries)

        shadow_roots: list[ShadowRoot] = []
        for shadow_data, host_backend_id in shadow_root_entries:
            backend_node_id = shadow_data.get('backendNodeId')
            if not backend_node_id:
                continue

            try:
                resolve_response: ResolveNodeResponse = await self._execute_command(
                    DomCommands.resolve_node(backend_node_id=backend_node_id)
                )
                shadow_object_id = resolve_response['result']['object']['objectId']
            except (CommandExecutionTimeout, WebSocketConnectionClosed, KeyError):
                logger.debug(f'Failed to resolve shadow root: backend_node_id={backend_node_id}')
                continue

            try:
                host_element = await self._resolve_shadow_host(host_backend_id)
            except (CommandExecutionTimeout, WebSocketConnectionClosed, KeyError):
                logger.debug(f'Failed to resolve shadow host: backend_node_id={host_backend_id}')
                host_element = None
            mode = ShadowRootType(shadow_data.get('shadowRootType', 'open'))
            shadow_roots.append(
                ShadowRoot(
                    object_id=shadow_object_id,
                    connection_handler=self._connection_handler,
                    mode=mode,
                    host_element=host_element,
                )
            )

        if deep:
            oopif_roots = await self._collect_oopif_shadow_roots()
            shadow_roots.extend(oopif_roots)

        logger.debug(f'Found {len(shadow_roots)} shadow roots')
        return shadow_roots

    async def _resolve_shadow_host(self, host_backend_id: int | None) -> WebElement | None:
        """Resolve the host element for a shadow root (best-effort)."""
        if not host_backend_id:
            return None

        host_response: ResolveNodeResponse = await self._execute_command(
            DomCommands.resolve_node(backend_node_id=host_backend_id)
        )
        host_object_id = host_response['result']['object']['objectId']
        host_attrs = await self._get_object_attributes(object_id=host_object_id)
        return WebElement(host_object_id, self._connection_handler, attributes_list=host_attrs)

    async def _collect_oopif_shadow_roots(self) -> list[ShadowRoot]:
        """Discover shadow roots inside cross-origin iframes (OOPIFs)."""
        browser_handler = ConnectionHandler(connection_port=self._connection_port)
        targets_response: GetTargetsResponse = await browser_handler.execute_command(
            TargetCommands.get_targets()
        )

        target_infos = targets_response.get('result', {}).get('targetInfos', [])
        iframe_targets = [t for t in target_infos if t.get('type') == 'iframe']

        if not iframe_targets:
            logger.debug('No OOPIF targets found')
            return []

        shadow_roots: list[ShadowRoot] = []
        for target in iframe_targets:
            roots = await self._collect_shadow_roots_from_oopif_target(target, browser_handler)
            shadow_roots.extend(roots)

        logger.debug(f'Found {len(shadow_roots)} shadow roots in OOPIFs')
        return shadow_roots

    async def _collect_shadow_roots_from_oopif_target(
        self,
        target: TargetInfo,
        browser_handler: ConnectionHandler,
    ) -> list[ShadowRoot]:
        """Collect shadow roots from a single OOPIF target."""
        target_id = target.get('targetId', '')
        try:
            attach_response: AttachToTargetResponse = await browser_handler.execute_command(
                TargetCommands.attach_to_target(target_id=target_id, flatten=True)
            )
            session_id = attach_response.get('result', {}).get('sessionId')
            if not session_id:
                return []
        except (CommandExecutionTimeout, WebSocketConnectionClosed):
            logger.debug(f'Failed to attach to OOPIF target: {target_id}')
            return []

        try:
            get_doc_command = DomCommands.get_document(depth=-1, pierce=True)
            get_doc_command['sessionId'] = session_id
            doc_response: GetDocumentResponse = await browser_handler.execute_command(
                get_doc_command
            )
            root_node = doc_response.get('result', {}).get('root', {})
        except (CommandExecutionTimeout, WebSocketConnectionClosed):
            logger.debug(f'Failed to get document from OOPIF target: {target_id}')
            return []

        entries: list[tuple[Node, int | None]] = []
        self._collect_shadow_roots_from_tree(root_node, entries)

        iframe_context = IFrameContext(
            frame_id=target_id,
            session_handler=browser_handler,
            session_id=session_id,
        )

        results: list[ShadowRoot] = []
        for shadow_data, host_backend_id in entries:
            sr = await self._resolve_oopif_shadow_entry(
                shadow_data, host_backend_id, browser_handler, session_id, iframe_context
            )
            if sr:
                results.append(sr)
        return results

    async def _resolve_oopif_shadow_entry(
        self,
        shadow_data: Node,
        host_backend_id: int | None,
        browser_handler: ConnectionHandler,
        session_id: str,
        iframe_context: IFrameContext,
    ) -> ShadowRoot | None:
        """Resolve a single shadow root entry from an OOPIF."""
        backend_node_id = shadow_data.get('backendNodeId')
        if not backend_node_id:
            return None

        try:
            resolve_command = DomCommands.resolve_node(backend_node_id=backend_node_id)
            resolve_command['sessionId'] = session_id
            resolve_response: ResolveNodeResponse = await browser_handler.execute_command(
                resolve_command
            )
            shadow_object_id = resolve_response['result']['object']['objectId']
        except (CommandExecutionTimeout, WebSocketConnectionClosed, KeyError):
            logger.debug(f'Failed to resolve OOPIF shadow root: backend_node_id={backend_node_id}')
            return None

        host_element = await self._resolve_oopif_shadow_host(
            host_backend_id, browser_handler, session_id
        )

        if host_element:
            host_element._iframe_context = iframe_context

        mode = ShadowRootType(shadow_data.get('shadowRootType', 'open'))
        sr = ShadowRoot(
            object_id=shadow_object_id,
            connection_handler=self._connection_handler,
            mode=mode,
            host_element=host_element,
        )

        if not host_element:
            sr._iframe_context = iframe_context

        return sr

    async def _resolve_oopif_shadow_host(
        self,
        host_backend_id: int | None,
        browser_handler: ConnectionHandler,
        session_id: str,
    ) -> WebElement | None:
        """Resolve the host element for a shadow root inside an OOPIF (best-effort)."""
        if not host_backend_id:
            return None

        try:
            resolve_command = DomCommands.resolve_node(backend_node_id=host_backend_id)
            resolve_command['sessionId'] = session_id
            host_response: ResolveNodeResponse = await browser_handler.execute_command(
                resolve_command
            )
            host_object_id = host_response['result']['object']['objectId']

            describe_command = DomCommands.describe_node(object_id=host_object_id)
            describe_command['sessionId'] = session_id
            describe_response: DescribeNodeResponse = await browser_handler.execute_command(
                describe_command
            )
            node_info = describe_response.get('result', {}).get('node', {})
            attributes = node_info.get('attributes', [])
            tag_name = node_info.get('nodeName', '').lower()
            attributes.extend(['tag_name', tag_name])

            return WebElement(host_object_id, self._connection_handler, attributes_list=attributes)
        except (CommandExecutionTimeout, WebSocketConnectionClosed, KeyError):
            logger.debug(f'Failed to resolve OOPIF shadow host: backend_node_id={host_backend_id}')
            return None

    @staticmethod
    def _collect_shadow_roots_from_tree(node: Node, results: list[tuple[Node, int | None]]) -> None:
        """Recursively walk a DOM tree collecting shadow root entries."""
        host_backend_id = node.get('backendNodeId')
        for shadow_root in node.get('shadowRoots', []):
            results.append((shadow_root, host_backend_id))
            Tab._collect_shadow_roots_from_tree(shadow_root, results)

        for child in node.get('children', []):
            Tab._collect_shadow_roots_from_tree(child, results)

        content_doc = node.get('contentDocument')
        if content_doc:
            Tab._collect_shadow_roots_from_tree(content_doc, results)

    async def bring_to_front(self):
        """Brings the page to front."""
        logger.info('Bringing page to front')
        return await self._execute_command(PageCommands.bring_to_front())

    async def get_cookies(self) -> list[Cookie]:
        """Get all cookies accessible from current page."""
        logger.debug('Fetching cookies for current page')
        if self._browser_context_id:
            response_storage: StorageGetCookiesResponse = await self._execute_command(
                StorageCommands.get_cookies(self._browser_context_id)
            )
            cookies = response_storage['result']['cookies']
            logger.debug(f'Fetched {len(cookies)} cookies')
            return cookies

        response_network: NetworkGetCookiesResponse = await self._execute_command(
            NetworkCommands.get_cookies()
        )
        cookies = response_network['result']['cookies']
        logger.debug(f'Fetched {len(cookies)} cookies')
        return cookies

    async def get_network_response_body(self, request_id: str) -> str:
        """
        Get the response body for a given request ID.

        Args:
            request_id: Request ID to get the response body for.

        Returns:
            The response body for the given request ID.

        Raises:
            NetworkEventsNotEnabled: If network events are not enabled.
        """
        if not self.network_events_enabled:
            raise NetworkEventsNotEnabled('Network events must be enabled to get response body')

        response: GetResponseBodyResponse = await self._execute_command(
            NetworkCommands.get_response_body(request_id)
        )
        logger.debug(f'Retrieved network response body for request_id={request_id}')
        return response['result']['body']

    async def get_network_logs(self, filter: Optional[str] = None) -> list[RequestWillBeSentEvent]:
        """
        Get network logs.

        Args:
            filter: Filter to apply to the network logs.

        Returns:
            The network logs.

        Raises:
            NetworkEventsNotEnabled: If network events are not enabled.
        """
        if not self.network_events_enabled:
            raise NetworkEventsNotEnabled('Network events must be enabled to get network logs')

        logs = self._connection_handler.network_logs
        if filter:
            logs = [
                log for log in logs if filter in log['params'].get('request', {}).get('url', '')
            ]
        logger.debug(f'Returning {len(logs)} network logs (filtered={bool(filter)})')
        return logs

    async def set_cookies(self, cookies: list[CookieParam]):
        """
        Set multiple cookies for current page.

        Args:
            cookies: Cookie parameters (name/value required, others optional).

        Note:
            Defaults to current page's domain if not specified.
        """
        logger.info(f'Setting {len(cookies)} cookies on current page')
        return await self._execute_command(
            StorageCommands.set_cookies(cookies, self._browser_context_id)
        )

    async def delete_all_cookies(self):
        """Delete all cookies from current browser context."""
        logger.info('Clearing all cookies from current browser context')
        return await self._execute_command(StorageCommands.clear_cookies(self._browser_context_id))

    async def go_to(self, url: str, timeout: int = 300):
        """
        Navigate to URL and wait for loading to complete.

        Refreshes if URL matches current page.

        Args:
            url: Target URL to navigate to.
            timeout: Maximum seconds to wait for page load (default 300).

        Raises:
            PageLoadTimeout: If page doesn't finish loading within timeout.
        """
        logger.info(f'Navigating to URL: {url} (timeout={timeout}s)')
        if await self._refresh_if_url_not_changed(url):
            logger.debug('URL matches current page; refreshing instead')
            return

        await self._execute_command(PageCommands.navigate(url))

        try:
            await self._wait_page_load(timeout=timeout)
            logger.info(f'Navigation complete: {url}')
        except WaitElementTimeout:
            logger.error(f'Page load timeout after {timeout}s for URL: {url}')
            raise PageLoadTimeout()

    async def refresh(
        self,
        ignore_cache: bool = False,
        script_to_evaluate_on_load: Optional[str] = None,
    ):
        """
        Reload current page and wait for completion.

        Args:
            ignore_cache: Bypass browser cache if True.
            script_to_evaluate_on_load: JavaScript to execute after load.

        Raises:
            PageLoadTimeout: If page doesn't finish loading within timeout.
        """
        logger.info(
            f'Reloading page (ignore_cache={ignore_cache}, '
            f'script_on_load={bool(script_to_evaluate_on_load)})'
        )
        await self._execute_command(
            PageCommands.reload(
                ignore_cache=ignore_cache, script_to_evaluate_on_load=script_to_evaluate_on_load
            )
        )
        try:
            await self._wait_page_load()
            logger.info('Page reloaded successfully')
        except WaitElementTimeout:
            logger.error('Page reload timed out')
            raise PageLoadTimeout()

    async def take_screenshot(
        self,
        path: Optional[str | Path] = None,
        quality: int = 100,
        beyond_viewport: bool = False,
        as_base64: bool = False,
    ) -> Optional[str]:
        """
        Capture screenshot of current page.

        Args:
            path: File path for screenshot (extension determines format).
            quality: Image quality 0-100 (default 100).
            beyond_viewport: The page will be scrolled to the bottom and the screenshot will
                include the entire page
            as_base64: Return as base64 string instead of saving file.

        Returns:
            Base64 screenshot data if as_base64=True, None otherwise.

        Raises:
            InvalidFileExtension: If file extension not supported.
            MissingScreenshotPath: If path is None and as_base64 is False.
        """
        if not path and not as_base64:
            raise MissingScreenshotPath()

        if path and isinstance(path, str):
            output_extension = path.split('.')[-1]
        elif path and isinstance(path, Path):
            output_extension = path.suffix.lstrip('.')
        else:
            output_extension = ScreenshotFormat.JPEG

        # Normalize jpg to jpeg (CDP only accepts jpeg)
        output_extension = (
            output_extension.replace('jpg', 'jpeg')
            if output_extension == 'jpg'
            else output_extension
        )

        if not ScreenshotFormat.has_value(output_extension):
            raise InvalidFileExtension(f'{output_extension} extension is not supported.')

        output_format = ScreenshotFormat.get_value(output_extension)

        logger.info(
            f'Taking screenshot: path={path}, quality={quality}, '
            f'beyond_viewport={beyond_viewport}, as_base64={as_base64}'
        )
        response: CaptureScreenshotResponse = await self._execute_command(
            PageCommands.capture_screenshot(
                format=output_format,
                quality=quality,
                capture_beyond_viewport=beyond_viewport,
            )
        )

        try:
            screenshot_data = response['result']['data']
        except KeyError:
            raise TopLevelTargetRequired(
                'Command can only be executed on top-level targets. Please use '
                'take_screenshot method on the WebElement object instead.'
            )

        if as_base64:
            logger.info('Screenshot captured and returned as base64')
            return screenshot_data

        if path:
            screenshot_bytes = decode_base64_to_bytes(screenshot_data)
            async with aiofiles.open(str(path), 'wb') as file:
                await file.write(screenshot_bytes)
            logger.info(f'Screenshot saved to: {path}')

        return None

    async def print_to_pdf(
        self,
        path: Optional[str | Path] = None,
        landscape: bool = False,
        display_header_footer: bool = False,
        print_background: bool = True,
        scale: float = 1.0,
        as_base64: bool = False,
    ) -> Optional[str]:
        """
        Generate PDF of current page.

        Args:
            path: File path for PDF output. Required if as_base64=False.
            landscape: Use landscape orientation.
            display_header_footer: Include header/footer.
            print_background: Include background graphics.
            scale: Scale factor (0.1-2.0).
            as_base64: Return as base64 string instead of saving.

        Returns:
            Base64 PDF data if as_base64=True, None otherwise.

        Raises:
            ValueError: If path is not provided when as_base64=False.
        """
        logger.info(
            f'Generating PDF: path={path}, landscape={landscape}, '
            f'header_footer={display_header_footer}, print_bg={print_background}, '
            f'scale={scale}, as_base64={as_base64}'
        )
        response: PrintToPDFResponse = await self._execute_command(
            PageCommands.print_to_pdf(
                landscape=landscape,
                display_header_footer=display_header_footer,
                print_background=print_background,
                scale=scale,
            )
        )
        pdf_data = response['result']['data']
        if as_base64:
            logger.info('PDF generated and returned as base64')
            return pdf_data

        if path is None:
            raise ValueError('path is required when as_base64=False')

        pdf_bytes = decode_base64_to_bytes(pdf_data)
        async with aiofiles.open(path, 'wb') as file:
            await file.write(pdf_bytes)
        logger.info(f'PDF saved to: {path}')

        return None

    async def has_dialog(self) -> bool:
        """
        Check if JavaScript dialog is currently displayed.

        Note:
            Page events must be enabled to detect dialogs.
        """
        if self._connection_handler.dialog:
            logger.debug('Dialog present')
            return True

        return False

    async def get_dialog_message(self) -> str:
        """
        Get message text from current JavaScript dialog.

        Raises:
            NoDialogPresent: If no dialog is currently displayed.
        """
        if not await self.has_dialog():
            raise NoDialogPresent()
        message = self._connection_handler.dialog['params']['message']
        logger.debug(f'Dialog message retrieved: {message}')
        return message

    async def handle_dialog(self, accept: bool, prompt_text: Optional[str] = None):
        """
        Respond to JavaScript dialog.

        Args:
            accept: Accept/confirm dialog if True, dismiss/cancel if False.
            prompt_text: Text for prompt dialogs (ignored for alert/confirm).

        Raises:
            NoDialogPresent: If no dialog is currently displayed.

        Note:
            Page events must be enabled to handle dialogs.
        """
        if not await self.has_dialog():
            raise NoDialogPresent()
        logger.info(f'Handling dialog: accept={accept}, has_prompt_text={bool(prompt_text)}')
        return await self._execute_command(
            PageCommands.handle_javascript_dialog(accept=accept, prompt_text=prompt_text)
        )

    @overload
    async def execute_script(
        self,
        script: str,
        *,
        object_group: Optional[str] = None,
        include_command_line_api: Optional[bool] = None,
        silent: Optional[bool] = None,
        context_id: Optional[int] = None,
        return_by_value: Optional[bool] = None,
        generate_preview: Optional[bool] = None,
        user_gesture: Optional[bool] = None,
        await_promise: Optional[bool] = None,
        throw_on_side_effect: Optional[bool] = None,
        timeout: Optional[float] = None,
        disable_breaks: Optional[bool] = None,
        repl_mode: Optional[bool] = None,
        allow_unsafe_eval_blocked_by_csp: Optional[bool] = None,
        unique_context_id: Optional[str] = None,
        serialization_options: Optional[SerializationOptions] = None,
    ) -> EvaluateResponse: ...

    @overload
    async def execute_script(
        self,
        script: str,
        element: WebElement,
        *,
        arguments: Optional[list[CallArgument]] = None,
        silent: Optional[bool] = None,
        return_by_value: Optional[bool] = None,
        generate_preview: Optional[bool] = None,
        user_gesture: Optional[bool] = None,
        await_promise: Optional[bool] = None,
        execution_context_id: Optional[int] = None,
        object_group: Optional[str] = None,
        throw_on_side_effect: Optional[bool] = None,
        unique_context_id: Optional[str] = None,
        serialization_options: Optional[SerializationOptions] = None,
    ) -> CallFunctionOnResponse: ...

    async def execute_script(
        self,
        script: str,
        element: Optional[WebElement] = None,
        *,
        arguments: Optional[list[CallArgument]] = None,
        object_group: Optional[str] = None,
        include_command_line_api: Optional[bool] = None,
        silent: Optional[bool] = None,
        context_id: Optional[int] = None,
        return_by_value: Optional[bool] = None,
        generate_preview: Optional[bool] = None,
        user_gesture: Optional[bool] = None,
        await_promise: Optional[bool] = None,
        execution_context_id: Optional[int] = None,
        throw_on_side_effect: Optional[bool] = None,
        timeout: Optional[float] = None,
        disable_breaks: Optional[bool] = None,
        repl_mode: Optional[bool] = None,
        allow_unsafe_eval_blocked_by_csp: Optional[bool] = None,
        unique_context_id: Optional[str] = None,
        serialization_options: Optional[SerializationOptions] = None,
    ) -> Union[EvaluateResponse, CallFunctionOnResponse]:
        """
        Execute JavaScript in page context.

        Args:
            script (str): JavaScript code to execute.
            element (Optional[WebElement]): Optional WebElement to execute script on.
            arguments (Optional[list[CallArgument]]): Arguments to pass to the function.
            object_group (Optional[str]): Symbolic group name for the result (Runtime.evaluate).
            include_command_line_api (Optional[bool]): Whether to include command line API
                (Runtime.evaluate).
            silent (Optional[bool]): Whether to silence exceptions (Runtime.evaluate).
            context_id (Optional[int]): ID of the execution context to evaluate in
                (Runtime.evaluate).
            return_by_value (Optional[bool]): Whether to return the result by value instead of
                reference (Runtime.evaluate).
            generate_preview (Optional[bool]): Whether to generate a preview for the result
                (Runtime.evaluate).
            user_gesture (Optional[bool]): Whether to treat evaluation as initiated by user
                gesture (Runtime.evaluate).
            await_promise (Optional[bool]): Whether to await promise result (Runtime.evaluate).
            execution_context_id (Optional[int]): ID of the execution context to call the
                function in.
            throw_on_side_effect (Optional[bool]): Whether to throw if side effect cannot be
                ruled out (Runtime.evaluate).
            timeout (Optional[float]): Timeout in milliseconds (Runtime.evaluate).
            disable_breaks (Optional[bool]): Whether to disable breakpoints during evaluation
                (Runtime.evaluate).
            repl_mode (Optional[bool]): Whether to execute in REPL mode (Runtime.evaluate).
            allow_unsafe_eval_blocked_by_csp (Optional[bool]): Allow unsafe evaluation
                (Runtime.evaluate).
            unique_context_id (Optional[str]): Unique context ID for evaluation
                (Runtime.evaluate).
            serialization_options (Optional[SerializationOptions]): Serialization options for
                the result (Runtime.evaluate).

        Returns:
            Union[EvaluateResponse, CallFunctionOnResponse]: The result of the script execution.

        Raises:
            InvalidScriptWithElement: If script uses 'argument' keyword but no element is provided.

        Examples:
            # Execute a simple script to log a message
            await page.execute_script('console.log("Hello World")')

            # Execute a script that returns the page title
            await page.execute_script('return document.title')

            # Execute a script on an element to click it
            await page.execute_script('argument.click()', element)

            # Execute a script on an element to set its value
            await page.execute_script('argument.value = "Hello"', element)
        """
        logger.debug(f'Executing script: with_element={bool(element)}, length={len(script)}')
        if element is not None:
            warnings.warn(
                'Passing a WebElement to Tab.execute_script() is deprecated. '
                'Use WebElement.execute_script() instead.',
                DeprecationWarning,
                stacklevel=2,
            )

            return await element.execute_script(
                script,
                arguments=arguments,
                silent=silent,
                return_by_value=return_by_value,
                generate_preview=generate_preview,
                user_gesture=user_gesture,
                await_promise=await_promise,
                execution_context_id=execution_context_id,
                object_group=object_group,
                throw_on_side_effect=throw_on_side_effect,
                unique_context_id=unique_context_id,
                serialization_options=serialization_options,
            )

        if has_return_outside_function(script):
            script = f'(function(){{ {script} }})()'

        command = self._get_evaluate_command(
            script,
            object_group=object_group,
            include_command_line_api=include_command_line_api,
            silent=silent,
            context_id=context_id,
            return_by_value=return_by_value,
            generate_preview=generate_preview,
            user_gesture=user_gesture,
            await_promise=await_promise,
            throw_on_side_effect=throw_on_side_effect,
            timeout=timeout,
            disable_breaks=disable_breaks,
            repl_mode=repl_mode,
            allow_unsafe_eval_blocked_by_csp=allow_unsafe_eval_blocked_by_csp,
            unique_context_id=unique_context_id,
            serialization_options=serialization_options,
        )
        logger.debug(f'Executing script without element: length={len(script)}')
        result: Union[EvaluateResponse, CallFunctionOnResponse] = await self._execute_command(
            command
        )
        self._validate_argument_error(result)
        return result

    # TODO: think about how to remove these duplications with the base class
    async def continue_request(
        self,
        request_id: str,
        url: Optional[str] = None,
        method: Optional[RequestMethod] = None,
        post_data: Optional[str] = None,
        headers: Optional[list[HeaderEntry]] = None,
        intercept_response: Optional[bool] = None,
    ):
        """
        Continue paused request without modifications.
        """
        logger.debug(f'Continue request on tab: id={request_id}')
        return await self._execute_command(
            FetchCommands.continue_request(
                request_id=request_id,
                url=url,
                method=method,
                post_data=post_data,
                headers=headers,
                intercept_response=intercept_response,
            )
        )

    async def fail_request(self, request_id: str, error_reason: ErrorReason):
        """Fail request with error code."""
        logger.debug(f'Fail request on tab: id={request_id}, reason={error_reason}')
        return await self._execute_command(FetchCommands.fail_request(request_id, error_reason))

    async def fulfill_request(
        self,
        request_id: str,
        response_code: int,
        response_headers: Optional[list[HeaderEntry]] = None,
        body: Optional[str] = None,
        response_phrase: Optional[str] = None,
    ):
        """Fulfill request with response data."""
        logger.debug(
            f'Fulfill request on tab: id={request_id}, code={response_code}, '
            f'headers_set={bool(response_headers)}, body_set={bool(body)}'
        )
        return await self._execute_command(
            FetchCommands.fulfill_request(
                request_id=request_id,
                response_code=response_code,
                response_headers=response_headers,
                body=body,
                response_phrase=response_phrase,
            )
        )

    async def continue_with_auth(
        self,
        request_id: str,
        auth_challenge_response: AuthChallengeResponseType,
        proxy_username: Optional[str] = None,
        proxy_password: Optional[str] = None,
    ):
        """Continue a paused request replying to an authentication challenge.

        Useful for proxy auth (407) or server auth (401) when Fetch is enabled
        with handle_auth=True.
        """
        logger.debug(
            f'Continue with auth on tab: id={request_id}, response={auth_challenge_response}, '
            f'user_set={bool(proxy_username)}'
        )
        return await self._execute_command(
            FetchCommands.continue_request_with_auth(
                request_id=request_id,
                auth_challenge_response=auth_challenge_response,
                proxy_username=proxy_username,
                proxy_password=proxy_password,
            )
        )

    @asynccontextmanager
    async def expect_file_chooser(
        self, files: str | Path | list[str | Path]
    ) -> AsyncGenerator[None, None]:
        """
        Context manager for automatic file upload handling.

        Args:
            files: File path(s) for upload.
        """

        async def event_handler(event: FileChooserOpenedEvent):
            logger.info('File chooser opened; setting files')
            file_list = [str(file) for file in files] if isinstance(files, list) else [str(files)]
            await self._execute_command(
                DomCommands.set_file_input_files(
                    files=file_list,
                    backend_node_id=event['params']['backendNodeId'],
                )
            )
            logger.debug(f'Files set on input: {file_list}')

        if self.page_events_enabled is False:
            _before_page_events_enabled = False
            await self.enable_page_events()
        else:
            _before_page_events_enabled = True

        if self.intercept_file_chooser_dialog_enabled is False:
            await self.enable_intercept_file_chooser_dialog()

        logger.info('Waiting for file chooser to open')
        await self.on(
            PageEvent.FILE_CHOOSER_OPENED,
            cast(Callable[[dict], Any], event_handler),
            temporary=True,
        )

        yield

        if self.intercept_file_chooser_dialog_enabled is True:
            await self.disable_intercept_file_chooser_dialog()

        if _before_page_events_enabled is False:
            await self.disable_page_events()

    @asynccontextmanager
    async def expect_and_bypass_cloudflare_captcha(
        self,
        custom_selector: Optional[tuple[By, str]] = None,
        time_before_click: Optional[float] = None,
        time_to_wait_captcha: float = 5,
    ) -> AsyncGenerator[None, None]:
        """
        Context manager for automatic Cloudflare captcha bypass.

        Args:
            custom_selector: Deprecated — ignored. Cloudflare Turnstile is now
                detected automatically via shadow root inspection.
            time_before_click: Deprecated — ignored. The checkbox is now
                located via shadow root polling and clicked immediately.
            time_to_wait_captcha: Timeout for captcha detection (default 5s).
        """
        if custom_selector is not None:
            warnings.warn(
                'custom_selector is deprecated and ignored. Cloudflare Turnstile is now '
                'detected automatically via shadow root inspection.',
                DeprecationWarning,
                stacklevel=2,
            )

        if time_before_click is not None:
            warnings.warn(
                'time_before_click is deprecated and ignored. The checkbox is now '
                'located via shadow root polling and clicked immediately.',
                DeprecationWarning,
                stacklevel=2,
            )

        captcha_processed = asyncio.Event()

        async def bypass_cloudflare(_: dict):
            try:
                await self._bypass_cloudflare(
                    _,
                    time_to_wait_captcha=time_to_wait_captcha,
                )
            finally:
                captcha_processed.set()

        _before_page_events_enabled = self.page_events_enabled

        if not _before_page_events_enabled:
            await self.enable_page_events()

        logger.info('Expecting and bypassing Cloudflare captcha if present')
        callback_id = await self.on(PageEvent.LOAD_EVENT_FIRED, bypass_cloudflare)

        try:
            yield
            await captcha_processed.wait()
        finally:
            await self._connection_handler.remove_callback(callback_id)
            if not _before_page_events_enabled:
                await self.disable_page_events()

    @asynccontextmanager
    async def expect_download(
        self,
        keep_file_at: Optional[Union[str, Path]] = None,
        timeout: Optional[float] = None,
    ) -> AsyncGenerator[_DownloadHandle, None]:
        """
        Context manager for handling a file download triggered inside the block.

        Behavior:
        - If keep_file_at is provided, configure browser to save into that directory and keep file.
        - Otherwise, a temporary directory is used and cleaned up after the context.

        Args:
            keep_file_at: Directory to persist the file. If None, uses a temporary
                directory and cleans it up afterwards.
            timeout: Max seconds to wait for download completion. Defaults to 60.

        Yields:
            _DownloadHandle: Handle to read the downloaded file (bytes/base64) and check its path.
        """
        download_timeout = 60.0 if timeout is None else float(timeout)

        cleanup_dir = False
        if keep_file_at is None:
            download_dir = mkdtemp(prefix='pydoll-download-')
            cleanup_dir = True
        else:
            download_dir = str(Path(keep_file_at))
            Path(download_dir).mkdir(parents=True, exist_ok=True)

        logger.info(f'Expecting download (dir={download_dir}, timeout={download_timeout}s)')
        await self._browser.set_download_behavior(
            behavior=DownloadBehavior.ALLOW,
            download_path=download_dir,
            browser_context_id=self._browser_context_id,
        )

        _page_events_was_enabled = True
        if not self._page_events_enabled:
            _page_events_was_enabled = False
            await self.enable_page_events()

        loop = asyncio.get_event_loop()
        will_begin: asyncio.Future[bool] = loop.create_future()
        done: asyncio.Future[bool] = loop.create_future()
        state: dict[str, Any] = {
            'guid': None,
            'url': None,
            'suggestedFilename': None,
            'filePath': None,
            'dir': download_dir,
        }

        async def on_will_begin(event: DownloadWillBeginEvent):
            params = event['params']
            state['guid'] = params['guid']
            state['url'] = params['url']
            state['suggestedFilename'] = params['suggestedFilename']
            if not will_begin.done():
                will_begin.set_result(True)
            logger.info(
                f'Download will begin: url={state["url"]}, filename={state["suggestedFilename"]}'
            )

        async def on_progress(event: DownloadProgressEvent):
            params = event['params']
            guid = params['guid']
            if (
                state.get('guid')
                and guid != state['guid']
                or params['state'] != DownloadProgressState.COMPLETED
            ):
                return
            file_path = params.get('filePath')
            if not file_path:
                file_path = str(Path(download_dir) / state['suggestedFilename'])
            state['filePath'] = file_path
            if not done.done():
                done.set_result(True)
            logger.info(f'Download completed: {file_path}')

        await self.on(
            PageEvent.DOWNLOAD_WILL_BEGIN,
            cast(Callable[[dict], Awaitable[Any]], on_will_begin),
            True,
        )
        cb_id_progress = await self.on(
            PageEvent.DOWNLOAD_PROGRESS,
            cast(Callable[[dict], Awaitable[Any]], on_progress),
            False,
        )

        handle = _DownloadHandle(
            state=state,
            will_begin_future=will_begin,
            done_future=done,
            timeout=download_timeout,
        )

        try:
            yield handle
            try:
                await asyncio.wait_for(done, timeout=download_timeout)
            except asyncio.TimeoutError as exc:
                raise DownloadTimeout() from exc
        finally:
            await self._cleanup_download_context(
                cb_id_progress,
                _page_events_was_enabled,
                cleanup_dir,
                state,
                download_dir,
            )

    async def _cleanup_download_context(
        self,
        cb_id_progress: int,
        page_events_was_enabled: bool,
        cleanup_dir: bool,
        state: dict[str, Any],
        download_dir: str,
    ) -> None:
        await self.remove_callback(cb_id_progress)
        await self._browser.set_download_behavior(
            behavior=DownloadBehavior.DEFAULT,
            browser_context_id=self._browser_context_id,
        )

        if cleanup_dir:
            file_path = state['filePath']
            if not file_path:
                return
            Path(file_path).unlink(missing_ok=True)
            shutil.rmtree(download_dir, ignore_errors=True)

        if not page_events_was_enabled:
            await self.disable_page_events()

    @overload
    async def on(
        self, event_name: str, callback: Callable[[dict], Any], temporary: bool = False
    ) -> int: ...
    @overload
    async def on(
        self, event_name: str, callback: Callable[[dict], Awaitable[Any]], temporary: bool = False
    ) -> int: ...
    async def on(
        self,
        event_name,
        callback,
        temporary=False,
    ) -> int:
        """
        Register CDP event listener.

        Callback runs in background task to prevent blocking.

        Args:
            event_name: CDP event name (e.g., 'Page.loadEventFired').
            callback: Function called on event (sync or async).
            temporary: Remove after first invocation.

        Returns:
            Callback ID for removal.

        Note:
            Corresponding domain must be enabled before events fire.
        """

        async def callback_wrapper(event):
            asyncio.create_task(callback(event))

        if asyncio.iscoroutinefunction(callback):
            function_to_register = callback_wrapper
        else:
            function_to_register = callback

        logger.debug(
            f'Registering callback on tab: event={event_name}, temporary={temporary}, '
            f'async={asyncio.iscoroutinefunction(callback)}'
        )
        return await self._connection_handler.register_callback(
            event_name, function_to_register, temporary
        )

    async def remove_callback(self, callback_id: int):
        """Remove callback from tab."""
        logger.debug(f'Removing callback from tab: id={callback_id}')
        return await self._connection_handler.remove_callback(callback_id)

    async def clear_callbacks(self):
        """Clear all registered event callbacks."""
        logger.debug('Clearing all callbacks from tab')
        await self._connection_handler.clear_callbacks()

    def _get_connection_handler(self) -> ConnectionHandler:
        if self._ws_address:
            logger.debug('Using WebSocket address for connection handler')
            return ConnectionHandler(ws_address=self._ws_address)
        logger.debug(
            'Using port/target for connection handler: '
            f'port={self._connection_port}, target_id={self._target_id}'
        )
        return ConnectionHandler(self._connection_port, self._target_id)

    @staticmethod
    def _get_evaluate_command(
        script: str,
        *,
        object_group: Optional[str] = None,
        include_command_line_api: Optional[bool] = None,
        silent: Optional[bool] = None,
        context_id: Optional[int] = None,
        return_by_value: Optional[bool] = None,
        generate_preview: Optional[bool] = None,
        user_gesture: Optional[bool] = None,
        await_promise: Optional[bool] = None,
        throw_on_side_effect: Optional[bool] = None,
        timeout: Optional[float] = None,
        disable_breaks: Optional[bool] = None,
        repl_mode: Optional[bool] = None,
        allow_unsafe_eval_blocked_by_csp: Optional[bool] = None,
        unique_context_id: Optional[str] = None,
        serialization_options: Optional[SerializationOptions] = None,
    ):
        """Create an evaluate command with the given parameters."""
        return RuntimeCommands.evaluate(
            expression=script,
            object_group=object_group,
            include_command_line_api=include_command_line_api,
            silent=silent,
            context_id=context_id,
            return_by_value=return_by_value,
            generate_preview=generate_preview,
            user_gesture=user_gesture,
            await_promise=await_promise,
            throw_on_side_effect=throw_on_side_effect,
            timeout=timeout,
            disable_breaks=disable_breaks,
            repl_mode=repl_mode,
            allow_unsafe_eval_blocked_by_csp=allow_unsafe_eval_blocked_by_csp,
            unique_context_id=unique_context_id,
            serialization_options=serialization_options,
        )

    async def _refresh_if_url_not_changed(self, url: str) -> bool:
        """Refresh page if URL hasn't changed."""
        current_url = await self.current_url
        if current_url == url:
            await self.refresh()
            return True
        return False

    @staticmethod
    def _validate_argument_error(response: EvaluateResponse) -> None:
        """
        Validate that script didn't fail with ReferenceError about 'argument' being undefined.

        Raises:
            InvalidScriptWithElement: If script uses 'argument' keyword but no element was provided.
        """
        evaluate_result = response.get('result')
        if not isinstance(evaluate_result, dict):
            return

        remote_object = evaluate_result.get('result')
        if not isinstance(remote_object, dict):
            return

        if not (
            remote_object.get('type') == 'object'
            and remote_object.get('subtype') == 'error'
            and remote_object.get('className') == 'ReferenceError'
        ):
            return

        description = remote_object.get('description', '')
        if 'argument is not defined' in description:
            raise InvalidScriptWithElement('Script contains "argument" but no element was provided')

    async def _wait_page_load(self, timeout: int = 300):
        """
        Wait for page to finish loading.

        Waits until ``document.readyState`` reaches **at least** the level
        configured in ``browser.options.page_load_state``.  For example, when
        the target state is ``interactive``, both ``"interactive"`` and
        ``"complete"`` satisfy the condition — this prevents an infinite
        polling loop when the page transitions past ``interactive`` before the
        first check runs.

        Raises:
            WaitElementTimeout: If page doesn't load within *timeout* seconds.
        """
        target_state = self._browser.options.page_load_state.value
        target_index = self._READY_STATE_ORDER.index(target_state)
        start_time = asyncio.get_event_loop().time()
        logger.debug(f'Waiting for page load (timeout={timeout}s)')
        while True:
            response: EvaluateResponse = await self._execute_command(
                RuntimeCommands.evaluate(expression='document.readyState')
            )
            current_state = response['result']['result']['value']
            current_index = self._READY_STATE_ORDER.index(current_state)
            if current_index >= target_index:
                logger.debug(f'Page load state reached: {current_state} (target: {target_state})')
                break
            if asyncio.get_event_loop().time() - start_time > timeout:
                raise WaitElementTimeout('Page load timed out')
            await asyncio.sleep(0.5)

    async def _find_cloudflare_shadow_root(self, timeout: float) -> ShadowRoot:
        """Poll for the Cloudflare Turnstile shadow root.

        Repeatedly calls ``find_shadow_roots(deep=False)`` and checks each
        shadow root's ``inner_html`` for the Cloudflare challenge domain.

        Args:
            timeout: Maximum seconds to wait for the shadow root.

        Returns:
            The first ShadowRoot whose inner HTML contains
            ``challenges.cloudflare.com``.

        Raises:
            WaitElementTimeout: If no matching shadow root is found within
                *timeout* seconds.
        """
        start_time = asyncio.get_event_loop().time()
        while True:
            shadow_roots = await self.find_shadow_roots(deep=False)
            for sr in shadow_roots:
                html = await sr.inner_html
                if _CLOUDFLARE_CHALLENGE_DOMAIN in html:
                    return sr

            if asyncio.get_event_loop().time() - start_time > timeout:
                raise WaitElementTimeout(
                    f'Timed out after {timeout}s waiting for Cloudflare Turnstile shadow root'
                )
            await asyncio.sleep(0.5)

    async def _bypass_cloudflare(
        self,
        event: dict,
        time_to_wait_captcha: float = 5,
    ) -> None:
        """Attempt to bypass Cloudflare Turnstile captcha via shadow root traversal.

        Traverses shadow roots to locate the Cloudflare iframe, navigates into
        it, and clicks the actual checkbox element (``span.cb-i``).
        """
        try:
            timeout_int = int(time_to_wait_captcha)
            shadow_root = await self._find_cloudflare_shadow_root(
                timeout=time_to_wait_captcha,
            )
            iframe = await shadow_root.query(_CLOUDFLARE_IFRAME_SELECTOR, timeout=timeout_int)
            body = await iframe.find(tag_name='body', timeout=timeout_int)
            inner_shadow = await body.get_shadow_root(timeout=time_to_wait_captcha)
            checkbox = await inner_shadow.query(_CLOUDFLARE_CHECKBOX_SELECTOR, timeout=timeout_int)
            await checkbox.click()
        except Exception as exc:
            logger.error(f'Error in cloudflare bypass: {exc}')


class _DownloadHandle:
    """Handle returned by expect_download to access the downloaded file."""

    def __init__(
        self,
        state: dict[str, Any],
        will_begin_future: asyncio.Future[bool],
        done_future: asyncio.Future[bool],
        timeout: float,
    ) -> None:
        self._state = state
        self._will_begin_future = will_begin_future
        self._done_future = done_future
        self._timeout = timeout

    @property
    def file_path(self) -> Optional[str]:
        return self._state.get('filePath')

    async def wait_started(self, timeout: Optional[float] = None) -> None:
        await asyncio.wait_for(self._will_begin_future, timeout=timeout or self._timeout)

    async def wait_finished(self, timeout: Optional[float] = None) -> None:
        await asyncio.wait_for(self._done_future, timeout=timeout or self._timeout)

    async def read_bytes(self) -> bytes:
        await self.wait_finished()
        if not self.file_path:
            raise FileNotFoundError('Download file path not available')
        async with aiofiles.open(self.file_path, 'rb') as f:  # type: ignore[arg-type]
            return await f.read()

    async def read_base64(self) -> str:
        data = await self.read_bytes()
        return _b64.b64encode(data).decode('ascii')
