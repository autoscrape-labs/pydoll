"""Unit tests for IFrameContextResolver and IFrameContext."""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from pydoll.interactions.iframe import IFrameContext, IFrameContextResolver
from pydoll.exceptions import InvalidIFrame


@pytest_asyncio.fixture
async def mock_element():
    """Create a mock WebElement for tests."""
    element = MagicMock()
    element._object_id = 'mock-object-id'
    element._connection_handler = MagicMock()
    element._connection_handler.execute_command = AsyncMock()
    element._connection_handler._connection_port = 9222
    element._describe_node = AsyncMock()
    return element


@pytest_asyncio.fixture
async def resolver(mock_element):
    """Create IFrameContextResolver with mocked element."""
    return IFrameContextResolver(mock_element)


class TestIFrameContext:
    """Test IFrameContext dataclass."""

    def test_default_values(self):
        """Test IFrameContext with only required field."""
        context = IFrameContext(frame_id='test-frame-id')

        assert context.frame_id == 'test-frame-id'
        assert context.document_url is None
        assert context.execution_context_id is None
        assert context.document_object_id is None
        assert context.session_handler is None
        assert context.session_id is None

    def test_all_values(self):
        """Test IFrameContext with all fields set."""
        mock_handler = MagicMock()

        context = IFrameContext(
            frame_id='frame-123',
            document_url='https://example.com',
            execution_context_id=42,
            document_object_id='doc-obj-456',
            session_handler=mock_handler,
            session_id='session-789',
        )

        assert context.frame_id == 'frame-123'
        assert context.document_url == 'https://example.com'
        assert context.execution_context_id == 42
        assert context.document_object_id == 'doc-obj-456'
        assert context.session_handler is mock_handler
        assert context.session_id == 'session-789'


class TestIFrameContextResolverInit:
    """Test IFrameContextResolver initialization."""

    def test_initialization(self, mock_element):
        """Test resolver stores element reference."""
        resolver = IFrameContextResolver(mock_element)

        assert resolver._element is mock_element


class TestGetBaseSession:
    """Test _get_base_session method."""

    def test_get_base_session_default(self, mock_element):
        """Test _get_base_session returns connection handler when no routing session."""
        # Explicitly set routing session to None to simulate no routing
        mock_element._routing_session_handler = None
        mock_element._routing_session_id = None

        resolver = IFrameContextResolver(mock_element)
        handler, session_id = resolver._get_base_session()

        assert handler is mock_element._connection_handler
        assert session_id is None

    def test_get_base_session_with_routing_session(self, mock_element):
        """Test _get_base_session returns routing session when set."""
        mock_routing_handler = MagicMock()
        mock_element._routing_session_handler = mock_routing_handler
        mock_element._routing_session_id = 'routing-session-123'

        resolver = IFrameContextResolver(mock_element)
        handler, session_id = resolver._get_base_session()

        assert handler is mock_routing_handler
        assert session_id == 'routing-session-123'


class TestExtractFrameMetadata:
    """Test _extract_frame_metadata static method."""

    def test_extract_with_content_document(self):
        """Test extracting metadata when contentDocument is present."""
        node_info = {
            'contentDocument': {
                'frameId': 'content-frame-id',
                'documentURL': 'https://iframe.example.com',
            },
            'frameId': 'parent-frame-id',
            'backendNodeId': 123,
        }

        frame_id, doc_url, parent_id, backend_id = (
            IFrameContextResolver._extract_frame_metadata(node_info)
        )

        assert frame_id == 'content-frame-id'
        assert doc_url == 'https://iframe.example.com'
        assert parent_id == 'parent-frame-id'
        assert backend_id == 123

    def test_extract_without_content_document(self):
        """Test extracting metadata when contentDocument is missing."""
        node_info = {
            'frameId': 'parent-frame-id',
            'backendNodeId': 456,
            'documentURL': 'https://fallback.example.com',
        }

        frame_id, doc_url, parent_id, backend_id = (
            IFrameContextResolver._extract_frame_metadata(node_info)
        )

        assert frame_id is None  # No contentDocument.frameId
        assert doc_url == 'https://fallback.example.com'
        assert parent_id == 'parent-frame-id'
        assert backend_id == 456

    def test_extract_with_base_url_fallback(self):
        """Test documentURL fallback to baseURL."""
        node_info = {
            'contentDocument': {
                'baseURL': 'https://base.example.com',
            },
            'backendNodeId': 789,
        }

        frame_id, doc_url, parent_id, backend_id = (
            IFrameContextResolver._extract_frame_metadata(node_info)
        )

        assert doc_url == 'https://base.example.com'

    def test_extract_empty_node_info(self):
        """Test extracting from empty node info."""
        node_info = {}

        frame_id, doc_url, parent_id, backend_id = (
            IFrameContextResolver._extract_frame_metadata(node_info)
        )

        assert frame_id is None
        assert doc_url is None
        assert parent_id is None
        assert backend_id is None


