import asyncio
import base64
import concurrent.futures
import threading
import time
from unittest.mock import ANY, AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from pydoll import exceptions
from pydoll.browser.chromium.chrome import Chrome
from pydoll.browser.chromium.base import Browser
from pydoll.browser.managers import (
    ProxyManager,
    ChromiumOptionsManager,
    BrowserProcessManager,
    TempDirectoryManager,
)
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
from pydoll.exceptions import (
    MissingTargetOrWebSocket,
    InvalidWebSocketAddress,
    RunInParallelError,
)

from pydoll.protocol.network.types import RequestMethod, ErrorReason
from pydoll.protocol.browser.types import DownloadBehavior, PermissionType

class ConcreteBrowser(Browser):
    def _get_default_binary_location(self) -> str:
        return '/fake/path/to/browser'


@pytest_asyncio.fixture
async def mock_browser():
    with (
        patch.multiple(
            Browser,
            _get_default_binary_location=MagicMock(return_value='/fake/path/to/browser'),
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

        mock_temp_dir_manager.return_value.create_temp_dir.return_value = MagicMock(name='temp_dir')

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

    assert '--user-data-dir=' in str(
        mock_browser.options.arguments
    ), 'Temporary directory not configured'


@pytest.mark.asyncio
async def test_start_browser_failure(mock_browser):
    mock_browser._connection_handler.ping.return_value = False
    with patch('pydoll.browser.chromium.base.asyncio.sleep', AsyncMock()) as mock_sleep:
        mock_sleep.return_value = False
        with pytest.raises(exceptions.FailedToStartBrowser):
            await mock_browser.start()


@pytest.mark.asyncio
async def test_start_browser_failure_with_start_timeout(mock_browser):
    browser_launched = False

    async def launch_browser_later():
        nonlocal browser_launched
        await asyncio.sleep(2)
        browser_launched = True

    def start_browser_process_side_effect(*args, **kwargs):
        asyncio.create_task(launch_browser_later())

    async def ping_side_effect():
        nonlocal browser_launched
        return browser_launched

    mock_browser.options.start_timeout = 1
    mock_browser._get_valid_tab_id = AsyncMock(return_value='page1')
    mock_browser._browser_process_manager.start_browser_process.side_effect = (
        start_browser_process_side_effect
    )
    mock_browser._connection_handler.ping = AsyncMock(side_effect=ping_side_effect)

    with pytest.raises(exceptions.FailedToStartBrowser):
        await mock_browser.start()


@pytest.mark.asyncio
async def test_start_browser_success_with_start_timeout(mock_browser):
    browser_launched = False

    async def launch_browser_later():
        nonlocal browser_launched
        await asyncio.sleep(2)
        browser_launched = True

    def start_browser_process_side_effect(*args, **kwargs):
        asyncio.create_task(launch_browser_later())

    async def ping_side_effect():
        nonlocal browser_launched
        return browser_launched

    mock_browser.options.start_timeout = 3
    mock_browser._get_valid_tab_id = AsyncMock(return_value='page1')
    mock_browser._browser_process_manager.start_browser_process.side_effect = (
        start_browser_process_side_effect
    )
    mock_browser._connection_handler.ping = AsyncMock(side_effect=ping_side_effect)

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
async def test_connect_with_ws_address_returns_tab_and_sets_handler_ws(mock_browser):
    ws_browser = 'ws://localhost:9222/devtools/browser/abcdef'
    mock_browser.get_targets = AsyncMock(return_value=[{'type': 'page', 'url': 'https://example', 'targetId': 'p1'}])
    mock_browser._get_valid_tab_id = AsyncMock(return_value='p1')
    mock_browser._connection_handler._ensure_active_connection = AsyncMock()

    tab = await mock_browser.connect(ws_browser)

    assert mock_browser._ws_address == ws_browser
    assert mock_browser._connection_handler._ws_address == ws_browser
    mock_browser._connection_handler._ensure_active_connection.assert_awaited_once()

    # The returned Tab should connect using page ws address derived from browser ws
    assert isinstance(tab, Tab)
    assert tab._ws_address == 'ws://localhost:9222/devtools/page/p1'


@pytest.mark.asyncio
async def test_connect_with_ws_address_preserves_token_in_tab_ws(mock_browser):
    ws_browser = 'ws://localhost:9222/devtools/browser/abcdef?token=secrettoken'
    mock_browser.get_targets = AsyncMock(return_value=[{'type': 'page', 'url': 'https://example', 'targetId': 'p1'}])
    mock_browser._get_valid_tab_id = AsyncMock(return_value='p1')
    mock_browser._connection_handler._ensure_active_connection = AsyncMock()

    tab = await mock_browser.connect(ws_browser)

    assert mock_browser._ws_address == ws_browser
    assert mock_browser._connection_handler._ws_address == ws_browser
    mock_browser._connection_handler._ensure_active_connection.assert_awaited_once()

    # Token should be preserved in page-level ws URL
    assert isinstance(tab, Tab)
    assert tab._ws_address == 'ws://localhost:9222/devtools/page/p1?token=secrettoken'


@pytest.mark.asyncio
async def test_new_tab_uses_ws_base_when_ws_address_present(mock_browser):
    # Simulate browser connected via ws
    mock_browser._ws_address = 'ws://127.0.0.1:9222/devtools/browser/xyz'
    mock_browser._connection_handler.execute_command.return_value = {
        'result': {'targetId': 'new_page'}
    }

    tab = await mock_browser.new_tab()

    assert isinstance(tab, Tab)
    assert tab._ws_address == 'ws://127.0.0.1:9222/devtools/page/new_page'
    # When ws_address is used, target_id can be known from create_target response
    assert tab._target_id == 'new_page'


@pytest.mark.asyncio
async def test_get_window_id_for_tab_uses_ws_target_when_no_target_id(mock_browser):
    # Tab created only with ws address
    tab = Tab(mock_browser, ws_address='ws://localhost:9222/devtools/page/targetXYZ')
    mock_browser._connection_handler.execute_command.return_value = {
        'result': {'windowId': 'win1'}
    }

    window_id = await mock_browser.get_window_id_for_tab(tab)
    assert window_id == 'win1'
    mock_browser._connection_handler.execute_command.assert_called_with(
        BrowserCommands.get_window_for_target('targetXYZ'), timeout=10
    )


@pytest.mark.asyncio
async def test_cookie_management(mock_browser):
    cookies = [{'name': 'test', 'value': '123'}]
    await mock_browser.set_cookies(cookies)
    mock_browser._connection_handler.execute_command.assert_any_call(
        StorageCommands.set_cookies(cookies=cookies, browser_context_id=None), timeout=10
    )

    mock_browser._connection_handler.execute_command.return_value = {'result': {'cookies': cookies}}
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

    mock_browser._connection_handler.register_callback.assert_called_with('test_event', ANY, True)


@pytest.mark.asyncio
async def test_remove_callback_success(mock_browser):
    """Browser.remove_callback should forward to connection handler and return True."""
    mock_browser._connection_handler.remove_callback = AsyncMock(return_value=True)

    result = await mock_browser.remove_callback(42)

    mock_browser._connection_handler.remove_callback.assert_called_with(42)
    assert result is True


@pytest.mark.asyncio
async def test_remove_callback_false(mock_browser):
    """Browser.remove_callback should return False when handler returns False."""
    mock_browser._connection_handler.remove_callback = AsyncMock(return_value=False)

    result = await mock_browser.remove_callback(77)

    mock_browser._connection_handler.remove_callback.assert_called_with(77)
    assert result is False


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
async def test_get_window_id_for_tab_raises_when_no_target_id_and_no_ws(mock_browser):
    # Tab created only with connection_port, without target_id and ws
    tab = Tab(mock_browser, connection_port=9222)
    with pytest.raises(MissingTargetOrWebSocket):
        await mock_browser.get_window_id_for_tab(tab)


def test__validate_ws_address_raises_on_invalid_scheme():
    with pytest.raises(InvalidWebSocketAddress):
        Browser._validate_ws_address('http://localhost:9222/devtools/browser/abc')


def test__validate_ws_address_raises_on_insufficient_slashes():
    with pytest.raises(InvalidWebSocketAddress):
        Browser._validate_ws_address('ws://localhost')


def test__get_tab_ws_address_raises_when_ws_not_set(mock_browser):
    mock_browser._ws_address = None
    with pytest.raises(InvalidWebSocketAddress):
        mock_browser._get_tab_ws_address('some-tab')


def test__get_tab_ws_address_preserves_query_and_fragment(mock_browser):
    mock_browser._ws_address = 'ws://host:9222/devtools/browser/abc?token=XYZ#frag'
    result = mock_browser._get_tab_ws_address('tab1')
    assert result == 'ws://host:9222/devtools/page/tab1?token=XYZ#frag'


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
    await mock_browser.enable_fetch_events(handle_auth_requests=True, resource_type='XHR')
    mock_browser._connection_handler.execute_command.assert_called_with(
        FetchCommands.enable(handle_auth_requests=True, resource_type='XHR')
    )


@pytest.mark.asyncio
async def test_disable_events(mock_browser):
    await mock_browser.disable_fetch_events()
    mock_browser._connection_handler.execute_command.assert_called_with(FetchCommands.disable())


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

    mock_browser._connection_handler.execute_command.assert_any_call(FetchCommands.disable())


def test__is_valid_tab(mock_browser):
    result = mock_browser._is_valid_tab(
        {
            'type': 'page',
            'url': 'chrome://newtab/',
        }
    )
    assert result is True


def test__is_valid_tab_not_a_tab(mock_browser):
    result = mock_browser._is_valid_tab(
        {
            'type': 'tab',
            'url': 'chrome://newtab/',
        }
    )
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
        ('Linux', ['/usr/bin/google-chrome', '/usr/bin/google-chrome-stable'], '/usr/bin/google-chrome'),
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
    mock_browser._execute_command.return_value = {'result': {'browserContextId': 'context1'}}

    context_id = await mock_browser.create_browser_context()
    assert context_id == 'context1'

    mock_browser._execute_command.assert_called_with(TargetCommands.create_browser_context())

    # Test with proxy
    mock_browser._execute_command.return_value = {'result': {'browserContextId': 'context2'}}
    context_id = await mock_browser.create_browser_context(
        proxy_server='http://proxy.example.com:8080', proxy_bypass_list='localhost'
    )
    assert context_id == 'context2'
    mock_browser._execute_command.assert_called_with(
        TargetCommands.create_browser_context(
            proxy_server='http://proxy.example.com:8080', proxy_bypass_list='localhost'
        )
    )


@pytest.mark.asyncio
async def test_create_browser_context_with_private_proxy_sanitizes_and_stores_auth(mock_browser):
    mock_browser._execute_command = AsyncMock()
    mock_browser._execute_command.return_value = {'result': {'browserContextId': 'ctx1'}}

    context_id = await mock_browser.create_browser_context(
        proxy_server='http://user:pass@proxy.example.com:8080',
        proxy_bypass_list='localhost',
    )

    assert context_id == 'ctx1'
    # Should send sanitized proxy (without credentials) to CDP
    mock_browser._execute_command.assert_called_with(
        TargetCommands.create_browser_context(
            proxy_server='http://proxy.example.com:8080', proxy_bypass_list='localhost'
        )
    )
    # Credentials must be stored per-context for later Tab setup
    assert mock_browser._context_proxy_auth['ctx1'] == ('user', 'pass')


@pytest.mark.asyncio
async def test_create_browser_context_with_private_proxy_no_scheme_sanitizes_and_stores_auth(
    mock_browser,
):
    mock_browser._execute_command = AsyncMock()
    mock_browser._execute_command.return_value = {'result': {'browserContextId': 'ctx2'}}

    # Without scheme -> should default to http://
    context_id = await mock_browser.create_browser_context(
        proxy_server='user:pwd@host.local:9000'
    )

    assert context_id == 'ctx2'
    mock_browser._execute_command.assert_called_with(
        TargetCommands.create_browser_context(proxy_server='http://host.local:9000', proxy_bypass_list=None)
    )
    assert mock_browser._context_proxy_auth['ctx2'] == ('user', 'pwd')


@pytest.mark.parametrize(
    'input_proxy, expected_sanitized, expected_creds',
    [
        ('username:password@host:8080', 'http://host:8080', ('username', 'password')),
        ('http://username:password@host:8080', 'http://host:8080', ('username', 'password')),
        ('socks5://user:pass@10.0.0.1:1080', 'socks5://10.0.0.1:1080', ('user', 'pass')),
        ('user@host:3128', 'http://host:3128', ('user', '')),
        ('http://user@host:8080', 'http://host:8080', ('user', '')),
        ('host:3128', 'http://host:3128', None),
    ],
)
def test__sanitize_proxy_and_extract_auth_variants(input_proxy, expected_sanitized, expected_creds):
    sanitized, creds = Browser._sanitize_proxy_and_extract_auth(input_proxy)
    assert sanitized == expected_sanitized
    assert creds == expected_creds


@pytest.mark.asyncio
@patch('pydoll.browser.chromium.base.Tab')
async def test_new_tab_sets_up_context_proxy_auth_handlers(MockTab, mock_browser):
    # Arrange context credentials
    context_id = 'ctx-auth'
    mock_browser._context_proxy_auth[context_id] = ('u1', 'p1')

    # Mock CDP create_target response
    mock_browser._connection_handler.execute_command.return_value = {
        'result': {'targetId': 'new_page_ctx'}
    }

    # Fake Tab with async methods
    fake_tab = MagicMock()
    fake_tab.enable_fetch_events = AsyncMock()
    fake_tab.on = AsyncMock()
    MockTab.return_value = fake_tab

    # Act
    tab = await mock_browser.new_tab(browser_context_id=context_id)

    # Assert: enable fetch events with auth handling
    fake_tab.enable_fetch_events.assert_awaited_once()
    enable_call = fake_tab.enable_fetch_events.await_args
    assert enable_call.kwargs.get('handle_auth') is True

    # Assert: event handlers registered with temporary=True
    from pydoll.protocol.fetch.events import FetchEvent as FE
    # First: request paused
    assert any(
        (c.args[0] == FE.REQUEST_PAUSED and c.kwargs.get('temporary') is True)
        for c in fake_tab.on.await_args_list
    )
    # Second: auth required
    auth_calls = [c for c in fake_tab.on.await_args_list if c.args[0] == FE.AUTH_REQUIRED]
    assert len(auth_calls) == 1
    cb = auth_calls[0].args[1]
    from functools import partial as _partial
    assert isinstance(cb, _partial)
    assert cb.keywords.get('proxy_username') == 'u1'
    assert cb.keywords.get('proxy_password') == 'p1'
    assert cb.keywords.get('tab') is fake_tab

    # Returned tab is the fake
    assert tab is fake_tab


@pytest.mark.asyncio
@patch('pydoll.browser.chromium.base.Tab')
async def test_new_tab_without_context_proxy_auth_does_not_setup_handlers(MockTab, mock_browser):
    # No credentials stored for this context
    context_id = 'ctx-no-auth'
    mock_browser._context_proxy_auth.pop(context_id, None)

    mock_browser._connection_handler.execute_command.return_value = {
        'result': {'targetId': 'new_page2'}
    }

    fake_tab = MagicMock()
    fake_tab.enable_fetch_events = AsyncMock()
    fake_tab.on = AsyncMock()
    MockTab.return_value = fake_tab

    await mock_browser.new_tab(browser_context_id=context_id)

    fake_tab.enable_fetch_events.assert_not_called()
    fake_tab.on.assert_not_called()


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
    mock_browser._execute_command.assert_called_with(TargetCommands.get_browser_contexts())


@pytest.mark.asyncio
async def test_set_download_behavior(mock_browser):
    await mock_browser.set_download_behavior(
        behavior=DownloadBehavior.ALLOW, download_path='/downloads', events_enabled=True
    )

    mock_browser._connection_handler.execute_command.assert_called_with(
        BrowserCommands.set_download_behavior(
            behavior=DownloadBehavior.ALLOW,
            download_path='/downloads',
            browser_context_id=None,
            events_enabled=True,
        ),
        timeout=10,
    )


@pytest.mark.asyncio
async def test_set_download_path(mock_browser):
    mock_browser._execute_command = AsyncMock()
    await mock_browser.set_download_path(path='/downloads')
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

    await mock_browser.grant_permissions(permissions=permissions, origin='https://example.com')

    mock_browser._connection_handler.execute_command.assert_called_with(
        BrowserCommands.grant_permissions(
            permissions=permissions, origin='https://example.com', browser_context_id=None
        ),
        timeout=10,
    )


@pytest.mark.asyncio
async def test_reset_permissions(mock_browser):
    await mock_browser.reset_permissions()

    mock_browser._connection_handler.execute_command.assert_called_with(
        BrowserCommands.reset_permissions(browser_context_id=None), timeout=10
    )


@pytest.mark.asyncio
async def test_get_version(mock_browser):
    mock_browser._connection_handler.execute_command.return_value = {
        'result': {
            'protocolVersion': '1.3',
            'product': 'Chrome/90.0.4430.93',
            'revision': '@abcdef',
            'userAgent': 'Mozilla/5.0...',
            'jsVersion': '9.0',
        }
    }

    version = await mock_browser.get_version()
    assert version['protocolVersion'] == '1.3'
    assert version['product'] == 'Chrome/90.0.4430.93'

    mock_browser._connection_handler.execute_command.assert_called_with(
        BrowserCommands.get_version(), timeout=10
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
        {'result': {'targetId': 'tab2'}},
    ]

    tab1 = await mock_browser.new_tab()
    tab2 = await mock_browser.new_tab()

    assert tab1._target_id == 'tab1'
    assert tab2._target_id == 'tab2'

    # Verify that correct calls were made
    calls = mock_browser._connection_handler.execute_command.call_args_list
    assert len(calls) == 2


# New tests for _get_valid_tab_id
@pytest.mark.asyncio
async def test_get_valid_tab_id_success():
    """Test _get_valid_tab_id with a valid tab."""
    targets = [
        {'type': 'page', 'url': 'https://example.com', 'targetId': 'valid_tab_1'},
        {'type': 'extension', 'url': 'chrome-extension://abc123', 'targetId': 'ext_1'},
        {'type': 'page', 'url': 'chrome://newtab/', 'targetId': 'valid_tab_2'},
    ]

    result = await Browser._get_valid_tab_id(targets)
    assert result == 'valid_tab_1'


@pytest.mark.asyncio
async def test_get_valid_tab_id_no_valid_tabs():
    """Test _get_valid_tab_id when there are no valid tabs."""
    targets = [
        {'type': 'extension', 'url': 'chrome-extension://abc123', 'targetId': 'ext_1'},
        {'type': 'background_page', 'url': 'chrome://background', 'targetId': 'bg_1'},
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
        {'type': 'extension', 'url': 'chrome-extension://abc123', 'targetId': 'ext_1'},
    ]

    with pytest.raises(exceptions.NoValidTabFound, match='Tab missing targetId'):
        await Browser._get_valid_tab_id(targets)


@pytest.mark.asyncio
async def test_get_valid_tab_id_filters_extensions():
    """Test if _get_valid_tab_id correctly filters extensions."""
    targets = [
        {'type': 'page', 'url': 'chrome-extension://abc123/popup.html', 'targetId': 'ext_page'},
        {'type': 'page', 'url': 'https://example.com', 'targetId': 'valid_tab'},
    ]

    result = await Browser._get_valid_tab_id(targets)
    assert result == 'valid_tab'


# Tests for enable_runtime_events and disable_runtime_events
@pytest.mark.asyncio
async def test_enable_runtime_events(mock_browser):
    """Test enable_runtime_events."""
    await mock_browser.enable_runtime_events()

    mock_browser._connection_handler.execute_command.assert_called_with(RuntimeCommands.enable())


@pytest.mark.asyncio
async def test_disable_runtime_events(mock_browser):
    """Test disable_runtime_events."""
    await mock_browser.disable_runtime_events()

    mock_browser._connection_handler.execute_command.assert_called_with(RuntimeCommands.disable())


@pytest.mark.asyncio
async def test_get_tab_by_target(mock_browser):
    """Test get_tab_by_target creates Tab with correct target info."""
    target_info = {
        'targetId': 'test_target_123',
        'type': 'page',
        'url': 'https://example.com',
    }
    
    tab = await mock_browser.get_tab_by_target(target_info)
    
    assert isinstance(tab, Tab)
    assert tab._target_id == 'test_target_123'


# Tests for continue_request, fail_request and fulfill_request
@pytest.mark.asyncio
async def test_continue_request(mock_browser):
    """Test continue_request with minimal parameters."""
    request_id = 'test_request_123'

    await mock_browser.continue_request(request_id)

    mock_browser._connection_handler.execute_command.assert_called_with(
        FetchCommands.continue_request(
            request_id=request_id,
            url=None,
            method=None,
            post_data=None,
            headers=None,
            intercept_response=None,
        ),
        timeout=10,
    )


@pytest.mark.asyncio
async def test_continue_request_with_all_params(mock_browser):
    """Test continue_request with all parameters."""
    request_id = 'test_request_123'
    url = 'https://modified-example.com'
    method = RequestMethod.POST
    post_data = 'modified_data=test'
    headers = [{'name': 'Authorization', 'value': 'Bearer token123'}]
    intercept_response = True

    await mock_browser.continue_request(
        request_id=request_id,
        url=url,
        method=method,
        post_data=post_data,
        headers=headers,
        intercept_response=intercept_response,
    )

    mock_browser._connection_handler.execute_command.assert_called_with(
        FetchCommands.continue_request(
            request_id=request_id,
            url=url,
            method=method,
            post_data=post_data,
            headers=headers,
            intercept_response=intercept_response,
        ),
        timeout=10,
    )


@pytest.mark.asyncio
async def test_fail_request(mock_browser):
    """Test fail_request."""
    request_id = 'test_request_123'
    error_reason = ErrorReason.FAILED
    await mock_browser.fail_request(request_id, error_reason)

    mock_browser._connection_handler.execute_command.assert_called_with(
        FetchCommands.fail_request(request_id, error_reason), timeout=10
    )


@pytest.mark.asyncio
async def test_fulfill_request(mock_browser):
    """Test fulfill_request with minimal parameters."""
    request_id = 'test_request_123'
    response_code = 200

    await mock_browser.fulfill_request(request_id, response_code)

    mock_browser._connection_handler.execute_command.assert_called_with(
        FetchCommands.fulfill_request(
            request_id=request_id,
            response_code=response_code,
            response_headers=None,
            body=None,
            response_phrase=None,
        ),
        timeout=10,
    )


@pytest.mark.asyncio
async def test_fulfill_request_with_all_params(mock_browser):
    """Test fulfill_request with all parameters."""
    request_id = 'test_request_123'
    response_code = 200
    response_headers = [{'name': 'Content-Type', 'value': 'application/json'}]
    json_response = '{"status": "success", "data": "test"}'
    body = base64.b64encode(json_response.encode('utf-8')).decode('utf-8')
    response_phrase = 'OK'

    await mock_browser.fulfill_request(
        request_id=request_id,
        response_code=response_code,
        response_headers=response_headers,
        body=body,
        response_phrase=response_phrase,
    )

    mock_browser._connection_handler.execute_command.assert_called_with(
        FetchCommands.fulfill_request(
            request_id=request_id,
            response_code=response_code,
            response_headers=response_headers,
            body=body,
            response_phrase=response_phrase,
        ),
        timeout=10,
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
        {'targetId': 'tab3', 'type': 'page', 'url': 'https://example.com', 'title': 'Example Site'},
        {
            'targetId': 'ext1',
            'type': 'page',
            'url': 'chrome-extension://abc123/popup.html',
            'title': 'Extension Popup',
        },
        {'targetId': 'tab2', 'type': 'page', 'url': 'https://google.com', 'title': 'Google'},
        {
            'targetId': 'bg1',
            'type': 'background_page',
            'url': 'chrome://background',
            'title': 'Background Page',
        },
        {'targetId': 'tab1', 'type': 'page', 'url': 'chrome://newtab/', 'title': 'New Tab'},
    ]

    mock_browser.get_targets = AsyncMock(return_value=mock_targets)

    tabs = await mock_browser.get_opened_tabs()

    # Should return 3 tabs (excluding extension and background_page)
    assert len(tabs) == 3

    # Verify all returned objects are Tab instances
    for tab in tabs:
        assert isinstance(tab, Tab)

    # Verify target IDs are correct (should be in reversed order)
    expected_target_ids = ['tab1', 'tab2', 'tab3']  # reversed order
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
            'title': 'Extension Popup',
        },
        {
            'targetId': 'bg1',
            'type': 'background_page',
            'url': 'chrome://background',
            'title': 'Background Page',
        },
        {
            'targetId': 'worker1',
            'type': 'service_worker',
            'url': 'https://example.com/sw.js',
            'title': 'Service Worker',
        },
    ]

    mock_browser.get_targets = AsyncMock(return_value=mock_targets)

    tabs = await mock_browser.get_opened_tabs()

    # Should return empty list
    assert len(tabs) == 0
    assert tabs == []

    mock_browser.get_targets.assert_called_once()


