"""Unit tests for FingerprintApplier against an in-memory FakeConnection.

A real Tab and its Browser share one FakeConnection so both the tab-scoped and
browser-scoped code paths run without sockets. Assertions check the CDP commands
emitted and the per-tab / per-context state the applier maintains.
"""

from __future__ import annotations

import asyncio
import logging

import pytest

from pydoll.browser.chromium import Chrome
from pydoll.browser.fingerprint_applier import FingerprintApplier
from pydoll.browser.tab import Tab
from pydoll.exceptions import FingerprintContextConflict

pytestmark = pytest.mark.asyncio

UA = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
    'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36'
)


@pytest.fixture
def fp_tab(fake_conn):
    """A real Tab whose Tab and Browser both use the same FakeConnection."""
    chrome = Chrome()
    chrome._connection_handler = fake_conn
    return Tab(browser=chrome, target_id='fp-tab', connection_handler=fake_conn)


class TestAcceptLanguage:
    def test_plain_unweighted_list(self):
        result = FingerprintApplier._build_accept_language({'locale': {'languages': ['en-US', 'en']}})
        assert result == 'en-US,en'

    def test_no_locale_returns_none(self):
        assert FingerprintApplier._build_accept_language({}) is None

    def test_empty_languages_returns_none(self):
        assert FingerprintApplier._build_accept_language({'locale': {'languages': []}}) is None


class TestDeviceMetrics:
    async def test_inner_dims_drive_viewport(self, fp_tab, fake_conn):
        screen = {'width': 1920, 'height': 1080, 'inner_width': 1900, 'inner_height': 1000}
        await FingerprintApplier(fp_tab)._apply_device_metrics(screen)
        params = fake_conn.last_command('Emulation.setDeviceMetricsOverride')['params']
        assert params['width'] == 1900
        assert params['height'] == 1000
        assert params['screenWidth'] == 1920
        assert params['screenHeight'] == 1080

    async def test_missing_inner_dims_disable_viewport_override(self, fp_tab, fake_conn):
        """Without inner dims the layout size override is disabled (0), not screen size."""
        screen = {'width': 1920, 'height': 1080}
        await FingerprintApplier(fp_tab)._apply_device_metrics(screen)
        params = fake_conn.last_command('Emulation.setDeviceMetricsOverride')['params']
        assert params['width'] == 0
        assert params['height'] == 0
        assert params['screenWidth'] == 1920
        assert params['screenHeight'] == 1080


class TestMediaFeatures:
    async def test_features_mapped_to_css_names(self, fp_tab, fake_conn):
        await FingerprintApplier(fp_tab)._apply_media_features(
            {'color_gamut': 'p3', 'prefers_color_scheme': 'dark'}
        )
        params = fake_conn.last_command('Emulation.setEmulatedMedia')['params']
        names = {f['name']: f['value'] for f in params['features']}
        assert names['color-gamut'] == 'p3'
        assert names['prefers-color-scheme'] == 'dark'

    async def test_only_color_gamut_when_alone(self, fp_tab, fake_conn):
        await FingerprintApplier(fp_tab)._apply_media_features({'color_gamut': 'srgb'})
        params = fake_conn.last_command('Emulation.setEmulatedMedia')['params']
        assert [f['name'] for f in params['features']] == ['color-gamut']

    async def test_empty_sends_no_command(self, fp_tab, fake_conn):
        await FingerprintApplier(fp_tab)._apply_media_features({})
        assert not fake_conn.commands_for('Emulation.setEmulatedMedia')


class TestIdempotency:
    async def test_repeat_identical_apply_is_noop(self, fp_tab, fake_conn):
        fingerprint = {'user_agent': UA, 'hardware': {'device_memory': 8}}

        await fp_tab.apply_fingerprint(fingerprint)
        scripts_after_first = len(fake_conn.commands_for('Page.addScriptToEvaluateOnNewDocument'))
        callbacks_after_first = len(fake_conn.callbacks_for('Target.attachedToTarget'))

        await fp_tab.apply_fingerprint(dict(fingerprint))  # equal value, new object

        assert len(fake_conn.commands_for('Page.addScriptToEvaluateOnNewDocument')) == \
            scripts_after_first
        assert len(fake_conn.callbacks_for('Target.attachedToTarget')) == callbacks_after_first
        assert fp_tab._fingerprint_applier is not None
        assert fp_tab._fingerprint_applier._applied == fingerprint

    async def test_different_fingerprint_same_context_conflicts(self, fp_tab):
        await fp_tab.apply_fingerprint({'user_agent': UA, 'hardware': {'device_memory': 8}})
        with pytest.raises(FingerprintContextConflict):
            await fp_tab.apply_fingerprint({'user_agent': UA, 'hardware': {'device_memory': 16}})


