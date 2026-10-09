from enum import Enum

from typing_extensions import NotRequired, TypedDict

from pydoll.protocol.cdp.network.types import LoaderId, ResourceType, TimeSinceEpoch
from pydoll.protocol.cdp.runtime.types import ScriptId, UniqueDebuggerId

FrameId = str
ScriptIdentifier = str


class AdFrameType(str, Enum):
    """Ad frame types."""

    NONE = 'none'
    CHILD = 'child'
    ROOT = 'root'


class AdFrameExplanation(str, Enum):
    """Ad frame explanation types."""

    PARENT_IS_AD = 'ParentIsAd'
    CREATED_BY_AD_SCRIPT = 'CreatedByAdScript'
    MATCHED_BLOCKING_RULE = 'MatchedBlockingRule'


class SecureContextType(str, Enum):
    """Secure context types."""

    SECURE = 'Secure'
    SECURE_LOCALHOST = 'SecureLocalhost'
    INSECURE_SCHEME = 'InsecureScheme'
    INSECURE_ANCESTOR = 'InsecureAncestor'


class CrossOriginIsolatedContextType(str, Enum):
    """Cross-origin isolated context types."""

    ISOLATED = 'Isolated'
    NOT_ISOLATED = 'NotIsolated'
    NOT_ISOLATED_FEATURE_DISABLED = 'NotIsolatedFeatureDisabled'


class GatedAPIFeatures(str, Enum):
    """Gated API features."""

    SHARED_ARRAY_BUFFERS = 'SharedArrayBuffers'
    SHARED_ARRAY_BUFFERS_TRANSFER_ALLOWED = 'SharedArrayBuffersTransferAllowed'
    PERFORMANCE_MEASURE_MEMORY = 'PerformanceMeasureMemory'
    PERFORMANCE_PROFILE = 'PerformanceProfile'


class PermissionsPolicyFeature(str, Enum):
    """Permissions policy features."""

    ACCELEROMETER = 'accelerometer'
    ALL_SCREENS_CAPTURE = 'all-screens-capture'
    AMBIENT_LIGHT_SENSOR = 'ambient-light-sensor'
    ARIA_NOTIFY = 'aria-notify'
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
    LANGUAGE_MODEL = 'language-model'
    LOCAL_FONTS = 'local-fonts'
    LOCAL_NETWORK_ACCESS = 'local-network-access'
    MAGNETOMETER = 'magnetometer'
    MEDIA_PLAYBACK_WHILE_NOT_VISIBLE = 'media-playback-while-not-visible'
    MICROPHONE = 'microphone'
    MIDI = 'midi'
    ON_DEVICE_SPEECH_RECOGNITION = 'on-device-speech-recognition'
    OTP_CREDENTIALS = 'otp-credentials'
    PAYMENT = 'payment'
    PICTURE_IN_PICTURE = 'picture-in-picture'
    POPINS = 'popins'
    PRIVATE_AGGREGATION = 'private-aggregation'
    PRIVATE_STATE_TOKEN_ISSUANCE = 'private-state-token-issuance'
    PRIVATE_STATE_TOKEN_REDEMPTION = 'private-state-token-redemption'
    PUBLICKEY_CREDENTIALS_CREATE = 'publickey-credentials-create'
    PUBLICKEY_CREDENTIALS_GET = 'publickey-credentials-get'
    RECORD_AD_AUCTION_EVENTS = 'record-ad-auction-events'
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
    USB_UNRESTRICTED = 'usb-unrestricted'
    VERTICAL_SCROLL = 'vertical-scroll'
    WEB_APP_INSTALLATION = 'web-app-installation'
    WEB_PRINTING = 'web-printing'
    WEB_SHARE = 'web-share'
    WINDOW_MANAGEMENT = 'window-management'
    WRITER = 'writer'
    XR_SPATIAL_TRACKING = 'xr-spatial-tracking'


class PermissionsPolicyBlockReason(str, Enum):
    """Permissions policy block reasons."""

    HEADER = 'Header'
    IFRAME_ATTRIBUTE = 'IframeAttribute'
    IN_FENCED_FRAME_TREE = 'InFencedFrameTree'
    IN_ISOLATED_APP = 'InIsolatedApp'