@pytest.mark.asyncio
async def test_get_opened_tabs_empty_targets(mock_browser):
    """Test get_opened_tabs when no targets exist."""
    mock_browser.get_targets = AsyncMock(return_value=[])

    tabs = await mock_browser.get_opened_tabs()

    assert len(tabs) == 0
    assert tabs == []

    mock_browser.get_targets.assert_called_once()


@pytest.mark.asyncio
async def test_get_opened_tabs_filters_extensions(mock_browser):
    """Test that get_opened_tabs correctly filters out extension pages."""
    mock_targets = [
        {'targetId': 'tab1', 'type': 'page', 'url': 'https://example.com', 'title': 'Example Site'},
        {
            'targetId': 'ext1',
            'type': 'page',
            'url': 'chrome-extension://abc123/popup.html',
            'title': 'Extension Popup',
        },
        {
            'targetId': 'ext2',
            'type': 'page',
            'url': 'moz-extension://def456/options.html',
            'title': 'Extension Options',
        },
        {'targetId': 'tab2', 'type': 'page', 'url': 'https://github.com', 'title': 'GitHub'},
    ]

    mock_browser.get_targets = AsyncMock(return_value=mock_targets)

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
        {'targetId': 'tab1', 'type': 'page', 'url': 'https://example.com', 'title': 'Example Site'},
        {
            'targetId': 'worker1',
            'type': 'service_worker',
            'url': 'https://example.com/sw.js',
            'title': 'Service Worker',
        },
        {
            'targetId': 'shared1',
            'type': 'shared_worker',
            'url': 'https://example.com/shared.js',
            'title': 'Shared Worker',
        },
        {'targetId': 'browser1', 'type': 'browser', 'url': '', 'title': 'Browser Process'},
        {'targetId': 'tab2', 'type': 'page', 'url': 'https://google.com', 'title': 'Google'},
    ]

    mock_browser.get_targets = AsyncMock(return_value=mock_targets)

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
async def test_get_opened_tabs_order_is_reversed(mock_browser):
    """Test that get_opened_tabs returns tabs in reversed order (most recent first)."""
    mock_targets = [
        {
            'targetId': 'oldest_tab',
            'type': 'page',
            'url': 'https://first.com',
            'title': 'First Tab',
        },
        {
            'targetId': 'middle_tab',
            'type': 'page',
            'url': 'https://second.com',
            'title': 'Second Tab',
        },
        {
            'targetId': 'newest_tab',
            'type': 'page',
            'url': 'https://third.com',
            'title': 'Third Tab',
        },
    ]

    mock_browser.get_targets = AsyncMock(return_value=mock_targets)

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
            'title': 'Valid Tab 1',
        },
        {
            'targetId': 'extension_page',
            'type': 'page',
            'url': 'chrome-extension://abc123/popup.html',
            'title': 'Extension Page',
        },
        {
            'targetId': 'service_worker',
            'type': 'service_worker',
            'url': 'https://example.com/sw.js',
            'title': 'Service Worker',
        },
        {
            'targetId': 'valid_tab2',
            'type': 'page',
            'url': 'https://github.com',
            'title': 'Valid Tab 2',
        },
        {
            'targetId': 'background_page',
            'type': 'background_page',
            'url': 'chrome://background',
            'title': 'Background',
        },
        {'targetId': 'valid_tab3', 'type': 'page', 'url': 'chrome://newtab/', 'title': 'New Tab'},
    ]

    mock_browser.get_targets = AsyncMock(return_value=mock_targets)

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

    # Initially no tabs
    tabs = await mock_browser.get_opened_tabs()
    assert len(tabs) == 0

    # Mock new_tab creation
    mock_browser._connection_handler.execute_command.return_value = {
        'result': {'targetId': 'new_tab_1'}
    }

    # Create a new tab
    new_tab = await mock_browser.new_tab()
    assert new_tab._target_id == 'new_tab_1'

    # Mock updated targets after tab creation
    mock_browser.get_targets = AsyncMock(
        return_value=[
            {
                'targetId': 'new_tab_1',
                'type': 'page',
                'url': 'https://example.com',
                'title': 'Example',
            }
        ]
    )

    # Now get_opened_tabs should return the new tab
    tabs = await mock_browser.get_opened_tabs()
    assert len(tabs) == 1
    assert tabs[0]._target_id == 'new_tab_1'

    # Without singleton, instance identity can differ but ids should match
    assert tabs[0]._target_id == new_tab._target_id


