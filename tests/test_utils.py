import aiohttp
import pytest
from aioresponses import aioresponses
import tempfile
import os
import sys
from unittest.mock import patch

from pydoll import exceptions
from pydoll.utils import (
    clean_script_for_analysis,
    decode_base64_to_bytes,
    get_browser_ws_address,
    has_return_outside_function,
    is_script_already_function,
    validate_browser_paths,
    extract_text_from_html,
)


class TestUtils:
    """
    Test class for utility functions in the pydoll.utils module.
    Groups tests related to image decoding, browser communication, and path validation.
    """

    def test_decode_image_to_bytes(self):
        """
        Test the decode_base64_to_bytes function.
        Verifies that the function correctly decodes a base64 string
        to its original bytes.
        """
        base64code = 'aGVsbG8gd29ybGQ='  # 'hello world' in base64
        assert decode_base64_to_bytes(base64code) == b'hello world'

    def test_decode_image_to_bytes_empty_string(self):
        """
        Test decode_base64_to_bytes with empty string.
        Verifies that the function handles empty input correctly.
        """
        assert decode_base64_to_bytes('') == b''

    def test_decode_image_to_bytes_complex_data(self):
        """
        Test decode_base64_to_bytes with more complex base64 data.
        Verifies that the function can handle longer, more complex encoded data.
        """
        # Base64 for "The quick brown fox jumps over the lazy dog"
        base64code = 'VGhlIHF1aWNrIGJyb3duIGZveCBqdW1wcyBvdmVyIHRoZSBsYXp5IGRvZw=='
        expected = b'The quick brown fox jumps over the lazy dog'
        assert decode_base64_to_bytes(base64code) == expected

    @pytest.mark.asyncio
    async def test_successful_response(self):
        """
        Test successful scenario when getting browser WebSocket address.
        Verifies that the function correctly returns the WebSocket URL when
        the API response contains the expected field.
        """
        port = 9222
        expected_url = 'ws://localhost:9222/devtools/browser/abc123'

        with aioresponses() as mocked:
            mocked.get(
                f'http://localhost:{port}/json/version',
                payload={'webSocketDebuggerUrl': expected_url},
            )
            result = await get_browser_ws_address(port)
            assert result == expected_url

    @pytest.mark.asyncio
    async def test_network_error(self):
        """
        Test behavior when a network error occurs.
        Verifies that the function raises the appropriate NetworkError exception
        when there's a communication failure with the browser.
        """
        port = 9222

        with pytest.raises(exceptions.NetworkError):
            with aioresponses() as mocked:
                mocked.get(
                    f'http://localhost:{port}/json/version',
                    exception=aiohttp.ClientError,
                )
                await get_browser_ws_address(port)

    @pytest.mark.asyncio
    async def test_missing_websocket_url(self):
        """
        Test behavior when API response doesn't contain WebSocket URL.
        Verifies that the function raises InvalidResponse exception when the
        'webSocketDebuggerUrl' field is missing from the response.
        """
        port = 9222

        with aioresponses() as mocked:
            mocked.get(
                f'http://localhost:{port}/json/version',
                payload={'someOtherKey': 'value'},
            )
            with pytest.raises(exceptions.InvalidResponse):
                await get_browser_ws_address(port)

    @pytest.mark.asyncio
    async def test_http_error_status(self):
        """
        Test behavior when HTTP request returns an error status.
        Verifies that the function raises NetworkError when the server
        returns an HTTP error status code.
        """
        port = 9222

        with pytest.raises(exceptions.NetworkError):
            with aioresponses() as mocked:
                mocked.get(
                    f'http://localhost:{port}/json/version',
                    status=404
                )
                await get_browser_ws_address(port)

    @pytest.mark.asyncio
    async def test_custom_port(self):
        """
        Test get_browser_ws_address with a custom port.
        Verifies that the function works correctly with non-default ports.
        """
        port = 9333
        expected_url = 'ws://localhost:9333/devtools/browser/xyz789'

        with aioresponses() as mocked:
            mocked.get(
                f'http://localhost:{port}/json/version',
                payload={'webSocketDebuggerUrl': expected_url},
            )
            result = await get_browser_ws_address(port)
            assert result == expected_url

    def test_validate_browser_paths_success(self):
        """
        Test validate_browser_paths with valid executable path.
        Verifies that the function returns the first valid path found.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a temporary executable file
            valid_path = os.path.join(temp_dir, 'browser')
            with open(valid_path, 'w') as f:
                f.write('#!/bin/bash\necho "browser"')
            os.chmod(valid_path, 0o755)  # Make it executable
            
            invalid_path = '/nonexistent/browser'
            paths = [invalid_path, valid_path]
            
            result = validate_browser_paths(paths)
            assert result == valid_path

    def test_validate_browser_paths_first_valid_wins(self):
        """
        Test that validate_browser_paths returns the first valid path.
        Verifies that when multiple valid paths exist, the first one is returned.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create two valid executable files
            first_valid = os.path.join(temp_dir, 'browser1')
            second_valid = os.path.join(temp_dir, 'browser2')
            
            for path in [first_valid, second_valid]:
                with open(path, 'w') as f:
                    f.write('#!/bin/bash\necho "browser"')
                os.chmod(path, 0o755)
            
            paths = [first_valid, second_valid]
            result = validate_browser_paths(paths)
            assert result == first_valid

    def test_validate_browser_paths_no_valid_paths(self):
        """
        Test validate_browser_paths when no valid paths exist.
        Verifies that InvalidBrowserPath exception is raised when no
        executable browser is found in the provided paths.
        """
        invalid_paths = [
            '/nonexistent/browser1',
            '/nonexistent/browser2',
            '/nonexistent/browser3'
        ]
        
        with pytest.raises(exceptions.InvalidBrowserPath) as exc_info:
            validate_browser_paths(invalid_paths)
        
        assert 'No valid browser path found in:' in str(exc_info.value)

    @pytest.mark.skipif(sys.platform.startswith('win'), reason='No executable bit on NTFS on Windows')
    def test_validate_browser_paths_file_exists_but_not_executable(self):
        """
        Test validate_browser_paths with non-executable file.
        Verifies that a file that exists but is not executable is not considered valid.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a file that exists but is not executable
            non_executable = os.path.join(temp_dir, 'browser')
            with open(non_executable, 'w') as f:
                f.write('not executable')
            # Don't set executable permissions

            with pytest.raises(exceptions.InvalidBrowserPath):
                validate_browser_paths([non_executable])

    def test_validate_browser_paths_empty_list(self):
        """
        Test validate_browser_paths with empty path list.
        Verifies that InvalidBrowserPath exception is raised when
        an empty list of paths is provided.
        """
        with pytest.raises(exceptions.InvalidBrowserPath):
            validate_browser_paths([])

    def test_validate_browser_paths_mixed_valid_invalid(self):
        """
        Test validate_browser_paths with mix of valid and invalid paths.
        Verifies that the function skips invalid paths and returns the first valid one.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create one valid executable
            valid_path = os.path.join(temp_dir, 'browser')
            with open(valid_path, 'w') as f:
                f.write('#!/bin/bash\necho "browser"')
            os.chmod(valid_path, 0o755)
            
            # Mix valid and invalid paths
            paths = [
                '/nonexistent/browser1',
                '/nonexistent/browser2',
                valid_path,
                '/nonexistent/browser3'
            ]
            
            result = validate_browser_paths(paths)
            assert result == valid_path


