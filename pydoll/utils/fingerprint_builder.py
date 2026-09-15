"""Builds JavaScript injection scripts from a FingerprintConfig.

Each builder function returns a JS statement block (or empty string if the
corresponding config section is absent). ``build_fingerprint_js`` wraps every
non-empty block inside a single bootstrap IIFE that installs a global
``Function.prototype.toString`` hook, so every getter or method this module
redefines reports ``[native code]`` under introspection. The result is injected
via ``Page.addScriptToEvaluateOnNewDocument``.

Native first:
    Every signal Chrome can override through the DevTools Protocol is applied
    there by ``FingerprintApplier`` and never touched here: User-Agent,
    ``navigator.platform`` / ``appVersion`` / ``vendor`` / ``language`` /
    ``languages`` (``Emulation.setUserAgentOverride`` sets all of them), screen
    metrics, ``devicePixelRatio``, ``hardwareConcurrency``, timezone,
    geolocation, locale, CSS media features, permissions
    (``Browser.setPermission``) and touch (``maxTouchPoints`` included). A
    native override has no JavaScript function behind it, so nothing shows up
    in a stack trace and every read path agrees. Only signals CDP cannot set
    (``deviceMemory``, WebGL, media devices, speech voices, audio device
    capabilities, network connection, fonts, WebRTC policy, and the screen
    extras in headful mode) are handled with hardened JavaScript here.

Detectability notes:
    Fingerprinting suites (CreepJS, FingerprintJS, the Castle and LinkedIn
    checks) inspect overrides these ways, all of which this module defends
    against:

    - ``Object.getOwnPropertyDescriptor(proto, prop).get.toString()`` must
      return ``[native code]``. Every getter is registered with the shared
      toString hook so it does.
    - Spoofed properties must live on the correct prototype (e.g. ``screen``
      dimensions on ``Screen.prototype``), not as own-properties of the
      instance. Every getter targets the native prototype, and fake platform
      objects (media devices, voices) are created from the real prototype with
      no own properties: their values come from prototype getters keyed by a
      WeakMap.
    - A native accessor or method invoked on a foreign receiver throws
      ``Illegal invocation``. Every override delegates to the original native
      first, so the brand check, and its error, is the real one.
    - Values must stay physically possible: an ``OfflineAudioContext`` reports
      the sample rate it was created with, a claimed WebGL extension the GPU
      lacks is never faked as an empty object.
    - Platform objects cannot be structured-cloned, so every sink that
      serialises one (``structuredClone``, ``postMessage``, the history state,
      a notification's ``data``, and the same sinks in another same-origin
      realm) refuses the fake objects with the native ``DataCloneError``
      (nested anywhere a clone would reach, within a bound).
    - Wrapped constructors are plain functions sharing the native prototype
      chain, never Proxies: a Proxy fails the ``Object.setPrototypeOf(fn, fn)``
      cyclic check and prints anonymous under another realm's ``toString``.

    Residual limitation: a JavaScript accessor is a JavaScript frame, so an
    error thrown while it runs (the ``Illegal invocation`` above) carries one
    extra ``at get <prop>`` line in ``Error.stack`` that a native accessor does
    not. That is inherent to any JS override; the native-first strategy keeps
    the set of such getters as small as Chrome allows.
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
        MediaDevicesFingerprint,
        NetworkConnectionFingerprint,
        ScreenFingerprint,
        SpeechFingerprint,
        WebGLProfile,
        WebGPUProfile,
    )

# Navigator properties that CDP setUserAgentOverride already sets natively when
# a user_agent string is present. Skipped from JS injection so the reported
# getters stay genuinely native (a JS getter would replace the native one).
_CDP_HANDLED_NAV_PROPS = frozenset({'platform', 'vendor', 'app_version'})

# WebGL parameters that return Int32Array (not Float32Array).
_WEBGL_INT32_PARAMS = frozenset({'max_viewport_dims'})

# Shared bootstrap injected once before every section. Replaces
# Function.prototype.toString with a plain (non-Proxy) function backed by a
# registry of faked source strings, so every redefined getter/method reports
# [native code] without exposing a Proxy exotic object. It then exposes the
# closure-scoped helpers: _defG (native-looking accessor returning a constant),
# _defGf (accessor computing its value with access to the native one), _patchM
# (replace a method with a native-looking one), _fake / _defF (platform objects
# built from a real prototype whose values live in a WeakMap read by prototype
# getters). Nothing leaks to any global scope.
#
# ``NP`` resolves navigator's prototype in both the page (Navigator.prototype)
# and worker (WorkerNavigator.prototype) realms.
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
// Computed-name getter in an object literal: its ``.name`` is ``get <prop>``
// (so _nativeStr rebuilds the exact native string) and it has no own
// ``prototype``. Every getter is a single JavaScript frame that first invokes
// the original native getter on the receiver, reproducing its brand check:
// reading the property on the prototype or on a foreign object throws exactly
// like the native accessor instead of silently returning the value.
const _install = (target, prop, _g) => {
  _mark(_g);
  Object.defineProperty(target, prop, {get: _g, configurable: true, enumerable: true});
};
const _nativeGetter = (target, prop) => {
  const _od = Object.getOwnPropertyDescriptor(target, prop);
  return _od && _od.get;
};
const _defG = (target, prop, value) => {
  try {
    const _og = _nativeGetter(target, prop);
    const _h = { get [prop]() { if (_og) _og.call(this); return value; } };
    _install(target, prop, Object.getOwnPropertyDescriptor(_h, prop).get);
  } catch (e) {}
};
// ``compute(receiver, realValue)`` runs after the native getter returned, so
// it can keep the real value for instances that must stay truthful.
const _defGf = (target, prop, compute) => {
  try {
    const _og = _nativeGetter(target, prop);
    const _h = { get [prop]() { return compute(this, _og ? _og.call(this) : undefined); } };
    _install(target, prop, Object.getOwnPropertyDescriptor(_h, prop).get);
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
// Fake platform objects: created from the REAL prototype with no own
// properties; their values live in a WeakMap that prototype getters consult
// before falling back to the native getter (which keeps the native brand check
// for every real instance and every foreign receiver).
const _FAKES = new WeakMap();
const _fake = (proto, props) => { const o = Object.create(proto); _FAKES.set(o, props); return o; };
const _defF = (proto, prop) => {
  try {
    const _og = _nativeGetter(proto, prop);
    const _h = { get [prop]() {
      const f = _FAKES.get(this);
      return f !== undefined && prop in f ? f[prop] : (_og ? _og.call(this) : undefined);
    } };
    _install(proto, prop, Object.getOwnPropertyDescriptor(_h, prop).get);
  } catch (e) {}
};
// Constructor wrapper as a plain function (not a Proxy: a Proxy forwards
// ``setPrototypeOf`` to its target, so ``Object.setPrototypeOf(fn, fn)`` fails
// to raise the native "Cyclic __proto__" TypeError, and a pristine realm's
// ``toString`` prints it anonymous). The wrapper shares the native's
// prototype chain, ``prototype`` object, ``length`` and statics, throws the
// native message when called without ``new``, and is marked so the toString
// hook of every realm prints it native. ``onConstruct(args)`` may return
// replacement arguments; ``onCreated`` sees each new instance.
const _wrapCtor = (owner, name, onConstruct, onCreated) => {
  try {
    const Orig = owner[name];
    if (typeof Orig !== 'function') return;
    const Patched = { [name]: function () {
      if (!new.target) {
        throw new TypeError("Failed to construct '" + name + "': Please use the 'new' operator, "
          + 'this DOM object constructor cannot be called as a function.');
      }
      const args = Array.prototype.slice.call(arguments);
      const finalArgs = onConstruct ? onConstruct(args) : args;
      const proto = new.target === Patched ? Orig : new.target;
      const instance = Reflect.construct(Orig, finalArgs, proto);
      if (onCreated) onCreated(instance, finalArgs);
      return instance;
    } }[name];
    Object.setPrototypeOf(Patched, Object.getPrototypeOf(Orig));
    Object.defineProperty(Patched, 'prototype', {value: Orig.prototype, writable: false});
    Object.defineProperty(Patched, 'length', {value: Orig.length, configurable: true});
    for (const key of Reflect.ownKeys(Orig)) {
      if (['length', 'name', 'prototype', 'arguments', 'caller'].includes(key)) continue;
      try { Object.defineProperty(Patched, key, Object.getOwnPropertyDescriptor(Orig, key)); }
      catch (e) {}
    }
    try {
      Object.defineProperty(Orig.prototype, 'constructor',
        {value: Patched, writable: true, configurable: true});
    } catch (e) {}
    _mark(Patched);
    owner[name] = Patched;
    return Patched;
  } catch (e) { return undefined; }
};
// Platform objects cannot be structured-cloned; the fakes must refuse it too.
const _cloneError = (context, value) => {
  const ctor = Object.getPrototypeOf(value).constructor.name;
  return new DOMException(context + ': ' + ctor + ' object could not be cloned.',
    'DataCloneError');
};
// A fake built in another same-origin realm is absent from this realm's _FAKES:
// each realm keeps its own, so there is no shared slot to find. It stays
// recognisable without one, the same way the toString hook works: the
// prototypes this script patches carry accessors whose source every realm
// records in _FAKED, so a foreign object standing on such a prototype is a
// platform object over there, and no platform object clones. The answer is
// cached per prototype.
const _MARKED = new WeakMap();
const _markedProto = (proto) => {
  let marked = _MARKED.get(proto);
  if (marked !== undefined) return marked;
  marked = false;
  try {
    for (const key of Object.getOwnPropertyNames(proto)) {
      const d = Object.getOwnPropertyDescriptor(proto, key);
      if (d && d.get && _FAKED.has(_ORIG.call(d.get))) { marked = true; break; }
    }
  } catch (e) {}
  _MARKED.set(proto, marked);
  return marked;
};
const _foreignFake = (value) => {
  if (value instanceof Object) return false;
  for (let proto = Object.getPrototypeOf(value); proto !== null;
    proto = Object.getPrototypeOf(proto)) {
    if (_markedProto(proto)) return true;
  }
  return false;
};
// Finds a fake anywhere a structured clone would reach: own enumerable
// properties of plain objects and arrays, Map / Set entries. Bounded so an
// adversarial graph cannot stall the page; a fake past the bound is missed.
const _findFake = (value, seen, budget) => {
  if (value === null || typeof value !== 'object' || seen.has(value)) return null;
  if (_FAKES.has(value) || _foreignFake(value)) return value;
  seen.add(value);
  if (seen.size > budget) return null;
  const proto = Object.getPrototypeOf(value);
  let children = [];
  if (Array.isArray(value) || proto === null || proto === Object.prototype
      || Object.getPrototypeOf(proto) === null) {
    children = Object.keys(value).map((k) => value[k]);
  } else if (value instanceof Map) {
    children = [...value.keys(), ...value.values()];
  } else if (value instanceof Set) {
    children = [...value];
  }
  for (const child of children) {
    const found = _findFake(child, seen, budget);
    if (found !== null) return found;
  }
  return null;
};
const _guardClone = (target, method, owner) => {
  try {
    const orig = target[method];
    if (typeof orig !== 'function') return;
    const context = "Failed to execute '" + method + "' on '" + owner + "'";
    _patchM(target, method, function (value) {
      const fake = _findFake(value, new Set(), 5000);
      if (fake !== null) throw _cloneError(context, fake);
      return orig.apply(this, arguments);
    });
  } catch (e) {}
};
const _globalName = typeof window !== 'undefined' ? 'Window' : 'WorkerGlobalScope';
_guardClone(self, 'structuredClone', _globalName);
if (typeof MessagePort !== 'undefined') {
  _guardClone(MessagePort.prototype, 'postMessage', 'MessagePort');
}
if (typeof Worker !== 'undefined') _guardClone(Worker.prototype, 'postMessage', 'Worker');
if (typeof BroadcastChannel !== 'undefined') {
  _guardClone(BroadcastChannel.prototype, 'postMessage', 'BroadcastChannel');
}
if (typeof window !== 'undefined') _guardClone(window, 'postMessage', 'Window');
else _guardClone(self, 'postMessage', 'DedicatedWorkerGlobalScope');
if (typeof History !== 'undefined') {
  _guardClone(History.prototype, 'pushState', 'History');
  _guardClone(History.prototype, 'replaceState', 'History');
}
// A notification serialises options.data, so its guard sits on the constructor
// and raises the message Chrome raises while constructing one.
if (typeof Notification !== 'undefined') {
  _wrapCtor(self, 'Notification', (args) => {
    const options = args.length > 1 ? args[1] : null;
    if (options !== null && typeof options === 'object') {
      const fake = _findFake(options.data, new Set(), 5000);
      if (fake !== null) throw _cloneError("Failed to construct 'Notification'", fake);
    }
    return args;
  }, null);
}
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
    """Build ``navigator.userAgent``/``appVersion``/``platform`` getters for workers.

    Injected in worker realms only. ``Emulation.setUserAgentOverride`` on a
    worker session updates ``WorkerNavigator.userAgent`` for dedicated workers
    but not for shared / service workers, and never updates
    ``WorkerNavigator.platform`` for any worker type, so those would leak the
    real values. In the page realm the override is fully native and no getter
    is injected. Each is guarded by existence so a scope lacking a property is
    left untouched.
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


