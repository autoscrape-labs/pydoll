"""Page, BrowserContext and Browser behaviour against real Chrome."""

from __future__ import annotations

import math
import time

import pytest

from _pages import page_url
from pydoll.playwright.async_api import Error, TargetClosedError, TimeoutError, async_playwright
from pydoll.utils.user_agent_parser import UserAgentParser

LAUNCH_ARGS = ['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage']


class TestLifecycle:
    @pytest.mark.asyncio
    async def test_launch_context_page_and_close(self, playwright):
        browser = await playwright.chromium.launch(headless=True, args=['--no-sandbox'], timeout=60_000)
        assert browser.is_connected()
        assert browser.version
        assert browser.contexts == []
        context = await browser.new_context()
        page = await context.new_page()
        assert context.pages == [page]
        assert browser.contexts == [context]
        await page.close()
        assert page.is_closed()
        assert context.pages == []
        await browser.close()
        assert not browser.is_connected()

    @pytest.mark.asyncio
    async def test_browser_new_page_owns_its_context(self, pw_browser):
        page = await pw_browser.new_page()
        assert len(pw_browser.contexts) == 1
        await page.close()
        assert pw_browser.contexts == []

    @pytest.mark.asyncio
    async def test_firefox_and_webkit_are_rejected(self, playwright):
        with pytest.raises(Error, match='only chromium'):
            await playwright.firefox.launch()

    @pytest.mark.asyncio
    async def test_page_close_event_and_target_closed(self, context):
        page = await context.new_page()
        closed = []
        page.on('close', lambda p: closed.append(p))
        await page.close()
        assert closed == [page]

    @pytest.mark.asyncio
    async def test_leaving_async_playwright_stops_the_browsers_it_launched(self):
        async with async_playwright() as instance:
            browser = await instance.chromium.launch(headless=True, args=LAUNCH_ARGS, timeout=60_000)
            page = await browser.new_page()
            await page.goto(page_url('test_core_simple.html'))
            process = browser.chrome._browser_process_manager._process
            assert process is not None and process.poll() is None
        assert not browser.is_connected()
        assert page.is_closed()
        assert process.poll() is not None

    @pytest.mark.asyncio
    async def test_browser_close_stops_the_process_it_launched(self, playwright):
        browser = await playwright.chromium.launch(headless=True, args=LAUNCH_ARGS, timeout=60_000)
        process = browser.chrome._browser_process_manager._process
        await browser.close()
        assert process is not None and process.poll() is not None

    @pytest.mark.asyncio
    async def test_calls_after_close_raise_target_closed_error(self, playwright, context):
        page = await context.new_page()
        await page.goto(page_url('test_core_simple.html'))
        await page.close()
        with pytest.raises(TargetClosedError):
            await page.evaluate('1 + 1')
        with pytest.raises(TargetClosedError):
            await page.locator('#main-heading').text_content(timeout=500)
        browser = await playwright.chromium.launch(headless=True, args=LAUNCH_ARGS, timeout=60_000)
        other = await browser.new_page()
        await browser.close()
        with pytest.raises(TargetClosedError):
            await other.title()
        with pytest.raises(TargetClosedError):
            await browser.new_context()

    @pytest.mark.asyncio
    async def test_connect_over_cdp_accepts_an_http_endpoint(self, playwright):
        launched = await playwright.chromium.launch(headless=True, args=LAUNCH_ARGS, timeout=60_000)
        try:
            attached = await playwright.chromium.connect_over_cdp(
                f'http://localhost:{launched.chrome._connection_port}'
            )
            try:
                assert attached.is_connected()
                page = await (await attached.new_context()).new_page()
                await page.goto(page_url('test_core_simple.html'))
                assert await page.title()
            finally:
                await attached.close()
            assert launched.is_connected()
            assert await launched.chrome.get_version()
        finally:
            await launched.close()
        with pytest.raises(Error, match='DevTools endpoint'):
            await playwright.chromium.connect_over_cdp('http://127.0.0.1:1', timeout=500)


