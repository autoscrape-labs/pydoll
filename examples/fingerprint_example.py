"""
Fingerprint Spoofing Feature Examples

Demonstrates how to use pydoll's fingerprint spoofing features to prevent browser
fingerprint tracking.
"""

import asyncio
import traceback

from pydoll.browser.chromium.chrome import Chrome
from pydoll.browser.chromium.edge import Edge
from pydoll.browser.options import ChromiumOptions
from pydoll.fingerprint import FingerprintConfig, FingerprintManager


async def basic_example():
    """Basic example: Enable fingerprint spoofing with one click"""
    print("=== Basic Example: Enable Fingerprint Spoofing ===")

    # Create Chrome browser with fingerprint spoofing enabled
    options = ChromiumOptions()
    options.enable_fingerprint_spoofing_mode()
    browser = Chrome(options=options)

    async with browser:
        # Start browser
        tab = await browser.start()

        # Visit fingerprint detection website
        await tab.go_to("https://fingerprintjs.github.io/fingerprintjs/")

        # Wait for page to load
        await asyncio.sleep(5)

        # Get fingerprint ID
        try:
            # Wait enough time for fingerprint generation
            await asyncio.sleep(3)

            # Try to use a more generic selector or directly execute JavaScript
            # to get fingerprint ID
            fingerprint_id = await tab.execute_script("""
                // Wait for fingerprint generation to complete
                if (window.fingerprintJsResult) {
                    return window.fingerprintJsResult.visitorId || 'No ID found';
                } else if (document.querySelector(".visitor-id")) {
                    return document.querySelector(".visitor-id").textContent;
                } else if (document.getElementById("fp-result")) {
                    return document.getElementById("fp-result").textContent;
                } else {
                    // Try to find any element containing a fingerprint ID
                    const elements = document.querySelectorAll('*');
                    for (const el of elements) {
                        if (el.textContent && el.textContent.match(/[a-f0-9]{32}/)) {
                            return el.textContent.match(/[a-f0-9]{32}/)[0];
                        }
                    }
                    return 'Could not find fingerprint ID on page';
                }
            """)
            print(f"Generated fingerprint ID: {fingerprint_id}")
        except Exception as e:
            print(f"Failed to get fingerprint ID: {e}")
            traceback.print_exc()

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
        # Configure browser and OS settings
        browser_type="chrome",
        preferred_os="windows",
        is_mobile=False,

        # Configure fingerprinting protection features
        enable_webgl_spoofing=True,
        enable_canvas_spoofing=True,
        enable_audio_spoofing=True,
        enable_webrtc_spoofing=True,

        # Custom settings
        preferred_languages=["zh-CN", "zh", "en-US", "en"],
        min_screen_width=1920,
        max_screen_width=2560,
        min_screen_height=1080,
        max_screen_height=1440
    )

    # Create browser instance
    options = ChromiumOptions()
    options.enable_fingerprint_spoofing_mode(config=config)
    browser = Chrome(options=options)

    async with browser:
        tab = await browser.start()

        # Visit fingerprint detection website
        await tab.go_to("https://fingerprintjs.github.io/fingerprintjs/")

        await asyncio.sleep(5)

        # Get and print custom fingerprint information
        try:
            user_agent = await tab.execute_script("return navigator.userAgent")
            print(f"Custom User Agent: {user_agent}")

            platform = await tab.execute_script("return navigator.platform")
            print(f"Custom Platform: {platform}")

            screen_info = await tab.execute_script("""
                return {
                    width: screen.width,
                    height: screen.height,
                    colorDepth: screen.colorDepth
                }
            """)
            print(f"Custom Screen info: {screen_info}")

            # Get fingerprint ID from the site
            fingerprint_id = await tab.execute_script("""
                // Wait for fingerprint generation to complete
                if (window.fingerprintJsResult) {
                    return window.fingerprintJsResult.visitorId || 'No ID found';
                } else if (document.querySelector(".visitor-id")) {
                    return document.querySelector(".visitor-id").textContent;
                } else if (document.getElementById("fp-result")) {
                    return document.getElementById("fp-result").textContent;
                } else {
                    // Try to find any element containing a fingerprint ID
                    const elements = document.querySelectorAll('*');
                    for (const el of elements) {
                        if (el.textContent && el.textContent.match(/[a-f0-9]{32}/)) {
                            return el.textContent.match(/[a-f0-9]{32}/)[0];
                        }
                    }
                    return 'Could not find fingerprint ID on page';
                }
            """)
            print(f"Custom config fingerprint ID: {fingerprint_id}")

        except Exception as e:
            print(f"Failed to get browser information: {e}")

        await asyncio.sleep(3)


