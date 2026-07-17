"""Integration tests for nested cross-origin iframe (OOPIF) resolution.

Two HTTP servers on different ports simulate cross-origin boundaries,
triggering Chrome's site isolation (OOPIF) mechanism. Tests verify
that Pydoll correctly routes CDP commands through the right session
handler when resolving nested iframes inside OOPIFs.
"""

import http.server
import socket
import threading
from pathlib import Path

import pytest
from _waits import wait_for_element_text, wait_for_js_value

from pydoll.browser.chromium import Chrome

PAGES_DIR = Path(__file__).parent / 'pages' / 'oopif'


class _SilentHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def _wait_for_server(host: str, port: int, timeout: float = 5.0) -> None:
    """Block until the server at host:port accepts a TCP connection."""
    import time

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return
        except OSError:
            time.sleep(0.05)
    raise RuntimeError(f'Server {host}:{port} not ready within {timeout}s')


def _cross_site_main_url(port_a: int, port_b: int) -> str:
    """Build a main-page URL that is a different *site* than the OOPIF.

    ``oopif_main.html`` always points its child iframe at ``127.0.0.1:{port_b}``,
    so serving the main page from ``localhost`` (a distinct registrable domain
    for Chrome's site isolation) forces the child into a real out-of-process
    iframe with its own target/session. Cross-*port* alone (``127.0.0.1`` on
    both sides) is same-site and would not create an OOPIF.

    Skips the test when ``localhost`` does not resolve to the loopback address
    the server is bound to (e.g. IPv6-only ``localhost``).
    """
    try:
        with socket.create_connection(('localhost', port_a), timeout=0.5):
            pass
    except OSError:
        pytest.skip('localhost is not reachable on the IPv4 loopback server')
    return f'http://localhost:{port_a}/oopif_main.html?port={port_b}'


@pytest.fixture(scope='module')
def cross_origin_servers():
    """Two HTTP servers on different ports -> different origins -> OOPIF."""

    def _handler():
        class H(_SilentHandler):
            def __init__(self, *a, **kw):
                super().__init__(*a, directory=str(PAGES_DIR), **kw)

        return H

    srv_a = http.server.ThreadingHTTPServer(('127.0.0.1', 0), _handler())
    srv_b = http.server.ThreadingHTTPServer(('127.0.0.1', 0), _handler())
    port_a = srv_a.server_address[1]
    port_b = srv_b.server_address[1]

    for srv in (srv_a, srv_b):
        threading.Thread(target=srv.serve_forever, daemon=True).start()

    _wait_for_server('127.0.0.1', port_a)
    _wait_for_server('127.0.0.1', port_b)

    yield port_a, port_b

    srv_a.shutdown()
    srv_b.shutdown()


class TestCrossOriginIframeResolution:
    """Finding elements inside cross-origin (OOPIF) iframes."""

    @pytest.mark.asyncio
    async def test_find_element_in_cross_origin_iframe(
        self, ci_chrome_options, cross_origin_servers
    ):
        port_a, port_b = cross_origin_servers
        url = f'http://127.0.0.1:{port_a}/oopif_main.html?port={port_b}'

        ci_chrome_options.add_argument('--site-per-process')
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(url)

            iframe = await tab.find(id='cross-origin-iframe', timeout=10)
            assert iframe.is_iframe

            heading = await iframe.find(id='oopif-heading', timeout=10)
            assert await heading.text == 'Cross-Origin Content'

    @pytest.mark.asyncio
    async def test_click_button_in_cross_origin_iframe(
        self, ci_chrome_options, cross_origin_servers
    ):
        port_a, port_b = cross_origin_servers
        url = f'http://127.0.0.1:{port_a}/oopif_main.html?port={port_b}'

        ci_chrome_options.add_argument('--site-per-process')
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(url)

            iframe = await tab.find(id='cross-origin-iframe', timeout=10)
            btn = await iframe.find(id='oopif-btn', timeout=10)
            counter = await iframe.find(id='oopif-btn-count', timeout=10)

            assert await counter.text == '0'
            await btn.click()
            await wait_for_element_text(counter, '1')


