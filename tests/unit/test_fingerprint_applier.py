"""Unit tests for FingerprintApplier against an in-memory FakeConnection.

A real Tab and its Browser share one FakeConnection so both the tab-scoped and
browser-scoped code paths run without sockets. Assertions check the CDP commands
emitted and the per-tab / per-context state the applier maintains.
"""

from __future__ import annotations

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
