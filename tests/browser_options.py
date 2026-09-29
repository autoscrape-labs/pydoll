"""Browser launch options shared by every test that starts a real Chrome."""

from pydoll.browser.options import ChromiumOptions as Options


def ci_options() -> Options:
    """Chrome options optimized for CI environments.

    A plain function so that fixtures of any scope (per test or per session)
    can build a fresh instance; ChromiumOptions must not be shared between
    browsers because the default arguments are added on construction.
    """
    options = Options()
    options.headless = True
    options.start_timeout = 60

    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-background-timer-throttling')
    options.add_argument('--disable-backgrounding-occluded-windows')
    options.add_argument('--disable-renderer-backgrounding')
    options.add_argument('--disable-default-apps')

    options.add_argument('--memory-pressure-off')
    options.add_argument('--max_old_space_size=4096')

    return options
