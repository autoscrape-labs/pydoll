import base64
import logging
import os
import re

import aiohttp

from pydoll.exceptions import InvalidBrowserPath, InvalidResponse, NetworkError

logger = logging.getLogger(__name__)


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
