"""
This module provides HTTP client functionality using the browser's fetch API.
It allows making HTTP requests within the browser context, reusing cookies and headers.
"""

from .har_recorder import HarCapture
from .request import Request
from .response import Response

__all__ = ['HarCapture', 'Request', 'Response']
