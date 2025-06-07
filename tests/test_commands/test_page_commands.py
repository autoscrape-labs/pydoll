"""
Tests for PageCommands class.

This module contains comprehensive tests for all PageCommands methods,
verifying that they generate the correct CDP commands with proper parameters.
"""

from pydoll.commands.page_commands import PageCommands
from pydoll.constants import (
    ReferrerPolicy,
    ScreencastFormat,
    ScreenshotFormat,
    TransferMode,
    TransitionType,
    WebLifecycleState,
)
from pydoll.protocol.page.methods import PageMethod


def test_add_script_to_evaluate_on_new_document_minimal():
    """Test add_script_to_evaluate_on_new_document with minimal parameters."""
    result = PageCommands.add_script_to_evaluate_on_new_document(
        source='console.log("Hello World");'
    )
    assert result['method'] == PageMethod.ADD_SCRIPT_TO_EVALUATE_ON_NEW_DOCUMENT
    assert result['params']['source'] == 'console.log("Hello World");'


def test_add_script_to_evaluate_on_new_document_with_all_params():
    """Test add_script_to_evaluate_on_new_document with all parameters."""
    result = PageCommands.add_script_to_evaluate_on_new_document(
        source='console.log("Test");',
        world_name='test_world',
        include_command_line_api=True,
        run_immediately=False
    )
    assert result['method'] == PageMethod.ADD_SCRIPT_TO_EVALUATE_ON_NEW_DOCUMENT
    assert result['params']['source'] == 'console.log("Test");'
    assert result['params']['worldName'] == 'test_world'
    assert result['params']['includeCommandLineAPI'] is True
    assert result['params']['runImmediately'] is False


def test_bring_to_front():
    """Test bring_to_front method generates correct command."""
    result = PageCommands.bring_to_front()
    assert result['method'] == PageMethod.BRING_TO_FRONT
    assert 'params' not in result


def test_capture_screenshot_minimal():
    """Test capture_screenshot with minimal parameters."""
    result = PageCommands.capture_screenshot()
    assert result['method'] == PageMethod.CAPTURE_SCREENSHOT
    assert result['params'] == {}


def test_capture_screenshot_with_format_and_quality():
    """Test capture_screenshot with format and quality."""
    result = PageCommands.capture_screenshot(
        format=ScreenshotFormat.JPEG,
        quality=80
    )
    assert result['method'] == PageMethod.CAPTURE_SCREENSHOT
    assert result['params']['format'] == ScreenshotFormat.JPEG
    assert result['params']['quality'] == 80


def test_capture_screenshot_with_clip():
    """Test capture_screenshot with clip viewport."""
    clip = {
        'x': 10,
        'y': 20,
        'width': 100,
        'height': 200,
        'scale': 1.0
    }
    result = PageCommands.capture_screenshot(
        format=ScreenshotFormat.PNG,
        clip=clip
    )
    assert result['method'] == PageMethod.CAPTURE_SCREENSHOT
    assert result['params']['format'] == ScreenshotFormat.PNG
    assert result['params']['clip'] == clip


def test_capture_screenshot_with_all_params():
    """Test capture_screenshot with all parameters."""
    clip = {
        'x': 0,
        'y': 0,
        'width': 1920,
        'height': 1080,
        'scale': 1.0
    }
    result = PageCommands.capture_screenshot(
        format=ScreenshotFormat.WEBP,
        quality=90,
        clip=clip,
        from_surface=True,
        capture_beyond_viewport=False,
        optimize_for_speed=True
    )
    assert result['method'] == PageMethod.CAPTURE_SCREENSHOT
    assert result['params']['format'] == ScreenshotFormat.WEBP
    assert result['params']['quality'] == 90
    assert result['params']['clip'] == clip
    assert result['params']['fromSurface'] is True
    assert result['params']['captureBeyondViewport'] is False
    assert result['params']['optimizeForSpeed'] is True


