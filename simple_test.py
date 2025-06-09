#!/usr/bin/env python3
"""Simple test to check fingerprint functionality."""

try:
    print("Testing imports...")
    from pydoll.fingerprint.models import Fingerprint
    from pydoll.fingerprint.injector import FingerprintInjector
    print("✓ Imports successful")

    print("Testing fingerprint creation...")
    fingerprint = Fingerprint(
        user_agent="Test User Agent",
        platform="Win32",
        language="en-US",
        languages=["en-US", "en"],
        hardware_concurrency=4,
        screen_width=1920,
        screen_height=1080,
        screen_color_depth=24,
        screen_pixel_depth=24,
        available_width=1920,
        available_height=1040,
        viewport_width=1200,
        viewport_height=800,
        inner_width=1200,
        inner_height=680,
        webgl_vendor="Google Inc.",
        webgl_renderer="Test Renderer",
        webgl_version="WebGL 1.0",
        webgl_shading_language_version="WebGL GLSL ES 1.0",
        webgl_extensions=["EXT_test"],
        canvas_fingerprint="test_canvas_123",
        audio_context_sample_rate=44100.0,
        audio_context_state="suspended",
        audio_context_max_channel_count=2,
        timezone="America/New_York",
        timezone_offset=-300,
        browser_type="chrome",
        browser_version="120.0.0.0",
        plugins=[],
    )
    print("✓ Fingerprint created")

    print("Testing injector...")
    injector = FingerprintInjector(fingerprint)
    script = injector.generate_script()
    print(f"✓ Script generated ({len(script)} chars)")

    print("Testing script content...")
    checks = [
        ("'userAgent'" in script, "'userAgent' found"),
        ("Test User Agent" in script, "Test User Agent found"),
        ("'width'" in script, "'width' found"),
        ("1920" in script, "1920 found"),
        ("webdriver" in script, "webdriver found"),
    ]
    
    for check, msg in checks:
        if check:
            print(f"✓ {msg}")
        else:
            print(f"✗ {msg}")

    print("All tests completed!")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc() 