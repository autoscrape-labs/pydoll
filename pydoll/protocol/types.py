from enum import Enum

from typing_extensions import NotRequired, TypedDict


class Header(TypedDict):
    """HTTP header."""

    name: str
    value: str


class CookieParam(TypedDict):
    """Cookie parameters for setting cookies."""

    name: str
    value: str
    url: NotRequired[str]
    domain: str
    path: NotRequired[str]
    httpOnly: NotRequired[bool]
    secure: NotRequired[bool]
    sameSite: NotRequired[str]
    expiry: NotRequired[int]


class Cookie(TypedDict):
    """Cookie returned by get_cookies."""

    name: str
    value: str
    domain: str
    path: str
    size: int
    httpOnly: bool
    secure: bool
    sameSite: str
    expiry: NotRequired[int]


class WindowBounds(TypedDict, total=False):
    """Window position and dimensions."""

    width: int
    height: int
    x: int
    y: int


class BrowserVersion(TypedDict):
    """Browser version information."""

    browserName: str
    browserVersion: str
    userAgent: str


class DownloadBehavior(str, Enum):
    """Download behavior options (portable subset across CDP and BiDi)."""

    ALLOW = 'allow'
    DENY = 'deny'


class RequestMethod(str, Enum):
    """HTTP request methods."""

    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    DELETE = 'DELETE'
    PATCH = 'PATCH'
    HEAD = 'HEAD'
    OPTIONS = 'OPTIONS'


class Permission(str, Enum):
    """Browser permission, portable across CDP and BiDi.

    Covers the full set of permissions Chromium/CDP supports (the superset).
    Member values are the CDP permission names; Chromium grants them directly,
    while Firefox/BiDi maps the subset it supports to W3C names and warns when a
    requested permission has no BiDi equivalent.
    """

    AR = 'ar'
    MICROPHONE = 'audioCapture'
    AUTOMATIC_FULLSCREEN = 'automaticFullscreen'
    BACKGROUND_FETCH = 'backgroundFetch'
    BACKGROUND_SYNC = 'backgroundSync'
    CAMERA_PAN_TILT_ZOOM = 'cameraPanTiltZoom'
    CAPTURED_SURFACE_CONTROL = 'capturedSurfaceControl'
    CLIPBOARD_READ = 'clipboardReadWrite'
    CLIPBOARD_WRITE = 'clipboardSanitizedWrite'
    DISPLAY_CAPTURE = 'displayCapture'
    PERSISTENT_STORAGE = 'durableStorage'
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
    CAMERA = 'videoCapture'
    VR = 'vr'
    SCREEN_WAKE_LOCK = 'wakeLockScreen'
    SYSTEM_WAKE_LOCK = 'wakeLockSystem'
    WEB_APP_INSTALLATION = 'webAppInstallation'
    WEB_PRINTING = 'webPrinting'
    WINDOW_MANAGEMENT = 'windowManagement'