class TestUserAgentOptionConflict:
    async def test_warns_when_option_differs(self, fp_tab, caplog):
        fp_tab._browser.options.add_argument('--user-agent=Mozilla/5.0 Different/1.0')
        with caplog.at_level(logging.WARNING):
            await fp_tab.apply_fingerprint({'user_agent': UA})
        assert any('--user-agent' in r.message for r in caplog.records)

    async def test_no_warning_when_no_option(self, fp_tab, caplog):
        with caplog.at_level(logging.WARNING):
            await fp_tab.apply_fingerprint({'user_agent': UA})
        assert not any('--user-agent' in r.message for r in caplog.records)


class TestWorkerHandlerCleanup:
    async def test_delete_context_removes_worker_callback(self, fake_conn):
        chrome = Chrome()
        chrome._connection_handler = fake_conn
        tab = Tab(
            browser=chrome,
            target_id='ctx-tab',
            connection_handler=fake_conn,
            browser_context_id='ctx-1',
        )

        await tab.apply_fingerprint({'user_agent': UA, 'hardware': {'device_memory': 8}})
        assert 'ctx-1' in chrome._context_worker_callbacks
        callback_id = chrome._context_worker_callbacks['ctx-1']
        assert fake_conn.callbacks_for('Target.attachedToTarget')

        await chrome.delete_browser_context('ctx-1')

        assert 'ctx-1' not in chrome._context_worker_callbacks
        assert callback_id not in fake_conn._callbacks


class TestWorkAreaInsets:
    def test_mac_menu_bar_split(self):
        """avail_top is the top inset; the remaining gap is the bottom (dock)."""
        screen = {'width': 1440, 'height': 900, 'avail_width': 1440, 'avail_height': 860,
                  'avail_top': 25}
        assert FingerprintApplier._work_area_insets(screen, 2) == \
            {'top': 50, 'bottom': 30, 'left': 0, 'right': 0}

    def test_windows_taskbar_bottom(self):
        screen = {'width': 1920, 'height': 1080, 'avail_width': 1920, 'avail_height': 1040,
                  'avail_top': 0}
        assert FingerprintApplier._work_area_insets(screen, 1) == \
            {'top': 0, 'bottom': 40, 'left': 0, 'right': 0}

    def test_defaults_whole_gap_to_top(self):
        """Without avail_top the whole vertical gap is reserved at the top."""
        screen = {'width': 1440, 'height': 900, 'avail_height': 860}
        assert FingerprintApplier._work_area_insets(screen, 1) == \
            {'top': 40, 'bottom': 0, 'left': 0, 'right': 0}

    def test_avail_top_clamped_to_gap(self):
        """avail_top without a matching avail_height cannot reserve absent space."""
        screen = {'width': 1440, 'height': 900, 'avail_top': 25}
        assert FingerprintApplier._work_area_insets(screen, 1) is None

    def test_negative_offsets_clamped_to_zero(self):
        """A negative avail_top/avail_left never yields a negative CDP inset."""
        screen = {'width': 1440, 'height': 900, 'avail_width': 1400, 'avail_height': 860,
                  'avail_top': -10, 'avail_left': -10}
        assert FingerprintApplier._work_area_insets(screen, 1) == \
            {'top': 0, 'bottom': 40, 'left': 0, 'right': 40}

    def test_none_when_no_gap(self):
        screen = {'width': 1440, 'height': 900, 'avail_width': 1440, 'avail_height': 900}
        assert FingerprintApplier._work_area_insets(screen, 1) is None


