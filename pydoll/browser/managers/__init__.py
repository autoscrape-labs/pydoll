from pydoll.browser.managers.browser_options_manager import (
    ChromiumOptionsManager,
)
from pydoll.browser.managers.browser_process_manager import (
    BrowserProcessManager,
)

# FirefoxOptionsManager is imported last because its module triggers the
# pydoll.browser.firefox package, which imports FirefoxBrowser, which in turn
# imports BrowserProcessManager and TempDirectoryManager from this package.
# Placing it last ensures those names are already present in the partially-
# initialised module when the circular import resolves.
from pydoll.browser.managers.firefox_options_manager import FirefoxOptionsManager
from pydoll.browser.managers.proxy_manager import ProxyManager
from pydoll.browser.managers.temp_dir_manager import TempDirectoryManager

__all__ = [
    'ChromiumOptionsManager',
    'FirefoxOptionsManager',
    'BrowserProcessManager',
    'ProxyManager',
    'TempDirectoryManager',
]
