import base64
import logging
import os
import re
from html import unescape
from html.parser import HTMLParser

import aiohttp

from pydoll.exceptions import InvalidBrowserPath, InvalidResponse, NetworkError

logger = logging.getLogger(__name__)


class TextExtractor(HTMLParser):
    """
    HTML parser for text extraction.

    Extracts visible text content from an HTML string, excluding the contents of
    tags specified in _skip_tags.
    """
    def __init__(self):
        super().__init__()
        self._parts = []
        self._skip = False
        self._skip_tags = {"script", "style", "template"}

    def handle_starttag(self, tag, attrs):
        """
        Marks the parser to skip content inside tags specified in _skip_tags.

        Args:
            tag (str): The tag name.
            attrs (list): A list of (attribute, value) pairs.
        """
        if tag in self._skip_tags:
            self._skip = True

    def handle_endtag(self, tag):
        """
        Marks the parser the end of skip tags.

        Args:
            tag (str): The tag name.
        """
        if tag in self._skip_tags:
            self._skip = False

    def handle_data(self, data):
        """
        Handles text nodes. Adds them to the result unless they are within a skip tag.

        Args:
            data (str): The text data.
        """
        if not self._skip:
            self._parts.append(unescape(data))

    def get_strings(self, strip: bool):
        """
        Yields all collected visible text fragments.

        Args:
            strip (bool): Whether to strip leading/trailing whitespace from each fragment.

        Yields:
            str: Visible text fragments.
        """
        for text in self._parts:
            yield text.strip() if strip else text

    def get_text(self, separator: str, strip: bool) -> str:
        """
        Returns all visible text.

        Args:
            separator (str): String inserted between extracted text fragments.
            strip (bool): Whether to strip whitespace from each fragment.

        Returns:
            str: The visible text.
        """
        return separator.join(self.get_strings(strip=strip))


def extract_text_from_html(html: str, separator: str = '', strip: bool = False) -> str:
    """
    Extracts visible text content from an HTML string.

    Args:
        html (str): The HTML string to extract text from.
        separator (str, optional): String inserted between extracted text fragments. Defaults to ''.
        strip (bool, optional): Whether to strip whitespace from text fragments. Defaults to False.

    Returns:
        str: The extracted visible text.
    """
    parser = TextExtractor()
    parser.feed(html)
    return parser.get_text(separator=separator, strip=strip)


def decode_base64_to_bytes(image: str) -> bytes:
    """
    Decodes a base64 image string to bytes.

    Args:
        image (str): The base64 image string to decode.

    Returns:
        bytes: The decoded image as bytes.
    """
    return base64.b64decode(image.encode('utf-8'))


async def get_browser_ws_address(port: int) -> str:
    """
    Fetches the WebSocket address for the browser instance.

    Returns:
        str: The WebSocket address for the browser.

    Raises:
        NetworkError: If the address cannot be fetched due to network errors
            or missing data.
        InvalidResponse: If the response is not valid JSON.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f'http://localhost:{port}/json/version') as response:
                response.raise_for_status()
                data = await response.json()
                return data['webSocketDebuggerUrl']

    except aiohttp.ClientError as e:
        raise NetworkError(f'Failed to get browser ws address: {e}')

    except KeyError as e:
        raise InvalidResponse(f'Failed to get browser ws address: {e}')


def validate_browser_paths(paths: list[str]) -> str:
    """
    Validates potential browser executable paths and returns the first valid one.

    Checks a list of possible browser binary locations to find an existing,
    executable browser. This is used by browser-specific subclasses to locate
    the browser executable when no explicit binary path is provided.

    Args:
        paths: List of potential file paths to check for the browser executable.
            These should be absolute paths appropriate for the current OS.

    Returns:
        str: The first valid browser executable path found.

    Raises:
        InvalidBrowserPath: If the browser executable is not found at the path.
    """
    for path in paths:
        if os.path.exists(path) and os.access(path, os.X_OK):
            return path
    raise InvalidBrowserPath(f'No valid browser path found in: {paths}')


def clean_script_for_analysis(script: str) -> str:
    """
    Clean JavaScript code by removing comments and string literals.

    This helps avoid false positives when analyzing script structure.

    Args:
        script: JavaScript code to clean.

    Returns:
        str: Cleaned script with comments and strings removed.
    """
    # Remove line comments
    cleaned = re.sub(r'//.*?$', '', script, flags=re.MULTILINE)
    # Remove block comments
    cleaned = re.sub(r'/\*.*?\*/', '', cleaned, flags=re.DOTALL)
    # Remove double quoted strings
    cleaned = re.sub(r'"[^"]*"', '""', cleaned)
    # Remove single quoted strings
    cleaned = re.sub(r"'[^']*'", "''", cleaned)
    # Remove template literals
    cleaned = re.sub(r'`[^`]*`', '``', cleaned)

    return cleaned


def is_script_already_function(script: str) -> bool:
    """
    Check if a JavaScript script is already wrapped in a function.

    Args:
        script: JavaScript code to analyze.

    Returns:
        bool: True if script is already a function, False otherwise.
    """
    cleaned_script = clean_script_for_analysis(script)

    function_pattern = r'^\s*function\s*\([^)]*\)\s*\{'
    arrow_function_pattern = r'^\s*\([^)]*\)\s*=>\s*\{'

    return bool(
        re.match(function_pattern, cleaned_script.strip())
        or re.match(arrow_function_pattern, cleaned_script.strip())
    )


def has_return_outside_function(script: str) -> bool:
    """
    Check if a JavaScript script has return statements outside of functions.

    Args:
        script: JavaScript code to analyze.

    Returns:
        bool: True if script has return outside function, False otherwise.
    """
    cleaned_script = clean_script_for_analysis(script)

    # If already a function, no need to check
    if is_script_already_function(cleaned_script):
        return False

    # Look for 'return' statements
    return_pattern = r'\breturn\b'
    if not re.search(return_pattern, cleaned_script):
        return False

    # Check if return is inside a function by counting braces
    lines = cleaned_script.split('\n')
    brace_count = 0
    in_function = False

    for line in lines:
        # Check for function declarations
        if re.search(r'\bfunction\b', line) or re.search(r'=>', line):
            in_function = True

        # Count braces
        brace_count += line.count('{') - line.count('}')

        # Check for return statement
        if re.search(return_pattern, line):
            if not in_function or brace_count <= 0:
                return True

        # Reset function flag if we're back to top level
        if brace_count <= 0:
            in_function = False

    return False
