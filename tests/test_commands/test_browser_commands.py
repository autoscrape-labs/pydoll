from pydoll.commands.browser_commands import BrowserCommands
from pydoll.constants import DownloadBehavior, PermissionType, WindowState
from pydoll.protocol.browser.methods import BrowserMethod


def test_get_version():
    """Test get_version command generation."""
    command = BrowserCommands.get_version()
    
    assert command['method'] == BrowserMethod.GET_VERSION
    assert 'params' not in command


def test_reset_permissions_without_context():
    """Test reset_permissions command without browser context."""
    command = BrowserCommands.reset_permissions()
    
    assert command['method'] == BrowserMethod.RESET_PERMISSIONS
    assert command['params'] == {}


def test_reset_permissions_with_context():
    """Test reset_permissions command with browser context."""
    browser_context_id = "test-context-123"
    command = BrowserCommands.reset_permissions(browser_context_id=browser_context_id)
    
    assert command['method'] == BrowserMethod.RESET_PERMISSIONS
    assert command['params']['browserContextId'] == browser_context_id


def test_cancel_download_minimal():
    """Test cancel_download command with minimal parameters."""
    guid = "download-guid-123"
    command = BrowserCommands.cancel_download(guid=guid)
    
    assert command['method'] == BrowserMethod.CANCEL_DOWNLOAD
    assert command['params']['guid'] == guid
    assert 'browserContextId' not in command['params']


def test_cancel_download_with_context():
    """Test cancel_download command with browser context."""
    guid = "download-guid-456"
    browser_context_id = "test-context-456"
    command = BrowserCommands.cancel_download(
        guid=guid, 
        browser_context_id=browser_context_id
    )
    
    assert command['method'] == BrowserMethod.CANCEL_DOWNLOAD
    assert command['params']['guid'] == guid
    assert command['params']['browserContextId'] == browser_context_id


def test_crash():
    """Test crash command generation."""
    command = BrowserCommands.crash()
    
    assert command['method'] == BrowserMethod.CRASH
    assert 'params' not in command


def test_crash_gpu_process():
    """Test crash_gpu_process command generation."""
    command = BrowserCommands.crash_gpu_process()
    
    assert command['method'] == BrowserMethod.CRASH_GPU_PROCESS
    assert 'params' not in command


def test_set_download_behavior_minimal():
    """Test set_download_behavior with minimal parameters."""
    behavior = DownloadBehavior.ALLOW
    command = BrowserCommands.set_download_behavior(behavior=behavior)
    
    assert command['method'] == BrowserMethod.SET_DOWNLOAD_BEHAVIOR
    assert command['params']['behavior'] == behavior
    assert command['params']['eventsEnabled'] is True
    assert 'downloadPath' not in command['params']
    assert 'browserContextId' not in command['params']


def test_set_download_behavior_with_path():
    """Test set_download_behavior with download path."""
    behavior = DownloadBehavior.ALLOW
    download_path = "/path/to/downloads"
    command = BrowserCommands.set_download_behavior(
        behavior=behavior,
        download_path=download_path
    )
    
    assert command['method'] == BrowserMethod.SET_DOWNLOAD_BEHAVIOR
    assert command['params']['behavior'] == behavior
    assert command['params']['downloadPath'] == download_path
    assert command['params']['eventsEnabled'] is True


def test_set_download_behavior_full_params():
    """Test set_download_behavior with all parameters."""
    behavior = DownloadBehavior.ALLOW_AND_NAME
    download_path = "/custom/download/path"
    browser_context_id = "context-789"
    events_enabled = False
    
    command = BrowserCommands.set_download_behavior(
        behavior=behavior,
        download_path=download_path,
        browser_context_id=browser_context_id,
        events_enabled=events_enabled
    )
    
    assert command['method'] == BrowserMethod.SET_DOWNLOAD_BEHAVIOR
    assert command['params']['behavior'] == behavior
    assert command['params']['downloadPath'] == download_path
    assert command['params']['browserContextId'] == browser_context_id


