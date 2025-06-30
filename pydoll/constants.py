from enum import Enum, auto
from typing import cast


class By(str, Enum):
    CSS_SELECTOR = 'css'
    XPATH = 'xpath'
    CLASS_NAME = 'class_name'
    ID = 'id'
    TAG_NAME = 'tag_name'
    NAME = 'name'


class Scripts:
    ELEMENT_VISIBLE = """
    function() {
        const rect = this.getBoundingClientRect();
        return (
            rect.width > 0 && rect.height > 0
            && getComputedStyle(this).visibility !== 'hidden'
            && getComputedStyle(this).display !== 'none'
        )
    }
    """

    ELEMENT_ON_TOP = """
    function() {
        const rect = this.getBoundingClientRect();
        const elementFromPoint = document.elementFromPoint(
            rect.x + rect.width / 2,
            rect.y + rect.height / 2
        );
        return elementFromPoint === this;
    }
    """

    CLICK = """
    function(){
        clicked = false;
        this.addEventListener('click', function(){
            clicked = true;
        });
        this.click();
        return clicked;
    }
    """

    CLICK_OPTION_TAG = """
    document.querySelector('option[value="{self.value}"]').selected = true;
    var selectParentXpath = (
        '//option[@value="{self.value}"]//ancestor::select'
    );
    var select = document.evaluate(
        selectParentXpath,
        document,
        null,
        XPathResult.FIRST_ORDERED_NODE_TYPE,
        null
    ).singleNodeValue;
    var event = new Event('change', { bubbles: true });
    select.dispatchEvent(event);
    """

    BOUNDS = """
    function() {
        return JSON.stringify(this.getBoundingClientRect());
    }
    """

    FIND_RELATIVE_XPATH_ELEMENT = """
        function() {
            return document.evaluate(
                "{escaped_value}", this, null,
                XPathResult.FIRST_ORDERED_NODE_TYPE, null
            ).singleNodeValue;
        }
    """

    FIND_XPATH_ELEMENT = """
        var element = document.evaluate(
            "{escaped_value}", document, null,
            XPathResult.FIRST_ORDERED_NODE_TYPE, null
        ).singleNodeValue;
        element;
    """

    FIND_RELATIVE_XPATH_ELEMENTS = """
        function() {
            var elements = document.evaluate(
                "{escaped_value}", this, null,
                XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null
            );
            var results = [];
            for (var i = 0; i < elements.snapshotLength; i++) {
                results.push(elements.snapshotItem(i));
            }
            return results;
        }
    """

    FIND_XPATH_ELEMENTS = """
        var elements = document.evaluate(
            "{escaped_value}", document, null,
            XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null
        );
        var results = [];
        for (var i = 0; i < elements.snapshotLength; i++) {
            results.push(elements.snapshotItem(i));
        }
        results;
    """

    QUERY_SELECTOR = 'document.querySelector("{selector}");'

    RELATIVE_QUERY_SELECTOR = """
        function() {
            return this.querySelector("{selector}");
        }
    """

    QUERY_SELECTOR_ALL = 'document.querySelectorAll("{selector}");'

    RELATIVE_QUERY_SELECTOR_ALL = """
        function() {
            return this.querySelectorAll("{selector}");
        }
    """

    # Fingerprint spoofing related scripts
    FINGERPRINT_WRAPPER = """
(function() {{
    'use strict';

    // Disable webdriver detection
    Object.defineProperty(navigator, 'webdriver', {{
        get: () => false,
        configurable: true
    }});

    // Remove automation indicators
    delete window.navigator.webdriver;
    delete window.__webdriver_script_fn;
    delete window.__webdriver_script_func;
    delete window.__webdriver_script_function;
    delete window.__fxdriver_evaluate;
    delete window.__fxdriver_unwrapped;
    delete window._Selenium_IDE_Recorder;
    delete window._selenium;
    delete window.calledSelenium;
    delete window.calledPhantom;
    delete window.__nightmare;
    delete window._phantom;
    delete window.phantom;
    delete window.callPhantom;

    {scripts}

    // Override toString to hide modifications
    const originalToString = Function.prototype.toString;
    Function.prototype.toString = function() {{
        const originalSource = originalToString.call(this);
        // Only hide fingerprint-related getter functions that return specific values
        if (this.name === 'get' && 
            originalSource.includes('return') && 
            (originalSource.includes('false') || 
             originalSource.includes("'{") || 
             originalSource.includes('{{')) {{
            return 'function get() {{ [native code] }}';
        }}
        return originalSource;
    }};
}})();
"""

    NAVIGATOR_OVERRIDE = """
    // Override navigator properties
    Object.defineProperty(navigator, 'userAgent', {{
        get: () => '{user_agent}',
        configurable: true
    }});

    Object.defineProperty(navigator, 'platform', {{
        get: () => '{platform}',
        configurable: true
    }});

    Object.defineProperty(navigator, 'language', {{
        get: () => '{language}',
        configurable: true
    }});

    Object.defineProperty(navigator, 'languages', {{
        get: () => {languages},
        configurable: true
    }});

    Object.defineProperty(navigator, 'hardwareConcurrency', {{
        get: () => {hardware_concurrency},
        configurable: true
    }});

    {device_memory_script}

    Object.defineProperty(navigator, 'cookieEnabled', {{
        get: () => {cookie_enabled},
        configurable: true
    }});

    {do_not_track_script}
    """

    SCREEN_OVERRIDE = """
    // Override screen properties
    Object.defineProperty(screen, 'width', {{
        get: () => {screen_width},
        configurable: true
    }});

    Object.defineProperty(screen, 'height', {{
        get: () => {screen_height},
        configurable: true
    }});

    Object.defineProperty(screen, 'colorDepth', {{
        get: () => {screen_color_depth},
        configurable: true
    }});

    Object.defineProperty(screen, 'pixelDepth', {{
        get: () => {screen_pixel_depth},
        configurable: true
    }});

    Object.defineProperty(screen, 'availWidth', {{
        get: () => {available_width},
        configurable: true
    }});

    Object.defineProperty(screen, 'availHeight', {{
        get: () => {available_height},
        configurable: true
    }});

    // Override window dimensions
    Object.defineProperty(window, 'innerWidth', {{
        get: () => {inner_width},
        configurable: true
    }});

    Object.defineProperty(window, 'innerHeight', {{
        get: () => {inner_height},
        configurable: true
    }});

    Object.defineProperty(window, 'outerWidth', {{
        get: () => {viewport_width},
        configurable: true
    }});

    Object.defineProperty(window, 'outerHeight', {{
        get: () => {viewport_height},
        configurable: true
    }});
    """

    WEBGL_OVERRIDE = """
    // Override WebGL properties
    const getParameter = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(parameter) {{
        if (parameter === 37445) {{ // VENDOR
            return '{webgl_vendor}';
        }}
        if (parameter === 37446) {{ // RENDERER
            return '{webgl_renderer}';
        }}
        if (parameter === 7938) {{ // VERSION
            return '{webgl_version}';
        }}
        if (parameter === 35724) {{ // SHADING_LANGUAGE_VERSION
            return '{webgl_shading_language_version}';
        }}
        return getParameter.call(this, parameter);
    }};

    const getSupportedExtensions = WebGLRenderingContext.prototype.getSupportedExtensions;
    WebGLRenderingContext.prototype.getSupportedExtensions = function() {{
        return {webgl_extensions};
    }};

    // Also override WebGL2 if available
    if (window.WebGL2RenderingContext) {{
        const getParameter2 = WebGL2RenderingContext.prototype.getParameter;
        WebGL2RenderingContext.prototype.getParameter = function(parameter) {{
            if (parameter === 37445) return '{webgl_vendor}';
            if (parameter === 37446) return '{webgl_renderer}';
            if (parameter === 7938) return '{webgl_version}';
            if (parameter === 35724) return '{webgl_shading_language_version}';
            return getParameter2.call(this, parameter);
        }};

        const getSupportedExtensions2 = WebGL2RenderingContext.prototype.getSupportedExtensions;
        WebGL2RenderingContext.prototype.getSupportedExtensions = function() {{
            return {webgl_extensions};
        }};
    }}
    """

    CANVAS_OVERRIDE = """
    // Override canvas fingerprinting
    const originalGetContext = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function(contextType) {{
        const context = originalGetContext.call(this, contextType);

        if (contextType === '2d') {{
            const originalToDataURL = this.toDataURL;
            this.toDataURL = function() {{
                // Generate dynamic base64 with subtle variations
                const baseFP = '{canvas_fingerprint}';
                const timeSeed = Date.now() % 10000;
                const urlSeed = window.location ? window.location.href.length % 100 : 0;
                const variation = (timeSeed + urlSeed).toString(36).slice(-4);
                
                // Replace some characters in the base fingerprint to create variation
                let variedFP = baseFP;
                if (baseFP.length > 10) {{
                    const replacePos = (timeSeed % (baseFP.length - 8)) + 4;
                    variedFP = baseFP.substring(0, replacePos) + variation + baseFP.substring(replacePos + 4);
                }}
                
                return 'data:image/png;base64,' + variedFP;
            }};

            const originalGetImageData = context.getImageData;
            context.getImageData = function() {{
                const imageData = originalGetImageData.apply(this, arguments);
                
                // Create a more robust seed based on context
                const seed = (Date.now() + 
                             (window.location ? window.location.href.length : 0) + 
                             imageData.data.length + 
                             (navigator.userAgent ? navigator.userAgent.length : 0)) % 1000000;
                
                // Simple seeded random function
                let seedState = seed;
                const seededRandom = () => {{
                    seedState = (seedState * 9301 + 49297) % 233280;
                    return seedState / 233280;
                }};
                
                // Add context-aware noise to RGB channels
                for (let i = 0; i < imageData.data.length; i += 4) {{
                    // Use seeded random with position-based variation
                    const positionSeed = (i / 4) * 0.001;
                    const noiseIntensity = 3 + (seededRandom() + positionSeed) % 2; // 3-5 range
                    
                    // Add small random variations to RGB channels
                    imageData.data[i] = Math.min(255, Math.max(0, imageData.data[i] + (seededRandom() - 0.5) * noiseIntensity));     // Red
                    imageData.data[i + 1] = Math.min(255, Math.max(0, imageData.data[i + 1] + (seededRandom() - 0.5) * noiseIntensity)); // Green
                    imageData.data[i + 2] = Math.min(255, Math.max(0, imageData.data[i + 2] + (seededRandom() - 0.5) * noiseIntensity)); // Blue
                    // Keep alpha channel unchanged to preserve transparency
                }}
                return imageData;
            }};
        }}

        return context;
    }};
    """

    AUDIO_OVERRIDE = """
    // Override AudioContext properties
    if (window.AudioContext || window.webkitAudioContext) {{
        const OriginalAudioContext = window.AudioContext || window.webkitAudioContext;

        function FakeAudioContext() {{
            const context = new OriginalAudioContext();

            Object.defineProperty(context, 'sampleRate', {{
                get: () => {audio_context_sample_rate},
                configurable: true
            }});

            Object.defineProperty(context, 'state', {{
                get: () => '{audio_context_state}',
                configurable: true
            }});

            Object.defineProperty(context.destination, 'maxChannelCount', {{
                get: () => {audio_context_max_channel_count},
                configurable: true
            }});

            return context;
        }}

        FakeAudioContext.prototype = OriginalAudioContext.prototype;
        window.AudioContext = FakeAudioContext;
        if (window.webkitAudioContext) {{
            window.webkitAudioContext = FakeAudioContext;
        }}
    }}
    """

    PLUGIN_OVERRIDE = """
    // Override plugin information
    Object.defineProperty(navigator, 'plugins', {{
        get: () => {{
            const plugins = {{}};
            plugins.length = {plugins_length};
            {plugins_js}
            return plugins;
        }},
        configurable: true
    }});
    """

    MISC_OVERRIDES = """
    // Override timezone
    const originalDateGetTimezoneOffset = Date.prototype.getTimezoneOffset;
    Date.prototype.getTimezoneOffset = function() {{
        return {timezone_offset};
    }};

    // Override Intl.DateTimeFormat
    if (window.Intl && window.Intl.DateTimeFormat) {{
        const originalResolvedOptions = Intl.DateTimeFormat.prototype.resolvedOptions;
        Intl.DateTimeFormat.prototype.resolvedOptions = function() {{
            const options = originalResolvedOptions.call(this);
            options.timeZone = '{timezone}';
            return options;
        }};
    }}

    // Override connection type
    if (navigator.connection || navigator.mozConnection || navigator.webkitConnection) {{
        const connection = navigator.connection ||
                          navigator.mozConnection ||
                          navigator.webkitConnection;
        Object.defineProperty(connection, 'effectiveType', {{
            get: () => '{connection_type}',
            configurable: true
        }});
    }}

    // Hide automation indicators in Chrome
    Object.defineProperty(window, 'chrome', {{
        get: () => {{
            return {{
                runtime: {{
                    onConnect: undefined,
                    onMessage: undefined
                }}
            }};
        }},
        configurable: true
    }});

    // Override permissions
    if (navigator.permissions && navigator.permissions.query) {{
        const originalQuery = navigator.permissions.query;
        navigator.permissions.query = function(parameters) {{
            return originalQuery(parameters).then(result => {{
                if (parameters.name === 'notifications') {{
                    Object.defineProperty(result, 'state', {{
                        get: () => 'denied',
                        configurable: true
                    }});
                }}
                return result;
            }});
        }};
    }}
    """


