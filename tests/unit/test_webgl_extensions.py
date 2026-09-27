"""The Chromium WebGL extension registry the fingerprint builder constructs extensions from."""

from __future__ import annotations

import re

from pydoll.utils.fingerprint_builder import _COMPRESSED_TEXTURE_FORMATS
from pydoll.utils.webgl_extensions import (
    EXTENSION_METHOD_RETURNS,
    EXTENSION_PARAMETER_DEFAULTS,
    WEBGL1_ORDER,
    WEBGL2_ORDER,
    WEBGL_EXTENSIONS,
)

MAX_GL_ENUM = 0xFFFF
WEBGL2 = 2


def test_every_extension_is_registered_on_at_least_one_context_and_the_orders_agree():
    assert set(WEBGL1_ORDER) | set(WEBGL2_ORDER) == set(WEBGL_EXTENSIONS)
    for name, spec in WEBGL_EXTENSIONS.items():
        assert set(spec['contexts']) <= {1, 2}
        assert (name in WEBGL1_ORDER) == (1 in spec['contexts'])
        assert (name in WEBGL2_ORDER) == (WEBGL2 in spec['contexts'])
    assert len(WEBGL1_ORDER) == len(set(WEBGL1_ORDER))
    assert len(WEBGL2_ORDER) == len(set(WEBGL2_ORDER))


def test_specs_have_blink_interface_names_gl_enums_and_method_lengths():
    for name, spec in WEBGL_EXTENSIONS.items():
        assert re.fullmatch(r'[A-Z][A-Za-z0-9]+', spec['interface']), name
        for constant, value in spec['constants'].items():
            assert re.fullmatch(r'[A-Z0-9_x]+', constant), (name, constant)
            assert isinstance(value, int), (name, constant)
            assert 0 <= value <= MAX_GL_ENUM, (name, constant)
        for method, length in spec['methods']:
            assert re.fullmatch(r'[a-z][A-Za-z0-9]+', method), (name, method)
            assert isinstance(length, int), (name, method)
            assert length >= 0, (name, method)


def test_registration_order_is_chromes_not_a_plain_sort():
    """Chrome registers alphabetically by C++ class name, so ``EXT_sRGB`` (EXTsRGB)
    follows ``EXT_texture_mirror_clamp_to_edge`` instead of sorting before ``EXT_shader``."""
    assert WEBGL1_ORDER.index('EXT_sRGB') > WEBGL1_ORDER.index('EXT_texture_mirror_clamp_to_edge')
    assert WEBGL1_ORDER.index('EXT_sRGB') < WEBGL1_ORDER.index('KHR_parallel_shader_compile')
    assert WEBGL1_ORDER != sorted(WEBGL1_ORDER)


def test_webgl1_only_and_webgl2_only_extensions_are_kept_apart():
    assert WEBGL_EXTENSIONS['OES_vertex_array_object']['contexts'] == (1,)
    assert WEBGL_EXTENSIONS['WEBGL_draw_buffers']['contexts'] == (1,)
    assert WEBGL_EXTENSIONS['OVR_multiview2']['contexts'] == (2,)
    assert WEBGL_EXTENSIONS['EXT_disjoint_timer_query_webgl2']['contexts'] == (2,)
    assert WEBGL_EXTENSIONS['KHR_parallel_shader_compile']['contexts'] == (1, 2)


def test_defaults_and_method_returns_refer_to_registered_names():
    methods = {method for spec in WEBGL_EXTENSIONS.values() for method, _ in spec['methods']}
    assert set(EXTENSION_METHOD_RETURNS) <= methods
    for name, params in EXTENSION_PARAMETER_DEFAULTS.items():
        constants = set(WEBGL_EXTENSIONS[name]['constants'].values())
        for pname in params:
            assert pname in constants, (name, hex(pname))


def test_compressed_format_tables_name_registered_extensions():
    for name in _COMPRESSED_TEXTURE_FORMATS:
        assert name.replace('WEBKIT_', '') in WEBGL_EXTENSIONS, name


def test_a_constructed_extension_matches_what_chrome_exposes():
    """Shape read from a real Chrome 152 ``ANGLE_instanced_arrays`` object."""
    spec = WEBGL_EXTENSIONS['ANGLE_instanced_arrays']
    assert spec['interface'] == 'ANGLEInstancedArrays'
    assert spec['constants'] == {'VERTEX_ATTRIB_ARRAY_DIVISOR_ANGLE': 0x88FE}
    assert spec['methods'] == [
        ('drawArraysInstancedANGLE', 4),
        ('drawElementsInstancedANGLE', 5),
        ('vertexAttribDivisorANGLE', 2),
    ]
    assert WEBGL_EXTENSIONS['WEBGL_blend_func_extended']['methods'] == []


def test_the_registry_keeps_idl_order_and_sorting_gives_chromes_method_order():
    """Chrome 152 exposes ``OES_vertex_array_object`` as bind, create, delete, is:
    operations are installed by name, not in IDL order, so the builder sorts."""
    methods = WEBGL_EXTENSIONS['OES_vertex_array_object']['methods']
    assert methods == [
        ('createVertexArrayOES', 0),
        ('deleteVertexArrayOES', 0),
        ('isVertexArrayOES', 0),
        ('bindVertexArrayOES', 0),
    ]
    assert [name for name, _ in sorted(methods)] == [
        'bindVertexArrayOES',
        'createVertexArrayOES',
        'deleteVertexArrayOES',
        'isVertexArrayOES',
    ]
