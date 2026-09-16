"""Example fingerprint profiles for pydoll's ``Tab.apply_fingerprint()``.

Three self-contained, internally consistent profiles: one Android (mobile), one
Windows desktop and one macOS desktop. Each aligns User-Agent / navigator /
Client Hints / WebGL / screen / fonts / locale so the browser tells one coherent
story.

Two rules keep a profile undetectable:

1. The Chrome MAJOR in the User-Agent must match the real Chrome binary you
   drive. The network-layer fingerprint (TLS JA3/JA4, HTTP/2 SETTINGS) comes from
   the actual browser and is NOT spoofable, so a UA claiming a different major
   than the binary is itself an inconsistency. Bump ``CHROME_*`` when you upgrade
   Chrome (these target Chrome 152).

2. The locale/timezone/geolocation must match the geography of your egress IP (or
   proxy). The ``Accept-Language`` header (built from ``locale``) is sent on every
   request and cross-referenced against the IP's country by anti-abuse systems
   (e.g. Google) — a US-English browser on a Brazilian IP gets blocked. The
   Windows and macOS profiles here are a US identity (pair them with a US proxy);
   the Android profile is a Brazilian identity.

UA reduction: ``navigator.userAgent`` only exposes ``Chrome/MAJOR.0.0.0``; the
full build (e.g. ``145.0.7632.75``) lives only in ``Sec-CH-UA-Full-Version-List``.
The full build is kept in the UA constants here as the source of truth and is
reduced automatically for ``navigator.userAgent``.
"""

from pydoll.protocol.fingerprint.types import (
    AudioFingerprint,
    ClientHintsFingerprint,
    FingerprintConfig,
    FontFingerprint,
    GeolocationFingerprint,
    HardwareFingerprint,
    LocaleFingerprint,
    MediaCodecsFingerprint,
    MediaDevicesFingerprint,
    MediaFeaturesFingerprint,
    NavigatorFingerprint,
    NetworkConnectionFingerprint,
    PermissionsFingerprint,
    PlatformApisFingerprint,
    ScreenFingerprint,
    SpeechFingerprint,
    SpeechVoice,
    WebGLProfile,
    WebGPUProfile,
)

CHROME_MOBILE = '145.0.7632.45'
CHROME_DESKTOP = '152.0.7977.83'

UA_ANDROID = (
    'Mozilla/5.0 (Linux; Android 10; K) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    f'Chrome/{CHROME_MOBILE} Mobile Safari/537.36'
)
UA_WINDOWS = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    f'Chrome/{CHROME_DESKTOP} Safari/537.36'
)
UA_MAC = (
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    f'Chrome/{CHROME_DESKTOP} Safari/537.36'
)

APP_ANDROID = UA_ANDROID[len('Mozilla/') :]
APP_WINDOWS = UA_WINDOWS[len('Mozilla/') :]
APP_MAC = UA_MAC[len('Mozilla/') :]

US_LOCALE = LocaleFingerprint(languages=['en-US', 'en'])
BR_LOCALE = LocaleFingerprint(languages=['pt-BR', 'pt', 'en-US', 'en'])

NEW_YORK_GEO = GeolocationFingerprint(latitude=40.7128, longitude=-74.0060, accuracy=100.0)
SAO_PAULO_GEO = GeolocationFingerprint(latitude=-23.5505, longitude=-46.6333, accuracy=100.0)


DESKTOP_EXTENSIONS = [
    'ANGLE_instanced_arrays',
    'EXT_blend_minmax',
    'EXT_clip_control',
    'EXT_color_buffer_half_float',
    'EXT_depth_clamp',
    'EXT_disjoint_timer_query',
    'EXT_float_blend',
    'EXT_frag_depth',
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
    'WEBGL_color_buffer_float',
    'WEBGL_compressed_texture_s3tc',
    'WEBGL_compressed_texture_s3tc_srgb',
    'WEBGL_debug_renderer_info',
    # 99.71% of Windows machines expose this one (web3dsurvey), so a Windows
    # profile that hides it stands out. It is only safe on a host whose real
    # backend matches the claim: getTranslatedShaderSource returns the compiled
    # source, and HLSL against Metal gives the host away. Drop it from this list
    # when running a Windows profile on a Mac or a Linux box.
    'WEBGL_debug_shaders',
    'WEBGL_depth_texture',
    'WEBGL_draw_buffers',
    'WEBGL_lose_context',
    'WEBGL_multi_draw',
    'WEBGL_polygon_mode',
]

