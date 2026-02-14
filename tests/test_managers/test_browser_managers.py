from unittest.mock import MagicMock, Mock, patch, ANY

import pytest

from pydoll.browser.managers import (
    ChromiumOptionsManager,
    BrowserProcessManager,
    ProxyManager,
    TempDirectoryManager,
)
from pydoll.browser.options import ChromiumOptions as Options
from pydoll.exceptions import InvalidOptionsObject


@pytest.fixture
def proxy_options():
    return Options()


@pytest.fixture
def temp_manager():
    mock_dir = MagicMock()
    mock_dir.name = '/fake/temp/dir'
    return TempDirectoryManager(temp_dir_factory=lambda: mock_dir)


@pytest.fixture
def process_manager():
    mock_creator = Mock(return_value=MagicMock())
    return BrowserProcessManager(process_creator=mock_creator)


@pytest.fixture
def chromium_options_manager(proxy_options):
    options_manager = ChromiumOptionsManager(proxy_options)
    return options_manager


def test_proxy_manager_no_proxy(proxy_options):
    manager = ProxyManager(proxy_options)
    result = manager.get_proxy_credentials()

    assert result[0] is False
    assert result[1] == (None, None)


def test_proxy_manager_with_credentials(proxy_options):
    proxy_options.add_argument('--proxy-server=user:pass@example.com')
    manager = ProxyManager(proxy_options)
    result = manager.get_proxy_credentials()

    assert result[0] is True
    assert result[1] == ('user', 'pass')
    assert proxy_options.arguments == ['--proxy-server=example.com']


def test_proxy_manager_invalid_credentials_format(proxy_options):
    proxy_options.add_argument('--proxy-server=invalidformat@example.com')
    manager = ProxyManager(proxy_options)
    result = manager.get_proxy_credentials()

    assert result[0] is False
    assert result[1] == (None, None)
    assert proxy_options.arguments == [
        '--proxy-server=invalidformat@example.com'
    ]


def test_proxy_manager_with_scheme_http(proxy_options):
    proxy_options.add_argument('--proxy-server=http://user:pass@proxy.local:8080')
    manager = ProxyManager(proxy_options)
    result = manager.get_proxy_credentials()

    assert result[0] is True
    assert result[1] == ('user', 'pass')
    assert proxy_options.arguments == ['--proxy-server=http://proxy.local:8080']


def test_proxy_manager_with_scheme_socks(proxy_options):
    proxy_options.add_argument('--proxy-server=socks5://alice:pwd@1.2.3.4:1080')
    manager = ProxyManager(proxy_options)
    result = manager.get_proxy_credentials()

    assert result[0] is True
    assert result[1] == ('alice', 'pwd')
    assert proxy_options.arguments == ['--proxy-server=socks5://1.2.3.4:1080']


def test_proxy_manager_invalid_proxy_format(proxy_options):
    proxy_options.add_argument('--proxy-server=invalidformat')
    manager = ProxyManager(proxy_options)
    result = manager.get_proxy_credentials()

    assert result[0] is False
    assert result[1] == (None, None)


def test_start_browser_process(process_manager):
    binary = '/fake/path/browser'
    port = 9222
    args = ['--test-arg']

    process_manager.start_browser_process(binary, port, args)

    expected_command = [binary, f'--remote-debugging-port={port}', *args]
    process_manager._process_creator.assert_called_once_with(expected_command)
    assert process_manager._process is not None


def test_stop_process(process_manager):
    mock_process = MagicMock()
    process_manager._process = mock_process

    process_manager.stop_process()

    mock_process.terminate.assert_called_once()


def test_create_temp_dir(temp_manager):
    temp_dir = temp_manager.create_temp_dir()

    assert len(temp_manager._temp_dirs) == 1
    assert temp_dir.name == '/fake/temp/dir'


