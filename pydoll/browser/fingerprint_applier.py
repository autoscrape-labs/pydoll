from __future__ import annotations

import logging
from contextlib import suppress
from typing import TYPE_CHECKING, Awaitable, Callable, Optional

from pydoll.commands import (
    EmulationCommands,
    PageCommands,
    RuntimeCommands,
    TargetCommands,
)
from pydoll.connection import ConnectionHandler
from pydoll.exceptions import (
    CommandExecutionTimeout,
    FingerprintContextConflict,
    WebSocketConnectionClosed,
)
from pydoll.protocol.emulation.types import (
    MediaFeature,
    ScreenOrientation,
    ScreenOrientationType,
)
from pydoll.protocol.target.events import TargetEvent
from pydoll.protocol.target.types import FilterEntry
from pydoll.utils import UserAgentParser
from pydoll.utils.fingerprint_builder import build_fingerprint_js, build_fingerprint_worker_js

if TYPE_CHECKING:
    from pydoll.browser.tab import Tab
    from pydoll.protocol.base import Command
    from pydoll.protocol.emulation.methods import GetScreenInfosResponse
    from pydoll.protocol.emulation.types import WorkAreaInsets
    from pydoll.protocol.fingerprint.types import (
        FingerprintConfig,
        MediaFeaturesFingerprint,
        ScreenFingerprint,
    )
    from pydoll.protocol.target.methods import GetTargetInfoResponse
    from pydoll.utils.user_agent_parser import ParsedUserAgent

logger = logging.getLogger(__name__)

# Sentinel meaning "no browser-context scoping" for worker handlers. It is
# distinct from ``None``, which is a valid concrete context id a worker can
# carry (the default context).
_NO_WORKER_SCOPE = object()


