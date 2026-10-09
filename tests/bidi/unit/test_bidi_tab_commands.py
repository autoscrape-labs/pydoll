"""Translate-only BiDiTab methods tested against an in-memory FakeBiDiConnection.

These cover the BiDi commands a BiDiTab emits and the values it carries — the
WebDriver BiDi equivalent of tests/cdp/unit/test_tab_commands.py. Behaviour that
needs real Firefox (events, real navigation, trusted input) lives in
tests/bidi/integration.
"""

from __future__ import annotations

import pytest

from pydoll.exceptions import ScriptEvaluationError, WaitTimeout


def _success(remote_value: dict) -> dict:
    """A BiDi script EvaluateResult wrapping a RemoteValue."""
    return {'type': 'success', 'result': remote_value, 'realm': 'realm-1'}


@pytest.mark.asyncio
async def test_go_to_navigates_with_context_and_complete_wait(fake_bidi_conn, fake_bidi_tab):
    await fake_bidi_tab.go_to('https://example.com')
    command = fake_bidi_conn.last_command('browsingContext.navigate')
    assert command['params']['context'] == 'fake-context'
    assert command['params']['url'] == 'https://example.com'
    assert command['params']['wait'] == 'complete'


@pytest.mark.asyncio
async def test_refresh_reloads_with_complete_wait(fake_bidi_conn, fake_bidi_tab):
    await fake_bidi_tab.refresh()
    command = fake_bidi_conn.last_command('browsingContext.reload')
    assert command['params']['context'] == 'fake-context'
    assert command['params']['wait'] == 'complete'


@pytest.mark.asyncio
async def test_current_url_evaluates_location_href(fake_bidi_conn, fake_bidi_tab):
    fake_bidi_conn.set_result(
        'script.evaluate', _success({'type': 'string', 'value': 'https://example.com/p'})
    )
    assert await fake_bidi_tab.current_url() == 'https://example.com/p'
    assert fake_bidi_conn.last_command('script.evaluate')['params']['expression'] == 'location.href'


@pytest.mark.asyncio
async def test_title_evaluates_document_title(fake_bidi_conn, fake_bidi_tab):
    fake_bidi_conn.set_result('script.evaluate', _success({'type': 'string', 'value': 'Hello'}))
    assert await fake_bidi_tab.title() == 'Hello'
    assert fake_bidi_conn.last_command('script.evaluate')['params']['expression'] == 'document.title'


@pytest.mark.asyncio
async def test_find_locates_node_by_css_and_builds_element(fake_bidi_conn, fake_bidi_tab):
    fake_bidi_conn.set_result(
        'browsingContext.locateNodes',
        {'nodes': [{'type': 'node', 'sharedId': 's1', 'value': {
            'localName': 'div', 'attributes': {'id': 'x'}}}]},
    )
    element = await fake_bidi_tab.find(id='x')
    assert element is not None
    assert element.id == 'x'
    command = fake_bidi_conn.last_command('browsingContext.locateNodes')
    assert command['params']['context'] == 'fake-context'
    assert command['params']['locator'] == {'type': 'css', 'value': '#x'}


@pytest.mark.asyncio
async def test_find_all_returns_every_node(fake_bidi_conn, fake_bidi_tab):
    fake_bidi_conn.set_result(
        'browsingContext.locateNodes',
        {'nodes': [
            {'type': 'node', 'sharedId': 's1', 'value': {'localName': 'li', 'attributes': {}}},
            {'type': 'node', 'sharedId': 's2', 'value': {'localName': 'li', 'attributes': {}}},
        ]},
    )
    elements = await fake_bidi_tab.find(tag_name='li', find_all=True)
    assert len(elements) == 2


@pytest.mark.asyncio
async def test_evaluate_evaluates_and_deserializes_value(fake_bidi_conn, fake_bidi_tab):
    fake_bidi_conn.set_result('script.evaluate', _success({'type': 'number', 'value': 7}))
    assert await fake_bidi_tab.evaluate('return 7') == 7
    expression = fake_bidi_conn.last_command('script.evaluate')['params']['expression']
    assert expression == '(function() { return 7 })()'


@pytest.mark.asyncio
async def test_evaluate_raises_script_evaluation_error_on_throw(fake_bidi_conn, fake_bidi_tab):
    fake_bidi_conn.set_result('script.evaluate', {
        'type': 'exception',
        'exceptionDetails': {'text': 'ReferenceError: nope is not defined', 'exception': {}},
        'realm': 'realm-1',
    })
    with pytest.raises(ScriptEvaluationError) as info:
        await fake_bidi_tab.evaluate('nope')
    assert info.value.error_text == 'ReferenceError: nope is not defined'


