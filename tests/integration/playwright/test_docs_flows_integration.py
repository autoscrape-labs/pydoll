"""The flows the documentation promises, run end to end against real Chrome.

Each test here mirrors a snippet on the "Bring your Playwright script" page or
the Playwright API guide: a script written for Playwright, the ``page.tab``
escape hatch in both API forms, attaching to a browser pydoll already runs, and
the transport promise that a plain script never enables the Runtime domain.
"""

from __future__ import annotations

import pytest

from _pages import page_url
from pydoll import ExtractionModel, Field
from pydoll.browser.tab import Tab
from pydoll.connection import ConnectionHandler
from pydoll.elements.web_element import WebElement
from pydoll.playwright.async_api import Error
from pydoll.playwright.sync_api import sync_playwright
from pydoll.sync import Tab as SyncTab
from pydoll.sync import WebElement as SyncWebElement
from pydoll.utils import get_browser_ws_address

LOGIN_URL = page_url('playwright_login.html')


class Quote(ExtractionModel):
    text: str = Field(selector='.text')
    author: str = Field(selector='.author')


async def _login(page) -> None:
    await page.goto(LOGIN_URL)
    await page.get_by_label('Username').fill('john')
    await page.get_by_label('Password').fill('SecretPass123')
    await page.get_by_role('button', name='Login').click()


class TestBringYourPlaywrightScript:
    @pytest.mark.asyncio
    async def test_login_flow_with_get_by_helpers(self, page):
        await _login(page)
        logout = page.get_by_role('link', name='Logout')
        assert await logout.is_visible()
        assert await page.get_by_text('Welcome, john!').count() == 1
        assert not await page.get_by_role('button', name='Login').is_visible()

    @pytest.mark.asyncio
    async def test_page_tab_is_the_pydoll_tab_and_extract_all_works(self, page):
        await page.goto(LOGIN_URL)
        assert isinstance(page.tab, Tab)
        quotes = await page.tab.extract_all(Quote, scope='.quote', timeout=5)
        assert [quote.author for quote in quotes] == ['Steve Jobs', 'Steve Jobs', 'Leonardo da Vinci']
        assert quotes[1].text == 'Stay hungry, stay foolish.'

    @pytest.mark.asyncio
    async def test_element_handle_exposes_the_web_element_for_humanized_clicks(self, page):
        await page.goto(LOGIN_URL)
        handle = await page.get_by_role('button', name='Clicked 0 times').element_handle()
        element = handle.web_element
        assert isinstance(element, WebElement)
        await element.click(humanize=True)
        assert await page.get_by_role('button', name='Clicked 1 times').count() == 1

    @pytest.mark.asyncio
    async def test_turnstile_handling_is_reachable_through_page_tab(self, page):
        async with page.tab.expect_cloudflare_turnstile(time_to_wait_captcha=0.5):
            await page.goto(LOGIN_URL)
        assert await page.title() == 'Login fixture'

    @pytest.mark.asyncio
    async def test_connect_over_cdp_attaches_to_a_browser_pydoll_already_runs(
        self, playwright, browser
    ):
        endpoint = await get_browser_ws_address(browser._connection_port)
        attached = await playwright.chromium.connect_over_cdp(endpoint)
        try:
            assert attached.is_connected()
            context = await attached.new_context()
            page = await context.new_page()
            await page.goto(LOGIN_URL)
            assert await page.title() == 'Login fixture'
            await context.close()
        finally:
            await attached.close()
        assert await browser.get_version()

    @pytest.mark.asyncio
    async def test_firefox_and_webkit_name_the_limitation(self, playwright):
        with pytest.raises(Error, match='Chromium'):
            await playwright.firefox.launch()
        with pytest.raises(Error, match='Chromium'):
            await playwright.webkit.launch()


class TestTransportPromises:
    @pytest.mark.asyncio
    async def test_a_plain_script_never_enables_runtime_or_console(self, page, monkeypatch):
        """Locating, filling and clicking must not turn on the domains detectors watch."""
        sent: list[str] = []
        original = ConnectionHandler.execute_command

        async def recording(self, command, timeout=60):
            sent.append(str(command.get('method')))
            return await original(self, command, timeout)

        monkeypatch.setattr(ConnectionHandler, 'execute_command', recording)
        await _login(page)
        await page.get_by_role('link', name='Logout').is_visible()
        await page.evaluate('() => document.title')
        assert sent, 'the recording hook did not see any command'
        assert 'Runtime.enable' not in sent
        assert 'Console.enable' not in sent


class TestSyncFlavor:
    def test_sync_login_flow(self, ci_chrome_options):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=ci_chrome_options.arguments, timeout=60_000)
            page = browser.new_page()
            page.goto(LOGIN_URL)
            page.get_by_label('Username').fill('john')
            page.get_by_label('Password').fill('SecretPass123')
            page.get_by_role('button', name='Login').click()
            assert page.get_by_role('link', name='Logout').is_visible()
            browser.close()

    def test_sync_page_tab_is_a_sync_facade(self, ci_chrome_options):
        """The documented escape hatch must block like the rest of the sync API."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=ci_chrome_options.arguments, timeout=60_000)
            page = browser.new_page()
            page.goto(LOGIN_URL)
            tab = page.tab
            assert isinstance(tab, SyncTab)
            assert tab.title() == 'Login fixture'
            quotes = tab.extract_all(Quote, scope='.quote', timeout=5)
            assert len(quotes) == 3
            handle = page.get_by_role('button', name='Clicked 0 times').element_handle()
            assert isinstance(handle.web_element, SyncWebElement)
            handle.web_element.click(humanize=True)
            assert page.get_by_role('button', name='Clicked 1 times').count() == 1
            browser.close()