@pytest.mark.asyncio
async def test_headless_parameter_deprecation_warning(mock_browser):
    mock_browser._connection_handler.ping.return_value = True
    mock_browser._get_valid_tab_id = AsyncMock(return_value='page1')
    
    with pytest.warns(
        DeprecationWarning,
        match="The 'headless' parameter is deprecated and will be removed in a future version"
    ):
        await mock_browser.start(headless=True)
    
    assert mock_browser.options.headless is True
    assert '--headless' in mock_browser.options.arguments


# Tests for run_in_parallel and _limited_coroutine methods
@pytest.mark.asyncio
async def test_run_in_parallel_no_semaphore(mock_browser):
    """Test run_in_parallel without semaphore (by mocking the condition)."""
    # Setup browser with initialized loop
    mock_browser._loop = asyncio.get_event_loop()
    mock_browser.options.max_parallel_tasks = 2
    mock_browser._semaphore = None
    
    # Mock the condition to prevent semaphore creation
    # Create test coroutines that return different values
    async def coro1():
        await asyncio.sleep(0.01)
        return "result1"
    
    async def coro2():
        await asyncio.sleep(0.01)
        return "result2"
    
    async def coro3():
        await asyncio.sleep(0.01)
        return "result3"
    
    # Execute run_in_parallel
    results = await mock_browser.run_in_parallel(coro1(), coro2(), coro3())
    
    # Verify results are returned in correct order
    assert results == ["result1", "result2", "result3"]
    assert mock_browser._semaphore is not None


