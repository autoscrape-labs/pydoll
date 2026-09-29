"""WebGL extension interfaces as Chromium exposes them.

The fingerprint builder uses this table to construct the extension objects a
profile declares but the real context lacks, so a page reading
getSupportedExtensions() and getExtension(name) sees the declared
GPU's extensions instead of the host rasterizer's. Names, interface names,
constants (in IDL order), methods with their JavaScript ``length`` (required
parameters only) and the context each extension is registered on were read
from Blink's modules/webgl IDL and .cc files at SOURCE_REVISION; draft extensions gated behind the
WebGLDraftExtensions flag are left out. Methods are kept in IDL order here;
the builder emits them sorted by name, which is the order Chrome installs an
interface's operations in (OES_vertex_array_object exposes bind, create,
delete, is). The registration order lists are what getSupportedExtensions()
follows in Chrome.
"""

from __future__ import annotations

from typing import TypedDict


class WebGLExtensionSpec(TypedDict):
    """One extension interface: Blink name, contexts, constants, methods with their ``length``."""

    interface: str
    contexts: tuple[int, ...]
    constants: dict[str, int]
    methods: list[tuple[str, int]]


SOURCE_REVISION = (
    'chromium/chromium main @ b078053ddcaf24f289a69416377be9875cfbf886 '
    '(mirror raw.githubusercontent.com, fetched 2026-09-27)'
)

