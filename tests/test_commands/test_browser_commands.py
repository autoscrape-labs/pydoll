from pydoll.commands.browser_commands import BrowserCommands
from pydoll.protocol.cdp.browser.methods import BrowserMethod
from pydoll.protocol.cdp.browser.types import (
    WindowState, 
    PermissionType, 
    DownloadBehavior,
    BrowserCommandId,
    PermissionDescriptor,
    PermissionSetting,
    PrivacySandboxAPI
)


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
    command = BrowserCommands.set_download_behavior(
        behavior=behavior,
        events_enabled=True,
    )
    
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
        download_path=download_path,
        events_enabled=True,
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


# Tests for new/missing methods

def test_get_browser_command_line():
    """Test get_browser_command_line command generation."""
    command = BrowserCommands.get_browser_command_line()
    
    assert command['method'] == BrowserMethod.GET_BROWSER_COMMAND_LINE
    assert 'params' not in command


def test_get_histograms_minimal():
    """Test get_histograms with minimal parameters."""
    command = BrowserCommands.get_histograms()
    
    assert command['method'] == BrowserMethod.GET_HISTOGRAMS
    assert command['params'] == {}


def test_get_histograms_with_query():
    """Test get_histograms with query parameter."""
    query = "Memory"
    command = BrowserCommands.get_histograms(query=query)
    
    assert command['method'] == BrowserMethod.GET_HISTOGRAMS
    assert command['params']['query'] == query
    assert 'delta' not in command['params']


def test_get_histograms_with_delta():
    """Test get_histograms with delta parameter."""
    command = BrowserCommands.get_histograms(delta=True)
    
    assert command['method'] == BrowserMethod.GET_HISTOGRAMS
    assert command['params']['delta'] is True
    assert 'query' not in command['params']


def test_get_histograms_with_all_params():
    """Test get_histograms with all parameters."""
    query = "Network"
    delta = True
    command = BrowserCommands.get_histograms(query=query, delta=delta)
    
    assert command['method'] == BrowserMethod.GET_HISTOGRAMS
    assert command['params']['query'] == query
    assert command['params']['delta'] == delta


def test_get_histogram_minimal():
    """Test get_histogram with minimal parameters."""
    name = "Memory.Browser.TotalPMF"
    command = BrowserCommands.get_histogram(name=name)
    
    assert command['method'] == BrowserMethod.GET_HISTOGRAM
    assert command['params']['name'] == name
    assert 'delta' not in command['params']


def test_get_histogram_with_delta():
    """Test get_histogram with delta parameter."""
    name = "PageLoad.Timing.NavigationStart"
    delta = True
    command = BrowserCommands.get_histogram(name=name, delta=delta)
    
    assert command['method'] == BrowserMethod.GET_HISTOGRAM
    assert command['params']['name'] == name
    assert command['params']['delta'] == delta


def test_get_window_bounds():
    """Test get_window_bounds command generation."""
    window_id = 42
    command = BrowserCommands.get_window_bounds(window_id=window_id)
    
    assert command['method'] == BrowserMethod.GET_WINDOW_BOUNDS
    assert command['params']['windowId'] == window_id


def test_set_contents_size_with_width_only():
    """Test set_contents_size with width only."""
    window_id = 1
    width = 1920
    command = BrowserCommands.set_contents_size(window_id=window_id, width=width)
    
    assert command['method'] == BrowserMethod.SET_CONTENTS_SIZE
    assert command['params']['windowId'] == window_id
    assert command['params']['width'] == width
    assert 'height' not in command['params']


def test_set_contents_size_with_height_only():
    """Test set_contents_size with height only."""
    window_id = 2
    height = 1080
    command = BrowserCommands.set_contents_size(window_id=window_id, height=height)
    
    assert command['method'] == BrowserMethod.SET_CONTENTS_SIZE
    assert command['params']['windowId'] == window_id
    assert command['params']['height'] == height
    assert 'width' not in command['params']


def test_set_contents_size_with_both_dimensions():
    """Test set_contents_size with both width and height."""
    window_id = 3
    width = 1600
    height = 900
    command = BrowserCommands.set_contents_size(
        window_id=window_id, 
        width=width, 
        height=height
    )
    
    assert command['method'] == BrowserMethod.SET_CONTENTS_SIZE
    assert command['params']['windowId'] == window_id
    assert command['params']['width'] == width
    assert command['params']['height'] == height


def test_set_dock_tile_minimal():
    """Test set_dock_tile with no parameters."""
    command = BrowserCommands.set_dock_tile()
    
    assert command['method'] == BrowserMethod.SET_DOCK_TILE
    assert command['params'] == {}


