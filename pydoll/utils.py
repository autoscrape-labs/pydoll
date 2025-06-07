import base64
import logging
import os
from typing import List

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
        ValueError: If the address cannot be fetched due to network errors
        or missing data.
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


def validate_browser_paths(paths: List[str]) -> str:
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