MOBILE_EXTENSIONS = [
    'ANGLE_instanced_arrays',
    'EXT_blend_minmax',
    'EXT_color_buffer_half_float',
    'EXT_float_blend',
    'EXT_frag_depth',
    'EXT_shader_texture_lod',
    'EXT_texture_filter_anisotropic',
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
    'WEBGL_color_buffer_float',
    'WEBGL_compressed_texture_astc',
    'WEBGL_compressed_texture_etc',
    'WEBGL_compressed_texture_etc1',
    'WEBGL_debug_renderer_info',
    'WEBGL_depth_texture',
    'WEBGL_draw_buffers',
    'WEBGL_lose_context',
    'WEBGL_multi_draw',
]

DESKTOP_WEBGL2_EXTENSIONS = [
    'EXT_clip_control',
    'EXT_color_buffer_float',
    'EXT_color_buffer_half_float',
    'EXT_conservative_depth',
    'EXT_depth_clamp',
    'EXT_float_blend',
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
    'WEBGL_clip_cull_distance',
    'WEBGL_compressed_texture_s3tc',
    'WEBGL_compressed_texture_s3tc_srgb',
    'WEBGL_debug_renderer_info',
    'WEBGL_debug_shaders',
    'WEBGL_lose_context',
    'WEBGL_multi_draw',
    'WEBGL_polygon_mode',
    'WEBGL_provoking_vertex',
    'WEBGL_stencil_texturing',
]

MOBILE_WEBGL2_EXTENSIONS = [
    'EXT_color_buffer_float',
    'EXT_color_buffer_half_float',
    'EXT_float_blend',
    'EXT_texture_filter_anisotropic',
    'EXT_texture_norm16',
    'KHR_parallel_shader_compile',
    'OES_draw_buffers_indexed',
    'OES_texture_float_linear',
    'WEBGL_compressed_texture_astc',
    'WEBGL_compressed_texture_etc',
    'WEBGL_debug_renderer_info',
    'WEBGL_lose_context',
    'WEBGL_multi_draw',
]

# ANGLE on Direct3D 11 has no reduced precision: every float precision reports
# the full 32-bit range and every int precision the full 32-bit int range.
SHADER_PRECISION_D3D11 = {
    'vertex': {
        'highFloat': [127, 127, 23],
        'mediumFloat': [127, 127, 23],
        'lowFloat': [127, 127, 23],
        'highInt': [31, 30, 0],
        'mediumInt': [31, 30, 0],
        'lowInt': [31, 30, 0],
    },
    'fragment': {
        'highFloat': [127, 127, 23],
        'mediumFloat': [127, 127, 23],
        'lowFloat': [127, 127, 23],
        'highInt': [31, 30, 0],
        'mediumInt': [31, 30, 0],
        'lowInt': [31, 30, 0],
    },
}

SHADER_PRECISION_DEFAULT = {
    'vertex': {
        'highFloat': [127, 127, 23],
        'mediumFloat': [15, 15, 10],
        'lowFloat': [15, 15, 10],
        'highInt': [31, 30, 0],
        'mediumInt': [15, 14, 0],
        'lowInt': [15, 14, 0],
    },
    'fragment': {
        'highFloat': [127, 127, 23],
        'mediumFloat': [15, 15, 10],
        'lowFloat': [15, 15, 10],
        'highInt': [31, 30, 0],
        'mediumInt': [15, 14, 0],
        'lowInt': [15, 14, 0],
    },
}