def test_close():
    """Test close method generates correct command."""
    result = PageCommands.close()
    assert result['method'] == PageMethod.CLOSE
    assert 'params' not in result


def test_create_isolated_world_minimal():
    """Test create_isolated_world with minimal parameters."""
    result = PageCommands.create_isolated_world(frame_id='frame123')
    assert result['method'] == PageMethod.CREATE_ISOLATED_WORLD
    assert result['params']['frameId'] == 'frame123'


def test_create_isolated_world_with_all_params():
    """Test create_isolated_world with all parameters."""
    result = PageCommands.create_isolated_world(
        frame_id='frame123',
        world_name='test_world',
        grant_universal_access=True
    )
    assert result['method'] == PageMethod.CREATE_ISOLATED_WORLD
    assert result['params']['frameId'] == 'frame123'
    assert result['params']['worldName'] == 'test_world'
    assert result['params']['grantUniveralAccess'] is True


def test_disable():
    """Test disable method generates correct command."""
    result = PageCommands.disable()
    assert result['method'] == PageMethod.DISABLE
    assert 'params' not in result


def test_enable_minimal():
    """Test enable with minimal parameters."""
    result = PageCommands.enable()
    assert result['method'] == PageMethod.ENABLE
    assert result['params'] == {}


def test_enable_with_file_chooser():
    """Test enable with file chooser event enabled."""
    result = PageCommands.enable(enable_file_chooser_opened_event=True)
    assert result['method'] == PageMethod.ENABLE
    assert result['params']['enableFileChooserOpenedEvent'] is True


def test_get_app_manifest_minimal():
    """Test get_app_manifest with minimal parameters."""
    result = PageCommands.get_app_manifest()
    assert result['method'] == PageMethod.GET_APP_MANIFEST
    assert result['params'] == {}


def test_get_app_manifest_with_id():
    """Test get_app_manifest with manifest ID."""
    result = PageCommands.get_app_manifest(manifest_id='manifest123')
    assert result['method'] == PageMethod.GET_APP_MANIFEST
    assert result['params']['manifestId'] == 'manifest123'


def test_get_frame_tree():
    """Test get_frame_tree method generates correct command."""
    result = PageCommands.get_frame_tree()
    assert result['method'] == PageMethod.GET_FRAME_TREE
    assert 'params' not in result


def test_get_layout_metrics():
    """Test get_layout_metrics method generates correct command."""
    result = PageCommands.get_layout_metrics()
    assert result['method'] == PageMethod.GET_LAYOUT_METRICS
    assert 'params' not in result


def test_get_navigation_history():
    """Test get_navigation_history method generates correct command."""
    result = PageCommands.get_navigation_history()
    assert result['method'] == PageMethod.GET_NAVIGATION_HISTORY
    assert 'params' not in result


def test_handle_javascript_dialog_accept():
    """Test handle_javascript_dialog with accept."""
    result = PageCommands.handle_javascript_dialog(accept=True)
    assert result['method'] == PageMethod.HANDLE_JAVASCRIPT_DIALOG
    assert result['params']['accept'] is True


def test_handle_javascript_dialog_with_prompt():
    """Test handle_javascript_dialog with prompt text."""
    result = PageCommands.handle_javascript_dialog(
        accept=True,
        prompt_text='test input'
    )
    assert result['method'] == PageMethod.HANDLE_JAVASCRIPT_DIALOG
    assert result['params']['accept'] is True
    assert result['params']['promptText'] == 'test input'


def test_navigate_minimal():
    """Test navigate with minimal parameters."""
    result = PageCommands.navigate(url='https://example.com')
    assert result['method'] == PageMethod.NAVIGATE
    assert result['params']['url'] == 'https://example.com'


