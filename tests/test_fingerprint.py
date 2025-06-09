"""
Tests for the fingerprint spoofing functionality.

This module contains unit tests for the fingerprint spoofing components
of the pydoll library.
"""

import pytest
from unittest.mock import Mock, patch

from pydoll.fingerprint import (
    FingerprintGenerator,
    FingerprintInjector,
    FingerprintManager,
    Fingerprint,
    FingerprintConfig,
)


class TestFingerprintConfig:
    """Test the FingerprintConfig class."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = FingerprintConfig()
        assert config.browser_type == "chrome"
        assert config.is_mobile == False
        assert config.min_screen_width == 1024
        assert config.enable_webgl_spoofing == True
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = FingerprintConfig(
            browser_type="edge",
            preferred_os="windows",
            enable_webgl_spoofing=False
        )
        assert config.browser_type == "edge"
        assert config.preferred_os == "windows"
        assert config.enable_webgl_spoofing == False
    
    def test_config_serialization(self):
        """Test configuration to/from dict conversion."""
        config = FingerprintConfig(browser_type="edge", is_mobile=True)
        config_dict = config.to_dict()
        restored_config = FingerprintConfig.from_dict(config_dict)
        
        assert restored_config.browser_type == config.browser_type
        assert restored_config.is_mobile == config.is_mobile


class TestFingerprintGenerator:
    """Test the FingerprintGenerator class."""
    
    def test_default_generation(self):
        """Test generating a fingerprint with default settings."""
        generator = FingerprintGenerator()
        fingerprint = generator.generate()
        
        assert isinstance(fingerprint, Fingerprint)
        assert fingerprint.user_agent
        assert fingerprint.platform
        assert fingerprint.screen_width > 0
        assert fingerprint.screen_height > 0
        assert fingerprint.hardware_concurrency > 0
        assert len(fingerprint.webgl_extensions) > 0
    
    def test_chrome_generation(self):
        """Test generating a Chrome fingerprint."""
        config = FingerprintConfig(browser_type="chrome")
        generator = FingerprintGenerator(config)
        fingerprint = generator.generate()
        
        assert fingerprint.browser_type == "chrome"
        assert "Chrome" in fingerprint.user_agent
    
    def test_edge_generation(self):
        """Test generating an Edge fingerprint."""
        config = FingerprintConfig(browser_type="edge")
        generator = FingerprintGenerator(config)
        fingerprint = generator.generate()
        
        assert fingerprint.browser_type == "edge"
        assert "Edg" in fingerprint.user_agent
    
    def test_consistent_generation(self):
        """Test that multiple generations produce different fingerprints."""
        generator = FingerprintGenerator()
        fp1 = generator.generate()
        fp2 = generator.generate()
        
        # Should be different (random generation)
        # At least user agent should be different due to version randomization
        assert fp1.canvas_fingerprint != fp2.canvas_fingerprint


class TestFingerprintInjector:
    """Test the FingerprintInjector class."""
    
    def test_script_generation(self):
        """Test JavaScript script generation."""
        # Create a test fingerprint
        fingerprint = Fingerprint(
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
        
        injector = FingerprintInjector(fingerprint)
        script = injector.generate_script()
        
        assert isinstance(script, str)
        assert len(script) > 0
        assert "'userAgent'" in script
        assert "Test User Agent" in script
        assert "'width'" in script
        assert "1920" in script
        assert "webdriver" in script
    
    def test_navigator_override(self):
        """Test navigator properties override generation."""
        fingerprint = Fingerprint(
            user_agent="Test UA",
            platform="Test Platform",
            language="en-US",
            languages=["en-US"],
            hardware_concurrency=8,
            screen_width=1920, screen_height=1080,
            screen_color_depth=24, screen_pixel_depth=24,
            available_width=1920, available_height=1040,
            viewport_width=1200, viewport_height=800,
            inner_width=1200, inner_height=680,
            webgl_vendor="Test", webgl_renderer="Test",
            webgl_version="Test", webgl_shading_language_version="Test",
            webgl_extensions=[], canvas_fingerprint="test",
            audio_context_sample_rate=44100.0, audio_context_state="suspended",
            audio_context_max_channel_count=2, timezone="UTC", timezone_offset=0,
            browser_type="chrome", browser_version="120.0.0.0", plugins=[],
        )
        
        injector = FingerprintInjector(fingerprint)
        nav_script = injector._generate_navigator_override()
        
        assert "Test UA" in nav_script
        assert "Test Platform" in nav_script
        assert "hardwareConcurrency" in nav_script
        assert "8" in nav_script


class TestFingerprintManager:
    """Test the FingerprintManager class."""
    
    def test_manager_initialization(self):
        """Test manager initialization."""
        manager = FingerprintManager()
        assert manager.current_fingerprint is None
        assert manager.injector is None
    
    def test_fingerprint_generation(self):
        """Test fingerprint generation through manager."""
        manager = FingerprintManager()
        fingerprint = manager.generate_new_fingerprint("chrome")
        
        assert manager.current_fingerprint is not None
        assert manager.injector is not None
        assert fingerprint.browser_type == "chrome"
    
    def test_javascript_generation(self):
        """Test JavaScript generation through manager."""
        manager = FingerprintManager()
        manager.generate_new_fingerprint("chrome")
        
        js_code = manager.get_fingerprint_js()
        assert isinstance(js_code, str)
        assert len(js_code) > 0
    
    def test_argument_generation(self):
        """Test command line argument generation."""
        manager = FingerprintManager()
        manager.generate_new_fingerprint("chrome")
        
        args = manager.get_fingerprint_arguments("chrome")
        assert isinstance(args, list)
        assert len(args) > 0
        assert any("--user-agent=" in arg for arg in args)
        assert any("--disable-blink-features=AutomationControlled" in arg for arg in args)
    
    def test_fingerprint_summary(self):
        """Test fingerprint summary generation."""
        manager = FingerprintManager()
        manager.generate_new_fingerprint("chrome")
        
        summary = manager.get_fingerprint_summary()
        assert isinstance(summary, dict)
        assert "Browser" in summary
        assert "User Agent" in summary
        assert "Screen" in summary
    
    @patch('pathlib.Path.mkdir')
    @patch('builtins.open')
    @patch('json.dump')
    def test_save_fingerprint(self, mock_json_dump, mock_open, mock_mkdir):
        """Test saving fingerprint to disk."""
        manager = FingerprintManager()
        manager.generate_new_fingerprint("chrome")
        
        # Mock file operations
        mock_open.return_value.__enter__.return_value = Mock()
        
        result = manager.save_fingerprint("test_fp")
        
        assert isinstance(result, str)
        assert "test_fp.json" in result
        mock_json_dump.assert_called_once()
    
    def test_error_without_fingerprint(self):
        """Test error handling when no fingerprint is generated."""
        manager = FingerprintManager()
        
        with pytest.raises(ValueError, match="No fingerprint has been generated"):
            manager.get_fingerprint_js()
        
        with pytest.raises(ValueError, match="No fingerprint has been generated"):
            manager.get_fingerprint_arguments()


class TestFingerprint:
    """Test the Fingerprint data class."""
    
    def test_fingerprint_serialization(self):
        """Test fingerprint to/from dict conversion."""
        fingerprint = Fingerprint(
            user_agent="Test",
            platform="Test",
            language="en",
            languages=["en"],
            hardware_concurrency=4,
            screen_width=1920, screen_height=1080,
            screen_color_depth=24, screen_pixel_depth=24,
            available_width=1920, available_height=1040,
            viewport_width=1200, viewport_height=800,
            inner_width=1200, inner_height=680,
            webgl_vendor="Test", webgl_renderer="Test",
            webgl_version="Test", webgl_shading_language_version="Test",
            webgl_extensions=[], canvas_fingerprint="test",
            audio_context_sample_rate=44100.0, audio_context_state="suspended",
            audio_context_max_channel_count=2, timezone="UTC", timezone_offset=0,
            browser_type="chrome", browser_version="120.0.0.0", plugins=[],
        )
        
        fp_dict = fingerprint.to_dict()
        restored_fp = Fingerprint.from_dict(fp_dict)
        
        assert restored_fp.user_agent == fingerprint.user_agent
        assert restored_fp.screen_width == fingerprint.screen_width
        assert restored_fp.hardware_concurrency == fingerprint.hardware_concurrency


if __name__ == "__main__":
    pytest.main([__file__]) 