# Playwright API

`pydoll.playwright` 是面向浏览器自动化接口的 Playwright 兼容 API：你的 Playwright Python 脚本已经在用的那些类、方法、选择器和事件，通过 Pydoll 的 CDP 连接执行，没有驱动进程。本页是契约：哪些完整实现，哪些可用但有一个已命名的差异，哪些缺失，让你在切换之前就心里有数。想要五分钟版本，请从 [带上你的 Playwright 脚本](../playwright.md) 开始。

支配这份列表的规则：如果一个浏览器自动化脚本在 Playwright 上能跑而在这里不能，那就是 bug，欢迎带着脚本[提交 issue](https://github.com/autoscrape-labs/pydoll/issues)。测试运行器的功能不算 bug；它们不在范围内。

## 导入路径

| Playwright | Pydoll |
|------------|--------|
| `from playwright.sync_api import sync_playwright` | `from pydoll.playwright.sync_api import sync_playwright` |
| `from playwright.async_api import async_playwright` | `from pydoll.playwright.async_api import async_playwright` |
| `from playwright.sync_api import Page, Locator, ...` | `from pydoll.playwright.sync_api import Page, Locator, ...` |
| `playwright.sync_api.TimeoutError`、`Error` | `pydoll.playwright.sync_api.TimeoutError`、`Error` |

同步模块由异步模块生成，和 Playwright 自己的做法一样，所以两者在方法和参数上永远不会有差异。

## 兼容性矩阵

**完整**表示签名和行为都相同。**部分**表示可用，差异写在旁边。**缺失**表示未实现，有 Pydoll 替代做法时会一并给出。

### Playwright 与 BrowserType

| 成员 | 状态 | 说明 |
|------|------|------|
| `chromium.launch()` | 完整 | `headless`、`args`、`executable_path`、`proxy`、`downloads_path` 映射到 [ChromiumOptions](browser-options.md) |
| `chromium.launch_persistent_context()` | 完整 | |
| `chromium.connect_over_cdp()` | 完整 | |
| `selectors.set_test_id_attribute()` | 完整 | |
| `devices` | 完整 | |
| `firefox`、`webkit` | 缺失 | Pydoll 只驱动基于 Chromium 的浏览器；抛出 `Error` |
| `chromium.connect()` | 缺失 | Playwright 服务器协议没有对应物；改用 `connect_over_cdp` |
| `request`（`APIRequestContext`） | 缺失 | 通过 `page.tab.request` 使用[浏览器上下文的 HTTP 请求](http-requests.md) |

在 `launch()` 上接受但忽略：`slow_mo`、`devtools`、`env`、`ignore_default_args`、`channel`、`chromium_sandbox`、`handle_sigint` 等。

### Browser

| 成员 | 状态 | 说明 |
|------|------|------|
| `new_context()`、`new_page()`、`contexts`、`version`、`close()` | 完整 | |
| `disconnected` 事件 | 部分 | 在你调用 `close()` 时触发；浏览器进程自行退出时不会触发 |
| `new_browser_cdp_session()` | 缺失 | 改用 `browser.chrome.execute_command(...)` |
| `start_tracing()`、`stop_tracing()` | 缺失 | 不在范围内 |

### BrowserContext

| 成员 | 状态 | 说明 |
|------|------|------|
| `new_page()`、`pages`、`close()` | 完整 | |
| `cookies()`、`add_cookies()`、`clear_cookies()` | 完整 | |
| `storage_state()` | 完整 | 读和写 |
| `grant_permissions()`、`clear_permissions()`、`set_geolocation()` | 完整 | |
| `set_extra_http_headers()`、`set_offline()` | 完整 | |
| `add_init_script()`、`expose_function()`、`expose_binding()` | 完整 | |
| `route()`、`unroute()`、`route_from_har()` | 部分 | `route` 和 `unroute` 完整；`route_from_har` 缺失 |
| `expect_page()`、`expect_event()`、`wait_for_event()` | 完整 | |
| `set_default_timeout()`、`set_default_navigation_timeout()` | 完整 | |
| 选项：`viewport`、`user_agent`、`locale`、`timezone_id`、`extra_http_headers`、`storage_state`、`permissions`、`offline`、`base_url`、`http_credentials`、`ignore_https_errors`、`java_script_enabled`、`bypass_csp`、`color_scheme`、`device_scale_factor`、`is_mobile`、`has_touch` | 完整 | `http_credentials` 通过 Fetch 域响应 `401` 认证挑战，而不是发送固定的头 |
| 选项：`record_video_dir`、`record_har_path`、`client_certificates`、`service_workers`、`strict_selectors`、`accept_downloads=False` | 部分 | 接受但忽略 |
| `new_cdp_session()` | 缺失 | 改用 `page.tab.execute_command(...)` |
| `request`（`APIRequestContext`） | 缺失 | 改用 `page.tab.request` |
| `tracing`、`clock` | 缺失 | 不在范围内 |

### Page

| 成员 | 状态 | 说明 |
|------|------|------|
| `goto()`、`reload()`、`go_back()`、`go_forward()` | 完整 | `wait_until='commit'` 在新文档提交（commit）时完成 |
| `wait_for_load_state()`、`wait_for_url()`、`expect_navigation()` | 完整 | |
| `evaluate()`、`evaluate_handle()` | 部分 | 在主世界运行，不经过 `eval`；`Date` 以 ISO 字符串返回，`undefined` 和 `null` 都变成 `None` |
| `query_selector()`、`query_selector_all()`、`wait_for_selector()`、`wait_for_function()`、`wait_for_timeout()` | 完整 | |
| `content()`、`set_content()`、`title()`、`url` | 完整 | |
| `frames`、`main_frame`、`frame()`、`frame_locator()` | 部分 | `frames` 由 frame 事件填充；子 frame 在解析完成之前（附加后不久）会报告父文档 |
| `add_init_script()`、`add_script_tag()`、`add_style_tag()` | 完整 | |
| `set_viewport_size()`、`viewport_size`、`emulate_media()`、`set_extra_http_headers()` | 完整 | |
| `screenshot()`、`pdf()` | 部分 | `screenshot` 的 `mask`、`animations`、`caret`、`scale` 和 `style` 选项接受但忽略 |
| `route()`、`unroute()`、`expose_function()`、`expose_binding()` | 完整 | |
| `keyboard`、`mouse`、`touchscreen` | 完整 | 使用 Playwright 的按键名和美式布局：`Enter`、`Control+A`、`KeyA`、`Digit1` |
| 选择器快捷方法：`click()`、`fill()`、`type()`、`press()`、`check()`、`select_option()`、`text_content()`、`inner_text()`、`inner_html()`、`get_attribute()`、`is_visible()` 等 | 完整 | |
| `get_by_role()`、`get_by_text()`、`get_by_label()`、`get_by_placeholder()`、`get_by_alt_text()`、`get_by_title()`、`get_by_test_id()` | 完整 | ARIA 角色和可访问名称由 Playwright 算法的移植版本计算 |
| 事件：`load`、`domcontentloaded`、`framenavigated`、`request`、`response`、`requestfinished`、`requestfailed`、`dialog`、`console`、`pageerror`、`download`、`popup`、`filechooser`、`close`、`crash` | 完整 | 配有对应的 `expect_*` 上下文管理器；`console` 和 `pageerror` 是仅有的会启用 `Runtime` 域的监听器 |
| 事件：`websocket`、`worker` | 缺失 | |
| `wait_for_request()`、`wait_for_response()` | 缺失 | 使用 `expect_request()` 和 `expect_response()` |
| `pause()`、`add_locator_handler()`、`aria_snapshot()`、`clock` | 缺失 | 不在范围内 |
| `request`（`APIRequestContext`） | 缺失 | 改用 `page.tab.request` |

### Frame、FrameLocator、Locator、ElementHandle、JSHandle

| 成员 | 状态 | 说明 |
|------|------|------|
| 完整的方法集，包括 `filter()`、`and_()`、`or_()`、`nth()`、`first`、`last`、`count()`、`all()`、`drag_to()`、`select_option()`、`set_input_files()`、`screenshot()`、`evaluate_all()`、`bounding_box()`、`scroll_into_view_if_needed()`、`dispatch_event()` | 完整 | 定位器惰性且严格；动作遵循 Playwright 的可操作性检查，超时时给出同样的调用日志 |
| `set_input_files()` | 完整 | 路径和 `FilePayload` |
| `highlight()`、`aria_snapshot()` | 缺失 | |

### 选择器

| 语法 | 状态 | 说明 |
|------|------|------|
| CSS、XPath、`text=`、`xpath=`、`css=`、`id=`、`data-testid=`、`nth=`、`visible=`、用 `>>` 链式组合、`get_by_*` 背后的 `internal:` 引擎 | 完整 | |
| Playwright 的 CSS 伪类 `:has-text()`、`:visible`、`:nth-match()`、`:text()` | 缺失 | 改用 `get_by_text()`、`filter(has_text=...)`、`locator(...).nth()` |
| 布局选择器 `:left-of()`、`:right-of()`、`:above()`、`:below()`、`:near()` | 缺失 | |
| `react=`、`vue=` 引擎和自定义选择器引擎 | 缺失 | |

### Request、Response、Route、Dialog、Download、ConsoleMessage、FileChooser

完整。路由运行在[请求拦截](request-interception.md)所用的 Fetch 域上。`route.fetch()` 让请求到达网络，并在响应阶段再次暂停，因此处理器可以用 `route.fulfill(response=..., body=...)` 改写响应体。

### 不在范围内

`expect()` 断言、`pytest-playwright` 插件及其 fixture、tracing、视频录制、HAR 回放、`Clock`、`Tracing`、`Worker`、`WebSocket`、`Android`、`Electron`。需要测试运行器的脚本继续用 Playwright 做运行器；测试内部的浏览器自动化仍然可以通过 `connect_over_cdp` 交给 Pydoll。

## 有意为之的行为差异

这些来自 Pydoll 的隐身默认值，被保留在 Playwright 接口之下：

- 求值不带合成的用户手势，所以 `navigator.userActivation` 在真实点击之前保持为 false。如果脚本需要在 `evaluate` 里调用 `window.open`，在上下文上设置 `user_gesture_on_evaluate=True`。
- 弹窗除非由用户动作打开，否则会被拦下，和普通 Chrome 一样。
- 动作不会等待它自己触发的导航，`no_wait_after` 会被接受但忽略。当一次点击提交了表单或跟随了链接，先用 `page.wait_for_url()` 或 `page.expect_navigation()` 等待，再读取新页面。
- `user_agent` 覆盖会附带一致的 Client Hints，并遵循 Chrome 的精简 UA 格式；你传入的字符串会按 Pydoll 处理自身选项的方式规范化。`locale` 设置 Chrome 形态的 `Accept-Language`。
- `http_credentials` 只响应来自其自身源的挑战。
- Chrome 在独立进程中渲染的跨源 iframe 无法通过 `frame_locator()` 或进入该框架的选择器链访问：选择器引擎位于父级会话中，而查询必须在子级会话里运行。对这类框架，请使用 `element_handle.content_frame()` 和该框架自己的方法。
- 上下文级的初始化脚本、绑定和仿真只有在弹窗被接管之后才会生效，因此会错过弹窗的第一个文档。
- 视口模拟会让 `screen` 至少和视口一样大，两者永远不会互相矛盾。
- 选择器和可操作性引擎在每个 frame 的隔离世界里运行，求值一次后复用，所以包装了 DOM 原型、`requestAnimationFrame` 或 `window.eval` 的页面永远看不到它。你自己的 `page.evaluate` 代码在页面全局对象所在的主世界运行，其源码嵌入在调用里，而不是经过 `eval`。

## 触达 Pydoll

| Playwright 对象 | 底下的 Pydoll 对象 |
|-----------------|-------------------|
| `browser.chrome` | [Chrome](../api/browser/chrome.md) |
| `page.tab` | [Tab](../api/browser/tab.md) |
| `locator.element_handle().web_element` | [WebElement](../api/elements/web_element.md) |

=== "Sync"

    ```python
    page.tab.enable_cloudflare_turnstile_handling()
    page.goto('https://example.com/protected')

    button = page.get_by_role('button', name='Continue').element_handle().web_element
    button.click(humanize=True)
    ```

=== "Async"

    ```python
    await page.tab.enable_cloudflare_turnstile_handling()
    await page.goto('https://example.com/protected')

    button = (await page.get_by_role('button', name='Continue').element_handle()).web_element
    await button.click(humanize=True)
    ```

## 下一步

- [带上你的 Playwright 脚本](../playwright.md)：完整的操作步骤，以及关于检测仍能看到什么的诚实说明。
- [请求拦截](request-interception.md)：路由所依赖的 Fetch 域。
- [从 Selenium 和 Playwright 迁移](../migrating.md)：同样的操作在 Pydoll 自己的 API 里怎么写。