def test_navigate_with_all_params():
    """Test navigate with all parameters."""
    result = PageCommands.navigate(
        url='https://example.com',
        referrer='https://google.com',
        transition_type=TransitionType.LINK,
        frame_id='frame123',
        referrer_policy=ReferrerPolicy.STRICT_ORIGIN
    )
    assert result['method'] == PageMethod.NAVIGATE
    assert result['params']['url'] == 'https://example.com'
    assert result['params']['referrer'] == 'https://google.com'
    assert result['params']['transitionType'] == TransitionType.LINK
    assert result['params']['frameId'] == 'frame123'
    assert result['params']['referrerPolicy'] == ReferrerPolicy.STRICT_ORIGIN


def test_navigate_to_history_entry():
    """Test navigate_to_history_entry method."""
    result = PageCommands.navigate_to_history_entry(entry_id=5)
    assert result['method'] == PageMethod.NAVIGATE_TO_HISTORY_ENTRY
    assert result['params']['entryId'] == 5


def test_print_to_pdf_minimal():
    """Test print_to_pdf with minimal parameters."""
    result = PageCommands.print_to_pdf()
    assert result['method'] == PageMethod.PRINT_TO_PDF
    assert result['params'] == {}


def test_print_to_pdf_with_basic_params():
    """Test print_to_pdf with basic parameters."""
    result = PageCommands.print_to_pdf(
        landscape=True,
        scale=1.5,
        paper_width=8.5,
        paper_height=11.0
    )
    assert result['method'] == PageMethod.PRINT_TO_PDF
    assert result['params']['landscape'] is True
    assert result['params']['scale'] == 1.5
    assert result['params']['paperWidth'] == 8.5
    assert result['params']['paperHeight'] == 11.0


def test_print_to_pdf_with_all_params():
    """Test print_to_pdf with all parameters."""
    result = PageCommands.print_to_pdf(
        landscape=False,
        display_header_footer=True,
        print_background=True,
        scale=1.0,
        paper_width=8.5,
        paper_height=11.0,
        margin_top=0.5,
        margin_bottom=0.5,
        margin_left=0.5,
        margin_right=0.5,
        page_ranges='1-5',
        header_template='<div>Header</div>',
        footer_template='<div>Footer</div>',
        prefer_css_page_size=True,
        transfer_mode=TransferMode.RETURN_AS_BASE64,
        generate_tagged_pdf=True,
        generate_document_outline=False
    )
    assert result['method'] == PageMethod.PRINT_TO_PDF
    assert result['params']['landscape'] is False
    assert result['params']['displayHeaderFooter'] is True
    assert result['params']['printBackground'] is True
    assert result['params']['scale'] == 1.0
    assert result['params']['paperWidth'] == 8.5
    assert result['params']['paperHeight'] == 11.0
    assert result['params']['marginTop'] == 0.5
    assert result['params']['marginBottom'] == 0.5
    assert result['params']['marginLeft'] == 0.5
    assert result['params']['marginRight'] == 0.5
    assert result['params']['pageRanges'] == '1-5'
    assert result['params']['headerTemplate'] == '<div>Header</div>'
    assert result['params']['footerTemplate'] == '<div>Footer</div>'
    assert result['params']['preferCSSPageSize'] is True
    assert result['params']['transferMode'] == TransferMode.RETURN_AS_BASE64
    assert result['params']['generateTaggedPDF'] is True
    assert result['params']['generateDocumentOutline'] is False


def test_reload_minimal():
    """Test reload with minimal parameters."""
    result = PageCommands.reload()
    assert result['method'] == PageMethod.RELOAD
    assert result['params'] == {}


def test_reload_with_all_params():
    """Test reload with all parameters."""
    result = PageCommands.reload(
        ignore_cache=True,
        script_to_evaluate_on_load='console.log("reloaded");',
        loader_id='loader123'
    )
    assert result['method'] == PageMethod.RELOAD
    assert result['params']['ignoreCache'] is True
    assert result['params']['scriptToEvaluateOnLoad'] == 'console.log("reloaded");'
    assert result['params']['loaderId'] == 'loader123'


def test_reset_navigation_history():
    """Test reset_navigation_history method generates correct command."""
    result = PageCommands.reset_navigation_history()
    assert result['method'] == PageMethod.RESET_NAVIGATION_HISTORY
    assert 'params' not in result


