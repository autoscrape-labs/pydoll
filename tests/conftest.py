"""Shared pytest fixtures for all tests (CDP + BiDi, unit + integration)."""

from pathlib import Path

import pytest

from pydoll.browser.chromium.options import ChromiumOptions
from pydoll.browser.firefox.options import FirefoxOptions

PAGES_DIR = Path(__file__).parent / 'pages'


@pytest.fixture
def ci_chrome_options():
    """Chrome options optimized for CI environments."""
    options = ChromiumOptions()
    options.headless = True
    options.start_timeout = 60  # Increased timeout for CI

    # CI-specific arguments - essentials only
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-background-timer-throttling')
    options.add_argument('--disable-backgrounding-occluded-windows')
    options.add_argument('--disable-renderer-backgrounding')
    options.add_argument('--disable-default-apps')

    # Memory optimization
    options.add_argument('--memory-pressure-off')
    options.add_argument('--max_old_space_size=4096')

    return options


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
