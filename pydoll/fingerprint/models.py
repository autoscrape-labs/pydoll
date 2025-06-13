"""
Data models for browser fingerprint spoofing.

This module defines the data structures used to represent browser fingerprints
and their configuration parameters.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Union


@dataclass
class Fingerprint:
    """
    Represents a complete browser fingerprint configuration.

    This class contains all the necessary data to spoof a browser's fingerprint,
    including navigator properties, screen dimensions, WebGL settings, and more.
    """

    # Navigator properties (required fields first)
    user_agent: str
    platform: str
    language: str
    languages: List[str]
    hardware_concurrency: int

    # Screen properties
    screen_width: int
    screen_height: int
    screen_color_depth: int
    screen_pixel_depth: int
    available_width: int
    available_height: int

    # Viewport properties
    viewport_width: int
    viewport_height: int
    inner_width: int
    inner_height: int

    # WebGL properties
    webgl_vendor: str
    webgl_renderer: str
    webgl_version: str
    webgl_shading_language_version: str
    webgl_extensions: List[str]

    # Canvas fingerprint
    canvas_fingerprint: str

    # Audio context properties
    audio_context_sample_rate: float
    audio_context_state: str
    audio_context_max_channel_count: int

    # Timezone and locale
    timezone: str
    timezone_offset: int

    # Browser specific
    browser_type: str
    browser_version: str

    # Plugin information
    plugins: List[Dict[str, str]]

    # Optional properties with defaults (must come last)
    device_memory: Optional[int] = None
    chrome_version: Optional[str] = None
    cookie_enabled: bool = True
    do_not_track: Optional[str] = None
    webdriver: bool = False
    connection_type: str = "wifi"

    def to_dict(self) -> Dict[str, Union[str, int, float, bool, List, None]]:
        """Convert fingerprint to dictionary format."""
        result = {}
        for key, value in self.__dict__.items():
            result[key] = value
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Union[str, int, float, bool, List, None]]) -> 'Fingerprint':
        """Create fingerprint from dictionary format."""
        return cls(**data)  # type: ignore[arg-type]


@dataclass
class FingerprintConfig:
    """
    Configuration for fingerprint generation.

    This class defines the parameters that control how fingerprints are generated,
    allowing for customization of the spoofing behavior.
    """

    # Browser configuration
    browser_type: str = "chrome"
    is_mobile: bool = False

    # Operating system preferences
    preferred_os: Optional[str] = None  # "windows", "macos", "linux"

    # Language and locale preferences
    preferred_languages: Optional[List[str]] = None
    preferred_timezone: Optional[str] = None

    # Screen configuration
    min_screen_width: int = 1024
    max_screen_width: int = 2560
    min_screen_height: int = 768
    max_screen_height: int = 1440

    # WebGL configuration
    enable_webgl_spoofing: bool = True
    enable_canvas_spoofing: bool = True
    enable_audio_spoofing: bool = True

    # Plugin configuration
    include_plugins: bool = True
    max_plugins: int = 5

    # Advanced options
    enable_touch_support: bool = False
    enable_webrtc_spoofing: bool = True

    def to_dict(self) -> Dict[str, Union[str, int, bool, List, None]]:
        """Convert config to dictionary format."""
        result = {}
        for key, value in self.__dict__.items():
            result[key] = value
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Union[str, int, bool, List, None]]) -> 'FingerprintConfig':
        """Create config from dictionary format."""
        return cls(**data)  # type: ignore[arg-type]
