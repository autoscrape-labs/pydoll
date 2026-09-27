"""The generated sync APIs against real Chrome, including callbacks that call back in."""

from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest

from pydoll.browser.options import ChromiumOptions
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