class TestPrimaryScreenId:
    def test_picks_primary(self):
        response = {'result': {'screenInfos': [
            {'id': '2', 'isPrimary': False}, {'id': '1', 'isPrimary': True}]}}
        assert FingerprintApplier._primary_screen_id(response) == '1'

    def test_falls_back_to_first(self):
        response = {'result': {'screenInfos': [{'id': '7'}]}}
        assert FingerprintApplier._primary_screen_id(response) == '7'

    def test_none_on_error_response(self):
        assert FingerprintApplier._primary_screen_id({'id': 1, 'error': {'message': 'x'}}) is None

    def test_none_on_empty(self):
        assert FingerprintApplier._primary_screen_id({'result': {'screenInfos': []}}) is None


class TestHeadlessScreen:
    async def test_headless_emits_update_screen(self, fp_tab, fake_conn):
        fp_tab._browser.options.headless = True
        fake_conn.set_response(
            'Emulation.getScreenInfos', {'screenInfos': [{'id': '1', 'isPrimary': True}]}
        )
        screen = {'width': 1440, 'height': 900, 'avail_width': 1440, 'avail_height': 860,
                  'avail_top': 25, 'color_depth': 30, 'device_pixel_ratio': 2.0}

        await FingerprintApplier(fp_tab)._apply_headless_screen(screen)

        params = fake_conn.last_command('Emulation.updateScreen')['params']
        assert params['screenId'] == '1'
        assert params['width'] == 2880
        assert params['height'] == 1800
        assert params['devicePixelRatio'] == 2.0
        assert params['colorDepth'] == 30
        assert params['workAreaInsets'] == {'top': 50, 'bottom': 30, 'left': 0, 'right': 0}

    async def test_screen_update_skipped_when_browser_rejects_get_screen_infos(
        self, fp_tab, fake_conn
    ):
        fp_tab._browser.options.headless = True
        fake_conn.set_failure(
            'Emulation.getScreenInfos', -32601, "'Emulation.getScreenInfos' wasn't found"
        )
        screen = {'width': 1440, 'height': 900, 'device_pixel_ratio': 2.0}
        await FingerprintApplier(fp_tab)._apply_headless_screen(screen)
        assert fake_conn.commands_for('Emulation.updateScreen') == []

    async def test_fractional_dpr_is_rounded_to_integer(self, fp_tab, fake_conn):
        """Headless virtual screens only accept an integer dpr, so it is rounded
        and the physical size is scaled by the rounded value."""
        fp_tab._browser.options.headless = True
        fake_conn.set_response(
            'Emulation.getScreenInfos', {'screenInfos': [{'id': '1', 'isPrimary': True}]}
        )
        # Samsung S24-style mobile: 384 CSS px at dpr 3.75.
        screen = {'width': 384, 'height': 832, 'device_pixel_ratio': 3.75}

        await FingerprintApplier(fp_tab)._apply_headless_screen(screen)

        params = fake_conn.last_command('Emulation.updateScreen')['params']
        assert params['devicePixelRatio'] == 4
        assert params['width'] == 384 * 4
        assert params['height'] == 832 * 4

    async def test_missing_dpr_defaults_to_one(self, fp_tab, fake_conn):
        fp_tab._browser.options.headless = True
        fake_conn.set_response(
            'Emulation.getScreenInfos', {'screenInfos': [{'id': '1', 'isPrimary': True}]}
        )

        await FingerprintApplier(fp_tab)._apply_headless_screen({'width': 1920, 'height': 1080})

        params = fake_conn.last_command('Emulation.updateScreen')['params']
        assert params['devicePixelRatio'] == 1
        assert params['width'] == 1920
        assert 'colorDepth' not in params
        assert 'workAreaInsets' not in params

    async def test_headful_does_not_touch_screen(self, fp_tab, fake_conn):
        fp_tab._browser.options.headless = False

        await FingerprintApplier(fp_tab)._apply_headless_screen(
            {'width': 1440, 'height': 900, 'device_pixel_ratio': 2.0}
        )

        assert fake_conn.commands_for('Emulation.getScreenInfos') == []
        assert fake_conn.commands_for('Emulation.updateScreen') == []

    async def test_headless_skips_when_no_screen_returned(self, fp_tab, fake_conn):
        fp_tab._browser.options.headless = True

        await FingerprintApplier(fp_tab)._apply_headless_screen({'width': 1440, 'height': 900})

        assert fake_conn.commands_for('Emulation.getScreenInfos')
        assert fake_conn.commands_for('Emulation.updateScreen') == []

    async def test_apply_fingerprint_wires_update_screen_in_headless(self, fp_tab, fake_conn):
        fp_tab._browser.options.headless = True
        fake_conn.set_response(
            'Emulation.getScreenInfos', {'screenInfos': [{'id': '1', 'isPrimary': True}]}
        )

        await fp_tab.apply_fingerprint({'screen': {'width': 1440, 'height': 900,
                                                   'avail_height': 860, 'avail_top': 25,
                                                   'device_pixel_ratio': 2.0}})

        assert fake_conn.commands_for('Emulation.updateScreen')


