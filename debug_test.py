#!/usr/bin/env python3
"""Debug script to check the generated JavaScript content."""

from pydoll.fingerprint.models import Fingerprint
from pydoll.fingerprint.injector import FingerprintInjector

# Create a test fingerprint
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

injector = FingerprintInjector(fingerprint)
script = injector.generate_script()

print("Generated script length:", len(script))
print("\nChecking for expected strings:")
print("- 'navigator.userAgent' found:", "navigator.userAgent" in script)
print("- 'Test User Agent' found:", "Test User Agent" in script)
print("- 'screen.width' found:", "screen.width" in script)
print("- '1920' found:", "1920" in script)
print("- 'webdriver' found:", "webdriver" in script)

print("\nFirst 500 characters of script:")
print(script[:500])
print("\n...")

# Look for navigator.userAgent specifically
import re
matches = re.findall(r'navigator\.userAgent', script)
print(f"\nFound {len(matches)} occurrences of 'navigator.userAgent'")

# Check the exact content around userAgent
userAgent_context = script.find("userAgent")
if userAgent_context != -1:
    start = max(0, userAgent_context - 50)
    end = min(len(script), userAgent_context + 100)
    print(f"\nContext around 'userAgent':")
    print(repr(script[start:end]))
else:
    print("\n'userAgent' not found in script!") 