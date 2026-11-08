"""Deleting a browser context or closing a tab releases the Tab Pydoll kept for it.

Chrome closes the context's tabs, but each Tab held by the browser keeps its
connection, its callbacks and its network log, so a long-running process that
uses one context per job would grow by one Tab per job.
"""

from __future__ import annotations

import asyncio
from contextlib import suppress

import pytest

from pydoll.browser.chromium import Chrome
from pydoll.browser.tab import Tab
from pydoll.commands import TargetCommands
from pydoll.protocol.network.events import NetworkEvent
from pydoll.protocol.page.events import PageEvent
from pydoll.utils import get_browser_ws_address
from tests.browser_options import ci_options


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


async def _popup_target_id(browser, opener_id: str, context_id: str) -> str:
    """Wait for the page target a window.open() in the context created."""
    for _ in range(250):
        for target in await browser.get_targets():
            if (
                target['type'] == 'page'
                and target['targetId'] != opener_id
                and target.get('browserContextId') == context_id
            ):
                return target['targetId']
        await asyncio.sleep(0.02)
    raise AssertionError('the popup never appeared')


@pytest.mark.asyncio
async def test_listing_tabs_keeps_a_live_tab_whose_url_mentions_extension(browser, tab):
    callback_id = await tab.on(NetworkEvent.REQUEST_WILL_BE_SENT, lambda _event: None)
    await tab.go_to('data:text/html,<title>browser extension guide</title>')

    await browser.get_opened_tabs()

    assert tab.target_id in browser._tabs_opened
    assert await tab.remove_callback(callback_id) is True


@pytest.mark.asyncio
async def test_a_popup_listed_from_a_context_belongs_to_it_and_goes_with_it(browser):
    context_id = await browser.create_browser_context()
    opener = await browser.new_tab(
        'data:text/html,<title>opener</title>', browser_context_id=context_id
    )
    await opener.execute_script('window.open("about:blank")', user_gesture=True)
    popup_id = await _popup_target_id(browser, opener.target_id, context_id)

    popup = next(tab for tab in await browser.get_opened_tabs() if tab.target_id == popup_id)
    assert popup.browser_context_id == context_id

    await browser.delete_browser_context(context_id)
    assert popup_id not in browser._tabs_opened


@pytest.mark.asyncio
async def test_tabs_listed_in_the_default_context_report_no_context(browser):
    tabs = await browser.get_opened_tabs()
    default_tabs = [tab for tab in tabs if tab.target_id not in _created_context_tabs(browser)]
    assert default_tabs
    assert all(tab.browser_context_id is None for tab in default_tabs)


def _created_context_tabs(browser) -> set[str]:
    """Target ids of the registered tabs that new_tab() opened in a created context."""
    return {
        target_id
        for target_id, tab in browser._tabs_opened.items()
        if tab.browser_context_id is not None
    }


@pytest.mark.asyncio
async def test_closing_a_tab_already_closed_elsewhere_still_unregisters_it(browser, tab):
    """Closing raises, since the target is gone, but the tab is still released."""
    callback_id = await tab.on(NetworkEvent.REQUEST_WILL_BE_SENT, lambda _event: None)
    await browser.execute_command(TargetCommands.close_target(tab.target_id))
    for _ in range(100):
        if tab.target_id not in [target['targetId'] for target in await browser.get_targets()]:
            break
        await asyncio.sleep(0.02)

    with suppress(Exception):
        await tab.close()

    assert tab.target_id not in browser._tabs_opened
    assert await tab.remove_callback(callback_id) is False


@pytest.mark.asyncio
async def test_closing_a_second_tab_object_for_a_target_closes_the_registered_one(browser, tab):
    callback_id = await tab.on(NetworkEvent.REQUEST_WILL_BE_SENT, lambda _event: None)
    target = next(t for t in await browser.get_targets() if t['targetId'] == tab.target_id)
    other = Tab(browser, **browser._get_tab_kwargs(target['targetId']))

    await other.close()

    assert tab.target_id not in browser._tabs_opened
    assert await tab.remove_callback(callback_id) is False


@pytest.mark.asyncio
async def test_listing_tabs_twice_at_once_hands_out_one_tab_per_target(browser):
    response = await browser.execute_command(TargetCommands.create_target(url='about:blank'))
    target_id = response['result']['targetId']

    first, second = await asyncio.gather(browser.get_opened_tabs(), browser.get_opened_tabs())

    mine = [tab for tab in first + second if tab.target_id == target_id]
    await mine[0].close()
    assert len(mine) == 2
    assert mine[0] is mine[1]


@pytest.mark.asyncio
async def test_a_tab_got_by_target_is_kept_and_closed_with_the_browser(ci_chrome_options):
    async with Chrome(options=ci_chrome_options) as owner:
        await owner.start()
        response = await owner.execute_command(TargetCommands.create_target(url='about:blank'))
        client = Chrome(options=ci_options())
        await client.connect(await get_browser_ws_address(owner._connection_port))
        target = next(
            t for t in await client.get_targets() if t['targetId'] == response['result']['targetId']
        )
        tab = await client.get_tab_by_target(target)
        callback_id = await tab.on(PageEvent.LOAD_EVENT_FIRED, lambda _event: None)

        assert await client.get_tab_by_target(target) is tab
        await client.close()

        assert await tab.remove_callback(callback_id) is False


@pytest.mark.asyncio
async def test_connect_through_a_page_websocket_returns_a_usable_tab(ci_chrome_options):
    async with Chrome(options=ci_chrome_options) as owner:
        owner_tab = await owner.start()
        browser_ws = await get_browser_ws_address(owner._connection_port)
        page_ws = browser_ws.split('/devtools/')[0] + f'/devtools/page/{owner_tab.target_id}'
        client = Chrome(options=ci_options())
        try:
            tab = await client.connect(page_ws)
            response = await tab.execute_script('return 1 + 1')
        finally:
            await client.close()

    assert response['result']['result']['value'] == 2