def test_remove_script_to_evaluate_on_new_document():
    """Test remove_script_to_evaluate_on_new_document method."""
    result = PageCommands.remove_script_to_evaluate_on_new_document(
        identifier='script123'
    )
    assert result['method'] == PageMethod.REMOVE_SCRIPT_TO_EVALUATE_ON_NEW_DOCUMENT
    assert result['params']['identifier'] == 'script123'


def test_set_bypass_csp():
    """Test set_bypass_csp method."""
    result = PageCommands.set_bypass_csp(enabled=True)
    assert result['method'] == PageMethod.SET_BYPASS_CSP
    assert result['params']['enabled'] is True


def test_set_document_content():
    """Test set_document_content method."""
    result = PageCommands.set_document_content(
        frame_id='frame123',
        html='<html><body>Test</body></html>'
    )
    assert result['method'] == PageMethod.SET_DOCUMENT_CONTENT
    assert result['params']['frameId'] == 'frame123'
    assert result['params']['html'] == '<html><body>Test</body></html>'


def test_set_intercept_file_chooser_dialog():
    """Test set_intercept_file_chooser_dialog method."""
    result = PageCommands.set_intercept_file_chooser_dialog(enabled=True)
    assert result['method'] == PageMethod.SET_INTERCEPT_FILE_CHOOSER_DIALOG
    assert result['params']['enabled'] is True


def test_set_lifecycle_events_enabled():
    """Test set_lifecycle_events_enabled method."""
    result = PageCommands.set_lifecycle_events_enabled(enabled=True)
    assert result['method'] == PageMethod.SET_LIFECYCLE_EVENTS_ENABLED
    assert result['params']['enabled'] is True


def test_stop_loading():
    """Test stop_loading method generates correct command."""
    result = PageCommands.stop_loading()
    assert result['method'] == PageMethod.STOP_LOADING
    assert 'params' not in result


def test_add_compilation_cache():
    """Test add_compilation_cache method."""
    result = PageCommands.add_compilation_cache(
        url='https://example.com/script.js',
        data='compiled_data_here'
    )
    assert result['method'] == PageMethod.ADD_COMPILATION_CACHE
    assert result['params']['url'] == 'https://example.com/script.js'
    assert result['params']['data'] == 'compiled_data_here'


def test_capture_snapshot():
    """Test capture_snapshot method."""
    result = PageCommands.capture_snapshot(format='mhtml')
    assert result['method'] == PageMethod.CAPTURE_SNAPSHOT
    assert result['params']['format'] == 'mhtml'


def test_clear_compilation_cache():
    """Test clear_compilation_cache method generates correct command."""
    result = PageCommands.clear_compilation_cache()
    assert result['method'] == PageMethod.CLEAR_COMPILATION_CACHE
    assert 'params' not in result


def test_crash():
    """Test crash method generates correct command."""
    result = PageCommands.crash()
    assert result['method'] == PageMethod.CRASH
    assert 'params' not in result


def test_generate_test_report_minimal():
    """Test generate_test_report with minimal parameters."""
    result = PageCommands.generate_test_report(message='Test message')
    assert result['method'] == PageMethod.GENERATE_TEST_REPORT
    assert result['params']['message'] == 'Test message'


def test_generate_test_report_with_group():
    """Test generate_test_report with group parameter."""
    result = PageCommands.generate_test_report(
        message='Test message',
        group='test_group'
    )
    assert result['method'] == PageMethod.GENERATE_TEST_REPORT
    assert result['params']['message'] == 'Test message'
    assert result['params']['group'] == 'test_group'


def test_get_ad_script_ancestry_ids():
    """Test get_ad_script_ancestry_ids method."""
    result = PageCommands.get_ad_script_ancestry_ids(frame_id='frame123')
    assert result['method'] == PageMethod.GET_AD_SCRIPT_ANCESTRY_IDS
    assert result['params']['frameId'] == 'frame123'


