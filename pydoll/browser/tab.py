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
    Dict,
    List,
    Optional,
    Tuple,
    TypeAlias,
    Union,
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
    NoDialogPresent,
    NotAnIFrame,
    PageLoadTimeout,
)
from pydoll.protocol.base import Response
from pydoll.protocol.network.types import Cookie, CookieParam
from pydoll.protocol.page.events import PageEvent
from pydoll.protocol.page.responses import CaptureScreenshotResponse, PrintToPDFResponse
from pydoll.protocol.runtime.responses import EvaluateResponse
from pydoll.protocol.storage.responses import GetCookiesResponse
from pydoll.utils import decode_base64_to_bytes

if TYPE_CHECKING:
    from pydoll.browser.chromium.base import Browser

logger = logging.getLogger(__name__)

IFrame: TypeAlias = 'Tab'


class Tab(FindElementsMixin):  # noqa: PLR0904
    """
    Represents and controls a browser tab via Chrome DevTools Protocol.

    The Tab class is the primary interface for interacting with web pages,
    providing comprehensive control over navigation, DOM manipulation, network
    monitoring, JavaScript execution, and many other browser automation tasks.

    Key capabilities include:
    1. Page navigation and state management
    2. Element finding and interaction (via FindElementsMixin)
    3. JavaScript execution and evaluation
    4. Event subscription and handling
    5. Network request interception and monitoring
    6. Cookie management
    7. File download/upload control
    8. Screenshot and PDF generation
    9. Dialog handling
    10. Specialized automation tasks (e.g., Cloudflare bypass)

    This class uses CDP to provide these capabilities without requiring
    WebDriver, offering improved performance and more granular control
    over the browser environment.
    """

    def __init__(
        self,
        browser: 'Browser',
        connection_port: int,
        target_id: str,
        browser_context_id: Optional[str] = None,
    ):
        """
        Initializes a new browser tab instance.

        Creates a tab controller that connects to an existing browser tab
        via CDP. The tab is identified by its target ID within the browser,
        and all commands are sent through a dedicated connection handler.

        Args:
            browser: Browser instance that created this tab.
            connection_port: Port number for CDP WebSocket connection.
                This should match the browser's --remote-debugging-port.
            target_id: CDP target identifier for this specific tab.
                Obtained when creating a new tab or listing existing tabs.
            browser_context_id: Optional browser context (incognito profile) ID
                that this tab belongs to. Used for context-specific operations.

        """
        self._browser = browser
        self._connection_port = connection_port
        self._target_id = target_id
        self._connection_handler = ConnectionHandler(connection_port, self._target_id)
        self._page_events_enabled = False
        self._network_events_enabled = False
        self._fetch_events_enabled = False
        self._dom_events_enabled = False
        self._runtime_events_enabled = False
        self._intercept_file_chooser_dialog_enabled = False
        self._cloudflare_captcha_callback_id: Optional[int] = None
        self._browser_context_id = browser_context_id

    @property
    def page_events_enabled(self) -> bool:
        """
        Whether CDP Page domain events are currently enabled.

        Returns:
            bool: True if page events (navigation, load, etc.) are being monitored,
                 False otherwise.

        Note:
            Many operations require page events to be enabled first.
            Use enable_page_events() to activate them.
        """
        return self._page_events_enabled

    @property
    def network_events_enabled(self) -> bool:
        """
        Whether CDP Network domain events are currently enabled.

        Returns:
            bool: True if network events (requests, responses, etc.) are being
                 monitored, False otherwise.

        Note:
            Network monitoring must be explicitly enabled with enable_network_events()
            before network-related events can be captured.
        """
        return self._network_events_enabled

    @property
    def fetch_events_enabled(self) -> bool:
        """
        Whether CDP Fetch domain events are currently enabled.

        Returns:
            bool: True if fetch events (request interception) are active,
                 False otherwise.

        Note:
            Fetch interception allows modifying requests before they're sent
            and must be explicitly enabled with enable_fetch_events().
        """
        return self._fetch_events_enabled

    @property
    def dom_events_enabled(self) -> bool:
        """
        Whether CDP DOM domain events are currently enabled.

        Returns:
            bool: True if DOM events (node changes, etc.) are being monitored,
                 False otherwise.

        Note:
            DOM events provide notification of changes to the page structure
            and must be enabled with enable_dom_events().
        """
        return self._dom_events_enabled

    @property
    def runtime_events_enabled(self) -> bool:
        """
        Whether CDP Runtime domain events are currently enabled.

        Returns:
            bool: True if runtime events are being monitored, False otherwise.

        Note:
            Runtime events must be enabled with enable_runtime_events().
        """
        return self._runtime_events_enabled

    @property
    def intercept_file_chooser_dialog_enabled(self) -> bool:
        """
        Whether file chooser dialog interception is active.

        Returns:
            bool: True if file chooser dialogs are being intercepted instead of
                 shown to the user, False if native dialogs appear.

        Note:
            When enabled, file upload dialogs emit events instead of showing UI,
            allowing automated file selection. Enable with
            enable_intercept_file_chooser_dialog().
        """
        return self._intercept_file_chooser_dialog_enabled

    @property
    async def current_url(self) -> str:
        """
        Gets the current URL of the page.

        Retrieves the current document URL by evaluating window.location.href
        in the page context. This is more reliable than tracking navigation
        events as it reflects redirects and client-side navigation.

        Returns:
            str: The complete current URL of the loaded document.

        Note:
            This is an async property that requires awaiting.

        """
        response: EvaluateResponse = await self._execute_command(
            RuntimeCommands.evaluate('window.location.href')
        )
        return response['result']['result']['value']

    @property
    async def page_source(self) -> str:
        """
        Gets the complete HTML source of the current page.

        Retrieves the HTML content by evaluating document.documentElement.outerHTML
        in the page context. This returns the live DOM representation including
        any modifications made by JavaScript.

        Returns:
            str: The complete HTML source of the current document.

        Note:
            This is an async property that requires awaiting.
            The returned HTML reflects the current state of the DOM,
            not the original HTML received from the server.

        """
        response: EvaluateResponse = await self._execute_command(
            RuntimeCommands.evaluate('document.documentElement.outerHTML')
        )
        return response['result']['result']['value']

    async def enable_page_events(self):
        """
        Activates the CDP Page domain for event monitoring.

        Enables subscription to Page domain events such as:
        - loadEventFired
        - domContentEventFired
        - frameNavigated
        - javascriptDialogOpening
        - fileChooserOpened

        These events allow tracking page lifecycle and user interactions.
        Many other methods depend on this being enabled first.

        Returns:
            Response: The CDP command response.

        """
        response = await self._execute_command(PageCommands.enable())
        self._page_events_enabled = True
        return response

    async def enable_network_events(self):
        """
        Activates the CDP Network domain for traffic monitoring.

        Enables subscription to Network domain events such as:
        - requestWillBeSent
        - responseReceived
        - loadingFailed
        - loadingFinished

        These events provide visibility into all network traffic including
        XHR, fetch, images, stylesheets, scripts, and other resources.

        Returns:
            Response: The CDP command response.

        Note:
            Network monitoring has some performance impact.
            Disable it with disable_network_events() when no longer needed.
        """
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
        Activates the CDP Fetch domain for request interception.

        Enables interception of network requests before they're sent,
        allowing inspection, modification, or blocking of requests.
        When enabled, matching requests will be paused until explicitly
        continued using FetchCommands.

        Args:
            handle_auth: Whether to intercept authentication challenges.
                If True, emits authRequired events for HTTP auth requests.
            resource_type: Optional filter to limit interception to specific
                resource types (Document, Stylesheet, Image, etc.).
                If None, intercepts all resource types.
            request_stage: When to intercept the request (Request, Response).
                If None, uses the default (Request).

        Returns:
            Response: The CDP command response.

        Note:
            Intercepted requests must be explicitly continued or they will
            time out. This is a powerful feature for request modification,
            mocking responses, and implementing custom networking behavior.
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
        """
        Activates the CDP DOM domain for document structure monitoring.

        Enables subscription to DOM domain events such as:
        - documentUpdated
        - setChildNodes
        - attributeModified
        - attributeRemoved
        - childNodeInserted
        - childNodeRemoved

        These events provide real-time notifications about changes to
        the document structure, allowing tracking of dynamic content.

        Returns:
            Response: The CDP command response.

        Note:
            DOM monitoring has some performance impact and increases memory usage.
            Disable it with disable_dom_events() when no longer needed.
        """
        response = await self._execute_command(DomCommands.enable())
        self._dom_events_enabled = True
        return response

    async def enable_runtime_events(self):
        """
        Enables runtime events.
        """
        response = await self._execute_command(RuntimeCommands.enable())
        self._runtime_events_enabled = True
        return response

    async def enable_intercept_file_chooser_dialog(self):
        """
        Enables interception of file selection dialogs.

        When enabled, native file chooser dialogs are not displayed.
        Instead, Page.fileChooserOpened events are emitted, allowing
        programmatic file selection without user interaction.

        This is essential for automated file upload testing.

        Returns:
            Response: The CDP command response.

        Note:
            Requires Page domain to be enabled first.
            For convenience, use the expect_file_chooser context manager
            which handles enabling/disabling automatically.
        """
        response = await self._execute_command(PageCommands.set_intercept_file_chooser_dialog(True))
        self._intercept_file_chooser_dialog_enabled = True
        return response

    async def enable_auto_solve_cloudflare_captcha(
        self,
        custom_selector: Optional[Tuple[By, str]] = None,
        time_before_click: int = 2,
        time_to_wait_captcha: int = 5,
    ):
        """
        Sets up automatic handling of Cloudflare Turnstile captchas.

        Establishes a permanent event listener that attempts to bypass
        Cloudflare's Turnstile captcha challenges whenever they appear.
        This works by automatically clicking the captcha widget to trigger
        the invisible challenge process.

        Args:
            custom_selector: Optional custom locator for the captcha element.
                Defaults to (By.CLASS_NAME, 'cf-turnstile') which targets
                the standard Cloudflare Turnstile widget.
            time_before_click: Seconds to wait before clicking the captcha.
                A short delay often improves success rate. Default is 2 seconds.
            time_to_wait_captcha: Maximum seconds to wait for captcha to appear.
                Default is 5 seconds.

        Returns:
            int: Callback ID that can be used to disable the auto-solver.

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
        """
        Deactivates the CDP Fetch domain and request interception.

        Stops interception of network requests and releases any currently
        paused requests. After calling this method, network requests will
        proceed normally without intervention.

        Returns:
            Response: The CDP command response.

        """
        response = await self._execute_command(FetchCommands.disable())
        self._fetch_events_enabled = False
        return response

    async def disable_page_events(self):
        """
        Deactivates the CDP Page domain and stops event monitoring.

        Stops subscription to Page domain events, reducing overhead
        when page lifecycle tracking is no longer needed.

        Returns:
            Response: The CDP command response.

        """
        response = await self._execute_command(PageCommands.disable())
        self._page_events_enabled = False
        return response

    async def disable_network_events(self):
        """
        Deactivates the CDP Network domain and stops traffic monitoring.

        Stops subscription to Network domain events, reducing overhead
        when network traffic monitoring is no longer needed.

        Returns:
            Response: The CDP command response.

        """
        response = await self._execute_command(NetworkCommands.disable())
        self._network_events_enabled = False
        return response

    async def disable_dom_events(self):
        """
        Deactivates the CDP DOM domain and stops structure monitoring.

        Stops subscription to DOM domain events, reducing overhead
        when document structure tracking is no longer needed.

        Returns:
            Response: The CDP command response.
        """
        response = await self._execute_command(DomCommands.disable())
        self._dom_events_enabled = False
        return response

    async def disable_runtime_events(self):
        """
        Disables runtime events.
        """
        response = await self._execute_command(RuntimeCommands.disable())
        self._runtime_events_enabled = False
        return response

    async def disable_intercept_file_chooser_dialog(self):
        """
        Disables interception of file selection dialogs.

        Reverts to default browser behavior where native file chooser
        dialogs are displayed to the user instead of emitting events.

        Returns:
            Response: The CDP command response.
        """
        response = await self._execute_command(
            PageCommands.set_intercept_file_chooser_dialog(False)
        )
        self._intercept_file_chooser_dialog_enabled = False
        return response

    async def disable_auto_solve_cloudflare_captcha(self):
        """
        Disables automatic handling of Cloudflare Turnstile captchas.

        Removes the event listener that was set up to automatically
        bypass Cloudflare captcha challenges.
        """
        await self._connection_handler.remove_callback(self._cloudflare_captcha_callback_id)
        self._cloudflare_captcha_callback_id = None

    async def close(self):
        """
        Closes this browser tab.

        Sends a command to close the current tab in the browser.
        After calling this method, the tab will be closed and this
        Tab instance should not be used for further operations.

        Returns:
            Response: The CDP command response.

        Note:
            This closes only the current tab, not the entire browser.
            The Tab instance becomes invalid after calling this method.
        """
        return await self._execute_command(PageCommands.close())

    async def get_frame(self, frame: WebElement) -> IFrame:
        """
        Gets a Tab object for interacting with an iframe element.

        Creates a new Tab instance that targets the content document of the
        specified iframe element. This allows automation to interact with
        content inside iframes as if they were separate pages.

        Args:
            frame: The WebElement representing the iframe to interact with.
                Must be an actual iframe element (<iframe> tag).

        Returns:
            IFrame: A new Tab instance configured to interact with the iframe
                content. This Tab shares the same browser instance but has
                a different target ID.

        Raises:
            NotAnIFrame: If the provided element is not an iframe.
            InvalidIFrame: If the iframe does not have a valid src attribute.
            IFrameNotFound: If the iframe's target cannot be found in the browser.
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

    async def get_cookies(self) -> List[Cookie]:
        """
        Retrieves all cookies accessible from this page.

        Gets all cookies associated with the current page, including
        both session and persistent cookies, from all domains that
        match the current page's security constraints.

        Returns:
            List[Cookie]: List of cookie objects containing detailed
                cookie information including name, value, domain, path,
                expiration, and security settings.
        """
        response: GetCookiesResponse = await self._execute_command(
            StorageCommands.get_cookies(self._browser_context_id)
        )
        return response['result']['cookies']

    async def set_cookies(self, cookies: List[CookieParam]):
        """
        Sets multiple cookies for the current page.

        Adds or updates cookies with the specified parameters.
        Each cookie must include name and value, and can optionally
        include domain, path, security settings, and expiration.

        Args:
            cookies: List of cookie parameters to set. Each cookie must
                include at minimum a name and value. Other attributes like
                domain, path, secure, httpOnly, etc. are optional.

        Returns:
            Response: The CDP command response.

        Note:
            Cookies are set in the browser context this tab belongs to.
            If no domain is specified, cookies default to the current page's domain.
        """
        return await self._execute_command(
            StorageCommands.set_cookies(cookies, self._browser_context_id)
        )

    async def delete_all_cookies(self):
        """
        Deletes all cookies accessible from this page.

        Removes all cookies from the current browser context,
        including session cookies and persistent cookies from
        all domains.

        Returns:
            Response: The CDP command response.
        """
        return await self._execute_command(StorageCommands.clear_cookies(self._browser_context_id))

    async def go_to(self, url: str, timeout: int = 300):
        """
        Navigates the tab to a specified URL and waits for loading to complete.

        Performs navigation to the target URL and waits for the page to finish
        loading. If the target URL matches the current URL, performs a page
        refresh instead of a new navigation.

        Args:
            url: The URL to navigate to. Should be a fully qualified URL
                (e.g., 'https://example.com').
            timeout: Maximum seconds to wait for the page to load completely.
                Default is 300 seconds (5 minutes).

        Raises:
            PageLoadTimeout: If the page doesn't finish loading within the
                specified timeout period.
        """
        if await self._refresh_if_url_not_changed(url):
            return

        await self._execute_command(PageCommands.navigate(url))

        try:
            await self._wait_page_load(timeout=timeout)
        except asyncio.TimeoutError:
            raise PageLoadTimeout()

    async def refresh(
        self,
        ignore_cache: bool = False,
        script_to_evaluate_on_load: Optional[str] = None,
    ):
        """
        Reloads the current page.

        Performs a page refresh, optionally bypassing the cache and/or
        executing JavaScript upon page load. Waits for the page to finish
        loading before returning.

        Args:
            ignore_cache: If True, bypasses the browser cache and forces
                all resources to be reloaded from the server. Default is False.
            script_to_evaluate_on_load: Optional JavaScript to execute when
                the page has finished loading. Useful for page initialization.

        Raises:
            PageLoadTimeout: If the page doesn't finish reloading within
                the default timeout period (300 seconds).
        """
        await self._execute_command(
            PageCommands.reload(
                ignore_cache=ignore_cache, script_to_evaluate_on_load=script_to_evaluate_on_load
            )
        )
        try:
            await self._wait_page_load()
        except asyncio.TimeoutError:
            raise PageLoadTimeout()

    async def take_screenshot(
        self,
        path: str,
        quality: int = 100,
        as_base64: bool = False,
    ) -> Optional[str]:
        """
        Captures a screenshot of the current page.

        Takes a full-page screenshot of the current viewport and either
        saves it to a file or returns it as a base64-encoded string.

        Args:
            path: File path where the screenshot should be saved.
                The file extension determines the format (png, jpg, etc.).
            quality: Image quality from 0-100 (applicable for lossy formats
                like JPEG). Default is 100 (maximum quality).
            as_base64: If True, returns the screenshot as a base64 string
                instead of saving to a file. Default is False.

        Returns:
            Optional[str]: If as_base64 is True, returns the base64-encoded
                screenshot data. Otherwise returns None.

        Raises:
            InvalidFileExtension: If the file extension in the path is not
                supported for screenshots.

        Note:
            This captures the full visible viewport. For element-specific
            screenshots, find the element and use its screenshot method.
        """
        output_extension = path.split('.')[-1]
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
        Generates a PDF of the current page.

        Creates a PDF representation of the current page with customizable
        print settings and either saves it to a file or returns it as a
        base64-encoded string.

        Args:
            path: File path where the PDF should be saved.
            landscape: If True, uses landscape orientation instead of portrait.
                Default is False (portrait).
            display_header_footer: If True, includes default header and footer.
                Default is False.
            print_background: If True, includes background graphics and colors.
                Default is True.
            scale: Scale factor for the PDF rendering (0.1 to 2.0).
                Default is 1.0 (100%).
            as_base64: If True, returns the PDF as a base64 string
                instead of saving to a file. Default is False.

        Returns:
            Optional[str]: If as_base64 is True, returns the base64-encoded
                PDF data. Otherwise returns None.

        Note:
            PDF generation uses Chrome's built-in printing functionality.
            For more advanced PDF options, see the full PrintToPDF command
            in the CDP documentation.
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
        Checks if a JavaScript dialog is currently displayed.

        Determines whether a JavaScript dialog (alert, confirm, prompt)
        is currently open in the page.

        Returns:
            bool: True if a dialog is present, False otherwise.

        Note:
            This method checks the connection handler's internal state
            which is updated via CDP events. Page events must be enabled
            to detect dialogs.
        """
        if self._connection_handler.dialog:
            return True

        return False

    async def get_dialog_message(self) -> str:
        """
        Gets the message text from the current JavaScript dialog.

        Retrieves the message displayed in the currently active
        JavaScript dialog (alert, confirm, or prompt).

        Returns:
            str: The text message from the dialog.

        Raises:
            NoDialogPresent: If no dialog is currently displayed.
        """
        if not await self.has_dialog():
            raise NoDialogPresent()
        return self._connection_handler.dialog['params']['message']

    async def handle_dialog(self, accept: bool, prompt_text: Optional[str] = None):
        """
        Responds to a JavaScript dialog.

        Handles the currently displayed JavaScript dialog by either
        accepting or dismissing it, and optionally providing text
        input for prompt dialogs.

        Args:
            accept: If True, accepts/confirms the dialog.
                If False, dismisses/cancels it.
            prompt_text: Optional text to enter for prompt dialogs.
                Ignored for alert and confirm dialogs.

        Raises:
            NoDialogPresent: If no dialog is currently displayed.

        Note:
            This method must be called after a dialog appears to allow
            page execution to continue. Page events must be enabled to
            handle dialogs.
        """
        if not await self.has_dialog():
            raise NoDialogPresent()
        return await self._execute_command(
            PageCommands.handle_javascript_dialog(accept=accept, prompt_text=prompt_text)
        )

    async def execute_script(self, script: str, element: Optional[WebElement] = None):
        """
        Executes a JavaScript script in the page.
        If an element is provided, the script will be executed in the context
        of that element. To provide the element context, use the 'argument'
        keyword in the script.

        Examples:
        ```python
        await page.execute_script('argument.click()', element)
        await page.execute_script('argument.value = "Hello, World!"', element)
        ```

        Args:
            script (str): The JavaScript script to execute.
            element (WebElement, optional): The element to execute the script
                on. Use 'argument' in your script to refer to this element.
                Defaults to None.

        Returns:
            dict: The result of the script execution from the browser.
        """
        if element:
            script = script.replace('argument', 'this')
            script = f'function(){{ {script} }}'
            object_id = element._object_id
            command = RuntimeCommands.call_function_on(
                object_id=object_id, function_declaration=script, return_by_value=True
            )
        else:
            command = RuntimeCommands.evaluate(expression=script)
        return await self._execute_command(command)

    @asynccontextmanager
    async def expect_file_chooser(
        self, files: Union[str, Path, List[Union[str, Path]]]
    ) -> AsyncGenerator[None, None]:
        """
        Context manager for handling file upload dialogs.

        Sets up automatic file selection when a file input is clicked
        within the context. This avoids the need for native file dialog
        interaction by programmatically setting the selected files.

        Args:
            files: Path(s) to the file(s) to be uploaded. Can be a single
                file path or a list of file paths for multi-file selection.

        Yields:
            None
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
        custom_selector: Optional[Tuple[By, str]] = None,
        time_before_click: int = 2,
        time_to_wait_captcha: int = 5,
    ) -> AsyncGenerator[None, None]:
        """
        Context manager to handle Cloudflare Turnstile captcha.

        This method sets up a callback that will automatically attempt to
        bypass the Cloudflare captcha when the page loads. The main code
        will wait until the captcha handling is complete before continuing.

        It creates an event to coordinate between the callback and the main
        code.

        Args:
            custom_selector (Optional[Tuple[By, str]]): Custom selector
                to locate the captcha element. Defaults to
                (By.CLASS_NAME, 'cf-turnstile').
            time_before_click (int): Time to wait before clicking the captcha
                element in seconds. Defaults to 2 seconds.
            time_to_wait_captcha (Optional[int]): Timeout for the captcha
                element to be found in seconds. Defaults to 5 seconds.

        Returns:
            None
        """
        captcha_processed = asyncio.Event()

        async def bypass_cloudflare(_: Dict):
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

    async def on(self, event_name: str, callback: Callable[[Dict], Any], temporary: bool = False):
        """
        Registers an event listener for CDP events.

        Subscribes to a specific Chrome DevTools Protocol event and
        executes the provided callback function whenever the event occurs.
        This allows reacting to browser events like page loads, network
        activity, DOM changes, and more.

        The callback is automatically wrapped to run in a separate task,
        preventing it from blocking the main event loop. This means your
        callback can perform longer operations without affecting the tab's
        responsiveness.

        Args:
            event_name: CDP event name to listen for (e.g., 'Page.loadEventFired',
                'Network.responseReceived', 'DOM.documentUpdated').
            callback: Function to call when the event occurs. Can be synchronous
                or asynchronous. Should accept a single parameter containing the
                event data. Runs in the background and won't block other operations.
            temporary: If True, removes the listener after first invocation.
                Default is False (persistent listener).

        Returns:
            int: Callback ID that can be used to remove the listener later.

        Note:
            The corresponding domain must be enabled before events will fire.
            For example, Page.loadEventFired requires enable_page_events()
            to be called first.
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

    async def _refresh_if_url_not_changed(self, url: str) -> bool:
        """
        Refreshes the page if the URL has not changed.

        Args:
            url (str): The URL to compare against.
        """
        current_url = await self.current_url
        if current_url == url:
            await self.refresh()
            return True
        return False

    async def _wait_page_load(self, timeout: int = 300):
        """
        Waits for the page to finish loading.

        Args:
            timeout (int): Maximum time in seconds to wait for the page
                to load. Defaults to 300 seconds.

        Raises:
            asyncio.TimeoutError: If the page does not finish loading within
                the specified timeout.
        """
        start_time = asyncio.get_event_loop().time()
        while True:
            response: EvaluateResponse = await self._execute_command(
                RuntimeCommands.evaluate(expression='document.readyState')
            )
            if response['result']['result']['value'] == 'complete':
                break
            if asyncio.get_event_loop().time() - start_time > timeout:
                raise asyncio.TimeoutError('Page load timed out')
            await asyncio.sleep(0.5)

    async def _bypass_cloudflare(
        self,
        event: dict,
        custom_selector: Optional[Tuple[By, str]] = None,
        time_before_click: int = 2,
        time_to_wait_captcha: int = 5,
    ):
        """
        Attempt to bypass Cloudflare Turnstile captcha when detected.

        Args:
            event (dict): The event payload (unused)
            custom_selector (Optional[Tuple[By, str]]): Custom selector
                to locate the captcha element. Defaults to
                (By.CLASS_NAME, 'cf-turnstile').
            time_before_click (int): Time to wait before clicking the captcha
                element in seconds. Defaults to 2 seconds.
            time_to_wait_captcha (int): Timeout for the captcha element to be
                found in seconds. Defaults to 5 seconds.
        """
        try:
            selector = custom_selector or (By.CLASS_NAME, 'cf-turnstile')
            if element := await self.find_or_wait_element(
                *selector, timeout=time_to_wait_captcha, raise_exc=False
            ):
                # adjust the external div size to shadow root width (usually 300px)
                await self.execute_script('argument.style="width: 300px"', element)
                await asyncio.sleep(time_before_click)
                await element.click()
        except Exception as exc:
            logger.error(f'Error in cloudflare bypass: {exc}')