class TestDecodeBase64ToBytes:
    """Test decode_base64_to_bytes function."""

    def test_decode_base64_to_bytes_valid_input(self):
        """Test decoding valid base64 string."""
        base64_string = 'SGVsbG8gV29ybGQ='  # "Hello World" in base64
        result = decode_base64_to_bytes(base64_string)
        assert result == b'Hello World'

    def test_decode_base64_to_bytes_empty_string(self):
        """Test decoding empty base64 string."""
        result = decode_base64_to_bytes('')
        assert result == b''


class TestValidateBrowserPaths:
    """Test validate_browser_paths function."""

    def test_validate_browser_paths_valid_path(self, tmp_path):
        """Test with valid executable path."""
        # Create a temporary executable file
        executable = tmp_path / "browser"
        executable.write_text("#!/bin/bash\necho 'browser'")
        executable.chmod(0o755)
        
        result = validate_browser_paths([str(executable)])
        assert result == str(executable)

    def test_validate_browser_paths_invalid_paths(self):
        """Test with invalid paths."""
        from pydoll.exceptions import InvalidBrowserPath
        
        with pytest.raises(InvalidBrowserPath):
            validate_browser_paths(['/nonexistent/path', '/another/invalid/path'])


class TestScriptAnalysisFunctions:
    """Test JavaScript script analysis functions."""

    def test_clean_script_for_analysis_removes_comments(self):
        """Test that comments are removed from script."""
        script = '''
        // This is a line comment
        var x = 5;
        /* This is a block comment */
        return x;
        '''
        
        result = clean_script_for_analysis(script)
        
        assert '// This is a line comment' not in result
        assert '/* This is a block comment */' not in result
        assert 'var x = 5;' in result
        assert 'return x;' in result

    def test_clean_script_for_analysis_removes_strings(self):
        """Test that string literals are removed from script."""
        script = '''
        var message = "This string contains return statement";
        var another = 'Another string with return';
        var template = `Template literal with return`;
        return "actual return";
        '''
        
        result = clean_script_for_analysis(script)
        
        assert 'This string contains return statement' not in result
        assert 'Another string with return' not in result
        assert 'Template literal with return' not in result
        assert 'return ""' in result  # String replaced with empty quotes

    def test_is_script_already_function_regular_function(self):
        """Test detection of regular function declaration."""
        script = 'function() { console.log("test"); }'
        assert is_script_already_function(script) is True

    def test_is_script_already_function_arrow_function(self):
        """Test detection of arrow function."""
        script = '() => { console.log("test"); }'
        assert is_script_already_function(script) is True

    def test_is_script_already_function_with_parameters(self):
        """Test detection of function with parameters."""
        script = 'function(a, b) { return a + b; }'
        assert is_script_already_function(script) is True

    def test_is_script_already_function_not_function(self):
        """Test detection when script is not a function."""
        script = 'console.log("test"); return "value";'
        assert is_script_already_function(script) is False

    def test_is_script_already_function_with_whitespace(self):
        """Test detection with leading/trailing whitespace."""
        script = '   function() { test(); }   '
        assert is_script_already_function(script) is True

    def test_has_return_outside_function_simple_return(self):
        """Test detection of simple return statement."""
        script = 'return document.title;'
        assert has_return_outside_function(script) is True

    def test_has_return_outside_function_no_return(self):
        """Test when script has no return statement."""
        script = 'console.log("test"); var x = 5;'
        assert has_return_outside_function(script) is False

    def test_has_return_outside_function_return_inside_function(self):
        """Test when return is inside a function."""
        script = '''
        function getTitle() {
            return document.title;
        }
        getTitle();
        '''
        assert has_return_outside_function(script) is False

    def test_has_return_outside_function_mixed_returns(self):
        """Test with both inside and outside returns."""
        script = '''
        function inner() {
            return "inner";
        }
        return "outer";
        '''
        assert has_return_outside_function(script) is True

    def test_has_return_outside_function_already_function(self):
        """Test when script is already a function."""
        script = 'function() { return "test"; }'
        assert has_return_outside_function(script) is False

    def test_has_return_outside_function_with_comments(self):
        """Test with comments containing 'return'."""
        script = '''
        // This comment has return in it
        var message = "This string has return in it";
        /* This block comment also has return */
        return "actual return";
        '''
        assert has_return_outside_function(script) is True

    def test_has_return_outside_function_nested_braces(self):
        """Test with nested braces and complex structure."""
        script = '''
        if (true) {
            var obj = {
                method: function() {
                    return "nested";
                }
            };
        }
        return "outside";
        '''
        assert has_return_outside_function(script) is True

    def test_has_return_outside_function_arrow_function(self):
        """Test with arrow function containing return."""
        script = '''
        var func = () => {
            return "arrow";
        };
        func();
        '''
        assert has_return_outside_function(script) is False

    def test_extract_text_without_strip_without_separator(self):
        html = ('<div>Hello <span> world </span><script>alert(1)</script><style>body { color: red; }</style>'
                '<template>hidden</template></div>')
        result = extract_text_from_html(html)
        assert result == 'Hello  world '

    def test_extract_text_with_strip_without_separator(self):
        html = ('<div>Hello <span> world </span><script>alert(1)</script><style>body { color: red; }</style>'
                '<template>hidden</template></div>')
        result = extract_text_from_html(html, strip=True)
        assert result == 'Helloworld'

    def test_extract_text_without_strip_with_separator(self):
        html = ('<div>Hello <span> world </span><script>alert(1)</script><style>body { color: red; }</style>'
                '<template>hidden</template></div>')
        result = extract_text_from_html(html, separator="/")
        assert result == 'Hello / world '

    def test_extract_text_with_strip_with_separator(self):
        html = ('<div>Hello <span> world </span><script>alert(1)</script><style>body { color: red; }</style>'
                '<template>hidden</template></div>')
        result = extract_text_from_html(html, strip=True, separator="/")
        assert result == 'Hello/world'
