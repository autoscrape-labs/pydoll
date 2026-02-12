import re
from dataclasses import dataclass, field

from pydoll.protocol.emulation.types import UserAgentBrandVersion, UserAgentMetadata

_CHROME_RE = re.compile(r'Chrome/(\d+)\.(\d+)\.(\d+)\.(\d+)')
_EDGE_RE = re.compile(r'Edg/(\d+)\.(\d+)\.(\d+)\.(\d+)')

_GREASE_BRANDS = [
    'Not/A)Brand',
    'Not A;Brand',
    'Not.A/Brand',
    'Not)A;Brand',
    'Not=A?Brand',
]

_GREASE_MODULO = 100

_PLATFORM_MAP = {
    'windows': 'Win32',
    'macintosh': 'MacIntel',
    'linux': 'Linux x86_64',
    'android': 'Linux armv81',
    'iphone': 'iPhone',
    'ipad': 'iPad',
    'cros': 'Linux x86_64',
}

_UA_PLATFORM_MAP = {
    'windows': 'Windows',
    'macintosh': 'macOS',
    'linux': 'Linux',
    'android': 'Android',
    'iphone': 'iOS',
    'ipad': 'iOS',
    'cros': 'Chrome OS',
}

_ARCHITECTURE_MAP = {
    'windows': 'x86',
    'macintosh': 'arm',
    'linux': 'x86',
    'android': 'arm',
    'iphone': 'arm',
    'ipad': 'arm',
    'cros': 'x86',
}

_WINDOWS_VERSION_MAP = {
    '6.1': '0.1.0',
    '6.2': '0.2.0',
    '6.3': '0.3.0',
    '10.0': '15.0.0',
}

_DEFAULT_PLATFORM_VERSIONS = {
    'windows': '15.0.0',
    'macintosh': '14.0.0',
    'android': '14.0.0',
    'iphone': '17.0.0',
    'ipad': '17.0.0',
    'linux': '6.1.0',
    'cros': '14541.0.0',
}

_OS_KEYWORDS = [
    ('android', 'android'),
    ('iphone', 'iphone'),
    ('ipad', 'ipad'),
    ('cros', 'cros'),
    ('windows', 'windows'),
    ('macintosh', 'macintosh'),
    ('mac os x', 'macintosh'),
    ('linux', 'linux'),
]

_MOBILE_KEYWORDS = frozenset({'mobile', 'android', 'iphone', 'ipad'})

_VERSION_PATTERNS = {
    'windows': (r'Windows NT (\d+\.\d+)', None),
    'macintosh': (r'Mac OS X (\d+)[_.](\d+)[_.]?(\d+)?', None),
    'android': (r'Android (\d+(?:\.\d+)*)', None),
    'iphone': (r'OS (\d+)[_.](\d+)[_.]?(\d+)?', None),
    'ipad': (r'OS (\d+)[_.](\d+)[_.]?(\d+)?', None),
}


@dataclass
class ParsedUserAgent:
    """Result of parsing a User-Agent string into consistent metadata."""

    platform: str
    vendor: str
    app_version: str
    user_agent_metadata: UserAgentMetadata
    navigator_override_js: str = field(default='', repr=False)