WEBGL_EXTENSIONS: dict[str, WebGLExtensionSpec] = {
    'ANGLE_instanced_arrays': {
        'interface': 'ANGLEInstancedArrays',
        'contexts': (1,),
        'constants': {
            'VERTEX_ATTRIB_ARRAY_DIVISOR_ANGLE': 0x88FE,
        },
        'methods': [
            ('drawArraysInstancedANGLE', 4),
            ('drawElementsInstancedANGLE', 5),
            ('vertexAttribDivisorANGLE', 2),
        ],
    },
    'EXT_blend_minmax': {
        'interface': 'EXTBlendMinMax',
        'contexts': (1,),
        'constants': {
            'MIN_EXT': 0x8007,
            'MAX_EXT': 0x8008,
        },
        'methods': [],
    },
    'EXT_clip_control': {
        'interface': 'EXTClipControl',
        'contexts': (1, 2),
        'constants': {
            'LOWER_LEFT_EXT': 0x8CA1,
            'UPPER_LEFT_EXT': 0x8CA2,
            'NEGATIVE_ONE_TO_ONE_EXT': 0x935E,
            'ZERO_TO_ONE_EXT': 0x935F,
            'CLIP_ORIGIN_EXT': 0x935C,
            'CLIP_DEPTH_MODE_EXT': 0x935D,
        },
        'methods': [('clipControlEXT', 2)],
    },
    'EXT_color_buffer_float': {
        'interface': 'EXTColorBufferFloat',
        'contexts': (2,),
        'constants': {},
        'methods': [],
    },
    'EXT_color_buffer_half_float': {
        'interface': 'EXTColorBufferHalfFloat',
        'contexts': (1, 2),
        'constants': {
            'RGBA16F_EXT': 0x881A,
            'RGB16F_EXT': 0x881B,
            'FRAMEBUFFER_ATTACHMENT_COMPONENT_TYPE_EXT': 0x8211,
            'UNSIGNED_NORMALIZED_EXT': 0x8C17,
        },
        'methods': [],
    },
    'EXT_conservative_depth': {
        'interface': 'EXTConservativeDepth',
        'contexts': (2,),
        'constants': {},
        'methods': [],
    },
    'EXT_depth_clamp': {
        'interface': 'EXTDepthClamp',
        'contexts': (1, 2),
        'constants': {
            'DEPTH_CLAMP_EXT': 0x864F,
        },
        'methods': [],
    },
    'EXT_disjoint_timer_query': {
        'interface': 'EXTDisjointTimerQuery',
        'contexts': (1,),
        'constants': {
            'QUERY_COUNTER_BITS_EXT': 0x8864,
            'CURRENT_QUERY_EXT': 0x8865,
            'QUERY_RESULT_EXT': 0x8866,
            'QUERY_RESULT_AVAILABLE_EXT': 0x8867,
            'TIME_ELAPSED_EXT': 0x88BF,
            'TIMESTAMP_EXT': 0x8E28,
            'GPU_DISJOINT_EXT': 0x8FBB,
        },
        'methods': [
            ('createQueryEXT', 0),
            ('deleteQueryEXT', 1),
            ('isQueryEXT', 1),
            ('beginQueryEXT', 2),
            ('endQueryEXT', 1),
            ('queryCounterEXT', 2),
            ('getQueryEXT', 2),
            ('getQueryObjectEXT', 2),
        ],
    },
    'EXT_disjoint_timer_query_webgl2': {
        'interface': 'EXTDisjointTimerQueryWebGL2',
        'contexts': (2,),
        'constants': {
            'QUERY_COUNTER_BITS_EXT': 0x8864,
            'TIME_ELAPSED_EXT': 0x88BF,
            'TIMESTAMP_EXT': 0x8E28,
            'GPU_DISJOINT_EXT': 0x8FBB,
        },
        'methods': [('queryCounterEXT', 2)],
    },
    'EXT_float_blend': {
        'interface': 'EXTFloatBlend',
        'contexts': (1, 2),
        'constants': {},
        'methods': [],
    },
    'EXT_frag_depth': {
        'interface': 'EXTFragDepth',
        'contexts': (1,),
        'constants': {},
        'methods': [],
    },
    'EXT_polygon_offset_clamp': {
        'interface': 'EXTPolygonOffsetClamp',
        'contexts': (1, 2),
        'constants': {
            'POLYGON_OFFSET_CLAMP_EXT': 0x8E1B,
        },
        'methods': [('polygonOffsetClampEXT', 3)],
    },
    'EXT_render_snorm': {
        'interface': 'EXTRenderSnorm',
        'contexts': (2,),
        'constants': {},
        'methods': [],
    },
    'EXT_sRGB': {
        'interface': 'EXTsRGB',
        'contexts': (1,),
        'constants': {
            'SRGB_EXT': 0x8C40,
            'SRGB_ALPHA_EXT': 0x8C42,
            'SRGB8_ALPHA8_EXT': 0x8C43,
            'FRAMEBUFFER_ATTACHMENT_COLOR_ENCODING_EXT': 0x8210,
        },
        'methods': [],
    },
    'EXT_shader_texture_lod': {
        'interface': 'EXTShaderTextureLOD',
        'contexts': (1,),
        'constants': {},
        'methods': [],
    },
    'EXT_texture_compression_bptc': {
        'interface': 'EXTTextureCompressionBPTC',
        'contexts': (1, 2),
        'constants': {
            'COMPRESSED_RGBA_BPTC_UNORM_EXT': 0x8E8C,
            'COMPRESSED_SRGB_ALPHA_BPTC_UNORM_EXT': 0x8E8D,
            'COMPRESSED_RGB_BPTC_SIGNED_FLOAT_EXT': 0x8E8E,
            'COMPRESSED_RGB_BPTC_UNSIGNED_FLOAT_EXT': 0x8E8F,
        },
        'methods': [],
    },
    'EXT_texture_compression_rgtc': {
        'interface': 'EXTTextureCompressionRGTC',
        'contexts': (1, 2),
        'constants': {
            'COMPRESSED_RED_RGTC1_EXT': 0x8DBB,
            'COMPRESSED_SIGNED_RED_RGTC1_EXT': 0x8DBC,
            'COMPRESSED_RED_GREEN_RGTC2_EXT': 0x8DBD,
            'COMPRESSED_SIGNED_RED_GREEN_RGTC2_EXT': 0x8DBE,
        },
        'methods': [],
    },
    'EXT_texture_filter_anisotropic': {
        'interface': 'EXTTextureFilterAnisotropic',
        'contexts': (1, 2),
        'constants': {
            'TEXTURE_MAX_ANISOTROPY_EXT': 0x84FE,
            'MAX_TEXTURE_MAX_ANISOTROPY_EXT': 0x84FF,
        },
        'methods': [],
    },
    'EXT_texture_mirror_clamp_to_edge': {
        'interface': 'EXTTextureMirrorClampToEdge',
        'contexts': (1, 2),
        'constants': {
            'MIRROR_CLAMP_TO_EDGE_EXT': 0x8743,
        },
        'methods': [],
    },
    'EXT_texture_norm16': {
        'interface': 'EXTTextureNorm16',
        'contexts': (2,),
        'constants': {
            'R16_EXT': 0x822A,
            'RG16_EXT': 0x822C,
            'RGB16_EXT': 0x8054,
            'RGBA16_EXT': 0x805B,
            'R16_SNORM_EXT': 0x8F98,
            'RG16_SNORM_EXT': 0x8F99,
            'RGB16_SNORM_EXT': 0x8F9A,
            'RGBA16_SNORM_EXT': 0x8F9B,
        },
        'methods': [],
    },
    'KHR_parallel_shader_compile': {
        'interface': 'KHRParallelShaderCompile',
        'contexts': (1, 2),
        'constants': {
            'COMPLETION_STATUS_KHR': 0x91B1,
        },
        'methods': [],
    },
    'NV_shader_noperspective_interpolation': {
        'interface': 'NVShaderNoperspectiveInterpolation',
        'contexts': (2,),
        'constants': {},
        'methods': [],
    },
    'OES_draw_buffers_indexed': {
        'interface': 'OESDrawBuffersIndexed',
        'contexts': (2,),
        'constants': {},
        'methods': [
            ('enableiOES', 2),
            ('disableiOES', 2),
            ('blendEquationiOES', 2),
            ('blendEquationSeparateiOES', 3),
            ('blendFunciOES', 3),
            ('blendFuncSeparateiOES', 5),
            ('colorMaskiOES', 5),
        ],
    },
    'OES_element_index_uint': {
        'interface': 'OESElementIndexUint',
        'contexts': (1,),
        'constants': {},
        'methods': [],
    },
    'OES_fbo_render_mipmap': {
        'interface': 'OESFboRenderMipmap',
        'contexts': (1,),
        'constants': {},
        'methods': [],
    },
    'OES_sample_variables': {
        'interface': 'OESSampleVariables',
        'contexts': (2,),
        'constants': {},
        'methods': [],
    },
    'OES_shader_multisample_interpolation': {
        'interface': 'OESShaderMultisampleInterpolation',
        'contexts': (2,),
        'constants': {
            'MIN_FRAGMENT_INTERPOLATION_OFFSET_OES': 0x8E5B,
            'MAX_FRAGMENT_INTERPOLATION_OFFSET_OES': 0x8E5C,
            'FRAGMENT_INTERPOLATION_OFFSET_BITS_OES': 0x8E5D,
        },
        'methods': [],
    },
    'OES_standard_derivatives': {
        'interface': 'OESStandardDerivatives',
        'contexts': (1,),
        'constants': {
            'FRAGMENT_SHADER_DERIVATIVE_HINT_OES': 0x8B8B,
        },
        'methods': [],
    },
    'OES_texture_float': {
        'interface': 'OESTextureFloat',
        'contexts': (1,),
        'constants': {},
        'methods': [],
    },
    'OES_texture_float_linear': {
        'interface': 'OESTextureFloatLinear',
        'contexts': (1, 2),
        'constants': {},
        'methods': [],
    },
    'OES_texture_half_float': {
        'interface': 'OESTextureHalfFloat',
        'contexts': (1,),
        'constants': {
            'HALF_FLOAT_OES': 0x8D61,
        },
        'methods': [],
    },
    'OES_texture_half_float_linear': {
        'interface': 'OESTextureHalfFloatLinear',
        'contexts': (1,),
        'constants': {},
        'methods': [],
    },
    'OES_vertex_array_object': {
        'interface': 'OESVertexArrayObject',
        'contexts': (1,),
        'constants': {
            'VERTEX_ARRAY_BINDING_OES': 0x85B5,
        },
        'methods': [
            ('createVertexArrayOES', 0),
            ('deleteVertexArrayOES', 0),
            ('isVertexArrayOES', 0),
            ('bindVertexArrayOES', 0),
        ],
    },
    'OVR_multiview2': {
        'interface': 'OVRMultiview2',
        'contexts': (2,),
        'constants': {
            'FRAMEBUFFER_ATTACHMENT_TEXTURE_NUM_VIEWS_OVR': 0x9630,
            'FRAMEBUFFER_ATTACHMENT_TEXTURE_BASE_VIEW_INDEX_OVR': 0x9632,
            'MAX_VIEWS_OVR': 0x9631,
            'FRAMEBUFFER_INCOMPLETE_VIEW_TARGETS_OVR': 0x9633,
        },
        'methods': [('framebufferTextureMultiviewOVR', 6)],
    },
    'WEBGL_blend_func_extended': {
        'interface': 'WebGLBlendFuncExtended',
        'contexts': (1, 2),
        'constants': {
            'SRC1_COLOR_WEBGL': 0x88F9,
            'SRC1_ALPHA_WEBGL': 0x8589,
            'ONE_MINUS_SRC1_COLOR_WEBGL': 0x88FA,
            'ONE_MINUS_SRC1_ALPHA_WEBGL': 0x88FB,
            'MAX_DUAL_SOURCE_DRAW_BUFFERS_WEBGL': 0x88FC,
        },
        'methods': [],
    },
    'WEBGL_clip_cull_distance': {
        'interface': 'WebGLClipCullDistance',
        'contexts': (2,),
        'constants': {
            'MAX_CLIP_DISTANCES_WEBGL': 0x0D32,
            'MAX_CULL_DISTANCES_WEBGL': 0x82F9,
            'MAX_COMBINED_CLIP_AND_CULL_DISTANCES_WEBGL': 0x82FA,
            'CLIP_DISTANCE0_WEBGL': 0x3000,
            'CLIP_DISTANCE1_WEBGL': 0x3001,
            'CLIP_DISTANCE2_WEBGL': 0x3002,
            'CLIP_DISTANCE3_WEBGL': 0x3003,
            'CLIP_DISTANCE4_WEBGL': 0x3004,
            'CLIP_DISTANCE5_WEBGL': 0x3005,
            'CLIP_DISTANCE6_WEBGL': 0x3006,
            'CLIP_DISTANCE7_WEBGL': 0x3007,
        },
        'methods': [],
    },
    'WEBGL_color_buffer_float': {
        'interface': 'WebGLColorBufferFloat',
        'contexts': (1,),
        'constants': {
            'RGBA32F_EXT': 0x8814,
            'FRAMEBUFFER_ATTACHMENT_COMPONENT_TYPE_EXT': 0x8211,
            'UNSIGNED_NORMALIZED_EXT': 0x8C17,
        },
        'methods': [],
    },
    'WEBGL_compressed_texture_astc': {
        'interface': 'WebGLCompressedTextureASTC',
        'contexts': (1, 2),
        'constants': {
            'COMPRESSED_RGBA_ASTC_4x4_KHR': 0x93B0,
            'COMPRESSED_RGBA_ASTC_5x4_KHR': 0x93B1,
            'COMPRESSED_RGBA_ASTC_5x5_KHR': 0x93B2,
            'COMPRESSED_RGBA_ASTC_6x5_KHR': 0x93B3,
            'COMPRESSED_RGBA_ASTC_6x6_KHR': 0x93B4,
            'COMPRESSED_RGBA_ASTC_8x5_KHR': 0x93B5,
            'COMPRESSED_RGBA_ASTC_8x6_KHR': 0x93B6,
            'COMPRESSED_RGBA_ASTC_8x8_KHR': 0x93B7,
            'COMPRESSED_RGBA_ASTC_10x5_KHR': 0x93B8,
            'COMPRESSED_RGBA_ASTC_10x6_KHR': 0x93B9,
            'COMPRESSED_RGBA_ASTC_10x8_KHR': 0x93BA,
            'COMPRESSED_RGBA_ASTC_10x10_KHR': 0x93BB,
            'COMPRESSED_RGBA_ASTC_12x10_KHR': 0x93BC,
            'COMPRESSED_RGBA_ASTC_12x12_KHR': 0x93BD,
            'COMPRESSED_SRGB8_ALPHA8_ASTC_4x4_KHR': 0x93D0,
            'COMPRESSED_SRGB8_ALPHA8_ASTC_5x4_KHR': 0x93D1,
            'COMPRESSED_SRGB8_ALPHA8_ASTC_5x5_KHR': 0x93D2,
            'COMPRESSED_SRGB8_ALPHA8_ASTC_6x5_KHR': 0x93D3,
            'COMPRESSED_SRGB8_ALPHA8_ASTC_6x6_KHR': 0x93D4,
            'COMPRESSED_SRGB8_ALPHA8_ASTC_8x5_KHR': 0x93D5,
            'COMPRESSED_SRGB8_ALPHA8_ASTC_8x6_KHR': 0x93D6,
            'COMPRESSED_SRGB8_ALPHA8_ASTC_8x8_KHR': 0x93D7,
            'COMPRESSED_SRGB8_ALPHA8_ASTC_10x5_KHR': 0x93D8,
            'COMPRESSED_SRGB8_ALPHA8_ASTC_10x6_KHR': 0x93D9,
            'COMPRESSED_SRGB8_ALPHA8_ASTC_10x8_KHR': 0x93DA,
            'COMPRESSED_SRGB8_ALPHA8_ASTC_10x10_KHR': 0x93DB,
            'COMPRESSED_SRGB8_ALPHA8_ASTC_12x10_KHR': 0x93DC,
            'COMPRESSED_SRGB8_ALPHA8_ASTC_12x12_KHR': 0x93DD,
        },
        'methods': [('getSupportedProfiles', 0)],
    },
    'WEBGL_compressed_texture_etc': {
        'interface': 'WebGLCompressedTextureETC',
        'contexts': (1, 2),
        'constants': {
            'COMPRESSED_R11_EAC': 0x9270,
            'COMPRESSED_SIGNED_R11_EAC': 0x9271,
            'COMPRESSED_RG11_EAC': 0x9272,
            'COMPRESSED_SIGNED_RG11_EAC': 0x9273,
            'COMPRESSED_RGB8_ETC2': 0x9274,
            'COMPRESSED_SRGB8_ETC2': 0x9275,
            'COMPRESSED_RGB8_PUNCHTHROUGH_ALPHA1_ETC2': 0x9276,
            'COMPRESSED_SRGB8_PUNCHTHROUGH_ALPHA1_ETC2': 0x9277,
            'COMPRESSED_RGBA8_ETC2_EAC': 0x9278,
            'COMPRESSED_SRGB8_ALPHA8_ETC2_EAC': 0x9279,
        },
        'methods': [],
    },
    'WEBGL_compressed_texture_etc1': {
        'interface': 'WebGLCompressedTextureETC1',
        'contexts': (1, 2),
        'constants': {
            'COMPRESSED_RGB_ETC1_WEBGL': 0x8D64,
        },
        'methods': [],
    },
    'WEBGL_compressed_texture_pvrtc': {
        'interface': 'WebGLCompressedTexturePVRTC',
        'contexts': (1, 2),
        'constants': {
            'COMPRESSED_RGB_PVRTC_4BPPV1_IMG': 0x8C00,
            'COMPRESSED_RGB_PVRTC_2BPPV1_IMG': 0x8C01,
            'COMPRESSED_RGBA_PVRTC_4BPPV1_IMG': 0x8C02,
            'COMPRESSED_RGBA_PVRTC_2BPPV1_IMG': 0x8C03,
        },
        'methods': [],
    },
    'WEBGL_compressed_texture_s3tc': {
        'interface': 'WebGLCompressedTextureS3TC',
        'contexts': (1, 2),
        'constants': {
            'COMPRESSED_RGB_S3TC_DXT1_EXT': 0x83F0,
            'COMPRESSED_RGBA_S3TC_DXT1_EXT': 0x83F1,
            'COMPRESSED_RGBA_S3TC_DXT3_EXT': 0x83F2,
            'COMPRESSED_RGBA_S3TC_DXT5_EXT': 0x83F3,
        },
        'methods': [],
    },
    'WEBGL_compressed_texture_s3tc_srgb': {
        'interface': 'WebGLCompressedTextureS3TCsRGB',
        'contexts': (1, 2),
        'constants': {
            'COMPRESSED_SRGB_S3TC_DXT1_EXT': 0x8C4C,
            'COMPRESSED_SRGB_ALPHA_S3TC_DXT1_EXT': 0x8C4D,
            'COMPRESSED_SRGB_ALPHA_S3TC_DXT3_EXT': 0x8C4E,
            'COMPRESSED_SRGB_ALPHA_S3TC_DXT5_EXT': 0x8C4F,
        },
        'methods': [],
    },
    'WEBGL_debug_renderer_info': {
        'interface': 'WebGLDebugRendererInfo',
        'contexts': (1, 2),
        'constants': {
            'UNMASKED_VENDOR_WEBGL': 0x9245,
            'UNMASKED_RENDERER_WEBGL': 0x9246,
        },
        'methods': [],
    },
    'WEBGL_debug_shaders': {
        'interface': 'WebGLDebugShaders',
        'contexts': (1, 2),
        'constants': {},
        'methods': [('getTranslatedShaderSource', 1)],
    },
    'WEBGL_depth_texture': {
        'interface': 'WebGLDepthTexture',
        'contexts': (1,),
        'constants': {
            'UNSIGNED_INT_24_8_WEBGL': 0x84FA,
        },
        'methods': [],
    },
    'WEBGL_draw_buffers': {
        'interface': 'WebGLDrawBuffers',
        'contexts': (1,),
        'constants': {
            'COLOR_ATTACHMENT0_WEBGL': 0x8CE0,
            'COLOR_ATTACHMENT1_WEBGL': 0x8CE1,
            'COLOR_ATTACHMENT2_WEBGL': 0x8CE2,
            'COLOR_ATTACHMENT3_WEBGL': 0x8CE3,
            'COLOR_ATTACHMENT4_WEBGL': 0x8CE4,
            'COLOR_ATTACHMENT5_WEBGL': 0x8CE5,
            'COLOR_ATTACHMENT6_WEBGL': 0x8CE6,
            'COLOR_ATTACHMENT7_WEBGL': 0x8CE7,
            'COLOR_ATTACHMENT8_WEBGL': 0x8CE8,
            'COLOR_ATTACHMENT9_WEBGL': 0x8CE9,
            'COLOR_ATTACHMENT10_WEBGL': 0x8CEA,
            'COLOR_ATTACHMENT11_WEBGL': 0x8CEB,
            'COLOR_ATTACHMENT12_WEBGL': 0x8CEC,
            'COLOR_ATTACHMENT13_WEBGL': 0x8CED,
            'COLOR_ATTACHMENT14_WEBGL': 0x8CEE,
            'COLOR_ATTACHMENT15_WEBGL': 0x8CEF,
            'DRAW_BUFFER0_WEBGL': 0x8825,
            'DRAW_BUFFER1_WEBGL': 0x8826,
            'DRAW_BUFFER2_WEBGL': 0x8827,
            'DRAW_BUFFER3_WEBGL': 0x8828,
            'DRAW_BUFFER4_WEBGL': 0x8829,
            'DRAW_BUFFER5_WEBGL': 0x882A,
            'DRAW_BUFFER6_WEBGL': 0x882B,
            'DRAW_BUFFER7_WEBGL': 0x882C,
            'DRAW_BUFFER8_WEBGL': 0x882D,
            'DRAW_BUFFER9_WEBGL': 0x882E,
            'DRAW_BUFFER10_WEBGL': 0x882F,
            'DRAW_BUFFER11_WEBGL': 0x8830,
            'DRAW_BUFFER12_WEBGL': 0x8831,
            'DRAW_BUFFER13_WEBGL': 0x8832,
            'DRAW_BUFFER14_WEBGL': 0x8833,
            'DRAW_BUFFER15_WEBGL': 0x8834,
            'MAX_COLOR_ATTACHMENTS_WEBGL': 0x8CDF,
            'MAX_DRAW_BUFFERS_WEBGL': 0x8824,
        },
        'methods': [('drawBuffersWEBGL', 1)],
    },
    'WEBGL_lose_context': {
        'interface': 'WebGLLoseContext',
        'contexts': (1, 2),
        'constants': {},
        'methods': [('loseContext', 0), ('restoreContext', 0)],
    },
    'WEBGL_multi_draw': {
        'interface': 'WebGLMultiDraw',
        'contexts': (1, 2),
        'constants': {},
        'methods': [
            ('multiDrawArraysWEBGL', 6),
            ('multiDrawElementsWEBGL', 7),
            ('multiDrawArraysInstancedWEBGL', 8),
            ('multiDrawElementsInstancedWEBGL', 9),
        ],
    },
    'WEBGL_polygon_mode': {
        'interface': 'WebGLPolygonMode',
        'contexts': (1, 2),
        'constants': {
            'POLYGON_MODE_WEBGL': 0x0B40,
            'POLYGON_OFFSET_LINE_WEBGL': 0x2A02,
            'LINE_WEBGL': 0x1B01,
            'FILL_WEBGL': 0x1B02,
        },
        'methods': [('polygonModeWEBGL', 2)],
    },
    'WEBGL_provoking_vertex': {
        'interface': 'WebGLProvokingVertex',
        'contexts': (2,),
        'constants': {
            'FIRST_VERTEX_CONVENTION_WEBGL': 0x8E4D,
            'LAST_VERTEX_CONVENTION_WEBGL': 0x8E4E,
            'PROVOKING_VERTEX_WEBGL': 0x8E4F,
        },
        'methods': [('provokingVertexWEBGL', 1)],
    },
    'WEBGL_render_shared_exponent': {
        'interface': 'WebGLRenderSharedExponent',
        'contexts': (2,),
        'constants': {},
        'methods': [],
    },
    'WEBGL_stencil_texturing': {
        'interface': 'WebGLStencilTexturing',
        'contexts': (2,),
        'constants': {
            'DEPTH_STENCIL_TEXTURE_MODE_WEBGL': 0x90EA,
            'STENCIL_INDEX_WEBGL': 0x1901,
        },
        'methods': [],
    },
}

