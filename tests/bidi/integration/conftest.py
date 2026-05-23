"""Fixtures for BiDi/Firefox integration tests (real headless Firefox)."""

from __future__ import annotations

import pytest_asyncio

from pydoll.browser import Firefox


@pytest_asyncio.fixture
async def tab(ci_firefox_options):
    """A started headless Firefox tab over WebDriver BiDi.

    ``ci_firefox_options`` comes from the root conftest so every BiDi integration
    test opens Firefox the same way.
    """
    async with Firefox(options=ci_firefox_options) as browser:
        yield await browser.start()
