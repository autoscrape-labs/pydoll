import base64
import asyncio
import pytest
import pytest_asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch, ANY
from pathlib import Path

from pydoll.browser.options import ChromiumOptions
from pydoll.protocol.network.types import ResourceType, RequestMethod
from pydoll.protocol.fetch.types import RequestStage
from pydoll.constants import By
from pydoll.browser.tab import Tab
from pydoll.protocol.browser.events import BrowserEvent
from pydoll.protocol.browser.types import DownloadBehavior
from pydoll.exceptions import DownloadTimeout, InvalidTabInitialization
from pydoll.exceptions import (
    NoDialogPresent,
    PageLoadTimeout,
    IFrameNotFound,
    InvalidIFrame,
    NotAnIFrame,
    InvalidFileExtension,
    WaitElementTimeout,
    NetworkEventsNotEnabled,
    InvalidScriptWithElement,
    TopLevelTargetRequired,
)

@pytest_asyncio.fixture
async def mock_connection_handler():
    """Mock connection handler for Tab tests."""
    with patch('pydoll.connection.ConnectionHandler', autospec=True) as mock:
        handler = mock.return_value
        handler.execute_command = AsyncMock()
        handler.register_callback = AsyncMock()
        handler.remove_callback = AsyncMock()
        handler.clear_callbacks = AsyncMock()
        handler.network_logs = []
        handler.dialog = None
        yield handler


@pytest_asyncio.fixture
async def mock_browser():
    """Mock browser instance."""
    browser = MagicMock()
    browser.close_tab = AsyncMock()
    browser.options = ChromiumOptions()
    return browser


@pytest_asyncio.fixture
async def tab(mock_browser, mock_connection_handler):
    """Tab fixture with mocked dependencies."""
    unique_target_id = f'test-target-{uuid.uuid4().hex[:8]}'
    with patch('pydoll.browser.tab.ConnectionHandler', return_value=mock_connection_handler):
        created = Tab(
            browser=mock_browser,
            connection_port=9222,
            target_id=unique_target_id,
            browser_context_id='test-context-id'
        )
        return created


def assert_mock_called_at_least_once(mock_obj, method_name='execute_command'):
    """
    Helper function to assert that a mock was called at least once.
    This is more robust than assert_called_once() for singleton tests.
    """
    mock_method = getattr(mock_obj, method_name)
    mock_method.assert_called()
    assert mock_method.call_count >= 1


@pytest.fixture(autouse=True)
def cleanup_tab_registry():
    """No-op: singleton removed; keep fixture for compatibility."""
    yield


class TestTabInitialization:
    """Test Tab initialization and basic properties."""

    def test_tab_initialization(self, tab, mock_browser):
        """Test basic Tab initialization."""
        assert tab._browser == mock_browser
        assert tab._connection_port == 9222
        assert tab._target_id.startswith('test-target-')
        assert tab._browser_context_id == 'test-context-id'
        assert not tab.page_events_enabled
        assert not tab.network_events_enabled
        assert not tab.fetch_events_enabled
        assert not tab.dom_events_enabled
        assert not tab.runtime_events_enabled
        assert not tab.intercept_file_chooser_dialog_enabled

    def test_tab_init_raises_when_no_identifiers(self, mock_browser):
        with pytest.raises(InvalidTabInitialization):
            Tab(browser=mock_browser)

    def test_tab_properties(self, tab):
        """Test Tab boolean properties."""
        # Initially all should be False
        assert tab.page_events_enabled is False
        assert tab.network_events_enabled is False
        assert tab.fetch_events_enabled is False
        assert tab.dom_events_enabled is False
        assert tab.runtime_events_enabled is False
        assert tab.intercept_file_chooser_dialog_enabled is False

        # Test setting properties
        tab._page_events_enabled = True
        tab._network_events_enabled = True
        tab._fetch_events_enabled = True
        tab._dom_events_enabled = True
        tab._runtime_events_enabled = True
        tab._intercept_file_chooser_dialog_enabled = True

        assert tab.page_events_enabled is True
        assert tab.network_events_enabled is True
        assert tab.fetch_events_enabled is True
        assert tab.dom_events_enabled is True
        assert tab.runtime_events_enabled is True
        assert tab.intercept_file_chooser_dialog_enabled is True


class TestTabProperties:
    """Test Tab async properties."""

    @pytest.mark.asyncio
    async def test_current_url(self, tab):
        """Test current_url property."""
        tab._connection_handler.execute_command.return_value = {
            'result': {'result': {'value': 'https://example.com'}}
        }

        url = await tab.current_url
        assert url == 'https://example.com'
        # Reset mock before assertion to avoid singleton interference
        tab._connection_handler.execute_command.assert_called()
        assert tab._connection_handler.execute_command.call_count >= 1

    @pytest.mark.asyncio
    async def test_page_source(self, tab):
        """Test page_source property."""
        expected_html = '<html><body>Test Content</body></html>'
        tab._connection_handler.execute_command.return_value = {
            'result': {'result': {'value': expected_html}}
        }

        source = await tab.page_source
        assert source == expected_html
        tab._connection_handler.execute_command.assert_called()
        assert tab._connection_handler.execute_command.call_count >= 1


class TestTabEventManagement:
    """Test Tab event enabling/disabling methods."""

    @pytest.mark.asyncio
    async def test_enable_page_events(self, tab):
        """Test enabling page events."""
        await tab.enable_page_events()
        assert tab.page_events_enabled is True
        assert_mock_called_at_least_once(tab._connection_handler)

    @pytest.mark.asyncio
    async def test_enable_network_events(self, tab):
        """Test enabling network events."""
        await tab.enable_network_events()
        assert tab.network_events_enabled is True
        assert_mock_called_at_least_once(tab._connection_handler)

    @pytest.mark.asyncio
    async def test_enable_fetch_events(self, tab):
        """Test enabling fetch events with default parameters."""
        await tab.enable_fetch_events()
        assert tab.fetch_events_enabled is True
        assert_mock_called_at_least_once(tab._connection_handler)

    @pytest.mark.asyncio
    async def test_enable_fetch_events_with_params(self, tab):
        """Test enabling fetch events with custom parameters."""
        await tab.enable_fetch_events(
            handle_auth=True,
            resource_type=ResourceType.DOCUMENT,
            request_stage=RequestStage.REQUEST
        )
        assert tab.fetch_events_enabled is True
        assert_mock_called_at_least_once(tab._connection_handler)

    @pytest.mark.asyncio
    async def test_enable_dom_events(self, tab):
        """Test enabling DOM events."""
        await tab.enable_dom_events()
        assert tab.dom_events_enabled is True
        assert_mock_called_at_least_once(tab._connection_handler)

    @pytest.mark.asyncio
    async def test_enable_runtime_events(self, tab):
        """Test enabling runtime events."""
        await tab.enable_runtime_events()
        assert tab.runtime_events_enabled is True
        assert_mock_called_at_least_once(tab._connection_handler)

    @pytest.mark.asyncio
    async def test_enable_intercept_file_chooser_dialog(self, tab):
        """Test enabling file chooser dialog interception."""
        await tab.enable_intercept_file_chooser_dialog()
        assert tab.intercept_file_chooser_dialog_enabled is True
        assert_mock_called_at_least_once(tab._connection_handler)

    @pytest.mark.asyncio
    async def test_disable_fetch_events(self, tab):
        """Test disabling fetch events."""
        tab._fetch_events_enabled = True
        await tab.disable_fetch_events()
        assert tab.fetch_events_enabled is False
        assert_mock_called_at_least_once(tab._connection_handler)

    @pytest.mark.asyncio
    async def test_disable_page_events(self, tab):
        """Test disabling page events."""
        tab._page_events_enabled = True
        await tab.disable_page_events()
        assert tab.page_events_enabled is False
        assert_mock_called_at_least_once(tab._connection_handler)

    @pytest.mark.asyncio
    async def test_disable_network_events(self, tab):
        """Test disabling network events."""
        tab._network_events_enabled = True
        await tab.disable_network_events()
        assert tab.network_events_enabled is False
        assert_mock_called_at_least_once(tab._connection_handler)

    @pytest.mark.asyncio
    async def test_disable_dom_events(self, tab):
        """Test disabling DOM events."""
        tab._dom_events_enabled = True
        await tab.disable_dom_events()
        assert tab.dom_events_enabled is False
        assert_mock_called_at_least_once(tab._connection_handler)

    @pytest.mark.asyncio
    async def test_disable_runtime_events(self, tab):
        """Test disabling runtime events."""
        tab._runtime_events_enabled = True
        await tab.disable_runtime_events()
        assert tab.runtime_events_enabled is False
        assert_mock_called_at_least_once(tab._connection_handler)

    @pytest.mark.asyncio
    async def test_disable_intercept_file_chooser_dialog(self, tab):
        """Test disabling file chooser dialog interception."""
        tab._intercept_file_chooser_dialog_enabled = True
        await tab.disable_intercept_file_chooser_dialog()
        assert tab.intercept_file_chooser_dialog_enabled is False
        assert_mock_called_at_least_once(tab._connection_handler)


