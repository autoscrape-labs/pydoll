import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from pydoll.browser.tab import Tab
from pydoll.elements.shadow_root import ShadowRoot
from pydoll.elements.web_element import WebElement
from pydoll.exceptions import (
    CommandExecutionTimeout,
    ElementNotFound,
    ShadowRootNotFound,
    WaitElementTimeout,
    WebSocketConnectionClosed,
)
from pydoll.interactions.iframe import IFrameContext
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
    """Tests for element finding within shadow root (CSS only)."""

    @pytest.mark.asyncio
    async def test_find_raises_not_implemented(self, shadow_root):
        """find() should raise NotImplementedError on ShadowRoot."""
        with pytest.raises(NotImplementedError, match='find\\(\\) is not supported on ShadowRoot'):
            await shadow_root.find(class_name='btn-primary')

    @pytest.mark.asyncio
    async def test_query_xpath_raises_not_implemented(self, shadow_root):
        """query() with XPath should raise NotImplementedError on ShadowRoot."""
        with pytest.raises(NotImplementedError, match='XPath is not supported on ShadowRoot'):
            await shadow_root.query('.//button')

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


# --- Tab.find_shadow_roots() tests ---


@pytest_asyncio.fixture
async def tab_connection_handler():
    """Mock connection handler for Tab tests."""
    with patch('pydoll.connection.ConnectionHandler', autospec=True) as mock:
        handler = mock.return_value
        handler.execute_command = AsyncMock()
        handler.register_callback = AsyncMock()
        handler.remove_callback = AsyncMock()
        handler.clear_callbacks = AsyncMock()
        handler.network_logs = []
        handler.dialog = None
        handler._connection_port = 9222
        yield handler


@pytest_asyncio.fixture
async def tab(tab_connection_handler):
    """Tab fixture with mocked dependencies."""
    browser = MagicMock()
    browser.options = MagicMock()
    with patch('pydoll.browser.tab.ConnectionHandler', return_value=tab_connection_handler):
        return Tab(
            browser=browser,
            connection_port=9222,
            target_id=f'test-target-{uuid.uuid4().hex[:8]}',
        )


