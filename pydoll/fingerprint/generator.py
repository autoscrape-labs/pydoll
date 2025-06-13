"""
Browser fingerprint generator.

This module provides the FingerprintGenerator class which creates realistic
browser fingerprints with randomized but consistent properties.
"""

import random
import string
from typing import Dict, List, Optional, Tuple

from .models import Fingerprint, FingerprintConfig

# Constants for magic values
DEVICE_MEMORY_THRESHOLD = 0.3
DO_NOT_TRACK_THRESHOLD = 0.8


class FingerprintGenerator:
    """
    Generates realistic browser fingerprints for spoofing purposes.

    This class creates fingerprints that appear authentic to fingerprinting
    detection systems by using realistic combinations of browser properties.
    """

    # Chrome versions (recent stable versions)
    CHROME_VERSIONS = [
        '120.0.6099.129', '121.0.6167.139', '122.0.6261.69',
        '123.0.6312.86', '124.0.6367.62', '125.0.6422.76',
        '126.0.6478.55', '127.0.6533.110', '128.0.6613.120',
        '129.0.6668.100', '130.0.6723.70', '131.0.6778.85'
    ]

    # Edge versions
    EDGE_VERSIONS = [
        '120.0.2210.89', '121.0.2277.98', '122.0.2365.59',
        '123.0.2420.53', '124.0.2478.49', '125.0.2535.33',
        '126.0.2592.68', '127.0.2651.105', '128.0.2739.67',
        '129.0.2792.52', '130.0.2849.68', '131.0.2903.70'
    ]

    # Operating systems with realistic distributions
    OPERATING_SYSTEMS = [
        {'name': 'Windows', 'version': '10.0', 'platform': 'Win32'},
        {'name': 'Windows', 'version': '11.0', 'platform': 'Win32'},
        {'name': 'Macintosh', 'version': '10.15.7', 'platform': 'MacIntel'},
        {'name': 'Macintosh', 'version': '11.6.8', 'platform': 'MacIntel'},
        {'name': 'Macintosh', 'version': '12.6.0', 'platform': 'MacIntel'},
        {'name': 'Linux', 'version': 'x86_64', 'platform': 'Linux x86_64'},
    ]

    # Common screen resolutions
    SCREEN_RESOLUTIONS = [
        (1920, 1080), (1366, 768), (1440, 900), (1536, 864),
        (1280, 720), (1600, 900), (2560, 1440), (1920, 1200),
        (1680, 1050), (1280, 1024), (2048, 1152), (1280, 800)
    ]

    # Language preferences
    LANGUAGES = [
        'en-US,en;q=0.9',
        'en-GB,en;q=0.9',
        'zh-CN,zh;q=0.9,en;q=0.8',
        'ja-JP,ja;q=0.9,en;q=0.8',
        'es-ES,es;q=0.9,en;q=0.8',
        'fr-FR,fr;q=0.9,en;q=0.8',
        'de-DE,de;q=0.9,en;q=0.8',
        'ru-RU,ru;q=0.9,en;q=0.8',
        'pt-BR,pt;q=0.9,en;q=0.8',
        'it-IT,it;q=0.9,en;q=0.8',
        'ko-KR,ko;q=0.9,en;q=0.8',
    ]

    # WebGL vendors and renderers
    WEBGL_VENDORS = [
        'Google Inc. (NVIDIA)',
        'Google Inc. (Intel)',
        'Google Inc. (AMD)',
        'Microsoft Corporation (NVIDIA)',
        'Microsoft Corporation (Intel)',
        'Microsoft Corporation (AMD)',
        'NVIDIA Corporation',
        'Intel Inc.',
        'AMD Inc.',
    ]

    WEBGL_RENDERERS = [
        'ANGLE (NVIDIA, NVIDIA GeForce GTX 1060 Direct3D11 vs_5_0 ps_5_0, D3D11)',
        'ANGLE (Intel, Intel(R) UHD Graphics 620 Direct3D11 vs_5_0 ps_5_0, D3D11)',
        'ANGLE (AMD, AMD Radeon RX 580 Direct3D11 vs_5_0 ps_5_0, D3D11)',
        'WebKit WebGL',
        'Mozilla',
        'ANGLE (NVIDIA Corporation, NVIDIA GeForce RTX 3070 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (Intel, Intel(R) Iris(R) Xe Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)',
    ]

    # Common WebGL extensions
    WEBGL_EXTENSIONS = [
        'ANGLE_instanced_arrays', 'EXT_blend_minmax', 'EXT_color_buffer_half_float',
        'EXT_disjoint_timer_query', 'EXT_float_blend', 'EXT_frag_depth',
        'EXT_shader_texture_lod', 'EXT_texture_compression_bptc', 'EXT_texture_compression_rgtc',
        'EXT_texture_filter_anisotropic', 'WEBKIT_EXT_texture_filter_anisotropic',
        'EXT_sRGB', 'OES_element_index_uint', 'OES_fbo_render_mipmap',
        'OES_standard_derivatives', 'OES_texture_float', 'OES_texture_float_linear',
        'OES_texture_half_float', 'OES_texture_half_float_linear', 'OES_vertex_array_object',
        'WEBGL_color_buffer_float', 'WEBGL_compressed_texture_s3tc',
        'WEBKIT_WEBGL_compressed_texture_s3tc', 'WEBGL_compressed_texture_s3tc_srgb',
        'WEBGL_debug_renderer_info', 'WEBGL_debug_shaders', 'WEBGL_depth_texture',
        'WEBKIT_WEBGL_depth_texture', 'WEBGL_draw_buffers', 'WEBGL_lose_context',
        'WEBKIT_WEBGL_lose_context'
    ]

    # Audio context sample rates
    AUDIO_SAMPLE_RATES = [44100, 48000, 96000]

    # Common timezones
    TIMEZONES = [
        'America/New_York', 'America/Los_Angeles', 'America/Chicago',
        'Europe/London', 'Europe/Paris', 'Europe/Berlin',
        'Asia/Tokyo', 'Asia/Shanghai', 'Asia/Seoul',
        'Australia/Sydney', 'America/Toronto', 'Europe/Madrid'
    ]

    def __init__(self, config: Optional[FingerprintConfig] = None):
        """
        Initialize the fingerprint generator.

        Args:
            config: Configuration for fingerprint generation. Uses default if None.
        """
        self.config = config or FingerprintConfig()

    def generate(self) -> Fingerprint:
        """
        Generate a complete browser fingerprint.

        Returns:
            A Fingerprint object with all properties set.
        """
        # Generate basic system properties
        system_properties = self._generate_system_properties()

        # Generate display properties
        display_properties = self._generate_display_properties()

        # Generate browser properties
        browser_properties = self._generate_browser_properties()

        # Generate multimedia properties
        multimedia_properties = self._generate_multimedia_properties()

        # Combine all properties into fingerprint
        return Fingerprint(**{
            **system_properties,
            **display_properties,
            **browser_properties,
            **multimedia_properties,
        })

    def _generate_system_properties(self) -> Dict:
        """Generate system-related properties."""
        os_info = self._choose_operating_system()
        browser_version = self._choose_browser_version()
        language = random.choice(self.LANGUAGES)
        timezone = random.choice(self.TIMEZONES)

        return {
            'user_agent': self._generate_user_agent(os_info, browser_version),
            'platform': os_info['platform'],
            'language': language.split(',')[0],
            'languages': self._generate_language_list(language),
            'hardware_concurrency': random.choice([2, 4, 6, 8, 12, 16]),
            'device_memory': (
                random.choice([2, 4, 8, 16])
                if random.random() > DEVICE_MEMORY_THRESHOLD
                else None
            ),
            'timezone': timezone,
            'timezone_offset': self._get_timezone_offset(timezone),
            'browser_type': self.config.browser_type,
            'browser_version': browser_version,
            'chrome_version': browser_version if self.config.browser_type == 'chrome' else None,
            'cookie_enabled': True,
            'do_not_track': (
                random.choice([None, '1'])
                if random.random() > DO_NOT_TRACK_THRESHOLD
                else None
            ),
            'webdriver': False,
            'connection_type': random.choice(['wifi', 'ethernet', 'cellular']),
        }

    def _generate_display_properties(self) -> Dict:
        """Generate display and viewport properties."""
        screen_width, screen_height = self._choose_screen_resolution()
        viewport_width = screen_width - random.randint(0, 100)
        viewport_height = screen_height - random.randint(100, 200)

        return {
            'screen_width': screen_width,
            'screen_height': screen_height,
            'screen_color_depth': 24,
            'screen_pixel_depth': 24,
            'available_width': screen_width,
            'available_height': screen_height - 40,  # Account for taskbar
            'viewport_width': viewport_width,
            'viewport_height': viewport_height,
            'inner_width': viewport_width,
            'inner_height': viewport_height - 120,  # Account for browser UI
        }

    def _generate_browser_properties(self) -> Dict:
        """Generate browser-specific properties."""
        webgl_vendor, webgl_renderer = self._choose_webgl_properties()

        return {
            'webgl_vendor': webgl_vendor,
            'webgl_renderer': webgl_renderer,
            'webgl_version': 'WebGL 1.0 (OpenGL ES 2.0 Chromium)',
            'webgl_shading_language_version': 'WebGL GLSL ES 1.0 (OpenGL ES GLSL ES 1.0 Chromium)',
            'webgl_extensions': random.sample(self.WEBGL_EXTENSIONS, random.randint(15, 25)),
            'canvas_fingerprint': self._generate_canvas_fingerprint(),
            'plugins': self._generate_plugins() if self.config.include_plugins else [],
        }

    def _generate_multimedia_properties(self) -> Dict:
        """Generate multimedia-related properties."""
        return {
            'audio_context_sample_rate': float(random.choice(self.AUDIO_SAMPLE_RATES)),
            'audio_context_state': 'suspended',
            'audio_context_max_channel_count': random.choice([2, 6, 8]),
        }

    def _choose_operating_system(self) -> Dict[str, str]:
        """Choose a random operating system."""
        if self.config.preferred_os:
            filtered_os = [os for os in self.OPERATING_SYSTEMS
                          if os['name'].lower() == self.config.preferred_os.lower()]
            if filtered_os:
                return random.choice(filtered_os)

        return random.choice(self.OPERATING_SYSTEMS)

    def _choose_browser_version(self) -> str:
        """Choose a random browser version."""
        if self.config.browser_type == 'edge':
            return random.choice(self.EDGE_VERSIONS)
        else:
            return random.choice(self.CHROME_VERSIONS)

    def _choose_screen_resolution(self) -> Tuple[int, int]:
        """Choose a screen resolution within configured bounds."""
        valid_resolutions = [
            (w, h) for w, h in self.SCREEN_RESOLUTIONS
            if self.config.min_screen_width <= w <= self.config.max_screen_width
            and self.config.min_screen_height <= h <= self.config.max_screen_height
        ]

        if not valid_resolutions:
            # Fallback to a default resolution
            return (1920, 1080)

        return random.choice(valid_resolutions)

    def _choose_webgl_properties(self) -> Tuple[str, str]:
        """Choose WebGL vendor and renderer."""
        vendor = random.choice(self.WEBGL_VENDORS)
        renderer = random.choice(self.WEBGL_RENDERERS)
        return vendor, renderer

    def _generate_user_agent(self, os_info: Dict[str, str], browser_version: str) -> str:
        """Generate a realistic user agent string."""
        os_name = os_info['name']
        os_version = os_info['version']

        if self.config.browser_type == 'chrome':
            return self._generate_chrome_user_agent(os_name, os_version, browser_version)
        elif self.config.browser_type == 'edge':
            return self._generate_edge_user_agent(os_name, os_version, browser_version)
        else:
            # Fallback to Chrome
            return self._generate_chrome_user_agent('Windows', '10.0', browser_version)

    def _generate_chrome_user_agent(self, os_name: str, os_version: str, browser_version: str) -> str:
        """Generate Chrome user agent for specific OS."""
        base_template = 'Mozilla/5.0 ({os_part}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36'

        os_parts = {
            'Windows': f'Windows NT {os_version}; Win64; x64',
            'Macintosh': f'Macintosh; Intel Mac OS X {os_version.replace(".", "_")}',
            'Linux': 'X11; Linux x86_64'
        }

        os_part = os_parts.get(os_name, os_parts['Windows'])
        return base_template.format(os_part=os_part, version=browser_version)

    def _generate_edge_user_agent(self, os_name: str, os_version: str, browser_version: str) -> str:
        """Generate Edge user agent for specific OS."""
        chrome_major = browser_version.split(".")[0]
        base_template = 'Mozilla/5.0 ({os_part}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_major}.0.0.0 Safari/537.36 Edg/{version}'

        os_parts = {
            'Windows': f'Windows NT {os_version}; Win64; x64',
            'Macintosh': f'Macintosh; Intel Mac OS X {os_version.replace(".", "_")}',
            'Linux': 'X11; Linux x86_64'
        }

        os_part = os_parts.get(os_name, os_parts['Windows'])
        return base_template.format(os_part=os_part, chrome_major=chrome_major, version=browser_version)

    @staticmethod
    def _generate_language_list(primary_language: str) -> List[str]:
        """Generate a list of languages based on the primary language."""
        base_lang = primary_language.split(',')[0]
        lang_code = base_lang.split('-')[0]

        languages = [base_lang]

        # Add the base language code if different
        if lang_code != base_lang:
            languages.append(lang_code)

        # Add English as fallback for non-English primary languages
        if not base_lang.startswith('en'):
            languages.extend(['en-US', 'en'])

        return languages

    @staticmethod
    def _get_timezone_offset(timezone: str) -> int:
        """Get timezone offset for a given timezone."""
        # Simplified timezone offset mapping
        offset_map = {
            'America/New_York': -300,  # EST/EDT
            'America/Los_Angeles': -480,  # PST/PDT
            'America/Chicago': -360,  # CST/CDT
            'Europe/London': 0,  # GMT/BST
            'Europe/Paris': 60,  # CET/CEST
            'Europe/Berlin': 60,  # CET/CEST
            'Asia/Tokyo': 540,  # JST
            'Asia/Shanghai': 480,  # CST
            'Asia/Seoul': 540,  # KST
            'Australia/Sydney': 600,  # AEST/AEDT
            'America/Toronto': -300,  # EST/EDT
            'Europe/Madrid': 60,  # CET/CEST
        }

        return offset_map.get(timezone, 0)

    @staticmethod
    def _generate_canvas_fingerprint() -> str:
        """Generate a unique canvas fingerprint."""
        # Generate a pseudo-random canvas fingerprint
        random_data = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        return f"canvas_fp_{random_data}"

    def _generate_plugins(self) -> List[Dict[str, str]]:
        """Generate a realistic list of browser plugins."""
        common_plugins = [
            {
                'name': 'PDF Viewer',
                'filename': 'internal-pdf-viewer',
                'description': 'Portable Document Format'
            },
            {
                'name': 'Chrome PDF Viewer',
                'filename': 'mhjfbmdgcfjbbpaeojofohoefgiehjai',
                'description': ''
            },
            {
                'name': 'Chromium PDF Viewer',
                'filename': 'mhjfbmdgcfjbbpaeojofohoefgiehjai',
                'description': ''
            },
            {
                'name': 'Microsoft Edge PDF Viewer',
                'filename': 'mhjfbmdgcfjbbpaeojofohoefgiehjai',
                'description': ''
            },
            {
                'name': 'WebKit built-in PDF',
                'filename': 'webkit-built-in-pdf',
                'description': ''
            },
        ]

        # Randomly select and return plugins
        num_plugins = min(random.randint(1, self.config.max_plugins), len(common_plugins))
        return random.sample(common_plugins, num_plugins)
