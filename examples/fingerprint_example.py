"""
Pydoll Browser Fingerprint Spoofing Example

This example demonstrates how to use pydoll's built-in fingerprint spoofing
functionality to avoid browser fingerprinting detection.
"""

import asyncio

# Import fingerprint-enabled browsers
from pydoll.fingerprint import Chrome, Edge, FingerprintConfig


async def basic_fingerprint_example():
    """Basic example: Enable fingerprint spoofing with default settings."""
    print("=== Basic Fingerprint Spoofing Example ===")
    
    # Simply set enable_fingerprint_spoofing=True
    async with Chrome(enable_fingerprint_spoofing=True) as browser:
        tab = await browser.start()
        
        # Print fingerprint summary
        summary = browser.get_fingerprint_summary()
        if summary:
            print("Generated Fingerprint:")
            for key, value in summary.items():
                print(f"  {key}: {value}")
        
        # Visit a fingerprinting test site
        await tab.go_to('https://fingerprintjs.github.io/fingerprintjs/')
        await asyncio.sleep(3)  # Wait for page to load
        
        print("✅ Visited fingerprinting test site with spoofed fingerprint")


async def custom_config_example():
    """Example with custom fingerprint configuration."""
    print("\n=== Custom Configuration Example ===")
    
    # Create custom fingerprint configuration
    config = FingerprintConfig(
        browser_type="chrome",
        preferred_os="windows",  # Force Windows
        min_screen_width=1920,
        max_screen_width=1920,
        min_screen_height=1080,
        max_screen_height=1080,
        enable_webgl_spoofing=True,
        enable_canvas_spoofing=True,
        enable_audio_spoofing=True,
    )
    
    async with Chrome(
        enable_fingerprint_spoofing=True,
        fingerprint_config=config
    ) as browser:
        tab = await browser.start()
        
        # Print custom fingerprint
        summary = browser.get_fingerprint_summary()
        if summary:
            print("Custom Fingerprint:")
            for key, value in summary.items():
                print(f"  {key}: {value}")
        
        # Test on multiple sites
        test_sites = [
            'https://amiunique.org/fp',
            'https://browserleaks.com/javascript',
        ]
        
        for site in test_sites:
            print(f"Testing on: {site}")
            await tab.go_to(site)
            await asyncio.sleep(2)
        
        print("✅ Tested custom fingerprint on multiple sites")


async def edge_fingerprint_example():
    """Example using Edge browser with fingerprinting."""
    print("\n=== Edge Browser Fingerprint Example ===")
    
    async with Edge(enable_fingerprint_spoofing=True) as browser:
        tab = await browser.start()
        
        # Edge automatically uses Edge-specific fingerprints
        summary = browser.get_fingerprint_summary()
        if summary:
            print("Edge Fingerprint:")
            for key, value in summary.items():
                print(f"  {key}: {value}")
        
        await tab.go_to('https://fingerprintjs.github.io/fingerprintjs/')
        await asyncio.sleep(3)
        
        print("✅ Used Edge browser with spoofed fingerprint")


async def fingerprint_persistence_example():
    """Example showing how to save and reuse fingerprints."""
    print("\n=== Fingerprint Persistence Example ===")
    
    # First session: Generate and save fingerprint
    async with Chrome(enable_fingerprint_spoofing=True) as browser:
        tab = await browser.start()
        
        # Save the fingerprint for later reuse
        if browser.fingerprint_manager:
            saved_path = browser.fingerprint_manager.save_fingerprint("my_identity")
            print(f"💾 Saved fingerprint to: {saved_path}")
            
            # Show what fingerprints are available
            saved_fingerprints = browser.fingerprint_manager.list_saved_fingerprints()
            print(f"Available fingerprints: {saved_fingerprints}")
    
    # Second session: Load the same fingerprint
    config = FingerprintConfig()
    async with Chrome(
        enable_fingerprint_spoofing=True,
        fingerprint_config=config
    ) as browser:
        # Load the saved fingerprint
        if browser.fingerprint_manager:
            browser.fingerprint_manager.load_fingerprint("my_identity")
            print("📂 Loaded saved fingerprint")
        
        tab = await browser.start()
        
        # Verify it's the same fingerprint
        summary = browser.get_fingerprint_summary()
        if summary:
            print("Loaded Fingerprint (should be same as before):")
            print(f"  User Agent: {summary['User Agent']}")
            print(f"  Screen: {summary['Screen']}")
        
        await tab.go_to('https://fingerprintjs.github.io/fingerprintjs/')
        await asyncio.sleep(3)
        
        print("✅ Successfully reused saved fingerprint")


