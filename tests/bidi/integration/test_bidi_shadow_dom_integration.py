"""Real-Firefox (WebDriver BiDi) integration tests for shadow DOM.

A shadow host exposes ``get_shadow_root()`` -> ``BiDiShadowRoot``, a finder
scoped to the shadow tree. Works for both open and closed roots — BiDi reaches a
closed root through the privileged sharedId, like the CDP path. Use ``query()``
with CSS inside the root.
"""

from __future__ import annotations

from contextlib import suppress

import pytest
import pytest_asyncio

from pydoll.exceptions import ShadowRootNotFound

SETUP = """(() => {
  for (const [hid, iid, mode] of [['open-host','open-inner','open'],
                                  ['closed-host','closed-inner','closed']]) {
    const h = document.createElement('div'); h.id = hid; document.body.appendChild(h);
    h.attachShadow({mode}).innerHTML =
      `<span id="${iid}" class="content">${mode}</span><b class="content">x</b>`;
  }
  return true;
})()"""


@pytest_asyncio.fixture(loop_scope='module')
async def tab(firefox_browser):
    """A tab (own context) pre-loaded with open + closed shadow hosts (see SETUP)."""
    context_id = await firefox_browser.create_browser_context()
    page = await firefox_browser.new_tab(browser_context_id=context_id)
    await page.go_to('data:text/html,<body></body>')
    await page.execute_script(SETUP)
    try:
        yield page
    finally:
        with suppress(Exception):
            await firefox_browser.delete_browser_context(context_id)


class TestShadowDom:
    @pytest.mark.asyncio(loop_scope='module')
    async def test_query_inside_open_shadow_root(self, tab):
        host = await tab.find(id='open-host')
        root = await host.get_shadow_root()
        assert root.mode == 'open'
        inner = await root.query('#open-inner', timeout=5)
        assert (await inner.text) == 'open'

    @pytest.mark.asyncio(loop_scope='module')
    async def test_query_inside_closed_shadow_root(self, tab):
        host = await tab.find(id='closed-host')
        root = await host.get_shadow_root()
        assert root.mode == 'closed'
        inner = await root.query('#closed-inner', timeout=5)
        assert (await inner.text) == 'closed'

    @pytest.mark.asyncio(loop_scope='module')
    async def test_find_all_inside_shadow_root(self, tab):
        host = await tab.find(id='open-host')
        root = await host.get_shadow_root()
        items = await root.query('.content', find_all=True, timeout=5)
        assert len(items) == 2

    @pytest.mark.asyncio(loop_scope='module')
    async def test_get_shadow_root_raises_without_shadow(self, tab):
        await tab.execute_script(
            "document.body.insertAdjacentHTML('beforeend', '<div id=\"plain\">x</div>')"
        )
        plain = await tab.find(id='plain')
        with pytest.raises(ShadowRootNotFound):
            await plain.get_shadow_root()

    @pytest.mark.asyncio(loop_scope='module')
    async def test_find_shadow_roots_collects_open_and_closed(self, tab):
        roots = await tab.find_shadow_roots()
        assert len(roots) == 2
        assert {root.mode for root in roots} == {'open', 'closed'}
