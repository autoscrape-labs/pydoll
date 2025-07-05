"""
Tests for fingerprint spoofing integration functionality.

This module contains integration tests for fingerprint spoofing features
including browser integration, options manager, and error handling.
"""

import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock

import pytest

from pydoll.browser.chromium.chrome import Chrome
from pydoll.browser.chromium.edge import Edge
from pydoll.browser.managers.browser_options_manager import ChromiumOptionsManager
from pydoll.browser.options import ChromiumOptions
from pydoll.browser.tab import Tab
from pydoll.fingerprint import (
    FingerprintConfig,
    FingerprintManager,
    FingerprintGenerator,
    Fingerprint,
)
from pydoll.exceptions import InvalidOptionsObject


class TestFingerprintIntegration:
    """Test fingerprint spoofing integration with browsers."""

    @pytest.fixture
    def mock_tab(self):
        """Create a mock tab for testing."""
        tab = Mock(spec=Tab)
        tab._execute_command = AsyncMock()
        tab.execute_script = AsyncMock()
        return tab

    @pytest.fixture
    def test_fingerprint(self):
        """Create a test fingerprint."""
        return Fingerprint(
            user_agent="Test User Agent",
            platform="Win32",
            language="en-US",
            languages=["en-US", "en"],
            hardware_concurrency=4,
            screen_width=1920,
            screen_height=1080,
            screen_color_depth=24,
            screen_pixel_depth=24,
            available_width=1920,
            available_height=1040,
            viewport_width=1200,
            viewport_height=800,
            inner_width=1200,
            inner_height=680,
            webgl_vendor="Google Inc.",
            webgl_renderer="Test Renderer",
            webgl_version="WebGL 1.0",
            webgl_shading_language_version="WebGL GLSL ES 1.0",
            webgl_extensions=["EXT_test"],
            canvas_fingerprint="test_canvas_123",
            audio_context_sample_rate=44100.0,
            audio_context_state="suspended",
            audio_context_max_channel_count=2,
            timezone="America/New_York",
            timezone_offset=-300,
            browser_type="chrome",
            browser_version="120.0.0.0",
            plugins=[],
        )

    @pytest.mark.asyncio
    async def test_browser_fingerprint_injection_chrome(self, mock_tab, test_fingerprint):
        """Test fingerprint script injection in Chrome browser."""
        with patch('pydoll.browser.chromium.chrome.Chrome._get_default_binary_location'), \
             patch('pydoll.browser.chromium.chrome.Chrome._setup_user_dir'), \
             patch('pydoll.browser.chromium.chrome.Chrome._verify_browser_running'), \
             patch('pydoll.browser.chromium.chrome.Chrome._get_valid_tab_id'), \
             patch('pydoll.browser.tab.Tab') as mock_tab_class:

            # Setup mocks
            mock_tab_class.return_value = mock_tab
            
            # Create Chrome with fingerprint spoofing enabled
            chrome = Chrome(enable_fingerprint_spoofing=True)
            
            # Verify fingerprint manager is created
            assert chrome.enable_fingerprint_spoofing is True
            assert chrome.fingerprint_manager is not None
            
            # Mock the fingerprint manager
            chrome.fingerprint_manager.get_fingerprint_js = Mock(return_value="test_script")
            
            # Test the injection method directly
            await chrome._inject_fingerprint_script(mock_tab)
            
            # Verify script injection was attempted
            mock_tab._execute_command.assert_called()
            mock_tab.execute_script.assert_called_with("test_script")

    @pytest.mark.asyncio
    async def test_browser_fingerprint_injection_edge(self, mock_tab):
        """Test fingerprint script injection in Edge browser."""
        with patch('pydoll.browser.chromium.edge.Edge._get_default_binary_location'), \
             patch('pydoll.browser.chromium.edge.Edge._setup_user_dir'), \
             patch('pydoll.browser.chromium.edge.Edge._verify_browser_running'), \
             patch('pydoll.browser.chromium.edge.Edge._get_valid_tab_id'), \
             patch('pydoll.browser.tab.Tab') as mock_tab_class:

            # Setup mocks
            mock_tab_class.return_value = mock_tab
            
            # Create Edge with fingerprint spoofing enabled
            edge = Edge(enable_fingerprint_spoofing=True)
            
            # Verify fingerprint manager is created
            assert edge.enable_fingerprint_spoofing is True
            assert edge.fingerprint_manager is not None
            
            # Mock the fingerprint manager
            edge.fingerprint_manager.get_fingerprint_js = Mock(return_value="test_script")
            
            # Test the injection method directly
            await edge._inject_fingerprint_script(mock_tab)
            
            # Verify script injection was attempted
            mock_tab._execute_command.assert_called()
            mock_tab.execute_script.assert_called_with("test_script")

    @pytest.mark.asyncio
    async def test_fingerprint_injection_with_script_error(self):
        """Test fingerprint injection handles script execution errors gracefully."""
        with patch('pydoll.browser.chromium.chrome.Chrome._get_default_binary_location'), \
             patch('pydoll.browser.chromium.chrome.Chrome._setup_user_dir'):

            chrome = Chrome(enable_fingerprint_spoofing=True)
            
            # Create mock tab
            mock_tab = Mock()
            mock_tab._execute_command = AsyncMock()
            mock_tab.execute_script = AsyncMock()
            
            # Mock fingerprint manager
            if chrome.fingerprint_manager:
                chrome.fingerprint_manager.get_fingerprint_js = Mock(return_value="test_script")
            
            # Make execute_script raise an exception
            mock_tab.execute_script.side_effect = Exception("Script execution failed")
            
            # Should not raise exception - errors should be handled gracefully
            await chrome._inject_fingerprint_script(mock_tab)
            
            # Verify script injection was still attempted
            mock_tab._execute_command.assert_called()

    @pytest.mark.asyncio
    async def test_fingerprint_injection_no_manager(self, mock_tab):
        """Test fingerprint injection when no manager is available."""
        with patch('pydoll.browser.chromium.chrome.Chrome._get_default_binary_location'), \
             patch('pydoll.browser.chromium.chrome.Chrome._setup_user_dir'):

            chrome = Chrome(enable_fingerprint_spoofing=False)
            chrome.fingerprint_manager = None
            
            # Should handle gracefully when no fingerprint manager
            await chrome._inject_fingerprint_script(mock_tab)
            
            # No commands should be executed
            mock_tab._execute_command.assert_not_called()
            mock_tab.execute_script.assert_not_called()

    def test_get_fingerprint_summary_with_manager(self):
        """Test getting fingerprint summary when manager exists."""
        with patch('pydoll.browser.chromium.chrome.Chrome._get_default_binary_location'), \
             patch('pydoll.browser.chromium.chrome.Chrome._setup_user_dir'):

            chrome = Chrome(enable_fingerprint_spoofing=True)
            
            # Mock fingerprint manager summary
            expected_summary = {"browser": "Chrome", "version": "120.0.0.0"}
            chrome.fingerprint_manager.get_fingerprint_summary = Mock(return_value=expected_summary)
            
            summary = chrome.get_fingerprint_summary()
            assert summary == expected_summary

    def test_get_fingerprint_summary_no_manager(self):
        """Test getting fingerprint summary when no manager exists."""
        with patch('pydoll.browser.chromium.chrome.Chrome._get_default_binary_location'), \
             patch('pydoll.browser.chromium.chrome.Chrome._setup_user_dir'):

            chrome = Chrome(enable_fingerprint_spoofing=False)
            chrome.fingerprint_manager = None
            
            summary = chrome.get_fingerprint_summary()
            assert summary is None


