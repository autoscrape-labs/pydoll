"""Fingerprint configuration types for browser identity management.

These TypedDicts define the structure for configuring a consistent browser
fingerprint profile that can be injected into a Tab via CDP commands and
JavaScript overrides.

Anti-bot systems (Cloudflare, Akamai, DataDome, Kasada) cross-reference
signals across ALL layers, so configured values must tell a coherent story:

    Network layer (genuine when using real Chrome — not controllable via CDP):
        - TLS fingerprint (JA3/JA4) from BoringSSL ClientHello
        - HTTP/2 fingerprint (SETTINGS, WINDOW_UPDATE, PRIORITY frames)
        - TCP fingerprint (TTL, window size, MSS — depends on host OS)

    Browser layer (controllable via this config):
        - User-Agent string + Client Hints + navigator properties
        - WebGL GPU identification (vendor, renderer, capabilities)
        - Screen dimensions and display properties
        - Hardware capabilities (CPU cores, memory, touch)
        - Geolocation coordinates
        - Timezone and locale/language
        - AudioContext properties
        - Media device counts

Key consistency rules:
    - User-Agent OS must match navigator.platform, WebGL renderer, and screen
    - Timezone must align with geolocation coordinates and proxy IP location
    - Languages must match Accept-Language header and locale settings
    - WebGL renderer must be plausible for the claimed OS/platform
    - Hardware specs (cores, memory) must be realistic for the device type
    - Screen dimensions must match the device class (mobile vs desktop)
    - devicePixelRatio must match the display type (1.0 standard, 2.0 retina)
"""

from typing_extensions import NotRequired, TypedDict


class WebGLProfile(TypedDict):
    """WebGL GPU fingerprint profile.

    Controls what the WebGL API reports about GPU hardware. Anti-bot systems
    use the WEBGL_debug_renderer_info extension to extract vendor and renderer
    strings, then cross-reference with the claimed OS/platform for consistency.
    WebGL fingerprinting alone can uniquely identify ~99% of desktop users.

    The vendor and renderer strings are the most critical fields — they must
    be plausible for the OS claimed in the User-Agent. The optional parameter
    overrides (max_texture_size, etc.) should only be set if you need to match
    a specific GPU's capability profile; incorrect values trigger inconsistency
    detection.

    Capability overrides must stay internally physical. In particular, if
    ``max_combined_texture_image_units`` is overridden, override the per-stage
    ``max_texture_image_units`` and ``max_vertex_texture_image_units`` too:
    leaving them unset lets them fall back to the real GPU, and the spec
    invariant ``combined >= vertex + fragment`` is then easily contradicted
    (e.g. a spoofed combined of 128 over a real per-stage of 16). A single
    impossible triple is a reliable WebGL lie signal.

    When ``webgl2_extensions`` is provided, it is used for WebGL2 contexts
    while ``supported_extensions`` is used for WebGL1. If only
    ``supported_extensions`` is provided, it is used for both contexts.
    WebGL2 has many WebGL1 extensions built-in (e.g. OES_vertex_array_object),
    so their extension lists differ in practice.

    Examples:
        NVIDIA on Windows::

            WebGLProfile(
                vendor='Google Inc. (NVIDIA)',
                renderer='ANGLE (NVIDIA, NVIDIA GeForce RTX 3080 '
                'Direct3D11 vs_5_0 ps_5_0, D3D11)',
            )

        Apple Silicon on macOS::

            WebGLProfile(
                vendor='Google Inc. (Apple)',
                renderer='ANGLE (Apple, Apple M1 Pro, OpenGL 4.1)',
            )

        Intel integrated on Linux::

            WebGLProfile(
                vendor='Google Inc. (Intel)',
                renderer='ANGLE (Intel, Mesa Intel(R) UHD Graphics 630 '
                '(CFL GT2), OpenGL 4.6)',
            )
    """

    vendor: str  # UNMASKED_VENDOR_WEBGL
    renderer: str  # UNMASKED_RENDERER_WEBGL
    max_texture_size: NotRequired[int]  # gl.MAX_TEXTURE_SIZE (e.g. 16384)
    max_renderbuffer_size: NotRequired[int]  # gl.MAX_RENDERBUFFER_SIZE
    max_viewport_dims: NotRequired[list[int]]  # [width, height]
    max_vertex_attribs: NotRequired[int]  # gl.MAX_VERTEX_ATTRIBS
    max_vertex_uniform_vectors: NotRequired[int]
    max_fragment_uniform_vectors: NotRequired[int]
    max_texture_image_units: NotRequired[int]  # gl.MAX_TEXTURE_IMAGE_UNITS (fragment stage)
    max_vertex_texture_image_units: NotRequired[int]  # gl.MAX_VERTEX_TEXTURE_IMAGE_UNITS
    max_combined_texture_image_units: NotRequired[int]
    aliased_line_width_range: NotRequired[list[float]]  # [min, max]
    aliased_point_size_range: NotRequired[list[float]]  # [min, max]
    supported_extensions: NotRequired[list[str]]  # WebGL1 extension names
    webgl2_extensions: NotRequired[list[str]]  # WebGL2-specific extension names
    shader_precision_formats: NotRequired[
        dict[str, dict[str, list[int]]]
    ]  # e.g. {"vertex": {"highFloat": [127, 127, 23]}}


