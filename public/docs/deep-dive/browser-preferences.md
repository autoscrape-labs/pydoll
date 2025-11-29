# Deep Dive: Custom Browser Preferences in Pydoll

## Overview

The `browser_preferences` feature (PR #204) enables direct, fine-grained control over Chromium browser settings via the `ChromiumOptions` API. This is essential for advanced automation, testing, and scraping scenarios where default browser behavior must be customized.

## How It Works

- `ChromiumOptions.browser_preferences` is a dictionary that maps directly to Chromium's internal preferences structure.
- Preferences are merged: setting new keys updates only those keys, preserving others.
- Helper methods (`set_default_download_directory`, `set_accept_languages`, etc.) are provided for common scenarios.
- Preferences are applied before browser launch, ensuring all settings take effect from the start of the session.
- Validation ensures only dictionaries are accepted; invalid structures raise clear errors.

## Example

```python
options = ChromiumOptions()
options.browser_preferences = {
    'download': {'default_directory': '/tmp', 'prompt_for_download': False},
    'intl': {'accept_languages': 'en-US,en'},
    'profile': {'default_content_setting_values': {'notifications': 2}}
}
```

## Advanced Usage

- **Merging:** Multiple assignments merge keys, so you can incrementally build your preferences.
- **Validation:** If you pass a non-dict or use the reserved 'prefs' key, an error is raised.
- **Internals:** Preferences are set via a recursive setter that creates nested dictionaries as needed.
- **Integration:** Used by the browser process manager to initialize the user data directory with your custom settings.

## Best Practices

- Use helper methods for common patterns; set `browser_preferences` directly for advanced needs.
- Check Chromium documentation for available preferences: https://chromium.googlesource.com/chromium/src/+/4aaa9f29d8fe5eac55b8632fa8fcb05a68d9005b/chrome/common/pref_names.cc
- Avoid setting experimental or undocumented preferences unless you know their effects.

## References

- See `pydoll/browser/options.py` for implementation details.
- See tests in `tests/test_browser/test_browser_chrome.py` for usage examples.

## Related: Page Load State

In addition to low-level preferences, you can control when Pydoll considers a page "loaded" by setting `ChromiumOptions.page_load_state`:

- Default: `PageLoadState.COMPLETE` (waits until `document.readyState == 'complete'`)
- Optional: `PageLoadState.INTERACTIVE` (ends earlier when the DOM is interactive)

```python
from pydoll.browser.options import ChromiumOptions
from pydoll.constants import PageLoadState

options = ChromiumOptions()
options.page_load_state = PageLoadState.INTERACTIVE
```

## Parallel Execution Control

Pydoll supports running multiple coroutines in parallel with the `browser.run_in_parallel()` method. You can control the maximum number of concurrent tasks using the `max_parallel_tasks` option:

```python
from pydoll.browser.options import ChromiumOptions

options = ChromiumOptions()
options.max_parallel_tasks = 5  # Allow up to 5 concurrent tasks (default: 2)
```

**Key Points:**

- Default value: `2` concurrent tasks
- Must be greater than `0` (raises `ValueError` otherwise)
- Controls semaphore-based concurrency limiting in `run_in_parallel()`
- Higher values allow more parallelism but may cause resource exhaustion
- Recommended range: 2-10 for most use cases

**Example Usage:**

```python
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

options = ChromiumOptions()
options.max_parallel_tasks = 4

browser = Chrome(options=options)
tab = await browser.start()

# Execute multiple tasks with max 4 running concurrently
tasks = [fetch_data(i) for i in range(10)]
results = await browser.run_in_parallel(*tasks)
```

See the [Browser Domain - Parallel Execution](browser-domain.md#parallel-execution) section for detailed documentation on using `run_in_parallel()`.
