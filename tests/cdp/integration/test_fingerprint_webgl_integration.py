"""Real-Chrome tests for the WebGL extension lists a fingerprint profile declares.

The browser runs on SwiftShader, whose extension list is shorter than any
discrete GPU's, so a profile that names a discrete GPU declares extensions the
context lacks. One raw tab reads what the host really exposes; a second tab
with the profile applied must report the declared list in Chrome's order, hand
out extension objects shaped like Blink's for the missing names, and answer
their parameters and compressed formats the way a context that has them does.
"""

from __future__ import annotations

import asyncio

import pytest

from pydoll import Chrome, ChromiumOptions
from pydoll.utils.webgl_extensions import WEBGL1_ORDER, WEBGL2_ORDER

EXTRA = [
    'KHR_parallel_shader_compile',
    'WEBGL_blend_func_extended',
    'WEBGL_compressed_texture_pvrtc',
    'WEBGL_provoking_vertex',
]
HIDDEN = 'OES_standard_derivatives'
COMPLETION_STATUS_KHR = 0x91B1
INVALID_ENUM = 0x0500
MAX_ANISOTROPY = 8

READ_REAL = """
(() => {
  const out = {};
  for (const kind of ['webgl', 'webgl2']) {
    const gl = document.createElement('canvas').getContext(kind);
    out[kind] = gl ? gl.getSupportedExtensions() : null;
  }
  return out;
})()
"""

PROBE = """
(() => {
  const out = {};
  const gl = document.createElement('canvas').getContext('webgl');
  const gl2 = document.createElement('canvas').getContext('webgl2');
  if (!gl || !gl2) return 'no-webgl';
  out.list1 = gl.getSupportedExtensions();
  out.list2 = gl2.getSupportedExtensions();
  out.unsupported = out.list1.filter((name) => gl.getExtension(name) === null);
  out.debugShaders = gl.getExtension('WEBGL_debug_shaders');
  out.vaoOnWebGL2 = gl2.getExtension('OES_vertex_array_object');

  const khr = gl.getExtension('KHR_parallel_shader_compile');
  const proto = Object.getPrototypeOf(khr);
  out.khr = {
    same: gl.getExtension('KHR_parallel_shader_compile') === khr,
    tag: Object.prototype.toString.call(khr),
    ownOnInstance: Object.getOwnPropertyNames(khr),
    protoKeys: Object.getOwnPropertyNames(proto),
    protoHasConstructor: Object.prototype.hasOwnProperty.call(proto, 'constructor'),
    ctorIsObject: khr.constructor === Object,
    completion: khr.COMPLETION_STATUS_KHR,
    constDesc: Object.getOwnPropertyDescriptor(proto, 'COMPLETION_STATUS_KHR'),
    tagDesc: Object.getOwnPropertyDescriptor(proto, Symbol.toStringTag),
  };

  const virgin = document.createElement('canvas').getContext('webgl');
  out.dualBefore = {value: virgin.getParameter(0x88FC), error: virgin.getError()};
  const blend = virgin.getExtension('WEBGL_blend_func_extended');
  out.dualAfter = {
    value: virgin.getParameter(blend.MAX_DUAL_SOURCE_DRAW_BUFFERS_WEBGL),
    error: virgin.getError(),
  };
  out.blendKeys = Object.getOwnPropertyNames(Object.getPrototypeOf(blend));

  const fresh = document.createElement('canvas').getContext('webgl');
  out.formatsBefore = Array.from(fresh.getParameter(0x86A3));
  fresh.getExtension('WEBGL_compressed_texture_pvrtc');
  out.formatsAfter = Array.from(fresh.getParameter(0x86A3));

  const vao = gl.getExtension('OES_vertex_array_object');
  out.vaoMethod = vao ? {
    src: Function.prototype.toString.call(vao.bindVertexArrayOES),
    name: vao.bindVertexArrayOES.name,
    hasPrototype: 'prototype' in vao.bindVertexArrayOES,
  } : null;

  const hidden = document.createElement('canvas').getContext('webgl');
  out.hidden = {
    ext: hidden.getExtension('OES_standard_derivatives'),
    listed: hidden.getSupportedExtensions().includes('OES_standard_derivatives'),
    hint: hidden.getParameter(0x8B8B),
    error: hidden.getError(),
  };

  const aniso = document.createElement('canvas').getContext('webgl');
  out.anisoBefore = {value: aniso.getParameter(0x84FF), error: aniso.getError()};
  aniso.getExtension('EXT_texture_filter_anisotropic');
  out.anisoAfter = {value: aniso.getParameter(0x84FF), error: aniso.getError()};

  const a = document.createElement('canvas').getContext('webgl2');
  const b = document.createElement('canvas').getContext('webgl2');
  const pa = a.getExtension('WEBGL_provoking_vertex');
  const pb = b.getExtension('WEBGL_provoking_vertex');
  out.provoking = {
    distinct: pa !== pb,
    sharedProto: Object.getPrototypeOf(pa) === Object.getPrototypeOf(pb),
    sameMethod: pa.provokingVertexWEBGL === pb.provokingVertexWEBGL,
    protoKeys: Object.getOwnPropertyNames(Object.getPrototypeOf(pa)),
    length: pa.provokingVertexWEBGL.length,
    returnsUndefined: pa.provokingVertexWEBGL(pa.FIRST_VERTEX_CONVENTION_WEBGL) === undefined,
    onWebGL1: gl.getExtension('WEBGL_provoking_vertex'),
  };

  const dying = document.createElement('canvas').getContext('webgl');
  dying.getExtension('WEBGL_blend_func_extended');
  dying.getExtension('WEBGL_lose_context').loseContext();
  out.lost = {
    isLost: dying.isContextLost(),
    supported: dying.getSupportedExtensions(),
    khr: dying.getExtension('KHR_parallel_shader_compile'),
    blend: dying.getExtension('WEBGL_blend_func_extended'),
    dual: dying.getParameter(0x88FC),
    vendor: dying.getParameter(0x9245),
    error: dying.getError(),
  };
  return out;
})()
"""

