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
   Chrome (these target Chrome 145).

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
    FingerprintConfig,
    FontFingerprint,
    GeolocationFingerprint,
    HardwareFingerprint,
    LocaleFingerprint,
    MediaDevicesFingerprint,
    MediaFeaturesFingerprint,
    NavigatorFingerprint,
    NetworkConnectionFingerprint,
    PermissionsFingerprint,
    ScreenFingerprint,
    SpeechFingerprint,
    SpeechVoice,
    WebGLProfile,
)

CHROME_MOBILE = '145.0.7632.45'
CHROME_DESKTOP = '151.0.7827.201'

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
    'EXT_color_buffer_half_float',
    'EXT_float_blend',
    'EXT_frag_depth',
    'EXT_shader_texture_lod',
    'EXT_texture_compression_bptc',
    'EXT_texture_compression_rgtc',
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
    'WEBGL_compressed_texture_s3tc',
    'WEBGL_compressed_texture_s3tc_srgb',
    'WEBGL_debug_renderer_info',
    'WEBGL_depth_texture',
    'WEBGL_draw_buffers',
    'WEBGL_lose_context',
    'WEBGL_multi_draw',
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
    'EXT_color_buffer_float',
    'EXT_color_buffer_half_float',
    'EXT_float_blend',
    'EXT_texture_compression_bptc',
    'EXT_texture_compression_rgtc',
    'EXT_texture_filter_anisotropic',
    'EXT_texture_norm16',
    'KHR_parallel_shader_compile',
    'OES_draw_buffers_indexed',
    'OES_texture_float_linear',
    'WEBGL_clip_cull_distance',
    'WEBGL_compressed_texture_s3tc',
    'WEBGL_compressed_texture_s3tc_srgb',
    'WEBGL_debug_renderer_info',
    'WEBGL_lose_context',
    'WEBGL_multi_draw',
    'WEBGL_provoking_vertex',
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

FINGERPRINTS: dict[str, FingerprintConfig] = {
    # Android (mobile) — Brazilian identity (pair with a Brazilian egress IP).
    'android_s24_ultra_sao_paulo': FingerprintConfig(
        user_agent=UA_ANDROID,
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
        audio=AudioFingerprint(sample_rate=48000, max_channel_count=2),
        speech=SPEECH_ANDROID,
        network_connection=MOBILE_NETWORK,
        fonts=ANDROID_FONTS,
        media_features=MediaFeaturesFingerprint(color_gamut='p3'),
        permissions=ANDROID_PERMISSIONS,
    ),
    # Windows desktop — US identity (pair with a US egress IP / proxy).
    'windows11_rtx3060_nyc': FingerprintConfig(
        user_agent=UA_WINDOWS,
        navigator=NavigatorFingerprint(
            platform='Win32',
            vendor='Google Inc.',
            app_version=APP_WINDOWS,
            pdf_viewer_enabled=True,
        ),
        webgl=WebGLProfile(
            vendor='Google Inc. (NVIDIA)',
            renderer='ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0, D3D11)',
            max_texture_size=32768,
            max_renderbuffer_size=32768,
            max_viewport_dims=[32768, 32768],
            max_vertex_attribs=16,
            max_vertex_uniform_vectors=4096,
            max_fragment_uniform_vectors=1024,
            max_texture_image_units=32,
            max_vertex_texture_image_units=32,
            max_combined_texture_image_units=192,
            aliased_line_width_range=[1, 1],
            aliased_point_size_range=[1, 1024],
            supported_extensions=DESKTOP_EXTENSIONS,
            webgl2_extensions=DESKTOP_WEBGL2_EXTENSIONS,
            shader_precision_formats=SHADER_PRECISION_DEFAULT,
        ),
        screen=ScreenFingerprint(
            width=1920,
            height=1080,
            avail_width=1920,
            avail_height=1040,
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
        audio=AudioFingerprint(sample_rate=48000, max_channel_count=2),
        speech=SPEECH_WINDOWS,
        network_connection=DESKTOP_NETWORK,
        fonts=WINDOWS_FONTS,
        media_features=MediaFeaturesFingerprint(color_gamut='srgb'),
        permissions=DESKTOP_PERMISSIONS,
    ),
    # macOS desktop — US identity (pair with a US egress IP / proxy).
    'macos_m3_new_york': FingerprintConfig(
        user_agent=UA_MAC,
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
            max_fragment_uniform_vectors=1024,
            max_texture_image_units=16,
            max_vertex_texture_image_units=16,
            max_combined_texture_image_units=32,
            aliased_line_width_range=[1, 1],
            aliased_point_size_range=[1, 511],
            shader_precision_formats=SHADER_PRECISION_DEFAULT,
        ),
        screen=ScreenFingerprint(
            width=1440,
            height=900,
            avail_width=1440,
            avail_height=860,
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
        audio=AudioFingerprint(sample_rate=44100, max_channel_count=2),
        speech=SPEECH_MAC,
        network_connection=DESKTOP_NETWORK,
        fonts=MAC_FONTS,
        media_features=MediaFeaturesFingerprint(color_gamut='p3'),
        permissions=DESKTOP_PERMISSIONS,
    ),
}

DEFAULT_FINGERPRINT = FINGERPRINTS['windows11_rtx3060_nyc']
