from unittest.mock import ANY, AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from pydoll import exceptions
from pydoll.browser.chromium.chrome import Chrome
from pydoll.browser.chromium.base import Browser
from pydoll.browser.managers import ProxyManager, ChromiumOptionsManager, BrowserProcessManager, TempDirectoryManager
from pydoll.browser.options import ChromiumOptions as Options
from pydoll.browser.tab import Tab
from pydoll.commands import (
    BrowserCommands,
    FetchCommands,
    RuntimeCommands,
    StorageCommands,
    TargetCommands,
)
from pydoll.protocol.fetch.events import FetchEvent
from pydoll.connection.connection_handler import ConnectionHandler
from pydoll.constants import DownloadBehavior, PermissionType, NetworkErrorReason


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
            'pydoll.browser.managers.browser_process_manager.BrowserProcessManager',
            autospec=True,
        ) as mock_process_manager,
        patch(
            'pydoll.browser.managers.temp_dir_manager.TempDirectoryManager',
            autospec=True,
        ) as mock_temp_dir_manager,
        patch(
            'pydoll.connection.connection_handler.ConnectionHandler',
            autospec=True,
        ) as mock_conn_handler,
        patch(
            'pydoll.browser.managers.proxy_manager.ProxyManager',
            autospec=True,
        ) as mock_proxy_manager,
    ):
        options = Options()
        options.binary_location = None

        options_manager = ChromiumOptionsManager(options)
        browser = ConcreteBrowser(options_manager)
        browser._browser_process_manager = mock_process_manager.return_value
        browser._temp_directory_manager = mock_temp_dir_manager.return_value
        browser._proxy_manager = mock_proxy_manager.return_value
        browser._connection_handler = mock_conn_handler.return_value
        browser._connection_handler.execute_command = AsyncMock()
        browser._connection_handler.register_callback = AsyncMock()

        mock_temp_dir_manager.return_value.create_temp_dir.return_value = (
            MagicMock(name='temp_dir')
        )

        yield browser


@pytest.mark.asyncio
async def test_browser_initialization(mock_browser):
    assert isinstance(mock_browser.options, Options)
    assert isinstance(mock_browser._proxy_manager, ProxyManager)
    assert isinstance(mock_browser._browser_process_manager, BrowserProcessManager)
    assert isinstance(mock_browser._temp_directory_manager, TempDirectoryManager)
    assert isinstance(mock_browser._connection_handler, ConnectionHandler)
    assert mock_browser._connection_port in range(9223, 9323)


@pytest.mark.asyncio
async def test_start_browser_success(mock_browser):
    mock_browser._connection_handler.ping.return_value = True
    mock_browser._get_valid_tab_id = AsyncMock(return_value='page1')

    tab = await mock_browser.start()
    assert isinstance(tab, Tab)

    mock_browser._browser_process_manager.start_browser_process.assert_called_once_with(
        '/fake/path/to/browser',
        mock_browser._connection_port,
        mock_browser.options.arguments,
    )

    assert '--user-data-dir=' in str(mock_browser.options.arguments), (
        'Temporary directory not configured'
    )



@pytest.mark.asyncio
async def test_start_browser_failure(mock_browser):
    mock_browser._connection_handler.ping.return_value = False
    with patch('pydoll.browser.chromium.base.asyncio.sleep', AsyncMock()) as mock_sleep:
        mock_sleep.return_value = False
        with pytest.raises(exceptions.FailedToStartBrowser):
            await mock_browser.start()

@pytest.mark.asyncio
async def test_proxy_configuration(mock_browser):
    mock_browser._proxy_manager.get_proxy_credentials = MagicMock(
        return_value=(True, ('user', 'pass'))
    )
    mock_browser._get_valid_tab_id = AsyncMock(return_value='page1')
    await mock_browser.start()

    mock_browser._connection_handler.execute_command.assert_any_call(
        FetchCommands.enable(handle_auth_requests=True, resource_type=None)
    )
    mock_browser._connection_handler.register_callback.assert_any_call(
        FetchEvent.REQUEST_PAUSED, ANY, True
    )
    mock_browser._connection_handler.register_callback.assert_any_call(
        FetchEvent.AUTH_REQUIRED,
        ANY,
        True,
    )

