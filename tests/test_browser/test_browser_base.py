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
    StorageCommands,
    TargetCommands,
)
from pydoll.protocol.fetch.events import FetchEvent
from pydoll.connection.connection_handler import ConnectionHandler
from pydoll.constants import DownloadBehavior, PermissionType


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
        'Diretório temporário não configurado'
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
        FetchCommands.enable(True, '')
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
    print('TAB: ', tab)
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
        FetchCommands.enable(True, 'XHR')
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
    
    # Testar com proxy
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
    # Simular a obtenção de múltiplas abas
    mock_browser._connection_handler.execute_command.side_effect = [
        {'result': {'targetId': 'tab1'}},
        {'result': {'targetId': 'tab2'}}
    ]
    
    tab1 = await mock_browser.new_tab(url='https://example1.com')
    tab2 = await mock_browser.new_tab(url='https://example2.com')
    
    assert tab1._target_id == 'tab1'
    assert tab2._target_id == 'tab2'
    
    # Verificar que as chamadas corretas foram feitas
    calls = mock_browser._connection_handler.execute_command.call_args_list
    assert calls[0][0][0] == TargetCommands.create_target('https://example1.com', None)
    assert calls[1][0][0] == TargetCommands.create_target('https://example2.com', None)


