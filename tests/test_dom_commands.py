# tests/test_dom_commands.py
import pytest
from unittest.mock import patch
from pydoll.protocol.commands import (
    DomCommands,
    RuntimeCommands,
)
from pydoll.constants import By


@pytest.fixture
def mock_runtime_commands():
    with patch('pydoll.protocol.commands.dom_commands.RuntimeCommands') as mock:
        yield mock


def test_enable_dom_events():
    expected = {'method': 'DOM.enable'}
    result = DomCommands.enable_dom_events()
    assert result == expected, (
        'The enable_dom_events method did not return the expected dictionary.'
    )


def test_disable_dom_events():
    expected = {'method': 'DOM.disable'}
    result = DomCommands.disable_dom_events()
    assert result == expected, (
        'The disable_dom_events method did not return the expected dictionary.'
    )


def test_dom_document():
    expected = {'method': 'DOM.getDocument'}
    result = DomCommands.dom_document()
    assert result == expected, (
        'The dom_document method did not return the expected dictionary.'
    )


def test_scroll_into_view():
    object_id = '12345'
    expected = {
        'method': 'DOM.scrollIntoViewIfNeeded',
        'params': {'objectId': object_id},
    }
    result = DomCommands.scroll_into_view(object_id)
    assert result == expected, (
        'The scroll_into_view method did not return the expected dictionary.'
    )


def test_get_outer_html():
    object_id = 67890
    expected = {
        'method': 'DOM.getOuterHTML',
        'params': {'objectId': object_id},
    }
    result = DomCommands.get_outer_html(object_id)
    assert result == expected, (
        'The get_outer_html method did not return the expected dictionary.'
    )


def test_request_node():
    object_id = 'abcde'
    expected = {'method': 'DOM.requestNode', 'params': {'objectId': object_id}}
    result = DomCommands.request_node(object_id)
    assert result == expected, (
        'The request_node method did not return the expected dictionary.'
    )


def test_describe_node():
    object_id = 'fghij'
    expected = {
        'method': 'DOM.describeNode',
        'params': {'objectId': object_id},
    }
    result = DomCommands.describe_node(object_id)
    assert result == expected, (
        'The describe_node method did not return the expected dictionary.'
    )


def test_box_model():
    object_id = 'klmno'
    expected = {'method': 'DOM.getBoxModel', 'params': {'objectId': object_id}}
    result = DomCommands.box_model(object_id)
    assert result == expected, (
        'The box_model method did not return the expected dictionary.'
    )


def test_upload_files():
    from pathlib import Path

    object_id = 'oiukw'
    backend_node_id = 9527
    single_files = str(Path('/fake/path/file1.txt').absolute())
    multi_files = [
        str(Path('/fake/path/file1.txt').absolute()),
        Path('/fake/path/file2.txt').absolute(),
    ]

    expected = {
        'method': 'DOM.setFileInputFiles',
        'params': {'objectId': object_id, 'files': [single_files]},
    }
    assert (
        DomCommands.upload_files(
            single_files, object_id=object_id, missing_ok=True
        )
        == expected
    ), 'The upload_files method did not return the expected dictionary.'
    assert (
        DomCommands.upload_files(
            Path(single_files), object_id=object_id, missing_ok=True
        )
        == expected
    ), 'The upload_files method did not return the expected dictionary.'

    expected_multi_files = {
        'method': 'DOM.setFileInputFiles',
        'params': {
            'objectId': object_id,
            'files': list(map(str, multi_files)),
        },
    }

    assert (
        DomCommands.upload_files(
            multi_files, object_id=object_id, missing_ok=True
        )
        == expected_multi_files
    ), 'The upload_files method did not return the expected dictionary.'

    expected_with_backend_id = {
        'method': 'DOM.setFileInputFiles',
        'params': {'backendNodeId': backend_node_id, 'files': [single_files]},
    }
    assert (
        DomCommands.upload_files(
            single_files, backend_node_id=backend_node_id, missing_ok=True
        )
        == expected_with_backend_id
    ), 'The upload_files method did not return the expected dictionary.'
    assert (
        DomCommands.upload_files(
            Path(single_files),
            backend_node_id=backend_node_id,
            missing_ok=True,
        )
        == expected_with_backend_id
    ), 'The upload_files method did not return the expected dictionary.'

    expected_multi_files_with_backend_id = {
        'method': 'DOM.setFileInputFiles',
        'params': {
            'backendNodeId': backend_node_id,
            'files': list(map(str, multi_files)),
        },
    }

    assert (
        DomCommands.upload_files(
            multi_files, backend_node_id=backend_node_id, missing_ok=True
        )
        == expected_multi_files_with_backend_id
    ), 'The upload_files method did not return the expected dictionary.'

    with pytest.raises(FileExistsError):
        DomCommands.upload_files(multi_files, object_id=object_id)

    with pytest.raises(ValueError):
        DomCommands.upload_files(multi_files)


