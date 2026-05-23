"""Unit tests for ProxyManager: credential extraction and argument sanitization.

Pure logic over a real ChromiumOptions: assert the returned (private, credentials)
tuple and the resulting (sanitized) arguments, never the parsing steps.
"""

from __future__ import annotations

from pydoll.browser.managers import ProxyManager
from pydoll.browser.chromium.options import ChromiumOptions


def _manager_with_args(*args) -> tuple[ProxyManager, ChromiumOptions]:
    options = ChromiumOptions()
    for arg in args:
        options.add_argument(arg)
    return ProxyManager(options), options


def test_no_proxy_returns_no_credentials():
    manager, _ = _manager_with_args('--headless')
    assert manager.get_proxy_credentials() == (False, (None, None))


def test_proxy_without_credentials_is_left_untouched():
    manager, options = _manager_with_args('--proxy-server=http://host:8080')
    private, credentials = manager.get_proxy_credentials()
    assert private is False
    assert credentials == (None, None)
    assert '--proxy-server=http://host:8080' in options.arguments


def test_proxy_with_scheme_credentials_extracted_and_sanitized():
    manager, options = _manager_with_args('--proxy-server=http://user:pass@host:8080')
    private, credentials = manager.get_proxy_credentials()
    assert private is True
    assert credentials == ('user', 'pass')
    assert '--proxy-server=http://host:8080' in options.arguments
    assert 'user:pass' not in ' '.join(options.arguments)


def test_proxy_without_scheme_credentials_extracted_and_sanitized():
    manager, options = _manager_with_args('--proxy-server=user:pass@host:8080')
    private, credentials = manager.get_proxy_credentials()
    assert private is True
    assert credentials == ('user', 'pass')
    assert '--proxy-server=host:8080' in options.arguments


def test_password_containing_colon_is_preserved():
    manager, _ = _manager_with_args('--proxy-server=http://user:p:a:ss@host:8080')
    private, credentials = manager.get_proxy_credentials()
    assert private is True
    assert credentials == ('user', 'p:a:ss')
