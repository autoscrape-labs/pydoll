from pydoll.utils.general import (
    TextExtractor,
    clean_script_for_analysis,
    decode_base64_to_bytes,
    extract_text_from_html,
    get_browser_ws_address,
    has_return_outside_function,
    is_script_already_function,
    normalize_synthetic_xpath,
    validate_browser_paths,
)
from pydoll.utils.socks5_proxy_forwarder import SOCKS5Forwarder

__all__ = [
    'TextExtractor',
    'clean_script_for_analysis',
    'decode_base64_to_bytes',
    'extract_text_from_html',
    'get_browser_ws_address',
    'has_return_outside_function',
    'is_script_already_function',
    'normalize_synthetic_xpath',
    'validate_browser_paths',
    'SOCKS5Forwarder',
]
