"""Unit tests for FindElementsMixin not-found outcomes.

These assert observable results — None, an empty list, or a raised exception —
which hold regardless of which CDP commands find()/query() emit to locate an
element (the FakeConnection answers everything with an empty result). The
found-element path is covered result-based by the real-Chrome suite.
"""

from __future__ import annotations

import pytest

from pydoll.exceptions import ElementNotFound


@pytest.mark.asyncio
async def test_find_returns_none_when_not_found(fake_tab):
    assert await fake_tab.find(id='missing', raise_exc=False) is None


@pytest.mark.asyncio
async def test_find_raises_when_not_found_and_raise_exc(fake_tab):
    with pytest.raises(ElementNotFound):
        await fake_tab.find(id='missing')


@pytest.mark.asyncio
async def test_find_all_returns_empty_list_when_not_found(fake_tab):
    assert await fake_tab.find(tag_name='div', find_all=True, raise_exc=False) == []


@pytest.mark.asyncio
async def test_find_with_multiple_attributes_returns_none_when_not_found(fake_tab):
    assert await fake_tab.find(tag_name='input', name='q', raise_exc=False) is None


@pytest.mark.asyncio
async def test_query_css_returns_none_when_not_found(fake_tab):
    assert await fake_tab.query('.missing', raise_exc=False) is None


@pytest.mark.asyncio
async def test_query_xpath_raises_when_not_found_and_raise_exc(fake_tab):
    with pytest.raises(ElementNotFound):
        await fake_tab.query('//div[@id="missing"]')