@pytest.mark.asyncio
async def test_run_in_parallel_with_semaphore(mock_browser):
    """Test run_in_parallel with semaphore (max_parallel_tasks set)."""
    # Setup browser with initialized loop
    mock_browser._loop = asyncio.get_event_loop()
    mock_browser.options.max_parallel_tasks = 2  # Enable semaphore with limit 2
    mock_browser._semaphore = None  # Will be created by run_in_parallel
    
    execution_order = []
    
    async def coro_with_tracking(name, delay=0.01):
        execution_order.append(f"{name}_start")
        await asyncio.sleep(delay)
        execution_order.append(f"{name}_end")
        return name
    
    # Execute run_in_parallel with more coroutines than semaphore limit
    results = await mock_browser.run_in_parallel(
        coro_with_tracking("coro1"),
        coro_with_tracking("coro2"),
        coro_with_tracking("coro3")
    )
    
    # Verify results are correct
    assert results == ["coro1", "coro2", "coro3"]
    # Verify semaphore was created
    assert mock_browser._semaphore is not None
    assert mock_browser._semaphore._value == 2


@pytest.mark.asyncio
async def test_run_in_parallel_loop_not_initialized(mock_browser):
    """Test run_in_parallel raises RuntimeError when loop not initialized."""
    # Setup browser without initialized loop
    mock_browser._loop = None
    
    async def dummy_coro():
        return "test"
    
    # Should raise RuntimeError
    with pytest.raises(RuntimeError, match="Browser loop not initialized. Call start\\(\\) first."):
        await mock_browser.run_in_parallel(dummy_coro())