FINGERPRINT_BASE = {
    'user_agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/152.0.7977.83 Safari/537.36'
    ),
    'webgl': {
        'vendor': 'Google Inc. (NVIDIA)',
        'renderer': (
            'ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 (0x00002503) Direct3D11 vs_5_0 ps_5_0, D3D11)'
        ),
    },
}


def _options() -> ChromiumOptions:
    options = ChromiumOptions()
    options.headless = True
    options.start_timeout = 60
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--use-angle=swiftshader')
    options.add_argument('--enable-unsafe-swiftshader')
    return options


async def _value(tab, script: str):
    response = await tab.execute_script(script, return_by_value=True)
    return response['result']['result'].get('value')


@pytest.fixture(scope='module')
def webgl_snapshot():
    """The host's real extension lists and the probe of a tab with the profile applied."""

    async def _run():
        async with Chrome(options=_options()) as browser:
            raw = await browser.start()
            await raw.go_to('about:blank')
            real = await _value(raw, READ_REAL)
            if not real or real['webgl'] is None or real['webgl2'] is None:
                return None, None
            profile = dict(FINGERPRINT_BASE)
            profile['webgl'] = dict(FINGERPRINT_BASE['webgl'])
            webgl1 = [name for name in real['webgl'] if name != HIDDEN] + EXTRA
            profile['webgl']['supported_extensions'] = webgl1
            webgl2 = real['webgl2'] + EXTRA + ['OES_vertex_array_object']
            profile['webgl']['webgl2_extensions'] = webgl2
            profile['webgl']['max_texture_max_anisotropy'] = MAX_ANISOTROPY
            tab = await browser.new_tab()
            await tab.apply_fingerprint(profile)
            await tab.go_to('about:blank')
            return real, await _value(tab, PROBE)

    return asyncio.run(_run())


@pytest.fixture
def snapshot(webgl_snapshot):
    real, probe = webgl_snapshot
    if real is None or probe == 'no-webgl':
        pytest.skip('WebGL unavailable on this host')
    return real, probe


def _declared_only(real: list[str]) -> list[str]:
    return [name for name in EXTRA if name not in real]


