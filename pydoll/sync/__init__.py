"""Synchronous API for pydoll.

The classes here mirror the asynchronous ones one to one: every ``await``-able
method blocks instead. They are generated from the async implementation by
``scripts/generate_sync_api.py``; see ``pydoll/sync/_runtime.py`` for how the
calls reach the event loop.

Example::

    from pydoll.sync import Chrome

    with Chrome() as browser:
        tab = browser.start()
        tab.go_to('https://example.com')
        print(tab.title)
"""

from pydoll.sync._generated import (
    Chrome,
    DownloadHandle,
    Edge,
    Keyboard,
    Mouse,
    Request,
    Response,
    Scroll,
    ShadowRoot,
    Tab,
    WebElement,
)
from pydoll.sync._runtime import SyncError

__all__ = [
    'Chrome',
    'DownloadHandle',
    'Edge',
    'Keyboard',
    'Mouse',
    'Request',
    'Response',
    'Scroll',
    'ShadowRoot',
    'SyncError',
    'Tab',
    'WebElement',
]
