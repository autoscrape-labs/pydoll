#!/usr/bin/env python3
"""Simple fingerprint test."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from pydoll.fingerprint.browser import Chrome

async def simple_test():
    """Simple fingerprint test."""
    print("🎭 Simple Fingerprint Test")
    print("=" * 30)
    
    try:
        print("Creating Chrome browser with fingerprint spoofing...")
        async with Chrome(enable_fingerprint_spoofing=True) as browser:
            print("✓ Browser created successfully")
            
            # Check fingerprint summary
            summary = browser.get_fingerprint_summary()
            if summary:
                print("✓ Fingerprint generated:")
                for key, value in summary.items():
                    print(f"  {key}: {value}")
            
            print("Starting browser...")
            tab = await browser.start()
            print("✓ Browser started successfully")
            
            print("Navigating to test page...")
            await tab.go_to('https://www.google.com')
            print("✓ Navigation successful")
            
            await asyncio.sleep(2)  # Wait a bit
            print("✅ Test completed successfully!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(simple_test()) 