def test_cleanup_temp_dirs(temp_manager):
    mock_dir1 = MagicMock()
    mock_dir2 = MagicMock()
    temp_manager._temp_dirs = [mock_dir1, mock_dir2]

    with patch('shutil.rmtree') as mock_rmtree:
        temp_manager.cleanup()

        assert mock_rmtree.call_count == 2
        mock_rmtree.assert_any_call(mock_dir1.name, onerror=ANY)
        mock_rmtree.assert_any_call(mock_dir2.name, onerror=ANY)


def test_retry_process_file(temp_manager):
    mock_func = Mock()

    # retry success
    success_at = 5
    mock_func.side_effect = [PermissionError] * (success_at - 1) + [None]
    temp_manager.retry_process_file(mock_func, "/test/path", retry_times=success_at)
    assert mock_func.call_count == success_at
    
    # exceed max retries
    mock_func.reset_mock()
    mock_func.side_effect = PermissionError
    with pytest.raises(PermissionError):
        temp_manager.retry_process_file(mock_func, "/test/path", retry_times=3)
    assert mock_func.call_count == 3

    # infinite_retries
    mock_func.reset_mock()
    mock_func.side_effect = [PermissionError] * 9 + [None]
    temp_manager.retry_process_file(mock_func, "/test/path", retry_times=-1)
    assert mock_func.call_count == 10


def test_handle_cleanup_error(temp_manager):
    func_mock = Mock()

    # matched permission error
    temp_manager.retry_process_file = Mock()
    path = "/tmp/CrashpadMetrics-active.pma"

    temp_manager.handle_cleanup_error(func_mock, path, (PermissionError, PermissionError(), None))
    temp_manager.retry_process_file.assert_called_once_with(func_mock, path)

    # matched permission error - should not raise, only log and continue
    temp_manager.retry_process_file = Mock()
    temp_manager.retry_process_file.side_effect = PermissionError
    path = "/tmp/CrashpadMetrics-active.pma"
    temp_manager.handle_cleanup_error(func_mock, path, (PermissionError, PermissionError(), None))

    # unmatched permission error
    temp_manager.retry_process_file = Mock()
    path = "/tmp/test.file"
    exc = PermissionError("Access denied")

    with pytest.raises(PermissionError) as e:
        temp_manager.handle_cleanup_error(func_mock, path, (PermissionError, exc, None))
    assert e.value is exc

    # pass OSError
    temp_manager.handle_cleanup_error(func_mock, "/tmp/path", (OSError, OSError(), None))

    # raise other Exception
    exc = ValueError("Test")
    with pytest.raises(ValueError) as e:
        temp_manager.handle_cleanup_error(func_mock, "/tmp/path", (ValueError, exc, None))
    assert e.value is exc


def test_initialize_options_with_none(chromium_options_manager):
    result = chromium_options_manager.initialize_options()

    assert isinstance(result, Options)
    assert result.arguments == ['--no-first-run', '--no-default-browser-check']


def test_initialize_options_with_valid_options():
    options = Options()
    options.add_argument('--test')
    chromium_options_manager = ChromiumOptionsManager(options)
    result = chromium_options_manager.initialize_options()

    assert result is options
    assert '--test' in result.arguments


def test_initialize_options_with_invalid_type():
    chromium_options_manager = ChromiumOptionsManager('invalid options object')
    with pytest.raises(InvalidOptionsObject):
        chromium_options_manager.initialize_options()


def test_add_default_arguments():
    options = Options()
    chromium_options_manager = ChromiumOptionsManager(options)
    chromium_options_manager.add_default_arguments()

    assert '--no-first-run' in options.arguments
    assert '--no-default-browser-check' in options.arguments



def test_initialize_options_creates_new_instance():
    manager = ChromiumOptionsManager(None)
    result = manager.initialize_options()
    assert isinstance(result, Options)
    assert '--no-first-run' in result.arguments
    assert '--no-default-browser-check' in result.arguments


def test_initialize_options_preserves_custom_arguments():
    options = Options()
    options.add_argument('--custom-flag')
    manager = ChromiumOptionsManager(options)
    result = manager.initialize_options()
    assert '--custom-flag' in result.arguments
    assert '--no-first-run' in result.arguments
    assert '--no-default-browser-check' in result.arguments
