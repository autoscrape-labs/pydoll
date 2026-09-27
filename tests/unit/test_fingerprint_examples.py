"""The shipped example profiles must obey the relations a real GPU obeys.

A detector recomputes these from one context, so a profile that overrides part
of a family and lets the rest fall back to the host GPU is caught by
arithmetic alone, with no reference table needed.
"""

import pytest

from examples.fingerprints import FINGERPRINTS
from pydoll.protocol.fingerprint.types import WebGLProfile, WebGPUProfile

COMPONENTS_PER_VECTOR = 4

VECTOR_FAMILIES = (
    ('max_vertex_uniform_vectors', 'max_vertex_uniform_components'),
    ('max_fragment_uniform_vectors', 'max_fragment_uniform_components'),
    ('max_varying_vectors', 'max_varying_components'),
)

COMBINED_FAMILIES = (
    (
        'max_combined_vertex_uniform_components',
        'max_vertex_uniform_components',
        'max_vertex_uniform_blocks',
    ),
    (
        'max_combined_fragment_uniform_components',
        'max_fragment_uniform_components',
        'max_fragment_uniform_blocks',
    ),
)

STAGE_LIMITS = (
    ('maxStorageBuffersInVertexStage', 'maxStorageBuffersPerShaderStage'),
    ('maxStorageBuffersInFragmentStage', 'maxStorageBuffersPerShaderStage'),
    ('maxStorageTexturesInVertexStage', 'maxStorageTexturesPerShaderStage'),
    ('maxStorageTexturesInFragmentStage', 'maxStorageTexturesPerShaderStage'),
)

PROFILE_NAMES = sorted(FINGERPRINTS)


def webgl_profile(name: str) -> WebGLProfile:
    return FINGERPRINTS[name].get('webgl') or WebGLProfile(vendor='', renderer='')


def webgpu_profile(name: str) -> WebGPUProfile:
    return FINGERPRINTS[name].get('webgpu') or WebGPUProfile(vendor='')


@pytest.mark.parametrize('name', PROFILE_NAMES)
def test_components_are_four_times_the_vectors(name: str) -> None:
    webgl = webgl_profile(name)
    for vectors, components in VECTOR_FAMILIES:
        if vectors not in webgl and components not in webgl:
            continue
        assert vectors in webgl, f'{name} sets {components} without {vectors}'
        assert components in webgl, f'{name} sets {vectors} without {components}'
        assert webgl[components] == COMPONENTS_PER_VECTOR * webgl[vectors], components


@pytest.mark.parametrize('name', PROFILE_NAMES)
def test_combined_components_follow_the_block_budget(name: str) -> None:
    webgl = webgl_profile(name)
    block_size = webgl.get('max_uniform_block_size')
    for combined, components, blocks in COMBINED_FAMILIES:
        if combined not in webgl:
            continue
        assert components in webgl, f'{name} sets {combined} without {components}'
        assert block_size is not None, f'{name} sets {combined} without max_uniform_block_size'
        assert components in webgl and blocks in webgl, f'{name} sets {combined} alone'
        expected = webgl[components] + webgl[blocks] * block_size // COMPONENTS_PER_VECTOR
        assert webgl[combined] == expected, combined


@pytest.mark.parametrize('name', PROFILE_NAMES)
def test_combined_limits_cover_their_per_stage_limits(name: str) -> None:
    webgl = webgl_profile(name)
    vertex = webgl.get('max_vertex_uniform_blocks')
    fragment = webgl.get('max_fragment_uniform_blocks')
    combined = webgl.get('max_combined_uniform_blocks')
    bindings = webgl.get('max_uniform_buffer_bindings')
    if combined is not None and vertex is not None and fragment is not None:
        assert vertex <= combined <= vertex + fragment
    if bindings is not None and combined is not None:
        assert bindings >= combined

    units = webgl.get('max_combined_texture_image_units')
    per_stage = (
        webgl.get('max_texture_image_units'),
        webgl.get('max_vertex_texture_image_units'),
    )
    if units is not None and None not in per_stage:
        assert max(per_stage) <= units <= sum(per_stage)  # type: ignore[type-var]


@pytest.mark.parametrize('name', PROFILE_NAMES)
def test_webgpu_per_stage_limits_reach_the_shared_maximum(name: str) -> None:
    limits = webgpu_profile(name).get('limits') or {}
    for stage, shared in STAGE_LIMITS:
        if stage in limits and shared in limits:
            assert limits[stage] >= limits[shared], stage
