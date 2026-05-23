"""
This module provides HTTP client functionality using the browser's fetch API.
It allows making HTTP requests within the browser context, reusing cookies and headers.
"""

from .bidi.request import BiDiRequest
from .cdp.har_recorder import HarCapture
from .cdp.request import Request
from .response import Response

__all__ = ['BiDiRequest', 'HarCapture', 'Request', 'Response']
