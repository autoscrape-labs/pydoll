"""
Tests for UserAgentParser class.

Verifies that User-Agent strings are parsed into consistent metadata
for CDP Emulation.setUserAgentOverride.
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
        assert any(
            b['brand'] not in {'Chromium', 'Google Chrome', 'Microsoft Edge'} for b in brands
        )

    def test_metadata_form_factors_desktop(self):
        result = UserAgentParser.parse(CHROME_WINDOWS_UA)
        assert result.user_agent_metadata['formFactors'] == ['Desktop']

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

    def test_metadata_platform_version_ignores_frozen_ua_token(self):
        """``10_15_7`` is the reduced-UA freeze, not the OS: a real macOS version is reported."""
        result = UserAgentParser.parse(CHROME_MACOS_UA)
        assert result.user_agent_metadata['platformVersion'] == '15.6.1'

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
        """``Linux armv81`` is the frozen Android value of the User-Agent reduction."""
        result = UserAgentParser.parse(CHROME_ANDROID_UA)
        assert result.platform == 'Linux armv81'

    def test_reduced_ua_does_not_echo_frozen_android_10(self):
        """``Android 10; K`` is the reduced-UA freeze; a current Android version is reported."""
        reduced = (
            'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/145.0.7632.45 Mobile Safari/537.36'
        )
        result = UserAgentParser.parse(reduced)
        assert result.user_agent_metadata['platformVersion'] == '15.0.0'
        assert result.user_agent_metadata['formFactors'] == ['Mobile']

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


def _ua_for_major(major: int) -> str:
    return (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
        f'(KHTML, like Gecko) Chrome/{major}.0.1000.10 Safari/537.36'
    )


class TestGreaseBrands:
    """The greased brand, its version and the brand order follow Chromium's
    per-major algorithm (``GetGreasedUserAgentBrandVersion`` /
    ``ShuffleBrandList``), which a detector can recompute exactly."""

    def test_chrome_152_matches_live_chrome(self):
        """Captured from a real Chrome 152.0.7977.83: Chromium, grease, Google Chrome."""
        brands = UserAgentParser.parse(_ua_for_major(152)).user_agent_metadata['brands']
        assert [(b['brand'], b['version']) for b in brands] == [
            ('Chromium', '152'),
            ('Not?A_Brand', '24'),
            ('Google Chrome', '152'),
        ]

    def test_chrome_151_grease_token_and_order(self):
        brands = UserAgentParser.parse(_ua_for_major(151)).user_agent_metadata['brands']
        assert [(b['brand'], b['version']) for b in brands] == [
            ('Not=A?Brand', '99'),
            ('Google Chrome', '151'),
            ('Chromium', '151'),
        ]

    def test_chrome_130_and_131_known_headers(self):
        """Two majors with widely observed real Sec-CH-UA headers."""
        brands_130 = UserAgentParser.parse(_ua_for_major(130)).user_agent_metadata['brands']
        brands_131 = UserAgentParser.parse(_ua_for_major(131)).user_agent_metadata['brands']
        assert [b['brand'] for b in brands_130] == ['Chromium', 'Google Chrome', 'Not?A_Brand']
        assert brands_130[2]['version'] == '99'
        assert [b['brand'] for b in brands_131] == ['Google Chrome', 'Chromium', 'Not_A Brand']
        assert brands_131[2]['version'] == '24'

    def test_full_version_list_shares_the_brand_order(self):
        metadata = UserAgentParser.parse(_ua_for_major(152)).user_agent_metadata
        assert [b['brand'] for b in metadata['fullVersionList']] == [
            b['brand'] for b in metadata['brands']
        ]
        grease = next(b for b in metadata['fullVersionList'] if b['brand'].startswith('Not'))
        assert grease['version'] == '24.0.0.0'
        assert metadata['fullVersionList'][0]['version'] == '152.0.1000.10'

    def test_grease_version_cycles_through_8_99_24(self):
        versions = {
            UserAgentParser._build_grease(major)[1] for major in (150, 151, 152)
        }
        assert versions == {'8', '99', '24'}


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