async def persistent_fingerprint_example():
    """Persistent fingerprint example: Save and reuse fingerprints"""
    print("\n=== Persistent Fingerprint Example ===")

    # Create fingerprint manager
    fingerprint_manager = FingerprintManager()

    # First use: Generate and save fingerprint
    print("First visit: Generate new fingerprint")

    # Generate a new fingerprint
    _ = fingerprint_manager.generate_new_fingerprint("chrome")

    # Save the fingerprint with a custom ID
    fingerprint_path = fingerprint_manager.save_fingerprint("my_persistent_fingerprint")
    print(f"Saved fingerprint to: {fingerprint_path}")

    # Create browser with the generated fingerprint
    options1 = ChromiumOptions()
    options1.enable_fingerprint_spoofing_mode(config=FingerprintConfig(browser_type="chrome"))
    browser1 = Chrome(options=options1)

    async with browser1:
        tab = await browser1.start()
        await tab.go_to("https://fingerprintjs.github.io/fingerprintjs/")
        await asyncio.sleep(5)

        # Get current fingerprint
        current_fingerprint = fingerprint_manager.current_fingerprint
        if current_fingerprint:
            print(f"Current User Agent: {current_fingerprint.user_agent}")
            print(f"Current platform: {current_fingerprint.platform}")

        # Get fingerprint ID from the website
        try:
            await asyncio.sleep(3)
            fingerprint_id = await tab.execute_script("""
                // Wait for fingerprint generation to complete
                if (window.fingerprintJsResult) {
                    return window.fingerprintJsResult.visitorId || 'No ID found';
                } else if (document.querySelector(".visitor-id")) {
                    return document.querySelector(".visitor-id").textContent;
                } else if (document.getElementById("fp-result")) {
                    return document.getElementById("fp-result").textContent;
                } else {
                    // Try to find any element containing a fingerprint ID
                    const elements = document.querySelectorAll('*');
                    for (const el of elements) {
                        if (el.textContent && el.textContent.match(/[a-f0-9]{32}/)) {
                            return el.textContent.match(/[a-f0-9]{32}/)[0];
                        }
                    }
                    return 'Could not find fingerprint ID on page';
                }
            """)
            print(f"Persistent fingerprint ID: {fingerprint_id}")
        except Exception as e:
            print(f"Failed to get fingerprint ID: {e}")

    # Second use: Load saved fingerprint
    print("\nSecond visit: Use same fingerprint")

    # Load previously saved fingerprint
    saved_fingerprint = fingerprint_manager.load_fingerprint("my_persistent_fingerprint")
    if saved_fingerprint:
        print(f"Loaded User Agent: {saved_fingerprint.user_agent}")
        print(f"Loaded platform: {saved_fingerprint.platform}")

    # List all saved fingerprints
    all_fingerprints = fingerprint_manager.list_saved_fingerprints()
    print(f"\nAll saved fingerprints: {list(all_fingerprints)}")


