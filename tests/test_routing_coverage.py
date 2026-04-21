import pytest
from unittest.mock import AsyncMock, MagicMock
from pydoll.elements.web_element import WebElement
from pydoll.interactions.iframe import IFrameContext
from pydoll.exceptions import ElementNotFound, WaitElementTimeout
from pydoll.constants import By
import asyncio

@pytest.mark.asyncio
async def test_find_elements_mixin_routing_coverage():
    handler = AsyncMock()
    handler.execute_command.return_value = {'result': {'node': {'nodeId': 1}}}
    
    el = WebElement(object_id='1', connection_handler=handler)
    
    # 1. Test _describe_node error path (Line 696)
    handler.execute_command.return_value = {'error': 'Node not found'}
    result = await el._describe_node('some-id')
    assert result == {}
    
    # 2. Test _resolve_routing with IFrameContext (Line 723)
    iframe_handler = AsyncMock()
    iframe_handler.execute_command.return_value = {'result': {'value': 'ok'}}
    
    ctx = IFrameContext(
        frame_id='frame-1',
        session_id='session-1',
        session_handler=iframe_handler
    )
    el._iframe_context = ctx
    
    h, sid = el._resolve_routing()
    assert h == iframe_handler
    assert sid == 'session-1'
    
    # 3. Test _execute_command with sessionId (Line 735)
    cmd = {'method': 'Runtime.evaluate', 'params': {'expression': '1+1'}}
    await el._execute_command(cmd)
    
    assert iframe_handler.execute_command.called
    assert cmd['sessionId'] == 'session-1' # Hits line 735
    
    # 4. Test fallback routing path (Line 726)
    el._iframe_context = None
    el._routing_session_handler = handler
    el._routing_session_id = 'routing-session-1'
    
    h, sid = el._resolve_routing()
    assert h == handler
    assert sid == 'routing-session-1'
    
    cmd2 = {'method': 'Foo.bar', 'params': {}}
    await el._execute_command(cmd2)
    assert cmd2['sessionId'] == 'routing-session-1'

@pytest.mark.asyncio
async def test_find_across_iframes_timeout_not_raise():
    handler = AsyncMock()
    el = WebElement(object_id='1', connection_handler=handler)
    
    # Mock attempt_find_across_iframes to return None
    el._attempt_find_across_iframes = AsyncMock(return_value=None)
    
    original_time = asyncio.get_event_loop().time
    calls = []
    def fake_time():
        calls.append(1)
        return original_time() + len(calls) * 20 
        
    async def fake_sleep(t):
        pass
    
    loop = asyncio.get_event_loop()
    loop.time = fake_time
    original_sleep = asyncio.sleep
    asyncio.sleep = fake_sleep
    
    try:
        # Line 409 coverage
        res = await el._find_across_iframes([], timeout=5, find_all=True, raise_exc=False)
        assert res == []
        res_none = await el._find_across_iframes([], timeout=5, find_all=False, raise_exc=False)
        assert res_none is None
    finally:
        loop.time = original_time
        asyncio.sleep = original_sleep

@pytest.mark.asyncio
async def test_attempt_find_across_iframes_not_iframe():
    handler = AsyncMock()
    el = WebElement(object_id='1', connection_handler=handler)
    
    # Line 445: element found but not an iframe
    mock_elem = MagicMock()
    mock_elem.is_iframe = False
    el._find_element = AsyncMock(return_value=mock_elem)
    
    segments = [(By.CSS_SELECTOR, 'div'), (By.CSS_SELECTOR, 'span')]
    res = await el._attempt_find_across_iframes(segments, find_all=False)
    assert res is None

@pytest.mark.asyncio
async def test_find_elements_empty_not_raise():
    # Line 554-557
    handler = AsyncMock()
    el = WebElement(object_id='1', connection_handler=handler)
    
    handler.execute_command.return_value = {'result': {}}
    
    res = await el._find_elements('id', 'test', raise_exc=False)
    assert res == []

@pytest.mark.asyncio
async def test_find_elements_keyerror_skip():
    # Line 574-575
    handler = AsyncMock()
    el = WebElement(object_id='1', connection_handler=handler)
    
    handler.execute_command.side_effect = [
        {'result': {'result': {'objectId': 'array-id'}}}, # eval result
        {'result': {'result': [{'name': '0', 'value': {'objectId': 'child-id'}}]}} # get_properties
    ]
    
    el._describe_node = AsyncMock(side_effect=KeyError('mock error'))
    
    res = await el._find_elements('id', 'test', raise_exc=False)
    assert res == []

@pytest.mark.asyncio
async def test_get_object_attributes_empty():
    # Line 602
    handler = AsyncMock()
    el = WebElement(object_id='1', connection_handler=handler)
    el._describe_node = AsyncMock(return_value={})
    
    res = await el._get_object_attributes('some-id')
    assert res == ['tag_name', '']

def test_get_find_elements_command_cases():
    # Cover lines 812, 823, 875-883, 889-891
    handler = AsyncMock()
    el = WebElement(object_id='1', connection_handler=handler)
    
    # By.ID (line 812)
    cmd = el._get_find_elements_command(By.ID, 'my-id', object_id='1')
    assert 'callFunctionOn' in cmd['method']
    
    # By.XPATH with object_id uses _get_find_elements_by_xpath_command (823) -> 875-883
    cmd = el._get_find_elements_command(By.XPATH, '//div', object_id='1')
    assert 'callFunctionOn' in cmd['method']
    
    # By.XPATH without object_id -> 889-891
    cmd2 = el._get_find_elements_command(By.XPATH, '//div', object_id='')
    assert 'evaluate' in cmd2['method']

@pytest.mark.asyncio
async def test_get_family_elements_coverage():
    # Coverage for lines 939-943, 957-958
    handler = AsyncMock()
    handler.execute_command.return_value = {'result': {'result': {'objectId': 'array-id'}}}
    
    # Create WebElement subclass that mimics an iframe but lacks id/execute_script
    class MockIframeElement(WebElement):
        @property
        def is_iframe(self):
            return True
            
        @property
        async def iframe_context(self):
            return "mocked-context"
            
    el = MockIframeElement(object_id='', connection_handler=handler)
    
    # Ensure properties exist for loop to be happy
    handler.execute_command.side_effect = [
        {'result': {'result': {'objectId': 'array-id'}}}, # evaluate
        {'result': {'result': []}} # get_properties returns empty so coverage continues past 957-958
    ]
    
    # Should hit lines 939-943 (fallback to evaluate since no object_id and no execute_script)
    # Also hits 957-958 (is_iframe property is true)
    res = await el._get_family_elements('script')
    assert res == []