def test_get_current_url(mock_runtime_commands):
    expected_command = RuntimeCommands.evaluate_script('window.location.href')
    mock_runtime_commands.evaluate_script.return_value = expected_command
    result = DomCommands.get_current_url()
    mock_runtime_commands.evaluate_script.assert_called_once_with(
        'window.location.href'
    )
    assert result == expected_command, (
        'The get_current_url method did not return the expected command.'
    )


def test_find_element_css(mock_runtime_commands):
    by = By.CSS_SELECTOR
    value = 'test-class'
    expected_selector = 'test-class'
    expected_expression = f'document.querySelector("{expected_selector}");'
    expected_command = {
        'method': 'Runtime.evaluate',
        'params': {
            'expression': expected_expression,
        },
    }
    mock_runtime_commands.evaluate_script.return_value = expected_command
    result = DomCommands.find_element(by, value)
    mock_runtime_commands.evaluate_script.assert_called_once_with(
        expected_expression
    )
    assert result == expected_command, (
        'The find_element method with CSS did not return the expected command.'
    )


def test_find_element_xpath(mock_runtime_commands):
    by = By.XPATH
    value = "//div[@id='test']"
    expected_expression = (
        '\n        var element = document.evaluate(\n'
        '            "//div[@id=\'test\']", document, null,\n'
        '            XPathResult.FIRST_ORDERED_NODE_TYPE, null\n'
        '        ).singleNodeValue;\n'
        '        element;\n    '
    )
    expected_command = {
        'method': 'Runtime.evaluate',
        'params': {
            'expression': expected_expression,
        },
    }
    mock_runtime_commands.evaluate_script.return_value = expected_command
    result = DomCommands.find_element(by, value)
    mock_runtime_commands.evaluate_script.assert_called_once_with(
        expected_expression
    )
    assert result == expected_command, (
        'The find_element method with XPATH did not return the expected command.'
    )


def test_find_element_id(mock_runtime_commands):
    by = By.ID
    value = 'test-id'
    expected_selector = '#test-id'
    expected_expression = f'document.querySelector("{expected_selector}");'
    expected_command = {
        'method': 'Runtime.evaluate',
        'params': {
            'expression': expected_expression,
            'returnByValue': False,
        },
    }
    mock_runtime_commands.evaluate_script.return_value = expected_command
    result = DomCommands.find_element(by, value)
    mock_runtime_commands.evaluate_script.assert_called_once_with(
        expected_expression
    )
    assert result == expected_command, (
        'The find_element method with ID did not return the expected command.'
    )


def test_find_element_class_name(mock_runtime_commands):
    by = By.CLASS_NAME
    value = 'test-class'
    expected_selector = '.test-class'
    expected_expression = f'document.querySelector("{expected_selector}");'
    expected_command = {
        'method': 'Runtime.evaluate',
        'params': {
            'expression': expected_expression,
            'returnByValue': False,
        },
    }
    mock_runtime_commands.evaluate_script.return_value = expected_command
    result = DomCommands.find_element(by, value)
    mock_runtime_commands.evaluate_script.assert_called_once_with(
        expected_expression
    )
    assert result == expected_command, (
        'The find_element method with CLASS_NAME did not return the expected command.'
    )


