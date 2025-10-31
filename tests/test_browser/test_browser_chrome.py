import json
import os
from unittest.mock import MagicMock, patch

import pytest

from pydoll.browser.chromium.chrome import Chrome
from pydoll.browser.options import ChromiumOptions
from pydoll.exceptions import InvalidBrowserPath, UnsupportedOS, InvalidConnectionPort


class TestChromeInitialization:
    """Tests for Chrome class initialization."""

    def test_chrome_initialization_default_options(self):
        """Test Chrome initialization with default options."""
        with patch.multiple(
            Chrome,
            _get_default_binary_location=MagicMock(return_value='/fake/chrome'),
        ), patch(
            'pydoll.browser.managers.browser_process_manager.BrowserProcessManager',
            autospec=True,
        ), patch(
            'pydoll.browser.managers.temp_dir_manager.TempDirectoryManager',
            autospec=True,
        ), patch(
            'pydoll.connection.connection_handler.ConnectionHandler',
            autospec=True,
        ), patch(
            'pydoll.browser.managers.proxy_manager.ProxyManager',
            autospec=True,
        ):
            chrome = Chrome()
            
            assert isinstance(chrome.options, ChromiumOptions)
            assert chrome._connection_port in range(9223, 9323)

    def test_chrome_initialization_custom_options(self):
        """Test Chrome initialization with custom options."""
        custom_options = ChromiumOptions()
        custom_options.add_argument('--disable-web-security')
        custom_options.binary_location = '/custom/chrome/path'
        
        with patch.multiple(
            Chrome,
            _get_default_binary_location=MagicMock(return_value='/fake/chrome'),
        ), patch(
            'pydoll.browser.managers.browser_process_manager.BrowserProcessManager',
            autospec=True,
        ), patch(
            'pydoll.browser.managers.temp_dir_manager.TempDirectoryManager',
            autospec=True,
        ), patch(
            'pydoll.connection.connection_handler.ConnectionHandler',
            autospec=True,
        ), patch(
            'pydoll.browser.managers.proxy_manager.ProxyManager',
            autospec=True,
        ):
            chrome = Chrome(options=custom_options)
            
            assert chrome.options == custom_options
            assert '--disable-web-security' in chrome.options.arguments
            assert chrome.options.binary_location == '/custom/chrome/path'

    def test_chrome_initialization_custom_port(self):
        """Test Chrome initialization with custom port."""
        custom_port = 9999
        
        with patch.multiple(
            Chrome,
            _get_default_binary_location=MagicMock(return_value='/fake/chrome'),
        ), patch(
            'pydoll.browser.managers.browser_process_manager.BrowserProcessManager',
            autospec=True,
        ), patch(
            'pydoll.browser.managers.temp_dir_manager.TempDirectoryManager',
            autospec=True,
        ), patch(
            'pydoll.connection.connection_handler.ConnectionHandler',
            autospec=True,
        ), patch(
            'pydoll.browser.managers.proxy_manager.ProxyManager',
            autospec=True,
        ):
            chrome = Chrome(connection_port=custom_port)
            
            assert chrome._connection_port == custom_port

    def test_chrome_initialization_both_custom(self):
        """Test Chrome initialization with both custom options and port."""
        custom_options = ChromiumOptions()
        custom_options.add_argument('--headless')
        custom_port = 8888
        
        with patch.multiple(
            Chrome,
            _get_default_binary_location=MagicMock(return_value='/fake/chrome'),
        ), patch(
            'pydoll.browser.managers.browser_process_manager.BrowserProcessManager',
            autospec=True,
        ), patch(
            'pydoll.browser.managers.temp_dir_manager.TempDirectoryManager',
            autospec=True,
        ), patch(
            'pydoll.connection.connection_handler.ConnectionHandler',
            autospec=True,
        ), patch(
            'pydoll.browser.managers.proxy_manager.ProxyManager',
            autospec=True,
        ):
            chrome = Chrome(options=custom_options, connection_port=custom_port)
            
            assert chrome.options == custom_options
            assert chrome._connection_port == custom_port
            assert '--headless' in chrome.options.arguments