def test_get_app_id_minimal():
    """Test get_app_id with minimal parameters."""
    result = PageCommands.get_app_id()
    assert result['method'] == PageMethod.GET_APP_ID
    assert result['params'] == {}


def test_get_app_id_with_params():
    """Test get_app_id with parameters."""
    result = PageCommands.get_app_id(
        app_id='app123',
        recommended_id='rec456'
    )
    assert result['method'] == PageMethod.GET_APP_ID
    assert result['params']['appId'] == 'app123'
    assert result['params']['recommendedId'] == 'rec456'


def test_get_installability_errors():
    """Test get_installability_errors method generates correct command."""
    result = PageCommands.get_installability_errors()
    assert result['method'] == PageMethod.GET_INSTALLABILITY_ERRORS
    assert 'params' not in result


def test_get_origin_trials():
    """Test get_origin_trials method."""
    result = PageCommands.get_origin_trials(frame_id='frame123')
    assert result['method'] == PageMethod.GET_ORIGIN_TRIALS
    assert result['params']['frameId'] == 'frame123'


def test_get_permissions_policy_state():
    """Test get_permissions_policy_state method."""
    result = PageCommands.get_permissions_policy_state(frame_id='frame123')
    assert result['method'] == PageMethod.GET_PERMISSIONS_POLICY_STATE
    assert result['params']['frameId'] == 'frame123'


def test_get_resource_content():
    """Test get_resource_content method."""
    result = PageCommands.get_resource_content(
        frame_id='frame123',
        url='https://example.com/resource.js'
    )
    assert result['method'] == PageMethod.GET_RESOURCE_CONTENT
    assert result['params']['frameId'] == 'frame123'
    assert result['params']['url'] == 'https://example.com/resource.js'


def test_get_resource_tree():
    """Test get_resource_tree method generates correct command."""
    result = PageCommands.get_resource_tree()
    assert result['method'] == PageMethod.GET_RESOURCE_TREE
    assert 'params' not in result


def test_produce_compilation_cache():
    """Test produce_compilation_cache method."""
    scripts = [
        {'url': 'https://example.com/script1.js', 'eager': True},
        {'url': 'https://example.com/script2.js', 'eager': False}
    ]
    result = PageCommands.produce_compilation_cache(scripts=scripts)
    assert result['method'] == PageMethod.PRODUCE_COMPILATION_CACHE
    assert result['params']['scripts'] == scripts


def test_screencast_frame_ack():
    """Test screencast_frame_ack method."""
    result = PageCommands.screencast_frame_ack(session_id='session123')
    assert result['method'] == PageMethod.SCREENCAST_FRAME_ACK
    assert result['params']['sessionId'] == 'session123'


def test_search_in_resource_minimal():
    """Test search_in_resource with minimal parameters."""
    result = PageCommands.search_in_resource(
        frame_id='frame123',
        url='https://example.com/resource.js',
        query='function'
    )
    assert result['method'] == PageMethod.SEARCH_IN_RESOURCE
    assert result['params']['frameId'] == 'frame123'
    assert result['params']['url'] == 'https://example.com/resource.js'
    assert result['params']['query'] == 'function'


def test_search_in_resource_with_options():
    """Test search_in_resource with all options."""
    result = PageCommands.search_in_resource(
        frame_id='frame123',
        url='https://example.com/resource.js',
        query='function.*test',
        case_sensitive=True,
        is_regex=True
    )
    assert result['method'] == PageMethod.SEARCH_IN_RESOURCE
    assert result['params']['frameId'] == 'frame123'
    assert result['params']['url'] == 'https://example.com/resource.js'
    assert result['params']['query'] == 'function.*test'
    assert result['params']['caseSensitive'] is True
    assert result['params']['isRegex'] is True


def test_set_ad_blocking_enabled():
    """Test set_ad_blocking_enabled method."""
    result = PageCommands.set_ad_blocking_enabled(enabled=True)
    assert result['method'] == PageMethod.SET_AD_BLOCKING_ENABLED
    assert result['params']['enabled'] is True