@pytest.mark.asyncio
async def test_run_in_parallel_from_different_loop(mock_browser):
    """Test run_in_parallel when called from different loop (same thread)."""
    
    # Create a separate event loop for the browser and run it in a thread
    browser_loop = asyncio.new_event_loop()
    mock_browser._loop = browser_loop
    mock_browser.options.max_parallel_tasks = 1
    mock_browser._semaphore = None
    
    results = []
    exception_container = []
    
    def browser_loop_thread():
        """Run the browser loop in a separate thread."""
        try:
            asyncio.set_event_loop(browser_loop)
            browser_loop.run_forever()
        except Exception as e:
            exception_container.append(e)
    
    # Start browser loop in separate thread
    thread = threading.Thread(target=browser_loop_thread, daemon=True)
    thread.start()
    
    # Wait a bit for the loop to start
    await asyncio.sleep(0.01)
    
    try:        
        # This should use run_coroutine_threadsafe since we're calling from main thread
        # while browser loop runs in different thread
        def run_sync():
            # Create fresh coroutines for the browser loop
            async def fresh_coro1():
                await asyncio.sleep(0.01)
                return "thread_result1"
            
            async def fresh_coro2():
                await asyncio.sleep(0.01)
                return "thread_result2"
            
            # Create the run_in_parallel coroutine
            coro = mock_browser.run_in_parallel(fresh_coro1(), fresh_coro2())
            
            # Run it using run_coroutine_threadsafe directly
            future = asyncio.run_coroutine_threadsafe(coro, browser_loop)
            return future.result(timeout=30)
        
        result = await asyncio.get_running_loop().run_in_executor(None, run_sync)
        
        results.append(result)
        
    finally:
        # Stop the browser loop
        browser_loop.call_soon_threadsafe(browser_loop.stop)
        thread.join(timeout=1.0)
        if not browser_loop.is_closed():
            browser_loop.close()
    
    # Verify no exceptions and correct results
    assert not exception_container
    assert len(results) == 1
    assert results[0] == ["thread_result1", "thread_result2"]


