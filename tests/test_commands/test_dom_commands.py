from pydoll.commands.dom_commands import DomCommands
from pydoll.constants import ElementRelation, IncludeWhitespace, LogicalAxes, PhysicalAxes
from pydoll.protocol.dom.methods import DomMethod


class TestDomCommands:
    """Tests for the DomCommands class."""

    def test_describe_node_with_node_id(self):
        """Test describe_node command with node_id."""
        result = DomCommands.describe_node(node_id=123)
        
        assert result['method'] == DomMethod.DESCRIBE_NODE
        assert result['params']['nodeId'] == 123

    def test_describe_node_with_backend_node_id(self):
        """Test describe_node command with backend_node_id."""
        result = DomCommands.describe_node(backend_node_id=456)
        
        assert result['method'] == DomMethod.DESCRIBE_NODE
        assert result['params']['backendNodeId'] == 456

    def test_describe_node_with_object_id(self):
        """Test describe_node command with object_id."""
        result = DomCommands.describe_node(object_id='obj123')
        
        assert result['method'] == DomMethod.DESCRIBE_NODE
        assert result['params']['objectId'] == 'obj123'

    def test_describe_node_with_all_params(self):
        """Test describe_node command with all parameters."""
        result = DomCommands.describe_node(
            node_id=123,
            backend_node_id=456,
            object_id='obj123',
            depth=2,
            pierce=True
        )
        
        assert result['method'] == DomMethod.DESCRIBE_NODE
        assert result['params']['nodeId'] == 123
        assert result['params']['backendNodeId'] == 456
        assert result['params']['objectId'] == 'obj123'
        assert result['params']['depth'] == 2
        assert result['params']['pierce'] is True

    def test_disable(self):
        """Test disable command."""
        result = DomCommands.disable()
        
        assert result['method'] == DomMethod.DISABLE
        assert 'params' not in result

    def test_enable_without_params(self):
        """Test enable command without parameters."""
        result = DomCommands.enable()
        
        assert result['method'] == DomMethod.ENABLE
        assert 'params' in result

    def test_enable_with_include_whitespace(self):
        """Test enable command with include_whitespace."""
        result = DomCommands.enable(include_whitespace=IncludeWhitespace.ALL)
        
        assert result['method'] == DomMethod.ENABLE
        assert result['params']['includeWhitespace'] == IncludeWhitespace.ALL

    def test_focus_with_node_id(self):
        """Test focus command with node_id."""
        result = DomCommands.focus(node_id=123)
        
        assert result['method'] == DomMethod.FOCUS
        assert result['params']['nodeId'] == 123

    def test_focus_with_backend_node_id(self):
        """Test focus command with backend_node_id."""
        result = DomCommands.focus(backend_node_id=456)
        
        assert result['method'] == DomMethod.FOCUS
        assert result['params']['backendNodeId'] == 456

    def test_focus_with_object_id(self):
        """Test focus command with object_id."""
        result = DomCommands.focus(object_id='obj123')
        
        assert result['method'] == DomMethod.FOCUS
        assert result['params']['objectId'] == 'obj123'

    def test_get_attributes(self):
        """Test get_attributes command."""
        result = DomCommands.get_attributes(node_id=123)
        
        assert result['method'] == DomMethod.GET_ATTRIBUTES
        assert result['params']['nodeId'] == 123

    def test_get_box_model_with_node_id(self):
        """Test get_box_model command with node_id."""
        result = DomCommands.get_box_model(node_id=123)
        
        assert result['method'] == DomMethod.GET_BOX_MODEL
        assert result['params']['nodeId'] == 123

    def test_get_box_model_with_backend_node_id(self):
        """Test get_box_model command with backend_node_id."""
        result = DomCommands.get_box_model(backend_node_id=456)
        
        assert result['method'] == DomMethod.GET_BOX_MODEL
        assert result['params']['backendNodeId'] == 456

    def test_get_box_model_with_object_id(self):
        """Test get_box_model command with object_id."""
        result = DomCommands.get_box_model(object_id='obj123')
        
        assert result['method'] == DomMethod.GET_BOX_MODEL
        assert result['params']['objectId'] == 'obj123'

    def test_get_document_without_params(self):
        """Test get_document command without parameters."""
        result = DomCommands.get_document()
        
        assert result['method'] == DomMethod.GET_DOCUMENT
        assert 'params' in result

    def test_get_document_with_depth(self):
        """Test get_document command with depth."""
        result = DomCommands.get_document(depth=2)
        
        assert result['method'] == DomMethod.GET_DOCUMENT
        assert result['params']['depth'] == 2

    def test_get_document_with_pierce(self):
        """Test get_document command with pierce."""
        result = DomCommands.get_document(pierce=True)
        
        assert result['method'] == DomMethod.GET_DOCUMENT
        assert result['params']['pierce'] is True

    def test_get_node_for_location(self):
        """Test get_node_for_location command."""
        result = DomCommands.get_node_for_location(x=100, y=200)
        
        assert result['method'] == DomMethod.GET_NODE_FOR_LOCATION
        assert result['params']['x'] == 100
        assert result['params']['y'] == 200

    def test_get_node_for_location_with_optional_params(self):
        """Test get_node_for_location command with optional parameters."""
        result = DomCommands.get_node_for_location(
            x=100, 
            y=200,
            include_user_agent_shadow_dom=True,
            ignore_pointer_events_none=False
        )
        
        assert result['method'] == DomMethod.GET_NODE_FOR_LOCATION
        assert result['params']['x'] == 100
        assert result['params']['y'] == 200
        assert result['params']['includeUserAgentShadowDOM'] is True
        assert result['params']['ignorePointerEventsNone'] is False

    def test_get_outer_html_with_node_id(self):
        """Test get_outer_html command with node_id."""
        result = DomCommands.get_outer_html(node_id=123)
        
        assert result['method'] == DomMethod.GET_OUTER_HTML
        assert result['params']['nodeId'] == 123

    def test_get_outer_html_with_backend_node_id(self):
        """Test get_outer_html command with backend_node_id."""
        result = DomCommands.get_outer_html(backend_node_id=456)
        
        assert result['method'] == DomMethod.GET_OUTER_HTML
        assert result['params']['backendNodeId'] == 456

    def test_get_outer_html_with_object_id(self):
        """Test get_outer_html command with object_id."""
        result = DomCommands.get_outer_html(object_id='obj123')
        
        assert result['method'] == DomMethod.GET_OUTER_HTML
        assert result['params']['objectId'] == 'obj123'

    def test_hide_highlight(self):
        """Test hide_highlight command."""
        result = DomCommands.hide_highlight()
        
        assert result['method'] == DomMethod.HIDE_HIGHLIGHT
        assert 'params' not in result

    def test_highlight_node(self):
        """Test highlight_node command."""
        result = DomCommands.highlight_node()
        
        assert result['method'] == DomMethod.HIGHLIGHT_NODE
        assert 'params' not in result

    def test_highlight_rect(self):
        """Test highlight_rect command."""
        result = DomCommands.highlight_rect()
        
        assert result['method'] == DomMethod.HIGHLIGHT_RECT
        assert 'params' not in result

    def test_move_to(self):
        """Test move_to command."""
        result = DomCommands.move_to(node_id=123, target_node_id=456)
        
        assert result['method'] == DomMethod.MOVE_TO
        assert result['params']['nodeId'] == 123
        assert result['params']['targetNodeId'] == 456

    def test_move_to_with_insert_before(self):
        """Test move_to command with insert_before_node_id."""
        result = DomCommands.move_to(
            node_id=123, 
            target_node_id=456, 
            insert_before_node_id=789
        )
        
        assert result['method'] == DomMethod.MOVE_TO
        assert result['params']['nodeId'] == 123
        assert result['params']['targetNodeId'] == 456
        assert result['params']['insertBeforeNodeId'] == 789

    def test_query_selector(self):
        """Test query_selector command."""
        result = DomCommands.query_selector(node_id=123, selector='.test-class')
        
        assert result['method'] == DomMethod.QUERY_SELECTOR
        assert result['params']['nodeId'] == 123
        assert result['params']['selector'] == '.test-class'

    def test_query_selector_all(self):
        """Test query_selector_all command."""
        result = DomCommands.query_selector_all(node_id=123, selector='div')
        
        assert result['method'] == DomMethod.QUERY_SELECTOR_ALL
        assert result['params']['nodeId'] == 123
        assert result['params']['selector'] == 'div'

    def test_remove_attribute(self):
        """Test remove_attribute command."""
        result = DomCommands.remove_attribute(node_id=123, name='class')
        
        assert result['method'] == DomMethod.REMOVE_ATTRIBUTE
        assert result['params']['nodeId'] == 123
        assert result['params']['name'] == 'class'

    def test_remove_node(self):
        """Test remove_node command."""
        result = DomCommands.remove_node(node_id=123)
        
        assert result['method'] == DomMethod.REMOVE_NODE
        assert result['params']['nodeId'] == 123

    def test_request_child_nodes(self):
        """Test request_child_nodes command."""
        result = DomCommands.request_child_nodes(node_id=123)
        
        assert result['method'] == DomMethod.REQUEST_CHILD_NODES
        assert result['params']['nodeId'] == 123

    def test_request_child_nodes_with_depth(self):
        """Test request_child_nodes command with depth."""
        result = DomCommands.request_child_nodes(node_id=123, depth=2)
        
        assert result['method'] == DomMethod.REQUEST_CHILD_NODES
        assert result['params']['nodeId'] == 123
        assert result['params']['depth'] == 2

    def test_request_child_nodes_with_pierce(self):
        """Test request_child_nodes command with pierce."""
        result = DomCommands.request_child_nodes(node_id=123, pierce=True)
        
        assert result['method'] == DomMethod.REQUEST_CHILD_NODES
        assert result['params']['nodeId'] == 123
        assert result['params']['pierce'] is True

    def test_request_node(self):
        """Test request_node command."""
        result = DomCommands.request_node(object_id='obj123')
        
        assert result['method'] == DomMethod.REQUEST_NODE
        assert result['params']['objectId'] == 'obj123'

    def test_resolve_node_with_node_id(self):
        """Test resolve_node command with node_id."""
        result = DomCommands.resolve_node(node_id=123)
        
        assert result['method'] == DomMethod.RESOLVE_NODE
        assert result['params']['nodeId'] == 123

    def test_resolve_node_with_backend_node_id(self):
        """Test resolve_node command with backend_node_id."""
        result = DomCommands.resolve_node(backend_node_id=456)
        
        assert result['method'] == DomMethod.RESOLVE_NODE
        assert result['params']['backendNodeId'] == 456

    def test_resolve_node_with_all_params(self):
        """Test resolve_node command with all parameters."""
        result = DomCommands.resolve_node(
            node_id=123,
            backend_node_id=456,
            object_group='test-group',
            execution_context_id=789
        )
        
        assert result['method'] == DomMethod.RESOLVE_NODE
        assert result['params']['nodeId'] == 123
        assert result['params']['backendNodeId'] == 456
        assert result['params']['objectGroup'] == 'test-group'
        assert result['params']['executionContextId'] == 789

    def test_scroll_into_view_if_needed_with_node_id(self):
        """Test scroll_into_view_if_needed command with node_id."""
        result = DomCommands.scroll_into_view_if_needed(node_id=123)
        
        assert result['method'] == DomMethod.SCROLL_INTO_VIEW_IF_NEEDED
        assert result['params']['nodeId'] == 123

    def test_scroll_into_view_if_needed_with_backend_node_id(self):
        """Test scroll_into_view_if_needed command with backend_node_id."""
        result = DomCommands.scroll_into_view_if_needed(backend_node_id=456)
        
        assert result['method'] == DomMethod.SCROLL_INTO_VIEW_IF_NEEDED
        assert result['params']['backendNodeId'] == 456

    def test_scroll_into_view_if_needed_with_object_id(self):
        """Test scroll_into_view_if_needed command with object_id."""
        result = DomCommands.scroll_into_view_if_needed(object_id='obj123')
        
        assert result['method'] == DomMethod.SCROLL_INTO_VIEW_IF_NEEDED
        assert result['params']['objectId'] == 'obj123'

    def test_set_attributes_as_text(self):
        """Test set_attributes_as_text command."""
        result = DomCommands.set_attributes_as_text(node_id=123, text='class="test"')
        
        assert result['method'] == DomMethod.SET_ATTRIBUTES_AS_TEXT
        assert result['params']['nodeId'] == 123
        assert result['params']['text'] == 'class="test"'

    def test_set_attributes_as_text_with_name(self):
        """Test set_attributes_as_text command with name."""
        result = DomCommands.set_attributes_as_text(
            node_id=123, 
            text='test-value', 
            name='class'
        )
        
        assert result['method'] == DomMethod.SET_ATTRIBUTES_AS_TEXT
        assert result['params']['nodeId'] == 123
        assert result['params']['text'] == 'test-value'
        assert result['params']['name'] == 'class'

    def test_set_attribute_value(self):
        """Test set_attribute_value command."""
        result = DomCommands.set_attribute_value(
            node_id=123, 
            name='class', 
            value='test-class'
        )
        
        assert result['method'] == DomMethod.SET_ATTRIBUTE_VALUE
        assert result['params']['nodeId'] == 123
        assert result['params']['name'] == 'class'
        assert result['params']['value'] == 'test-class'

    def test_set_file_input_files_with_node_id(self):
        """Test set_file_input_files command with node_id."""
        files = ['/path/to/file1.txt', '/path/to/file2.txt']
        result = DomCommands.set_file_input_files(files=files, node_id=123)
        
        assert result['method'] == DomMethod.SET_FILE_INPUT_FILES
        assert result['params']['files'] == files
        assert result['params']['nodeId'] == 123

    def test_set_file_input_files_with_backend_node_id(self):
        """Test set_file_input_files command with backend_node_id."""
        files = ['/path/to/file.txt']
        result = DomCommands.set_file_input_files(files=files, backend_node_id=456)
        
        assert result['method'] == DomMethod.SET_FILE_INPUT_FILES
        assert result['params']['files'] == files
        assert result['params']['backendNodeId'] == 456

    def test_set_file_input_files_with_object_id(self):
        """Test set_file_input_files command with object_id."""
        files = ['/path/to/file.txt']
        result = DomCommands.set_file_input_files(files=files, object_id='obj123')
        
        assert result['method'] == DomMethod.SET_FILE_INPUT_FILES
        assert result['params']['files'] == files
        assert result['params']['objectId'] == 'obj123'

    def test_set_node_name(self):
        """Test set_node_name command."""
        result = DomCommands.set_node_name(node_id=123, name='div')
        
        assert result['method'] == DomMethod.SET_NODE_NAME
        assert result['params']['nodeId'] == 123
        assert result['params']['name'] == 'div'

    def test_set_node_value(self):
        """Test set_node_value command."""
        result = DomCommands.set_node_value(node_id=123, value='test text')
        
        assert result['method'] == DomMethod.SET_NODE_VALUE
        assert result['params']['nodeId'] == 123
        assert result['params']['value'] == 'test text'

    def test_set_outer_html(self):
        """Test set_outer_html command."""
        html = '<div class="test">content</div>'
        result = DomCommands.set_outer_html(node_id=123, outer_html=html)
        
        assert result['method'] == DomMethod.SET_OUTER_HTML
        assert result['params']['nodeId'] == 123
        assert result['params']['outerHTML'] == html

    def test_collect_class_names_from_subtree(self):
        """Test collect_class_names_from_subtree command."""
        result = DomCommands.collect_class_names_from_subtree(node_id=123)
        
        assert result['method'] == DomMethod.COLLECT_CLASS_NAMES_FROM_SUBTREE
        assert result['params']['nodeId'] == 123

    def test_copy_to(self):
        """Test copy_to command."""
        result = DomCommands.copy_to(node_id=123, target_node_id=456)
        
        assert result['method'] == DomMethod.COPY_TO
        assert result['params']['nodeId'] == 123
        assert result['params']['targetNodeId'] == 456

    def test_copy_to_with_insert_before(self):
        """Test copy_to command with insert_before_node_id."""
        result = DomCommands.copy_to(
            node_id=123, 
            target_node_id=456, 
            insert_before_node_id=789
        )
        
        assert result['method'] == DomMethod.COPY_TO
        assert result['params']['nodeId'] == 123
        assert result['params']['targetNodeId'] == 456
        assert result['params']['insertBeforeNodeId'] == 789

    def test_discard_search_results(self):
        """Test discard_search_results command."""
        result = DomCommands.discard_search_results(search_id='search123')
        
        assert result['method'] == DomMethod.DISCARD_SEARCH_RESULTS
        assert result['params']['searchId'] == 'search123'

    def test_get_anchor_element(self):
        """Test get_anchor_element command."""
        result = DomCommands.get_anchor_element(node_id=123)
        
        assert result['method'] == DomMethod.GET_ANCHOR_ELEMENT
        assert result['params']['nodeId'] == 123

    def test_get_anchor_element_with_specifier(self):
        """Test get_anchor_element command with anchor_specifier."""
        result = DomCommands.get_anchor_element(
            node_id=123, 
            anchor_specifier='href'
        )
        
        assert result['method'] == DomMethod.GET_ANCHOR_ELEMENT
        assert result['params']['nodeId'] == 123
        assert result['params']['anchorSpecifier'] == 'href'

    def test_get_container_for_node(self):
        """Test get_container_for_node command."""
        result = DomCommands.get_container_for_node(node_id=123)
        
        assert result['method'] == DomMethod.GET_CONTAINER_FOR_NODE
        assert result['params']['nodeId'] == 123

    def test_get_container_for_node_with_all_params(self):
        """Test get_container_for_node command with all parameters."""
        result = DomCommands.get_container_for_node(
            node_id=123,
            container_name='scrollable',
            physical_axes=PhysicalAxes.HORIZONTAL,
            logical_axes=LogicalAxes.INLINE,
            queries_scroll_state=True
        )
        
        assert result['method'] == DomMethod.GET_CONTAINER_FOR_NODE
        assert result['params']['nodeId'] == 123
        assert result['params']['containerName'] == 'scrollable'
        assert result['params']['physicalAxes'] == PhysicalAxes.HORIZONTAL
        assert result['params']['logicalAxes'] == LogicalAxes.INLINE
        assert result['params']['queriesScrollState'] is True

    def test_get_content_quads_with_node_id(self):
        """Test get_content_quads command with node_id."""
        result = DomCommands.get_content_quads(node_id=123)
        
        assert result['method'] == DomMethod.GET_CONTENT_QUADS
        assert result['params']['nodeId'] == 123

    def test_get_content_quads_with_backend_node_id(self):
        """Test get_content_quads command with backend_node_id."""
        result = DomCommands.get_content_quads(backend_node_id=456)
        
        assert result['method'] == DomMethod.GET_CONTENT_QUADS
        assert result['params']['backendNodeId'] == 456

    def test_get_content_quads_with_object_id(self):
        """Test get_content_quads command with object_id."""
        result = DomCommands.get_content_quads(object_id='obj123')
        
        assert result['method'] == DomMethod.GET_CONTENT_QUADS
        assert result['params']['objectId'] == 'obj123'

    def test_get_detached_dom_nodes(self):
        """Test get_detached_dom_nodes command."""
        result = DomCommands.get_detached_dom_nodes()
        
        assert result['method'] == DomMethod.GET_DETACHED_DOM_NODES
        assert 'params' not in result

    def test_get_element_by_relation(self):
        """Test get_element_by_relation command."""
        result = DomCommands.get_element_by_relation(
            node_id=123, 
            relation=ElementRelation.INTEREST_TARGET
        )
        
        assert result['method'] == DomMethod.GET_ELEMENT_BY_RELATION
        assert result['params']['nodeId'] == 123
        assert result['params']['relation'] == ElementRelation.INTEREST_TARGET

    def test_get_file_info(self):
        """Test get_file_info command."""
        result = DomCommands.get_file_info(object_id='file123')
        
        assert result['method'] == DomMethod.GET_FILE_INFO
        assert result['params']['objectId'] == 'file123'

    def test_get_frame_owner(self):
        """Test get_frame_owner command."""
        result = DomCommands.get_frame_owner(frame_id='frame123')
        
        assert result['method'] == DomMethod.GET_FRAME_OWNER
        assert result['params']['frameId'] == 'frame123'

    def test_get_nodes_for_subtree_by_style(self):
        """Test get_nodes_for_subtree_by_style command."""
        computed_styles = [{'name': 'color', 'value': 'red'}]
        result = DomCommands.get_nodes_for_subtree_by_style(
            node_id=123, 
            computed_styles=computed_styles
        )
        
        assert result['method'] == DomMethod.GET_NODES_FOR_SUBTREE_BY_STYLE
        assert result['params']['nodeId'] == 123
        assert result['params']['computedStyles'] == computed_styles

    def test_get_nodes_for_subtree_by_style_with_pierce(self):
        """Test get_nodes_for_subtree_by_style command with pierce."""
        computed_styles = [{'name': 'display', 'value': 'block'}]
        result = DomCommands.get_nodes_for_subtree_by_style(
            node_id=123, 
            computed_styles=computed_styles,
            pierce=True
        )
        
        assert result['method'] == DomMethod.GET_NODES_FOR_SUBTREE_BY_STYLE
        assert result['params']['nodeId'] == 123
        assert result['params']['computedStyles'] == computed_styles
        assert result['params']['pierce'] is True

    def test_get_node_stack_traces(self):
        """Test get_node_stack_traces command."""
        result = DomCommands.get_node_stack_traces(node_id=123)
        
        assert result['method'] == DomMethod.GET_NODE_STACK_TRACES
        assert result['params']['nodeId'] == 123

    def test_get_querying_descendants_for_container(self):
        """Test get_querying_descendants_for_container command."""
        result = DomCommands.get_querying_descendants_for_container(node_id=123)
        
        assert result['method'] == DomMethod.GET_QUERYING_DESCENDANTS_FOR_CONTAINER
        assert result['params']['nodeId'] == 123

    def test_get_relayout_boundary(self):
        """Test get_relayout_boundary command."""
        result = DomCommands.get_relayout_boundary(node_id=123)
        
        assert result['method'] == DomMethod.GET_RELAYOUT_BOUNDARY
        assert result['params']['nodeId'] == 123

    def test_get_search_results(self):
        """Test get_search_results command."""
        result = DomCommands.get_search_results(
            search_id='search123', 
            from_index=0, 
            to_index=10
        )
        
        assert result['method'] == DomMethod.GET_SEARCH_RESULTS
        assert result['params']['searchId'] == 'search123'
        assert result['params']['fromIndex'] == 0
        assert result['params']['toIndex'] == 10

    def test_get_top_layer_elements(self):
        """Test get_top_layer_elements command."""
        result = DomCommands.get_top_layer_elements()
        
        assert result['method'] == DomMethod.GET_TOP_LAYER_ELEMENTS
        assert 'params' not in result

    def test_mark_undoable_state(self):
        """Test mark_undoable_state command."""
        result = DomCommands.mark_undoable_state()
        
        assert result['method'] == DomMethod.MARK_UNDOABLE_STATE
        assert 'params' not in result

    def test_perform_search(self):
        """Test perform_search command."""
        result = DomCommands.perform_search(query='test')
        
        assert result['method'] == DomMethod.PERFORM_SEARCH
        assert result['params']['query'] == 'test'

    def test_perform_search_with_shadow_dom(self):
        """Test perform_search command with include_user_agent_shadow_dom."""
        result = DomCommands.perform_search(
            query='test', 
            include_user_agent_shadow_dom=True
        )
        
        assert result['method'] == DomMethod.PERFORM_SEARCH
        assert result['params']['query'] == 'test'
        assert result['params']['includeUserAgentShadowDOM'] is True

    def test_push_node_by_path_to_frontend(self):
        """Test push_node_by_path_to_frontend command."""
        result = DomCommands.push_node_by_path_to_frontend(path='1,2,3')
        
        assert result['method'] == DomMethod.PUSH_NODE_BY_PATH_TO_FRONTEND
        assert result['params']['path'] == '1,2,3'

    def test_push_nodes_by_backend_ids_to_frontend(self):
        """Test push_nodes_by_backend_ids_to_frontend command."""
        backend_ids = [123, 456, 789]
        result = DomCommands.push_nodes_by_backend_ids_to_frontend(
            backend_node_ids=backend_ids
        )
        
        assert result['method'] == DomMethod.PUSH_NODES_BY_BACKEND_IDS_TO_FRONTEND
        assert result['params']['backendNodeIds'] == backend_ids

    def test_redo(self):
        """Test redo command."""
        result = DomCommands.redo()
        
        assert result['method'] == DomMethod.REDO
        assert 'params' not in result

    def test_set_inspected_node(self):
        """Test set_inspected_node command."""
        result = DomCommands.set_inspected_node(node_id=123)
        
        assert result['method'] == DomMethod.SET_INSPECTED_NODE
        assert result['params']['nodeId'] == 123

    def test_set_node_stack_traces_enabled(self):
        """Test set_node_stack_traces_enabled command."""
        result = DomCommands.set_node_stack_traces_enabled(enable=True)
        
        assert result['method'] == DomMethod.SET_NODE_STACK_TRACES_ENABLED
        assert result['params']['enable'] is True

    def test_undo(self):
        """Test undo command."""
        result = DomCommands.undo()
        
        assert result['method'] == DomMethod.UNDO
        assert 'params' not in result
