from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from pydoll.protocol.bidi.base import Command
from pydoll.protocol.bidi.browsing_context.methods import (
    ActivateParameters,
    BrowsingContextMethod,
    CaptureScreenshotParameters,
    CloseParameters,
    CreateParameters,
    GetTreeParameters,
    HandleUserPromptParameters,
    LocateNodesParameters,
    NavigateParameters,
    PrintParameters,
    ReloadParameters,
    SetBypassCSPParameters,
    SetViewportParameters,
    TraverseHistoryParameters,
)
from pydoll.protocol.bidi.browsing_context.types import (
    ClipRectangle,
    CreateType,
    ImageFormat,
    Locator,
    PrintMarginParameters,
    PrintPageParameters,
    ReadinessState,
    Viewport,
)

if TYPE_CHECKING:
    from pydoll.protocol.bidi.browsing_context.methods import (
        ActivateCommand,
        CaptureScreenshotCommand,
        CloseCommand,
        CreateCommand,
        GetTreeCommand,
        HandleUserPromptCommand,
        LocateNodesCommand,
        NavigateCommand,
        PrintCommand,
        ReloadCommand,
        SetBypassCSPCommand,
        SetViewportCommand,
        TraverseHistoryCommand,
    )
    from pydoll.protocol.bidi.script.types import SerializationOptions, SharedReference


