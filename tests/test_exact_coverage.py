import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from pydoll.fingerprint.generator import FingerprintGenerator
from pydoll.fingerprint.manager import FingerprintManager
from pydoll.fingerprint.models import FingerprintConfig
from pydoll.browser.managers.browser_options_manager import ChromiumOptionsManager
from pydoll.browser.options import ChromiumOptions


class TestLine55EarlyReturn:
    """Specific tests for the early return at line 55 in generate_new_fingerprint"""

    def test_line_55_early_return_when_fingerprint_exists_and_no_force(self):
        """
        Test line 55: return self.current_fingerprint - early return in generate_new_fingerprint
        This tests the case when current_fingerprint exists and force=False (default)
        """
        manager = FingerprintManager()
        
        # First, generate a fingerprint to set current_fingerprint
        first_fingerprint = manager.generate_new_fingerprint()
        assert manager.current_fingerprint is first_fingerprint
        
        # Now call generate_new_fingerprint again WITHOUT force=True
        # This should trigger the early return at line 55
        returned_fingerprint = manager.generate_new_fingerprint()
        
        # Verify that line 55 was executed - the same fingerprint was returned
        assert returned_fingerprint is first_fingerprint
        assert returned_fingerprint is manager.current_fingerprint
        
        # Verify no new fingerprint was generated (same object)
        assert id(returned_fingerprint) == id(first_fingerprint)

    def test_line_55_early_return_with_different_browser_types(self):
        """
        Test line 55 early return with different browser types
        """
        manager = FingerprintManager()
        
        # Generate initial fingerprint with chrome
        chrome_fingerprint = manager.generate_new_fingerprint(browser_type='chrome')
        assert manager.current_fingerprint is chrome_fingerprint
        
        # Call generate_new_fingerprint with edge but force=False (default)
        # This should still trigger line 55 early return
        returned_fingerprint = manager.generate_new_fingerprint(browser_type='edge')
        
        # Line 55 should have been executed - same fingerprint returned
        assert returned_fingerprint is chrome_fingerprint
        assert manager.current_fingerprint is chrome_fingerprint

    def test_line_55_early_return_multiple_calls(self):
        """
        Test line 55 early return with multiple sequential calls
        """
        manager = FingerprintManager()
        
        # Generate initial fingerprint
        original_fingerprint = manager.generate_new_fingerprint()
        
        # Multiple calls without force should all trigger line 55
        for i in range(5):
            returned_fingerprint = manager.generate_new_fingerprint()
            
            # Each call should execute line 55 and return the same fingerprint
            assert returned_fingerprint is original_fingerprint
            assert manager.current_fingerprint is original_fingerprint

    def test_line_55_early_return_vs_force_generation(self):
        """
        Test the difference between line 55 early return and force generation
        """
        manager = FingerprintManager()
        
        # Generate initial fingerprint
        first_fingerprint = manager.generate_new_fingerprint()
        
        # Call without force - should hit line 55
        same_fingerprint = manager.generate_new_fingerprint(force=False)
        assert same_fingerprint is first_fingerprint  # Line 55 executed
        
        # Call with force=True - should NOT hit line 55, creates new fingerprint
        new_fingerprint = manager.generate_new_fingerprint(force=True)
        assert new_fingerprint is not first_fingerprint  # Line 55 NOT executed
        assert manager.current_fingerprint is new_fingerprint

    def test_line_55_early_return_with_explicit_force_false(self):
        """
        Test line 55 with explicitly setting force=False
        """
        manager = FingerprintManager()
        
        # Generate initial fingerprint
        initial_fingerprint = manager.generate_new_fingerprint()
        
        # Explicitly set force=False to trigger line 55
        returned_fingerprint = manager.generate_new_fingerprint(force=False)
        
        # Verify line 55 was executed
        assert returned_fingerprint is initial_fingerprint
        assert manager.current_fingerprint is initial_fingerprint


