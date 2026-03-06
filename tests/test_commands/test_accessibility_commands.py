"""
Tests for AccessibilityCommands class.

This module contains tests for all AccessibilityCommands methods,
verifying that they generate the correct CDP commands with proper parameters.
"""

import pytest

from pydoll.commands.accessibility_commands import AccessibilityCommands
from pydoll.protocol.accessibility.methods import AccessibilityMethod


# ---------------------------------------------------------------------------
# disable
# ---------------------------------------------------------------------------


def test_disable_returns_correct_method():
    result = AccessibilityCommands.disable()
    assert result['method'] == AccessibilityMethod.DISABLE


def test_disable_has_no_params():
    result = AccessibilityCommands.disable()
    assert 'params' not in result


# ---------------------------------------------------------------------------
# enable
# ---------------------------------------------------------------------------


def test_enable_returns_correct_method():
    result = AccessibilityCommands.enable()
    assert result['method'] == AccessibilityMethod.ENABLE


def test_enable_has_no_params():
    result = AccessibilityCommands.enable()
    assert 'params' not in result


# ---------------------------------------------------------------------------
# get_partial_ax_tree
# ---------------------------------------------------------------------------


def test_get_partial_ax_tree_no_args_returns_correct_method():
    result = AccessibilityCommands.get_partial_ax_tree()
    assert result['method'] == AccessibilityMethod.GET_PARTIAL_AX_TREE


def test_get_partial_ax_tree_no_args_has_empty_params():
    result = AccessibilityCommands.get_partial_ax_tree()
    assert result['params'] == {}


def test_get_partial_ax_tree_with_node_id():
    result = AccessibilityCommands.get_partial_ax_tree(node_id=42)
    assert result['params']['nodeId'] == 42
    assert 'backendNodeId' not in result['params']
    assert 'objectId' not in result['params']
    assert 'fetchRelatives' not in result['params']


def test_get_partial_ax_tree_with_backend_node_id():
    result = AccessibilityCommands.get_partial_ax_tree(backend_node_id=99)
    assert result['params']['backendNodeId'] == 99
    assert 'nodeId' not in result['params']


def test_get_partial_ax_tree_with_object_id():
    result = AccessibilityCommands.get_partial_ax_tree(object_id='remote-obj-1')
    assert result['params']['objectId'] == 'remote-obj-1'
    assert 'nodeId' not in result['params']


def test_get_partial_ax_tree_with_fetch_relatives_true():
    result = AccessibilityCommands.get_partial_ax_tree(fetch_relatives=True)
    assert result['params']['fetchRelatives'] is True


def test_get_partial_ax_tree_with_fetch_relatives_false():
    result = AccessibilityCommands.get_partial_ax_tree(fetch_relatives=False)
    assert result['params']['fetchRelatives'] is False


def test_get_partial_ax_tree_with_all_params():
    result = AccessibilityCommands.get_partial_ax_tree(
        node_id=1,
        backend_node_id=2,
        object_id='obj-abc',
        fetch_relatives=True,
    )
    assert result['params']['nodeId'] == 1
    assert result['params']['backendNodeId'] == 2
    assert result['params']['objectId'] == 'obj-abc'
    assert result['params']['fetchRelatives'] is True


def test_get_partial_ax_tree_none_params_excluded():
    result = AccessibilityCommands.get_partial_ax_tree(
        node_id=None,
        backend_node_id=None,
        object_id=None,
        fetch_relatives=None,
    )
    assert 'nodeId' not in result['params']
    assert 'backendNodeId' not in result['params']
    assert 'objectId' not in result['params']
    assert 'fetchRelatives' not in result['params']


# ---------------------------------------------------------------------------
# get_full_ax_tree
# ---------------------------------------------------------------------------


def test_get_full_ax_tree_no_args_returns_correct_method():
    result = AccessibilityCommands.get_full_ax_tree()
    assert result['method'] == AccessibilityMethod.GET_FULL_AX_TREE


def test_get_full_ax_tree_no_args_has_empty_params():
    result = AccessibilityCommands.get_full_ax_tree()
    assert result['params'] == {}