def test_find_element_relative_css(mock_runtime_commands):
    by = By.CSS_SELECTOR
    value = 'div[id="test"]'
    object_id = '12345'
    expected_expression = (
        '\n        function() {\n'
        '            return this.querySelector("div[id=\\"test\\"]");\n'
        '        }\n    '
    )
    expected_command = {
        'method': 'Runtime.callFunctionOn',
        'params': {
            'functionDeclaration': expected_expression,
            'objectId': object_id,
            'returnByValue': False,
        },
    }
    mock_runtime_commands.call_function_on.return_value = expected_command
    result = DomCommands.find_element(by, value, object_id)
    mock_runtime_commands.call_function_on.assert_called_once_with(
        object_id, expected_expression, return_by_value=False
    )

    assert result == expected_command, (
        'The find_element relative method did not return the expected command.'
    )


def test_find_element_relative_class_name(mock_runtime_commands):
    by = By.CLASS_NAME
    value = 'test-class'
    object_id = '12345'
    expected_selector = '.test-class'
    expected_expression = (
        f'\n        function() {{\n'
        f'            return this.querySelector("'
        f'{expected_selector}");\n'
        f'        }}\n    '
    )
    expected_command = {
        'method': 'Runtime.callFunctionOn',
        'params': {
            'functionDeclaration': expected_expression,
            'objectId': object_id,
            'returnByValue': False,
        },
    }
    mock_runtime_commands.call_function_on.return_value = expected_command
    result = DomCommands.find_element(by, value, object_id)
    mock_runtime_commands.call_function_on.assert_called_once_with(
        object_id, expected_expression, return_by_value=False
    )
    assert result == expected_command, (
        'The find_element relative method did not return the expected command.'
    )


def test_find_element_relative_id(mock_runtime_commands):
    by = By.ID
    value = 'test-id'
    object_id = '12345'
    expected_selector = '#test-id'
    expected_command = {
        'method': 'Runtime.callFunctionOn',
        'params': {
            'functionDeclaration': (
                f'function() {{ return this.querySelector("'
                f'{expected_selector}"); }}'
            ),
            'objectId': object_id,
            'returnByValue': False,
        },
    }
    mock_runtime_commands.call_function_on.return_value = expected_command
    result = DomCommands.find_element(by, value, object_id)
    mock_runtime_commands.call_function_on.assert_called_once_with(
        object_id,
        (
            f'\n        function() {{\n'
            f'            return this.querySelector("'
            f'{expected_selector}");\n'
            f'        }}\n    '
        ),
        return_by_value=False,
    )
    assert result == expected_command, (
        'The find_element relative method did not return the expected command.'
    )


def test_find_element_relative_xpath(mock_runtime_commands):
    by = By.XPATH
    value = '//div[@id="test"]'
    object_id = '12345'
    expected_command = {
        'method': 'Runtime.callFunctionOn',
        'params': {
            'functionDeclaration': (
                '\n        function() {\n'
                '            return document.evaluate(\n'
                '                ".//div[@id=\\"test\\"]", this, null,\n'
                '                XPathResult.FIRST_ORDERED_NODE_TYPE, null\n'
                '            ).singleNodeValue;\n'
                '        }\n    '
            ),
            'objectId': object_id,
            'returnByValue': False,
        },
    }
    mock_runtime_commands.call_function_on.return_value = expected_command
    result = DomCommands.find_element(by, value, object_id)
    mock_runtime_commands.call_function_on.assert_called_once_with(
        object_id,
        (
            '\n        function() {\n'
            '            return document.evaluate(\n'
            '                ".//div[@id=\\"test\\"]", this, null,\n'
            '                XPathResult.FIRST_ORDERED_NODE_TYPE, null\n'
            '            ).singleNodeValue;\n'
            '        }\n    '
        ),
        return_by_value=False,
    )
    assert result == expected_command, (
        'The find_elements relative method did not return the expected command.'
    )


def test_find_elements_class_name(mock_runtime_commands):
    by = By.CLASS_NAME
    value = 'test-class'
    expected_selector = '.test-class'
    expected_expression = f'document.querySelectorAll("{expected_selector}");'
    expected_command = {
        'method': 'Runtime.evaluate',
        'params': {
            'expression': expected_expression,
        },
    }

    mock_runtime_commands.evaluate_script.return_value = expected_command
    result = DomCommands.find_elements(by, value)
    mock_runtime_commands.evaluate_script.assert_called_once_with(
        expected_expression
    )
    assert result == expected_command, (
        'The find_elements method with CLASS_NAME did not return the expected command.'
    )


