from typing import Optional

from pydoll.constants import WindowState
from pydoll.protocol.base import Command, Response
from pydoll.protocol.target.methods import TargetMethod
from pydoll.protocol.target.params import (
    ActivateTargetParams,
    AttachToBrowserTargetParams,
    AttachToTargetParams,
    CloseTargetParams,
    CreateBrowserContextParams,
    CreateTargetParams,
    DetachFromTargetParams,
    DisposeBrowserContextParams,
    GetTargetInfoParams,
    GetTargetsParams,
    RemoteLocation,
    SetAutoAttachParams,
    SetDiscoverTargetsParams,
    SetRemoteLocationsParams,
)
from pydoll.protocol.target.responses import (
    AttachToBrowserTargetResponse,
    AttachToTargetResponse,
    CreateBrowserContextResponse,
    CreateTargetResponse,
    GetBrowserContextsResponse,
    GetTargetInfoResponse,
    GetTargetsResponse,
)


class TargetCommands:
    """
    A class for managing browser targets using Chrome DevTools Protocol.

    The Target domain of CDP supports additional targets discovery and allows to attach to them.
    Targets can represent browser tabs, windows, frames, web workers, service workers, etc.
    The domain provides methods to create, discover, and control these targets.

    This class provides methods to create commands for interacting with browser targets,
    including creating, activating, attaching to, and closing targets through CDP commands.
    """

    @staticmethod
    def activate_target(target_id: str) -> Command[Response]:
        """
        Generates a command to activate (focus) a target.

        Args:
            target_id: ID of the target to activate.

        Returns:
            Command: The CDP command to activate the target.
        """
        params = ActivateTargetParams(targetId=target_id)
        return Command(method=TargetMethod.ACTIVATE_TARGET, params=params)

    @staticmethod
    def attach_to_target(
        target_id: str, flatten: Optional[bool] = None
    ) -> Command[AttachToTargetResponse]:
        """
        Generates a command to attach to a target with the given ID.

        When attached to a target, you can send commands to it and receive events from it.
        This is essential for controlling and automating targets like browser tabs.

        Args:
            target_id: ID of the target to attach to.
            flatten: If true, enables "flat" access to the session via specifying sessionId
                    attribute in the commands. This is recommended as the non-flattened
                    mode is being deprecated. See https://crbug.com/991325

        Returns:
            Command: The CDP command to attach to the target, which will return a sessionId.
        """
        params = AttachToTargetParams(targetId=target_id)
        if flatten is not None:
            params['flatten'] = flatten
        return Command(method=TargetMethod.ATTACH_TO_TARGET, params=params)

    @staticmethod
    def close_target(target_id: str) -> Command[Response]:
        """
        Generates a command to close a target.

        If the target is a page or a tab, it will be closed. This is equivalent to
        clicking the close button on a browser tab.

        Args:
            target_id: ID of the target to close.

        Returns:
            Command: The CDP command to close the target, which will return a success flag.
        """
        params = CloseTargetParams(targetId=target_id)
        return Command(method=TargetMethod.CLOSE_TARGET, params=params)

    @staticmethod
    def create_browser_context(
        dispose_on_detach: Optional[bool] = None,
        proxy_server: Optional[str] = None,
        proxy_bypass_list: Optional[str] = None,
        origins_with_universal_network_access: Optional[list[str]] = None,
    ) -> Command[CreateBrowserContextResponse]:
        """
        Generates a command to create a new empty browser context.

        A browser context is similar to an incognito profile but you can have more than one.
        Each context has its own set of cookies, local storage, and other browser data.
        This is useful for testing multiple users or isolating sessions.

        Args:
            dispose_on_detach: If specified, the context will be disposed when the
                              debugging session disconnects.
            proxy_server: Proxy server string, similar to the one passed to --proxy-server
                         command line argument (e.g., "socks5://192.168.1.100:1080").
            proxy_bypass_list: Proxy bypass list, similar to the one passed to
                               --proxy-bypass-list command line argument
                               (e.g., "*.example.com,localhost").
            origins_with_universal_network_access: An optional list of origins to grant
                                                  unlimited cross-origin access to.
                                                  Parts of the URL other than those
                                                  constituting origin are ignored.

        Returns:
            Command: The CDP command to create a browser context, which will return
                    the ID of the created context.
        """
        params = CreateBrowserContextParams()
        if dispose_on_detach is not None:
            params['disposeOnDetach'] = dispose_on_detach
        if proxy_server is not None:
            params['proxyServer'] = proxy_server
        if proxy_bypass_list is not None:
            params['proxyBypassList'] = proxy_bypass_list
        if origins_with_universal_network_access is not None:
            params['originsWithUniversalNetworkAccess'] = origins_with_universal_network_access
        return Command(method=TargetMethod.CREATE_BROWSER_CONTEXT, params=params)

    @staticmethod
    def create_target(  # noqa: PLR0913, PLR0917
        url: str,
        left: Optional[int] = None,
        top: Optional[int] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        window_state: Optional[WindowState] = None,
        browser_context_id: Optional[str] = None,
        enable_begin_frame_control: Optional[bool] = None,
        new_window: Optional[bool] = None,
        background: Optional[bool] = None,
        for_tab: Optional[bool] = None,
        hidden: Optional[bool] = None,
    ) -> Command[CreateTargetResponse]:
        """
        Generates a command to create a new page (target).

        This is one of the primary methods to open a new tab or window with specific
        properties such as position, size, and browser context.

        Args:
            url: The initial URL the page will navigate to. An empty string indicates about:blank.
            left: Frame left position in device-independent pixels (DIP).
                 Requires newWindow to be true or in headless mode.
            top: Frame top position in DIP. Requires newWindow to be true or in headless mode.
            width: Frame width in DIP.
            height: Frame height in DIP.
            window_state: Frame window state: normal, minimized, maximized, or fullscreen.
                         Default is normal.
            browser_context_id: The browser context to create the page in.
                               If not specified, the default browser context is used.
            enable_begin_frame_control: Whether BeginFrames for this target will be controlled
                                       via DevTools (headless shell only, not supported on
                                       MacOS yet, false by default).
            new_window: Whether to create a new window or tab (false by default,
                       not supported by headless shell).
            background: Whether to create the target in background or foreground
                       (false by default, not supported by headless shell).
            for_tab: Whether to create the target of type "tab".
            hidden: Whether to create a hidden target. The hidden target is observable via
                   protocol, but not present in the tab UI strip. Cannot be created with
                   forTab:true, newWindow:true or background:false. The life-time of the
                   tab is limited to the life-time of the session.

        Returns:
            Command: The CDP command to create a target, which will return the ID
                of the created target.
        """
        params = CreateTargetParams(url=url)
        if left is not None:
            params['left'] = left
        if top is not None:
            params['top'] = top
        if width is not None:
            params['width'] = width
        if height is not None:
            params['height'] = height
        if window_state is not None:
            params['windowState'] = window_state
        if browser_context_id is not None:
            params['browserContextId'] = browser_context_id
        if enable_begin_frame_control is not None:
            params['enableBeginFrameControl'] = enable_begin_frame_control
        if new_window is not None:
            params['newWindow'] = new_window
        if background is not None:
            params['background'] = background
        if for_tab is not None:
            params['forTab'] = for_tab
        if hidden is not None:
            params['hidden'] = hidden
        return Command(method=TargetMethod.CREATE_TARGET, params=params)

    @staticmethod
    def detach_from_target(session_id: Optional[str] = None) -> Command[Response]:
        """
        Generates a command to detach a session from its target.

        After detaching, you will no longer receive events from the target and
        cannot send commands to it.

        Args:
            session_id: Session ID to detach. If not specified, detaches all sessions.

        Returns:
            Command: The CDP command to detach from the target.
        """
        params = DetachFromTargetParams()
        if session_id is not None:
            params['sessionId'] = session_id
        return Command(method=TargetMethod.DETACH_FROM_TARGET, params=params)

    @staticmethod
    def dispose_browser_context(browser_context_id: str) -> Command[Response]:
        """
        Generates a command to delete a browser context.

        All pages belonging to the browser context will be closed without calling
        their beforeunload hooks. This is similar to closing an incognito profile.

        Args:
            browser_context_id: The ID of the browser context to dispose.

        Returns:
            Command: The CDP command to dispose the browser context.
        """
        params = DisposeBrowserContextParams(browserContextId=browser_context_id)
        return Command(method=TargetMethod.DISPOSE_BROWSER_CONTEXT, params=params)

    @staticmethod
    def get_browser_contexts() -> Command[GetBrowserContextsResponse]:
        """
        Generates a command to get all browser contexts created with createBrowserContext.

        This is useful for obtaining a list of all available contexts for managing
        multiple isolated browser sessions.

        Returns:
            Command: The CDP command to get all browser contexts, which will return
                    an array of browser context IDs.
        """
        return Command(method=TargetMethod.GET_BROWSER_CONTEXTS, params={})

    @staticmethod
    def get_targets(filter: Optional[list] = None) -> Command[GetTargetsResponse]:
        """
        Generates a command to retrieve a list of available targets.

        Targets include tabs, extensions, web workers, and other attachable entities
        in the browser. This is useful for discovering what targets exist before
        attaching to them.

        Args:
            filter: Only targets matching the filter will be reported. If filter is not
                   specified and target discovery is currently enabled, a filter used for
                   target discovery is used for consistency.

        Returns:
            Command: The CDP command to get targets, which will return a list of
                    TargetInfo objects with details about each target.
        """
        params = GetTargetsParams()
        if filter is not None:
            params['filter'] = filter
        return Command(method=TargetMethod.GET_TARGETS, params=params)

    @staticmethod
    def set_auto_attach(
        auto_attach: bool,
        wait_for_debugger_on_start: Optional[bool] = None,
        flatten: Optional[bool] = None,
        filter: Optional[list] = None,
    ) -> Command[Response]:
        """
        Generates a command to control whether to automatically attach to new targets.

        This method controls whether to automatically attach to new targets which are
        considered to be directly related to the current one (for example, iframes or workers).
        When turned on, it also attaches to all existing related targets. When turned off,
        it automatically detaches from all currently attached targets.

        Args:
            auto_attach: Whether to auto-attach to related targets.
            wait_for_debugger_on_start: Whether to pause new targets when attaching to them.
                                       Use Runtime.runIfWaitingForDebugger to run paused targets.
            flatten: Enables "flat" access to the session via specifying sessionId attribute
                    in the commands. This mode is being preferred, and non-flattened mode
                    is being deprecated (see crbug.com/991325).
            filter: Only targets matching filter will be attached.

        Returns:
            Command: The CDP command to set auto-attach behavior.
        """
        params = SetAutoAttachParams(autoAttach=auto_attach)
        if wait_for_debugger_on_start is not None:
            params['waitForDebuggerOnStart'] = wait_for_debugger_on_start
        if flatten is not None:
            params['flatten'] = flatten
        if filter is not None:
            params['filter'] = filter
        return Command(method=TargetMethod.SET_AUTO_ATTACH, params=params)

    @staticmethod
    def set_discover_targets(discover: bool, filter: Optional[list] = None) -> Command[Response]:
        """
        Generates a command to control target discovery.

        This method controls whether to discover available targets and notify via
        targetCreated/targetInfoChanged/targetDestroyed events. Target discovery is useful
        for monitoring when new tabs, workers, or other targets are created or destroyed.

        Args:
            discover: Whether to discover available targets.
            filter: Only targets matching filter will be discovered. If discover is false,
                   filter must be omitted or empty.

        Returns:
            Command: The CDP command to set target discovery.
        """
        params = SetDiscoverTargetsParams(discover=discover)
        if filter is not None:
            params['filter'] = filter
        return Command(method=TargetMethod.SET_DISCOVER_TARGETS, params=params)

    @staticmethod
    def attach_to_browser_target(session_id: str) -> Command[AttachToBrowserTargetResponse]:
        """
        Generates a command to attach to the browser target.

        This is an experimental method that attaches to the browser target,
        only using flat sessionId mode. The browser target is a special target that
        represents the browser itself rather than a page or other content.

        Args:
            session_id: ID of the session to attach to the browser target.

        Returns:
            Command: The CDP command to attach to the browser target,
                    which will return a new session ID.
        """
        params = AttachToBrowserTargetParams(sessionId=session_id)
        return Command(method=TargetMethod.ATTACH_TO_BROWSER_TARGET, params=params)

    @staticmethod
    def get_target_info(target_id: str) -> Command[GetTargetInfoResponse]:
        """
        Generates a command to get information about a specific target.

        This experimental method returns detailed information about a target,
        such as its type, URL, title, and other properties.

        Args:
            target_id: ID of the target to get information about.

        Returns:
            Command: The CDP command to get target information, which will return
                    a TargetInfo object with details about the target.
        """
        params = GetTargetInfoParams(targetId=target_id)
        return Command(method=TargetMethod.GET_TARGET_INFO, params=params)

    @staticmethod
    def set_remote_locations(locations: list[RemoteLocation]) -> Command[Response]:
        """
        Generates a command to enable target discovery for specified remote locations.

        This experimental method enables target discovery for remote locations when
        setDiscoverTargets was set to true. This is useful for discovering targets
        on remote devices or in different browser instances.

        Args:
            locations: list of remote locations, each containing a host and port.

        Returns:
            Command: The CDP command to set remote locations for target discovery.
        """
        params = SetRemoteLocationsParams(locations=locations)
        return Command(method=TargetMethod.SET_REMOTE_LOCATIONS, params=params)