def test_get_full_ax_tree_with_depth():
    result = AccessibilityCommands.get_full_ax_tree(depth=3)
    assert result['params']['depth'] == 3
    assert 'frameId' not in result['params']


def test_get_full_ax_tree_with_frame_id():
    result = AccessibilityCommands.get_full_ax_tree(frame_id='frame-abc')
    assert result['params']['frameId'] == 'frame-abc'
    assert 'depth' not in result['params']


def test_get_full_ax_tree_with_all_params():
    result = AccessibilityCommands.get_full_ax_tree(depth=5, frame_id='frame-xyz')
    assert result['params']['depth'] == 5
    assert result['params']['frameId'] == 'frame-xyz'


def test_get_full_ax_tree_none_params_excluded():
    result = AccessibilityCommands.get_full_ax_tree(depth=None, frame_id=None)
    assert 'depth' not in result['params']
    assert 'frameId' not in result['params']


# ---------------------------------------------------------------------------
# get_root_ax_node
# ---------------------------------------------------------------------------


def test_get_root_ax_node_no_args_returns_correct_method():
    result = AccessibilityCommands.get_root_ax_node()
    assert result['method'] == AccessibilityMethod.GET_ROOT_AX_NODE


def test_get_root_ax_node_no_args_has_empty_params():
    result = AccessibilityCommands.get_root_ax_node()
    assert result['params'] == {}


def test_get_root_ax_node_with_frame_id():
    result = AccessibilityCommands.get_root_ax_node(frame_id='main-frame')
    assert result['params']['frameId'] == 'main-frame'


def test_get_root_ax_node_none_frame_id_excluded():
    result = AccessibilityCommands.get_root_ax_node(frame_id=None)
    assert 'frameId' not in result['params']


# ---------------------------------------------------------------------------
# get_ax_node_and_ancestors
# ---------------------------------------------------------------------------


def test_get_ax_node_and_ancestors_no_args_returns_correct_method():
    result = AccessibilityCommands.get_ax_node_and_ancestors()
    assert result['method'] == AccessibilityMethod.GET_AX_NODE_AND_ANCESTORS


def test_get_ax_node_and_ancestors_no_args_has_empty_params():
    result = AccessibilityCommands.get_ax_node_and_ancestors()
    assert result['params'] == {}


def test_get_ax_node_and_ancestors_with_node_id():
    result = AccessibilityCommands.get_ax_node_and_ancestors(node_id=10)
    assert result['params']['nodeId'] == 10
    assert 'backendNodeId' not in result['params']
    assert 'objectId' not in result['params']


def test_get_ax_node_and_ancestors_with_backend_node_id():
    result = AccessibilityCommands.get_ax_node_and_ancestors(backend_node_id=20)
    assert result['params']['backendNodeId'] == 20
    assert 'nodeId' not in result['params']


def test_get_ax_node_and_ancestors_with_object_id():
    result = AccessibilityCommands.get_ax_node_and_ancestors(object_id='obj-xyz')
    assert result['params']['objectId'] == 'obj-xyz'
    assert 'nodeId' not in result['params']


def test_get_ax_node_and_ancestors_with_all_params():
    result = AccessibilityCommands.get_ax_node_and_ancestors(
        node_id=1, backend_node_id=2, object_id='obj-1'
    )
    assert result['params']['nodeId'] == 1
    assert result['params']['backendNodeId'] == 2
    assert result['params']['objectId'] == 'obj-1'


def test_get_ax_node_and_ancestors_none_params_excluded():
    result = AccessibilityCommands.get_ax_node_and_ancestors(
        node_id=None, backend_node_id=None, object_id=None
    )
    assert 'nodeId' not in result['params']
    assert 'backendNodeId' not in result['params']
    assert 'objectId' not in result['params']


# ---------------------------------------------------------------------------
# get_child_ax_nodes
# ---------------------------------------------------------------------------