class TestNavigation:
    @pytest.mark.asyncio
    async def test_goto_returns_response_and_updates_url(self, page, http_server):
        response = await page.goto(f'{http_server}/test_core_simple.html')
        assert response is not None
        assert response.status == 200
        assert response.ok
        assert response.url == f'{http_server}/test_core_simple.html'
        assert page.url == f'{http_server}/test_core_simple.html'
        assert 'text/html' in (await response.header_value('content-type') or '')
        assert 'main-heading' in await response.text()

    @pytest.mark.asyncio
    async def test_goto_follows_redirects(self, page, http_server):
        response = await page.goto(f'{http_server}/redirect')
        assert response is not None
        assert response.status == 200
        assert page.url.endswith('/test_core_simple.html')
        assert response.request.redirected_from is not None
        assert response.request.redirected_from.url == f'{http_server}/redirect'

    @pytest.mark.asyncio
    async def test_goto_failure_raises_error(self, page):
        with pytest.raises(Error, match='ERR_NAME_NOT_RESOLVED'):
            await page.goto('http://nonexistent.invalid/')

    @pytest.mark.asyncio
    async def test_wait_until_and_load_states(self, page):
        await page.goto(page_url('playwright_events.html'), wait_until='domcontentloaded')
        await page.wait_for_load_state('load')
        await page.wait_for_load_state('networkidle')
        assert await page.evaluate('() => window.__loaded') is True

    @pytest.mark.asyncio
    async def test_reload_back_forward(self, page):
        await page.goto(page_url('playwright_events.html'))
        await page.goto(page_url('test_core_simple.html'))
        await page.go_back()
        assert page.url.endswith('playwright_events.html')
        await page.go_forward()
        assert page.url.endswith('test_core_simple.html')
        await page.evaluate('() => { window.__marker = 1 }')
        await page.reload()
        assert await page.evaluate('() => window.__marker') is None

    @pytest.mark.asyncio
    async def test_wait_for_url_and_same_document_navigation(self, page):
        await page.goto(page_url('playwright_events.html'))
        await page.click('#hash-link')
        await page.wait_for_url('**/playwright_events.html#section')
        assert page.url.endswith('#section')

    @pytest.mark.asyncio
    async def test_expect_navigation_around_a_click(self, page):
        await page.goto(page_url('playwright_events.html'))
        async with page.expect_navigation() as info:
            await page.click('#page-link')
        await info.value
        assert page.url.endswith('test_core_simple.html')

    @pytest.mark.asyncio
    async def test_navigation_timeout(self, page, http_server):
        with pytest.raises(TimeoutError, match='Timeout 1ms exceeded'):
            await page.goto(f'{http_server}/test_core_simple.html', timeout=1)

    @pytest.mark.asyncio
    async def test_goto_wait_until_commit_resolves(self, page, http_server):
        response = await page.goto(
            f'{http_server}/test_core_simple.html', wait_until='commit', timeout=5000
        )
        assert response is not None and response.status == 200
        assert page.url == f'{http_server}/test_core_simple.html'
        await page.wait_for_load_state('load')
        assert await page.title() == 'Core Test Page'

    @pytest.mark.asyncio
    async def test_goto_without_a_network_request_returns_promptly(self, page):
        await page.goto(page_url('test_core_simple.html'))
        started = time.monotonic()
        assert await page.goto('about:blank', timeout=5000) is None
        assert time.monotonic() - started < 1
        assert page.url == 'about:blank'

    @pytest.mark.asyncio
    async def test_base_url_resolves_relative_paths(self, pw_browser, http_server):
        context = await pw_browser.new_context(base_url=http_server)
        page = await context.new_page()
        await page.goto('/test_core_simple.html')
        assert page.url == f'{http_server}/test_core_simple.html'
        await context.close()


