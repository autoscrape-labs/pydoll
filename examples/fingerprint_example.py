"""
Fingerprint Spoofing Feature Examples

Demonstrates how to use pydoll's fingerprint spoofing features to prevent browser
fingerprint tracking.
"""

import asyncio
import traceback

from pydoll.browser.chromium.chrome import Chrome
from pydoll.browser.chromium.edge import Edge
from pydoll.fingerprint import FingerprintConfig, FingerprintManager


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
            # 等待足够时间让指纹生成
            await asyncio.sleep(3)

            # 尝试使用更通用的选择器或直接执行 JavaScript 获取指纹 ID
            fingerprint_id = await tab.execute_script("""
                // 等待指纹生成完成
                if (window.fingerprintJsResult) {
                    return window.fingerprintJsResult.visitorId || 'No ID found';
                } else if (document.querySelector(".visitor-id")) {
                    return document.querySelector(".visitor-id").textContent;
                } else if (document.getElementById("fp-result")) {
                    return document.getElementById("fp-result").textContent;
                } else {
                    // 尝试查找包含指纹 ID 的任何元素
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

    # First use: Generate and save fingerprint
    print("First visit: Generate new fingerprint")

    # Generate a new fingerprint
    _ = fingerprint_manager.generate_new_fingerprint("chrome")

    # Save the fingerprint with a custom ID
    fingerprint_path = fingerprint_manager.save_fingerprint("my_persistent_fingerprint")
    print(f"Saved fingerprint to: {fingerprint_path}")

    # Create browser with the generated fingerprint
    browser1 = Chrome(
        enable_fingerprint_spoofing=True,
        fingerprint_config=FingerprintConfig(browser_type="chrome")
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
    print(f"\nAll saved fingerprints: {list(all_fingerprints)}")


async def multiple_browsers_example():
    """Multiple browsers example: Run multiple browsers with different fingerprints
    simultaneously"""
    print("\n=== Multiple Browsers Example ===")

    # 创建指纹管理器以便获取指纹对象
    fingerprint_manager1 = FingerprintManager()
    fingerprint_manager2 = FingerprintManager()

    # 生成两个不同的指纹
    fingerprint1 = fingerprint_manager1.generate_new_fingerprint("chrome")
    fingerprint2 = fingerprint_manager2.generate_new_fingerprint("chrome")

    # 比较两个指纹
    print("\n指纹比较:")
    print(f"指纹1 ID: {fingerprint1.unique_id}")
    print(f"指纹2 ID: {fingerprint2.unique_id}")

    if fingerprint1.unique_id != fingerprint2.unique_id:
        print("✓ 成功: 两个指纹有不同的唯一ID!")
    else:
        print("✗ 警告: 两个指纹的唯一ID相同")

    # 比较其他关键属性
    print("\n关键属性比较:")
    print(f"用户代理1: {fingerprint1.user_agent}")
    print(f"用户代理2: {fingerprint2.user_agent}")
    print(f"平台1: {fingerprint1.platform}")
    print(f"平台2: {fingerprint2.platform}")
    print(f"Canvas指纹1: {fingerprint1.canvas_fingerprint}")
    print(f"Canvas指纹2: {fingerprint2.canvas_fingerprint}")

    # Create two browsers with different fingerprints
    # 创建Chrome浏览器实例，并启用指纹伪装
    # 注意：Chrome类不接受fingerprint_manager参数，而是接受fingerprint_config参数
    browser1 = Chrome(
        enable_fingerprint_spoofing=True,
        # 创建一个新的FingerprintConfig，并使用已生成的指纹的配置
        fingerprint_config=FingerprintConfig(browser_type="chrome")
    )
    browser2 = Chrome(
        enable_fingerprint_spoofing=True,
        fingerprint_config=FingerprintConfig(browser_type="chrome")
    )

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
            # 等待足够时间让指纹生成
            await asyncio.sleep(3)

            # 使用 JavaScript 获取指纹 ID
            fp_id1 = await tab1.execute_script("""
                // 等待指纹生成完成
                if (window.fingerprintJsResult) {
                    return window.fingerprintJsResult.visitorId || 'No ID found';
                } else if (document.querySelector(".visitor-id")) {
                    return document.querySelector(".visitor-id").textContent;
                } else if (document.getElementById("fp-result")) {
                    return document.getElementById("fp-result").textContent;
                } else {
                    // 尝试查找包含指纹 ID 的任何元素
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
                // 等待指纹生成完成
                if (window.fingerprintJsResult) {
                    return window.fingerprintJsResult.visitorId || 'No ID found';
                } else if (document.querySelector(".visitor-id")) {
                    return document.querySelector(".visitor-id").textContent;
                } else if (document.getElementById("fp-result")) {
                    return document.getElementById("fp-result").textContent;
                } else {
                    // 尝试查找包含指纹 ID 的任何元素
                    const elements = document.querySelectorAll('*');
                    for (const el of elements) {
                        if (el.textContent && el.textContent.match(/[a-f0-9]{32}/)) {
                            return el.textContent.match(/[a-f0-9]{32}/)[0];
                        }
                    }
                    return 'Could not find fingerprint ID on page';
                }
            """)

            print("\n网站检测到的指纹:")
            print(f"浏览器1指纹ID: {fp_id1}")
            print(f"浏览器2指纹ID: {fp_id2}")

            if fp_id1 != fp_id2:
                print("✓ 成功: 两个浏览器生成了不同的指纹!")
            else:
                print("✗ 警告: 两个浏览器有相同的指纹")
        except Exception as e:
            print(f"获取指纹ID失败: {e}")
            traceback.print_exc()

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
        # 只运行多浏览器示例来测试指纹唯一性
        await multiple_browsers_example()

        # 以下示例暂时注释掉
        # await basic_example()
        # await custom_config_example()
        # await persistent_fingerprint_example()
        # await edge_browser_example()

    except Exception as e:
        print(f"Error running examples: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    # Run examples
    asyncio.run(main())
