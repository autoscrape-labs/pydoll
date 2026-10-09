"""BiDiTab.apply_fingerprint against an in-memory FakeBiDiConnection.

Asserts the exact WebDriver BiDi commands the Firefox fingerprint applier sends
for each profile section (native-first), the content of the preload script that
carries the JavaScript layer, and the touch fallback when Firefox answers
``unknown command``. The observable effect on a real page is covered by
tests/bidi/integration/test_bidi_fingerprint_integration.py.
"""

from __future__ import annotations

import pytest

from pydoll.exceptions import CommandFailed

WINDOWS_UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:157.0) Gecko/20100101 Firefox/157.0'
MAC_UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:157.0) Gecko/20100101 Firefox/157.0'


def _full_profile() -> dict:
    return {
        'user_agent': WINDOWS_UA,
        'hardware': {'hardware_concurrency': 8, 'device_memory': 8, 'max_touch_points': 5},
        'locale': {'languages': ['en-US', 'en']},
        'timezone': 'America/New_York',
        'geolocation': {'latitude': 40.7128, 'longitude': -74.006, 'accuracy': 25},
        'screen': {
            'width': 1920,
            'height': 1080,
            'avail_height': 1040,
            'inner_width': 1600,
            'inner_height': 900,
            'device_pixel_ratio': 1.25,
            'orientation_type': 'landscape-primary',
        },
        'network_connection': {'effective_type': '4g'},
        'client_hints': {'platform_version': '15.0.0'},
    }


def _preload_source(fake_bidi_conn) -> str:
    return fake_bidi_conn.last_command('script.addPreloadScript')['params']['functionDeclaration']


@pytest.mark.asyncio
async def test_native_overrides_are_scoped_to_the_tab_context(fake_bidi_conn, fake_bidi_tab):
    fake_bidi_conn.set_result('script.addPreloadScript', {'script': 'preload-1'})
    await fake_bidi_tab.apply_fingerprint(_full_profile())

    contexts = ['fake-context']
    assert fake_bidi_conn.last_command('emulation.setUserAgentOverride')['params'] == {
        'userAgent': WINDOWS_UA,
        'contexts': contexts,
    }
    assert fake_bidi_conn.last_command('emulation.setLocaleOverride')['params'] == {
        'locale': 'en-US',
        'contexts': contexts,
    }
    assert fake_bidi_conn.last_command('emulation.setTimezoneOverride')['params'] == {
        'timezone': 'America/New_York',
        'contexts': contexts,
    }
    assert fake_bidi_conn.last_command('emulation.setGeolocationOverride')['params'] == {
        'coordinates': {'latitude': 40.7128, 'longitude': -74.006, 'accuracy': 25},
        'contexts': contexts,
    }
    assert fake_bidi_conn.last_command('emulation.setScreenSettingsOverride')['params'] == {
        'screenArea': {'width': 1920, 'height': 1080},
        'contexts': contexts,
    }
    assert fake_bidi_conn.last_command('emulation.setScreenOrientationOverride')['params'] == {
        'screenOrientation': {'natural': 'landscape', 'type': 'landscape-primary'},
        'contexts': contexts,
    }
    assert fake_bidi_conn.last_command('browsingContext.setViewport')['params'] == {
        'context': 'fake-context',
        'viewport': {'width': 1600, 'height': 900},
        'devicePixelRatio': 1.25,
    }
    assert fake_bidi_conn.last_command('emulation.setTouchOverride')['params'] == {
        'maxTouchPoints': 5,
        'contexts': contexts,
    }


@pytest.mark.asyncio
async def test_preload_script_carries_the_js_layer_and_gecko_gaps(fake_bidi_conn, fake_bidi_tab):
    fake_bidi_conn.set_result('script.addPreloadScript', {'script': 'preload-1'})
    await fake_bidi_tab.apply_fingerprint(_full_profile())

    params = fake_bidi_conn.last_command('script.addPreloadScript')['params']
    assert params['contexts'] == ['fake-context']
    source = params['functionDeclaration']
    assert source.startswith('() => {')
    assert '_defG(Screen.prototype, "availHeight", 1040);' in source
    assert '_defG(NP, "hardwareConcurrency", 8);' in source
    assert '_defG(NP, "languages", Object.freeze(["en-US", "en"]));' in source
    assert '_defG(NP, "platform", "Win32");' in source
    assert '_defG(NP, "appVersion", "5.0 (Windows)");' in source
    assert 'if ("oscpu" in navigator) _defG(NP, "oscpu", "Windows NT 10.0; Win64; x64");' in source
    assert 'userAgent' not in source
    assert 'deviceMemory' not in source
    assert 'connection' not in source
    assert 'maxTouchPoints' not in source
    evaluated = fake_bidi_conn.last_command('script.evaluate')['params']
    assert evaluated['target'] == {'context': 'fake-context'}
    assert evaluated['expression'] in source