class TestContent:
    @pytest.mark.asyncio
    async def test_title_content_set_content(self, page):
        await page.goto(page_url('test_core_simple.html'))
        assert await page.title()
        assert '<html' in await page.content()
        await page.set_content('<!DOCTYPE html><html><body><p id="p">set</p></body></html>')
        assert await page.text_content('#p') == 'set'
        assert (await page.content()).startswith('<!DOCTYPE html>')

    @pytest.mark.asyncio
    async def test_evaluate_expressions_functions_and_arguments(self, page):
        await page.goto(page_url('test_core_simple.html'))
        assert await page.evaluate('1 + 1') == 2
        assert await page.evaluate('() => 7') == 7
        assert await page.evaluate('async x => x * 2', 21) == 42
        assert await page.evaluate('({a, b}) => a + b', {'a': 1, 'b': 2}) == 3
        assert await page.evaluate('([a, b]) => [b, a]', [1, 2]) == [2, 1]
        assert await page.evaluate('() => undefined') is None
        assert await page.evaluate('() => document.body') is None
        assert await page.evaluate('() => window') is None
        assert math.isnan(await page.evaluate('() => NaN'))
        assert await page.evaluate('x => x', float('inf')) == float('inf')
        assert await page.evaluate('() => new Map([["k", 1]])') == {'k': 1}
        assert await page.evaluate('() => ({ nested: { list: [1, { deep: true }] } })') == {
            'nested': {'list': [1, {'deep': True}]}
        }

    @pytest.mark.asyncio
    async def test_evaluate_errors_surface_as_error(self, page):
        await page.goto(page_url('test_core_simple.html'))
        with pytest.raises(Error, match='boom'):
            await page.evaluate('() => { throw new Error("boom") }')
        with pytest.raises(Error, match='SyntaxError'):
            await page.evaluate('() => {')

    @pytest.mark.asyncio
    async def test_handles_round_trip(self, page):
        await page.goto(page_url('test_core_simple.html'))
        handle = await page.evaluate_handle('() => ({ n: 5, el: document.body })')
        assert await handle.evaluate('o => o.n') == 5
        assert await page.evaluate('([o, extra]) => o.n + extra', [handle, 1]) == 6
        props = await handle.get_properties()
        assert set(props) == {'n', 'el'}
        assert props['el'].as_element() is None
        await handle.dispose()
        element = await page.evaluate_handle('() => document.querySelector("#main-heading")')
        assert element.as_element() is not None
        assert await element.as_element().text_content()
        assert await page.evaluate('e => e.id', element) == 'main-heading'
        assert await page.evaluate('(...args) => args.length', None) == 1

    @pytest.mark.asyncio
    async def test_query_selector_and_wait_for_selector(self, page):
        await page.goto(page_url('playwright_events.html'))
        assert await page.query_selector('#nope') is None
        assert len(await page.query_selector_all('button')) > 3
        handle = await page.query_selector('#title')
        assert handle is not None
        assert await handle.get_attribute('id') == 'title'
        with pytest.raises(TimeoutError):
            await page.wait_for_selector('#delayed-btn', timeout=200)
        await page.click('#reveal')
        found = await page.wait_for_selector('#delayed-btn')
        assert found is not None
        assert await found.is_visible()
        assert await page.wait_for_selector('#nope', state='detached', timeout=500) is None

    @pytest.mark.asyncio
    async def test_wait_for_function_and_timeout(self, page):
        await page.goto(page_url('test_core_simple.html'))
        await page.evaluate('() => setTimeout(() => { window.__ready = "yes" }, 100)')
        handle = await page.wait_for_function('() => window.__ready')
        assert await handle.json_value() == 'yes'
        with pytest.raises(TimeoutError):
            await page.wait_for_function('() => false', timeout=200)

    @pytest.mark.asyncio
    async def test_eval_on_selector(self, page):
        await page.goto(page_url('test_core_simple.html'))
        assert (
            await page.eval_on_selector('#main-heading', '(e, suffix) => e.id + suffix', '!')
            == 'main-heading!'
        )
        assert await page.eval_on_selector_all('#list li', 'items => items.length') == 3
        with pytest.raises(Error, match='Failed to find element'):
            await page.eval_on_selector('#nope', 'e => e')

    @pytest.mark.asyncio
    async def test_add_init_script_script_tag_style_tag(self, page):
        await page.add_init_script('window.__init = 42')
        await page.goto(page_url('test_core_simple.html'))
        assert await page.evaluate('() => window.__init') == 42
        await page.add_script_tag(content='window.__tag = 1')
        assert await page.evaluate('() => window.__tag') == 1
        await page.add_style_tag(content='body { margin: 7px }')
        assert await page.evaluate('() => getComputedStyle(document.body).margin') == '7px'

    @pytest.mark.asyncio
    async def test_expose_function_and_binding(self, page):
        await page.expose_function('add', lambda a, b: a + b)
        await page.expose_binding('who', lambda source, name: f'{name}@{source["page"].url[:4]}')
        await page.goto(page_url('test_core_simple.html'))
        assert await page.evaluate('async () => add(2, 3)') == 5
        assert await page.evaluate('async () => who("me")') == 'me@file'

    @pytest.mark.asyncio
    async def test_exposed_function_with_unserializable_result_rejects_in_page(self, page):
        await page.expose_function('weird', lambda: {1, 2})
        await page.goto(page_url('test_core_simple.html'))
        outcome = await page.evaluate(
            'async () => weird().then(() => "resolved", error => error.message)',
        )
        assert 'not JSON serializable' in outcome

    @pytest.mark.asyncio
    async def test_evaluate_accepts_a_trailing_semicolon(self, page):
        await page.goto(page_url('test_core_simple.html'))
        assert await page.evaluate('document.title;') == 'Core Test Page'
        assert await page.evaluate('1 + 1; ') == 2

    @pytest.mark.asyncio
    async def test_wait_for_selector_hidden_and_detached_honour_strict(self, page):
        await page.goto(page_url('playwright_frames.html'))
        with pytest.raises(Error, match='strict mode violation'):
            await page.wait_for_selector('.twin', state='hidden', strict=True, timeout=500)
        with pytest.raises(Error, match='strict mode violation'):
            await page.wait_for_selector('.twin', state='detached', strict=True, timeout=500)
        assert await page.wait_for_selector('.twin', state='hidden', timeout=500) is None