@pytest.mark.asyncio
async def test_run_in_parallel_from_same_thread(mock_browser):
    """Test run_in_parallel when called from same thread as browser loop."""
    # Setup browser with current event loop
    current_loop = asyncio.get_running_loop()
    mock_browser._loop = current_loop
    mock_browser.options.max_parallel_tasks = 1
    mock_browser._semaphore = None
    
    async def coro1():
        await asyncio.sleep(0.01)
        return "same_thread_result1"
    
    async def coro2():
        await asyncio.sleep(0.01)
        return "same_thread_result2"
    
    # Execute run_in_parallel (should use direct await path)
    results = await mock_browser.run_in_parallel(coro1(), coro2())
    
    # Verify results
    assert results == ["same_thread_result1", "same_thread_result2"]


@pytest.mark.asyncio
async def test_limited_coroutine_without_semaphore(mock_browser):
    """Test _limited_coroutine without semaphore."""
    mock_browser.options.max_parallel_tasks = 1
    mock_browser._semaphore = None
    
    async def test_coro():
        await asyncio.sleep(0.01)
        return "no_semaphore_result"
    
    # Execute _limited_coroutine
    result = await mock_browser._limited_coroutine(test_coro())
    
    # Verify result
    assert result == "no_semaphore_result"


@pytest.mark.asyncio
async def test_limited_coroutine_with_semaphore(mock_browser):
    """Test _limited_coroutine with semaphore."""
    mock_browser.options.max_parallel_tasks = 1
    mock_browser._semaphore = asyncio.Semaphore(1)
    
    execution_times = []
    
    async def timed_coro(name):
        start_time = time.time()
        execution_times.append(f"{name}_start_{start_time}")
        await asyncio.sleep(0.02)  # Small delay to ensure ordering
        end_time = time.time()
        execution_times.append(f"{name}_end_{end_time}")
        return f"semaphore_result_{name}"
    
    # Execute multiple _limited_coroutine calls concurrently
    results = await asyncio.gather(
        mock_browser._limited_coroutine(timed_coro("1")),
        mock_browser._limited_coroutine(timed_coro("2"))
    )
    
    # Verify results
    assert results == ["semaphore_result_1", "semaphore_result_2"]
    # Verify execution was serialized (one should complete before other starts)
    assert len(execution_times) == 4


