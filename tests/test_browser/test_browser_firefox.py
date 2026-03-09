"""Tests for the Firefox BiDi browser module."""
from __future__ import annotations

import base64
import platform
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from pydoll.browser.firefox.element import FirefoxElement, KEYS
from pydoll.browser.firefox.firefox import Firefox
from pydoll.browser.firefox.base import FirefoxBrowser
from pydoll.browser.firefox_options import FirefoxOptions
from pydoll.browser.firefox.tab import FirefoxTab
from pydoll.browser.managers.firefox_options_manager import FirefoxOptionsManager
from pydoll.connection.bidi_connection_handler import BiDiConnectionHandler
from pydoll.exceptions import (
    ArgumentAlreadyExistsInOptions,
    ArgumentNotFoundInOptions,
    BiDiCommandError,
    FailedToStartBrowser,
    BrowserNotRunning,
    InvalidConnectionPort,
    InvalidOptionsObject,
    UnsupportedOS,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def mock_bidi_handler():
    """A fully mocked BiDiConnectionHandler."""
    handler = MagicMock(spec=BiDiConnectionHandler)
    handler.execute_command = AsyncMock(return_value={'result': {}})
    handler.register_callback = AsyncMock(return_value=1)
    handler.remove_callback = AsyncMock(return_value=True)
    handler.ping = AsyncMock(return_value=True)
    handler.new_session = AsyncMock(return_value={'result': {'sessionId': 'test-session'}})
    handler.close = AsyncMock()
    return handler


@pytest_asyncio.fixture
async def firefox_tab(mock_bidi_handler):
    """A FirefoxTab backed by a mocked handler."""
    return FirefoxTab(context_id='ctx-1', connection_handler=mock_bidi_handler)


@pytest_asyncio.fixture
async def firefox_element(mock_bidi_handler):
    """A FirefoxElement backed by a mocked handler."""
    node = {'type': 'node', 'sharedId': 'shared-1', 'value': {'nodeType': 1}}
    return FirefoxElement(node=node, context_id='ctx-1', connection_handler=mock_bidi_handler)


@pytest_asyncio.fixture
async def mock_firefox(mock_bidi_handler):
    """A Firefox instance with all external dependencies mocked out."""
    with (
        patch.multiple(
            Firefox,
            _get_default_binary_location=MagicMock(return_value='/fake/firefox'),
        ),
        patch(
            'pydoll.browser.managers.browser_process_manager.BrowserProcessManager',
            autospec=True,
        ) as mock_pm,
        patch(
            'pydoll.browser.managers.temp_dir_manager.TempDirectoryManager',
            autospec=True,
        ) as mock_tdm,
    ):
        browser = Firefox()
        browser._browser_process_manager = mock_pm.return_value
        browser._temp_directory_manager = mock_tdm.return_value
        browser._connection_handler = mock_bidi_handler

        # Fake temp profile dir
        temp_dir = MagicMock()
        temp_dir.name = '/tmp/fake-profile'
        mock_tdm.return_value.create_temp_dir.return_value = temp_dir

        yield browser


# ---------------------------------------------------------------------------
# FirefoxOptions tests
# ---------------------------------------------------------------------------

class TestFirefoxOptions:
    def test_default_state(self):
        opts = FirefoxOptions()
        assert opts.arguments == []
        assert opts.binary_location == ''
        assert opts.start_timeout == 30
        assert opts.headless is False
        assert opts.browser_preferences == {}

    def test_add_argument(self):
        opts = FirefoxOptions()
        opts.add_argument('--safe-mode')
        assert '--safe-mode' in opts.arguments

    def test_add_duplicate_argument_raises(self):
        opts = FirefoxOptions()
        opts.add_argument('--safe-mode')
        with pytest.raises(ArgumentAlreadyExistsInOptions):
            opts.add_argument('--safe-mode')

    def test_remove_argument(self):
        opts = FirefoxOptions()
        opts.add_argument('--safe-mode')
        opts.remove_argument('--safe-mode')
        assert '--safe-mode' not in opts.arguments

    def test_remove_nonexistent_argument_raises(self):
        opts = FirefoxOptions()
        with pytest.raises(ArgumentNotFoundInOptions):
            opts.remove_argument('--safe-mode')

    def test_headless_adds_argument(self):
        opts = FirefoxOptions()
        opts.headless = True
        assert '--headless' in opts.arguments
        assert opts.headless is True

    def test_headless_removes_argument_when_disabled(self):
        opts = FirefoxOptions()
        opts.headless = True
        opts.headless = False
        assert '--headless' not in opts.arguments
        assert opts.headless is False

    def test_headless_noop_when_already_set(self):
        opts = FirefoxOptions()
        opts.headless = True
        opts.headless = True  # second call should not raise
        assert opts.arguments.count('--headless') == 1

    def test_binary_location_setter(self):
        opts = FirefoxOptions()
        opts.binary_location = '/usr/bin/firefox'
        assert opts.binary_location == '/usr/bin/firefox'

    def test_browser_preferences_merges(self):
        opts = FirefoxOptions()
        opts.browser_preferences = {'key1': 'val1'}
        opts.browser_preferences = {'key2': 'val2'}
        assert opts.browser_preferences == {'key1': 'val1', 'key2': 'val2'}

    def test_browser_preferences_invalid_type_raises(self):
        opts = FirefoxOptions()
        with pytest.raises(ValueError):
            opts.browser_preferences = 'not-a-dict'  # type: ignore


# ---------------------------------------------------------------------------
# FirefoxOptionsManager tests
# ---------------------------------------------------------------------------

class TestFirefoxOptionsManager:
    def test_initialize_creates_default_options(self):
        mgr = FirefoxOptionsManager()
        opts = mgr.initialize_options()
        assert isinstance(opts, FirefoxOptions)

    def test_initialize_uses_provided_options(self):
        custom = FirefoxOptions()
        mgr = FirefoxOptionsManager(custom)
        opts = mgr.initialize_options()
        assert opts is custom

    def test_initialize_invalid_type_raises(self):
        mgr = FirefoxOptionsManager('not-options')  # type: ignore
        with pytest.raises(InvalidOptionsObject):
            mgr.initialize_options()

    def test_add_default_arguments(self):
        mgr = FirefoxOptionsManager()
        opts = mgr.initialize_options()
        assert '--no-remote' in opts.arguments
        assert '--new-instance' in opts.arguments


# ---------------------------------------------------------------------------
# BiDiConnectionHandler tests
# ---------------------------------------------------------------------------

class TestBiDiConnectionHandler:
    @pytest.mark.asyncio
    async def test_resolve_ws_address(self):
        handler = BiDiConnectionHandler(connection_port=9222)
        address = await handler._resolve_ws_address()
        assert address == 'ws://localhost:9222/session'

    @pytest.mark.asyncio
    async def test_new_session_stores_session_id(self):
        handler = BiDiConnectionHandler(connection_port=9222)
        handler.execute_command = AsyncMock(
            return_value={'result': {'sessionId': 'abc-123', 'capabilities': {}}}
        )
        await handler.new_session()
        assert handler._session_id == 'abc-123'

    @pytest.mark.asyncio
    async def test_new_session_returns_response(self):
        handler = BiDiConnectionHandler(connection_port=9222)
        expected = {'result': {'sessionId': 'xyz', 'capabilities': {}}}
        handler.execute_command = AsyncMock(return_value=expected)
        result = await handler.new_session()
        assert result == expected

    @pytest.mark.asyncio
    async def test_execute_command_raises_on_bidi_error(self):
        handler = BiDiConnectionHandler(connection_port=9222)
        error_response = {
            'type': 'error',
            'id': 1,
            'error': 'invalid argument',
            'message': 'No such context',
        }
        # Bypass super().execute_command by patching the parent
        with patch(
            'pydoll.connection.bidi_connection_handler.ConnectionHandler.execute_command',
            new=AsyncMock(return_value=error_response),
        ):
            with pytest.raises(BiDiCommandError, match='invalid argument: No such context'):
                await handler.execute_command({'method': 'browsingContext.navigate', 'params': {}})

    @pytest.mark.asyncio
    async def test_execute_command_passes_through_success(self):
        handler = BiDiConnectionHandler(connection_port=9222)
        success_response = {'type': 'success', 'id': 1, 'result': {'url': 'https://example.com'}}
        with patch(
            'pydoll.connection.bidi_connection_handler.ConnectionHandler.execute_command',
            new=AsyncMock(return_value=success_response),
        ):
            result = await handler.execute_command({'method': 'browsingContext.navigate', 'params': {}})
        assert result == success_response


# ---------------------------------------------------------------------------
# FirefoxTab tests
# ---------------------------------------------------------------------------

class TestFirefoxTab:
    def test_context_id_property(self, firefox_tab):
        assert firefox_tab.context_id == 'ctx-1'

    def test_repr(self, firefox_tab):
        assert 'ctx-1' in repr(firefox_tab)

    @pytest.mark.asyncio
    async def test_go_to_sends_navigate_command(self, firefox_tab, mock_bidi_handler):
        mock_bidi_handler.execute_command.return_value = {
            'result': {'url': 'https://example.com', 'navigation': 'nav-1'}
        }
        result = await firefox_tab.go_to('https://example.com')
        assert result['url'] == 'https://example.com'
        mock_bidi_handler.execute_command.assert_called_once()
        cmd = mock_bidi_handler.execute_command.call_args[0][0]
        assert cmd['method'] == 'browsingContext.navigate'
        assert cmd['params']['context'] == 'ctx-1'
        assert cmd['params']['url'] == 'https://example.com'

    @pytest.mark.asyncio
    async def test_evaluate_returns_value(self, firefox_tab, mock_bidi_handler):
        mock_bidi_handler.execute_command.return_value = {
            'result': {'result': {'type': 'string', 'value': 'hello'}, 'realm': 'r1'}
        }
        value = await firefox_tab.evaluate('document.title')
        assert value == 'hello'
        cmd = mock_bidi_handler.execute_command.call_args[0][0]
        assert cmd['method'] == 'script.evaluate'
        assert cmd['params']['expression'] == 'document.title'
        assert cmd['params']['target']['context'] == 'ctx-1'

    @pytest.mark.asyncio
    async def test_find_returns_firefox_elements(self, firefox_tab, mock_bidi_handler):
        nodes = [{'type': 'node', 'sharedId': 'node-1'}]
        mock_bidi_handler.execute_command.return_value = {'result': {'nodes': nodes}}
        result = await firefox_tab.find('.my-class')
        assert len(result) == 1
        assert isinstance(result[0], FirefoxElement)
        assert result[0].shared_id == 'node-1'
        cmd = mock_bidi_handler.execute_command.call_args[0][0]
        assert cmd['method'] == 'browsingContext.locateNodes'
        assert cmd['params']['locator'] == {'type': 'css', 'value': '.my-class'}

    @pytest.mark.asyncio
    async def test_find_empty_result(self, firefox_tab, mock_bidi_handler):
        mock_bidi_handler.execute_command.return_value = {'result': {'nodes': []}}
        result = await firefox_tab.find('.missing')
        assert result == []

    @pytest.mark.asyncio
    async def test_find_with_xpath_locator(self, firefox_tab, mock_bidi_handler):
        mock_bidi_handler.execute_command.return_value = {'result': {'nodes': []}}
        await firefox_tab.find('//h1', selector_type='xpath')
        cmd = mock_bidi_handler.execute_command.call_args[0][0]
        assert cmd['params']['locator'] == {'type': 'xpath', 'value': '//h1'}

    @pytest.mark.asyncio
    async def test_find_with_max_node_count(self, firefox_tab, mock_bidi_handler):
        mock_bidi_handler.execute_command.return_value = {'result': {'nodes': []}}
        await firefox_tab.find('p', max_node_count=5)
        cmd = mock_bidi_handler.execute_command.call_args[0][0]
        assert cmd['params']['maxNodeCount'] == 5

    @pytest.mark.asyncio
    async def test_take_screenshot_returns_bytes(self, firefox_tab, mock_bidi_handler):
        raw = b'fake-png-data'
        encoded = base64.b64encode(raw).decode()
        mock_bidi_handler.execute_command.return_value = {'result': {'data': encoded}}
        result = await firefox_tab.take_screenshot()
        assert result == raw
        cmd = mock_bidi_handler.execute_command.call_args[0][0]
        assert cmd['method'] == 'browsingContext.captureScreenshot'
        assert cmd['params']['context'] == 'ctx-1'

    @pytest.mark.asyncio
    async def test_current_url(self, firefox_tab, mock_bidi_handler):
        mock_bidi_handler.execute_command.return_value = {
            'result': {'result': {'type': 'string', 'value': 'https://example.com'}, 'realm': 'r'}
        }
        url = await firefox_tab.current_url
        assert url == 'https://example.com'

    @pytest.mark.asyncio
    async def test_page_source(self, firefox_tab, mock_bidi_handler):
        mock_bidi_handler.execute_command.return_value = {
            'result': {'result': {'type': 'string', 'value': '<html></html>'}, 'realm': 'r'}
        }
        source = await firefox_tab.page_source
        assert source == '<html></html>'

    @pytest.mark.asyncio
    async def test_title(self, firefox_tab, mock_bidi_handler):
        mock_bidi_handler.execute_command.return_value = {
            'result': {'result': {'type': 'string', 'value': 'My Page'}, 'realm': 'r'}
        }
        title = await firefox_tab.title
        assert title == 'My Page'

    @pytest.mark.asyncio
    async def test_press_key_named_key(self, firefox_tab, mock_bidi_handler):
        await firefox_tab.press_key('enter')
        cmd = mock_bidi_handler.execute_command.call_args[0][0]
        assert cmd['method'] == 'input.performActions'
        assert cmd['params']['context'] == 'ctx-1'
        actions = cmd['params']['actions'][0]['actions']
        assert actions == [
            {'type': 'keyDown', 'value': KEYS['enter']},
            {'type': 'keyUp', 'value': KEYS['enter']},
        ]

    @pytest.mark.asyncio
    async def test_press_key_single_char(self, firefox_tab, mock_bidi_handler):
        await firefox_tab.press_key('z')
        cmd = mock_bidi_handler.execute_command.call_args[0][0]
        actions = cmd['params']['actions'][0]['actions']
        assert actions == [
            {'type': 'keyDown', 'value': 'z'},
            {'type': 'keyUp', 'value': 'z'},
        ]

    @pytest.mark.asyncio
    async def test_press_key_unknown_key_uses_value_as_is(self, firefox_tab, mock_bidi_handler):
        await firefox_tab.press_key('X')
        cmd = mock_bidi_handler.execute_command.call_args[0][0]
        actions = cmd['params']['actions'][0]['actions']
        assert actions[0]['value'] == 'X'

    @pytest.mark.asyncio
    async def test_on_subscribes_and_registers_callback(self, firefox_tab, mock_bidi_handler):
        callback = AsyncMock()
        mock_bidi_handler.register_callback.return_value = 42
        cb_id = await firefox_tab.on('browsingContext.load', callback)
        assert cb_id == 42
        # subscribe command sent
        sub_cmd = mock_bidi_handler.execute_command.call_args[0][0]
        assert sub_cmd['method'] == 'session.subscribe'
        assert 'browsingContext.load' in sub_cmd['params']['events']
        assert 'ctx-1' in sub_cmd['params']['contexts']
        mock_bidi_handler.register_callback.assert_called_once()

    @pytest.mark.asyncio
    async def test_on_sync_callback(self, firefox_tab, mock_bidi_handler):
        callback = MagicMock()  # sync
        mock_bidi_handler.register_callback.return_value = 1
        cb_id = await firefox_tab.on('browsingContext.load', callback)
        assert cb_id == 1

    @pytest.mark.asyncio
    async def test_remove_callback(self, firefox_tab, mock_bidi_handler):
        mock_bidi_handler.remove_callback.return_value = True
        result = await firefox_tab.remove_callback(99)
        assert result is True
        mock_bidi_handler.remove_callback.assert_called_once_with(99)

    @pytest.mark.asyncio
    async def test_new_tab_creates_tab(self, firefox_tab, mock_bidi_handler):
        mock_bidi_handler.execute_command.return_value = {'result': {'context': 'ctx-new'}}
        new_tab = await firefox_tab.new_tab()
        assert isinstance(new_tab, FirefoxTab)
        assert new_tab.context_id == 'ctx-new'

    @pytest.mark.asyncio
    async def test_new_tab_navigates_if_url_given(self, firefox_tab, mock_bidi_handler):
        mock_bidi_handler.execute_command.side_effect = [
            {'result': {'context': 'ctx-new'}},                          # create
            {'result': {'url': 'https://example.com', 'navigation': ''}},  # navigate
        ]
        new_tab = await firefox_tab.new_tab('https://example.com')
        assert new_tab.context_id == 'ctx-new'
        assert mock_bidi_handler.execute_command.call_count == 2

    @pytest.mark.asyncio
    async def test_close_sends_close_command(self, firefox_tab, mock_bidi_handler):
        await firefox_tab.close()
        cmd = mock_bidi_handler.execute_command.call_args[0][0]
        assert cmd['method'] == 'browsingContext.close'
        assert cmd['params']['context'] == 'ctx-1'


# ---------------------------------------------------------------------------
# Firefox (binary detection) tests
# ---------------------------------------------------------------------------

class TestFirefoxBinaryDetection:
    def test_unsupported_os_raises(self):
        with patch('platform.system', return_value='SunOS'):
            with pytest.raises(UnsupportedOS):
                Firefox._get_default_binary_location()

    def test_linux_binary_found(self):
        with (
            patch('platform.system', return_value='Linux'),
            patch('pydoll.browser.firefox.firefox.validate_browser_paths', return_value='/usr/bin/firefox'),
        ):
            path = Firefox._get_default_binary_location()
        assert path == '/usr/bin/firefox'

    def test_darwin_binary_found(self):
        with (
            patch('platform.system', return_value='Darwin'),
            patch(
                'pydoll.browser.firefox.firefox.validate_browser_paths',
                return_value='/Applications/Firefox.app/Contents/MacOS/firefox',
            ),
        ):
            path = Firefox._get_default_binary_location()
        assert 'firefox' in path.lower()

    def test_windows_binary_found(self):
        with (
            patch('platform.system', return_value='Windows'),
            patch(
                'pydoll.browser.firefox.firefox.validate_browser_paths',
                return_value=r'C:\Program Files\Mozilla Firefox\firefox.exe',
            ),
        ):
            path = Firefox._get_default_binary_location()
        assert 'firefox.exe' in path.lower()

    def test_invalid_port_raises(self):
        with pytest.raises(InvalidConnectionPort):
            Firefox(connection_port=-1)


# ---------------------------------------------------------------------------
# FirefoxBrowser lifecycle tests
# ---------------------------------------------------------------------------

class TestFirefoxBrowserLifecycle:
    @pytest.mark.asyncio
    async def test_start_returns_tab(self, mock_firefox, mock_bidi_handler):
        mock_bidi_handler.ping.return_value = True
        mock_bidi_handler.execute_command.return_value = {
            'result': {'contexts': [{'context': 'ctx-1', 'url': 'about:blank'}]}
        }
        tab = await mock_firefox.start()
        assert isinstance(tab, FirefoxTab)
        assert tab.context_id == 'ctx-1'

    @pytest.mark.asyncio
    async def test_start_failure_raises(self, mock_firefox, mock_bidi_handler):
        mock_bidi_handler.ping.return_value = False
        with patch('pydoll.browser.firefox.base.asyncio.sleep', new=AsyncMock()):
            with pytest.raises(FailedToStartBrowser):
                await mock_firefox.start()

    @pytest.mark.asyncio
    async def test_start_no_contexts_raises(self, mock_firefox, mock_bidi_handler):
        mock_bidi_handler.ping.return_value = True
        mock_bidi_handler.execute_command.return_value = {'result': {'contexts': []}}
        with pytest.raises(FailedToStartBrowser):
            await mock_firefox.start()

    @pytest.mark.asyncio
    async def test_stop_calls_process_stop(self, mock_firefox, mock_bidi_handler):
        mock_bidi_handler.ping.return_value = True
        await mock_firefox.stop()
        mock_firefox._browser_process_manager.stop_process.assert_called_once()
        mock_bidi_handler.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_raises_when_not_running(self, mock_firefox, mock_bidi_handler):
        mock_bidi_handler.ping.return_value = False
        with patch('pydoll.browser.firefox.base.asyncio.sleep', new=AsyncMock()):
            with pytest.raises(BrowserNotRunning):
                await mock_firefox.stop()

    @pytest.mark.asyncio
    async def test_new_tab(self, mock_firefox, mock_bidi_handler):
        mock_bidi_handler.execute_command.return_value = {'result': {'context': 'ctx-2'}}
        tab = await mock_firefox.new_tab()
        assert isinstance(tab, FirefoxTab)
        assert tab.context_id == 'ctx-2'

    @pytest.mark.asyncio
    async def test_new_tab_with_url(self, mock_firefox, mock_bidi_handler):
        mock_bidi_handler.execute_command.side_effect = [
            {'result': {'context': 'ctx-2'}},
            {'result': {'url': 'https://example.com', 'navigation': ''}},
        ]
        tab = await mock_firefox.new_tab('https://example.com')
        assert tab.context_id == 'ctx-2'
        assert mock_bidi_handler.execute_command.call_count == 2

    @pytest.mark.asyncio
    async def test_get_opened_tabs(self, mock_firefox, mock_bidi_handler):
        mock_bidi_handler.execute_command.return_value = {
            'result': {
                'contexts': [
                    {'context': 'ctx-1', 'url': 'about:blank'},
                    {'context': 'ctx-2', 'url': 'https://example.com'},
                ]
            }
        }
        tabs = await mock_firefox.get_opened_tabs()
        assert len(tabs) == 2
        assert all(isinstance(t, FirefoxTab) for t in tabs)
        assert tabs[0].context_id == 'ctx-1'
        assert tabs[1].context_id == 'ctx-2'

    @pytest.mark.asyncio
    async def test_get_opened_tabs_reuses_existing(self, mock_firefox, mock_bidi_handler):
        existing = FirefoxTab('ctx-1', mock_bidi_handler)
        mock_firefox._tabs['ctx-1'] = existing
        mock_bidi_handler.execute_command.return_value = {
            'result': {'contexts': [{'context': 'ctx-1', 'url': 'about:blank'}]}
        }
        tabs = await mock_firefox.get_opened_tabs()
        assert tabs[0] is existing

    @pytest.mark.asyncio
    async def test_on_browser_level_subscribes(self, mock_firefox, mock_bidi_handler):
        callback = AsyncMock()
        mock_bidi_handler.register_callback.return_value = 10
        cb_id = await mock_firefox.on('browsingContext.load', callback)
        assert cb_id == 10
        sub_cmd = mock_bidi_handler.execute_command.call_args[0][0]
        assert sub_cmd['method'] == 'session.subscribe'

    @pytest.mark.asyncio
    async def test_context_manager_stops_on_exit(self, mock_firefox, mock_bidi_handler):
        mock_bidi_handler.ping.return_value = True
        async with mock_firefox:
            pass
        mock_firefox._browser_process_manager.stop_process.assert_called_once()


# ---------------------------------------------------------------------------
# FirefoxElement tests
# ---------------------------------------------------------------------------

class TestFirefoxElement:
    def test_shared_id_property(self, firefox_element):
        assert firefox_element.shared_id == 'shared-1'

    def test_node_property(self, firefox_element):
        assert firefox_element.node['sharedId'] == 'shared-1'
        assert firefox_element.node['type'] == 'node'

    def test_repr(self, firefox_element):
        assert 'shared-1' in repr(firefox_element)

    # --- click ---

    @pytest.mark.asyncio
    async def test_click_sends_perform_actions(self, firefox_element, mock_bidi_handler):
        await firefox_element.click()
        mock_bidi_handler.execute_command.assert_called_once()
        cmd = mock_bidi_handler.execute_command.call_args[0][0]
        assert cmd['method'] == 'input.performActions'
        assert cmd['params']['context'] == 'ctx-1'

    @pytest.mark.asyncio
    async def test_click_uses_element_origin(self, firefox_element, mock_bidi_handler):
        await firefox_element.click()
        cmd = mock_bidi_handler.execute_command.call_args[0][0]
        pointer_group = cmd['params']['actions'][0]
        assert pointer_group['type'] == 'pointer'
        assert pointer_group['parameters'] == {'pointerType': 'mouse'}
        actions = pointer_group['actions']
        assert actions[0]['type'] == 'pointerMove'
        assert actions[0]['origin'] == {
            'type': 'element',
            'element': {'sharedId': 'shared-1'},
        }
        assert actions[1] == {'type': 'pointerDown', 'button': 0}
        assert actions[2] == {'type': 'pointerUp', 'button': 0}

    # --- hover ---

    @pytest.mark.asyncio
    async def test_hover_sends_only_pointer_move(self, firefox_element, mock_bidi_handler):
        await firefox_element.hover()
        cmd = mock_bidi_handler.execute_command.call_args[0][0]
        assert cmd['method'] == 'input.performActions'
        actions = cmd['params']['actions'][0]['actions']
        assert len(actions) == 1
        assert actions[0]['type'] == 'pointerMove'
        assert actions[0]['origin']['element']['sharedId'] == 'shared-1'

    # --- type ---

    @pytest.mark.asyncio
    async def test_type_calls_click_then_key_actions(self, firefox_element, mock_bidi_handler):
        await firefox_element.type('ab', clear_first=False)
        # First call: click; second call: key actions
        assert mock_bidi_handler.execute_command.call_count == 2
        key_cmd = mock_bidi_handler.execute_command.call_args_list[1][0][0]
        assert key_cmd['method'] == 'input.performActions'
        assert key_cmd['params']['actions'][0]['type'] == 'key'

    @pytest.mark.asyncio
    async def test_type_sends_chars_as_key_pairs(self, firefox_element, mock_bidi_handler):
        await firefox_element.type('hi', clear_first=False)
        key_cmd = mock_bidi_handler.execute_command.call_args_list[1][0][0]
        actions = key_cmd['params']['actions'][0]['actions']
        assert actions == [
            {'type': 'keyDown', 'value': 'h'},
            {'type': 'keyUp', 'value': 'h'},
            {'type': 'keyDown', 'value': 'i'},
            {'type': 'keyUp', 'value': 'i'},
        ]

    @pytest.mark.asyncio
    async def test_type_with_clear_prepends_select_all_delete(self, firefox_element, mock_bidi_handler):
        await firefox_element.type('x', clear_first=True)
        key_cmd = mock_bidi_handler.execute_command.call_args_list[1][0][0]
        actions = key_cmd['params']['actions'][0]['actions']
        # First 6 actions are the clear sequence
        assert actions[0] == {'type': 'keyDown', 'value': KEYS['ctrl']}
        assert actions[1] == {'type': 'keyDown', 'value': 'a'}
        assert actions[2] == {'type': 'keyUp', 'value': 'a'}
        assert actions[3] == {'type': 'keyUp', 'value': KEYS['ctrl']}
        assert actions[4] == {'type': 'keyDown', 'value': KEYS['delete']}
        assert actions[5] == {'type': 'keyUp', 'value': KEYS['delete']}
        # Then the typed character
        assert actions[6] == {'type': 'keyDown', 'value': 'x'}
        assert actions[7] == {'type': 'keyUp', 'value': 'x'}

    @pytest.mark.asyncio
    async def test_type_empty_string_still_clicks(self, firefox_element, mock_bidi_handler):
        await firefox_element.type('', clear_first=False)
        assert mock_bidi_handler.execute_command.call_count == 2
        key_cmd = mock_bidi_handler.execute_command.call_args_list[1][0][0]
        actions = key_cmd['params']['actions'][0]['actions']
        assert actions == []

    # --- press_key ---

    @pytest.mark.asyncio
    async def test_press_key_named_key(self, firefox_element, mock_bidi_handler):
        await firefox_element.press_key('enter')
        cmd = mock_bidi_handler.execute_command.call_args[0][0]
        assert cmd['method'] == 'input.performActions'
        actions = cmd['params']['actions'][0]['actions']
        assert actions == [
            {'type': 'keyDown', 'value': KEYS['enter']},
            {'type': 'keyUp', 'value': KEYS['enter']},
        ]

    @pytest.mark.asyncio
    async def test_press_key_escape(self, firefox_element, mock_bidi_handler):
        await firefox_element.press_key('escape')
        cmd = mock_bidi_handler.execute_command.call_args[0][0]
        actions = cmd['params']['actions'][0]['actions']
        assert actions[0]['value'] == KEYS['escape']

    @pytest.mark.asyncio
    async def test_press_key_single_char(self, firefox_element, mock_bidi_handler):
        await firefox_element.press_key('a')
        cmd = mock_bidi_handler.execute_command.call_args[0][0]
        actions = cmd['params']['actions'][0]['actions']
        assert actions == [
            {'type': 'keyDown', 'value': 'a'},
            {'type': 'keyUp', 'value': 'a'},
        ]

    @pytest.mark.asyncio
    async def test_press_key_unknown_falls_back_to_value(self, firefox_element, mock_bidi_handler):
        await firefox_element.press_key('Q')
        cmd = mock_bidi_handler.execute_command.call_args[0][0]
        actions = cmd['params']['actions'][0]['actions']
        assert actions[0]['value'] == 'Q'

    # --- get_attribute ---

    @pytest.mark.asyncio
    async def test_get_attribute_sends_call_function(self, firefox_element, mock_bidi_handler):
        mock_bidi_handler.execute_command.return_value = {
            'result': {'result': {'type': 'string', 'value': 'https://example.com'}, 'realm': 'r'}
        }
        result = await firefox_element.get_attribute('href')
        cmd = mock_bidi_handler.execute_command.call_args[0][0]
        assert cmd['method'] == 'script.callFunction'
        assert cmd['params']['functionDeclaration'] == '(el) => el.getAttribute("href")'
        assert cmd['params']['arguments'] == [{'sharedId': 'shared-1'}]
        assert cmd['params']['target']['context'] == 'ctx-1'
        assert result == 'https://example.com'

    @pytest.mark.asyncio
    async def test_get_attribute_returns_none_when_missing(self, firefox_element, mock_bidi_handler):
        mock_bidi_handler.execute_command.return_value = {
            'result': {'result': {'type': 'null'}, 'realm': 'r'}
        }
        result = await firefox_element.get_attribute('data-missing')
        assert result is None

    # --- get_property ---

    @pytest.mark.asyncio
    async def test_get_property_sends_call_function(self, firefox_element, mock_bidi_handler):
        mock_bidi_handler.execute_command.return_value = {
            'result': {'result': {'type': 'string', 'value': 'typed text'}, 'realm': 'r'}
        }
        result = await firefox_element.get_property('value')
        cmd = mock_bidi_handler.execute_command.call_args[0][0]
        assert cmd['method'] == 'script.callFunction'
        assert cmd['params']['functionDeclaration'] == '(el) => el["value"]'
        assert result == 'typed text'

    @pytest.mark.asyncio
    async def test_get_property_boolean(self, firefox_element, mock_bidi_handler):
        mock_bidi_handler.execute_command.return_value = {
            'result': {'result': {'type': 'boolean', 'value': True}, 'realm': 'r'}
        }
        result = await firefox_element.get_property('checked')
        assert result is True

    # --- text ---

    @pytest.mark.asyncio
    async def test_text_uses_inner_text(self, firefox_element, mock_bidi_handler):
        mock_bidi_handler.execute_command.return_value = {
            'result': {'result': {'type': 'string', 'value': 'Hello world'}, 'realm': 'r'}
        }
        result = await firefox_element.text
        cmd = mock_bidi_handler.execute_command.call_args[0][0]
        assert cmd['params']['functionDeclaration'] == '(el) => el.innerText'
        assert result == 'Hello world'

    @pytest.mark.asyncio
    async def test_text_returns_empty_string_when_none(self, firefox_element, mock_bidi_handler):
        mock_bidi_handler.execute_command.return_value = {
            'result': {'result': {'type': 'null'}, 'realm': 'r'}
        }
        result = await firefox_element.text
        assert result == ''

    # --- inner_html ---

    @pytest.mark.asyncio
    async def test_inner_html_uses_inner_html(self, firefox_element, mock_bidi_handler):
        mock_bidi_handler.execute_command.return_value = {
            'result': {'result': {'type': 'string', 'value': '<span>hi</span>'}, 'realm': 'r'}
        }
        result = await firefox_element.inner_html
        cmd = mock_bidi_handler.execute_command.call_args[0][0]
        assert cmd['params']['functionDeclaration'] == '(el) => el.innerHTML'
        assert result == '<span>hi</span>'

    @pytest.mark.asyncio
    async def test_inner_html_returns_empty_string_when_none(self, firefox_element, mock_bidi_handler):
        mock_bidi_handler.execute_command.return_value = {
            'result': {'result': {'type': 'null'}, 'realm': 'r'}
        }
        result = await firefox_element.inner_html
        assert result == ''
