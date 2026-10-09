from enum import Enum

from typing_extensions import TypedDict

BrowserContextID = str
WindowID = int


class WindowState(str, Enum):
    """The state of the browser window."""

    NORMAL = 'normal'
    MINIMIZED = 'minimized'
    MAXIMIZED = 'maximized'
    FULLSCREEN = 'fullscreen'


class DownloadBehavior(str, Enum):
    """Download behavior options."""

    DENY = 'deny'
    ALLOW = 'allow'
    ALLOW_AND_NAME = 'allowAndName'
    DEFAULT = 'default'


class DownloadProgressState(str, Enum):
    """Download progress state."""

    IN_PROGRESS = 'inProgress'
    COMPLETED = 'completed'
    CANCELED = 'canceled'


class Bounds(TypedDict, total=False):
    """Browser window bounds information."""

    left: int  # The offset from the left edge of the screen to the window in pixels.
    top: int  # The offset from the top edge of the screen to the window in pixels.
    width: int  # The window width in pixels.
    height: int  # The window height in pixels.
    windowState: WindowState  # The window state. Default to normal.


class PermissionType(str, Enum):
    """Permission types."""

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


class PermissionSetting(str, Enum):
    """Permission setting values."""

    GRANTED = 'granted'
    DENIED = 'denied'
    PROMPT = 'prompt'


class PermissionDescriptor(TypedDict, total=False):
    """Definition of PermissionDescriptor defined in the Permissions API.

    See https://w3c.github.io/permissions/#dom-permissiondescriptor.
    """

    name: str  # Name of permission.
    sysex: bool  # For "midi" permission, may also specify sysex control.
    userVisibleOnly: bool  # For "push" permission, may specify userVisibleOnly.
    allowWithoutSanitization: (
        bool  # For "clipboard" permission, may specify allowWithoutSanitization.
    )
    allowWithoutGesture: bool  # For "fullscreen" permission, must specify allowWithoutGesture:true.
    panTiltZoom: bool  # For "camera" permission, may specify panTiltZoom.


class BrowserCommandId(str, Enum):
    """Browser command ids used by executeBrowserCommand."""

    OPEN_TAB_SEARCH = 'openTabSearch'
    CLOSE_TAB_SEARCH = 'closeTabSearch'
    OPEN_GLIC = 'openGlic'


class Bucket(TypedDict):
    """Chrome histogram bucket."""

    low: int  # Minimum value (inclusive).
    high: int  # Maximum value (exclusive).
    count: int  # Number of samples.


class Histogram(TypedDict):
    """Chrome histogram."""

    name: str  # Name.
    sum: int  # Sum of sample values.
    count: int  # Total number of samples.
    buckets: list['Bucket']  # Buckets.


class PrivacySandboxAPI(str, Enum):
    """Privacy Sandbox API types."""

    BIDDING_AND_AUCTION_SERVICES = 'BiddingAndAuctionServices'
    TRUSTED_KEY_VALUE = 'TrustedKeyValue'