def build_fingerprint_js(config: FingerprintConfig) -> str:
    """Build the complete page fingerprint injection script.

    Returns a single JS string that installs the shared native-toString hook
    and overrides every configured fingerprint surface CDP cannot handle.
    Empty string if nothing to inject. Identity (User-Agent, platform,
    languages), permissions and screen metrics in headless mode are applied
    natively by ``FingerprintApplier`` and are never part of this script.

    Args:
        config: Fingerprint configuration.
    """
    parts: list[str] = []

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
    ``navigator.platform``, ``navigator.deviceMemory``, ``navigator.connection``,
    WebGL (via ``OffscreenCanvas``) and fonts. ``languages`` and
    ``hardwareConcurrency`` are applied natively to the worker session by
    ``FingerprintApplier`` (``acceptLanguage`` reaches every worker type).
    WebGPU is not part of this script: its interfaces are installed after the
    paused-on-start point, so ``build_fingerprint_worker_deferred_js`` carries
    it and the applier evaluates that script after resuming the worker.
    ``vendor`` is never injected: ``WorkerNavigator`` does not expose it, so
    adding it would itself be an anomaly.

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
    if 'network_connection' in config:
        parts.append(_build_network_connection_js(config['network_connection']))
    if 'webgl' in config:
        parts.append(_build_webgl_js(config['webgl']))
    if 'fonts' in config:
        parts.append(_build_fonts_js(config['fonts']))
    return _wrap(parts)


