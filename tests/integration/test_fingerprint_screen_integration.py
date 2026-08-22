"""Integration tests for headless screen coherence via Emulation.updateScreen.

Headless Chrome has a single hardcoded virtual screen (800x600, no work area).
``apply_fingerprint`` now reshapes that browser-global screen so every frame,
including cross-origin iframes (OOPIFs) that ``setDeviceMetricsOverride`` cannot
reach, reads the fingerprint's screen. The OOPIF must be a TRUE out-of-process
iframe: the top page is served from ``localhost`` and the iframe from
``127.0.0.1`` (distinct sites for Chrome's isolation), under ``--site-per-process``.
Same-host, different-port is same-site and would keep the iframe in-process.
"""

import http.server
import json
import socket
import threading
from pathlib import Path

import pytest

from pydoll.browser.chromium import Chrome
from pydoll.commands.emulation_commands import EmulationCommands

PAGES_DIR = Path(__file__).parent / 'pages' / 'oopif'

# A macOS desktop screen: 1440x900 CSS, Retina (dpr 2), 25px menu bar.
MAC_SCREEN = {
    'width': 1440,
    'height': 900,
    'avail_width': 1440,
    'avail_height': 860,
    'avail_top': 25,
    'color_depth': 30,
    'pixel_depth': 30,
    'device_pixel_ratio': 2.0,
}
# A mobile screen with a fractional dpr (rounded to 4 for the virtual screen).
MOBILE_SCREEN = {'width': 384, 'height': 832, 'color_depth': 24, 'device_pixel_ratio': 3.75}


class _SilentHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def _wait_for_server(host: str, port: int, timeout: float = 5.0) -> None:
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
    """Main page on ``localhost`` embedding an iframe on ``127.0.0.1``.

    Those are distinct registrable domains for Chrome's site isolation, so the
    iframe becomes a real OOPIF (unlike a same-host, different-port iframe).
    Skips when localhost is not reachable on the IPv4 loopback the servers bind.
    """
    try:
        with socket.create_connection(('localhost', port_a), timeout=0.5):
            pass
    except OSError:
        pytest.skip('localhost is not reachable on the IPv4 loopback server')
    return f'http://localhost:{port_a}/screen_main.html?port={port_b}'


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


async def _read_oopif_screen(browser, tab):
    """Assert a real OOPIF exists, then read its window.screen JSON."""
    assert any(t['type'] == 'iframe' for t in await browser.get_targets()), \
        'expected a true out-of-process iframe target'
    iframe = await tab.find(id='cross-origin-iframe', timeout=10)
    assert iframe.is_iframe
    reporter = await iframe.find(id='screen-info', timeout=10)
    return json.loads(await reporter.text)


@pytest.mark.asyncio
async def test_headless_virtual_screen_matches_fingerprint(ci_chrome_options):
    """getScreenInfos and the main-page window.screen reflect the fingerprint."""
    async with Chrome(options=ci_chrome_options) as browser:
        tab = await browser.start()
        await tab.apply_fingerprint({'screen': MAC_SCREEN})
        await tab.go_to('about:blank')

        infos = await tab._execute_command(EmulationCommands.get_screen_infos())
        primary = next(s for s in infos['result']['screenInfos'] if s['isPrimary'])
        assert primary['width'] == 1440
        assert primary['height'] == 900
        assert primary['availTop'] == 25
        assert primary['availHeight'] == 860
        assert primary['colorDepth'] == 30
        assert primary['devicePixelRatio'] == 2

        script = (
            '(() => JSON.stringify({w: screen.width, h: screen.height, '
            'availTop: screen.availTop, availHeight: screen.availHeight, '
            'cd: screen.colorDepth, dpr: window.devicePixelRatio}))()'
        )
        resp = await tab.execute_script(script, return_by_value=True)
        page = json.loads(resp['result']['result']['value'])
        assert page == {'w': 1440, 'h': 900, 'availTop': 25, 'availHeight': 860,
                        'cd': 30, 'dpr': 2}


@pytest.mark.asyncio
async def test_screen_reaches_true_cross_origin_oopif(ci_chrome_options, cross_origin_servers):
    """The reshaped screen is visible inside a real cross-site OOPIF.

    This is the regression this feature exists for: setDeviceMetricsOverride does
    not reach an OOPIF, so before updateScreen the iframe read the raw 800x600 /
    availTop 0 headless screen, contradicting the top page.
    """
    port_a, port_b = cross_origin_servers
    url = _cross_site_main_url(port_a, port_b)
    ci_chrome_options.add_argument('--site-per-process')
    async with Chrome(options=ci_chrome_options) as browser:
        tab = await browser.start()
        await tab.apply_fingerprint({'screen': MAC_SCREEN})
        await tab.go_to(url)

        data = await _read_oopif_screen(browser, tab)
        assert data['width'] == 1440
        assert data['height'] == 900
        assert data['availTop'] == 25
        assert data['availHeight'] == 860
        assert data['colorDepth'] == 30
        assert data['dpr'] == 2


@pytest.mark.asyncio
async def test_fractional_dpr_screen_reaches_oopif_rounded(
    ci_chrome_options, cross_origin_servers
):
    """A fractional-dpr (mobile) profile no longer leaks 800x600 into the OOPIF.

    The virtual screen only takes an integer dpr, so the OOPIF reads the correct
    CSS size and colorDepth with the dpr rounded (here 3.75 -> 4).
    """
    port_a, port_b = cross_origin_servers
    url = _cross_site_main_url(port_a, port_b)
    ci_chrome_options.add_argument('--site-per-process')
    async with Chrome(options=ci_chrome_options) as browser:
        tab = await browser.start()
        await tab.apply_fingerprint({'screen': MOBILE_SCREEN})
        await tab.go_to(url)

        data = await _read_oopif_screen(browser, tab)
        assert data['width'] == 384
        assert data['height'] == 832
        assert data['colorDepth'] == 24
        assert data['dpr'] == 4