WEBGL1_ORDER: list[str] = [
    'ANGLE_instanced_arrays',
    'EXT_blend_minmax',
    'EXT_clip_control',
    'EXT_color_buffer_half_float',
    'EXT_depth_clamp',
    'EXT_disjoint_timer_query',
    'EXT_float_blend',
    'EXT_frag_depth',
    'EXT_polygon_offset_clamp',
    'EXT_shader_texture_lod',
    'EXT_texture_compression_bptc',
    'EXT_texture_compression_rgtc',
    'EXT_texture_filter_anisotropic',
    'EXT_texture_mirror_clamp_to_edge',
    'EXT_sRGB',
    'KHR_parallel_shader_compile',
    'OES_element_index_uint',
    'OES_fbo_render_mipmap',
    'OES_standard_derivatives',
    'OES_texture_float',
    'OES_texture_float_linear',
    'OES_texture_half_float',
    'OES_texture_half_float_linear',
    'OES_vertex_array_object',
    'WEBGL_blend_func_extended',
    'WEBGL_color_buffer_float',
    'WEBGL_compressed_texture_astc',
    'WEBGL_compressed_texture_etc',
    'WEBGL_compressed_texture_etc1',
    'WEBGL_compressed_texture_pvrtc',
    'WEBGL_compressed_texture_s3tc',
    'WEBGL_compressed_texture_s3tc_srgb',
    'WEBGL_debug_renderer_info',
    'WEBGL_debug_shaders',
    'WEBGL_depth_texture',
    'WEBGL_draw_buffers',
    'WEBGL_lose_context',
    'WEBGL_multi_draw',
    'WEBGL_polygon_mode',
]