class TestLine55And262Coverage:
    """Precise tests specifically targeting line 55 and line 262"""

    def test_line_55_get_current_fingerprint_return_statement(self):
        """
        Specifically test manager.py line 55: return self.current_fingerprint
        """
        manager = FingerprintManager()
        
        # Case 1: current_fingerprint is None
        assert manager.current_fingerprint is None
        result = manager.get_current_fingerprint()  # Execute line 55
        assert result is None
        
        # Case 2: current_fingerprint exists
        fingerprint = manager.generate_new_fingerprint()
        assert manager.current_fingerprint is not None
        result = manager.get_current_fingerprint()  # Execute line 55 again
        assert result is fingerprint
        assert result is manager.current_fingerprint

    def test_line_262_get_fingerprint_summary_return_statement(self):
        """
        Specifically test manager.py line 262: return { ... } - return statement of get_fingerprint_summary method
        """
        manager = FingerprintManager()
        
        # Generate a fingerprint for testing summary
        fingerprint = manager.generate_new_fingerprint()
        
        # Call get_fingerprint_summary - this executes line 262's return { statement
        summary = manager.get_fingerprint_summary()
        
        # Verify the returned dictionary structure and content
        assert isinstance(summary, dict)
        expected_keys = [
            'Browser', 'User Agent', 'Platform', 'Language', 'Screen',
            'Viewport', 'WebGL Vendor', 'WebGL Renderer', 'Hardware Concurrency',
            'Device Memory', 'Timezone', 'Canvas Fingerprint'
        ]
        for key in expected_keys:
            assert key in summary
        
        # Verify specific content
        assert fingerprint.browser_type.title() in summary['Browser']
        assert summary['User Agent'] == fingerprint.user_agent
        assert summary['Platform'] == fingerprint.platform

    def test_line_262_with_explicit_fingerprint_parameter(self):
        """
        Test line 262 using explicit fingerprint parameter
        """
        manager = FingerprintManager()
        
        # Generate two fingerprints
        fp1 = manager.generate_new_fingerprint()
        manager.clear_current_fingerprint()
        fp2 = manager.generate_new_fingerprint(force=True)
        
        # Call get_fingerprint_summary with explicit fingerprint parameter - executes line 262
        summary1 = manager.get_fingerprint_summary(fp1)
        summary2 = manager.get_fingerprint_summary(fp2)
        
        # Verify summaries are different
        assert summary1['User Agent'] != summary2['User Agent']
        assert isinstance(summary1, dict)
        assert isinstance(summary2, dict)

    def test_both_lines_in_sequence(self):
        """
        Test both lines sequentially in one test
        """
        manager = FingerprintManager()
        
        # Test line 55 - when None
        result = manager.get_current_fingerprint()  # Line 55
        assert result is None
        
        # Generate fingerprint
        fingerprint = manager.generate_new_fingerprint()
        
        # Test line 55 - when exists
        current = manager.get_current_fingerprint()  # Line 55
        assert current is fingerprint
        
        # Test line 262 - get_fingerprint_summary
        summary = manager.get_fingerprint_summary()  # Line 262
        assert isinstance(summary, dict)
        assert 'Browser' in summary
        assert 'User Agent' in summary

    def test_multiple_calls_ensure_line_coverage(self):
        """
        Multiple calls to ensure line coverage
        """
        manager = FingerprintManager()
        
        # Multiple calls to line 55
        for i in range(10):
            result = manager.get_current_fingerprint()  # Line 55
            assert result is None
        
        # Generate fingerprint
        fingerprint = manager.generate_new_fingerprint()
        
        # Multiple calls to line 55 and line 262
        for i in range(10):
            current = manager.get_current_fingerprint()  # Line 55
            assert current is fingerprint
            
            summary = manager.get_fingerprint_summary()  # Line 262
            assert isinstance(summary, dict)

    def test_line_262_edge_cases(self):
        """
        Test edge cases for line 262
        """
        manager = FingerprintManager()
        
        # Use different browser types to generate fingerprints
        browser_types = ['chrome', 'edge']
        
        for browser_type in browser_types:
            fingerprint = manager.generate_new_fingerprint(browser_type=browser_type, force=True)
            
            # Test line 262 - return dictionary statement
            summary = manager.get_fingerprint_summary()  # Line 262
            
            assert isinstance(summary, dict)
            assert browser_type.title() in summary['Browser']
            
            # Clear current fingerprint
            manager.clear_current_fingerprint()
            
            # Test line 262 again with explicit parameter
            summary_explicit = manager.get_fingerprint_summary(fingerprint)  # Line 262
            assert summary == summary_explicit