class Key(tuple[str, int], Enum):
    BACKSPACE = ('Backspace', 8)
    TAB = ('Tab', 9)
    ENTER = ('Enter', 13)
    SHIFT = ('Shift', 16)
    CONTROL = ('Control', 17)
    ALT = ('Alt', 18)
    PAUSE = ('Pause', 19)
    CAPSLOCK = ('CapsLock', 20)
    ESCAPE = ('Escape', 27)
    SPACE = ('Space', 32)
    PAGEUP = ('PageUp', 33)
    PAGEDOWN = ('PageDown', 34)
    END = ('End', 35)
    HOME = ('Home', 36)
    ARROWLEFT = ('ArrowLeft', 37)
    ARROWUP = ('ArrowUp', 38)
    ARROWRIGHT = ('ArrowRight', 39)
    ARROWDOWN = ('ArrowDown', 40)
    PRINTSCREEN = ('PrintScreen', 44)
    INSERT = ('Insert', 45)
    DELETE = ('Delete', 46)
    META = ('Meta', 91)
    METARIGHT = ('MetaRight', 92)
    CONTEXTMENU = ('ContextMenu', 93)
    NUMLOCK = ('NumLock', 144)
    SCROLLLOCK = ('ScrollLock', 145)

    F1 = ('F1', 112)
    F2 = ('F2', 113)
    F3 = ('F3', 114)
    F4 = ('F4', 115)
    F5 = ('F5', 116)
    F6 = ('F6', 117)
    F7 = ('F7', 118)
    F8 = ('F8', 119)
    F9 = ('F9', 120)
    F10 = ('F10', 121)
    F11 = ('F11', 122)
    F12 = ('F12', 123)

    SEMICOLON = ('Semicolon', 186)
    EQUALSIGN = ('EqualSign', 187)
    COMMA = ('Comma', 188)
    MINUS = ('Minus', 189)
    PERIOD = ('Period', 190)
    SLASH = ('Slash', 191)
    GRAVEACCENT = ('GraveAccent', 192)
    BRACKETLEFT = ('BracketLeft', 219)
    BACKSLASH = ('Backslash', 220)
    BRACKETRIGHT = ('BracketRight', 221)
    QUOTE = ('Quote', 222)


