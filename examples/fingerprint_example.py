"""
Fingerprint Spoofing Feature Examples

Demonstrates how to use pydoll's fingerprint spoofing features to prevent browser
fingerprint tracking.
"""

import asyncio
import traceback

from pydoll.fingerprint import FingerprintConfig, FingerprintManager
from pydoll.fingerprint.browser import Chrome, Edge


async def basic_example():
    """Basic example: Enable fingerprint spoofing with one click"""
    print("=== Basic Example: Enable Fingerprint Spoofing ===")

    # Create Chrome browser with fingerprint spoofing enabled
    browser = Chrome(enable_fingerprint_spoofing=True)

    async with browser:
        # Start browser
        tab = await browser.start()

        # Visit fingerprint detection website
        await tab.go_to("https://fingerprintjs.github.io/fingerprintjs/")

        # Wait for page to load
        await asyncio.sleep(5)

        # Get fingerprint ID
        try:
            fingerprint_element = await tab.find_element("css", ".visitor-id")
            if fingerprint_element:
                fingerprint_id = await fingerprint_element.text
                print(f"Generated fingerprint ID: {fingerprint_id}")
        except Exception as e:
            print(f"Failed to get fingerprint ID: {e}")

        # Take screenshot to save result
        try:
            await tab.take_screenshot("fingerprint_result.png")
            print("Screenshot saved as fingerprint_result.png")
        except Exception as e:
            print(f"Screenshot failed: {e}")

        await asyncio.sleep(3)


async def custom_config_example():
    """Advanced example: Custom fingerprint configuration"""
    print("\n=== Advanced Example: Custom Fingerprint Configuration ===")

    # Create custom fingerprint configuration
    config = FingerprintConfig(
        # Select features to spoof
        spoof_user_agent=True,
        spoof_screen=True,
        spoof_hardware=True,
        spoof_webgl=True,
        spoof_canvas=True,
        spoof_audio=True,
        spoof_webrtc=True,

        # Custom settings
        browser_type="chrome",
        os_type="windows",
        device_type="desktop",
        custom_languages=["zh-CN", "zh", "en-US", "en"],
        custom_screen_resolution=(2560, 1440),
    )

    # Create browser instance
    browser = Chrome(
        enable_fingerprint_spoofing=True,
        fingerprint_config=config
    )

    async with browser:
        tab = await browser.start()

        # Visit browser information detection website
        await tab.go_to("https://browserleaks.com/javascript")

        await asyncio.sleep(5)

        # Get and print some browser information
        try:
            user_agent = await tab.execute_script("return navigator.userAgent")
            print(f"User Agent: {user_agent}")

            platform = await tab.execute_script("return navigator.platform")
            print(f"Platform: {platform}")

            screen_info = await tab.execute_script("""
                return {
                    width: screen.width,
                    height: screen.height,
                    colorDepth: screen.colorDepth
                }
            """)
            print(f"Screen info: {screen_info}")
        except Exception as e:
            print(f"Failed to get browser information: {e}")

        await asyncio.sleep(3)


async def persistent_fingerprint_example():
    """Persistent fingerprint example: Save and reuse fingerprints"""
    print("\n=== Persistent Fingerprint Example ===")

    # Create fingerprint manager
    fingerprint_manager = FingerprintManager()

    # Configure persistent fingerprint
    config = FingerprintConfig(
        persist_fingerprint=True,
        fingerprint_id="my_persistent_fingerprint"
    )

    # First use: Generate and save fingerprint
    print("First visit: Generate new fingerprint")
    browser1 = Chrome(
        enable_fingerprint_spoofing=True,
        fingerprint_config=config
    )

    async with browser1:
        tab = await browser1.start()
        await tab.go_to("https://amiunique.org/fingerprint")
        await asyncio.sleep(5)

        # Get current fingerprint
        current_fingerprint = fingerprint_manager.current_fingerprint
        if current_fingerprint:
            print(f"Current User Agent: {current_fingerprint.user_agent}")
            print(f"Current platform: {current_fingerprint.platform}")

    # Second use: Load saved fingerprint
    print("\nSecond visit: Use same fingerprint")

    # Load previously saved fingerprint
    saved_fingerprint = fingerprint_manager.load_fingerprint("my_persistent_fingerprint")
    if saved_fingerprint:
        print(f"Loaded User Agent: {saved_fingerprint.user_agent}")
        print(f"Loaded platform: {saved_fingerprint.platform}")

    # List all saved fingerprints
    all_fingerprints = fingerprint_manager.list_fingerprints()
    print(f"\nAll saved fingerprints: {list(all_fingerprints.keys())}")


async def multiple_browsers_example():
    """Multiple browsers example: Run multiple browsers with different fingerprints
    simultaneously"""
    print("\n=== Multiple Browsers Example ===")

    # Create two browsers with different fingerprints
    browser1 = Chrome(enable_fingerprint_spoofing=True)
    browser2 = Chrome(enable_fingerprint_spoofing=True)

    async with browser1, browser2:
        # Start both browsers
        tab1 = await browser1.start()
        tab2 = await browser2.start()

        # Both visit the same fingerprint detection website
        await tab1.go_to("https://fingerprintjs.github.io/fingerprintjs/")
        await tab2.go_to("https://fingerprintjs.github.io/fingerprintjs/")

        await asyncio.sleep(5)

        # Get fingerprint IDs from both browsers
        try:
            fp_element1 = await tab1.find_element("css", ".visitor-id")
            fp_element2 = await tab2.find_element("css", ".visitor-id")

            if fp_element1 and fp_element2:
                fp_id1 = await fp_element1.text
                fp_id2 = await fp_element2.text

                print(f"Browser 1 fingerprint ID: {fp_id1}")
                print(f"Browser 2 fingerprint ID: {fp_id2}")

                if fp_id1 != fp_id2:
                    print("✓ Success: Two browsers generated different fingerprints!")
                else:
                    print("✗ Warning: Both browsers have the same fingerprint")
        except Exception as e:
            print(f"Failed to get fingerprint ID: {e}")

        await asyncio.sleep(3)


async def edge_browser_example():
    """Edge browser example"""
    print("\n=== Edge Browser Example ===")

    # Create Edge browser with fingerprint spoofing enabled
    browser = Edge(enable_fingerprint_spoofing=True)

    async with browser:
        tab = await browser.start()

        await tab.go_to("https://www.whatismybrowser.com/")
        await asyncio.sleep(5)

        # Check browser identification
        try:
            browser_info = await tab.execute_script("""
                return {
                    userAgent: navigator.userAgent,
                    appVersion: navigator.appVersion,
                    vendor: navigator.vendor
                }
            """)

            print(f"Edge browser info: {browser_info}")
        except Exception as e:
            print(f"Failed to get browser information: {e}")

        await asyncio.sleep(3)


async def main():
    """Run all examples"""
    try:
        # Run basic example
        await basic_example()

        # Run custom configuration example
        await custom_config_example()

        # Run persistent fingerprint example
        await persistent_fingerprint_example()

        # Run multiple browsers example
        await multiple_browsers_example()

        # Run Edge browser example
        await edge_browser_example()

    except Exception as e:
        print(f"Error running examples: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    # Run examples
    asyncio.run(main())
