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
