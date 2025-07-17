#!/usr/bin/env python3
"""
Example demonstrating the refactored fingerprint options API.

This example shows how fingerprint-related options are now centralized
in the ChromiumOptions class, making the API cleaner and more maintainable.
"""

import asyncio

from pydoll.browser.chromium.chrome import Chrome
from pydoll.browser.chromium.edge import Edge
from pydoll.browser.options import ChromiumOptions


async def demonstrate_new_api():
    """Demonstrate the new centralized options API."""

    print("=== Refactored API Demo: Centralized Fingerprint Options ===\n")

    # Example 1: Basic Chrome usage without fingerprint spoofing
    print("1. Basic Chrome usage (no fingerprint spoofing):")
    options_basic = ChromiumOptions()
    options_basic.add_argument('--window-size=1024,768')

    async with Chrome(options=options_basic) as chrome:
        print(f"   Fingerprint spoofing: {chrome.enable_fingerprint_spoofing}")
        print("   ✓ Basic Chrome instance created successfully\n")

    # Example 2: Enable fingerprint spoofing with the convenience method
    print("2. Chrome with fingerprint spoofing (convenience method):")
    options_spoofing = ChromiumOptions()
    options_spoofing.enable_fingerprint_spoofing_mode()  # Enable with default config

    async with Chrome(options=options_spoofing) as chrome:
        print(f"   Fingerprint spoofing: {chrome.enable_fingerprint_spoofing}")
        print("   ✓ Fingerprint spoofing enabled successfully\n")

    # Example 3: Enable fingerprint spoofing with custom configuration
    print("3. Chrome with custom fingerprint configuration:")
    options_custom = ChromiumOptions()
    custom_config = {
        "browser_type": "chrome",
        "is_mobile": False,
        "preferred_os": "windows",
        "preferred_languages": ["zh-CN", "en-US"],
        "enable_webgl_spoofing": True,
        "enable_canvas_spoofing": True
    }
    options_custom.enable_fingerprint_spoofing_mode(config=custom_config)

    async with Chrome(options=options_custom) as chrome:
        print(f"   Fingerprint spoofing: {chrome.enable_fingerprint_spoofing}")
        print(f"   Custom config applied: {options_custom.fingerprint_config}")
        print("   ✓ Custom fingerprint configuration applied\n")

    # Example 4: Using property setters for fine-grained control
    print("4. Using property setters for fine-grained control:")
    options_properties = ChromiumOptions()
    options_properties.enable_fingerprint_spoofing = True
    options_properties.fingerprint_config = {
        "enable_webgl_spoofing": False,
        "include_plugins": False
    }
    options_properties.add_argument('--disable-blink-features=AutomationControlled')

    async with Chrome(options=options_properties) as chrome:
        print(f"   Fingerprint spoofing: {chrome.enable_fingerprint_spoofing}")
        print(f"   Config via property: {options_properties.fingerprint_config}")
        print("   ✓ Property setters work perfectly\n")

    # Example 5: Same pattern works for Edge
    print("5. Edge browser with fingerprint spoofing:")
    options_edge = ChromiumOptions()
    options_edge.enable_fingerprint_spoofing_mode()

    async with Edge(options=options_edge) as edge:
        print(f"   Edge fingerprint spoofing: {edge.enable_fingerprint_spoofing}")
        print("   ✓ Edge browser with fingerprint spoofing enabled\n")

    print("=== Key Benefits of the Refactored API ===")
    print("✓ Centralized configuration: All fingerprint settings in options")
    print("✓ Cleaner constructors: No need for extra fingerprint parameters")
    print("✓ Better maintainability: One place to manage fingerprint options")
    print("✓ Consistent API: Same pattern for Chrome and Edge")
    print("✓ Flexibility: Multiple ways to configure (convenience method + properties)")


def demonstrate_usage_patterns():
    """Show different usage patterns for the new API."""

    print("\n=== Different Usage Patterns ===\n")

    # Pattern 1: Method chaining style
    print("Pattern 1: Method chaining style")
    options1 = ChromiumOptions()
    options1.enable_fingerprint_spoofing_mode({"method": "chaining"})
    options1.add_argument('--no-sandbox')
    print("   ✓ Configuration complete\n")

    # Pattern 2: Property assignment style
    print("Pattern 2: Property assignment style")
    options2 = ChromiumOptions()
    options2.enable_fingerprint_spoofing = True
    options2.fingerprint_config = {"browser_type": "chrome", "is_mobile": False}
    print("   ✓ Configuration complete\n")

    # Pattern 3: Build pattern
    print("Pattern 3: Builder pattern")

    def build_options_with_fingerprint(config=None):
        options = ChromiumOptions()
        options.enable_fingerprint_spoofing_mode(config)
        options.add_argument('--disable-web-security')
        return options

    _options3 = build_options_with_fingerprint({"builder": "pattern"})
    print("   ✓ Builder pattern complete\n")

    print("All patterns provide the same clean, centralized configuration!")


if __name__ == "__main__":
    print("Running refactored API demonstration...")

    # Demonstrate the new API patterns
    demonstrate_usage_patterns()

    # Run the async demo
    asyncio.run(demonstrate_new_api())

    print("\n🎉 Refactored API demonstration complete!")
    print("The fingerprint options are now properly centralized in ChromiumOptions!")
