"""Builds JavaScript injection scripts from a FingerprintConfig.

Each builder function returns a JS statement block (or empty string if the
corresponding config section is absent). ``build_fingerprint_js`` wraps every
non-empty block inside a single bootstrap IIFE that installs a global
``Function.prototype.toString`` hook, so every getter or method this module
redefines reports ``[native code]`` under introspection. The result is injected
via ``Page.addScriptToEvaluateOnNewDocument``.

Detectability notes:
    Fingerprinting suites (CreepJS, FingerprintJS) inspect overrides two ways
    that this module defends against:

    - ``Object.getOwnPropertyDescriptor(proto, prop).get.toString()`` must
      return ``[native code]``. Every getter is registered with the shared
      toString hook so it does.
    - Spoofed properties must live on the correct prototype (e.g. ``screen``
      dimensions on ``Screen.prototype``), not as own-properties of the
      instance. Every getter targets the native prototype.

    Signals the browser can override natively via CDP (User-Agent / platform /
    vendor / appVersion, screen dimensions, devicePixelRatio,
    hardwareConcurrency, timezone, geolocation, locale) are NOT touched here.
    They are applied by ``Tab.apply_fingerprint`` through the Emulation domain,
    which keeps the reported getters genuinely native. Only signals CDP cannot
    set (deviceMemory, maxTouchPoints, languages, WebGL, plugins, media
    devices, speech, audio, network connection, fonts, permissions, WebRTC
    policy) are handled with hardened JavaScript here.

    Residual limitation: a JavaScript accessor still returns a value when its
    getter is invoked against an unrelated receiver, whereas a native accessor
    throws ``Illegal invocation``. The CDP-first strategy avoids JS getters for
    the highest-entropy signals precisely to minimise this residual surface.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pydoll.protocol.fingerprint.types import (
        AudioFingerprint,
        FingerprintConfig,
        FontFingerprint,
        HardwareFingerprint,
        LocaleFingerprint,
        MediaDevicesFingerprint,
        NetworkConnectionFingerprint,
        PermissionsFingerprint,
        ScreenFingerprint,
        SpeechFingerprint,
        WebGLProfile,
    )

# Navigator properties that CDP setUserAgentOverride already sets natively when
# a user_agent string is present. Skipped from JS injection so the reported
# getters stay genuinely native (a JS getter would replace the native one).
_CDP_HANDLED_NAV_PROPS = frozenset({'platform', 'vendor', 'app_version'})

# WebGL parameters that return Int32Array (not Float32Array).
_WEBGL_INT32_PARAMS = frozenset({'max_viewport_dims'})

# Shared bootstrap injected once before every section. Replaces
# Function.prototype.toString with a plain (non-Proxy) function backed by a
# WeakMap registry, so every redefined getter/method reports [native code]
# without exposing a Proxy exotic object (fingerprinting suites specifically
# flag a proxied toString). It then exposes the closure-scoped helpers _defG
# (define a native-looking accessor) and _patchM (replace a method with a
# native-looking one). Nothing leaks to any global scope: the helpers live only
# in the IIFE closure the sections run inside.
#
# ``NP`` resolves navigator's prototype in both the page (Navigator.prototype)
# and worker (WorkerNavigator.prototype) realms, so the same navigator getters
# apply consistently in either scope.
_BOOTSTRAP = r"""
const _ORIG = Function.prototype.toString;
// Cross-realm native-toString hook WITHOUT shared state. Page + workers + nested
// iframes all receive this byte-identical script, so each realm independently
// records the SAME set of faked-function source strings. Recognition is by
// string equality, not object identity, so a pristine cross-realm
// Function.prototype.toString (e.g. CreepJS's same-origin phantom iframe) still
// resolves our functions to a native string. No window/Symbol slot to scan.
const _FAKED = new Set();
const _mark = (fn) => { try { _FAKED.add(_ORIG.call(fn)); } catch (e) {} return fn; };
const _nativeStr = (fn) => 'function ' + fn.name + '() { [native code] }';
const _hook = Object.getOwnPropertyDescriptor({
  toString() { const s = _ORIG.call(this); return _FAKED.has(s) ? _nativeStr(this) : s; }
}, 'toString').value;
_mark(_hook);
try {
  Object.defineProperty(Function.prototype, 'toString',
    {value: _hook, configurable: true, writable: true});
} catch (e) {}
const _defG = (target, prop, value) => {
  try {
    const _od = Object.getOwnPropertyDescriptor(target, prop);
    const _og = _od && _od.get;
    // Computed-name getter in an object literal: its ``.name`` is ``get <prop>``
    // (so _nativeStr rebuilds the exact native string) and it has no own
    // ``prototype``. Delegating to the original native getter reproduces its
    // receiver brand check, so reading the property on the prototype throws
    // like a native accessor instead of silently returning the value.
    const _h = { get [prop]() { if (_og) _og.call(this); return value; } };
    const _g = Object.getOwnPropertyDescriptor(_h, prop).get;
    _mark(_g);
    Object.defineProperty(target, prop, {get: _g, configurable: true, enumerable: true});
  } catch (e) {}
};
const _patchM = (obj, prop, fn) => {
  try {
    const wrapper = { [prop](...args) { return fn.apply(this, args); } }[prop];
    try { Object.defineProperty(wrapper, 'length', {value: fn.length, configurable: true}); }
    catch (e) {}
    _mark(wrapper);
    Object.defineProperty(obj, prop, {value: wrapper, configurable: true, writable: true});
  } catch (e) {}
};
const _gp = (o, p, v) => {
  try {
    // Same computed-name + _mark path as _defG so the getter's ``toString``
    // resolves to native and its ``.name`` is ``get <p>`` with no own prototype.
    // Unlike _defG this defines on the given (instance) object and has no
    // original native getter to delegate to (these are freshly created props).
    const _h = { get [p]() { return v; } };
    const _g = Object.getOwnPropertyDescriptor(_h, p).get;
    _mark(_g);
    Object.defineProperty(o, p, {get: _g, enumerable: true, configurable: true});
  } catch (e) {}
};
const NP = Object.getPrototypeOf(navigator);
"""


def _wrap(parts: list[str]) -> str:
    """Wrap non-empty section blocks in the bootstrap IIFE.

    Each section is guarded by its own try-catch so a failure in one never
    prevents the others from executing. Returns '' when nothing to inject.
    """
    non_empty = [p for p in parts if p]
    if not non_empty:
        return ''
    guarded = [f'try {{\n{p}\n}} catch (_) {{}}' for p in non_empty]
    body = '\n'.join(guarded)
    return f'(function() {{\n{_BOOTSTRAP}\n{body}\n}})();'


def _build_identity_js(user_agent: str, platform: str) -> str:
    """Build ``navigator.userAgent``/``appVersion``/``platform`` getters.

    Injected in every realm (page + workers + detached iframes) because CDP's
    ``setUserAgentOverride`` is lost in a detached ("dead") iframe realm and does
    not reach ``WorkerNavigator``, so those realms would otherwise leak the real
    values. Each is guarded by existence so a scope lacking a property (e.g. a
    worker without it) is left untouched.
    """
    lines: list[str] = []
    if user_agent:
        app_version = user_agent[len('Mozilla/') :] if user_agent.startswith('Mozilla/') else ''
        ua_json = json.dumps(user_agent)
        lines.append(f"if ('userAgent' in navigator) _defG(NP, 'userAgent', {ua_json});")
        if app_version:
            lines.append(
                "if ('appVersion' in navigator) "
                f'_defG(NP, "appVersion", {json.dumps(app_version)});'
            )
    if platform:
        lines.append(f"if ('platform' in navigator) _defG(NP, 'platform', {json.dumps(platform)});")
    return '\n'.join(lines)


def build_fingerprint_js(
    config: FingerprintConfig, user_agent: str = '', platform: str = ''
) -> str:
    """Build the complete page fingerprint injection script.

    Returns a single JS string that installs the shared native-toString hook
    and overrides every configured fingerprint surface CDP cannot handle.
    Empty string if nothing to inject.

    Args:
        config: Fingerprint configuration.
        user_agent: Reduced User-Agent string to expose as ``navigator.userAgent``
            in every realm (including detached iframes). Empty string skips it.
        platform: ``navigator.platform`` value to expose in every realm.
    """
    parts: list[str] = [_build_identity_js(user_agent, platform)]

    if 'navigator' in config:
        nav: dict[str, object] = dict(config['navigator'])
        if 'user_agent' in config:
            nav = {k: v for k, v in nav.items() if k not in _CDP_HANDLED_NAV_PROPS}
        if nav:
            parts.append(_build_navigator_js(nav))

    section_config: dict[str, object] = dict(config)
    for key, builder in _SECTION_BUILDERS.items():
        if key in section_config:
            parts.append(builder(section_config[key]))

    return _wrap(parts)


def build_fingerprint_worker_js(
    config: FingerprintConfig, user_agent: str = '', platform: str = ''
) -> str:
    """Build the worker fingerprint injection script.

    Web Workers expose ``WorkerNavigator`` (not the page ``Navigator``) and have
    no ``screen``/``window``/``document``, so only the surfaces that exist in a
    worker are injected: ``navigator.userAgent``, ``navigator.appVersion``,
    ``navigator.platform``, ``navigator.deviceMemory``, ``navigator.languages`` /
    ``navigator.language``, ``navigator.connection`` and WebGL (via
    ``OffscreenCanvas``).

    ``userAgent`` / ``appVersion`` / ``platform`` are injected here (guarded by
    existence) because ``Emulation.setUserAgentOverride`` does not reliably update
    those ``WorkerNavigator`` properties on out-of-page worker targets (e.g.
    service workers), only the outgoing request headers. ``hardwareConcurrency``
    is reapplied to the worker session natively via CDP by
    ``Tab.apply_fingerprint``. ``vendor`` is never injected: ``WorkerNavigator``
    does not expose it, so adding it would itself be an anomaly.

    All getters route through the shared native-``toString`` hook, so they report
    ``[native code]`` under introspection.

    Args:
        config: Fingerprint configuration.
        platform: ``navigator.platform`` value derived from the User-Agent
            (e.g. ``'Win32'``). Empty string skips the platform override.
        user_agent: Reduced User-Agent string (``Chrome/MAJOR.0.0.0`` form) to
            expose as ``navigator.userAgent``; ``appVersion`` is derived from it.
            Empty string skips the User-Agent override.

    Returns:
        The worker injection script, or '' when nothing worker-relevant applies.
    """
    nav_lines: list[str] = [_build_identity_js(user_agent, platform)]
    if 'hardware' in config and 'device_memory' in config['hardware']:
        val = json.dumps(config['hardware']['device_memory'])
        nav_lines.append(f"if ('deviceMemory' in navigator) _defG(NP, 'deviceMemory', {val});")

    parts: list[str] = ['\n'.join(p for p in nav_lines if p)]
    if 'locale' in config:
        parts.append(_build_locale_js(config['locale']))
    if 'network_connection' in config:
        parts.append(_build_network_connection_js(config['network_connection']))
    if 'webgl' in config:
        parts.append(_build_webgl_js(config['webgl']))
    if 'fonts' in config:
        parts.append(_build_fonts_js(config['fonts']))
    return _wrap(parts)


def _build_navigator_js(nav: dict[str, object]) -> str:
    lines: list[str] = []
    for key, js_prop in (
        ('platform', 'platform'),
        ('vendor', 'vendor'),
        ('app_version', 'appVersion'),
        ('do_not_track', 'doNotTrack'),
    ):
        if key in nav:
            val = json.dumps(nav[key])
            lines.append(f'_defG(NP, {json.dumps(js_prop)}, {val});')
    if 'pdf_viewer_enabled' in nav:
        val = 'true' if nav['pdf_viewer_enabled'] else 'false'
        lines.append(f'_defG(NP, "pdfViewerEnabled", {val});')
    return '\n'.join(lines)


def _build_hardware_js(hw: HardwareFingerprint) -> str:
    """Override navigator hardware getters CDP does not cover.

    ``hardware_concurrency`` is intentionally omitted: ``Tab.apply_fingerprint``
    sets it via ``Emulation.setHardwareConcurrencyOverride`` so the getter stays
    genuinely native.
    """
    items: dict[str, object] = dict(hw)
    lines: list[str] = []
    for key, js_prop in (
        ('device_memory', 'deviceMemory'),
        ('max_touch_points', 'maxTouchPoints'),
    ):
        if key in items:
            val = json.dumps(items[key])
            lines.append(f'_defG(NP, {json.dumps(js_prop)}, {val});')
    return '\n'.join(lines)


def _build_screen_js(scr: ScreenFingerprint) -> str:
    """Override screen/display getters CDP does not cover.

    ``width``, ``height``, ``device_pixel_ratio``, ``inner_*`` and orientation
    are omitted: they are applied natively via
    ``Emulation.setDeviceMetricsOverride`` in ``Tab.apply_fingerprint``.

    ``avail_width``/``avail_height`` ARE injected here (on ``Screen.prototype``):
    CDP forces ``availWidth``/``availHeight`` equal to the screen size, which is a
    headless tell (no taskbar/dock gap). ``avail_top``/``avail_left`` are injected
    too: ``availTop == 0`` on the main page is a headless tell, and it must match
    the ``availTop`` that ``Emulation.updateScreen`` gives cross-origin iframes.
    ``color_depth``/``pixel_depth`` are on ``Screen.prototype`` and ``outer_*`` are
    own-properties on ``window``, both matching the native location.
    """
    items: dict[str, object] = dict(scr)
    lines: list[str] = []
    for py_key, js_prop in (
        ('avail_width', 'availWidth'),
        ('avail_height', 'availHeight'),
        ('avail_top', 'availTop'),
        ('avail_left', 'availLeft'),
        ('color_depth', 'colorDepth'),
        ('pixel_depth', 'pixelDepth'),
    ):
        if py_key in items:
            val = json.dumps(items[py_key])
            lines.append(f'_defG(Screen.prototype, {json.dumps(js_prop)}, {val});')
    for py_key, js_prop in (
        ('outer_width', 'outerWidth'),
        ('outer_height', 'outerHeight'),
    ):
        if py_key in items:
            val = json.dumps(items[py_key])
            lines.append(f'_defG(window, {json.dumps(js_prop)}, {val});')
    return '\n'.join(lines)


_WEBGL_JS_TEMPLATE = """\
const VENDOR = 0x9245;
const RENDERER = 0x9246;
const spoofVendor = %s;
const spoofRenderer = %s;
const paramOverrides = %s;
const ext1 = %s;
const ext2 = %s;
const precisionOverrides = %s;

