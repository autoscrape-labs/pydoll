"""Integration tests for the native-first fingerprint paths against real Chrome.

Every signal with a CDP path is applied natively and must read as native:
no JavaScript frame in the stack of a foreign-receiver call, a genuine
``PermissionStatus`` that agrees with ``Notification.permission``, Client
Hints brands ordered by Chromium's own per-major algorithm. The remaining
JavaScript overrides must keep the native shape (real prototypes, no own
properties, native brand checks, physically possible values) and reach every
worker realm, nested workers included.

Pages are served over loopback because ``navigator.userAgentData`` requires a
secure context.
"""

import asyncio
import http.server
import socket
import threading
from pathlib import Path

import pytest

from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions
from pydoll.utils.user_agent_parser import UserAgentParser

PAGES_DIR = Path(__file__).parent / 'pages' / 'fingerprint_native'

UA = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/152.0.7977.83 Safari/537.36'
)

FINGERPRINT = {
    'user_agent': UA,
    'client_hints': {'platform_version': '19.0.0'},
    'timezone': 'America/New_York',
    'locale': {'languages': ['en-US', 'en']},
    'hardware': {'hardware_concurrency': 12, 'device_memory': 8, 'max_touch_points': 0},
    'permissions': {'overrides': {'notifications': 'denied'}},
    'media_devices': {'audio_inputs': 1, 'audio_outputs': 1, 'video_inputs': 1},
    'speech': {'voices': [{'name': 'Microsoft David - English (United States)', 'lang': 'en-US'}]},
    'audio': {'sample_rate': 48000, 'max_channel_count': 2},
    'webgl': {'vendor': 'Google Inc. (NVIDIA)', 'renderer': 'ANGLE (NVIDIA, RTX 3060, D3D11)'},
}


REQUEST_LOG: list[tuple[str, str, str]] = []


class _SilentHandler(http.server.SimpleHTTPRequestHandler):
    """Serves the pages and records (path, User-Agent, Accept-Language) per request."""

    def log_message(self, *args):
        pass

    def do_GET(self):
        REQUEST_LOG.append(
            (
                self.path,
                self.headers.get('User-Agent', ''),
                self.headers.get('Accept-Language', ''),
            )
        )
        super().do_GET()


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


@pytest.fixture(scope='module')
def native_server():
    """Serve the probe page and its workers over loopback (a secure context)."""

    class _Handler(_SilentHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(PAGES_DIR), **kwargs)

    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), _Handler)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    _wait_for_server('127.0.0.1', port)

    yield port

    server.shutdown()


async def _wait_for_global(tab, expression: str, timeout: float = 15.0) -> dict:
    """Poll a page global until the page or worker has reported its snapshot."""
    deadline = asyncio.get_event_loop().time() + timeout
    while asyncio.get_event_loop().time() < deadline:
        response = await tab.execute_script(f'return {expression}', return_by_value=True)
        value = response['result']['result'].get('value')
        if value:
            return value
        await asyncio.sleep(0.1)
    raise AssertionError(f'Timed out waiting for {expression}')


def _frames(stack: str) -> list[str]:
    return [line.strip() for line in stack.split('\n')[1:]]


def _ci_options() -> ChromiumOptions:
    """Headless options for CI, mirroring the shared ``ci_chrome_options`` fixture
    (module-scoped here so one browser serves every read-only assertion)."""
    options = ChromiumOptions()
    options.headless = True
    options.start_timeout = 60
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    return options


@pytest.fixture(scope='module')
def applied_page(native_server):
    """One browser with the profile applied; the page and worker snapshots."""

    async def _run():
        url = f'http://127.0.0.1:{native_server}/main.html'
        async with Chrome(options=_ci_options()) as browser:
            tab = await browser.start()
            await tab.apply_fingerprint(dict(FINGERPRINT))
            await tab.go_to(url)
            page = await _wait_for_global(tab, 'window.__page')
            workers = await _wait_for_global(tab, 'window.__workers')
            await _wait_for_global(tab, 'window.__serviceWorker')
            return page, workers

    return asyncio.run(_run())