# Captured from Chrome 152 on an Apple M4 (macOS, Metal backend). Chrome blanks
# ``device`` and ``description``; the limits and the feature set are the whole
# adapter as ``requestAdapter()`` reports it.
WEBGPU_APPLE_M_SERIES = WebGPUProfile(
    vendor='apple',
    architecture='metal-3',
    device='',
    description='',
    limits={
        'maxTextureDimension1D': 16384,
        'maxTextureDimension2D': 16384,
        'maxTextureDimension3D': 2048,
        'maxTextureArrayLayers': 2048,
        'maxBindGroups': 4,
        'maxBindGroupsPlusVertexBuffers': 24,
        'maxBindingsPerBindGroup': 1000,
        'maxDynamicUniformBuffersPerPipelineLayout': 10,
        'maxDynamicStorageBuffersPerPipelineLayout': 8,
        'maxSampledTexturesPerShaderStage': 48,
        'maxSamplersPerShaderStage': 16,
        'maxStorageBuffersPerShaderStage': 10,
        'maxStorageTexturesPerShaderStage': 8,
        'maxUniformBuffersPerShaderStage': 12,
        'maxUniformBufferBindingSize': 65536,
        'maxStorageBufferBindingSize': 4294967292,
        'minUniformBufferOffsetAlignment': 256,
        'minStorageBufferOffsetAlignment': 256,
        'maxVertexBuffers': 8,
        'maxBufferSize': 4294967292,
        'maxVertexAttributes': 30,
        'maxVertexBufferArrayStride': 2048,
        'maxInterStageShaderVariables': 28,
        'maxColorAttachments': 8,
        'maxColorAttachmentBytesPerSample': 128,
        'maxComputeWorkgroupStorageSize': 32768,
        'maxComputeInvocationsPerWorkgroup': 1024,
        'maxComputeWorkgroupSizeX': 1024,
        'maxComputeWorkgroupSizeY': 1024,
        'maxComputeWorkgroupSizeZ': 64,
        'maxComputeWorkgroupsPerDimension': 65535,
        'maxImmediateSize': 64,
        'maxStorageBuffersInFragmentStage': 10,
        'maxStorageTexturesInFragmentStage': 8,
        'maxStorageBuffersInVertexStage': 10,
        'maxStorageTexturesInVertexStage': 8,
    },
    features=[
        'depth32float-stencil8',
        'rg11b10ufloat-renderable',
        'bgra8unorm-storage',
        'texture-formats-tier1',
        'texture-compression-bc',
        'dual-source-blending',
        'core-features-and-limits',
        'float32-filterable',
        'indirect-first-instance',
        'texture-compression-astc-sliced-3d',
        'float32-blendable',
        'subgroup-size-control',
        'texture-compression-astc',
        'texture-compression-etc2',
        'depth-clip-control',
        'texture-compression-bc-sliced-3d',
        'clip-distances',
        'texture-formats-tier2',
        'shader-f16',
        'timestamp-query',
        'primitive-index',
        'texture-component-swizzle',
        'subgroups',
    ],
)

# NVIDIA GeForce RTX 3060 on Windows, Chrome D3D12 backend. ``vendor`` and
# ``architecture`` come from a real Chrome 150 capture of an RTX 3060; the
# limits are the webgpu.report aggregate for NVIDIA + Windows + Chrome (42
# adapters, every limit identical across them, including the per-stage storage
# buffer limits at 16) and match Dawn's D3D12 tier tables; the features are the
# ones at 100% in that aggregate (Ampere has shader-f16), plus
# subgroup-size-control which Dawn enables on any current NVIDIA driver.
WEBGPU_NVIDIA_AMPERE_D3D12 = WebGPUProfile(
    vendor='nvidia',
    architecture='ampere',
    device='',
    description='',
    limits={
        'maxTextureDimension1D': 16384,
        'maxTextureDimension2D': 16384,
        'maxTextureDimension3D': 2048,
        'maxTextureArrayLayers': 2048,
        'maxBindGroups': 4,
        'maxBindGroupsPlusVertexBuffers': 24,
        'maxBindingsPerBindGroup': 1000,
        'maxDynamicUniformBuffersPerPipelineLayout': 10,
        'maxDynamicStorageBuffersPerPipelineLayout': 8,
        'maxSampledTexturesPerShaderStage': 48,
        'maxSamplersPerShaderStage': 16,
        'maxStorageBuffersPerShaderStage': 16,
        'maxStorageTexturesPerShaderStage': 8,
        'maxUniformBuffersPerShaderStage': 12,
        'maxUniformBufferBindingSize': 65536,
        'maxStorageBufferBindingSize': 2147483644,
        'minUniformBufferOffsetAlignment': 256,
        'minStorageBufferOffsetAlignment': 256,
        'maxVertexBuffers': 8,
        'maxBufferSize': 2147483648,
        'maxVertexAttributes': 30,
        'maxVertexBufferArrayStride': 2048,
        'maxInterStageShaderVariables': 28,
        'maxColorAttachments': 8,
        'maxColorAttachmentBytesPerSample': 128,
        'maxComputeWorkgroupStorageSize': 32768,
        'maxComputeInvocationsPerWorkgroup': 1024,
        'maxComputeWorkgroupSizeX': 1024,
        'maxComputeWorkgroupSizeY': 1024,
        'maxComputeWorkgroupSizeZ': 64,
        'maxComputeWorkgroupsPerDimension': 65535,
        'maxStorageBuffersInVertexStage': 16,
        'maxStorageBuffersInFragmentStage': 16,
    },
    features=[
        'core-features-and-limits',
        'depth-clip-control',
        'depth32float-stencil8',
        'texture-compression-bc',
        'texture-compression-bc-sliced-3d',
        'timestamp-query',
        'indirect-first-instance',
        'shader-f16',
        'rg11b10ufloat-renderable',
        'bgra8unorm-storage',
        'float32-filterable',
        'float32-blendable',
        'clip-distances',
        'dual-source-blending',
        'subgroups',
        'texture-component-swizzle',
        'texture-formats-tier1',
        'texture-formats-tier2',
        'primitive-index',
        'subgroup-size-control',
    ],
)

