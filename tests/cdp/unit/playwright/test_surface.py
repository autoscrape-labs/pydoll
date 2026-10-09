"""The members the Playwright API guide lists as Full must exist, in both API forms.

The compatibility matrix in ``docs/en/guides/playwright-api.md`` is a promise;
this test keeps the code and the promise from drifting apart without needing
a browser.
"""

from __future__ import annotations

import pytest

from pydoll.playwright import async_api, sync_api

FULL_MEMBERS = {
    'BrowserType': [
        'launch',
        'launch_persistent_context',
        'connect_over_cdp',
    ],
    'Browser': ['new_context', 'new_page', 'contexts', 'version', 'close', 'is_connected'],
    'BrowserContext': [
        'new_page',
        'pages',
        'close',
        'cookies',
        'add_cookies',
        'clear_cookies',
        'storage_state',
        'grant_permissions',
        'clear_permissions',
        'set_geolocation',
        'set_extra_http_headers',
        'set_offline',
        'add_init_script',
        'expose_function',
        'expose_binding',
        'route',
        'unroute',
        'expect_page',
        'expect_event',
        'wait_for_event',
        'set_default_timeout',
        'set_default_navigation_timeout',
    ],
    'Page': [
        'goto',
        'reload',
        'go_back',
        'go_forward',
        'wait_for_load_state',
        'wait_for_url',
        'expect_navigation',
        'evaluate',
        'evaluate_handle',
        'query_selector',
        'query_selector_all',
        'wait_for_selector',
        'wait_for_function',
        'wait_for_timeout',
        'content',
        'set_content',
        'title',
        'url',
        'frames',
        'main_frame',
        'frame',
        'frame_locator',
        'add_init_script',
        'add_script_tag',
        'add_style_tag',
        'set_viewport_size',
        'viewport_size',
        'emulate_media',
        'set_extra_http_headers',
        'screenshot',
        'pdf',
        'route',
        'unroute',
        'expose_function',
        'expose_binding',
        'keyboard',
        'mouse',
        'touchscreen',
        'click',
        'fill',
        'type',
        'press',
        'check',
        'select_option',
        'text_content',
        'inner_text',
        'inner_html',
        'get_attribute',
        'is_visible',
        'get_by_role',
        'get_by_text',
        'get_by_label',
        'get_by_placeholder',
        'get_by_alt_text',
        'get_by_title',
        'get_by_test_id',
        'expect_download',
        'expect_popup',
        'expect_file_chooser',
        'expect_console_message',
        'expect_request',
        'expect_response',
        'tab',
    ],
    'Locator': [
        'filter',
        'and_',
        'or_',
        'nth',
        'first',
        'last',
        'count',
        'all',
        'drag_to',
        'select_option',
        'set_input_files',
        'screenshot',
        'evaluate_all',
        'bounding_box',
        'scroll_into_view_if_needed',
        'dispatch_event',
        'element_handle',
    ],
    'ElementHandle': ['web_element', 'bounding_box', 'screenshot', 'evaluate'],
    'Keyboard': ['down', 'up', 'press', 'type', 'insert_text'],
    'Mouse': ['move', 'down', 'up', 'click', 'dblclick', 'wheel'],
    'Route': ['abort', 'continue_', 'fulfill', 'fetch', 'fallback', 'request'],
}


@pytest.mark.parametrize('module', [async_api, sync_api], ids=['async_api', 'sync_api'])
@pytest.mark.parametrize('class_name', sorted(FULL_MEMBERS))
def test_documented_full_members_exist(module, class_name):
    cls = getattr(module, class_name)
    missing = [name for name in FULL_MEMBERS[class_name] if not hasattr(cls, name)]
    assert missing == [], f'{module.__name__}.{class_name} lacks {missing}'


def test_both_forms_export_the_same_names():
    assert set(async_api.__all__) - {'async_playwright'} == set(sync_api.__all__) - {
        'sync_playwright'
    }