class TestChromeDefaultBinaryLocation:
    """Tests for Chrome default binary location detection."""

    @pytest.mark.parametrize(
        'os_name, expected_paths',
        [
            (
                'Windows',
                [
                    r'C:\Program Files\Google\Chrome\Application\chrome.exe',
                    r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
                ]
            ),
            (
                'Linux',
                ['/usr/bin/google-chrome', '/usr/bin/google-chrome-stable', '/usr/bin/chromium', '/usr/bin/chromium-browser']
            ),
            (
                'Darwin',
                ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome']
            ),
        ],
    )
    @patch('pydoll.browser.chromium.chrome.validate_browser_paths')
    @patch('platform.system')
    def test_get_default_binary_location_success(
        self, mock_platform_system, mock_validate_browser_paths, os_name, expected_paths
    ):
        """Test successful default binary detection for different operating systems."""
        mock_platform_system.return_value = os_name
        expected_path = expected_paths[0]  # First path in the list
        mock_validate_browser_paths.return_value = expected_path
        
        result = Chrome._get_default_binary_location()
        
        mock_platform_system.assert_called_once()
        mock_validate_browser_paths.assert_called_once_with(expected_paths)
        assert result == expected_path

    @patch('platform.system')
    def test_get_default_binary_location_unsupported_os(self, mock_platform_system):
        """Test exception for unsupported operating system."""
        mock_platform_system.return_value = 'FreeBSD'
        
        with pytest.raises(UnsupportedOS, match='Unsupported OS: FreeBSD'):
            Chrome._get_default_binary_location()

    @patch('platform.system')
    def test_get_default_binary_location_unknown_os(self, mock_platform_system):
        """Test exception for unknown operating system."""
        mock_platform_system.return_value = 'UnknownOS'
        
        with pytest.raises(UnsupportedOS, match='Unsupported OS: UnknownOS'):
            Chrome._get_default_binary_location()

    @patch('pydoll.browser.chromium.chrome.validate_browser_paths')
    @patch('platform.system')
    def test_get_default_binary_location_validation_error(
        self, mock_platform_system, mock_validate_browser_paths
    ):
        """Test when path validation fails."""
        mock_platform_system.return_value = 'Linux'
        mock_validate_browser_paths.side_effect = InvalidBrowserPath('Chrome executable not found')
        
        with pytest.raises(InvalidBrowserPath, match='Chrome executable not found'):
            Chrome._get_default_binary_location()

    @patch('pydoll.browser.chromium.chrome.validate_browser_paths')
    @patch('platform.system')
    def test_get_default_binary_location_windows_fallback(
        self, mock_platform_system, mock_validate_browser_paths
    ):
        """Test fallback for different paths on Windows."""
        mock_platform_system.return_value = 'Windows'
        expected_path = r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'
        mock_validate_browser_paths.return_value = expected_path
        
        result = Chrome._get_default_binary_location()
        
        expected_paths = [
            r'C:\Program Files\Google\Chrome\Application\chrome.exe',
            r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
        ]
        mock_validate_browser_paths.assert_called_once_with(expected_paths)
        assert result == expected_path


class TestChromeOptionsManager:
    """Tests for ChromiumOptionsManager integration."""

    def test_options_manager_creation(self):
        """Test options manager creation."""
        custom_options = ChromiumOptions()
        custom_options.add_argument('--no-sandbox')
        
        with patch.multiple(
            Chrome,
            _get_default_binary_location=MagicMock(return_value='/fake/chrome'),
        ), patch(
            'pydoll.browser.managers.browser_process_manager.BrowserProcessManager',
            autospec=True,
        ), patch(
            'pydoll.browser.managers.temp_dir_manager.TempDirectoryManager',
            autospec=True,
        ), patch(
            'pydoll.connection.connection_handler.ConnectionHandler',
            autospec=True,
        ), patch(
            'pydoll.browser.managers.proxy_manager.ProxyManager',
            autospec=True,
        ):
            chrome = Chrome(options=custom_options)
            
            # Verify that options were configured correctly
            assert chrome.options == custom_options
            assert '--no-sandbox' in chrome.options.arguments

    def test_options_manager_with_none_options(self):
        """Test options manager creation with None options."""
        with patch.multiple(
            Chrome,
            _get_default_binary_location=MagicMock(return_value='/fake/chrome'),
        ), patch(
            'pydoll.browser.managers.browser_process_manager.BrowserProcessManager',
            autospec=True,
        ), patch(
            'pydoll.browser.managers.temp_dir_manager.TempDirectoryManager',
            autospec=True,
        ), patch(
            'pydoll.connection.connection_handler.ConnectionHandler',
            autospec=True,
        ), patch(
            'pydoll.browser.managers.proxy_manager.ProxyManager',
            autospec=True,
        ):
            chrome = Chrome(options=None)
            
            # Verify that default options were created
            assert isinstance(chrome.options, ChromiumOptions)