def test_set_font_families():
    """Test set_font_families method."""
    font_families = {
        'standard': 'Arial',
        'serif': 'Times New Roman',
        'sansSerif': 'Helvetica',
        'cursive': 'Comic Sans MS',
        'fantasy': 'Impact',
        'math': 'Latin Modern Math'
    }
    for_scripts = [
        {'script': 'Latn', 'fontFamilies': font_families}
    ]
    result = PageCommands.set_font_families(
        font_families=font_families,
        for_scripts=for_scripts
    )
    assert result['method'] == PageMethod.SET_FONT_FAMILIES
    assert result['params']['fontFamilies'] == font_families
    assert result['params']['forScripts'] == for_scripts


def test_set_font_sizes():
    """Test set_font_sizes method."""
    font_sizes = {
        'standard': 16,
        'fixed': 14
    }
    result = PageCommands.set_font_sizes(font_sizes=font_sizes)
    assert result['method'] == PageMethod.SET_FONT_SIZES
    assert result['params']['fontSizes'] == font_sizes


def test_set_prerendering_allowed():
    """Test set_prerendering_allowed method."""
    result = PageCommands.set_prerendering_allowed(allowed=True)
    assert result['method'] == PageMethod.SET_PRERENDERING_ALLOWED
    assert result['params']['allowed'] == True


def test_set_rph_registration_mode():
    """Test set_rph_registration_mode method."""
    from pydoll.protocol.page.params import AutoResponseMode
    result = PageCommands.set_rph_registration_mode(mode=AutoResponseMode.AUTO_ACCEPT)
    assert result['method'] == PageMethod.SET_RPH_REGISTRATION_MODE
    assert result['params']['mode'] == AutoResponseMode.AUTO_ACCEPT


def test_set_spc_transaction_mode():
    """Test set_spc_transaction_mode method."""
    from pydoll.protocol.page.params import AutoResponseMode
    result = PageCommands.set_spc_transaction_mode(mode=AutoResponseMode.AUTO_REJECT)
    assert result['method'] == PageMethod.SET_SPC_TRANSACTION_MODE
    assert result['params']['mode'] == AutoResponseMode.AUTO_REJECT


def test_set_web_lifecycle_state():
    """Test set_web_lifecycle_state method."""
    result = PageCommands.set_web_lifecycle_state(state=WebLifecycleState.FROZEN)
    assert result['method'] == PageMethod.SET_WEB_LIFECYCLE_STATE
    assert result['params']['state'] == WebLifecycleState.FROZEN


def test_start_screencast_minimal():
    """Test start_screencast with minimal parameters."""
    result = PageCommands.start_screencast(format=ScreencastFormat.JPEG)
    assert result['method'] == PageMethod.START_SCREENCAST
    assert result['params']['format'] == ScreencastFormat.JPEG


def test_start_screencast_with_all_params():
    """Test start_screencast with all parameters."""
    result = PageCommands.start_screencast(
        format=ScreencastFormat.PNG,
        quality=80,
        max_width=1920,
        max_height=1080,
        every_nth_frame=2
    )
    assert result['method'] == PageMethod.START_SCREENCAST
    assert result['params']['format'] == ScreencastFormat.PNG
    assert result['params']['quality'] == 80
    assert result['params']['maxWidth'] == 1920
    assert result['params']['maxHeight'] == 1080
    assert result['params']['everyNthFrame'] == 2


def test_stop_screencast():
    """Test stop_screencast method generates correct command."""
    result = PageCommands.stop_screencast()
    assert result['method'] == PageMethod.STOP_SCREENCAST
    assert 'params' not in result


def test_wait_for_debugger():
    """Test wait_for_debugger method generates correct command."""
    result = PageCommands.wait_for_debugger()
    assert result['method'] == PageMethod.WAIT_FOR_DEBUGGER
    assert 'params' not in result