class TestTabCookieManagement:
    """Test Tab cookie management methods."""

    @pytest.mark.asyncio
    async def test_get_cookies(self, tab):
        """Test getting cookies."""
        test_cookies = [{'name': 'test', 'value': 'value', 'domain': 'example.com'}]
        tab._connection_handler.execute_command.return_value = {
            'result': {'cookies': test_cookies}
        }

        cookies = await tab.get_cookies()
        assert cookies == test_cookies
        assert_mock_called_at_least_once(tab._connection_handler)

    @pytest.mark.asyncio
    async def test_set_cookies(self, tab):
        """Test setting cookies."""
        test_cookies = [{'name': 'test', 'value': 'value', 'domain': 'example.com'}]
        await tab.set_cookies(test_cookies)
        
        # Should call Network command for each cookie
        assert tab._connection_handler.execute_command.call_count == 1

    @pytest.mark.asyncio
    async def test_delete_all_cookies(self, tab):
        """Test deleting all cookies."""
        await tab.delete_all_cookies()
        
        # Should call Network command to clear cookies
        assert tab._connection_handler.execute_command.call_count == 1


class TestTabNavigation:
    """Test Tab navigation methods."""

    @pytest.mark.asyncio
    async def test_go_to_new_url(self, tab):
        """Test navigating to a new URL."""
        tab._connection_handler.execute_command.side_effect = [
            {'result': {'result': {'value': 'https://old-url.com'}}},  # current_url
            {'result': {'frameId': 'frame-id'}},  # navigate command
            {'result': {'result': {'value': 'complete'}}},  # _wait_page_load
        ]
        
        await tab.go_to('https://example.com')
        
        # Should call current_url, navigate, and _wait_page_load
        assert tab._connection_handler.execute_command.call_count == 3

    @pytest.mark.asyncio
    async def test_go_to_same_url(self, tab):
        """Test navigating to the same URL (should refresh)."""
        tab._connection_handler.execute_command.side_effect = [
            {'result': {'result': {'value': 'https://example.com'}}},  # current_url
            {'result': {}},  # refresh command
            {'result': {'result': {'value': 'complete'}}},  # _wait_page_load
        ]
        
        await tab.go_to('https://example.com')
        
        # Should call current_url, refresh, and _wait_page_load
        assert tab._connection_handler.execute_command.call_count == 3

    @pytest.mark.asyncio
    async def test_go_to_timeout(self, tab):
        """Test navigation timeout."""
        # Mock current_url to return different URL
        tab._connection_handler.execute_command.side_effect = [
            {'result': {'result': {'value': 'https://old-url.com'}}},  # current_url
            {'result': {'frameId': 'frame-id'}},  # navigate command
            {'result': {'result': {'value': 'loading'}}},  # _wait_page_load (loading state)
            {'result': {'result': {'value': 'loading'}}},  # _wait_page_load (still loading)
        ]
        
        # Mock time to simulate timeout
        with patch('pydoll.browser.tab.asyncio.get_event_loop') as mock_loop:
            mock_loop.return_value.time.side_effect = [0, 1]  # timeout after 1 second
            with patch('pydoll.browser.tab.asyncio.sleep', AsyncMock()):
                with pytest.raises(PageLoadTimeout):
                    await tab.go_to('https://example.com', timeout=0.5)

    @pytest.mark.asyncio
    async def test_refresh(self, tab):
        """Test page refresh."""
        tab._connection_handler.execute_command.side_effect = [
            {'result': {}},  # refresh command
            {'result': {'result': {'value': 'complete'}}},  # _wait_page_load
        ]
        
        await tab.refresh()
        
        # Should call refresh and _wait_page_load
        assert tab._connection_handler.execute_command.call_count == 2

    @pytest.mark.asyncio
    async def test_refresh_with_params(self, tab):
        """Test page refresh with parameters."""
        tab._connection_handler.execute_command.side_effect = [
            {'result': {}},  # refresh command
            {'result': {'result': {'value': 'complete'}}},  # _wait_page_load
        ]
        
        await tab.refresh(ignore_cache=True, script_to_evaluate_on_load='console.log("test")')
        
        # Should call refresh and _wait_page_load
        assert tab._connection_handler.execute_command.call_count == 2


class TestTabScreenshotAndPDF:
    """Test Tab screenshot and PDF methods."""

    @pytest.mark.asyncio
    async def test_take_screenshot_to_file(self, tab, tmp_path):
        """Test taking screenshot and saving to file."""
        screenshot_data = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/wcAAgAB/edzE+oAAAAASUVORK5CYII='
        tab._connection_handler.execute_command.return_value = {
            'result': {'data': screenshot_data}
        }
        
        screenshot_path = tmp_path / 'screenshot.png'
        
        # Mock aiofiles.open properly for async context manager
        mock_file = AsyncMock()
        mock_file.write = AsyncMock()
        
        with patch('aiofiles.open') as mock_aiofiles_open:
            mock_aiofiles_open.return_value.__aenter__.return_value = mock_file
            result = await tab.take_screenshot(str(screenshot_path))
        
        assert result is None  # Should return None when saving to file
        assert_mock_called_at_least_once(tab._connection_handler)

    @pytest.mark.asyncio
    async def test_take_screenshot_as_base64(self, tab):
        """Test taking screenshot and returning as base64."""
        screenshot_data = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/wcAAgAB/edzE+oAAAAASUVORK5CYII='
        tab._connection_handler.execute_command.return_value = {
            'result': {'data': screenshot_data}
        }
        
        result = await tab.take_screenshot('screenshot.png', as_base64=True)
        
        assert result == screenshot_data
        assert_mock_called_at_least_once(tab._connection_handler)

    @pytest.mark.asyncio
    async def test_take_screenshot_beyond_viewport(self, tab):
        """Test capture_beyond_viewport flag is forwarded to command."""
        screenshot_data = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/wcAAgAB/edzE+oAAAAASUVORK5CYII='

        with patch.object(tab, '_execute_command', AsyncMock(return_value={
            'result': {'data': screenshot_data}
        })) as mock_execute:
            result = await tab.take_screenshot(
                path=None,
                beyond_viewport=True,
                as_base64=True,
            )

            mock_execute.assert_called_once()
            command = mock_execute.call_args[0][0]
            assert command['method'] == 'Page.captureScreenshot'
            assert command['params']['captureBeyondViewport'] is True
            assert result == screenshot_data

    @pytest.mark.asyncio
    async def test_take_screenshot_in_iframe_raises_top_level_required(self, tab):
        """Tab.take_screenshot must be called on top-level targets; iframe Tab raises."""
        # Simulate CDP returning no image data (missing 'data' key) for non top-level target
        with patch.object(tab, '_execute_command', AsyncMock(return_value={'result': {}})):
            with pytest.raises(TopLevelTargetRequired):
                await tab.take_screenshot(path=None, as_base64=True)

    @pytest.mark.asyncio
    async def test_print_to_pdf_to_file(self, tab, tmp_path):
        """Test printing to PDF and saving to file."""
        pdf_data = 'JVBERi0xLjQKJdPr6eEKMSAwIG9iago8PAovVHlwZSAvQ2F0YWxvZwo+PgplbmRvYmoKdHJhaWxlcgo8PAovUm9vdCAxIDAgUgo+PgpzdGFydHhyZWYKMTgKJSVFT0Y='
        tab._connection_handler.execute_command.return_value = {
            'result': {'data': pdf_data}
        }
        
        pdf_path = tmp_path / 'document.pdf'
        
        # Mock aiofiles.open properly for async context manager
        mock_file = AsyncMock()
        mock_file.write = AsyncMock()
        
        with patch('aiofiles.open') as mock_aiofiles_open:
            mock_aiofiles_open.return_value.__aenter__.return_value = mock_file
            result = await tab.print_to_pdf(str(pdf_path))
        
        assert result is None  # Should return None when saving to file
        assert_mock_called_at_least_once(tab._connection_handler)

    @pytest.mark.asyncio
    async def test_print_to_pdf_as_base64(self, tab):
        """Test printing to PDF and returning as base64."""
        pdf_data = 'JVBERi0xLjQKJdPr6eEKMSAwIG9iago8PAovVHlwZSAvQ2F0YWxvZwo+PgplbmRvYmoKdHJhaWxlcgo8PAovUm9vdCAxIDAgUgo+PgpzdGFydHhyZWYKMTgKJSVFT0Y='
        tab._connection_handler.execute_command.return_value = {
            'result': {'data': pdf_data}
        }
        
        result = await tab.print_to_pdf('', as_base64=True)
        
        assert result == pdf_data
        assert_mock_called_at_least_once(tab._connection_handler)

    @pytest.mark.asyncio
    async def test_print_to_pdf_with_options(self, tab, tmp_path):
        """Test printing to PDF with custom options."""
        pdf_data = 'JVBERi0xLjQKJdPr6eEKMSAwIG9iago8PAovVHlwZSAvQ2F0YWxvZwo+PgplbmRvYmoKdHJhaWxlcgo8PAovUm9vdCAxIDAgUgo+PgpzdGFydHhyZWYKMTgKJSVFT0Y='
        tab._connection_handler.execute_command.return_value = {
            'result': {'data': pdf_data}
        }
        
        pdf_path = tmp_path / 'document.pdf'
        
        # Mock aiofiles.open properly for async context manager
        mock_file = AsyncMock()
        mock_file.write = AsyncMock()
        
        with patch('aiofiles.open') as mock_aiofiles_open:
            mock_aiofiles_open.return_value.__aenter__.return_value = mock_file
            result = await tab.print_to_pdf(
                str(pdf_path),
                landscape=True,
                display_header_footer=True,
                print_background=False,
                scale=0.8
            )
        
        assert result is None
        assert_mock_called_at_least_once(tab._connection_handler)


