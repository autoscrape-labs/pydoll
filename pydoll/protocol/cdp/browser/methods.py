from enum import Enum

from typing_extensions import NotRequired, TypedDict

from pydoll.protocol.cdp.base import Command, EmptyParams, EmptyResponse, Response
from pydoll.protocol.cdp.browser.types import (
    Bounds,
    BrowserCommandId,
    BrowserContextID,
    DownloadBehavior,
    Histogram,
    PermissionDescriptor,
    PermissionSetting,
    PermissionType,
    PrivacySandboxAPI,
    WindowID,
)


class BrowserMethod(str, Enum):
    """Browser domain method names."""

    ADD_PRIVACY_SANDBOX_COORDINATOR_KEY_CONFIG = 'Browser.addPrivacySandboxCoordinatorKeyConfig'
    ADD_PRIVACY_SANDBOX_ENROLLMENT_OVERRIDE = 'Browser.addPrivacySandboxEnrollmentOverride'
    CANCEL_DOWNLOAD = 'Browser.cancelDownload'
    CLOSE = 'Browser.close'
    CRASH = 'Browser.crash'
    CRASH_GPU_PROCESS = 'Browser.crashGpuProcess'
    EXECUTE_BROWSER_COMMAND = 'Browser.executeBrowserCommand'
    GET_BROWSER_COMMAND_LINE = 'Browser.getBrowserCommandLine'
    GET_HISTOGRAM = 'Browser.getHistogram'
    GET_HISTOGRAMS = 'Browser.getHistograms'
    GET_VERSION = 'Browser.getVersion'
    GET_WINDOW_BOUNDS = 'Browser.getWindowBounds'
    GET_WINDOW_FOR_TARGET = 'Browser.getWindowForTarget'
    GRANT_PERMISSIONS = 'Browser.grantPermissions'
    RESET_PERMISSIONS = 'Browser.resetPermissions'
    SET_CONTENTS_SIZE = 'Browser.setContentsSize'
    SET_DOCK_TILE = 'Browser.setDockTile'
    SET_DOWNLOAD_BEHAVIOR = 'Browser.setDownloadBehavior'
    SET_PERMISSION = 'Browser.setPermission'
    SET_WINDOW_BOUNDS = 'Browser.setWindowBounds'


class SetPermissionParams(TypedDict):
    """Parameters for setting permission settings for given origin."""

    permission: PermissionDescriptor
    setting: PermissionSetting
    origin: NotRequired[str]
    browserContextId: NotRequired[BrowserContextID]


class GrantPermissionsParams(TypedDict):
    """Parameters for granting specific permissions to the given origin."""

    permissions: list[PermissionType]
    origin: NotRequired[str]
    browserContextId: NotRequired[BrowserContextID]


class ResetPermissionsParams(TypedDict):
    """Parameters for resetting all permission management for all origins."""

    browserContextId: NotRequired[BrowserContextID]


class SetDownloadBehaviorParams(TypedDict):
    """Parameters for setting the behavior when downloading a file."""

    behavior: DownloadBehavior
    browserContextId: NotRequired[BrowserContextID]
    downloadPath: NotRequired[str]
    eventsEnabled: NotRequired[bool]


class CancelDownloadParams(TypedDict):
    """Parameters for cancelling a download if in progress."""

    guid: str
    browserContextId: NotRequired[BrowserContextID]


class GetHistogramsParams(TypedDict):
    """Parameters for getting Chrome histograms."""

    query: NotRequired[str]
    delta: NotRequired[bool]


class GetHistogramParams(TypedDict):
    """Parameters for getting a Chrome histogram by name."""

    name: str
    delta: NotRequired[bool]


class GetWindowBoundsParams(TypedDict):
    """Parameters for getting position and size of the browser window."""

    windowId: WindowID


class GetWindowForTargetParams(TypedDict):
    """Parameters for getting the browser window that contains the devtools target."""

    targetId: NotRequired[str]  # Target.TargetID


class SetWindowBoundsParams(TypedDict):
    """Parameters for setting position and/or size of the browser window."""

    windowId: WindowID
    bounds: Bounds


