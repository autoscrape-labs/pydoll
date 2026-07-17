"""Unit tests for HarRecorder.stop() lifecycle (deterministic, no browser).

stop() must await any in-flight getResponseBody tasks before flushing, remove
its CDP callbacks, and disable network events it turned on. This is exercised
here with a fake tab so the body-await path runs deterministically instead of
racing a real browser's internal finalize against context exit.
"""

from __future__ import annotations

import asyncio

import pytest

from pydoll.browser.requests.har_recorder import HarRecorder


class _FakeTab:
    network_events_enabled = True

    def __init__(self):
        self.removed: list[int] = []
        self.network_disabled = False

    async def remove_callback(self, callback_id):
        self.removed.append(callback_id)

    async def disable_network_events(self):
        self.network_disabled = True


@pytest.mark.asyncio
async def test_stop_awaits_in_flight_body_tasks_and_cleans_up():
    fake_tab = _FakeTab()
    recorder = HarRecorder(tab=fake_tab)
    recorder._network_was_enabled = True
    recorder._callback_ids = [1, 2, 3]

    completed: list[bool] = []

    async def slow_body_fetch():
        await asyncio.sleep(0.02)
        completed.append(True)

    recorder._body_tasks = [asyncio.ensure_future(slow_body_fetch())]

    await recorder.stop()

    assert completed == [True]
    assert recorder._body_tasks == []
    assert fake_tab.removed == [1, 2, 3]
    assert fake_tab.network_disabled is True


@pytest.mark.asyncio
async def test_stop_flushes_in_flight_request_as_pending_entry():
    recorder = HarRecorder(tab=_FakeTab())
    recorder._on_request_will_be_sent({
        'params': {
            'requestId': 'r1',
            'request': {'url': 'http://x/slow', 'method': 'GET', 'headers': {}},
            'type': 'Fetch',
            'wallTime': 1000.0,
            'timestamp': 1.0,
        }
    })

    await recorder.stop()

    assert len(recorder._entries) == 1
    entry = recorder._entries[0]
    assert entry['request']['url'] == 'http://x/slow'
    assert entry['response']['status'] == 0
    assert entry['response']['statusText'] == '(pending)'


class _BodyTab(_FakeTab):
    """Fake tab whose getResponseBody returns empty until a given attempt."""

    def __init__(self, body: str, ready_on_attempt: int):
        super().__init__()
        self._body = body
        self._ready_on_attempt = ready_on_attempt
        self.body_calls = 0

    async def _execute_command(self, command):
        self.body_calls += 1
        if self.body_calls < self._ready_on_attempt:
            return {'result': {'body': '', 'base64Encoded': False}}
        return {'result': {'body': self._body, 'base64Encoded': False}}


@pytest.mark.asyncio
async def test_fetch_response_body_retries_until_body_available():
    """A body arriving a few attempts late (Windows race) is still captured."""
    tab = _BodyTab('Hello from the test server', ready_on_attempt=3)
    recorder = HarRecorder(tab=tab)

    body, is_base64 = await recorder._fetch_response_body('r1', expects_body=True)

    assert body == 'Hello from the test server'
    assert is_base64 is False
    assert tab.body_calls == 3


@pytest.mark.asyncio
async def test_fetch_response_body_no_retry_when_body_not_expected():
    """A legitimately empty body must not incur retries (204/redirect/etc)."""
    tab = _BodyTab('never', ready_on_attempt=99)
    recorder = HarRecorder(tab=tab)

    body, is_base64 = await recorder._fetch_response_body('r1', expects_body=False)

    assert body == ''
    assert tab.body_calls == 1


@pytest.mark.asyncio
async def test_fetch_response_body_gives_up_after_max_attempts():
    """When the body never materializes, fall back to empty without hanging."""
    tab = _BodyTab('never', ready_on_attempt=99)
    recorder = HarRecorder(tab=tab)

    body, _ = await recorder._fetch_response_body('r1', expects_body=True)

    assert body == ''
    assert tab.body_calls == 5