class TestTabDialogHandling:
    """Test Tab dialog handling methods."""

    @pytest.mark.asyncio
    async def test_has_dialog_true(self, tab):
        """Test has_dialog when dialog is present."""
        tab._connection_handler.dialog = {'params': {'type': 'alert', 'message': 'Test'}}
        
        result = await tab.has_dialog()
        assert result is True

    @pytest.mark.asyncio
    async def test_has_dialog_false(self, tab):
        """Test has_dialog when no dialog is present."""
        tab._connection_handler.dialog = None
        
        result = await tab.has_dialog()
        assert result is False

    @pytest.mark.asyncio
    async def test_get_dialog_message_success(self, tab):
        """Test getting dialog message when dialog is present."""
        tab._connection_handler.dialog = {'params': {'message': 'Test message'}}
        
        message = await tab.get_dialog_message()
        assert message == 'Test message'

    @pytest.mark.asyncio
    async def test_get_dialog_message_no_dialog(self, tab):
        """Test getting dialog message when no dialog is present."""
        tab._connection_handler.dialog = None
        
        with pytest.raises(NoDialogPresent):
            await tab.get_dialog_message()

    @pytest.mark.asyncio
    async def test_handle_dialog_accept(self, tab):
        """Test accepting a dialog."""
        tab._connection_handler.dialog = {'params': {'type': 'alert'}}
        
        await tab.handle_dialog(accept=True)
        
        assert_mock_called_at_least_once(tab._connection_handler)

    @pytest.mark.asyncio
    async def test_handle_dialog_dismiss(self, tab):
        """Test dismissing a dialog."""
        tab._connection_handler.dialog = {'params': {'type': 'confirm'}}
        
        await tab.handle_dialog(accept=False)
        
        assert_mock_called_at_least_once(tab._connection_handler)

    @pytest.mark.asyncio
    async def test_handle_dialog_with_prompt_text(self, tab):
        """Test handling a prompt dialog with text."""
        tab._connection_handler.dialog = {'params': {'type': 'prompt'}}
        
        await tab.handle_dialog(accept=True, prompt_text='Test input')
        
        assert_mock_called_at_least_once(tab._connection_handler)

    @pytest.mark.asyncio
    async def test_handle_dialog_no_dialog(self, tab):
        """Test handling dialog when none is present."""
        tab._connection_handler.dialog = None
        
        with pytest.raises(NoDialogPresent):
            await tab.handle_dialog(accept=True)


class TestTabScriptExecution:
    """Test Tab script execution methods."""

    @pytest.mark.asyncio
    async def test_execute_script_simple(self, tab):
        """Test execute_script with simple JavaScript."""
        tab._connection_handler.execute_command.return_value = {
            'result': {'result': {'value': 'Test Result'}}
        }
        
        result = await tab.execute_script('return "Test Result"')
        
        assert_mock_called_at_least_once(tab._connection_handler)

    @pytest.mark.asyncio
    async def test_execute_script_with_element(self, tab):
        """Test execute_script with element context."""
        # Mock element
        element = MagicMock()
        element._object_id = 'test-object-id'
        
        tab._connection_handler.execute_command.return_value = {
            'result': {'result': {'value': 'Element clicked'}}
        }
        
        result = await tab.execute_script('argument.click()', element)
        
        assert_mock_called_at_least_once(tab._connection_handler)

    @pytest.mark.asyncio
    async def test_execute_script_argument_without_element_raises_exception(self, tab):
        """Test execute_script raises exception when script contains 'argument' but no element provided."""
        with pytest.raises(InvalidScriptWithElement) as exc_info:
            await tab.execute_script('argument.click()')
        
        assert str(exc_info.value) == 'Script contains "argument" but no element was provided'
        tab._connection_handler.execute_command.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_script_element_without_argument_raises_exception(self, tab):
        """Test execute_script raises exception when element is provided but script doesn't contain 'argument'."""
        element = MagicMock()
        element._object_id = 'test-object-id'
        
        with pytest.raises(InvalidScriptWithElement) as exc_info:
            await tab.execute_script('console.log("test")', element)
        
        assert str(exc_info.value) == 'Script does not contain "argument"'
        tab._connection_handler.execute_command.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_script_with_element_already_function(self, tab):
        """Test execute_script with element when script is already a function."""
        element = MagicMock()
        element._object_id = 'test-object-id'
        
        tab._connection_handler.execute_command.return_value = {
            'result': {'result': {'value': 'Function executed'}}
        }
        
        # Script already wrapped in function
        script = 'function() { argument.click(); return "done"; }'
        result = await tab.execute_script(script, element)
        
        assert_mock_called_at_least_once(tab._connection_handler)

    @pytest.mark.asyncio
    async def test_execute_script_with_element_arrow_function(self, tab):
        """Test execute_script with element when script is already an arrow function."""
        element = MagicMock()
        element._object_id = 'test-object-id'
        
        tab._connection_handler.execute_command.return_value = {
            'result': {'result': {'value': 'Arrow function executed'}}
        }
        
        # Script already wrapped in arrow function
        script = '() => { argument.click(); return "done"; }'
        result = await tab.execute_script(script, element)
        
        assert_mock_called_at_least_once(tab._connection_handler)

    @pytest.mark.asyncio
    async def test_execute_script_return_outside_function(self, tab):
        """Test execute_script wraps return statement outside function."""
        tab._connection_handler.execute_command.return_value = {
            'result': {'result': {'value': 'Wrapped result'}}
        }
        
        # Script with return outside function should be wrapped
        result = await tab.execute_script('return document.title')
        
        assert_mock_called_at_least_once(tab._connection_handler)

    @pytest.mark.asyncio
    async def test_execute_script_return_inside_function(self, tab):
        """Test execute_script doesn't wrap when return is inside function."""
        tab._connection_handler.execute_command.return_value = {
            'result': {'result': {'value': 'Function result'}}
        }
        
        # Script with return inside function should not be wrapped
        script = '''
        function getTitle() {
            return document.title;
        }
        getTitle();
        '''
        result = await tab.execute_script(script)
        
        assert_mock_called_at_least_once(tab._connection_handler)

    @pytest.mark.asyncio
    async def test_execute_script_no_return_statement(self, tab):
        """Test execute_script without return statement."""
        tab._connection_handler.execute_command.return_value = {
            'result': {'result': {'value': None}}
        }
        
        # Script without return should not be wrapped
        result = await tab.execute_script('console.log("Hello World")')
        
        assert_mock_called_at_least_once(tab._connection_handler)

    @pytest.mark.asyncio
    async def test_execute_script_with_comments_and_strings(self, tab):
        """Test execute_script handles comments and strings correctly."""
        tab._connection_handler.execute_command.return_value = {
            'result': {'result': {'value': 'Test with comments'}}
        }
        
        # Script with comments and strings containing 'return'
        script = '''
        // This comment has return in it
        var message = "This string has return in it";
        /* This block comment also has return */
        return "actual return";
        '''
        result = await tab.execute_script(script)
        
        assert_mock_called_at_least_once(tab._connection_handler)

    @pytest.mark.asyncio
    async def test_execute_script_already_wrapped_function(self, tab):
        """Test execute_script with already wrapped function."""
        tab._connection_handler.execute_command.return_value = {
            'result': {'result': {'value': 'Already wrapped'}}
        }
        
        # Script already wrapped in function should not be wrapped again
        script = 'function() { console.log("test"); return "done"; }'
        result = await tab.execute_script(script)
        
        assert_mock_called_at_least_once(tab._connection_handler)


