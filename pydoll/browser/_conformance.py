"""Static conformance checks (mypy-only): concrete classes satisfy the portable protocols.

This module has no runtime effect. The functions exist purely so mypy verifies that the
concrete CDP and BiDi classes (browser, tab, element, shadow root) implement the portable
protocol surface, keeping the two backends from drifting apart. Check with::

    mypy --follow-imports=silent pydoll/browser/_conformance.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pydoll.browser.chromium.base import Browser
    from pydoll.browser.chromium.tab import Tab
    from pydoll.browser.firefox.base import FirefoxBrowser
    from pydoll.browser.firefox.tab import BiDiTab
    from pydoll.browser.protocols import BrowserProtocol, TabProtocol
    from pydoll.elements.bidi.shadow_root import BiDiShadowRoot
    from pydoll.elements.bidi.web_element import BiDiWebElement
    from pydoll.elements.cdp.shadow_root import ShadowRoot
    from pydoll.elements.cdp.web_element import WebElement
    from pydoll.elements.protocols import ShadowRootProtocol, WebElementProtocol

    def _cdp_tab_conforms(tab: Tab) -> TabProtocol:
        return tab

    def _bidi_tab_conforms(tab: BiDiTab) -> TabProtocol:
        return tab

    def _cdp_browser_conforms(browser: Browser) -> BrowserProtocol:
        return browser

    def _bidi_browser_conforms(browser: FirefoxBrowser) -> BrowserProtocol:
        return browser

    def _cdp_element_conforms(element: WebElement) -> WebElementProtocol:
        return element

    def _bidi_element_conforms(element: BiDiWebElement) -> WebElementProtocol:
        return element

    def _cdp_shadow_root_conforms(root: ShadowRoot) -> ShadowRootProtocol:
        return root

    def _bidi_shadow_root_conforms(root: BiDiShadowRoot) -> ShadowRootProtocol:
        return root