class TestTabFindShadowRoots:
    """Tests for Tab.find_shadow_roots()."""

    @pytest.mark.asyncio
    async def test_find_shadow_roots_single(self, tab):
        """Should return a single shadow root found in the page."""
        get_doc_response = {
            'result': {
                'root': {
                    'nodeId': 1,
                    'backendNodeId': 1,
                    'nodeName': '#document',
                    'children': [
                        {
                            'nodeId': 2,
                            'backendNodeId': 2,
                            'nodeName': 'HTML',
                            'children': [
                                {
                                    'nodeId': 3,
                                    'backendNodeId': 3,
                                    'nodeName': 'BODY',
                                    'children': [
                                        {
                                            'nodeId': 4,
                                            'backendNodeId': 10,
                                            'nodeName': 'DIV',
                                            'attributes': ['id', 'host'],
                                            'shadowRoots': [
                                                {
                                                    'nodeId': 5,
                                                    'backendNodeId': 20,
                                                    'shadowRootType': 'open',
                                                    'children': [],
                                                }
                                            ],
                                        }
                                    ],
                                }
                            ],
                        }
                    ],
                }
            }
        }
        tab._connection_handler.execute_command.side_effect = [
            get_doc_response,
            {'result': {'object': {'objectId': 'shadow-obj-1'}}},
            {'result': {'object': {'objectId': 'host-obj-1'}}},
            {'result': {'node': {'nodeName': 'DIV', 'attributes': ['id', 'host']}}},
        ]

        result = await tab.find_shadow_roots()

        assert len(result) == 1
        assert isinstance(result[0], ShadowRoot)
        assert result[0]._object_id == 'shadow-obj-1'
        assert result[0].mode == ShadowRootType.OPEN
        assert result[0].host_element is not None
        assert result[0].host_element._object_id == 'host-obj-1'

    @pytest.mark.asyncio
    async def test_find_shadow_roots_none_found(self, tab):
        """Should return empty list when no shadow roots exist."""
        get_doc_response = {
            'result': {
                'root': {
                    'nodeId': 1,
                    'backendNodeId': 1,
                    'nodeName': '#document',
                    'children': [
                        {
                            'nodeId': 2,
                            'backendNodeId': 2,
                            'nodeName': 'HTML',
                            'children': [],
                        }
                    ],
                }
            }
        }
        tab._connection_handler.execute_command.return_value = get_doc_response

        result = await tab.find_shadow_roots()

        assert result == []

    @pytest.mark.asyncio
    async def test_find_shadow_roots_multiple(self, tab):
        """Should return multiple shadow roots at different depths."""
        get_doc_response = {
            'result': {
                'root': {
                    'nodeId': 1,
                    'backendNodeId': 1,
                    'nodeName': '#document',
                    'children': [
                        {
                            'nodeId': 2,
                            'backendNodeId': 2,
                            'nodeName': 'HTML',
                            'children': [
                                {
                                    'nodeId': 3,
                                    'backendNodeId': 10,
                                    'nodeName': 'DIV',
                                    'shadowRoots': [
                                        {
                                            'nodeId': 4,
                                            'backendNodeId': 20,
                                            'shadowRootType': 'open',
                                            'children': [],
                                        }
                                    ],
                                },
                                {
                                    'nodeId': 5,
                                    'backendNodeId': 11,
                                    'nodeName': 'CUSTOM-ELEMENT',
                                    'shadowRoots': [
                                        {
                                            'nodeId': 6,
                                            'backendNodeId': 30,
                                            'shadowRootType': 'closed',
                                            'children': [],
                                        }
                                    ],
                                },
                            ],
                        }
                    ],
                }
            }
        }
        tab._connection_handler.execute_command.side_effect = [
            get_doc_response,
            {'result': {'object': {'objectId': 'shadow-obj-1'}}},
            {'result': {'object': {'objectId': 'host-obj-1'}}},
            {'result': {'node': {'nodeName': 'DIV', 'attributes': ['id', 'host1']}}},
            {'result': {'object': {'objectId': 'shadow-obj-2'}}},
            {'result': {'object': {'objectId': 'host-obj-2'}}},
            {'result': {'node': {'nodeName': 'CUSTOM-ELEMENT', 'attributes': []}}},
        ]

        result = await tab.find_shadow_roots()

        assert len(result) == 2
        assert result[0].mode == ShadowRootType.OPEN
        assert result[1].mode == ShadowRootType.CLOSED

    @pytest.mark.asyncio
    async def test_find_shadow_roots_nested_in_shadow_root(self, tab):
        """Should find shadow roots nested inside other shadow roots."""
        get_doc_response = {
            'result': {
                'root': {
                    'nodeId': 1,
                    'backendNodeId': 1,
                    'nodeName': '#document',
                    'children': [
                        {
                            'nodeId': 2,
                            'backendNodeId': 10,
                            'nodeName': 'DIV',
                            'shadowRoots': [
                                {
                                    'nodeId': 3,
                                    'backendNodeId': 20,
                                    'shadowRootType': 'open',
                                    'children': [
                                        {
                                            'nodeId': 4,
                                            'backendNodeId': 11,
                                            'nodeName': 'INNER-HOST',
                                            'shadowRoots': [
                                                {
                                                    'nodeId': 5,
                                                    'backendNodeId': 30,
                                                    'shadowRootType': 'closed',
                                                    'children': [],
                                                }
                                            ],
                                        }
                                    ],
                                }
                            ],
                        }
                    ],
                }
            }
        }
        tab._connection_handler.execute_command.side_effect = [
            get_doc_response,
            {'result': {'object': {'objectId': 'shadow-outer'}}},
            {'result': {'object': {'objectId': 'host-outer'}}},
            {'result': {'node': {'nodeName': 'DIV', 'attributes': []}}},
            {'result': {'object': {'objectId': 'shadow-inner'}}},
            {'result': {'object': {'objectId': 'host-inner'}}},
            {'result': {'node': {'nodeName': 'INNER-HOST', 'attributes': []}}},
        ]

        result = await tab.find_shadow_roots()

        assert len(result) == 2
        assert result[0]._object_id == 'shadow-outer'
        assert result[1]._object_id == 'shadow-inner'

    @pytest.mark.asyncio
    async def test_find_shadow_roots_in_iframe(self, tab):
        """Should find shadow roots inside iframe content documents."""
        get_doc_response = {
            'result': {
                'root': {
                    'nodeId': 1,
                    'backendNodeId': 1,
                    'nodeName': '#document',
                    'children': [
                        {
                            'nodeId': 2,
                            'backendNodeId': 2,
                            'nodeName': 'HTML',
                            'children': [
                                {
                                    'nodeId': 3,
                                    'backendNodeId': 3,
                                    'nodeName': 'IFRAME',
                                    'contentDocument': {
                                        'nodeId': 4,
                                        'backendNodeId': 4,
                                        'nodeName': '#document',
                                        'children': [
                                            {
                                                'nodeId': 5,
                                                'backendNodeId': 15,
                                                'nodeName': 'BODY',
                                                'shadowRoots': [
                                                    {
                                                        'nodeId': 6,
                                                        'backendNodeId': 25,
                                                        'shadowRootType': 'closed',
                                                        'children': [],
                                                    }
                                                ],
                                            }
                                        ],
                                    },
                                }
                            ],
                        }
                    ],
                }
            }
        }
        tab._connection_handler.execute_command.side_effect = [
            get_doc_response,
            {'result': {'object': {'objectId': 'iframe-shadow-obj'}}},
            {'result': {'object': {'objectId': 'iframe-host-obj'}}},
            {'result': {'node': {'nodeName': 'BODY', 'attributes': []}}},
        ]

        result = await tab.find_shadow_roots()

        assert len(result) == 1
        assert result[0]._object_id == 'iframe-shadow-obj'
        assert result[0].mode == ShadowRootType.CLOSED

    @pytest.mark.asyncio
    async def test_find_shadow_roots_skips_unresolvable(self, tab):
        """Should skip shadow roots that fail to resolve."""
        get_doc_response = {
            'result': {
                'root': {
                    'nodeId': 1,
                    'backendNodeId': 1,
                    'nodeName': '#document',
                    'children': [
                        {
                            'nodeId': 2,
                            'backendNodeId': 10,
                            'nodeName': 'DIV',
                            'shadowRoots': [
                                {
                                    'nodeId': 3,
                                    'backendNodeId': 20,
                                    'shadowRootType': 'open',
                                    'children': [],
                                }
                            ],
                        },
                        {
                            'nodeId': 4,
                            'backendNodeId': 11,
                            'nodeName': 'OTHER',
                            'shadowRoots': [
                                {
                                    'nodeId': 5,
                                    'backendNodeId': 30,
                                    'shadowRootType': 'open',
                                    'children': [],
                                }
                            ],
                        },
                    ],
                }
            }
        }
        tab._connection_handler.execute_command.side_effect = [
            get_doc_response,
            {'result': {'object': {'objectId': 'shadow-ok'}}},
            {'result': {'object': {'objectId': 'host-ok'}}},
            {'result': {'node': {'nodeName': 'DIV', 'attributes': []}}},
            CommandExecutionTimeout(),
        ]

        result = await tab.find_shadow_roots()

        assert len(result) == 1
        assert result[0]._object_id == 'shadow-ok'

    @pytest.mark.asyncio
    async def test_find_shadow_roots_host_resolution_fails_gracefully(self, tab):
        """Shadow root should still be returned when host resolution fails."""
        get_doc_response = {
            'result': {
                'root': {
                    'nodeId': 1,
                    'backendNodeId': 1,
                    'nodeName': '#document',
                    'children': [
                        {
                            'nodeId': 2,
                            'backendNodeId': 10,
                            'nodeName': 'DIV',
                            'shadowRoots': [
                                {
                                    'nodeId': 3,
                                    'backendNodeId': 20,
                                    'shadowRootType': 'open',
                                    'children': [],
                                }
                            ],
                        }
                    ],
                }
            }
        }
        tab._connection_handler.execute_command.side_effect = [
            get_doc_response,
            {'result': {'object': {'objectId': 'shadow-obj'}}},
            CommandExecutionTimeout(),
        ]

        result = await tab.find_shadow_roots()

        assert len(result) == 1
        assert result[0]._object_id == 'shadow-obj'
        assert result[0].host_element is None

    @pytest.mark.asyncio
    async def test_find_shadow_roots_skips_missing_backend_id(self, tab):
        """Should skip shadow roots without backendNodeId."""
        get_doc_response = {
            'result': {
                'root': {
                    'nodeId': 1,
                    'backendNodeId': 1,
                    'nodeName': '#document',
                    'children': [
                        {
                            'nodeId': 2,
                            'backendNodeId': 10,
                            'nodeName': 'DIV',
                            'shadowRoots': [
                                {
                                    'shadowRootType': 'open',
                                    'children': [],
                                }
                            ],
                        }
                    ],
                }
            }
        }
        tab._connection_handler.execute_command.return_value = get_doc_response

        result = await tab.find_shadow_roots()

        assert result == []