class TestTabEventCallbacks:
    """Test Tab event callback management."""

    @pytest.mark.asyncio
    async def test_on_callback_registration(self, tab):
        """Test registering event callbacks."""
        callback_id = 123
        tab._connection_handler.register_callback.return_value = callback_id
        
        async def test_callback(event):
            pass
        
        result = await tab.on('Page.loadEventFired', test_callback)
        
        assert result == callback_id
        assert_mock_called_at_least_once(tab._connection_handler, 'register_callback')

    @pytest.mark.asyncio
    async def test_on_temporary_callback(self, tab):
        """Test registering temporary event callbacks."""
        callback_id = 456
        tab._connection_handler.register_callback.return_value = callback_id
        
        async def test_callback(event):
            pass
        
        result = await tab.on('Page.loadEventFired', test_callback, temporary=True)
        
        assert result == callback_id
        tab._connection_handler.register_callback.assert_called_with(
            'Page.loadEventFired', ANY, True
        )
        assert tab._connection_handler.register_callback.call_count >= 1

    @pytest.mark.asyncio
    async def test_remove_callback_success(self, tab):
        """Tab.remove_callback should forward to connection handler and return True."""
        tab._connection_handler.remove_callback.return_value = True

        result = await tab.remove_callback(123)

        tab._connection_handler.remove_callback.assert_called_with(123)
        assert result is True

    @pytest.mark.asyncio
    async def test_remove_callback_false(self, tab):
        """Tab.remove_callback should return False when handler returns False."""
        tab._connection_handler.remove_callback.return_value = False

        result = await tab.remove_callback(999)

        tab._connection_handler.remove_callback.assert_called_with(999)
        assert result is False


class TestTabFileChooser:
    """Test Tab file chooser functionality."""

    @pytest.mark.asyncio
    async def test_expect_file_chooser_single_file(self, tab):
        """Test expect_file_chooser with single file."""
        tab._connection_handler.register_callback.return_value = 123
        
        # Set initial state to False so methods get called
        tab._page_events_enabled = False
        tab._intercept_file_chooser_dialog_enabled = False
        
        mock_enable_page_events = AsyncMock()
        mock_enable_intercept = AsyncMock(side_effect=lambda: setattr(tab, '_intercept_file_chooser_dialog_enabled', True))
        mock_disable_intercept = AsyncMock()
        mock_on = AsyncMock()
        
        with patch.object(tab, 'enable_page_events', mock_enable_page_events):
            with patch.object(tab, 'enable_intercept_file_chooser_dialog', mock_enable_intercept):
                with patch.object(tab, 'disable_intercept_file_chooser_dialog', mock_disable_intercept):
                    with patch.object(tab, 'on', mock_on):
                        async with tab.expect_file_chooser('test.txt'):
                            pass
        
        mock_enable_page_events.assert_awaited_once()
        mock_enable_intercept.assert_awaited_once()
        mock_disable_intercept.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_expect_file_chooser_multiple_files(self, tab):
        """Test expect_file_chooser with multiple files."""
        tab._connection_handler.register_callback.return_value = 456
        
        files = ['file1.txt', 'file2.txt', 'file3.txt']
        
        # Set initial state to False so methods get called
        tab._page_events_enabled = False
        tab._intercept_file_chooser_dialog_enabled = False
        
        mock_enable_page_events = AsyncMock()
        mock_enable_intercept = AsyncMock(side_effect=lambda: setattr(tab, '_intercept_file_chooser_dialog_enabled', True))
        mock_disable_intercept = AsyncMock()
        mock_on = AsyncMock()
        
        with patch.object(tab, 'enable_page_events', mock_enable_page_events):
            with patch.object(tab, 'enable_intercept_file_chooser_dialog', mock_enable_intercept):
                with patch.object(tab, 'disable_intercept_file_chooser_dialog', mock_disable_intercept):
                    with patch.object(tab, 'on', mock_on):
                        async with tab.expect_file_chooser(files):
                            pass
        
        mock_enable_page_events.assert_called_once()
        mock_enable_intercept.assert_called_once()
        mock_disable_intercept.assert_called_once()

    @pytest.mark.asyncio
    async def test_expect_file_chooser_with_path_objects(self, tab):
        """Test expect_file_chooser with Path objects."""
        tab._connection_handler.register_callback.return_value = 789
        
        files = [Path('file1.txt'), Path('file2.txt')]
        
        # Set initial state to False so methods get called
        tab._page_events_enabled = False
        tab._intercept_file_chooser_dialog_enabled = False
        
        mock_enable_page_events = AsyncMock()
        mock_enable_intercept = AsyncMock(side_effect=lambda: setattr(tab, '_intercept_file_chooser_dialog_enabled', True))
        mock_disable_intercept = AsyncMock()
        mock_on = AsyncMock()
        
        with patch.object(tab, 'enable_page_events', mock_enable_page_events):
            with patch.object(tab, 'enable_intercept_file_chooser_dialog', mock_enable_intercept):
                with patch.object(tab, 'disable_intercept_file_chooser_dialog', mock_disable_intercept):
                    with patch.object(tab, 'on', mock_on):
                        async with tab.expect_file_chooser(files):
                            pass
        
        mock_enable_page_events.assert_called_once()
        mock_enable_intercept.assert_called_once()
        mock_disable_intercept.assert_called_once()

    @pytest.mark.asyncio
    async def test_expect_file_chooser_event_handler_single_file(self, tab):
        """Test the real event_handler function with single file."""
        from pydoll.protocol.page.events import FileChooserOpenedEvent, PageEvent
        
        # Mock execute_command to capture the call
        tab._execute_command = AsyncMock()
        
        # Create mock event data
        mock_event: FileChooserOpenedEvent = {
            'method': 'Page.fileChooserOpened',
            'params': {
                'frameId': 'test-frame-id',
                'mode': 'selectSingle',
                'backendNodeId': 12345
            }
        }
        
        # Capture the real event handler from expect_file_chooser
        captured_handler = None
        
        async def mock_on(event_name, handler, temporary=False):
            nonlocal captured_handler
            if event_name == PageEvent.FILE_CHOOSER_OPENED:
                captured_handler = handler
            return 123
        
        # Mock the required methods
        with patch.object(tab, 'enable_page_events', AsyncMock()):
            with patch.object(tab, 'enable_intercept_file_chooser_dialog', AsyncMock()):
                with patch.object(tab, 'disable_intercept_file_chooser_dialog', AsyncMock()):
                    with patch.object(tab, 'disable_page_events', AsyncMock()):
                        with patch.object(tab, 'on', mock_on):
                            async with tab.expect_file_chooser('test.txt'):
                                # Execute the captured real handler
                                assert captured_handler is not None
                                await captured_handler(mock_event)
        
        # Verify the command was called correctly
        tab._execute_command.assert_called_once()
        call_args = tab._execute_command.call_args[0][0]
        assert call_args['method'] == 'DOM.setFileInputFiles'
        assert call_args['params']['files'] == ['test.txt']
        assert call_args['params']['backendNodeId'] == 12345

    @pytest.mark.asyncio
    async def test_expect_file_chooser_event_handler_multiple_files(self, tab):
        """Test the real event_handler function with multiple files."""
        from pydoll.protocol.page.events import FileChooserOpenedEvent, PageEvent
        
        # Mock execute_command to capture the call
        tab._execute_command = AsyncMock()
        
        # Create mock event data
        mock_event: FileChooserOpenedEvent = {
            'method': 'Page.fileChooserOpened',
            'params': {
                'frameId': 'test-frame-id',
                'mode': 'selectMultiple',
                'backendNodeId': 67890
            }
        }

        # Capture the real event handler from expect_file_chooser
        captured_handler = None
        
        async def mock_on(event_name, handler, temporary=False):
            nonlocal captured_handler
            if event_name == PageEvent.FILE_CHOOSER_OPENED:
                captured_handler = handler
            return 123
        
        # Mock the required methods
        with patch.object(tab, 'enable_page_events', AsyncMock()):
            with patch.object(tab, 'enable_intercept_file_chooser_dialog', AsyncMock()):
                with patch.object(tab, 'disable_intercept_file_chooser_dialog', AsyncMock()):
                    with patch.object(tab, 'disable_page_events', AsyncMock()):
                        with patch.object(tab, 'on', mock_on):
                            async with tab.expect_file_chooser(['file1.txt', 'file2.pdf', 'file3.jpg']):
                                # Execute the captured real handler
                                assert captured_handler is not None
                                await captured_handler(mock_event)
        
        # Verify the command was called correctly
        tab._execute_command.assert_called_once()
        call_args = tab._execute_command.call_args[0][0]
        assert call_args['method'] == 'DOM.setFileInputFiles'
        assert call_args['params']['files'] == ['file1.txt', 'file2.pdf', 'file3.jpg']
        assert call_args['params']['backendNodeId'] == 67890

    async def _test_event_handler_with_files(self, tab, files, expected_files, backend_node_id):
        """Helper method to test event handler with different file types."""
        from pydoll.protocol.page.events import FileChooserOpenedEvent, PageEvent
        
        # Mock execute_command to capture the call
        tab._execute_command = AsyncMock()
        
        # Create mock event data
        mock_event: FileChooserOpenedEvent = {
            'method': 'Page.fileChooserOpened',
            'params': {
                'frameId': 'test-frame-id',
                'mode': 'selectMultiple',
                'backendNodeId': backend_node_id
            }
        }
        
        # Capture the real event handler from expect_file_chooser
        captured_handler = None
        
        async def mock_on(event_name, handler, temporary=False):
            nonlocal captured_handler
            if event_name == PageEvent.FILE_CHOOSER_OPENED:
                captured_handler = handler
            return 123
        
        # Mock the required methods
        with patch.object(tab, 'enable_page_events', AsyncMock()):
            with patch.object(tab, 'enable_intercept_file_chooser_dialog', AsyncMock()):
                with patch.object(tab, 'disable_intercept_file_chooser_dialog', AsyncMock()):
                    with patch.object(tab, 'disable_page_events', AsyncMock()):
                        with patch.object(tab, 'on', mock_on):
                            async with tab.expect_file_chooser(files):
                                # Execute the captured real handler
                                assert captured_handler is not None
                                await captured_handler(mock_event)
        
        # Verify the command was called correctly
        tab._execute_command.assert_called_once()
        call_args = tab._execute_command.call_args[0][0]
        assert call_args['method'] == 'DOM.setFileInputFiles'
        assert call_args['params']['files'] == expected_files
        assert call_args['params']['backendNodeId'] == backend_node_id

    @pytest.mark.asyncio
    async def test_expect_file_chooser_event_handler_path_objects(self, tab):
        """Test the real event_handler function with Path objects."""
        from pathlib import Path
        
        files = [Path('documents/file1.txt'), Path('images/file2.jpg')]
        expected_files = [str(file) for file in files]
        
        await self._test_event_handler_with_files(tab, files, expected_files, 54321)

    @pytest.mark.asyncio
    async def test_expect_file_chooser_event_handler_single_path_object(self, tab):
        """Test the real event_handler function with single Path object."""
        from pathlib import Path
        
        files = Path('documents/important.pdf')
        expected_files = [str(files)]
        
        await self._test_event_handler_with_files(tab, files, expected_files, 98765)

    @pytest.mark.asyncio
    async def test_expect_file_chooser_event_handler_empty_list(self, tab):
        """Test the real event_handler function with empty file list."""
        files = []
        expected_files = []
        
        await self._test_event_handler_with_files(tab, files, expected_files, 11111)