class UserAgentParser:
    """Stateless parser that extracts consistent metadata from a User-Agent string.

    Given a UA string like:
        Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
        (KHTML, like Gecko) Chrome/120.0.6099.109 Safari/537.36

    It produces all the metadata needed for CDP Emulation.setUserAgentOverride
    and JavaScript navigator property overrides, ensuring full consistency
    between HTTP headers and JS properties.
    """

    @staticmethod
    def parse(user_agent: str) -> ParsedUserAgent:
        """Parse a User-Agent string into consistent browser metadata.

        Args:
            user_agent: Full User-Agent string.

        Returns:
            ParsedUserAgent with platform, vendor, appVersion,
            userAgentMetadata, and JS override script.
        """
        os_key = UserAgentParser._detect_os_key(user_agent)
        browser_name, major_version, full_version = UserAgentParser._detect_browser(user_agent)
        is_mobile = UserAgentParser._detect_mobile(user_agent)
        metadata = UserAgentParser._build_metadata(
            user_agent, os_key, browser_name, major_version, full_version, is_mobile
        )
        vendor = 'Google Inc.'
        app_version = UserAgentParser._build_app_version(user_agent)

        return ParsedUserAgent(
            platform=_PLATFORM_MAP.get(os_key, 'Win32'),
            vendor=vendor,
            app_version=app_version,
            user_agent_metadata=metadata,
            navigator_override_js=UserAgentParser._build_navigator_override_js(vendor, app_version),
        )

    @staticmethod
    def _build_metadata(
        user_agent: str,
        os_key: str,
        browser_name: str,
        major_version: str,
        full_version: str,
        is_mobile: bool,
    ) -> UserAgentMetadata:
        return UserAgentMetadata(
            platform=_UA_PLATFORM_MAP.get(os_key, 'Windows'),
            platformVersion=UserAgentParser._get_platform_version(user_agent, os_key),
            architecture=_ARCHITECTURE_MAP.get(os_key, 'x86'),
            model=UserAgentParser._extract_model(user_agent) if is_mobile else '',
            mobile=is_mobile,
            brands=UserAgentParser._build_brands(browser_name, major_version),
            fullVersionList=UserAgentParser._build_full_version_list(browser_name, full_version),
            bitness='64',
            wow64=False,
        )

    @staticmethod
    def _detect_os_key(user_agent: str) -> str:
        ua_lower = user_agent.lower()
        for keyword, os_key in _OS_KEYWORDS:
            if keyword in ua_lower:
                return os_key
        return 'windows'

    @staticmethod
    def _detect_browser(user_agent: str) -> tuple[str, str, str]:
        edge_match = _EDGE_RE.search(user_agent)
        if edge_match:
            return 'Microsoft Edge', edge_match.group(1), '.'.join(edge_match.groups())

        chrome_match = _CHROME_RE.search(user_agent)
        if chrome_match:
            return (
                'Google Chrome',
                chrome_match.group(1),
                '.'.join(chrome_match.groups()),
            )

        return 'Google Chrome', '120', '120.0.0.0'

    @staticmethod
    def _detect_mobile(user_agent: str) -> bool:
        ua_lower = user_agent.lower()
        return any(keyword in ua_lower for keyword in _MOBILE_KEYWORDS)

    @staticmethod
    def _build_app_version(user_agent: str) -> str:
        if user_agent.startswith('Mozilla/'):
            return user_agent[len('Mozilla/') :]
        return user_agent

    @staticmethod
    def _get_platform_version(user_agent: str, os_key: str) -> str:
        default = _DEFAULT_PLATFORM_VERSIONS.get(os_key, '0.0.0')

        if os_key == 'windows':
            return UserAgentParser._parse_windows_version(user_agent, default)

        if os_key in {'macintosh', 'iphone', 'ipad'}:
            pattern = _VERSION_PATTERNS[os_key][0]
            return UserAgentParser._parse_dotted_version(user_agent, pattern, default)

        if os_key == 'android':
            match = re.search(r'Android (\d+(?:\.\d+)*)', user_agent)
            return match.group(1) if match else default

        return default

    @staticmethod
    def _parse_windows_version(user_agent: str, default: str) -> str:
        match = re.search(r'Windows NT (\d+\.\d+)', user_agent)
        if not match:
            return default
        return _WINDOWS_VERSION_MAP.get(match.group(1), '15.0.0')

    @staticmethod
    def _parse_dotted_version(user_agent: str, pattern: str, default: str) -> str:
        match = re.search(pattern, user_agent)
        if not match:
            return default
        major = match.group(1)
        minor = match.group(2)
        patch = match.group(3) or '0'
        return f'{major}.{minor}.{patch}'

    @staticmethod
    def _build_grease(major_int: int) -> tuple[str, str, str]:
        """Build GREASE brand, short version, and full version."""
        grease_index = major_int % len(_GREASE_BRANDS)
        brand = _GREASE_BRANDS[grease_index]
        short_ver = str(major_int % _GREASE_MODULO) if major_int >= _GREASE_MODULO else '99'
        full_ver = (
            f'{major_int % _GREASE_MODULO}.0.0.0' if major_int >= _GREASE_MODULO else '99.0.0.0'
        )
        return brand, short_ver, full_ver

    @staticmethod
    def _build_brands(browser_name: str, major_version: str) -> list[UserAgentBrandVersion]:
        major_int = int(major_version) if major_version.isdigit() else 120
        grease_brand, grease_version, _ = UserAgentParser._build_grease(major_int)

        brands: list[UserAgentBrandVersion] = [
            UserAgentBrandVersion(brand=grease_brand, version=grease_version),
            UserAgentBrandVersion(brand='Chromium', version=major_version),
        ]

        if browser_name in {'Google Chrome', 'Microsoft Edge'}:
            brands.append(UserAgentBrandVersion(brand=browser_name, version=major_version))

        return brands

    @staticmethod
    def _build_full_version_list(
        browser_name: str, full_version: str
    ) -> list[UserAgentBrandVersion]:
        major = full_version.split('.')[0] if '.' in full_version else full_version
        major_int = int(major) if major.isdigit() else 120
        grease_brand, _, grease_full_version = UserAgentParser._build_grease(major_int)

        versions: list[UserAgentBrandVersion] = [
            UserAgentBrandVersion(brand=grease_brand, version=grease_full_version),
            UserAgentBrandVersion(brand='Chromium', version=full_version),
        ]

        if browser_name in {'Google Chrome', 'Microsoft Edge'}:
            versions.append(UserAgentBrandVersion(brand=browser_name, version=full_version))

        return versions

    @staticmethod
    def _extract_model(user_agent: str) -> str:
        match = re.search(r';\s*([A-Za-z0-9_ ]+)\s*Build/', user_agent)
        if match:
            return match.group(1).strip()
        return ''

    @staticmethod
    def _build_navigator_override_js(vendor: str, app_version: str) -> str:
        safe_vendor = vendor.replace("'", "\\'")
        safe_app_version = app_version.replace('\\', '\\\\').replace("'", "\\'")
        return (
            "Object.defineProperty(Navigator.prototype, 'vendor', "
            f"{{get: () => '{safe_vendor}'}});\n"
            "Object.defineProperty(Navigator.prototype, 'appVersion', "
            f"{{get: () => '{safe_app_version}'}});"
        )