class ScreenFingerprint(TypedDict):
    """Screen and display fingerprint profile.

    Controls screen dimensions and display properties reported by the
    ``screen`` object and ``window.devicePixelRatio``. Must be consistent
    with the claimed device type — headless browsers often report unusual
    dimensions that anti-bot systems flag.

    ``avail_width`` and ``avail_height`` should be slightly less than
    ``width`` and ``height`` to account for the OS taskbar/dock. Setting
    them equal to width/height is a headless indicator.

    ``outer_width`` and ``outer_height`` represent the browser window
    dimensions including chrome (toolbar, scrollbar). In headless mode
    these are often 0, which is an instant detection signal.

    ``inner_width`` and ``inner_height`` override ``window.innerWidth``
    and ``window.innerHeight``. For mobile profiles these should be
    close to or equal to ``width``/``height``. If not set, the real
    browser viewport dimensions are used.

    ``orientation_type`` controls ``screen.orientation.type`` and should
    be ``'portrait-primary'`` for mobile or ``'landscape-primary'`` for
    desktop. ``orientation_angle`` defaults to 0.

    Common desktop profiles:
        - 1920x1080, DPR 1.0 (Full HD)
        - 2560x1440, DPR 1.0 (QHD)
        - 1920x1080, DPR 2.0 (Retina/HiDPI)
        - 3840x2160, DPR 2.0 (4K Retina)

    Common mobile profiles:
        - 390x844, DPR 3.0 (iPhone 14)
        - 360x800, DPR 2.0 (Android mid-range)
    """

    width: int  # screen.width
    height: int  # screen.height
    avail_width: NotRequired[int]  # screen.availWidth
    avail_height: NotRequired[int]  # screen.availHeight
    outer_width: NotRequired[int]  # window.outerWidth
    outer_height: NotRequired[int]  # window.outerHeight
    color_depth: NotRequired[int]  # screen.colorDepth (typically 24)
    pixel_depth: NotRequired[int]  # screen.pixelDepth (usually == colorDepth)
    device_pixel_ratio: NotRequired[float]  # window.devicePixelRatio
    inner_width: NotRequired[int]  # window.innerWidth
    inner_height: NotRequired[int]  # window.innerHeight
    orientation_type: NotRequired[str]  # 'portrait-primary', 'landscape-primary'
    orientation_angle: NotRequired[int]  # 0, 90, 180, 270


class GeolocationFingerprint(TypedDict):
    """Geolocation fingerprint profile.

    Injected via CDP ``Emulation.setGeolocationOverride``. Coordinates
    should be consistent with the proxy IP's geographic location and
    the configured timezone. Anti-bot systems cross-reference these:
    a New York IP with Tokyo coordinates and UTC+3 timezone is flagged.
    """

    latitude: float
    longitude: float
    accuracy: NotRequired[float]  # meters (default ~100)


