"""
Tests for UserAgentParser class.

Verifies that User-Agent strings are parsed into consistent metadata
for CDP Emulation.setUserAgentOverride and navigator JS overrides.
"""

import pytest

from pydoll.utils.user_agent_parser import UserAgentParser, ParsedUserAgent


# --- Chrome on Windows ---

CHROME_WINDOWS_UA = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/120.0.6099.109 Safari/537.36'
)


class TestChromeWindows:
    def test_platform(self):
        result = UserAgentParser.parse(CHROME_WINDOWS_UA)
        assert result.platform == 'Win32'

    def test_vendor(self):
        result = UserAgentParser.parse(CHROME_WINDOWS_UA)
        assert result.vendor == 'Google Inc.'

    def test_app_version(self):
        result = UserAgentParser.parse(CHROME_WINDOWS_UA)
        assert result.app_version.startswith('5.0 (Windows NT 10.0')

    def test_metadata_platform(self):
        result = UserAgentParser.parse(CHROME_WINDOWS_UA)
        assert result.user_agent_metadata['platform'] == 'Windows'

    def test_metadata_platform_version(self):
        result = UserAgentParser.parse(CHROME_WINDOWS_UA)
        assert result.user_agent_metadata['platformVersion'] == '15.0.0'

    def test_metadata_architecture(self):
        result = UserAgentParser.parse(CHROME_WINDOWS_UA)
        assert result.user_agent_metadata['architecture'] == 'x86'

    def test_metadata_mobile(self):
        result = UserAgentParser.parse(CHROME_WINDOWS_UA)
        assert result.user_agent_metadata['mobile'] is False

    def test_metadata_model_empty(self):
        result = UserAgentParser.parse(CHROME_WINDOWS_UA)
        assert result.user_agent_metadata['model'] == ''

    def test_metadata_bitness(self):
        result = UserAgentParser.parse(CHROME_WINDOWS_UA)
        assert result.user_agent_metadata['bitness'] == '64'

    def test_metadata_wow64(self):
        result = UserAgentParser.parse(CHROME_WINDOWS_UA)
        assert result.user_agent_metadata['wow64'] is False

    def test_brands_contains_chromium(self):
        result = UserAgentParser.parse(CHROME_WINDOWS_UA)
        brands = result.user_agent_metadata['brands']
        brand_names = [b['brand'] for b in brands]
        assert 'Chromium' in brand_names

    def test_brands_contains_chrome(self):
        result = UserAgentParser.parse(CHROME_WINDOWS_UA)
        brands = result.user_agent_metadata['brands']
        brand_names = [b['brand'] for b in brands]
        assert 'Google Chrome' in brand_names

    def test_brands_contains_grease(self):
        result = UserAgentParser.parse(CHROME_WINDOWS_UA)
        brands = result.user_agent_metadata['brands']
        assert len(brands) == 3
        # First brand is GREASE
        assert brands[0]['brand'] not in {'Chromium', 'Google Chrome', 'Microsoft Edge'}

    def test_brands_major_version(self):
        result = UserAgentParser.parse(CHROME_WINDOWS_UA)
        brands = result.user_agent_metadata['brands']
        chromium_brand = next(b for b in brands if b['brand'] == 'Chromium')
        assert chromium_brand['version'] == '120'

    def test_full_version_list(self):
        result = UserAgentParser.parse(CHROME_WINDOWS_UA)
        fvl = result.user_agent_metadata['fullVersionList']
        chromium_fv = next(b for b in fvl if b['brand'] == 'Chromium')
        assert chromium_fv['version'] == '120.0.6099.109'

    def test_navigator_js_contains_vendor(self):
        result = UserAgentParser.parse(CHROME_WINDOWS_UA)
        assert "Navigator.prototype, 'vendor'" in result.navigator_override_js

    def test_navigator_js_contains_app_version(self):
        result = UserAgentParser.parse(CHROME_WINDOWS_UA)
        assert "Navigator.prototype, 'appVersion'" in result.navigator_override_js


# --- Chrome on macOS ---

CHROME_MACOS_UA = (
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/121.0.6167.85 Safari/537.36'
)


class TestChromeMacOS:
    def test_platform(self):
        result = UserAgentParser.parse(CHROME_MACOS_UA)
        assert result.platform == 'MacIntel'

    def test_metadata_platform(self):
        result = UserAgentParser.parse(CHROME_MACOS_UA)
        assert result.user_agent_metadata['platform'] == 'macOS'

    def test_metadata_platform_version(self):
        result = UserAgentParser.parse(CHROME_MACOS_UA)
        assert result.user_agent_metadata['platformVersion'] == '10.15.7'

    def test_metadata_architecture(self):
        result = UserAgentParser.parse(CHROME_MACOS_UA)
        assert result.user_agent_metadata['architecture'] == 'arm'

    def test_brands_version(self):
        result = UserAgentParser.parse(CHROME_MACOS_UA)
        brands = result.user_agent_metadata['brands']
        chromium_brand = next(b for b in brands if b['brand'] == 'Chromium')
        assert chromium_brand['version'] == '121'


