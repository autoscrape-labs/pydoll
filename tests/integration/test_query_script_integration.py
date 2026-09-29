"""Integration tests for FindElementsMixin.query_script against real Chrome."""

from pathlib import Path

import pytest

from pydoll.elements.web_element import WebElement
from pydoll.exceptions import ScriptException

PAGES = Path(__file__).parent / 'pages'
SIMPLE_PAGE = f'file://{(PAGES / "test_core_simple.html").absolute()}'
IFRAME_PAGE = f'file://{(PAGES / "test_iframe_simple.html").absolute()}'
SHADOW_PAGE = f'file://{(PAGES / "shadow_dom_test.html").absolute()}'


class TestQueryScript:
    """query_script wraps whatever elements a JS function returns."""

    @pytest.mark.asyncio
    async def test_tab_root_returns_node_list_in_order(self, tab):
        await tab.go_to(SIMPLE_PAGE)

        items = await tab.query_script('function() { return this.querySelectorAll("#list li"); }')

        assert [item.get_attribute('id') for item in items] == ['li-1', 'li-2', 'li-3']
        assert all(isinstance(item, WebElement) for item in items)
        assert items[0].tag_name == 'li'

    @pytest.mark.asyncio
    async def test_arguments_are_passed_positionally(self, tab):
        await tab.go_to(SIMPLE_PAGE)

        found = await tab.query_script(
            'function(tag, index) { return [this.getElementsByTagName(tag)[index]]; }',
            arguments=[{'value': 'li'}, {'value': 1}],
        )

        assert [element.get_attribute('id') for element in found] == ['li-2']

    @pytest.mark.asyncio
    async def test_single_element_and_null_results(self, tab):
        await tab.go_to(SIMPLE_PAGE)

        single = await tab.query_script('function() { return this.getElementById("btn-1"); }')
        nothing = await tab.query_script('function() { return null; }')
        empty = await tab.query_script('function() { return []; }')

        assert [element.get_attribute('id') for element in single] == ['btn-1']
        assert nothing == []
        assert empty == []

    @pytest.mark.asyncio
    async def test_element_root_binds_this_to_the_element(self, tab):
        await tab.go_to(SIMPLE_PAGE)
        container = await tab.find(id='list', timeout=5)

        children = await container.query_script('function() { return this.children; }')

        assert [child.get_attribute('id') for child in children] == ['li-1', 'li-2', 'li-3']

    @pytest.mark.asyncio
    async def test_iframe_root_runs_inside_the_frame(self, tab):
        await tab.go_to(IFRAME_PAGE)
        iframe = await tab.find(id='simple-iframe', timeout=5)

        inside = await iframe.query_script(
            'function() { return this.querySelectorAll("#iframe-form input, #iframe-form textarea"); }'
        )

        ids = [element.get_attribute('id') for element in inside]
        assert 'iframe-input' in ids
        assert 'iframe-textarea' in ids
        assert await inside[0].execute_script(
            'return this.ownerDocument !== window.top.document', return_by_value=True
        )

    @pytest.mark.asyncio
    async def test_shadow_root_binds_this_to_the_root(self, tab):
        await tab.go_to(SHADOW_PAGE)
        host = await tab.find(id='open-host', timeout=5)
        shadow = await host.get_shadow_root()

        buttons = await shadow.query_script('function() { return this.querySelectorAll("button"); }')

        assert [button.get_attribute('id') for button in buttons] == ['open-btn']

    @pytest.mark.asyncio
    async def test_thrown_exception_surfaces_as_script_exception(self, tab):
        await tab.go_to(SIMPLE_PAGE)

        with pytest.raises(ScriptException, match='boom'):
            await tab.query_script('function() { throw new Error("boom"); }')
