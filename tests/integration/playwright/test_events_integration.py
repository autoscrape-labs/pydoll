"""Dialogs, console, downloads, popups, file chooser and network routing."""

from __future__ import annotations

import asyncio

import pytest

from _pages import page_url
from pydoll.playwright.async_api import Error, TimeoutError


class TestDialogs:
    @pytest.mark.asyncio
    async def test_dialogs_are_dismissed_when_unhandled(self, page):
        await page.goto(page_url('playwright_events.html'))
        await page.click('#confirm-btn')
        assert await page.text_content('#confirm-result') == 'false'

    @pytest.mark.asyncio
    async def test_dialog_handler_accepts_with_prompt_text(self, page):
        await page.goto(page_url('playwright_events.html'))
        seen = []

        async def handle(dialog):
            seen.append((dialog.type, dialog.message, dialog.default_value))
            if dialog.type == 'prompt':
                await dialog.accept('typed')
            else:
                await dialog.accept()

        page.on('dialog', handle)
        await page.click('#confirm-btn')
        await page.click('#prompt-btn')
        await page.click('#alert-btn')
        assert await page.text_content('#confirm-result') == 'true'
        assert await page.text_content('#prompt-result') == 'typed'
        assert seen == [('confirm', 'sure?', ''), ('prompt', 'name?', 'dflt'), ('alert', 'hi there', '')]

    @pytest.mark.asyncio
    async def test_expect_event_dialog(self, page):
        await page.goto(page_url('playwright_events.html'))
        page.once('dialog', lambda dialog: asyncio.ensure_future(dialog.dismiss()))
        async with page.expect_event('dialog') as info:
            await page.click('#alert-btn')
        dialog = await info.value
        assert dialog.message == 'hi there'


class TestConsoleAndErrors:
    @pytest.mark.asyncio
    async def test_console_messages(self, page):
        await page.goto(page_url('test_core_simple.html'))
        messages = []
        page.on('console', lambda message: messages.append(message))
        async with page.expect_console_message(lambda m: m.type == 'warning') as info:
            await page.evaluate('() => { console.log("plain", 1, {a: 2}); console.warn("careful") }')
        warning = await info.value
        assert warning.text == 'careful'
        assert warning.type == 'warning'
        assert warning.location['url'] is not None
        log = next(message for message in messages if message.type == 'log')
        assert log.text.startswith('plain 1')
        assert await log.args[1].json_value() == 1

    @pytest.mark.asyncio
    async def test_page_errors(self, page):
        await page.goto(page_url('test_core_simple.html'))
        errors = []
        page.on('pageerror', lambda error: errors.append(error))
        await page.evaluate('() => setTimeout(() => { throw new Error("later") }, 0)')
        await page.wait_for_timeout(200)
        assert errors and 'later' in errors[0].message


class TestDownloadsPopupsFiles:
    @pytest.mark.asyncio
    async def test_download(self, page, tmp_path):
        await page.goto(page_url('playwright_events.html'))
        async with page.expect_download() as info:
            await page.click('#download-link')
        download = await info.value
        assert download.suggested_filename == 'hello.txt'
        path = await download.path()
        assert path.read_text() == 'hello download'
        await download.save_as(tmp_path / 'saved.txt')
        assert (tmp_path / 'saved.txt').read_text() == 'hello download'
        assert await download.failure() is None
        await download.delete()
        assert not path.exists()

    @pytest.mark.asyncio
    async def test_popup(self, page, context):
        await page.goto(page_url('playwright_events.html'))
        async with page.expect_popup() as info:
            await page.click('#popup-btn')
        popup = await info.value
        assert popup.context is context
        assert await popup.opener() is page
        assert len(context.pages) == 2
        await popup.close()
        assert len(context.pages) == 1

    @pytest.mark.asyncio
    async def test_context_expect_page(self, page, context):
        await page.goto(page_url('playwright_events.html'))
        async with context.expect_page() as info:
            await page.click('#popup-btn')
        new_page = await info.value
        assert new_page in context.pages

    @pytest.mark.asyncio
    async def test_file_chooser(self, page, tmp_path):
        await page.goto(page_url('playwright_events.html'))
        upload = tmp_path / 'chosen.txt'
        upload.write_text('data')
        async with page.expect_file_chooser() as info:
            await page.click('#file-input')
        chooser = await info.value
        assert not chooser.is_multiple()
        await chooser.set_files(upload)
        assert await page.text_content('#file-result') == 'chosen.txt'