class HardwareFingerprint(TypedDict):
    """Hardware fingerprint profile.

    Controls ``navigator`` properties that reveal hardware capabilities.
    Values must be plausible for the claimed platform.

    ``device_memory`` only accepts values from the set:
    {0.25, 0.5, 1, 2, 4, 8} — these are the only values the browser
    API can return (values are bucketed for fingerprinting resistance).

    ``max_touch_points`` is 0 for desktop browsers and typically 5 or 10
    for mobile. Setting a non-zero value on a desktop User-Agent is an
    inconsistency signal.

    Typical desktop profiles:
        - hardware_concurrency: 4, 8, 12, 16
        - device_memory: 4, 8
        - max_touch_points: 0

    Typical mobile profiles:
        - hardware_concurrency: 4, 8
        - device_memory: 2, 4
        - max_touch_points: 5, 10
    """

    hardware_concurrency: NotRequired[int]  # navigator.hardwareConcurrency
    device_memory: NotRequired[float]  # navigator.deviceMemory (GB)
    max_touch_points: NotRequired[int]  # navigator.maxTouchPoints


class MediaDevicesFingerprint(TypedDict):
    """Media devices fingerprint profile.

    Controls what ``navigator.mediaDevices.enumerateDevices()`` reports.
    A typical desktop setup has 1 audio input (microphone), 1-2 audio
    outputs (speakers + headphones), and 1 video input (webcam).
    Headless browsers often report 0 devices for all categories.
    """

    audio_inputs: NotRequired[int]  # microphones
    audio_outputs: NotRequired[int]  # speakers/headphones
    video_inputs: NotRequired[int]  # cameras


class AudioFingerprint(TypedDict):
    """AudioContext fingerprint profile.

    Controls ``AudioContext`` properties. Anti-bot systems fingerprint
    audio by creating an ``OfflineAudioContext``, running an oscillator
    through a ``DynamicsCompressorNode``, and hashing the output samples.
    The actual processing output depends on hardware/OS/browser internals
    and is extremely difficult to spoof without detection.

    These properties control the reported capabilities only — they do not
    affect the actual audio processing output.
    """

    sample_rate: NotRequired[float]  # AudioContext.sampleRate (44100, 48000)
    max_channel_count: NotRequired[int]  # destination.maxChannelCount (2, 6)


class SpeechVoice(TypedDict):
    """A single speech synthesis voice entry.

    Speech voices vary by OS and reveal the platform. Windows has
    Microsoft voices, macOS has Apple voices, Linux has espeak voices.
    """

    name: str  # e.g. "Microsoft David - English (United States)"
    lang: str  # e.g. "en-US"
    local_service: NotRequired[bool]  # whether it's a local voice


class SpeechFingerprint(TypedDict):
    """Speech synthesis fingerprint profile.

    Controls what ``speechSynthesis.getVoices()`` returns. The available
    voices are highly OS-specific and provide an independent platform
    verification signal.
    """

    voices: list[SpeechVoice]


class LocaleFingerprint(TypedDict):
    """Locale and language fingerprint profile.

    Controls language-related properties. Must be consistent with the
    ``Accept-Language`` HTTP header and the proxy IP's geographic region.

    ``languages`` maps to ``navigator.languages`` (an ordered list of
    preferred languages). The first element must match ``navigator.language``.

    Example for a US English user::

        LocaleFingerprint(languages=['en-US', 'en'])

    Example for a Brazilian Portuguese user::

        LocaleFingerprint(languages=['pt-BR', 'pt', 'en-US', 'en'])
    """

    languages: list[str]  # navigator.languages


class NavigatorFingerprint(TypedDict):
    """Extra navigator properties for fine-grained control.

    Most navigator properties are automatically derived from the
    ``user_agent`` string via the UserAgentParser. Use this only when
    you need to override specific properties that aren't captured by
    the automatic derivation.

    When ``user_agent`` is also set in the parent ``FingerprintConfig``,
    ``platform``, ``vendor``, and ``app_version`` are handled by CDP
    and UserAgentParser at a lower level. JS overrides for these are
    skipped to avoid creating detectable own-properties.
    """

    platform: NotRequired[str]  # navigator.platform ("Win32", "MacIntel")
    vendor: NotRequired[str]  # navigator.vendor ("Google Inc.")
    app_version: NotRequired[str]  # navigator.appVersion
    pdf_viewer_enabled: NotRequired[bool]  # navigator.pdfViewerEnabled
    do_not_track: NotRequired[str]  # navigator.doNotTrack (null, "1")


