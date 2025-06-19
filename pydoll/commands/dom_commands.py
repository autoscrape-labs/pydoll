from typing import Optional

from pydoll.constants import ElementRelation, IncludeWhitespace, LogicalAxes, PhysicalAxes
from pydoll.protocol.base import Command, Response
from pydoll.protocol.dom.methods import DomMethod
from pydoll.protocol.dom.params import (
    CollectClassNamesFromSubtreeParams,
    CopyToParams,
    CSSComputedStyleProperty,
    DescribeNodeParams,
    DiscardSearchResultsParams,
    DomEnableParams,
    DomFocusParams,
    GetAnchorElementParams,
    GetAttributesParams,
    GetBoxModelParams,
    GetContainerForNodeParams,
    GetContentQuadsParams,
    GetDocumentParams,
    GetElementByRelationParams,
    GetFileInfoParams,
    GetFrameOwnerParams,
    GetNodeForLocationParams,
    GetNodesForSubtreeByStyleParams,
    GetNodeStackTracesParams,
    GetOuterHTMLParams,
    GetQueryingDescendantForContainerParams,
    GetRelayoutBoundaryParams,
    GetSearchResultsParams,
    MoveToParams,
    PerformSearchParams,
    PushNodeByPathToFrontendParams,
    PushNodesByBackendIdsToFrontendParams,
    QuerySelectorAllParams,
    QuerySelectorParams,
    Rect,
    RemoveAttributeParams,
    RemoveNodeParams,
    RequestChildNodesParams,
    RequestNodeParams,
    ResolveNodeParams,
    ScrollIntoViewIfNeededParams,
    SetAttributeAsTextParams,
    SetAttributeValueParams,
    SetFileInputFilesParams,
    SetInspectedNodeParams,
    SetNodeNameParams,
    SetNodeStackTracesEnabledParams,
    SetNodeValueParams,
    SetOuterHTMLParams,
)
from pydoll.protocol.dom.responses import (
    CollectClassNamesFromSubtreeResponse,
    CopyToResponse,
    DescribeNodeResponse,
    GetAnchorElementResponse,
    GetAttributesResponse,
    GetBoxModelResponse,
    GetContainerForNodeResponse,
    GetContentQuadsResponse,
    GetDetachedDomNodesResponse,
    GetDocumentResponse,
    GetElementByRelationResponse,
    GetFileInfoResponse,
    GetFrameOwnerResponse,
    GetNodeForLocationResponse,
    GetNodesForSubtreeByStyleResponse,
    GetNodeStackTracesResponse,
    GetOuterHTMLResponse,
    GetQueryingDescendantForContainerResponse,
    GetRelayoutBoundaryResponse,
    GetSearchResultsResponse,
    GetTopLayerElementsResponse,
    MoveToResponse,
    PerformSearchResponse,
    PushNodeByPathToFrontendResponse,
    PushNodesByBackendIdsToFrontendResponse,
    QuerySelectorAllResponse,
    QuerySelectorResponse,
    RequestNodeResponse,
    ResolveNodeResponse,
    SetNodeNameResponse,
)