WEBGL2_ORDER: list[str] = [
    'EXT_clip_control',
    'EXT_color_buffer_float',
    'EXT_color_buffer_half_float',
    'EXT_conservative_depth',
    'EXT_depth_clamp',
    'EXT_disjoint_timer_query_webgl2',
    'EXT_float_blend',
    'EXT_polygon_offset_clamp',
    'EXT_render_snorm',
    'EXT_texture_compression_bptc',
    'EXT_texture_compression_rgtc',
    'EXT_texture_filter_anisotropic',
    'EXT_texture_mirror_clamp_to_edge',
    'EXT_texture_norm16',
    'KHR_parallel_shader_compile',
    'NV_shader_noperspective_interpolation',
    'OES_draw_buffers_indexed',
    'OES_sample_variables',
    'OES_shader_multisample_interpolation',
    'OES_texture_float_linear',
    'OVR_multiview2',
    'WEBGL_blend_func_extended',
    'WEBGL_clip_cull_distance',
    'WEBGL_compressed_texture_astc',
    'WEBGL_compressed_texture_etc',
    'WEBGL_compressed_texture_etc1',
    'WEBGL_compressed_texture_pvrtc',
    'WEBGL_compressed_texture_s3tc',
    'WEBGL_compressed_texture_s3tc_srgb',
    'WEBGL_debug_renderer_info',
    'WEBGL_debug_shaders',
    'WEBGL_lose_context',
    'WEBGL_multi_draw',
    'WEBGL_polygon_mode',
    'WEBGL_provoking_vertex',
    'WEBGL_render_shared_exponent',
    'WEBGL_stencil_texturing',
]


