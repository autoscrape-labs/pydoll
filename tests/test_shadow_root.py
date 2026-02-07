from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio

from pydoll.elements.shadow_root import ShadowRoot
from pydoll.elements.web_element import WebElement
from pydoll.exceptions import ShadowRootNotFound
from pydoll.protocol.dom.types import ShadowRootType


@pytest_asyncio.fixture
async def mock_connection_handler():
    """Mock connection handler for ShadowRoot tests."""
    with patch('pydoll.connection.ConnectionHandler', autospec=True) as mock:
        handler = mock.return_value
        handler.execute_command = AsyncMock()
        yield handler


@pytest.fixture
def shadow_root(mock_connection_handler):
    """Basic ShadowRoot fixture with open mode."""
    return ShadowRoot(
        object_id='shadow-root-object-id',
        connection_handler=mock_connection_handler,
        mode=ShadowRootType.OPEN,
    )


@pytest.fixture
def host_element(mock_connection_handler):
    """WebElement fixture acting as shadow host."""
    return WebElement(
        object_id='host-object-id',
        connection_handler=mock_connection_handler,
        method='css',
        selector='#host',
        attributes_list=['id', 'host', 'tag_name', 'div'],
    )


class TestShadowRootInit:
    """Tests for ShadowRoot initialization."""

    def test_init_with_defaults(self, mock_connection_handler):
        sr = ShadowRoot(
            object_id='sr-id',
            connection_handler=mock_connection_handler,
        )
        assert sr._object_id == 'sr-id'
        assert sr._connection_handler is mock_connection_handler
        assert sr._mode == ShadowRootType.OPEN
        assert sr._host_element is None

    def test_init_with_all_params(self, mock_connection_handler, host_element):
        sr = ShadowRoot(
            object_id='sr-id',
            connection_handler=mock_connection_handler,
            mode=ShadowRootType.CLOSED,
            host_element=host_element,
        )
        assert sr._object_id == 'sr-id'
        assert sr._mode == ShadowRootType.CLOSED
        assert sr._host_element is host_element

    def test_init_with_user_agent_mode(self, mock_connection_handler):
        sr = ShadowRoot(
            object_id='sr-id',
            connection_handler=mock_connection_handler,
            mode=ShadowRootType.USER_AGENT,
        )
        assert sr._mode == ShadowRootType.USER_AGENT


class TestShadowRootProperties:
    """Tests for ShadowRoot properties."""

    def test_mode_property(self, shadow_root):
        assert shadow_root.mode == ShadowRootType.OPEN

    def test_host_element_none(self, shadow_root):
        assert shadow_root.host_element is None

    def test_host_element_with_reference(self, mock_connection_handler, host_element):
        sr = ShadowRoot(
            object_id='sr-id',
            connection_handler=mock_connection_handler,
            host_element=host_element,
        )
        assert sr.host_element is host_element


class TestShadowRootInnerHtml:
    """Tests for ShadowRoot.inner_html property."""

    @pytest.mark.asyncio
    async def test_inner_html(self, shadow_root):
        shadow_root._connection_handler.execute_command.return_value = {
            'result': {'outerHTML': '<div class="internal">Hello</div>'}
        }
        html = await shadow_root.inner_html
        assert html == '<div class="internal">Hello</div>'
        shadow_root._connection_handler.execute_command.assert_called_once()

    @pytest.mark.asyncio
    async def test_inner_html_empty(self, shadow_root):
        shadow_root._connection_handler.execute_command.return_value = {
            'result': {'outerHTML': ''}
        }
        html = await shadow_root.inner_html
        assert html == ''


class TestShadowRootRepr:
    """Tests for ShadowRoot string representations."""

    def test_repr(self, shadow_root):
        result = repr(shadow_root)
        assert 'ShadowRoot' in result
        assert 'open' in result
        assert 'shadow-root-object-id' in result

    def test_str(self, shadow_root):
        result = str(shadow_root)
        assert result == 'ShadowRoot(open)'

    def test_str_closed(self, mock_connection_handler):
        sr = ShadowRoot(
            object_id='sr-id',
            connection_handler=mock_connection_handler,
            mode=ShadowRootType.CLOSED,
        )
        assert str(sr) == 'ShadowRoot(closed)'


