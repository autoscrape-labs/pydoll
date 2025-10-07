import asyncio
import base64 as _b64
import logging
import shutil
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
)
from pydoll.connection import ConnectionHandler
from pydoll.constants import By
from pydoll.elements.mixins import FindElementsMixin
from pydoll.elements.web_element import WebElement
from pydoll.exceptions import (
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
)
from pydoll.protocol.base import EmptyResponse, Response
from pydoll.protocol.browser.events import (
    BrowserEvent,
    DownloadProgressEvent,
    DownloadWillBeginEvent,
)
from pydoll.protocol.browser.types import DownloadBehavior, DownloadProgressState
from pydoll.protocol.fetch.types import AuthChallengeResponseType, HeaderEntry, RequestStage
from pydoll.protocol.network.events import RequestWillBeSentEvent
from pydoll.protocol.network.types import (
    Cookie,
    CookieParam,
    ErrorReason,
    RequestMethod,
    ResourceType,
)
from pydoll.protocol.page.events import FileChooserOpenedEvent, PageEvent
from pydoll.protocol.page.methods import CaptureScreenshotResponse, PrintToPDFResponse
from pydoll.protocol.page.types import ScreenshotFormat
from pydoll.protocol.runtime.methods import CallFunctionOnResponse, EvaluateResponse
from pydoll.protocol.storage.methods import GetCookiesResponse
from pydoll.utils import (
    decode_base64_to_bytes,
    has_return_outside_function,
    is_script_already_function,
)

if TYPE_CHECKING:
    from pydoll.browser.chromium.base import Browser
    from pydoll.protocol.network.methods import GetResponseBodyResponse

logger = logging.getLogger(__name__)

IFrame: TypeAlias = 'Tab'