class TestMedia:
    @pytest.mark.asyncio
    async def test_screenshot_and_pdf(self, page, tmp_path):
        await page.goto(page_url('test_core_simple.html'))
        png = await page.screenshot(path=tmp_path / 'shot.png')
        assert png.startswith(b'\x89PNG')
        assert (tmp_path / 'shot.png').read_bytes() == png
        jpeg = await page.screenshot(type='jpeg', quality=50, full_page=True)
        assert jpeg[:2] == b'\xff\xd8'
        clipped = await page.screenshot(clip={'x': 0, 'y': 0, 'width': 20, 'height': 10})
        assert clipped.startswith(b'\x89PNG')
        pdf = await page.pdf(path=tmp_path / 'out.pdf', format='A4')
        assert pdf.startswith(b'%PDF')
        element_png = await page.locator('#main-heading').screenshot()
        assert element_png.startswith(b'\x89PNG')

    @pytest.mark.asyncio
    async def test_viewport_and_emulation(self, page):
        await page.set_viewport_size({'width': 640, 'height': 480})
        await page.goto(page_url('test_core_simple.html'))
        assert await page.evaluate('() => [innerWidth, innerHeight]') == [640, 480]
        assert page.viewport_size == {'width': 640, 'height': 480}
        await page.emulate_media(color_scheme='dark')
        assert (
            await page.evaluate('() => matchMedia("(prefers-color-scheme: dark)").matches') is True
        )


