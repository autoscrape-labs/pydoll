from __future__ import annotations

import json
import logging
import re
from typing import TYPE_CHECKING

from pydoll.commands.bidi.browsing_context_commands import BrowsingContextCommands
from pydoll.commands.bidi.emulation_commands import EmulationCommands
from pydoll.commands.bidi.script_commands import ScriptCommands
from pydoll.exceptions import CommandFailed
from pydoll.protocol.bidi.browsing_context.types import Viewport
from pydoll.protocol.bidi.emulation.types import (
    GeolocationCoordinates,
    ScreenArea,
    ScreenOrientation,
    ScreenOrientationNatural,
    ScreenOrientationType,
)
from pydoll.protocol.bidi.script.types import ContextTarget
from pydoll.utils import UserAgentParser
from pydoll.utils.fingerprint_builder import _wrap, build_fingerprint_js

if TYPE_CHECKING:
    from pydoll.browser.firefox.tab import BiDiTab
    from pydoll.protocol.bidi.base import Command, T_CommandParams, T_CommandResult
    from pydoll.protocol.fingerprint.types import FingerprintConfig, ScreenFingerprint

logger = logging.getLogger(__name__)

_UNKNOWN_COMMAND = 'unknown command'

_UA_PLATFORM_SEGMENT = re.compile(r'\(([^)]*)\)')

_GECKO_DESKTOP_TOKENS = frozenset({'Macintosh', 'X11'})


