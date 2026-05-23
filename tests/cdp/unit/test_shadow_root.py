"""Unit tests for ShadowRoot: state, HTML result, and shadow-DOM query rules.

Assertions are on observable results: the mode/host it was built with, the HTML
it returns, and the not-found / XPath-rejection outcomes — never on which CDP
commands were issued. Real shadow-DOM traversal is covered by the integration
suite.
"""

from __future__ import annotations

import pytest

from pydoll.elements.cdp.shadow_root import ShadowRoot
from pydoll.protocol.cdp.dom.types import ShadowRootType


def _shadow(fake_conn, mode=ShadowRootType.OPEN, host_element=None) -> ShadowRoot:
    return ShadowRoot(
        object_id='shadow-1',
        connection_handler=fake_conn,
        mode=mode,
        host_element=host_element,
    )


def test_mode_property_reflects_construction(fake_conn):
    assert _shadow(fake_conn, mode=ShadowRootType.CLOSED).mode == ShadowRootType.CLOSED


def test_host_element_property_reflects_construction(fake_conn):
    host = object()
    assert _shadow(fake_conn, host_element=host).host_element is host


@pytest.mark.asyncio
async def test_inner_html_returns_the_shadow_html(fake_conn):
    fake_conn.set_response('DOM.getOuterHTML', {'outerHTML': '<span>inner</span>'})
    assert await _shadow(fake_conn).inner_html == '<span>inner</span>'


@pytest.mark.asyncio
async def test_query_returns_none_when_not_found(fake_conn):
    assert await _shadow(fake_conn).query('.missing', raise_exc=False) is None


@pytest.mark.asyncio
async def test_query_rejects_xpath_on_shadow_root(fake_conn):
    with pytest.raises(NotImplementedError):
        await _shadow(fake_conn).query('//div')
