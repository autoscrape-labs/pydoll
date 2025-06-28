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
    print("✓ Browser classes imported successfully")
    
    # Test fingerprint configuration imports
    from pydoll.fingerprint import FingerprintConfig, FingerprintManager
    print("✓ Fingerprint configuration imported successfully")
    
    # Test if old imports have been removed
    try:
        from pydoll.fingerprint.browser_options import FingerprintBrowserOptionsManager
        print("✗ Error: Old FingerprintBrowserOptionsManager still exists")
        assert False, "Old FingerprintBrowserOptionsManager still exists"
    except ImportError:
        print("✓ Old FingerprintBrowserOptionsManager correctly removed")

def test_chrome_initialization():
    """Test Chrome browser initialization"""
    print("\n=== Testing Chrome Browser ===")
    
    from pydoll.browser.chromium.chrome import Chrome
    from pydoll.fingerprint import FingerprintConfig
    
    # Test basic initialization
    chrome = Chrome()
    print(f"✓ Chrome basic initialization: fingerprint_spoofing={chrome.enable_fingerprint_spoofing}")
    assert chrome.enable_fingerprint_spoofing == False
    
    # Test with fingerprint spoofing enabled
    chrome_fp = Chrome(enable_fingerprint_spoofing=True)
    print(f"✓ Chrome fingerprint spoofing: enabled={chrome_fp.enable_fingerprint_spoofing}, manager={chrome_fp.fingerprint_manager is not None}")
    assert chrome_fp.enable_fingerprint_spoofing == True
    assert chrome_fp.fingerprint_manager is not None
    
    # Test custom configuration
    config = FingerprintConfig(browser_type="chrome", enable_webgl_spoofing=True)
    chrome_custom = Chrome(enable_fingerprint_spoofing=True, fingerprint_config=config)
    print(f"✓ Chrome custom configuration: enabled={chrome_custom.enable_fingerprint_spoofing}")
    assert chrome_custom.enable_fingerprint_spoofing == True

def test_edge_initialization():
    """Test Edge browser initialization"""
    print("\n=== Testing Edge Browser ===")
    
    from pydoll.browser.chromium.edge import Edge
    from pydoll.fingerprint import FingerprintConfig
    
    # Test basic initialization
    edge = Edge()
    print(f"✓ Edge basic initialization: fingerprint_spoofing={edge.enable_fingerprint_spoofing}")
    assert edge.enable_fingerprint_spoofing == False
    
    # Test with fingerprint spoofing enabled
    edge_fp = Edge(enable_fingerprint_spoofing=True)
    print(f"✓ Edge fingerprint spoofing: enabled={edge_fp.enable_fingerprint_spoofing}, manager={edge_fp.fingerprint_manager is not None}")
    assert edge_fp.enable_fingerprint_spoofing == True
    assert edge_fp.fingerprint_manager is not None

def test_options_manager():
    """Test options manager"""
    print("\n=== Testing Options Manager ===")
    
    from pydoll.browser.managers.browser_options_manager import ChromiumOptionsManager
    from pydoll.fingerprint import FingerprintConfig
    
    # Test basic manager
    manager = ChromiumOptionsManager()
    print(f"✓ Basic manager: fingerprint_spoofing={getattr(manager, 'enable_fingerprint_spoofing', False)}")
    assert getattr(manager, 'enable_fingerprint_spoofing', False) == False
    
    # Test manager with fingerprint spoofing enabled
    config = FingerprintConfig(browser_type="chrome", enable_webgl_spoofing=True)
    manager_fp = ChromiumOptionsManager(enable_fingerprint_spoofing=True, fingerprint_config=config)
    print(f"✓ Fingerprint manager: enabled={manager_fp.enable_fingerprint_spoofing}, manager={manager_fp.fingerprint_manager is not None}")
    assert manager_fp.enable_fingerprint_spoofing == True
    assert manager_fp.fingerprint_manager is not None
    
    # Test options initialization
    options = manager_fp.initialize_options()
    print(f"✓ Options initialization: number of arguments={len(options.arguments)}")
    assert len(options.arguments) >= 2  # Should have at least default arguments

def main():
    """Run all tests"""
    print("🔧 Refactoring Verification Tests")
    print("=" * 50)
    
    # Run tests directly, no need to collect return values
    test_imports()
    test_chrome_initialization()
    test_edge_initialization()
    test_options_manager()
    
    print("\n" + "=" * 50)
    print("🎉 All tests passed! Refactoring successful!")

if __name__ == "__main__":
    main() 