class BrowserType(Enum):
    CHROME = auto()
    EDGE = auto()


class WindowState(str, Enum):
    """Possible states for a browser window."""

    MAXIMIZED = 'maximized'
    MINIMIZED = 'minimized'
    NORMAL = 'normal'


class DownloadBehavior(str, Enum):
    """Possible behaviors for download handling."""

    ALLOW = 'allow'
    DENY = 'deny'
    ALLOW_AND_NAME = 'allowAndName'
    DEFAULT = 'default'


class PermissionType(str, Enum):
    """Browser permission types as defined in the Chrome DevTools Protocol."""

    AR = 'ar'
    AUDIO_CAPTURE = 'audioCapture'
    AUTOMATIC_FULLSCREEN = 'automaticFullscreen'
    BACKGROUND_FETCH = 'backgroundFetch'
    BACKGROUND_SYNC = 'backgroundSync'
    CAMERA_PAN_TILT_ZOOM = 'cameraPanTiltZoom'
    CAPTURED_SURFACE_CONTROL = 'capturedSurfaceControl'
    CLIPBOARD_READ_WRITE = 'clipboardReadWrite'
    CLIPBOARD_SANITIZED_WRITE = 'clipboardSanitizedWrite'
    DISPLAY_CAPTURE = 'displayCapture'
    DURABLE_STORAGE = 'durableStorage'
    GEOLOCATION = 'geolocation'
    HAND_TRACKING = 'handTracking'
    IDLE_DETECTION = 'idleDetection'
    KEYBOARD_LOCK = 'keyboardLock'
    LOCAL_FONTS = 'localFonts'
    LOCAL_NETWORK_ACCESS = 'localNetworkAccess'
    MIDI = 'midi'
    MIDI_SYSEX = 'midiSysex'
    NFC = 'nfc'
    NOTIFICATIONS = 'notifications'
    PAYMENT_HANDLER = 'paymentHandler'
    PERIODIC_BACKGROUND_SYNC = 'periodicBackgroundSync'
    POINTER_LOCK = 'pointerLock'
    PROTECTED_MEDIA_IDENTIFIER = 'protectedMediaIdentifier'
    SENSORS = 'sensors'
    SMART_CARD = 'smartCard'
    SPEAKER_SELECTION = 'speakerSelection'
    STORAGE_ACCESS = 'storageAccess'
    TOP_LEVEL_STORAGE_ACCESS = 'topLevelStorageAccess'
    VIDEO_CAPTURE = 'videoCapture'
    VR = 'vr'
    WAKE_LOCK_SCREEN = 'wakeLockScreen'
    WAKE_LOCK_SYSTEM = 'wakeLockSystem'
    WEB_APP_INSTALLATION = 'webAppInstallation'
    WEB_PRINTING = 'webPrinting'
    WINDOW_MANAGEMENT = 'windowManagement'