class TestNetwork:
    @pytest.mark.asyncio
    async def test_request_and_response_events(self, page, http_server):
        requests, responses, finished = [], [], []
        page.on('request', lambda r: requests.append(r))
        page.on('response', lambda r: responses.append(r))
        page.on('requestfinished', lambda r: finished.append(r))
        response = await page.goto(f'{http_server}/test_core_simple.html')
        assert response is not None
        request = response.request
        assert request.method == 'GET'
        assert request.resource_type == 'document'
        assert request.is_navigation_request()
        assert request.frame is page.main_frame
        assert await request.response() is response
        assert requests[0].url == request.url
        assert responses[0].status == 200
        await page.wait_for_load_state('networkidle')
        assert finished
        assert (await response.finished()) is None
        assert response.frame is page.main_frame
        assert (await response.server_addr())['ipAddress'] == '127.0.0.1'

    @pytest.mark.asyncio
    async def test_expect_request_and_response(self, page, http_server):
        await page.goto(f'{http_server}/test_core_simple.html')
        async with page.expect_response('**/echo-headers') as response_info:
            async with page.expect_request(lambda r: r.url.endswith('/echo-headers')) as request_info:
                await page.evaluate('() => fetch("/echo-headers")')
        assert (await request_info.value).url.endswith('/echo-headers')
        assert (await response_info.value).status == 200
        with pytest.raises(TimeoutError):
            async with page.expect_response('**/never', timeout=200):
                pass

    @pytest.mark.asyncio
    async def test_route_fulfill_abort_continue_and_fallback(self, page, http_server):
        await page.goto(f'{http_server}/test_core_simple.html')
        seen = []

        async def logger(route, request):
            seen.append(request.url)
            await route.fallback()

        await page.route('**/data.json', lambda route: route.fulfill(json={'ok': True}, headers={'x-served': 'yes'}))
        await page.route('**/blocked', lambda route: route.abort())
        await page.route(
            '**/echo-headers',
            lambda route: route.continue_(headers={**route.request.headers, 'x-added': '1'}),
        )
        await page.route('**/*', logger)
        assert await page.evaluate('() => fetch("/data.json").then(r => r.json())') == {'ok': True}
        assert await page.evaluate('() => fetch("/data.json").then(r => r.headers.get("x-served"))') == 'yes'
        assert await page.evaluate('() => fetch("/blocked").then(() => "ok", () => "failed")') == 'failed'
        body = await page.evaluate('() => fetch("/echo-headers").then(r => r.text())')
        assert "'X-Added': '1'" in body or "'x-added': '1'" in body
        assert any(url.endswith('/data.json') for url in seen)
        await page.unroute('**/data.json')
        assert await page.evaluate('() => fetch("/data.json").then(r => r.status)') == 404

    @pytest.mark.asyncio
    async def test_route_fetch_and_fulfill_with_response(self, page, http_server):
        await page.goto(f'{http_server}/test_core_simple.html')

        async def handler(route):
            response = await route.fetch()
            text = await response.text()
            await route.fulfill(response=response, body=text.replace('main-heading', 'patched-heading'))

        await page.route('**/test_core_simple.html', handler)
        await page.reload()
        assert await page.query_selector('#patched-heading') is not None

    @pytest.mark.asyncio
    async def test_context_route_and_times(self, pw_browser, http_server):
        context = await pw_browser.new_context()
        calls = []

        async def once(route):
            calls.append(1)
            await route.fulfill(body='once')

        await context.route('**/echo-headers', once, times=1)
        page = await context.new_page()
        await page.goto(f'{http_server}/test_core_simple.html')
        assert await page.evaluate('() => fetch("/echo-headers").then(r => r.text())') == 'once'
        assert 'once' != await page.evaluate('() => fetch("/echo-headers").then(r => r.text())')
        assert calls == [1]
        await context.close()

    @pytest.mark.asyncio
    async def test_response_body_and_json(self, page, http_server):
        await page.goto(f'{http_server}/test_core_simple.html')
        async with page.expect_response('**/echo-headers') as info:
            await page.evaluate('() => fetch("/echo-headers").then(r => r.text())')
        response = await info.value
        assert b'Host' in await response.body()
        with pytest.raises(Error):
            await response.json()

    @pytest.mark.asyncio
    async def test_offline_context(self, pw_browser, http_server):
        context = await pw_browser.new_context(offline=True)
        page = await context.new_page()
        with pytest.raises(Error, match='ERR_INTERNET_DISCONNECTED'):
            await page.goto(f'{http_server}/test_core_simple.html')
        await context.set_offline(False)
        assert (await page.goto(f'{http_server}/test_core_simple.html')).ok
        await context.close()


class TestWaits:
    @pytest.mark.asyncio
    async def test_wait_for_event_with_predicate(self, page):
        await page.goto(page_url('playwright_events.html'))
        page.on('dialog', lambda dialog: asyncio.ensure_future(dialog.dismiss()))
        waiter = asyncio.ensure_future(page.wait_for_event('dialog', predicate=lambda d: d.type == 'alert'))
        await page.click('#alert-btn')
        dialog = await waiter
        assert dialog.type == 'alert'

    @pytest.mark.asyncio
    async def test_wait_for_timeout(self, page):
        await page.wait_for_timeout(50)