def build_fingerprint_worker_deferred_js(config: FingerprintConfig) -> str:
    """Build the worker script for sections that need the worker's conditional features.

    A worker paused on start (``waitForDebuggerOnStart``) is evaluated before
    Blink installs its conditional features: the ``[SecureContext]`` WebGPU
    interfaces (``GPU``, ``GPUAdapterInfo``, ``GPUSupportedLimits``) do not
    exist yet, so a WebGPU override evaluated at that point is a no-op, and a
    timer scheduled there never fires.

    Args:
        config: Fingerprint configuration.

    Returns:
        The deferred worker script, or '' when the profile has no such section.
    """
    parts: list[str] = []
    if 'webgpu' in config:
        parts.append(_build_webgpu_js(config['webgpu']))
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

    ``hardware_concurrency`` and ``max_touch_points`` are intentionally
    omitted: ``FingerprintApplier`` sets them via
    ``Emulation.setHardwareConcurrencyOverride`` and
    ``Emulation.setTouchEmulationEnabled`` (which also sets
    ``navigator.maxTouchPoints``), so both getters stay genuinely native. A
    profile with zero touch points relies on the host being non-touch.
    """
    if 'device_memory' not in hw:
        return ''
    return f'_defG(NP, "deviceMemory", {json.dumps(hw["device_memory"])});'


def _build_screen_js(scr: ScreenFingerprint) -> str:
    """Override screen/display getters CDP does not cover in headful mode.

    ``width``, ``height``, ``device_pixel_ratio``, ``inner_*`` and orientation
    are omitted: they are applied natively via
    ``Emulation.setDeviceMetricsOverride``. In headless mode this whole section
    is skipped by ``FingerprintApplier``: ``Emulation.updateScreen`` reshapes the
    virtual screen (size, work area, color depth, dpr) and
    ``Browser.setWindowBounds`` sizes the window, so every value below is native
    there.

    In headful mode ``avail_width``/``avail_height`` ARE injected here (on
    ``Screen.prototype``): CDP forces ``availWidth``/``availHeight`` equal to the
    screen size, which is a headless tell (no taskbar/dock gap).
    ``avail_top``/``avail_left``, ``color_depth``/``pixel_depth`` follow on
    ``Screen.prototype`` and ``outer_*`` are own accessors on ``window``, both
    matching the native location.
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
const COMPRESSED_FORMATS = 0x86A3;
const spoofVendor = %s;
const spoofRenderer = %s;
const paramOverrides = %s;
const ext1 = %s;
const ext2 = %s;
const precisionOverrides = %s;
const formatsByExtension = %s;
// getTranslatedShaderSource names the real backend (Metal, HLSL, GLSL), so the
// extension is dropped unless the profile lists it: a profile that claims a host
// where almost every machine exposes it can ask for it back, and then the
// translated source has to match the claimed backend.
const HIDDEN_EXT = 'WEBGL_debug_shaders';

