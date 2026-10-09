"""Real-Firefox (WebDriver BiDi) integration test for BiDiTab.apply_fingerprint.

Applies a desktop Windows profile to a tab of a headless macOS/Linux Firefox and
reads back, from a page loaded afterwards, every signal the applier claims to
honour: the native BiDi overrides (User-Agent, locale, timezone, screen,
viewport) and the JavaScript layer (platform, appVersion, oscpu,
hardwareConcurrency, the full languages list, the screen extras).
"""

from __future__ import annotations

import pytest

from pydoll.browser.firefox.tab import BiDiTab

WINDOWS_UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:157.0) Gecko/20100101 Firefox/157.0'
TOKYO_UTC_OFFSET_MINUTES = -540

PROFILE = {
    'user_agent': WINDOWS_UA,
    'hardware': {'hardware_concurrency': 12, 'device_memory': 16},
    'locale': {'languages': ['de-DE', 'de', 'en']},
    'timezone': 'Asia/Tokyo',
    'screen': {
        'width': 2560,
        'height': 1440,
        'avail_width': 2560,
        'avail_height': 1400,
        'color_depth': 24,
        'inner_width': 1280,
        'inner_height': 720,
        'device_pixel_ratio': 2.0,
    },
}


@pytest.mark.asyncio(loop_scope='module')
async def test_apply_fingerprint_is_what_the_page_reads(tab: BiDiTab, page_url):
    await tab.apply_fingerprint(PROFILE)
    await tab.go_to(page_url('bidi_fingerprint.html'))

    read = await tab.evaluate('window.__fingerprint')
    assert isinstance(read, dict)
    screen = PROFILE['screen']

    assert read['userAgent'] == WINDOWS_UA
    assert read['platform'] == 'Win32'
    assert read['appVersion'] == '5.0 (Windows)'
    assert read['oscpu'] == 'Windows NT 10.0; Win64; x64'
    assert read['hardwareConcurrency'] == PROFILE['hardware']['hardware_concurrency']

    assert read['language'] == PROFILE['locale']['languages'][0]
    assert read['languages'] == PROFILE['locale']['languages']
    assert read['timeZone'] == PROFILE['timezone']
    assert read['timezoneOffset'] == TOKYO_UTC_OFFSET_MINUTES

    assert read['screenWidth'] == screen['width']
    assert read['screenHeight'] == screen['height']
    assert read['availHeight'] == screen['avail_height']
    assert read['colorDepth'] == screen['color_depth']
    assert read['innerWidth'] == screen['inner_width']
    assert read['innerHeight'] == screen['inner_height']
    assert read['devicePixelRatio'] == screen['device_pixel_ratio']

    assert read['hasDeviceMemory'] is False
    assert read['hasConnection'] is False
    assert '[native code]' in read['userAgentGetter']
    assert '[native code]' in read['hardwareConcurrencyGetter']