class TestShadowRootFindElements:
    """Tests for element finding within shadow root (inherited from FindElementsMixin)."""

    @pytest.mark.asyncio
    async def test_find_element_in_shadow_root(self, shadow_root):
        """find() should use relative querySelector via _object_id."""
        evaluate_response = {
            'result': {'result': {'objectId': 'found-element-id'}}
        }
        describe_response = {
            'result': {
                'node': {
                    'nodeName': 'BUTTON',
                    'attributes': ['class', 'btn-primary'],
                }
            }
        }
        shadow_root._connection_handler.execute_command.side_effect = [
            evaluate_response,
            describe_response,
        ]

        element = await shadow_root.find(class_name='btn-primary')

        assert isinstance(element, WebElement)
        assert element._object_id == 'found-element-id'
        call_args = shadow_root._connection_handler.execute_command.call_args_list
        first_command = call_args[0].args[0]
        assert first_command['params']['objectId'] == 'shadow-root-object-id'

    @pytest.mark.asyncio
    async def test_find_element_not_found_in_shadow_root(self, shadow_root):
        """find() should raise ElementNotFound when no element matches."""
        from pydoll.exceptions import ElementNotFound

        shadow_root._connection_handler.execute_command.return_value = {
            'result': {'result': {}}
        }

        with pytest.raises(ElementNotFound):
            await shadow_root.find(id='nonexistent')

    @pytest.mark.asyncio
    async def test_query_css_in_shadow_root(self, shadow_root):
        """query() should work with CSS selectors inside shadow root."""
        evaluate_response = {
            'result': {'result': {'objectId': 'queried-element-id'}}
        }
        describe_response = {
            'result': {
                'node': {
                    'nodeName': 'INPUT',
                    'attributes': ['type', 'email', 'name', 'user-email'],
                }
            }
        }
        shadow_root._connection_handler.execute_command.side_effect = [
            evaluate_response,
            describe_response,
        ]

        element = await shadow_root.query('input[type="email"]')

        assert isinstance(element, WebElement)
        assert element._object_id == 'queried-element-id'


class TestWebElementGetShadowRoot:
    """Tests for WebElement.get_shadow_root()."""

    @pytest.mark.asyncio
    async def test_get_shadow_root_success(self, host_element):
        """get_shadow_root() should return ShadowRoot when shadow root exists."""
        describe_response = {
            'result': {
                'node': {
                    'nodeName': 'DIV',
                    'attributes': ['id', 'host'],
                    'shadowRoots': [
                        {
                            'backendNodeId': 42,
                            'shadowRootType': 'open',
                        }
                    ],
                }
            }
        }
        resolve_response = {
            'result': {
                'object': {'objectId': 'shadow-root-resolved-id'}
            }
        }
        host_element._connection_handler.execute_command.side_effect = [
            describe_response,
            resolve_response,
        ]

        shadow_root = await host_element.get_shadow_root()

        assert isinstance(shadow_root, ShadowRoot)
        assert shadow_root._object_id == 'shadow-root-resolved-id'
        assert shadow_root.mode == ShadowRootType.OPEN
        assert shadow_root.host_element is host_element

    @pytest.mark.asyncio
    async def test_get_shadow_root_closed_mode(self, host_element):
        """get_shadow_root() should handle closed shadow roots."""
        describe_response = {
            'result': {
                'node': {
                    'nodeName': 'DIV',
                    'attributes': [],
                    'shadowRoots': [
                        {
                            'backendNodeId': 99,
                            'shadowRootType': 'closed',
                        }
                    ],
                }
            }
        }
        resolve_response = {
            'result': {
                'object': {'objectId': 'closed-shadow-id'}
            }
        }
        host_element._connection_handler.execute_command.side_effect = [
            describe_response,
            resolve_response,
        ]

        shadow_root = await host_element.get_shadow_root()

        assert shadow_root.mode == ShadowRootType.CLOSED

    @pytest.mark.asyncio
    async def test_get_shadow_root_not_found(self, host_element):
        """get_shadow_root() should raise ShadowRootNotFound when no shadow root."""
        describe_response = {
            'result': {
                'node': {
                    'nodeName': 'DIV',
                    'attributes': ['id', 'no-shadow'],
                }
            }
        }
        host_element._connection_handler.execute_command.return_value = describe_response

        with pytest.raises(ShadowRootNotFound):
            await host_element.get_shadow_root()

    @pytest.mark.asyncio
    async def test_get_shadow_root_empty_shadow_roots_list(self, host_element):
        """get_shadow_root() should raise when shadowRoots is empty list."""
        describe_response = {
            'result': {
                'node': {
                    'nodeName': 'DIV',
                    'attributes': [],
                    'shadowRoots': [],
                }
            }
        }
        host_element._connection_handler.execute_command.return_value = describe_response

        with pytest.raises(ShadowRootNotFound):
            await host_element.get_shadow_root()

    @pytest.mark.asyncio
    async def test_get_shadow_root_no_node_id(self, host_element):
        """get_shadow_root() should raise when shadow root has no nodeId."""
        describe_response = {
            'result': {
                'node': {
                    'nodeName': 'DIV',
                    'attributes': [],
                    'shadowRoots': [
                        {
                            'shadowRootType': 'open',
                        }
                    ],
                }
            }
        }
        host_element._connection_handler.execute_command.return_value = describe_response

        with pytest.raises(ShadowRootNotFound):
            await host_element.get_shadow_root()