class TestCollectShadowRootsFromTree:
    """Tests for the _collect_shadow_roots_from_tree static helper."""

    def test_empty_tree(self):
        results = []
        Tab._collect_shadow_roots_from_tree({}, results)
        assert results == []

    def test_no_shadow_roots(self):
        tree = {
            'nodeId': 1,
            'backendNodeId': 1,
            'children': [
                {'nodeId': 2, 'backendNodeId': 2},
            ],
        }
        results = []
        Tab._collect_shadow_roots_from_tree(tree, results)
        assert results == []

    def test_collects_shadow_root(self):
        shadow = {'backendNodeId': 20, 'shadowRootType': 'open', 'children': []}
        tree = {
            'backendNodeId': 10,
            'shadowRoots': [shadow],
        }
        results = []
        Tab._collect_shadow_roots_from_tree(tree, results)
        assert len(results) == 1
        assert results[0] == (shadow, 10)

    def test_collects_from_content_document(self):
        shadow = {'backendNodeId': 30, 'shadowRootType': 'closed', 'children': []}
        tree = {
            'backendNodeId': 1,
            'children': [
                {
                    'backendNodeId': 2,
                    'nodeName': 'IFRAME',
                    'contentDocument': {
                        'backendNodeId': 3,
                        'children': [
                            {
                                'backendNodeId': 15,
                                'shadowRoots': [shadow],
                            }
                        ],
                    },
                }
            ],
        }
        results = []
        Tab._collect_shadow_roots_from_tree(tree, results)
        assert len(results) == 1
        assert results[0] == (shadow, 15)

    def test_collects_nested_shadow_roots(self):
        inner_shadow = {'backendNodeId': 40, 'shadowRootType': 'closed', 'children': []}
        outer_shadow = {
            'backendNodeId': 20,
            'shadowRootType': 'open',
            'children': [
                {
                    'backendNodeId': 30,
                    'shadowRoots': [inner_shadow],
                }
            ],
        }
        tree = {
            'backendNodeId': 10,
            'shadowRoots': [outer_shadow],
        }
        results = []
        Tab._collect_shadow_roots_from_tree(tree, results)
        assert len(results) == 2
        assert results[0] == (outer_shadow, 10)
        assert results[1] == (inner_shadow, 30)