class TestWalkFrames:
    """Test _walk_frames static method."""

    def test_walk_frames_single_frame(self):
        """Test walking a tree with single frame."""
        frame_tree = {
            'frame': {'id': 'frame-1', 'url': 'https://example.com'},
            'childFrames': [],
        }

        frames = list(IFrameContextResolver._walk_frames(frame_tree))

        assert len(frames) == 1
        assert frames[0]['id'] == 'frame-1'

    def test_walk_frames_with_children(self):
        """Test walking a tree with child frames."""
        frame_tree = {
            'frame': {'id': 'parent-frame', 'url': 'https://parent.com'},
            'childFrames': [
                {
                    'frame': {'id': 'child-frame-1', 'url': 'https://child1.com'},
                    'childFrames': [],
                },
                {
                    'frame': {'id': 'child-frame-2', 'url': 'https://child2.com'},
                    'childFrames': [],
                },
            ],
        }

        frames = list(IFrameContextResolver._walk_frames(frame_tree))

        assert len(frames) == 3
        frame_ids = [f['id'] for f in frames]
        assert 'parent-frame' in frame_ids
        assert 'child-frame-1' in frame_ids
        assert 'child-frame-2' in frame_ids

    def test_walk_frames_nested_children(self):
        """Test walking deeply nested frame tree."""
        frame_tree = {
            'frame': {'id': 'level-0'},
            'childFrames': [
                {
                    'frame': {'id': 'level-1'},
                    'childFrames': [
                        {
                            'frame': {'id': 'level-2'},
                            'childFrames': [],
                        }
                    ],
                }
            ],
        }

        frames = list(IFrameContextResolver._walk_frames(frame_tree))

        assert len(frames) == 3
        frame_ids = [f['id'] for f in frames]
        assert 'level-0' in frame_ids
        assert 'level-1' in frame_ids
        assert 'level-2' in frame_ids

    def test_walk_frames_empty_tree(self):
        """Test walking empty frame tree."""
        frames = list(IFrameContextResolver._walk_frames(None))
        assert frames == []

    def test_walk_frames_no_child_frames_key(self):
        """Test walking frame tree with no childFrames key."""
        frame_tree = {
            'frame': {'id': 'single-frame'},
        }

        frames = list(IFrameContextResolver._walk_frames(frame_tree))

        assert len(frames) == 1
        assert frames[0]['id'] == 'single-frame'


class TestFindChildByParent:
    """Test _find_child_by_parent static method."""

    def test_find_direct_child(self):
        """Test finding direct child by parent ID."""
        frame_tree = {
            'frame': {'id': 'root'},
            'childFrames': [
                {
                    'frame': {'id': 'child-1', 'parentId': 'target-parent'},
                    'childFrames': [],
                },
            ],
        }

        result = IFrameContextResolver._find_child_by_parent(frame_tree, 'target-parent')

        assert result == 'child-1'

    def test_find_nested_child(self):
        """Test finding nested child by parent ID."""
        frame_tree = {
            'frame': {'id': 'root'},
            'childFrames': [
                {
                    'frame': {'id': 'level-1', 'parentId': 'root'},
                    'childFrames': [
                        {
                            'frame': {'id': 'level-2', 'parentId': 'target-parent'},
                            'childFrames': [],
                        }
                    ],
                }
            ],
        }

        result = IFrameContextResolver._find_child_by_parent(frame_tree, 'target-parent')

        assert result == 'level-2'

    def test_find_child_not_found(self):
        """Test when child with matching parent is not found."""
        frame_tree = {
            'frame': {'id': 'root'},
            'childFrames': [
                {
                    'frame': {'id': 'child', 'parentId': 'other-parent'},
                    'childFrames': [],
                }
            ],
        }

        result = IFrameContextResolver._find_child_by_parent(frame_tree, 'non-existent')

        assert result is None

    def test_find_child_empty_tree(self):
        """Test finding in empty tree."""
        result = IFrameContextResolver._find_child_by_parent(None, 'any-parent')

        assert result is None

    def test_find_child_no_child_frames(self):
        """Test finding in tree with no child frames."""
        frame_tree = {
            'frame': {'id': 'root'},
            'childFrames': [],
        }

        result = IFrameContextResolver._find_child_by_parent(frame_tree, 'any-parent')

        assert result is None


