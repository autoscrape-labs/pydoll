"""Unit tests for FindElementsMixin not-found outcomes.

These assert observable results — None, an empty list, or a raised exception —
which hold regardless of which CDP commands find()/query() emit to locate an
element (the FakeConnection answers everything with an empty result). The
found-element path is covered result-based by the real-Chrome suite.
"""

from __future__ import annotations

import pytest

from pydoll.exceptions import ElementNotFound, WaitElementTimeout


@pytest.mark.asyncio
async def test_find_returns_none_when_not_found(fake_tab):
    assert await fake_tab.find(id='missing', raise_exc=False) is None


@pytest.mark.asyncio
async def test_find_with_timeout_raises_wait_timeout_when_never_found(fake_tab):
    with pytest.raises(WaitElementTimeout):
        await fake_tab.find(id='missing', timeout=1)


@pytest.mark.asyncio
async def test_find_with_timeout_returns_none_without_raise(fake_tab):
    assert await fake_tab.find(id='missing', timeout=1, raise_exc=False) is None


@pytest.mark.asyncio
async def test_cross_iframe_selector_raises_element_not_found(fake_tab):
    with pytest.raises(ElementNotFound):
        await fake_tab.query('iframe button')


@pytest.mark.asyncio
async def test_cross_iframe_selector_returns_none_without_raise(fake_tab):
    assert await fake_tab.query('iframe button', raise_exc=False) is None


@pytest.mark.asyncio
async def test_cross_iframe_selector_times_out(fake_tab):
    with pytest.raises(WaitElementTimeout):
        await fake_tab.query('iframe button', timeout=1)


@pytest.mark.asyncio
async def test_cross_iframe_find_all_returns_empty_without_raise(fake_tab):
    assert await fake_tab.query('iframe span', find_all=True, raise_exc=False, timeout=1) == []


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