function patchContext(proto, extOverrides) {
  const origGetParameter = proto.getParameter;
  _patchM(proto, 'getParameter', function getParameter(pname) {
    if (pname === VENDOR) return spoofVendor;
    if (pname === RENDERER) return spoofRenderer;
    if (paramOverrides[pname] !== undefined) return paramOverrides[pname];
    return origGetParameter.call(this, pname);
  });

  if (Object.keys(precisionOverrides).length > 0) {
    const origGetShaderPrecisionFormat = proto.getShaderPrecisionFormat;
    _patchM(proto, 'getShaderPrecisionFormat',
      function getShaderPrecisionFormat(shaderType, precisionType) {
        const key = shaderType + ':' + precisionType;
        if (precisionOverrides[key]) {
          const p = precisionOverrides[key];
          return {rangeMin: p[0], rangeMax: p[1], precision: p[2]};
        }
        return origGetShaderPrecisionFormat.call(this, shaderType, precisionType);
      });
  }

  if (extOverrides !== null) {
    const origGetExtension = proto.getExtension;
    _patchM(proto, 'getExtension', function getExtension(name) {
      if (!extOverrides.includes(name)) return null;
      return origGetExtension.call(this, name) || {};
    });
    _patchM(proto, 'getSupportedExtensions', function getSupportedExtensions() {
      return extOverrides.slice();
    });
  }
}