class TestGetFrameTreeFor:
    """Test _get_frame_tree_for static method."""

    @pytest.mark.asyncio
    async def test_get_frame_tree_without_session(self):
        """Test getting frame tree without session ID."""
        mock_handler = MagicMock()
        mock_handler.execute_command = AsyncMock(
            return_value={
                'result': {
                    'frameTree': {
                        'frame': {'id': 'main-frame'},
                        'childFrames': [],
                    }
                }
            }
        )

        result = await IFrameContextResolver._get_frame_tree_for(mock_handler, None)

        assert result['frame']['id'] == 'main-frame'
        # Verify command was called
        mock_handler.execute_command.assert_called_once()
        call_args = mock_handler.execute_command.call_args[0][0]
        assert 'sessionId' not in call_args

    @pytest.mark.asyncio
    async def test_get_frame_tree_with_session(self):
        """Test getting frame tree with session ID."""
        mock_handler = MagicMock()
        mock_handler.execute_command = AsyncMock(
            return_value={
                'result': {
                    'frameTree': {
                        'frame': {'id': 'session-frame'},
                        'childFrames': [],
                    }
                }
            }
        )

        result = await IFrameContextResolver._get_frame_tree_for(
            mock_handler, 'session-123'
        )

        assert result['frame']['id'] == 'session-frame'
        call_args = mock_handler.execute_command.call_args[0][0]
        assert call_args['sessionId'] == 'session-123'


class TestOwnerBackendFor:
    """Test _owner_backend_for static method."""

    @pytest.mark.asyncio
    async def test_owner_backend_without_session(self):
        """Test getting owner backend ID without session."""
        mock_handler = MagicMock()
        mock_handler.execute_command = AsyncMock(
            return_value={'result': {'backendNodeId': 456}}
        )

        result = await IFrameContextResolver._owner_backend_for(
            mock_handler, None, 'frame-id-123'
        )

        assert result == 456
        call_args = mock_handler.execute_command.call_args[0][0]
        assert 'sessionId' not in call_args

    @pytest.mark.asyncio
    async def test_owner_backend_with_session(self):
        """Test getting owner backend ID with session."""
        mock_handler = MagicMock()
        mock_handler.execute_command = AsyncMock(
            return_value={'result': {'backendNodeId': 789}}
        )

        result = await IFrameContextResolver._owner_backend_for(
            mock_handler, 'session-xyz', 'frame-id-456'
        )

        assert result == 789
        call_args = mock_handler.execute_command.call_args[0][0]
        assert call_args['sessionId'] == 'session-xyz'

    @pytest.mark.asyncio
    async def test_owner_backend_missing_result(self):
        """Test handling missing result."""
        mock_handler = MagicMock()
        mock_handler.execute_command = AsyncMock(return_value={})

        result = await IFrameContextResolver._owner_backend_for(
            mock_handler, None, 'frame-id'
        )

        assert result is None


class TestCreateIsolatedWorldForFrame:
    """Test _create_isolated_world_for_frame static method."""

    @pytest.mark.asyncio
    async def test_create_isolated_world_success(self):
        """Test successful creation of isolated world."""
        mock_handler = MagicMock()
        mock_handler.execute_command = AsyncMock(
            return_value={'result': {'executionContextId': 42}}
        )

        result = await IFrameContextResolver._create_isolated_world_for_frame(
            'frame-id-123', mock_handler, None
        )

        assert result == 42
        call_args = mock_handler.execute_command.call_args[0][0]
        assert 'sessionId' not in call_args
        assert 'pydoll::iframe::frame-id-123' in call_args['params']['worldName']

    @pytest.mark.asyncio
    async def test_create_isolated_world_with_session(self):
        """Test creation with session ID."""
        mock_handler = MagicMock()
        mock_handler.execute_command = AsyncMock(
            return_value={'result': {'executionContextId': 99}}
        )

        result = await IFrameContextResolver._create_isolated_world_for_frame(
            'frame-id', mock_handler, 'session-abc'
        )

        assert result == 99
        call_args = mock_handler.execute_command.call_args[0][0]
        assert call_args['sessionId'] == 'session-abc'

    @pytest.mark.asyncio
    async def test_create_isolated_world_failure(self):
        """Test failure when no execution context ID returned."""
        mock_handler = MagicMock()
        mock_handler.execute_command = AsyncMock(return_value={'result': {}})

        with pytest.raises(InvalidIFrame, match='Unable to create isolated world'):
            await IFrameContextResolver._create_isolated_world_for_frame(
                'frame-id', mock_handler, None
            )


