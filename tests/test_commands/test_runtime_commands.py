"""
Tests for RuntimeCommands class.

This module contains comprehensive tests for all RuntimeCommands methods,
verifying that they generate the correct CDP commands with proper parameters.
"""

from pydoll.commands.runtime_commands import RuntimeCommands
from pydoll.protocol.runtime.methods import RuntimeMethod


def test_add_binding_minimal():
    """Test add_binding with minimal parameters."""
    result = RuntimeCommands.add_binding(name='testBinding')
    assert result['method'] == RuntimeMethod.ADD_BINDING
    assert result['params']['name'] == 'testBinding'


def test_add_binding_with_context():
    """Test add_binding with execution context name."""
    result = RuntimeCommands.add_binding(
        name='testBinding',
        execution_context_name='main'
    )
    assert result['method'] == RuntimeMethod.ADD_BINDING
    assert result['params']['name'] == 'testBinding'
    assert result['params']['executionContextName'] == 'main'


def test_await_promise_minimal():
    """Test await_promise with minimal parameters."""
    result = RuntimeCommands.await_promise(promise_object_id='promise123')
    assert result['method'] == RuntimeMethod.AWAIT_PROMISE
    assert result['params']['promiseObjectId'] == 'promise123'


def test_await_promise_with_all_params():
    """Test await_promise with all parameters."""
    result = RuntimeCommands.await_promise(
        promise_object_id='promise123',
        return_by_value=True,
        generate_preview=False
    )
    assert result['method'] == RuntimeMethod.AWAIT_PROMISE
    assert result['params']['promiseObjectId'] == 'promise123'
    assert result['params']['returnByValue'] is True
    assert result['params']['generatePreview'] is False


def test_call_function_on_minimal():
    """Test call_function_on with minimal parameters."""
    result = RuntimeCommands.call_function_on(
        function_declaration='function() { return this.value; }'
    )
    assert result['method'] == RuntimeMethod.CALL_FUNCTION_ON
    assert result['params']['functionDeclaration'] == 'function() { return this.value; }'


def test_call_function_on_with_object_id():
    """Test call_function_on with object ID."""
    result = RuntimeCommands.call_function_on(
        function_declaration='function() { return this.value; }',
        object_id='obj123'
    )
    assert result['method'] == RuntimeMethod.CALL_FUNCTION_ON
    assert result['params']['functionDeclaration'] == 'function() { return this.value; }'
    assert result['params']['objectId'] == 'obj123'


def test_call_function_on_with_all_params():
    """Test call_function_on with all parameters."""
    arguments = [
        {'value': 42},
        {'value': 'test string'}
    ]
    serialization_options = {
        'serialization': 'deep',
        'maxDepth': 5
    }
    result = RuntimeCommands.call_function_on(
        function_declaration='function(a, b) { return a + b; }',
        object_id='obj123',
        arguments=arguments,
        silent=True,
        return_by_value=False,
        generate_preview=True,
        user_gesture=False,
        await_promise=True,
        execution_context_id='ctx456',
        object_group='testGroup',
        throw_on_side_effect=False,
        unique_context_id='unique789',
        serialization_options=serialization_options
    )
    assert result['method'] == RuntimeMethod.CALL_FUNCTION_ON
    assert result['params']['functionDeclaration'] == 'function(a, b) { return a + b; }'
    assert result['params']['objectId'] == 'obj123'
    assert result['params']['arguments'] == arguments
    assert result['params']['silent'] is True
    assert result['params']['returnByValue'] is False
    assert result['params']['generatePreview'] is True
    assert result['params']['userGesture'] is False
    assert result['params']['awaitPromise'] is True
    assert result['params']['executionContextId'] == 'ctx456'
    assert result['params']['objectGroup'] == 'testGroup'
    assert result['params']['throwOnSideEffect'] is False
    assert result['params']['uniqueContextId'] == 'unique789'
    assert result['params']['serializationOptions'] == serialization_options


def test_compile_script_minimal():
    """Test compile_script with minimal parameters."""
    result = RuntimeCommands.compile_script(expression='2 + 2')
    assert result['method'] == RuntimeMethod.COMPILE_SCRIPT
    assert result['params']['expression'] == '2 + 2'


def test_compile_script_with_all_params():
    """Test compile_script with all parameters."""
    result = RuntimeCommands.compile_script(
        expression='function test() { return 42; }',
        source_url='https://example.com/script.js',
        persist_script=True,
        execution_context_id='ctx123'
    )
    assert result['method'] == RuntimeMethod.COMPILE_SCRIPT
    assert result['params']['expression'] == 'function test() { return 42; }'
    assert result['params']['sourceURL'] == 'https://example.com/script.js'
    assert result['params']['persistScript'] is True
    assert result['params']['executionContextId'] == 'ctx123'


def test_disable():
    """Test disable method generates correct command."""
    result = RuntimeCommands.disable()
    assert result['method'] == RuntimeMethod.DISABLE
    assert 'params' not in result