if (typeof WebGLRenderingContext !== 'undefined') {
  patchContext(WebGLRenderingContext.prototype, ext1);
}
if (typeof WebGL2RenderingContext !== 'undefined') {
  patchContext(WebGL2RenderingContext.prototype, ext2);
}"""

# Maps python key -> WebGL parameter constant
_WEBGL_PARAM_MAP: dict[str, int] = {
    'max_texture_size': 0x0D33,
    'max_renderbuffer_size': 0x84E8,
    'max_viewport_dims': 0x0D3A,
    'max_vertex_attribs': 0x8869,
    'max_vertex_uniform_vectors': 0x8DFB,
    'max_fragment_uniform_vectors': 0x8DFD,
    'max_texture_image_units': 0x8872,
    'max_vertex_texture_image_units': 0x8B4C,
    'max_combined_texture_image_units': 0x8B4D,
    'aliased_line_width_range': 0x846E,
    'aliased_point_size_range': 0x846D,
}

# Maps shader type names to WebGL constants
_SHADER_TYPE_MAP: dict[str, int] = {
    'vertex': 0x8B31,
    'fragment': 0x8B30,
}

_PRECISION_TYPE_MAP: dict[str, int] = {
    'lowFloat': 0x8DF0,
    'mediumFloat': 0x8DF1,
    'highFloat': 0x8DF2,
    'lowInt': 0x8DF3,
    'mediumInt': 0x8DF4,
    'highInt': 0x8DF5,
}


def _build_webgl_param_js(webgl: WebGLProfile) -> str:
    """Build the JS object literal for WebGL parameter overrides."""
    items: dict[str, object] = dict(webgl)
    param_overrides: dict[int, object] = {}
    for py_key, gl_const in _WEBGL_PARAM_MAP.items():
        if py_key in items:
            val = items[py_key]
            if isinstance(val, list):
                array_type = 'Int32Array' if py_key in _WEBGL_INT32_PARAMS else 'Float32Array'
                param_overrides[gl_const] = f'new {array_type}({json.dumps(val)})'
            else:
                param_overrides[gl_const] = val

    if not param_overrides:
        return '{}'

    entries = []
    for k, v in param_overrides.items():
        if isinstance(v, str) and v.startswith('new '):
            entries.append(f'{k}: {v}')
        else:
            entries.append(f'{k}: {json.dumps(v)}')
    return '{' + ', '.join(entries) + '}'


def _build_webgl_precision_js(webgl: WebGLProfile) -> str:
    """Build the JS object literal for shader precision format overrides."""
    if 'shader_precision_formats' not in webgl:
        return '{}'

    precision_entries = []
    for shader_name, precisions in webgl['shader_precision_formats'].items():
        shader_const = _SHADER_TYPE_MAP.get(shader_name)
        if shader_const is None:
            continue
        for precision_name, values in precisions.items():
            precision_const = _PRECISION_TYPE_MAP.get(precision_name)
            if precision_const is None:
                continue
            key = f'{shader_const}:{precision_const}'
            precision_entries.append(f"'{key}': {json.dumps(values)}")

    if not precision_entries:
        return '{}'
    return '{' + ', '.join(precision_entries) + '}'


def _build_webgl_js(webgl: WebGLProfile) -> str:
    param_js = _build_webgl_param_js(webgl)

    if 'supported_extensions' in webgl:
        ext1_js = json.dumps(webgl.get('supported_extensions'))
    else:
        ext1_js = 'null'

    if 'webgl2_extensions' in webgl:
        ext2_js = json.dumps(webgl['webgl2_extensions'])
    else:
        ext2_js = ext1_js

    precision_js = _build_webgl_precision_js(webgl)

    return _WEBGL_JS_TEMPLATE % (
        json.dumps(webgl['vendor']),
        json.dumps(webgl['renderer']),
        param_js,
        ext1_js,
        ext2_js,
        precision_js,
    )


def _build_media_devices_js(md: MediaDevicesFingerprint) -> str:
    audio_in = md.get('audio_inputs', 0)
    audio_out = md.get('audio_outputs', 0)
    video_in = md.get('video_inputs', 0)
    return f"""\