class TestDirectLineCoverage:
    """Direct and simple tests for specific uncovered lines - merged from verification script"""

    def test_line_55_when_none(self):
        """
        Direct test for line 55: return self.current_fingerprint (when None)
        """
        manager = FingerprintManager()
        
        # Ensure current_fingerprint is None
        assert manager.current_fingerprint is None
        
        # Call get_current_fingerprint - EXECUTES LINE 55: return self.current_fingerprint
        result = manager.get_current_fingerprint()
        
        # Verify line 55 returned None correctly
        assert result is None

    def test_line_55_when_exists(self):
        """
        Direct test for line 55: return self.current_fingerprint (when exists)
        """
        manager = FingerprintManager()
        
        # Generate a fingerprint to set current_fingerprint
        fingerprint = manager.generate_new_fingerprint()
        assert manager.current_fingerprint is not None
        assert manager.current_fingerprint is fingerprint
        
        # Call get_current_fingerprint - EXECUTES LINE 55: return self.current_fingerprint
        result = manager.get_current_fingerprint()
        
        # Verify line 55 was executed correctly
        assert result is fingerprint
        assert result is manager.current_fingerprint

    def test_line_262_return_false(self):
        """
        Direct test for line 262: return False (when file doesn't exist)
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = FingerprintManager()
            manager.storage_dir = Path(temp_dir)
            
            # Ensure directory is empty
            assert len(list(manager.storage_dir.glob("*.json"))) == 0
            
            # Try to delete non-existent file - EXECUTES return False LINE
            result = manager.delete_fingerprint("nonexistent_file")
            
            # Verify False was returned (line 262 executed)
            assert result is False

    def test_line_262_multiple_names(self):
        """
        Test line 262 with multiple different non-existent file names
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = FingerprintManager()
            manager.storage_dir = Path(temp_dir)
            
            # Test various non-existent file names
            test_names = ["fake", "test", "nonexistent", "", "long_name_that_doesnt_exist", "another_fake"]
            
            for name in test_names:
                # Each call should execute the return False line
                result = manager.delete_fingerprint(name)
                assert result is False

    def test_comprehensive_workflow(self):
        """
        Complete workflow test that covers both lines 55 and 262
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = FingerprintManager()
            manager.storage_dir = Path(temp_dir)
            
            # Test line 55 (when None)
            assert manager.get_current_fingerprint() is None  # Executes line 55
            
            # Generate fingerprint
            fp = manager.generate_new_fingerprint()
            
            # Test line 55 (when not None)  
            current = manager.get_current_fingerprint()  # Executes line 55
            assert current is fp
            
            # Test line 262
            result = manager.delete_fingerprint("fake_file")  # Executes return False line
            assert result is False
            
            # Test state changes and line 55 again
            manager.clear_current_fingerprint()
            assert manager.get_current_fingerprint() is None  # Executes line 55

    def test_multiple_calls_for_coverage_assurance(self):
        """
        Multiple calls to ensure the lines are definitely hit during coverage measurement
        """
        manager = FingerprintManager()
        
        # Multiple calls to get_current_fingerprint (line 55) when None
        for i in range(10):
            result = manager.get_current_fingerprint()
            assert result is None
        
        # Generate fingerprint
        fp = manager.generate_new_fingerprint()
        
        # Multiple calls when fingerprint exists (line 55)
        for i in range(10):
            result = manager.get_current_fingerprint()
            assert result is fp
        
        # Multiple calls to delete_fingerprint (return False line 262)
        with tempfile.TemporaryDirectory() as temp_dir:
            manager.storage_dir = Path(temp_dir)
            for i in range(10):
                result = manager.delete_fingerprint(f"fake_{i}")
                assert result is False

    def test_state_transitions_line_55(self):
        """
        Test manager state transitions to thoroughly cover line 55
        """
        manager = FingerprintManager()
        
        # Initial state - line 55 returns None
        assert manager.get_current_fingerprint() is None
        assert manager.get_current_fingerprint() is None  # Call again
        
        # After generating - line 55 returns fingerprint
        fp1 = manager.generate_new_fingerprint()
        assert manager.get_current_fingerprint() is fp1
        assert manager.get_current_fingerprint() is fp1  # Call again
        
        # After forcing new - line 55 returns new fingerprint  
        fp2 = manager.generate_new_fingerprint(force=True)
        assert manager.get_current_fingerprint() is fp2
        assert manager.get_current_fingerprint() is fp2  # Call again
        
        # After clearing - line 55 returns None again
        manager.clear_current_fingerprint()
        assert manager.get_current_fingerprint() is None
        assert manager.get_current_fingerprint() is None  # Call again

    def test_edge_cases_line_262(self):
        """
        Edge cases for line 262 to ensure complete coverage
        """
        # Test with different temporary directories
        for i in range(5):
            with tempfile.TemporaryDirectory() as temp_dir:
                manager = FingerprintManager()
                manager.storage_dir = Path(temp_dir)
                
                # Test the return False line with different names
                assert manager.delete_fingerprint(f"test_{i}") is False
                assert manager.delete_fingerprint("") is False  # Empty string
                assert manager.delete_fingerprint("a" * 100) is False  # Long name


class TestExactLineCoverage:
    """Additional focused tests for specific uncovered lines"""

    def test_line_55_return_current_fingerprint_when_exists(self):
        """
        Test manager.py#L55 - get_current_fingerprint returns current fingerprint
        Directly tests the return statement at line 55
        """
        manager = FingerprintManager()
        
        # Ensure it starts with None
        assert manager.current_fingerprint is None
        
        # Generate a fingerprint to set current_fingerprint
        fingerprint = manager.generate_new_fingerprint()
        assert manager.current_fingerprint is not None
        assert manager.current_fingerprint is fingerprint
        
        # Call get_current_fingerprint - THIS EXECUTES LINE 55: return self.current_fingerprint
        result = manager.get_current_fingerprint()
        
        # Verify line 55 was executed correctly
        assert result is fingerprint
        assert result is manager.current_fingerprint

    def test_line_55_return_current_fingerprint_when_none(self):
        """
        Additional test for line 55 when current_fingerprint is None
        """
        manager = FingerprintManager()
        
        # Ensure current_fingerprint is None
        assert manager.current_fingerprint is None
        
        # Call get_current_fingerprint - THIS ALSO EXECUTES LINE 55: return self.current_fingerprint
        result = manager.get_current_fingerprint()
        
        # Verify line 55 returned None correctly
        assert result is None

    def test_line_262_delete_fingerprint_return_false(self):
        """
        Test manager.py#L262 - delete_fingerprint returns False when file doesn't exist
        Directly tests the return False statement
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = FingerprintManager()
            manager.storage_dir = Path(temp_dir)
            
            # Ensure directory is empty
            assert len(list(manager.storage_dir.glob("*.json"))) == 0
            
            # Try to delete non-existent file - THIS EXECUTES THE return False LINE
            result = manager.delete_fingerprint("nonexistent_file")
            
            # Verify False was returned (line 262 executed)
            assert result is False

    def test_line_262_with_various_nonexistent_names(self):
        """
        Additional tests for line 262 with different non-existent names
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = FingerprintManager()
            manager.storage_dir = Path(temp_dir)
            
            # Test various non-existent file names
            test_names = ["fake", "test", "nonexistent", "", "long_name_that_doesnt_exist"]
            
            for name in test_names:
                # Each call should execute the return False line
                result = manager.delete_fingerprint(name)
                assert result is False

    def test_complete_workflow_covering_both_lines(self):
        """
        Complete test that covers both lines 55 and 262 in one workflow
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = FingerprintManager()
            manager.storage_dir = Path(temp_dir)
            
            # Test line 55 (when None)
            assert manager.get_current_fingerprint() is None  # Executes line 55
            
            # Generate fingerprint
            fp = manager.generate_new_fingerprint()
            
            # Test line 55 (when not None)  
            current = manager.get_current_fingerprint()  # Executes line 55
            assert current is fp
            
            # Test line 262
            result = manager.delete_fingerprint("fake")  # Executes return False line
            assert result is False

    def test_multiple_calls_to_ensure_coverage(self):
        """
        Multiple calls to the methods to ensure the lines are definitely hit
        """
        manager = FingerprintManager()
        
        # Multiple calls to get_current_fingerprint (line 55)
        for _ in range(5):
            result = manager.get_current_fingerprint()
            assert result is None
        
        # Generate fingerprint
        fp = manager.generate_new_fingerprint()
        
        # Multiple calls when fingerprint exists (line 55)
        for _ in range(5):
            result = manager.get_current_fingerprint()
            assert result is fp
        
        # Multiple calls to delete_fingerprint (return False line)
        with tempfile.TemporaryDirectory() as temp_dir:
            manager.storage_dir = Path(temp_dir)
            for i in range(5):
                result = manager.delete_fingerprint(f"fake_{i}")
                assert result is False

    def test_manager_state_changes_line_55(self):
        """
        Test state changes to ensure line 55 is covered in all scenarios
        """
        manager = FingerprintManager()
        
        # Initial state - line 55 returns None
        assert manager.get_current_fingerprint() is None
        
        # After generating - line 55 returns fingerprint
        fp1 = manager.generate_new_fingerprint()
        assert manager.get_current_fingerprint() is fp1
        
        # After forcing new - line 55 returns new fingerprint  
        fp2 = manager.generate_new_fingerprint(force=True)
        assert manager.get_current_fingerprint() is fp2
        
        # After clearing - line 55 returns None again
        manager.clear_current_fingerprint()
        assert manager.get_current_fingerprint() is None

    def test_edge_case_scenarios(self):
        """Test edge cases to ensure complete coverage"""
        
        # Test with different temporary directories
        for i in range(3):
            with tempfile.TemporaryDirectory() as temp_dir:
                manager = FingerprintManager()
                manager.storage_dir = Path(temp_dir)
                
                # Test the return False line
                assert manager.delete_fingerprint(f"test_{i}") is False
        
        # Test get_current_fingerprint in different scenarios
        manager = FingerprintManager()
        
        # Before any fingerprint
        assert manager.get_current_fingerprint() is None
        
        # With fingerprint
        fp = manager.generate_new_fingerprint() 
        assert manager.get_current_fingerprint() is fp
        
        # Multiple calls
        assert manager.get_current_fingerprint() is fp
        assert manager.get_current_fingerprint() is fp


