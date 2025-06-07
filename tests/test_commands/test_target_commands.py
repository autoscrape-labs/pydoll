"""
Tests for TargetCommands class.

This module contains comprehensive tests for all TargetCommands methods,
verifying that they generate the correct CDP commands with proper parameters.
"""

from pydoll.commands.target_commands import TargetCommands
from pydoll.constants import WindowState
from pydoll.protocol.target.methods import TargetMethod


def test_activate_target():
    """Test activate_target method."""
    result = TargetCommands.activate_target(target_id='target123')
    assert result['method'] == TargetMethod.ACTIVATE_TARGET
    assert result['params']['targetId'] == 'target123'


def test_attach_to_target_minimal():
    """Test attach_to_target with minimal parameters."""
    result = TargetCommands.attach_to_target(target_id='target456')
    assert result['method'] == TargetMethod.ATTACH_TO_TARGET
    assert result['params']['targetId'] == 'target456'


def test_attach_to_target_with_flatten():
    """Test attach_to_target with flatten parameter."""
    result = TargetCommands.attach_to_target(target_id='target456', flatten=True)
    assert result['method'] == TargetMethod.ATTACH_TO_TARGET
    assert result['params']['targetId'] == 'target456'
    assert result['params']['flatten'] is True


def test_close_target():
    """Test close_target method."""
    result = TargetCommands.close_target(target_id='target789')
    assert result['method'] == TargetMethod.CLOSE_TARGET
    assert result['params']['targetId'] == 'target789'


def test_create_browser_context_minimal():
    """Test create_browser_context with minimal parameters."""
    result = TargetCommands.create_browser_context()
    assert result['method'] == TargetMethod.CREATE_BROWSER_CONTEXT
    assert result['params'] == {}


def test_create_browser_context_with_all_params():
    """Test create_browser_context with all parameters."""
    origins = ['https://example.com', 'https://test.com']
    result = TargetCommands.create_browser_context(
        dispose_on_detach=True,
        proxy_server='socks5://192.168.1.100:1080',
        proxy_bypass_list='*.example.com,localhost',
        origins_with_universal_network_access=origins
    )
    assert result['method'] == TargetMethod.CREATE_BROWSER_CONTEXT
    assert result['params']['disposeOnDetach'] is True
    assert result['params']['proxyServer'] == 'socks5://192.168.1.100:1080'
    assert result['params']['proxyBypassList'] == '*.example.com,localhost'
    assert result['params']['originsWithUniversalNetworkAccess'] == origins


def test_create_target_minimal():
    """Test create_target with minimal parameters."""
    result = TargetCommands.create_target(url='https://example.com')
    assert result['method'] == TargetMethod.CREATE_TARGET
    assert result['params']['url'] == 'https://example.com'


def test_create_target_with_position_and_size():
    """Test create_target with position and size parameters."""
    result = TargetCommands.create_target(
        url='https://test.com',
        left=100,
        top=200,
        width=800,
        height=600
    )
    assert result['method'] == TargetMethod.CREATE_TARGET
    assert result['params']['url'] == 'https://test.com'
    assert result['params']['left'] == 100
    assert result['params']['top'] == 200
    assert result['params']['width'] == 800
    assert result['params']['height'] == 600


def test_create_target_with_window_state():
    """Test create_target with window state."""
    result = TargetCommands.create_target(
        url='https://example.com',
        window_state=WindowState.MAXIMIZED
    )
    assert result['method'] == TargetMethod.CREATE_TARGET
    assert result['params']['url'] == 'https://example.com'
    assert result['params']['windowState'] == WindowState.MAXIMIZED


def test_create_target_with_all_params():
    """Test create_target with all parameters."""
    result = TargetCommands.create_target(
        url='https://full-test.com',
        left=50,
        top=100,
        width=1200,
        height=800,
        window_state=WindowState.NORMAL,
        browser_context_id='context123',
        enable_begin_frame_control=True,
        new_window=False,
        background=True,
        for_tab=False,
        hidden=True
    )
    assert result['method'] == TargetMethod.CREATE_TARGET
    assert result['params']['url'] == 'https://full-test.com'
    assert result['params']['left'] == 50
    assert result['params']['top'] == 100
    assert result['params']['width'] == 1200
    assert result['params']['height'] == 800
    assert result['params']['windowState'] == WindowState.NORMAL
    assert result['params']['browserContextId'] == 'context123'
    assert result['params']['enableBeginFrameControl'] is True
    assert result['params']['newWindow'] is False
    assert result['params']['background'] is True
    assert result['params']['forTab'] is False
    assert result['params']['hidden'] is True


def test_detach_from_target_minimal():
    """Test detach_from_target with minimal parameters."""
    result = TargetCommands.detach_from_target()
    assert result['method'] == TargetMethod.DETACH_FROM_TARGET
    assert result['params'] == {}


def test_detach_from_target_with_session():
    """Test detach_from_target with session ID."""
    result = TargetCommands.detach_from_target(session_id='session123')
    assert result['method'] == TargetMethod.DETACH_FROM_TARGET
    assert result['params']['sessionId'] == 'session123'


def test_dispose_browser_context():
    """Test dispose_browser_context method."""
    result = TargetCommands.dispose_browser_context(browser_context_id='context456')
    assert result['method'] == TargetMethod.DISPOSE_BROWSER_CONTEXT
    assert result['params']['browserContextId'] == 'context456'


def test_get_browser_contexts():
    """Test get_browser_contexts method."""
    result = TargetCommands.get_browser_contexts()
    assert result['method'] == TargetMethod.GET_BROWSER_CONTEXTS
    assert result['params'] == {}


def test_get_targets_minimal():
    """Test get_targets with minimal parameters."""
    result = TargetCommands.get_targets()
    assert result['method'] == TargetMethod.GET_TARGETS
    assert result['params'] == {}


