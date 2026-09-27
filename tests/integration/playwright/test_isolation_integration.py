"""The selector engine must be invisible to the page and cheap in round trips."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from _pages import page_url
from pydoll.connection.connection_handler import ConnectionHandler

HOOKS = """
(() => {
  const calls = [];
  const record = (name) => calls.push(name);
  const wrap = (proto, name) => {
    const original = proto[name];
    proto[name] = function (...args) { record(name); return original.apply(this, args); };
  };
  wrap(Element.prototype, 'getBoundingClientRect');
  wrap(Element.prototype, 'checkVisibility');
  wrap(Document.prototype, 'elementsFromPoint');
  wrap(Document.prototype, 'elementFromPoint');
  wrap(Document.prototype, 'evaluate');
  wrap(Document.prototype, 'querySelectorAll');
  const raf = window.requestAnimationFrame;
  window.requestAnimationFrame = function (cb) { record('requestAnimationFrame'); return raf.call(this, cb); };
  const style = window.getComputedStyle;
  window.getComputedStyle = function (...args) { record('getComputedStyle'); return style.apply(this, args); };
  const originalEval = window.eval;
  window.eval = function (source) { record('eval:' + source); return originalEval(source); };
  window.__calls = calls;
  window.__keys = Object.keys(window);
})();
"""


class TestMainWorldInvisibility:
    @pytest.mark.asyncio
    async def test_page_hooks_never_see_the_engine(self, page):
        await page.add_init_script(HOOKS)
        await page.goto(page_url('playwright_engine.html'))
        baseline = list(await page.evaluate('() => window.__calls'))
        await page.locator('#btn-save').click()
        await page.get_by_label('Full name').fill('Ana')
        await page.locator('xpath=//h2').count()
        assert await page.get_by_role('button', name='Save').is_visible()
        await page.locator('#btn-save').hover()
        await page.locator('#select-single').select_option('a')
        await page.locator('#p-hello').text_content()
        calls = list(await page.evaluate('() => window.__calls'))
        assert calls == baseline, f'the page observed engine calls: {calls[len(baseline):]}'

    @pytest.mark.asyncio
    async def test_no_globals_and_no_page_eval(self, page):
        await page.add_init_script(HOOKS)
        await page.goto(page_url('playwright_engine.html'))
        keys_before = await page.evaluate('() => Object.keys(window)')
        await page.locator('#list li').count()
        await page.locator('#btn-save').click()
        assert await page.evaluate('6 * 7') == 42
        keys_after = await page.evaluate('() => Object.keys(window)')
        assert keys_after == keys_before
        calls = await page.evaluate('() => window.__calls')
        assert not [call for call in calls if str(call).startswith('eval:')]

    @pytest.mark.asyncio
    async def test_user_evaluate_still_runs_in_the_main_world(self, page):
        await page.goto(page_url('playwright_engine.html'))
        await page.evaluate('() => { window.__app = { ready: true } }')
        assert await page.evaluate('() => window.__app.ready') is True
        handle = await page.locator('#btn-save').element_handle()
        assert await handle.evaluate('e => window.__app.ready && e.id') == 'btn-save'
        assert await page.locator('#btn-save').evaluate('e => e.id') == 'btn-save'
        assert await page.eval_on_selector_all('#list li', 'items => items.length') == 3
        element = await page.evaluate_handle('() => document.querySelector("#btn-save")')
        assert await element.as_element().inner_text() == 'Save'


class TestRoundTrips:
    @pytest.mark.asyncio
    async def test_click_uses_few_commands(self, page):
        await page.goto(page_url('playwright_engine.html'))
        await page.locator('#btn-save').click()
        original = ConnectionHandler.execute_command
        counted: list[str] = []

        async def counting(self, command, *args, **kwargs):
            method = command.get('method')
            counted.append(method.value if hasattr(method, 'value') else str(method))
            return await original(self, command, *args, **kwargs)

        with patch.object(ConnectionHandler, 'execute_command', counting):
            await page.locator('#btn-save').click()
        assert len(counted) <= 9, counted
        assert counted.count('Runtime.callFunctionOn') <= 3, counted
