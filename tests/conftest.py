"""Shared pytest fixtures for all tests."""

import pytest

from pydoll.browser.options import ChromiumOptions as Options


@pytest.fixture
def ci_chrome_options():
    """Chrome options optimized for CI environments."""
    options = Options()
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