def test_get_child_ax_nodes_returns_correct_method():
    result = AccessibilityCommands.get_child_ax_nodes(id='ax-node-1')
    assert result['method'] == AccessibilityMethod.GET_CHILD_AX_NODES


def test_get_child_ax_nodes_sets_id():
    result = AccessibilityCommands.get_child_ax_nodes(id='ax-node-1')
    assert result['params']['id'] == 'ax-node-1'


def test_get_child_ax_nodes_without_frame_id_excludes_key():
    result = AccessibilityCommands.get_child_ax_nodes(id='ax-node-1')
    assert 'frameId' not in result['params']


def test_get_child_ax_nodes_with_frame_id():
    result = AccessibilityCommands.get_child_ax_nodes(id='ax-node-1', frame_id='frame-1')
    assert result['params']['id'] == 'ax-node-1'
    assert result['params']['frameId'] == 'frame-1'


def test_get_child_ax_nodes_none_frame_id_excluded():
    result = AccessibilityCommands.get_child_ax_nodes(id='ax-node-2', frame_id=None)
    assert 'frameId' not in result['params']


# ---------------------------------------------------------------------------
# query_ax_tree
# ---------------------------------------------------------------------------


def test_query_ax_tree_no_args_returns_correct_method():
    result = AccessibilityCommands.query_ax_tree()
    assert result['method'] == AccessibilityMethod.QUERY_AX_TREE


def test_query_ax_tree_no_args_has_empty_params():
    result = AccessibilityCommands.query_ax_tree()
    assert result['params'] == {}


def test_query_ax_tree_with_node_id():
    result = AccessibilityCommands.query_ax_tree(node_id=5)
    assert result['params']['nodeId'] == 5
    assert 'backendNodeId' not in result['params']
    assert 'objectId' not in result['params']


def test_query_ax_tree_with_backend_node_id():
    result = AccessibilityCommands.query_ax_tree(backend_node_id=15)
    assert result['params']['backendNodeId'] == 15


def test_query_ax_tree_with_object_id():
    result = AccessibilityCommands.query_ax_tree(object_id='remote-2')
    assert result['params']['objectId'] == 'remote-2'


def test_query_ax_tree_with_accessible_name():
    result = AccessibilityCommands.query_ax_tree(accessible_name='Submit')
    assert result['params']['accessibleName'] == 'Submit'
    assert 'role' not in result['params']


def test_query_ax_tree_with_role():
    result = AccessibilityCommands.query_ax_tree(role='button')
    assert result['params']['role'] == 'button'
    assert 'accessibleName' not in result['params']


def test_query_ax_tree_with_name_and_role():
    result = AccessibilityCommands.query_ax_tree(accessible_name='Submit', role='button')
    assert result['params']['accessibleName'] == 'Submit'
    assert result['params']['role'] == 'button'


def test_query_ax_tree_with_all_params():
    result = AccessibilityCommands.query_ax_tree(
        node_id=1,
        backend_node_id=2,
        object_id='obj-3',
        accessible_name='Close',
        role='button',
    )
    assert result['params']['nodeId'] == 1
    assert result['params']['backendNodeId'] == 2
    assert result['params']['objectId'] == 'obj-3'
    assert result['params']['accessibleName'] == 'Close'
    assert result['params']['role'] == 'button'


def test_query_ax_tree_none_params_excluded():
    result = AccessibilityCommands.query_ax_tree(
        node_id=None,
        backend_node_id=None,
        object_id=None,
        accessible_name=None,
        role=None,
    )
    assert 'nodeId' not in result['params']
    assert 'backendNodeId' not in result['params']
    assert 'objectId' not in result['params']
    assert 'accessibleName' not in result['params']
    assert 'role' not in result['params']


# ---------------------------------------------------------------------------
# parametric: all commands include expected method string
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    'method, expected',
    [
        (AccessibilityCommands.disable, AccessibilityMethod.DISABLE),
        (AccessibilityCommands.enable, AccessibilityMethod.ENABLE),
    ],
)
def test_no_param_commands_return_correct_method(method, expected):
    result = method()
    assert result['method'] == expected