class TestBrowserOptionsManagerFingerprinting:
    """Test fingerprint spoofing integration with browser options manager."""

    def test_options_manager_with_fingerprinting_enabled(self):
        """Test options manager with fingerprint spoofing enabled."""
        config = FingerprintConfig(browser_type="chrome", enable_webgl_spoofing=True)
        manager = ChromiumOptionsManager(
            enable_fingerprint_spoofing=True,
            fingerprint_config=config
        )
        
        # Verify fingerprint manager is created
        assert manager.enable_fingerprint_spoofing is True
        assert manager.fingerprint_manager is not None
        assert manager.fingerprint_config is not None

    def test_options_manager_fingerprint_spoofing_disabled(self):
        """Test options manager with fingerprint spoofing disabled."""
        manager = ChromiumOptionsManager(enable_fingerprint_spoofing=False)
        
        assert manager.enable_fingerprint_spoofing is False
        assert manager.fingerprint_manager is None

    def test_initialize_options_with_fingerprinting(self):
        """Test options initialization with fingerprint spoofing."""
        config = FingerprintConfig(browser_type="chrome")
        manager = ChromiumOptionsManager(
            enable_fingerprint_spoofing=True,
            fingerprint_config=config
        )
        
        # Mock fingerprint manager methods
        manager.fingerprint_manager.generate_new_fingerprint = Mock()
        manager.fingerprint_manager.get_fingerprint_arguments = Mock(return_value=[
            '--user-agent=Test Agent',
            '--lang=en-US'
        ])
        
        options = manager.initialize_options()
        
        # Verify options were initialized
        assert isinstance(options, ChromiumOptions)
        
        # Verify fingerprint methods were called
        manager.fingerprint_manager.generate_new_fingerprint.assert_called_with('chrome')
        manager.fingerprint_manager.get_fingerprint_arguments.assert_called_with('chrome')

    def test_detect_browser_type_chrome(self):
        """Test browser type detection for Chrome."""
        manager = ChromiumOptionsManager(enable_fingerprint_spoofing=True)
        manager.options = ChromiumOptions()
        manager.options.binary_location = "/path/to/chrome"
        
        browser_type = manager._detect_browser_type()
        assert browser_type == 'chrome'

    def test_detect_browser_type_edge(self):
        """Test browser type detection for Edge."""
        manager = ChromiumOptionsManager(enable_fingerprint_spoofing=True)
        manager.options = ChromiumOptions()
        manager.options.binary_location = "/path/to/msedge"
        
        browser_type = manager._detect_browser_type()
        assert browser_type == 'edge'

    def test_detect_browser_type_default(self):
        """Test browser type detection defaults to chrome."""
        manager = ChromiumOptionsManager(enable_fingerprint_spoofing=True)
        manager.options = ChromiumOptions()
        manager.options.binary_location = None
        
        browser_type = manager._detect_browser_type()
        assert browser_type == 'chrome'

    def test_get_fingerprint_manager(self):
        """Test getting fingerprint manager instance."""
        manager = ChromiumOptionsManager(enable_fingerprint_spoofing=True)
        
        fingerprint_manager = manager.get_fingerprint_manager()
        assert fingerprint_manager is not None
        assert fingerprint_manager == manager.fingerprint_manager

    def test_get_fingerprint_manager_disabled(self):
        """Test getting fingerprint manager when disabled."""
        manager = ChromiumOptionsManager(enable_fingerprint_spoofing=False)
        
        fingerprint_manager = manager.get_fingerprint_manager()
        assert fingerprint_manager is None

    def test_invalid_options_object(self):
        """Test error handling for invalid options object."""
        manager = ChromiumOptionsManager()
        manager.options = Mock()  # Invalid options object
        
        with pytest.raises(InvalidOptionsObject):
            manager.initialize_options()