class TestTabCloudflareBypass:
    """Test Tab Cloudflare bypass functionality."""

    @pytest.mark.asyncio
    async def test_enable_auto_solve_cloudflare_captcha(self, tab):
        """Test enabling auto-solve Cloudflare captcha."""
        callback_id = 999
        tab._connection_handler.register_callback.return_value = callback_id
        
        mock_enable_page_events = AsyncMock()
        with patch.object(tab, 'enable_page_events', mock_enable_page_events):
            await tab.enable_auto_solve_cloudflare_captcha()
        
        mock_enable_page_events.assert_called_once()
        assert_mock_called_at_least_once(tab._connection_handler, 'register_callback')
        assert tab._cloudflare_captcha_callback_id == callback_id

    @pytest.mark.asyncio
    async def test_enable_auto_solve_cloudflare_captcha_with_params(self, tab):
        """Test enabling auto-solve Cloudflare captcha with custom parameters."""
        callback_id = 888
        tab._connection_handler.register_callback.return_value = callback_id
        
        custom_selector = (By.ID, 'custom-captcha')
        
        mock_enable_page_events = AsyncMock()
        with patch.object(tab, 'enable_page_events', mock_enable_page_events):
            await tab.enable_auto_solve_cloudflare_captcha(
                custom_selector=custom_selector,
                time_before_click=3,
                time_to_wait_captcha=10
            )
        
        mock_enable_page_events.assert_called_once()
        assert_mock_called_at_least_once(tab._connection_handler, 'register_callback')
        assert tab._cloudflare_captcha_callback_id == callback_id