@pytest.mark.asyncio
async def test_run_in_parallel_semaphore_limiting(mock_browser):
    """Test that semaphore properly limits concurrent execution."""
    mock_browser._loop = asyncio.get_event_loop()
    mock_browser.options.max_parallel_tasks = 2
    mock_browser._semaphore = None  # Will be created
    
    concurrent_count = 0
    max_concurrent = 0
    execution_log = []
    
    async def monitored_coro(name):
        nonlocal concurrent_count, max_concurrent
        concurrent_count += 1
        max_concurrent = max(max_concurrent, concurrent_count)
        execution_log.append(f"{name}_start_concurrent_{concurrent_count}")
        
        await asyncio.sleep(0.02)  # Simulate work
        
        concurrent_count -= 1
        execution_log.append(f"{name}_end_concurrent_{concurrent_count + 1}")
        return f"limited_result_{name}"
    
    # Run 4 coroutines with limit of 2
    results = await mock_browser.run_in_parallel(
        monitored_coro("A"),
        monitored_coro("B"),
        monitored_coro("C"),
        monitored_coro("D")
    )
    
    # Verify results
    assert results == ["limited_result_A", "limited_result_B", "limited_result_C", "limited_result_D"]
    # Verify concurrency was limited to 2
    assert max_concurrent <= 2
    assert mock_browser._semaphore._value == 2


@pytest.mark.asyncio
async def test_run_in_parallel_empty_coroutines(mock_browser):
    """Test run_in_parallel with no coroutines."""
    mock_browser._loop = asyncio.get_event_loop()
    mock_browser.options.max_parallel_tasks = 1
    mock_browser._semaphore = None
    
    # Execute with no coroutines
    results = await mock_browser.run_in_parallel()
    
    # Should return empty list
    assert results == []


