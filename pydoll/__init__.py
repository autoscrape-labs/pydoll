"""Pydoll: browser automation over the Chrome DevTools Protocol.

The names exported here are the asynchronous API. ``pydoll.sync`` exports the
same names as blocking equivalents, so a script switches between the two by
changing one import line::

    from pydoll import Chrome  # async: await every call
    from pydoll.sync import Chrome  # sync: plain calls
"""

from pydoll.browser.chromium.chrome import Chrome
from pydoll.browser.chromium.edge import Edge
from pydoll.browser.options import ChromiumOptions
from pydoll.browser.requests.request import Request
from pydoll.browser.requests.response import Response
from pydoll.browser.tab import DownloadHandle, RequestHandle, ResponseHandle, Tab
from pydoll.constants import Key
from pydoll.elements.shadow_root import ShadowRoot
from pydoll.elements.web_element import WebElement
from pydoll.extractor import ExtractionModel, Field
from pydoll.interactions.keyboard import Keyboard
from pydoll.interactions.mouse import Mouse
from pydoll.interactions.scroll import Scroll
from pydoll.protocol.fetch.events import FetchEvent
from pydoll.protocol.network.events import NetworkEvent
from pydoll.protocol.page.events import PageEvent

__all__ = [
    'Chrome',
    'ChromiumOptions',
    'DownloadHandle',
    'Edge',
    'ExtractionModel',
    'FetchEvent',
    'Field',
    'Key',
    'Keyboard',
    'Mouse',
    'NetworkEvent',
    'PageEvent',
    'Request',
    'RequestHandle',
    'Response',
    'ResponseHandle',
    'Scroll',
    'ShadowRoot',
    'Tab',
    'WebElement',
]