class DomCommands:  # noqa
    """
    Implementation of Chrome DevTools Protocol for the DOM domain.

    This class provides commands for interacting with the Document Object Model (DOM) in the
    browser, enabling access and manipulation of the element structure in a web page.
    The DOM domain in Chrome DevTools Protocol exposes operations for reading and writing to the
    DOM, which is fundamental for browser automation, testing, and debugging.

    Each DOM element is represented by a mirror object with a unique ID. This ID can be used
    to gather additional information about the node, resolve it into JavaScript object wrappers,
    manipulate attributes, and perform various other operations on the DOM structure.
    """

    @staticmethod
    def describe_node(
        node_id: Optional[int] = None,
        backend_node_id: Optional[int] = None,
        object_id: Optional[str] = None,
        depth: Optional[int] = None,
        pierce: Optional[bool] = None,
    ) -> Command[DescribeNodeResponse]:
        """
        Describes a DOM node identified by its ID without requiring domain to be enabled.

        The describe_node command is particularly useful in scenarios where you need to quickly
        gather information about a specific element without subscribing to DOM change events,
        making it more lightweight for isolated element inspection operations.

        Args:
            node_id: Identifier of the node known to the client.
            backend_node_id: Identifier of the backend node used internally by the browser.
            object_id: JavaScript object id of the node wrapper.
            depth: Maximum depth at which children should be retrieved (default is 1).
                  Use -1 for the entire subtree or provide an integer greater than 0.
            pierce: Whether iframes and shadow roots should be traversed when returning
                   the subtree (default is false).

        Returns:
            Command: CDP command that returns detailed information about the requested node.
        """
        params = DescribeNodeParams()
        if node_id is not None:
            params['nodeId'] = node_id
        if backend_node_id is not None:
            params['backendNodeId'] = backend_node_id
        if object_id is not None:
            params['objectId'] = object_id
        if depth:
            params['depth'] = depth
        if pierce is not None:
            params['pierce'] = pierce
        return Command(method=DomMethod.DESCRIBE_NODE, params=params)

    @staticmethod
    def disable() -> Command[Response]:
        """
        Disables DOM agent for the current page.

        Disabling the DOM domain stops the CDP from sending DOM-related events and
        prevents further DOM manipulation operations until the domain is enabled again.
        This can be important for optimizing performance when you're done with DOM
        operations and want to minimize background processing.

        Returns:
            Command: CDP command to disable the DOM domain.
        """
        return Command(method=DomMethod.DISABLE)

    @staticmethod
    def enable(include_whitespace: Optional[IncludeWhitespace] = None) -> Command[Response]:
        """
        Enables DOM agent for the current page.

        Enabling the DOM domain is a prerequisite for receiving DOM events and using most DOM
        manipulation methods. The DOM events include changes to the DOM tree structure,
        attribute modifications, and many others. Without enabling this domain first,
        many DOM operations would fail or provide incomplete information.

        Args:
            include_whitespace: Whether to include whitespace-only text nodes in the
                               children array of returned Nodes. Allowed values: "none", "all".

        Returns:
            Command: CDP command to enable the DOM domain.
        """
        params = DomEnableParams()
        if include_whitespace:
            params['includeWhitespace'] = include_whitespace
        return Command(method=DomMethod.ENABLE, params=params)

    @staticmethod
    def focus(
        node_id: Optional[int] = None,
        backend_node_id: Optional[int] = None,
        object_id: Optional[str] = None,
    ) -> Command[Response]:
        """
        Focuses the given element.

        The focus command is crucial for simulating realistic user interactions, as many
        events (like keyboard input) require that an element has focus first. It's also
        important for testing proper tab order and keyboard accessibility of web pages.

        Args:
            node_id: Identifier of the node to focus.
            backend_node_id: Identifier of the backend node to focus.
            object_id: JavaScript object id of the node wrapper.

        Returns:
            Command: CDP command to focus on the specified element.
        """
        params = DomFocusParams()
        if node_id:
            params['nodeId'] = node_id
        if backend_node_id:
            params['backendNodeId'] = backend_node_id
        if object_id:
            params['objectId'] = object_id
        return Command(method=DomMethod.FOCUS, params=params)

    @staticmethod
    def get_attributes(node_id: int) -> Command[GetAttributesResponse]:
        """
        Returns attributes for the specified node.

        Attribute information is essential in web testing and automation because attributes
        often contain crucial information about element state, behavior, and metadata.
        This command provides an efficient way to access all attributes of an element
        without parsing HTML or using JavaScript evaluation.

        Args:
            node_id: Id of the node to retrieve attributes for.

        Returns:
            Command: CDP command that returns an interleaved array of node attribute
                    names and values [name1, value1, name2, value2, ...].
        """
        params = GetAttributesParams(nodeId=node_id)
        return Command(method=DomMethod.GET_ATTRIBUTES, params=params)

    @staticmethod
    def get_box_model(
        node_id: Optional[int] = None,
        backend_node_id: Optional[int] = None,
        object_id: Optional[str] = None,
    ) -> Command[GetBoxModelResponse]:
        """
        Returns box model information for the specified node.

        The box model is a fundamental concept in CSS that describes how elements are
        rendered with content, padding, borders, and margins. This command provides
        detailed information about these dimensions and coordinates, which is invaluable
        for spatial analysis and precision interactions with elements on the page.

        Args:
            node_id: Identifier of the node.
            backend_node_id: Identifier of the backend node.
            object_id: JavaScript object id of the node wrapper.

        Returns:
            Command: CDP command that returns the box model for the node, including
                    coordinates for content, padding, border, and margin boxes.
        """
        params = GetBoxModelParams()
        if node_id is not None:
            params['nodeId'] = node_id
        if backend_node_id is not None:
            params['backendNodeId'] = backend_node_id
        if object_id is not None:
            params['objectId'] = object_id
        return Command(method=DomMethod.GET_BOX_MODEL, params=params)

    @staticmethod
    def get_document(
        depth: Optional[int] = None, pierce: Optional[bool] = None
    ) -> Command[GetDocumentResponse]:
        """
        Returns the root DOM node (and optionally the subtree) to the caller.

        This is typically the first command called when interacting with the DOM, as it
        provides access to the document's root node. From this root, you can traverse to
        any other element on the page. This command implicitly enables DOM domain events
        for the current target, making it a good starting point for DOM interaction.

        Args:
            depth: Maximum depth at which children should be retrieved (default is 1).
                  Use -1 for the entire subtree or provide an integer greater than 0.
            pierce: Whether iframes and shadow roots should be traversed when returning
                  the subtree (default is false).

        Returns:
            Command: CDP command that returns the root DOM node.
        """
        params = GetDocumentParams()
        if depth is not None:
            params['depth'] = depth
        if pierce is not None:
            params['pierce'] = pierce
        return Command(method=DomMethod.GET_DOCUMENT, params=params)

    @staticmethod
    def get_node_for_location(
        x: int,
        y: int,
        include_user_agent_shadow_dom: Optional[bool] = None,
        ignore_pointer_events_none: Optional[bool] = None,
    ) -> Command[GetNodeForLocationResponse]:
        """
        Returns node id at given location on the page.

        This command is particularly useful for bridging the gap between visual/pixel-based
        information and the DOM structure. It allows you to convert screen coordinates to
        actual DOM elements, which is essential for creating inspection tools or for testing
        spatially-oriented interactions.

        Args:
            x: X coordinate relative to the main frame's viewport.
            y: Y coordinate relative to the main frame's viewport.
            include_user_agent_shadow_dom: Whether to include nodes in user agent shadow roots.
            ignore_pointer_events_none: Whether to ignore pointer-events:none and test elements
                                       underneath them.

        Returns:
            Command: CDP command that returns the node at the given location, including
                   frame information when available.
        """
        params = GetNodeForLocationParams(x=x, y=y)
        if include_user_agent_shadow_dom is not None:
            params['includeUserAgentShadowDOM'] = include_user_agent_shadow_dom
        if ignore_pointer_events_none is not None:
            params['ignorePointerEventsNone'] = ignore_pointer_events_none
        return Command(method=DomMethod.GET_NODE_FOR_LOCATION, params=params)

    @staticmethod
    def get_outer_html(
        node_id: Optional[int] = None,
        backend_node_id: Optional[int] = None,
        object_id: Optional[str] = None,
    ) -> Command[GetOuterHTMLResponse]:
        """
        Returns node's HTML markup, including the node itself and all its children.

        This command provides a way to access the complete HTML representation of an
        element, making it valuable for when you need to extract, analyze, or verify
        HTML content. It's more comprehensive than just getting text content as it
        preserves the full markup structure including tags, attributes, and child elements.

        Args:
            node_id: Identifier of the node.
            backend_node_id: Identifier of the backend node.
            object_id: JavaScript object id of the node wrapper.

        Returns:
            Command: CDP command that returns the outer HTML markup of the node.
        """
        params = GetOuterHTMLParams()
        if node_id is not None:
            params['nodeId'] = node_id
        if backend_node_id is not None:
            params['backendNodeId'] = backend_node_id
        if object_id is not None:
            params['objectId'] = object_id
        return Command(method=DomMethod.GET_OUTER_HTML, params=params)

    @staticmethod
    def hide_highlight() -> Command[Response]:
        """
        Hides any DOM element highlight.

        This command is particularly useful in automation workflows where multiple elements
        are highlighted in sequence, and you need to clear previous highlights before
        proceeding to the next element to avoid visual clutter or interference.

        Returns:
            Command: CDP command to hide DOM element highlights.
        """
        return Command(method=DomMethod.HIDE_HIGHLIGHT)

    @staticmethod
    def highlight_node() -> Command[Response]:
        """
        Highlights DOM node.

        Highlighting nodes is especially valuable during development and debugging sessions
        to visually confirm which elements are being selected by selectors or coordinates.

        Returns:
            Command: CDP command to highlight a DOM node.
        """
        return Command(method=DomMethod.HIGHLIGHT_NODE)

    @staticmethod
    def highlight_rect() -> Command[Response]:
        """
        Highlights given rectangle.

        Unlike node highlighting, rectangle highlighting allows highlighting arbitrary
        regions of the page, which is useful for highlighting computed areas or
        regions that don't correspond directly to DOM elements.

        Returns:
            Command: CDP command to highlight a rectangular area.
        """
        return Command(method=DomMethod.HIGHLIGHT_RECT)

    @staticmethod
    def move_to(
        node_id: int,
        target_node_id: int,
        insert_before_node_id: Optional[int] = None,
    ) -> Command[MoveToResponse]:
        """
        Moves node into the new container, placing it before the given anchor.

        This command allows for more complex DOM restructuring than simple attribute or
        content changes. It's particularly useful when testing applications that involve
        rearranging elements, such as sortable lists, kanban boards, or drag-and-drop interfaces.

        Args:
            node_id: Id of the node to move.
            target_node_id: Id of the element to drop the moved node into.
            insert_before_node_id: Drop node before this one (if absent, the moved node
                                 becomes the last child of target_node_id).

        Returns:
            Command: CDP command to move a node, returning the new id of the moved node.
        """
        params = MoveToParams(nodeId=node_id, targetNodeId=target_node_id)
        if insert_before_node_id is not None:
            params['insertBeforeNodeId'] = insert_before_node_id
        return Command(method=DomMethod.MOVE_TO, params=params)

    @staticmethod
    def query_selector(
        node_id: int,
        selector: str,
    ) -> Command[QuerySelectorResponse]:
        """
        Executes querySelector on a given node.

        This method is one of the most fundamental tools for element location, allowing
        the use of standard CSS selectors to find elements in the DOM. Unlike JavaScript's
        querySelector, this can be executed on any node (not just document), enabling
        scoped searches within specific sections of the page.

        Args:
            node_id: Id of the node to query upon.
            selector: CSS selector string.

        Returns:
            Command: CDP command that returns the first element matching the selector.
        """
        params = QuerySelectorParams(nodeId=node_id, selector=selector)
        return Command(method=DomMethod.QUERY_SELECTOR, params=params)

    @staticmethod
    def query_selector_all(
        node_id: int,
        selector: str,
    ) -> Command[QuerySelectorAllResponse]:
        """
        Executes querySelectorAll on a given node.

        This method extends querySelector by returning all matching elements rather than just
        the first one. This is essential for operations that need to process multiple elements,
        such as extracting data from tables, lists, or grids, or verifying that the correct
        number of elements are present.

        Args:
            node_id: Id of the node to query upon.
            selector: CSS selector string.

        Returns:
            Command: CDP command that returns all elements matching the selector.
        """
        params = QuerySelectorAllParams(nodeId=node_id, selector=selector)
        return Command(method=DomMethod.QUERY_SELECTOR_ALL, params=params)

    @staticmethod
    def remove_attribute(
        node_id: int,
        name: str,
    ) -> Command[Response]:
        """
        Removes attribute with given name from an element with given id.

        This command allows direct manipulation of element attributes without using JavaScript
        in the page context. It's useful for testing how elements behave when specific
        attributes are removed or for preparing elements for specific test conditions.

        Args:
            node_id: Id of the element to remove attribute from.
            name: Name of the attribute to remove.

        Returns:
            Command: CDP command to remove the specified attribute.
        """
        params = RemoveAttributeParams(nodeId=node_id, name=name)
        return Command(method=DomMethod.REMOVE_ATTRIBUTE, params=params)

    @staticmethod
    def remove_node(node_id: int) -> Command[Response]:
        """
        Removes node with given id.

        This command allows direct removal of DOM elements, which can be useful when
        testing how an application responds to missing elements or when simplifying
        a page for focused testing scenarios.

        Args:
            node_id: Id of the node to remove.

        Returns:
            Command: CDP command to remove the specified node.
        """
        params = RemoveNodeParams(nodeId=node_id)
        return Command(method=DomMethod.REMOVE_NODE, params=params)

    @staticmethod
    def request_child_nodes(
        node_id: int,
        depth: Optional[int] = None,
        pierce: Optional[bool] = None,
    ) -> Command[Response]:
        """
        Requests that children of the node with given id are returned to the caller.

        This method is particularly useful when dealing with large DOM trees, as it allows
        for more efficient exploration by loading children on demand rather than loading
        the entire tree at once. Child nodes are returned as setChildNodes events.

        Args:
            node_id: Id of the node to get children for.
            depth: The maximum depth at which children should be retrieved,
                  defaults to 1. Use -1 for the entire subtree.
            pierce: Whether or not iframes and shadow roots should be traversed.

        Returns:
            Command: CDP command to request child nodes.
        """
        params = RequestChildNodesParams(nodeId=node_id)
        if depth is not None:
            params['depth'] = depth
        if pierce is not None:
            params['pierce'] = pierce
        return Command(method=DomMethod.REQUEST_CHILD_NODES, params=params)

    @staticmethod
    def request_node(
        object_id: str,
    ) -> Command[RequestNodeResponse]:
        """
        Requests that the node is sent to the caller given the JavaScript node object reference.

        This method bridges the gap between JavaScript objects in the page context and the
        CDP's node representation system, allowing automation to work with elements that
        might only be available as JavaScript references (e.g., from event handlers).

        Args:
            object_id: JavaScript object id to convert into a Node.

        Returns:
            Command: CDP command that returns the Node id for the given object.
        """
        params = RequestNodeParams(objectId=object_id)
        return Command(method=DomMethod.REQUEST_NODE, params=params)

    @staticmethod
    def resolve_node(
        node_id: Optional[int] = None,
        backend_node_id: Optional[int] = None,
        object_group: Optional[str] = None,
        execution_context_id: Optional[int] = None,
    ) -> Command[ResolveNodeResponse]:
        """
        Resolves the JavaScript node object for a given NodeId or BackendNodeId.

        This method provides the opposite functionality of requestNode - instead of getting
        a CDP node from a JavaScript object, it gets a JavaScript object from a CDP node.
        This enables executing JavaScript operations on nodes identified through CDP.

        Args:
            node_id: Id of the node to resolve.
            backend_node_id: Backend id of the node to resolve.
            object_group: Symbolic group name that can be used to release multiple objects.
            execution_context_id: Execution context in which to resolve the node.

        Returns:
            Command: CDP command that returns a JavaScript object wrapper for the node.
        """
        params = ResolveNodeParams()
        if node_id is not None:
            params['nodeId'] = node_id
        if backend_node_id is not None:
            params['backendNodeId'] = backend_node_id
        if object_group is not None:
            params['objectGroup'] = object_group
        if execution_context_id is not None:
            params['executionContextId'] = execution_context_id
        return Command(method=DomMethod.RESOLVE_NODE, params=params)

    @staticmethod
    def scroll_into_view_if_needed(
        node_id: Optional[int] = None,
        backend_node_id: Optional[int] = None,
        object_id: Optional[str] = None,
        rect: Optional[Rect] = None,
    ) -> Command[Response]:
        """
        Scrolls the specified node into view if not already visible.

        This command is crucial for reliable web automation, as it ensures elements
        are actually visible in the viewport before attempting interactions. Modern
        websites often use lazy loading and have long scrollable areas, making this
        command essential for working with elements that may not be initially visible.

        Args:
            node_id: Identifier of the node.
            backend_node_id: Identifier of the backend node.
            object_id: JavaScript object id of the node wrapper.
            rect: Optional rect to scroll into view, relative to the node bounds.

        Returns:
            Command: CDP command to scroll the element into view.
        """
        params = ScrollIntoViewIfNeededParams()
        if node_id is not None:
            params['nodeId'] = node_id
        if backend_node_id is not None:
            params['backendNodeId'] = backend_node_id
        if object_id is not None:
            params['objectId'] = object_id
        if rect is not None:
            params['rect'] = rect
        return Command(method=DomMethod.SCROLL_INTO_VIEW_IF_NEEDED, params=params)

    @staticmethod
    def set_attributes_as_text(
        node_id: int,
        text: str,
        name: Optional[str] = None,
    ) -> Command[Response]:
        """
        Sets attribute for an element with given id, using text representation.

        This command allows for more complex attribute manipulation than set_attribute_value,
        as it accepts a text representation that can potentially define multiple attributes
        or include special formatting. It's particularly useful when trying to replicate
        exactly how attributes would be defined in HTML source code.

        Args:
            node_id: Id of the element to set attribute for.
            text: Text with a new attribute value.
            name: Attribute name to replace with new text value.

        Returns:
            Command: CDP command to set an attribute as text.
        """
        params = SetAttributeAsTextParams(nodeId=node_id, text=text)
        if name is not None:
            params['name'] = name
        return Command(method=DomMethod.SET_ATTRIBUTES_AS_TEXT, params=params)

    @staticmethod
    def set_attribute_value(
        node_id: int,
        name: str,
        value: str,
    ) -> Command[Response]:
        """
        Sets attribute for element with given id.

        This command provides direct control over element attributes without using JavaScript,
        which is essential for testing how applications respond to attribute changes or for
        setting up specific test conditions by controlling element attributes directly.

        Args:
            node_id: Id of the element to set attribute for.
            name: Attribute name.
            value: Attribute value.

        Returns:
            Command: CDP command to set an attribute value.
        """
        params = SetAttributeValueParams(nodeId=node_id, name=name, value=value)
        return Command(method=DomMethod.SET_ATTRIBUTE_VALUE, params=params)

    @staticmethod
    def set_file_input_files(
        files: list[str],
        node_id: Optional[int] = None,
        backend_node_id: Optional[int] = None,
        object_id: Optional[str] = None,
    ) -> Command[Response]:
        """
        Sets files for the given file input element.

        This command solves one of the most challenging automation problems: working with
        file inputs. It bypasses the OS-level file dialog that normally appears when clicking
        a file input, allowing automated tests to provide files programmatically.

        Args:
            files: list of file paths to set.
            node_id: Identifier of the node.
            backend_node_id: Identifier of the backend node.
            object_id: JavaScript object id of the node wrapper.

        Returns:
            Command: CDP command to set files for a file input element.
        """
        params = SetFileInputFilesParams(files=files)
        if node_id is not None:
            params['nodeId'] = node_id
        if backend_node_id is not None:
            params['backendNodeId'] = backend_node_id
        if object_id is not None:
            params['objectId'] = object_id
        return Command(method=DomMethod.SET_FILE_INPUT_FILES, params=params)

    @staticmethod
    def set_node_name(
        node_id: int,
        name: str,
    ) -> Command[SetNodeNameResponse]:
        """
        Sets node name for a node with given id.

        This command allows changing the actual tag name of an element, which can be useful
        for testing how applications handle different types of elements or for testing the
        impact of semantic HTML choices on accessibility and behavior.

        Args:
            node_id: Id of the node to set name for.
            name: New node name.

        Returns:
            Command: CDP command that returns the new node id after the name change.
        """
        params = SetNodeNameParams(nodeId=node_id, name=name)
        return Command(method=DomMethod.SET_NODE_NAME, params=params)

    @staticmethod
    def set_node_value(
        node_id: int,
        value: str,
    ) -> Command[Response]:
        """
        Sets node value for a node with given id.

        This command is particularly useful for updating the content of text nodes and
        comments, allowing direct manipulation of text content without changing the
        surrounding HTML structure.

        Args:
            node_id: Id of the node to set value for.
            value: New node value.

        Returns:
            Command: CDP command to set a node's value.
        """
        params = SetNodeValueParams(nodeId=node_id, value=value)
        return Command(method=DomMethod.SET_NODE_VALUE, params=params)

    @staticmethod
    def set_outer_html(
        node_id: int,
        outer_html: str,
    ) -> Command[Response]:
        """
        Sets node HTML markup, replacing existing one.

        This is one of the most powerful DOM manipulation commands, as it allows completely
        replacing an element and all its children with new HTML. This is useful for making
        major structural changes to the page or for testing how applications handle
        dynamically inserted content.

        Args:
            node_id: Id of the node to set outer HTML for.
            outer_html: HTML markup to set.

        Returns:
            Command: CDP command to set the outer HTML of a node.
        """
        params = SetOuterHTMLParams(nodeId=node_id, outerHTML=outer_html)
        return Command(method=DomMethod.SET_OUTER_HTML, params=params)

    @staticmethod
    def collect_class_names_from_subtree(
        node_id: int,
    ) -> Command[CollectClassNamesFromSubtreeResponse]:
        """
        Collects class names for the node with given id and all of its children.

        This method is valuable for understanding the styling landscape of a page,
        especially in complex applications where multiple CSS frameworks might be
        in use or where classes are dynamically applied.

        Args:
            node_id: Id of the node to collect class names for.

        Returns:
            Command: CDP command that returns a list of all unique class names in the subtree.
        """
        params = CollectClassNamesFromSubtreeParams(nodeId=node_id)
        return Command(method=DomMethod.COLLECT_CLASS_NAMES_FROM_SUBTREE, params=params)

    @staticmethod
    def copy_to(
        node_id: int,
        target_node_id: int,
        insert_before_node_id: Optional[int] = None,
    ) -> Command[CopyToResponse]:
        """
        Creates a deep copy of the specified node and places it into the target container.

        Unlike move_to, this command creates a copy of the node, leaving the original intact.
        This is useful when you want to duplicate content rather than move it, such as when
        testing how multiple instances of the same component behave.

        Args:
            node_id: Id of the node to copy.
            target_node_id: Id of the element to drop the copy into.
            insert_before_node_id: Drop the copy before this node (if absent, the copy becomes
                                 the last child of target_node_id).

        Returns:
            Command: CDP command that returns the id of the new copy.
        """
        params = CopyToParams(nodeId=node_id, targetNodeId=target_node_id)
        if insert_before_node_id is not None:
            params['insertBeforeNodeId'] = insert_before_node_id
        return Command(method=DomMethod.COPY_TO, params=params)

    @staticmethod
    def discard_search_results(
        search_id: str,
    ) -> Command[Response]:
        """
        Discards search results from the session with the given id.

        This method helps manage resources when performing multiple searches during
        a session, allowing explicit cleanup of search results that are no longer needed.

        Args:
            search_id: Unique search session identifier.

        Returns:
            Command: CDP command to discard search results.
        """
        params = DiscardSearchResultsParams(searchId=search_id)
        return Command(method=DomMethod.DISCARD_SEARCH_RESULTS, params=params)

    @staticmethod
    def get_anchor_element(
        node_id: int,
        anchor_specifier: Optional[str] = None,
    ) -> Command[GetAnchorElementResponse]:
        """
        Finds the closest ancestor node that is an anchor element for the given node.

        This method is useful when working with content inside links or when you need to
        find the enclosing link element for text or other elements. This helps in cases
        where you might locate text but need to find the actual link around it.

        Args:
            node_id: Id of the node to search for an anchor around.
            anchor_specifier: Optional specifier for anchor tag properties.

        Returns:
            Command: CDP command that returns the anchor element node information.
        """
        params = GetAnchorElementParams(nodeId=node_id)
        if anchor_specifier is not None:
            params['anchorSpecifier'] = anchor_specifier
        return Command(method=DomMethod.GET_ANCHOR_ELEMENT, params=params)

    @staticmethod
    def get_container_for_node(
        node_id: int,
        container_name: Optional[str] = None,
        physical_axes: Optional[PhysicalAxes] = None,
        logical_axes: Optional[LogicalAxes] = None,
        queries_scroll_state: Optional[bool] = None,
    ) -> Command[GetContainerForNodeResponse]:
        """
        Finds a containing element for the given node based on specified parameters.

        This method helps in understanding the structural and layout context of elements,
        particularly in complex layouts using CSS features like flexbox, grid, or when
        dealing with scrollable containers.

        Args:
            node_id: Id of the node to find the container for.
            container_name: Name of the container to look for (e.g., 'scrollable', 'flex').
            physical_axes: Physical axes to consider (Horizontal, Vertical, Both).
            logical_axes: Logical axes to consider (Inline, Block, Both).
            queries_scroll_state: Whether to query scroll state or not.

        Returns:
            Command: CDP command that returns information about the containing element.
        """
        params = GetContainerForNodeParams(nodeId=node_id)
        if container_name is not None:
            params['containerName'] = container_name
        if physical_axes is not None:
            params['physicalAxes'] = physical_axes
        if logical_axes is not None:
            params['logicalAxes'] = logical_axes
        if queries_scroll_state is not None:
            params['queriesScrollState'] = queries_scroll_state
        return Command(method=DomMethod.GET_CONTAINER_FOR_NODE, params=params)

    @staticmethod
    def get_content_quads(
        node_id: Optional[int] = None,
        backend_node_id: Optional[int] = None,
        object_id: Optional[str] = None,
    ) -> Command[GetContentQuadsResponse]:
        """
        Returns quads that describe node position on the page.

        This method provides detailed geometric information about an element's position
        on the page, accounting for any transformations, rotations, or other CSS effects.
        This is more precise than getBoxModel for complex layouts.

        Args:
            node_id: Identifier of the node.
            backend_node_id: Identifier of the backend node.
            object_id: JavaScript object id of the node wrapper.

        Returns:
            Command: CDP command that returns the quads describing the node position.
        """
        params = GetContentQuadsParams()
        if node_id is not None:
            params['nodeId'] = node_id
        if backend_node_id is not None:
            params['backendNodeId'] = backend_node_id
        if object_id is not None:
            params['objectId'] = object_id
        return Command(method=DomMethod.GET_CONTENT_QUADS, params=params)

    @staticmethod
    def get_detached_dom_nodes() -> Command[GetDetachedDomNodesResponse]:
        """
        Returns information about detached DOM tree elements.

        This method is primarily useful for debugging memory issues related to the DOM,
        as detached DOM nodes (nodes no longer in the document but still referenced in
        JavaScript) are a common cause of memory leaks in web applications.

        Returns:
            Command: CDP command that returns information about detached DOM nodes.
        """
        return Command(method=DomMethod.GET_DETACHED_DOM_NODES)

    @staticmethod
    def get_element_by_relation(
        node_id: int,
        relation: ElementRelation,
    ) -> Command[GetElementByRelationResponse]:
        """
        Retrieves an element related to the given one in a specified way.

        This method provides a way to find elements based on their relationships to other
        elements, such as finding the next focusable element after a given one. This is
        useful for simulating keyboard navigation or for analyzing element relationships.

        Args:
            node_id: Id of the reference node.
            relation: Type of relationship (e.g., nextSibling, previousSibling, firstChild).

        Returns:
            Command: CDP command that returns the related element node.
        """
        params = GetElementByRelationParams(nodeId=node_id, relation=relation)
        return Command(method=DomMethod.GET_ELEMENT_BY_RELATION, params=params)

    @staticmethod
    def get_file_info(
        object_id: str,
    ) -> Command[GetFileInfoResponse]:
        """
        Returns file information for the given File object.

        This method is useful when working with file inputs and the File API, providing
        access to file metadata like name, size, and MIME type for files selected in
        file input elements or created programmatically.

        Args:
            object_id: JavaScript object id of the File object to get info for.

        Returns:
            Command: CDP command that returns file information.
        """
        params = GetFileInfoParams(objectId=object_id)
        return Command(method=DomMethod.GET_FILE_INFO, params=params)

    @staticmethod
    def get_frame_owner(
        frame_id: str,
    ) -> Command[GetFrameOwnerResponse]:
        """
        Returns iframe element that owns the given frame.

        This method is essential when working with pages that contain iframes, as it
        allows mapping between frame IDs (used in CDP) and the actual iframe elements
        in the parent document.

        Args:
            frame_id: Id of the frame to get the owner element for.

        Returns:
            Command: CDP command that returns the frame owner element.
        """
        params = GetFrameOwnerParams(frameId=frame_id)
        return Command(method=DomMethod.GET_FRAME_OWNER, params=params)

    @staticmethod
    def get_nodes_for_subtree_by_style(
        node_id: int,
        computed_styles: list[CSSComputedStyleProperty],
        pierce: Optional[bool] = None,
    ) -> Command[GetNodesForSubtreeByStyleResponse]:
        """
        Finds nodes with a given computed style in a subtree.

        This method allows finding elements based on their computed styles rather than just
        structure or attributes. This is powerful for testing visual aspects of a page or
        for finding elements that match specific visual criteria.

        Args:
            node_id: Node to start the search from.
            computed_styles: list of computed style properties to match against.
            pierce: Whether or not iframes and shadow roots should be traversed.

        Returns:
            Command: CDP command that returns nodes matching the specified styles.
        """
        params = GetNodesForSubtreeByStyleParams(nodeId=node_id, computedStyles=computed_styles)
        if pierce is not None:
            params['pierce'] = pierce
        return Command(method=DomMethod.GET_NODES_FOR_SUBTREE_BY_STYLE, params=params)

    @staticmethod
    def get_node_stack_traces(
        node_id: int,
    ) -> Command[GetNodeStackTracesResponse]:
        """
        Gets stack traces associated with a specific node.

        This method is powerful for debugging, as it reveals the JavaScript execution paths
        that led to the creation of specific DOM elements, helping developers understand
        the relationship between their code and the resulting DOM structure.

        Args:
            node_id: Id of the node to get stack traces for.

        Returns:
            Command: CDP command that returns stack traces related to the node.
        """
        params = GetNodeStackTracesParams(nodeId=node_id)
        return Command(method=DomMethod.GET_NODE_STACK_TRACES, params=params)

    @staticmethod
    def get_querying_descendants_for_container(
        node_id: int,
    ) -> Command[GetQueryingDescendantForContainerResponse]:
        """
        Returns the querying descendants for container.

        This method is particularly useful for working with CSS Container Queries, helping
        to identify which descendant elements are affected by or querying a particular
        container element.

        Args:
            node_id: Id of the container node to find querying descendants for.

        Returns:
            Command: CDP command that returns querying descendant information.
        """
        params = GetQueryingDescendantForContainerParams(nodeId=node_id)
        return Command(method=DomMethod.GET_QUERYING_DESCENDANTS_FOR_CONTAINER, params=params)

    @staticmethod
    def get_relayout_boundary(
        node_id: int,
    ) -> Command[GetRelayoutBoundaryResponse]:
        """
        Returns the root of the relayout boundary for the given node.

        This method helps in understanding layout performance by identifying the boundary
        of layout recalculations when a particular element changes. This is valuable for
        optimizing rendering performance.

        Args:
            node_id: Id of the node to find relayout boundary for.

        Returns:
            Command: CDP command that returns the relayout boundary node.
        """
        params = GetRelayoutBoundaryParams(nodeId=node_id)
        return Command(method=DomMethod.GET_RELAYOUT_BOUNDARY, params=params)

    @staticmethod
    def get_search_results(
        search_id: str,
        from_index: int,
        to_index: int,
    ) -> Command[GetSearchResultsResponse]:
        """
        Returns search results from given `fromIndex` to given `toIndex` from a search.

        This method is used in conjunction with performSearch to retrieve search results
        in batches, which is essential when dealing with large result sets that might
        be inefficient to transfer all at once.

        Args:
            search_id: Unique search session identifier from performSearch.
            from_index: Start index to retrieve results from.
            to_index: End index to retrieve results to (exclusive).

        Returns:
            Command: CDP command that returns the requested search results.
        """
        params = GetSearchResultsParams(searchId=search_id, fromIndex=from_index, toIndex=to_index)
        return Command(method=DomMethod.GET_SEARCH_RESULTS, params=params)

    @staticmethod
    def get_top_layer_elements() -> Command[GetTopLayerElementsResponse]:
        """
        Returns all top layer elements in the document.

        This method is valuable for working with modern web UIs that make extensive use
        of overlays, modals, dropdowns, and other elements that need to appear above
        the normal document flow.

        Returns:
            Command: CDP command that returns the top layer element information.
        """
        return Command(method=DomMethod.GET_TOP_LAYER_ELEMENTS)

    @staticmethod
    def mark_undoable_state() -> Command[Response]:
        """
        Marks last undoable state.

        This method helps in managing DOM manipulation state, allowing the creation of
        savepoints that can be reverted to with the undo command. This is useful for
        complex sequences of DOM operations that should be treated as a unit.

        Returns:
            Command: CDP command to mark the current state as undoable.
        """
        return Command(method=DomMethod.MARK_UNDOABLE_STATE)

    @staticmethod
    def perform_search(
        query: str,
        include_user_agent_shadow_dom: Optional[bool] = None,
    ) -> Command[PerformSearchResponse]:
        """
        Searches for a given string in the DOM tree.

        This method initiates a search across the DOM tree, supporting plain text,
        CSS selectors, or XPath expressions. It's a powerful way to find elements
        or content across the entire document without knowing the exact structure.

        Args:
            query: Plain text or query selector or XPath search query.
            include_user_agent_shadow_dom: True to include user agent shadow DOM in the search.

        Returns:
            Command: CDP command that returns search results identifier and count.
        """
        params = PerformSearchParams(query=query)
        if include_user_agent_shadow_dom is not None:
            params['includeUserAgentShadowDOM'] = include_user_agent_shadow_dom
        return Command(method=DomMethod.PERFORM_SEARCH, params=params)

    @staticmethod
    def push_node_by_path_to_frontend(
        path: str,
    ) -> Command[PushNodeByPathToFrontendResponse]:
        """
        Requests that the node is sent to the caller given its path.

        This method provides an alternative way to reference nodes when node IDs aren't
        available, using path expressions instead. This can be useful when integrating
        with systems that identify elements by path rather than by ID.

        Args:
            path: Path to node in the proprietary format.

        Returns:
            Command: CDP command that returns the node id for the node.
        """
        params = PushNodeByPathToFrontendParams(path=path)
        return Command(method=DomMethod.PUSH_NODE_BY_PATH_TO_FRONTEND, params=params)

    @staticmethod
    def push_nodes_by_backend_ids_to_frontend(
        backend_node_ids: list[int],
    ) -> Command[PushNodesByBackendIdsToFrontendResponse]:
        """
        Requests that a batch of nodes is sent to the caller given their backend node ids.

        This method allows for efficient batch processing when you have multiple backend
        node IDs and need to convert them to frontend node IDs for further operations.

        Args:
            backend_node_ids: The array of backend node ids.

        Returns:
            Command: CDP command that returns an array of node ids.
        """
        params = PushNodesByBackendIdsToFrontendParams(backendNodeIds=backend_node_ids)
        return Command(method=DomMethod.PUSH_NODES_BY_BACKEND_IDS_TO_FRONTEND, params=params)

    @staticmethod
    def redo() -> Command[Response]:
        """
        Re-does the last undone action.

        This method works in conjunction with undo and markUndoableState to provide
        a transactional approach to DOM manipulations, allowing for stepping back and
        forth through a sequence of changes.

        Returns:
            Command: CDP command to redo the last undone action.
        """
        return Command(method=DomMethod.REDO)

    @staticmethod
    def set_inspected_node(
        node_id: int,
    ) -> Command[Response]:
        """
        Enables console to refer to the node with given id via $x command line API.

        This method creates a bridge between automated testing/scripting and manual console
        interaction, making it easy to reference specific nodes in the console for
        debugging or experimentation.

        Args:
            node_id: DOM node id to be accessible by means of $x command line API.

        Returns:
            Command: CDP command to set the inspected node.
        """
        params = SetInspectedNodeParams(nodeId=node_id)
        return Command(method=DomMethod.SET_INSPECTED_NODE, params=params)

    @staticmethod
    def set_node_stack_traces_enabled(
        enable: bool,
    ) -> Command[Response]:
        """
        Sets if stack traces should be captured for Nodes.

        This method enables or disables the collection of stack traces when DOM nodes
        are created, which can be extremely valuable for debugging complex applications
        to understand where and why specific DOM elements are being created.

        Args:
            enable: Enable or disable stack trace collection.

        Returns:
            Command: CDP command to enable or disable node stack traces.
        """
        params = SetNodeStackTracesEnabledParams(enable=enable)
        return Command(method=DomMethod.SET_NODE_STACK_TRACES_ENABLED, params=params)

    @staticmethod
    def undo() -> Command[Response]:
        """
        Undoes the last performed action.

        This method works in conjunction with redo and markUndoableState to provide
        transactional control over DOM manipulations, allowing for reverting changes
        when needed.

        Returns:
            Command: CDP command to undo the last performed action.
        """
        return Command(method=DomMethod.UNDO)