# --- Chrome on Linux ---

CHROME_LINUX_UA = (
    'Mozilla/5.0 (X11; Linux x86_64) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/122.0.6261.94 Safari/537.36'
)


class TestChromeLinux:
    def test_platform(self):
        result = UserAgentParser.parse(CHROME_LINUX_UA)
        assert result.platform == 'Linux x86_64'

    def test_metadata_platform(self):
        result = UserAgentParser.parse(CHROME_LINUX_UA)
        assert result.user_agent_metadata['platform'] == 'Linux'

    def test_metadata_platform_version(self):
        result = UserAgentParser.parse(CHROME_LINUX_UA)
        assert result.user_agent_metadata['platformVersion'] == '6.1.0'

    def test_metadata_architecture(self):
        result = UserAgentParser.parse(CHROME_LINUX_UA)
        assert result.user_agent_metadata['architecture'] == 'x86'


# --- Edge on Windows ---

EDGE_WINDOWS_UA = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/120.0.0.0 Safari/537.36 Edg/120.0.2210.91'
)


class TestEdgeWindows:
    def test_platform(self):
        result = UserAgentParser.parse(EDGE_WINDOWS_UA)
        assert result.platform == 'Win32'

    def test_brands_contains_edge(self):
        result = UserAgentParser.parse(EDGE_WINDOWS_UA)
        brands = result.user_agent_metadata['brands']
        brand_names = [b['brand'] for b in brands]
        assert 'Microsoft Edge' in brand_names

    def test_brands_does_not_contain_chrome(self):
        result = UserAgentParser.parse(EDGE_WINDOWS_UA)
        brands = result.user_agent_metadata['brands']
        brand_names = [b['brand'] for b in brands]
        assert 'Google Chrome' not in brand_names

    def test_brands_chromium_present(self):
        result = UserAgentParser.parse(EDGE_WINDOWS_UA)
        brands = result.user_agent_metadata['brands']
        brand_names = [b['brand'] for b in brands]
        assert 'Chromium' in brand_names

    def test_full_version_list_edge_version(self):
        result = UserAgentParser.parse(EDGE_WINDOWS_UA)
        fvl = result.user_agent_metadata['fullVersionList']
        edge_fv = next(b for b in fvl if b['brand'] == 'Microsoft Edge')
        assert edge_fv['version'] == '120.0.2210.91'


# --- Android Chrome ---

CHROME_ANDROID_UA = (
    'Mozilla/5.0 (Linux; Android 14; Pixel 7 Build/AP2A.240805.005) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/120.0.6099.144 Mobile Safari/537.36'
)


class TestChromeAndroid:
    def test_platform(self):
        result = UserAgentParser.parse(CHROME_ANDROID_UA)
        assert result.platform == 'Linux armv81'

    def test_metadata_platform(self):
        result = UserAgentParser.parse(CHROME_ANDROID_UA)
        assert result.user_agent_metadata['platform'] == 'Android'

    def test_metadata_platform_version(self):
        result = UserAgentParser.parse(CHROME_ANDROID_UA)
        assert result.user_agent_metadata['platformVersion'] == '14'

    def test_metadata_mobile(self):
        result = UserAgentParser.parse(CHROME_ANDROID_UA)
        assert result.user_agent_metadata['mobile'] is True

    def test_metadata_model(self):
        result = UserAgentParser.parse(CHROME_ANDROID_UA)
        assert result.user_agent_metadata['model'] == 'Pixel 7'

    def test_metadata_architecture(self):
        result = UserAgentParser.parse(CHROME_ANDROID_UA)
        assert result.user_agent_metadata['architecture'] == 'arm'


# --- iPhone Safari-like UA ---

IPHONE_UA = (
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1_2 like Mac OS X) '
    'AppleWebKit/605.1.15 (KHTML, like Gecko) '
    'CriOS/120.0.6099.119 Mobile/15E148 Safari/604.1'
)


class TestIPhone:
    def test_platform(self):
        result = UserAgentParser.parse(IPHONE_UA)
        assert result.platform == 'iPhone'

    def test_metadata_platform(self):
        result = UserAgentParser.parse(IPHONE_UA)
        assert result.user_agent_metadata['platform'] == 'iOS'

    def test_metadata_platform_version(self):
        result = UserAgentParser.parse(IPHONE_UA)
        assert result.user_agent_metadata['platformVersion'] == '17.1.2'

    def test_metadata_mobile(self):
        result = UserAgentParser.parse(IPHONE_UA)
        assert result.user_agent_metadata['mobile'] is True

    def test_metadata_architecture(self):
        result = UserAgentParser.parse(IPHONE_UA)
        assert result.user_agent_metadata['architecture'] == 'arm'