class BackForwardCacheNotRestoredReasonType(str, Enum):
    """Back/forward cache not restored explanation type."""

    SUPPORT_PENDING = 'SupportPending'
    PAGE_SUPPORT_NEEDED = 'PageSupportNeeded'
    CIRCUMSTANTIAL = 'Circumstantial'


class BackForwardCacheNotRestoredReason(str, Enum):
    NOT_PRIMARY_MAIN_FRAME = 'NotPrimaryMainFrame'
    BACK_FORWARD_CACHE_DISABLED = 'BackForwardCacheDisabled'
    RELATED_ACTIVE_CONTENTS_EXIST = 'RelatedActiveContentsExist'
    HTTP_STATUS_NOT_OK = 'HTTPStatusNotOK'
    SCHEME_NOT_HTTP_OR_HTTPS = 'SchemeNotHTTPOrHTTPS'
    LOADING = 'Loading'
    WAS_GRANTED_MEDIA_ACCESS = 'WasGrantedMediaAccess'
    DISABLE_FOR_RENDER_FRAME_HOST_CALLED = 'DisableForRenderFrameHostCalled'
    DOMAIN_NOT_ALLOWED = 'DomainNotAllowed'
    HTTP_METHOD_NOT_GET = 'HTTPMethodNotGET'
    SUBFRAME_IS_NAVIGATING = 'SubframeIsNavigating'
    TIMEOUT = 'Timeout'
    CACHE_LIMIT = 'CacheLimit'
    JAVASCRIPT_EXECUTION = 'JavaScriptExecution'
    RENDERER_PROCESS_KILLED = 'RendererProcessKilled'
    RENDERER_PROCESS_CRASHED = 'RendererProcessCrashed'
    SCHEDULER_TRACKED_FEATURE_USED = 'SchedulerTrackedFeatureUsed'
    CONFLICTING_BROWSING_INSTANCE = 'ConflictingBrowsingInstance'
    CACHE_FLUSHED = 'CacheFlushed'
    SERVICE_WORKER_VERSION_ACTIVATION = 'ServiceWorkerVersionActivation'
    SESSION_RESTORED = 'SessionRestored'
    SERVICE_WORKER_POST_MESSAGE = 'ServiceWorkerPostMessage'
    ENTERED_BACK_FORWARD_CACHE_BEFORE_SERVICE_WORKER_HOST_ADDED = (
        'EnteredBackForwardCacheBeforeServiceWorkerHostAdded'
    )
    RENDER_FRAME_HOST_REUSED_SAME_SITE = 'RenderFrameHostReused_SameSite'
    RENDER_FRAME_HOST_REUSED_CROSS_SITE = 'RenderFrameHostReused_CrossSite'
    SERVICE_WORKER_CLAIM = 'ServiceWorkerClaim'
    IGNORE_EVENT_AND_EVICT = 'IgnoreEventAndEvict'
    HAVE_INNER_CONTENTS = 'HaveInnerContents'
    TIMEOUT_PUTTING_IN_CACHE = 'TimeoutPuttingInCache'
    BACK_FORWARD_CACHE_DISABLED_BY_LOW_MEMORY = 'BackForwardCacheDisabledByLowMemory'
    BACK_FORWARD_CACHE_DISABLED_BY_COMMAND_LINE = 'BackForwardCacheDisabledByCommandLine'
    NETWORK_REQUEST_DATAPIPE_DRAINED_AS_BYTES_CONSUMER = (
        'NetworkRequestDatapipeDrainedAsBytesConsumer'
    )
    NETWORK_REQUEST_REDIRECTED = 'NetworkRequestRedirected'
    NETWORK_REQUEST_TIMEOUT = 'NetworkRequestTimeout'
    NETWORK_EXCEEDS_BUFFER_LIMIT = 'NetworkExceedsBufferLimit'
    NAVIGATION_CANCELLED_WHILE_RESTORING = 'NavigationCancelledWhileRestoring'
    NOT_MOST_RECENT_NAVIGATION_ENTRY = 'NotMostRecentNavigationEntry'
    BACK_FORWARD_CACHE_DISABLED_FOR_PRERENDER = 'BackForwardCacheDisabledForPrerender'
    USER_AGENT_OVERRIDE_DIFFERS = 'UserAgentOverrideDiffers'
    FOREGROUND_CACHE_LIMIT = 'ForegroundCacheLimit'
    BROWSING_INSTANCE_NOT_SWAPPED = 'BrowsingInstanceNotSwapped'
    BACK_FORWARD_CACHE_DISABLED_FOR_DELEGATE = 'BackForwardCacheDisabledForDelegate'
    UNLOAD_HANDLER_EXISTS_IN_MAIN_FRAME = 'UnloadHandlerExistsInMainFrame'
    UNLOAD_HANDLER_EXISTS_IN_SUB_FRAME = 'UnloadHandlerExistsInSubFrame'
    SERVICE_WORKER_UNREGISTRATION = 'ServiceWorkerUnregistration'
    CACHE_CONTROL_NO_STORE = 'CacheControlNoStore'
    CACHE_CONTROL_NO_STORE_COOKIE_MODIFIED = 'CacheControlNoStoreCookieModified'
    CACHE_CONTROL_NO_STORE_HTTP_ONLY_COOKIE_MODIFIED = 'CacheControlNoStoreHTTPOnlyCookieModified'
    NO_RESPONSE_HEAD = 'NoResponseHead'
    UNKNOWN = 'Unknown'
    ACTIVATION_NAVIGATIONS_DISALLOWED_FOR_BUG_1234857 = (
        'ActivationNavigationsDisallowedForBug1234857'
    )
    ERROR_DOCUMENT = 'ErrorDocument'
    FENCED_FRAMES_EMBEDDER = 'FencedFramesEmbedder'
    COOKIE_DISABLED = 'CookieDisabled'
    HTTP_AUTH_REQUIRED = 'HTTPAuthRequired'
    COOKIE_FLUSHED = 'CookieFlushed'
    BROADCAST_CHANNEL_ON_MESSAGE = 'BroadcastChannelOnMessage'
    WEB_VIEW_SETTINGS_CHANGED = 'WebViewSettingsChanged'
    WEB_VIEW_JAVASCRIPT_OBJECT_CHANGED = 'WebViewJavaScriptObjectChanged'
    WEB_VIEW_MESSAGE_LISTENER_INJECTED = 'WebViewMessageListenerInjected'
    WEB_VIEW_SAFE_BROWSING_ALLOWLIST_CHANGED = 'WebViewSafeBrowsingAllowlistChanged'
    WEB_VIEW_DOCUMENT_START_JAVASCRIPT_CHANGED = 'WebViewDocumentStartJavascriptChanged'
    WEB_SOCKET = 'WebSocket'
    WEB_TRANSPORT = 'WebTransport'
    WEB_RTC = 'WebRTC'
    MAIN_RESOURCE_HAS_CACHE_CONTROL_NO_STORE = 'MainResourceHasCacheControlNoStore'
    MAIN_RESOURCE_HAS_CACHE_CONTROL_NO_CACHE = 'MainResourceHasCacheControlNoCache'
    SUBRESOURCE_HAS_CACHE_CONTROL_NO_STORE = 'SubresourceHasCacheControlNoStore'
    SUBRESOURCE_HAS_CACHE_CONTROL_NO_CACHE = 'SubresourceHasCacheControlNoCache'
    CONTAINS_PLUGINS = 'ContainsPlugins'
    DOCUMENT_LOADED = 'DocumentLoaded'
    OUTSTANDING_NETWORK_REQUEST_OTHERS = 'OutstandingNetworkRequestOthers'
    REQUESTED_MIDI_PERMISSION = 'RequestedMIDIPermission'
    REQUESTED_AUDIO_CAPTURE_PERMISSION = 'RequestedAudioCapturePermission'
    REQUESTED_VIDEO_CAPTURE_PERMISSION = 'RequestedVideoCapturePermission'
    REQUESTED_BACK_FORWARD_CACHE_BLOCKED_SENSORS = 'RequestedBackForwardCacheBlockedSensors'
    REQUESTED_BACKGROUND_WORK_PERMISSION = 'RequestedBackgroundWorkPermission'
    BROADCAST_CHANNEL = 'BroadcastChannel'
    WEB_XR = 'WebXR'
    SHARED_WORKER = 'SharedWorker'
    SHARED_WORKER_MESSAGE = 'SharedWorkerMessage'
    WEB_LOCKS = 'WebLocks'
    WEB_HID = 'WebHID'
    WEB_SHARE = 'WebShare'
    REQUESTED_STORAGE_ACCESS_GRANT = 'RequestedStorageAccessGrant'
    WEB_NFC = 'WebNfc'
    OUTSTANDING_NETWORK_REQUEST_FETCH = 'OutstandingNetworkRequestFetch'
    OUTSTANDING_NETWORK_REQUEST_XHR = 'OutstandingNetworkRequestXHR'
    APP_BANNER = 'AppBanner'
    PRINTING = 'Printing'
    WEB_DATABASE = 'WebDatabase'
    PICTURE_IN_PICTURE = 'PictureInPicture'
    SPEECH_RECOGNIZER = 'SpeechRecognizer'
    IDLE_MANAGER = 'IdleManager'
    PAYMENT_MANAGER = 'PaymentManager'
    SPEECH_SYNTHESIS = 'SpeechSynthesis'
    KEYBOARD_LOCK = 'KeyboardLock'
    WEB_OTP_SERVICE = 'WebOTPService'
    OUTSTANDING_NETWORK_REQUEST_DIRECT_SOCKET = 'OutstandingNetworkRequestDirectSocket'
    INJECTED_JAVASCRIPT = 'InjectedJavascript'
    INJECTED_STYLE_SHEET = 'InjectedStyleSheet'
    KEEPALIVE_REQUEST = 'KeepaliveRequest'
    INDEXED_DB_EVENT = 'IndexedDBEvent'
    DUMMY = 'Dummy'
    JS_NETWORK_REQUEST_RECEIVED_CACHE_CONTROL_NO_STORE_RESOURCE = (
        'JsNetworkRequestReceivedCacheControlNoStoreResource'
    )
    WEB_RTC_STICKY = 'WebRTCSticky'
    WEB_TRANSPORT_STICKY = 'WebTransportSticky'
    WEB_SOCKET_STICKY = 'WebSocketSticky'
    SMART_CARD = 'SmartCard'
    LIVE_MEDIA_STREAM_TRACK = 'LiveMediaStreamTrack'
    UNLOAD_HANDLER = 'UnloadHandler'
    PARSER_ABORTED = 'ParserAborted'
    CONTENT_SECURITY_HANDLER = 'ContentSecurityHandler'
    CONTENT_WEB_AUTHENTICATION_API = 'ContentWebAuthenticationAPI'
    CONTENT_FILE_CHOOSER = 'ContentFileChooser'
    CONTENT_SERIAL = 'ContentSerial'
    CONTENT_FILE_SYSTEM_ACCESS = 'ContentFileSystemAccess'
    CONTENT_MEDIA_DEVICES_DISPATCHER_HOST = 'ContentMediaDevicesDispatcherHost'
    CONTENT_WEB_BLUETOOTH = 'ContentWebBluetooth'
    CONTENT_WEB_USB = 'ContentWebUSB'
    CONTENT_MEDIA_SESSION_SERVICE = 'ContentMediaSessionService'
    CONTENT_SCREEN_READER = 'ContentScreenReader'
    CONTENT_DISCARDED = 'ContentDiscarded'
    EMBEDDER_POPUP_BLOCKER_TAB_HELPER = 'EmbedderPopupBlockerTabHelper'
    EMBEDDER_SAFE_BROWSING_TRIGGERED_POPUP_BLOCKER = 'EmbedderSafeBrowsingTriggeredPopupBlocker'
    EMBEDDER_SAFE_BROWSING_THREAT_DETAILS = 'EmbedderSafeBrowsingThreatDetails'
    EMBEDDER_APP_BANNER_MANAGER = 'EmbedderAppBannerManager'
    EMBEDDER_DOM_DISTILLER_VIEWER_SOURCE = 'EmbedderDomDistillerViewerSource'
    EMBEDDER_DOM_DISTILLER_SELF_DELETING_REQUEST_DELEGATE = (
        'EmbedderDomDistillerSelfDeletingRequestDelegate'
    )
    EMBEDDER_OOM_INTERVENTION_TAB_HELPER = 'EmbedderOomInterventionTabHelper'
    EMBEDDER_OFFLINE_PAGE = 'EmbedderOfflinePage'
    EMBEDDER_CHROME_PASSWORD_MANAGER_CLIENT_BIND_CREDENTIAL_MANAGER = (
        'EmbedderChromePasswordManagerClientBindCredentialManager'
    )
    EMBEDDER_PERMISSION_REQUEST_MANAGER = 'EmbedderPermissionRequestManager'
    EMBEDDER_MODAL_DIALOG = 'EmbedderModalDialog'
    EMBEDDER_EXTENSIONS = 'EmbedderExtensions'
    EMBEDDER_EXTENSION_MESSAGING = 'EmbedderExtensionMessaging'
    EMBEDDER_EXTENSION_MESSAGING_FOR_OPEN_PORT = 'EmbedderExtensionMessagingForOpenPort'
    EMBEDDER_EXTENSION_SENT_MESSAGE_TO_CACHED_FRAME = 'EmbedderExtensionSentMessageToCachedFrame'
    REQUESTED_BY_WEB_VIEW_CLIENT = 'RequestedByWebViewClient'
    POST_MESSAGE_BY_WEB_VIEW_CLIENT = 'PostMessageByWebViewClient'
    CACHE_CONTROL_NO_STORE_DEVICE_BOUND_SESSION_TERMINATED = (
        'CacheControlNoStoreDeviceBoundSessionTerminated'
    )
    CACHE_LIMIT_PRUNED_ON_MODERATE_MEMORY_PRESSURE = 'CacheLimitPrunedOnModerateMemoryPressure'
    CACHE_LIMIT_PRUNED_ON_CRITICAL_MEMORY_PRESSURE = 'CacheLimitPrunedOnCriticalMemoryPressure'