@pytest.mark.asyncio
async def test_execute_command_sends_raw_bidi_command(fake_bidi_conn, fake_bidi_tab):
    from pydoll.commands.bidi.browsing_context_commands import BrowsingContextCommands

    fake_bidi_conn.set_result('browsingContext.getTree', {'contexts': []})
    response = await fake_bidi_tab.execute_command(BrowsingContextCommands.get_tree())
    assert response['result'] == {'contexts': []}
    assert fake_bidi_conn.last_command('browsingContext.getTree')


@pytest.mark.asyncio
async def test_evaluate_with_args_calls_function_with_local_values(
    fake_bidi_conn, fake_bidi_tab
):
    fake_bidi_conn.set_result('script.callFunction', _success({'type': 'undefined'}))
    await fake_bidi_tab.evaluate('(a) => a', 5)
    command = fake_bidi_conn.last_command('script.callFunction')
    assert command['params']['arguments'] == [{'type': 'number', 'value': 5}]


@pytest.mark.asyncio
async def test_get_cookies_returns_protocol_agnostic_cookies(fake_bidi_conn, fake_bidi_tab):
    fake_bidi_conn.set_result(
        'storage.getCookies',
        {'cookies': [{
            'name': 'session', 'value': {'type': 'string', 'value': 'abc'},
            'domain': 'example.com', 'path': '/', 'size': 10,
            'httpOnly': False, 'secure': True, 'sameSite': 'lax',
        }]},
    )
    cookies = await fake_bidi_tab.get_cookies()
    assert cookies[0]['name'] == 'session'
    assert cookies[0]['value'] == 'abc'
    assert cookies[0]['domain'] == 'example.com'
    assert cookies[0]['sameSite'] == 'Lax'
    assert cookies[0]['session'] is True
    assert cookies[0]['expires'] == -1


@pytest.mark.asyncio
async def test_set_cookies_sends_set_cookie_per_cookie(fake_bidi_conn, fake_bidi_tab):
    await fake_bidi_tab.set_cookies([{'name': 'a', 'value': '1', 'domain': 'example.com'}])
    cookie = fake_bidi_conn.last_command('storage.setCookie')['params']['cookie']
    assert cookie['name'] == 'a'
    assert cookie['value'] == {'type': 'string', 'value': '1'}
    assert cookie['domain'] == 'example.com'


@pytest.mark.asyncio
async def test_delete_all_cookies_sends_delete_cookies(fake_bidi_conn, fake_bidi_tab):
    await fake_bidi_tab.delete_all_cookies()
    assert fake_bidi_conn.commands_for('storage.deleteCookies')


@pytest.mark.asyncio
async def test_useragent_override_sets_ua_for_this_context(fake_bidi_conn, fake_bidi_tab):
    await fake_bidi_tab.useragent_override('CustomUA/1.0')
    command = fake_bidi_conn.last_command('emulation.setUserAgentOverride')
    assert command['params']['userAgent'] == 'CustomUA/1.0'
    assert command['params']['contexts'] == ['fake-context']


def _one_node(conn, local_name='div'):
    conn.set_result(
        'browsingContext.locateNodes',
        {'nodes': [{'type': 'node', 'sharedId': 's1', 'value': {
            'localName': local_name, 'attributes': {}}}]},
    )


@pytest.mark.asyncio
async def test_find_raises_when_not_found(fake_bidi_conn, fake_bidi_tab):
    from pydoll.exceptions import ElementNotFound

    fake_bidi_conn.set_result('browsingContext.locateNodes', {'nodes': []})
    with pytest.raises(ElementNotFound):
        await fake_bidi_tab.find(id='nope')


@pytest.mark.asyncio
async def test_find_returns_none_when_not_found_and_no_raise(fake_bidi_conn, fake_bidi_tab):
    fake_bidi_conn.set_result('browsingContext.locateNodes', {'nodes': []})
    assert await fake_bidi_tab.find(id='nope', raise_exc=False) is None


@pytest.mark.asyncio
async def test_find_all_empty_returns_empty_list(fake_bidi_conn, fake_bidi_tab):
    fake_bidi_conn.set_result('browsingContext.locateNodes', {'nodes': []})
    assert await fake_bidi_tab.find(tag_name='li', find_all=True, raise_exc=False) == []


@pytest.mark.asyncio
async def test_find_by_class_name_builds_css_locator(fake_bidi_conn, fake_bidi_tab):
    _one_node(fake_bidi_conn)
    await fake_bidi_tab.find(class_name='btn')
    locator = fake_bidi_conn.last_command('browsingContext.locateNodes')['params']['locator']
    assert locator == {'type': 'css', 'value': '.btn'}