class BiDiFingerprintApplier:
    """Applies a fingerprint profile to a single Firefox tab over WebDriver BiDi.

    The Firefox counterpart of :class:`pydoll.browser.fingerprint_applier.FingerprintApplier`,
    following the same native-first rule: every signal Firefox can override through
    the BiDi ``emulation`` module is set there (no JavaScript getter behind it), and
    only the remaining surfaces are patched by the hardened JavaScript from
    :mod:`pydoll.utils.fingerprint_builder`, installed as a ``script.addPreloadScript``
    scoped to the tab's browsing context so it runs before page scripts on every
    navigation. A ``BiDiTab`` composes one instance and
    ``BiDiTab.apply_fingerprint`` delegates to :meth:`apply`.

    Measured against Firefox 157:

    Native (``emulation.*`` / ``browsingContext.setViewport``, scoped to this tab):
        - ``user_agent``: ``navigator.userAgent`` and the ``User-Agent`` header
          (``setUserAgentOverride``); dedicated workers inherit it for http(s)
          origins
        - ``locale.languages[0]``: ``navigator.language``, ``navigator.languages``
          (single entry), the ``Intl`` default locale and the ``Accept-Language``
          header (``setLocaleOverride``, BCP 47 form; ``en_US`` is rejected)
        - ``timezone`` (``setTimezoneOverride``, page and workers)
        - ``geolocation`` (``setGeolocationOverride``; the permission itself is
          granted with ``Firefox.grant_permissions``)
        - ``screen.width`` / ``height`` (``setScreenSettingsOverride``, which also
          forces ``availWidth`` / ``availHeight`` to the full area)
        - ``screen.orientation_type`` (``setScreenOrientationOverride``)
        - ``screen.inner_width`` / ``inner_height`` / ``device_pixel_ratio``
          (``browsingContext.setViewport``)
        - ``hardware.max_touch_points`` (``setTouchOverride``) when Firefox knows the
          command; Firefox 157 answers ``unknown command`` and the value falls back
          to a JavaScript getter

    JavaScript (preload script, window realms only):
        - ``navigator.platform`` / ``appVersion`` / ``oscpu`` derived from the
          User-Agent (Firefox's ``setUserAgentOverride`` changes only
          ``navigator.userAgent``), overridable by the ``navigator`` section
        - ``hardware.hardware_concurrency`` (no BiDi command exists)
        - the full ``locale.languages`` list when it has more than one entry
        - every section ``fingerprint_builder`` handles in Chromium too: WebGL,
          WebGPU, media devices, media codecs, plugins, audio, speech, fonts,
          platform APIs, WebRTC policy, and the screen extras (``avail_*``,
          ``color_depth``, ``pixel_depth``, ``outer_*``)

    Not applied on Firefox:
        - ``hardware.device_memory`` and ``network_connection``: Gecko has no
          ``navigator.deviceMemory`` / ``navigator.connection``; installing them
          would itself be a Chromium tell
        - ``client_hints``: Firefox sends no ``Sec-CH-UA-*`` headers and has no
          ``navigator.userAgentData``
        - ``media_features`` and ``permissions``: no BiDi command on Firefox 157
          for CSS media features, and ``permissions.setPermission`` needs an
          origin, so grant permissions with ``Firefox.grant_permissions`` instead
        - workers: BiDi preload scripts run in window realms only, and Firefox
          offers no auto-attach equivalent, so a dedicated or shared worker reads
          the real ``platform``, ``appVersion`` and ``hardwareConcurrency``
          (``userAgent``, ``languages`` and the timezone do reach it)
    """

    _ORIENTATION_TYPES: dict[str, ScreenOrientationType] = {
        'portrait-primary': ScreenOrientationType.PORTRAIT_PRIMARY,
        'portrait-secondary': ScreenOrientationType.PORTRAIT_SECONDARY,
        'landscape-primary': ScreenOrientationType.LANDSCAPE_PRIMARY,
        'landscape-secondary': ScreenOrientationType.LANDSCAPE_SECONDARY,
    }

    def __init__(self, tab: BiDiTab) -> None:
        self._tab = tab
        self._applied: FingerprintConfig | None = None
        self._preload_script_id: str | None = None

    async def apply(self, fingerprint: FingerprintConfig) -> None:
        """Apply a fingerprint profile to the tab.

        Idempotent for an identical profile. A different profile replaces the
        previous preload script and re-sends the native overrides; sections the
        new profile omits keep whatever Firefox currently reports.

        Args:
            fingerprint: Fingerprint configuration. Only specified fields are
                overridden; unspecified fields keep real browser values.
        """
        if self._applied == fingerprint:
            logger.debug('Fingerprint already applied to this tab; skipping (idempotent)')
            return
        logger.info('Applying fingerprint profile to Firefox tab %s', self._tab._context_id)
        fallback_lines = await self._apply_native_overrides(fingerprint)
        js = self._build_page_js(fingerprint, fallback_lines)
        await self._install_preload_script(js)
        self._applied = fingerprint
        logger.info('Fingerprint profile applied')

    async def _apply_native_overrides(self, fingerprint: FingerprintConfig) -> list[str]:
        """Send every BiDi-native override and return JS lines for the rejected ones."""
        contexts = [self._tab._context_id]
        fallback_lines: list[str] = []
        if 'user_agent' in fingerprint:
            await self._send(
                EmulationCommands.set_user_agent_override(
                    fingerprint['user_agent'], contexts=contexts
                )
            )
        languages = fingerprint.get('locale', {}).get('languages', [])
        if languages:
            await self._send(EmulationCommands.set_locale_override(languages[0], contexts=contexts))
        if 'timezone' in fingerprint:
            await self._send(
                EmulationCommands.set_timezone_override(fingerprint['timezone'], contexts=contexts)
            )
        if 'geolocation' in fingerprint:
            geo = fingerprint['geolocation']
            coordinates = GeolocationCoordinates(
                latitude=geo['latitude'], longitude=geo['longitude']
            )
            if 'accuracy' in geo:
                coordinates['accuracy'] = geo['accuracy']
            await self._send(
                EmulationCommands.set_geolocation_override(
                    coordinates=coordinates, contexts=contexts
                )
            )
        if 'screen' in fingerprint:
            await self._apply_screen(fingerprint['screen'], mobile=self._is_mobile(fingerprint))
        max_touch_points = fingerprint.get('hardware', {}).get('max_touch_points')
        if max_touch_points:
            touch_command = EmulationCommands.set_touch_override(
                max_touch_points, contexts=contexts
            )
            if not await self._send_if_supported(touch_command):
                fallback_lines.append(f'_defG(NP, "maxTouchPoints", {max_touch_points});')
        return fallback_lines

    async def _apply_screen(self, screen: ScreenFingerprint, mobile: bool) -> None:
        """Reshape the screen, its orientation and the viewport natively.

        ``setScreenSettingsOverride`` sets ``screen.width`` / ``height`` (and resets
        ``availWidth`` / ``availHeight`` / ``availTop`` to the full area, which the
        JS screen extras correct afterwards). The natural orientation follows the
        device class: portrait for a mobile profile, landscape otherwise.
        ``browsingContext.setViewport`` drives ``innerWidth`` / ``innerHeight`` and
        ``devicePixelRatio``; a viewport needs both inner dimensions.
        """
        context = self._tab._context_id
        await self._send(
            EmulationCommands.set_screen_settings_override(
                ScreenArea(width=screen['width'], height=screen['height']), contexts=[context]
            )
        )
        orientation_type = self._ORIENTATION_TYPES.get(screen.get('orientation_type', ''))
        if orientation_type is not None:
            natural = (
                ScreenOrientationNatural.PORTRAIT if mobile else ScreenOrientationNatural.LANDSCAPE
            )
            await self._send(
                EmulationCommands.set_screen_orientation_override(
                    ScreenOrientation(natural=natural, type=orientation_type), contexts=[context]
                )
            )
        viewport: Viewport | None = None
        if 'inner_width' in screen and 'inner_height' in screen:
            viewport = Viewport(width=screen['inner_width'], height=screen['inner_height'])
        device_pixel_ratio = screen.get('device_pixel_ratio')
        if viewport is not None or device_pixel_ratio is not None:
            await self._send(
                BrowsingContextCommands.set_viewport(
                    context=context, viewport=viewport, device_pixel_ratio=device_pixel_ratio
                )
            )

    async def _send(self, command: Command[T_CommandParams, T_CommandResult]) -> T_CommandResult:
        return await self._tab._execute_command(command)

    async def _send_if_supported(self, command: Command[T_CommandParams, T_CommandResult]) -> bool:
        """Send a command, returning False when this Firefox does not know it."""
        try:
            await self._send(command)
        except CommandFailed as error:
            if error.data != _UNKNOWN_COMMAND:
                raise
            logger.info(
                '%s is not supported by this Firefox; falling back to JavaScript', command['method']
            )
            return False
        return True

    @staticmethod
    def _is_mobile(fingerprint: FingerprintConfig) -> bool:
        mobile = fingerprint.get('mobile')
        if mobile is not None:
            return mobile
        if 'user_agent' in fingerprint:
            return UserAgentParser.parse(fingerprint['user_agent']).user_agent_metadata['mobile']
        return False

    def _build_page_js(self, fingerprint: FingerprintConfig, fallback_lines: list[str]) -> str:
        """Compose the preload script: the shared builder output plus the Gecko gaps."""
        parts = [build_fingerprint_js(self._page_js_config(fingerprint))]
        gap_lines = self._gecko_gap_lines(fingerprint) + fallback_lines
        if gap_lines:
            parts.append(_wrap(gap_lines))
        return '\n'.join(part for part in parts if part)

    @staticmethod
    def _page_js_config(fingerprint: FingerprintConfig) -> FingerprintConfig:
        """Shape the profile for ``build_fingerprint_js`` on Gecko.

        ``user_agent`` is dropped so the builder emits the explicit ``navigator``
        fields (on Chromium those are native side effects of the UA override, on
        Firefox they are not). ``network_connection`` and
        ``hardware.device_memory`` are dropped because the APIs do not exist in
        Firefox. ``client_hints`` is dropped because Firefox has no
        ``navigator.userAgentData``.
        """
        page_config = fingerprint.copy()
        page_config.pop('user_agent', None)
        page_config.pop('network_connection', None)
        page_config.pop('client_hints', None)
        if 'hardware' in page_config:
            hardware = page_config['hardware'].copy()
            hardware.pop('device_memory', None)
            page_config['hardware'] = hardware
        return page_config

    def _gecko_gap_lines(self, fingerprint: FingerprintConfig) -> list[str]:
        """JS getters for the signals neither BiDi nor the shared builder covers on Gecko."""
        lines: list[str] = []
        hardware_concurrency = fingerprint.get('hardware', {}).get('hardware_concurrency')
        if hardware_concurrency is not None:
            lines.append(f'_defG(NP, "hardwareConcurrency", {hardware_concurrency});')
        languages = fingerprint.get('locale', {}).get('languages', [])
        if len(languages) > 1:
            lines.append(f'_defG(NP, "languages", Object.freeze({json.dumps(languages)}));')
        if 'user_agent' in fingerprint:
            lines.extend(self._identity_lines(fingerprint))
        return lines

    @staticmethod
    def _identity_lines(fingerprint: FingerprintConfig) -> list[str]:
        """Derive ``platform`` / ``appVersion`` / ``oscpu`` from the User-Agent.

        Firefox's ``setUserAgentOverride`` leaves the three untouched, so a Windows
        User-Agent on a macOS host would still report ``MacIntel`` /
        ``5.0 (Macintosh)`` / ``Intel Mac OS X 10.15``. Explicit ``navigator``
        fields win; ``appVersion`` and ``oscpu`` follow Gecko's own conventions
        (``5.0 (Windows)``, ``Windows NT 10.0; Win64; x64``) and are derived for
        desktop User-Agents only.
        """
        user_agent = fingerprint['user_agent']
        navigator = fingerprint.get('navigator', {})
        lines: list[str] = []
        if 'platform' not in navigator:
            platform = UserAgentParser.parse(user_agent).platform
            lines.append(f'_defG(NP, "platform", {json.dumps(platform)});')
        tokens = _ua_platform_tokens(user_agent)
        if 'app_version' not in navigator:
            app_version = _gecko_app_version(tokens)
            if app_version:
                lines.append(f'_defG(NP, "appVersion", {json.dumps(app_version)});')
        oscpu = _gecko_oscpu(tokens)
        if oscpu:
            lines.append(f'if ("oscpu" in navigator) _defG(NP, "oscpu", {json.dumps(oscpu)});')
        return lines

    async def _install_preload_script(self, js: str) -> None:
        """Replace the tab's fingerprint preload script and run it in the current document."""
        if self._preload_script_id is not None:
            await self._send(ScriptCommands.remove_preload_script(self._preload_script_id))
            self._preload_script_id = None
        if not js:
            return
        context = self._tab._context_id
        response = await self._send(
            ScriptCommands.add_preload_script(
                function_declaration=f'() => {{\n{js}\n}}', contexts=[context]
            )
        )
        self._preload_script_id = response['result']['script']
        await self._send(
            ScriptCommands.evaluate(
                expression=js, target=ContextTarget(context=context), await_promise=False
            )
        )


