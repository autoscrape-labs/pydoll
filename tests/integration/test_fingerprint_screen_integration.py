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
import sys
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


# A Windows/NVIDIA identity whose WebGL renderer is a host-independent marker: no
# CI runner has an "RTX 3060", so it only appears inside a frame the injection reached.
IDENTITY_FP = {
    'user_agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36'
    ),
    'navigator': {'platform': 'Win32', 'vendor': 'Google Inc.'},
    'hardware': {'device_memory': 8, 'hardware_concurrency': 12},
    'webgl': {
        'vendor': 'Google Inc. (NVIDIA)',
        'renderer': 'ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0, D3D11)',
    },
    'timezone': 'America/New_York',
}


def _identity_main_url(port_a: int, port_b: int) -> str:
    """Main page on ``localhost`` embedding the identity reporter on ``127.0.0.1``."""
    try:
        with socket.create_connection(('localhost', port_a), timeout=0.5):
            pass
    except OSError:
        pytest.skip('localhost is not reachable on the IPv4 loopback server')
    return f'http://localhost:{port_a}/identity_main.html?port={port_b}'


async def _read_oopif_identity(browser, tab) -> dict:
    """Assert a real OOPIF exists, then read the identity it reports from its own realm."""
    assert any(t['type'] == 'iframe' for t in await browser.get_targets()), \
        'expected a true out-of-process iframe target'
    iframe = await tab.find(id='cross-origin-iframe', timeout=10)
    assert iframe.is_iframe
    reporter = await iframe.find(id='identity-info', timeout=10)
    return json.loads(await reporter.text)


@pytest.mark.asyncio
async def test_identity_reaches_true_cross_origin_oopif(ci_chrome_options, cross_origin_servers):
    """With cross_origin_iframes=True the injected identity reaches the OOPIF's own realm."""
    port_a, port_b = cross_origin_servers
    url = _identity_main_url(port_a, port_b)
    ci_chrome_options.add_argument('--site-per-process')
    async with Chrome(options=ci_chrome_options) as browser:
        tab = await browser.start()
        await tab.apply_fingerprint(IDENTITY_FP, cross_origin_iframes=True)
        await tab.go_to(url)

        data = await _read_oopif_identity(browser, tab)
        # Windows UA/platform are the injected values; a non-Windows CI host is not Win32.
        # deviceMemory is JS-injected. WebGL is asserted only when a renderer is available
        # (CI may run software WebGL gated behind a flag).
        assert data['platform'] == 'Win32'
        assert 'Windows NT 10.0' in data['ua']
        assert data['deviceMemory'] == 8
        if data['webgl'] not in ('no-webgl', 'no-ext', 'err'):
            assert 'RTX 3060' in data['webgl']


@pytest.mark.asyncio
async def test_identity_absent_from_oopif_when_disabled(ci_chrome_options, cross_origin_servers):
    """With cross_origin_iframes=False the OOPIF keeps the real host identity."""
    port_a, port_b = cross_origin_servers
    url = _identity_main_url(port_a, port_b)
    ci_chrome_options.add_argument('--site-per-process')
    async with Chrome(options=ci_chrome_options) as browser:
        tab = await browser.start()
        await tab.apply_fingerprint(IDENTITY_FP, cross_origin_iframes=False)
        await tab.go_to(url)

        data = await _read_oopif_identity(browser, tab)

        # The WebGL renderer is the host-independent proof: no CI GPU is an RTX 3060,
        # so its absence means the injected identity did not reach this realm.
        webgl_available = data['webgl'] not in ('no-webgl', 'no-ext', 'err')
        if webgl_available:
            assert 'RTX 3060' not in data['webgl']

        # platform and User-Agent only discriminate when the host OS differs from the
        # injected Windows profile. On the Windows CI runner the real values ARE Win32 /
        # 'Windows NT 10.0', so they cannot tell a leaked identity from the host's own.
        if sys.platform != 'win32':
            assert data['platform'] != 'Win32'
            assert 'Windows NT 10.0' not in data['ua']
        elif not webgl_available:
            pytest.skip(
                'No host-independent identity marker on this Windows host '
                '(WebGL unavailable); the injected Win32 profile is indistinguishable '
                'from the real host identity.'
            )