@pytest.mark.asyncio
async def test_new_tab(mock_browser):
    mock_browser._connection_handler.execute_command.return_value = {
        'result': {'targetId': 'new_page'}
    }
    tab = await mock_browser.new_tab()
    assert tab._target_id == 'new_page'
    assert isinstance(tab, Tab)


@pytest.mark.asyncio
async def test_cookie_management(mock_browser):
    cookies = [{'name': 'test', 'value': '123'}]
    await mock_browser.set_cookies(cookies)
    mock_browser._connection_handler.execute_command.assert_any_call(
        StorageCommands.set_cookies(cookies=cookies, browser_context_id=None), timeout=10
    )

    mock_browser._connection_handler.execute_command.return_value = {
        'result': {'cookies': cookies}
    }
    result = await mock_browser.get_cookies()
    assert result == cookies

    await mock_browser.delete_all_cookies()
    mock_browser._connection_handler.execute_command.assert_any_await(
        StorageCommands.clear_cookies(), timeout=10
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
    mock_browser.get_window_id = AsyncMock(return_value='window1')

    bounds = {'width': 800, 'height': 600}
    await mock_browser.set_window_bounds(bounds)
    mock_browser._connection_handler.execute_command.assert_any_await(
        BrowserCommands.set_window_bounds('window1', bounds), timeout=10
    )

    await mock_browser.set_window_maximized()
    mock_browser._connection_handler.execute_command.assert_any_await(
        BrowserCommands.set_window_maximized('window1'), timeout=10
    )

    await mock_browser.set_window_minimized()
    mock_browser._connection_handler.execute_command.assert_any_await(
        BrowserCommands.set_window_minimized('window1'), timeout=10
    )

@pytest.mark.asyncio
async def test_get_window_id_for_target(mock_browser):
    mock_browser._connection_handler.ping.return_value = True
    mock_browser._get_valid_tab_id = AsyncMock(return_value='page1')

    tab = await mock_browser.start()
    mock_browser._connection_handler.execute_command.return_value = {
        'result': {'windowId': 'page1'}
    }
    window_id = await mock_browser.get_window_id_for_tab(tab)
    assert window_id == 'page1'
    mock_browser._connection_handler.execute_command.assert_called_with(
        BrowserCommands.get_window_for_target('page1'), timeout=10
    )


@pytest.mark.asyncio
async def test_get_window_id(mock_browser):
    mock_browser.get_targets = AsyncMock(return_value=[{'targetId': 'target1', 'type': 'page'}])
    mock_browser._connection_handler.execute_command.return_value = {
        'result': {'windowId': 'window1'}
    }
    window_id = await mock_browser.get_window_id()
    assert window_id == 'window1'
    mock_browser._connection_handler.execute_command.assert_called_with(
        BrowserCommands.get_window_for_target('target1'), timeout=10
    )

@pytest.mark.asyncio
async def test_stop_browser(mock_browser):
    await mock_browser.stop()
    mock_browser._connection_handler.execute_command.assert_any_await(
        BrowserCommands.close(), timeout=10
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
        FetchCommands.enable(handle_auth_requests=True, resource_type='XHR')
    )


@pytest.mark.asyncio
async def test_disable_events(mock_browser):
    await mock_browser.disable_fetch_events()
    mock_browser._connection_handler.execute_command.assert_called_with(
        FetchCommands.disable()
    )


@pytest.mark.asyncio
async def test__continue_request_callback(mock_browser):
    await mock_browser._continue_request_callback({'params': {'requestId': 'request1'}})
    mock_browser._connection_handler.execute_command.assert_called_with(
        FetchCommands.continue_request('request1'), timeout=10
    )


@pytest.mark.asyncio
async def test__continue_request_auth_required_callback(mock_browser):
    await mock_browser._continue_request_with_auth_callback(
        event={'params': {'requestId': 'request1'}},
        proxy_username='user',
        proxy_password='pass',
    )

    mock_browser._connection_handler.execute_command.assert_any_call(
        FetchCommands.continue_request_with_auth('request1', 'ProvideCredentials', 'user', 'pass'),
        timeout=10,
    )

    mock_browser._connection_handler.execute_command.assert_any_call(
        FetchCommands.disable()
    )


def test__is_valid_tab(mock_browser):
    result = mock_browser._is_valid_tab({
        'type': 'page',
        'url': 'chrome://newtab/',
    })
    assert result is True


def test__is_valid_tab_not_a_tab(mock_browser):
    result = mock_browser._is_valid_tab({
        'type': 'tab',
        'url': 'chrome://newtab/',
    })
    assert result is False


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
@patch('pydoll.browser.chromium.chrome.validate_browser_paths')
@patch('platform.system')
def test__get_default_binary_location(
    mock_platform_system,
    mock_validate_browser_paths,
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
        with pytest.raises(exceptions.UnsupportedOS, match='Unsupported OS: SomethingElse'):
            Chrome._get_default_binary_location()


@patch('platform.system')
def test__get_default_binary_location_throws_exception_if_os_not_supported(
    mock_platform_system,
):
    mock_platform_system.return_value = 'FreeBSD'

    with pytest.raises(exceptions.UnsupportedOS, match='Unsupported OS: FreeBSD'):
        Chrome._get_default_binary_location()


@pytest.mark.asyncio
async def test_create_browser_context(mock_browser):
    mock_browser._execute_command = AsyncMock()
    mock_browser._execute_command.return_value = {
        'result': {'browserContextId': 'context1'}
    }
    
    context_id = await mock_browser.create_browser_context()
    assert context_id == 'context1'

    mock_browser._execute_command.assert_called_with(
        TargetCommands.create_browser_context()
    )
    
    # Test with proxy
    mock_browser._execute_command.return_value = {
        'result': {'browserContextId': 'context2'}
    }
    context_id = await mock_browser.create_browser_context(
        proxy_server='http://proxy.example.com:8080',
        proxy_bypass_list='localhost'
    )
    assert context_id == 'context2'
    mock_browser._execute_command.assert_called_with(
        TargetCommands.create_browser_context(
            proxy_server='http://proxy.example.com:8080',
            proxy_bypass_list='localhost'
        )
    )


@pytest.mark.asyncio
async def test_delete_browser_context(mock_browser):
    mock_browser._execute_command = AsyncMock()
    await mock_browser.delete_browser_context('context1')
    mock_browser._execute_command.assert_called_with(
        TargetCommands.dispose_browser_context('context1')
    )


@pytest.mark.asyncio
async def test_get_browser_contexts(mock_browser):
    mock_browser._execute_command = AsyncMock()
    mock_browser._execute_command.return_value = {
        'result': {'browserContextIds': ['context1', 'context2']}
    }
    
    contexts = await mock_browser.get_browser_contexts()
    assert contexts == ['context1', 'context2']
    mock_browser._execute_command.assert_called_with(
        TargetCommands.get_browser_contexts()
    )


@pytest.mark.asyncio
async def test_set_download_behavior(mock_browser):
    await mock_browser.set_download_behavior(
        behavior=DownloadBehavior.ALLOW,
        download_path='/downloads',
        events_enabled=True
    )
    
    mock_browser._connection_handler.execute_command.assert_called_with(
        BrowserCommands.set_download_behavior(
            behavior=DownloadBehavior.ALLOW,
            download_path='/downloads',
            browser_context_id=None,
            events_enabled=True
        ),
        timeout=10
    )


@pytest.mark.asyncio
async def test_set_download_path(mock_browser):
    mock_browser._execute_command = AsyncMock()
    await mock_browser.set_download_path('/downloads')
    
    mock_browser._execute_command.assert_called_with(
        BrowserCommands.set_download_behavior(
            behavior=DownloadBehavior.ALLOW,
            download_path='/downloads',
            browser_context_id=None,
        )
    )


@pytest.mark.asyncio
async def test_grant_permissions(mock_browser):
    permissions = [PermissionType.GEOLOCATION, PermissionType.NOTIFICATIONS]
    
    await mock_browser.grant_permissions(
        permissions=permissions,
        origin='https://example.com'
    )
    
    mock_browser._connection_handler.execute_command.assert_called_with(
        BrowserCommands.grant_permissions(
            permissions=permissions,
            origin='https://example.com',
            browser_context_id=None
        ),
        timeout=10
    )


@pytest.mark.asyncio
async def test_reset_permissions(mock_browser):
    await mock_browser.reset_permissions()
    
    mock_browser._connection_handler.execute_command.assert_called_with(
        BrowserCommands.reset_permissions(browser_context_id=None),
        timeout=10
    )


@pytest.mark.asyncio
async def test_get_version(mock_browser):
    mock_browser._connection_handler.execute_command.return_value = {
        'result': {
            'protocolVersion': '1.3',
            'product': 'Chrome/90.0.4430.93',
            'revision': '@abcdef',
            'userAgent': 'Mozilla/5.0...',
            'jsVersion': '9.0'
        }
    }
    
    version = await mock_browser.get_version()
    assert version['protocolVersion'] == '1.3'
    assert version['product'] == 'Chrome/90.0.4430.93'
    
    mock_browser._connection_handler.execute_command.assert_called_with(
        BrowserCommands.get_version(),
        timeout=10
    )


@pytest.mark.asyncio
async def test_headless_mode(mock_browser):
    mock_browser._connection_handler.ping.return_value = True
    mock_browser._get_valid_tab_id = AsyncMock(return_value='page1')
    
    await mock_browser.start(headless=True)
    
    assert '--headless' in mock_browser.options.arguments
    mock_browser._browser_process_manager.start_browser_process.assert_called_once()


@pytest.mark.asyncio
async def test_multiple_tab_handling(mock_browser):
    # Simulate getting multiple tabs
    mock_browser._connection_handler.execute_command.side_effect = [
        {'result': {'targetId': 'tab1'}},
        {'result': {'targetId': 'tab2'}}
    ]
    
    tab1 = await mock_browser.new_tab(url='https://example1.com')
    tab2 = await mock_browser.new_tab(url='https://example2.com')
    
    assert tab1._target_id == 'tab1'
    assert tab2._target_id == 'tab2'
    
    # Verify that correct calls were made
    calls = mock_browser._connection_handler.execute_command.call_args_list
    assert calls[0][0][0] == TargetCommands.create_target('https://example1.com', None)
    assert calls[1][0][0] == TargetCommands.create_target('https://example2.com', None)


# New tests for _get_valid_tab_id
@pytest.mark.asyncio
async def test_get_valid_tab_id_success():
    """Test _get_valid_tab_id with a valid tab."""
    targets = [
        {'type': 'page', 'url': 'https://example.com', 'targetId': 'valid_tab_1'},
        {'type': 'extension', 'url': 'chrome-extension://abc123', 'targetId': 'ext_1'},
        {'type': 'page', 'url': 'chrome://newtab/', 'targetId': 'valid_tab_2'}
    ]
    
    result = await Browser._get_valid_tab_id(targets)
    assert result == 'valid_tab_1'


@pytest.mark.asyncio
async def test_get_valid_tab_id_no_valid_tabs():
    """Test _get_valid_tab_id when there are no valid tabs."""
    targets = [
        {'type': 'extension', 'url': 'chrome-extension://abc123', 'targetId': 'ext_1'},
        {'type': 'background_page', 'url': 'chrome://background', 'targetId': 'bg_1'}
    ]
    
    with pytest.raises(exceptions.NoValidTabFound):
        await Browser._get_valid_tab_id(targets)


@pytest.mark.asyncio
async def test_get_valid_tab_id_empty_targets():
    """Test _get_valid_tab_id with empty targets list."""
    targets = []
    
    with pytest.raises(exceptions.NoValidTabFound):
        await Browser._get_valid_tab_id(targets)


@pytest.mark.asyncio
async def test_get_valid_tab_id_missing_target_id():
    """Test _get_valid_tab_id when valid tab has no targetId."""
    targets = [
        {'type': 'page', 'url': 'https://example.com'},  # No targetId
        {'type': 'extension', 'url': 'chrome-extension://abc123', 'targetId': 'ext_1'}
    ]
    
    with pytest.raises(exceptions.NoValidTabFound, match='Tab missing targetId'):
        await Browser._get_valid_tab_id(targets)


@pytest.mark.asyncio
async def test_get_valid_tab_id_filters_extensions():
    """Test if _get_valid_tab_id correctly filters extensions."""
    targets = [
        {'type': 'page', 'url': 'chrome-extension://abc123/popup.html', 'targetId': 'ext_page'},
        {'type': 'page', 'url': 'https://example.com', 'targetId': 'valid_tab'}
    ]
    
    result = await Browser._get_valid_tab_id(targets)
    assert result == 'valid_tab'


# Tests for enable_runtime_events and disable_runtime_events
@pytest.mark.asyncio
async def test_enable_runtime_events(mock_browser):
    """Test enable_runtime_events."""
    await mock_browser.enable_runtime_events()
    
    mock_browser._connection_handler.execute_command.assert_called_with(
        RuntimeCommands.enable()
    )


@pytest.mark.asyncio
async def test_disable_runtime_events(mock_browser):
    """Test disable_runtime_events."""
    await mock_browser.disable_runtime_events()
    
    mock_browser._connection_handler.execute_command.assert_called_with(
        RuntimeCommands.disable()
    )


# Tests for fail_request and fulfill_request
@pytest.mark.asyncio
async def test_fail_request(mock_browser):
    """Test fail_request."""
    request_id = 'test_request_123'
    error_reason = NetworkErrorReason.FAILED
    
    await mock_browser.fail_request(request_id, error_reason)
    
    mock_browser._connection_handler.execute_command.assert_called_with(
        FetchCommands.fail_request(request_id, error_reason), timeout=10
    )


@pytest.mark.asyncio
async def test_fulfill_request(mock_browser):
    """Test fulfill_request."""
    request_id = 'test_request_123'
    response_code = 200
    response_headers = [{'name': 'Content-Type', 'value': 'application/json'}]
    response_body = {'status': 'success', 'data': 'test'}
    
    await mock_browser.fulfill_request(
        request_id, response_code, response_headers, response_body
    )
    
    mock_browser._connection_handler.execute_command.assert_called_with(
        FetchCommands.fulfill_request(
            request_id, response_code, response_headers, response_body
        ), timeout=10
    )


# Additional test for 'on' with async callback
@pytest.mark.asyncio
async def test_event_registration_with_async_callback(mock_browser):
    """Test async callback registration."""
    mock_browser._connection_handler.register_callback.return_value = 456
    
    async def async_test_callback(event):
        """Test async callback."""
        return f"Processed event: {event}"
    
    callback_id = await mock_browser.on('test_async_event', async_test_callback, temporary=False)
    assert callback_id == 456
    
    mock_browser._connection_handler.register_callback.assert_called_with(
        'test_async_event', ANY, False
    )
    
    # Verify that callback was registered correctly
    call_args = mock_browser._connection_handler.register_callback.call_args
    registered_callback = call_args[0][1]  # Second argument (callback)
    
    # The registered callback should be a function
    assert callable(registered_callback)


@pytest.mark.asyncio
async def test_event_registration_sync_callback(mock_browser):
    """Test sync callback registration."""
    mock_browser._connection_handler.register_callback.return_value = 789
    
    def sync_test_callback(event):
        """Test sync callback."""
        return f"Processed sync event: {event}"
    
    callback_id = await mock_browser.on('test_sync_event', sync_test_callback, temporary=True)
    assert callback_id == 789
    
    mock_browser._connection_handler.register_callback.assert_called_with(
        'test_sync_event', ANY, True
    )


# Tests for get_opened_tabs method
@pytest.mark.asyncio
async def test_get_opened_tabs_success(mock_browser):
    """Test get_opened_tabs with multiple valid tabs."""
    # Mock get_targets to return various target types
    mock_targets = [
        {
            'targetId': 'tab1',
            'type': 'page',
            'url': 'https://example.com',
            'title': 'Example Site'
        },
        {
            'targetId': 'ext1',
            'type': 'page',
            'url': 'chrome-extension://abc123/popup.html',
            'title': 'Extension Popup'
        },
        {
            'targetId': 'tab2',
            'type': 'page',
            'url': 'https://google.com',
            'title': 'Google'
        },
        {
            'targetId': 'bg1',
            'type': 'background_page',
            'url': 'chrome://background',
            'title': 'Background Page'
        },
        {
            'targetId': 'tab3',
            'type': 'page',
            'url': 'chrome://newtab/',
            'title': 'New Tab'
        }
    ]
    
    mock_browser.get_targets = AsyncMock(return_value=mock_targets)
    
    # Clear Tab singleton registry to avoid conflicts
    Tab._instances.clear()
    
    tabs = await mock_browser.get_opened_tabs()
    
    # Should return 3 tabs (excluding extension and background_page)
    assert len(tabs) == 3
    
    # Verify all returned objects are Tab instances
    for tab in tabs:
        assert isinstance(tab, Tab)
    
    # Verify target IDs are correct (should be in reversed order)
    expected_target_ids = ['tab3', 'tab2', 'tab1']  # reversed order
    actual_target_ids = [tab._target_id for tab in tabs]
    assert actual_target_ids == expected_target_ids
    
    # Verify get_targets was called
    mock_browser.get_targets.assert_called_once()


@pytest.mark.asyncio
async def test_get_opened_tabs_no_valid_tabs(mock_browser):
    """Test get_opened_tabs when no valid tabs exist."""
    # Mock get_targets to return only non-page targets
    mock_targets = [
        {
            'targetId': 'ext1',
            'type': 'page',
            'url': 'chrome-extension://abc123/popup.html',
            'title': 'Extension Popup'
        },
        {
            'targetId': 'bg1',
            'type': 'background_page',
            'url': 'chrome://background',
            'title': 'Background Page'
        },
        {
            'targetId': 'worker1',
            'type': 'service_worker',
            'url': 'https://example.com/sw.js',
            'title': 'Service Worker'
        }
    ]
    
    mock_browser.get_targets = AsyncMock(return_value=mock_targets)
    
    # Clear Tab singleton registry
    Tab._instances.clear()
    
    tabs = await mock_browser.get_opened_tabs()
    
    # Should return empty list
    assert len(tabs) == 0
    assert tabs == []
    
    mock_browser.get_targets.assert_called_once()


@pytest.mark.asyncio
async def test_get_opened_tabs_empty_targets(mock_browser):
    """Test get_opened_tabs when no targets exist."""
    mock_browser.get_targets = AsyncMock(return_value=[])
    
    # Clear Tab singleton registry
    Tab._instances.clear()
    
    tabs = await mock_browser.get_opened_tabs()
    
    assert len(tabs) == 0
    assert tabs == []
    
    mock_browser.get_targets.assert_called_once()


@pytest.mark.asyncio
async def test_get_opened_tabs_filters_extensions(mock_browser):
    """Test that get_opened_tabs correctly filters out extension pages."""
    mock_targets = [
        {
            'targetId': 'tab1',
            'type': 'page',
            'url': 'https://example.com',
            'title': 'Example Site'
        },
        {
            'targetId': 'ext1',
            'type': 'page',
            'url': 'chrome-extension://abc123/popup.html',
            'title': 'Extension Popup'
        },
        {
            'targetId': 'ext2',
            'type': 'page',
            'url': 'moz-extension://def456/options.html',
            'title': 'Extension Options'
        },
        {
            'targetId': 'tab2',
            'type': 'page',
            'url': 'https://github.com',
            'title': 'GitHub'
        }
    ]
    
    mock_browser.get_targets = AsyncMock(return_value=mock_targets)
    
    # Clear Tab singleton registry
    Tab._instances.clear()
    
    tabs = await mock_browser.get_opened_tabs()
    
    # Should return only 2 tabs (excluding extensions)
    assert len(tabs) == 2
    
    # Verify no extension URLs in results
    for tab in tabs:
        assert 'extension' not in tab._target_id
    
    # Verify correct target IDs (reversed order)
    expected_target_ids = ['tab2', 'tab1']
    actual_target_ids = [tab._target_id for tab in tabs]
    assert actual_target_ids == expected_target_ids


@pytest.mark.asyncio
async def test_get_opened_tabs_filters_non_page_types(mock_browser):
    """Test that get_opened_tabs only returns 'page' type targets."""
    mock_targets = [
        {
            'targetId': 'tab1',
            'type': 'page',
            'url': 'https://example.com',
            'title': 'Example Site'
        },
        {
            'targetId': 'worker1',
            'type': 'service_worker',
            'url': 'https://example.com/sw.js',
            'title': 'Service Worker'
        },
        {
            'targetId': 'shared1',
            'type': 'shared_worker',
            'url': 'https://example.com/shared.js',
            'title': 'Shared Worker'
        },
        {
            'targetId': 'browser1',
            'type': 'browser',
            'url': '',
            'title': 'Browser Process'
        },
        {
            'targetId': 'tab2',
            'type': 'page',
            'url': 'https://google.com',
            'title': 'Google'
        }
    ]
    
    mock_browser.get_targets = AsyncMock(return_value=mock_targets)
    
    # Clear Tab singleton registry
    Tab._instances.clear()
    
    tabs = await mock_browser.get_opened_tabs()
    
    # Should return only 2 tabs (only 'page' type)
    assert len(tabs) == 2
    
    # Verify all are Tab instances
    for tab in tabs:
        assert isinstance(tab, Tab)
    
    # Verify correct target IDs (reversed order)
    expected_target_ids = ['tab2', 'tab1']
    actual_target_ids = [tab._target_id for tab in tabs]
    assert actual_target_ids == expected_target_ids


@pytest.mark.asyncio
async def test_get_opened_tabs_singleton_behavior(mock_browser):
    """Test that get_opened_tabs respects Tab singleton pattern."""
    mock_targets = [
        {
            'targetId': 'tab1',
            'type': 'page',
            'url': 'https://example.com',
            'title': 'Example Site'
        },
        {
            'targetId': 'tab2',
            'type': 'page',
            'url': 'https://google.com',
            'title': 'Google'
        }
    ]
    
    mock_browser.get_targets = AsyncMock(return_value=mock_targets)
    
    # Clear Tab singleton registry
    Tab._instances.clear()
    
    # First call
    tabs1 = await mock_browser.get_opened_tabs()
    
    # Second call with same targets
    tabs2 = await mock_browser.get_opened_tabs()
    
    # Should return same instances due to singleton pattern
    assert len(tabs1) == len(tabs2) == 2
    
    # Verify singleton behavior - same target_id should return same instance
    for tab1, tab2 in zip(tabs1, tabs2):
        if tab1._target_id == tab2._target_id:
            assert tab1 is tab2  # Same object reference


@pytest.mark.asyncio
async def test_get_opened_tabs_order_is_reversed(mock_browser):
    """Test that get_opened_tabs returns tabs in reversed order (most recent first)."""
    mock_targets = [
        {
            'targetId': 'oldest_tab',
            'type': 'page',
            'url': 'https://first.com',
            'title': 'First Tab'
        },
        {
            'targetId': 'middle_tab',
            'type': 'page',
            'url': 'https://second.com',
            'title': 'Second Tab'
        },
        {
            'targetId': 'newest_tab',
            'type': 'page',
            'url': 'https://third.com',
            'title': 'Third Tab'
        }
    ]
    
    mock_browser.get_targets = AsyncMock(return_value=mock_targets)
    
    # Clear Tab singleton registry
    Tab._instances.clear()
    
    tabs = await mock_browser.get_opened_tabs()
    
    # Should return in reversed order (newest first)
    expected_order = ['newest_tab', 'middle_tab', 'oldest_tab']
    actual_order = [tab._target_id for tab in tabs]
    
    assert actual_order == expected_order


@pytest.mark.asyncio
async def test_get_opened_tabs_with_mixed_valid_invalid_targets(mock_browser):
    """Test get_opened_tabs with a mix of valid and invalid targets."""
    mock_targets = [
        {
            'targetId': 'valid_tab1',
            'type': 'page',
            'url': 'https://example.com',
            'title': 'Valid Tab 1'
        },
        {
            'targetId': 'extension_page',
            'type': 'page',
            'url': 'chrome-extension://abc123/popup.html',
            'title': 'Extension Page'
        },
        {
            'targetId': 'service_worker',
            'type': 'service_worker',
            'url': 'https://example.com/sw.js',
            'title': 'Service Worker'
        },
        {
            'targetId': 'valid_tab2',
            'type': 'page',
            'url': 'https://github.com',
            'title': 'Valid Tab 2'
        },
        {
            'targetId': 'background_page',
            'type': 'background_page',
            'url': 'chrome://background',
            'title': 'Background'
        },
        {
            'targetId': 'valid_tab3',
            'type': 'page',
            'url': 'chrome://newtab/',
            'title': 'New Tab'
        }
    ]
    
    mock_browser.get_targets = AsyncMock(return_value=mock_targets)
    
    # Clear Tab singleton registry
    Tab._instances.clear()
    
    tabs = await mock_browser.get_opened_tabs()
    
    # Should return only 3 valid tabs
    assert len(tabs) == 3
    
    # Verify correct filtering and order
    expected_target_ids = ['valid_tab3', 'valid_tab2', 'valid_tab1']
    actual_target_ids = [tab._target_id for tab in tabs]
    assert actual_target_ids == expected_target_ids
    
    # Verify all are Tab instances
    for tab in tabs:
        assert isinstance(tab, Tab)


@pytest.mark.asyncio
async def test_get_opened_tabs_integration_with_new_tab(mock_browser):
    """Test get_opened_tabs integration with new_tab method."""
    # Mock initial targets (empty)
    mock_browser.get_targets = AsyncMock(return_value=[])
    
    # Clear Tab singleton registry
    Tab._instances.clear()
    
    # Initially no tabs
    tabs = await mock_browser.get_opened_tabs()
    assert len(tabs) == 0
    
    # Mock new_tab creation
    mock_browser._connection_handler.execute_command.return_value = {
        'result': {'targetId': 'new_tab_1'}
    }
    
    # Create a new tab
    new_tab = await mock_browser.new_tab('https://example.com')
    assert new_tab._target_id == 'new_tab_1'
    
    # Mock updated targets after tab creation
    mock_browser.get_targets = AsyncMock(return_value=[
        {
            'targetId': 'new_tab_1',
            'type': 'page',
            'url': 'https://example.com',
            'title': 'Example'
        }
    ])
    
    # Now get_opened_tabs should return the new tab
    tabs = await mock_browser.get_opened_tabs()
    assert len(tabs) == 1
    assert tabs[0]._target_id == 'new_tab_1'
    
    # Due to singleton pattern, should be the same instance
    assert tabs[0] is new_tab