class TestCrossOriginIframes:
    """The ``cross_origin_iframes`` option that reaches OOPIF targets.

    OOPIFs attach on the tab connection paused; the single tab handler branches by
    target type, replays the full identity on the iframe session, and resumes last.
    FakeConnection does not fire callbacks, so the handler is invoked directly with a
    simulated ``Target.attachedToTarget`` iframe event.
    """

    FP = {
        'user_agent': UA,
        'timezone': 'America/New_York',
        'hardware': {'hardware_concurrency': 8, 'device_memory': 8},
        'screen': {'width': 1920, 'height': 1080},
        'media_features': {'color_gamut': 'srgb'},
    }

    @staticmethod
    async def _fire_iframe_attach(fake_conn, session_id='oopif-1'):
        event = {
            'params': {
                'sessionId': session_id,
                'targetInfo': {'type': 'iframe', 'url': ''},
                'waitingForDebugger': True,
            }
        }
        for callback in fake_conn.callbacks_for('Target.attachedToTarget'):
            await callback(event)
        # Tab.on wraps handlers in asyncio.create_task; let those tasks run.
        await asyncio.sleep(0.05)

    async def test_default_enables_iframe_auto_attach(self, fp_tab, fake_conn):
        await fp_tab.apply_fingerprint(dict(self.FP))
        tab_filter = fake_conn.commands_for('Target.setAutoAttach')[0]['params']['filter']
        assert {entry['type'] for entry in tab_filter} == {'worker', 'iframe'}

    async def test_disabled_keeps_worker_only_filter(self, fp_tab, fake_conn):
        await fp_tab.apply_fingerprint(dict(self.FP), cross_origin_iframes=False)
        tab_filter = fake_conn.commands_for('Target.setAutoAttach')[0]['params']['filter']
        assert {entry['type'] for entry in tab_filter} == {'worker'}

    async def test_iframe_attach_replays_full_identity(self, fp_tab, fake_conn):
        await fp_tab.apply_fingerprint(dict(self.FP))
        await self._fire_iframe_attach(fake_conn)

        methods = [c['method'] for c in fake_conn.commands if c.get('sessionId') == 'oopif-1']
        assert 'Emulation.setUserAgentOverride' in methods
        assert 'Emulation.setTimezoneOverride' in methods
        assert 'Emulation.setHardwareConcurrencyOverride' in methods
        assert 'Emulation.setDeviceMetricsOverride' in methods
        assert 'Emulation.setEmulatedMedia' in methods
        assert 'Page.enable' in methods
        assert 'Page.addScriptToEvaluateOnNewDocument' in methods
        assert 'Runtime.runIfWaitingForDebugger' in methods
        # Page enabled before the script; the target resumed last.
        assert methods.index('Page.enable') < methods.index('Page.addScriptToEvaluateOnNewDocument')
        assert methods.index('Page.addScriptToEvaluateOnNewDocument') < methods.index(
            'Runtime.runIfWaitingForDebugger'
        )

    async def test_iframe_attach_still_resumes_when_a_command_is_rejected(self, fp_tab, fake_conn):
        await fp_tab.apply_fingerprint(dict(self.FP))
        fake_conn.set_failure(
            'Emulation.setUserAgentOverride', -32001, 'Session with given id not found.'
        )
        await self._fire_iframe_attach(fake_conn)
        methods = [c['method'] for c in fake_conn.commands if c.get('sessionId') == 'oopif-1']
        assert 'Runtime.runIfWaitingForDebugger' in methods

    async def test_iframe_attach_not_replayed_when_disabled(self, fp_tab, fake_conn):
        await fp_tab.apply_fingerprint(dict(self.FP), cross_origin_iframes=False)
        await self._fire_iframe_attach(fake_conn)

        methods = [c['method'] for c in fake_conn.commands if c.get('sessionId') == 'oopif-1']
        assert 'Page.addScriptToEvaluateOnNewDocument' not in methods
        assert 'Emulation.setUserAgentOverride' not in methods
        # A paused iframe is still resumed so it never hangs.
        assert 'Runtime.runIfWaitingForDebugger' in methods