class RequestMethod(str, Enum):
    """HTTP request methods."""

    GET = 'GET'
    POST = 'POST'
    OPTIONS = 'OPTIONS'
    PUT = 'PUT'
    DELETE = 'DELETE'


class AuthChallengeResponseValues(str, Enum):
    DEFAULT = 'Default'
    CANCEL_AUTH = 'CancelAuth'
    PROVIDE_CREDENTIALS = 'ProvideCredentials'


class ResourceType(str, Enum):
    DOCUMENT = 'Document'
    STYLESHEET = 'Stylesheet'
    IMAGE = 'Image'
    MEDIA = 'Media'
    FONT = 'Font'
    SCRIPT = 'Script'
    TEXT_TRACK = 'TextTrack'
    XHR = 'XHR'
    FETCH = 'Fetch'
    PREFETCH = 'Prefetch'
    EVENT_SOURCE = 'EventSource'
    WEBSOCKET = 'WebSocket'
    MANIFEST = 'Manifest'
    SIGNED_EXCHANGE = 'SignedExchange'
    PING = 'Ping'
    CSP_VIOLATION_REPORT = 'CSPViolationReport'
    PREFLIGHT = 'Preflight'
    OTHER = 'OTHER'


class RequestStage(str, Enum):
    REQUEST = 'Request'
    RESPONSE = 'Response'


class NetworkErrorReason(str, Enum):
    """Network level fetch failure reason."""

    FAILED = 'Failed'
    ABORTED = 'Aborted'
    TIMED_OUT = 'TimedOut'
    ACCESS_DENIED = 'AccessDenied'
    CONNECTION_CLOSED = 'ConnectionClosed'
    CONNECTION_RESET = 'ConnectionReset'
    CONNECTION_REFUSED = 'ConnectionRefused'
    CONNECTION_ABORTED = 'ConnectionAborted'
    CONNECTION_FAILED = 'ConnectionFailed'
    NAME_NOT_RESOLVED = 'NameNotResolved'
    INTERNET_DISCONNECTED = 'InternetDisconnected'
    ADDRESS_UNREACHABLE = 'AddressUnreachable'
    BLOCKED_BY_CLIENT = 'BlockedByClient'
    BLOCKED_BY_RESPONSE = 'BlockedByResponse'


class CookiePriority(str, Enum):
    """Cookie priority levels."""

    LOW = 'Low'
    MEDIUM = 'Medium'
    HIGH = 'High'


class CookieSourceScheme(str, Enum):
    """Cookie source schemes."""

    UNSET = 'Unset'
    NON_SECURE = 'NonSecure'
    SECURE = 'Secure'


class CookieSameSite(str, Enum):
    """Cookie same site values."""

    STRICT = 'Strict'
    LAX = 'Lax'
    NONE = 'None'


class ConnectionType(str, Enum):
    """Network connection types."""

    NONE = 'none'
    CELLULAR2G = 'cellular2g'
    CELLULAR3G = 'cellular3g'
    CELLULAR4G = 'cellular4g'
    WIFI = 'wifi'
    ETHERNET = 'ethernet'
    BLUETOOTH = 'bluetooth'
    WIMAX = 'wimax'
    OTHER = 'other'


class ContentEncoding(str, Enum):
    """Content encoding types."""

    GZIP = 'gzip'
    DEFLATE = 'deflate'
    BR = 'br'
    ZSTD = 'zstd'


class ScreenshotFormat(str, Enum):
    """Screenshot formats."""

    JPEG = 'jpeg'
    PNG = 'png'
    WEBP = 'webp'

    @classmethod
    def has_value(cls, value: str) -> bool:
        return value in cls._value2member_map_

    @classmethod
    def get_value(cls, value: str) -> 'ScreenshotFormat':
        return cast(ScreenshotFormat, cls._value2member_map_[value])


class TransitionType(str, Enum):
    """Transition types."""

    LINK = 'link'
    TYPED = 'typed'
    ADDRESS_BAR = 'address_bar'
    AUTO_BOOKMARK = 'auto_bookmark'
    AUTO_SUBFRAME = 'auto_subframe'
    MANUAL_SUBFRAME = 'manual_subframe'
    GENERATED = 'generated'
    AUTO_TOPLEVEL = 'auto_toplevel'
    FORM_SUBMIT = 'form_submit'
    RELOAD = 'reload'
    KEYWORD = 'keyword'
    KEYWORD_GENERATED = 'keyword_generated'
    OTHER = 'other'


