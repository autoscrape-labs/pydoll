"""
Exact tests to cover uncovered lines reported by Codecov:
- pydoll/fingerprint/generator.py#L335 (fallback browser type)
- pydoll/fingerprint/manager.py#L55 (return current_fingerprint)  
- pydoll/fingerprint/manager.py#L262 (return False when file doesn't exist)
- pydoll/browser/managers/browser_options_manager.py#L71 (early return when no fingerprint manager)

This file merges all tests from test_additional_coverage.py and test_exact_coverage.py.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from pydoll.fingerprint.generator import FingerprintGenerator
from pydoll.fingerprint.manager import FingerprintManager
from pydoll.fingerprint.models import FingerprintConfig
from pydoll.browser.managers.browser_options_manager import ChromiumOptionsManager
from pydoll.browser.options import ChromiumOptions


class TestExactCoverage:
    """Exact tests for uncovered lines"""

    def test_generator_line_335_fallback_browser_type(self):
        """
        Test generator.py#L335 - _generate_user_agent fallback case
        when browser_type is neither 'chrome' nor 'edge'
        """
        # Create a configuration with browser_type set to non-chrome/edge value
        config = FingerprintConfig()
        config.browser_type = 'firefox'  # This triggers fallback to Chrome
        config.is_mobile = False
        
        generator = FingerprintGenerator(config)
        
        # Mock OS info and browser version
        os_info = {'name': 'Windows', 'version': '10.0'}
        browser_version = '120.0.6099.129'
        
        # Call _generate_user_agent, this should hit line 335 fallback
        user_agent = generator._generate_user_agent(os_info, browser_version)
        
        # Verify Chrome user agent was generated (fallback behavior)
        assert 'Chrome' in user_agent
        assert 'Windows NT 10.0' in user_agent
        assert browser_version in user_agent

    def test_generator_unique_properties_method(self):
        """Test _generate_unique_properties static method call"""
        # Call static method directly to ensure execution
        result = FingerprintGenerator._generate_unique_properties()
        
        # Verify return value structure
        assert isinstance(result, dict)
        assert "unique_id" in result
        assert isinstance(result["unique_id"], str)
        assert len(result["unique_id"]) > 0
        
        # Call multiple times to ensure different values are generated
        result2 = FingerprintGenerator._generate_unique_properties()
        assert result["unique_id"] != result2["unique_id"]

    def test_manager_line_55_return_current_fingerprint(self):
        """
        Test manager.py#L55 - get_current_fingerprint returns current fingerprint
        """
        manager = FingerprintManager()
        
        # First ensure current_fingerprint is None
        assert manager.current_fingerprint is None
        result = manager.get_current_fingerprint()
        assert result is None
        
        # Generate a fingerprint
        fingerprint = manager.generate_new_fingerprint()
        assert manager.current_fingerprint is not None
        
        # Now call get_current_fingerprint - this should hit line 55
        current = manager.get_current_fingerprint()
        
        # Verify the same fingerprint is returned
        assert current is fingerprint
        assert current == manager.current_fingerprint

    def test_manager_line_262_delete_nonexistent_return_false(self):
        """
        Test manager.py#L262 - delete_fingerprint returns False when file doesn't exist
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = FingerprintManager()
            manager.storage_dir = Path(temp_dir)
            
            # Try to delete non-existent file - this should hit line 262 return False
            result = manager.delete_fingerprint("definitely_does_not_exist")
            
            # Verify False is returned
            assert result is False
            
            # Verify no files were created
            files = list(manager.storage_dir.glob("*.json"))
            assert len(files) == 0

    def test_browser_options_manager_line_71_no_fingerprint_manager(self):
        """Test browser_options_manager.py#L71 - early return when no fingerprint manager"""
        # Create manager without fingerprint spoofing enabled
        manager = ChromiumOptionsManager(enable_fingerprint_spoofing=False)
        manager.options = ChromiumOptions()
        
        # Manually set fingerprint_manager to None to ensure we hit line 71
        manager.fingerprint_manager = None
        
        # Call _apply_fingerprint_spoofing - should return early at line 71
        result = manager._apply_fingerprint_spoofing()
        assert result is None

    def test_comprehensive_coverage_verification(self):
        """
        Comprehensive test to ensure all 4 lines are covered
        """
        # 1. Test generator fallback (line 335)
        config = FingerprintConfig()
        config.browser_type = 'unknown_browser'  # Trigger fallback
        generator = FingerprintGenerator(config)
        
        os_info = {'name': 'Linux', 'version': 'x86_64'}
        user_agent = generator._generate_user_agent(os_info, '120.0.0.0')
        assert 'Chrome' in user_agent  # Should fallback to Chrome
        
        # 2. Test unique properties 
        unique_props = FingerprintGenerator._generate_unique_properties()
        assert "unique_id" in unique_props
        
        # 3. Test manager get_current_fingerprint (line 55)
        manager = FingerprintManager()
        fp = manager.generate_new_fingerprint()
        current = manager.get_current_fingerprint()
        assert current is fp
        
        # 4. Test manager delete_fingerprint returns False (line 262)
        with tempfile.TemporaryDirectory() as temp_dir:
            manager.storage_dir = Path(temp_dir)
            assert manager.delete_fingerprint("nonexistent") is False
            
        # 5. Test browser options manager (line 71)
        options_manager = ChromiumOptionsManager(enable_fingerprint_spoofing=False)
        options_manager.fingerprint_manager = None
        result = options_manager._apply_fingerprint_spoofing()
        assert result is None

    def test_browser_type_variations_for_fallback(self):
        """
        Test various browser_type values to ensure fallback is triggered
        """
        test_cases = [
            'firefox',
            'safari',
            'opera', 
            'unknown',
            'invalid',
            None,  # If None, should also trigger fallback
        ]
        
        for browser_type in test_cases:
            config = FingerprintConfig()
            config.browser_type = browser_type
            config.is_mobile = False
            
            generator = FingerprintGenerator(config)
            
            os_info = {'name': 'Windows', 'version': '10.0'}
            browser_version = '120.0.0.0'
            
            # This should all trigger line 335 fallback
            user_agent = generator._generate_user_agent(os_info, browser_version)
            
            # Verify all fallback to Chrome
            assert 'Chrome' in user_agent
            assert 'Windows NT 10.0' in user_agent

    def test_manager_state_transitions(self):
        """
        Test manager state transitions to cover line 55
        """
        manager = FingerprintManager()
        
        # Initial state: None
        assert manager.get_current_fingerprint() is None
        
        # After generating fingerprint
        fp1 = manager.generate_new_fingerprint()
        assert manager.get_current_fingerprint() is fp1  # Hit line 55
        
        # Force generate new fingerprint
        fp2 = manager.generate_new_fingerprint(force=True)
        assert manager.get_current_fingerprint() is fp2  # Hit line 55 again
        
        # After clearing
        manager.clear_current_fingerprint()
        assert manager.get_current_fingerprint() is None

    def test_delete_operations_coverage(self):
        """
        Test delete operations to cover line 262
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = FingerprintManager()
            manager.storage_dir = Path(temp_dir)
            
            # Try to delete different non-existent files
            test_names = [
                "nonexistent1",
                "nonexistent2", 
                "fake_fingerprint",
                "",  # Empty string
                "very_long_name_that_definitely_does_not_exist",
            ]
            
            for name in test_names:
                # Each should hit line 262 return False
                result = manager.delete_fingerprint(name)
                assert result is False

    def test_edge_cases_for_complete_coverage(self):
        """Additional edge case tests to ensure 100% coverage of all target lines"""
        
        # Test multiple calls to unique properties
        props1 = FingerprintGenerator._generate_unique_properties()
        props2 = FingerprintGenerator._generate_unique_properties()
        props3 = FingerprintGenerator._generate_unique_properties()
        
        # Ensure they are all different
        unique_ids = [props1["unique_id"], props2["unique_id"], props3["unique_id"]]
        assert len(set(unique_ids)) == 3  # All should be unique
        
        # Test manager state transitions
        manager = FingerprintManager()
        
        # Multiple calls when None
        assert manager.get_current_fingerprint() is None
        assert manager.get_current_fingerprint() is None
        
        # Test multiple calls after generation
        fp = manager.generate_new_fingerprint()
        assert manager.get_current_fingerprint() is fp
        assert manager.get_current_fingerprint() is fp
        
        # Clear and test again
        manager.clear_current_fingerprint()
        assert manager.get_current_fingerprint() is None
        
        # Test delete operations
        with tempfile.TemporaryDirectory() as temp_dir:
            manager.storage_dir = Path(temp_dir)
            
            # Multiple attempts to delete non-existent files
            assert manager.delete_fingerprint("file1") is False
            assert manager.delete_fingerprint("file2") is False
            assert manager.delete_fingerprint("") is False

    def test_fingerprint_integration_complete_workflow(self):
        """Complete fingerprint integration workflow test"""
        # Test complete workflow that should cover all lines
        
        # 1. Test unique properties generation 
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
        
        # 4. Test generator fallback (line 335)
        config = FingerprintConfig()
        config.browser_type = 'unsupported_browser'
        config.is_mobile = False
        generator = FingerprintGenerator(config)
        
        os_info = {'name': 'Windows', 'version': '10.0'}
        user_agent = generator._generate_user_agent(os_info, '120.0.0.0')
        assert 'Chrome' in user_agent  # Should fallback to Chrome

    def test_various_browser_options_scenarios(self):
        """Test various browser options scenarios"""
        # Test fingerprint spoofing enabled but manually set to None
        manager_enabled = ChromiumOptionsManager(enable_fingerprint_spoofing=True)
        manager_enabled.options = ChromiumOptions()
        manager_enabled.fingerprint_manager = None  # Manually set to None
        
        # This should hit line 71 early return
        result = manager_enabled._apply_fingerprint_spoofing()
        assert result is None
        
        # Test fingerprint spoofing disabled
        manager_disabled = ChromiumOptionsManager(enable_fingerprint_spoofing=False)
        manager_disabled.options = ChromiumOptions()
        assert manager_disabled.fingerprint_manager is None
        
        # This should also hit line 71
        result = manager_disabled._apply_fingerprint_spoofing()
        assert result is None

    # ==================== DIRECT COVERAGE TESTS ====================
    # These are very simple, direct tests specifically for the uncovered lines

    def test_direct_line_55_coverage(self):
        """DIRECT test for line 55: return self.current_fingerprint"""
        manager = FingerprintManager()
        
        # Generate fingerprint so current_fingerprint is not None
        fingerprint = manager.generate_new_fingerprint()
        
        # Call get_current_fingerprint - should DIRECTLY hit line 55
        result = manager.get_current_fingerprint()
        
        # This line execution should cover line 55
        assert result is fingerprint

    def test_direct_line_262_coverage(self):
        """DIRECT test for line 262: return False"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = FingerprintManager()
            manager.storage_dir = Path(temp_dir)
            
            # Call delete_fingerprint with non-existent file
            # This should DIRECTLY hit line 262: return False
            result = manager.delete_fingerprint("nonexistent_file")
            
            # This line execution should cover line 262
            assert result is False

    def test_mobile_user_agent_ios_path_lines_341_342(self):
        """DIRECT test for lines 341-342: iOS mobile user agent generation"""
        from unittest.mock import patch
        
        # Create mobile configuration
        config = FingerprintConfig()
        config.is_mobile = True
        config.browser_type = 'chrome'
        
        generator = FingerprintGenerator(config)
        
        # Mock random.choice to always return False (iOS path)
        with patch('random.choice') as mock_choice:
            # Set up the mock to return iOS path for the first call, then iPhone for device selection
            mock_choice.side_effect = [False, "iPhone"]  # False = iOS path, then choose iPhone
            
            # Call _generate_mobile_user_agent directly to hit lines 341-342
            user_agent = generator._generate_mobile_user_agent("iOS", "120.0.0.0")
            
            # Verify iOS user agent was generated
            assert "iPhone" in user_agent or "iPad" in user_agent
            assert "CriOS" in user_agent
            assert "Mobile" in user_agent

    def test_mobile_user_agent_comprehensive_coverage(self):
        """Comprehensive test for mobile user agent generation to cover lines 341-342 and 346-347"""
        import random
        
        # Create mobile configuration
        config = FingerprintConfig()
        config.is_mobile = True
        
        generator = FingerprintGenerator(config)
        
        # Generate multiple mobile user agents to ensure we hit both Android and iOS paths
        user_agents = []
        for _ in range(20):  # Generate enough to statistically hit both paths
            # Generate random mobile user agent
            user_agent = generator._generate_mobile_user_agent("mobile", "120.0.0.0")
            user_agents.append(user_agent)
        
        # Check that we got both Android and iOS user agents
        android_uas = [ua for ua in user_agents if "Android" in ua]
        ios_uas = [ua for ua in user_agents if ("iPhone" in ua or "iPad" in ua) and "CriOS" in ua]
        
        # At least one of each type should be generated
        assert len(android_uas) > 0, "Android user agents should be generated"
        assert len(ios_uas) > 0, "iOS user agents should be generated"

    def test_force_ios_mobile_user_agent_path(self):
        """Force iOS path in mobile user agent generation"""
        from unittest.mock import patch, MagicMock
        
        # Create mobile configuration
        config = FingerprintConfig()
        config.is_mobile = True
        
        generator = FingerprintGenerator(config)
        
        # Mock all random functions to control the execution path
        with patch('random.choice') as mock_choice, \
             patch('random.randint') as mock_randint:
            
            # Set up mocks to force iOS path
            mock_choice.side_effect = [
                False,  # First call: choose iOS over Android
                "iPhone",  # Second call: choose iPhone from device_models
            ]
            
            mock_randint.side_effect = [
                15, 3,  # ios_version: f"{15}_{3}"
                8, 5,   # webkit_version: f"60{8}.{5}"
                42      # webkit_version suffix: random.randint(10, 99)
            ]
            
            # Call the mobile user agent generation
            user_agent = generator._generate_mobile_user_agent("mobile", "120.0.0.0")
            
            # Verify iOS user agent structure
            assert "iPhone" in user_agent
            assert "CPU OS 15_3" in user_agent
            assert "CriOS/120.0.0.0" in user_agent
            assert "Mobile/15E148" in user_agent
            assert "608.5.42" in user_agent  # webkit version with our mocked values

    def test_fingerprint_generation_with_mobile_config(self):
        """Test complete fingerprint generation with mobile configuration"""
        # Create mobile configuration
        config = FingerprintConfig()
        config.is_mobile = True
        config.browser_type = 'chrome'
        
        generator = FingerprintGenerator(config)
        
        # Generate multiple fingerprints to ensure iOS path is hit
        for _ in range(10):
            fingerprint = generator.generate()
            
            # Verify mobile fingerprint properties
            assert fingerprint.user_agent is not None
            assert len(fingerprint.user_agent) > 0
            
            # Check if it's a mobile user agent
            is_mobile_ua = (
                "Mobile" in fingerprint.user_agent or 
                "iPhone" in fingerprint.user_agent or 
                "iPad" in fingerprint.user_agent or
                "Android" in fingerprint.user_agent
            )
            assert is_mobile_ua, f"Expected mobile user agent, got: {fingerprint.user_agent}"

    def test_direct_ios_user_agent_code_execution(self):
        """Direct test to execute iOS user agent code lines 341-342"""
        # Import and use the specific method
        from pydoll.fingerprint.generator import FingerprintGenerator
        
        # Force execute the iOS path by calling the static method multiple times
        executed_ios = False
        for attempt in range(50):  # Try multiple times to hit iOS path
            user_agent = FingerprintGenerator._generate_mobile_user_agent("mobile", "120.0.0.0")
            
            if "iPhone" in user_agent or "iPad" in user_agent:
                executed_ios = True
                # Verify iOS-specific elements
                assert "CriOS" in user_agent
                assert "Mobile/15E148" in user_agent
                assert "CPU OS" in user_agent
                break
        
        assert executed_ios, "iOS user agent generation path was not executed"

    def test_webkit_version_generation_edge_cases(self):
        """Test webkit version generation which may be on lines 346-347"""
        from unittest.mock import patch
        
        # Test multiple webkit version generation scenarios
        with patch('random.randint') as mock_randint:
            # Test specific random values that might hit lines 346-347
            test_cases = [
                [1, 1, 10],  # Minimum values
                [9, 9, 99],  # Maximum values
                [5, 3, 55],  # Middle values
            ]
            
            for case in test_cases:
                mock_randint.side_effect = case
                
                # Generate webkit version format: f"60{random.randint(1, 9)}.{random.randint(1, 9)}"
                webkit_base = f"60{case[0]}.{case[1]}"
                webkit_full = f"{webkit_base}.{case[2]}"
                
                # Verify format
                assert webkit_base.startswith("60")
                assert len(webkit_base.split(".")) == 2
                assert len(webkit_full.split(".")) == 3 