class TestChromeInheritance:
    """Tests to verify correct inheritance from Browser class."""

    def test_chrome_inherits_from_browser(self):
        """Test if Chrome correctly inherits from Browser."""
        from pydoll.browser.chromium.base import Browser
        
        with patch.multiple(
            Chrome,
            _get_default_binary_location=MagicMock(return_value='/fake/chrome'),
        ), patch(
            'pydoll.browser.managers.browser_process_manager.BrowserProcessManager',
            autospec=True,
        ), patch(
            'pydoll.browser.managers.temp_dir_manager.TempDirectoryManager',
            autospec=True,
        ), patch(
            'pydoll.connection.connection_handler.ConnectionHandler',
            autospec=True,
        ), patch(
            'pydoll.browser.managers.proxy_manager.ProxyManager',
            autospec=True,
        ):
            chrome = Chrome()
            
            assert isinstance(chrome, Browser)
            assert hasattr(chrome, 'start')
            assert hasattr(chrome, 'stop')
            assert hasattr(chrome, 'new_tab')

    def test_chrome_overrides_get_default_binary_location(self):
        """Test if Chrome overrides the _get_default_binary_location method."""
        # Verify that the method is static and exists
        assert hasattr(Chrome, '_get_default_binary_location')
        assert callable(Chrome._get_default_binary_location)
        
        # Verify that it's different from the base implementation
        from pydoll.browser.chromium.base import Browser
        assert Chrome._get_default_binary_location != Browser._get_default_binary_location


class TestChromeEdgeCases:
    """Tests for edge cases and special situations."""

    def test_chrome_with_empty_options(self):
        """Test Chrome with empty options."""
        empty_options = ChromiumOptions()
        
        with patch.multiple(
            Chrome,
            _get_default_binary_location=MagicMock(return_value='/fake/chrome'),
        ), patch(
            'pydoll.browser.managers.browser_process_manager.BrowserProcessManager',
            autospec=True,
        ), patch(
            'pydoll.browser.managers.temp_dir_manager.TempDirectoryManager',
            autospec=True,
        ), patch(
            'pydoll.connection.connection_handler.ConnectionHandler',
            autospec=True,
        ), patch(
            'pydoll.browser.managers.proxy_manager.ProxyManager',
            autospec=True,
        ):
            chrome = Chrome(options=empty_options)
            
            assert chrome.options == empty_options
            assert len(chrome.options.arguments) >= 0  # May have default arguments

    def test_chrome_with_zero_port(self):
        """Test Chrome with zero port (should generate random port since 0 is falsy)."""
        with patch.multiple(
            Chrome,
            _get_default_binary_location=MagicMock(return_value='/fake/chrome'),
        ), patch(
            'pydoll.browser.managers.browser_process_manager.BrowserProcessManager',
            autospec=True,
        ), patch(
            'pydoll.browser.managers.temp_dir_manager.TempDirectoryManager',
            autospec=True,
        ), patch(
            'pydoll.connection.connection_handler.ConnectionHandler',
            autospec=True,
        ), patch(
            'pydoll.browser.managers.proxy_manager.ProxyManager',
            autospec=True,
        ):
            chrome = Chrome(connection_port=0)
            
            # Port 0 is falsy, so should generate a random port
            assert chrome._connection_port in range(9223, 9323)

    def test_chrome_with_negative_port(self):
        """Test Chrome with negative port (should raise InvalidConnectionPort)."""
        with patch.multiple(
            Chrome,
            _get_default_binary_location=MagicMock(return_value='/fake/chrome'),
        ), patch(
            'pydoll.browser.managers.browser_process_manager.BrowserProcessManager',
            autospec=True,
        ), patch(
            'pydoll.browser.managers.temp_dir_manager.TempDirectoryManager',
            autospec=True,
        ), patch(
            'pydoll.connection.connection_handler.ConnectionHandler',
            autospec=True,
        ), patch(
            'pydoll.browser.managers.proxy_manager.ProxyManager',
            autospec=True,
        ):
            with pytest.raises(InvalidConnectionPort):
                Chrome(connection_port=-1)