class ReferrerPolicy(str, Enum):
    """Referrer policies."""

    NO_REFERRER = 'noReferrer'
    NO_REFERRER_WHEN_DOWNGRADE = 'noReferrerWhenDowngrade'
    ORIGIN = 'origin'
    ORIGIN_WHEN_CROSS_ORIGIN = 'originWhenCrossOrigin'
    SAME_ORIGIN = 'sameOrigin'
    STRICT_ORIGIN = 'strictOrigin'
    STRICT_ORIGIN_WHEN_CROSS_ORIGIN = 'strictOriginWhenCrossOrigin'
    UNSAFE_URL = 'unsafeUrl'


class TransferMode(str, Enum):
    """Transfer modes."""

    RETURN_AS_STREAM = 'returnAsStream'
    RETURN_AS_BASE64 = 'returnAsBase64'


class AutoResponseMode(str, Enum):
    NONE = 'none'
    AUTO_ACCEPT = 'autoAccept'
    AUTO_REJECT = 'autoReject'
    AUTO_OPTOUT = 'autoOptout'


class WebLifecycleState(str, Enum):
    """Web lifecycle states."""

    FROZEN = 'frozen'
    ACTIVE = 'active'


class ScreencastFormat(str, Enum):
    """Screencast formats."""

    JPEG = 'jpeg'
    PNG = 'png'


class OriginTrialStatus(str, Enum):
    ENABLED = 'Enabled'
    VALID_TOKEN_NOT_PROVIDED = 'ValidTokenNotProvided'
    OS_NOT_SUPPORTED = 'OsNotSupported'
    TRIAL_NOT_ALLOWED = 'TrialNotAllowed'


class OriginTrialUsageRestriction(str, Enum):
    NONE = 'None'
    SUBSET = 'Subset'


class OriginTrialTokenStatus(str, Enum):
    SUCCESS = 'Success'
    NOT_SUPPORTED = 'NotSupported'
    INSECURE = 'Insecure'
    EXPIRED = 'Expired'
    WRONG_ORIGIN = 'WrongOrigin'
    INVALID_SIGNATURE = 'InvalidSignature'
    MALFORMED = 'Malformed'
    WRONG_VERSION = 'WrongVersion'
    FEATURE_DISABLED = 'FeatureDisabled'
    TOKEN_DISABLED = 'TokenDisabled'
    FEATURE_DISABLED_FOR_USER = 'FeatureDisabledForUser'
    UNKNOWN_TRIAL = 'UnknownTrial'


class PermissionsPolicyBlockReason(str, Enum):
    HEADER = 'Header'
    IFRAME_ATTRIBUTE = 'IframeAttribute'
    IN_FANCED_FRAME_TREE = 'InFancedFrameTree'
    IN_ISOLATED_APP = 'InIsolatedApp'


