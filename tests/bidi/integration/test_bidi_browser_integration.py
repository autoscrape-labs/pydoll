"""Real-Firefox (WebDriver BiDi) integration tests for the browser lifecycle.

The BiDi counterpart of the applicable parts of
tests/cdp/integration/test_browser_integration.py: Firefox actually starts,
reports its version, opens tabs, navigates, and manages browser contexts — each
asserted by an observable result.
"""

from __future__ import annotations

import pytest

from pydoll.browser import Firefox
from pydoll.browser.firefox.tab import BiDiTab


@pytest.mark.asyncio
async def test_start_returns_a_tab(ci_firefox_options):
    async with Firefox(options=ci_firefox_options) as browser:
        tab = await browser.start()
        assert isinstance(tab, BiDiTab)


@pytest.mark.asyncio
async def test_get_version_reports_browser_name(ci_firefox_options):
    async with Firefox(options=ci_firefox_options) as browser:
        await browser.start()
        version = await browser.get_version()
        assert 'browserName' in version
        assert version['browserName']


@pytest.mark.asyncio
async def test_navigation_reports_current_url_and_title(ci_firefox_options, page_url):
    async with Firefox(options=ci_firefox_options) as browser:
        tab = await browser.start()
        await tab.go_to(page_url('web_element.html'))
        assert 'web_element.html' in (await tab.current_url)
        assert (await tab.title) == 'WebElement Test Page'


@pytest.mark.asyncio
async def test_page_source_reflects_loaded_document(ci_firefox_options, page_url):
    async with Firefox(options=ci_firefox_options) as browser:
        tab = await browser.start()
        await tab.go_to(page_url('web_element.html'))
        source = await tab.page_source
        assert 'WebElement Test Page' in source


@pytest.mark.asyncio
async def test_new_tab_opens_and_navigates(ci_firefox_options, page_url):
    async with Firefox(options=ci_firefox_options) as browser:
        await browser.start()
        tab = await browser.new_tab()
        assert isinstance(tab, BiDiTab)
        await tab.go_to(page_url('web_element.html'))
        assert 'web_element.html' in (await tab.current_url)


@pytest.mark.asyncio
async def test_get_opened_tabs_lists_open_contexts(ci_firefox_options):
    async with Firefox(options=ci_firefox_options) as browser:
        await browser.start()
        await browser.new_tab()
        tabs = await browser.get_opened_tabs()
        assert len(tabs) >= 1
        assert all(isinstance(tab, BiDiTab) for tab in tabs)


@pytest.mark.asyncio
async def test_useragent_override_changes_navigator_user_agent(ci_firefox_options):
    async with Firefox(options=ci_firefox_options) as browser:
        tab = await browser.start()
        await tab.useragent_override('CustomUA/9.9')
        await tab.go_to('data:text/html,<p>ua</p>')
        assert await tab.execute_script('return navigator.userAgent') == 'CustomUA/9.9'


@pytest.mark.asyncio
async def test_browser_context_create_list_and_delete(ci_firefox_options):
    async with Firefox(options=ci_firefox_options) as browser:
        await browser.start()
        context_id = await browser.create_browser_context()
        assert context_id in await browser.get_browser_contexts()
        await browser.delete_browser_context(context_id)
        assert context_id not in await browser.get_browser_contexts()