class BackForwardCacheBlockingDetails(TypedDict):
    url: NotRequired[str]
    function: NotRequired[str]
    lineNumber: int
    columnNumber: int


class BackForwardCacheNotRestoredExplanation(TypedDict):
    """Back/forward cache not restored explanation."""

    type: BackForwardCacheNotRestoredReasonType
    reason: BackForwardCacheNotRestoredReason
    context: NotRequired[str]
    details: NotRequired[list[BackForwardCacheBlockingDetails]]


class BackForwardCacheNotRestoredExplanationTree(TypedDict):
    url: str
    explanations: list[BackForwardCacheNotRestoredExplanation]
    children: NotRequired[list['BackForwardCacheNotRestoredExplanationTree']]


class OriginTrialTokenStatus(str, Enum):
    """Origin trial token status."""

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


class OriginTrialStatus(str, Enum):
    """Origin trial status."""

    ENABLED = 'Enabled'
    VALID_TOKEN_NOT_PROVIDED = 'ValidTokenNotProvided'
    OS_NOT_SUPPORTED = 'OSNotSupported'
    TRIAL_NOT_ALLOWED = 'TrialNotAllowed'


class OriginTrialUsageRestriction(str, Enum):
    """Origin trial usage restriction."""

    NONE = 'None'
    SUBSET = 'Subset'


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