class TestGetDocumentObjectId:
    """Test _get_document_object_id method."""

    @pytest.mark.asyncio
    async def test_get_document_object_id_success(self, resolver, mock_element):
        """Test successful retrieval of document object ID."""
        mock_element._connection_handler.execute_command.return_value = {
            'result': {'result': {'objectId': 'doc-object-123'}}
        }

        context = IFrameContext(frame_id='test-frame')

        result = await resolver._get_document_object_id(42, context)

        assert result == 'doc-object-123'

    @pytest.mark.asyncio
    async def test_get_document_object_id_with_session(self, resolver, mock_element):
        """Test retrieval with session handler."""
        mock_session_handler = MagicMock()
        mock_session_handler.execute_command = AsyncMock(
            return_value={'result': {'result': {'objectId': 'session-doc-obj'}}}
        )

        context = IFrameContext(
            frame_id='test-frame',
            session_handler=mock_session_handler,
            session_id='session-123',
        )

        result = await resolver._get_document_object_id(99, context)

        assert result == 'session-doc-obj'
        mock_session_handler.execute_command.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_document_object_id_failure(self, resolver, mock_element):
        """Test failure when document object ID not found."""
        mock_element._connection_handler.execute_command.return_value = {
            'result': {'result': {}}
        }

        context = IFrameContext(frame_id='test-frame')

        with pytest.raises(InvalidIFrame, match='Unable to obtain document reference'):
            await resolver._get_document_object_id(42, context)


class TestResolveOopifIfNeeded:
    """Test _resolve_oopif_if_needed method."""

    @pytest.mark.asyncio
    async def test_returns_early_when_no_parent_frame(self, resolver):
        """Test early return when parent_frame_id is None."""
        result = await resolver._resolve_oopif_if_needed(
            current_frame_id='frame-123',
            parent_frame_id=None,
            backend_node_id=456,
            current_document_url='https://example.com',
        )

        handler, session_id, frame_id, url = result
        assert handler is None
        assert session_id is None
        assert frame_id == 'frame-123'
        assert url == 'https://example.com'

    @pytest.mark.asyncio
    async def test_returns_early_when_frame_resolved_without_backend(self, resolver):
        """Test early return when frame is resolved and no backend_node_id."""
        result = await resolver._resolve_oopif_if_needed(
            current_frame_id='resolved-frame',
            parent_frame_id='parent-123',
            backend_node_id=None,
            current_document_url='https://resolved.com',
        )

        handler, session_id, frame_id, url = result
        assert handler is None
        assert session_id is None
        assert frame_id == 'resolved-frame'
        assert url == 'https://resolved.com'


class TestResolveFrameByOwner:
    """Test _resolve_frame_by_owner method."""

    @pytest.mark.asyncio
    async def test_resolve_returns_current_url_on_failure(self, resolver):
        """Test that current URL is preserved when resolution fails."""
        # Mock _find_frame_by_owner to return no match
        resolver._find_frame_by_owner = AsyncMock(return_value=(None, None))

        mock_handler = MagicMock()

        result = await resolver._resolve_frame_by_owner(
            mock_handler, None, 123, 'https://current.com'
        )

        frame_id, url = result
        assert frame_id is None
        assert url == 'https://current.com'

    @pytest.mark.asyncio
    async def test_resolve_returns_found_frame(self, resolver):
        """Test successful frame resolution by owner."""
        resolver._find_frame_by_owner = AsyncMock(
            return_value=('found-frame-id', 'https://found.com')
        )

        mock_handler = MagicMock()

        result = await resolver._resolve_frame_by_owner(
            mock_handler, None, 456, 'https://fallback.com'
        )

        frame_id, url = result
        assert frame_id == 'found-frame-id'
        assert url == 'https://found.com'

    @pytest.mark.asyncio
    async def test_resolve_uses_fallback_url(self, resolver):
        """Test URL fallback when found frame has no URL."""
        resolver._find_frame_by_owner = AsyncMock(
            return_value=('frame-id', None)
        )

        mock_handler = MagicMock()

        result = await resolver._resolve_frame_by_owner(
            mock_handler, None, 789, 'https://fallback.com'
        )

        frame_id, url = result
        assert frame_id == 'frame-id'
        assert url == 'https://fallback.com'