function patchContext(proto, extOverrides) {
  const allowed = (name) => (extOverrides === null
    ? name !== HIDDEN_EXT
    : extOverrides.includes(name));
  const formatAllowed = (code) => {
    let owned = false;
    for (const name in formatsByExtension) {
      if (formatsByExtension[name].indexOf(code) === -1) continue;
      if (allowed(name)) return true;
      owned = true;
    }
    return !owned;
  };
  const origGetParameter = proto.getParameter;
  _patchM(proto, 'getParameter', function getParameter(pname) {
    const real = origGetParameter.call(this, pname);
    if (pname === VENDOR) return spoofVendor;
    if (pname === RENDERER) return spoofRenderer;
    if (pname === COMPRESSED_FORMATS && ArrayBuffer.isView(real)) {
      return new Uint32Array(Array.prototype.filter.call(real, formatAllowed));
    }
    const override = paramOverrides[pname];
    if (override === undefined) return real;
    return ArrayBuffer.isView(override) ? override.slice() : override;
  });

  const hasPrecision = typeof WebGLShaderPrecisionFormat !== 'undefined';
  if (hasPrecision && Object.keys(precisionOverrides).length > 0) {
    const origGetShaderPrecisionFormat = proto.getShaderPrecisionFormat;
    _patchM(proto, 'getShaderPrecisionFormat',
      function getShaderPrecisionFormat(shaderType, precisionType) {
        const real = origGetShaderPrecisionFormat.call(this, shaderType, precisionType);
        const p = precisionOverrides[shaderType + ':' + precisionType];
        if (!p || real === null) return real;
        return _fake(WebGLShaderPrecisionFormat.prototype,
          {rangeMin: p[0], rangeMax: p[1], precision: p[2]});
      });
  }

  const origGetExtension = proto.getExtension;
  const origGetSupportedExtensions = proto.getSupportedExtensions;
  _patchM(proto, 'getExtension', function getExtension(name) {
    const real = origGetExtension.call(this, name);
    return allowed(name) ? real : null;
  });
  _patchM(proto, 'getSupportedExtensions', function getSupportedExtensions() {
    const real = origGetSupportedExtensions.call(this);
    return real === null ? real : real.filter(allowed);
  });
}

