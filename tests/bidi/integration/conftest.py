"""Fixtures for BiDi/Firefox integration tests (real headless Firefox).

To keep the suite fast, one headless Firefox is shared per test module and each
test gets a fresh browser context (isolated cookies/storage), instead of
reopening the browser for every test. Tests in modules that use these fixtures
run on a module-scoped event loop (``@pytest.mark.asyncio(loop_scope='module')``).
"""

from __future__ import annotations

from contextlib import suppress

import pytest_asyncio

from pydoll.browser import Firefox
from pydoll.browser.firefox.options import FirefoxOptions


def _firefox_options() -> FirefoxOptions:
    """Headless Firefox options tuned for CI (matches ci_firefox_options)."""
    options = FirefoxOptions()
    options.headless = True
    options.start_timeout = 60
    return options


@pytest_asyncio.fixture(scope='module', loop_scope='module')
async def firefox_browser():
    """One headless Firefox shared by every test in a module."""
    async with Firefox(options=_firefox_options()) as browser:
        await browser.start()
        yield browser


@pytest_asyncio.fixture(loop_scope='module')
async def tab(firefox_browser):
    """A fresh tab in its own browser context (isolated per test).

    Reuses the shared Firefox process; only a lightweight context + tab are
    created and torn down per test.
    """
    context_id = await firefox_browser.create_browser_context()
    new_tab = await firefox_browser.new_tab(browser_context_id=context_id)
    try:
        yield new_tab
    finally:
        with suppress(Exception):
            await firefox_browser.delete_browser_context(context_id)