class TestNativeFirst:
    """Signals with a CDP path are applied natively; the JS script never carries them."""

    async def test_permissions_applied_via_browser_set_permission(self, fake_conn):
        chrome = Chrome()
        chrome._connection_handler = fake_conn
        tab = Tab(
            browser=chrome,
            target_id='perm-tab',
            connection_handler=fake_conn,
            browser_context_id='ctx-perm',
        )

        await tab.apply_fingerprint(
            {'permissions': {'overrides': {'notifications': 'denied', 'geolocation': 'prompt'}}}
        )

        commands = fake_conn.commands_for('Browser.setPermission')
        states = {c['params']['permission']['name']: c['params']['setting'] for c in commands}
        assert states == {'notifications': 'denied', 'geolocation': 'prompt'}
        assert all(c['params']['browserContextId'] == 'ctx-perm' for c in commands)
        assert not fake_conn.commands_for('Page.addScriptToEvaluateOnNewDocument')

    async def test_touch_emulation_enabled_for_touch_profiles(self, fp_tab, fake_conn):
        await fp_tab.apply_fingerprint({'hardware': {'max_touch_points': 10}})
        params = fake_conn.last_command('Emulation.setTouchEmulationEnabled')['params']
        assert params == {'enabled': True, 'maxTouchPoints': 10}

    async def test_touch_emulation_untouched_for_desktop_profiles(self, fp_tab, fake_conn):
        await fp_tab.apply_fingerprint({'hardware': {'max_touch_points': 0}})
        assert not fake_conn.commands_for('Emulation.setTouchEmulationEnabled')

    async def test_languages_reach_page_only_through_accept_language(self, fp_tab, fake_conn):
        await fp_tab.apply_fingerprint({'user_agent': UA, 'locale': {'languages': ['pt-BR', 'pt']}})
        ua_params = fake_conn.last_command('Emulation.setUserAgentOverride')['params']
        assert ua_params['acceptLanguage'] == 'pt-BR,pt'
        assert fake_conn.last_command('Emulation.setLocaleOverride')['params']['locale'] == 'pt_BR'
        assert not fake_conn.commands_for('Page.addScriptToEvaluateOnNewDocument')

    async def test_client_hints_override_parsed_metadata(self, fp_tab, fake_conn):
        await fp_tab.apply_fingerprint(
            {
                'user_agent': UA,
                'client_hints': {'platform_version': '13.0.0', 'form_factors': ['Desktop']},
            }
        )
        metadata = fake_conn.last_command('Emulation.setUserAgentOverride')['params'][
            'userAgentMetadata'
        ]
        assert metadata['platformVersion'] == '13.0.0'
        assert metadata['formFactors'] == ['Desktop']

    async def test_worker_session_auto_attaches_nested_workers(self, fp_tab, fake_conn):
        await fp_tab.apply_fingerprint({'user_agent': UA})
        event = {
            'params': {
                'sessionId': 'worker-1',
                'targetInfo': {'type': 'worker', 'url': ''},
                'waitingForDebugger': True,
            }
        }
        for callback in fake_conn.callbacks_for('Target.attachedToTarget'):
            await callback(event)
        await asyncio.sleep(0.05)

        nested = [
            c for c in fake_conn.commands_for('Target.setAutoAttach')
            if c.get('sessionId') == 'worker-1'
        ]
        assert nested
        assert nested[0]['params']['waitForDebuggerOnStart'] is True
        assert {entry['type'] for entry in nested[0]['params']['filter']} == {'worker'}


