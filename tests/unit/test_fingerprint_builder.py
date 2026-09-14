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
    def test_getters_use_computed_name_and_mark(self):
        """Getters must resolve to native under toString (computed-name + _mark)."""
        js = build_fingerprint_js({'media_devices': {'audio_inputs': 1}})
        assert 'get [prop]()' in js
        assert 'get: () => v' not in js
        block = js[js.index('const _install') : js.index('const _nativeGetter')]
        assert '_mark(_g)' in block

    def test_getters_invoke_native_getter_for_brand_check(self):
        """Every constant getter calls the original native getter first, so a
        foreign receiver throws the real Illegal invocation."""
        js = build_fingerprint_js({'hardware': {'device_memory': 8}})
        assert 'if (_og) _og.call(this); return value;' in js


class TestFakePlatformObjects:
    """Fake devices/voices are real-prototype objects with no own properties."""

    def test_no_instance_own_properties(self):
        js = build_fingerprint_js({'media_devices': {'audio_inputs': 1}})
        assert '_gp(' not in js
        assert '_fake(' in js
        assert '_defF(MediaDeviceInfo.prototype' in js

    def test_inputs_use_input_device_info_prototype(self):
        js = build_fingerprint_js({'media_devices': {'audio_inputs': 1, 'video_inputs': 1}})
        assert 'InputDeviceInfo.prototype' in js
        assert "kind === 'audiooutput' ? MediaDeviceInfo.prototype : inputProto" in js

    def test_enumerate_devices_awaits_native_call(self):
        js = build_fingerprint_js({'media_devices': {'audio_inputs': 1, 'video_inputs': 1}})
        assert 'origEnumerate.call(this).then(() => makeDevices())' in js
        inputs = js.index("makeDev('audioinput')")
        video = js.index("makeDev('videoinput')")
        outputs = js.index("makeDev('audiooutput')")
        assert inputs < video < outputs
        assert "_FAKES.has(this) ? {}" in js

    def test_voices_on_real_prototype_with_native_receiver_check(self):
        voices = [{'name': 'Samantha', 'lang': 'en-US', 'local_service': True}]
        js = build_fingerprint_js({'speech': {'voices': voices}})
        assert '_fake(SpeechSynthesisVoice.prototype' in js
        assert '_defF(SpeechSynthesisVoice.prototype, prop)' in js
        assert 'origGetVoices.call(this);' in js


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

    def test_permissions_are_never_javascript(self):
        """Permissions are applied natively (Browser.setPermission), not patched."""
        js = build_fingerprint_js({'permissions': {'overrides': {'notifications': 'denied'}}})
        assert js == ''


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
        js = build_fingerprint_js(config)
        # platform/vendor are CDP-handled and must not be JS-injected as navigator getters
        assert "_defG(NP, \"vendor\"" not in js
        assert "_defG(NP, \"platform\"" not in js
        assert 'doNotTrack' in js

    def test_page_never_injects_identity_or_languages(self):
        """User-Agent, platform and languages are native on the page (CDP)."""
        config = {
            'user_agent': 'Mozilla/5.0 ... Chrome/151.0.0.0 Safari/537.36',
            'locale': {'languages': ['en-US', 'en']},
            'hardware': {'device_memory': 8},
        }
        js = build_fingerprint_js(config)
        assert "'userAgent'" not in js
        assert 'appVersion' not in js
        assert '"languages"' not in js
        assert '"language"' not in js

    def test_audio_keeps_offline_contexts_native(self):
        js = build_fingerprint_js({'audio': {'sample_rate': 48000, 'max_channel_count': 2}})
        assert '(_isOffline(self) || _truthful.has(self)) ? real : 48000' in js
        assert '_isOffline(self.context) ? real : 2' in js
        assert "_wrapCtor(self, 'AudioContext'" in js

    def test_precision_overrides_are_real_prototype_objects(self):
        config = {
            'webgl': {
                'vendor': 'v',
                'renderer': 'r',
                'shader_precision_formats': {'vertex': {'highFloat': [127, 127, 23]}},
            }
        }
        js = build_fingerprint_js(config)
        assert '_fake(WebGLShaderPrecisionFormat.prototype' in js
        assert "_defF(WebGLShaderPrecisionFormat.prototype, prop)" in js

    def test_fonts_patch_load_only_and_keep_check_native(self):
        js = build_fingerprint_js({'fonts': {'available_fonts': ['Arial']}})
        assert 'FontFaceSet.prototype' not in js
        assert "_patchM(FontFace.prototype, 'load'" in js
        assert 'return real.catch(() => face)' in js

    def test_webgl_never_fakes_extension_objects(self):
        config = {
            'webgl': {
                'vendor': 'Google Inc. (NVIDIA)',
                'renderer': 'ANGLE (NVIDIA)',
                'supported_extensions': ['WEBGL_debug_renderer_info'],
                'max_samples': 8,
            }
        }
        js = build_fingerprint_js(config)
        assert '|| {}' not in js
        assert "HIDDEN_EXT = 'WEBGL_debug_shaders'" in js
        assert 'real.filter(allowed)' in js
        assert 'const real = origGetParameter.call(this, pname);' in js
        assert f'{0x8D57}: 8' in js

    def test_webgpu_registers_real_adapter_objects(self):
        config = {
            'webgpu': {
                'vendor': 'nvidia',
                'architecture': 'ampere',
                'limits': {'maxBufferSize': 2147483648},
                'features': ['shader-f16'],
            }
        }
        js = build_fingerprint_js(config)
        assert '_defF(GPUAdapterInfo.prototype, prop)' in js
        assert '_defF(GPUSupportedLimits.prototype, prop)' in js
        assert '_FAKES.set(adapter.info, info)' in js
        assert "_patchM(GPU.prototype, 'requestAdapter'" in js
        assert '"maxBufferSize": 2147483648' in js
        assert 'featureSet.has(String(value))' in js
        worker = build_fingerprint_worker_js(config)
        assert '_FAKES.set(adapter.limits, limits)' in worker

    def test_webgpu_without_limits_or_features_keeps_them_real(self):
        js = build_fingerprint_js({'webgpu': {'vendor': 'intel'}})
        assert 'const limits = null;' in js
        assert 'const features = null;' in js

    def test_webrtc_patches_webkit_alias_too(self):
        js = build_fingerprint_js({'webrtc_ip_policy': 'relay'})
        assert "_wrapCtor(window, 'RTCPeerConnection'" in js
        assert 'window.webkitRTCPeerConnection = Patched' in js

    def test_fonts_reject_other_os_markers(self):
        js = build_fingerprint_js({'fonts': {'available_fonts': ['Segoe UI', 'Arial']}})
        assert '"helvetica neue"' in js
        assert '"menlo"' in js
        assert '"dejavu sans"' in js
        assert '"segoe ui emoji"' in js

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

    def test_worker_includes_webgl_but_not_languages(self):
        """languages reach every worker natively via acceptLanguage; no JS getter."""
        config = {
            'webgl': {'vendor': 'Google Inc. (Apple)', 'renderer': 'ANGLE (Apple, M3)'},
            'locale': {'languages': ['en-US', 'en']},
        }
        worker = build_fingerprint_worker_js(config, user_agent='Chrome/151.0.0.0')
        assert 'ANGLE (Apple, M3)' in worker
        assert 'languages' not in worker

    def test_worker_identity_getters(self):
        worker = build_fingerprint_worker_js(
            {'hardware': {'device_memory': 8}},
            user_agent='Chrome/151.0.0.0',
            platform='Win32',
        )
        assert 'userAgent' in worker
        assert 'deviceMemory' in worker
