"""Unit tests for the fingerprint JavaScript builder.

The builder is a pure function producing the injection script, so these tests
assert on the generated source: that overrides target prototypes (never the
instance), that every faked getter/method routes through the shared
native-``toString`` hook, and that the worker script omits page-only surfaces.
"""

from __future__ import annotations

from pydoll.utils.fingerprint_builder import (
    build_fingerprint_js,
    build_fingerprint_worker_js,
)


class TestEmptyAndBootstrap:
    def test_empty_config_page_is_empty(self):
        assert build_fingerprint_js({}) == ''

    def test_empty_config_worker_is_empty(self):
        assert build_fingerprint_worker_js({}) == ''

    def test_bootstrap_present_when_content_exists(self):
        js = build_fingerprint_js({'hardware': {'device_memory': 8}})
        assert 'Function.prototype' in js
        assert '_defG' in js
        assert 'NP' in js

    def test_output_is_deterministic(self):
        config = {'hardware': {'device_memory': 8}, 'locale': {'languages': ['en-US', 'en']}}
        assert build_fingerprint_js(config) == build_fingerprint_js(config)


class TestNativeToStringHook:
    def test_gp_uses_computed_name_getter_not_arrow(self):
        """_gp getters must resolve to native under toString (computed-name + _mark)."""
        js = build_fingerprint_js({'media_devices': {'audio_inputs': 1}})
        assert 'get [p]()' in js
        assert 'get: () => v' not in js

    def test_gp_registers_with_mark(self):
        js = build_fingerprint_js({'media_devices': {'audio_inputs': 1}})
        gp_block = js[js.index('const _gp') : js.index('const NP')]
        assert '_mark(_g)' in gp_block


class TestPrototypePatching:
    """Overrides must patch the prototype, never create own-properties on instances."""

    def test_media_devices_patches_prototype(self):
        js = build_fingerprint_js({'media_devices': {'audio_inputs': 1, 'video_inputs': 1}})
        assert 'MediaDevices.prototype' in js
        assert "typeof MediaDevices !== 'undefined'" in js
        assert '_patchM(navigator.mediaDevices' not in js

    def test_speech_patches_prototype(self):
        voices = [{'name': 'Samantha', 'lang': 'en-US', 'local_service': True}]
        js = build_fingerprint_js({'speech': {'voices': voices}})
        assert 'SpeechSynthesis.prototype' in js
        assert "typeof SpeechSynthesis !== 'undefined'" in js
        assert '_patchM(speechSynthesis' not in js

    def test_permissions_patches_prototype_with_unbound_original(self):
        js = build_fingerprint_js({'permissions': {'overrides': {'notifications': 'denied'}}})
        assert 'Permissions.prototype.query' in js
        assert 'const origQuery = Permissions.prototype.query;' in js
        assert 'origQuery.call(this, desc)' in js
        assert '_patchM(navigator.permissions' not in js
        assert '.bind(navigator.permissions)' not in js


class TestSections:
    def test_hardware_concurrency_not_injected_via_js(self):
        """hardware_concurrency is applied natively via CDP, never as a JS getter."""
        js = build_fingerprint_js({'hardware': {'device_memory': 8, 'hardware_concurrency': 12}})
        assert 'deviceMemory' in js
        assert 'hardwareConcurrency' not in js

    def test_navigator_cdp_props_skipped_when_user_agent_present(self):
        config = {
            'user_agent': 'Mozilla/5.0 ... Chrome/151.0.0.0 Safari/537.36',
            'navigator': {'platform': 'Win32', 'vendor': 'Google Inc.', 'do_not_track': '1'},
        }
        js = build_fingerprint_js(config, user_agent='Chrome/151.0.0.0', platform='Win32')
        # platform/vendor are CDP-handled and must not be JS-injected as navigator getters
        assert "_defG(NP, \"vendor\"" not in js
        assert 'doNotTrack' in js

    def test_webgl_vendor_and_renderer_present(self):
        config = {'webgl': {'vendor': 'Google Inc. (Apple)', 'renderer': 'ANGLE (Apple, M3)'}}
        js = build_fingerprint_js(config)
        assert 'Google Inc. (Apple)' in js
        assert 'ANGLE (Apple, M3)' in js

    def test_fonts_section_present(self):
        js = build_fingerprint_js({'fonts': {'available_fonts': ['Arial', 'Helvetica']}})
        assert 'FontFace.prototype' in js


class TestWorkerScript:
    """The worker script only injects surfaces that exist in a WorkerNavigator."""

    def test_worker_excludes_page_only_sections(self):
        config = {
            'media_devices': {'audio_inputs': 1},
            'speech': {'voices': [{'name': 'A', 'lang': 'en-US'}]},
            'permissions': {'overrides': {'notifications': 'denied'}},
            'screen': {'width': 1920, 'height': 1080},
        }
        worker = build_fingerprint_worker_js(config)
        assert 'MediaDevices' not in worker
        assert 'SpeechSynthesis' not in worker
        assert 'Permissions.prototype' not in worker
        assert 'Screen.prototype' not in worker

    def test_worker_includes_webgl_and_locale(self):
        config = {
            'webgl': {'vendor': 'Google Inc. (Apple)', 'renderer': 'ANGLE (Apple, M3)'},
            'locale': {'languages': ['en-US', 'en']},
        }
        worker = build_fingerprint_worker_js(config, user_agent='Chrome/151.0.0.0')
        assert 'ANGLE (Apple, M3)' in worker
        assert 'languages' in worker

    def test_worker_identity_getters(self):
        worker = build_fingerprint_worker_js(
            {'hardware': {'device_memory': 8}},
            user_agent='Chrome/151.0.0.0',
            platform='Win32',
        )
        assert 'userAgent' in worker
        assert 'deviceMemory' in worker
