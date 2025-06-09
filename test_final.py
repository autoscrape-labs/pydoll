#!/usr/bin/env python3
"""Final test for fingerprint spoofing functionality."""

import sys
import traceback
import asyncio

def test_browser_creation():
    """Test browser creation."""
    print("=== Testing Browser Creation ===")
    from pydoll.fingerprint.browser import Chrome, Edge
    print("✓ Import successful")
    
    print("Creating Chrome with fingerprint spoofing...")
    chrome = Chrome(enable_fingerprint_spoofing=True)
    print("✓ Chrome created")
    
    print("Creating Edge with fingerprint spoofing...")
    edge = Edge(enable_fingerprint_spoofing=True)
    print("✓ Edge created")
    
    print("Getting fingerprint summary...")
    summary = chrome.get_fingerprint_summary()
    print(f"✓ Summary type: {type(summary).__name__}")
    if summary:
        print(f"✓ Browser: {summary.get('Browser', 'N/A')}")
        print(f"✓ User agent length: {len(summary.get('User Agent', ''))}")
        print(f"✓ Platform: {summary.get('Platform', 'N/A')}")
    
    # Assertions for pytest compatibility
    assert chrome is not None
    assert edge is not None
    assert summary is not None

def test_fingerprint_example():
    """Test the original fingerprint example."""
    print("\n=== Testing Fingerprint Example ===")
    
    async def simple_test():
        from pydoll.fingerprint.browser import Chrome
        print("Starting browser...")
        
        # Create browser with fingerprint spoofing
        async with Chrome(enable_fingerprint_spoofing=True) as browser:
            print("✓ Browser started successfully")
            summary = browser.get_fingerprint_summary()
            if summary:
                print(f"✓ Active fingerprint: {summary.get('Browser', 'Unknown')}")
            return summary
    
    # Run the async test
    result = asyncio.run(simple_test())
    
    # Assertions for pytest compatibility
    assert result is not None, "Should get fingerprint summary"
    assert isinstance(result, dict), "Summary should be a dictionary"
    assert 'Browser' in result, "Summary should contain Browser information"

def main():
    """Run all tests."""
    print("🎭 Pydoll Fingerprint Spoofing - Final Test")
    print("=" * 50)
    
    results = []
    
    # Test 1: Browser creation
    results.append(test_browser_creation())
    
    # Test 2: Example functionality
    results.append(test_fingerprint_example())
    
    # Summary
    print("\n" + "=" * 50)
    passed = sum(results)
    total = len(results)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests PASSED!")
        return 0
    else:
        print("❌ Some tests FAILED!")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"Fatal error: {e}")
        traceback.print_exc()
        sys.exit(1) 