def test_set_dock_tile_with_badge_label():
    """Test set_dock_tile with badge label."""
    badge_label = "5"
    command = BrowserCommands.set_dock_tile(badge_label=badge_label)
    
    assert command['method'] == BrowserMethod.SET_DOCK_TILE
    assert command['params']['badgeLabel'] == badge_label
    assert 'image' not in command['params']


def test_set_dock_tile_with_image():
    """Test set_dock_tile with image."""
    image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAGAz"
    command = BrowserCommands.set_dock_tile(image=image)
    
    assert command['method'] == BrowserMethod.SET_DOCK_TILE
    assert command['params']['image'] == image
    assert 'badgeLabel' not in command['params']


def test_set_dock_tile_with_all_params():
    """Test set_dock_tile with all parameters."""
    badge_label = "3"
    image = "base64encodedimage"
    command = BrowserCommands.set_dock_tile(badge_label=badge_label, image=image)
    
    assert command['method'] == BrowserMethod.SET_DOCK_TILE
    assert command['params']['badgeLabel'] == badge_label
    assert command['params']['image'] == image


def test_execute_browser_command():
    """Test execute_browser_command command generation."""
    command_id = BrowserCommandId.OPEN_TAB_SEARCH
    command = BrowserCommands.execute_browser_command(command_id=command_id)
    
    assert command['method'] == BrowserMethod.EXECUTE_BROWSER_COMMAND
    assert command['params']['commandId'] == command_id


def test_add_privacy_sandbox_enrollment_override():
    """Test add_privacy_sandbox_enrollment_override command generation."""
    url = "https://example.test"
    command = BrowserCommands.add_privacy_sandbox_enrollment_override(url=url)
    
    assert command['method'] == BrowserMethod.ADD_PRIVACY_SANDBOX_ENROLLMENT_OVERRIDE
    assert command['params']['url'] == url


def test_add_privacy_sandbox_coordinator_key_config_minimal():
    """Test add_privacy_sandbox_coordinator_key_config with minimal parameters."""
    api = PrivacySandboxAPI.BIDDING_AND_AUCTION_SERVICES
    coordinator_origin = "https://coordinator.test"
    key_config = "test-key-config"
    
    command = BrowserCommands.add_privacy_sandbox_coordinator_key_config(
        api=api,
        coordinator_origin=coordinator_origin,
        key_config=key_config
    )
    
    assert command['method'] == BrowserMethod.ADD_PRIVACY_SANDBOX_COORDINATOR_KEY_CONFIG
    assert command['params']['api'] == api
    assert command['params']['coordinatorOrigin'] == coordinator_origin
    assert command['params']['keyConfig'] == key_config
    assert 'browserContextId' not in command['params']


def test_add_privacy_sandbox_coordinator_key_config_with_context():
    """Test add_privacy_sandbox_coordinator_key_config with browser context."""
    api = PrivacySandboxAPI.TRUSTED_KEY_VALUE
    coordinator_origin = "https://sandbox.test" 
    key_config = "config-data"
    browser_context_id = "test-context"
    
    command = BrowserCommands.add_privacy_sandbox_coordinator_key_config(
        api=api,
        coordinator_origin=coordinator_origin,
        key_config=key_config,
        browser_context_id=browser_context_id
    )
    
    assert command['method'] == BrowserMethod.ADD_PRIVACY_SANDBOX_COORDINATOR_KEY_CONFIG
    assert command['params']['api'] == api
    assert command['params']['coordinatorOrigin'] == coordinator_origin
    assert command['params']['keyConfig'] == key_config
    assert command['params']['browserContextId'] == browser_context_id


def test_set_permission_minimal():
    """Test set_permission with minimal parameters."""
    permission = PermissionDescriptor(name=PermissionType.GEOLOCATION)
    setting = PermissionSetting.GRANTED
    
    command = BrowserCommands.set_permission(
        permission=permission,
        setting=setting
    )
    
    assert command['method'] == BrowserMethod.SET_PERMISSION
    assert command['params']['permission'] == permission
    assert command['params']['setting'] == setting
    assert 'origin' not in command['params']
    assert 'browserContextId' not in command['params']


def test_set_permission_with_origin():
    """Test set_permission with origin."""
    permission = PermissionDescriptor(name=PermissionType.NOTIFICATIONS)
    setting = PermissionSetting.DENIED
    origin = "https://example.com"
    
    command = BrowserCommands.set_permission(
        permission=permission,
        setting=setting,
        origin=origin
    )
    
    assert command['method'] == BrowserMethod.SET_PERMISSION
    assert command['params']['permission'] == permission
    assert command['params']['setting'] == setting
    assert command['params']['origin'] == origin
    assert 'browserContextId' not in command['params']


