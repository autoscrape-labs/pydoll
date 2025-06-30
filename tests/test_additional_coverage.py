"""
Additional tests specifically for uncovered lines mentioned by Codecov.
This file targets the exact lines that need coverage:
- pydoll/fingerprint/generator.py#L335
- pydoll/fingerprint/manager.py#L55  
- pydoll/fingerprint/manager.py#L262
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

import pytest

from pydoll.fingerprint.generator import FingerprintGenerator
from pydoll.fingerprint.manager import FingerprintManager
from pydoll.fingerprint.models import FingerprintConfig
from pydoll.browser.managers.browser_options_manager import ChromiumOptionsManager
from pydoll.browser.options import ChromiumOptions


class TestUncoveredLines:
    """Tests specifically targeting uncovered lines reported by Codecov."""

    def test_generator_line_335_unique_properties(self):
        """Test generator.py#L335 - _generate_unique_properties return statement"""
        # Call the static method directly to ensure line 335 is executed
        result = FingerprintGenerator._generate_unique_properties()
        
        # Verify the return value structure to ensure line 335 is hit
        assert isinstance(result, dict)
        assert "unique_id" in result
        assert isinstance(result["unique_id"], str)
        assert len(result["unique_id"]) > 0
        
        # Call it multiple times to ensure different values
        result2 = FingerprintGenerator._generate_unique_properties()
        assert result["unique_id"] != result2["unique_id"]

    def test_manager_line_55_get_current_fingerprint(self):
        """Test manager.py#L55 - get_current_fingerprint return statement"""
        manager = FingerprintManager()
        
        # First, ensure current_fingerprint is None
        assert manager.current_fingerprint is None
        result = manager.get_current_fingerprint()
        assert result is None
        
        # Generate a fingerprint to set current_fingerprint
        fingerprint = manager.generate_new_fingerprint()
        assert manager.current_fingerprint is not None
        
        # Now call get_current_fingerprint to hit line 55
        result = manager.get_current_fingerprint()
        assert result is fingerprint
        assert result == manager.current_fingerprint

    def test_manager_line_262_delete_nonexistent_fingerprint(self):
        """Test manager.py#L262 - delete_fingerprint return False statement"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = FingerprintManager()
            manager.storage_dir = Path(temp_dir)
            
            # Try to delete a fingerprint that doesn't exist
            # This should hit line 262 where it returns False
            result = manager.delete_fingerprint("nonexistent_fingerprint")
            assert result is False
            
            # Verify no files were created
            files = list(manager.storage_dir.glob("*.json"))
            assert len(files) == 0

    def test_browser_options_manager_line_71_no_fingerprint_manager(self):
        """Test browser_options_manager.py#L71 - early return when no fingerprint manager"""
        # Create manager without fingerprint spoofing
        manager = ChromiumOptionsManager(enable_fingerprint_spoofing=False)
        manager.options = ChromiumOptions()
        
        # Manually set fingerprint_manager to None to ensure we hit line 71
        manager.fingerprint_manager = None
        
        # Call _apply_fingerprint_spoofing - should return early on line 71
        result = manager._apply_fingerprint_spoofing()
        assert result is None

    def test_fingerprint_integration_complete_workflow(self):
        """Comprehensive test to ensure all targeted lines are covered"""
        # Test the complete workflow that should cover all lines
        
        # 1. Test unique properties generation (line 335)
        unique_props = FingerprintGenerator._generate_unique_properties()
        assert "unique_id" in unique_props
        
        # 2. Test fingerprint manager workflow (line 55 and 262)
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = FingerprintManager()
            manager.storage_dir = Path(temp_dir)
            
            # Initially no fingerprint
            assert manager.get_current_fingerprint() is None
            
            # Generate one
            fingerprint = manager.generate_new_fingerprint()
            
            # Test line 55 - return current fingerprint
            current = manager.get_current_fingerprint()
            assert current is fingerprint
            
            # Test line 262 - delete non-existent file
            assert manager.delete_fingerprint("fake") is False
            
        # 3. Test browser options manager (line 71)
        options_manager = ChromiumOptionsManager(enable_fingerprint_spoofing=False)
        options_manager.fingerprint_manager = None
        result = options_manager._apply_fingerprint_spoofing()
        assert result is None

    def test_edge_cases_for_complete_coverage(self):
        """Additional edge cases to ensure 100% coverage of targeted lines"""
        
        # Test multiple calls to unique properties
        props1 = FingerprintGenerator._generate_unique_properties()
        props2 = FingerprintGenerator._generate_unique_properties()
        props3 = FingerprintGenerator._generate_unique_properties()
        
        # Ensure they're all different
        unique_ids = [props1["unique_id"], props2["unique_id"], props3["unique_id"]]
        assert len(set(unique_ids)) == 3  # All should be unique
        
        # Test manager state transitions
        manager = FingerprintManager()
        
        # Multiple calls when None
        assert manager.get_current_fingerprint() is None
        assert manager.get_current_fingerprint() is None
        
        # Generate and test multiple calls when exists
        fp = manager.generate_new_fingerprint()
        assert manager.get_current_fingerprint() is fp
        assert manager.get_current_fingerprint() is fp
        
        # Clear and test again
        manager.clear_current_fingerprint()
        assert manager.get_current_fingerprint() is None
        
        # Test delete operations
        with tempfile.TemporaryDirectory() as temp_dir:
            manager.storage_dir = Path(temp_dir)
            
            # Multiple delete attempts on non-existent files
            assert manager.delete_fingerprint("file1") is False
            assert manager.delete_fingerprint("file2") is False
            assert manager.delete_fingerprint("") is False 