class TestContext:
    @pytest.mark.asyncio
    async def test_context_options_apply_to_pages(self, pw_browser):
        custom_ua = (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'
        )
        context = await pw_browser.new_context(
            viewport={'width': 500, 'height': 400},
            user_agent=custom_ua,
            locale='fr-CA',
            timezone_id='America/Sao_Paulo',
            extra_http_headers={'X-Test': '1'},
        )
        page = await context.new_page()
        await page.goto(page_url('test_core_simple.html'))
        reduced = UserAgentParser.parse(custom_ua).reduced_user_agent or custom_ua
        assert await page.evaluate(
            '() => [innerWidth, innerHeight, navigator.userAgent, navigator.language, navigator.languages]'
        ) == [500, 400, reduced, 'fr-CA', ['fr-CA', 'fr', 'en-US', 'en']]
        assert (
            await page.evaluate('() => Intl.DateTimeFormat().resolvedOptions().timeZone')
            == 'America/Sao_Paulo'
        )
        brands = await page.evaluate('() => navigator.userAgentData.brands.map(b => b.brand)')
        assert any('Chrom' in brand for brand in brands)
        assert await page.evaluate('() => navigator.userAgentData.platform') == 'Windows'
        assert await page.evaluate(
            '() => screen.width >= innerWidth && screen.height >= innerHeight'
        )
        await context.close()

    @pytest.mark.asyncio
    async def test_extra_headers_reach_the_server(self, pw_browser, http_server):
        context = await pw_browser.new_context(
            extra_http_headers={'X-Test': 'value-1'}, locale='pt-BR'
        )
        page = await context.new_page()
        await page.goto(f'{http_server}/echo-headers')
        content = await page.content()
        assert 'value-1' in content
        assert 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7' in content
        assert 'Authorization' not in content
        await context.close()

    @pytest.mark.asyncio
    async def test_cookies_and_storage_state(self, pw_browser, http_server):
        context = await pw_browser.new_context()
        page = await context.new_page()
        await page.goto(f'{http_server}/set-cookie')
        cookies = await context.cookies()
        assert any(cookie['name'] == 'session' and cookie['value'] == 'abc' for cookie in cookies)
        await context.add_cookies([{'name': 'extra', 'value': 'v', 'url': http_server}])
        assert {cookie['name'] for cookie in await context.cookies()} >= {'session', 'extra'}
        await page.evaluate('() => localStorage.setItem("k", "v")')
        state = await context.storage_state()
        assert state['origins'][0]['localStorage'] == [{'name': 'k', 'value': 'v'}]
        await context.clear_cookies()
        assert await context.cookies() == []
        await context.close()

        restored = await pw_browser.new_context(storage_state=state)
        page = await restored.new_page()
        await page.goto(f'{http_server}/test_core_simple.html')
        assert await page.evaluate('() => localStorage.getItem("k")') == 'v'
        assert any(cookie['name'] == 'extra' for cookie in await restored.cookies())
        await restored.close()

    @pytest.mark.asyncio
    async def test_storage_state_covers_origins_without_an_open_page(self, pw_browser, http_server):
        port = http_server.rsplit(':', 1)[1]
        first_origin = http_server
        second_origin = f'http://localhost:{port}'
        context = await pw_browser.new_context()
        page = await context.new_page()
        await page.goto(f'{first_origin}/test_core_simple.html')
        await page.evaluate('() => localStorage.setItem("where", "first")')
        await page.goto(f'{second_origin}/test_core_simple.html')
        await page.evaluate('() => localStorage.setItem("where", "second")')
        state = await context.storage_state()
        by_origin = {entry['origin']: entry['localStorage'] for entry in state['origins']}
        assert by_origin[first_origin] == [{'name': 'where', 'value': 'first'}]
        assert by_origin[second_origin] == [{'name': 'where', 'value': 'second'}]
        assert context.pages == [page]
        await context.close()

    @pytest.mark.asyncio
    async def test_new_context_accepts_a_device_descriptor(self, playwright, pw_browser):
        context = await pw_browser.new_context(**playwright.devices['iPhone 13'])
        page = await context.new_page()
        await page.goto(page_url('test_core_simple.html'))
        assert await page.evaluate('() => navigator.userAgent') == playwright.devices['iPhone 13']['user_agent']
        assert await page.evaluate('() => devicePixelRatio') == 3
        assert await page.evaluate('() => navigator.maxTouchPoints') > 0
        await context.close()

    @pytest.mark.asyncio
    async def test_contexts_are_isolated(self, pw_browser, http_server):
        first = await pw_browser.new_context()
        second = await pw_browser.new_context()
        page = await first.new_page()
        await page.goto(f'{http_server}/set-cookie')
        assert await second.cookies() == []
        await first.close()
        await second.close()

    @pytest.mark.asyncio
    async def test_context_init_script_and_default_timeout(self, pw_browser):
        context = await pw_browser.new_context()
        await context.add_init_script('window.__ctx = "yes"')
        page = await context.new_page()
        await page.goto(page_url('test_core_simple.html'))
        assert await page.evaluate('() => window.__ctx') == 'yes'
        context.set_default_timeout(150)
        with pytest.raises(TimeoutError, match='Timeout 150ms'):
            await page.locator('#nope').click()
        await context.close()

    @pytest.mark.asyncio
    async def test_persistent_context(self, playwright, tmp_path):
        context = await playwright.chromium.launch_persistent_context(
            tmp_path / 'profile', headless=True, args=['--no-sandbox'], timeout=60_000
        )
        assert len(context.pages) == 1
        page = context.pages[0]
        await page.goto(page_url('test_core_simple.html'))
        assert await page.title()
        await context.close()

    @pytest.mark.asyncio
    async def test_closing_a_persistent_context_closes_its_browser(self, playwright, tmp_path):
        context = await playwright.chromium.launch_persistent_context(
            tmp_path / 'owned-profile', headless=True, args=['--no-sandbox'], timeout=60_000
        )
        browser = context.browser
        assert browser is not None
        assert browser.is_connected()
        await context.close()
        assert not browser.is_connected()

    @pytest.mark.asyncio
    async def test_closing_a_browser_page_closes_the_context_made_for_it(self, pw_browser):
        before = len(pw_browser.contexts)
        page = await pw_browser.new_page()
        assert len(pw_browser.contexts) == before + 1
        await page.close()
        assert len(pw_browser.contexts) == before

    @pytest.mark.asyncio
    async def test_set_test_id_attribute_redirects_get_by_test_id(self, playwright, page):
        await page.set_content(
            '<button data-qa="save">By qa</button><button data-testid="save">By testid</button>'
        )
        assert await page.get_by_test_id('save').text_content() == 'By testid'
        playwright.selectors.set_test_id_attribute('data-qa')
        try:
            assert await page.get_by_test_id('save').text_content() == 'By qa'
        finally:
            playwright.selectors.set_test_id_attribute('data-testid')
        assert await page.get_by_test_id('save').text_content() == 'By testid'