const hasMDI = typeof MediaDeviceInfo !== 'undefined';

function makeDev(kind) {{
  const d = hasMDI ? Object.create(MediaDeviceInfo.prototype) : {{}};
  _gp(d, 'deviceId', '');
  _gp(d, 'kind', kind);
  _gp(d, 'label', '');
  _gp(d, 'groupId', '');
  if (hasMDI) {{
    _patchM(d, 'toJSON', function toJSON() {{
      return {{deviceId: '', kind: kind, label: '', groupId: ''}};
    }});
  }}
  return d;
}}

const devices = [];
for (let i = 0; i < {audio_in}; i++) devices.push(makeDev('audioinput'));
for (let i = 0; i < {audio_out}; i++) devices.push(makeDev('audiooutput'));
for (let i = 0; i < {video_in}; i++) devices.push(makeDev('videoinput'));

if (typeof MediaDevices !== 'undefined' && MediaDevices.prototype.enumerateDevices) {{
  _patchM(MediaDevices.prototype, 'enumerateDevices', function enumerateDevices() {{
    return Promise.resolve(devices.slice());
  }});
}}"""


def _build_audio_js(audio: AudioFingerprint) -> str:
    lines: list[str] = []
    if 'sample_rate' in audio:
        val = json.dumps(audio['sample_rate'])
        lines.append(f'_defG(BaseAudioContext.prototype, "sampleRate", {val});')
    if 'max_channel_count' in audio:
        val = json.dumps(audio['max_channel_count'])
        lines.append(f'_defG(AudioDestinationNode.prototype, "maxChannelCount", {val});')
    return '\n'.join(lines)


def _build_speech_js(speech: SpeechFingerprint) -> str:
    voices_data = json.dumps(speech['voices'])
    return f"""\
