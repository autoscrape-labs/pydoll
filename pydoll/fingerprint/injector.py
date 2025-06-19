"""
Browser fingerprint injection module.

This module provides the FingerprintInjector class, which generates JavaScript
code for fingerprint spoofing.
"""

from ..constants import Scripts
from .models import Fingerprint


class FingerprintInjector:
    """
    Generates JavaScript code to inject fingerprint spoofing into browsers.

    This class creates JavaScript that overrides various browser APIs and
    properties to present a fake fingerprint to detection systems.
    """

    def __init__(self, fingerprint: Fingerprint):
        """
        Initialize the injector with a fingerprint.

        Args:
            fingerprint: The fingerprint data to inject.
        """
        self.fingerprint = fingerprint

    def generate_script(self) -> str:
        """
        Generate the complete JavaScript injection script.

        Returns:
            JavaScript code as a string that will override browser properties.
        """
        scripts = [
            self._generate_navigator_override(),
            self._generate_screen_override(),
            self._generate_webgl_override(),
            self._generate_canvas_override(),
            self._generate_audio_override(),
            self._generate_plugin_override(),
            self._generate_misc_overrides(),
        ]

        # Use the script template from constants
        return Scripts.FINGERPRINT_WRAPPER.format(scripts=chr(10).join(scripts))

    def _generate_navigator_override(self) -> str:
        """Generate JavaScript to override navigator properties."""
        languages_js = str(self.fingerprint.languages).replace("'", '"')

        # Conditional script parts
        device_memory_script = (
            'Object.defineProperty(navigator, "deviceMemory", { get: () => ' +
            str(self.fingerprint.device_memory) +
            ', configurable: true });'
        ) if self.fingerprint.device_memory else ''

        do_not_track_script = (
            'Object.defineProperty(navigator, "doNotTrack", { get: () => "' +
            str(self.fingerprint.do_not_track) +
            '", configurable: true });'
        ) if self.fingerprint.do_not_track else ''

        # Use the script template from constants
        return Scripts.NAVIGATOR_OVERRIDE.format(
            user_agent=self.fingerprint.user_agent,
            platform=self.fingerprint.platform,
            language=self.fingerprint.language,
            languages=languages_js,
            hardware_concurrency=self.fingerprint.hardware_concurrency,
            device_memory_script=device_memory_script,
            cookie_enabled=str(self.fingerprint.cookie_enabled).lower(),
            do_not_track_script=do_not_track_script
        )

    def _generate_screen_override(self) -> str:
        """Generate JavaScript to override screen properties."""
        # Use the script template from constants
        return Scripts.SCREEN_OVERRIDE.format(
            screen_width=self.fingerprint.screen_width,
            screen_height=self.fingerprint.screen_height,
            screen_color_depth=self.fingerprint.screen_color_depth,
            screen_pixel_depth=self.fingerprint.screen_pixel_depth,
            available_width=self.fingerprint.available_width,
            available_height=self.fingerprint.available_height,
            inner_width=self.fingerprint.inner_width,
            inner_height=self.fingerprint.inner_height,
            viewport_width=self.fingerprint.viewport_width,
            viewport_height=self.fingerprint.viewport_height
        )

    def _generate_webgl_override(self) -> str:
        """Generate JavaScript to override WebGL properties."""
        extensions_js = str(self.fingerprint.webgl_extensions).replace("'", '"')

        # Use the script template from constants
        return Scripts.WEBGL_OVERRIDE.format(
            webgl_vendor=self.fingerprint.webgl_vendor,
            webgl_renderer=self.fingerprint.webgl_renderer,
            webgl_version=self.fingerprint.webgl_version,
            webgl_shading_language_version=self.fingerprint.webgl_shading_language_version,
            webgl_extensions=extensions_js
        )

    def _generate_canvas_override(self) -> str:
        """Generate JavaScript to override canvas fingerprinting."""
        # Use the script template from constants
        return Scripts.CANVAS_OVERRIDE.format(
            canvas_fingerprint=self.fingerprint.canvas_fingerprint
        )

    def _generate_audio_override(self) -> str:
        """Generate JavaScript to override audio context properties."""
        # Use the script template from constants
        return Scripts.AUDIO_OVERRIDE.format(
            audio_context_sample_rate=self.fingerprint.audio_context_sample_rate,
            audio_context_state=self.fingerprint.audio_context_state,
            audio_context_max_channel_count=self.fingerprint.audio_context_max_channel_count
        )

    def _generate_plugin_override(self) -> str:
        """Generate JavaScript to override plugin information."""
        if not self.fingerprint.plugins:
            return ""

        plugins_js = []
        for i, plugin in enumerate(self.fingerprint.plugins):
            plugins_js.append(f"""
        plugins[{i}] = {{
            name: '{plugin['name']}',
            filename: '{plugin['filename']}',
            description: '{plugin['description']}',
            length: 1,
            0: {{
                type: 'application/pdf',
                suffixes: 'pdf',
                description: '{plugin['description']}'
            }}
        }};""")

        # Use the script template from constants
        return Scripts.PLUGIN_OVERRIDE.format(
            plugins_length=len(self.fingerprint.plugins),
            plugins_js=''.join(plugins_js)
        )

    def _generate_misc_overrides(self) -> str:
        """Generate JavaScript for miscellaneous overrides."""
        # Use the script template from constants
        return Scripts.MISC_OVERRIDES.format(
            timezone_offset=self.fingerprint.timezone_offset,
            timezone=self.fingerprint.timezone,
            connection_type=self.fingerprint.connection_type
        )