class BrowsingContextCommands:
    """Command builders for the BiDi browsingContext module."""

    @staticmethod
    def activate(context: str) -> ActivateCommand:
        """Generates a command to activate and focus a top-level context."""
        return Command(
            method=BrowsingContextMethod.ACTIVATE,
            params=ActivateParameters(context=context),
        )

    @staticmethod
    def capture_screenshot(
        context: str,
        origin: Optional[str] = None,
        format: Optional[ImageFormat] = None,
        clip: Optional[ClipRectangle] = None,
    ) -> CaptureScreenshotCommand:
        """Generates a command to capture a screenshot."""
        params = CaptureScreenshotParameters(context=context)
        if origin is not None:
            params['origin'] = origin
        if format is not None:
            params['format'] = format
        if clip is not None:
            params['clip'] = clip
        return Command(method=BrowsingContextMethod.CAPTURE_SCREENSHOT, params=params)

    @staticmethod
    def close(
        context: str,
        prompt_unload: Optional[bool] = None,
    ) -> CloseCommand:
        """Generates a command to close a top-level context."""
        params = CloseParameters(context=context)
        if prompt_unload is not None:
            params['promptUnload'] = prompt_unload
        return Command(method=BrowsingContextMethod.CLOSE, params=params)

    @staticmethod
    def create(
        type: CreateType,
        reference_context: Optional[str] = None,
        background: Optional[bool] = None,
        user_context: Optional[str] = None,
    ) -> CreateCommand:
        """Generates a command to create a new tab or window."""
        params = CreateParameters(type=type)
        if reference_context is not None:
            params['referenceContext'] = reference_context
        if background is not None:
            params['background'] = background
        if user_context is not None:
            params['userContext'] = user_context
        return Command(method=BrowsingContextMethod.CREATE, params=params)

    @staticmethod
    def get_tree(
        max_depth: Optional[int] = None,
        root: Optional[str] = None,
    ) -> GetTreeCommand:
        """Generates a command to get the tree of browsing contexts."""
        params = GetTreeParameters()
        if max_depth is not None:
            params['maxDepth'] = max_depth
        if root is not None:
            params['root'] = root
        return Command(method=BrowsingContextMethod.GET_TREE, params=params)

    @staticmethod
    def handle_user_prompt(
        context: str,
        accept: Optional[bool] = None,
        user_text: Optional[str] = None,
    ) -> HandleUserPromptCommand:
        """Generates a command to handle a user prompt (alert/confirm/prompt)."""
        params = HandleUserPromptParameters(context=context)
        if accept is not None:
            params['accept'] = accept
        if user_text is not None:
            params['userText'] = user_text
        return Command(method=BrowsingContextMethod.HANDLE_USER_PROMPT, params=params)

    @staticmethod
    def locate_nodes(
        context: str,
        locator: Locator,
        max_node_count: Optional[int] = None,
        serialization_options: Optional[SerializationOptions] = None,
        start_nodes: Optional[list[SharedReference]] = None,
    ) -> LocateNodesCommand:
        """Generates a command to locate nodes matching a locator."""
        params = LocateNodesParameters(context=context, locator=locator)
        if max_node_count is not None:
            params['maxNodeCount'] = max_node_count
        if serialization_options is not None:
            params['serializationOptions'] = serialization_options
        if start_nodes is not None:
            params['startNodes'] = start_nodes
        return Command(method=BrowsingContextMethod.LOCATE_NODES, params=params)

    @staticmethod
    def navigate(
        context: str,
        url: str,
        wait: Optional[ReadinessState] = None,
    ) -> NavigateCommand:
        """Generates a command to navigate to a URL."""
        params = NavigateParameters(context=context, url=url)
        if wait is not None:
            params['wait'] = wait
        return Command(method=BrowsingContextMethod.NAVIGATE, params=params)

    @staticmethod
    def print(
        context: str,
        background: Optional[bool] = None,
        margin: Optional[PrintMarginParameters] = None,
        orientation: Optional[str] = None,
        page: Optional[PrintPageParameters] = None,
        page_ranges: Optional[list[int | str]] = None,
        scale: Optional[float] = None,
        shrink_to_fit: Optional[bool] = None,
    ) -> PrintCommand:
        """Generates a command to print a page as PDF."""
        params = PrintParameters(context=context)
        if background is not None:
            params['background'] = background
        if margin is not None:
            params['margin'] = margin
        if orientation is not None:
            params['orientation'] = orientation
        if page is not None:
            params['page'] = page
        if page_ranges is not None:
            params['pageRanges'] = page_ranges
        if scale is not None:
            params['scale'] = scale
        if shrink_to_fit is not None:
            params['shrinkToFit'] = shrink_to_fit
        return Command(method=BrowsingContextMethod.PRINT, params=params)

    @staticmethod
    def reload(
        context: str,
        ignore_cache: Optional[bool] = None,
        wait: Optional[ReadinessState] = None,
    ) -> ReloadCommand:
        """Generates a command to reload the current page."""
        params = ReloadParameters(context=context)
        if ignore_cache is not None:
            params['ignoreCache'] = ignore_cache
        if wait is not None:
            params['wait'] = wait
        return Command(method=BrowsingContextMethod.RELOAD, params=params)

    @staticmethod
    def set_bypass_csp(
        bypass: bool | None,
        contexts: Optional[list[str]] = None,
        user_contexts: Optional[list[str]] = None,
    ) -> SetBypassCSPCommand:
        """Generates a command to bypass Content Security Policy."""
        params = SetBypassCSPParameters(bypass=bypass)
        if contexts is not None:
            params['contexts'] = contexts
        if user_contexts is not None:
            params['userContexts'] = user_contexts
        return Command(method=BrowsingContextMethod.SET_BYPASS_CSP, params=params)

    @staticmethod
    def set_viewport(
        context: Optional[str] = None,
        viewport: Optional[Viewport] = None,
        device_pixel_ratio: Optional[float] = None,
        user_contexts: Optional[list[str]] = None,
    ) -> SetViewportCommand:
        """Generates a command to set viewport dimensions."""
        params = SetViewportParameters()
        if context is not None:
            params['context'] = context
        if viewport is not None:
            params['viewport'] = viewport
        if device_pixel_ratio is not None:
            params['devicePixelRatio'] = device_pixel_ratio
        if user_contexts is not None:
            params['userContexts'] = user_contexts
        return Command(method=BrowsingContextMethod.SET_VIEWPORT, params=params)

    @staticmethod
    def traverse_history(context: str, delta: int) -> TraverseHistoryCommand:
        """Generates a command to traverse browsing history."""
        return Command(
            method=BrowsingContextMethod.TRAVERSE_HISTORY,
            params=TraverseHistoryParameters(context=context, delta=delta),
        )