class FingerprintApplier:
    """Applies a fingerprint profile to a single tab and its worker targets.

    Owns the whole fingerprint-injection subsystem so ``Tab`` does not: the CDP
    ``Emulation`` overrides, the ``addScriptToEvaluateOnNewDocument`` JavaScript
    injection, and the auto-attach machinery that replays the same identity on
    dedicated, shared and service workers. A ``Tab`` composes an instance of this
    and ``Tab.apply_fingerprint`` is a thin wrapper delegating to :meth:`apply`.
    """

    # Per-session worker CDP commands use a short timeout so a slow or
    # unresponsive worker target can never block resuming the worker.
    _WORKER_COMMAND_TIMEOUT = 5

    _ORIENTATION_CDP_MAP: dict[str, ScreenOrientationType] = {
        'portrait-primary': ScreenOrientationType.PORTRAIT_PRIMARY,
        'portrait-secondary': ScreenOrientationType.PORTRAIT_SECONDARY,
        'landscape-primary': ScreenOrientationType.LANDSCAPE_PRIMARY,
        'landscape-secondary': ScreenOrientationType.LANDSCAPE_SECONDARY,
    }

    def __init__(self, tab: 'Tab') -> None:
        self._tab = tab
        self._applied: Optional[FingerprintConfig] = None

    async def apply(
        self, fingerprint: FingerprintConfig, cross_origin_iframes: bool = True
    ) -> None:
        """Apply a browser fingerprint profile to the tab.

        Overrides browser identity signals via CDP commands and JavaScript
        injection. Must be called before navigating to any page for full
        effect, since JS overrides are registered via
        ``Page.addScriptToEvaluateOnNewDocument``.

        CDP-level overrides (applied immediately):
            - User-Agent string + Client Hints (``Emulation.setUserAgentOverride``)
            - Timezone (``Emulation.setTimezoneOverride``)
            - Geolocation (``Emulation.setGeolocationOverride``)
            - Device metrics / screen (``Emulation.setDeviceMetricsOverride``)
            - Locale (``Emulation.setLocaleOverride``)
            - CSS media features / color-gamut (``Emulation.setEmulatedMedia``)

        JS-level overrides (injected on every new document):
            - Navigator properties, hardware, WebGL, screen extras,
              plugins, media devices, audio, speech, locale/languages

        The same overrides are also replayed on Web Worker targets, which have
        their own ``WorkerNavigator`` and would otherwise leak the real
        User-Agent, platform, ``hardwareConcurrency``, ``deviceMemory`` and
        languages.

        Args:
            fingerprint: Fingerprint configuration. Only specified fields
                are overridden; unspecified fields keep real browser values.
            cross_origin_iframes: When true (default), the identity is also
                replayed into every cross-site iframe (OOPIF) so the fingerprint
                stays coherent across process boundaries. Set false to cover only
                the top page, same-origin frames, and workers.
        """
        tab = self._tab
        if self._applied == fingerprint:
            logger.debug('Fingerprint already applied to this tab; skipping (idempotent)')
            return

        logger.info('Applying fingerprint profile to tab')

        context_already_set = self._register_context(fingerprint)

        if not tab.page_events_enabled:
            await tab.enable_page_events()

        accept_language = self._build_accept_language(fingerprint)

        parsed = (
            UserAgentParser.parse(fingerprint['user_agent'])
            if 'user_agent' in fingerprint
            else None
        )

        mobile = fingerprint.get('mobile')
        if mobile is None:
            mobile = parsed.user_agent_metadata['mobile'] if parsed else False

        if parsed is not None:
            self._warn_on_user_agent_option_conflict(fingerprint['user_agent'])
            await self._apply_user_agent(parsed, accept_language, mobile=mobile)
        if 'timezone' in fingerprint:
            await tab._execute_command(
                EmulationCommands.set_timezone_override(fingerprint['timezone'])
            )
        if 'geolocation' in fingerprint:
            geo = fingerprint['geolocation']
            await tab._execute_command(
                EmulationCommands.set_geolocation_override(
                    latitude=geo['latitude'],
                    longitude=geo['longitude'],
                    accuracy=geo.get('accuracy'),
                )
            )
        if 'screen' in fingerprint:
            await self._apply_device_metrics(fingerprint['screen'], mobile=mobile)
            await self._apply_headless_screen(fingerprint['screen'])
        if 'hardware' in fingerprint and 'hardware_concurrency' in fingerprint['hardware']:
            await tab._execute_command(
                EmulationCommands.set_hardware_concurrency_override(
                    fingerprint['hardware']['hardware_concurrency']
                )
            )
        if 'locale' in fingerprint:
            languages = fingerprint['locale']['languages']
            if languages:
                await tab._execute_command(
                    EmulationCommands.set_locale_override(languages[0].replace('-', '_'))
                )
        if 'media_features' in fingerprint:
            await self._apply_media_features(fingerprint['media_features'])

        identity_ua = parsed.reduced_user_agent if parsed else ''
        identity_platform = parsed.platform if parsed else ''
        js = build_fingerprint_js(fingerprint, user_agent=identity_ua, platform=identity_platform)
        if js:
            await tab._execute_command(
                PageCommands.add_script_to_evaluate_on_new_document(
                    source=js,
                    run_immediately=True,
                )
            )

        await self._setup_worker_override(
            fingerprint,
            parsed,
            accept_language,
            mobile=mobile,
            setup_browser_scope=not context_already_set,
            cross_origin_iframes=cross_origin_iframes,
            page_js=js,
        )
        self._applied = fingerprint
        logger.info('Fingerprint profile applied')

    async def _apply_media_features(self, media_features: MediaFeaturesFingerprint) -> None:
        """Emulate the configured CSS media features via ``setEmulatedMedia``.

        Applied natively so ``window.matchMedia`` stays genuine. Only the
        features Chrome can emulate through CDP have a config field; unset
        features keep the browser's real values.
        """
        command = self._media_features_command(media_features)
        if command is not None:
            await self._tab._execute_command(command)

    def _warn_on_user_agent_option_conflict(self, fingerprint_user_agent: str) -> None:
        """Warn when a ``--user-agent`` option contradicts the fingerprint UA.

        The options-based ``--user-agent`` handling
        (``_apply_user_agent_override`` / ``_setup_worker_user_agent_override``)
        registers its own worker ``ATTACHED_TO_TARGET`` handlers. Combining it
        with a fingerprint carrying a *different* User-Agent stacks a second,
        conflicting worker override, so the two disagree on what a worker reports.
        The fingerprint owns the page User-Agent, but the option handler may still
        fire on workers, so setting both is a misconfiguration.
        """
        options_user_agent = self._tab._browser._get_user_agent_from_options()
        if options_user_agent and options_user_agent != fingerprint_user_agent:
            logger.warning(
                'A --user-agent browser option is set and differs from the fingerprint '
                "User-Agent; don't combine --user-agent with apply_fingerprint (the "
                'fingerprint owns the User-Agent, but the option may still override workers).'
            )

    def _register_context(self, fingerprint: FingerprintConfig) -> bool:
        """Register a fingerprint for this tab's browser context.

        Returns whether the context was already registered (so browser-scoped
        worker setup can be skipped as a no-op). Raises if a *different*
        fingerprint is already applied to the context.

        Raises:
            FingerprintContextConflict: If the context already carries a
                different fingerprint (its service/shared workers are shared
                across tabs, so a context holds a single identity).
        """
        registry = self._tab._browser._context_fingerprints
        context_id = self._tab._browser_context_id
        existing = registry.get(context_id)
        if existing is not None and existing != fingerprint:
            raise FingerprintContextConflict()
        already_set = context_id in registry
        registry[context_id] = fingerprint
        return already_set

    async def _setup_worker_override(
        self,
        fingerprint: FingerprintConfig,
        parsed: Optional['ParsedUserAgent'],
        accept_language: Optional[str],
        mobile: bool,
        setup_browser_scope: bool = True,
        cross_origin_iframes: bool = True,
        page_js: str = '',
    ) -> None:
        """Auto-attach to Web Workers (and optionally OOPIFs) and replay the fingerprint.

        Workers keep their own ``WorkerNavigator``: CDP overrides scoped to the
        page session and ``addScriptToEvaluateOnNewDocument`` do not reach them,
        so each worker is attached (paused on start), overridden, then resumed.

        Dedicated workers are children of the page target and are driven over the
        tab connection, so they are always set up (once per tab). Service and
        shared workers are browser-scoped targets whose sessions only answer over
        the browser connection; that handler is registered once per browser
        context (``setup_browser_scope``), scoped to this context, to avoid
        stacking a handler for every tab in the same context.

        A cross-site iframe (OOPIF) is also a child of the page target, so it
        attaches over the tab connection too. When ``cross_origin_iframes`` is set,
        the tab handler additionally replays the full identity on each OOPIF
        session (see :meth:`_apply_oopif_session`). The single tab handler branches
        by target type and resumes last, so there is no race with the worker path.
        """
        tab = self._tab
        worker_js = build_fingerprint_worker_js(
            fingerprint,
            platform=parsed.platform if parsed else '',
            user_agent=parsed.reduced_user_agent if parsed else '',
        )
        hardware_concurrency = fingerprint.get('hardware', {}).get('hardware_concurrency')

        tab_conn = tab._connection_handler
        tab_handler = self._build_worker_handler(
            tab_conn,
            {'worker'},
            parsed,
            accept_language,
            mobile,
            hardware_concurrency,
            worker_js,
            include_iframes=cross_origin_iframes,
            fingerprint=fingerprint,
            page_js=page_js,
        )
        await tab.on(TargetEvent.ATTACHED_TO_TARGET, tab_handler)
        tab_filters = [FilterEntry(type='worker')]
        if cross_origin_iframes:
            tab_filters.append(FilterEntry(type='iframe'))
        await tab._execute_command(
            TargetCommands.set_auto_attach(
                auto_attach=True,
                wait_for_debugger_on_start=True,
                flatten=True,
                filter=tab_filters,
            )
        )

        if not setup_browser_scope:
            return

        scope_context_id = await self._resolve_browser_context_id()
        browser_conn = tab._browser._connection_handler
        browser_handler = self._build_worker_handler(
            browser_conn,
            {'service_worker', 'shared_worker'},
            parsed,
            accept_language,
            mobile,
            hardware_concurrency,
            worker_js,
            scope_context_id=scope_context_id,
        )
        callback_id = await tab._browser.on(TargetEvent.ATTACHED_TO_TARGET, browser_handler)
        tab._browser._context_worker_callbacks[tab._browser_context_id] = callback_id
        await browser_conn.execute_command(
            TargetCommands.set_auto_attach(
                auto_attach=True,
                wait_for_debugger_on_start=True,
                flatten=True,
                filter=[FilterEntry(type='service_worker'), FilterEntry(type='shared_worker')],
            )
        )

    async def _resolve_browser_context_id(self) -> object:
        """Resolve this tab's concrete browser context id for scoping workers.

        ``tab._browser_context_id`` is ``None`` for the default context, but a
        worker's ``targetInfo.browserContextId`` carries the concrete
        default-context id, so scoping by the stored ``None`` would never match
        and every default-context service/shared worker would be skipped (leaking
        the real identity). This reads the concrete id from the tab's own target.
        Falls back to ``_NO_WORKER_SCOPE`` (no scoping) if it cannot be resolved,
        so workers are still overridden rather than skipped.
        """
        tab = self._tab
        if not tab._target_id:
            return _NO_WORKER_SCOPE
        try:
            response: GetTargetInfoResponse = await tab._execute_command(
                TargetCommands.get_target_info(tab._target_id)
            )
            return response['result']['targetInfo'].get('browserContextId', _NO_WORKER_SCOPE)
        except (CommandExecutionTimeout, WebSocketConnectionClosed) as exc:
            logger.debug('Could not resolve browser context id for worker scope: %s', exc)
            return _NO_WORKER_SCOPE
        except KeyError as exc:
            logger.debug('Unexpected getTargetInfo response, missing key %s', exc)
            return _NO_WORKER_SCOPE

    def _build_worker_handler(
        self,
        connection: ConnectionHandler,
        worker_types: set[str],
        parsed: Optional['ParsedUserAgent'],
        accept_language: Optional[str],
        mobile: bool,
        hardware_concurrency: Optional[int],
        worker_js: str,
        scope_context_id: object = _NO_WORKER_SCOPE,
        include_iframes: bool = False,
        fingerprint: Optional['FingerprintConfig'] = None,
        page_js: str = '',
    ) -> Callable[[dict], Awaitable[None]]:
        """Build an attachedToTarget handler that replays the fingerprint on workers.

        The returned coroutine reapplies the User-Agent / hardwareConcurrency CDP
        overrides and injects the worker fingerprint JS on each attached worker
        session whose type is in ``worker_types``, over ``connection``, then always
        resumes targets paused via ``waitForDebuggerOnStart`` so a worker never
        hangs on attach.

        ``scope_context_id`` scopes a browser-wide handler to a single browser
        context: service and shared workers are browser-global targets, so a
        handler registered on the browser connection sees every context's workers.
        When set (including to ``None`` for the default context), the fingerprint
        is applied only to workers whose ``browserContextId`` matches, so
        different tabs in different contexts get their own identity without
        cross-contamination. The worker is still resumed regardless of match, so a
        worker from another context never hangs. Left unset (``_NO_WORKER_SCOPE``)
        for tab-scoped dedicated workers, which are already isolated to this tab.
        """

        async def on_worker_attached(event: dict) -> None:
            params = event['params']
            session_id = params['sessionId']
            try:
                target_info = params['targetInfo']
                in_scope = (
                    scope_context_id is _NO_WORKER_SCOPE
                    or target_info.get('browserContextId') == scope_context_id
                )
                if target_info['type'] in worker_types and in_scope:
                    await self._apply_worker_session(
                        connection,
                        session_id,
                        parsed,
                        accept_language,
                        mobile,
                        hardware_concurrency,
                        worker_js,
                    )
                elif include_iframes and target_info['type'] == 'iframe':
                    if fingerprint is not None:
                        await self._apply_oopif_session(
                            connection,
                            session_id,
                            parsed,
                            accept_language,
                            mobile,
                            fingerprint,
                            page_js,
                        )
            except (CommandExecutionTimeout, WebSocketConnectionClosed, KeyError) as exc:
                logger.debug('Skipped fingerprint on attached session %s: %s', session_id, exc)
            finally:
                if params.get('waitingForDebugger'):
                    resume = RuntimeCommands.run_if_waiting_for_debugger()
                    resume['sessionId'] = session_id
                    with suppress(CommandExecutionTimeout, WebSocketConnectionClosed):
                        await connection.execute_command(
                            resume, timeout=self._WORKER_COMMAND_TIMEOUT
                        )

        return on_worker_attached

    async def _apply_worker_session(
        self,
        connection: ConnectionHandler,
        session_id: str,
        parsed: Optional['ParsedUserAgent'],
        accept_language: Optional[str],
        mobile: bool,
        hardware_concurrency: Optional[int],
        worker_js: str,
    ) -> None:
        """Replay UA / hardwareConcurrency / JS overrides on a single worker session."""
        commands: list[Command] = []
        if parsed is not None:
            commands.append(self._user_agent_command(parsed, accept_language, mobile))
        if hardware_concurrency is not None:
            commands.append(
                EmulationCommands.set_hardware_concurrency_override(hardware_concurrency)
            )
        if worker_js:
            commands.append(RuntimeCommands.evaluate(expression=worker_js))
        for command in commands:
            command['sessionId'] = session_id
            await connection.execute_command(command, timeout=self._WORKER_COMMAND_TIMEOUT)

    async def _apply_oopif_session(
        self,
        connection: ConnectionHandler,
        session_id: str,
        parsed: Optional['ParsedUserAgent'],
        accept_language: Optional[str],
        mobile: bool,
        fingerprint: FingerprintConfig,
        page_js: str,
    ) -> None:
        """Replay the full identity on a single cross-site iframe (OOPIF) session.

        A cross-site iframe runs in its own process, so the page-session Emulation
        overrides and the page ``addScriptToEvaluateOnNewDocument`` never reach it.
        This reapplies the whole override set on the iframe's own session, then the
        page JS after enabling the Page domain (required for
        ``addScriptToEvaluateOnNewDocument`` to take effect on this session). The
        caller resumes the paused target afterwards, so the overrides are in place
        before the iframe runs a line. Every command is sent on ``connection`` (the
        one that received ``attachedToTarget``), since a flattened session answers
        only there.
        """
        commands: list[Command] = []
        if parsed is not None:
            commands.append(self._user_agent_command(parsed, accept_language, mobile))
        if 'timezone' in fingerprint:
            commands.append(EmulationCommands.set_timezone_override(fingerprint['timezone']))
        languages = fingerprint.get('locale', {}).get('languages')
        if languages:
            commands.append(EmulationCommands.set_locale_override(languages[0].replace('-', '_')))
        if 'geolocation' in fingerprint:
            geo = fingerprint['geolocation']
            commands.append(
                EmulationCommands.set_geolocation_override(
                    latitude=geo['latitude'],
                    longitude=geo['longitude'],
                    accuracy=geo.get('accuracy'),
                )
            )
        hardware_concurrency = fingerprint.get('hardware', {}).get('hardware_concurrency')
        if hardware_concurrency is not None:
            commands.append(
                EmulationCommands.set_hardware_concurrency_override(hardware_concurrency)
            )
        if 'screen' in fingerprint:
            commands.append(self._device_metrics_command(fingerprint['screen'], mobile))
        if 'media_features' in fingerprint:
            media_command = self._media_features_command(fingerprint['media_features'])
            if media_command is not None:
                commands.append(media_command)
        commands.append(PageCommands.enable())
        if page_js:
            commands.append(
                PageCommands.add_script_to_evaluate_on_new_document(
                    source=page_js, run_immediately=True
                )
            )
        for command in commands:
            command['sessionId'] = session_id
            await connection.execute_command(command, timeout=self._WORKER_COMMAND_TIMEOUT)

    @staticmethod
    def _user_agent_command(
        parsed: 'ParsedUserAgent', accept_language: Optional[str], mobile: bool
    ) -> 'Command':
        """Build the ``setUserAgentOverride`` command for a parsed User-Agent."""
        metadata = parsed.user_agent_metadata
        metadata['mobile'] = mobile
        return EmulationCommands.set_user_agent_override(
            user_agent=parsed.reduced_user_agent,
            accept_language=accept_language,
            platform=parsed.platform,
            user_agent_metadata=metadata,
        )

    def _device_metrics_command(self, screen: 'ScreenFingerprint', mobile: bool) -> 'Command':
        """Build the ``setDeviceMetricsOverride`` command from screen config.

        When ``inner_width`` / ``inner_height`` are omitted, the layout-size is
        disabled (``0``) so the real window drives ``window.innerWidth`` /
        ``innerHeight`` instead of ``screen.width`` (a headless-like tell). The
        ``screen.width`` / ``screen.height`` overrides are always applied.
        """
        screen_orientation: Optional[ScreenOrientation] = None
        orientation_type = screen.get('orientation_type')
        if orientation_type:
            cdp_type = self._ORIENTATION_CDP_MAP.get(orientation_type)
            if cdp_type:
                screen_orientation = ScreenOrientation(
                    type=cdp_type, angle=screen.get('orientation_angle', 0)
                )
        return EmulationCommands.set_device_metrics_override(
            width=screen.get('inner_width', 0),
            height=screen.get('inner_height', 0),
            device_scale_factor=screen.get('device_pixel_ratio', 0),
            mobile=mobile,
            screen_width=screen['width'],
            screen_height=screen['height'],
            screen_orientation=screen_orientation,
        )

    @staticmethod
    def _media_features_command(
        media_features: 'MediaFeaturesFingerprint',
    ) -> Optional['Command']:
        """Build the ``setEmulatedMedia`` command, or ``None`` when nothing is set."""
        candidates = (
            ('color-gamut', media_features.get('color_gamut')),
            ('forced-colors', media_features.get('forced_colors')),
            ('prefers-color-scheme', media_features.get('prefers_color_scheme')),
            ('prefers-contrast', media_features.get('prefers_contrast')),
            ('prefers-reduced-motion', media_features.get('prefers_reduced_motion')),
            ('prefers-reduced-transparency', media_features.get('prefers_reduced_transparency')),
        )
        features: list[MediaFeature] = [
            MediaFeature(name=name, value=value) for name, value in candidates if value is not None
        ]
        if not features:
            return None
        return EmulationCommands.set_emulated_media(features=features)

    @staticmethod
    def _build_accept_language(fingerprint: FingerprintConfig) -> Optional[str]:
        """Build the Accept-Language value passed to CDP from locale config.

        Returns a plain, unweighted language list (e.g. ``'en-US,en'``). CDP's
        ``Emulation.setUserAgentOverride.acceptLanguage`` computes the ``q`` values
        itself, so a pre-weighted string here yields a malformed header with
        doubled ``q`` values (``en-US,en;q=0.9;q=0.9``) that no real browser emits.
        """
        if 'locale' not in fingerprint:
            return None
        languages = fingerprint['locale'].get('languages', [])
        if not languages:
            return None
        return ','.join(languages)

    async def _apply_user_agent(
        self,
        parsed: 'ParsedUserAgent',
        accept_language: Optional[str] = None,
        mobile: bool = False,
    ) -> None:
        """Apply user-agent override from an already-parsed User-Agent.

        Exposes the reduced UA (``Chrome/MAJOR.0.0.0``) as ``navigator.userAgent``
        and the ``User-Agent`` header, matching what real Chrome sends after UA
        reduction. The true build number survives in
        ``metadata['fullVersionList']`` (``Sec-CH-UA-Full-Version-List``), so all
        layers stay mutually consistent.

        ``Emulation.setUserAgentOverride`` sets ``navigator.platform``,
        ``navigator.appVersion`` and ``navigator.vendor`` natively from the
        overridden UA / platform, so no JavaScript getter is injected for them
        (a JS getter would replace the genuinely native one and become
        detectable under ``toString`` introspection).

        Args:
            parsed: Parsed User-Agent metadata (from ``UserAgentParser.parse``).
            accept_language: Accept-Language header value.
            mobile: Whether to emulate a mobile device. Propagated to
                Client Hints (``Sec-CH-UA-Mobile``).
        """
        await self._tab._execute_command(
            self._user_agent_command(parsed, accept_language, mobile)
        )

    async def _apply_device_metrics(self, screen: ScreenFingerprint, mobile: bool = False) -> None:
        """Apply device metrics override from screen fingerprint config.

        When ``inner_width`` / ``inner_height`` are omitted, the layout-size
        (``width`` / ``height``) override is disabled by passing ``0`` so the real
        window drives ``window.innerWidth`` / ``innerHeight``, instead of forcing
        them to the full screen size (which yields ``innerWidth == screen.width``,
        a headless-like tell). The ``screen.width`` / ``screen.height`` overrides
        (``screen_width`` / ``screen_height``) are applied regardless.

        Args:
            screen: Screen fingerprint configuration.
            mobile: Whether to emulate a mobile device.
        """
        await self._tab._execute_command(self._device_metrics_command(screen, mobile))

    async def _apply_headless_screen(self, screen: 'ScreenFingerprint') -> None:
        """Match the browser-global headless virtual screen to the fingerprint.

        Headless Chrome has a single hardcoded virtual screen (800x600,
        colorDepth 24, no work area). ``setDeviceMetricsOverride`` is session
        scoped, so cross-origin iframes (OOPIFs) never see it and read that raw
        800x600 / ``availTop 0`` screen, contradicting the page's own overridden
        ``window.screen`` and betraying headless. ``Emulation.updateScreen``
        targets the browser-global device, so every frame - top page and OOPIFs -
        reads one coherent desktop. Unsupported outside headless, so this no-ops
        there (guarded, and defensive against an error response).

        Two constraints are inherent to the headless one-screen model:

        - The device is browser-global. Applying two screen-distinct
          fingerprints to one headless browser (even in separate contexts) makes
          the last one win globally, so an earlier tab's OOPIFs read the other
          identity's screen. Use one browser process per screen-distinct identity.
        - The virtual screen only accepts an INTEGER device pixel ratio. A
          fractional dpr (Windows display scaling, mobile) is rounded for the
          screen, so size / colorDepth / work-area stay coherent in OOPIFs while
          the OOPIF ``devicePixelRatio`` becomes that rounded value; the top page
          keeps the exact dpr via ``setDeviceMetricsOverride``.

        Sizes and work-area insets are physical pixels (CSS = physical / dpr).
        """
        if not self._is_headless():
            return
        tab = self._tab
        with suppress(CommandExecutionTimeout, WebSocketConnectionClosed):
            response: GetScreenInfosResponse = await tab._execute_command(
                EmulationCommands.get_screen_infos()
            )
            screen_id = self._primary_screen_id(response)
            if screen_id is None:
                return
            dpr = screen.get('device_pixel_ratio') or 1.0
            screen_dpr = max(1, round(dpr))
            await tab._execute_command(
                EmulationCommands.update_screen(
                    screen_id,
                    width=screen['width'] * screen_dpr,
                    height=screen['height'] * screen_dpr,
                    device_pixel_ratio=screen_dpr,
                    color_depth=screen.get('color_depth'),
                    work_area_insets=self._work_area_insets(screen, screen_dpr),
                )
            )

    def _is_headless(self) -> bool:
        """Whether this tab's browser was launched headless."""
        options = getattr(self._tab._browser, 'options', None)
        if options is None:
            return False
        if getattr(options, 'headless', False):
            return True
        arguments = getattr(options, 'arguments', None) or []
        return any('--headless' in argument for argument in arguments)

    @staticmethod
    def _primary_screen_id(response: 'GetScreenInfosResponse') -> Optional[str]:
        """Pick the primary screen id from a getScreenInfos response.

        Returns ``None`` when the response carries no screens (e.g. an error
        response returned outside headless), so the caller skips the update.
        """
        try:
            screens = response['result']['screenInfos']
        except (KeyError, TypeError):
            return None
        if not screens:
            return None
        for candidate in screens:
            if candidate.get('isPrimary'):
                return candidate.get('id')
        return screens[0].get('id')

    @staticmethod
    def _work_area_insets(screen: 'ScreenFingerprint', dpr: int) -> Optional['WorkAreaInsets']:
        """Build physical-pixel work-area insets from the fingerprint's avail_*.

        The vertical gap ``height - avail_height`` is reserved at ``avail_top``
        (menu bar) with the remainder at the bottom (dock); the horizontal gap
        defaults entirely to the right of ``avail_left``. Each offset is clamped to
        ``[0, gap]``, so an ``avail_top`` without a matching ``avail_height`` cannot
        reserve absent space, and a negative ``avail_top``/``avail_left`` cannot
        produce a negative inset. Returns ``None`` when there is no gap (nothing to
        reserve).
        """
        width, height = screen['width'], screen['height']
        vertical_gap = max(0, height - screen.get('avail_height', height))
        horizontal_gap = max(0, width - screen.get('avail_width', width))
        top = max(0, min(screen.get('avail_top', vertical_gap), vertical_gap))
        left = max(0, min(screen.get('avail_left', 0), horizontal_gap))
        insets: 'WorkAreaInsets' = {
            'top': top * dpr,
            'bottom': (vertical_gap - top) * dpr,
            'left': left * dpr,
            'right': (horizontal_gap - left) * dpr,
        }
        return insets if any(insets.values()) else None