def test_find_elements_xpath(mock_runtime_commands):
    by = By.XPATH
    value = "//div[@class='test']"
    expected_expression = (
        '\n        var elements = document.evaluate(\n'
        '            "//div[@class=\'test\']", document, null,\n'
        '            XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null\n'
        '        );\n        var results = [];\n'
        '        for (var i = 0; i < elements.snapshotLength; i++) {\n'
        '            results.push(elements.snapshotItem(i));\n'
        '        }\n        results;\n    '
    )
    expected_command = {
        'method': 'Runtime.evaluate',
        'params': {
            'expression': expected_expression,
        },
    }
    mock_runtime_commands.evaluate_script.return_value = expected_command
    result = DomCommands.find_elements(by, value)
    mock_runtime_commands.evaluate_script.assert_called_once_with(
        expected_expression
    )
    assert result == expected_command, (
        'The find_elements method with XPATH did not return the expected command.'
    )


def test_find_elements_id(mock_runtime_commands):
    by = By.ID
    value = 'test-id'
    expected_selector = '#test-id'
    expected_command = {
        'method': 'Runtime.evaluate',
        'params': {
            'expression': f'document.querySelectorAll("{expected_selector}")'
        },
    }
    mock_runtime_commands.evaluate_script.return_value = expected_command
    result = DomCommands.find_elements(by, value)
    mock_runtime_commands.evaluate_script.assert_called_once_with(
        'document.querySelectorAll("#test-id");'
    )
    assert result == expected_command, (
        'The find_elements method with ID did not return the expected command.'
    )


def test_find_elements_css(mock_runtime_commands):
    by = By.CSS_SELECTOR
    value = 'test-class'
    expected_selector = 'test-class'
    expected_expression = f'document.querySelectorAll("{expected_selector}");'
    expected_command = {
        'method': 'Runtime.evaluate',
        'params': {
            'expression': expected_expression,
        },
    }
    mock_runtime_commands.evaluate_script.return_value = expected_command
    result = DomCommands.find_elements(by, value)
    mock_runtime_commands.evaluate_script.assert_called_once_with(
        expected_expression
    )
    assert result == expected_command, (
        'The find_elements method with CSS did not return the expected command.'
    )


def test_find_elements_relative_xpath(mock_runtime_commands):
    by = By.XPATH
    value = '//div[@id="test"]'
    object_id = '12345'
    expected_expression = (
        '\n        function() {\n'
        '            var elements = document.evaluate(\n'
        '                ".//div[@id=\\"test\\"]", this, null,\n'
        '                XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null\n'
        '            );\n'
        '            var results = [];\n'
        '            for (var i = 0; i < elements.snapshotLength; i++) {\n'
        '                results.push(elements.snapshotItem(i));\n'
        '            }\n'
        '            return results;\n'
        '        }\n    '
    )
    expected_command = {
        'method': 'Runtime.callFunctionOn',
        'params': {
            'functionDeclaration': expected_expression,
            'objectId': object_id,
            'returnByValue': False,
        },
    }
    mock_runtime_commands.call_function_on.return_value = expected_command
    result = DomCommands.find_elements(by, value, object_id)
    mock_runtime_commands.call_function_on.assert_called_once_with(
        object_id, expected_expression, return_by_value=False
    )
    assert result == expected_command, (
        'The find_elements relative method did not return the expected command.'
    )


def test_find_elements_relative_css(mock_runtime_commands):
    by = By.CSS_SELECTOR
    value = 'div[id="test"]'
    object_id = '12345'
    expected_expression = (
        '\n        function() {\n'
        '            return this.querySelectorAll("div[id=\\"test\\"]");\n'
        '        }\n    '
    )
    expected_command = {
        'method': 'Runtime.callFunctionOn',
        'params': {
            'functionDeclaration': expected_expression,
            'objectId': object_id,
            'returnByValue': False,
        },
    }
    mock_runtime_commands.call_function_on.return_value = expected_command
    result = DomCommands.find_elements(by, value, object_id)
    mock_runtime_commands.call_function_on.assert_called_once_with(
        object_id, expected_expression, return_by_value=False
    )
    assert result == expected_command, (
        'The find_elements relative method did not return the expected command.'
    )
