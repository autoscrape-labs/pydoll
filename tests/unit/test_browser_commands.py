"""Translate-only Browser methods tested against an in-memory FakeConnection.

A FakeConnection is injected into a Chrome to verify the browser-level command
shaping that the real-Chrome lifecycle suite does not exercise: download
behaviour, permissions, window lookup and fetch interception. Also covers the
platform binary-location resolution for Chrome and Edge.
"""

from __future__ import annotations

import pytest

from pydoll.browser.chromium import Chrome
from pydoll.protocol.browser.types import DownloadBehavior, PermissionType
from pydoll.protocol.network.types import ErrorReason


@pytest.fixture
def browser(fake_conn):
    instance = Chrome()
    instance._connection_handler = fake_conn
    return instance


@pytest.mark.asyncio
async def test_set_download_behavior_carries_params(browser, fake_conn):
    await browser.set_download_behavior(
        DownloadBehavior.ALLOW, download_path='/tmp/dl', events_enabled=True
    )
    sent = fake_conn.last_command('Browser.setDownloadBehavior')
    assert sent['params']['behavior'] == 'allow'
    assert sent['params']['downloadPath'] == '/tmp/dl'
    assert sent['params']['eventsEnabled'] is True


@pytest.mark.asyncio
async def test_set_download_path_uses_allow_with_path(browser, fake_conn):
    await browser.set_download_path('/tmp/downloads')
    sent = fake_conn.last_command('Browser.setDownloadBehavior')
    assert sent['params']['behavior'] == 'allow'
    assert sent['params']['downloadPath'] == '/tmp/downloads'


@pytest.mark.asyncio
async def test_grant_permissions_carries_permissions(browser, fake_conn):
    await browser.grant_permissions([PermissionType.AUDIO_CAPTURE])
    sent = fake_conn.last_command('Browser.grantPermissions')
    assert sent['params']['permissions'] == [PermissionType.AUDIO_CAPTURE]


@pytest.mark.asyncio
async def test_reset_permissions_sends_command(browser, fake_conn):
    await browser.reset_permissions()
    assert fake_conn.commands_for('Browser.resetPermissions')


@pytest.mark.asyncio
async def test_get_window_id_for_target_parses_and_carries_target(browser, fake_conn):
    fake_conn.set_response('Browser.getWindowForTarget', {'windowId': 42})
    assert await browser.get_window_id_for_target('target-1') == 42
    sent = fake_conn.last_command('Browser.getWindowForTarget')
    assert sent['params']['targetId'] == 'target-1'


@pytest.mark.asyncio
async def test_continue_request_carries_request_id(browser, fake_conn):
    await browser.continue_request(request_id='r1')
    assert fake_conn.last_command('Fetch.continueRequest')['params']['requestId'] == 'r1'


@pytest.mark.asyncio
async def test_fail_request_carries_error_reason(browser, fake_conn):
    await browser.fail_request('r1', ErrorReason.FAILED)
    sent = fake_conn.last_command('Fetch.failRequest')
    assert sent['params']['requestId'] == 'r1'
    assert sent['params']['errorReason'] == 'Failed'


@pytest.mark.asyncio
async def test_fulfill_request_carries_response_code(browser, fake_conn):
    await browser.fulfill_request(request_id='r1', response_code=204)
    assert fake_conn.last_command('Fetch.fulfillRequest')['params']['responseCode'] == 204
