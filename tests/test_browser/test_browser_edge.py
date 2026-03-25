import platform
from unittest.mock import MagicMock, patch

import pytest

from pydoll.browser.chromium.edge import Edge
from pydoll.browser.chromium.options import ChromiumOptionsManager
from pydoll.browser.chromium.options import ChromiumOptions
from pydoll.exceptions import UnsupportedOS, InvalidBrowserPath, InvalidConnectionPort


class TestEdgeInitialization:
    """Tests for Edge class initialization."""

    def test_edge_initialization_default_options(self):
        """Test Edge initialization with default options."""
        with patch.multiple(
            Edge,
            _get_default_binary_location=MagicMock(return_value='/fake/edge'),
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
            edge = Edge()
            
            assert isinstance(edge.options, ChromiumOptions)
            assert edge._connection_port in range(9223, 9323)

    def test_edge_initialization_custom_options(self):
        """Test Edge initialization with custom options."""
        custom_options = ChromiumOptions()
        custom_options.add_argument('--disable-web-security')
        custom_options.binary_location = '/custom/edge/path'
        
        with patch.multiple(
            Edge,
            _get_default_binary_location=MagicMock(return_value='/fake/edge'),
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
            edge = Edge(options=custom_options)
            
            assert edge.options == custom_options
            assert '--disable-web-security' in edge.options.arguments
            assert edge.options.binary_location == '/custom/edge/path'

    def test_edge_initialization_custom_port(self):
        """Test Edge initialization with custom port."""
        custom_port = 9999
        
        with patch.multiple(
            Edge,
            _get_default_binary_location=MagicMock(return_value='/fake/edge'),
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
            edge = Edge(connection_port=custom_port)
            
            assert edge._connection_port == custom_port

    def test_edge_initialization_both_custom(self):
        """Test Edge initialization with both custom options and port."""
        custom_options = ChromiumOptions()
        custom_options.add_argument('--headless')
        custom_port = 8888
        
        with patch.multiple(
            Edge,
            _get_default_binary_location=MagicMock(return_value='/fake/edge'),
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
            edge = Edge(options=custom_options, connection_port=custom_port)
            
            assert edge.options == custom_options
            assert edge._connection_port == custom_port
            assert '--headless' in edge.options.arguments


class TestEdgeDefaultBinaryLocation:
    """Tests for Edge default binary location detection."""

    @pytest.mark.parametrize(
        'os_name, expected_paths',
        [
            (
                'Windows',
                [
                    r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
                    r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
                ]
            ),
            (
                'Linux',
                ['/usr/bin/microsoft-edge']
            ),
            (
                'Darwin',
                ['/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge']
            ),
        ],
    )
    @patch('pydoll.browser.chromium.edge.validate_browser_paths')
    @patch('platform.system')
    def test_get_default_binary_location_success(
        self, mock_platform_system, mock_validate_browser_paths, os_name, expected_paths
    ):
        """Test successful default binary detection for different operating systems."""
        mock_platform_system.return_value = os_name
        expected_path = expected_paths[0]  # First path in the list
        mock_validate_browser_paths.return_value = expected_path
        
        result = Edge._get_default_binary_location()
        
        mock_platform_system.assert_called_once()
        mock_validate_browser_paths.assert_called_once_with(expected_paths)
        assert result == expected_path

    @patch('platform.system')
    def test_get_default_binary_location_unsupported_os(self, mock_platform_system):
        """Test exception for unsupported operating system."""
        mock_platform_system.return_value = 'FreeBSD'
        
        with pytest.raises(UnsupportedOS):
            Edge._get_default_binary_location()

    @patch('platform.system')
    def test_get_default_binary_location_unknown_os(self, mock_platform_system):
        """Test exception for unknown operating system."""
        mock_platform_system.return_value = 'UnknownOS'
        
        with pytest.raises(UnsupportedOS):
            Edge._get_default_binary_location()

    @patch('pydoll.browser.chromium.edge.validate_browser_paths')
    @patch('platform.system')
    def test_get_default_binary_location_validation_error(
        self, mock_platform_system, mock_validate_browser_paths
    ):
        """Test when path validation fails."""
        mock_platform_system.return_value = 'Linux'
        mock_validate_browser_paths.side_effect = InvalidBrowserPath('Edge executable not found')
        
        with pytest.raises(InvalidBrowserPath, match='Edge executable not found'):
            Edge._get_default_binary_location()

    @patch('pydoll.browser.chromium.edge.validate_browser_paths')
    @patch('platform.system')
    def test_get_default_binary_location_windows_fallback(
        self, mock_platform_system, mock_validate_browser_paths
    ):
        """Test fallback for different paths on Windows."""
        mock_platform_system.return_value = 'Windows'
        expected_path = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
        mock_validate_browser_paths.return_value = expected_path
        
        result = Edge._get_default_binary_location()
        
        expected_paths = [
            r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
            r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
        ]
        mock_validate_browser_paths.assert_called_once_with(expected_paths)
        assert result == expected_path

    @patch('pydoll.browser.chromium.edge.validate_browser_paths')
    @patch('platform.system')
    def test_get_default_binary_location_linux_path(
        self, mock_platform_system, mock_validate_browser_paths
    ):
        """Test Linux-specific Edge path."""
        mock_platform_system.return_value = 'Linux'
        expected_path = '/usr/bin/microsoft-edge'
        mock_validate_browser_paths.return_value = expected_path
        
        result = Edge._get_default_binary_location()
        
        mock_validate_browser_paths.assert_called_once_with(['/usr/bin/microsoft-edge'])
        assert result == expected_path

    @patch('pydoll.browser.chromium.edge.validate_browser_paths')
    @patch('platform.system')
    def test_get_default_binary_location_macos_path(
        self, mock_platform_system, mock_validate_browser_paths
    ):
        """Test macOS-specific Edge path."""
        mock_platform_system.return_value = 'Darwin'
        expected_path = '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge'
        mock_validate_browser_paths.return_value = expected_path
        
        result = Edge._get_default_binary_location()
        
        mock_validate_browser_paths.assert_called_once_with([expected_path])
        assert result == expected_path


class TestEdgeOptionsManager:
    """Tests for ChromiumOptionsManager integration."""

    def test_options_manager_creation(self):
        """Test options manager creation."""
        custom_options = ChromiumOptions()
        custom_options.add_argument('--no-sandbox')
        
        with patch.multiple(
            Edge,
            _get_default_binary_location=MagicMock(return_value='/fake/edge'),
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
            edge = Edge(options=custom_options)
            
            # Verify that options were configured correctly
            assert edge.options == custom_options
            assert '--no-sandbox' in edge.options.arguments

    def test_options_manager_with_none_options(self):
        """Test options manager creation with None options."""
        with patch.multiple(
            Edge,
            _get_default_binary_location=MagicMock(return_value='/fake/edge'),
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
            edge = Edge(options=None)
            
            # Verify that default options were created
            assert isinstance(edge.options, ChromiumOptions)


class TestEdgeInheritance:
    """Tests to verify correct inheritance from Browser class."""

    def test_edge_inherits_from_browser(self):
        """Test if Edge correctly inherits from Browser."""
        from pydoll.browser.chromium.base import Browser
        
        with patch.multiple(
            Edge,
            _get_default_binary_location=MagicMock(return_value='/fake/edge'),
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
            edge = Edge()
            
            assert isinstance(edge, Browser)
            assert hasattr(edge, 'start')
            assert hasattr(edge, 'stop')
            assert hasattr(edge, 'new_tab')

    def test_edge_overrides_get_default_binary_location(self):
        """Test if Edge overrides the _get_default_binary_location method."""
        # Verify that the method is static and exists
        assert hasattr(Edge, '_get_default_binary_location')
        assert callable(Edge._get_default_binary_location)
        
        # Verify that it's different from the base implementation
        from pydoll.browser.chromium.base import Browser
        assert Edge._get_default_binary_location != Browser._get_default_binary_location

    def test_edge_uses_chromium_options_manager(self):
        """Test if Edge uses ChromiumOptionsManager like Chrome."""
        with patch.multiple(
            Edge,
            _get_default_binary_location=MagicMock(return_value='/fake/edge'),
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
            edge = Edge()
            
            # Edge should use the same options type as Chrome since it's Chromium-based
            assert isinstance(edge.options, ChromiumOptions)


class TestEdgeEdgeCases:
    """Tests for edge cases and special situations."""

    def test_edge_with_empty_options(self):
        """Test Edge with empty options."""
        empty_options = ChromiumOptions()
        
        with patch.multiple(
            Edge,
            _get_default_binary_location=MagicMock(return_value='/fake/edge'),
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
            edge = Edge(options=empty_options)
            
            assert edge.options == empty_options
            assert len(edge.options.arguments) >= 0  # May have default arguments

    def test_edge_with_zero_port(self):
        """Test Edge with zero port (should generate random port since 0 is falsy)."""
        with patch.multiple(
            Edge,
            _get_default_binary_location=MagicMock(return_value='/fake/edge'),
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
            edge = Edge(connection_port=0)
            
            # Port 0 is falsy, so should generate a random port
            assert edge._connection_port in range(9223, 9323)

    def test_edge_with_negative_port(self):
        """Test Edge with negative port (should raise InvalidConnectionPort)."""
        with patch.multiple(
            Edge,
            _get_default_binary_location=MagicMock(return_value='/fake/edge'),
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
                Edge(connection_port=-1)

    def test_edge_with_edge_specific_arguments(self):
        """Test Edge with Edge-specific command line arguments."""
        custom_options = ChromiumOptions()
        custom_options.add_argument('--enable-features=msEdgeEnhancedSecurity')
        custom_options.add_argument('--edge-webview-enable-builtin-background-extensions')
        
        with patch.multiple(
            Edge,
            _get_default_binary_location=MagicMock(return_value='/fake/edge'),
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
            edge = Edge(options=custom_options)
            
            assert '--enable-features=msEdgeEnhancedSecurity' in edge.options.arguments
            assert '--edge-webview-enable-builtin-background-extensions' in edge.options.arguments


class TestEdgeIntegration:
    """Integration tests to verify components working together."""

    def test_edge_full_initialization_flow(self):
        """Test complete Edge initialization flow."""
        custom_options = ChromiumOptions()
        custom_options.add_argument('--disable-gpu')
        custom_options.add_argument('--no-sandbox')
        custom_options.binary_location = '/custom/edge'
        custom_port = 9876
        
        with patch.multiple(
            Edge,
            _get_default_binary_location=MagicMock(return_value='/fake/edge'),
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
            
            edge = Edge(options=custom_options, connection_port=custom_port)
            
            # Verify correct initialization
            assert edge.options == custom_options
            assert edge._connection_port == custom_port
            assert '--disable-gpu' in edge.options.arguments
            assert '--no-sandbox' in edge.options.arguments
            assert edge.options.binary_location == '/custom/edge'
            
            # Verify that managers were created
            assert edge._browser_process_manager is not None
            assert edge._temp_directory_manager is not None
            assert edge._connection_handler is not None
            assert edge._proxy_manager is not None

    def test_edge_options_initialization_flow(self):
        """Test Edge options initialization flow."""
        with patch.multiple(
            Edge,
            _get_default_binary_location=MagicMock(return_value='/fake/edge'),
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
            edge = Edge(options=None)
            assert isinstance(edge.options, ChromiumOptions)
            
            # Test with custom options
            custom_options = ChromiumOptions()
            custom_options.add_argument('--test-arg')
            edge2 = Edge(options=custom_options)
            assert edge2.options == custom_options
            assert '--test-arg' in edge2.options.arguments

    def test_edge_vs_chrome_compatibility(self):
        """Test that Edge and Chrome use compatible interfaces."""
        from pydoll.browser.chromium.chrome import Chrome
        
        with patch.multiple(
            Edge,
            _get_default_binary_location=MagicMock(return_value='/fake/edge'),
        ), patch.multiple(
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
            edge = Edge()
            chrome = Chrome()
            
            # Both should have the same interface
            assert type(edge.options) == type(chrome.options)
            assert hasattr(edge, 'start') and hasattr(chrome, 'start')
            assert hasattr(edge, 'stop') and hasattr(chrome, 'stop')
            assert hasattr(edge, 'new_tab') and hasattr(chrome, 'new_tab')