class TestTabDownload:
    """Tests for Tab.expect_download context manager."""

    @pytest.mark.asyncio
    async def test_expect_download_keeps_file_when_path_provided(self, tab, tmp_path):
        target_dir = tmp_path / "dl"
        tab._browser.set_download_behavior = AsyncMock()

        # Prepare to capture callbacks and trigger them
        handlers = {}

        async def fake_on(event_name, handler, temporary=False):
            handlers[event_name] = handler
            return 100 if event_name == BrowserEvent.DOWNLOAD_WILL_BEGIN else 101

        with patch.object(tab, 'on', fake_on):
            async with tab.expect_download(keep_file_at=str(target_dir)) as download:
                # Simulate willBegin
                await handlers[BrowserEvent.DOWNLOAD_WILL_BEGIN]({
                    'method': BrowserEvent.DOWNLOAD_WILL_BEGIN,
                    'params': {
                        'frameId': 'frame-1',
                        'guid': 'guid-1',
                        'url': 'https://example.com/file.txt',
                        'suggestedFilename': 'file.txt',
                    }
                })
                # Simulate progress Completed without filePath (fallback to suggested)
                await handlers[BrowserEvent.DOWNLOAD_PROGRESS]({
                    'method': BrowserEvent.DOWNLOAD_PROGRESS,
                    'params': {
                        'guid': 'guid-1',
                        'totalBytes': 10,
                        'receivedBytes': 10,
                        'state': 'completed',
                    }
                })

                # Create the expected file to allow read
                expected_path = target_dir / 'file.txt'
                expected_path.parent.mkdir(parents=True, exist_ok=True)
                expected_path.write_bytes(b'content')

                data = await download.read_bytes()
                assert data == b'content'
                assert str(download.file_path).endswith('file.txt')

        # Ensure behavior reset called
        tab._browser.set_download_behavior.assert_awaited()

    @pytest.mark.asyncio
    async def test_expect_download_timeout_raises(self, tab, tmp_path):
        tab._browser.set_download_behavior = AsyncMock()

        handlers = {}

        async def fake_on(event_name, handler, temporary=False):
            handlers[event_name] = handler
            return 200 if event_name == BrowserEvent.DOWNLOAD_WILL_BEGIN else 201

        with patch.object(tab, 'on', fake_on):
            with pytest.raises(DownloadTimeout):
                async with tab.expect_download(keep_file_at=str(tmp_path), timeout=0.01):
                    # Trigger will begin but never complete
                    await handlers[BrowserEvent.DOWNLOAD_WILL_BEGIN]({
                        'method': BrowserEvent.DOWNLOAD_WILL_BEGIN,
                        'params': {
                            'frameId': 'frame-1',
                            'guid': 'guid-2',
                            'url': 'https://example.com/slow.bin',
                            'suggestedFilename': 'slow.bin',
                        }
                    })
                    # Do not trigger completed
                    await asyncio.sleep(0.02)

    @pytest.mark.asyncio
    async def test_expect_download_cleans_temp_directory(self, tab, tmp_path):
        tab._browser.set_download_behavior = AsyncMock()
        handlers = {}

        async def fake_on(event_name, handler, temporary=False):
            handlers[event_name] = handler
            return 300 if event_name == BrowserEvent.DOWNLOAD_WILL_BEGIN else 301

        with patch.object(tab, 'on', fake_on):
            # Use None to create temp dir and ensure cleanup occurs
            async with tab.expect_download(keep_file_at=None) as download:
                await handlers[BrowserEvent.DOWNLOAD_WILL_BEGIN]({
                    'method': BrowserEvent.DOWNLOAD_WILL_BEGIN,
                    'params': {
                        'frameId': 'frame-1',
                        'guid': 'guid-3',
                        'url': 'https://example.com/tmp.txt',
                        'suggestedFilename': 'tmp.txt',
                    }
                })
                await handlers[BrowserEvent.DOWNLOAD_PROGRESS]({
                    'method': BrowserEvent.DOWNLOAD_PROGRESS,
                    'params': {
                        'guid': 'guid-3',
                        'totalBytes': 3,
                        'receivedBytes': 3,
                        'state': 'completed',
                    }
                })

                # Create the expected file inside the dynamically chosen dir
                assert download.file_path is not None
                file_path = Path(download.file_path)
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_bytes(b'abc')
                assert (await download.read_base64()) == base64.b64encode(b'abc').decode('ascii')

            # After context, temp dir should be removed
            # We cannot know the exact temp dir path (random), but ensure file is gone
            assert not file_path.exists()

    @pytest.mark.asyncio
    async def test_disable_auto_solve_cloudflare_captcha(self, tab):
        """Test disabling auto-solve Cloudflare captcha."""
        tab._cloudflare_captcha_callback_id = 777
        tab._connection_handler.remove_callback.return_value = True
        
        await tab.disable_auto_solve_cloudflare_captcha()
        
        tab._connection_handler.remove_callback.assert_called_with(777)

    @pytest.mark.asyncio
    async def test_expect_and_bypass_cloudflare_captcha(self, tab):
        """Test expect_and_bypass_cloudflare_captcha context manager."""
        mock_event = AsyncMock()
        mock_event.set = MagicMock()
        mock_event.wait = AsyncMock()
        
        callback_id = 666
        tab._connection_handler.register_callback.return_value = callback_id
        
        mock_enable_page_events = AsyncMock()
        mock_disable_page_events = AsyncMock()
        
        with patch.object(tab, 'enable_page_events', mock_enable_page_events):
            with patch.object(tab, 'disable_page_events', mock_disable_page_events):
                with patch('asyncio.Event', return_value=mock_event):
                    async with tab.expect_and_bypass_cloudflare_captcha():
                        pass
        
        mock_enable_page_events.assert_called_once()
        mock_disable_page_events.assert_called_once()
        assert_mock_called_at_least_once(tab._connection_handler, 'register_callback')
        tab._connection_handler.remove_callback.assert_called_with(callback_id)

    @pytest.mark.asyncio
    async def test_bypass_cloudflare_with_element_found(self, tab):
        """Test _bypass_cloudflare when element is found."""
        mock_element = AsyncMock()
        
        mock_find = AsyncMock(return_value=mock_element)
        mock_execute_script = AsyncMock()
        
        with patch.object(tab, 'find_or_wait_element', mock_find):
            with patch.object(tab, 'execute_script', mock_execute_script):
                with patch('asyncio.sleep', AsyncMock()):
                    await tab._bypass_cloudflare({})
        
        mock_find.assert_called_once()
        mock_execute_script.assert_called_once()
        mock_element.click.assert_called_once()

    @pytest.mark.asyncio
    async def test_bypass_cloudflare_no_element_found(self, tab):
        """Test _bypass_cloudflare when no element is found."""
        mock_find = AsyncMock(return_value=None)
        mock_execute_script = AsyncMock()
        
        with patch.object(tab, 'find_or_wait_element', mock_find):
            with patch.object(tab, 'execute_script', mock_execute_script):
                await tab._bypass_cloudflare({})
        
        mock_find.assert_called_once()
        # execute_script and click should not be called
        mock_execute_script.assert_not_called()

    @pytest.mark.asyncio
    async def test_bypass_cloudflare_with_custom_selector(self, tab):
        """Test _bypass_cloudflare with custom selector."""
        mock_element = AsyncMock()
        custom_selector = (By.ID, 'custom-captcha')
        
        mock_find = AsyncMock(return_value=mock_element)
        mock_execute_script = AsyncMock()
        
        with patch.object(tab, 'find_or_wait_element', mock_find):
            with patch.object(tab, 'execute_script', mock_execute_script):
                with patch('asyncio.sleep', AsyncMock()):
                    await tab._bypass_cloudflare(
                        {},
                        custom_selector=custom_selector,
                        time_before_click=3,
                        time_to_wait_captcha=10
                    )
        
        mock_find.assert_called_with(
            By.ID, 'custom-captcha', timeout=10, raise_exc=False
        )


class TestTabFrameHandling:
    """Test Tab iframe handling methods."""

    @pytest.mark.asyncio
    async def test_get_frame_success(self, tab, mock_browser):
        """Test getting frame from iframe element."""
        mock_iframe_element = MagicMock()
        mock_iframe_element.tag_name = 'iframe'
        mock_iframe_element.get_attribute.return_value = 'https://example.com/iframe'
        mock_iframe_element._object_id = 'iframe-object-id'
        
        mock_browser.get_targets = AsyncMock(return_value=[
            {'targetId': 'iframe-target-id', 'url': 'https://example.com/iframe'}
        ])

        frame = await tab.get_frame(mock_iframe_element)
        
        assert isinstance(frame, Tab)
        mock_browser.get_targets.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_frame_uses_cache_on_subsequent_calls(self, tab, mock_browser):
        """Subsequent calls to get_frame should return cached Tab instance."""
        # Prepare iframe element
        mock_iframe_element = MagicMock()
        mock_iframe_element.tag_name = 'iframe'
        frame_url = 'https://example.com/iframe'
        mock_iframe_element.get_attribute.return_value = frame_url
        # Prepare browser targets and cache
        mock_browser.get_targets = AsyncMock(return_value=[
            {'targetId': 'iframe-target-id', 'url': frame_url, 'type': 'page'}
        ])
        tab._browser._tabs_opened = {}

        with patch('pydoll.browser.tab.ConnectionHandler', autospec=True):
            frame1 = await tab.get_frame(mock_iframe_element)
            # Second call should reuse from cache and not create a new Tab
            frame2 = await tab.get_frame(mock_iframe_element)

        assert isinstance(frame1, Tab)
        assert frame1 is frame2
        assert tab._browser._tabs_opened['iframe-target-id'] is frame1

    @pytest.mark.asyncio
    async def test_get_frame_not_iframe(self, tab):
        """Test getting frame from non-iframe element."""
        mock_element = MagicMock()
        mock_element.tag_name = 'div'  # Mock the property directly
        
        with pytest.raises(NotAnIFrame):
            await tab.get_frame(mock_element)

    @pytest.mark.asyncio
    async def test_get_frame_no_frame_id(self, tab, mock_browser):
        """Test getting frame when no frame ID is found."""
        mock_iframe_element = MagicMock()
        mock_iframe_element.tag_name = 'iframe'  # Mock the _attributes dict
        mock_iframe_element.get_attribute.return_value = 'https://example.com/iframe'
        mock_iframe_element._object_id = 'iframe-object-id'

        mock_browser.get_targets = AsyncMock(return_value=[])
        
        with pytest.raises(IFrameNotFound):
            await tab.get_frame(mock_iframe_element)