async def multiple_browsers_example():
    """Multiple browsers example: Run multiple browsers with different fingerprints
    simultaneously"""
    print("\n=== Multiple Browsers Example ===")

    # Create fingerprint managers to get fingerprint objects
    fingerprint_manager1 = FingerprintManager()
    fingerprint_manager2 = FingerprintManager()

    # Generate two different fingerprints
    fingerprint1 = fingerprint_manager1.generate_new_fingerprint("chrome")
    fingerprint2 = fingerprint_manager2.generate_new_fingerprint("chrome")

    # Compare the two fingerprints
    print("\nFingerprint Comparison:")
    print(f"Fingerprint 1 ID: {fingerprint1.unique_id}")
    print(f"Fingerprint 2 ID: {fingerprint2.unique_id}")

    if fingerprint1.unique_id != fingerprint2.unique_id:
        print("✓ Success: The two fingerprints have different unique IDs!")
    else:
        print("✗ Warning: The two fingerprints have the same unique ID")

    # Compare other key attributes
    print("\nKey Attributes Comparison:")
    print(f"User Agent 1: {fingerprint1.user_agent}")
    print(f"User Agent 2: {fingerprint2.user_agent}")
    print(f"Platform 1: {fingerprint1.platform}")
    print(f"Platform 2: {fingerprint2.platform}")
    print(f"Canvas Fingerprint 1: {fingerprint1.canvas_fingerprint}")
    print(f"Canvas Fingerprint 2: {fingerprint2.canvas_fingerprint}")

    # Create two browsers with different fingerprints
    # Create Chrome browser instances with fingerprint spoofing enabled
    options1 = ChromiumOptions()
    options1.enable_fingerprint_spoofing_mode(config=FingerprintConfig(browser_type="chrome"))
    browser1 = Chrome(options=options1)
    
    options2 = ChromiumOptions()
    options2.enable_fingerprint_spoofing_mode(config=FingerprintConfig(browser_type="chrome"))
    browser2 = Chrome(options=options2)

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
            # Wait enough time for fingerprint generation
            await asyncio.sleep(3)

            # Use JavaScript to get fingerprint ID
            fp_id1 = await tab1.execute_script("""
                // Wait for fingerprint generation to complete
                if (window.fingerprintJsResult) {
                    return window.fingerprintJsResult.visitorId || 'No ID found';
                } else if (document.querySelector(".visitor-id")) {
                    return document.querySelector(".visitor-id").textContent;
                } else if (document.getElementById("fp-result")) {
                    return document.getElementById("fp-result").textContent;
                } else {
                    // Try to find any element containing a fingerprint ID
                    const elements = document.querySelectorAll('*');
                    for (const el of elements) {
                        if (el.textContent && el.textContent.match(/[a-f0-9]{32}/)) {
                            return el.textContent.match(/[a-f0-9]{32}/)[0];
                        }
                    }
                    return 'Could not find fingerprint ID on page';
                }
            """)

            fp_id2 = await tab2.execute_script("""
                // Wait for fingerprint generation to complete
                if (window.fingerprintJsResult) {
                    return window.fingerprintJsResult.visitorId || 'No ID found';
                } else if (document.querySelector(".visitor-id")) {
                    return document.querySelector(".visitor-id").textContent;
                } else if (document.getElementById("fp-result")) {
                    return document.getElementById("fp-result").textContent;
                } else {
                    // Try to find any element containing a fingerprint ID
                    const elements = document.querySelectorAll('*');
                    for (const el of elements) {
                        if (el.textContent && el.textContent.match(/[a-f0-9]{32}/)) {
                            return el.textContent.match(/[a-f0-9]{32}/)[0];
                        }
                    }
                    return 'Could not find fingerprint ID on page';
                }
            """)

            print("\nFingerprints detected by the website:")
            print(f"Browser 1 Fingerprint ID: {fp_id1}")
            print(f"Browser 2 Fingerprint ID: {fp_id2}")

            if fp_id1 != fp_id2:
                print("✓ Success: The two browsers generated different fingerprints!")
            else:
                print("✗ Warning: The two browsers have the same fingerprint")
        except Exception as e:
            print(f"Failed to get fingerprint IDs: {e}")
            traceback.print_exc()

        await asyncio.sleep(3)


async def edge_browser_example():
    """Edge browser example"""
    print("\n=== Edge Browser Example ===")

    # Create Edge browser with fingerprint spoofing enabled
    options = ChromiumOptions()
    options.enable_fingerprint_spoofing_mode()
    browser = Edge(options=options)

    async with browser:
        tab = await browser.start()

        await tab.go_to("https://fingerprintjs.github.io/fingerprintjs/")
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

            # Get fingerprint ID from the site
            await asyncio.sleep(3)
            fingerprint_id = await tab.execute_script("""
                // Wait for fingerprint generation to complete
                if (window.fingerprintJsResult) {
                    return window.fingerprintJsResult.visitorId || 'No ID found';
                } else if (document.querySelector(".visitor-id")) {
                    return document.querySelector(".visitor-id").textContent;
                } else if (document.getElementById("fp-result")) {
                    return document.getElementById("fp-result").textContent;
                } else {
                    // Try to find any element containing a fingerprint ID
                    const elements = document.querySelectorAll('*');
                    for (const el of elements) {
                        if (el.textContent && el.textContent.match(/[a-f0-9]{32}/)) {
                            return el.textContent.match(/[a-f0-9]{32}/)[0];
                        }
                    }
                    return 'Could not find fingerprint ID on page';
                }
            """)
            print(f"Edge fingerprint ID: {fingerprint_id}")

        except Exception as e:
            print(f"Failed to get browser information: {e}")

        await asyncio.sleep(3)


async def main():
    """Run all examples"""
    try:
        # Run all fingerprint examples using fingerprintjs.github.io
        await basic_example()
        await custom_config_example()
        await persistent_fingerprint_example()
        await multiple_browsers_example()
        await edge_browser_example()

    except Exception as e:
        print(f"Error running examples: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    # Run examples
    asyncio.run(main())