def test_get_targets_with_filter():
    """Test get_targets with filter parameter."""
    filter_list = [{'type': 'page'}, {'type': 'worker'}]
    result = TargetCommands.get_targets(filter=filter_list)
    assert result['method'] == TargetMethod.GET_TARGETS
    assert result['params']['filter'] == filter_list


def test_set_auto_attach_minimal():
    """Test set_auto_attach with minimal parameters."""
    result = TargetCommands.set_auto_attach(auto_attach=True)
    assert result['method'] == TargetMethod.SET_AUTO_ATTACH
    assert result['params']['autoAttach'] is True


def test_set_auto_attach_with_all_params():
    """Test set_auto_attach with all parameters."""
    filter_list = [{'type': 'page'}]
    result = TargetCommands.set_auto_attach(
        auto_attach=False,
        wait_for_debugger_on_start=True,
        flatten=False,
        filter=filter_list
    )
    assert result['method'] == TargetMethod.SET_AUTO_ATTACH
    assert result['params']['autoAttach'] is False
    assert result['params']['waitForDebuggerOnStart'] is True
    assert result['params']['flatten'] is False
    assert result['params']['filter'] == filter_list


def test_set_discover_targets_minimal():
    """Test set_discover_targets with minimal parameters."""
    result = TargetCommands.set_discover_targets(discover=True)
    assert result['method'] == TargetMethod.SET_DISCOVER_TARGETS
    assert result['params']['discover'] is True


def test_set_discover_targets_with_filter():
    """Test set_discover_targets with filter parameter."""
    filter_list = [{'type': 'service_worker'}]
    result = TargetCommands.set_discover_targets(discover=False, filter=filter_list)
    assert result['method'] == TargetMethod.SET_DISCOVER_TARGETS
    assert result['params']['discover'] is False
    assert result['params']['filter'] == filter_list


def test_attach_to_browser_target():
    """Test attach_to_browser_target method."""
    result = TargetCommands.attach_to_browser_target(session_id='browser_session123')
    assert result['method'] == TargetMethod.ATTACH_TO_BROWSER_TARGET
    assert result['params']['sessionId'] == 'browser_session123'


def test_get_target_info():
    """Test get_target_info method."""
    result = TargetCommands.get_target_info(target_id='info_target123')
    assert result['method'] == TargetMethod.GET_TARGET_INFO
    assert result['params']['targetId'] == 'info_target123'


def test_set_remote_locations():
    """Test set_remote_locations method."""
    locations = [
        {
            'host': 'remote1.example.com',
            'port': 9222
        },
        {
            'host': 'remote2.example.com',
            'port': 9223
        }
    ]
    result = TargetCommands.set_remote_locations(locations=locations)
    assert result['method'] == TargetMethod.SET_REMOTE_LOCATIONS
    assert result['params']['locations'] == locations


def test_create_target_about_blank():
    """Test create_target with about:blank URL."""
    result = TargetCommands.create_target(url='')
    assert result['method'] == TargetMethod.CREATE_TARGET
    assert result['params']['url'] == ''


def test_create_target_new_window():
    """Test create_target with new window option."""
    result = TargetCommands.create_target(
        url='https://newwindow.com',
        new_window=True,
        width=1024,
        height=768
    )
    assert result['method'] == TargetMethod.CREATE_TARGET
    assert result['params']['url'] == 'https://newwindow.com'
    assert result['params']['newWindow'] is True
    assert result['params']['width'] == 1024
    assert result['params']['height'] == 768


def test_create_target_background():
    """Test create_target with background option."""
    result = TargetCommands.create_target(
        url='https://background.com',
        background=True
    )
    assert result['method'] == TargetMethod.CREATE_TARGET
    assert result['params']['url'] == 'https://background.com'
    assert result['params']['background'] is True


def test_create_target_for_tab():
    """Test create_target with for_tab option."""
    result = TargetCommands.create_target(
        url='https://tab.com',
        for_tab=True
    )
    assert result['method'] == TargetMethod.CREATE_TARGET
    assert result['params']['url'] == 'https://tab.com'
    assert result['params']['forTab'] is True


def test_create_target_hidden():
    """Test create_target with hidden option."""
    result = TargetCommands.create_target(
        url='https://hidden.com',
        hidden=True
    )
    assert result['method'] == TargetMethod.CREATE_TARGET
    assert result['params']['url'] == 'https://hidden.com'
    assert result['params']['hidden'] is True


def test_create_browser_context_with_proxy():
    """Test create_browser_context with proxy configuration."""
    result = TargetCommands.create_browser_context(
        proxy_server='http://proxy.example.com:8080',
        proxy_bypass_list='localhost,127.0.0.1'
    )
    assert result['method'] == TargetMethod.CREATE_BROWSER_CONTEXT
    assert result['params']['proxyServer'] == 'http://proxy.example.com:8080'
    assert result['params']['proxyBypassList'] == 'localhost,127.0.0.1'


def test_create_target_with_context():
    """Test create_target with browser context."""
    result = TargetCommands.create_target(
        url='https://context-test.com',
        browser_context_id='isolated_context'
    )
    assert result['method'] == TargetMethod.CREATE_TARGET
    assert result['params']['url'] == 'https://context-test.com'
    assert result['params']['browserContextId'] == 'isolated_context'


def test_set_auto_attach_disabled():
    """Test set_auto_attach with auto attach disabled."""
    result = TargetCommands.set_auto_attach(
        auto_attach=False,
        wait_for_debugger_on_start=False
    )
    assert result['method'] == TargetMethod.SET_AUTO_ATTACH
    assert result['params']['autoAttach'] is False
    assert result['params']['waitForDebuggerOnStart'] is False
