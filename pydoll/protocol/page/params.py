from typing import Literal

try:
    from typing import NotRequired
except ImportError:
    from typing_extensions import NotRequired


from pydoll.constants import (
    AutoResponseMode,
    ReferrerPolicy,
    ScreencastFormat,
    ScreenshotFormat,
    TransferMode,
    TransitionType,
    WebLifecycleState,
)
from pydoll.protocol.base import CommandParams
from pydoll.protocol.page.types import (
    FontFamilies,
    FontSizes,
    InstallabilityError,
    ScriptFontFamilies,
    Viewport,
)


class AddScriptToEvaluateOnNewDocumentParams(CommandParams):
    """Parameters for adding script to evaluate on new document."""

    source: str
    worldName: NotRequired[str]
    includeCommandLineAPI: NotRequired[bool]
    runImmediately: NotRequired[bool]


class CaptureScreenshotParams(CommandParams):
    """Parameters for capturing page screenshot."""

    format: NotRequired[ScreenshotFormat]
    quality: NotRequired[int]
    clip: NotRequired[Viewport]
    fromSurface: NotRequired[bool]
    captureBeyondViewport: NotRequired[bool]
    optimizeForSpeed: NotRequired[bool]


class CreateIsolatedWorldParams(CommandParams):
    """Parameters for creating an isolated world."""

    frameId: str
    worldName: NotRequired[str]
    grantUniveralAccess: NotRequired[bool]


class PageEnableParams(CommandParams):
    """Parameters for enabling page domain."""

    enableFileChooserOpenedEvent: NotRequired[bool]


class GetAppManifestParams(CommandParams):
    """Parameters for getting app manifest."""

    manifestId: NotRequired[str]


class HandleJavaScriptDialogParams(CommandParams):
    """Parameters for handling JavaScript dialog."""

    accept: bool
    promptText: NotRequired[str]


class NavigateParams(CommandParams):
    """Parameters for navigating to URL."""

    url: str
    referrer: NotRequired[str]
    transitionType: NotRequired[TransitionType]
    frameId: NotRequired[str]
    referrerPolicy: NotRequired[ReferrerPolicy]


class NavigateToHistoryEntryParams(CommandParams):
    """Parameters for navigating to history entry."""

    entryId: int


class PrintToPDFParams(CommandParams):
    """Parameters for printing to PDF."""

    landscape: NotRequired[bool]
    displayHeaderFooter: NotRequired[bool]
    printBackground: NotRequired[bool]
    scale: NotRequired[float]
    paperWidth: NotRequired[float]
    paperHeight: NotRequired[float]
    marginTop: NotRequired[float]
    marginBottom: NotRequired[float]
    marginLeft: NotRequired[float]
    marginRight: NotRequired[float]
    pageRanges: NotRequired[str]
    headerTemplate: NotRequired[str]
    footerTemplate: NotRequired[str]
    preferCSSPageSize: NotRequired[bool]
    transferMode: NotRequired[TransferMode]
    generateTaggedPDF: NotRequired[bool]
    generateDocumentOutline: NotRequired[bool]


class RemoveScriptToEvaluateOnNewDocumentParams(CommandParams):
    """Parameters for removing script to evaluate on new document."""

    identifier: str


class ReloadParams(CommandParams):
    """Parameters for reloading page."""

    ignoreCache: NotRequired[bool]
    scriptToEvaluateOnLoad: NotRequired[str]
    loaderId: NotRequired[str]


class SetBypassCSPParams(CommandParams):
    """Parameters for setting bypass CSP."""

    enabled: bool


class SetDocumentContentParams(CommandParams):
    """Parameters for setting document content."""

    frameId: str
    html: str


class SetInterceptFileChooserDialogParams(CommandParams):
    """Parameters for setting intercept file chooser dialog."""

    enabled: bool
    cancel: NotRequired[bool]


class SetLifecycleEventsEnabledParams(CommandParams):
    """Parameters for setting lifecycle events enabled."""

    enabled: bool


class AddCompilationCacheParams(CommandParams):
    url: str
    data: str


class CaptureSnapshotParams(CommandParams):
    format: Literal['mhtml']


class GenerateTestReportParams(CommandParams):
    message: str
    group: NotRequired[str]


class GetAdScriptAncestryIdsParams(CommandParams):
    frameId: str


class GetAppIdParams(CommandParams):
    appId: NotRequired[str]
    recommendedId: NotRequired[str]


class GetInstallabilityErrorsParams(CommandParams):
    installabilityErrors: NotRequired[list[InstallabilityError]]


class GetOriginTrialsParams(CommandParams):
    frameId: str


class GetPermissionsPolicyStateParams(CommandParams):
    frameId: str


class GetResourceContentParams(CommandParams):
    frameId: str
    url: str


class ScreencastFrameAckParams(CommandParams):
    sessionId: str


class SearchInResourceParams(CommandParams):
    frameId: str
    url: str
    query: str
    caseSensitive: NotRequired[bool]
    isRegex: NotRequired[bool]


class SetAdBlockingEnabledParams(CommandParams):
    enabled: bool


class SetFontFamiliesParams(CommandParams):
    fontFamilies: FontFamilies
    forScripts: list[ScriptFontFamilies]


class SetFontSizesParams(CommandParams):
    fontSizes: FontSizes


class SetPrerenderingAllowedParams(CommandParams):
    allowed: bool


class SetRPHRegistrationModeParams(CommandParams):
    mode: AutoResponseMode


class SetSPCTransactionModeParams(CommandParams):
    mode: AutoResponseMode


class SetWebLifecycleStateParams(CommandParams):
    state: WebLifecycleState


class StartScreencastParams(CommandParams):
    format: ScreencastFormat
    quality: NotRequired[int]
    maxWidth: NotRequired[int]
    maxHeight: NotRequired[int]
    everyNthFrame: NotRequired[int]


class CompilationCacheParams(CommandParams):
    url: str
    eager: NotRequired[bool]


class ProduceCompilationCacheParams(CommandParams):
    scripts: list[CompilationCacheParams]