def test_enable():
    """Test enable method generates correct command."""
    result = RuntimeCommands.enable()
    assert result['method'] == RuntimeMethod.ENABLE
    assert 'params' not in result


def test_evaluate_minimal():
    """Test evaluate with minimal parameters."""
    result = RuntimeCommands.evaluate(expression='2 + 2')
    assert result['method'] == RuntimeMethod.EVALUATE
    assert result['params']['expression'] == '2 + 2'


def test_evaluate_with_basic_params():
    """Test evaluate with basic parameters."""
    result = RuntimeCommands.evaluate(
        expression='document.title',
        return_by_value=True,
        silent=False
    )
    assert result['method'] == RuntimeMethod.EVALUATE
    assert result['params']['expression'] == 'document.title'
    assert result['params']['returnByValue'] is True
    assert result['params']['silent'] is False


def test_evaluate_with_all_params():
    """Test evaluate with all parameters."""
    serialization_options = {
        'serialization': 'json',
        'maxDepth': 3
    }
    result = RuntimeCommands.evaluate(
        expression='window.location.href',
        object_group='testGroup',
        include_command_line_api=True,
        silent=False,
        context_id='ctx123',
        return_by_value=False,
        generate_preview=True,
        user_gesture=False,
        await_promise=True,
        throw_on_side_effect=False,
        timeout=5000.0,
        disable_breaks=True,
        repl_mode=False,
        allow_unsafe_eval_blocked_by_csp=False,
        unique_context_id='unique456',
        serialization_options=serialization_options
    )
    assert result['method'] == RuntimeMethod.EVALUATE
    assert result['params']['expression'] == 'window.location.href'
    assert result['params']['objectGroup'] == 'testGroup'
    assert result['params']['includeCommandLineAPI'] is True
    assert result['params']['silent'] is False
    assert result['params']['contextId'] == 'ctx123'
    assert result['params']['returnByValue'] is False
    assert result['params']['generatePreview'] is True
    assert result['params']['userGesture'] is False
    assert result['params']['awaitPromise'] is True
    assert result['params']['throwOnSideEffect'] is False
    assert result['params']['timeout'] == 5000.0
    assert result['params']['disableBreaks'] is True
    assert result['params']['replMode'] is False
    assert result['params']['allowUnsafeEvalBlockedByCSP'] is False
    assert result['params']['uniqueContextId'] == 'unique456'
    assert result['params']['serializationOptions'] == serialization_options


def test_get_properties_minimal():
    """Test get_properties with minimal parameters."""
    result = RuntimeCommands.get_properties(object_id='obj123')
    assert result['method'] == RuntimeMethod.GET_PROPERTIES
    assert result['params']['objectId'] == 'obj123'


def test_get_properties_with_all_params():
    """Test get_properties with all parameters."""
    result = RuntimeCommands.get_properties(
        object_id='obj123',
        own_properties=True,
        accessor_properties_only=False,
        generate_preview=True,
        non_indexed_properties_only=False
    )
    assert result['method'] == RuntimeMethod.GET_PROPERTIES
    assert result['params']['objectId'] == 'obj123'
    assert result['params']['ownProperties'] is True
    assert result['params']['accessorPropertiesOnly'] is False
    assert result['params']['generatePreview'] is True
    assert result['params']['nonIndexedPropertiesOnly'] is False


def test_global_lexical_scope_names_minimal():
    """Test global_lexical_scope_names with minimal parameters."""
    result = RuntimeCommands.global_lexical_scope_names()
    assert result['method'] == RuntimeMethod.GLOBAL_LEXICAL_SCOPE_NAMES
    assert result['params'] == {}


def test_global_lexical_scope_names_with_context():
    """Test global_lexical_scope_names with execution context ID."""
    result = RuntimeCommands.global_lexical_scope_names(
        execution_context_id='ctx123'
    )
    assert result['method'] == RuntimeMethod.GLOBAL_LEXICAL_SCOPE_NAMES
    assert result['params']['executionContextId'] == 'ctx123'


def test_query_objects_minimal():
    """Test query_objects with minimal parameters."""
    result = RuntimeCommands.query_objects(prototype_object_id='proto123')
    assert result['method'] == RuntimeMethod.QUERY_OBJECTS
    assert result['params']['prototypeObjectId'] == 'proto123'


def test_query_objects_with_group():
    """Test query_objects with object group."""
    result = RuntimeCommands.query_objects(
        prototype_object_id='proto123',
        object_group='testGroup'
    )
    assert result['method'] == RuntimeMethod.QUERY_OBJECTS
    assert result['params']['prototypeObjectId'] == 'proto123'
    assert result['params']['objectGroup'] == 'testGroup'


def test_release_object():
    """Test release_object method."""
    result = RuntimeCommands.release_object(object_id='obj123')
    assert result['method'] == RuntimeMethod.RELEASE_OBJECT
    assert result['params']['objectId'] == 'obj123'


