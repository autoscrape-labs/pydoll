"""A tab whose renderer crashed fails fast instead of waiting out each command's timeout.

Chrome reports the crash with ``Inspector.targetCrashed`` on the tab's own
connection and stops answering every command that needs the renderer, so
without acting on the event each of them would wait the full 60 s.
"""

from __future__ import annotations

import asyncio
import logging
import time

import pytest

from pydoll.browser.tab import Tab
from pydoll.commands import PageCommands, RuntimeCommands
from pydoll.exceptions import TargetCrashed
from pydoll.protocol.network.events import NetworkEvent


async def _crash(tab: Tab) -> None:
    """Crash the tab's renderer the way an out-of-memory page would."""
    await tab._connection_handler.execute_command_nowait(PageCommands.crash())


async def _evaluate(tab: Tab, expression: str) -> object:
    response = await tab.execute_script(f'return {expression}')
    return response['result']['result']['value']


@pytest.mark.asyncio
async def test_running_and_later_scripts_fail_at_once_when_the_renderer_crashes(browser, tab):
    await tab.go_to('data:text/html,<title>crash</title>')
    started = time.monotonic()
    running = asyncio.create_task(tab.execute_script('while (true) {}'))
    await asyncio.sleep(0.3)
    await _crash(tab)
    with pytest.raises(TargetCrashed):
        await running
    with pytest.raises(TargetCrashed):
        await tab.execute_script('return 1 + 1')
    assert time.monotonic() - started < 10

    other = await browser.new_tab(browser_context_id=tab.browser_context_id)
    assert await _evaluate(other, '1 + 1') == 2


@pytest.mark.asyncio
async def test_unawaited_script_cut_short_by_a_crash_raises_nothing_in_the_loop(tab, caplog):
    caplog.set_level(logging.ERROR, logger='asyncio')
    await tab.go_to('data:text/html,<title>crash</title>')
    handler = tab._connection_handler
    await handler.execute_command_nowait(RuntimeCommands.evaluate('while (true) {}'))
    await asyncio.sleep(0.3)
    await _crash(tab)
    await _wait_crashed(tab)
    await asyncio.sleep(0.1)
    assert [record for record in caplog.records if record.name == 'asyncio'] == []


@pytest.mark.asyncio
async def test_go_to_recovers_a_crashed_tab(tab):
    await tab.go_to('data:text/html,<title>before</title>')
    await _crash(tab)
    await _wait_crashed(tab)
    await tab.go_to('data:text/html,<title>after</title>', timeout=10)
    assert await tab.title() == 'after'
    assert await _evaluate(tab, '1 + 1') == 2


@pytest.mark.asyncio
async def test_go_to_recovers_a_crashed_tab_that_had_page_events_on(tab):
    await tab.enable_page_events()
    await tab.go_to('data:text/html,<title>before</title>')
    await _crash(tab)
    await _wait_crashed(tab)
    await tab.go_to('data:text/html,<title>after</title>', timeout=10)
    assert await tab.title() == 'after'
    assert tab.page_events_enabled is True


@pytest.mark.asyncio
async def test_refresh_loads_the_crashed_page_again(tab):
    await tab.go_to('data:text/html,<title>crashed page</title>')
    await _crash(tab)
    await _wait_crashed(tab)
    await tab.refresh()
    assert await tab.title() == 'crashed page'


@pytest.mark.asyncio
async def test_a_crashed_tab_can_still_be_closed(browser, tab):
    await _crash(tab)
    await _wait_crashed(tab)
    await tab.close()
    targets = await browser.get_targets()
    assert tab.target_id not in [target['targetId'] for target in targets]


async def _wait_crashed(tab: Tab) -> None:
    """Wait until the tab's connection has seen the crash event."""
    loop = asyncio.get_running_loop()
    deadline = loop.time() + 5
    while not tab._connection_handler.target_crashed:
        assert loop.time() < deadline, 'the crash event never arrived'
        await asyncio.sleep(0.02)


@pytest.mark.asyncio
async def test_a_crashed_tab_whose_connection_dropped_recovers_with_its_domains(tab):
    """A session opened after the crash never hears that the renderer is back."""
    seen: list[str] = []
    await tab.enable_page_events()
    await tab.enable_network_events()
    await tab.on(
        NetworkEvent.REQUEST_WILL_BE_SENT,
        lambda event: seen.append(event['params']['request']['url']),
    )
    await tab.go_to('data:text/html,<title>before</title>')
    await _crash(tab)
    await _wait_crashed(tab)
    handler = tab._connection_handler
    await handler._ws_connection.close()
    await asyncio.wait_for(handler.wait_disconnected(), timeout=5)
    seen.clear()

    await tab.go_to('data:text/html,<title>after</title>', timeout=10)

    assert await tab.title() == 'after'
    assert seen
