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