class TestTabUtilityMethods:
    """Test Tab utility and helper methods."""

    @pytest.mark.asyncio
    async def test_bring_to_front(self, tab):
        """Test bringing the tab to front sends the correct command."""
        with patch.object(tab, '_execute_command', AsyncMock()) as mock_execute:
            await tab.bring_to_front()

            mock_execute.assert_called_once()
            command = mock_execute.call_args[0][0]
            assert command['method'] == 'Page.bringToFront'

    @pytest.mark.asyncio
    async def test_close(self, tab, mock_browser):
        """Test closing the tab."""
        with patch.object(tab, '_execute_command', AsyncMock()) as mock_execute:
            await tab.close()
            
            # Should call _execute_command with PageCommands.close()
            mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_wait_page_load_complete(self, tab):
        """Test _wait_page_load when page is complete."""
        tab._connection_handler.execute_command.return_value = {
            'result': {'result': {'value': 'complete'}}
        }
        
        await tab._wait_page_load()
        
        assert_mock_called_at_least_once(tab._connection_handler)

    @pytest.mark.asyncio
    async def test_wait_page_load_timeout(self, tab):
        """Test _wait_page_load timeout."""
        # Mock execute_command to always return 'loading' state
        tab._connection_handler.execute_command.return_value = {
            'result': {'result': {'value': 'loading'}}
        }
        
        # Mock time to simulate timeout without actually waiting
        with patch('pydoll.browser.tab.asyncio.get_event_loop') as mock_loop:
            # First call returns 0, second call returns time > timeout
            mock_loop.return_value.time.side_effect = [0, 1]  # 1 > 0.5 timeout
            with patch('pydoll.browser.tab.asyncio.sleep', AsyncMock()):
                with pytest.raises(WaitElementTimeout, match="Page load timed out"):
                    await tab._wait_page_load(timeout=0.5)

    @pytest.mark.asyncio
    async def test_refresh_if_url_not_changed_same_url(self, tab):
        """Test _refresh_if_url_not_changed with same URL."""
        # Mock multiple calls: current_url, refresh, and _wait_page_load
        tab._connection_handler.execute_command.side_effect = [
            {'result': {'result': {'value': 'https://example.com'}}},  # current_url call
            {'result': {}},  # refresh call
            {'result': {'result': {'value': 'complete'}}},  # _wait_page_load call
        ]
        
        result = await tab._refresh_if_url_not_changed('https://example.com')
        
        assert result is True
        assert tab._connection_handler.execute_command.call_count == 3

    @pytest.mark.asyncio
    async def test_refresh_if_url_not_changed_different_url(self, tab):
        """Test _refresh_if_url_not_changed with different URL."""
        tab._connection_handler.execute_command.return_value = {
            'result': {'result': {'value': 'https://different.com'}}
        }
        
        result = await tab._refresh_if_url_not_changed('https://example.com')
        
        assert result is False
        assert_mock_called_at_least_once(tab._connection_handler)


class TestTabRequestManagement:
    """Test Tab request management methods."""

    @pytest.mark.asyncio
    async def test_continue_request(self, tab):
        """Test continue_request method with minimal parameters."""
        request_id = 'test_request_123'
        
        await tab.continue_request(request_id)
        
        # Verify the command was executed with correct parameters
        assert_mock_called_at_least_once(tab._connection_handler)
        
        # Get the call arguments to verify the command
        call_args = tab._connection_handler.execute_command.call_args_list[-1]
        command = call_args[0][0]  # First argument is the command
        
        # Verify it's a FetchCommands.continue_request command
        assert command['method'] == 'Fetch.continueRequest'
        assert command['params']['requestId'] == request_id
        # Verify optional parameters are None/not set
        params = command['params']
        assert params.get('url') is None
        assert params.get('method') is None
        assert params.get('postData') is None
        assert params.get('headers') is None
        assert params.get('interceptResponse') is None

    @pytest.mark.asyncio
    async def test_fail_request(self, tab):
        """Test fail_request method."""
        from pydoll.protocol.network.types import ErrorReason
        
        request_id = 'test_request_456'
        error_reason = ErrorReason.FAILED
        
        await tab.fail_request(request_id, error_reason)
        
        # Verify the command was executed with correct parameters
        assert_mock_called_at_least_once(tab._connection_handler)
        
        # Get the call arguments to verify the command
        call_args = tab._connection_handler.execute_command.call_args_list[-1]
        command = call_args[0][0]  # First argument is the command
        
        # Verify it's a FetchCommands.fail_request command
        assert command['method'] == 'Fetch.failRequest'
        assert command['params']['requestId'] == request_id
        assert command['params']['errorReason'] == error_reason

    @pytest.mark.asyncio
    async def test_fulfill_request(self, tab):
        """Test fulfill_request method with minimal parameters."""
        request_id = 'test_request_789'
        response_code = 200
        
        await tab.fulfill_request(request_id, response_code)
        
        # Verify the command was executed with correct parameters
        assert_mock_called_at_least_once(tab._connection_handler)
        
        # Get the call arguments to verify the command
        call_args = tab._connection_handler.execute_command.call_args_list[-1]
        command = call_args[0][0]  # First argument is the command
        
        # Verify it's a FetchCommands.fulfill_request command
        assert command['method'] == 'Fetch.fulfillRequest'
        assert command['params']['requestId'] == request_id
        assert command['params']['responseCode'] == response_code
        # Verify optional parameters are None/not set
        params = command['params']
        assert params.get('responseHeaders') is None
        assert params.get('body') is None
        assert params.get('responsePhrase') is None

    @pytest.mark.asyncio
    async def test_continue_request_with_all_params(self, tab):
        """Test continue_request with all parameters."""
        from pydoll.protocol.network.types import RequestMethod
        
        request_id = 'test_request_456'
        url = 'https://modified-example.com'
        method = RequestMethod.POST
        post_data = 'modified_data=test'
        headers = [{'name': 'Authorization', 'value': 'Bearer token123'}]
        intercept_response = True
        
        await tab.continue_request(
            request_id=request_id,
            url=url,
            method=method,
            post_data=post_data,
            headers=headers,
            intercept_response=intercept_response,
        )
        
        # Verify the command was executed with correct parameters
        assert_mock_called_at_least_once(tab._connection_handler)
        
        # Get the call arguments to verify the command
        call_args = tab._connection_handler.execute_command.call_args_list[-1]
        command = call_args[0][0]  # First argument is the command
        
        # Verify all parameters
        params = command['params']
        assert params['requestId'] == request_id
        assert params['url'] == url
        assert params['method'] == method
        assert params['postData'] == post_data
        assert params['headers'] == headers
        assert params['interceptResponse'] == intercept_response

    @pytest.mark.asyncio
    async def test_continue_request_with_different_id(self, tab):
        """Test continue_request with different request ID."""
        request_id = 'another_request_id_xyz'
        
        await tab.continue_request(request_id)
        
        assert_mock_called_at_least_once(tab._connection_handler)
        
        # Verify the request ID was passed correctly
        call_args = tab._connection_handler.execute_command.call_args_list[-1]
        command = call_args[0][0]
        assert command['params']['requestId'] == request_id

    @pytest.mark.asyncio
    async def test_fail_request_with_different_error(self, tab):
        """Test fail_request with different error reason."""
        from pydoll.protocol.network.types import ErrorReason
        
        request_id = 'test_request_error'
        error_reason = ErrorReason.ABORTED
        
        await tab.fail_request(request_id, error_reason)
        
        assert_mock_called_at_least_once(tab._connection_handler)
        
        # Verify the error reason was passed correctly
        call_args = tab._connection_handler.execute_command.call_args_list[-1]
        command = call_args[0][0]
        assert command['params']['errorReason'] == error_reason

    @pytest.mark.asyncio
    async def test_fulfill_request_with_all_params(self, tab):
        """Test fulfill_request with all parameters."""
        request_id = 'test_request_complete'
        response_code = 200
        response_headers = [{'name': 'Content-Type', 'value': 'application/json'}]
        json_response = '{"status": "success", "data": "test"}'
        body = base64.b64encode(json_response.encode('utf-8')).decode('utf-8')
        response_phrase = 'OK'
        
        await tab.fulfill_request(
            request_id=request_id,
            response_code=response_code,
            response_headers=response_headers,
            body=body,
            response_phrase=response_phrase,
        )
        
        # Verify the command was executed with correct parameters
        assert_mock_called_at_least_once(tab._connection_handler)
        
        # Get the call arguments to verify the command
        call_args = tab._connection_handler.execute_command.call_args_list[-1]
        command = call_args[0][0]  # First argument is the command
        
        # Verify all parameters
        params = command['params']
        assert params['requestId'] == request_id
        assert params['responseCode'] == response_code
        assert params['responseHeaders'] == response_headers
        assert params['body'] == body
        assert params['responsePhrase'] == response_phrase

    @pytest.mark.asyncio
    async def test_fulfill_request_with_different_status_code(self, tab):
        """Test fulfill_request with different status code."""
        request_id = 'test_request_404'
        response_code = 404
        response_headers = [{'name': 'Content-Type', 'value': 'text/html'}]
        html_response = '<html><body><h1>404 - Not Found</h1></body></html>'
        response_body = base64.b64encode(html_response.encode('utf-8')).decode('utf-8')
        
        await tab.fulfill_request(
            request_id, response_code, response_headers, response_body
        )
        
        assert_mock_called_at_least_once(tab._connection_handler)
        
        # Verify all parameters were passed correctly
        call_args = tab._connection_handler.execute_command.call_args_list[-1]
        command = call_args[0][0]
        assert command['params']['responseCode'] == response_code
        assert command['params']['responseHeaders'] == response_headers
        assert command['params']['body'] == response_body

    @pytest.mark.asyncio
    async def test_fulfill_request_empty_headers(self, tab):
        """Test fulfill_request with empty headers."""
        request_id = 'test_request_empty_headers'
        response_code = 200
        response_headers = []
        json_response = '{"message": "success"}'
        response_body = base64.b64encode(json_response.encode('utf-8')).decode('utf-8')
        
        await tab.fulfill_request(
            request_id, response_code, response_headers, response_body
        )
        
        assert_mock_called_at_least_once(tab._connection_handler)
        
        # Verify empty headers are handled correctly
        call_args = tab._connection_handler.execute_command.call_args_list[-1]
        command = call_args[0][0]
        assert command['params']['responseHeaders'] == []
        assert command['params']['body'] == response_body


