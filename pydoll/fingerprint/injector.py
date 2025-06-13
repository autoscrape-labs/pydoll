"""
Browser fingerprint injection module.

This module provides the FingerprintInjector class which generates JavaScript
code to override browser properties for fingerprint spoofing.
"""

from typing import Dict, List
from .models import Fingerprint


class FingerprintInjector:
    """
    Generates JavaScript code to inject fingerprint spoofing into browsers.

    This class creates JavaScript that overrides various browser APIs and
    properties to present a fake fingerprint to detection systems.
    """

    def __init__(self, fingerprint: Fingerprint):
        """
        Initialize the injector with a fingerprint.

        Args:
            fingerprint: The fingerprint data to inject.
        """
        self.fingerprint = fingerprint

    def generate_script(self) -> str:
        """
        Generate the complete JavaScript injection script.

        Returns:
            JavaScript code as a string that will override browser properties.
        """
        scripts = [
            self._generate_navigator_override(),
            self._generate_screen_override(),
            self._generate_webgl_override(),
            self._generate_canvas_override(),
            self._generate_audio_override(),
            self._generate_plugin_override(),
            self._generate_misc_overrides(),
        ]

        # Wrap everything in an IIFE to avoid namespace pollution
        full_script = f"""
(function() {{
    'use strict';

    // Disable webdriver detection
    Object.defineProperty(navigator, 'webdriver', {{
        get: () => false,
        configurable: true
    }});

    // Remove automation indicators
    delete window.navigator.webdriver;
    delete window.__webdriver_script_fn;
    delete window.__webdriver_script_func;
    delete window.__webdriver_script_function;
    delete window.__fxdriver_evaluate;
    delete window.__fxdriver_unwrapped;
    delete window._Selenium_IDE_Recorder;
    delete window._selenium;
    delete window.calledSelenium;
    delete window.calledPhantom;
    delete window.__nightmare;
    delete window._phantom;
    delete window.phantom;
    delete window.callPhantom;

    {chr(10).join(scripts)}

    // Override toString to hide modifications
    const originalToString = Function.prototype.toString;
    Function.prototype.toString = function() {{
        if (this.name === 'get' && this.toString().includes('return')) {{
            return 'function get() {{ [native code] }}';
        }}
        return originalToString.call(this);
    }};
}})();
"""

        return full_script

    def _generate_navigator_override(self) -> str:
        """Generate JavaScript to override navigator properties."""
        languages_js = str(self.fingerprint.languages).replace("'", '"')

        return f"""
    // Override navigator properties
    Object.defineProperty(navigator, 'userAgent', {{
        get: () => '{self.fingerprint.user_agent}',
        configurable: true
    }});

    Object.defineProperty(navigator, 'platform', {{
        get: () => '{self.fingerprint.platform}',
        configurable: true
    }});

    Object.defineProperty(navigator, 'language', {{
        get: () => '{self.fingerprint.language}',
        configurable: true
    }});

    Object.defineProperty(navigator, 'languages', {{
        get: () => {languages_js},
        configurable: true
    }});

    Object.defineProperty(navigator, 'hardwareConcurrency', {{
        get: () => {self.fingerprint.hardware_concurrency},
        configurable: true
    }});

    {'Object.defineProperty(navigator, "deviceMemory", { get: () => ' + str(self.fingerprint.device_memory) + ', configurable: true });' if self.fingerprint.device_memory else ''}

    Object.defineProperty(navigator, 'cookieEnabled', {{
        get: () => {str(self.fingerprint.cookie_enabled).lower()},
        configurable: true
    }});

    {'Object.defineProperty(navigator, "doNotTrack", { get: () => "' + str(self.fingerprint.do_not_track) + '", configurable: true });' if self.fingerprint.do_not_track else ''}
    """

    def _generate_screen_override(self) -> str:
        """Generate JavaScript to override screen properties."""
        return f"""
    // Override screen properties
    Object.defineProperty(screen, 'width', {{
        get: () => {self.fingerprint.screen_width},
        configurable: true
    }});

    Object.defineProperty(screen, 'height', {{
        get: () => {self.fingerprint.screen_height},
        configurable: true
    }});

    Object.defineProperty(screen, 'colorDepth', {{
        get: () => {self.fingerprint.screen_color_depth},
        configurable: true
    }});

    Object.defineProperty(screen, 'pixelDepth', {{
        get: () => {self.fingerprint.screen_pixel_depth},
        configurable: true
    }});

    Object.defineProperty(screen, 'availWidth', {{
        get: () => {self.fingerprint.available_width},
        configurable: true
    }});

    Object.defineProperty(screen, 'availHeight', {{
        get: () => {self.fingerprint.available_height},
        configurable: true
    }});

    // Override window dimensions
    Object.defineProperty(window, 'innerWidth', {{
        get: () => {self.fingerprint.inner_width},
        configurable: true
    }});

    Object.defineProperty(window, 'innerHeight', {{
        get: () => {self.fingerprint.inner_height},
        configurable: true
    }});

    Object.defineProperty(window, 'outerWidth', {{
        get: () => {self.fingerprint.viewport_width},
        configurable: true
    }});

    Object.defineProperty(window, 'outerHeight', {{
        get: () => {self.fingerprint.viewport_height},
        configurable: true
    }});
    """

    def _generate_webgl_override(self) -> str:
        """Generate JavaScript to override WebGL properties."""
        extensions_js = str(self.fingerprint.webgl_extensions).replace("'", '"')

        return f"""
    // Override WebGL properties
    const getParameter = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(parameter) {{
        if (parameter === 37445) {{ // VENDOR
            return '{self.fingerprint.webgl_vendor}';
        }}
        if (parameter === 37446) {{ // RENDERER
            return '{self.fingerprint.webgl_renderer}';
        }}
        if (parameter === 7938) {{ // VERSION
            return '{self.fingerprint.webgl_version}';
        }}
        if (parameter === 35724) {{ // SHADING_LANGUAGE_VERSION
            return '{self.fingerprint.webgl_shading_language_version}';
        }}
        return getParameter.call(this, parameter);
    }};

    const getSupportedExtensions = WebGLRenderingContext.prototype.getSupportedExtensions;
    WebGLRenderingContext.prototype.getSupportedExtensions = function() {{
        return {extensions_js};
    }};

    // Also override WebGL2 if available
    if (window.WebGL2RenderingContext) {{
        const getParameter2 = WebGL2RenderingContext.prototype.getParameter;
        WebGL2RenderingContext.prototype.getParameter = function(parameter) {{
            if (parameter === 37445) return '{self.fingerprint.webgl_vendor}';
            if (parameter === 37446) return '{self.fingerprint.webgl_renderer}';
            if (parameter === 7938) return '{self.fingerprint.webgl_version}';
            if (parameter === 35724) return '{self.fingerprint.webgl_shading_language_version}';
            return getParameter2.call(this, parameter);
        }};

        const getSupportedExtensions2 = WebGL2RenderingContext.prototype.getSupportedExtensions;
        WebGL2RenderingContext.prototype.getSupportedExtensions = function() {{
            return {extensions_js};
        }};
    }}
    """

    def _generate_canvas_override(self) -> str:
        """Generate JavaScript to override canvas fingerprinting."""
        return f"""
    // Override canvas fingerprinting
    const originalGetContext = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function(contextType) {{
        const context = originalGetContext.call(this, contextType);

        if (contextType === '2d') {{
            const originalToDataURL = this.toDataURL;
            this.toDataURL = function() {{
                return 'data:image/png;base64,{self.fingerprint.canvas_fingerprint}';
            }};

            const originalGetImageData = context.getImageData;
            context.getImageData = function() {{
                const imageData = originalGetImageData.apply(this, arguments);
                // Add some noise to the image data
                for (let i = 0; i < imageData.data.length; i += 4) {{
                    imageData.data[i] = Math.floor(Math.random() * 256);
                }}
                return imageData;
            }};
        }}

        return context;
    }};
    """

    def _generate_audio_override(self) -> str:
        """Generate JavaScript to override audio context properties."""
        return f"""
    // Override AudioContext properties
    if (window.AudioContext || window.webkitAudioContext) {{
        const OriginalAudioContext = window.AudioContext || window.webkitAudioContext;

        function FakeAudioContext() {{
            const context = new OriginalAudioContext();

            Object.defineProperty(context, 'sampleRate', {{
                get: () => {self.fingerprint.audio_context_sample_rate},
                configurable: true
            }});

            Object.defineProperty(context, 'state', {{
                get: () => '{self.fingerprint.audio_context_state}',
                configurable: true
            }});

            Object.defineProperty(context.destination, 'maxChannelCount', {{
                get: () => {self.fingerprint.audio_context_max_channel_count},
                configurable: true
            }});

            return context;
        }}

        FakeAudioContext.prototype = OriginalAudioContext.prototype;
        window.AudioContext = FakeAudioContext;
        if (window.webkitAudioContext) {{
            window.webkitAudioContext = FakeAudioContext;
        }}
    }}
    """

    def _generate_plugin_override(self) -> str:
        """Generate JavaScript to override plugin information."""
        if not self.fingerprint.plugins:
            return ""

        plugins_js = []
        for i, plugin in enumerate(self.fingerprint.plugins):
            plugins_js.append(f"""
        plugins[{i}] = {{
            name: '{plugin['name']}',
            filename: '{plugin['filename']}',
            description: '{plugin['description']}',
            length: 1,
            0: {{
                type: 'application/pdf',
                suffixes: 'pdf',
                description: '{plugin['description']}'
            }}
        }};""")

        return f"""
    // Override plugin information
    Object.defineProperty(navigator, 'plugins', {{
        get: () => {{
            const plugins = {{}};
            plugins.length = {len(self.fingerprint.plugins)};
            {''.join(plugins_js)}
            return plugins;
        }},
        configurable: true
    }});
    """

    def _generate_misc_overrides(self) -> str:
        """Generate JavaScript for miscellaneous overrides."""
        return f"""
    // Override timezone
    const originalDateGetTimezoneOffset = Date.prototype.getTimezoneOffset;
    Date.prototype.getTimezoneOffset = function() {{
        return {self.fingerprint.timezone_offset};
    }};

    // Override Intl.DateTimeFormat
    if (window.Intl && window.Intl.DateTimeFormat) {{
        const originalResolvedOptions = Intl.DateTimeFormat.prototype.resolvedOptions;
        Intl.DateTimeFormat.prototype.resolvedOptions = function() {{
            const options = originalResolvedOptions.call(this);
            options.timeZone = '{self.fingerprint.timezone}';
            return options;
        }};
    }}

    // Override connection type
    if (navigator.connection || navigator.mozConnection || navigator.webkitConnection) {{
        const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
        Object.defineProperty(connection, 'effectiveType', {{
            get: () => '{self.fingerprint.connection_type}',
            configurable: true
        }});
    }}

    // Hide automation indicators in Chrome
    Object.defineProperty(window, 'chrome', {{
        get: () => {{
            return {{
                runtime: {{
                    onConnect: undefined,
                    onMessage: undefined
                }}
            }};
        }},
        configurable: true
    }});

    // Override permissions
    if (navigator.permissions && navigator.permissions.query) {{
        const originalQuery = navigator.permissions.query;
        navigator.permissions.query = function(parameters) {{
            return originalQuery(parameters).then(result => {{
                if (parameters.name === 'notifications') {{
                    Object.defineProperty(result, 'state', {{
                        get: () => 'denied',
                        configurable: true
                    }});
                }}
                return result;
            }});
        }};
    }}
    """