async def advanced_fingerprint_management():
    """Advanced example showing fingerprint management features."""
    print("\n=== Advanced Fingerprint Management ===")
    
    # Import the manager directly for advanced usage
    from pydoll.fingerprint import FingerprintManager, FingerprintConfig
    
    # Create manager with custom config
    config = FingerprintConfig(
        browser_type="chrome",
        preferred_os="linux",
        enable_webgl_spoofing=True,
    )
    
    manager = FingerprintManager(config)
    
    # Generate multiple fingerprints
    print("Generating 3 different fingerprints:")
    for i in range(3):
        fingerprint = manager.generate_new_fingerprint(force=True)
        print(f"\nFingerprint {i+1}:")
        print(f"  User Agent: {fingerprint.user_agent}")
        print(f"  Screen: {fingerprint.screen_width}x{fingerprint.screen_height}")
        print(f"  WebGL Vendor: {fingerprint.webgl_vendor}")
        
        # Save each fingerprint
        manager.save_fingerprint(f"fingerprint_{i+1}")
    
    # List all saved fingerprints
    all_fingerprints = manager.list_saved_fingerprints()
    print(f"\nAll saved fingerprints: {all_fingerprints}")
    
    # Use one of the saved fingerprints in a browser
    async with Chrome(enable_fingerprint_spoofing=True) as browser:
        if browser.fingerprint_manager:
            browser.fingerprint_manager.load_fingerprint("fingerprint_2")
            print("\n🎭 Using fingerprint_2 in browser session")
        
        tab = await browser.start()
        await tab.go_to('https://fingerprintjs.github.io/fingerprintjs/')
        await asyncio.sleep(3)
        
        print("✅ Advanced fingerprint management completed")


async def multiple_tabs_example():
    """Example showing fingerprint spoofing across multiple tabs."""
    print("\n=== Multiple Tabs Example ===")
    
    async with Chrome(enable_fingerprint_spoofing=True) as browser:
        # Start with first tab
        tab1 = await browser.start()
        print("Tab 1: Started with fingerprint spoofing")
        
        # Create additional tabs - they all inherit the same fingerprint
        tab2 = await browser.new_tab()
        tab3 = await browser.new_tab()
        print("Created additional tabs with same fingerprint")
        
        # Test each tab on different sites
        test_tasks = [
            tab1.go_to('https://fingerprintjs.github.io/fingerprintjs/'),
            tab2.go_to('https://amiunique.org/fp'),
            tab3.go_to('https://browserleaks.com/javascript'),
        ]
        
        # Run all tabs concurrently
        await asyncio.gather(*test_tasks)
        print("✅ All tabs loaded with consistent fingerprint spoofing")
        
        await asyncio.sleep(3)  # Let pages fully load


async def main():
    """Run all fingerprint spoofing examples."""
    print("🎭 Pydoll Fingerprint Spoofing Examples")
    print("=" * 50)
    
    try:
        await basic_fingerprint_example()
        await custom_config_example()
        await edge_fingerprint_example()
        await fingerprint_persistence_example()
        await advanced_fingerprint_management()
        await multiple_tabs_example()
        
        print("\n" + "=" * 50)
        print("🎉 All fingerprint spoofing examples completed successfully!")
        print("\nKey Features Demonstrated:")
        print("✅ Basic one-line fingerprint spoofing")
        print("✅ Custom fingerprint configuration")
        print("✅ Chrome and Edge browser support")
        print("✅ Fingerprint persistence and reuse")
        print("✅ Advanced fingerprint management")
        print("✅ Multiple tabs with consistent spoofing")
        
    except Exception as e:
        print(f"❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 