@pytest.mark.asyncio
async def test_find_by_name_builds_xpath_locator(fake_bidi_conn, fake_bidi_tab):
    _one_node(fake_bidi_conn)
    await fake_bidi_tab.find(name='email')
    locator = fake_bidi_conn.last_command('browsingContext.locateNodes')['params']['locator']
    assert locator['type'] == 'xpath'
    assert 'email' in locator['value']


@pytest.mark.asyncio
async def test_find_by_tag_name_builds_css_locator(fake_bidi_conn, fake_bidi_tab):
    _one_node(fake_bidi_conn, local_name='section')
    await fake_bidi_tab.find(tag_name='section')
    locator = fake_bidi_conn.last_command('browsingContext.locateNodes')['params']['locator']
    assert locator == {'type': 'css', 'value': 'section'}


@pytest.mark.asyncio
async def test_find_by_multiple_attributes_builds_css(fake_bidi_conn, fake_bidi_tab):
    _one_node(fake_bidi_conn)
    await fake_bidi_tab.find(tag_name='input', type='text')
    locator = fake_bidi_conn.last_command('browsingContext.locateNodes')['params']['locator']
    assert locator['type'] in ('css', 'xpath')
    assert 'text' in locator['value']


@pytest.mark.asyncio
async def test_wait_for_url_returns_matching_url(fake_bidi_conn, fake_bidi_tab):
    fake_bidi_conn.set_result(
        'script.evaluate', _success({'type': 'string', 'value': 'https://shop.test/checkout/1'})
    )
    assert await fake_bidi_tab.wait_for_url('**/checkout/*') == 'https://shop.test/checkout/1'


@pytest.mark.asyncio
async def test_wait_for_url_times_out(fake_bidi_conn, fake_bidi_tab):
    fake_bidi_conn.set_result('script.evaluate', _success({'type': 'string', 'value': 'https://a/'}))
    with pytest.raises(WaitTimeout):
        await fake_bidi_tab.wait_for_url('**/never', timeout=0.05)


@pytest.mark.asyncio
async def test_wait_for_script_returns_primitive_when_truthy(fake_bidi_conn, fake_bidi_tab):
    fake_bidi_conn.set_result('script.evaluate', _success({'type': 'number', 'value': 3}))
    assert await fake_bidi_tab.wait_for_script('window.count') == 3


@pytest.mark.asyncio
async def test_wait_for_script_returns_true_for_objects(fake_bidi_conn, fake_bidi_tab):
    fake_bidi_conn.set_result('script.evaluate', _success({'type': 'object'}))
    assert await fake_bidi_tab.wait_for_script('window.app') is True


@pytest.mark.asyncio
async def test_wait_for_script_times_out_on_falsy(fake_bidi_conn, fake_bidi_tab):
    fake_bidi_conn.set_result('script.evaluate', _success({'type': 'number', 'value': 'NaN'}))
    with pytest.raises(WaitTimeout):
        await fake_bidi_tab.wait_for_script('NaN', timeout=0.05)


@pytest.mark.asyncio
async def test_wait_for_script_raises_on_throw(fake_bidi_conn, fake_bidi_tab):
    fake_bidi_conn.set_result('script.evaluate', {
        'type': 'exception', 'realm': 'r',
        'exceptionDetails': {'text': 'TypeError: boom', 'exception': {}},
    })
    with pytest.raises(ScriptEvaluationError):
        await fake_bidi_tab.wait_for_script('boom()')


@pytest.mark.asyncio
async def test_wait_for_absence_returns_when_no_element(fake_bidi_conn, fake_bidi_tab):
    fake_bidi_conn.set_result('browsingContext.locateNodes', {'nodes': []})
    await fake_bidi_tab.wait_for_absence(id='spinner', timeout=1)


@pytest.mark.asyncio
async def test_wait_for_absence_times_out_while_present(fake_bidi_conn, fake_bidi_tab):
    _one_node(fake_bidi_conn)
    with pytest.raises(WaitTimeout):
        await fake_bidi_tab.wait_for_absence(id='spinner', timeout=0.05)


def _registered_callback(conn, event):
    return next(cb['callback'] for cb in conn._callbacks.values() if cb['event'] == event)


def _listeners(conn, event):
    return [cb for cb in conn._callbacks.values() if cb['event'] == event]


