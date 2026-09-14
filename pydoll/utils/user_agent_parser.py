import re
from dataclasses import dataclass

from pydoll.protocol.emulation.types import UserAgentBrandVersion, UserAgentMetadata

_CHROME_RE = re.compile(r'Chrome/(\d+)\.(\d+)\.(\d+)\.(\d+)')
_EDGE_RE = re.compile(r'Edg/(\d+)\.(\d+)\.(\d+)\.(\d+)')

# Token-reduction patterns: collapse a full 4-part Chrome/Edge build number
# (e.g. 145.0.7632.75) down to the frozen "MAJOR.0.0.0" form. This is the only
# form modern Chrome exposes in navigator.userAgent / the User-Agent header
# after the Chromium User-Agent reduction; the real build number lives solely
# in the Sec-CH-UA-Full-Version[-List] Client Hints.
_CHROME_VERSION_TOKEN_RE = re.compile(r'(Chrome/)(\d+)\.\d+\.\d+\.\d+')
_EDGE_VERSION_TOKEN_RE = re.compile(r'(Edg/)(\d+)\.\d+\.\d+\.\d+')

# Chromium's greased brand generator (components/embedder_support/user_agent_utils.cc):
# the brand text, its version and the order of the brand list are all a
# deterministic function of the browser major version, so a detector can
# recompute the exact Sec-CH-UA a real Chrome of that major emits.
_GREASE_CHARS = (' ', '(', ':', '-', '.', '/', ')', ';', '=', '?', '_')
_GREASE_VERSIONS = ('8', '99', '24')
_BRAND_ORDERS = ((0, 1, 2), (0, 2, 1), (1, 0, 2), (1, 2, 0), (2, 0, 1), (2, 1, 0))

# The frozen tokens the User-Agent reduction leaves in place of the real OS
# version: no real OS version can be recovered from a UA carrying these.
_REDUCED_MAC_VERSION = '10.15.7'
_REDUCED_ANDROID_MARKER = 'Android 10; K'