def test_release_object_group():
    """Test release_object_group method."""
    result = RuntimeCommands.release_object_group(object_group='testGroup')
    assert result['method'] == RuntimeMethod.RELEASE_OBJECT_GROUP
    assert result['params']['objectGroup'] == 'testGroup'


def test_remove_binding():
    """Test remove_binding method."""
    result = RuntimeCommands.remove_binding(name='testBinding')
    assert result['method'] == RuntimeMethod.REMOVE_BINDING
    assert result['params']['name'] == 'testBinding'


def test_run_script_minimal():
    """Test run_script with minimal parameters."""
    result = RuntimeCommands.run_script(script_id='script123')
    assert result['method'] == RuntimeMethod.RUN_SCRIPT
    assert result['params']['scriptId'] == 'script123'


def test_run_script_with_all_params():
    """Test run_script with all parameters."""
    result = RuntimeCommands.run_script(
        script_id='script123',
        execution_context_id='ctx456',
        object_group='testGroup',
        silent=True,
        include_command_line_api=False,
        return_by_value=True,
        generate_preview=False,
        await_promise=True
    )
    assert result['method'] == RuntimeMethod.RUN_SCRIPT
    assert result['params']['scriptId'] == 'script123'
    assert result['params']['executionContextId'] == 'ctx456'
    assert result['params']['objectGroup'] == 'testGroup'
    assert result['params']['silent'] is True
    assert result['params']['includeCommandLineAPI'] is False
    assert result['params']['returnByValue'] is True
    assert result['params']['generatePreview'] is False
    assert result['params']['awaitPromise'] is True


def test_set_async_call_stack_depth():
    """Test set_async_call_stack_depth method."""
    result = RuntimeCommands.set_async_call_stack_depth(max_depth=10)
    assert result['method'] == RuntimeMethod.SET_ASYNC_CALL_STACK_DEPTH
    assert result['params']['maxDepth'] == 10


def test_set_custom_object_formatter_enabled():
    """Test set_custom_object_formatter_enabled method."""
    result = RuntimeCommands.set_custom_object_formatter_enabled(enabled=True)
    assert result['method'] == RuntimeMethod.SET_CUSTOM_OBJECT_FORMATTER_ENABLED
    assert result['params']['enabled'] is True


def test_set_max_call_stack_size_to_capture():
    """Test set_max_call_stack_size_to_capture method."""
    result = RuntimeCommands.set_max_call_stack_size_to_capture(size=100)
    assert result['method'] == RuntimeMethod.SET_MAX_CALL_STACK_SIZE_TO_CAPTURE
    assert result['params']['size'] == 100


def test_evaluate_simple_expression():
    """Test evaluate with a simple mathematical expression."""
    result = RuntimeCommands.evaluate(expression='Math.PI * 2')
    assert result['method'] == RuntimeMethod.EVALUATE
    assert result['params']['expression'] == 'Math.PI * 2'


def test_call_function_on_with_arguments():
    """Test call_function_on with function arguments."""
    arguments = [
        {'value': 10},
        {'value': 20}
    ]
    result = RuntimeCommands.call_function_on(
        function_declaration='function(a, b) { return a * b; }',
        object_id='obj123',
        arguments=arguments,
        return_by_value=True
    )
    assert result['method'] == RuntimeMethod.CALL_FUNCTION_ON
    assert result['params']['functionDeclaration'] == 'function(a, b) { return a * b; }'
    assert result['params']['objectId'] == 'obj123'
    assert result['params']['arguments'] == arguments
    assert result['params']['returnByValue'] is True


def test_get_properties_own_only():
    """Test get_properties with own properties only."""
    result = RuntimeCommands.get_properties(
        object_id='obj123',
        own_properties=True,
        generate_preview=False
    )
    assert result['method'] == RuntimeMethod.GET_PROPERTIES
    assert result['params']['objectId'] == 'obj123'
    assert result['params']['ownProperties'] is True
    assert result['params']['generatePreview'] is False


def test_evaluate_with_context():
    """Test evaluate with specific execution context."""
    result = RuntimeCommands.evaluate(
        expression='this.document.title',
        context_id='ctx123',
        include_command_line_api=True
    )
    assert result['method'] == RuntimeMethod.EVALUATE
    assert result['params']['expression'] == 'this.document.title'
    assert result['params']['contextId'] == 'ctx123'
    assert result['params']['includeCommandLineAPI'] is True


def test_compile_script_with_source_url():
    """Test compile_script with source URL."""
    result = RuntimeCommands.compile_script(
        expression='const x = 42; console.log(x);',
        source_url='test://script.js',
        persist_script=False
    )
    assert result['method'] == RuntimeMethod.COMPILE_SCRIPT
    assert result['params']['expression'] == 'const x = 42; console.log(x);'
    assert result['params']['sourceURL'] == 'test://script.js'
    assert result['params']['persistScript'] is False
