from pydoll.protocol.commands import BrowserCommands


def test_close():
    expected_command = {'method': 'Browser.close'}
    assert BrowserCommands.close() == expected_command


def test_get_window_id():
    expected_command = {'method': 'Browser.WindowID'}
    assert BrowserCommands.get_window_id() == expected_command


def test_set_download_path():
    path = '/path/to/download'
    expected_command = {
        'method': 'Browser.setDownloadBehavior',
        'params': {'behavior': 'allow', 'downloadPath': path},
    }
    assert BrowserCommands.set_download_path(path) == expected_command


def test_set_window_bounds():
    window_id = 1
    bounds = {'width': 800, 'height': 600}
    expected_command = {
        'method': 'Browser.setWindowBounds',
        'params': {'windowId': window_id, 'bounds': bounds},
    }
    assert (
        BrowserCommands.set_window_bounds(window_id, bounds)
        == expected_command
    )


def test_set_window_maximized():
    window_id = 1
    expected_command = {
        'method': 'Browser.setWindowBounds',
        'params': {
            'windowId': window_id,
            'bounds': {'windowState': 'maximized'},
        },
    }
    assert BrowserCommands.set_window_maximized(window_id) == expected_command


def test_set_window_minimized():
    window_id = 1
    expected_command = {
        'method': 'Browser.setWindowBounds',
        'params': {
            'windowId': window_id,
            'bounds': {'windowState': 'minimized'},
        },
    }
    assert BrowserCommands.set_window_minimized(window_id) == expected_command
