from unittest.mock import ANY, AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from pydoll import exceptions
from pydoll.browser.chromium.chrome import Chrome
from pydoll.browser.chromium.base import Browser
from pydoll.browser.managers import ProxyManager, BrowserOptionsManager
from pydoll.browser.options import Options
from pydoll.browser.page import Page
from pydoll.protocol.commands import (
    BrowserCommands,
    DomCommands,
    FetchCommands,
    NetworkCommands,
    StorageCommands,
    TargetCommands,
)
from pydoll.protocol.events import FetchEvents, PageEvents


class ConcreteBrowser(Browser):
    def _get_default_binary_location(self) -> str:
        return '/fake/path/to/browser'


@pytest_asyncio.fixture
async def mock_browser():
    with (
        patch.multiple(
            Browser,
            _get_default_binary_location=MagicMock(
                return_value='/fake/path/to/browser'
            ),
        ),
        patch(
            'pydoll.browser.managers.BrowserProcessManager',
            autospec=True,
        ) as mock_process_manager,
        patch(
            'pydoll.browser.managers.TempDirectoryManager',
            autospec=True,
        ) as mock_temp_dir_manager,
        patch(
            'pydoll.connection.ConnectionHandler',
            autospec=True,
        ) as mock_conn_handler,
        patch(
            'pydoll.browser.managers.ProxyManager',
            autospec=True,
        ) as mock_proxy_manager,
    ):
        options = Options()
        options.binary_location = None

        browser = ConcreteBrowser(options=options)
        browser._browser_process_manager = mock_process_manager.return_value
        browser._temp_directory_manager = mock_temp_dir_manager.return_value
        browser._proxy_manager = mock_proxy_manager.return_value
        browser._connection_handler = mock_conn_handler.return_value
        browser._connection_handler.execute_command = AsyncMock()
        browser._connection_handler.register_callback = AsyncMock()

        mock_temp_dir_manager.return_value.create_temp_dir.return_value = (
            MagicMock(name='temp_dir')
        )
        browser._pages = ['page1']

        yield browser


@pytest.mark.asyncio
async def test_browser_initialization(mock_browser):
    assert isinstance(mock_browser.options, Options)
    assert isinstance(mock_browser._proxy_manager, ProxyManager)
    assert mock_browser._connection_port in range(9223, 9323)
    assert mock_browser._pages == ['page1']


@pytest.mark.asyncio
async def test_start_browser_success(mock_browser):
    mock_browser._connection_handler.ping.return_value = True

    await mock_browser.start()

    mock_browser._browser_process_manager.start_browser_process.assert_called_once_with(
        '/fake/path/to/browser',
        mock_browser._connection_port,
        mock_browser.options.arguments,
    )

    assert '--user-data-dir=' in str(mock_browser.options.arguments), (
        'Diretório temporário não configurado'
    )

    assert 'page1' in mock_browser._pages


@pytest.mark.asyncio
async def test_start_browser_failure(mock_browser):
    mock_browser._connection_handler.ping.return_value = False
    with patch('pydoll.browser.chromium.base.asyncio.sleep', AsyncMock()) as mock_sleep:
        mock_sleep.return_value = False
        with pytest.raises(exceptions.BrowserNotRunning):
            await mock_browser.start()


@pytest.mark.asyncio
async def test_start_headless(mock_browser):
    mock_browser._connection_handler.ping.return_value = True
    await mock_browser.start(headless=True)

    assert "--headless" in mock_browser.options.arguments


@pytest.mark.asyncio
async def test_connect_to_existing_browser(mock_browser):
    """Test connecting to an existing browser instance instead of starting a new one."""
    # Setup mocks for a successful connection
    mock_browser._connection_handler.ping.return_value = True
    
    # Mock the necessary internal methods
    mock_browser._verify_browser_running = AsyncMock()
    mock_browser._init_first_page = AsyncMock()
    
    # Set a test page ID in the _pages list
    mock_browser._pages = ['existing_page_id']
    
    # Call the connect method
    page = await mock_browser.connect()
    
    # Verify that verify_browser_running was called
    mock_browser._verify_browser_running.assert_called_once()
    
    # Verify that init_first_page was called
    mock_browser._init_first_page.assert_called_once()
    
    # Verify that a Page instance was returned with the correct connection port and page ID
    assert isinstance(page, Page)
    assert page._connection_handler._connection_port == mock_browser._connection_port
    assert page._connection_handler._page_id == 'existing_page_id'
    
    # Verify that the page ID was removed from the _pages list
    assert len(mock_browser._pages) == 0
    
    # Verify that start_browser_process was NOT called
    mock_browser._browser_process_manager.start_browser_process.assert_not_called()


@pytest.mark.asyncio
async def test_connect_browser_not_running(mock_browser):
    """Test connect method when browser is not running."""
    # Setup mocks for a browser that is not running
    mock_browser._connection_handler.ping.return_value = False
    mock_browser._init_first_page = AsyncMock()
    
    # Make _verify_browser_running raise an exception
    mock_browser._verify_browser_running = AsyncMock(
        side_effect=exceptions.BrowserNotRunning('Browser is not running')
    )
    
    # Check that connect raises the appropriate exception
    with pytest.raises(exceptions.BrowserNotRunning):
        await mock_browser.connect()
    
    # Verify that _verify_browser_running was called
    mock_browser._verify_browser_running.assert_called_once()
    
    # Verify that _init_first_page was NOT called
    mock_browser._init_first_page.assert_not_called()


