"""Real-Firefox (WebDriver BiDi) integration tests for element relationships.

Validates BiDiWebElement.get_children_elements / get_siblings_elements (the
methods that make BiDiWebElement satisfy WebElementProtocol), exercising the
:scope-based locateNodes path and the parent-derived sibling logic.
"""

from __future__ import annotations

import pytest


PAGE = (
    'data:text/html,'
    '<div id="parent">'
    '<span id="first" class="c">1</span>'
    '<span class="c">2</span>'
    '<b id="b">3</b>'
    '</div>'
)


class TestElementRelations:
    @pytest.mark.asyncio
    async def test_get_children_direct(self, tab):
        await tab.go_to(PAGE)
        parent = await tab.find(id='parent')
        children = await parent.get_children_elements()
        assert len(children) == 3

    @pytest.mark.asyncio
    async def test_get_children_tag_filter(self, tab):
        await tab.go_to(PAGE)
        parent = await tab.find(id='parent')
        spans = await parent.get_children_elements(tag_filter=['span'])
        assert len(spans) == 2

    @pytest.mark.asyncio
    async def test_get_siblings(self, tab):
        await tab.go_to(PAGE)
        first = await tab.find(id='first')
        siblings = await first.get_siblings_elements()
        assert len(siblings) == 2

    @pytest.mark.asyncio
    async def test_get_siblings_tag_filter(self, tab):
        await tab.go_to(PAGE)
        first = await tab.find(id='first')
        bold = await first.get_siblings_elements(tag_filter=['b'])
        assert len(bold) == 1