class DialogType(str, Enum):
    """Dialog types."""

    ALERT = 'alert'
    CONFIRM = 'confirm'
    PROMPT = 'prompt'
    BEFOREUNLOAD = 'beforeunload'


class ClientNavigationReason(Enum):
    """Client navigation reasons."""

    ANCHOR_CLICK = 'anchorClick'
    FORM_SUBMISSION_GET = 'formSubmissionGet'
    FORM_SUBMISSION_POST = 'formSubmissionPost'
    HTTP_HEADER_REFRESH = 'httpHeaderRefresh'
    INITIAL_FRAME_NAVIGATION = 'initialFrameNavigation'
    META_TAG_REFRESH = 'metaTagRefresh'
    OTHER = 'other'
    PAGE_BLOCK_INTERSTITIAL = 'pageBlockInterstitial'
    RELOAD = 'reload'
    SCRIPT_INITIATED = 'scriptInitiated'


class ClientNavigationDisposition(str, Enum):
    """Client navigation dispositions."""

    CURRENT_TAB = 'currentTab'
    NEW_TAB = 'newTab'
    NEW_WINDOW = 'newWindow'
    DOWNLOAD = 'download'


class ReferrerPolicy(str, Enum):
    """Referrer policy types."""

    NO_REFERRER = 'noReferrer'
    NO_REFERRER_WHEN_DOWNGRADE = 'noReferrerWhenDowngrade'
    ORIGIN = 'origin'
    ORIGIN_WHEN_CROSS_ORIGIN = 'originWhenCrossOrigin'
    SAME_ORIGIN = 'sameOrigin'
    STRICT_ORIGIN = 'strictOrigin'
    STRICT_ORIGIN_WHEN_CROSS_ORIGIN = 'strictOriginWhenCrossOrigin'
    UNSAFE_URL = 'unsafeUrl'


