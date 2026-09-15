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

    The uniform limits are bound by GLES 3.0 arithmetic a detector recomputes
    from the same context: ``MAX_*_UNIFORM_COMPONENTS`` is exactly
    ``4 * MAX_*_UNIFORM_VECTORS``, and ``MAX_COMBINED_*_UNIFORM_COMPONENTS`` is
    exactly ``MAX_*_UNIFORM_COMPONENTS + MAX_*_UNIFORM_BLOCKS *
    MAX_UNIFORM_BLOCK_SIZE / 4``. Override one member of a family and the rest
    fall back to the real GPU, which leaves the identity broken, so set the
    whole family from one device or leave all of it unset.

    When ``webgl2_extensions`` is provided, it is used for WebGL2 contexts
    while ``supported_extensions`` is used for WebGL1. If only
    ``supported_extensions`` is provided, it is used for both contexts.
    WebGL2 has many WebGL1 extensions built-in (e.g. OES_vertex_array_object),
    so their extension lists differ in practice.

    ``supported_extensions`` / ``webgl2_extensions`` are an allow-list: an
    extension the real GPU does not implement is dropped from
    ``getSupportedExtensions()`` and ``getExtension()`` returns ``null`` for it,
    so the page never sees a fake extension object. WebGL2-only limits
    (``max_3d_texture_size``, ``max_samples``, ``max_uniform_block_size``, ...)
    are read by fingerprinting suites alongside the WebGL1 ones; leave any of
    them unset and the real GPU's value is reported, so set the whole family
    from one real device capture. ``WEBGL_debug_shaders`` is always hidden
    when a WebGL profile is applied: its translated shader source names the
    real backend (HLSL, Metal, GLSL) and would contradict the claimed renderer.

    Examples:
        NVIDIA on Windows (current Chrome includes the PCI device id)::

            WebGLProfile(
                vendor='Google Inc. (NVIDIA)',
                renderer='ANGLE (NVIDIA, NVIDIA GeForce RTX 3080 (0x00002206) '
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
    max_vertex_uniform_components: NotRequired[int]  # gl2.MAX_VERTEX_UNIFORM_COMPONENTS
    max_fragment_uniform_vectors: NotRequired[int]
    max_fragment_uniform_components: NotRequired[int]  # gl2.MAX_FRAGMENT_UNIFORM_COMPONENTS
    max_texture_image_units: NotRequired[int]  # gl.MAX_TEXTURE_IMAGE_UNITS (fragment stage)
    max_vertex_texture_image_units: NotRequired[int]  # gl.MAX_VERTEX_TEXTURE_IMAGE_UNITS
    max_combined_texture_image_units: NotRequired[int]
    aliased_line_width_range: NotRequired[list[float]]  # [min, max]
    aliased_point_size_range: NotRequired[list[float]]  # [min, max]
    max_cube_map_texture_size: NotRequired[int]  # gl.MAX_CUBE_MAP_TEXTURE_SIZE
    max_varying_vectors: NotRequired[int]  # gl.MAX_VARYING_VECTORS
    max_varying_components: NotRequired[int]  # gl2.MAX_VARYING_COMPONENTS
    max_3d_texture_size: NotRequired[int]  # gl2.MAX_3D_TEXTURE_SIZE
    max_array_texture_layers: NotRequired[int]  # gl2.MAX_ARRAY_TEXTURE_LAYERS
    max_color_attachments: NotRequired[int]  # gl2.MAX_COLOR_ATTACHMENTS
    max_draw_buffers: NotRequired[int]  # gl2.MAX_DRAW_BUFFERS
    max_samples: NotRequired[int]  # gl2.MAX_SAMPLES
    max_uniform_block_size: NotRequired[int]  # gl2.MAX_UNIFORM_BLOCK_SIZE
    max_uniform_buffer_bindings: NotRequired[int]  # gl2.MAX_UNIFORM_BUFFER_BINDINGS
    max_vertex_uniform_blocks: NotRequired[int]  # gl2.MAX_VERTEX_UNIFORM_BLOCKS
    max_fragment_uniform_blocks: NotRequired[int]  # gl2.MAX_FRAGMENT_UNIFORM_BLOCKS
    max_combined_uniform_blocks: NotRequired[int]  # gl2.MAX_COMBINED_UNIFORM_BLOCKS
    max_combined_vertex_uniform_components: NotRequired[int]
    max_combined_fragment_uniform_components: NotRequired[int]
    uniform_buffer_offset_alignment: NotRequired[int]  # gl2.UNIFORM_BUFFER_OFFSET_ALIGNMENT
    max_texture_lod_bias: NotRequired[float]  # gl2.MAX_TEXTURE_LOD_BIAS
    max_transform_feedback_interleaved_components: NotRequired[int]
    max_vertex_output_components: NotRequired[int]  # gl2.MAX_VERTEX_OUTPUT_COMPONENTS
    max_fragment_input_components: NotRequired[int]  # gl2.MAX_FRAGMENT_INPUT_COMPONENTS
    max_element_index: NotRequired[int]  # gl2.MAX_ELEMENT_INDEX
    supported_extensions: NotRequired[list[str]]  # WebGL1 extension names
    webgl2_extensions: NotRequired[list[str]]  # WebGL2-specific extension names
    shader_precision_formats: NotRequired[
        dict[str, dict[str, list[int]]]
    ]  # e.g. {"vertex": {"highFloat": [127, 127, 23]}}


class WebGPUProfile(TypedDict):
    """WebGPU adapter fingerprint profile.

    Controls what ``navigator.gpu.requestAdapter()`` reports through
    ``adapter.info`` (``vendor``, ``architecture``, ``device``,
    ``description``), ``adapter.limits`` and ``adapter.features``. Detection
    scripts cross-check the WebGPU vendor against the WebGL renderer and the
    User-Agent OS, so a WebGL profile that names one GPU while WebGPU reports
    the host's is a contradiction; this section closes it.

    The real adapter is kept (device creation and rendering stay genuine) and
    only its reported values are replaced, on the real ``GPUAdapterInfo`` /
    ``GPUSupportedLimits`` / ``GPUSupportedFeatures`` prototypes. Every value
    must come from a capture of a real device of the claimed class: the limit
    set and the feature list are a physical signature of GPU, driver and
    backend, and a guessed one is easier to flag than the truth. Unset limits
    keep the real value; an unset ``features`` keeps the real set. On a host
    with no WebGPU adapter nothing can be reported, since there is no adapter
    to attach the values to.

    Example (Apple M-series on macOS, Chrome 152, captured)::

        WebGPUProfile(
            vendor='apple',
            architecture='metal-3',
            limits={'maxBufferSize': 4294967292, 'maxTextureDimension2D': 16384},
            features=['depth-clip-control', 'shader-f16', 'timestamp-query'],
        )
    """

    vendor: str  # adapter.info.vendor, e.g. 'nvidia', 'apple', 'intel', 'qualcomm'
    architecture: NotRequired[str]  # adapter.info.architecture, e.g. 'ampere', 'metal-3'
    device: NotRequired[str]  # adapter.info.device (Chrome reports '' by default)
    description: NotRequired[str]  # adapter.info.description (Chrome reports '' by default)
    is_fallback_adapter: NotRequired[bool]  # adapter.info.isFallbackAdapter (False on hardware)
    limits: NotRequired[dict[str, int]]  # adapter.limits, by limit name
    features: NotRequired[list[str]]  # adapter.features, the complete set


class ScreenFingerprint(TypedDict):
    """Screen and display fingerprint profile.

    Controls screen dimensions and display properties reported by the
    ``screen`` object and ``window.devicePixelRatio``. Must be consistent
    with the claimed device type — headless browsers often report unusual
    dimensions that anti-bot systems flag.

    ``avail_width`` and ``avail_height`` should be slightly less than
    ``width`` and ``height`` to account for the OS taskbar/dock. Setting
    them equal to width/height is a headless indicator.

    ``avail_top`` (and ``avail_left``) place that reserved area: on macOS
    ``avail_top`` is the menu-bar height (e.g. 25). When unset it defaults to
    the whole vertical gap ``height - avail_height`` (all at the top). In
    headless mode these also drive ``Emulation.updateScreen`` so cross-origin
    iframes read the same work area (``availTop == 0`` there is a headless tell).

    ``outer_width`` and ``outer_height`` represent the browser window
    dimensions including chrome (toolbar, scrollbar). In headless mode
    these are often 0, which is an instant detection signal.

    ``inner_width`` and ``inner_height`` override ``window.innerWidth``
    and ``window.innerHeight``. For mobile profiles these should be
    close to or equal to ``width``/``height``. If not set, the real
    browser viewport dimensions are used. In headless mode a desktop
    profile is applied without any metrics override (the virtual screen and
    the window are reshaped natively instead), so there ``inner_*`` follow
    from ``outer_*`` minus the window chrome; they are honoured for mobile
    profiles.

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
    avail_top: NotRequired[int]  # screen.availTop (top work-area inset, e.g. macOS menu bar)
    avail_left: NotRequired[int]  # screen.availLeft (left work-area inset)
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

    ``device_memory`` only accepts values from the set
    {0.25, 0.5, 1, 2, 4, 8, 16}: these are the only values the browser
    API returns (bucketed for fingerprinting resistance; current Chrome
    reports 16 on machines with 16 GB or more).

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
    A host with no devices (a server) reports 0 for every category.

    The fake entries are real ``InputDeviceInfo`` / ``MediaDeviceInfo``
    prototypes with no own properties. The native alternative, preferable
    when the host has no devices, is launching with
    ``--use-fake-device-for-media-stream``, which makes Chrome itself expose
    one fake microphone, camera and speaker.
    """

    audio_inputs: NotRequired[int]  # microphones
    audio_outputs: NotRequired[int]  # speakers/headphones
    video_inputs: NotRequired[int]  # cameras


class AudioFingerprint(TypedDict):
    """AudioContext fingerprint profile.

    Controls what a realtime ``AudioContext`` reports as its device
    ``sampleRate`` and destination ``maxChannelCount``. Anti-bot systems
    fingerprint audio by creating an ``OfflineAudioContext``, running an
    oscillator through a ``DynamicsCompressorNode``, and hashing the output
    samples; that rendered hash is not affected by these values.

    Only realtime contexts created without an explicit ``sampleRate`` are
    overridden. An ``OfflineAudioContext``, or an ``AudioContext`` constructed
    with ``{sampleRate}``, must report exactly the rate it was created with,
    so those keep their real value (reporting anything else is an impossible
    value a detector spots without any reference data).
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


class PlatformApisFingerprint(TypedDict):
    """Web APIs that exist on some operating systems and not on others.

    Chrome only exposes an API where the platform can back it, so the set of
    interfaces a browser has is itself a statement about the host: the Contact
    Picker and the Content Index ship on Android only, WebHID, Web Serial and
    ``SharedWorker`` on desktop only, the Web Share API everywhere but desktop
    Linux, Shape Detection (``BarcodeDetector``) only where the platform has a
    barcode backend (macOS, Android, ChromeOS), and ``downlinkMax`` only on
    Chrome for Android. A profile that claims one OS while the host exposes
    another's set contradicts itself, and CreepJS reads exactly this.

    ``hidden`` names what to remove, as a dotted path resolved from the global
    scope (``BarcodeDetector``, ``navigator.share``, ``NetworkInformation.downlinkMax``).
    Removing is all a profile can do honestly: an API the host does not
    implement cannot be conjured, so a profile that needs one the host lacks
    belongs on a different host.
    """

    hidden: list[str]  # dotted paths to delete, e.g. ['BarcodeDetector', 'navigator.share']


class FontFingerprint(TypedDict):
    """Font fingerprint profile.

    Controls which local fonts ``new FontFace(name, 'local(name)').load()``
    resolves for: the listed fonts resolve, cross-OS marker fonts not listed
    reject like absent fonts, everything else stays native. Font availability
    is highly OS-specific and a strong fingerprinting signal. The width-based
    probe (an element measured in the claimed family against a fallback) reads
    the layout engine and cannot be overridden: install the claimed fonts on
    the host and list exactly what is installed.
    """

    available_fonts: list[str]  # font families reported as available


class PermissionsFingerprint(TypedDict):
    """Permissions API fingerprint profile.

    Controls what ``navigator.permissions.query()`` returns for specific
    permission names. Maps permission name to state string. Applied natively
    through ``Browser.setPermission`` for the tab's browser context, so the
    query returns a genuine ``PermissionStatus`` and the matching legacy
    surfaces (``Notification.permission``) agree with it.

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


class MediaFeaturesFingerprint(TypedDict):
    """CSS media-feature fingerprint profile.

    Controls what ``window.matchMedia`` reports for display and preference
    media features, applied natively through ``Emulation.setEmulatedMedia`` so
    the query result stays genuine (no JavaScript wrapper). Detection suites
    hash these queries, so a headless browser reporting unusual values (or a
    profile whose display characteristics contradict the claimed device) is a
    signal.

    Only the features Chrome emulates through the DevTools Protocol are exposed
    here. ``dynamic-range`` and ``inverted-colors`` are NOT emulatable via CDP
    and are intentionally omitted.

    ``color_gamut`` is a display-hardware characteristic and the safest to set:
    Apple/OLED displays report ``'p3'``, a typical sRGB monitor reports
    ``'srgb'``. The ``prefers_*`` and ``forced_colors`` features are user
    preferences, and emulating them also changes how the page renders (dark
    mode, high contrast, reduced motion), so set them only when you want that
    behavior; leave them unset to keep the browser's real values.

    Example::

        MediaFeaturesFingerprint(color_gamut='p3')
    """

    color_gamut: NotRequired[str]  # 'srgb' | 'p3' | 'rec2020'
    forced_colors: NotRequired[str]  # 'none' | 'active'
    prefers_color_scheme: NotRequired[str]  # 'light' | 'dark'
    prefers_contrast: NotRequired[str]  # 'no-preference' | 'more' | 'less' | 'custom'
    prefers_reduced_motion: NotRequired[str]  # 'no-preference' | 'reduce'
    prefers_reduced_transparency: NotRequired[str]  # 'no-preference' | 'reduce'


class ClientHintsFingerprint(TypedDict):
    """High-entropy User-Agent Client Hints overrides.

    The User-Agent string no longer carries the real OS version (the reduction
    froze it at ``Mac OS X 10_15_7`` / ``Android 10; K``), while real Chrome
    keeps reporting the true one in ``Sec-CH-UA-Platform-Version`` and
    ``navigator.userAgentData.getHighEntropyValues()``. The parser fills a
    plausible default per OS; set these to pin the exact values read from the
    device you are impersonating (Windows 11 hosts report ``'13.0.0'`` and up,
    the exact value depending on the build; an Android phone reports its model
    such as ``'SM-S928B'``).

    Example::

        ClientHintsFingerprint(platform_version='15.0.0')
    """

    platform_version: NotRequired[str]  # Sec-CH-UA-Platform-Version
    architecture: NotRequired[str]  # 'x86' | 'arm'
    bitness: NotRequired[str]  # '64' | '32'
    wow64: NotRequired[bool]
    model: NotRequired[str]  # Sec-CH-UA-Model (mobile devices)
    form_factors: NotRequired[list[str]]  # Sec-CH-UA-Form-Factors, e.g. ['Desktop']


class FingerprintConfig(TypedDict):
    """Complete browser fingerprint configuration.

    Defines a consistent browser identity profile that can be injected
    into a Tab. All fields are optional — only specified fields will be
    overridden; unspecified fields retain the browser's real values.

    When ``user_agent`` is set, pydoll automatically synchronizes the
    User-Agent across all layers using the existing UserAgentParser:
    HTTP headers, ``navigator.userAgent``, ``navigator.platform``,
    ``navigator.vendor``, ``navigator.appVersion``, and ``Sec-CH-UA``
    Client Hints, with the greased brand and the brand order computed by
    Chromium's own per-major algorithm. ``client_hints`` pins the
    high-entropy values the UA string cannot carry.

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
    client_hints: NotRequired[ClientHintsFingerprint]
    navigator: NotRequired[NavigatorFingerprint]
    webgl: NotRequired[WebGLProfile]
    webgpu: NotRequired[WebGPUProfile]
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
    platform_apis: NotRequired[PlatformApisFingerprint]
    permissions: NotRequired[PermissionsFingerprint]
    media_features: NotRequired[MediaFeaturesFingerprint]
    webrtc_ip_policy: NotRequired[str]  # 'default' or 'relay'