def test_set_download_behavior_default_behavior():
    """Test set_download_behavior with DEFAULT behavior."""
    behavior = DownloadBehavior.DEFAULT
    command = BrowserCommands.set_download_behavior(behavior=behavior)
    
    assert command['method'] == BrowserMethod.SET_DOWNLOAD_BEHAVIOR
    assert command['params']['behavior'] == behavior


def test_close():
    """Test close command generation."""
    command = BrowserCommands.close()
    
    assert command['method'] == BrowserMethod.CLOSE
    assert 'params' not in command


def test_get_window_for_target():
    """Test get_window_for_target command generation."""
    target_id = "target-123"
    command = BrowserCommands.get_window_for_target(target_id=target_id)
    
    assert command['method'] == BrowserMethod.GET_WINDOW_FOR_TARGET
    assert command['params']['targetId'] == target_id


def test_set_window_bounds():
    """Test set_window_bounds command generation."""
    window_id = 42
    bounds = {
        'width': 1920,
        'height': 1080,
        'x': 100,
        'y': 50,
        'windowState': WindowState.NORMAL
    }
    command = BrowserCommands.set_window_bounds(window_id=window_id, bounds=bounds)
    
    assert command['method'] == BrowserMethod.SET_WINDOW_BOUNDS
    assert command['params']['windowId'] == window_id
    assert command['params']['bounds'] == bounds


def test_set_window_bounds_minimal():
    """Test set_window_bounds with minimal bounds."""
    window_id = 1
    bounds = {'windowState': WindowState.MAXIMIZED}
    command = BrowserCommands.set_window_bounds(window_id=window_id, bounds=bounds)
    
    assert command['method'] == BrowserMethod.SET_WINDOW_BOUNDS
    assert command['params']['windowId'] == window_id
    assert command['params']['bounds'] == bounds


def test_set_window_maximized():
    """Test set_window_maximized command generation."""
    window_id = 5
    command = BrowserCommands.set_window_maximized(window_id=window_id)
    
    assert command['method'] == BrowserMethod.SET_WINDOW_BOUNDS
    assert command['params']['windowId'] == window_id
    assert command['params']['bounds']['windowState'] == WindowState.MAXIMIZED


def test_set_window_minimized():
    """Test set_window_minimized command generation."""
    window_id = 10
    command = BrowserCommands.set_window_minimized(window_id=window_id)
    assert command['method'] == BrowserMethod.SET_WINDOW_BOUNDS
    assert command['params']['windowId'] == window_id
    assert command['params']['bounds']['windowState'] == WindowState.MINIMIZED


def test_grant_permissions_minimal():
    """Test grant_permissions with minimal parameters."""
    permissions = [PermissionType.GEOLOCATION, PermissionType.NOTIFICATIONS]
    command = BrowserCommands.grant_permissions(permissions=permissions)
    
    assert command['method'] == BrowserMethod.GRANT_PERMISSIONS
    assert command['params']['permissions'] == permissions
    assert 'origin' not in command['params']
    assert 'browserContextId' not in command['params']


def test_grant_permissions_with_origin():
    """Test grant_permissions with origin."""
    permissions = [PermissionType.DISPLAY_CAPTURE]
    origin = "https://example.com"
    command = BrowserCommands.grant_permissions(
        permissions=permissions,
        origin=origin
    )
    
    assert command['method'] == BrowserMethod.GRANT_PERMISSIONS
    assert command['params']['permissions'] == permissions
    assert command['params']['origin'] == origin
    assert 'browserContextId' not in command['params']


def test_grant_permissions_full_params():
    """Test grant_permissions with all parameters."""
    permissions = [PermissionType.MIDI, PermissionType.CLIPBOARD_READ_WRITE]
    origin = "https://test.example.com"
    browser_context_id = "context-permissions"
    
    command = BrowserCommands.grant_permissions(
        permissions=permissions,
        origin=origin,
        browser_context_id=browser_context_id
    )
    
    assert command['method'] == BrowserMethod.GRANT_PERMISSIONS
    assert command['params']['permissions'] == permissions
    assert command['params']['origin'] == origin
    assert command['params']['browserContextId'] == browser_context_id