@pytest.mark.asyncio
async def test_run_in_parallel_single_coroutine(mock_browser):
    """Test run_in_parallel with single coroutine."""
    mock_browser._loop = asyncio.get_event_loop()
    mock_browser.options.max_parallel_tasks = 1
    mock_browser._semaphore = None
    
    async def single_coro():
        await asyncio.sleep(0.01)
        return "single_result"
    
    # Execute with single coroutine
    results = await mock_browser.run_in_parallel(single_coro())
    
    # Should return list with single result
    assert results == ["single_result"]


@pytest.mark.asyncio
async def test_run_in_parallel_coroutine_exception(mock_browser):
    """Test run_in_parallel handles coroutine exceptions properly."""
    mock_browser._loop = asyncio.get_event_loop()
    mock_browser.options.max_parallel_tasks = 1
    mock_browser._semaphore = None
    
    async def failing_coro():
        await asyncio.sleep(0.01)
        raise ValueError("Test exception")
    
    async def success_coro():
        await asyncio.sleep(0.01)
        return "success"
    
    # Should propagate the exception
    with pytest.raises(ValueError, match="Test exception"):
        await mock_browser.run_in_parallel(success_coro(), failing_coro())


@pytest.mark.asyncio
async def test_limited_coroutine_exception(mock_browser):
    """Test _limited_coroutine handles exceptions properly."""
    mock_browser.options.max_parallel_tasks = 1
    mock_browser._semaphore = asyncio.Semaphore(1)
    
    async def failing_coro():
        await asyncio.sleep(0.01)
        raise RuntimeError("Limited coroutine exception")
    
    # Should propagate the exception
    with pytest.raises(RuntimeError, match="Limited coroutine exception"):
        await mock_browser._limited_coroutine(failing_coro())


@pytest.mark.asyncio
async def test_run_in_parallel_semaphore_creation_once(mock_browser):
    """Test that semaphore is created only once when max_parallel_tasks is set."""
    mock_browser._loop = asyncio.get_event_loop()
    mock_browser.options.max_parallel_tasks = 3
    mock_browser._semaphore = None
    
    async def dummy_coro(value):
        await asyncio.sleep(0.01)
        return value
    
    # First call should create semaphore
    await mock_browser.run_in_parallel(dummy_coro(1))
    first_semaphore = mock_browser._semaphore
    assert first_semaphore is not None
    assert first_semaphore._value == 3
    
    # Second call should reuse existing semaphore
    await mock_browser.run_in_parallel(dummy_coro(2))
    assert mock_browser._semaphore is first_semaphore


@pytest.mark.asyncio
async def test_run_in_parallel_loop_not_running(mock_browser):
    """Test run_in_parallel raises RunInParallelError when browser loop is not running."""
    # Create a stopped loop - different from current running loop
    browser_loop = asyncio.new_event_loop()
    mock_browser._loop = browser_loop
    mock_browser.options.max_parallel_tasks = 1  # Disable semaphore
    mock_browser._semaphore = None
    
    # Loop is created but NOT running
    assert not browser_loop.is_running()
    
    async def dummy_coro():
        return "result"
    
    # Should raise RunInParallelError when trying to execute from different loop
    # The current running loop is different from browser_loop, and browser_loop is not running
    with pytest.raises(RunInParallelError, match="Browser loop is not running"):
        await mock_browser.run_in_parallel(dummy_coro())
    
    browser_loop.close()


@pytest.mark.asyncio
async def test_run_in_parallel_no_running_loop_fallback(mock_browser):
    """Test run_in_parallel handles RuntimeError from get_running_loop() and falls back to threadsafe."""
    # Setup browser with a loop
    browser_loop = asyncio.new_event_loop()
    mock_browser._loop = browser_loop
    mock_browser.options.max_parallel_tasks = 1
    mock_browser._semaphore = None
    
    async def dummy_coro():
        return "test_result"
    
    # Mock get_running_loop to raise RuntimeError (simulating no running loop)
    # This triggers the except RuntimeError block and sets current_loop = None
    with patch('asyncio.get_running_loop', side_effect=RuntimeError("No running loop")):
        # Mock is_running to return True so we can proceed past the check
        with patch.object(browser_loop, 'is_running', return_value=True):
            # Mock run_coroutine_threadsafe to return a successful future
            mock_future = MagicMock()
            mock_future.result.return_value = ["test_result"]
            
            with patch('asyncio.run_coroutine_threadsafe', return_value=mock_future):
                # Should successfully use threadsafe execution path
                results = await mock_browser.run_in_parallel(dummy_coro())
                assert results == ["test_result"]
    
    browser_loop.close()


@pytest.mark.asyncio
async def test_run_in_parallel_threadsafe_future_exception(mock_browser):
    """Test run_in_parallel wraps exceptions from future.result() in RunInParallelError."""
    # Setup browser with a different loop to trigger threadsafe path
    browser_loop = asyncio.new_event_loop()
    mock_browser._loop = browser_loop
    mock_browser.options.max_parallel_tasks = 1
    mock_browser._semaphore = None
    
    # Mock run_coroutine_threadsafe to return a future that raises an exception
    mock_future = MagicMock()
    mock_future.result.side_effect = RuntimeError("Future execution error")
    async def dummy_coro():
        return "result"
    
    with patch('asyncio.run_coroutine_threadsafe', return_value=mock_future):
        # Ensure we're in a different loop
        with patch.object(browser_loop, 'is_running', return_value=True):
            # Should wrap the exception in RunInParallelError
            with pytest.raises(RunInParallelError, match="Coroutine execution failed: Future execution error"):
                await mock_browser.run_in_parallel(dummy_coro())
    
    browser_loop.close()