class PermissionsPolicyFeature(str, Enum):
    ACCELEROMETER = 'accelerometer'
    ALL_SCREENS_CAPTURE = 'all-screens-capture'
    AMBIENT_LIGHT_SENSOR = 'ambient-light-sensor'
    ATTRIBUTION_REPORTING = 'attribution-reporting'
    AUTOPLAY = 'autoplay'
    BLUETOOTH = 'bluetooth'
    BROWSING_TOPICS = 'browsing-topics'
    CAMERA = 'camera'
    CAPTURED_SURFACE_CONTROL = 'captured-surface-control'
    CH_DPR = 'ch-dpr'
    CH_DEVICE_MEMORY = 'ch-device-memory'
    CH_DOWNLINK = 'ch-downlink'
    CH_ECT = 'ch-ect'
    CH_PREFERS_COLOR_SCHEME = 'ch-prefers-color-scheme'
    CH_PREFERS_REDUCED_MOTION = 'ch-prefers-reduced-motion'
    CH_PREFERS_REDUCED_TRANSPARENCY = 'ch-prefers-reduced-transparency'
    CH_RTT = 'ch-rtt'
    CH_SAVE_DATA = 'ch-save-data'
    CH_UA = 'ch-ua'
    CH_UA_ARCH = 'ch-ua-arch'
    CH_UA_BITNESS = 'ch-ua-bitness'
    CH_UA_HIGH_ENTROPY_VALUES = 'ch-ua-high-entropy-values'
    CH_UA_PLATFORM = 'ch-ua-platform'
    CH_UA_MODEL = 'ch-ua-model'
    CH_UA_MOBILE = 'ch-ua-mobile'
    CH_UA_FORM_FACTORS = 'ch-ua-form-factors'
    CH_UA_FULL_VERSION = 'ch-ua-full-version'
    CH_UA_FULL_VERSION_LIST = 'ch-ua-full-version-list'
    CH_UA_PLATFORM_VERSION = 'ch-ua-platform-version'
    CH_UA_WOW64 = 'ch-ua-wow64'
    CH_VIEWPORT_HEIGHT = 'ch-viewport-height'
    CH_VIEWPORT_WIDTH = 'ch-viewport-width'
    CH_WIDTH = 'ch-width'
    CLIPBOARD_READ = 'clipboard-read'
    CLIPBOARD_WRITE = 'clipboard-write'
    COMPUTE_PRESSURE = 'compute-pressure'
    CONTROLLED_FRAME = 'controlled-frame'
    CROSS_ORIGIN_ISOLATED = 'cross-origin-isolated'
    DEFERRED_FETCH = 'deferred-fetch'
    DEFERRED_FETCH_MINIMAL = 'deferred-fetch-minimal'
    DEVICE_ATTRIBUTES = 'device-attributes'
    DIGITAL_CREDENTIALS_GET = 'digital-credentials-get'
    DIRECT_SOCKETS = 'direct-sockets'
    DIRECT_SOCKETS_PRIVATE = 'direct-sockets-private'
    DISPLAY_CAPTURE = 'display-capture'
    DOCUMENT_DOMAIN = 'document-domain'
    ENCRYPTED_MEDIA = 'encrypted-media'
    EXECUTION_WHILE_OUT_OF_VIEWPORT = 'execution-while-out-of-viewport'
    EXECUTION_WHILE_NOT_RENDERED = 'execution-while-not-rendered'
    FENCED_UNPARTITIONED_STORAGE_READ = 'fenced-unpartitioned-storage-read'
    FOCUS_WITHOUT_USER_ACTIVATION = 'focus-without-user-activation'
    FULLSCREEN = 'fullscreen'
    FROBULATE = 'frobulate'
    GAMEPAD = 'gamepad'
    GEOLOCATION = 'geolocation'
    GYROSCOPE = 'gyroscope'
    HID = 'hid'
    IDENTITY_CREDENTIALS_GET = 'identity-credentials-get'
    IDLE_DETECTION = 'idle-detection'
    INTEREST_COHORT = 'interest-cohort'
    JOIN_AD_INTEREST_GROUP = 'join-ad-interest-group'
    KEYBOARD_MAP = 'keyboard-map'
    LANGUAGE_DETECTOR = 'language-detector'
    LOCAL_FONTS = 'local-fonts'
    MAGNETOMETER = 'magnetometer'
    MEDIA_PLAYBACK_WHILE_NOT_VISIBLE = 'media-playback-while-not-visible'
    MICROPHONE = 'microphone'
    MIDI = 'midi'
    OTP_CREDENTIALS = 'otp-credentials'
    PAYMENT = 'payment'
    PICTURE_IN_PICTURE = 'picture-in-picture'
    POPINS = 'popins'
    PRIVATE_AGGREGATION = 'private-aggregation'
    PRIVATE_STATE_TOKEN_ISSUANCE = 'private-state-token-issuance'
    PRIVATE_STATE_TOKEN_REDEMPTION = 'private-state-token-redemption'
    PUBLICKEY_CREDENTIALS_CREATE = 'publickey-credentials-create'
    PUBLICKEY_CREDENTIALS_GET = 'publickey-credentials-get'
    REWRITER = 'rewriter'
    RUN_AD_AUCTION = 'run-ad-auction'
    SCREEN_WAKE_LOCK = 'screen-wake-lock'
    SERIAL = 'serial'
    SHARED_AUTOFILL = 'shared-autofill'
    SHARED_STORAGE = 'shared-storage'
    SHARED_STORAGE_SELECT_URL = 'shared-storage-select-url'
    SMART_CARD = 'smart-card'
    SPEAKER_SELECTION = 'speaker-selection'
    STORAGE_ACCESS = 'storage-access'
    SUB_APPS = 'sub-apps'
    SUMMARIZER = 'summarizer'
    SYNC_XHR = 'sync-xhr'
    TRANSLATOR = 'translator'
    UNLOAD = 'unload'
    USB = 'usb'
    USB_UNRESTRICTED = 'usb-unresStricted'
    VERTICAL_SCROLL = 'vertical-scroll'
    WEB_APP_INSTALLATION = 'web-app-installation'
    WEB_PRINTING = 'web-printing'
    WEB_SHARE = 'web-share'
    WINDOW_MANAGEMENT = 'window-management'
    WRITER = 'writer'
    XR_SPATIAL_TRACKING = 'xr-spatial-tracking'


class CrossOriginOpenerPolicyStatus(str, Enum):
    SAME_ORIGIN = 'SameOrigin'
    SAME_ORIGIN_ALLOW_POPUPS = 'SameOriginAllowPopups'
    RESTRICT_PROPERTIES = 'RestrictProperties'
    UNSAFE_NONE = 'UnsafeNone'
    SAME_ORIGIN_PLUS_COEP = 'SameOriginPlusCoep'
    RESTRICT_PROPERTIES_PLUS_COEP = 'RestrictPropertiesPlusCoep'
    NO_OPENER_ALLOW_POPUPS = 'NoopenerAllowPopups'


class CrossOriginEmbedderPolicyStatus(str, Enum):
    """Cross-origin embedder policy status values."""

    NONE = 'None'
    CREDENTIALLESS = 'Credentialless'
    REQUIRE_CORP = 'RequireCorp'


class ContentSecurityPolicySource(str, Enum):
    HTTP = 'HTTP'
    META = 'Meta'


class UnserializableEnum(str, Enum):
    NEGATIVE_ZERO = '-0'
    NAN = 'NaN'
    INFINITY = 'Infinity'
    NEGATIVE_INFINITY = '-Infinity'


class SerializationValue(str, Enum):
    DEEP = 'deep'
    JSON = 'json'
    ID_ONLY = 'idOnly'


class RemoteObjectType(str, Enum):
    OBJECT = 'object'
    FUNCTION = 'function'
    UNDEFINED = 'undefined'
    STRING = 'string'
    NUMBER = 'number'
    BOOLEAN = 'boolean'
    SYMBOL = 'symbol'
    BIGINT = 'bigint'


class RemoteObjectSubtype(str, Enum):
    ARRAY = 'array'
    NULL = 'null'
    NODE = 'node'
    REGEXP = 'regexp'
    DATE = 'date'
    MAP = 'map'
    SET = 'set'
    WEAK_MAP = 'weakmap'
    WEAK_SET = 'weakset'
    ITERATOR = 'iterator'
    GENERATOR = 'generator'
    ERROR = 'error'
    PROXY = 'proxy'
    PROMISE = 'promise'
    TYPED_ARRAY = 'typedarray'
    ARRAY_BUFFER = 'arraybuffer'
    DATA_VIEW = 'dataview'
    WEB_ASSEMBLY_MEMORY = 'webassemblymemory'
    WASM_VALUE = 'wasmvalue'


