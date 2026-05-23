"""Translate-only BiDiShadowRoot tests against an in-memory FakeBiDiConnection.

A shadow root scopes finds to the shadow tree via its sharedId. These cover the
non-find surface (mode, host, inner_html, repr); scoped finding is exercised in
the shadow-DOM integration suite against real Firefox.
"""

from __future__ import annotations

import pytest

from pydoll.elements.bidi.shadow_root import BiDiShadowRoot


def _root(conn, mode='open'):
    return BiDiShadowRoot('sr1', 'ctx', conn, mode=mode)


def _success(remote_value: dict) -> dict:
    return {'type': 'success', 'result': remote_value, 'realm': 'realm-1'}


def test_mode_and_host_element(fake_bidi_conn):
    root = _root(fake_bidi_conn, mode='closed')
    assert root.mode == 'closed'
    assert root.host_element is None


def test_repr_includes_mode_and_shared_id(fake_bidi_conn):
    assert 'BiDiShadowRoot' in repr(_root(fake_bidi_conn))
    assert 'open' in repr(_root(fake_bidi_conn))


@pytest.mark.asyncio
async def test_inner_html_reads_shadow_content(fake_bidi_conn):
    root = _root(fake_bidi_conn)
    fake_bidi_conn.set_result('script.callFunction', _success({'type': 'string', 'value': '<b>x</b>'}))
    assert await root.inner_html == '<b>x</b>'


@pytest.mark.asyncio
async def test_inner_html_empty_on_failure(fake_bidi_conn):
    root = _root(fake_bidi_conn)
    fake_bidi_conn.set_result('script.callFunction', {'type': 'exception', 'exceptionDetails': {}})
    assert await root.inner_html == ''