# Qualcomm Adreno 750 (Galaxy S24 Ultra) on Android, Chrome Vulkan backend.
# ``vendor`` / ``architecture`` come from a real Chrome 150 capture of an
# Adreno 740 (same ``adreno-7xx`` bucket in Dawn's gpu_info); the limits are
# derived from the Galaxy S24 Ultra Vulkan capability reports through Dawn's
# Vulkan mapping and Chrome's limit tiers, and agree with the webgpu.report
# Qualcomm + Android aggregate on every discriminating value (128 MiB storage
# binding, 16 inter-stage variables, 2 GiB maxBufferSize). The per-stage
# storage buffer limits repeat maxStorageBuffersPerShaderStage, which is how
# Dawn reports them on every adapter webgpu.report has measured.
WEBGPU_ADRENO_750_VULKAN = WebGPUProfile(
    vendor='qualcomm',
    architecture='adreno-7xx',
    device='',
    description='',
    limits={
        'maxTextureDimension1D': 16384,
        'maxTextureDimension2D': 16384,
        'maxTextureDimension3D': 2048,
        'maxTextureArrayLayers': 2048,
        'maxBindGroups': 4,
        'maxBindGroupsPlusVertexBuffers': 24,
        'maxBindingsPerBindGroup': 1000,
        'maxDynamicUniformBuffersPerPipelineLayout': 10,
        'maxDynamicStorageBuffersPerPipelineLayout': 8,
        'maxSampledTexturesPerShaderStage': 48,
        'maxSamplersPerShaderStage': 16,
        'maxStorageBuffersPerShaderStage': 16,
        'maxStorageTexturesPerShaderStage': 8,
        'maxUniformBuffersPerShaderStage': 12,
        'maxUniformBufferBindingSize': 65536,
        'maxStorageBufferBindingSize': 134217728,
        'minUniformBufferOffsetAlignment': 256,
        'minStorageBufferOffsetAlignment': 256,
        'maxVertexBuffers': 8,
        'maxBufferSize': 2147483648,
        'maxVertexAttributes': 30,
        'maxVertexBufferArrayStride': 2048,
        'maxInterStageShaderVariables': 16,
        'maxColorAttachments': 8,
        'maxColorAttachmentBytesPerSample': 128,
        'maxComputeWorkgroupStorageSize': 32768,
        'maxComputeInvocationsPerWorkgroup': 1024,
        'maxComputeWorkgroupSizeX': 1024,
        'maxComputeWorkgroupSizeY': 1024,
        'maxComputeWorkgroupSizeZ': 64,
        'maxComputeWorkgroupsPerDimension': 65535,
        'maxStorageBuffersInVertexStage': 16,
        'maxStorageBuffersInFragmentStage': 16,
    },
    features=[
        'core-features-and-limits',
        'depth-clip-control',
        'depth32float-stencil8',
        'texture-compression-bc',
        'texture-compression-bc-sliced-3d',
        'texture-compression-etc2',
        'texture-compression-astc',
        'texture-compression-astc-sliced-3d',
        'timestamp-query',
        'indirect-first-instance',
        'shader-f16',
        'rg11b10ufloat-renderable',
        'bgra8unorm-storage',
        'float32-filterable',
        'float32-blendable',
        'clip-distances',
        'dual-source-blending',
        'subgroups',
        'texture-component-swizzle',
        'texture-formats-tier1',
        'texture-formats-tier2',
        'primitive-index',
        'subgroup-size-control',
    ],
)