class TestNativeIdentity:
    def test_user_agent_and_languages_have_no_javascript_frame(self, applied_page):
        """A native accessor throws with no getter frame; a JS override would add one."""
        page, _ = applied_page
        assert 'Windows NT 10.0' in page['userAgent']
        assert page['languages'] == ['en-US', 'en']
        for prop in ('userAgent', 'language'):
            stack = page['stacks'][prop]
            assert 'Illegal invocation' in stack
            assert not any(frame.startswith(f'at get {prop}') for frame in _frames(stack))

    def test_device_memory_keeps_native_brand_check(self, applied_page):
        """deviceMemory stays a JS getter, but a foreign receiver still throws natively."""
        page, _ = applied_page
        assert 'Illegal invocation' in page['stacks']['deviceMemory']

    def test_brands_follow_chromium_algorithm(self, applied_page):
        page, _ = applied_page
        expected = UserAgentParser.parse(UA).user_agent_metadata['brands']
        assert page['brands'] == expected
        assert page['platformVersion'] == '19.0.0'
        assert page['formFactors'] == ['Desktop']


class TestNativePermissions:
    def test_permission_status_is_native_and_consistent(self, applied_page):
        page, _ = applied_page
        assert page['permission']['state'] == 'denied'
        assert page['permission']['isNative'] is True
        assert page['permission']['ownProps'] == []
        assert page['permission']['legacy'] == 'denied'


class TestHardenedJavaScriptOverrides:
    def test_media_devices_are_real_prototypes_without_own_properties(self, applied_page):
        page, _ = applied_page
        kinds = {d['kind']: d for d in page['devices']}
        assert set(kinds) == {'audioinput', 'audiooutput', 'videoinput'}
        assert kinds['audioinput']['ctor'] == 'InputDeviceInfo'
        assert kinds['videoinput']['ctor'] == 'InputDeviceInfo'
        assert kinds['audiooutput']['ctor'] == 'MediaDeviceInfo'
        assert all(d['ownProps'] == [] for d in page['devices'])

    def test_voices_are_real_prototypes_with_native_receiver_check(self, applied_page):
        page, _ = applied_page
        assert [v['name'] for v in page['voices']] == [
            'Microsoft David - English (United States)'
        ]
        assert page['voices'][0]['ctor'] == 'SpeechSynthesisVoice'
        assert page['voices'][0]['ownProps'] == []
        assert 'Illegal invocation' in page['stacks']['getVoices']

    def test_offline_audio_context_keeps_its_construction_values(self, applied_page):
        page, _ = applied_page
        assert page['offlineSampleRate'] == 44100
        assert page['offlineMaxChannelCount'] == 1

    def test_debug_shaders_extension_is_hidden(self, applied_page):
        page, _ = applied_page
        if page['debugShaders'] == 'no-webgl':
            pytest.skip('WebGL unavailable on this host')
        assert page['debugShaders'] == {'hidden': True, 'listed': False}


class TestWorkerRealms:
    def test_dedicated_worker_reads_the_identity(self, applied_page):
        _, workers = applied_page
        own = workers['own']
        assert own['platform'] == 'Win32'
        assert 'Windows NT 10.0' in own['userAgent']
        assert own['hardwareConcurrency'] == 12
        assert own['deviceMemory'] == 8
        assert own['languages'] == ['en-US', 'en']
        assert own['timezone'] == 'America/New_York'
        assert own['formFactors'] == ['Desktop']

    def test_nested_worker_reads_the_identity(self, applied_page):
        """A worker spawned by a worker is a child of the worker target and must
        be attached from the worker session, or it runs with the real identity."""
        _, workers = applied_page
        nested = workers['nested']
        assert nested['platform'] == 'Win32'
        assert 'Windows NT 10.0' in nested['userAgent']
        assert nested['hardwareConcurrency'] == 12
        assert nested['deviceMemory'] == 8
        assert nested['languages'] == ['en-US', 'en']
        assert nested['formFactors'] == ['Desktop']


class TestBrowserProcessFetches:
    """Scripts fetched by the browser process carry the profile identity too."""

    @staticmethod
    def _request(path: str) -> tuple[str, str, str]:
        for entry in REQUEST_LOG:
            if entry[0].split('?')[0] == path:
                return entry
        raise AssertionError(f'{path} was never requested; log: {REQUEST_LOG}')

    def test_service_worker_script_fetch_carries_the_profile(self, applied_page):
        _, user_agent, accept_language = self._request('/sw.js')
        assert 'Windows NT 10.0' in user_agent
        assert 'HeadlessChrome' not in user_agent
        assert accept_language == 'en-US,en;q=0.9'

    def test_nested_worker_script_fetch_carries_the_profile(self, applied_page):
        _, user_agent, accept_language = self._request('/nested_worker.js')
        assert 'Windows NT 10.0' in user_agent
        assert accept_language == 'en-US,en;q=0.9'
