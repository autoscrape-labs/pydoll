"""Synchronous Playwright-compatible API backed by pydoll.

Swap ``from playwright.sync_api import sync_playwright`` for
``from pydoll.playwright.sync_api import sync_playwright`` and keep the rest of
the script. Generated from the async layer by ``scripts/generate_sync_api.py``.
"""

from pydoll.playwright._errors import Error, TargetClosedError, TimeoutError
from pydoll.playwright._locator import FilePayload
from pydoll.playwright.sync_api._generated import (
    APIResponse,
    Browser,
    BrowserContext,
    BrowserType,
    ConsoleMessage,
    Dialog,
    Download,
    ElementHandle,
    EventInfo,
    FileChooser,
    Frame,
    FrameLocator,
    JSHandle,
    Keyboard,
    Locator,
    Mouse,
    Page,
    Playwright,
    PlaywrightContextManager,
    Request,
    Response,
    Route,
    Selectors,
    Touchscreen,
    sync_playwright,
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
    'sync_playwright',
]
