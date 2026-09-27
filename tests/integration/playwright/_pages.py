"""Fixture page URLs shared by the Playwright-layer tests (underscore: not collected)."""

from pathlib import Path

PAGES = Path(__file__).parent.parent / 'pages'


def page_url(name: str) -> str:
    """file:// URL of a fixture page under tests/integration/pages."""
    return f'file://{(PAGES / name).absolute()}'
