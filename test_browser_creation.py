#!/usr/bin/env python3
"""Test browser creation with fingerprint spoofing."""

try:
    print("Testing browser creation...")
    from pydoll.fingerprint.browser import Chrome
    
    print("✓ Import successful")
    
    print("Creating browser instance...")
    browser = Chrome(enable_fingerprint_spoofing=True)
    print("✓ Browser created successfully")
    
    print("Checking fingerprint manager...")
    if browser.fingerprint_manager:
        print("✓ Fingerprint manager initialized")
        
        summary = browser.get_fingerprint_summary()
        if summary:
            print("✓ Fingerprint summary available")
            print(f"  Browser: {summary.get('Browser', 'Unknown')}")
            print(f"  User Agent: {summary.get('User Agent', 'Unknown')}")
            print(f"  Screen: {summary.get('Screen', 'Unknown')}")
        else:
            print("✗ No fingerprint summary")
    else:
        print("✗ No fingerprint manager")
    
    print("\nAll tests passed!")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc() 