if (typeof WebGLShaderPrecisionFormat !== 'undefined'
    && Object.keys(precisionOverrides).length > 0) {
  for (const prop of ['rangeMin', 'rangeMax', 'precision']) {
    _defF(WebGLShaderPrecisionFormat.prototype, prop);
  }
}
if (typeof WebGLRenderingContext !== 'undefined') {
  patchContext(WebGLRenderingContext.prototype, ext1);
}
if (typeof WebGL2RenderingContext !== 'undefined') {
  patchContext(WebGL2RenderingContext.prototype, ext2);
}"""

# Maps python key -> WebGL parameter constant (WebGL1 and WebGL2 limits).
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
    'max_cube_map_texture_size': 0x851C,
    'max_varying_vectors': 0x8DFC,
    'max_3d_texture_size': 0x8073,
    'max_array_texture_layers': 0x88FF,
    'max_color_attachments': 0x8CDF,
    'max_draw_buffers': 0x8824,
    'max_samples': 0x8D57,
    'max_uniform_block_size': 0x8A30,
    'max_uniform_buffer_bindings': 0x8A2F,
    'max_vertex_uniform_blocks': 0x8A2B,
    'max_fragment_uniform_blocks': 0x8A2D,
    'max_combined_uniform_blocks': 0x8A2E,
    'max_vertex_output_components': 0x9122,
    'max_fragment_input_components': 0x9125,
    'max_element_index': 0x8D6B,
    'max_vertex_uniform_components': 0x8B4A,
    'max_fragment_uniform_components': 0x8B49,
    'max_varying_components': 0x8B4B,
    'max_combined_vertex_uniform_components': 0x8A31,
    'max_combined_fragment_uniform_components': 0x8A33,
    'uniform_buffer_offset_alignment': 0x8A34,
    'max_texture_lod_bias': 0x84FD,
    'max_transform_feedback_interleaved_components': 0x8C8A,
}

# Maps shader type names to WebGL constants
_SHADER_TYPE_MAP: dict[str, int] = {
    'vertex': 0x8B31,
    'fragment': 0x8B30,
}

# Format enums each compressed-texture extension contributes to
# getParameter(COMPRESSED_TEXTURE_FORMATS), as (first, last) inclusive ranges.
# Chrome enables an extension the moment getExtension asks for it, even when the
# profile hides the extension from the context, and an enabled extension adds
# its formats to that list: without filtering, a claimed D3D11 GPU still reports
# the ASTC/ETC/PVRTC formats of the host's real GPU.
_COMPRESSED_TEXTURE_FORMATS: dict[str, tuple[tuple[int, int], ...]] = {
    'WEBGL_compressed_texture_s3tc': ((0x83F0, 0x83F3),),
    'WEBKIT_WEBGL_compressed_texture_s3tc': ((0x83F0, 0x83F3),),
    'WEBGL_compressed_texture_s3tc_srgb': ((0x8C4C, 0x8C4F),),
    'WEBGL_compressed_texture_pvrtc': ((0x8C00, 0x8C03),),
    'WEBKIT_WEBGL_compressed_texture_pvrtc': ((0x8C00, 0x8C03),),
    'WEBGL_compressed_texture_etc1': ((0x8D64, 0x8D64),),
    'WEBGL_compressed_texture_etc': ((0x9270, 0x9279),),
    'WEBGL_compressed_texture_astc': ((0x93B0, 0x93BD), (0x93D0, 0x93DD)),
    'EXT_texture_compression_rgtc': ((0x8DBB, 0x8DBE),),
    'EXT_texture_compression_bptc': ((0x8E8C, 0x8E8F),),
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


def _build_compressed_formats_js() -> str:
    """Build the JS map of extension name to the format enums it advertises."""
    expanded = {
        name: [code for low, high in ranges for code in range(low, high + 1)]
        for name, ranges in _COMPRESSED_TEXTURE_FORMATS.items()
    }
    return json.dumps(expanded)


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
    """Build the WebGL override block.

    Every patched method calls the native one first, so the receiver brand
    check and the real value come from Chrome. Extension lists are an
    allow-list intersected with what the GPU really exposes: a claimed
    extension the GPU lacks is dropped rather than faked (a fake ``{}`` has
    none of the extension's constants and is an instant tell), and
    ``WEBGL_debug_shaders`` is always hidden because its translated shader
    source names the real backend.

    ``COMPRESSED_TEXTURE_FORMATS`` follows the same allow-list: the native
    ``getExtension`` call the override makes before hiding an extension still
    enables it inside Chrome, which appends the extension's formats to that
    parameter, so the array is filtered back to the formats of the extensions
    the context advertises (an ASTC or ETC format under a D3D11 renderer names
    the host GPU on its own).
    """
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
        _build_compressed_formats_js(),
    )


_WEBGPU_JS_TEMPLATE = """\
if (typeof GPU !== 'undefined' && navigator.gpu && typeof GPUAdapterInfo !== 'undefined'
    && typeof GPUSupportedLimits !== 'undefined') {
  const info = %s;
  const limits = %s;
  const features = %s;
  for (const prop of Object.keys(info)) _defF(GPUAdapterInfo.prototype, prop);
  if (limits !== null) {
    for (const prop of Object.keys(limits)) _defF(GPUSupportedLimits.prototype, prop);
  }
  const featureSet = features === null ? null : new Set(features);
  if (featureSet !== null && typeof GPUSupportedFeatures !== 'undefined') {
    const FP = GPUSupportedFeatures.prototype;
    const origHas = FP.has;
    _patchM(FP, 'has', function has(value) {
      const real = origHas.call(this, value);
      return _FAKES.has(this) ? featureSet.has(String(value)) : real;
    });
    _defGf(FP, 'size', (self, real) => (_FAKES.has(self) ? featureSet.size : real));
    const sameAsReal = (set) => {
      if (set.size !== featureSet.size) return false;
      for (const value of set) if (!featureSet.has(value)) return false;
      return true;
    };
    for (const method of ['keys', 'values', 'entries']) {
      const orig = FP[method];
      _patchM(FP, method, function () {
        const real = orig.call(this);
        if (!_FAKES.has(this) || sameAsReal(new Set(orig.call(this)))) return real;
        const it = new Set(featureSet)[method]();
        try {
          Object.defineProperty(it, Symbol.toStringTag,
            {value: 'GPUSupportedFeatures Iterator', configurable: true});
        } catch (e) {}
        return it;
      });
    }
    const origForEach = FP.forEach;
    _patchM(FP, 'forEach', function forEach(callback, thisArg) {
      if (!_FAKES.has(this)) return origForEach.apply(this, arguments);
      origForEach.call(this, () => {});
      const self = this;
      new Set(featureSet).forEach((value, key) => callback.call(thisArg, value, key, self));
    });
    try {
      Object.defineProperty(FP, Symbol.iterator,
        {value: FP.values, writable: true, configurable: true});
    } catch (e) {}
  }
  if (typeof GPUAdapter !== 'undefined') {
    const registry = {info: info, limits: limits, features: featureSet === null ? null : {}};
    for (const prop of Object.keys(registry)) {
      if (registry[prop] === null) continue;
      _defGf(GPUAdapter.prototype, prop, (adapter, real) => {
        if (real) _FAKES.set(real, registry[prop]);
        return real;
      });
    }
  }
  if (typeof GPUAdapter !== 'undefined' && GPUAdapter.prototype.requestDevice) {
    const origRequestDevice = GPUAdapter.prototype.requestDevice;
    _patchM(GPUAdapter.prototype, 'requestDevice', function requestDevice() {
      return origRequestDevice.apply(this, arguments).then((device) => {
        try { _FAKES.set(device.adapterInfo, info); } catch (e) {}
        return device;
      });
    });
  }
}"""


def _build_webgpu_js(webgpu: WebGPUProfile) -> str:
    """Override what the real WebGPU adapter reports.

    ``requestAdapter()`` still resolves the real adapter (so ``requestDevice``
    and rendering work). ``features`` is a setlike, so ``has``, ``size``,
    the iterators and ``forEach`` are patched together to describe one set.
    """
    info: dict[str, object] = {'vendor': webgpu['vendor']}
    for key in ('architecture', 'device', 'description'):
        if key in webgpu:
            info[key] = webgpu[key]
    if 'is_fallback_adapter' in webgpu:
        info['isFallbackAdapter'] = webgpu['is_fallback_adapter']
    limits = webgpu.get('limits')
    features = webgpu.get('features')
    return _WEBGPU_JS_TEMPLATE % (
        json.dumps(info),
        json.dumps(limits) if limits else 'null',
        json.dumps(features) if features is not None else 'null',
    )


def _build_media_devices_js(md: MediaDevicesFingerprint) -> str:
    """Override ``enumerateDevices`` with fake devices built on the real prototypes.

    Inputs are ``InputDeviceInfo`` instances and outputs ``MediaDeviceInfo``,
    listed in Chrome's order (audio inputs, video inputs, audio outputs), with
    no own properties: the values come from prototype getters that consult the
    fake registry and otherwise defer to the native getter. Each call returns
    fresh objects, as the native method does, and ``getCapabilities()`` on a
    fake input answers ``{}`` like a device without permission.
    ``enumerateDevices`` awaits the native call first so the receiver check and
    the async timing are the real ones.
    """
    audio_in = md.get('audio_inputs', 0)
    audio_out = md.get('audio_outputs', 0)
    video_in = md.get('video_inputs', 0)
    return f"""\
if (typeof MediaDeviceInfo !== 'undefined' && typeof MediaDevices !== 'undefined'
    && MediaDevices.prototype.enumerateDevices) {{
  const inputProto = typeof InputDeviceInfo !== 'undefined'
    ? InputDeviceInfo.prototype : MediaDeviceInfo.prototype;
  const makeDev = (kind) => _fake(kind === 'audiooutput' ? MediaDeviceInfo.prototype : inputProto,
    {{deviceId: '', kind: kind, label: '', groupId: ''}});
  for (const prop of ['deviceId', 'kind', 'label', 'groupId']) {{
    _defF(MediaDeviceInfo.prototype, prop);
  }}
  const origToJSON = MediaDeviceInfo.prototype.toJSON;
  _patchM(MediaDeviceInfo.prototype, 'toJSON', function toJSON() {{
    const f = _FAKES.get(this);
    return f !== undefined ? Object.assign({{}}, f) : origToJSON.call(this);
  }});
  const makeDevices = () => {{
    const devices = [];
    for (let i = 0; i < {audio_in}; i++) devices.push(makeDev('audioinput'));
    for (let i = 0; i < {video_in}; i++) devices.push(makeDev('videoinput'));
    for (let i = 0; i < {audio_out}; i++) devices.push(makeDev('audiooutput'));
    return devices;
  }};
  if (typeof InputDeviceInfo !== 'undefined' && InputDeviceInfo.prototype.getCapabilities) {{
    const origCapabilities = InputDeviceInfo.prototype.getCapabilities;
    _patchM(InputDeviceInfo.prototype, 'getCapabilities', function getCapabilities() {{
      return _FAKES.has(this) ? {{}} : origCapabilities.call(this);
    }});
  }}
  const origEnumerate = MediaDevices.prototype.enumerateDevices;
  _patchM(MediaDevices.prototype, 'enumerateDevices', function enumerateDevices() {{
    return origEnumerate.call(this).then(() => makeDevices());
  }});
}}"""


def _build_audio_js(audio: AudioFingerprint) -> str:
    """Override realtime ``AudioContext`` device capabilities.

    An ``OfflineAudioContext``, or an ``AudioContext`` constructed with an
    explicit ``sampleRate``, must report the rate it was constructed with, so
    those keep the native value (the constructor is wrapped to remember
    explicit rates); only realtime contexts created without a rate,
    the ones that describe the audio device, take the profile's values. The
    rendered audio hash is not touched by any of this.

    ``baseLatency`` and ``outputLatency`` are a whole output buffer divided by
    the device rate, so overriding the rate alone leaves a latency that resolves
    to a fractional frame count at the claimed rate (measured: 256/44100 s
    reported next to a claimed 48000 Hz, which needs 278.64 frames). Both are
    re-derived here: the host's buffer size in frames, recovered from the real
    getters, divided by the claimed rate. A zero ``outputLatency`` (headless has
    no output device) stays zero.
    """
    lines: list[str] = [
        'const _truthful = new WeakSet();',
        "const _isOffline = (ctx) => typeof OfflineAudioContext !== 'undefined'"
        ' && ctx instanceof OfflineAudioContext;',
        "if (typeof AudioContext !== 'undefined') {",
        "  const _ctor = _wrapCtor(self, 'AudioContext', null, (ctx, args) => {",
        '    if (args[0] && args[0].sampleRate !== undefined) _truthful.add(ctx);',
        '  });',
        "  if (_ctor && 'webkitAudioContext' in self) self.webkitAudioContext = _ctor;",
        '}',
    ]
    if 'sample_rate' in audio:
        val = json.dumps(audio['sample_rate'])
        lines.append("const _deviceRate = _nativeGetter(BaseAudioContext.prototype, 'sampleRate');")
        lines.append(
            "_defGf(BaseAudioContext.prototype, 'sampleRate', (self, real) =>\n"
            f'  (_isOffline(self) || _truthful.has(self)) ? real : {val});'
        )
        lines.append(
            "if (typeof AudioContext !== 'undefined' && _deviceRate) {\n"
            "  for (const _prop of ['baseLatency', 'outputLatency']) {\n"
            '    if (!_nativeGetter(AudioContext.prototype, _prop)) continue;\n'
            '    _defGf(AudioContext.prototype, _prop, (self, real) =>\n'
            '      (!real || _truthful.has(self))\n'
            f'        ? real : Math.round(real * _deviceRate.call(self)) / {val});\n'
            '  }\n'
            '}'
        )
    if 'max_channel_count' in audio:
        val = json.dumps(audio['max_channel_count'])
        lines.append(
            "_defGf(AudioDestinationNode.prototype, 'maxChannelCount', (self, real) =>\n"
            f'  _isOffline(self.context) ? real : {val});'
        )
    return '\n'.join(lines)


def _build_speech_js(speech: SpeechFingerprint) -> str:
    """Override ``speechSynthesis.getVoices()`` with voices on the real prototype.

    Each voice is a ``SpeechSynthesisVoice`` with no own properties; ``getVoices``
    invokes the native method first so a foreign receiver throws the native
    ``Illegal invocation``. The list is returned synchronously on the first
    call, which is how Chrome on Windows behaves (its voices load with the
    process).
    """
    voices_data = json.dumps(speech['voices'])
    return f"""\
if (typeof SpeechSynthesisVoice !== 'undefined' && typeof SpeechSynthesis !== 'undefined'
    && SpeechSynthesis.prototype.getVoices) {{
  const voicesData = {voices_data};
  for (const prop of ['name', 'lang', 'localService', 'voiceURI', 'default']) {{
    _defF(SpeechSynthesisVoice.prototype, prop);
  }}
  const fakeVoices = voicesData.map((v, idx) => _fake(SpeechSynthesisVoice.prototype, {{
    name: v.name, lang: v.lang,
    localService: v.local_service !== undefined ? v.local_service : true,
    voiceURI: v.name, default: idx === 0,
  }}));
  const origGetVoices = SpeechSynthesis.prototype.getVoices;
  _patchM(SpeechSynthesis.prototype, 'getVoices', function getVoices() {{
    origGetVoices.call(this);
    return fakeVoices.slice();
  }});
}}"""


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


_FONTS_JS_TEMPLATE = r"""if (typeof FontFace !== 'undefined' && FontFace.prototype.load) {
  const allow = new Set(%s);
  const LOCAL = /local\s*\(/i;
  const REMOTE = /url\s*\(/i;
  const sources = new WeakMap();
  _wrapCtor(self, 'FontFace', null, (face, args) => {
    if (typeof args[1] === 'string') sources.set(face, args[1]);
  });
  const norm = (s) => String(s).trim().replace(/^["']|["']$/g, '').toLowerCase();
  const _realLoad = FontFace.prototype.load;
  _patchM(FontFace.prototype, 'load', function load() {
    const source = sources.get(this);
    const local = typeof source === 'string' && LOCAL.test(source) && !REMOTE.test(source);
    const real = _realLoad.apply(this, arguments);
    if (!local || allow.has(norm(this.family))) return real;
    return real.then(() => {
      throw new DOMException('A network error occurred.', 'NetworkError');
    });
  });
}"""


def _build_fonts_js(fonts: FontFingerprint) -> str:
    """Override ``FontFace.load()`` to present a coherent local font set.

    ``new FontFace(f, 'local("f")').load()`` is the JavaScript presence probe
    (CreepJS unions it with the width-based measurement): it resolves when the
    local font exists and rejects with a ``NetworkError`` otherwise. The probe
    is answered from the profile's own list: a family outside
    ``available_fonts`` rejects the way an absent font does, whatever the host
    has installed, so the host's own font set (and the OS it names) stops
    leaking through the families the profile never mentions.

    A family on the list still has to convince the layout engine, which this
    cannot reach, so a listed family the host lacks keeps the native rejection
    instead of resolving against a fallback the page would measure. Only
    ``local()``-only sources are answered this way: the source string is
    recorded at construction so a real ``url()`` web font, which loads
    regardless of what is installed, keeps native behaviour end to end.

    ``FontFaceSet.check()`` is deliberately left native: it answers whether a
    font needs loading, so real Chrome returns ``true`` for any family name,
    and forcing ``false`` there would be a lie against the native API itself,
    not only against the layout engine.

    Width-based detection (the FingerprintJS technique: a span's ``offsetWidth``
    in the probed family against a fallback) reads the layout engine and is
    not reachable from here. The only way to pass it is to install the claimed
    fonts on the host and keep ``available_fonts`` equal to what is installed.
    Works in workers too (``FontFace`` exists there).
    """
    available = fonts.get('available_fonts', [])
    if not available:
        return ''
    allow = sorted({f.lower() for f in available})
    return _FONTS_JS_TEMPLATE % json.dumps(allow)


def _build_webrtc_js(policy: str) -> str:
    """Patch RTCPeerConnection (and its ``webkit`` alias) to force iceTransportPolicy.

    Chrome exposes the same constructor as ``RTCPeerConnection`` and
    ``webkitRTCPeerConnection``; both are replaced by one wrapper that shares
    the native prototype chain, ``prototype`` object, ``length`` and statics,
    so the alias cannot bypass the policy, the identity stays equal, and a
    call without ``new`` throws the native error. The native launch flag
    ``--force-webrtc-ip-handling-policy`` (``ChromiumOptions.webrtc_leak_protection``)
    needs no patch at all and is the preferred route.
    """
    if policy == 'default':
        return ''
    return (
        "if (typeof RTCPeerConnection !== 'undefined') {\n"
        "  const Patched = _wrapCtor(window, 'RTCPeerConnection', (args) => {\n"
        '    const config = Object.assign({}, args[0] || {});\n'
        f'    config.iceTransportPolicy = {json.dumps(policy)};\n'
        '    return [config].concat(Array.prototype.slice.call(args, 1));\n'
        '  }, null);\n'
        "  if (Patched && 'webkitRTCPeerConnection' in window) {\n"
        '    window.webkitRTCPeerConnection = Patched;\n'
        '  }\n'
        '}'
    )


_SECTION_BUILDERS: dict[str, Callable[..., str]] = {
    'hardware': _build_hardware_js,
    'screen': _build_screen_js,
    'webgl': _build_webgl_js,
    'webgpu': _build_webgpu_js,
    'media_devices': _build_media_devices_js,
    'audio': _build_audio_js,
    'speech': _build_speech_js,
    'network_connection': _build_network_connection_js,
    'fonts': _build_fonts_js,
    'webrtc_ip_policy': _build_webrtc_js,
}
