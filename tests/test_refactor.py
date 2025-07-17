#!/usr/bin/env python3
"""
Test file to verify fingerprint spoofing functionality after refactoring
"""

def test_imports():
    """Test if all imports work properly"""
    print("=== Testing Imports ===")
    
    # Test browser class imports
    from pydoll.browser.chromium.chrome import Chrome
    from pydoll.browser.chromium.edge import Edge
    print("[PASS] Browser classes imported successfully")
    
    # Test fingerprint configuration imports
    from pydoll.fingerprint import FingerprintConfig, FingerprintManager
    print("[PASS] Fingerprint configuration imported successfully")
    
    # Test if old imports have been removed
    try:
        from pydoll.fingerprint.browser_options import FingerprintBrowserOptionsManager
        print("[FAIL] Error: Old FingerprintBrowserOptionsManager still exists")
        assert False, "Old FingerprintBrowserOptionsManager still exists"
    except ImportError:
        print("[PASS] Old FingerprintBrowserOptionsManager correctly removed")

def test_chrome_initialization():
    """Test Chrome browser initialization"""
    print("\n=== Testing Chrome Browser ===")
    
    from pydoll.browser.chromium.chrome import Chrome
    from pydoll.browser.options import ChromiumOptions
    from pydoll.fingerprint import FingerprintConfig
    
    # Test basic initialization
    chrome = Chrome()
    print(f"[PASS] Chrome basic initialization: fingerprint_spoofing={chrome.enable_fingerprint_spoofing}")
    assert chrome.enable_fingerprint_spoofing == False
    
    # Test with fingerprint spoofing enabled
    options_fp = ChromiumOptions()
    options_fp.enable_fingerprint_spoofing_mode()
    chrome_fp = Chrome(options=options_fp)
    print(f"[PASS] Chrome fingerprint spoofing: enabled={chrome_fp.enable_fingerprint_spoofing}, manager={chrome_fp.fingerprint_manager is not None}")
    assert chrome_fp.enable_fingerprint_spoofing == True
    assert chrome_fp.fingerprint_manager is not None
    
    # Test custom configuration
    config = FingerprintConfig(browser_type="chrome", enable_webgl_spoofing=True)
    options_custom = ChromiumOptions()
    options_custom.enable_fingerprint_spoofing_mode(config=config)
    chrome_custom = Chrome(options=options_custom)
    print(f"[PASS] Chrome custom configuration: enabled={chrome_custom.enable_fingerprint_spoofing}")
    assert chrome_custom.enable_fingerprint_spoofing == True

def test_edge_initialization():
    """Test Edge browser initialization"""
    print("\n=== Testing Edge Browser ===")
    
    from pydoll.browser.chromium.edge import Edge
    from pydoll.browser.options import ChromiumOptions
    from pydoll.fingerprint import FingerprintConfig
    
    # Test basic initialization
    edge = Edge()
    print(f"[PASS] Edge basic initialization: fingerprint_spoofing={edge.enable_fingerprint_spoofing}")
    assert edge.enable_fingerprint_spoofing == False
    
    # Test with fingerprint spoofing enabled
    options_fp = ChromiumOptions()
    options_fp.enable_fingerprint_spoofing_mode()
    edge_fp = Edge(options=options_fp)
    print(f"[PASS] Edge fingerprint spoofing: enabled={edge_fp.enable_fingerprint_spoofing}, manager={edge_fp.fingerprint_manager is not None}")
    assert edge_fp.enable_fingerprint_spoofing == True
    assert edge_fp.fingerprint_manager is not None

def test_options_manager():
    """Test options manager"""
    print("\n=== Testing Options Manager ===")
    
    from pydoll.browser.managers.browser_options_manager import ChromiumOptionsManager
    from pydoll.browser.options import ChromiumOptions
    from pydoll.fingerprint import FingerprintConfig
    
    # Test basic manager
    manager = ChromiumOptionsManager()
    print(f"[PASS] Basic manager: fingerprint_manager={manager.fingerprint_manager is None}")
    assert manager.fingerprint_manager is None
    
    # Test manager with fingerprint spoofing enabled
    config = FingerprintConfig(browser_type="chrome", enable_webgl_spoofing=True)
    options = ChromiumOptions()
    options.enable_fingerprint_spoofing_mode(config=config)
    manager_fp = ChromiumOptionsManager(options=options)
    
    # Initialize options to create fingerprint manager
    initialized_options = manager_fp.initialize_options()
    print(f"[PASS] Fingerprint manager: enabled={initialized_options.enable_fingerprint_spoofing}, manager={manager_fp.fingerprint_manager is not None}")
    assert initialized_options.enable_fingerprint_spoofing == True
    assert manager_fp.fingerprint_manager is not None
    
    # Test options initialization
    print(f"[PASS] Options initialization: number of arguments={len(initialized_options.arguments)}")
    assert len(initialized_options.arguments) >= 2  # Should have at least default arguments

def main():
    """Run all tests"""
    print("[INFO] Refactoring Verification Tests")
    print("=" * 50)
    
    # Run tests directly, no need to collect return values
    test_imports()
    test_chrome_initialization()
    test_edge_initialization()
    test_options_manager()
    
    print("\n" + "=" * 50)
    print("[SUCCESS] All tests passed! Refactoring successful!")

if __name__ == "__main__":
    main() 