class TestTabEdgeCases:
    """Test Tab edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_take_screenshot_invalid_extension(self, tab):
        """Test take_screenshot with invalid file extension."""
        with pytest.raises(InvalidFileExtension):
            await tab.take_screenshot('screenshot.txt')

    @pytest.mark.asyncio
    async def test_print_to_pdf_with_invalid_path(self, tab):
        """Test print_to_pdf with invalid path handling."""
        # Mock the response
        tab._connection_handler.execute_command.return_value = {
            'result': {'data': 'JVBERi0xLjQKJdPr6eEKMSAwIG9iago8PAovVHlwZSAvQ2F0YWxvZwo+PgplbmRvYmoKdHJhaWxlcgo8PAovUm9vdCAxIDAgUgo+PgpzdGFydHhyZWYKMTgKJSVFT0Y='}
        }
        
        # Should not raise exception - print_to_pdf doesn't validate extensions
        result = await tab.print_to_pdf('document.txt', as_base64=True)
        
        assert result is not None
        assert_mock_called_at_least_once(tab._connection_handler)

    @pytest.mark.asyncio
    async def test_execute_script_with_none_element(self, tab):
        """Test execute_script with None element."""
        tab._connection_handler.execute_command.return_value = {
            'result': {'result': {'value': 'Test Result'}}
        }
        
        result = await tab.execute_script('return "Test Result"', None)
        
        assert_mock_called_at_least_once(tab._connection_handler)

    @pytest.mark.asyncio
    async def test_network_logs_property(self, tab):
        """Test network_logs property access."""
        test_logs = [{'request': {'url': 'https://example.com'}}]
        tab._connection_handler.network_logs = test_logs
        
        logs = tab._connection_handler.network_logs
        assert logs == test_logs

    @pytest.mark.asyncio
    async def test_dialog_property(self, tab):
        """Test dialog property access."""
        test_dialog = {'type': 'alert', 'message': 'Test message'}
        tab._connection_handler.dialog = test_dialog
        
        dialog = tab._connection_handler.dialog
        assert dialog == test_dialog


class TestTabNetworkMethods:
    """Test Tab network-related methods."""

    @pytest.mark.asyncio
    async def test_get_network_response_body_success(self, tab):
        """Test get_network_response_body with network events enabled."""
        # Enable network events
        tab._network_events_enabled = True
        
        # Mock the response
        expected_body = '<html><body>Response content</body></html>'
        tab._connection_handler.execute_command.return_value = {
            'result': {'body': expected_body}
        }
        
        result = await tab.get_network_response_body('test_request_123')
        
        assert result == expected_body
        assert_mock_called_at_least_once(tab._connection_handler)

    @pytest.mark.asyncio
    async def test_get_network_response_body_events_not_enabled(self, tab):
        """Test get_network_response_body when network events are not enabled."""
        # Ensure network events are disabled
        tab._network_events_enabled = False
        
        with pytest.raises(NetworkEventsNotEnabled) as exc_info:
            await tab.get_network_response_body('test_request_123')
        
        assert str(exc_info.value) == 'Network events must be enabled to get response body'
        tab._connection_handler.execute_command.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_network_logs_success_no_filter(self, tab):
        """Test get_network_logs without filter."""
        # Enable network events
        tab._network_events_enabled = True
        
        # Mock network logs
        test_logs = [
            {
                'method': 'Network.requestWillBeSent',
                'params': {
                    'request': {'url': 'https://example.com/api/data'},
                    'requestId': 'req_1'
                }
            },
            {
                'method': 'Network.responseReceived',
                'params': {
                    'request': {'url': 'https://example.com/static/style.css'},
                    'requestId': 'req_2'
                }
            }
        ]
        tab._connection_handler.network_logs = test_logs
        
        result = await tab.get_network_logs()
        
        assert result == test_logs
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_network_logs_success_with_filter(self, tab):
        """Test get_network_logs with URL filter."""
        # Enable network events
        tab._network_events_enabled = True
        
        # Mock network logs
        test_logs = [
            {
                'method': 'Network.requestWillBeSent',
                'params': {
                    'request': {'url': 'https://example.com/api/data'},
                    'requestId': 'req_1'
                }
            },
            {
                'method': 'Network.responseReceived',
                'params': {
                    'request': {'url': 'https://example.com/static/style.css'},
                    'requestId': 'req_2'
                }
            },
            {
                'method': 'Network.requestWillBeSent',
                'params': {
                    'request': {'url': 'https://api.example.com/users'},
                    'requestId': 'req_3'
                }
            }
        ]
        tab._connection_handler.network_logs = test_logs
        
        result = await tab.get_network_logs(filter='api')
        
        # Should return only logs with 'api' in the URL
        assert len(result) == 2
        assert result[0]['params']['request']['url'] == 'https://example.com/api/data'
        assert result[1]['params']['request']['url'] == 'https://api.example.com/users'

    @pytest.mark.asyncio
    async def test_get_network_logs_empty_filter_result(self, tab):
        """Test get_network_logs with filter that matches no logs."""
        # Enable network events
        tab._network_events_enabled = True
        
        # Mock network logs
        test_logs = [
            {
                'method': 'Network.requestWillBeSent',
                'params': {
                    'request': {'url': 'https://example.com/static/style.css'},
                    'requestId': 'req_1'
                }
            }
        ]
        tab._connection_handler.network_logs = test_logs
        
        result = await tab.get_network_logs(filter='nonexistent')
        
        assert result == []

    @pytest.mark.asyncio
    async def test_get_network_logs_events_not_enabled(self, tab):
        """Test get_network_logs when network events are not enabled."""
        # Ensure network events are disabled
        tab._network_events_enabled = False
        
        with pytest.raises(NetworkEventsNotEnabled) as exc_info:
            await tab.get_network_logs()
        
        assert str(exc_info.value) == 'Network events must be enabled to get network logs'

    @pytest.mark.asyncio
    async def test_get_network_logs_missing_request_params(self, tab):
        """Test get_network_logs with logs missing request parameters."""
        # Enable network events
        tab._network_events_enabled = True
        
        # Mock network logs with missing request data
        test_logs = [
            {
                'method': 'Network.requestWillBeSent',
                'params': {
                    'requestId': 'req_1'
                    # Missing 'request' key
                }
            },
            {
                'method': 'Network.responseReceived',
                'params': {
                    'request': {},  # Empty request object
                    'requestId': 'req_2'
                }
            }
        ]
        tab._connection_handler.network_logs = test_logs
        
        result = await tab.get_network_logs(filter='example')
        
        # Should handle missing request data gracefully
        assert result == []