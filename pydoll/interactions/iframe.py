from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterable, Optional

from pydoll.commands import DomCommands, PageCommands, RuntimeCommands, TargetCommands
from pydoll.connection import ConnectionHandler
from pydoll.exceptions import InvalidIFrame
from pydoll.protocol.dom.methods import GetFrameOwnerResponse
from pydoll.protocol.dom.types import Node
from pydoll.protocol.page.methods import CreateIsolatedWorldResponse, GetFrameTreeResponse
from pydoll.protocol.page.types import Frame, FrameTree
from pydoll.protocol.runtime.methods import EvaluateResponse
from pydoll.protocol.target.methods import AttachToTargetResponse, GetTargetsResponse

if TYPE_CHECKING:
    from pydoll.elements.web_element import WebElement

logger = logging.getLogger(__name__)


@dataclass
class IFrameContext:
    """Context information for an iframe element."""

    frame_id: str
    document_url: Optional[str] = None
    execution_context_id: Optional[int] = None
    document_object_id: Optional[str] = None
    session_handler: Optional[ConnectionHandler] = None
    session_id: Optional[str] = None


class IFrameContextResolver:
    """Resolves iframe context for WebElement."""

    def __init__(self, element: WebElement):
        self._element = element

    async def resolve(self) -> IFrameContext:
        """
        Resolve and return iframe context.

        Returns:
            IFrameContext with frame_id, document_url, execution_context_id,
            document_object_id and session info for OOPIF targets.

        Raises:
            InvalidIFrame: If unable to resolve the iframe context.
        """
        node_info = await self._element._describe_node(object_id=self._element._object_id)
        base_handler, base_session_id = self._get_base_session()
        frame_id, document_url, parent_frame_id, backend_node_id = self._extract_frame_metadata(
            node_info
        )

        if not frame_id and backend_node_id is not None:
            frame_id, document_url = await self._resolve_frame_by_owner(
                base_handler, base_session_id, backend_node_id, document_url
            )

        session_handler, session_id, frame_id, document_url = await self._resolve_oopif_if_needed(
            frame_id, parent_frame_id, backend_node_id, document_url
        )

        if not frame_id:
            raise InvalidIFrame('Unable to resolve frameId for the iframe element')

        context = IFrameContext(frame_id=frame_id, document_url=document_url)

        if session_handler and session_id:
            context.session_handler = session_handler
            context.session_id = session_id

        effective_handler = session_handler or base_handler
        effective_session_id = session_id or base_session_id

        execution_context_id = await self._create_isolated_world_for_frame(
            frame_id, effective_handler, effective_session_id
        )
        context.execution_context_id = execution_context_id

        document_object_id = await self._get_document_object_id(execution_context_id, context)
        context.document_object_id = document_object_id

        return context

    def _get_base_session(self) -> tuple[ConnectionHandler, Optional[str]]:
        """Return the default handler and session id for routing commands."""
        handler = (
            getattr(self._element, '_routing_session_handler', None)
            or self._element._connection_handler
        )
        session_id = getattr(self._element, '_routing_session_id', None)
        return handler, session_id

    @staticmethod
    def _extract_frame_metadata(
        node_info: Node,
    ) -> tuple[Optional[str], Optional[str], Optional[str], Optional[int]]:
        """Extract iframe-related metadata from DOM node info."""
        content_document = node_info.get('contentDocument') or {}
        parent_frame_id = node_info.get('frameId')
        backend_node_id = node_info.get('backendNodeId')
        frame_id = content_document.get('frameId')
        document_url = (
            content_document.get('documentURL')
            or content_document.get('baseURL')
            or node_info.get('documentURL')
            or node_info.get('baseURL')
        )
        return frame_id, document_url, parent_frame_id, backend_node_id

    async def _resolve_frame_by_owner(
        self,
        base_handler: ConnectionHandler,
        base_session_id: Optional[str],
        backend_node_id: int,
        current_document_url: Optional[str],
    ) -> tuple[Optional[str], Optional[str]]:
        """Resolve frame id and URL by matching owner backend_node_id."""
        owner_frame_id, owner_url = await self._find_frame_by_owner(
            base_handler, base_session_id, backend_node_id
        )
        if not owner_frame_id:
            return None, current_document_url
        return owner_frame_id, owner_url or current_document_url

    async def _find_frame_by_owner(
        self,
        handler: ConnectionHandler,
        session_id: Optional[str],
        backend_node_id: int,
    ) -> tuple[Optional[str], Optional[str]]:
        """Find frame by matching owner backend_node_id."""
        frame_tree = await self._get_frame_tree_for(handler, session_id)
        for frame_node in self._walk_frames(frame_tree):
            candidate_frame_id = frame_node.get('id', '')
            if not candidate_frame_id:
                continue
            owner_backend_id = await self._owner_backend_for(
                handler, session_id, candidate_frame_id
            )
            if owner_backend_id == backend_node_id:
                return candidate_frame_id, frame_node.get('url')
        return None, None

    @staticmethod
    async def _get_frame_tree_for(
        handler: ConnectionHandler,
        session_id: Optional[str],
    ) -> FrameTree:
        """Get Page frame tree for the given connection/target."""
        command = PageCommands.get_frame_tree()
        if session_id:
            command['sessionId'] = session_id
        response: GetFrameTreeResponse = await handler.execute_command(command)
        return response['result']['frameTree']

    @staticmethod
    def _walk_frames(tree: FrameTree) -> Iterable[Frame]:
        """Recursively traverse FrameTree and collect all frame descriptors."""
        if not tree:
            return []
        frames: list[Frame] = [tree['frame']]
        for child_frame in tree.get('childFrames', []) or []:
            frames.extend(IFrameContextResolver._walk_frames(child_frame))
        return [frame_node for frame_node in frames if frame_node]

    @staticmethod
    async def _owner_backend_for(
        handler: ConnectionHandler,
        session_id: Optional[str],
        frame_id: str,
    ) -> Optional[int]:
        """Get backendNodeId of the DOM element that owns the given frame."""
        command = DomCommands.get_frame_owner(frame_id=frame_id)
        if session_id:
            command['sessionId'] = session_id
        response: GetFrameOwnerResponse = await handler.execute_command(command)
        return response.get('result', {}).get('backendNodeId')

    async def _resolve_oopif_if_needed(
        self,
        current_frame_id: Optional[str],
        parent_frame_id: Optional[str],
        backend_node_id: Optional[int],
        current_document_url: Optional[str],
    ) -> tuple[Optional[ConnectionHandler], Optional[str], Optional[str], Optional[str]]:
        """Resolve OOPIF and routing when needed."""
        if not parent_frame_id or (current_frame_id and backend_node_id is None):
            return None, None, current_frame_id, current_document_url

        (
            session_handler,
            session_id,
            resolved_frame_id,
            resolved_url,
        ) = await self._resolve_oopif_by_parent(parent_frame_id, backend_node_id)

        if session_handler and session_id and resolved_url:
            return (
                session_handler,
                session_id,
                resolved_frame_id or current_frame_id,
                resolved_url or current_document_url,
            )

        return (
            None,
            None,
            current_frame_id or resolved_frame_id,
            current_document_url or resolved_url,
        )

    async def _resolve_oopif_by_parent(
        self,
        parent_frame_id: str,
        backend_node_id: Optional[int],
    ) -> tuple[Optional[ConnectionHandler], Optional[str], Optional[str], Optional[str]]:
        """Resolve out-of-process iframe using parent frame id."""
        browser_handler = ConnectionHandler(
            connection_port=self._element._connection_handler._connection_port
        )
        targets_response: GetTargetsResponse = await browser_handler.execute_command(
            TargetCommands.get_targets()
        )
        target_infos = targets_response.get('result', {}).get('targetInfos', [])

        direct_children = [
            target_info
            for target_info in target_infos
            if target_info.get('type') in {'iframe', 'page'}
            and target_info.get('parentFrameId') == parent_frame_id
        ]

        is_single_child = len(direct_children) == 1
        for child_target in direct_children:
            attach_response: AttachToTargetResponse = await browser_handler.execute_command(
                TargetCommands.attach_to_target(target_id=child_target['targetId'], flatten=True)
            )
            attached_session_id = attach_response.get('result', {}).get('sessionId')
            if not attached_session_id:
                continue

            frame_tree = await self._get_frame_tree_for(browser_handler, attached_session_id)
            root_frame = (frame_tree or {}).get('frame', {})
            root_frame_id = root_frame.get('id', '')

            if is_single_child and root_frame_id and backend_node_id is None:
                return (
                    browser_handler,
                    attached_session_id,
                    root_frame_id,
                    root_frame.get('url'),
                )

            if root_frame_id and backend_node_id is not None:
                owner_backend_id = await self._owner_backend_for(
                    self._element._connection_handler, None, root_frame_id
                )
                if owner_backend_id == backend_node_id:
                    return (
                        browser_handler,
                        attached_session_id,
                        root_frame_id,
                        root_frame.get('url'),
                    )

        for target_info in target_infos:
            if target_info.get('type') not in {'iframe', 'page'}:
                continue
            attach_response = await browser_handler.execute_command(
                TargetCommands.attach_to_target(
                    target_id=target_info.get('targetId', ''), flatten=True
                )
            )
            attached_session_id = attach_response.get('result', {}).get('sessionId')
            if not attached_session_id:
                continue

            frame_tree = await self._get_frame_tree_for(browser_handler, attached_session_id)
            root_frame = (frame_tree or {}).get('frame', {})
            root_frame_id = root_frame.get('id', '')

            if root_frame_id and backend_node_id is not None:
                owner_backend_id = await self._owner_backend_for(
                    self._element._connection_handler, None, root_frame_id
                )
                if owner_backend_id == backend_node_id:
                    return (
                        browser_handler,
                        attached_session_id,
                        root_frame_id,
                        root_frame.get('url'),
                    )

            child_frame_id = self._find_child_by_parent(frame_tree, parent_frame_id)
            if child_frame_id:
                return browser_handler, attached_session_id, child_frame_id, None

        return None, None, None, None

    @staticmethod
    def _find_child_by_parent(tree: FrameTree, parent_id: str) -> Optional[str]:
        """Find id of child frame whose parentId equals the given one."""
        if not tree:
            return None
        for child in tree.get('childFrames', []) or []:
            child_frame = child.get('frame', {})
            if child_frame.get('parentId') == parent_id:
                return child_frame.get('id')
            found = IFrameContextResolver._find_child_by_parent(child, parent_id)
            if found:
                return found
        return None

    @staticmethod
    async def _create_isolated_world_for_frame(
        frame_id: str,
        handler: ConnectionHandler,
        session_id: Optional[str],
    ) -> int:
        """Create isolated world for the given frame."""
        create_command = PageCommands.create_isolated_world(
            frame_id=frame_id,
            world_name=f'pydoll::iframe::{frame_id}',
            grant_universal_access=True,
        )
        if session_id:
            create_command['sessionId'] = session_id
        create_response: CreateIsolatedWorldResponse = await handler.execute_command(create_command)
        execution_context_id = create_response.get('result', {}).get('executionContextId')
        if not execution_context_id:
            raise InvalidIFrame('Unable to create isolated world for iframe')
        return execution_context_id

    async def _get_document_object_id(
        self,
        execution_context_id: int,
        context: IFrameContext,
    ) -> str:
        """Get document.documentElement object id in iframe context."""
        evaluate_command = RuntimeCommands.evaluate(
            expression='document.documentElement',
            context_id=execution_context_id,
        )
        if context.session_id:
            evaluate_command['sessionId'] = context.session_id

        handler = context.session_handler or self._element._connection_handler
        evaluate_response: EvaluateResponse = await handler.execute_command(evaluate_command)

        result_object = evaluate_response.get('result', {}).get('result', {})
        document_object_id = result_object.get('objectId')
        if not document_object_id:
            raise InvalidIFrame('Unable to obtain document reference for iframe')
        return document_object_id
