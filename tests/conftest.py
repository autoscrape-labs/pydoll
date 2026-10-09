"""Shared pytest fixtures for all tests (CDP + BiDi, unit + integration)."""

from pathlib import Path

import pytest

from pydoll.browser.firefox.options import FirefoxOptions
from tests.browser_options import ci_options

PAGES_DIR = Path(__file__).parent / 'pages'


@pytest.fixture
def ci_chrome_options():
    """Fresh CI options for tests that need a browser of their own."""
    return ci_options()


@pytest.fixture
def ci_firefox_options():
    """Firefox (WebDriver BiDi) options optimized for CI environments."""
    options = FirefoxOptions()
    options.headless = True
    options.start_timeout = 60
    return options


@pytest.fixture
def pages_dir() -> Path:
    """Absolute path to the shared HTML fixture pages directory."""
    return PAGES_DIR


@pytest.fixture
def page_url():
    """Return a callable mapping a fixture page filename to its file:// URL."""

    def _url(name: str) -> str:
        return f'file://{(PAGES_DIR / name).absolute()}'

    return _url