class TestFingerprintManagerErrorHandling:
    """Test error handling in fingerprint manager."""

    def test_get_fingerprint_js_without_injector(self):
        """Test error when getting JS without generated fingerprint."""
        manager = FingerprintManager()
        
        with pytest.raises(ValueError, match="No fingerprint has been generated"):
            manager.get_fingerprint_js()

    def test_get_fingerprint_arguments_without_fingerprint(self):
        """Test error when getting arguments without generated fingerprint."""
        manager = FingerprintManager()
        
        with pytest.raises(ValueError, match="No fingerprint has been generated"):
            manager.get_fingerprint_arguments()

    def test_save_fingerprint_without_fingerprint(self):
        """Test error when saving without current fingerprint."""
        manager = FingerprintManager()
        
        with pytest.raises(ValueError, match="No fingerprint provided"):
            manager.save_fingerprint("test")

    def test_get_fingerprint_summary_without_fingerprint(self):
        """Test error when getting summary without fingerprint."""
        manager = FingerprintManager()
        
        with pytest.raises(ValueError, match="No fingerprint provided"):
            manager.get_fingerprint_summary()

    def test_load_nonexistent_fingerprint(self):
        """Test error when loading non-existent fingerprint."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = FingerprintConfig()
            manager = FingerprintManager(config)
            manager.storage_dir = Path(temp_dir)
            
            with pytest.raises(FileNotFoundError, match="Fingerprint 'nonexistent' not found"):
                manager.load_fingerprint("nonexistent")

    def test_load_invalid_fingerprint_file(self):
        """Test error when loading invalid fingerprint file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = FingerprintConfig()
            manager = FingerprintManager(config)
            manager.storage_dir = Path(temp_dir)
            
            # Create invalid JSON file
            invalid_file = Path(temp_dir) / "invalid.json"
            with open(invalid_file, 'w') as f:
                f.write("invalid json content")
            
            with pytest.raises(ValueError, match="Invalid fingerprint file"):
                manager.load_fingerprint("invalid")


