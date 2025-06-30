"""
Tests to achieve 100% code coverage for fingerprint functionality.
Specifically targets uncovered lines in PR #129.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import pytest

from pydoll.browser.chromium.chrome import Chrome
from pydoll.browser.managers.browser_options_manager import ChromiumOptionsManager
from pydoll.browser.options import ChromiumOptions
from pydoll.fingerprint import (
    FingerprintConfig,
    FingerprintManager,
    FingerprintGenerator,
)


class TestCoverageSpecific:
    """Tests to cover specific uncovered lines."""

    def test_browser_options_apply_fingerprint_spoofing(self):
        """Test _apply_fingerprint_spoofing method - covers browser_options_manager.py#L71"""
        config = FingerprintConfig(browser_type="chrome")
        manager = ChromiumOptionsManager(
            enable_fingerprint_spoofing=True,
            fingerprint_config=config
        )
        
        # Set up options
        manager.options = ChromiumOptions()
        manager.options.binary_location = "/path/to/chrome"
        
        # Ensure fingerprint manager exists and mock its methods
        assert manager.fingerprint_manager is not None
        manager.fingerprint_manager.generate_new_fingerprint = Mock()
        manager.fingerprint_manager.get_fingerprint_arguments = Mock(return_value=[
            '--user-agent=Test Agent'
        ])
        
        # Call the method that contains uncovered line
        manager._apply_fingerprint_spoofing()
        
        # Verify the method was called
        manager.fingerprint_manager.generate_new_fingerprint.assert_called_with('chrome')
        manager.fingerprint_manager.get_fingerprint_arguments.assert_called_with('chrome')

    def test_fingerprint_generator_unique_properties(self):
        """Test _generate_unique_properties - covers generator.py#L335"""
        # This covers the uncovered line in generator.py
        unique_props = FingerprintGenerator._generate_unique_properties()
        
        assert "unique_id" in unique_props
        assert isinstance(unique_props["unique_id"], str)
        assert len(unique_props["unique_id"]) > 0

    def test_fingerprint_manager_get_current_fingerprint_none(self):
        """Test get_current_fingerprint when None - covers manager.py#L55"""
        manager = FingerprintManager()
        
        # Initially should be None - this covers line 55
        current = manager.get_current_fingerprint()
        assert current is None

    def test_fingerprint_manager_delete_nonexistent_file(self):
        """Test delete_fingerprint with nonexistent file - covers manager.py#L262"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = FingerprintConfig()
            manager = FingerprintManager(config)
            manager.storage_dir = Path(temp_dir)
            
            # Try to delete non-existent file - this covers line 262
            result = manager.delete_fingerprint("nonexistent")
            assert result is False

    @pytest.mark.asyncio
    async def test_browser_start_with_fingerprint_injection(self):
        """Test browser.start() with fingerprint injection - covers base.py#L137"""
        with patch('pydoll.browser.chromium.chrome.Chrome._get_default_binary_location'), \
             patch('pydoll.browser.chromium.chrome.Chrome._setup_user_dir'), \
             patch('pydoll.browser.chromium.chrome.Chrome._verify_browser_running'), \
             patch('pydoll.browser.chromium.chrome.Chrome._configure_proxy'), \
             patch('pydoll.browser.chromium.chrome.Chrome._get_valid_tab_id', return_value="test_id"), \
             patch('pydoll.browser.tab.Tab') as mock_tab_class, \
             patch('pydoll.browser.chromium.chrome.Chrome._inject_fingerprint_script') as mock_inject:

            # Create mock tab
            mock_tab = Mock()
            mock_tab._execute_command = AsyncMock()
            mock_tab_class.return_value = mock_tab
            
            # Create Chrome with fingerprint spoofing enabled
            chrome = Chrome(enable_fingerprint_spoofing=True)
            
            # Mock all necessary components
            chrome._browser_process_manager = Mock()
            chrome._browser_process_manager.start_process = Mock()
            chrome._connection_handler = Mock()
            chrome._connection_handler.connect = AsyncMock()
            chrome._execute_command = AsyncMock()
            
            # This should trigger the fingerprint injection on line 137
            await chrome.start()
            
            # Verify fingerprint injection was called (covers line 137)
            mock_inject.assert_called_once()

    @pytest.mark.asyncio
    async def test_browser_new_tab_with_fingerprint_injection(self):
        """Test browser.new_tab() with fingerprint injection - covers base.py#L226"""
        with patch('pydoll.browser.chromium.chrome.Chrome._get_default_binary_location'), \
             patch('pydoll.browser.chromium.chrome.Chrome._setup_user_dir'), \
             patch('pydoll.browser.tab.Tab') as mock_tab_class, \
             patch('pydoll.browser.chromium.chrome.Chrome._inject_fingerprint_script') as mock_inject:

            # Create mock tab
            mock_tab = Mock()
            mock_tab._execute_command = AsyncMock()
            mock_tab_class.return_value = mock_tab
            
            # Create Chrome with fingerprint spoofing enabled
            chrome = Chrome(enable_fingerprint_spoofing=True)
            
            # Mock the execute command to return a valid response
            chrome._execute_command = AsyncMock(return_value={
                'result': {'targetId': 'test_target_id'}
            })
            
            # This should trigger the fingerprint injection on line 226
            await chrome.new_tab(url="https://example.com")
            
            # Verify fingerprint injection was called (covers line 226)
            mock_inject.assert_called_once()

    @pytest.mark.asyncio
    async def test_browser_fingerprint_injection_method_coverage(self):
        """Test the actual _inject_fingerprint_script method to ensure it's covered"""
        with patch('pydoll.browser.chromium.chrome.Chrome._get_default_binary_location'), \
             patch('pydoll.browser.chromium.chrome.Chrome._setup_user_dir'):

            chrome = Chrome(enable_fingerprint_spoofing=True)
            
            # Create mock tab
            mock_tab = Mock()
            mock_tab._execute_command = AsyncMock()
            mock_tab.execute_script = AsyncMock()
            
            # Ensure fingerprint manager exists and mock its method
            assert chrome.fingerprint_manager is not None
            chrome.fingerprint_manager.get_fingerprint_js = Mock(return_value="test_script")
            
            # Call the method directly
            await chrome._inject_fingerprint_script(mock_tab)
            
            # Verify both script injection methods were called
            mock_tab._execute_command.assert_called()
            mock_tab.execute_script.assert_called_with("test_script")

    @pytest.mark.asyncio
    async def test_fingerprint_injection_with_exception_handling(self):
        """Test fingerprint injection with exception handling"""
        with patch('pydoll.browser.chromium.chrome.Chrome._get_default_binary_location'), \
             patch('pydoll.browser.chromium.chrome.Chrome._setup_user_dir'):

            chrome = Chrome(enable_fingerprint_spoofing=True)
            
            # Create mock tab that raises exception
            mock_tab = Mock()
            mock_tab._execute_command = AsyncMock()
            mock_tab.execute_script = AsyncMock(side_effect=Exception("Test exception"))
            
            # Ensure fingerprint manager exists
            assert chrome.fingerprint_manager is not None
            chrome.fingerprint_manager.get_fingerprint_js = Mock(return_value="test_script")
            
            # Should not raise exception
            await chrome._inject_fingerprint_script(mock_tab)
            
            # Verify that both attempts were made despite the exception
            mock_tab._execute_command.assert_called()
            mock_tab.execute_script.assert_called_with("test_script")

    def test_fingerprint_manager_edge_case_coverage(self):
        """Test additional edge cases for fingerprint manager"""
        manager = FingerprintManager()
        
        # Test getting current fingerprint when None
        assert manager.get_current_fingerprint() is None
        
        # Generate a fingerprint
        fingerprint = manager.generate_new_fingerprint()
        assert fingerprint is not None
        
        # Now test getting current fingerprint when it exists
        current = manager.get_current_fingerprint()
        assert current is fingerprint
        
        # Test clear functionality
        manager.clear_current_fingerprint()
        assert manager.current_fingerprint is None
        assert manager.injector is None

    def test_options_manager_edge_cases(self):
        """Test edge cases in options manager"""
        # Test with Chrome-style binary path
        manager = ChromiumOptionsManager(enable_fingerprint_spoofing=True)
        manager.options = ChromiumOptions()
        manager.options.binary_location = "/usr/bin/google-chrome"
        
        browser_type = manager._detect_browser_type()
        assert browser_type == 'chrome'
        
        # Test with Edge-style binary path
        manager.options.binary_location = "/usr/bin/microsoft-edge"
        browser_type = manager._detect_browser_type()
        assert browser_type == 'edge'
        
        # Test without binary location (should default to chrome)
        manager.options.binary_location = ""
        browser_type = manager._detect_browser_type()
        assert browser_type == 'chrome' 