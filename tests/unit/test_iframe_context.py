from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from pydoll.interactions.iframe import IFrameContext, IFrameContextResolver


@pytest.mark.asyncio
async def test_resolve_preserves_inherited_routing_session_without_new_oopif_session():
    execution_context_id = 42
    element = MagicMock()
    element._object_id = 'iframe-object'
    element._connection_handler = MagicMock()
    element._routing_session_handler = MagicMock()
    element._routing_session_id = 'parent-session-id'

    resolver = IFrameContextResolver(element)
    resolver._describe_element_node = AsyncMock(
        return_value={
            'contentDocument': {
                'frameId': 'inner-frame-id',
                'documentURL': 'https://inner-frame.test',
            },
            'frameId': 'content-frame-id',
            'backendNodeId': 123,
        }
    )
    resolver._resolve_oopif_if_needed = AsyncMock(
        return_value=(None, None, 'inner-frame-id', 'https://inner-frame.test')
    )
    resolver._create_isolated_world_for_frame = AsyncMock(return_value=execution_context_id)
    resolver._get_document_object_id = AsyncMock(return_value='document-object-id')

    context = await resolver.resolve()

    assert context.session_handler is element._routing_session_handler
    assert context.session_id == 'parent-session-id'
    assert context.execution_context_id == execution_context_id
    assert context.document_object_id == 'document-object-id'
    resolver._create_isolated_world_for_frame.assert_awaited_once_with(
        'inner-frame-id',
        element._routing_session_handler,
        'parent-session-id',
    )
    resolver._get_document_object_id.assert_awaited_once_with(execution_context_id, context)


@pytest.mark.asyncio
async def test_get_document_object_id_evaluates_through_context_session():
    execution_context_id = 42
    element = MagicMock()
    element._connection_handler = MagicMock()
    element._connection_handler.execute_command = AsyncMock()
    session_handler = MagicMock()
    session_handler.execute_command = AsyncMock(
        return_value={'result': {'result': {'objectId': 'document-object-id'}}}
    )
    resolver = IFrameContextResolver(element)
    context = IFrameContext(
        frame_id='inner-frame-id',
        session_handler=session_handler,
        session_id='parent-session-id',
    )

    document_object_id = await resolver._get_document_object_id(execution_context_id, context)

    assert document_object_id == 'document-object-id'
    element._connection_handler.execute_command.assert_not_called()
    session_handler.execute_command.assert_awaited_once()
    command = session_handler.execute_command.await_args.args[0]
    assert command['method'] == 'Runtime.evaluate'
    assert command['params']['contextId'] == execution_context_id
    assert command['sessionId'] == 'parent-session-id'