SPEECH_WINDOWS = SpeechFingerprint(
    voices=[
        SpeechVoice(
            name='Microsoft David - English (United States)', lang='en-US', local_service=True
        ),
        SpeechVoice(
            name='Microsoft Zira - English (United States)', lang='en-US', local_service=True
        ),
        SpeechVoice(name='Google US English', lang='en-US', local_service=False),
    ]
)

SPEECH_MAC = SpeechFingerprint(
    voices=[
        SpeechVoice(name='Samantha', lang='en-US', local_service=True),
        SpeechVoice(name='Alex', lang='en-US', local_service=True),
        SpeechVoice(name='Google US English', lang='en-US', local_service=False),
    ]
)

SPEECH_ANDROID = SpeechFingerprint(
    voices=[
        SpeechVoice(
            name='Android Speech Recognition and Synthesis from Google en-us-x-sfg-local',
            lang='en_US',
            local_service=True,
        ),
        SpeechVoice(
            name='Android Speech Recognition and Synthesis from Google en-us-x-sfg-network',
            lang='en_US',
            local_service=False,
        ),
    ]
)

# Media codec support, which is a statement about the build and the operating
# system: ``canPlayType()`` and ``MediaSource.isTypeSupported()`` answer from
# what the binary can decode. Measured on 2026-09-16 with Chrome 152: a macOS
# Chrome answers 'probably' for HEVC, while the Chromium of Debian trixie
# answers '' for the same type and 'probably' for everything else here. H.264
# and AAC are the pair that separates Google Chrome from a Chromium built
# without the proprietary codecs, whatever the platform.
_BASE_CODECS = {
    'video/mp4; codecs="avc1.42E01E"': 'probably',
    'video/mp4; codecs="avc1.64001F"': 'probably',
    'audio/mp4; codecs="mp4a.40.2"': 'probably',
    'audio/mpeg': 'probably',
    'video/webm; codecs="vp9"': 'probably',
    'video/webm; codecs="vp8"': 'probably',
    'audio/ogg; codecs="opus"': 'probably',
    'audio/webm; codecs="opus"': 'probably',
}

_BASE_MEDIA_SOURCE = {
    'video/mp4; codecs="avc1.42E01E"': True,
    'audio/mp4; codecs="mp4a.40.2"': True,
    'video/webm; codecs="vp9"': True,
}

#: HEVC decodes on macOS and on Windows, so both claim it.
HEVC_TYPES = {
    'video/mp4; codecs="hvc1.1.6.L93.B0"': 'probably',
    'video/mp4; codecs="hev1.1.6.L93.B0"': 'probably',
}

#: A Linux desktop Chrome refuses HEVC; saying so is what makes the profile
#: coherent with the platform it claims. Measured on Debian trixie.
NO_HEVC_TYPES = {
    'video/mp4; codecs="hvc1.1.6.L93.B0"': '',
    'video/mp4; codecs="hev1.1.6.L93.B0"': '',
}

WINDOWS_CODECS = MediaCodecsFingerprint(
    can_play_type={**_BASE_CODECS, **HEVC_TYPES},
    media_source={**_BASE_MEDIA_SOURCE, 'video/mp4; codecs="hvc1.1.6.L93.B0"': True},
)

MACOS_CODECS = MediaCodecsFingerprint(
    can_play_type={**_BASE_CODECS, **HEVC_TYPES},
    media_source={**_BASE_MEDIA_SOURCE, 'video/mp4; codecs="hvc1.1.6.L93.B0"': True},
)

LINUX_CODECS = MediaCodecsFingerprint(
    can_play_type={**_BASE_CODECS, **NO_HEVC_TYPES},
    media_source={**_BASE_MEDIA_SOURCE, 'video/mp4; codecs="hvc1.1.6.L93.B0"': False},
)

ANDROID_CODECS = MediaCodecsFingerprint(
    can_play_type={**_BASE_CODECS, **HEVC_TYPES},
    media_source={**_BASE_MEDIA_SOURCE, 'video/mp4; codecs="hvc1.1.6.L93.B0"': True},
)


DESKTOP_NETWORK = NetworkConnectionFingerprint(
    effective_type='4g',
    downlink=10.0,
    rtt=50,
    save_data=False,
)

MOBILE_NETWORK = NetworkConnectionFingerprint(
    effective_type='4g',
    downlink=5.0,
    rtt=100,
    save_data=False,
)

