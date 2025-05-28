from pydoll.protocol.commands import RuntimeCommands


def test_get_properties():
    object_id = '12345'
    expected_command = {
        'method': 'Runtime.getProperties',
        'params': {'objectId': object_id, 'ownProperties': True},
    }
    assert RuntimeCommands.get_properties(object_id) == expected_command


def test_call_function_on():
    object_id = '12345'
    function_declaration = 'function() { return this; }'
    return_by_value = True
    expected_command = {
        'method': 'Runtime.callFunctionOn',
        'params': {
            'objectId': object_id,
            'functionDeclaration': function_declaration,
            'returnByValue': return_by_value,
        },
    }
    assert (
        RuntimeCommands.call_function_on(
            object_id, function_declaration, return_by_value
        )
        == expected_command
    )


def test_evaluate_script():
    expression = '2 + 2'
    expected_command = {
        'method': 'Runtime.evaluate',
        'params': {'expression': expression, 'returnByValue': False},
    }
    assert RuntimeCommands.evaluate_script(expression) == expected_command
