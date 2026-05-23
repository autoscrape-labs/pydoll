"""Static conformance checks (mypy-only): concrete classes satisfy the portable protocols.

This module has no runtime effect. The assignments exist purely so mypy verifies that the
concrete CDP and BiDi tab classes implement the portable protocol surface, keeping the two
backends from drifting apart. Check with::

    mypy --follow-imports=silent pydoll/browser/_conformance.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pydoll.browser.chromium.tab import Tab
    from pydoll.browser.firefox.tab import BiDiTab
    from pydoll.browser.protocols import TabProtocol

    def _cdp_tab_conforms(tab: Tab) -> TabProtocol:
        return tab

    def _bidi_tab_conforms(tab: BiDiTab) -> TabProtocol:
        return tab