class TestTabFindShadowRootsDeep:
    """Tests for Tab.find_shadow_roots(deep=True) — OOPIF traversal."""

    @pytest.mark.asyncio
    async def test_deep_false_same_as_default(self, tab):
        """deep=False should behave identically to the default (no OOPIF traversal)."""
        get_doc_response = {
            'result': {
                'root': {
                    'nodeId': 1,
                    'backendNodeId': 1,
                    'nodeName': '#document',
                    'children': [
                        {
                            'nodeId': 2,
                            'backendNodeId': 10,
                            'nodeName': 'DIV',
                            'shadowRoots': [
                                {
                                    'nodeId': 3,
                                    'backendNodeId': 20,
                                    'shadowRootType': 'open',
                                    'children': [],
                                }
                            ],
                        }
                    ],
                }
            }
        }
        tab._connection_handler.execute_command.side_effect = [
            get_doc_response,
            {'result': {'object': {'objectId': 'shadow-obj-1'}}},
            {'result': {'object': {'objectId': 'host-obj-1'}}},
            {'result': {'node': {'nodeName': 'DIV', 'attributes': ['id', 'host']}}},
        ]

        result = await tab.find_shadow_roots(deep=False)

        assert len(result) == 1
        assert result[0]._object_id == 'shadow-obj-1'

    @pytest.mark.asyncio
    async def test_deep_collects_oopif_shadow_roots(self, tab):
        """deep=True should discover shadow roots inside OOPIF targets."""
        # Main doc has no shadow roots
        get_doc_response = {
            'result': {
                'root': {
                    'nodeId': 1,
                    'backendNodeId': 1,
                    'nodeName': '#document',
                    'children': [],
                }
            }
        }
        tab._connection_handler.execute_command.return_value = get_doc_response

        # Mock the browser-level ConnectionHandler used in _collect_oopif_shadow_roots
        mock_browser_handler = AsyncMock()
        mock_browser_handler.execute_command = AsyncMock()
        mock_browser_handler.execute_command.side_effect = [
            # Target.getTargets
            {
                'result': {
                    'targetInfos': [
                        {'targetId': 'oopif-1', 'type': 'iframe', 'url': 'https://cf.example.com'},
                    ]
                }
            },
            # Target.attachToTarget
            {'result': {'sessionId': 'session-1'}},
            # DOM.getDocument (in OOPIF)
            {
                'result': {
                    'root': {
                        'nodeId': 1,
                        'backendNodeId': 100,
                        'nodeName': '#document',
                        'children': [
                            {
                                'nodeId': 2,
                                'backendNodeId': 200,
                                'nodeName': 'BODY',
                                'shadowRoots': [
                                    {
                                        'nodeId': 3,
                                        'backendNodeId': 300,
                                        'shadowRootType': 'closed',
                                        'children': [],
                                    }
                                ],
                            }
                        ],
                    }
                }
            },
            # DOM.resolveNode (shadow root)
            {'result': {'object': {'objectId': 'oopif-shadow-obj'}}},
            # DOM.resolveNode (host element)
            {'result': {'object': {'objectId': 'oopif-host-obj'}}},
            # DOM.describeNode (host element attrs)
            {'result': {'node': {'nodeName': 'BODY', 'attributes': []}}},
        ]

        with patch('pydoll.browser.tab.ConnectionHandler', return_value=mock_browser_handler):
            result = await tab.find_shadow_roots(deep=True)

        assert len(result) == 1
        sr = result[0]
        assert sr._object_id == 'oopif-shadow-obj'
        assert sr.mode == ShadowRootType.CLOSED
        assert sr.host_element is not None
        assert sr.host_element._object_id == 'oopif-host-obj'

    @pytest.mark.asyncio
    async def test_deep_no_oopif_targets(self, tab):
        """deep=True with no iframe targets returns only main-doc roots."""
        get_doc_response = {
            'result': {
                'root': {
                    'nodeId': 1,
                    'backendNodeId': 1,
                    'nodeName': '#document',
                    'children': [],
                }
            }
        }
        tab._connection_handler.execute_command.return_value = get_doc_response

        mock_browser_handler = AsyncMock()
        mock_browser_handler.execute_command = AsyncMock()
        mock_browser_handler.execute_command.return_value = {
            'result': {'targetInfos': []}
        }

        with patch('pydoll.browser.tab.ConnectionHandler', return_value=mock_browser_handler):
            result = await tab.find_shadow_roots(deep=True)

        assert result == []

    @pytest.mark.asyncio
    async def test_deep_oopif_attachment_fails_gracefully(self, tab):
        """When an OOPIF target fails to attach, others should still be collected."""
        get_doc_response = {
            'result': {
                'root': {
                    'nodeId': 1,
                    'backendNodeId': 1,
                    'nodeName': '#document',
                    'children': [],
                }
            }
        }
        tab._connection_handler.execute_command.return_value = get_doc_response

        mock_browser_handler = AsyncMock()
        mock_browser_handler.execute_command = AsyncMock()
        mock_browser_handler.execute_command.side_effect = [
            # Target.getTargets — two iframe targets
            {
                'result': {
                    'targetInfos': [
                        {'targetId': 'fail-target', 'type': 'iframe', 'url': 'https://a.com'},
                        {'targetId': 'ok-target', 'type': 'iframe', 'url': 'https://b.com'},
                    ]
                }
            },
            # First target: attachment fails
            WebSocketConnectionClosed(),
            # Second target: attachment succeeds
            {'result': {'sessionId': 'session-ok'}},
            # DOM.getDocument for second target
            {
                'result': {
                    'root': {
                        'nodeId': 1,
                        'backendNodeId': 50,
                        'nodeName': '#document',
                        'children': [
                            {
                                'nodeId': 2,
                                'backendNodeId': 60,
                                'nodeName': 'DIV',
                                'shadowRoots': [
                                    {
                                        'nodeId': 3,
                                        'backendNodeId': 70,
                                        'shadowRootType': 'open',
                                        'children': [],
                                    }
                                ],
                            }
                        ],
                    }
                }
            },
            # DOM.resolveNode (shadow root)
            {'result': {'object': {'objectId': 'sr-from-ok-target'}}},
            # DOM.resolveNode (host element)
            {'result': {'object': {'objectId': 'host-from-ok-target'}}},
            # DOM.describeNode (host attrs)
            {'result': {'node': {'nodeName': 'DIV', 'attributes': ['id', 'widget']}}},
        ]

        with patch('pydoll.browser.tab.ConnectionHandler', return_value=mock_browser_handler):
            result = await tab.find_shadow_roots(deep=True)

        assert len(result) == 1
        assert result[0]._object_id == 'sr-from-ok-target'

    @pytest.mark.asyncio
    async def test_deep_oopif_shadow_root_has_routing_context(self, tab):
        """ShadowRoot from OOPIF should have _iframe_context with correct routing."""
        get_doc_response = {
            'result': {
                'root': {
                    'nodeId': 1,
                    'backendNodeId': 1,
                    'nodeName': '#document',
                    'children': [],
                }
            }
        }
        tab._connection_handler.execute_command.return_value = get_doc_response

        mock_browser_handler = AsyncMock()
        mock_browser_handler.execute_command = AsyncMock()
        mock_browser_handler.execute_command.side_effect = [
            # Target.getTargets
            {
                'result': {
                    'targetInfos': [
                        {'targetId': 'oopif-42', 'type': 'iframe', 'url': 'https://cf.example.com'},
                    ]
                }
            },
            # Target.attachToTarget
            {'result': {'sessionId': 'sess-42'}},
            # DOM.getDocument
            {
                'result': {
                    'root': {
                        'nodeId': 1,
                        'backendNodeId': 100,
                        'nodeName': '#document',
                        'children': [
                            {
                                'nodeId': 2,
                                'backendNodeId': 200,
                                'nodeName': 'DIV',
                                'shadowRoots': [
                                    {
                                        'nodeId': 3,
                                        'backendNodeId': 300,
                                        'shadowRootType': 'closed',
                                        'children': [],
                                    }
                                ],
                            }
                        ],
                    }
                }
            },
            # DOM.resolveNode (shadow root)
            {'result': {'object': {'objectId': 'sr-obj-42'}}},
            # DOM.resolveNode (host element)
            {'result': {'object': {'objectId': 'host-obj-42'}}},
            # DOM.describeNode (host attrs)
            {'result': {'node': {'nodeName': 'DIV', 'attributes': ['class', 'turnstile']}}},
        ]

        with patch('pydoll.browser.tab.ConnectionHandler', return_value=mock_browser_handler):
            result = await tab.find_shadow_roots(deep=True)

        assert len(result) == 1
        sr = result[0]

        # Verify the ShadowRoot inherited IFrameContext from host
        ctx = getattr(sr, '_iframe_context', None)
        assert ctx is not None
        assert isinstance(ctx, IFrameContext)
        assert ctx.frame_id == 'oopif-42'
        assert ctx.session_id == 'sess-42'
        assert ctx.session_handler is mock_browser_handler

    @pytest.mark.asyncio
    async def test_deep_combines_main_and_oopif_roots(self, tab):
        """deep=True should return both main-doc and OOPIF shadow roots."""
        # Main doc has one shadow root
        get_doc_response = {
            'result': {
                'root': {
                    'nodeId': 1,
                    'backendNodeId': 1,
                    'nodeName': '#document',
                    'children': [
                        {
                            'nodeId': 2,
                            'backendNodeId': 10,
                            'nodeName': 'DIV',
                            'shadowRoots': [
                                {
                                    'nodeId': 3,
                                    'backendNodeId': 20,
                                    'shadowRootType': 'open',
                                    'children': [],
                                }
                            ],
                        }
                    ],
                }
            }
        }
        tab._connection_handler.execute_command.side_effect = [
            get_doc_response,
            # resolve shadow root
            {'result': {'object': {'objectId': 'main-shadow'}}},
            # resolve host
            {'result': {'object': {'objectId': 'main-host'}}},
            # describe host
            {'result': {'node': {'nodeName': 'DIV', 'attributes': ['id', 'main']}}},
        ]

        mock_browser_handler = AsyncMock()
        mock_browser_handler.execute_command = AsyncMock()
        mock_browser_handler.execute_command.side_effect = [
            # Target.getTargets
            {
                'result': {
                    'targetInfos': [
                        {'targetId': 'oopif-1', 'type': 'iframe', 'url': 'https://cf.example.com'},
                    ]
                }
            },
            # Target.attachToTarget
            {'result': {'sessionId': 'session-1'}},
            # DOM.getDocument
            {
                'result': {
                    'root': {
                        'nodeId': 1,
                        'backendNodeId': 50,
                        'nodeName': '#document',
                        'children': [
                            {
                                'nodeId': 2,
                                'backendNodeId': 60,
                                'nodeName': 'BODY',
                                'shadowRoots': [
                                    {
                                        'nodeId': 3,
                                        'backendNodeId': 70,
                                        'shadowRootType': 'closed',
                                        'children': [],
                                    }
                                ],
                            }
                        ],
                    }
                }
            },
            # DOM.resolveNode (shadow root)
            {'result': {'object': {'objectId': 'oopif-shadow'}}},
            # DOM.resolveNode (host)
            {'result': {'object': {'objectId': 'oopif-host'}}},
            # DOM.describeNode (host attrs)
            {'result': {'node': {'nodeName': 'BODY', 'attributes': []}}},
        ]

        with patch('pydoll.browser.tab.ConnectionHandler', return_value=mock_browser_handler):
            result = await tab.find_shadow_roots(deep=True)

        assert len(result) == 2
        assert result[0]._object_id == 'main-shadow'
        assert result[0].mode == ShadowRootType.OPEN
        assert result[1]._object_id == 'oopif-shadow'
        assert result[1].mode == ShadowRootType.CLOSED

    @pytest.mark.asyncio
    async def test_deep_oopif_no_host_sets_iframe_context_on_shadow_root(self, tab):
        """When host resolution fails, IFrameContext should be set directly on ShadowRoot."""
        get_doc_response = {
            'result': {
                'root': {
                    'nodeId': 1,
                    'backendNodeId': 1,
                    'nodeName': '#document',
                    'children': [],
                }
            }
        }
        tab._connection_handler.execute_command.return_value = get_doc_response

        mock_browser_handler = AsyncMock()
        mock_browser_handler.execute_command = AsyncMock()
        mock_browser_handler.execute_command.side_effect = [
            # Target.getTargets
            {
                'result': {
                    'targetInfos': [
                        {'targetId': 'oopif-99', 'type': 'iframe', 'url': 'https://cf.example.com'},
                    ]
                }
            },
            # Target.attachToTarget
            {'result': {'sessionId': 'sess-99'}},
            # DOM.getDocument
            {
                'result': {
                    'root': {
                        'nodeId': 1,
                        'backendNodeId': 100,
                        'nodeName': '#document',
                        'children': [
                            {
                                'nodeId': 2,
                                'backendNodeId': 200,
                                'nodeName': 'DIV',
                                'shadowRoots': [
                                    {
                                        'nodeId': 3,
                                        'backendNodeId': 300,
                                        'shadowRootType': 'open',
                                        'children': [],
                                    }
                                ],
                            }
                        ],
                    }
                }
            },
            # DOM.resolveNode (shadow root) - success
            {'result': {'object': {'objectId': 'sr-obj-99'}}},
            # DOM.resolveNode (host element) - fails
            CommandExecutionTimeout(),
        ]

        with patch('pydoll.browser.tab.ConnectionHandler', return_value=mock_browser_handler):
            result = await tab.find_shadow_roots(deep=True)

        assert len(result) == 1
        sr = result[0]
        assert sr.host_element is None
        # IFrameContext set directly on ShadowRoot since no host
        ctx = getattr(sr, '_iframe_context', None)
        assert ctx is not None
        assert ctx.frame_id == 'oopif-99'
        assert ctx.session_id == 'sess-99'