class Tab(FindElementsMixin):
    """
    Controls a browser tab via Chrome DevTools Protocol.

    Primary interface for web page automation including navigation, DOM manipulation,
    JavaScript execution, event handling, network monitoring, and specialized tasks
    like Cloudflare bypass.
    """

    def __init__(
        self,
        browser: 'Browser',
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

    async def enable_page_events(self):
        """Enable CDP Page domain events (load, navigation, dialogs, etc.)."""
        response = await self._execute_command(PageCommands.enable())
        self._page_events_enabled = True
        return response

    async def enable_network_events(self):
        """Enable CDP Network domain events (requests, responses, etc.)."""
        response = await self._execute_command(NetworkCommands.enable())
        self._network_events_enabled = True
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
        response: Response[EmptyResponse] = await self._execute_command(
            FetchCommands.enable(
                handle_auth_requests=handle_auth,
                resource_type=resource_type,
                request_stage=request_stage,
            )
        )
        self._fetch_events_enabled = True
        return response

    async def enable_dom_events(self):
        """Enable CDP DOM domain events (document structure changes)."""
        response = await self._execute_command(DomCommands.enable())
        self._dom_events_enabled = True
        return response

    async def enable_runtime_events(self):
        """Enable CDP Runtime domain events."""
        response = await self._execute_command(RuntimeCommands.enable())
        self._runtime_events_enabled = True
        return response

    async def enable_intercept_file_chooser_dialog(self):
        """
        Enable file chooser dialog interception for automated uploads.

        Note:
            Use expect_file_chooser context manager for convenience.
        """
        response = await self._execute_command(PageCommands.set_intercept_file_chooser_dialog(True))
        self._intercept_file_chooser_dialog_enabled = True
        return response

    async def enable_auto_solve_cloudflare_captcha(
        self,
        custom_selector: Optional[tuple[By, str]] = None,
        time_before_click: int = 5,
        time_to_wait_captcha: int = 5,
    ):
        """
        Enable automatic Cloudflare Turnstile captcha bypass.

        Args:
            custom_selector: Custom captcha selector (default: cf-turnstile class).
            time_before_click: Delay before clicking captcha (default 2s).
            time_to_wait_captcha: Timeout for captcha detection (default 5s).
        """
        if not self.page_events_enabled:
            await self.enable_page_events()

        callback = partial(
            self._bypass_cloudflare,
            custom_selector=custom_selector,
            time_before_click=time_before_click,
            time_to_wait_captcha=time_to_wait_captcha,
        )

        self._cloudflare_captcha_callback_id = await self.on(PageEvent.LOAD_EVENT_FIRED, callback)

    async def disable_fetch_events(self):
        """Disable CDP Fetch domain and release paused requests."""
        response = await self._execute_command(FetchCommands.disable())
        self._fetch_events_enabled = False
        return response

    async def disable_page_events(self):
        """Disable CDP Page domain events."""
        response = await self._execute_command(PageCommands.disable())
        self._page_events_enabled = False
        return response

    async def disable_network_events(self):
        """Disable CDP Network domain events."""
        response = await self._execute_command(NetworkCommands.disable())
        self._network_events_enabled = False
        return response

    async def disable_dom_events(self):
        """Disable CDP DOM domain events."""
        response = await self._execute_command(DomCommands.disable())
        self._dom_events_enabled = False
        return response

    async def disable_runtime_events(self):
        """Disable CDP Runtime domain events."""
        response = await self._execute_command(RuntimeCommands.disable())
        self._runtime_events_enabled = False
        return response

    async def disable_intercept_file_chooser_dialog(self):
        """Disable file chooser dialog interception."""
        response = await self._execute_command(
            PageCommands.set_intercept_file_chooser_dialog(False)
        )
        self._intercept_file_chooser_dialog_enabled = False
        return response

    async def disable_auto_solve_cloudflare_captcha(self):
        """Disable automatic Cloudflare Turnstile captcha bypass."""
        await self._connection_handler.remove_callback(self._cloudflare_captcha_callback_id)
        self._cloudflare_captcha_callback_id = None

    async def close(self):
        """
        Close this browser tab.

        Note:
            Tab instance becomes invalid after calling this method.
        """
        result = await self._execute_command(PageCommands.close())
        self._browser._tabs_opened.pop(self._target_id)
        return result

    async def get_frame(self, frame: WebElement) -> IFrame:
        """
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
        if not frame.tag_name == 'iframe':
            raise NotAnIFrame

        frame_url = frame.get_attribute('src')
        if not frame_url:
            raise InvalidIFrame('The iframe does not have a valid src attribute')

        targets = await self._browser.get_targets()
        iframe_target = next((target for target in targets if target['url'] == frame_url), None)
        if not iframe_target:
            raise IFrameNotFound('The target for the iframe was not found')

        target_id = iframe_target['targetId']
        if target_id in self._browser._tabs_opened:
            return self._browser._tabs_opened[target_id]

        tab = Tab(
            self._browser,
            target_id=target_id,
            connection_port=self._connection_port,
        )
        self._browser._tabs_opened[target_id] = tab
        return tab

    async def bring_to_front(self):
        """Brings the page to front."""
        return await self._execute_command(PageCommands.bring_to_front())

    async def get_cookies(self) -> list[Cookie]:
        """Get all cookies accessible from current page."""
        response: GetCookiesResponse = await self._execute_command(
            StorageCommands.get_cookies(self._browser_context_id)
        )
        return response['result']['cookies']

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

        response: 'GetResponseBodyResponse' = await self._execute_command(
            NetworkCommands.get_response_body(request_id)
        )
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
        return logs

    async def set_cookies(self, cookies: list[CookieParam]):
        """
        Set multiple cookies for current page.

        Args:
            cookies: Cookie parameters (name/value required, others optional).

        Note:
            Defaults to current page's domain if not specified.
        """
        return await self._execute_command(
            StorageCommands.set_cookies(cookies, self._browser_context_id)
        )

    async def delete_all_cookies(self):
        """Delete all cookies from current browser context."""
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
        if await self._refresh_if_url_not_changed(url):
            return

        await self._execute_command(PageCommands.navigate(url))

        try:
            await self._wait_page_load(timeout=timeout)
        except WaitElementTimeout:
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
        await self._execute_command(
            PageCommands.reload(
                ignore_cache=ignore_cache, script_to_evaluate_on_load=script_to_evaluate_on_load
            )
        )
        try:
            await self._wait_page_load()
        except WaitElementTimeout:
            raise PageLoadTimeout()

    async def take_screenshot(
        self,
        path: Optional[str] = None,
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

        output_extension = path.split('.')[-1] if path else ScreenshotFormat.PNG
        if not ScreenshotFormat.has_value(output_extension):
            raise InvalidFileExtension(f'{output_extension} extension is not supported.')

        response: CaptureScreenshotResponse = await self._execute_command(
            PageCommands.capture_screenshot(
                format=ScreenshotFormat.get_value(output_extension),
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
            return screenshot_data

        if path:
            screenshot_bytes = decode_base64_to_bytes(screenshot_data)
            async with aiofiles.open(path, 'wb') as file:
                await file.write(screenshot_bytes)

        return None

    async def print_to_pdf(
        self,
        path: str,
        landscape: bool = False,
        display_header_footer: bool = False,
        print_background: bool = True,
        scale: float = 1.0,
        as_base64: bool = False,
    ) -> Optional[str]:
        """
        Generate PDF of current page.

        Args:
            path: File path for PDF output.
            landscape: Use landscape orientation.
            display_header_footer: Include header/footer.
            print_background: Include background graphics.
            scale: Scale factor (0.1-2.0).
            as_base64: Return as base64 string instead of saving.

        Returns:
            Base64 PDF data if as_base64=True, None otherwise.
        """
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
            return pdf_data

        pdf_bytes = decode_base64_to_bytes(pdf_data)
        async with aiofiles.open(path, 'wb') as file:
            await file.write(pdf_bytes)

        return None

    async def has_dialog(self) -> bool:
        """
        Check if JavaScript dialog is currently displayed.

        Note:
            Page events must be enabled to detect dialogs.
        """
        if self._connection_handler.dialog:
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
        return self._connection_handler.dialog['params']['message']

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
        return await self._execute_command(
            PageCommands.handle_javascript_dialog(accept=accept, prompt_text=prompt_text)
        )

    @overload
    async def execute_script(self, script: str) -> EvaluateResponse: ...

    @overload
    async def execute_script(self, script: str, element: WebElement) -> CallFunctionOnResponse: ...

    async def execute_script(
        self, script: str, element: Optional[WebElement] = None
    ) -> Union[EvaluateResponse, CallFunctionOnResponse]:
        """
        Execute JavaScript in page context.

        Args:
            script: JavaScript code to execute.
            element: Element context (use 'argument' in script to reference).

        Examples:
            await page.execute_script('argument.click()', element)
            await page.execute_script('argument.value = "Hello"', element)

        Raises:
            InvalidScriptWithElement: If script contains 'argument' but no element is provided.
        """
        if 'argument' in script and element is None:
            raise InvalidScriptWithElement('Script contains "argument" but no element was provided')

        if element:
            return await self._execute_script_with_element(script, element)

        return await self._execute_script_without_element(script)

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
        self, files: Union[str, Path, list[Union[str, Path]]]
    ) -> AsyncGenerator[None, None]:
        """
        Context manager for automatic file upload handling.

        Args:
            files: File path(s) for upload.
        """

        async def event_handler(event: FileChooserOpenedEvent):
            file_list = [str(file) for file in files] if isinstance(files, list) else [str(files)]
            await self._execute_command(
                DomCommands.set_file_input_files(
                    files=file_list,
                    backend_node_id=event['params']['backendNodeId'],
                )
            )

        if self.page_events_enabled is False:
            _before_page_events_enabled = False
            await self.enable_page_events()
        else:
            _before_page_events_enabled = True

        if self.intercept_file_chooser_dialog_enabled is False:
            await self.enable_intercept_file_chooser_dialog()

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
        time_before_click: int = 2,
        time_to_wait_captcha: int = 5,
    ) -> AsyncGenerator[None, None]:
        """
        Context manager for automatic Cloudflare captcha bypass.

        Args:
            custom_selector: Custom captcha selector (default: cf-turnstile class).
            time_before_click: Delay before clicking (default 2s).
            time_to_wait_captcha: Timeout for captcha detection (default 5s).
        """
        captcha_processed = asyncio.Event()

        async def bypass_cloudflare(_: dict):
            try:
                await self._bypass_cloudflare(
                    _,
                    custom_selector,
                    time_before_click,
                    time_to_wait_captcha,
                )
            finally:
                captcha_processed.set()

        _before_page_events_enabled = self.page_events_enabled

        if not _before_page_events_enabled:
            await self.enable_page_events()

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
    ) -> AsyncGenerator['_DownloadHandle', None]:
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

        await self._browser.set_download_behavior(
            behavior=DownloadBehavior.ALLOW,
            download_path=download_dir,
            browser_context_id=self._browser_context_id,
            events_enabled=True,
        )

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

        cb_id_will_begin = await self.on(
            BrowserEvent.DOWNLOAD_WILL_BEGIN,
            cast(Callable[[dict], Awaitable[Any]], on_will_begin),
            True,
        )
        cb_id_progress = await self.on(
            BrowserEvent.DOWNLOAD_PROGRESS,
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
            await self.remove_callback(cb_id_progress)
            await self.remove_callback(cb_id_will_begin)
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

        return await self._connection_handler.register_callback(
            event_name, function_to_register, temporary
        )

    async def remove_callback(self, callback_id: int):
        """Remove callback from tab."""
        return await self._connection_handler.remove_callback(callback_id)

    async def clear_callbacks(self):
        """Clear all registered event callbacks."""
        await self._connection_handler.clear_callbacks()

    def _get_connection_handler(self) -> ConnectionHandler:
        if self._ws_address:
            return ConnectionHandler(ws_address=self._ws_address)
        return ConnectionHandler(self._connection_port, self._target_id)

    async def _execute_script_with_element(self, script: str, element: WebElement):
        """
        Execute script with element context.

        Args:
            script: JavaScript code to execute.
            element: Element context (use 'argument' in script to reference).

        Returns:
            The result of the script execution.
        """
        if 'argument' not in script:
            raise InvalidScriptWithElement('Script does not contain "argument"')

        script = script.replace('argument', 'this')

        if not is_script_already_function(script):
            script = f'function(){{ {script} }}'

        command = RuntimeCommands.call_function_on(
            object_id=element._object_id, function_declaration=script, return_by_value=True
        )
        return await self._execute_command(command)

    async def _execute_script_without_element(self, script: str):
        """
        Execute script without element context.

        Args:
            script: JavaScript code to execute.

        Returns:
            The result of the script execution.
        """
        if has_return_outside_function(script):
            script = f'(function(){{ {script} }})()'

        command = RuntimeCommands.evaluate(expression=script)
        return await self._execute_command(command)

    async def _refresh_if_url_not_changed(self, url: str) -> bool:
        """Refresh page if URL hasn't changed."""
        current_url = await self.current_url
        if current_url == url:
            await self.refresh()
            return True
        return False

    async def _wait_page_load(self, timeout: int = 300):
        """
        Wait for page to finish loading.

        Raises:
            asyncio.TimeoutError: If page doesn't load within timeout.
        """
        start_time = asyncio.get_event_loop().time()
        while True:
            response: EvaluateResponse = await self._execute_command(
                RuntimeCommands.evaluate(expression='document.readyState')
            )
            if (
                response['result']['result']['value']
                == self._browser.options.page_load_state.value
            ):
                break
            if asyncio.get_event_loop().time() - start_time > timeout:
                raise WaitElementTimeout('Page load timed out')
            await asyncio.sleep(0.5)

    async def _bypass_cloudflare(
        self,
        event: dict,
        custom_selector: Optional[tuple[By, str]] = None,
        time_before_click: int = 2,
        time_to_wait_captcha: int = 5,
    ):
        """Attempt to bypass Cloudflare Turnstile captcha when detected."""
        try:
            selector = custom_selector or (By.CLASS_NAME, 'cf-turnstile')
            element = await self.find_or_wait_element(
                *selector, timeout=time_to_wait_captcha, raise_exc=False
            )
            element = cast(WebElement, element)
            if element:
                # adjust the external div size to shadow root width (usually 300px)
                await self.execute_script('argument.style="width: 300px"', element)
                await asyncio.sleep(time_before_click)
                await element.click()
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
