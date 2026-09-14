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


def _reject_searches(fake_conn, message='Cannot find context with specified id'):
    """Make every search evaluation fail the way a navigating page does."""
    fake_conn.set_failure('Runtime.evaluate', -32000, message)
    fake_conn.set_failure('Runtime.callFunctionOn', -32000, message)


@pytest.mark.asyncio
async def test_find_returns_none_when_browser_rejects_the_search(fake_tab, fake_conn):
    _reject_searches(fake_conn)
    assert await fake_tab.find(id='anything', raise_exc=False) is None


@pytest.mark.asyncio
async def test_find_raises_element_not_found_when_browser_rejects_the_search(fake_tab, fake_conn):
    _reject_searches(fake_conn)
    with pytest.raises(ElementNotFound):
        await fake_tab.find(id='anything')


@pytest.mark.asyncio
async def test_find_all_returns_empty_list_when_browser_rejects_the_search(fake_tab, fake_conn):
    _reject_searches(fake_conn)
    assert await fake_tab.find(tag_name='div', find_all=True, raise_exc=False) == []


@pytest.mark.asyncio
async def test_find_all_returns_empty_list_when_element_list_vanishes(fake_tab, fake_conn):
    fake_conn.set_response('Runtime.evaluate', {'result': {'objectId': 'array-object-id'}})
    fake_conn.set_response('Runtime.callFunctionOn', {'result': {'objectId': 'array-object-id'}})
    fake_conn.set_failure('Runtime.getProperties', -32000, 'Could not find object with given id')
    assert await fake_tab.find(tag_name='div', find_all=True, raise_exc=False) == []


@pytest.mark.asyncio
async def test_find_all_raises_element_not_found_when_element_list_vanishes(fake_tab, fake_conn):
    fake_conn.set_response('Runtime.evaluate', {'result': {'objectId': 'array-object-id'}})
    fake_conn.set_response('Runtime.callFunctionOn', {'result': {'objectId': 'array-object-id'}})
    fake_conn.set_failure('Runtime.getProperties', -32000, 'Could not find object with given id')
    with pytest.raises(ElementNotFound):
        await fake_tab.find(tag_name='div', find_all=True)


@pytest.mark.asyncio
async def test_find_with_timeout_keeps_polling_when_browser_rejects_the_search(fake_tab, fake_conn):
    _reject_searches(fake_conn)
    with pytest.raises(WaitElementTimeout):
        await fake_tab.find(id='anything', timeout=1)
    assert len(fake_conn.commands_for('Runtime.evaluate') + fake_conn.commands_for('Runtime.callFunctionOn')) > 1