class TestTabFindShadowRootsTimeout:
    """Tests for Tab.find_shadow_roots(timeout=...) — polling behavior."""

    @pytest.mark.asyncio
    async def test_timeout_zero_returns_immediately(self, tab):
        """timeout=0 (default) should return immediately without polling."""
        get_doc_response = {
            'result': {
                'root': {
                    'nodeId': 1,
                    'backendNodeId': 1,
                    'nodeName': '#document',
                    'children': [],
                }
            }
        }
        tab._connection_handler.execute_command.return_value = get_doc_response

        result = await tab.find_shadow_roots(timeout=0)

        assert result == []

    @pytest.mark.asyncio
    async def test_timeout_raises_when_no_shadow_roots_found(self, tab):
        """Should raise WaitElementTimeout when no shadow roots appear within timeout."""
        get_doc_response = {
            'result': {
                'root': {
                    'nodeId': 1,
                    'backendNodeId': 1,
                    'nodeName': '#document',
                    'children': [],
                }
            }
        }
        tab._connection_handler.execute_command.return_value = get_doc_response

        with pytest.raises(WaitElementTimeout):
            await tab.find_shadow_roots(timeout=1)

    @pytest.mark.asyncio
    async def test_timeout_returns_when_shadow_roots_appear(self, tab):
        """Should return shadow roots as soon as they appear during polling."""
        empty_doc = {
            'result': {
                'root': {
                    'nodeId': 1,
                    'backendNodeId': 1,
                    'nodeName': '#document',
                    'children': [],
                }
            }
        }
        doc_with_shadow = {
            'result': {
                'root': {
                    'nodeId': 1,
                    'backendNodeId': 1,
                    'nodeName': '#document',
                    'children': [
                        {
                            'nodeId': 2,
                            'backendNodeId': 10,
                            'nodeName': 'DIV',
                            'shadowRoots': [
                                {
                                    'nodeId': 3,
                                    'backendNodeId': 20,
                                    'shadowRootType': 'open',
                                    'children': [],
                                }
                            ],
                        }
                    ],
                }
            }
        }
        tab._connection_handler.execute_command.side_effect = [
            # First poll: empty
            empty_doc,
            # Second poll: shadow root appears
            doc_with_shadow,
            # resolve shadow root
            {'result': {'object': {'objectId': 'shadow-obj'}}},
            # resolve host
            {'result': {'object': {'objectId': 'host-obj'}}},
            # describe host attrs
            {'result': {'node': {'nodeName': 'DIV', 'attributes': ['id', 'host']}}},
        ]

        result = await tab.find_shadow_roots(timeout=5)

        assert len(result) == 1
        assert result[0]._object_id == 'shadow-obj'

    @pytest.mark.asyncio
    async def test_timeout_with_deep_waits_for_oopif_roots(self, tab):
        """timeout + deep=True should poll until OOPIF shadow roots appear."""
        empty_doc = {
            'result': {
                'root': {
                    'nodeId': 1,
                    'backendNodeId': 1,
                    'nodeName': '#document',
                    'children': [],
                }
            }
        }
        tab._connection_handler.execute_command.return_value = empty_doc

        call_count = 0

        async def browser_side_effect(cmd, **kwargs):
            nonlocal call_count
            call_count += 1
            # First cycle: no iframe targets
            if call_count == 1:
                return {'result': {'targetInfos': []}}
            # Second cycle: iframe target appears
            if call_count == 2:
                return {
                    'result': {
                        'targetInfos': [
                            {'targetId': 'oopif-1', 'type': 'iframe', 'url': 'https://cf.test'},
                        ]
                    }
                }
            if call_count == 3:
                return {'result': {'sessionId': 'sess-1'}}
            if call_count == 4:
                return {
                    'result': {
                        'root': {
                            'nodeId': 1,
                            'backendNodeId': 100,
                            'nodeName': '#document',
                            'children': [
                                {
                                    'nodeId': 2,
                                    'backendNodeId': 200,
                                    'nodeName': 'BODY',
                                    'shadowRoots': [
                                        {
                                            'nodeId': 3,
                                            'backendNodeId': 300,
                                            'shadowRootType': 'closed',
                                            'children': [],
                                        }
                                    ],
                                }
                            ],
                        }
                    }
                }
            if call_count == 5:
                return {'result': {'object': {'objectId': 'oopif-sr-obj'}}}
            if call_count == 6:
                return {'result': {'object': {'objectId': 'oopif-host-obj'}}}
            if call_count == 7:
                return {'result': {'node': {'nodeName': 'BODY', 'attributes': []}}}
            return {}

        mock_browser_handler = AsyncMock()
        mock_browser_handler.execute_command = AsyncMock(side_effect=browser_side_effect)

        with patch('pydoll.browser.tab.ConnectionHandler', return_value=mock_browser_handler):
            result = await tab.find_shadow_roots(deep=True, timeout=5)

        assert len(result) == 1
        assert result[0]._object_id == 'oopif-sr-obj'
        assert result[0].mode == ShadowRootType.CLOSED


