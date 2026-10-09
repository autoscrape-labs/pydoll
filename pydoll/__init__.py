"""Pydoll: browser automation over the Chrome DevTools Protocol.

The names exported here are the asynchronous API. ``pydoll.sync`` exports the
same names as blocking equivalents, so a script switches between the two by
changing one import line::

    from pydoll import Chrome  # async: await every call
    from pydoll.sync import Chrome  # sync: plain calls
"""

from pydoll.browser.chromium.chrome import Chrome
from pydoll.browser.chromium.edge import Edge
from pydoll.browser.chromium.options import ChromiumOptions
from pydoll.browser.chromium.tab import DownloadHandle, RequestHandle, ResponseHandle, Tab
from pydoll.browser.requests.cdp.request import Request
from pydoll.browser.requests.response import Response
from pydoll.constants import Key
from pydoll.elements.cdp.shadow_root import ShadowRoot
from pydoll.elements.cdp.web_element import WebElement
from pydoll.extractor import ExtractionModel, Field
from pydoll.interactions.keyboard import Keyboard
from pydoll.interactions.mouse import Mouse
from pydoll.interactions.scroll import Scroll
from pydoll.protocol.cdp.fetch.events import FetchEvent
from pydoll.protocol.cdp.network.events import NetworkEvent
from pydoll.protocol.cdp.page.events import PageEvent

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