class TestNestedIframeInsideOopif:
    """Finding elements in iframes nested inside cross-origin iframes."""

    @pytest.mark.asyncio
    async def test_find_element_in_nested_iframe_inside_oopif(
        self, ci_chrome_options, cross_origin_servers
    ):
        """Navigate: main -> OOPIF -> nested iframe -> find element."""
        port_a, port_b = cross_origin_servers
        url = f'http://127.0.0.1:{port_a}/oopif_main.html?port={port_b}'

        ci_chrome_options.add_argument('--site-per-process')
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(url)

            oopif = await tab.find(id='cross-origin-iframe', timeout=10)
            nested = await oopif.find(id='nested-iframe', timeout=10)
            assert nested.is_iframe

            heading = await nested.find(id='nested-heading', timeout=10)
            assert await heading.text == 'Nested Iframe Content'

    @pytest.mark.asyncio
    async def test_type_text_in_nested_iframe_inside_oopif(
        self, ci_chrome_options, cross_origin_servers
    ):
        """Type text into an input inside a nested iframe within an OOPIF."""
        port_a, port_b = cross_origin_servers
        url = f'http://127.0.0.1:{port_a}/oopif_main.html?port={port_b}'

        ci_chrome_options.add_argument('--site-per-process')
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(url)

            oopif = await tab.find(id='cross-origin-iframe', timeout=10)
            nested = await oopif.find(id='nested-iframe', timeout=10)

            input_el = await nested.find(id='nested-input', timeout=10)
            await input_el.type_text('hello from nested oopif')
            await wait_for_js_value(input_el, 'this.value', 'hello from nested oopif')


class TestDataUrlIframeInsideOopif:
    """Regression for nested cross-origin iframes: main -> OOPIF -> data: iframe.

    Reproduces the reporter's scenario (nestedframes.netlify.app) where the
    inner iframe uses a ``data:`` URL. A ``data:`` frame has an opaque origin
    and stays inside the parent OOPIF's process, so it has no target of its
    own. IFrameContextResolver therefore resolves no OOPIF session for it and
    must fall back to the parent OOPIF session that created the isolated world;
    before the fix it evaluated on the tab session and raised InvalidIFrame.
    """

    @pytest.mark.asyncio
    async def test_find_element_in_data_iframe_inside_oopif(
        self, ci_chrome_options, cross_origin_servers
    ):
        port_a, port_b = cross_origin_servers
        url = _cross_site_main_url(port_a, port_b)

        ci_chrome_options.add_argument('--site-per-process')
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(url)

            oopif = await tab.find(id='cross-origin-iframe', timeout=10)
            data_iframe = await oopif.find(id='data-iframe', timeout=10)
            assert data_iframe.is_iframe

            heading = await data_iframe.find(id='data-heading', timeout=10)
            assert await heading.text == 'Data Frame Content'

    @pytest.mark.asyncio
    async def test_find_body_in_data_iframe_inside_oopif(
        self, ci_chrome_options, cross_origin_servers
    ):
        """The exact call from the bug report: find(tag_name='body')."""
        port_a, port_b = cross_origin_servers
        url = _cross_site_main_url(port_a, port_b)

        ci_chrome_options.add_argument('--site-per-process')
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(url)

            oopif = await tab.find(id='cross-origin-iframe', timeout=10)
            data_iframe = await oopif.find(id='data-iframe', timeout=10)

            body = await data_iframe.find(tag_name='body', timeout=10)
            assert 'Data Frame Content' in await body.text

    @pytest.mark.asyncio
    async def test_type_text_in_data_iframe_inside_oopif(
        self, ci_chrome_options, cross_origin_servers
    ):
        port_a, port_b = cross_origin_servers
        url = _cross_site_main_url(port_a, port_b)

        ci_chrome_options.add_argument('--site-per-process')
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(url)

            oopif = await tab.find(id='cross-origin-iframe', timeout=10)
            data_iframe = await oopif.find(id='data-iframe', timeout=10)

            input_el = await data_iframe.find(id='data-input', timeout=10)
            await input_el.type_text('typed into data frame')
            await wait_for_js_value(input_el, 'this.value', 'typed into data frame')