@pytest.mark.asyncio
async def test_proxy_configuration(mock_browser):
    mock_browser._proxy_manager.get_proxy_credentials = MagicMock(
        return_value=(True, ('user', 'pass'))
    )

    await mock_browser.start()

    mock_browser._connection_handler.execute_command.assert_any_call(
        FetchCommands.enable_fetch_events(True, '')
    )
    mock_browser._connection_handler.register_callback.assert_any_call(
        FetchEvents.REQUEST_PAUSED, ANY, True
    )
    mock_browser._connection_handler.register_callback.assert_any_call(
        FetchEvents.AUTH_REQUIRED,
        ANY,
        True,
    )


@pytest.mark.asyncio
async def test_get_page_existing(mock_browser):
    page = await mock_browser.get_page()
    assert isinstance(page, Page)
    assert len(mock_browser._pages) == 0


@pytest.mark.asyncio
async def test_get_page_new(mock_browser):
    mock_browser._pages = []
    mock_browser._connection_handler.execute_command.return_value = {
        'result': {'targetId': 'new_page'}
    }

    page = await mock_browser.get_page()
    assert isinstance(page, Page)
    assert len(mock_browser._pages) == 0


@pytest.mark.asyncio
async def test_get_existing_page(mock_browser):
    mock_browser._pages = [Page(1234, 'page1')]
    mock_browser._connection_handler.execute_command.return_value = {
        'result': {'targetId': 'new_page'}
    }

    page = await mock_browser.get_page()
    assert isinstance(page, Page)
    assert len(mock_browser._pages) == 0


@pytest.mark.asyncio
async def test_cookie_management(mock_browser):
    cookies = [{'name': 'test', 'value': '123'}]
    await mock_browser.set_cookies(cookies)
    mock_browser._connection_handler.execute_command.assert_any_await(
        StorageCommands.set_cookies(cookies), timeout=60
    )
    mock_browser._connection_handler.execute_command.assert_any_await(
        NetworkCommands.set_cookies(cookies), timeout=60
    )

    mock_browser._connection_handler.execute_command.return_value = {
        'result': {'cookies': cookies}
    }
    result = await mock_browser.get_cookies()
    assert result == cookies

    await mock_browser.delete_all_cookies()
    mock_browser._connection_handler.execute_command.assert_any_await(
        StorageCommands.clear_cookies(), timeout=60
    )
    mock_browser._connection_handler.execute_command.assert_any_await(
        NetworkCommands.clear_browser_cookies(), timeout=60
    )


@pytest.mark.asyncio
async def test_event_registration(mock_browser):
    callback = MagicMock()
    mock_browser._connection_handler.register_callback.return_value = 123

    callback_id = await mock_browser.on('test_event', callback, temporary=True)
    assert callback_id == 123

    mock_browser._connection_handler.register_callback.assert_called_with(
        'test_event', ANY, True
    )


@pytest.mark.asyncio
async def test_window_management(mock_browser):
    mock_browser._connection_handler.execute_command.return_value = {
        'result': {'windowId': 'window1'}
    }

    bounds = {'width': 800, 'height': 600}
    await mock_browser.set_window_bounds(bounds)
    mock_browser._connection_handler.execute_command.assert_any_await(
        BrowserCommands.set_window_bounds('window1', bounds), timeout=60
    )

    await mock_browser.set_window_maximized()
    mock_browser._connection_handler.execute_command.assert_any_await(
        BrowserCommands.set_window_maximized('window1'), timeout=60
    )

    await mock_browser.set_window_minimized()
    mock_browser._connection_handler.execute_command.assert_any_await(
        BrowserCommands.set_window_minimized('window1'), timeout=60
    )


@pytest.mark.asyncio
async def test_stop_browser(mock_browser):
    await mock_browser.stop()
    mock_browser._connection_handler.execute_command.assert_any_await(
        BrowserCommands.CLOSE, timeout=60
    )
    mock_browser._browser_process_manager.stop_process.assert_called_once()
    mock_browser._temp_directory_manager.cleanup.assert_called_once()


@pytest.mark.asyncio
async def test_stop_browser_not_running(mock_browser):
    mock_browser._connection_handler.ping.return_value = False
    with patch('pydoll.browser.chromium.base.asyncio.sleep', AsyncMock()) as mock_sleep:
        mock_sleep.return_value = False
        with pytest.raises(exceptions.BrowserNotRunning):
            await mock_browser.stop()


@pytest.mark.asyncio
async def test_context_manager(mock_browser):
    async with mock_browser as browser:
        assert browser == mock_browser

    mock_browser._temp_directory_manager.cleanup.assert_called_once()
    mock_browser._browser_process_manager.stop_process.assert_called_once()