def _ua_platform_tokens(user_agent: str) -> list[str]:
    """Split the first parenthesised User-Agent segment into its ``;`` tokens."""
    match = _UA_PLATFORM_SEGMENT.search(user_agent)
    if match is None:
        return []
    return [token.strip() for token in match.group(1).split(';') if token.strip()]


def _gecko_app_version(tokens: list[str]) -> str | None:
    """Gecko ``navigator.appVersion`` for a desktop UA: ``5.0 (Windows|Macintosh|X11)``."""
    if not tokens:
        return None
    first = tokens[0]
    if first.startswith('Windows'):
        return '5.0 (Windows)'
    if first in _GECKO_DESKTOP_TOKENS:
        return f'5.0 ({first})'
    return None


def _gecko_oscpu(tokens: list[str]) -> str | None:
    """Gecko ``navigator.oscpu`` for a desktop UA.

    Windows keeps every token before ``rv:`` (``Windows NT 10.0; Win64; x64``);
    macOS and X11 report the OS/CPU token alone (``Intel Mac OS X 10.15``,
    ``Linux x86_64``), which is the last token before ``rv:``.
    """
    if not tokens:
        return None
    body = [token for token in tokens if not token.startswith('rv:')]
    first = body[0] if body else ''
    if first.startswith('Windows'):
        return '; '.join(body)
    if first in _GECKO_DESKTOP_TOKENS and len(body) > 1:
        return body[-1]
    return None
