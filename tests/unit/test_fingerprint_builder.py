"""Unit tests for the fingerprint JavaScript builder.

The builder is a pure function producing the injection script, so these tests
assert on the generated source: that overrides target prototypes (never the
instance), that every faked getter/method routes through the shared
native-``toString`` hook, and that the worker script omits page-only surfaces.
"""

from __future__ import annotations

import json

from pydoll.utils.fingerprint_builder import (
    build_fingerprint_js,
    build_fingerprint_worker_deferred_js,
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
        assert '_FAKES.has(this) ? {}' in js

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

    def test_max_touch_points_not_injected_via_js(self):
        """max_touch_points is applied natively via setTouchEmulationEnabled."""
        js = build_fingerprint_js({'hardware': {'device_memory': 8, 'max_touch_points': 5}})
        assert 'deviceMemory' in js
        assert 'maxTouchPoints' not in js

    def test_navigator_cdp_props_skipped_when_user_agent_present(self):
        config = {
            'user_agent': 'Mozilla/5.0 ... Chrome/151.0.0.0 Safari/537.36',
            'navigator': {'platform': 'Win32', 'vendor': 'Google Inc.', 'do_not_track': '1'},
        }
        js = build_fingerprint_js(config)
        # platform/vendor are CDP-handled and must not be JS-injected as navigator getters
        assert '_defG(NP, "vendor"' not in js
        assert '_defG(NP, "platform"' not in js
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

    def test_audio_latency_is_a_whole_buffer_at_the_claimed_rate(self):
        """baseLatency/outputLatency keep the host buffer, divided by the claimed rate."""
        js = build_fingerprint_js({'audio': {'sample_rate': 48000}})
        assert "for (const _prop of ['baseLatency', 'outputLatency'])" in js
        assert 'Math.round(real * _deviceRate.call(self)) / 48000' in js
        assert '(!real || _truthful.has(self))' in js

    def test_audio_reads_the_device_rate_before_overriding_it(self):
        js = build_fingerprint_js({'audio': {'sample_rate': 48000}})
        captured = js.index('const _deviceRate = _nativeGetter(BaseAudioContext.prototype')
        overridden = js.index("_defGf(BaseAudioContext.prototype, 'sampleRate'")
        assert captured < overridden

    def test_audio_without_sample_rate_leaves_latency_native(self):
        js = build_fingerprint_js({'audio': {'max_channel_count': 2}})
        assert 'baseLatency' not in js
        assert 'outputLatency' not in js

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
        assert '_defF(WebGLShaderPrecisionFormat.prototype, prop)' in js

    def test_fonts_patch_load_only_and_keep_check_native(self):
        js = build_fingerprint_js({'fonts': {'available_fonts': ['Arial']}})
        assert 'FontFaceSet.prototype' not in js
        assert "_patchM(FontFace.prototype, 'load'" in js
        assert 'check(' not in js

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

    def test_compressed_formats_follow_the_advertised_extensions(self):
        """A hidden extension takes its format enums out of COMPRESSED_TEXTURE_FORMATS."""
        config = {
            'webgl': {
                'vendor': 'Google Inc. (NVIDIA)',
                'renderer': 'ANGLE (NVIDIA)',
                'supported_extensions': ['WEBGL_compressed_texture_s3tc'],
            }
        }
        js = build_fingerprint_js(config)
        assert 'const COMPRESSED_FORMATS = 0x86A3;' in js
        assert 'if (pname === COMPRESSED_FORMATS && ArrayBuffer.isView(real))' in js
        assert 'new Uint32Array(Array.prototype.filter.call(real, formatAllowed))' in js
        assert 'if (allowed(name)) return true;' in js

    def test_compressed_format_enums_match_the_extension_specs(self):
        js = build_fingerprint_js({'webgl': {'vendor': 'v', 'renderer': 'r'}})
        head = 'const formatsByExtension = '
        start = js.index(head) + len(head)
        formats = json.loads(js[start : js.index(';\n', start)])
        assert formats['WEBGL_compressed_texture_s3tc'] == [0x83F0, 0x83F1, 0x83F2, 0x83F3]
        assert formats['WEBGL_compressed_texture_s3tc_srgb'] == [0x8C4C, 0x8C4D, 0x8C4E, 0x8C4F]
        assert formats['WEBGL_compressed_texture_pvrtc'] == [0x8C00, 0x8C01, 0x8C02, 0x8C03]
        assert formats['WEBGL_compressed_texture_etc1'] == [0x8D64]
        assert formats['WEBGL_compressed_texture_etc'] == list(range(0x9270, 0x927A))
        assert formats['WEBGL_compressed_texture_astc'] == list(range(0x93B0, 0x93BE)) + list(
            range(0x93D0, 0x93DE)
        )
        assert formats['EXT_texture_compression_rgtc'] == [0x8DBB, 0x8DBC, 0x8DBD, 0x8DBE]
        assert formats['EXT_texture_compression_bptc'] == [0x8E8C, 0x8E8D, 0x8E8E, 0x8E8F]

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
        assert '_defGf(GPUAdapter.prototype, prop' in js
        assert '_FAKES.set(real, registry[prop])' in js
        assert 'requestAdapter' not in js
        assert '"maxBufferSize": 2147483648' in js
        assert 'featureSet.has(String(value))' in js

    def test_webgpu_is_deferred_in_workers(self):
        config = {
            'webgpu': {'vendor': 'nvidia', 'limits': {'maxBufferSize': 2147483648}},
            'webgl': {'vendor': 'Google Inc. (NVIDIA)', 'renderer': 'ANGLE (NVIDIA)'},
        }
        worker = build_fingerprint_worker_js(config)
        assert 'GPUAdapterInfo' not in worker
        assert 'ANGLE (NVIDIA)' in worker
        deferred = build_fingerprint_worker_deferred_js(config)
        assert '_defF(GPUAdapterInfo.prototype, prop)' in deferred
        assert '_FAKES.set(real, registry[prop])' in deferred
        assert 'ANGLE (NVIDIA)' not in deferred
        assert build_fingerprint_worker_deferred_js({'webgl': config['webgl']}) == ''

    def test_webgpu_fallback_flag_is_part_of_info(self):
        js = build_fingerprint_js({'webgpu': {'vendor': 'nvidia', 'is_fallback_adapter': False}})
        assert '"isFallbackAdapter": false' in js

    def test_webgpu_without_limits_or_features_keeps_them_real(self):
        js = build_fingerprint_js({'webgpu': {'vendor': 'intel'}})
        assert 'const limits = null;' in js
        assert 'const features = null;' in js

    def test_webrtc_patches_webkit_alias_too(self):
        js = build_fingerprint_js({'webrtc_ip_policy': 'relay'})
        assert "_wrapCtor(window, 'RTCPeerConnection'" in js
        assert 'window.webkitRTCPeerConnection = Patched' in js
        assert 'new Proxy(' not in js
        assert "Please use the 'new' operator" in js

    def test_fakes_refuse_structured_clone(self):
        js = build_fingerprint_js({'media_devices': {'audio_inputs': 1}})
        assert "_guardClone(self, 'structuredClone'" in js
        assert "_guardClone(MessagePort.prototype, 'postMessage'" in js
        assert "'DataCloneError'" in js

    def test_fakes_refuse_every_clone_sink(self):
        """History state and notification data serialise too, so both refuse a fake."""
        js = build_fingerprint_js({'media_devices': {'audio_inputs': 1}})
        assert "_guardClone(History.prototype, 'pushState', 'History')" in js
        assert "_guardClone(History.prototype, 'replaceState', 'History')" in js
        assert "_wrapCtor(self, 'Notification'" in js
        assert '_findFake(options.data, new Set(), 5000)' in js
        assert '_cloneError("Failed to construct \'Notification\'", fake)' in js

    def test_clone_guard_recognises_a_fake_from_another_realm(self):
        """Each realm keeps its own _FAKES, so a foreign fake is found by its prototype."""
        js = build_fingerprint_js({'media_devices': {'audio_inputs': 1}})
        assert '_FAKES.has(value) || _foreignFake(value)' in js
        assert 'if (value instanceof Object) return false;' in js
        assert '_FAKED.has(_ORIG.call(d.get))' in js
        assert 'new Proxy(' not in js

    def test_clone_error_keeps_the_native_message(self):
        js = build_fingerprint_js({'media_devices': {'audio_inputs': 1}})
        assert '"Failed to execute \'" + method + "\' on \'" + owner + "\'"' in js
        assert "context + ': ' + ctor + ' object could not be cloned.'" in js

    def test_fonts_resolve_only_the_families_the_profile_lists(self):
        """load() answers from the profile's allow-list, not from a marker denylist."""
        js = build_fingerprint_js({'fonts': {'available_fonts': ['Segoe UI', 'Arial']}})
        assert 'const allow = new Set(["arial", "segoe ui"]);' in js
        assert 'if (!local || allow.has(norm(this.family))) return real;' in js
        assert "throw new DOMException('A network error occurred.', 'NetworkError');" in js
        assert 'const reject' not in js
        assert '"helvetica neue"' not in js

    def test_fonts_answer_local_sources_only(self):
        """A url() web font must keep loading: only local() probes are answered."""
        js = build_fingerprint_js({'fonts': {'available_fonts': ['Arial']}})
        assert "_wrapCtor(self, 'FontFace', null" in js
        assert 'sources.set(face, args[1])' in js
        assert 'LOCAL.test(source) && !REMOTE.test(source)' in js

    def test_fonts_keep_the_native_rejection_for_a_family_the_host_lacks(self):
        """An allowed family the host lacks rejects natively instead of resolving."""
        js = build_fingerprint_js({'fonts': {'available_fonts': ['Segoe UI']}})
        assert 'real.catch' not in js

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


class TestPlatformApis:
    def test_hidden_paths_are_deleted_where_they_live(self):
        js = build_fingerprint_js({
            'platform_apis': {'hidden': ['BarcodeDetector', 'navigator.share']}
        })
        assert '"BarcodeDetector", "navigator.share"' in js
        assert 'delete target[prop]' in js
        assert 'hasOwnProperty.call(target, prop)' in js

    def test_empty_list_injects_nothing(self):
        assert build_fingerprint_js({'platform_apis': {'hidden': []}}) == ''

    def test_workers_hide_the_same_apis(self):
        worker = build_fingerprint_worker_js({'platform_apis': {'hidden': ['SharedWorker']}})
        assert '"SharedWorker"' in worker


class TestMediaCodecs:
    def test_keys_are_normalised_so_any_spelling_matches(self):
        js = build_fingerprint_js({
            'media_codecs': {'can_play_type': {'video/mp4; codecs="avc1.42E01E"': 'probably'}}
        })
        assert '"video/mp4;codecs=avc1.42e01e": "probably"' in js

    def test_native_answer_runs_first_on_every_call(self):
        js = build_fingerprint_js({'media_codecs': {'can_play_type': {'audio/mpeg': 'maybe'}}})
        assert '_native.apply(this, arguments)' in js
        assert 'answer === undefined ? real : answer' in js

    def test_media_source_map_is_coerced_to_booleans(self):
        js = build_fingerprint_js({
            'media_codecs': {'media_source': {'video/webm; codecs="vp9"': 1}}
        })
        assert '"video/webm;codecs=vp9": true' in js

    def test_both_probes_are_guarded_by_existence(self):
        js = build_fingerprint_js({'media_codecs': {'can_play_type': {'audio/mpeg': ''}}})
        assert "typeof HTMLMediaElement !== 'undefined'" in js
        assert "typeof MediaSource !== 'undefined'" in js

    def test_empty_section_injects_nothing(self):
        assert build_fingerprint_js({'media_codecs': {}}) == ''
        assert build_fingerprint_js({'media_codecs': {'can_play_type': {}}}) == ''

    def test_workers_get_the_same_script(self):
        worker = build_fingerprint_worker_js({
            'media_codecs': {'media_source': {'audio/mpeg': True}}
        })
        assert '"audio/mpeg": true' in worker
        assert 'isTypeSupported' in worker


class TestPlugins:
    def test_both_arrays_are_built_from_the_real_prototypes(self):
        js = build_fingerprint_js({
            'plugins': {
                'mime_types': [{'type': 'application/pdf', 'suffixes': 'pdf'}],
                'plugins': [{'name': 'PDF Viewer', 'mime_types': [0]}],
            }
        })
        assert '_fake(MimeType.prototype' in js
        assert '_fake(Plugin.prototype' in js
        assert '_fake(PluginArray.prototype' in js
        assert '_fake(MimeTypeArray.prototype' in js

    def test_named_and_indexed_access_are_both_defined(self):
        js = build_fingerprint_js({'plugins': {'plugins': [{'name': 'PDF Viewer'}]}})
        assert "_patchM(proto, 'item'" in js
        assert "_patchM(proto, 'namedItem'" in js
        assert 'Object.defineProperty(obj, i,' in js

    def test_every_mime_type_points_back_at_its_plugin(self):
        js = build_fingerprint_js({
            'plugins': {
                'mime_types': [{'type': 'application/pdf'}],
                'plugins': [{'name': 'PDF Viewer', 'mime_types': [0]}],
            }
        })
        assert '_FAKES.get(m).enabledPlugin = owner || null;' in js

    def test_the_arrays_replace_the_navigator_getters(self):
        js = build_fingerprint_js({'plugins': {'plugins': [{'name': 'PDF Viewer'}]}})
        assert "_defG(NP, 'plugins', pluginArray);" in js
        assert "_defG(NP, 'mimeTypes', mimeArray);" in js

    def test_guarded_by_the_four_interfaces(self):
        js = build_fingerprint_js({'plugins': {'plugins': [{'name': 'x'}]}})
        for name in ('Plugin', 'PluginArray', 'MimeType', 'MimeTypeArray'):
            assert f"typeof {name} !== 'undefined'" in js

    def test_empty_section_injects_nothing(self):
        assert build_fingerprint_js({'plugins': {}}) == ''
        assert build_fingerprint_js({'plugins': {'plugins': [], 'mime_types': []}}) == ''