class TestFingerprintManagerFileOperations:
    """Test file operations in fingerprint manager."""

    def test_save_and_load_fingerprint(self):
        """Test saving and loading fingerprint functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = FingerprintConfig()
            manager = FingerprintManager(config)
            manager.storage_dir = Path(temp_dir)
            
            # Generate a fingerprint
            fingerprint = manager.generate_new_fingerprint()
            
            # Save fingerprint
            saved_path = manager.save_fingerprint("test_fp")
            assert Path(saved_path).exists()
            
            # Clear current fingerprint
            manager.clear_current_fingerprint()
            assert manager.current_fingerprint is None
            
            # Load fingerprint
            loaded_fp = manager.load_fingerprint("test_fp")
            assert loaded_fp.user_agent == fingerprint.user_agent
            assert loaded_fp.browser_type == fingerprint.browser_type

    def test_list_saved_fingerprints(self):
        """Test listing saved fingerprints."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = FingerprintConfig()
            manager = FingerprintManager(config)
            manager.storage_dir = Path(temp_dir)
            
            # Initially no fingerprints
            assert manager.list_saved_fingerprints() == []
            
            # Generate and save fingerprints
            manager.generate_new_fingerprint()
            manager.save_fingerprint("fp1")
            
            manager.generate_new_fingerprint(force=True)
            manager.save_fingerprint("fp2")
            
            # List should contain both
            saved_fps = manager.list_saved_fingerprints()
            assert len(saved_fps) == 2
            assert "fp1" in saved_fps
            assert "fp2" in saved_fps

    def test_delete_fingerprint(self):
        """Test deleting saved fingerprint."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = FingerprintConfig()
            manager = FingerprintManager(config)
            manager.storage_dir = Path(temp_dir)
            
            # Generate and save fingerprint
            manager.generate_new_fingerprint()
            manager.save_fingerprint("to_delete")
            
            # Verify it exists
            assert "to_delete" in manager.list_saved_fingerprints()
            
            # Delete it
            result = manager.delete_fingerprint("to_delete")
            assert result is True
            
            # Verify it's gone
            assert "to_delete" not in manager.list_saved_fingerprints()

    def test_delete_nonexistent_fingerprint(self):
        """Test deleting non-existent fingerprint."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = FingerprintConfig()
            manager = FingerprintManager(config)
            manager.storage_dir = Path(temp_dir)
            
            # Try to delete non-existent fingerprint
            result = manager.delete_fingerprint("nonexistent")
            assert result is False

    def test_get_current_fingerprint(self):
        """Test getting current fingerprint."""
        manager = FingerprintManager()
        
        # Initially None
        assert manager.get_current_fingerprint() is None
        
        # After generation
        fingerprint = manager.generate_new_fingerprint()
        current = manager.get_current_fingerprint()
        assert current is not None
        assert current == fingerprint

    def test_clear_current_fingerprint(self):
        """Test clearing current fingerprint."""
        manager = FingerprintManager()
        
        # Generate fingerprint
        manager.generate_new_fingerprint()
        assert manager.current_fingerprint is not None
        assert manager.injector is not None
        
        # Clear it
        manager.clear_current_fingerprint()
        assert manager.current_fingerprint is None
        assert manager.injector is None


class TestFingerprintGeneratorEdgeCases:
    """Test edge cases in fingerprint generator."""

    def test_generate_unique_properties(self):
        """Test unique properties generation."""
        from pydoll.fingerprint.generator import FingerprintGenerator
        
        props = FingerprintGenerator._generate_unique_properties()
        assert "unique_id" in props
        assert isinstance(props["unique_id"], str)
        assert len(props["unique_id"]) > 0

    def test_generate_plugins(self):
        """Test plugins generation."""
        config = FingerprintConfig()
        generator = FingerprintGenerator(config)
        
        plugins = generator._generate_plugins()
        assert isinstance(plugins, list)
        assert len(plugins) > 0
        
        # Check plugin structure
        for plugin in plugins:
            assert "name" in plugin
            assert "filename" in plugin
            assert "description" in plugin 