class TestDeclaredExtensions:
    def test_the_lists_are_the_profiles_in_chrome_order(self, snapshot):
        real, probe = snapshot
        want1 = set(real['webgl']) | {name for name in EXTRA if name in WEBGL1_ORDER}
        want1.discard('WEBGL_debug_shaders')
        want1.discard(HIDDEN)
        assert set(probe['list1']) == want1
        assert probe['list1'] == [name for name in WEBGL1_ORDER if name in want1]
        want2 = set(real['webgl2']) | {name for name in EXTRA if name in WEBGL2_ORDER}
        want2.discard('WEBGL_debug_shaders')
        assert set(probe['list2']) == want2
        assert probe['list2'] == [name for name in WEBGL2_ORDER if name in want2]

    def test_every_listed_extension_is_handed_out(self, snapshot):
        _, probe = snapshot
        assert probe['unsupported'] == []
        assert probe['debugShaders'] is None

    def test_a_webgl1_only_name_is_not_constructed_on_webgl2(self, snapshot):
        _, probe = snapshot
        assert probe['vaoOnWebGL2'] is None

    def test_a_constructed_extension_has_blinks_shape(self, snapshot):
        real, probe = snapshot
        if 'KHR_parallel_shader_compile' not in _declared_only(real['webgl']):
            pytest.skip('host exposes KHR_parallel_shader_compile itself')
        khr = probe['khr']
        assert khr['same'] is True
        assert khr['tag'] == '[object KHRParallelShaderCompile]'
        assert khr['ownOnInstance'] == []
        assert khr['protoKeys'] == ['COMPLETION_STATUS_KHR']
        assert khr['protoHasConstructor'] is False
        assert khr['ctorIsObject'] is True
        assert khr['completion'] == COMPLETION_STATUS_KHR
        assert khr['constDesc'] == {
            'value': COMPLETION_STATUS_KHR,
            'writable': False,
            'enumerable': True,
            'configurable': False,
        }
        assert khr['tagDesc'] == {
            'value': 'KHRParallelShaderCompile',
            'writable': False,
            'enumerable': False,
            'configurable': True,
        }

    def test_an_extension_parameter_answers_only_once_enabled(self, snapshot):
        real, probe = snapshot
        if 'WEBGL_blend_func_extended' not in _declared_only(real['webgl']):
            pytest.skip('host exposes WEBGL_blend_func_extended itself')
        assert probe['dualBefore'] == {'value': None, 'error': INVALID_ENUM}
        assert probe['dualAfter'] == {'value': 1, 'error': 0}
        assert probe['blendKeys'] == [
            'SRC1_COLOR_WEBGL',
            'SRC1_ALPHA_WEBGL',
            'ONE_MINUS_SRC1_COLOR_WEBGL',
            'ONE_MINUS_SRC1_ALPHA_WEBGL',
            'MAX_DUAL_SOURCE_DRAW_BUFFERS_WEBGL',
        ]

    def test_compressed_formats_appear_when_the_extension_is_enabled(self, snapshot):
        real, probe = snapshot
        if 'WEBGL_compressed_texture_pvrtc' not in _declared_only(real['webgl']):
            pytest.skip('host exposes WEBGL_compressed_texture_pvrtc itself')
        pvrtc = [0x8C00, 0x8C01, 0x8C02, 0x8C03]
        assert not any(code in probe['formatsBefore'] for code in pvrtc)
        assert probe['formatsAfter'][-4:] == pvrtc

    def test_real_extension_methods_stay_native(self, snapshot):
        _, probe = snapshot
        assert probe['vaoMethod'] is not None
        assert probe['vaoMethod']['src'] == 'function bindVertexArrayOES() { [native code] }'
        assert probe['vaoMethod']['name'] == 'bindVertexArrayOES'
        assert probe['vaoMethod']['hasPrototype'] is False


class TestChromeParity:
    """Behaviours measured on a real Chrome the override has to reproduce."""

    def test_hiding_an_extension_does_not_enable_it_inside_chrome(self, snapshot):
        """Asking Chrome for the extension would enable it and unlock its parameter,
        so a hidden extension is never requested: its parameter stays INVALID_ENUM."""
        real, probe = snapshot
        if HIDDEN not in real['webgl']:
            pytest.skip(f'host does not expose {HIDDEN}, nothing to hide')
        assert probe['hidden'] == {'ext': None, 'listed': False, 'hint': None, 'error': INVALID_ENUM}

    def test_a_profile_limit_of_an_extension_parameter_waits_for_the_extension(self, snapshot):
        _, probe = snapshot
        assert probe['anisoBefore'] == {'value': None, 'error': INVALID_ENUM}
        assert probe['anisoAfter'] == {'value': MAX_ANISOTROPY, 'error': 0}

    def test_constructed_extensions_share_one_interface_per_realm(self, snapshot):
        """Two contexts get two objects on one prototype, so the method is the same
        function for both, the way Chrome's interface objects behave."""
        real, probe = snapshot
        if 'WEBGL_provoking_vertex' in real['webgl2']:
            pytest.skip('host exposes WEBGL_provoking_vertex itself')
        provoking = probe['provoking']
        assert provoking['distinct'] is True
        assert provoking['sharedProto'] is True
        assert provoking['sameMethod'] is True
        assert provoking['protoKeys'] == [
            'FIRST_VERTEX_CONVENTION_WEBGL',
            'LAST_VERTEX_CONVENTION_WEBGL',
            'PROVOKING_VERTEX_WEBGL',
            'provokingVertexWEBGL',
        ]
        assert provoking['length'] == 1
        assert provoking['returnsUndefined'] is True
        assert provoking['onWebGL1'] is None

    def test_a_lost_context_answers_null_like_chrome(self, snapshot):
        _, probe = snapshot
        assert probe['lost'] == {
            'isLost': True,
            'supported': None,
            'khr': None,
            'blend': None,
            'dual': None,
            'vendor': None,
            'error': 0x9242,
        }
