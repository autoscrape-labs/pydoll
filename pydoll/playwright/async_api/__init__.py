"""Playwright-compatible async API backed by pydoll.

Swap ``from playwright.async_api import async_playwright`` for
``from pydoll.playwright.async_api import async_playwright`` and keep the rest
of the script.
"""

from pydoll.playwright._browser import Browser
from pydoll.playwright._browser_context import BrowserContext
from pydoll.playwright._dialog import ConsoleMessage, Dialog, Download, FileChooser
from pydoll.playwright._element_handle import ElementHandle, JSHandle
from pydoll.playwright._errors import Error, TargetClosedError, TimeoutError
from pydoll.playwright._events import EventInfo
from pydoll.playwright._frame import Frame
from pydoll.playwright._input import Keyboard, Mouse, Touchscreen
from pydoll.playwright._locator import FilePayload, FrameLocator, Locator
from pydoll.playwright._network import APIResponse, Request, Response, Route
from pydoll.playwright._page import Page
from pydoll.playwright._playwright import (
    BrowserType,
    Playwright,
    PlaywrightContextManager,
    Selectors,
    async_playwright,
)

__all__ = [
    'APIResponse',
    'Browser',
    'BrowserContext',
    'BrowserType',
    'ConsoleMessage',
    'Dialog',
    'Download',
    'ElementHandle',
    'Error',
    'EventInfo',
    'FileChooser',
    'FilePayload',
    'Frame',
    'FrameLocator',
    'JSHandle',
    'Keyboard',
    'Locator',
    'Mouse',
    'Page',
    'Playwright',
    'PlaywrightContextManager',
    'Request',
    'Response',
    'Route',
    'Selectors',
    'TargetClosedError',
    'TimeoutError',
    'Touchscreen',
    'async_playwright',
]
