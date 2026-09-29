"""The generated sync APIs against real Chrome, including callbacks that call back in."""

from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest

from pydoll.browser.options import ChromiumOptions
from pydoll.playwright.sync_api import Page, TimeoutError, sync_playwright
from pydoll.protocol.page.events import PageEvent
from pydoll.sync import Chrome, DownloadHandle, SyncError, Tab, WebElement

PAGES = Path(__file__).parent.parent / 'pages'


def page_url(name: str) -> str:
    return f'file://{(PAGES / name).absolute()}'


@pytest.fixture
def options():
    instance = ChromiumOptions()
    instance.headless = True
    instance.add_argument('--no-sandbox')
    instance.add_argument('--disable-gpu')
    return instance


class TestPydollSync:
    def test_browse_find_and_read(self, options):
        with Chrome(options=options) as browser:
            tab = browser.start()
            assert isinstance(tab, Tab)
            tab.go_to(page_url('test_core_simple.html'))
            assert tab.title() == 'Core Test Page'
            assert tab.current_url().endswith('test_core_simple.html')
            button = tab.find(id='btn-1')
            assert isinstance(button, WebElement)
            assert button.text() == 'Click Me'
            assert [item.text() for item in tab.query('#list li', find_all=True)] == [
                'Item 1',
                'Item 2',
                'Item 3',
            ]
            assert tab.find(id='nope', raise_exc=False) is None
            assert tab.execute_script('return 1 + 1', return_by_value=True)['result']['result']['value'] == 2

    def test_actions_and_screenshot(self, options, tmp_path):
        with Chrome(options=options) as browser:
            tab = browser.start()
            tab.go_to(page_url('test_core_simple.html'))
            field = tab.find(id='text-input')
            field.type_text('Ana')
            typed = tab.execute_script(
                'return document.getElementById("text-input").value', return_by_value=True
            )
            assert typed['result']['result']['value'] == 'Ana'
            tab.find(id='btn-1').click()
            assert tab.find(id='btn-1-count').text() == '1'
            tab.take_screenshot(tmp_path / 'shot.png')
            assert (tmp_path / 'shot.png').stat().st_size > 0

    def test_callback_can_call_sync_methods(self, options):
        with Chrome(options=options) as browser:
            tab = browser.start()
            seen: list[tuple[str, str]] = []

            def on_load(event):
                seen.append((threading.current_thread().name, tab.title()))

            tab.enable_page_events()
            tab.on(PageEvent.LOAD_EVENT_FIRED, on_load)
            tab.go_to(page_url('test_core_simple.html'))
            deadline = time.monotonic() + 5
            while not seen and time.monotonic() < deadline:
                time.sleep(0.05)
            assert seen and seen[0][1] == 'Core Test Page'
            assert 'pydoll-sync-callbacks' in seen[0][0]

    def test_expect_download_with_block(self, options):
        with Chrome(options=options) as browser:
            tab = browser.start()
            tab.go_to(page_url('sync_download.html'))
            with tab.expect_download() as download:
                tab.find(id='download-link').click()
                assert isinstance(download, DownloadHandle)
                download.wait_finished()
                assert download.read_bytes() == b'hello download'

    def test_calling_from_loop_thread_is_rejected(self, options):
        from pydoll.sync._runtime import EventLoopThread

        with Chrome(options=options) as browser:
            tab = browser.start()
            tab.go_to(page_url('test_core_simple.html'))
            runtime = EventLoopThread.instance()
            outcome: list[BaseException] = []

            def misuse() -> None:
                try:
                    tab.title()
                except SyncError as error:
                    outcome.append(error)

            runtime.loop.call_soon_threadsafe(misuse)
            deadline = time.monotonic() + 5
            while not outcome and time.monotonic() < deadline:
                time.sleep(0.05)
            assert outcome and isinstance(outcome[0], SyncError)


class TestPlaywrightSync:
    def test_end_to_end_script(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=['--no-sandbox'], timeout=60_000)
            context = browser.new_context(viewport={'width': 800, 'height': 600})
            page = context.new_page()
            assert isinstance(page, Page)
            response = page.goto(page_url('playwright_engine.html'))
            assert response is not None and response.ok
            assert page.title() == 'Engine fixtures'
            assert page.locator('#list li').count() == 3
            assert page.get_by_role('button', name='Save').inner_text() == 'Save'
            page.get_by_label('Full name').fill('Ana')
            assert page.input_value('#name-input') == 'Ana'
            assert page.evaluate('([a, b]) => a + b', [1, 2]) == 3
            assert page.evaluate('() => [innerWidth, innerHeight]') == [800, 600]
            handle = page.query_selector('#title')
            assert handle is not None and handle.text_content() == 'Engine fixtures'
            with pytest.raises(TimeoutError, match='Timeout 200ms'):
                page.locator('#btn-hidden').click(timeout=200)
            frame_text = page.frame_locator('#simple-iframe').locator('#iframe-heading')
            page.goto(page_url('test_iframe_simple.html'))
            assert frame_text.text_content() == 'Iframe Content'
            browser.close()

    def test_handlers_run_off_the_loop_and_call_back_in(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=['--no-sandbox'], timeout=60_000)
            page = browser.new_page()
            page.goto(page_url('playwright_events.html'))
            threads: list[str] = []

            def on_dialog(dialog):
                threads.append(threading.current_thread().name)
                dialog.accept()

            page.on('dialog', on_dialog)
            page.click('#confirm-btn')
            assert page.text_content('#confirm-result') == 'true'
            assert threads and 'pydoll-sync-callbacks' in threads[0]

            def handler(route, request):
                route.fulfill(
                    json={'from': request.method},
                    headers={'Access-Control-Allow-Origin': '*'},
                )

            page.route('**/*.json', handler)
            assert page.evaluate('() => fetch("http://example.invalid/a.json").then(r => r.json())') == {
                'from': 'GET'
            }
            page.expose_function('twice', lambda n: n * 2)
            assert page.evaluate('async () => twice(21)') == 42
            browser.close()

    def test_expect_context_managers(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=['--no-sandbox'], timeout=60_000)
            page = browser.new_page()
            page.goto(page_url('playwright_events.html'))
            with page.expect_download() as info:
                page.click('#download-link')
            assert info.value.suggested_filename == 'hello.txt'
            with page.expect_popup() as popup_info:
                page.click('#popup-btn')
            assert popup_info.value.url == 'about:blank'
            with page.expect_navigation():
                page.click('#page-link')
            assert page.url.endswith('test_core_simple.html')
            with page.expect_console_message() as message_info:
                page.evaluate('() => console.log("sync", 1)')
            assert message_info.value.text == 'sync 1'
            browser.close()