class NavigationType(str, Enum):
    """Navigation types."""

    NAVIGATION = 'Navigation'
    BACK_FORWARD_CACHE_RESTORE = 'BackForwardCacheRestore'


class AdFrameStatus(TypedDict):
    """Ad frame status."""

    adFrameType: AdFrameType
    explanations: NotRequired[list[AdFrameExplanation]]


class AdScriptId(TypedDict):
    """Ad script identifier."""

    scriptId: ScriptId
    debuggerId: UniqueDebuggerId


class AdScriptAncestry(TypedDict):
    """Ad script ancestry."""

    ancestryChain: list[AdScriptId]
    rootScriptFilterlistRule: NotRequired[str]


class PermissionsPolicyBlockLocator(TypedDict):
    """Permissions policy block locator."""

    frameId: FrameId
    blockReason: PermissionsPolicyBlockReason


class PermissionsPolicyFeatureState(TypedDict):
    """Permissions policy feature state."""

    feature: PermissionsPolicyFeature
    allowed: bool
    locator: NotRequired[PermissionsPolicyBlockLocator]


class OriginTrialToken(TypedDict):
    """Origin trial token."""

    origin: str
    matchSubDomains: bool
    trialName: str
    expiryTime: TimeSinceEpoch
    isThirdParty: bool
    usageRestriction: OriginTrialUsageRestriction