class TestShadowRootInsideOopif:
    """Discovering and interacting with shadow roots inside OOPIFs."""

    @pytest.mark.asyncio
    async def test_find_shadow_roots_inside_oopif(
        self, ci_chrome_options, cross_origin_servers
    ):
        """find_shadow_roots(True) should discover shadow roots across OOPIFs."""
        port_a, port_b = cross_origin_servers
        url = f'http://127.0.0.1:{port_a}/oopif_main.html?port={port_b}'

        ci_chrome_options.add_argument('--site-per-process')
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(url)

            shadow_roots = await tab.find_shadow_roots(True, timeout=10)
            for sr in shadow_roots:
                html = await sr.inner_html
                if 'Shadow content inside OOPIF' in html:
                    text_el = await sr.query('#shadow-text', timeout=10)
                    assert await text_el.text == 'Shadow content inside OOPIF'
                    return

            pytest.fail('Shadow root inside OOPIF not found via find_shadow_roots')

    @pytest.mark.asyncio
    async def test_click_button_in_shadow_root_inside_oopif(
        self, ci_chrome_options, cross_origin_servers
    ):
        port_a, port_b = cross_origin_servers
        url = f'http://127.0.0.1:{port_a}/oopif_main.html?port={port_b}'

        ci_chrome_options.add_argument('--site-per-process')
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(url)

            shadow_roots = await tab.find_shadow_roots(True, timeout=10)
            for sr in shadow_roots:
                html = await sr.inner_html
                if 'Shadow content inside OOPIF' in html:
                    btn = await sr.query('#shadow-btn', timeout=10)
                    counter = await sr.query('#shadow-btn-count', timeout=10)
                    assert await counter.text == '0'

                    await btn.click()
                    await wait_for_element_text(counter, '1')
                    return

            pytest.fail('Shadow root inside OOPIF not found')


class TestIframeInsideShadowRootInsideOopif:
    """The exact bug scenario: main -> OOPIF -> shadow root -> iframe."""

    @pytest.mark.asyncio
    async def test_find_element_in_iframe_inside_shadow_in_oopif(
        self, ci_chrome_options, cross_origin_servers
    ):
        """This reproduces the original bug where IFrameContextResolver
        failed with InvalidIFrame because DOM.getFrameOwner was routed
        through the wrong session handler.
        """
        port_a, port_b = cross_origin_servers
        url = f'http://127.0.0.1:{port_a}/oopif_main.html?port={port_b}'

        ci_chrome_options.add_argument('--site-per-process')
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(url)

            shadow_roots = await tab.find_shadow_roots(True, timeout=10)
            for sr in shadow_roots:
                html = await sr.inner_html
                if 'Shadow content inside OOPIF' in html:
                    iframe = await sr.query('#shadow-iframe', timeout=10)
                    assert iframe.is_iframe

                    heading = await iframe.find(
                        id='shadow-iframe-heading', timeout=10
                    )
                    assert await heading.text == 'Shadow Iframe Content'
                    return

            pytest.fail('Shadow root inside OOPIF not found')

    @pytest.mark.asyncio
    async def test_type_text_in_iframe_inside_shadow_in_oopif(
        self, ci_chrome_options, cross_origin_servers
    ):
        """Type text through: main -> OOPIF -> shadow root -> iframe -> input."""
        port_a, port_b = cross_origin_servers
        url = f'http://127.0.0.1:{port_a}/oopif_main.html?port={port_b}'

        ci_chrome_options.add_argument('--site-per-process')
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(url)

            shadow_roots = await tab.find_shadow_roots(True, timeout=10)
            for sr in shadow_roots:
                html = await sr.inner_html
                if 'Shadow content inside OOPIF' in html:
                    iframe = await sr.query('#shadow-iframe', timeout=10)
                    input_el = await iframe.find(
                        id='shadow-iframe-input', timeout=10
                    )
                    await input_el.type_text('deep nested text')
                    await wait_for_js_value(input_el, 'this.value', 'deep nested text')
                    return

            pytest.fail('Shadow root inside OOPIF not found')