EXTENSION_METHOD_RETURNS: dict[str, object] = {
    'createVertexArrayOES': None,
    'isVertexArrayOES': False,
    'createQueryEXT': None,
    'isQueryEXT': False,
    'getQueryEXT': None,
    'getQueryObjectEXT': None,
    'getSupportedProfiles': [],
    'getTranslatedShaderSource': '',
}
"""What a method of a constructed extension object returns; anything else returns undefined."""

EXTENSION_PARAMETER_DEFAULTS: dict[str, dict[int, object]] = {
    'EXT_texture_filter_anisotropic': {0x84FF: 16},
    'OES_standard_derivatives': {0x8B8B: 0x1100},
    'OES_vertex_array_object': {0x85B5: None},
    'WEBGL_draw_buffers': {0x8CDF: 8, 0x8824: 8, **{0x8825 + i: 0x0405 for i in range(8)}},
    'EXT_disjoint_timer_query': {0x8E28: 0, 0x8FBB: False},
    'EXT_disjoint_timer_query_webgl2': {0x8E28: 0, 0x8FBB: False},
    'OVR_multiview2': {0x9631: 4},
    'WEBGL_clip_cull_distance': {0x0D32: 8, 0x82F9: 8, 0x82FA: 16},
    'WEBGL_blend_func_extended': {0x88FC: 1},
    'WEBGL_polygon_mode': {0x0B40: 0x1B02, 0x2A02: False},
    'EXT_clip_control': {0x935C: 0x8CA1, 0x935D: 0x935E},
    'EXT_depth_clamp': {0x864F: False},
    'EXT_polygon_offset_clamp': {0x8E1B: 0},
    'WEBGL_provoking_vertex': {0x8E4F: 0x8E4E},
}
"""getParameter answers an extension unlocks once enabled, keyed by pname.

Measured on Chrome 152 (ANGLE on SwiftShader and Metal, 2026-09-27): sixteen
levels of anisotropy, DONT_CARE derivative hint, no bound vertex array,
eight draw buffers all pointing at BACK, timer queries reporting a zero
timestamp and no disjoint event, four multiview views, eight clip and cull
distances, one dual-source draw buffer, fill polygon mode with offset line
off, lower-left clip origin with negative-one-to-one depth, depth clamp off and
a zero offset clamp. The provoking vertex is the LAST_VERTEX_CONVENTION
initial value the extension specification gives. Before the extension is
enabled the real context answers, which is INVALID_ENUM like real Chrome.
"""