@pytest.mark.asyncio
async def test_enable_events(mock_browser):
    await mock_browser.enable_fetch_events(
        handle_auth_requests=True, resource_type='XHR'
    )
    mock_browser._connection_handler.execute_command.assert_called_with(
        FetchCommands.enable_fetch_events(True, 'XHR')
    )


@pytest.mark.asyncio
async def test_disable_events(mock_browser):
    await mock_browser.disable_fetch_events()
    mock_browser._connection_handler.execute_command.assert_called_with(
        FetchCommands.disable_fetch_events()
    )


@pytest.mark.asyncio
async def test__continue_request(mock_browser):
    await mock_browser._continue_request({'params': {'requestId': 'request1'}})
    mock_browser._connection_handler.execute_command.assert_called_with(
        FetchCommands.continue_request('request1'), timeout=60
    )


@pytest.mark.asyncio
async def test__continue_request_auth_required(mock_browser):
    await mock_browser._continue_request_auth_required(
        event={'params': {'requestId': 'request1'}},
        proxy_username='user',
        proxy_password='pass',
    )

    mock_browser._connection_handler.execute_command.assert_any_call(
        FetchCommands.continue_request_with_auth('request1', 'user', 'pass'),
        timeout=60,
    )

    mock_browser._connection_handler.execute_command.assert_any_call(
        FetchCommands.disable_fetch_events()
    )


def test__is_valid_page(mock_browser):
    result = mock_browser._is_valid_page({
        'type': 'page',
        'url': 'chrome://newtab/',
    })
    assert result is True


def test__is_valid_page_not_a_page(mock_browser):
    result = mock_browser._is_valid_page({
        'type': 'tab',
        'url': 'chrome://newtab/',
    })
    assert result is False


@pytest.mark.asyncio
async def test__get_valid_page(mock_browser):
    pages = [
        {
            'type': 'page',
            'url': 'chrome://newtab/',
            'targetId': 'valid_page_id',
        },
        {
            'type': 'page',
            'url': 'https://example.com/',
            'targetId': 'invalid_page_id',
        },
        {
            'type': 'tab',
            'url': 'chrome://newtab/',
            'targetId': 'invalid_page_id',
        },
    ]

    result = await mock_browser._get_valid_page(pages)
    assert result == 'valid_page_id'


@pytest.mark.asyncio
async def test__get_valid_page_key_error(mock_browser):
    pages = [
        {'type': 'page', 'url': 'chrome://newtab/'},
        {'type': 'page', 'url': 'https://example.com/'},
        {'type': 'tab', 'url': 'chrome://newtab/'},
    ]

    mock_browser._connection_handler.execute_command.return_value = {
        'result': {'targetId': 'new_page'}
    }
    result = await mock_browser._get_valid_page(pages)
    assert result == 'new_page'
    mock_browser._connection_handler.execute_command.assert_called_with(
        TargetCommands.create_target(''), timeout=60
    )


@pytest.mark.parametrize(
    'os_name, expected_browser_paths, mock_return_value',
    [
        (
            'Windows',
            [
                r'C:\Program Files\Google\Chrome\Application\chrome.exe',
                r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
            ],
            r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        ),
        ('Linux', ['/usr/bin/google-chrome'], '/usr/bin/google-chrome'),
        (
            'Darwin',
            ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'],
            '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        ),
    ],
)
@patch('platform.system')
@patch.object(BrowserOptionsManager, 'validate_browser_paths')
def test__get_default_binary_location(
    mock_validate_browser_paths,
    mock_platform_system,
    os_name,
    expected_browser_paths,
    mock_return_value,
):
    mock_platform_system.return_value = os_name
    mock_validate_browser_paths.return_value = mock_return_value
    path = Chrome._get_default_binary_location()
    mock_validate_browser_paths.assert_called_once_with(expected_browser_paths)

    assert path == mock_return_value


def test__get_default_binary_location_unsupported_os():
    with patch('platform.system', return_value='SomethingElse'):
        with pytest.raises(ValueError, match='Unsupported OS'):
            Chrome._get_default_binary_location()


@patch('platform.system')
def test__get_default_binary_location_throws_exception_if_os_not_supported(
    mock_platform_system,
):
    mock_platform_system.return_value = 'FreeBSD'

    with pytest.raises(ValueError, match='Unsupported OS'):
        Chrome._get_default_binary_location()


@pytest.mark.asyncio
async def test_register_event_callback_page_event():
    mock_conn_handler = AsyncMock()
    browser = ConcreteBrowser()
    browser._connection_handler = mock_conn_handler

    with pytest.raises(exceptions.EventNotSupported) as excinfo:
        await browser.on(PageEvents.PAGE_LOADED, AsyncMock())
    assert 'Page events are not supported in the browser domain' in str(
        excinfo.value
    )

    with pytest.raises(exceptions.EventNotSupported) as excinfo:
        await browser.on(PageEvents.DOM_CONTENT_LOADED, AsyncMock())
    assert 'Page events are not supported in the browser domain' in str(
        excinfo.value
    )

    for event in PageEvents.ALL_EVENTS:
        with pytest.raises(exceptions.EventNotSupported):
            await browser.on(event, AsyncMock())

