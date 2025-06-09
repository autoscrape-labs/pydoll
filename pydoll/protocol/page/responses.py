from typing import TypedDict

try:
    from typing import NotRequired
except ImportError:
    from typing_extensions import NotRequired

from pydoll.protocol.dom.types import Rect
from pydoll.protocol.network.types import SearchMatch
from pydoll.protocol.page.types import (
    AdScriptId,
    AppManifestError,
    FrameResourceTree,
    FrameTree,
    InstallabilityError,
    LayoutViewport,
    NavigationEntry,
    OriginTrial,
    PermissionsPolicyFeatureState,
    VisualViewport,
    WebAppManifest,
)


class AddScriptToEvaluateOnNewDocumentResultDict(TypedDict):
    """Response result for addScriptToEvaluateOnNewDocument command."""

    identifier: str


class CaptureScreenshotResultDict(TypedDict):
    """Response result for captureScreenshot command."""

    data: str  # Base64-encoded image data


class CreateIsolatedWorldResultDict(TypedDict):
    """Response result for createIsolatedWorld command."""

    executionContextId: int


class GetAppManifestResultDict(TypedDict):
    """Response result for getAppManifest command."""

    url: str
    errors: list[AppManifestError]
    data: str  # Manifest content as string
    manifest: NotRequired[WebAppManifest]


class GetFrameTreeResultDict(TypedDict):
    """Response result for getFrameTree command."""

    frameTree: FrameTree


class GetLayoutMetricsResultDict(TypedDict):
    """Response result for getLayoutMetrics command."""

    cssLayoutViewport: LayoutViewport
    cssVisualViewport: VisualViewport
    cssContentSize: Rect


class GetNavigationHistoryResultDict(TypedDict):
    """Response result for getNavigationHistory command."""

    currentIndex: int
    entries: list[NavigationEntry]


class NavigateResultDict(TypedDict):
    """Response result for navigate command."""

    frameId: str
    loaderId: NotRequired[str]
    errorText: NotRequired[str]


class PrintToPDFResultDict(TypedDict):
    """Response result for printToPDF command."""

    data: str  # Base64-encoded pdf data
    stream: NotRequired[str]  # A handle to the stream that holds the PDF data


class CaptureSnapshotResultDict(TypedDict):
    """Response result for captureSnapshot command."""

    data: str  # Base64-encoded image data


class GetAdScriptAncestryIdsResultDict(TypedDict):
    """Response result for getAdScriptAncestryIds command."""

    adScriptAncestryIds: list[AdScriptId]


class GetAppIdResultDict(TypedDict):
    """Response result for getAppId command."""

    appId: NotRequired[str]
    recommendedId: NotRequired[str]


class GetInstallabilityErrorsResultDict(TypedDict):
    """Response result for getInstallabilityErrors command."""

    installabilityErrors: list[InstallabilityError]


class GetOriginTrialsResultDict(TypedDict):
    """Response result for getOriginTrials command."""

    originTrials: list[OriginTrial]


class GetPermissionsPolicyStateResultDict(TypedDict):
    """Response result for getPermissionsPolicyState command."""

    states: list[PermissionsPolicyFeatureState]


class GetResourceContentResultDict(TypedDict):
    """Response result for getResourceContent command."""

    content: str
    base64Encoded: bool


class GetResourceTreeResultDict(TypedDict):
    """Response result for getResourceTree command."""

    frameTree: FrameResourceTree


class SearchInResourceResultDict(TypedDict):
    """Response result for searchInResource command."""

    result: list[SearchMatch]


# Response classes that inherit from Response
class AddScriptToEvaluateOnNewDocumentResponse(TypedDict):
    """Response for addScriptToEvaluateOnNewDocument command."""

    result: AddScriptToEvaluateOnNewDocumentResultDict


class CaptureScreenshotResponse(TypedDict):
    """Response for captureScreenshot command."""

    result: CaptureScreenshotResultDict


class CreateIsolatedWorldResponse(TypedDict):
    """Response for createIsolatedWorld command."""

    result: CreateIsolatedWorldResultDict


class GetAppManifestResponse(TypedDict):
    """Response for getAppManifest command."""

    result: GetAppManifestResultDict


class GetFrameTreeResponse(TypedDict):
    """Response for getFrameTree command."""

    result: GetFrameTreeResultDict


class GetLayoutMetricsResponse(TypedDict):
    """Response for getLayoutMetrics command."""

    result: GetLayoutMetricsResultDict


class GetNavigationHistoryResponse(TypedDict):
    """Response for getNavigationHistory command."""

    result: GetNavigationHistoryResultDict


class NavigateResponse(TypedDict):
    """Response for navigate command."""

    result: NavigateResultDict


class PrintToPDFResponse(TypedDict):
    """Response for printToPDF command."""

    result: PrintToPDFResultDict


class CaptureSnapshotResponse(TypedDict):
    """Response for captureSnapshot command."""

    result: CaptureSnapshotResultDict


class GetAdScriptAncestryIdsResponse(TypedDict):
    """Response for getAdScriptAncestryIds command."""

    result: GetAdScriptAncestryIdsResultDict


class GetAppIdResponse(TypedDict):
    """Response for getAppId command."""

    result: GetAppIdResultDict


class GetInstallabilityErrorsResponse(TypedDict):
    """Response for getInstallabilityErrors command."""

    result: GetInstallabilityErrorsResultDict


class GetOriginTrialsResponse(TypedDict):
    """Response for getOriginTrials command."""

    result: GetOriginTrialsResultDict


class GetPermissionsPolicyStateResponse(TypedDict):
    """Response for getPermissionsPolicyState command."""

    result: GetPermissionsPolicyStateResultDict


class GetResourceContentResponse(TypedDict):
    """Response for getResourceContent command."""

    result: GetResourceContentResultDict


class GetResourceTreeResponse(TypedDict):
    """Response for getResourceTree command."""

    result: GetResourceTreeResultDict


class SearchInResourceResponse(TypedDict):
    """Response for searchInResource command."""

    result: SearchInResourceResultDict