WINDOWS_FONTS = FontFingerprint(
    available_fonts=[
        'Arial',
        'Arial Black',
        'Calibri',
        'Cambria',
        'Comic Sans MS',
        'Consolas',
        'Courier New',
        'Georgia',
        'Impact',
        'Lucida Console',
        'Microsoft Sans Serif',
        'Palatino Linotype',
        'Segoe UI',
        'Tahoma',
        'Times New Roman',
        'Trebuchet MS',
        'Verdana',
    ]
)

MAC_FONTS = FontFingerprint(
    available_fonts=[
        'Arial',
        'Arial Black',
        'Comic Sans MS',
        'Courier New',
        'Georgia',
        'Helvetica',
        'Helvetica Neue',
        'Impact',
        'Lucida Grande',
        'Menlo',
        'Monaco',
        'Palatino',
        'SF Pro Display',
        'SF Pro Text',
        'Tahoma',
        'Times New Roman',
        'Trebuchet MS',
        'Verdana',
    ]
)

ANDROID_FONTS = FontFingerprint(
    available_fonts=[
        'Roboto',
        'Noto Sans',
        'Noto Color Emoji',
        'Droid Sans',
        'Droid Sans Mono',
        'Courier New',
    ]
)

DESKTOP_PERMISSIONS = PermissionsFingerprint(
    overrides={
        'notifications': 'denied',
        'geolocation': 'prompt',
        'camera': 'prompt',
        'microphone': 'prompt',
    }
)

ANDROID_PERMISSIONS = PermissionsFingerprint(
    overrides={
        'notifications': 'prompt',
        'geolocation': 'prompt',
        'camera': 'prompt',
        'microphone': 'prompt',
    }
)

WINDOWS_ABSENT_APIS = [
    # Shape Detection needs a platform barcode backend, which Windows has none of.
    'BarcodeDetector',
    # The Contact Picker and the Content Index ship on Android only.
    'ContactsManager',
    'ContentIndex',
    'navigator.contacts',
    # NetworkInformation.downlinkMax is exposed on Chrome for Android only.
    'NetworkInformation.downlinkMax',
]
MACOS_ABSENT_APIS = [
    'ContactsManager',
    'ContentIndex',
    'navigator.contacts',
    'NetworkInformation.downlinkMax',
]
ANDROID_ABSENT_APIS = [
    # Chrome for Android has no SharedWorker, no WebHID and no Web Serial, no
    # audio output selection, and the window controls overlay and the built-in
    # AI models are desktop only.
    'SharedWorker',
    'navigator.hid',
    'navigator.serial',
    'navigator.windowControlsOverlay',
    'HTMLMediaElement.sinkId',
    'HTMLMediaElement.setSinkId',
    'MediaDevices.selectAudioOutput',
    'Summarizer',
    'LanguageModel',
]
# Removing is all a profile can do. The Contact Picker and the Content Index
# exist on Android and not on a desktop host, so an Android profile run from a
# desktop still answers without them: that pair only closes on an Android host.