@pytest.mark.asyncio
async def test_expect_request_fills_handle_from_before_request_sent(fake_bidi_conn, fake_bidi_tab):
    async with fake_bidi_tab.expect_request('**/api/*') as request:
        on_request = _registered_callback(fake_bidi_conn, 'network.beforeRequestSent')
        on_request({'method': 'network.beforeRequestSent', 'params': {
            'context': 'fake-context',
            'request': {
                'request': 'r1', 'url': 'http://x/api/items', 'method': 'POST',
                'headers': [{'name': 'Accept', 'value': {'type': 'string', 'value': 'json'}}],
                'destination': '', 'initiatorType': 'fetch',
            },
        }})
    assert request.request_id == 'r1'
    assert request.url == 'http://x/api/items'
    assert request.method == 'POST'
    assert request.headers == {'Accept': 'json'}
    assert request.post_data is None
    assert request.resource_type == 'fetch'
    assert _listeners(fake_bidi_conn, 'network.beforeRequestSent') == []


@pytest.mark.asyncio
async def test_expect_request_ignores_other_contexts_and_times_out(fake_bidi_conn, fake_bidi_tab):
    with pytest.raises(WaitTimeout):
        async with fake_bidi_tab.expect_request('**/api/*', timeout=0.05):
            on_request = _registered_callback(fake_bidi_conn, 'network.beforeRequestSent')
            on_request({'params': {'context': 'other', 'request': {'url': 'http://x/api/a'}}})


@pytest.mark.asyncio
async def test_expect_response_reads_body_from_collector(fake_bidi_conn, fake_bidi_tab):
    fake_bidi_conn.set_result('network.addDataCollector', {'collector': 'col-1'})
    fake_bidi_conn.set_result('network.getData', {'bytes': {'type': 'string', 'value': '{"a": 1}'}})
    async with fake_bidi_tab.expect_response('**/api/*') as response:
        on_completed = _registered_callback(fake_bidi_conn, 'network.responseCompleted')
        on_completed({'params': {
            'context': 'fake-context',
            'request': {'request': 'r1', 'url': 'http://x/api/a'},
            'response': {
                'url': 'http://x/api/a', 'status': 200, 'mimeType': 'application/json',
                'headers': [{'name': 'X-A', 'value': {'type': 'string', 'value': '1'}}],
            },
        }})
    assert response.ok is True
    assert response.status == 200
    assert response.headers == {'X-A': '1'}
    assert response.json() == {'a': 1}
    assert fake_bidi_conn.last_command('network.getData')['params']['collector'] == 'col-1'
    assert fake_bidi_conn.commands_for('network.removeDataCollector')


@pytest.mark.asyncio
async def test_expect_response_failed_request_has_no_body(fake_bidi_conn, fake_bidi_tab):
    fake_bidi_conn.set_result('network.addDataCollector', {'collector': 'col-1'})
    async with fake_bidi_tab.expect_response('**/api/*') as response:
        on_failed = _registered_callback(fake_bidi_conn, 'network.fetchError')
        on_failed({'params': {
            'context': 'fake-context',
            'request': {'request': 'r1', 'url': 'http://x/api/a'},
            'errorText': 'NS_ERROR_FAILURE',
        }})
    with pytest.raises(WaitTimeout):
        response.body()


@pytest.mark.asyncio
async def test_expect_navigation_waits_for_matching_load(fake_bidi_conn, fake_bidi_tab):
    async with fake_bidi_tab.expect_navigation('**/next.html'):
        on_load = _registered_callback(fake_bidi_conn, 'browsingContext.load')
        on_load({'params': {'context': 'other-tab', 'url': 'http://x/next.html'}})
        on_load({'params': {'context': 'fake-context', 'url': 'http://x/other.html'}})
        on_load({'params': {'context': 'fake-context', 'url': 'http://x/next.html'}})
    assert _listeners(fake_bidi_conn, 'browsingContext.load') == []


@pytest.mark.asyncio
async def test_wait_for_network_idle_returns_once_quiet(fake_bidi_conn, fake_bidi_tab):
    await fake_bidi_tab.wait_for_network_idle(idle_time=0.01, timeout=1)
    subscribed = {
        event
        for command in fake_bidi_conn.commands_for('session.subscribe')
        for event in command['params']['events']
    }
    assert {'network.beforeRequestSent', 'network.responseCompleted', 'network.fetchError'} <= subscribed
    assert _listeners(fake_bidi_conn, 'network.beforeRequestSent') == []


@pytest.mark.asyncio
async def test_on_subscribes_this_context_and_translates_portable_events(
    fake_bidi_conn, fake_bidi_tab
):
    from pydoll.protocol.events import Event

    await fake_bidi_tab.on(Event.PAGE_LOADED, lambda _event: None)
    params = fake_bidi_conn.last_command('session.subscribe')['params']
    assert params['events'] == ['browsingContext.load']
    assert params['contexts'] == ['fake-context']
    assert _listeners(fake_bidi_conn, 'browsingContext.load')