# --- Old Windows versions ---

class TestWindowsVersionMapping:
    def test_windows_7(self):
        ua = (
            'Mozilla/5.0 (Windows NT 6.1; Win64; x64) '
            'AppleWebKit/537.36 Chrome/120.0.6099.109 Safari/537.36'
        )
        result = UserAgentParser.parse(ua)
        assert result.user_agent_metadata['platformVersion'] == '0.1.0'

    def test_windows_8(self):
        ua = (
            'Mozilla/5.0 (Windows NT 6.2; Win64; x64) '
            'AppleWebKit/537.36 Chrome/120.0.6099.109 Safari/537.36'
        )
        result = UserAgentParser.parse(ua)
        assert result.user_agent_metadata['platformVersion'] == '0.2.0'

    def test_windows_8_1(self):
        ua = (
            'Mozilla/5.0 (Windows NT 6.3; Win64; x64) '
            'AppleWebKit/537.36 Chrome/120.0.6099.109 Safari/537.36'
        )
        result = UserAgentParser.parse(ua)
        assert result.user_agent_metadata['platformVersion'] == '0.3.0'


# --- GREASE brands ---

class TestGreaseBrands:
    def test_grease_brand_is_first(self):
        result = UserAgentParser.parse(CHROME_WINDOWS_UA)
        brands = result.user_agent_metadata['brands']
        grease_brand = brands[0]['brand']
        assert grease_brand not in {'Chromium', 'Google Chrome', 'Microsoft Edge'}

    def test_full_version_list_grease_is_first(self):
        result = UserAgentParser.parse(CHROME_WINDOWS_UA)
        fvl = result.user_agent_metadata['fullVersionList']
        grease_brand = fvl[0]['brand']
        assert grease_brand not in {'Chromium', 'Google Chrome', 'Microsoft Edge'}

    def test_grease_version_format_for_brands(self):
        result = UserAgentParser.parse(CHROME_WINDOWS_UA)
        brands = result.user_agent_metadata['brands']
        grease_version = brands[0]['version']
        assert grease_version.isdigit()

    def test_grease_version_format_for_full_version_list(self):
        result = UserAgentParser.parse(CHROME_WINDOWS_UA)
        fvl = result.user_agent_metadata['fullVersionList']
        grease_version = fvl[0]['version']
        assert '.' in grease_version


# --- Edge cases ---

class TestEdgeCases:
    def test_unknown_browser_defaults_to_chrome(self):
        ua = 'Some random string without browser info'
        result = UserAgentParser.parse(ua)
        brands = result.user_agent_metadata['brands']
        brand_names = [b['brand'] for b in brands]
        assert 'Google Chrome' in brand_names

    def test_unknown_os_defaults_to_windows(self):
        ua = (
            'Mozilla/5.0 AppleWebKit/537.36 '
            'Chrome/120.0.6099.109 Safari/537.36'
        )
        result = UserAgentParser.parse(ua)
        assert result.platform == 'Win32'
        assert result.user_agent_metadata['platform'] == 'Windows'

    def test_returns_parsed_user_agent_type(self):
        result = UserAgentParser.parse(CHROME_WINDOWS_UA)
        assert isinstance(result, ParsedUserAgent)

    def test_navigator_js_escapes_single_quotes(self):
        ua = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/120.0.6099.109 Safari/537.36"
        )
        result = UserAgentParser.parse(ua)
        assert "\\'" not in result.navigator_override_js or "'" in result.vendor

    def test_app_version_strips_mozilla_prefix(self):
        result = UserAgentParser.parse(CHROME_WINDOWS_UA)
        assert not result.app_version.startswith('Mozilla/')
        assert result.app_version.startswith('5.0')

    def test_non_mozilla_ua_keeps_full_string(self):
        ua = 'CustomBot/1.0 Chrome/120.0.6099.109'
        result = UserAgentParser.parse(ua)
        assert result.app_version == ua


# --- ChromeOS ---

CHROMEOS_UA = (
    'Mozilla/5.0 (X11; CrOS x86_64 14541.0.0) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/120.0.6099.109 Safari/537.36'
)


class TestChromeOS:
    def test_platform(self):
        result = UserAgentParser.parse(CHROMEOS_UA)
        assert result.platform == 'Linux x86_64'

    def test_metadata_platform(self):
        result = UserAgentParser.parse(CHROMEOS_UA)
        assert result.user_agent_metadata['platform'] == 'Chrome OS'

    def test_metadata_platform_version(self):
        result = UserAgentParser.parse(CHROMEOS_UA)
        assert result.user_agent_metadata['platformVersion'] == '14541.0.0'