class SetContentsSizeParams(TypedDict):
    """Parameters for setting size of the browser contents."""

    windowId: WindowID
    width: NotRequired[int]
    height: NotRequired[int]


class SetDockTileParams(TypedDict):
    """Parameters for setting dock tile details, platform-specific."""

    badgeLabel: NotRequired[str]
    image: NotRequired[str]  # Png encoded image (base64)


class ExecuteBrowserCommandParams(TypedDict):
    """Parameters for invoking custom browser commands used by telemetry."""

    commandId: BrowserCommandId


class AddPrivacySandboxEnrollmentOverrideParams(TypedDict):
    """Parameters for allowing a site to use privacy sandbox features without enrollment."""

    url: str


class AddPrivacySandboxCoordinatorKeyConfigParams(TypedDict):
    """Parameters for configuring encryption keys for privacy sandbox API."""

    api: PrivacySandboxAPI
    coordinatorOrigin: str
    keyConfig: str
    browserContextId: NotRequired[BrowserContextID]


# Result types
class GetVersionResult(TypedDict):
    """Result for getVersion command."""

    protocolVersion: str
    product: str
    revision: str
    userAgent: str
    jsVersion: str


class GetBrowserCommandLineResult(TypedDict):
    """Result for getBrowserCommandLine command."""

    arguments: list[str]


class GetHistogramsResult(TypedDict):
    """Result for getHistograms command."""

    histograms: list[Histogram]


class GetHistogramResult(TypedDict):
    """Result for getHistogram command."""

    histogram: Histogram


class GetWindowBoundsResult(TypedDict):
    """Result for getWindowBounds command."""

    bounds: Bounds


class GetWindowForTargetResult(TypedDict):
    """Result for getWindowForTarget command."""

    windowId: WindowID
    bounds: Bounds


# Response types
GetVersionResponse = Response[GetVersionResult]
GetBrowserCommandLineResponse = Response[GetBrowserCommandLineResult]
GetHistogramsResponse = Response[GetHistogramsResult]
GetHistogramResponse = Response[GetHistogramResult]
GetWindowBoundsResponse = Response[GetWindowBoundsResult]
GetWindowForTargetResponse = Response[GetWindowForTargetResult]


# Command types
AddPrivacySandboxCoordinatorKeyConfigCommand = Command[
    AddPrivacySandboxCoordinatorKeyConfigParams, Response[EmptyResponse]
]
AddPrivacySandboxEnrollmentOverrideCommand = Command[
    AddPrivacySandboxEnrollmentOverrideParams, Response[EmptyResponse]
]
CancelDownloadCommand = Command[CancelDownloadParams, Response[EmptyResponse]]
CloseCommand = Command[EmptyParams, Response[EmptyResponse]]
CrashCommand = Command[EmptyParams, Response[EmptyResponse]]
CrashGpuProcessCommand = Command[EmptyParams, Response[EmptyResponse]]
ExecuteBrowserCommandCommand = Command[ExecuteBrowserCommandParams, Response[EmptyResponse]]
GetBrowserCommandLineCommand = Command[EmptyParams, GetBrowserCommandLineResponse]
GetHistogramCommand = Command[GetHistogramParams, GetHistogramResponse]
GetHistogramsCommand = Command[GetHistogramsParams, GetHistogramsResponse]
GetVersionCommand = Command[EmptyParams, GetVersionResponse]
GetWindowBoundsCommand = Command[GetWindowBoundsParams, GetWindowBoundsResponse]
GetWindowForTargetCommand = Command[GetWindowForTargetParams, GetWindowForTargetResponse]
GrantPermissionsCommand = Command[GrantPermissionsParams, Response[EmptyResponse]]
ResetPermissionsCommand = Command[ResetPermissionsParams, Response[EmptyResponse]]
SetContentsSizeCommand = Command[SetContentsSizeParams, Response[EmptyResponse]]
SetDockTileCommand = Command[SetDockTileParams, Response[EmptyResponse]]
SetDownloadBehaviorCommand = Command[SetDownloadBehaviorParams, Response[EmptyResponse]]
SetPermissionCommand = Command[SetPermissionParams, Response[EmptyResponse]]
SetWindowBoundsCommand = Command[SetWindowBoundsParams, Response[EmptyResponse]]