FINGERPRINTS: dict[str, FingerprintConfig] = {
    # Android (mobile) — Brazilian identity (pair with a Brazilian egress IP).
    'android_s24_ultra_sao_paulo': FingerprintConfig(
        user_agent=UA_ANDROID,
        client_hints=ClientHintsFingerprint(platform_version='15.0.0', model='SM-S928B'),
        navigator=NavigatorFingerprint(
            platform='Linux armv81',
            vendor='Google Inc.',
            app_version=APP_ANDROID,
            pdf_viewer_enabled=False,
        ),
        webgl=WebGLProfile(
            vendor='Qualcomm',
            renderer='Adreno (TM) 750',
            max_texture_size=16384,
            max_renderbuffer_size=16384,
            max_viewport_dims=[16384, 16384],
            max_vertex_attribs=32,
            max_vertex_uniform_vectors=256,
            max_fragment_uniform_vectors=224,
            max_texture_image_units=16,
            max_vertex_texture_image_units=16,
            max_combined_texture_image_units=32,
            aliased_line_width_range=[1, 1],
            aliased_point_size_range=[1, 1024],
            supported_extensions=MOBILE_EXTENSIONS,
            webgl2_extensions=MOBILE_WEBGL2_EXTENSIONS,
            shader_precision_formats=SHADER_PRECISION_DEFAULT,
        ),
        webgpu=WEBGPU_ADRENO_750_VULKAN,
        screen=ScreenFingerprint(
            width=384,
            height=832,
            avail_width=384,
            avail_height=832,
            outer_width=384,
            outer_height=784,
            inner_width=384,
            inner_height=728,
            color_depth=24,
            pixel_depth=24,
            device_pixel_ratio=3.75,
            orientation_type='portrait-primary',
            orientation_angle=0,
        ),
        hardware=HardwareFingerprint(hardware_concurrency=8, device_memory=8, max_touch_points=10),
        geolocation=SAO_PAULO_GEO,
        timezone='America/Sao_Paulo',
        locale=BR_LOCALE,
        media_devices=MediaDevicesFingerprint(audio_inputs=1, audio_outputs=1, video_inputs=1),
        media_codecs=ANDROID_CODECS,
        audio=AudioFingerprint(sample_rate=48000, max_channel_count=2),
        speech=SPEECH_ANDROID,
        network_connection=MOBILE_NETWORK,
        fonts=ANDROID_FONTS,
        platform_apis=PlatformApisFingerprint(hidden=ANDROID_ABSENT_APIS),
        media_features=MediaFeaturesFingerprint(color_gamut='p3'),
        permissions=ANDROID_PERMISSIONS,
    ),
    # Windows desktop — US identity (pair with a US egress IP / proxy).
    # The uniform, varying and transform-feedback limits are ANGLE's own D3D11
    # caps (renderer11_utils.cpp GenerateCaps): 14 constant buffer slots minus
    # 2 reserved gives 12 uniform blocks per stage, bindings and combined
    # blocks are their sum, components are 4 x vectors, combined components are
    # components + blocks x blockSize/4, maxLODBias is 2.0, the UBO alignment
    # is 256 and interleaved transform-feedback components are vertex output
    # vectors x 4. web3dsurvey's Windows distribution reports the same values
    # on 97% of machines or more.
    'windows11_rtx3060_nyc': FingerprintConfig(
        user_agent=UA_WINDOWS,
        client_hints=ClientHintsFingerprint(platform_version='15.0.0'),
        navigator=NavigatorFingerprint(
            platform='Win32',
            vendor='Google Inc.',
            app_version=APP_WINDOWS,
            pdf_viewer_enabled=True,
        ),
        webgl=WebGLProfile(
            vendor='Google Inc. (NVIDIA)',
            renderer=(
                'ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 (0x00002504) '
                'Direct3D11 vs_5_0 ps_5_0, D3D11)'
            ),
            max_texture_size=16384,
            max_renderbuffer_size=16384,
            max_viewport_dims=[32767, 32767],
            max_cube_map_texture_size=16384,
            max_3d_texture_size=2048,
            max_array_texture_layers=2048,
            max_vertex_attribs=16,
            max_vertex_uniform_vectors=4096,
            max_vertex_uniform_components=16384,
            max_fragment_uniform_vectors=1024,
            max_fragment_uniform_components=4096,
            max_varying_vectors=30,
            max_varying_components=120,
            max_vertex_output_components=120,
            max_fragment_input_components=120,
            max_texture_image_units=16,
            max_vertex_texture_image_units=16,
            max_combined_texture_image_units=32,
            max_color_attachments=8,
            max_draw_buffers=8,
            max_samples=8,
            max_uniform_block_size=65536,
            max_uniform_buffer_bindings=24,
            max_vertex_uniform_blocks=12,
            max_fragment_uniform_blocks=12,
            max_combined_uniform_blocks=24,
            max_combined_vertex_uniform_components=212992,
            max_combined_fragment_uniform_components=200704,
            uniform_buffer_offset_alignment=256,
            max_texture_lod_bias=2.0,
            max_transform_feedback_interleaved_components=120,
            aliased_line_width_range=[1, 1],
            aliased_point_size_range=[1, 1024],
            supported_extensions=DESKTOP_EXTENSIONS,
            webgl2_extensions=DESKTOP_WEBGL2_EXTENSIONS,
            shader_precision_formats=SHADER_PRECISION_D3D11,
        ),
        webgpu=WEBGPU_NVIDIA_AMPERE_D3D12,
        screen=ScreenFingerprint(
            width=1920,
            height=1080,
            avail_width=1920,
            avail_height=1040,
            avail_top=0,  # Windows taskbar sits at the bottom
            avail_left=0,
            outer_width=1920,
            outer_height=1040,
            inner_width=1903,
            inner_height=969,
            color_depth=24,
            pixel_depth=24,
            device_pixel_ratio=1.0,
            orientation_type='landscape-primary',
            orientation_angle=0,
        ),
        hardware=HardwareFingerprint(hardware_concurrency=12, device_memory=8, max_touch_points=0),
        geolocation=NEW_YORK_GEO,
        timezone='America/New_York',
        locale=US_LOCALE,
        media_devices=MediaDevicesFingerprint(audio_inputs=1, audio_outputs=1, video_inputs=1),
        media_codecs=WINDOWS_CODECS,
        audio=AudioFingerprint(sample_rate=48000, max_channel_count=2),
        speech=SPEECH_WINDOWS,
        network_connection=DESKTOP_NETWORK,
        fonts=WINDOWS_FONTS,
        platform_apis=PlatformApisFingerprint(hidden=WINDOWS_ABSENT_APIS),
        media_features=MediaFeaturesFingerprint(color_gamut='srgb'),
        permissions=DESKTOP_PERMISSIONS,
    ),
    # macOS desktop — US identity (pair with a US egress IP / proxy).
    # The uniform, varying and transform-feedback limits are ANGLE Metal on
    # Apple silicon, read from an M4 under Chrome 152. No public per-parameter
    # distribution exists for Metal, so this capture is the only reference.
    'macos_m3_new_york': FingerprintConfig(
        user_agent=UA_MAC,
        client_hints=ClientHintsFingerprint(platform_version='15.6.1'),
        navigator=NavigatorFingerprint(
            platform='MacIntel',
            vendor='Google Inc.',
            app_version=APP_MAC,
            pdf_viewer_enabled=True,
        ),
        webgl=WebGLProfile(
            vendor='Google Inc. (Apple)',
            renderer='ANGLE (Apple, ANGLE Metal Renderer: Apple M3, Unspecified Version)',
            max_texture_size=16384,
            max_renderbuffer_size=16384,
            max_viewport_dims=[16384, 16384],
            max_vertex_attribs=16,
            max_vertex_uniform_vectors=1024,
            max_vertex_uniform_components=4096,
            max_fragment_uniform_vectors=1024,
            max_fragment_uniform_components=4096,
            max_varying_vectors=30,
            max_varying_components=120,
            max_vertex_output_components=120,
            max_fragment_input_components=120,
            max_texture_image_units=16,
            max_vertex_texture_image_units=16,
            max_combined_texture_image_units=32,
            max_uniform_block_size=16384,
            max_uniform_buffer_bindings=32,
            max_vertex_uniform_blocks=16,
            max_fragment_uniform_blocks=16,
            max_combined_uniform_blocks=32,
            max_combined_vertex_uniform_components=69632,
            max_combined_fragment_uniform_components=69632,
            uniform_buffer_offset_alignment=16,
            max_texture_lod_bias=15.0,
            max_transform_feedback_interleaved_components=128,
            aliased_line_width_range=[1, 1],
            aliased_point_size_range=[1, 511],
            shader_precision_formats=SHADER_PRECISION_DEFAULT,
        ),
        webgpu=WEBGPU_APPLE_M_SERIES,
        screen=ScreenFingerprint(
            width=1440,
            height=900,
            avail_width=1440,
            avail_height=860,
            avail_top=25,  # macOS menu bar at the top; remainder (15) is the dock
            avail_left=0,
            outer_width=1440,
            outer_height=860,
            inner_width=1440,
            inner_height=785,
            color_depth=24,
            pixel_depth=24,
            device_pixel_ratio=2.0,
            orientation_type='landscape-primary',
            orientation_angle=0,
        ),
        hardware=HardwareFingerprint(hardware_concurrency=8, device_memory=8, max_touch_points=0),
        geolocation=NEW_YORK_GEO,
        timezone='America/New_York',
        locale=US_LOCALE,
        media_devices=MediaDevicesFingerprint(audio_inputs=1, audio_outputs=2, video_inputs=1),
        media_codecs=MACOS_CODECS,
        audio=AudioFingerprint(sample_rate=44100, max_channel_count=2),
        speech=SPEECH_MAC,
        network_connection=DESKTOP_NETWORK,
        fonts=MAC_FONTS,
        platform_apis=PlatformApisFingerprint(hidden=MACOS_ABSENT_APIS),
        media_features=MediaFeaturesFingerprint(color_gamut='p3'),
        permissions=DESKTOP_PERMISSIONS,
    ),
}

DEFAULT_FINGERPRINT = FINGERPRINTS['windows11_rtx3060_nyc']