class TestScreenNativePaths:
    SCREEN = {
        'width': 1920,
        'height': 1080,
        'avail_height': 1040,
        'outer_width': 1920,
        'outer_height': 1040,
        'inner_width': 1903,
        'inner_height': 969,
        'device_pixel_ratio': 1.0,
    }

    async def test_headless_screen_is_fully_native(self, fp_tab, fake_conn):
        fp_tab._browser.options.headless = True
        fake_conn.set_response(
            'Emulation.getScreenInfos', {'screenInfos': [{'id': '1', 'isPrimary': True}]}
        )
        fake_conn.set_response('Browser.getWindowForTarget', {'windowId': 7, 'bounds': {}})

        await fp_tab.apply_fingerprint({'screen': dict(self.SCREEN)})

        assert not fake_conn.commands_for('Emulation.setDeviceMetricsOverride')
        assert fake_conn.commands_for('Emulation.updateScreen')
        bounds = fake_conn.last_command('Browser.setWindowBounds')['params']
        assert bounds['windowId'] == 7
        assert bounds['bounds']['width'] == 1920
        assert bounds['bounds']['height'] == 1040
        assert not fake_conn.commands_for('Page.addScriptToEvaluateOnNewDocument')

    async def test_headful_keeps_screen_override_and_js_extras(self, fp_tab, fake_conn):
        fp_tab._browser.options.headless = False
        fake_conn.set_response('Browser.getWindowForTarget', {'windowId': 7, 'bounds': {}})

        await fp_tab.apply_fingerprint({'screen': dict(self.SCREEN)})

        metrics = fake_conn.last_command('Emulation.setDeviceMetricsOverride')['params']
        assert metrics['screenWidth'] == 1920
        assert fake_conn.commands_for('Browser.setWindowBounds')
        script = fake_conn.last_command('Page.addScriptToEvaluateOnNewDocument')['params']
        assert 'availHeight' in script['source']
        assert 'outerWidth' not in script['source']

    async def test_headless_fractional_dpr_overrides_dpr_without_screen_size(
        self, fp_tab, fake_conn
    ):
        fp_tab._browser.options.headless = True
        fake_conn.set_response(
            'Emulation.getScreenInfos', {'screenInfos': [{'id': '1', 'isPrimary': True}]}
        )
        screen = dict(self.SCREEN, device_pixel_ratio=1.25)

        await fp_tab.apply_fingerprint({'screen': screen})

        metrics = fake_conn.last_command('Emulation.setDeviceMetricsOverride')['params']
        assert metrics['deviceScaleFactor'] == 1.25
        assert metrics['width'] == 0
        assert 'screenWidth' not in metrics

    async def test_headless_mobile_keeps_viewport_override(self, fp_tab, fake_conn):
        fp_tab._browser.options.headless = True
        fake_conn.set_response(
            'Emulation.getScreenInfos', {'screenInfos': [{'id': '1', 'isPrimary': True}]}
        )
        screen = {'width': 384, 'height': 832, 'inner_width': 384, 'inner_height': 728,
                  'device_pixel_ratio': 3.75}

        await fp_tab.apply_fingerprint({'mobile': True, 'screen': screen})

        metrics = fake_conn.last_command('Emulation.setDeviceMetricsOverride')['params']
        assert metrics['mobile'] is True
        assert metrics['width'] == 384
        assert 'screenWidth' not in metrics

    async def test_no_window_bounds_without_outer_size(self, fp_tab, fake_conn):
        await fp_tab.apply_fingerprint({'screen': {'width': 1920, 'height': 1080}})
        assert not fake_conn.commands_for('Browser.getWindowForTarget')

    def test_page_js_config_strips_native_screen(self):
        fingerprint = {'screen': dict(self.SCREEN), 'hardware': {'device_memory': 8}}
        headless = FingerprintApplier._page_js_config(fingerprint, headless=True)
        headful = FingerprintApplier._page_js_config(fingerprint, headless=False)
        assert 'screen' not in headless
        assert headless['hardware'] == {'device_memory': 8}
        assert 'outer_width' not in headful['screen']
        assert headful['screen']['avail_height'] == 1040
        assert fingerprint['screen']['outer_width'] == 1920