@pytest.mark.asyncio
async def test_touch_falls_back_to_js_when_firefox_lacks_the_command(fake_bidi_conn, fake_bidi_tab):
    fake_bidi_conn.set_result('script.addPreloadScript', {'script': 'preload-1'})
    fake_bidi_conn.set_error(
        'emulation.setTouchOverride', 'unknown command', 'emulation.setTouchOverride'
    )
    await fake_bidi_tab.apply_fingerprint({'hardware': {'max_touch_points': 5}})

    assert len(fake_bidi_conn.commands_for('emulation.setTouchOverride')) == 1
    assert '_defG(NP, "maxTouchPoints", 5);' in _preload_source(fake_bidi_conn)


@pytest.mark.asyncio
async def test_other_native_failures_propagate(fake_bidi_conn, fake_bidi_tab):
    fake_bidi_conn.set_error('emulation.setLocaleOverride', 'invalid argument', 'bad tag')
    with pytest.raises(CommandFailed, match='invalid argument'):
        await fake_bidi_tab.apply_fingerprint({'locale': {'languages': ['en_US']}})
    assert fake_bidi_conn.commands_for('script.addPreloadScript') == []


@pytest.mark.asyncio
async def test_explicit_navigator_fields_win_over_ua_derivation(fake_bidi_conn, fake_bidi_tab):
    fake_bidi_conn.set_result('script.addPreloadScript', {'script': 'preload-1'})
    await fake_bidi_tab.apply_fingerprint({
        'user_agent': MAC_UA,
        'navigator': {'platform': 'MacIntel', 'app_version': '5.0 (Macintosh)'},
    })

    source = _preload_source(fake_bidi_conn)
    assert source.count('"platform"') == 1
    assert '_defG(NP, "platform", "MacIntel");' in source
    assert source.count('"appVersion"') == 1
    assert '_defG(NP, "appVersion", "5.0 (Macintosh)");' in source
    assert 'if ("oscpu" in navigator) _defG(NP, "oscpu", "Intel Mac OS X 10.15");' in source


@pytest.mark.asyncio
async def test_single_language_and_zero_touch_stay_native(fake_bidi_conn, fake_bidi_tab):
    await fake_bidi_tab.apply_fingerprint({
        'locale': {'languages': ['pt-BR']},
        'hardware': {'max_touch_points': 0},
        'timezone': 'America/Sao_Paulo',
    })

    assert fake_bidi_conn.last_command('emulation.setLocaleOverride')['params']['locale'] == 'pt-BR'
    assert fake_bidi_conn.commands_for('emulation.setTouchOverride') == []
    assert fake_bidi_conn.commands_for('script.addPreloadScript') == []
    assert fake_bidi_conn.commands_for('script.evaluate') == []


@pytest.mark.asyncio
async def test_mobile_profile_uses_portrait_as_natural_orientation(fake_bidi_conn, fake_bidi_tab):
    await fake_bidi_tab.apply_fingerprint({
        'mobile': True,
        'screen': {'width': 390, 'height': 844, 'orientation_type': 'portrait-primary'},
    })

    orientation = fake_bidi_conn.last_command('emulation.setScreenOrientationOverride')['params']
    assert orientation['screenOrientation'] == {'natural': 'portrait', 'type': 'portrait-primary'}
    assert fake_bidi_conn.commands_for('browsingContext.setViewport') == []


@pytest.mark.asyncio
async def test_reapply_is_idempotent_and_replaces_the_preload_on_change(
    fake_bidi_conn, fake_bidi_tab
):
    fake_bidi_conn.set_result('script.addPreloadScript', {'script': 'preload-1'})
    profile = {'hardware': {'hardware_concurrency': 4}}
    await fake_bidi_tab.apply_fingerprint(profile)
    await fake_bidi_tab.apply_fingerprint(dict(profile))
    assert len(fake_bidi_conn.commands_for('script.addPreloadScript')) == 1

    fake_bidi_conn.set_result('script.addPreloadScript', {'script': 'preload-2'})
    await fake_bidi_tab.apply_fingerprint({'hardware': {'hardware_concurrency': 16}})
    removed = fake_bidi_conn.last_command('script.removePreloadScript')['params']
    assert removed == {'script': 'preload-1'}
    assert '_defG(NP, "hardwareConcurrency", 16);' in _preload_source(fake_bidi_conn)
    assert len(fake_bidi_conn.commands_for('script.addPreloadScript')) == 2
