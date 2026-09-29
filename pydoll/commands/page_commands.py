from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pydoll.protocol.base import Command
from pydoll.protocol.page.methods import (
    AddCompilationCacheParams,
    AddScriptToEvaluateOnNewDocumentParams,
    CaptureScreenshotParams,
    CaptureSnapshotParams,
    CreateIsolatedWorldParams,
    EnableParams,
    GenerateTestReportParams,
    GetAdScriptAncestryIdsParams,
    GetAppIdParams,
    GetAppManifestParams,
    GetOriginTrialsParams,
    GetPermissionsPolicyStateParams,
    GetResourceContentParams,
    HandleJavaScriptDialogParams,
    NavigateParams,
    NavigateToHistoryEntryParams,
    PageMethod,
    PrintToPDFParams,
    ProduceCompilationCacheParams,
    ReloadParams,
    RemoveScriptToEvaluateOnNewDocumentParams,
    ScreencastFrameAckParams,
    SearchInResourceParams,
    SetAdBlockingEnabledParams,
    SetBypassCSPParams,
    SetDocumentContentParams,
    SetFontFamiliesParams,
    SetFontSizesParams,
    SetInterceptFileChooserDialogParams,
    SetLifecycleEventsEnabledParams,
    SetPrerenderingAllowedParams,
    SetRPHRegistrationModeParams,
    SetSPCTransactionModeParams,
    SetWebLifecycleStateParams,
    StartScreencastParams,
)
from pydoll.protocol.page.types import (
    CompilationCacheParams,
    FontFamilies,
    FontSizes,
    ScriptFontFamilies,
)

if TYPE_CHECKING:
    from pydoll.protocol.page.methods import (
        AddCompilationCacheCommand,
        AddScriptToEvaluateOnNewDocumentCommand,
        BringToFrontCommand,
        CaptureScreenshotCommand,
        CaptureSnapshotCommand,
        ClearCompilationCacheCommand,
        CloseCommand,
        CrashCommand,
        CreateIsolatedWorldCommand,
        DisableCommand,
        EnableCommand,
        GenerateTestReportCommand,
        GetAdScriptAncestryIdsCommand,
        GetAppIdCommand,
        GetAppManifestCommand,
        GetFrameTreeCommand,
        GetInstallabilityErrorsCommand,
        GetLayoutMetricsCommand,
        GetNavigationHistoryCommand,
        GetOriginTrialsCommand,
        GetPermissionsPolicyStateCommand,
        GetResourceContentCommand,
        GetResourceTreeCommand,
        HandleJavaScriptDialogCommand,
        NavigateCommand,
        NavigateToHistoryEntryCommand,
        PrintToPDFCommand,
        ProduceCompilationCacheCommand,
        ReloadCommand,
        RemoveScriptToEvaluateOnNewDocumentCommand,
        ResetNavigationHistoryCommand,
        ScreencastFrameAckCommand,
        SearchInResourceCommand,
        SetAdBlockingEnabledCommand,
        SetBypassCSPCommand,
        SetDocumentContentCommand,
        SetFontFamiliesCommand,
        SetFontSizesCommand,
        SetInterceptFileChooserDialogCommand,
        SetLifecycleEventsEnabledCommand,
        SetPrerenderingAllowedCommand,
        SetRPHRegistrationModeCommand,
        SetSPCTransactionModeCommand,
        SetWebLifecycleStateCommand,
        StartScreencastCommand,
        StopLoadingCommand,
        StopScreencastCommand,
        WaitForDebuggerCommand,
    )
    from pydoll.protocol.page.types import (
        AutoResponseMode,
        ReferrerPolicy,
        ScreencastFormat,
        ScreenshotFormat,
        TransferMode,
        TransitionType,
        Viewport,
        WebLifecycleState,
    )


