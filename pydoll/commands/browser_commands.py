from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from pydoll.protocol.base import Command
from pydoll.protocol.browser.methods import (
    AddPrivacySandboxCoordinatorKeyConfigParams,
    AddPrivacySandboxEnrollmentOverrideParams,
    BrowserMethod,
    CancelDownloadParams,
    ExecuteBrowserCommandParams,
    GetHistogramParams,
    GetHistogramsParams,
    GetWindowBoundsParams,
    GetWindowForTargetParams,
    GrantPermissionsParams,
    ResetPermissionsParams,
    SetContentsSizeParams,
    SetDockTileParams,
    SetDownloadBehaviorParams,
    SetPermissionParams,
    SetWindowBoundsParams,
)
from pydoll.protocol.browser.types import (
    Bounds,
    WindowState,
)

if TYPE_CHECKING:
    from pydoll.protocol.browser.methods import (
        AddPrivacySandboxCoordinatorKeyConfigCommand,
        AddPrivacySandboxEnrollmentOverrideCommand,
        CancelDownloadCommand,
        CloseCommand,
        CrashCommand,
        CrashGpuProcessCommand,
        DownloadBehavior,
        ExecuteBrowserCommandCommand,
        GetBrowserCommandLineCommand,
        GetHistogramCommand,
        GetHistogramsCommand,
        GetVersionCommand,
        GetWindowBoundsCommand,
        GetWindowForTargetCommand,
        GrantPermissionsCommand,
        ResetPermissionsCommand,
        SetContentsSizeCommand,
        SetDockTileCommand,
        SetDownloadBehaviorCommand,
        SetPermissionCommand,
        SetWindowBoundsCommand,
    )
    from pydoll.protocol.browser.types import (
        BrowserCommandId,
        BrowserContextID,
        PermissionDescriptor,
        PermissionSetting,
        PermissionType,
        PrivacySandboxAPI,
        WindowID,
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
    def get_version() -> GetVersionCommand:
        """
        Generates a command to get browser version information.

        Returns:
            GetVersionCommand: The CDP command that returns browser version details
                including protocol version, product name, revision, and user agent.
        """
        return Command(method=BrowserMethod.GET_VERSION)

    @staticmethod
    def get_browser_command_line() -> GetBrowserCommandLineCommand:
        """
        Returns the command line switches for the browser process.

        Returns:
            GetBrowserCommandLineCommand: The CDP command that returns command line arguments.

        Note: Only works if --enable-automation is on the command line.
        """
        return Command(method=BrowserMethod.GET_BROWSER_COMMAND_LINE)

    @staticmethod
    def get_histograms(
        query: Optional[str] = None,
        delta: bool = False,
    ) -> GetHistogramsCommand:
        """
        Get Chrome histograms.

        Args:
            query: Requested substring in name. Only histograms which have query as a
                   substring in their name are extracted. An empty or absent query returns
                   all histograms.
            delta: If true, retrieve delta since last delta call.

        Returns:
            GetHistogramsCommand: The CDP command that returns histogram data.
        """
        params = GetHistogramsParams()
        if query is not None:
            params['query'] = query
        if delta:
            params['delta'] = delta
        return Command(method=BrowserMethod.GET_HISTOGRAMS, params=params)

    @staticmethod
    def get_histogram(
        name: str,
        delta: bool = False,
    ) -> GetHistogramCommand:
        """
        Get a Chrome histogram by name.

        Args:
            name: Requested histogram name.
            delta: If true, retrieve delta since last delta call.

        Returns:
            GetHistogramCommand: The CDP command that returns histogram data.
        """
        params = GetHistogramParams(name=name)
        if delta:
            params['delta'] = delta
        return Command(method=BrowserMethod.GET_HISTOGRAM, params=params)

    @staticmethod
    def get_window_bounds(window_id: WindowID) -> GetWindowBoundsCommand:
        """
        Get position and size of the browser window.

        Args:
            window_id: Browser window id.

        Returns:
            GetWindowBoundsCommand: The CDP command that returns window bounds information.
        """
        params = GetWindowBoundsParams(windowId=window_id)
        return Command(method=BrowserMethod.GET_WINDOW_BOUNDS, params=params)

    @staticmethod
    def get_window_for_target(
        target_id: Optional[str] = None,
    ) -> GetWindowForTargetCommand:
        """
        Get the browser window that contains the devtools target.

        Args:
            target_id: Devtools agent host id. If called as a part of the session,
                      associated targetId is used.

        Returns:
            GetWindowForTargetCommand: The CDP command that returns window information
                including windowId and bounds.
        """
        params = GetWindowForTargetParams()
        if target_id is not None:
            params['targetId'] = target_id
        return Command(method=BrowserMethod.GET_WINDOW_FOR_TARGET, params=params)

    @staticmethod
    def set_window_bounds(window_id: WindowID, bounds: Bounds) -> SetWindowBoundsCommand:
        """
        Set position and/or size of the browser window.

        Args:
            window_id: Browser window id.
            bounds: New window bounds. The 'minimized', 'maximized' and 'fullscreen' states
                   cannot be combined with 'left', 'top', 'width' or 'height'. Leaves
                   unspecified fields unchanged.

        Returns:
            SetWindowBoundsCommand: The CDP command that sets window bounds.
        """
        params = SetWindowBoundsParams(windowId=window_id, bounds=bounds)
        return Command(method=BrowserMethod.SET_WINDOW_BOUNDS, params=params)

    @staticmethod
    def set_contents_size(
        window_id: WindowID,
        width: Optional[int] = None,
        height: Optional[int] = None,
    ) -> SetContentsSizeCommand:
        """
        Set size of the browser contents resizing browser window as necessary.

        Args:
            window_id: Browser window id.
            width: The window contents width in DIP. Assumes current width if omitted.
                  Must be specified if 'height' is omitted.
            height: The window contents height in DIP. Assumes current height if omitted.
                   Must be specified if 'width' is omitted.

        Returns:
            SetContentsSizeCommand: The CDP command that sets window contents size.
        """
        params = SetContentsSizeParams(windowId=window_id)
        if width is not None:
            params['width'] = width
        if height is not None:
            params['height'] = height
        return Command(method=BrowserMethod.SET_CONTENTS_SIZE, params=params)

    @staticmethod
    def set_dock_tile(
        badge_label: Optional[str] = None,
        image: Optional[str] = None,
    ) -> SetDockTileCommand:
        """
        Set dock tile details, platform-specific.

        Args:
            badge_label: Optional badge label.
            image: Png encoded image (base64 string when passed over JSON).

        Returns:
            SetDockTileCommand: The CDP command that sets dock tile details.
        """
        params = SetDockTileParams()
        if badge_label is not None:
            params['badgeLabel'] = badge_label
        if image is not None:
            params['image'] = image
        return Command(method=BrowserMethod.SET_DOCK_TILE, params=params)

    @staticmethod
    def execute_browser_command(command_id: BrowserCommandId) -> ExecuteBrowserCommandCommand:
        """
        Invoke custom browser commands used by telemetry.

        Args:
            command_id: Browser command identifier.

        Returns:
            ExecuteBrowserCommandCommand: The CDP command that executes browser command.
        """
        params = ExecuteBrowserCommandParams(commandId=command_id)
        return Command(method=BrowserMethod.EXECUTE_BROWSER_COMMAND, params=params)

    @staticmethod
    def add_privacy_sandbox_enrollment_override(
        url: str,
    ) -> AddPrivacySandboxEnrollmentOverrideCommand:
        """
        Allows a site to use privacy sandbox features that require enrollment
        without the site actually being enrolled. Only supported on page targets.

        Args:
            url: Site URL.

        Returns:
            AddPrivacySandboxEnrollmentOverrideCommand: The CDP command that adds enrollment
            override.
        """
        params = AddPrivacySandboxEnrollmentOverrideParams(url=url)
        return Command(method=BrowserMethod.ADD_PRIVACY_SANDBOX_ENROLLMENT_OVERRIDE, params=params)

    @staticmethod
    def add_privacy_sandbox_coordinator_key_config(
        api: PrivacySandboxAPI,
        coordinator_origin: str,
        key_config: str,
        browser_context_id: Optional[BrowserContextID] = None,
    ) -> AddPrivacySandboxCoordinatorKeyConfigCommand:
        """
        Configures encryption keys used with a given privacy sandbox API to talk
        to a trusted coordinator. Since this is intended for test automation only,
        coordinatorOrigin must be a .test domain. No existing coordinator
        configuration for the origin may exist.

        Args:
            api: Privacy Sandbox API type.
            coordinator_origin: Coordinator origin (must be .test domain).
            key_config: Key configuration string.
            browser_context_id: BrowserContext to perform the action in. When omitted,
                               default browser context is used.

        Returns:
            AddPrivacySandboxCoordinatorKeyConfigCommand: The CDP command that adds key config.
        """
        params = AddPrivacySandboxCoordinatorKeyConfigParams(
            api=api,
            coordinatorOrigin=coordinator_origin,
            keyConfig=key_config,
        )
        if browser_context_id is not None:
            params['browserContextId'] = browser_context_id
        return Command(
            method=BrowserMethod.ADD_PRIVACY_SANDBOX_COORDINATOR_KEY_CONFIG, params=params
        )

    @staticmethod
    def set_permission(
        permission: PermissionDescriptor,
        setting: PermissionSetting,
        origin: Optional[str] = None,
        browser_context_id: Optional[BrowserContextID] = None,
    ) -> SetPermissionCommand:
        """
        Set permission settings for given origin.

        Args:
            permission: Descriptor of permission to override.
            setting: Setting of the permission.
            origin: Origin the permission applies to, all origins if not specified.
            browser_context_id: Context to override. When omitted, default browser context is used.

        Returns:
            SetPermissionCommand: The CDP command that sets permission.
        """
        params = SetPermissionParams(permission=permission, setting=setting)
        if origin is not None:
            params['origin'] = origin
        if browser_context_id is not None:
            params['browserContextId'] = browser_context_id
        return Command(method=BrowserMethod.SET_PERMISSION, params=params)

    @staticmethod
    def grant_permissions(
        permissions: list['PermissionType'],
        origin: Optional[str] = None,
        browser_context_id: Optional['BrowserContextID'] = None,
    ) -> GrantPermissionsCommand:
        """
        Grant specific permissions to the given origin and reject all others.

        Args:
            permissions: List of permissions to grant.
            origin: Origin the permission applies to, all origins if not specified.
            browser_context_id: BrowserContext to override permissions. When omitted,
                               default browser context is used.

        Returns:
            GrantPermissionsCommand: The CDP command that grants permissions.
        """
        params = GrantPermissionsParams(permissions=permissions)
        if origin is not None:
            params['origin'] = origin
        if browser_context_id is not None:
            params['browserContextId'] = browser_context_id
        return Command(method=BrowserMethod.GRANT_PERMISSIONS, params=params)

    @staticmethod
    def reset_permissions(
        browser_context_id: Optional['BrowserContextID'] = None,
    ) -> ResetPermissionsCommand:
        """
        Reset all permission management for all origins.

        Args:
            browser_context_id: BrowserContext to reset permissions. When omitted,
                               default browser context is used.

        Returns:
            ResetPermissionsCommand: The CDP command that resets permissions.
        """
        params = ResetPermissionsParams()
        if browser_context_id is not None:
            params['browserContextId'] = browser_context_id
        return Command(method=BrowserMethod.RESET_PERMISSIONS, params=params)

    @staticmethod
    def set_download_behavior(
        behavior: DownloadBehavior,
        browser_context_id: Optional['BrowserContextID'] = None,
        download_path: Optional[str] = None,
        events_enabled: bool = False,
    ) -> SetDownloadBehaviorCommand:
        """
        Set the behavior when downloading a file.

        Args:
            behavior: Whether to allow all or deny all download requests, or use default
                     Chrome behavior if available (otherwise deny). allowAndName allows
                     download and names files according to their download guids.
            browser_context_id: BrowserContext to set download behavior. When omitted,
                               default browser context is used.
            download_path: The default path to save downloaded files to. This is required
                          if behavior is set to 'allow' or 'allowAndName'.
            events_enabled: Whether to emit download events (defaults to false).

        Returns:
            SetDownloadBehaviorCommand: The CDP command that sets download behavior.
        """
        params = SetDownloadBehaviorParams(behavior=behavior)
        if browser_context_id is not None:
            params['browserContextId'] = browser_context_id
        if download_path is not None:
            params['downloadPath'] = download_path
        if events_enabled is not None:
            params['eventsEnabled'] = events_enabled
        return Command(method=BrowserMethod.SET_DOWNLOAD_BEHAVIOR, params=params)

    @staticmethod
    def cancel_download(
        guid: str,
        browser_context_id: Optional['BrowserContextID'] = None,
    ) -> CancelDownloadCommand:
        """
        Cancel a download if in progress.

        Args:
            guid: Global unique identifier of the download.
            browser_context_id: BrowserContext to perform the action in. When omitted,
                               default browser context is used.

        Returns:
            CancelDownloadCommand: The CDP command that cancels download.
        """
        params = CancelDownloadParams(guid=guid)
        if browser_context_id is not None:
            params['browserContextId'] = browser_context_id
        return Command(method=BrowserMethod.CANCEL_DOWNLOAD, params=params)

    @staticmethod
    def close() -> CloseCommand:
        """
        Close browser gracefully.

        Returns:
            CloseCommand: The CDP command that closes the browser.
        """
        return Command(method=BrowserMethod.CLOSE)

    @staticmethod
    def crash() -> CrashCommand:
        """
        Crashes browser on the main thread.

        Returns:
            CrashCommand: The CDP command that crashes the browser.
        """
        return Command(method=BrowserMethod.CRASH)

    @staticmethod
    def crash_gpu_process() -> CrashGpuProcessCommand:
        """
        Crashes GPU process.

        Returns:
            CrashGpuProcessCommand: The CDP command that crashes the GPU process.
        """
        return Command(method=BrowserMethod.CRASH_GPU_PROCESS)

    # Helper methods for common window operations
    @staticmethod
    def set_window_maximized(window_id: WindowID) -> SetWindowBoundsCommand:
        """
        Maximize a browser window.

        Args:
            window_id: Browser window id.

        Returns:
            SetWindowBoundsCommand: The CDP command that maximizes the window.
        """
        bounds = Bounds(windowState=WindowState.MAXIMIZED)
        return BrowserCommands.set_window_bounds(window_id, bounds)

    @staticmethod
    def set_window_minimized(window_id: WindowID) -> SetWindowBoundsCommand:
        """
        Minimize a browser window.

        Args:
            window_id: Browser window id.

        Returns:
            SetWindowBoundsCommand: The CDP command that minimizes the window.
        """
        bounds = Bounds(windowState=WindowState.MINIMIZED)
        return BrowserCommands.set_window_bounds(window_id, bounds)

    @staticmethod
    def set_window_fullscreen(window_id: WindowID) -> SetWindowBoundsCommand:
        """
        Set a browser window to fullscreen.

        Args:
            window_id: Browser window id.

        Returns:
            SetWindowBoundsCommand: The CDP command that sets window to fullscreen.
        """
        bounds = Bounds(windowState=WindowState.FULLSCREEN)
        return BrowserCommands.set_window_bounds(window_id, bounds)

    @staticmethod
    def set_window_normal(window_id: WindowID) -> SetWindowBoundsCommand:
        """
        Set a browser window to normal state.

        Args:
            window_id: Browser window id.

        Returns:
            SetWindowBoundsCommand: The CDP command that sets window to normal state.
        """
        bounds = Bounds(windowState=WindowState.NORMAL)
        return BrowserCommands.set_window_bounds(window_id, bounds)
