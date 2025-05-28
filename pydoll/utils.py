import base64
import logging

import aiohttp

from pydoll import exceptions

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
        raise exceptions.NetworkError(f'Failed to get browser ws address: {e}')

    except KeyError as e:
        raise exceptions.InvalidResponse(f'Failed to get browser ws address: {e}')
