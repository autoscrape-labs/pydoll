"""Playwright-compatible API for pydoll.

Only the browser automation surface is covered: Playwright, BrowserType,
Browser, BrowserContext, Page, Frame, Locator, ElementHandle, Keyboard,
Mouse, network routing, dialogs and downloads. Test-runner features (expect
assertions, fixtures, tracing) are out of scope.
"""

from pydoll.playwright._errors import Error, TargetClosedError, TimeoutError

__all__ = ['Error', 'TargetClosedError', 'TimeoutError']