class PageCommands:
    """
    This class encapsulates the page commands of the Chrome DevTools Protocol (CDP).

    CDP's Page domain allows for interacting with browser pages, including navigation,
    content manipulation, and page state monitoring. These commands provide powerful
    capabilities for web automation, testing, and debugging.

    The commands defined in this class provide functionality for:
    - Navigating to URLs and managing page history
    - Capturing screenshots and generating PDFs
    - Handling JavaScript dialogs
    - Enabling and controlling page events
    - Managing download behavior
    - Manipulating page content and state
    """

    @staticmethod
    def add_script_to_evaluate_on_new_document(
        source: str,
        world_name: str | None = None,
        include_command_line_api: bool | None = None,
        run_immediately: bool | None = None,
    ) -> AddScriptToEvaluateOnNewDocumentCommand:
        """
        Creates a command to add a script that will be evaluated when a new document is created.

        Args:
            source (str): Script source to be evaluated when a new document is created.
            world_name (str | None): If specified, creates an isolated world with the given name.
            include_command_line_api (bool | None): Whether to include command line API.
            run_immediately (bool | None): Whether to run the script immediately on
                existing contexts.

        Returns:
            AddScriptToEvaluateOnNewDocumentCommand: Command object with the identifier
                of the added script.
        """
        params = AddScriptToEvaluateOnNewDocumentParams(source=source)
        if world_name is not None:
            params['worldName'] = world_name
        if include_command_line_api is not None:
            params['includeCommandLineAPI'] = include_command_line_api
        if run_immediately is not None:
            params['runImmediately'] = run_immediately

        return Command(method=PageMethod.ADD_SCRIPT_TO_EVALUATE_ON_NEW_DOCUMENT, params=params)

    @staticmethod
    def bring_to_front() -> BringToFrontCommand:
        """
        Brings the page to front.
        """
        return Command(method=PageMethod.BRING_TO_FRONT)

    @staticmethod
    def capture_screenshot(
        format: ScreenshotFormat | None = None,
        quality: int | None = None,
        clip: Viewport | None = None,
        from_surface: bool | None = None,
        capture_beyond_viewport: bool | None = None,
        optimize_for_speed: bool | None = None,
    ) -> CaptureScreenshotCommand:
        """
        Creates a command to capture a screenshot of the current page.

        Args:
            format (str | None): Image compression format (jpeg, png, or webp).
            quality (int | None): Compression quality from 0-100 (jpeg only).
            clip (Viewport | None): Region of the page to capture.
            from_surface (bool | None): Capture from the surface, not the view.
            capture_beyond_viewport (bool | None): Capture beyond the viewport.
            optimize_for_speed (bool | None): Optimize for speed, not for size.

        Returns:
            CaptureScreenshotCommand: Command object with base64-encoded image data.
        """
        params = CaptureScreenshotParams()
        if format is not None:
            params['format'] = format
        if quality is not None:
            params['quality'] = quality
        if clip is not None:
            params['clip'] = clip
        if from_surface is not None:
            params['fromSurface'] = from_surface
        if capture_beyond_viewport is not None:
            params['captureBeyondViewport'] = capture_beyond_viewport
        if optimize_for_speed is not None:
            params['optimizeForSpeed'] = optimize_for_speed

        return Command(method=PageMethod.CAPTURE_SCREENSHOT, params=params)

    @staticmethod
    def close() -> CloseCommand:
        """
        Creates a command to close the current page.

        Returns:
            CloseCommand: Command object to close the page.
        """
        return Command(method=PageMethod.CLOSE)

    @staticmethod
    def create_isolated_world(
        frame_id: str,
        world_name: str | None = None,
        grant_universal_access: bool | None = None,
    ) -> CreateIsolatedWorldCommand:
        """
        Creates a command to create an isolated world for the given frame.

        Args:
            frame_id (str): ID of the frame in which to create the isolated world.
            world_name (str | None): Name to be reported in the Execution Context.
            grant_universal_access (bool | None): Whether to grant universal access.

        Returns:
            CreateIsolatedWorldCommand: Command object with the execution context ID.
        """
        params = CreateIsolatedWorldParams(frameId=frame_id)
        if world_name is not None:
            params['worldName'] = world_name
        if grant_universal_access is not None:
            params['grantUniveralAccess'] = grant_universal_access

        return Command(method=PageMethod.CREATE_ISOLATED_WORLD, params=params)

    @staticmethod
    def disable() -> DisableCommand:
        """
        Creates a command to disable page domain notifications.

        Returns:
            DisableCommand: Command object to disable the Page domain.
        """
        return Command(method=PageMethod.DISABLE)

    @staticmethod
    def enable(
        enable_file_chooser_opened_event: bool | None = None,
    ) -> EnableCommand:
        """
        Creates a command to enable page domain notifications.

        Args:
            enable_file_chooser_opened_event (bool | None): Whether to emit
                Page.fileChooserOpened event.

        Returns:
            EnableCommand: Command object to enable the Page domain.
        """
        params = EnableParams()
        if enable_file_chooser_opened_event is not None:
            params['enableFileChooserOpenedEvent'] = enable_file_chooser_opened_event

        return Command(method=PageMethod.ENABLE, params=params)

    @staticmethod
    def get_app_manifest(
        manifest_id: str | None = None,
    ) -> GetAppManifestCommand:
        """
        Creates a command to get the manifest for the current document.

        Returns:
            GetAppManifestCommand: Command object with manifest information.
        """
        params = GetAppManifestParams()
        if manifest_id is not None:
            params['manifestId'] = manifest_id
        return Command(method=PageMethod.GET_APP_MANIFEST, params=params)

    @staticmethod
    def get_frame_tree() -> GetFrameTreeCommand:
        """
        Creates a command to get the frame tree for the current page.

        Returns:
            GetFrameTreeCommand: Command object with frame tree information.
        """
        return Command(method=PageMethod.GET_FRAME_TREE)

    @staticmethod
    def get_layout_metrics() -> GetLayoutMetricsCommand:
        """
        Creates a command to get layout metrics for the page.

        Returns:
            GetLayoutMetricsCommand: Command object with layout metrics.
        """
        return Command(method=PageMethod.GET_LAYOUT_METRICS)

    @staticmethod
    def get_navigation_history() -> GetNavigationHistoryCommand:
        """
        Creates a command to get the navigation history for the current page.

        Returns:
            GetNavigationHistoryCommand: Command object with navigation history.
        """
        return Command(method=PageMethod.GET_NAVIGATION_HISTORY)

    @staticmethod
    def handle_javascript_dialog(
        accept: bool, prompt_text: str | None = None
    ) -> HandleJavaScriptDialogCommand:
        """
        Creates a command to handle a JavaScript dialog.

        Args:
            accept (bool): Whether to accept or dismiss the dialog.
            prompt_text (str | None): Text to enter in prompt dialogs.

        Returns:
            HandleJavaScriptDialogCommand: Command object to handle a JavaScript dialog.
        """
        params = HandleJavaScriptDialogParams(accept=accept)
        if prompt_text is not None:
            params['promptText'] = prompt_text

        return Command(method=PageMethod.HANDLE_JAVASCRIPT_DIALOG, params=params)

    @staticmethod
    def navigate(
        url: str,
        referrer: str | None = None,
        transition_type: TransitionType | None = None,
        frame_id: str | None = None,
        referrer_policy: ReferrerPolicy | None = None,
    ) -> NavigateCommand:
        """
        Creates a command to navigate to a specific URL.

        Args:
            url (str): URL to navigate to.
            referrer (str | None): Referrer URL.
            transition_type (str | None): Intended transition type.
            frame_id (str | None): Frame ID to navigate.
            referrer_policy (str | None): Referrer policy.

        Returns:
            NavigateCommand: Command object to navigate to a URL.
        """
        params = NavigateParams(url=url)
        if referrer is not None:
            params['referrer'] = referrer
        if transition_type is not None:
            params['transitionType'] = transition_type
        if frame_id is not None:
            params['frameId'] = frame_id
        if referrer_policy is not None:
            params['referrerPolicy'] = referrer_policy

        return Command(method=PageMethod.NAVIGATE, params=params)

    @staticmethod
    def navigate_to_history_entry(entry_id: int) -> NavigateToHistoryEntryCommand:
        """
        Creates a command to navigate to a specific history entry.

        Args:
            entry_id (int): ID of the history entry to navigate to.

        Returns:
            NavigateToHistoryEntryCommand: Command object to navigate to a history entry.
        """
        params = NavigateToHistoryEntryParams(entryId=entry_id)
        return Command(method=PageMethod.NAVIGATE_TO_HISTORY_ENTRY, params=params)

    @staticmethod
    def print_to_pdf(  # noqa: PLR0912
        landscape: bool | None = None,
        display_header_footer: bool | None = None,
        print_background: bool | None = None,
        scale: float | None = None,
        paper_width: float | None = None,
        paper_height: float | None = None,
        margin_top: float | None = None,
        margin_bottom: float | None = None,
        margin_left: float | None = None,
        margin_right: float | None = None,
        page_ranges: str | None = None,
        header_template: str | None = None,
        footer_template: str | None = None,
        prefer_css_page_size: bool | None = None,
        transfer_mode: TransferMode | None = None,
        generate_tagged_pdf: bool | None = None,
        generate_document_outline: bool | None = None,
    ) -> PrintToPDFCommand:
        """
        Creates a command to print the current page to PDF.

        Args:
            landscape (bool | None): Paper orientation.
            display_header_footer (bool | None): Display header and footer.
            print_background (bool | None): Print background graphics.
            scale (float | None): Scale of the webpage rendering.
            paper_width (float | None): Paper width in inches.
            paper_height (float | None): Paper height in inches.
            margin_top (float | None): Top margin in inches.
            margin_bottom (float | None): Bottom margin in inches.
            margin_left (float | None): Left margin in inches.
            margin_right (float | None): Right margin in inches.
            page_ranges (str | None): Paper ranges to print, e.g., '1-5, 8, 11-13'.
            header_template (str | None): HTML template for the print header.
            footer_template (str | None): HTML template for the print footer.
            prefer_css_page_size (bool | None): Whether to prefer page size as defined by CSS.
            transfer_mode (str | None): Transfer mode.

        Returns:
            PrintToPDFCommand: Command object to print the page to PDF.
        """
        params = PrintToPDFParams()
        if landscape is not None:
            params['landscape'] = landscape
        if display_header_footer is not None:
            params['displayHeaderFooter'] = display_header_footer
        if print_background is not None:
            params['printBackground'] = print_background
        if scale is not None:
            params['scale'] = scale
        if paper_width is not None:
            params['paperWidth'] = paper_width
        if paper_height is not None:
            params['paperHeight'] = paper_height
        if margin_top is not None:
            params['marginTop'] = margin_top
        if margin_bottom is not None:
            params['marginBottom'] = margin_bottom
        if margin_left is not None:
            params['marginLeft'] = margin_left
        if margin_right is not None:
            params['marginRight'] = margin_right
        if page_ranges is not None:
            params['pageRanges'] = page_ranges
        if header_template is not None:
            params['headerTemplate'] = header_template
        if footer_template is not None:
            params['footerTemplate'] = footer_template
        if prefer_css_page_size is not None:
            params['preferCSSPageSize'] = prefer_css_page_size
        if transfer_mode is not None:
            params['transferMode'] = transfer_mode
        if generate_tagged_pdf is not None:
            params['generateTaggedPDF'] = generate_tagged_pdf
        if generate_document_outline is not None:
            params['generateDocumentOutline'] = generate_document_outline

        return Command(method=PageMethod.PRINT_TO_PDF, params=params)

    @staticmethod
    def reload(
        ignore_cache: bool | None = None,
        script_to_evaluate_on_load: str | None = None,
        loader_id: str | None = None,
    ) -> ReloadCommand:
        """
        Creates a command to reload the current page.

        Args:
            ignore_cache (bool | None): If true, browser cache is ignored.
            script_to_evaluate_on_load (str | None): Script to be injected into the page on load.

        Returns:
            ReloadCommand: Command object to reload the page.
        """
        params = ReloadParams()
        if ignore_cache is not None:
            params['ignoreCache'] = ignore_cache
        if script_to_evaluate_on_load is not None:
            params['scriptToEvaluateOnLoad'] = script_to_evaluate_on_load
        if loader_id is not None:
            params['loaderId'] = loader_id

        return Command(method=PageMethod.RELOAD, params=params)

    @staticmethod
    def reset_navigation_history() -> ResetNavigationHistoryCommand:
        """
        Creates a command to reset the navigation history.
        """
        return Command(method=PageMethod.RESET_NAVIGATION_HISTORY)

    @staticmethod
    def remove_script_to_evaluate_on_new_document(
        identifier: str,
    ) -> RemoveScriptToEvaluateOnNewDocumentCommand:
        """
        Creates a command to remove a script that was added to be evaluated on new documents.

        Args:
            identifier (str): Identifier of the script to remove.

        Returns:
            RemoveScriptToEvaluateOnNewDocumentCommand: Command object to remove a script.
        """
        params = RemoveScriptToEvaluateOnNewDocumentParams(identifier=identifier)
        return Command(method=PageMethod.REMOVE_SCRIPT_TO_EVALUATE_ON_NEW_DOCUMENT, params=params)

    @staticmethod
    def set_bypass_csp(enabled: bool) -> SetBypassCSPCommand:
        """
        Creates a command to toggle bypassing page CSP.

        Args:
            enabled (bool): Whether to bypass page CSP.

        Returns:
            SetBypassCSPCommand: Command object to toggle bypassing page CSP.
        """
        params = SetBypassCSPParams(enabled=enabled)
        return Command(method=PageMethod.SET_BYPASS_CSP, params=params)

    @staticmethod
    def set_document_content(frame_id: str, html: str) -> SetDocumentContentCommand:
        """
        Creates a command to set the document content of a frame.

        Args:
            frame_id (str): Frame ID to set the document content for.
            html (str): HTML content to set.

        Returns:
            SetDocumentContentCommand: Command object to set the document content.
        """
        params = SetDocumentContentParams(frameId=frame_id, html=html)
        return Command(method=PageMethod.SET_DOCUMENT_CONTENT, params=params)

    @staticmethod
    def set_intercept_file_chooser_dialog(enabled: bool) -> SetInterceptFileChooserDialogCommand:
        """
        Creates a command to set whether to intercept file chooser dialogs.

        Args:
            enabled (bool): Whether to intercept file chooser dialogs.

        Returns:
            SetInterceptFileChooserDialogCommand: Command object to set file chooser dialog
                interception.
        """
        params = SetInterceptFileChooserDialogParams(enabled=enabled)
        return Command(method=PageMethod.SET_INTERCEPT_FILE_CHOOSER_DIALOG, params=params)

    @staticmethod
    def set_lifecycle_events_enabled(enabled: bool) -> SetLifecycleEventsEnabledCommand:
        """
        Creates a command to enable/disable lifecycle events.

        Args:
            enabled (bool): Whether to enable lifecycle events.

        Returns:
            SetLifecycleEventsEnabledCommand: Command object to enable/disable lifecycle events.
        """
        params = SetLifecycleEventsEnabledParams(enabled=enabled)
        return Command(method=PageMethod.SET_LIFECYCLE_EVENTS_ENABLED, params=params)

    @staticmethod
    def stop_loading() -> StopLoadingCommand:
        """
        Creates a command to stop loading the page.

        Returns:
            StopLoadingCommand: Command object to stop loading the page.
        """
        return Command(method=PageMethod.STOP_LOADING)

    @staticmethod
    def add_compilation_cache(url: str, data: str) -> AddCompilationCacheCommand:
        """
        Creates a command to add a compilation cache entry.

        Experimental: This method is experimental and may be subject to change.

        Args:
            url (str): URL for which to add the compilation cache entry.
            data (str): Base64-encoded data.

        Returns:
            AddCompilationCacheCommand: Command object to add a compilation cache entry.
        """
        params = AddCompilationCacheParams(url=url, data=data)
        return Command(method=PageMethod.ADD_COMPILATION_CACHE, params=params)

    @staticmethod
    def capture_snapshot(
        format: Literal['mhtml'] = 'mhtml',
    ) -> CaptureSnapshotCommand:
        """
        Creates a command to capture a snapshot of the page.

        Experimental: This method is experimental and may be subject to change.

        Args:
            format (Literal['mhtml']): Format of the snapshot (only 'mhtml' is supported).

        Returns:
            CaptureSnapshotCommand: Command object to capture a snapshot.
        """
        params = CaptureSnapshotParams(format=format)
        return Command(method=PageMethod.CAPTURE_SNAPSHOT, params=params)

    @staticmethod
    def clear_compilation_cache() -> ClearCompilationCacheCommand:
        """
        Creates a command to clear the compilation cache.
        """
        return Command(method=PageMethod.CLEAR_COMPILATION_CACHE)

    @staticmethod
    def crash() -> CrashCommand:
        """
        Creates a command to crash the page.
        """
        return Command(method=PageMethod.CRASH)

    @staticmethod
    def generate_test_report(message: str, group: str | None = None) -> GenerateTestReportCommand:
        """
        Creates a command to generate a test report.

        Experimental: This method is experimental and may be subject to change.

        Args:
            message (str): Message to be displayed in the report.
            group (str | None): Group label for the report.

        Returns:
            GenerateTestReportCommand: Command object to generate a test report.
        """
        params = GenerateTestReportParams(message=message)
        if group is not None:
            params['group'] = group
        return Command(method=PageMethod.GENERATE_TEST_REPORT, params=params)

    @staticmethod
    def get_ad_script_ancestry_ids(
        frame_id: str,
    ) -> GetAdScriptAncestryIdsCommand:
        """
        Creates a command to get the ad script ancestry IDs for a given frame.

        Experimental: This method is experimental and may be subject to change.

        Args:
            frame_id (str): ID of the frame to get ad script ancestry IDs for.

        Returns:
            GetAdScriptAncestryIdsCommand: Command object to get ad script ancestry IDs.
        """
        params = GetAdScriptAncestryIdsParams(frameId=frame_id)
        return Command(method=PageMethod.GET_AD_SCRIPT_ANCESTRY_IDS, params=params)

    @staticmethod
    def get_app_id(app_id: str | None = None, recommended_id: str | None = None) -> GetAppIdCommand:
        """
        Creates a command to get the app ID.

        Experimental: This method is experimental and may be subject to change.

        Args:
            app_id (str | None): App ID for verification.
            recommended_id (str | None): Recommended app ID.

        Returns:
            GetAppIdCommand: Command object to get the app ID.
        """
        params = GetAppIdParams()
        if app_id is not None:
            params['appId'] = app_id
        if recommended_id is not None:
            params['recommendedId'] = recommended_id
        return Command(method=PageMethod.GET_APP_ID, params=params)

    @staticmethod
    def get_installability_errors() -> GetInstallabilityErrorsCommand:
        """
        Creates a command to get the installability errors.
        """
        return Command(method=PageMethod.GET_INSTALLABILITY_ERRORS)

    @staticmethod
    def get_origin_trials(frame_id: str) -> GetOriginTrialsCommand:
        """
        Creates a command to get origin trials for a given origin.

        Experimental: This method is experimental and may be subject to change.

        Args:
            frame_id (str | None): Frame ID to get trials for.

        Returns:
            GetOriginTrialsCommand: Command object to get origin trials.
        """
        params = GetOriginTrialsParams(frameId=frame_id)
        return Command(method=PageMethod.GET_ORIGIN_TRIALS, params=params)

    @staticmethod
    def get_permissions_policy_state(
        frame_id: str,
    ) -> GetPermissionsPolicyStateCommand:
        """
        Creates a command to get the permissions policy state.
        """
        params = GetPermissionsPolicyStateParams(frameId=frame_id)
        return Command(method=PageMethod.GET_PERMISSIONS_POLICY_STATE, params=params)

    @staticmethod
    def get_resource_content(
        frame_id: str,
        url: str,
    ) -> GetResourceContentCommand:
        """
        Creates a command to get the resource content.
        """
        params = GetResourceContentParams(frameId=frame_id, url=url)
        return Command(method=PageMethod.GET_RESOURCE_CONTENT, params=params)

    @staticmethod
    def get_resource_tree() -> GetResourceTreeCommand:
        """
        Creates a command to get the resource tree.
        """
        return Command(method=PageMethod.GET_RESOURCE_TREE)

    @staticmethod
    def produce_compilation_cache(
        scripts: list[CompilationCacheParams],
    ) -> ProduceCompilationCacheCommand:
        """
        Creates a command to produce a compilation cache entry.
        """
        params = ProduceCompilationCacheParams(scripts=scripts)
        return Command(method=PageMethod.PRODUCE_COMPILATION_CACHE, params=params)

    @staticmethod
    def screencast_frame_ack(
        session_id: int,
    ) -> ScreencastFrameAckCommand:
        """
        Creates a command to acknowledge a screencast frame.
        """
        params = ScreencastFrameAckParams(sessionId=session_id)
        return Command(method=PageMethod.SCREENCAST_FRAME_ACK, params=params)

    @staticmethod
    def search_in_resource(
        frame_id: str,
        url: str,
        query: str,
        case_sensitive: bool | None = None,
        is_regex: bool | None = None,
    ) -> SearchInResourceCommand:
        """
        Creates a command to search for a string in a resource.
        """
        params = SearchInResourceParams(frameId=frame_id, url=url, query=query)
        if case_sensitive is not None:
            params['caseSensitive'] = case_sensitive
        if is_regex is not None:
            params['isRegex'] = is_regex
        return Command(method=PageMethod.SEARCH_IN_RESOURCE, params=params)

    @staticmethod
    def set_ad_blocking_enabled(
        enabled: bool,
    ) -> SetAdBlockingEnabledCommand:
        """
        Creates a command to set ad blocking enabled.
        """
        params = SetAdBlockingEnabledParams(enabled=enabled)
        return Command(method=PageMethod.SET_AD_BLOCKING_ENABLED, params=params)

    @staticmethod
    def set_font_families(
        font_families: FontFamilies,
        for_scripts: list[ScriptFontFamilies],
    ) -> SetFontFamiliesCommand:
        """
        Creates a command to set font families.
        """
        params = SetFontFamiliesParams(fontFamilies=font_families, forScripts=for_scripts)
        return Command(method=PageMethod.SET_FONT_FAMILIES, params=params)

    @staticmethod
    def set_font_sizes(
        font_sizes: FontSizes,
    ) -> SetFontSizesCommand:
        """
        Creates a command to set font sizes.
        """
        params = SetFontSizesParams(fontSizes=font_sizes)
        return Command(method=PageMethod.SET_FONT_SIZES, params=params)

    @staticmethod
    def set_prerendering_allowed(
        is_allowed: bool,
    ) -> SetPrerenderingAllowedCommand:
        """
        Creates a command to set prerendering allowed.
        """
        params = SetPrerenderingAllowedParams(isAllowed=is_allowed)
        return Command(method=PageMethod.SET_PRERENDERING_ALLOWED, params=params)

    @staticmethod
    def set_rph_registration_mode(
        mode: AutoResponseMode,
    ) -> SetRPHRegistrationModeCommand:
        """
        Creates a command to set the RPH registration mode.
        """
        params = SetRPHRegistrationModeParams(mode=mode)
        return Command(method=PageMethod.SET_RPH_REGISTRATION_MODE, params=params)

    @staticmethod
    def set_spc_transaction_mode(
        mode: AutoResponseMode,
    ) -> SetSPCTransactionModeCommand:
        """
        Creates a command to set the SPC transaction mode.
        """
        params = SetSPCTransactionModeParams(mode=mode)
        return Command(method=PageMethod.SET_SPC_TRANSACTION_MODE, params=params)

    @staticmethod
    def set_web_lifecycle_state(
        state: WebLifecycleState,
    ) -> SetWebLifecycleStateCommand:
        """
        Creates a command to set the web lifecycle state.
        """
        params = SetWebLifecycleStateParams(state=state)
        return Command(method=PageMethod.SET_WEB_LIFECYCLE_STATE, params=params)

    @staticmethod
    def start_screencast(
        format: ScreencastFormat,
        quality: int | None = None,
        max_width: int | None = None,
        max_height: int | None = None,
        every_nth_frame: int | None = None,
    ) -> StartScreencastCommand:
        """
        Creates a command to start a screencast.
        """
        params = StartScreencastParams(format=format)
        if quality is not None:
            params['quality'] = quality
        if max_width is not None:
            params['maxWidth'] = max_width
        if max_height is not None:
            params['maxHeight'] = max_height
        if every_nth_frame is not None:
            params['everyNthFrame'] = every_nth_frame
        return Command(method=PageMethod.START_SCREENCAST, params=params)

    @staticmethod
    def stop_screencast() -> StopScreencastCommand:
        """
        Creates a command to stop a screencast.
        """
        return Command(method=PageMethod.STOP_SCREENCAST)

    @staticmethod
    def wait_for_debugger() -> WaitForDebuggerCommand:
        """
        Creates a command to wait for a debugger.
        """
        return Command(method=PageMethod.WAIT_FOR_DEBUGGER)
