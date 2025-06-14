import asyncio
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch, ANY, PropertyMock
from pathlib import Path

from pydoll.constants import By, RequestStage, ResourceType, ScreenshotFormat
from pydoll.browser.tab import Tab
from pydoll.elements.web_element import WebElement
from pydoll.exceptions import (
    NoDialogPresent,
    PageLoadTimeout,
    IFrameNotFound,
    InvalidIFrame,
    NotAnIFrame,
    InvalidFileExtension,
    WaitElementTimeout,
    NetworkEventsNotEnabled,
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
    return browser


@pytest_asyncio.fixture
async def tab(mock_browser, mock_connection_handler):
    """Tab fixture with mocked dependencies."""
    with patch('pydoll.browser.tab.ConnectionHandler', return_value=mock_connection_handler):
        tab = Tab(
            browser=mock_browser,
            connection_port=9222,
            target_id='test-target-id',
            browser_context_id='test-context-id'
        )
        return tab


class TestTabInitialization:
    """Test Tab initialization and basic properties."""

    def test_tab_initialization(self, tab, mock_browser):
        """Test basic Tab initialization."""
        assert tab._browser == mock_browser
        assert tab._connection_port == 9222
        assert tab._target_id == 'test-target-id'
        assert tab._browser_context_id == 'test-context-id'
        assert not tab.page_events_enabled
        assert not tab.network_events_enabled
        assert not tab.fetch_events_enabled
        assert not tab.dom_events_enabled
        assert not tab.runtime_events_enabled
        assert not tab.intercept_file_chooser_dialog_enabled

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
        tab._connection_handler.execute_command.assert_called_once()

    @pytest.mark.asyncio
    async def test_page_source(self, tab):
        """Test page_source property."""
        expected_html = '<html><body>Test Content</body></html>'
        tab._connection_handler.execute_command.return_value = {
            'result': {'result': {'value': expected_html}}
        }

        source = await tab.page_source
        assert source == expected_html
        tab._connection_handler.execute_command.assert_called_once()


class TestTabEventManagement:
    """Test Tab event enabling/disabling methods."""

    @pytest.mark.asyncio
    async def test_enable_page_events(self, tab):
        """Test enabling page events."""
        await tab.enable_page_events()
        assert tab.page_events_enabled is True
        tab._connection_handler.execute_command.assert_called_once()

    @pytest.mark.asyncio
    async def test_enable_network_events(self, tab):
        """Test enabling network events."""
        await tab.enable_network_events()
        assert tab.network_events_enabled is True
        tab._connection_handler.execute_command.assert_called_once()

    @pytest.mark.asyncio
    async def test_enable_fetch_events(self, tab):
        """Test enabling fetch events with default parameters."""
        await tab.enable_fetch_events()
        assert tab.fetch_events_enabled is True
        tab._connection_handler.execute_command.assert_called_once()

    @pytest.mark.asyncio
    async def test_enable_fetch_events_with_params(self, tab):
        """Test enabling fetch events with custom parameters."""
        await tab.enable_fetch_events(
            handle_auth=True,
            resource_type=ResourceType.DOCUMENT,
            request_stage=RequestStage.REQUEST
        )
        assert tab.fetch_events_enabled is True
        tab._connection_handler.execute_command.assert_called_once()

    @pytest.mark.asyncio
    async def test_enable_dom_events(self, tab):
        """Test enabling DOM events."""
        await tab.enable_dom_events()
        assert tab.dom_events_enabled is True
        tab._connection_handler.execute_command.assert_called_once()

    @pytest.mark.asyncio
    async def test_enable_runtime_events(self, tab):
        """Test enabling runtime events."""
        await tab.enable_runtime_events()
        assert tab.runtime_events_enabled is True
        tab._connection_handler.execute_command.assert_called_once()

    @pytest.mark.asyncio
    async def test_enable_intercept_file_chooser_dialog(self, tab):
        """Test enabling file chooser dialog interception."""
        await tab.enable_intercept_file_chooser_dialog()
        assert tab.intercept_file_chooser_dialog_enabled is True
        tab._connection_handler.execute_command.assert_called_once()

    @pytest.mark.asyncio
    async def test_disable_fetch_events(self, tab):
        """Test disabling fetch events."""
        tab._fetch_events_enabled = True
        await tab.disable_fetch_events()
        assert tab.fetch_events_enabled is False
        tab._connection_handler.execute_command.assert_called_once()

    @pytest.mark.asyncio
    async def test_disable_page_events(self, tab):
        """Test disabling page events."""
        tab._page_events_enabled = True
        await tab.disable_page_events()
        assert tab.page_events_enabled is False
        tab._connection_handler.execute_command.assert_called_once()

    @pytest.mark.asyncio
    async def test_disable_network_events(self, tab):
        """Test disabling network events."""
        tab._network_events_enabled = True
        await tab.disable_network_events()
        assert tab.network_events_enabled is False
        tab._connection_handler.execute_command.assert_called_once()

    @pytest.mark.asyncio
    async def test_disable_dom_events(self, tab):
        """Test disabling DOM events."""
        tab._dom_events_enabled = True
        await tab.disable_dom_events()
        assert tab.dom_events_enabled is False
        tab._connection_handler.execute_command.assert_called_once()

    @pytest.mark.asyncio
    async def test_disable_runtime_events(self, tab):
        """Test disabling runtime events."""
        tab._runtime_events_enabled = True
        await tab.disable_runtime_events()
        assert tab.runtime_events_enabled is False
        tab._connection_handler.execute_command.assert_called_once()

    @pytest.mark.asyncio
    async def test_disable_intercept_file_chooser_dialog(self, tab):
        """Test disabling file chooser dialog interception."""
        tab._intercept_file_chooser_dialog_enabled = True
        await tab.disable_intercept_file_chooser_dialog()
        assert tab.intercept_file_chooser_dialog_enabled is False
        tab._connection_handler.execute_command.assert_called_once()


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
        tab._connection_handler.execute_command.assert_called_once()

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
        tab._connection_handler.execute_command.assert_called_once()

    @pytest.mark.asyncio
    async def test_take_screenshot_as_base64(self, tab):
        """Test taking screenshot and returning as base64."""
        screenshot_data = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/wcAAgAB/edzE+oAAAAASUVORK5CYII='
        tab._connection_handler.execute_command.return_value = {
            'result': {'data': screenshot_data}
        }
        
        result = await tab.take_screenshot('screenshot.png', as_base64=True)
        
        assert result == screenshot_data
        tab._connection_handler.execute_command.assert_called_once()

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
        tab._connection_handler.execute_command.assert_called_once()

    @pytest.mark.asyncio
    async def test_print_to_pdf_as_base64(self, tab):
        """Test printing to PDF and returning as base64."""
        pdf_data = 'JVBERi0xLjQKJdPr6eEKMSAwIG9iago8PAovVHlwZSAvQ2F0YWxvZwo+PgplbmRvYmoKdHJhaWxlcgo8PAovUm9vdCAxIDAgUgo+PgpzdGFydHhyZWYKMTgKJSVFT0Y='
        tab._connection_handler.execute_command.return_value = {
            'result': {'data': pdf_data}
        }
        
        result = await tab.print_to_pdf('', as_base64=True)
        
        assert result == pdf_data
        tab._connection_handler.execute_command.assert_called_once()

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
        tab._connection_handler.execute_command.assert_called_once()


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
        
        tab._connection_handler.execute_command.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_dialog_dismiss(self, tab):
        """Test dismissing a dialog."""
        tab._connection_handler.dialog = {'params': {'type': 'confirm'}}
        
        await tab.handle_dialog(accept=False)
        
        tab._connection_handler.execute_command.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_dialog_with_prompt_text(self, tab):
        """Test handling a prompt dialog with text."""
        tab._connection_handler.dialog = {'params': {'type': 'prompt'}}
        
        await tab.handle_dialog(accept=True, prompt_text='Test input')
        
        tab._connection_handler.execute_command.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_dialog_no_dialog(self, tab):
        """Test handling dialog when none is present."""
        tab._connection_handler.dialog = None
        
        with pytest.raises(NoDialogPresent):
            await tab.handle_dialog(accept=True)


class TestTabScriptExecution:
    """Test Tab JavaScript execution methods."""

    @pytest.mark.asyncio
    async def test_execute_script_simple(self, tab):
        """Test executing simple JavaScript."""
        tab._connection_handler.execute_command.return_value = {
            'result': {'result': {'value': 'Test Result'}}
        }
        
        result = await tab.execute_script('return "Test Result"')
        
        tab._connection_handler.execute_command.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_script_with_element(self, tab):
        """Test executing JavaScript with element context."""
        mock_element = WebElement(
            object_id='test-element-id',
            connection_handler=tab._connection_handler
        )
        
        tab._connection_handler.execute_command.return_value = {
            'result': {'result': {'value': 'Element clicked'}}
        }
        
        result = await tab.execute_script('this.click()', mock_element)
        
        tab._connection_handler.execute_command.assert_called_once()


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
        tab._connection_handler.register_callback.assert_called_once()

    @pytest.mark.asyncio
    async def test_on_temporary_callback(self, tab):
        """Test registering temporary event callbacks."""
        callback_id = 456
        tab._connection_handler.register_callback.return_value = callback_id
        
        async def test_callback(event):
            pass
        
        result = await tab.on('Page.loadEventFired', test_callback, temporary=True)
        
        assert result == callback_id
        tab._connection_handler.register_callback.assert_called_once_with(
            'Page.loadEventFired', ANY, True
        )


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
        tab._connection_handler.register_callback.assert_called_once()
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
        tab._connection_handler.register_callback.assert_called_once()
        assert tab._cloudflare_captcha_callback_id == callback_id

    @pytest.mark.asyncio
    async def test_disable_auto_solve_cloudflare_captcha(self, tab):
        """Test disabling auto-solve Cloudflare captcha."""
        tab._cloudflare_captcha_callback_id = 777
        tab._connection_handler.remove_callback.return_value = True
        
        await tab.disable_auto_solve_cloudflare_captcha()
        
        tab._connection_handler.remove_callback.assert_called_once_with(777)

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
        tab._connection_handler.register_callback.assert_called_once()
        tab._connection_handler.remove_callback.assert_called_once_with(callback_id)

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
        
        mock_find.assert_called_once_with(
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
        
        tab._connection_handler.execute_command.assert_called_once()

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
        tab._connection_handler.execute_command.assert_called_once()


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
        tab._connection_handler.execute_command.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_script_with_none_element(self, tab):
        """Test execute_script with None element."""
        tab._connection_handler.execute_command.return_value = {
            'result': {'result': {'value': 'Test Result'}}
        }
        
        result = await tab.execute_script('return "Test Result"', None)
        
        tab._connection_handler.execute_command.assert_called_once()

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
        tab._connection_handler.execute_command.assert_called_once()

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