class TestScriptFetchOverride:
    """Browser-process script fetches (service worker, nested worker) get the profile headers."""

    EVENT = {
        'params': {
            'requestId': 'req-1',
            'frameId': 'fp-tab',
            'resourceType': 'Other',
            'request': {
                'url': 'http://127.0.0.1/sw.js',
                'headers': {'User-Agent': 'real', 'Accept-Language': 'pt-BR', 'Accept': '*/*'},
            },
        }
    }

    async def test_enables_fetch_for_other_resources_once(self, fp_tab, fake_conn):
        await fp_tab.apply_fingerprint({'user_agent': UA, 'locale': {'languages': ['en-US', 'en']}})
        enables = fake_conn.commands_for('Fetch.enable')
        assert len(enables) == 1
        pattern = enables[0]['params']['patterns'][0]
        assert pattern['resourceType'] == 'Other'
        assert pattern['requestStage'] == 'Request'
        assert fake_conn.callbacks_for('Fetch.requestPaused')

    async def test_paused_script_fetch_gets_profile_headers(self, fp_tab, fake_conn):
        await fp_tab.apply_fingerprint({'user_agent': UA, 'locale': {'languages': ['en-US', 'en']}})
        for callback in fake_conn.callbacks_for('Fetch.requestPaused'):
            await callback(self.EVENT)
        await asyncio.sleep(0.05)

        params = fake_conn.last_command('Fetch.continueRequest')['params']
        headers = {h['name']: h['value'] for h in params['headers']}
        assert params['requestId'] == 'req-1'
        assert headers['User-Agent'] == UA
        assert headers['Accept-Language'] == 'en-US,en;q=0.9'
        assert headers['Accept'] == '*/*'

    @staticmethod
    def _two_contexts(fake_conn):
        chrome = Chrome()
        chrome._connection_handler = fake_conn
        first = Tab(browser=chrome, target_id='t1', connection_handler=fake_conn, browser_context_id='c1')
        second = Tab(browser=chrome, target_id='t2', connection_handler=fake_conn, browser_context_id='c2')
        return chrome, first, second

    async def test_worker_target_id_resolves_its_context_fingerprint(self, fake_conn):
        """The frameId of a service worker script fetch is the worker target's id,
        so the context comes from Target.getTargetInfo, not from a tab lookup."""
        chrome, first, second = self._two_contexts(fake_conn)
        await first.apply_fingerprint({'user_agent': UA, 'locale': {'languages': ['en-US', 'en']}})
        await second.apply_fingerprint(
            {'user_agent': UA.replace('151', '150'), 'locale': {'languages': ['pt-BR', 'pt']}}
        )
        fake_conn.set_response(
            'Target.getTargetInfo',
            {'targetInfo': {'targetId': 'sw-1', 'type': 'service_worker', 'browserContextId': 'c2'}},
        )
        event = {'params': dict(self.EVENT['params'], frameId='sw-1')}
        for callback in fake_conn.callbacks_for('Fetch.requestPaused'):
            await callback(event)
        await asyncio.sleep(0.05)

        assert fake_conn.last_command('Target.getTargetInfo')['params']['targetId'] == 'sw-1'
        params = fake_conn.last_command('Fetch.continueRequest')['params']
        headers = {h['name']: h['value'] for h in params['headers']}
        assert '150' in headers['User-Agent']
        assert headers['Accept-Language'] == 'pt-BR,pt;q=0.9'

    async def test_request_continues_untouched_without_a_matching_profile(self, fake_conn):
        chrome, first, second = self._two_contexts(fake_conn)
        await first.apply_fingerprint({'user_agent': UA})
        await second.apply_fingerprint({'user_agent': UA.replace('151', '150')})
        fake_conn.set_response('Target.getTargetInfo', {'targetInfo': {'targetId': 'x', 'type': 'worker'}})
        event = {'params': dict(self.EVENT['params'], frameId='unknown-frame')}
        for callback in fake_conn.callbacks_for('Fetch.requestPaused'):
            await callback(event)
        await asyncio.sleep(0.05)

        params = fake_conn.last_command('Fetch.continueRequest')['params']
        assert 'headers' not in params

    async def test_fetch_override_registered_once_per_browser(self, fake_conn):
        chrome, first, second = self._two_contexts(fake_conn)
        await first.apply_fingerprint({'user_agent': UA})
        await chrome.delete_browser_context('c1')
        await second.apply_fingerprint({'user_agent': UA})
        assert len(fake_conn.commands_for('Fetch.enable')) == 1
        assert len(fake_conn.callbacks_for('Fetch.requestPaused')) == 1

    def test_accept_language_header_matches_chrome_shape(self):
        assert FingerprintApplier._accept_language_header(['pt-BR', 'pt', 'en-US', 'en']) == (
            'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7'
        )