class TestExactCoverage:
    """Legacy tests merged for compatibility"""

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

    def test_browser_options_manager_line_71_no_fingerprint_manager(self):
        """Test browser_options_manager.py#L71 - early return when no fingerprint manager"""
        # Create manager without fingerprint spoofing enabled
        manager = ChromiumOptionsManager()
        manager.options = ChromiumOptions()
        
        # Manually set fingerprint_manager to None to ensure we hit line 71
        manager.fingerprint_manager = None
        
        # Call _apply_fingerprint_spoofing - should return early at line 71
        result = manager._apply_fingerprint_spoofing()
        assert result is None

    def test_comprehensive_integration_all_lines(self):
        """
        Final comprehensive test that ensures all target lines are covered
        """
        # Test generator fallback (line 335)
        config = FingerprintConfig()
        config.browser_type = 'unsupported_browser'
        config.is_mobile = False
        generator = FingerprintGenerator(config)
        
        os_info = {'name': 'Windows', 'version': '10.0'}
        user_agent = generator._generate_user_agent(os_info, '120.0.0.0')
        assert 'Chrome' in user_agent  # Should fallback to Chrome
        
        # Test unique properties 
        unique_props = FingerprintGenerator._generate_unique_properties()
        assert "unique_id" in unique_props
        
        # Test manager lines 55 and 262
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = FingerprintManager()
            manager.storage_dir = Path(temp_dir)
            
            # Line 55 tests
            assert manager.get_current_fingerprint() is None  # Line 55
            fp = manager.generate_new_fingerprint()
            assert manager.get_current_fingerprint() is fp  # Line 55
            
            # Test the early return line 55 in generate_new_fingerprint
            same_fp = manager.generate_new_fingerprint()  # Should execute line 55 early return
            assert same_fp is fp
            
            # Test get_fingerprint_summary (this might be line 262)
            summary = manager.get_fingerprint_summary()  # Possible line 262
            assert isinstance(summary, dict)
            
            # Line 262 test for delete_fingerprint
            assert manager.delete_fingerprint("nonexistent") is False  # Possible line 262
            
        # Test browser options manager (line 71)
        options_manager = ChromiumOptionsManager()
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
        options_manager = ChromiumOptionsManager()
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
        options = ChromiumOptions()
        options.enable_fingerprint_spoofing_mode()
        manager_enabled = ChromiumOptionsManager(options)
        manager_enabled.fingerprint_manager = None  # Manually set to None
        
        # This should hit line 71 early return
        result = manager_enabled._apply_fingerprint_spoofing()
        assert result is None
        
        # Test fingerprint spoofing disabled
        manager_disabled = ChromiumOptionsManager()
        manager_disabled.options = ChromiumOptions()
        assert manager_disabled.fingerprint_manager is None
        
        # This should also hit line 71
        result = manager_disabled._apply_fingerprint_spoofing()
        assert result is None 