const hasSV = typeof SpeechSynthesisVoice !== 'undefined';
const voicesData = {voices_data};

const fakeVoices = voicesData.map((v, idx) => {{
  const voice = hasSV ? Object.create(SpeechSynthesisVoice.prototype) : {{}};
  _gp(voice, 'name', v.name);
  _gp(voice, 'lang', v.lang);
  _gp(voice, 'localService', v.local_service !== undefined ? v.local_service : true);
  _gp(voice, 'voiceURI', v.name);
  _gp(voice, 'default', idx === 0);
  return voice;
}});

if (typeof SpeechSynthesis !== 'undefined' && SpeechSynthesis.prototype.getVoices) {{
  _patchM(SpeechSynthesis.prototype, 'getVoices', function getVoices() {{
    return fakeVoices.slice();
  }});
}}"""


def _build_locale_js(locale: LocaleFingerprint) -> str:
    languages = locale['languages']
    if not languages:
        return ''
    first = json.dumps(languages[0])
    all_langs = json.dumps(languages)
    return (
        f'const _langs = Object.freeze({all_langs});\n'
        f'_defG(NP, "language", {first});\n'
        '_defG(NP, "languages", _langs);'
    )


def _build_network_connection_js(nc: NetworkConnectionFingerprint) -> str:
    """Override navigator.connection (NetworkInformation API) getters."""
    items: dict[str, object] = dict(nc)
    lines: list[str] = []
    for py_key, js_prop in (
        ('effective_type', 'effectiveType'),
        ('downlink', 'downlink'),
        ('rtt', 'rtt'),
        ('save_data', 'saveData'),
    ):
        if py_key in items:
            val = json.dumps(items[py_key])
            prop = json.dumps(js_prop)
            lines.append(f'  _defG(NetworkInformation.prototype, {prop}, {val});')
    if not lines:
        return ''
    body = '\n'.join(lines)
    return f"if (typeof NetworkInformation !== 'undefined') {{\n{body}\n}}"


_OS_MARKER_FONTS = frozenset({
    'Cambria Math',
    'Nirmala UI',
    'Leelawadee UI',
    'HoloLens MDL2 Assets',
    'Segoe Fluent Icons',
    'Helvetica Neue',
    'Luminari',
    'PingFang HK Light',
    'InaiMathi Bold',
    'Galvji',
    'Chakra Petch',
    'Arimo',
    'MONO',
    'Ubuntu',
    'Noto Color Emoji',
    'Dancing Script',
    'Droid Sans Mono',
})


_FONTS_JS_TEMPLATE = """\
if (typeof FontFace !== 'undefined' && FontFace.prototype.load) {
  const allow = new Set(%s);
  const reject = new Set(%s);
  const norm = (s) => String(s).trim().replace(/^["']|["']$/g, '').toLowerCase();
  const famOf = (font) => {
    const m = /["']([^"']+)["']\\s*$/.exec(String(font)) || /(\\S+)\\s*$/.exec(String(font));
    return m ? norm(m[1]) : '';
  };
  const _realLoad = FontFace.prototype.load;
  _patchM(FontFace.prototype, 'load', function load() {
    const fam = norm(this.family);
    if (allow.has(fam)) return Promise.resolve(this);
    if (reject.has(fam)) {
      return Promise.reject(new DOMException('A network error occurred.', 'NetworkError'));
    }
    return _realLoad.apply(this, arguments);
  });
  if (typeof FontFaceSet !== 'undefined' && FontFaceSet.prototype.check) {
    const _realCheck = FontFaceSet.prototype.check;
    _patchM(FontFaceSet.prototype, 'check', function check(font, text) {
      const fam = famOf(font);
      if (allow.has(fam)) return true;
      if (reject.has(fam)) return false;
      return _realCheck.apply(this, arguments);
    });
  }
}"""


def _build_fonts_js(fonts: FontFingerprint) -> str:
    """Override FontFace.load()/FontFaceSet.check() to present a coherent font set.

    CreepJS detects fonts via BOTH ``FontFaceSet.check`` and
    ``new FontFace(f, 'local("f")').load()`` and unions the results. Overriding
    only ``check`` leaves ``load`` genuinely loading the host's real (e.g. macOS)
    fonts, so the union mixes the spoofed set with the real OS set, a cross-OS
    lie (``isFontOSBad``). Both are overridden here with the same allow/reject
    sets: allowed fonts resolve / return true, cross-OS marker fonts the profile
    does not claim reject / return false, and everything else (real ``url()`` web
    fonts, the random-name liar probe) falls through to native behaviour.

    Works in workers too (``FontFace``/``FontFaceSet`` exist there, ``document``
    does not). The emoji glyph-metric layer CreepJS also reads is native
    rasterisation of the host emoji font and is not spoofable from JavaScript.
    """
    available = fonts.get('available_fonts', [])
    if not available:
        return ''
    allow = sorted({f.lower() for f in available})
    reject = sorted({m.lower() for m in _OS_MARKER_FONTS} - set(allow))
    return _FONTS_JS_TEMPLATE % (json.dumps(allow), json.dumps(reject))


def _build_permissions_js(perms: PermissionsFingerprint) -> str:
    """Override navigator.permissions.query() for specified permissions."""
    overrides = perms.get('overrides', {})
    if not overrides:
        return ''
    overrides_json = json.dumps(overrides)
    return (
        'if (typeof Permissions !== "undefined" && Permissions.prototype.query) {\n'
        f'  const overrides = {overrides_json};\n'
        '  const origQuery = Permissions.prototype.query;\n'
        '  _patchM(Permissions.prototype, "query", function query(desc) {\n'
        '    const name = desc && desc.name;\n'
        '    if (name && overrides[name] !== undefined) {\n'
        '      return Promise.resolve({\n'
        '        state: overrides[name],\n'
        '        status: overrides[name],\n'
        '        onchange: null,\n'
        '        addEventListener: function() {},\n'
        '        removeEventListener: function() {},\n'
        '        dispatchEvent: function() { return true; },\n'
        '      });\n'
        '    }\n'
        '    return origQuery.call(this, desc);\n'
        '  });\n'
        '}'
    )


def _build_webrtc_js(policy: str) -> str:
    """Patch RTCPeerConnection to force iceTransportPolicy."""
    if policy == 'default':
        return ''
    return (
        "if (typeof RTCPeerConnection !== 'undefined') {\n"
        '  const Orig = RTCPeerConnection;\n'
        '  const Patched = function RTCPeerConnection(config, constraints) {\n'
        '    config = Object.assign({}, config || {});\n'
        f'    config.iceTransportPolicy = {json.dumps(policy)};\n'
        '    return new Orig(config, constraints);\n'
        '  };\n'
        '  Patched.prototype = Orig.prototype;\n'
        '  Patched.prototype.constructor = Patched;\n'
        '  Object.getOwnPropertyNames(Orig).forEach(function(p) {\n'
        "    if (p !== 'prototype' && p !== 'length' && p !== 'name') {\n"
        '      try { Patched[p] = Orig[p]; } catch (e) {}\n'
        '    }\n'
        '  });\n'
        "  Object.defineProperty(Patched, 'name',\n"
        "    {value: 'RTCPeerConnection', configurable: true});\n"
        '  _mark(Patched);\n'
        '  window.RTCPeerConnection = Patched;\n'
        '}'
    )


_SECTION_BUILDERS: dict[str, Callable[..., str]] = {
    'hardware': _build_hardware_js,
    'screen': _build_screen_js,
    'webgl': _build_webgl_js,
    'media_devices': _build_media_devices_js,
    'audio': _build_audio_js,
    'speech': _build_speech_js,
    'locale': _build_locale_js,
    'network_connection': _build_network_connection_js,
    'fonts': _build_fonts_js,
    'permissions': _build_permissions_js,
    'webrtc_ip_policy': _build_webrtc_js,
}