_PLATFORM_MAP = {
    'windows': 'Win32',
    'macintosh': 'MacIntel',
    'linux': 'Linux x86_64',
    'android': 'Linux aarch64',
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
    'macintosh': '15.6.1',
    'android': '15.0.0',
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
    reduced_user_agent: str = ''


class UserAgentParser:
    """Stateless parser that extracts consistent metadata from a User-Agent string.

    Given a UA string like:
        Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
        (KHTML, like Gecko) Chrome/120.0.6099.109 Safari/537.36

    It produces all the metadata needed for CDP Emulation.setUserAgentOverride,
    ensuring full consistency between HTTP headers, navigator properties and
    Client Hints.
    """

    @staticmethod
    def parse(user_agent: str) -> ParsedUserAgent:
        """Parse a User-Agent string into consistent browser metadata.

        Args:
            user_agent: Full User-Agent string.

        Returns:
            ParsedUserAgent with platform, vendor, appVersion, the reduced
            User-Agent and the Client Hints metadata.
        """
        os_key = UserAgentParser._detect_os_key(user_agent)
        browser_name, major_version, full_version = UserAgentParser._detect_browser(user_agent)
        is_mobile = UserAgentParser._detect_mobile(user_agent)
        metadata = UserAgentParser._build_metadata(
            user_agent, os_key, browser_name, major_version, full_version, is_mobile
        )
        vendor = 'Google Inc.'
        app_version = UserAgentParser._build_app_version(user_agent)
        platform = _PLATFORM_MAP.get(os_key, 'Win32')
        reduced_user_agent = UserAgentParser._reduce_user_agent(user_agent)

        return ParsedUserAgent(
            platform=platform,
            vendor=vendor,
            app_version=app_version,
            user_agent_metadata=metadata,
            reduced_user_agent=reduced_user_agent,
        )

    @staticmethod
    def _reduce_user_agent(user_agent: str) -> str:
        """Collapse Chrome/Edge build numbers to the frozen ``MAJOR.0.0.0`` form.

        After the Chromium User-Agent reduction, ``navigator.userAgent`` (and
        the ``User-Agent`` header) only ever expose ``Chrome/<MAJOR>.0.0.0`` -
        the real 4-part build number (e.g. ``145.0.7632.75``) appears solely in
        the ``Sec-CH-UA-Full-Version[-List]`` Client Hints. The fingerprint
        catalog keeps the full build in the UA string as the single source of
        truth (so the full version list stays correct); this reduces it so the
        emulated ``navigator.userAgent`` matches what real Chrome reports.
        """
        reduced = _CHROME_VERSION_TOKEN_RE.sub(r'\g<1>\g<2>.0.0.0', user_agent)
        return _EDGE_VERSION_TOKEN_RE.sub(r'\g<1>\g<2>.0.0.0', reduced)

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
            fullVersion=full_version,
            bitness='64',
            wow64=False,
            formFactors=['Mobile'] if is_mobile else ['Desktop'],
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
        """Derive the Client Hints ``platformVersion`` from the User-Agent.

        After the User-Agent reduction the UA string carries a frozen OS token
        (``Mac OS X 10_15_7``, ``Android 10; K``) while real Chrome still
        reports the true OS version in ``Sec-CH-UA-Platform-Version``. Those
        frozen tokens therefore fall back to a plausible current version instead
        of being echoed (no Apple-silicon Mac runs 10.15, no current phone runs
        Android 10). Set ``client_hints.platform_version`` to pin the exact value.
        """
        default = _DEFAULT_PLATFORM_VERSIONS.get(os_key, '0.0.0')

        if os_key == 'windows':
            return UserAgentParser._parse_windows_version(user_agent, default)

        if os_key in {'macintosh', 'iphone', 'ipad'}:
            pattern = _VERSION_PATTERNS[os_key][0]
            parsed = UserAgentParser._parse_dotted_version(user_agent, pattern, default)
            return default if parsed == _REDUCED_MAC_VERSION else parsed

        if os_key == 'android':
            if _REDUCED_ANDROID_MARKER in user_agent:
                return default
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
        """Build the greased brand exactly as Chromium does for a browser major.

        Mirrors ``GetGreasedUserAgentBrandVersion``: the brand is
        ``Not<c1>A<c2>Brand`` with ``c1 = chars[major % 11]`` and
        ``c2 = chars[(major + 1) % 11]``, and the version is one of ``8``, ``99``
        or ``24`` selected by ``major % 3``. Chrome 152 thus emits
        ``"Not?A_Brand";v="24"``, Chrome 151 ``"Not=A?Brand";v="99"``.
        """
        first = _GREASE_CHARS[major_int % len(_GREASE_CHARS)]
        second = _GREASE_CHARS[(major_int + 1) % len(_GREASE_CHARS)]
        brand = f'Not{first}A{second}Brand'
        version = _GREASE_VERSIONS[major_int % len(_GREASE_VERSIONS)]
        return brand, version, f'{version}.0.0.0'

    @staticmethod
    def _order_brands(
        major_int: int, brands: list[UserAgentBrandVersion]
    ) -> list[UserAgentBrandVersion]:
        """Permute ``[grease, Chromium, branded]`` the way Chromium shuffles it.

        Mirrors ``ShuffleBrandList``: the permutation is picked by
        ``major % 6`` from a fixed table and applied as
        ``shuffled[order[i]] = brands[i]``, so the list order is stable for a given
        major and differs between majors (Chrome 152 leads with Chromium, 151
        with the greased brand).
        """
        order = _BRAND_ORDERS[major_int % len(_BRAND_ORDERS)]
        shuffled: list[UserAgentBrandVersion] = list(brands)
        for index, brand in enumerate(brands):
            shuffled[order[index]] = brand
        return shuffled

    @staticmethod
    def _major_int(version: str) -> int:
        major = version.split('.')[0]
        return int(major) if major.isdigit() else 120

    @staticmethod
    def _build_brands(browser_name: str, major_version: str) -> list[UserAgentBrandVersion]:
        major_int = UserAgentParser._major_int(major_version)
        grease_brand, grease_version, _ = UserAgentParser._build_grease(major_int)

        brands: list[UserAgentBrandVersion] = [
            UserAgentBrandVersion(brand=grease_brand, version=grease_version),
            UserAgentBrandVersion(brand='Chromium', version=major_version),
            UserAgentBrandVersion(brand=browser_name, version=major_version),
        ]
        return UserAgentParser._order_brands(major_int, brands)

    @staticmethod
    def _build_full_version_list(
        browser_name: str, full_version: str
    ) -> list[UserAgentBrandVersion]:
        major_int = UserAgentParser._major_int(full_version)
        grease_brand, _, grease_full_version = UserAgentParser._build_grease(major_int)

        versions: list[UserAgentBrandVersion] = [
            UserAgentBrandVersion(brand=grease_brand, version=grease_full_version),
            UserAgentBrandVersion(brand='Chromium', version=full_version),
            UserAgentBrandVersion(brand=browser_name, version=full_version),
        ]
        return UserAgentParser._order_brands(major_int, versions)

    @staticmethod
    def _extract_model(user_agent: str) -> str:
        match = re.search(r';\s*([A-Za-z0-9_ ]+)\s*Build/', user_agent)
        if match:
            return match.group(1).strip()
        return ''