class NetworkConnectionFingerprint(TypedDict):
    """Navigator.connection (NetworkInformation API) fingerprint.

    Controls what ``navigator.connection`` reports. Values should be
    consistent with the claimed device type and network conditions.

    Typical profiles:
        - Desktop on broadband: effective_type='4g', downlink=10.0, rtt=50
        - Mobile on LTE: effective_type='4g', downlink=5.0, rtt=100
        - Mobile on 3G: effective_type='3g', downlink=1.5, rtt=300
    """

    effective_type: NotRequired[str]  # '4g', '3g', '2g', 'slow-2g'
    downlink: NotRequired[float]  # Mbps
    rtt: NotRequired[int]  # ms
    save_data: NotRequired[bool]


class FontFingerprint(TypedDict):
    """Font fingerprint profile.

    Controls what ``document.fonts.check()`` reports as available.
    Font availability is highly OS-specific and a strong fingerprinting
    signal. Windows, macOS, and Linux each have distinct default font sets.
    """

    available_fonts: list[str]  # font families reported as available


class PermissionsFingerprint(TypedDict):
    """Permissions API fingerprint profile.

    Controls what ``navigator.permissions.query()`` returns for specific
    permission names. Maps permission name to state string.

    Valid states: 'granted', 'denied', 'prompt'

    Example::

        PermissionsFingerprint(
            overrides={
                'notifications': 'denied',
                'geolocation': 'prompt',
            }
        )
    """

    overrides: dict[str, str]  # permission name -> 'granted'|'denied'|'prompt'


class FingerprintConfig(TypedDict):
    """Complete browser fingerprint configuration.

    Defines a consistent browser identity profile that can be injected
    into a Tab. All fields are optional — only specified fields will be
    overridden; unspecified fields retain the browser's real values.

    When ``user_agent`` is set, pydoll automatically synchronizes the
    User-Agent across all layers using the existing UserAgentParser:
    HTTP headers, ``navigator.userAgent``, ``navigator.platform``,
    ``navigator.vendor``, ``navigator.appVersion``, and ``Sec-CH-UA``
    Client Hints (including GREASE brand rotation).

    When ``mobile`` is set, it overrides the auto-detected mobile flag
    from the User-Agent for both CDP device metrics and Client Hints
    (``Sec-CH-UA-Mobile``). If not set, mobile is auto-detected from
    the User-Agent string, defaulting to ``False`` when no UA is given.

    Usage example::

        fingerprint = FingerprintConfig(
            user_agent=(
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            ),
            webgl=WebGLProfile(
                vendor='Google Inc. (NVIDIA)',
                renderer='ANGLE (NVIDIA, NVIDIA GeForce RTX 3080 '
                'Direct3D11 vs_5_0 ps_5_0, D3D11)',
            ),
            screen=ScreenFingerprint(
                width=1920,
                height=1080,
                device_pixel_ratio=1.0,
            ),
            hardware=HardwareFingerprint(
                hardware_concurrency=8,
                device_memory=8,
                max_touch_points=0,
            ),
            geolocation=GeolocationFingerprint(
                latitude=40.7128,
                longitude=-74.0060,
            ),
            timezone='America/New_York',
            locale=LocaleFingerprint(languages=['en-US', 'en']),
        )
    """

    user_agent: NotRequired[str]  # full User-Agent string
    mobile: NotRequired[bool]  # override mobile flag (auto-detected from UA)
    navigator: NotRequired[NavigatorFingerprint]
    webgl: NotRequired[WebGLProfile]
    screen: NotRequired[ScreenFingerprint]
    geolocation: NotRequired[GeolocationFingerprint]
    hardware: NotRequired[HardwareFingerprint]
    media_devices: NotRequired[MediaDevicesFingerprint]
    audio: NotRequired[AudioFingerprint]
    speech: NotRequired[SpeechFingerprint]
    locale: NotRequired[LocaleFingerprint]
    timezone: NotRequired[str]  # IANA timezone e.g. "America/New_York"
    network_connection: NotRequired[NetworkConnectionFingerprint]
    fonts: NotRequired[FontFingerprint]
    permissions: NotRequired[PermissionsFingerprint]
    webrtc_ip_policy: NotRequired[str]  # 'default' or 'relay'
