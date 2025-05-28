from typing import List, Optional

from pydoll.constants import (
    DownloadBehavior,
    PermissionType,
    WindowState,
)
from pydoll.protocol.base import Command, Response
from pydoll.protocol.browser.methods import BrowserMethod
from pydoll.protocol.browser.params import (
    CancelDownloadParams,
    GetWindowForTargetParams,
    GrantPermissionsParams,
    ResetPermissionsParams,
    SetDownloadBehaviorParams,
    SetWindowBoundsParams,
    WindowBoundsDict,
)
from pydoll.protocol.browser.responses import (
    GetVersionResponse,
    GetWindowForTargetResponse,
)


class BrowserCommands:
    """
    BrowserCommands class provides a set of commands to interact with the
    browser's main functionality based on CDP. These commands allow for
    managing browser windows, such as closing windows, retrieving window IDs,
    and adjusting window bounds (size and state).

    The commands defined in this class provide functionality for:
    - Managing browser windows and targets.
    - Setting permissions and download behavior.
    - Controlling browser windows (size, state).
    - Retrieving browser information and versioning.
    """

    @staticmethod
    def get_version() -> Command[GetVersionResponse]:
        """
        Generates a command to get browser version information.

        Returns:
            Command[GetVersionResponse]: The CDP command that returns browser version details
                including protocol version, product name, revision, and user agent.
        """
        return Command(method=BrowserMethod.GET_VERSION)

    @staticmethod
    def reset_permissions(
        browser_context_id: Optional[str] = None,
    ) -> Command[Response]:
        """
        Generates a command to reset all permissions.

        Args:
            browser_context_id (Optional[str]): The browser context to reset permissions for.
                If not specified, resets permissions for the default context.

        Returns:
            Command[Response]: The CDP command that returns a basic success response.
        """
        params = ResetPermissionsParams()
        if browser_context_id:
            params['browserContextId'] = browser_context_id
        return Command(method=BrowserMethod.RESET_PERMISSIONS, params=params)

    @staticmethod
    def cancel_download(guid: str, browser_context_id: Optional[str] = None) -> Command[Response]:
        """
        Generates a command to cancel a download.

        Args:
            guid (str): Global unique identifier of the download.
            browser_context_id (Optional[str]): The browser context the download belongs to.
                If not specified, uses the default context.

        Returns:
            Command[Response]: The CDP command that returns a basic success response.
        """
        params = CancelDownloadParams(guid=guid)
        if browser_context_id:
            params['browserContextId'] = browser_context_id
        return Command(method=BrowserMethod.CANCEL_DOWNLOAD, params=params)

    @staticmethod
    def crash() -> Command[Response]:
        """
        Generates a command to crash the browser main process.

        Returns:
            Command[Response]: The CDP command that returns a basic success response
                before crashing the browser.
        """
        return Command(method=BrowserMethod.CRASH)

    @staticmethod
    def crash_gpu_process() -> Command[Response]:
        """
        Generates a command to crash the browser GPU process.

        Returns:
            Command[Response]: The CDP command that returns a basic success response
                before crashing the GPU process.
        """
        return Command(method=BrowserMethod.CRASH_GPU_PROCESS)

    @staticmethod
    def set_download_behavior(
        behavior: DownloadBehavior,
        download_path: Optional[str] = None,
        browser_context_id: Optional[str] = None,
        events_enabled: bool = True,
    ) -> Command[Response]:
        """
        Generates a command to set the download behavior for the browser.

        Args:
            behavior (DownloadBehavior): The behavior to set for downloads.
            download_path (Optional[str]): The path to set for downloads.

        Returns:
            Command[Response]: The CDP command that returns a basic success response
                after setting the download path.
        """
        params = SetDownloadBehaviorParams(behavior=behavior)
        if download_path:
            params['downloadPath'] = download_path
        if browser_context_id:
            params['browserContextId'] = browser_context_id
        if events_enabled:
            params['eventsEnabled'] = events_enabled
        return Command(method=BrowserMethod.SET_DOWNLOAD_BEHAVIOR, params=params)

    @staticmethod
    def close() -> Command[Response]:
        """
        Generates a command to close the browser.

        Returns:
            Command[Response]: The CDP command that returns a basic success response
                before closing the browser.
        """
        return Command(method=BrowserMethod.CLOSE)

    @staticmethod
    def get_window_for_target(
        target_id: str,
    ) -> Command[GetWindowForTargetResponse]:
        """
        Generates a command to get the window for a given target ID.

        Args:
            target_id (str): The target_id to get the window for.

        Returns:
            Command[GetWindowForTargetResponse]: The CDP command that returns window
                information including windowId and bounds.
        """
        params = GetWindowForTargetParams(targetId=target_id)
        return Command(method=BrowserMethod.GET_WINDOW_FOR_TARGET, params=params)

    @staticmethod
    def set_window_bounds(window_id: int, bounds: WindowBoundsDict) -> Command[Response]:
        """
        Generates a command to set the bounds of a window.

        Args:
            window_id (int): The ID of the window to set the bounds for.
            bounds (WindowBoundsDict): The bounds to set for the window,
                which should include windowState and optionally width, height,
                x, and y coordinates.

        Returns:
            Command[Response]: The CDP command that returns a basic success response
                after setting the window bounds.
        """
        params = SetWindowBoundsParams(windowId=window_id, bounds=bounds)
        return Command(method=BrowserMethod.SET_WINDOW_BOUNDS, params=params)

    @staticmethod
    def set_window_maximized(window_id: int) -> Command[Response]:
        """
        Generates a command to maximize a window.

        Args:
            window_id (int): The ID of the window to maximize.

        Returns:
            Command[Response]: The CDP command that returns a basic success response
                after maximizing the window.
        """
        bounds = WindowBoundsDict(windowState=WindowState.MAXIMIZED)
        return BrowserCommands.set_window_bounds(window_id, bounds)

    @staticmethod
    def set_window_minimized(window_id: int) -> Command[Response]:
        """
        Generates a command to minimize a window.

        Args:
            window_id (int): The ID of the window to minimize.

        Returns:
            Command[Response]: The CDP command that returns a basic success response
                after minimizing the window.
        """
        bounds = WindowBoundsDict(windowState=WindowState.MINIMIZED)
        return BrowserCommands.set_window_bounds(window_id, bounds)

    @staticmethod
    def grant_permissions(
        permissions: List[PermissionType],
        origin: Optional[str] = None,
        browser_context_id: Optional[str] = None,
    ) -> Command[Response]:
        """
        Generates a command to grant specific permissions to the given origin.

        Args:
            permissions (List[PermissionType]): List of permissions to grant.
                See PermissionType enum for available permissions.
            origin (Optional[str]): The origin to grant permissions to.
                If not specified, grants for all origins.
            browser_context_id (Optional[str]): The browser context to grant permissions in.
                If not specified, uses the default context.

        Returns:
            Command[Response]: The CDP command that returns a basic success response
                after granting the specified permissions.
        """
        params = GrantPermissionsParams(permissions=permissions)
        if origin:
            params['origin'] = origin

        if browser_context_id:
            params['browserContextId'] = browser_context_id

        return Command(method=BrowserMethod.GRANT_PERMISSIONS, params=params)