class OriginTrialTokenWithStatus(TypedDict):
    """Origin trial token with status."""

    rawTokenText: str
    status: OriginTrialTokenStatus
    parsedToken: NotRequired[OriginTrialToken]


class OriginTrial(TypedDict):
    """Origin trial."""

    trialName: str
    status: OriginTrialStatus
    tokensWithStatus: list[OriginTrialTokenWithStatus]


class SecurityOriginDetails(TypedDict):
    """Security origin details."""

    isLocalhost: bool


class Frame(TypedDict):
    """Frame information."""

    id: FrameId
    loaderId: LoaderId
    url: str
    domainAndRegistry: str
    securityOrigin: str
    mimeType: str
    secureContextType: SecureContextType
    crossOriginIsolatedContextType: CrossOriginIsolatedContextType
    gatedAPIFeatures: list[GatedAPIFeatures]
    parentId: NotRequired[FrameId]
    name: NotRequired[str]
    urlFragment: NotRequired[str]
    securityOriginDetails: NotRequired[SecurityOriginDetails]
    unreachableUrl: NotRequired[str]
    adFrameStatus: NotRequired[AdFrameStatus]


class FrameResource(TypedDict):
    """Frame resource information."""

    url: str
    type: ResourceType
    mimeType: str
    lastModified: NotRequired[TimeSinceEpoch]
    contentSize: NotRequired[float]
    failed: NotRequired[bool]
    canceled: NotRequired[bool]


class FrameResourceTree(TypedDict):
    """Frame resource tree."""

    frame: Frame
    resources: list[FrameResource]
    childFrames: NotRequired[list['FrameResourceTree']]


class FrameTree(TypedDict):
    """Frame tree."""

    frame: Frame
    childFrames: NotRequired[list['FrameTree']]


class NavigationEntry(TypedDict):
    """Navigation entry."""

    id: int
    url: str
    userTypedURL: str
    title: str
    transitionType: TransitionType


class ScreencastFrameMetadata(TypedDict):
    """Screencast frame metadata."""

    offsetTop: float
    pageScaleFactor: float
    deviceWidth: float
    deviceHeight: float
    scrollOffsetX: float
    scrollOffsetY: float
    timestamp: NotRequired[TimeSinceEpoch]


class AppManifestError(TypedDict):
    """App manifest error."""

    message: str
    critical: int
    line: int
    column: int


class AppManifestParsedProperties(TypedDict):
    """App manifest parsed properties."""

    scope: str


class LayoutViewport(TypedDict):
    """Layout viewport."""

    pageX: int
    pageY: int
    clientWidth: int
    clientHeight: int


class VisualViewport(TypedDict):
    """Visual viewport."""

    offsetX: float
    offsetY: float
    pageX: float
    pageY: float
    clientWidth: float
    clientHeight: float
    scale: float
    zoom: NotRequired[float]


