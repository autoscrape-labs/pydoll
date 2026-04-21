import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from pydoll.elements.shadow_root import ShadowRoot
from pydoll.elements.web_element import WebElement
from pydoll.protocol.dom.types import ShadowRootType
from pydoll.exceptions import ElementNotFound

@pytest_asyncio.fixture
async def mock_connection():
    mock = AsyncMock()
    mock.execute_command = AsyncMock()
    return mock

@pytest.fixture
def host_element(mock_connection):
    return WebElement(
        object_id='host-id',
        connection_handler=mock_connection,
        method='css',
        selector='#host'
    )

@pytest.fixture
def shadow_root(mock_connection, host_element):
    return ShadowRoot(
        object_id='shadow-id',
        connection_handler=mock_connection,
        mode=ShadowRootType.OPEN,
        host_element=host_element
    )

@pytest.mark.asyncio
async def test_get_children_elements_success(shadow_root, mock_connection):
    # Mock for JS execution to get array objectId
    mock_connection.execute_command.side_effect = [
        {'result': {'result': {'objectId': 'array-id'}}},  # evaluate
        {'result': {'result': [
            {'name': '0', 'value': {'objectId': 'child-1'}},
            {'name': '1', 'value': {'objectId': 'child-2'}}
        ]}},  # getProperties
        {'result': {'node': {'attributes': ['id', 'child1', 'class', 'btn']}}},  # describeNode attributes for child 1
        {'result': {'node': {'attributes': ['id', 'child2']}}},  # describeNode attributes for child 2
    ]
    
    children = await shadow_root.get_children_elements()
    assert len(children) == 2
    assert children[0]._object_id == 'child-1'
    assert children[1]._object_id == 'child-2'

@pytest.mark.asyncio
async def test_get_children_elements_empty(shadow_root, mock_connection):
    # Mock for empty response
    mock_connection.execute_command.return_value = {'result': {'result': {}}}
    
    children = await shadow_root.get_children_elements(raise_exc=False)
    assert children == []
    
    with pytest.raises(ElementNotFound):
        await shadow_root.get_children_elements(raise_exc=True)

@pytest.mark.asyncio
async def test_get_siblings_elements_via_host(shadow_root, host_element, mock_connection):
    # Mock for host's sibling retrieval
    mock_connection.execute_command.side_effect = [
        {'result': {'result': {'objectId': 'array-id'}}},  # evaluate
        {'result': {'result': [
            {'name': '0', 'value': {'objectId': 'sibling-1'}}
        ]}},  # getProperties
        {'result': {'node': {'attributes': ['id', 'sib1']}}},  # describeNode attributes
    ]
    
    # We also need to mock host_element's internal family element retrieval
    # Since shadow_root.get_siblings_elements calls host_element.get_siblings_elements
    siblings = await shadow_root.get_siblings_elements()
    assert len(siblings) == 1
    assert siblings[0]._object_id == 'sibling-1'

@pytest.mark.asyncio
async def test_get_siblings_no_host(mock_connection):
    # Test shadow root with no host_element
    sr = ShadowRoot(object_id='sr-id', connection_handler=mock_connection)
    siblings = await sr.get_siblings_elements()
    assert siblings == []