def test_set_permission_with_all_params():
    """Test set_permission with all parameters."""
    permission = PermissionDescriptor(name=PermissionType.MIDI)
    setting = PermissionSetting.PROMPT
    origin = "https://test.example.com"
    browser_context_id = "permission-context"
    
    command = BrowserCommands.set_permission(
        permission=permission,
        setting=setting,
        origin=origin,
        browser_context_id=browser_context_id
    )
    
    assert command['method'] == BrowserMethod.SET_PERMISSION
    assert command['params']['permission'] == permission
    assert command['params']['setting'] == setting
    assert command['params']['origin'] == origin
    assert command['params']['browserContextId'] == browser_context_id


def test_set_window_fullscreen():
    """Test set_window_fullscreen command generation."""
    window_id = 7
    command = BrowserCommands.set_window_fullscreen(window_id=window_id)
    
    assert command['method'] == BrowserMethod.SET_WINDOW_BOUNDS
    assert command['params']['windowId'] == window_id
    assert command['params']['bounds']['windowState'] == WindowState.FULLSCREEN


def test_set_window_normal():
    """Test set_window_normal command generation."""
    window_id = 8
    command = BrowserCommands.set_window_normal(window_id=window_id)
    
    assert command['method'] == BrowserMethod.SET_WINDOW_BOUNDS
    assert command['params']['windowId'] == window_id
    assert command['params']['bounds']['windowState'] == WindowState.NORMAL


# Additional edge case and integration tests

def test_all_window_state_helpers():
    """Test all window state helper methods."""
    window_id = 99
    
    # Test all window state helpers return correct commands
    maximized = BrowserCommands.set_window_maximized(window_id)
    minimized = BrowserCommands.set_window_minimized(window_id)
    fullscreen = BrowserCommands.set_window_fullscreen(window_id)
    normal = BrowserCommands.set_window_normal(window_id)
    
    # All should use the same method
    for command in [maximized, minimized, fullscreen, normal]:
        assert command['method'] == BrowserMethod.SET_WINDOW_BOUNDS
        assert command['params']['windowId'] == window_id
    
    # Check specific states
    assert maximized['params']['bounds']['windowState'] == WindowState.MAXIMIZED
    assert minimized['params']['bounds']['windowState'] == WindowState.MINIMIZED
    assert fullscreen['params']['bounds']['windowState'] == WindowState.FULLSCREEN
    assert normal['params']['bounds']['windowState'] == WindowState.NORMAL


def test_privacy_sandbox_apis():
    """Test privacy sandbox with different API types."""
    coordinator_origin = "https://api.test"
    key_config = "test-config"
    
    # Test BIDDING_AND_AUCTION_SERVICES API
    bidding_cmd = BrowserCommands.add_privacy_sandbox_coordinator_key_config(
        api=PrivacySandboxAPI.BIDDING_AND_AUCTION_SERVICES,
        coordinator_origin=coordinator_origin,
        key_config=key_config
    )
    assert bidding_cmd['params']['api'] == PrivacySandboxAPI.BIDDING_AND_AUCTION_SERVICES
    
    # Test TRUSTED_KEY_VALUE API  
    trusted_key_cmd = BrowserCommands.add_privacy_sandbox_coordinator_key_config(
        api=PrivacySandboxAPI.TRUSTED_KEY_VALUE,
        coordinator_origin=coordinator_origin,
        key_config=key_config
    )
    assert trusted_key_cmd['params']['api'] == PrivacySandboxAPI.TRUSTED_KEY_VALUE


def test_permission_settings_variations():
    """Test set_permission with different permission settings."""
    permission = PermissionDescriptor(name=PermissionType.GEOLOCATION)
    
    # Test GRANTED setting
    granted_cmd = BrowserCommands.set_permission(permission, PermissionSetting.GRANTED)
    assert granted_cmd['params']['setting'] == PermissionSetting.GRANTED
    
    # Test DENIED setting
    denied_cmd = BrowserCommands.set_permission(permission, PermissionSetting.DENIED)
    assert denied_cmd['params']['setting'] == PermissionSetting.DENIED
    
    # Test PROMPT setting
    prompt_cmd = BrowserCommands.set_permission(permission, PermissionSetting.PROMPT)
    assert prompt_cmd['params']['setting'] == PermissionSetting.PROMPT


def test_browser_command_ids():
    """Test execute_browser_command with different command IDs."""
    # Test different browser command IDs
    tab_search_cmd = BrowserCommands.execute_browser_command(BrowserCommandId.OPEN_TAB_SEARCH)
    assert tab_search_cmd['params']['commandId'] == BrowserCommandId.OPEN_TAB_SEARCH