class Viewport(TypedDict):
    """Viewport for capturing screenshot."""

    x: float
    y: float
    width: float
    height: float
    scale: float


class FontFamilies(TypedDict, total=False):
    """Font families."""

    standard: str
    fixed: str
    serif: str
    sansSerif: str
    cursive: str
    fantasy: str
    math: str


class ScriptFontFamilies(TypedDict):
    """Script font families."""

    script: str
    fontFamilies: FontFamilies


class FontSizes(TypedDict, total=False):
    """Font sizes."""

    standard: int
    fixed: int


class CompilationCacheParams(TypedDict):
    """Compilation cache parameters."""

    url: str
    eager: NotRequired[bool]


class FileFilter(TypedDict, total=False):
    """File filter."""

    name: str
    accepts: list[str]


class ImageResource(TypedDict):
    """Image resource."""

    url: str
    sizes: NotRequired[str]
    type: NotRequired[str]


class FileHandler(TypedDict):
    """File handler."""

    action: str
    name: str
    launchType: str
    icons: NotRequired[list[ImageResource]]
    accepts: NotRequired[list[FileFilter]]


class LaunchHandler(TypedDict):
    """Launch handler."""

    clientMode: str


class ProtocolHandler(TypedDict):
    """Protocol handler."""

    protocol: str
    url: str


class RelatedApplication(TypedDict):
    """Related application."""

    url: str
    id: NotRequired[str]


class ScopeExtension(TypedDict):
    """Scope extension."""

    origin: str
    hasOriginWildcard: bool


class Screenshot(TypedDict):
    """Screenshot."""

    image: ImageResource
    formFactor: str
    label: NotRequired[str]


class ShareTarget(TypedDict):
    """Share target."""

    action: str
    method: str
    enctype: str
    title: NotRequired[str]
    text: NotRequired[str]
    url: NotRequired[str]
    files: NotRequired[list[FileFilter]]


class Shortcut(TypedDict):
    """Shortcut."""

    name: str
    url: str


class WebAppManifest(TypedDict, total=False):
    """Web app manifest."""

    backgroundColor: str
    description: str
    dir: str
    display: str
    displayOverrides: list[str]
    fileHandlers: list[FileHandler]
    icons: list[ImageResource]
    id: str
    lang: str
    launchHandler: LaunchHandler
    name: str
    orientation: str
    preferRelatedApplications: bool
    protocolHandlers: list[ProtocolHandler]
    relatedApplications: list[RelatedApplication]
    scope: str
    scopeExtensions: list[ScopeExtension]
    screenshots: list[Screenshot]
    shareTarget: ShareTarget
    shortName: str
    shortcuts: list[Shortcut]
    startUrl: str
    themeColor: str


class InstallabilityErrorArgument(TypedDict):
    """Installability error argument."""

    name: str
    value: str


class InstallabilityError(TypedDict):
    """Installability error."""

    errorId: str
    errorArguments: list[InstallabilityErrorArgument]


class AutoResponseMode(str, Enum):
    """Auto response mode values."""

    NONE = 'none'
    AUTO_ACCEPT = 'autoAccept'
    AUTO_CHOOSE_TO_AUTH_ANOTHER_WAY = 'autoChooseToAuthAnotherWay'
    AUTO_REJECT = 'autoReject'
    AUTO_OPT_OUT = 'autoOptOut'


class WebLifecycleState(str, Enum):
    """Web lifecycle state values."""

    FROZEN = 'frozen'
    ACTIVE = 'active'


class ScreenshotFormat(str, Enum):
    """Screenshot format values."""

    JPEG = 'jpeg'
    PNG = 'png'
    WEBP = 'webp'

    @classmethod
    def has_value(cls, value: str) -> bool:
        """Check if value is a valid screenshot format."""
        return value in cls._value2member_map_

    @classmethod
    def get_value(cls, value: str) -> 'ScreenshotFormat':
        """Get the value of the screenshot format."""
        return cls(value)


class ScreencastFormat(str, Enum):
    """Screencast format values."""

    JPEG = 'jpeg'
    PNG = 'png'


class TransferMode(str, Enum):
    """Transfer mode values."""

    RETURN_AS_BASE64 = 'ReturnAsBase64'
    RETURN_AS_STREAM = 'ReturnAsStream'
