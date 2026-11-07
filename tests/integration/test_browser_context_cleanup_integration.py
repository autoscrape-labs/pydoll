"""Deleting a browser context or closing a tab releases the Tab Pydoll kept for it.

Chrome closes the context's tabs, but each Tab held by the browser keeps its
connection, its callbacks and its network log, so a long-running process that
uses one context per job would grow by one Tab per job.
"""

from __future__ import annotations

import asyncio

import pytest

from pydoll.browser.chromium import Chrome
from pydoll.commands import TargetCommands
from pydoll.protocol.network.events import NetworkEvent


@pytest.mark.asyncio
async def test_deleting_contexts_leaves_no_tab_registered(browser):
    registered_before = set(browser._tabs_opened)
    for _ in range(5):
        context_id = await browser.create_browser_context()
        tab = await browser.new_tab('about:blank', browser_context_id=context_id)
        await tab.enable_network_events()
        await browser.delete_browser_context(context_id)

    assert set(browser._tabs_opened) == registered_before


@pytest.mark.asyncio
async def test_deleting_a_context_closes_the_connections_of_its_tabs(browser):
    context_id = await browser.create_browser_context()
    tab = await browser.new_tab('about:blank', browser_context_id=context_id)
    callback_id = await tab.on(NetworkEvent.REQUEST_WILL_BE_SENT, lambda _event: None)

    await browser.delete_browser_context(context_id)

    assert await tab.remove_callback(callback_id) is False


@pytest.mark.asyncio
async def test_deleting_a_context_keeps_the_tabs_of_other_contexts(browser, tab):
    other_context = await browser.create_browser_context()
    await browser.new_tab('about:blank', browser_context_id=other_context)

    await browser.delete_browser_context(other_context)

    assert tab.target_id in browser._tabs_opened
    response = await tab.execute_script('return 1 + 1')
    assert response['result']['result']['value'] == 2


@pytest.mark.asyncio
async def test_closing_a_tab_unregisters_it_and_closes_its_connection(browser, tab):
    callback_id = await tab.on(NetworkEvent.REQUEST_WILL_BE_SENT, lambda _event: None)

    await tab.close()

    assert tab.target_id not in browser._tabs_opened
    assert await tab.remove_callback(callback_id) is False


@pytest.mark.asyncio
async def test_listing_tabs_forgets_a_tab_closed_outside_pydoll(browser, tab):
    callback_id = await tab.on(NetworkEvent.REQUEST_WILL_BE_SENT, lambda _event: None)
    await browser.execute_command(TargetCommands.close_target(tab.target_id))
    for _ in range(100):
        if tab.target_id not in [target['targetId'] for target in await browser.get_targets()]:
            break
        await asyncio.sleep(0.02)

    opened = await browser.get_opened_tabs()

    assert tab not in opened
    assert tab.target_id not in browser._tabs_opened
    assert await tab.remove_callback(callback_id) is False


@pytest.mark.asyncio
async def test_listed_tabs_are_registered_under_their_own_targets(ci_chrome_options):
    async with Chrome(options=ci_chrome_options) as browser:
        await browser.start()
        for _ in range(3):
            await browser.execute_command(TargetCommands.create_target(url='about:blank'))

        await browser.get_opened_tabs()

        assert all(tab.target_id == key for key, tab in browser._tabs_opened.items())


@pytest.mark.asyncio
async def test_listing_tabs_again_drops_only_the_tab_whose_target_closed(ci_chrome_options):
    async with Chrome(options=ci_chrome_options) as browser:
        await browser.start()
        for _ in range(3):
            await browser.execute_command(TargetCommands.create_target(url='about:blank'))
        tabs = await browser.get_opened_tabs()
        closed = tabs[-1].target_id
        await browser.execute_command(TargetCommands.close_target(closed))
        for _ in range(100):
            if closed not in [target['targetId'] for target in await browser.get_targets()]:
                break
            await asyncio.sleep(0.02)

        remaining = {tab.target_id for tab in await browser.get_opened_tabs()}

        assert remaining == {tab.target_id for tab in tabs} - {closed}
