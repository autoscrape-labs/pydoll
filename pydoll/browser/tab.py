import asyncio
import logging
from contextlib import asynccontextmanager
from functools import partial
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncGenerator,
    Callable,
    Optional,
    TypeAlias,
    Union,
    cast,
    overload,
)

import aiofiles

from pydoll.commands import (
    DomCommands,
    FetchCommands,
    NetworkCommands,
    PageCommands,
    RuntimeCommands,
    StorageCommands,
)
from pydoll.connection import ConnectionHandler
from pydoll.constants import By, RequestStage, ResourceType, ScreenshotFormat
from pydoll.elements.mixins import FindElementsMixin
from pydoll.elements.web_element import WebElement
from pydoll.exceptions import (
    IFrameNotFound,
    InvalidFileExtension,
    InvalidIFrame,
    InvalidScriptWithElement,
    NetworkEventsNotEnabled,
    NoDialogPresent,
    NotAnIFrame,
    PageLoadTimeout,
    WaitElementTimeout,
)
from pydoll.protocol.base import Response
from pydoll.protocol.network.responses import GetResponseBodyResponse
from pydoll.protocol.network.types import Cookie, CookieParam, NetworkLog
from pydoll.protocol.page.events import PageEvent
from pydoll.protocol.page.responses import CaptureScreenshotResponse, PrintToPDFResponse
from pydoll.protocol.runtime.responses import CallFunctionOnResponse, EvaluateResponse
from pydoll.protocol.storage.responses import GetCookiesResponse
from pydoll.utils import (
    decode_base64_to_bytes,
    has_return_outside_function,
    is_script_already_function,
)

if TYPE_CHECKING:
    from pydoll.browser.chromium.base import Browser

logger = logging.getLogger(__name__)

IFrame: TypeAlias = 'Tab'


class Tab(FindElementsMixin):  # noqa: PLR0904
    """
    Controls a browser tab via Chrome DevTools Protocol.

    Primary interface for web page automation including navigation, DOM manipulation,
    JavaScript execution, event handling, network monitoring, and specialized tasks
    like Cloudflare bypass.

    This class implements a singleton pattern based on target_id to ensure
    only one Tab instance exists per browser tab.
    """

    _instances: dict[str, 'Tab'] = {}

    def __new__(
        cls,
        browser: 'Browser',
        connection_port: int,
        target_id: str,
        browser_context_id: Optional[str] = None,
    ) -> 'Tab':
        """
        Create or return existing Tab instance for the given target_id.

        Args:
            browser: Browser instance that created this tab.
            connection_port: CDP WebSocket port.
            target_id: CDP target identifier for this tab.
            browser_context_id: Optional browser context ID.

        Returns:
            Tab instance (new or existing) for the target_id.
        """
        if target_id in cls._instances:
            existing_instance = cls._instances[target_id]
            existing_instance._browser = browser
            existing_instance._connection_port = connection_port
            existing_instance._browser_context_id = browser_context_id
            return existing_instance

        instance = super().__new__(cls)
        cls._instances[target_id] = instance
        return instance

    def __init__(
        self,
        browser: 'Browser',
        connection_port: int,
        target_id: str,
        browser_context_id: Optional[str] = None,
    ):
        """
        Initialize tab controller for existing browser tab.

        Args:
            browser: Browser instance that created this tab.
            connection_port: CDP WebSocket port.
            target_id: CDP target identifier for this tab.
            browser_context_id: Optional browser context ID.
        """
        if hasattr(self, '_initialized') and self._initialized:
            return

        self._browser: 'Browser' = browser
        self._connection_port: int = connection_port
        self._target_id: str = target_id
        self._connection_handler: ConnectionHandler = ConnectionHandler(
            connection_port, self._target_id
        )
        self._page_events_enabled: bool = False
        self._network_events_enabled: bool = False
        self._fetch_events_enabled: bool = False
        self._dom_events_enabled: bool = False
        self._runtime_events_enabled: bool = False
        self._intercept_file_chooser_dialog_enabled: bool = False
        self._cloudflare_captcha_callback_id: Optional[int] = None
        self._browser_context_id: Optional[str] = browser_context_id
        self._initialized: bool = True

    @classmethod
    def _remove_instance(cls, target_id: str) -> None:
        """
        Remove instance from registry when tab is closed.

        Args:
            target_id: Target ID to remove from registry.
        """
        cls._instances.pop(target_id, None)

    @classmethod
    def get_instance(cls, target_id: str) -> Optional['Tab']:
        """
        Get existing Tab instance for target_id if it exists.

        Args:
            target_id: Target ID to look up.

        Returns:
            Existing Tab instance or None if not found.
        """
        return cls._instances.get(target_id)

    @classmethod
    def get_all_instances(cls) -> dict[str, 'Tab']:
        """
        Get all active Tab instances.

        Returns:
            Dictionary mapping target_id to Tab instances.
        """
        return cls._instances.copy()

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
        response: Response = await self._execute_command(
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
        time_before_click: int = 2,
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
        self._remove_instance(self._target_id)
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

        return Tab(self._browser, self._connection_port, iframe_target['targetId'])

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

        response: GetResponseBodyResponse = await self._execute_command(
            NetworkCommands.get_response_body(request_id)
        )
        return response['result']['body']

    async def get_network_logs(self, filter: Optional[str] = None) -> list[NetworkLog]:
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
        as_base64: bool = False,
    ) -> Optional[str]:
        """
        Capture screenshot of current page.

        Args:
            path: File path for screenshot (extension determines format).
            quality: Image quality 0-100 (default 100).
            as_base64: Return as base64 string instead of saving file.

        Returns:
            Base64 screenshot data if as_base64=True, None otherwise.

        Raises:
            InvalidFileExtension: If file extension not supported.
            ValueError: If path is None and as_base64 is False.
        """
        if not path and not as_base64:
            raise ValueError('path is required when as_base64 is False')

        output_extension = path.split('.')[-1] if path else ScreenshotFormat.PNG
        if not ScreenshotFormat.has_value(output_extension):
            raise InvalidFileExtension(f'{output_extension} extension is not supported.')

        response: CaptureScreenshotResponse = await self._execute_command(
            PageCommands.capture_screenshot(
                format=ScreenshotFormat.get_value(output_extension),
                quality=quality,
            )
        )
        screenshot_data = response['result']['data']
        if as_base64:
            return screenshot_data

        if path:
            screenshot_bytes = decode_base64_to_bytes(screenshot_data)
            async with aiofiles.open(path, 'wb') as file:
                await file.write(screenshot_bytes)

        return None

    async def print_to_pdf(  # noqa: PLR0913, PLR0917
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

    @asynccontextmanager
    async def expect_file_chooser(
        self, files: Union[str, Path, list[Union[str, Path]]]
    ) -> AsyncGenerator[None, None]:
        """
        Context manager for automatic file upload handling.

        Args:
            files: File path(s) for upload.
        """

        async def event_handler(event):
            await self._execute_command(
                DomCommands.upload_files(
                    files=files,
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

        await self.on(PageEvent.FILE_CHOOSER_OPENED, event_handler, temporary=True)

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

    async def on(
        self,
        event_name: str,
        callback: Callable[[dict], Any],
        temporary: bool = False,
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
            if response['result']['result']['value'] == 'complete':
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