class TestChromeIntegration:
    """Integration tests to verify components working together."""

    def test_chrome_full_initialization_flow(self):
        """Test complete Chrome initialization flow."""
        custom_options = ChromiumOptions()
        custom_options.add_argument('--disable-gpu')
        custom_options.add_argument('--no-sandbox')
        custom_options.browser_preferences = {
        "download": {"directory_upgrade": True},
        }
        custom_options.set_default_download_directory('/tmp/all')
        custom_options.block_notifications = True
        custom_options.binary_location = '/custom/chrome'
        custom_port = 9876
        
        with patch.multiple(
            Chrome,
            _get_default_binary_location=MagicMock(return_value='/fake/chrome'),
        ), patch(
            'pydoll.browser.managers.browser_process_manager.BrowserProcessManager',
            autospec=True,
        ) as mock_process_manager, patch(
            'pydoll.browser.managers.temp_dir_manager.TempDirectoryManager',
            autospec=True,
        ) as mock_temp_manager, patch(
            'pydoll.connection.connection_handler.ConnectionHandler',
            autospec=True,
        ) as mock_connection, patch(
            'pydoll.browser.managers.proxy_manager.ProxyManager',
            autospec=True,
        ) as mock_proxy_manager:
            
            chrome = Chrome(options=custom_options, connection_port=custom_port)
            chrome._setup_user_dir()
            with open(
                os.path.join(chrome._temp_directory_manager._temp_dirs[0].name, 'Default', 'Preferences'), 'r'
            ) as json_file:
                preferences = json.loads(json_file.read())
            assert preferences == custom_options.browser_preferences

            # Verify correct initialization
            assert chrome.options == custom_options
            assert chrome._connection_port == custom_port
            assert '--disable-gpu' in chrome.options.arguments
            assert '--no-sandbox' in chrome.options.arguments
            assert chrome.options.binary_location == '/custom/chrome'
            
            # Verify that managers were created
            assert chrome._browser_process_manager is not None
            assert chrome._temp_directory_manager is not None
            assert chrome._connection_handler is not None
            assert chrome._proxy_manager is not None

    def test_chrome_options_initialization_flow(self):
        """Test Chrome options initialization flow."""
        with patch.multiple(
            Chrome,
            _get_default_binary_location=MagicMock(return_value='/fake/chrome'),
        ), patch(
            'pydoll.browser.managers.browser_process_manager.BrowserProcessManager',
            autospec=True,
        ), patch(
            'pydoll.browser.managers.temp_dir_manager.TempDirectoryManager',
            autospec=True,
        ), patch(
            'pydoll.connection.connection_handler.ConnectionHandler',
            autospec=True,
        ), patch(
            'pydoll.browser.managers.proxy_manager.ProxyManager',
            autospec=True,
        ):
            # Test with None options (should create default options)
            chrome = Chrome(options=None)
            assert isinstance(chrome.options, ChromiumOptions)
            
            # Test with custom options
            custom_options = ChromiumOptions()
            custom_options.add_argument('--test-arg')
            chrome2 = Chrome(options=custom_options)
            assert chrome2.options == custom_options
            assert '--test-arg' in chrome2.options.arguments

    @pytest.mark.asyncio
    async def test_chrome_user_data_dir_and_preferences(self, tmp_path):
        """Test Chrome with user data directory and preferences."""
        user_data_dir = tmp_path / 'chrome_profile'
        user_data_dir.mkdir()
        
        prefs_dir = user_data_dir / 'Default'
        prefs_dir.mkdir()
        prefs_file = prefs_dir / 'Preferences'
        
        initial_prefs = {
            'profile': {
                'exit_type': 'Normal',
                'exited_cleanly': True
            },
            'test_pref': 'initial_value'
        }
        
        prefs_file.write_text(json.dumps(initial_prefs), encoding='utf-8')
        
        custom_options = ChromiumOptions()
        custom_options.add_argument(f'--user-data-dir={user_data_dir}')
        custom_options.browser_preferences = {
            'test_pref': 'new_value',
            'new_pref': 'some_value'
        }
        custom_options.prompt_for_download = False # ok
        with patch.multiple(
            Chrome,
            _get_default_binary_location=MagicMock(return_value='/fake/chrome'),
        ), patch(
            'pydoll.browser.managers.browser_process_manager.BrowserProcessManager',
            autospec=True,
        ), patch(
            'pydoll.browser.managers.temp_dir_manager.TempDirectoryManager',
            autospec=True,
        ), patch(
            'pydoll.connection.connection_handler.ConnectionHandler',
            autospec=True,
        ), patch(
            'pydoll.browser.managers.proxy_manager.ProxyManager',
            autospec=True,
        ):
            async with Chrome(options=custom_options) as chrome:
                chrome._setup_user_dir()
                assert f'--user-data-dir={user_data_dir}' in chrome.options.arguments

                with open(prefs_file, 'r', encoding='utf-8') as f:
                    updated_prefs = json.load(f)
                assert updated_prefs['test_pref'] == 'new_value'
                assert updated_prefs['new_pref'] == 'some_value'
                
                assert updated_prefs['profile']['exit_type'] == 'Normal'
                assert updated_prefs['profile']['exited_cleanly'] is True
                backup_file = user_data_dir / 'Default' / 'Preferences.backup'
                assert backup_file.exists()
                with open(backup_file, 'r', encoding='utf-8') as f:
                    backup_prefs = json.load(f)
                assert backup_prefs == initial_prefs
            with open(prefs_file, 'r', encoding='utf-8') as f:
                final_prefs = json.load(f)
            assert final_prefs == initial_prefs

    @pytest.mark.asyncio
    async def test_chrome_user_data_dir_with_invalid_json_preferences(self, tmp_path):
        """Test Chrome with user data directory containing invalid JSON preferences."""
        user_data_dir = tmp_path / 'chrome_profile'
        user_data_dir.mkdir()
        
        prefs_dir = user_data_dir / 'Default'
        prefs_dir.mkdir()
        prefs_file = prefs_dir / 'Preferences'
        
        # Write invalid JSON to the Preferences file
        invalid_json = '{ "profile": { "exit_type": "Normal", "exited_cleanly": true, } }' # trailing comma makes it invalid
        prefs_file.write_text(invalid_json, encoding='utf-8')
        
        custom_options = ChromiumOptions()
        custom_options.add_argument(f'--user-data-dir={user_data_dir}')
        custom_options.browser_preferences = {
            'test_pref': 'new_value',
            'new_pref': 'some_value'
        }
        custom_options.prompt_for_download = False
        
        with patch.multiple(
            Chrome,
            _get_default_binary_location=MagicMock(return_value='/fake/chrome'),
        ), patch(
            'pydoll.browser.managers.browser_process_manager.BrowserProcessManager',
            autospec=True,
        ), patch(
            'pydoll.browser.managers.temp_dir_manager.TempDirectoryManager',
            autospec=True,
        ), patch(
            'pydoll.connection.connection_handler.ConnectionHandler',
            autospec=True,
        ), patch(
            'pydoll.browser.managers.proxy_manager.ProxyManager',
            autospec=True,
        ):
            async with Chrome(options=custom_options) as chrome:
                chrome._setup_user_dir()
                assert f'--user-data-dir={user_data_dir}' in chrome.options.arguments

                # The invalid JSON should be handled gracefully by suppress(json.JSONDecodeError)
                # and the preferences should be written with only the new preferences
                with open(prefs_file, 'r', encoding='utf-8') as f:
                    updated_prefs = json.load(f)
                assert updated_prefs['test_pref'] == 'new_value'
                assert updated_prefs['new_pref'] == 'some_value'
                
                # The original invalid JSON should be backed up
                backup_file = user_data_dir / 'Default' / 'Preferences.backup'
                assert backup_file.exists()
                with open(backup_file, 'r', encoding='utf-8') as f:
                    backup_content = f.read()
                assert backup_content == invalid_json
