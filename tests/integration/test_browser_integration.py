"""Real-Chrome integration tests for the Browser lifecycle and management API.

These launch an actual Chrome to exercise behaviour that depends on a live
browser process and CDP: starting, opening tabs, browser contexts, cookies,
version and targets. Browser-level command shaping (download behaviour,
permissions, window bounds) is covered against an in-memory FakeConnection in
the unit suite.
"""

from __future__ import annotations

import pytest

from pydoll.browser.chromium import Chrome
from pydoll.browser.chromium.tab import Tab


@pytest.mark.asyncio
async def test_start_returns_a_tab_and_reports_version(ci_chrome_options):
    async with Chrome(options=ci_chrome_options) as browser:
        tab = await browser.start()
        assert isinstance(tab, Tab)
        version = await browser.get_version()
        assert 'browserName' in version
        assert 'browserVersion' in version


@pytest.mark.asyncio
async def test_new_tab_increases_opened_tabs(ci_chrome_options):
    async with Chrome(options=ci_chrome_options) as browser:
        await browser.start()
        before = await browser.get_opened_tabs()
        opened = await browser.new_tab()
        assert isinstance(opened, Tab)
        after = await browser.get_opened_tabs()
        assert len(after) > len(before)


@pytest.mark.asyncio
async def test_browser_context_create_list_and_delete(ci_chrome_options):
    async with Chrome(options=ci_chrome_options) as browser:
        await browser.start()
        context_id = await browser.create_browser_context()
        assert context_id in await browser.get_browser_contexts()
        await browser.delete_browser_context(context_id)
        assert context_id not in await browser.get_browser_contexts()


@pytest.mark.asyncio
async def test_new_tab_is_created_in_requested_context(ci_chrome_options):
    async with Chrome(options=ci_chrome_options) as browser:
        await browser.start()
        context_id = await browser.create_browser_context()
        tab = await browser.new_tab(browser_context_id=context_id)
        assert isinstance(tab, Tab)
        assert tab._browser_context_id == context_id


@pytest.mark.asyncio
async def test_set_then_get_cookies_roundtrip(ci_chrome_options):
    async with Chrome(options=ci_chrome_options) as browser:
        await browser.start()
        await browser.set_cookies(
            [{'name': 'session', 'value': 'abc', 'domain': 'example.com', 'path': '/'}]
        )
        cookies = await browser.get_cookies()
        assert any(c['name'] == 'session' and c['value'] == 'abc' for c in cookies)


@pytest.mark.asyncio
async def test_get_targets_includes_a_page(ci_chrome_options):
    async with Chrome(options=ci_chrome_options) as browser:
        await browser.start()
        targets = await browser._get_targets()
        assert isinstance(targets, list)
        assert any(target.get('type') == 'page' for target in targets)