# --- WebElement.get_shadow_root(timeout=...) tests ---


class TestGetShadowRootTimeout:
    """Tests for WebElement.get_shadow_root(timeout=...) — polling behavior."""

    @pytest.mark.asyncio
    async def test_timeout_zero_raises_immediately(self, mock_connection_handler):
        """timeout=0 (default) should raise ShadowRootNotFound immediately."""
        element = WebElement('elem-obj-1', mock_connection_handler)
        mock_connection_handler.execute_command.return_value = {
            'result': {
                'node': {
                    'nodeId': 1,
                    'backendNodeId': 10,
                    'nodeName': 'DIV',
                }
            }
        }

        with pytest.raises(ShadowRootNotFound):
            await element.get_shadow_root()

    @pytest.mark.asyncio
    async def test_timeout_raises_wait_element_timeout(self, mock_connection_handler):
        """Should raise WaitElementTimeout when shadow root doesn't appear within timeout."""
        element = WebElement('elem-obj-1', mock_connection_handler)
        mock_connection_handler.execute_command.return_value = {
            'result': {
                'node': {
                    'nodeId': 1,
                    'backendNodeId': 10,
                    'nodeName': 'DIV',
                }
            }
        }

        with pytest.raises(WaitElementTimeout):
            await element.get_shadow_root(timeout=1)

    @pytest.mark.asyncio
    async def test_timeout_returns_when_shadow_root_appears(self, mock_connection_handler):
        """Should return the shadow root as soon as it appears during polling."""
        element = WebElement('elem-obj-1', mock_connection_handler)
        no_shadow = {
            'result': {
                'node': {
                    'nodeId': 1,
                    'backendNodeId': 10,
                    'nodeName': 'DIV',
                }
            }
        }
        with_shadow = {
            'result': {
                'node': {
                    'nodeId': 1,
                    'backendNodeId': 10,
                    'nodeName': 'DIV',
                    'shadowRoots': [
                        {
                            'nodeId': 2,
                            'backendNodeId': 20,
                            'shadowRootType': 'closed',
                        }
                    ],
                }
            }
        }
        mock_connection_handler.execute_command.side_effect = [
            # First poll: no shadow root
            no_shadow,
            # Second poll: shadow root appears
            with_shadow,
            # resolve shadow root
            {'result': {'object': {'objectId': 'sr-delayed'}}},
        ]

        result = await element.get_shadow_root(timeout=5)

        assert result._object_id == 'sr-delayed'
        assert result.mode == ShadowRootType.CLOSED
        assert result.host_element is element