class DeepSerializedValueType(str, Enum):
    UNDEFINED = 'undefined'
    NULL = 'null'
    STRING = 'string'
    NUMBER = 'number'
    BOOLEAN = 'boolean'
    BIGINT = 'bigint'
    REGEXP = 'regexp'
    DATE = 'date'
    SYMBOL = 'symbol'
    ARRAY = 'array'
    OBJECT = 'object'
    FUNCTION = 'function'
    MAP = 'map'
    SET = 'set'
    WEAK_MAP = 'weakmap'
    WEAK_SET = 'weakset'
    ERROR = 'error'
    PROXY = 'proxy'
    PROMISE = 'promise'
    TYPED_ARRAY = 'typedarray'
    ARRAY_BUFFER = 'arraybuffer'
    NODE = 'node'
    WINDOW = 'window'
    GENERATOR = 'generator'


class ObjectPreviewType(str, Enum):
    OBJECT = 'object'
    FUNCTION = 'function'
    UNDEFINED = 'undefined'
    STRING = 'string'
    NUMBER = 'number'
    BOOLEAN = 'boolean'
    SYMBOL = 'symbol'
    BIGINT = 'bigint'


class ObjectPreviewSubtype(str, Enum):
    ARRAY = 'array'
    NULL = 'null'
    NODE = 'node'
    REGEXP = 'regexp'
    DATE = 'date'
    MAP = 'map'
    SET = 'set'
    WEAKMAP = 'weakmap'
    WEAKSET = 'weakset'
    ITERATOR = 'iterator'
    GENERATOR = 'generator'
    ERROR = 'error'
    PROXY = 'proxy'
    PROMISE = 'promise'
    TYPEDARRAY = 'typedarray'
    ARRAYBUFFER = 'arraybuffer'
    DATAVIEW = 'dataview'
    WEB_ASSEMBLY_MEMORY = 'webassemblymemory'
    WASM_VALUE = 'wasmvalue'


class PropertyPreviewType(str, Enum):
    OBJECT = 'object'
    FUNCTION = 'function'
    UNDEFINED = 'undefined'
    STRING = 'string'
    NUMBER = 'number'
    BOOLEAN = 'boolean'
    SYMBOL = 'symbol'
    ACCESSOR = 'accessor'
    BIGINT = 'bigint'


class PropertyPreviewSubtype(str, Enum):
    ARRAY = 'array'
    NULL = 'null'
    NODE = 'node'
    REGEXP = 'regexp'
    DATE = 'date'
    MAP = 'map'
    SET = 'set'
    WEAKMAP = 'weakmap'
    WEAKSET = 'weakset'
    ITERATOR = 'iterator'
    GENERATOR = 'generator'
    ERROR = 'error'
    PROXY = 'proxy'
    PROMISE = 'promise'
    TYPEDARRAY = 'typedarray'
    ARRAYBUFFER = 'arraybuffer'
    DATAVIEW = 'dataview'
    WEB_ASSEMBLY_MEMORY = 'webassemblymemory'
    WASM_VALUE = 'wasmvalue'


class StorageBucketDurability(str, Enum):
    RELAXED = 'relaxed'
    STRICT = 'strict'


class StorageType(str, Enum):
    COOKIES = 'cookies'
    FILE_SYSTEMS = 'file_systems'
    INDEXEDDB = 'indexeddb'
    LOCAL_STORAGE = 'local_storage'
    SHADER_CACHE = 'shader_cache'
    WEBSQL = 'websql'
    SERVICE_WORKERS = 'service_workers'
    CACHE_STORAGE = 'cache_storage'
    INTEREST_GROUPS = 'interest_groups'
    SHARED_STORAGE = 'shared_storage'
    STORAGE_BUCKETS = 'storage_buckets'
    ALL = 'all'
    OTHER = 'other'


class KeyEventType(str, Enum):
    KEY_DOWN = 'keyDown'
    KEY_UP = 'keyUp'
    CHAR = 'char'
    RAW_KEY_DOWN = 'rawKeyDown'


class KeyModifier(int, Enum):
    ALT = 1
    CTRL = 2
    META = 4
    SHIFT = 8


class KeyLocation(int, Enum):
    LEFT = 1
    RIGHT = 2


class MouseEventType(str, Enum):
    MOUSE_PRESSED = 'mousePressed'
    MOUSE_RELEASED = 'mouseReleased'
    MOUSE_MOVED = 'mouseMoved'
    MOUSE_WHEEL = 'mouseWheel'


class MouseButton(str, Enum):
    NONE = 'none'
    LEFT = 'left'
    MIDDLE = 'middle'
    RIGHT = 'right'
    BACK = 'back'
    FORWARD = 'forward'


class PointerType(str, Enum):
    MOUSE = 'mouse'
    PEN = 'pen'


class TouchEventType(str, Enum):
    TOUCH_START = 'touchStart'
    TOUCH_MOVE = 'touchMove'
    TOUCH_END = 'touchEnd'
    TOUCH_CANCEL = 'touchCancel'


class DragEventType(str, Enum):
    DRAG_ENTER = 'dragEnter'
    DRAG_OVER = 'dragOver'
    DROP = 'drop'
    DRAG_CANCEL = 'dragCancel'


class GestureSourceType(str, Enum):
    TOUCH = 'touch'
    MOUSE = 'mouse'
    DEFAULT = 'default'


class IncludeWhitespace(str, Enum):
    NONE = 'none'
    ALL = 'all'


class PhysicalAxes(str, Enum):
    HORIZONTAL = 'Horizontal'
    VERTICAL = 'Vertical'
    BOTH = 'Both'