def test_grant_permissions_single_permission():
    """Test grant_permissions with single permission."""
    permissions = [PermissionType.PAYMENT_HANDLER]
    command = BrowserCommands.grant_permissions(permissions=permissions)
    
    assert command['method'] == BrowserMethod.GRANT_PERMISSIONS
    assert command['params']['permissions'] == permissions


def test_grant_permissions_multiple_permissions():
    """Test grant_permissions with multiple permissions."""
    permissions = [
        PermissionType.GEOLOCATION,
        PermissionType.NOTIFICATIONS,
        PermissionType.MIDI
    ]
    command = BrowserCommands.grant_permissions(permissions=permissions)
    
    assert command['method'] == BrowserMethod.GRANT_PERMISSIONS
    assert command['params']['permissions'] == permissions


def test_grant_permissions_empty_list():
    """Test grant_permissions with empty permissions list."""
    permissions = []
    command = BrowserCommands.grant_permissions(permissions=permissions)
    
    assert command['method'] == BrowserMethod.GRANT_PERMISSIONS
    assert command['params']['permissions'] == permissions


# Edge cases and additional coverage tests

def test_window_bounds_with_all_states():
    """Test window bounds with all possible window states."""
    window_id = 1
    
    # Test NORMAL state
    bounds_normal = {'windowState': WindowState.NORMAL}
    command_normal = BrowserCommands.set_window_bounds(window_id, bounds_normal)
    assert command_normal['params']['bounds']['windowState'] == WindowState.NORMAL
    
    # Test MAXIMIZED state
    bounds_max = {'windowState': WindowState.MAXIMIZED}
    command_max = BrowserCommands.set_window_bounds(window_id, bounds_max)
    assert command_max['params']['bounds']['windowState'] == WindowState.MAXIMIZED
    
    # Test MINIMIZED state
    bounds_min = {'windowState': WindowState.MINIMIZED}
    command_min = BrowserCommands.set_window_bounds(window_id, bounds_min)
    assert command_min['params']['bounds']['windowState'] == WindowState.MINIMIZED


def test_download_behaviors():
    """Test all download behavior types."""
    # Test ALLOW
    command_allow = BrowserCommands.set_download_behavior(DownloadBehavior.ALLOW)
    assert command_allow['params']['behavior'] == DownloadBehavior.ALLOW
    
    # Test ALLOW_AND_NAME
    command_allow_name = BrowserCommands.set_download_behavior(DownloadBehavior.ALLOW_AND_NAME)
    assert command_allow_name['params']['behavior'] == DownloadBehavior.ALLOW_AND_NAME
    
    # Test DEFAULT
    command_default = BrowserCommands.set_download_behavior(DownloadBehavior.DEFAULT)
    assert command_default['params']['behavior'] == DownloadBehavior.DEFAULT


def test_events_enabled_variations():
    """Test set_download_behavior with different events_enabled values."""
    behavior = DownloadBehavior.ALLOW
    
    # Test with events_enabled=True (default)
    command_true = BrowserCommands.set_download_behavior(behavior, events_enabled=True)
    assert command_true['params']['eventsEnabled'] is True
    
    # Test with events_enabled=False
    command_false = BrowserCommands.set_download_behavior(behavior, events_enabled=False)
    assert command_false['params'] == {'behavior': behavior, 'eventsEnabled': False}


def test_various_permission_types():
    """Test grant_permissions with various permission types."""
    # Test web-related permissions
    web_permissions = [
        PermissionType.GEOLOCATION,
        PermissionType.NOTIFICATIONS,
    ]
    command_web = BrowserCommands.grant_permissions(web_permissions)
    assert command_web['params']['permissions'] == web_permissions

    # Test storage permissions
    storage_permissions = [
        PermissionType.DURABLE_STORAGE,
        PermissionType.STORAGE_ACCESS
    ]
    command_storage = BrowserCommands.grant_permissions(storage_permissions)
    assert command_storage['params']['permissions'] == storage_permissions
