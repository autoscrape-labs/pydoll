#!/usr/bin/env python3
"""Test fingerprint browser creation."""

import traceback

def test_browser_creation():
    """Test that fingerprint browsers can be created without errors."""
    print("Testing Chrome import...")
    from pydoll.fingerprint.browser import Chrome, Edge
    print("✓ Import successful")
    
    print("Testing Chrome creation...")
    chrome = Chrome(enable_fingerprint_spoofing=True)
    print("✓ Chrome created successfully")
    
    print("Testing Edge creation...")
    edge = Edge(enable_fingerprint_spoofing=True)
    print("✓ Edge created successfully")
    
    print("Testing fingerprint summary...")
    summary = chrome.get_fingerprint_summary()
    print(f"✓ Fingerprint summary type: {type(summary).__name__}")
    if summary:
        print(f"✓ Browser: {summary.get('Browser', 'N/A')}")
        print(f"✓ User Agent length: {len(summary.get('User Agent', ''))}")
    
    # Assert that browsers were created successfully
    assert chrome is not None, "Chrome browser should be created"
    assert edge is not None, "Edge browser should be created"
    assert summary is not None, "Fingerprint summary should be available"
    assert isinstance(summary, dict), "Summary should be a dictionary"
    
    print("All browser creation tests passed!")

if __name__ == "__main__":
    try:
        test_browser_creation()
        print(f"\nTest result: PASSED")
    except Exception as e:
        print(f"\nTest result: FAILED - {e}")
        traceback.print_exc() 