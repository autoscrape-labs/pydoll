# Playwright API

`pydoll.playwright` is a Playwright-compatible API for the browser automation surface: the same classes, methods, selectors and events your Playwright Python script already uses, executed over Pydoll's CDP connection with no driver process. This page is the contract: what is implemented in full, what works with a named difference, and what is missing, so you know before you switch. For the five-minute version, start with [Bring your Playwright script](../playwright.md).

The rule that governs the list: if a browser automation script works on Playwright and not here, it is a bug, and [an issue](https://github.com/autoscrape-labs/pydoll/issues) with the script is welcome. Test-runner features are not bugs; they are out of scope.

## Import paths

| Playwright | Pydoll |
|------------|--------|
| `from playwright.sync_api import sync_playwright` | `from pydoll.playwright.sync_api import sync_playwright` |
| `from playwright.async_api import async_playwright` | `from pydoll.playwright.async_api import async_playwright` |
| `from playwright.sync_api import Page, Locator, ...` | `from pydoll.playwright.sync_api import Page, Locator, ...` |
| `playwright.sync_api.TimeoutError`, `Error` | `pydoll.playwright.sync_api.TimeoutError`, `Error` |

The sync module is generated from the async one, the way Playwright's own is, so the two never differ in methods or arguments.

## Compatibility matrix

**Full** means the same signature and behavior. **Partial** means it works and the difference is named next to it. **Missing** means not implemented, with the Pydoll way to do it when there is one.

### Playwright and BrowserType

| Member | Status | Notes |
|--------|--------|-------|
| `chromium.launch()` | Full | `headless`, `args`, `executable_path`, `proxy`, `downloads_path` map onto [ChromiumOptions](browser-options.md) |
| `chromium.launch_persistent_context()` | Full | |
| `chromium.connect_over_cdp()` | Full | |
| `selectors.set_test_id_attribute()` | Full | |
| `devices` | Full | |
| `firefox`, `webkit` | Missing | Pydoll drives Chromium-based browsers only; raises `Error` |
| `chromium.connect()` | Missing | The Playwright server protocol has no equivalent; use `connect_over_cdp` |
| `request` (`APIRequestContext`) | Missing | Use [browser-context HTTP requests](http-requests.md) through `page.tab.request` |

Accepted and ignored on `launch()`: `slow_mo`, `devtools`, `env`, `ignore_default_args`, `channel`, `chromium_sandbox`, `handle_sigint` and friends.

### Browser

| Member | Status | Notes |
|--------|--------|-------|
| `new_context()`, `new_page()`, `contexts`, `version`, `close()` | Full | |
| `disconnected` event | Partial | Fires when you call `close()`; it does not fire when the browser process dies on its own |
| `new_browser_cdp_session()` | Missing | Use `browser.chrome.execute_command(...)` |
| `start_tracing()`, `stop_tracing()` | Missing | Out of scope |

### BrowserContext

| Member | Status | Notes |
|--------|--------|-------|
| `new_page()`, `pages`, `close()` | Full | |
| `cookies()`, `add_cookies()`, `clear_cookies()` | Full | |
| `storage_state()` | Full | Read and write |
| `grant_permissions()`, `clear_permissions()`, `set_geolocation()` | Full | |
| `set_extra_http_headers()`, `set_offline()` | Full | |
| `add_init_script()`, `expose_function()`, `expose_binding()` | Full | |
| `route()`, `unroute()`, `route_from_har()` | Partial | `route` and `unroute` are full; `route_from_har` is missing |
| `expect_page()`, `expect_event()`, `wait_for_event()` | Full | |
| `set_default_timeout()`, `set_default_navigation_timeout()` | Full | |
| Options: `viewport`, `user_agent`, `locale`, `timezone_id`, `extra_http_headers`, `storage_state`, `permissions`, `offline`, `base_url`, `http_credentials`, `ignore_https_errors`, `java_script_enabled`, `bypass_csp`, `color_scheme`, `device_scale_factor`, `is_mobile`, `has_touch` | Full | `http_credentials` answer the `401` challenge through the Fetch domain rather than sending a fixed header |
| Options: `record_video_dir`, `record_har_path`, `client_certificates`, `service_workers`, `strict_selectors`, `accept_downloads=False` | Partial | Accepted and ignored |
| `new_cdp_session()` | Missing | Use `page.tab.execute_command(...)` |
| `request` (`APIRequestContext`) | Missing | Use `page.tab.request` |
| `tracing`, `clock` | Missing | Out of scope |

### Page

| Member | Status | Notes |
|--------|--------|-------|
| `goto()`, `reload()`, `go_back()`, `go_forward()` | Full | `wait_until='commit'` resolves when the new document commits |
| `wait_for_load_state()`, `wait_for_url()`, `expect_navigation()` | Full | |
| `evaluate()`, `evaluate_handle()` | Partial | Runs in the main world without `eval`; `Date` comes back as an ISO string, `undefined` and `null` both as `None` |
| `query_selector()`, `query_selector_all()`, `wait_for_selector()`, `wait_for_function()`, `wait_for_timeout()` | Full | |
| `content()`, `set_content()`, `title()`, `url` | Full | |
| `frames`, `main_frame`, `frame()`, `frame_locator()` | Partial | `frames` fills from frame events; a child frame reports its parent's document until it resolves, shortly after attach |
| `add_init_script()`, `add_script_tag()`, `add_style_tag()` | Full | |
| `set_viewport_size()`, `viewport_size`, `emulate_media()`, `set_extra_http_headers()` | Full | |
| `screenshot()`, `pdf()` | Partial | `mask`, `animations`, `caret`, `scale` and `style` options of `screenshot` are accepted and ignored |
| `route()`, `unroute()`, `expose_function()`, `expose_binding()` | Full | |
| `keyboard`, `mouse`, `touchscreen` | Full | Playwright key names with the US layout: `Enter`, `Control+A`, `KeyA`, `Digit1` |
| Selector shortcuts: `click()`, `fill()`, `type()`, `press()`, `check()`, `select_option()`, `text_content()`, `inner_text()`, `inner_html()`, `get_attribute()`, `is_visible()`, ... | Full | |
| `get_by_role()`, `get_by_text()`, `get_by_label()`, `get_by_placeholder()`, `get_by_alt_text()`, `get_by_title()`, `get_by_test_id()` | Full | ARIA roles and accessible names computed with a port of Playwright's algorithm |
| Events: `load`, `domcontentloaded`, `framenavigated`, `request`, `response`, `requestfinished`, `requestfailed`, `dialog`, `console`, `pageerror`, `download`, `popup`, `filechooser`, `close`, `crash` | Full | With the matching `expect_*` context managers; `console` and `pageerror` are the only listeners that enable the `Runtime` domain |
| Events: `websocket`, `worker` | Missing | |
| `wait_for_request()`, `wait_for_response()` | Missing | Use `expect_request()` and `expect_response()` |
| `pause()`, `add_locator_handler()`, `aria_snapshot()`, `clock` | Missing | Out of scope |
| `request` (`APIRequestContext`) | Missing | Use `page.tab.request` |

### Frame, FrameLocator, Locator, ElementHandle, JSHandle

| Member | Status | Notes |
|--------|--------|-------|
| The full method set, including `filter()`, `and_()`, `or_()`, `nth()`, `first`, `last`, `count()`, `all()`, `drag_to()`, `select_option()`, `set_input_files()`, `screenshot()`, `evaluate_all()`, `bounding_box()`, `scroll_into_view_if_needed()`, `dispatch_event()` | Full | Locators are lazy and strict; actions follow Playwright's actionability checks and produce the same call log on timeout |
| `set_input_files()` | Full | Paths and `FilePayload` |
| `highlight()`, `aria_snapshot()` | Missing | |

### Selectors

| Syntax | Status | Notes |
|--------|--------|-------|
| CSS, XPath, `text=`, `xpath=`, `css=`, `id=`, `data-testid=`, `nth=`, `visible=`, chaining with `>>`, `internal:` engines behind `get_by_*` | Full | |
| Playwright CSS pseudo-classes `:has-text()`, `:visible`, `:nth-match()`, `:text()` | Missing | Use `get_by_text()`, `filter(has_text=...)`, `locator(...).nth()` |
| Layout selectors `:left-of()`, `:right-of()`, `:above()`, `:below()`, `:near()` | Missing | |
| `react=`, `vue=` engines, custom selector engines | Missing | |

### Request, Response, Route, Dialog, Download, ConsoleMessage, FileChooser

Full. Routing runs on the Fetch domain that [request interception](request-interception.md) uses. `route.fetch()` lets the request reach the network and pauses again at the response stage, so a handler can rewrite a body with `route.fulfill(response=..., body=...)`.

### Not in scope

`expect()` assertions, the `pytest-playwright` plugin and its fixtures, tracing, video recording, HAR replay, `Clock`, `Tracing`, `Worker`, `WebSocket`, `Android`, `Electron`. A script that needs the test runner keeps using Playwright for the runner; the browser automation inside a test can still be Pydoll through `connect_over_cdp`.

## Behaviors that differ on purpose

These come from Pydoll's stealth defaults and are kept under the Playwright surface:

- Evaluations run without a synthetic user gesture, so `navigator.userActivation` stays false until a real click. Set `user_gesture_on_evaluate=True` on the context if a script needs `window.open` from `evaluate`.
- Popups are blocked unless a user action opens them, as in a normal Chrome.
- Actions do not wait for a navigation they start, and `no_wait_after` is accepted and ignored. When a click submits a form or follows a link, wait with `page.wait_for_url()` or `page.expect_navigation()` before reading the new page.
- A `user_agent` override ships coherent Client Hints and follows Chrome's reduced UA format; the string you pass is normalized the way Pydoll does for its own options. `locale` sets a Chrome-shaped `Accept-Language`.
- `http_credentials` only answer a challenge from their own origin.
- A cross-origin iframe that Chrome renders out of process cannot be reached through `frame_locator()` or a selector chain that enters the frame: the selector engine lives in the parent's session while the query would have to run in the child's. Use `element_handle.content_frame()` and the frame's own methods for those frames.
- Context-level init scripts, bindings and emulation reach a popup only after it is adopted, so they miss the popup's very first document.
- Viewport emulation keeps `screen` at least as large as the viewport, so the two never contradict each other.
- The selector and actionability engine runs in an isolated world of each frame, evaluated once and reused, so a page that wraps DOM prototypes, `requestAnimationFrame` or `window.eval` never sees it. Your own `page.evaluate` code runs in the main world, where the page's globals live, and its source is embedded in the call rather than passed through `eval`.

## Reaching Pydoll

| Playwright object | Pydoll object underneath |
|-------------------|--------------------------|
| `browser.chrome` | [Chrome](../api/browser/chrome.md) |
| `page.tab` | [Tab](../api/browser/tab.md) |
| `locator.element_handle().web_element` | [WebElement](../api/elements/web_element.md) |

=== "Sync"

    ```python
    with page.tab.expect_cloudflare_turnstile():
        page.goto('https://example.com/protected')

    button = page.get_by_role('button', name='Continue').element_handle().web_element
    button.click(humanize=True)
    ```

=== "Async"

    ```python
    async with page.tab.expect_cloudflare_turnstile():
        await page.goto('https://example.com/protected')

    button = (await page.get_by_role('button', name='Continue').element_handle()).web_element
    await button.click(humanize=True)
    ```

## What's next

- [Bring your Playwright script](../playwright.md): the walkthrough, with the honest note on what detection still sees.
- [Request interception](request-interception.md): the Fetch domain that routes are built on.
- [Migrating from Selenium and Playwright](../migrating.md): the same moves in Pydoll's own API.