class LogicalAxes(str, Enum):
    INLINE = 'Inline'
    BLOCK = 'Block'
    BOTH = 'Both'


class PseudoType(str, Enum):
    FIRST_LINE = 'first-line'
    FIRST_LETTER = 'first-letter'
    CHECKMARK = 'checkmark'
    BEFORE = 'before'
    AFTER = 'after'
    PICKER_ICON = 'picker-icon'
    MARKER = 'marker'
    BACKDROP = 'backdrop'
    COLUMN = 'column'
    SELECTION = 'selection'
    SEARCH_TEXT = 'search-text'
    TARGET_TEXT = 'target-text'
    SPELLING_ERROR = 'spelling-error'
    GRAMMAR_ERROR = 'grammar-error'
    HIGHLIGHT = 'highlight'
    FIRST_LINE_INHERITED = 'first-line-inherited'
    SCROLL_MARKER = 'scroll-marker'
    SCROLL_MARKER_GROUP = 'scroll-marker-group'
    SCROLL_BUTTON = 'scroll-button'
    SCROLLBAR = 'scrollbar'
    SCROLLBAR_THUMB = 'scrollbar-thumb'
    SCROLLBAR_BUTTON = 'scrollbar-button'
    SCROLLBAR_TRACK = 'scrollbar-track'
    SCROLLBAR_TRACK_PIECE = 'scrollbar-track-piece'
    SCROLLBAR_CORNER = 'scrollbar-corner'
    RESIZER = 'resizer'
    INPUT_LIST_BUTTON = 'input-list-button'
    VIEW_TRANSITION = 'view-transition'
    VIEW_TRANSITION_GROUP = 'view-transition-group'
    VIEW_TRANSITION_IMAGE_PAIR = 'view-transition-image-pair'
    VIEW_TRANSITION_OLD = 'view-transition-old'
    VIEW_TRANSITION_NEW = 'view-transition-new'
    PLACEHOLDER = 'placeholder'
    FILE_SELECTOR_BUTTON = 'file-selector-button'
    DETAILS_CONTENT = 'details-content'
    PICKER = 'picker'


class ShadowRootType(str, Enum):
    OPEN = 'open'
    CLOSED = 'closed'
    USER_AGENT = 'user-agent'


class CompatibilityMode(str, Enum):
    QUIRKS_MODE = 'QuirksMode'
    LIMITED_QUIRKS_MODE = 'LimitedQuirksMode'
    NO_QUIRKS_MODE = 'NoQuirksMode'


class ElementRelation(str, Enum):
    POPOVER_TARGET = 'PopoverTarget'
    INTEREST_TARGET = 'InterestTarget'


class MixedContentType(str, Enum):
    BLOCKABLE = 'blockable'
    OPTIONALLY_BLOCKABLE = 'optionally-blockable'
    NONE = 'none'


class ResourcePriority(str, Enum):
    VERY_LOW = 'VeryLow'
    LOW = 'Low'
    MEDIUM = 'Medium'
    HIGH = 'High'
    VERY_HIGH = 'VeryHigh'


class TrustTokenOperationType(str, Enum):
    ISSUANCE = 'Issuance'
    REDEMPTION = 'Redemption'
    SIGNING = 'Signing'


class RefreshPolicy(str, Enum):
    USE_CACHED = 'UseCached'
    REFRESH = 'Refresh'


class DialogType(str, Enum):
    ALERT = 'alert'
    CONFIRM = 'confirm'
    PROMPT = 'prompt'
    BEFORE_UNLOAD = 'beforeunload'


class InitiatorType(str, Enum):
    PARSER = 'parser'
    SCRIPT = 'script'
    PRELOAD = 'preload'
    SIGNED_EXCHANGE = 'SignedExchange'
    PREFLIGHT = 'preflight'
    OTHER = 'other'


class NetworkServiceWorkerRouterSourceType(str, Enum):
    """Network service worker router source types."""

    NETWORK = 'network'
    CACHE = 'cache'
    FETCH_EVENT = 'fetch-event'
    RACE_NETWORK = 'race-network'
    RACE_NETWORK_AND_FETCH_HANDLER = 'race-network-and-fetch-handler'
    RACE_NETWORK_AND_CACHE = 'race-network-and-cache'


class NetworkServiceWorkerResponseSource(str, Enum):
    """Network service worker response source types."""

    CACHE_STORAGE = 'cache-storage'
    HTTP_CACHE = 'http-cache'
    FALLBACK_CODE = 'fallback-code'
    NETWORK = 'network'


class AlternateProtocolUsage(str, Enum):
    """Alternate protocol usage types."""

    ALTERNATIVE_JOB_WON_WITHOUT_RACE = 'alternativeJobWonWithoutRace'
    ALTERNATIVE_JOB_WON_RACE = 'alternativeJobWonRace'
    MAIN_JOB_WON_RACE = 'mainJobWonRace'
    MAPPING_MISSING = 'mappingMissing'
    BROKEN = 'broken'
    DNS_ALPN_H3_JOB_WON_WITHOUT_RACE = 'dnsAlpnH3JobWonWithoutRace'
    DNS_ALPN_H3_JOB_WON_RACE = 'dnsAlpnH3JobWonRace'
    UNSPECIFIED_REASON = 'unspecifiedReason'


class SecurityState(str, Enum):
    """Security state types."""

    UNKNOWN = 'unknown'
    NEUTRAL = 'neutral'
    INSECURE = 'insecure'
    INFO = 'info'
    INSECURE_BROKEN = 'insecure-broken'


class CertificateTransparencyCompliance(str, Enum):
    """Certificate transparency compliance types."""

    UNKNOWN = 'unknown'
    NOT_COMPLIANT = 'not-compliant'
    COMPLIANT = 'compliant'
