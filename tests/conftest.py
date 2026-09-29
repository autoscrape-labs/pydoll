"""Shared pytest fixtures for all tests."""

import pytest

from tests.browser_options import ci_options


@pytest.fixture
def ci_chrome_options():
    """Fresh CI options for tests that need a browser of their own."""
    return ci_options()
