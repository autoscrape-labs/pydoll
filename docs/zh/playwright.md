# 带上你的 Playwright 脚本

你的 Playwright 脚本一直好用，直到某个站点开始拦截它。Pydoll 用纯 CDP 运行同一个脚本，没有驱动进程，也没有打过补丁的浏览器，所以传输层里没有任何东西可供检测器发现，你也不需要重写任何代码。本页从一个已有的 Playwright 脚本出发，五分钟内让它跑在 Pydoll 上，然后展示在你需要时 Pydoll 比 Playwright 多走的那一步。

**你将学到**

- [如何只改一行导入就切换脚本](#swap-the-import)
- [你的脚本底下发生了什么变化](#what-changed-under-your-script)
- [如何在 Playwright 脚本里使用 Pydoll 的功能](#reach-pydoll-from-a-playwright-object)
- [这对检测改变了什么，没改变什么](#what-this-does-not-change)

## 替换导入 {#swap-the-import}

把 `playwright.sync_api` 换成 `pydoll.playwright.sync_api`，或者把 `playwright.async_api` 换成 `pydoll.playwright.async_api`。其余一切照旧。你不需要安装 `playwright` 包或它附带的浏览器；Pydoll 驱动的是你机器上已经装好的 Chrome 或 Edge。

=== "Sync"

    ```python
    from pydoll.playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto('https://quotes.toscrape.com/login')

        page.get_by_label('Username').fill('john')
        page.locator('#password').fill('SecretPass123')
        page.get_by_role('button', name='Login').click()
        page.wait_for_url('**/')

        print(page.get_by_role('link', name='Logout').is_visible())
        browser.close()
    ```

=== "Async"

    ```python
    import asyncio

    from pydoll.playwright.async_api import async_playwright


    async def main():
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto('https://quotes.toscrape.com/login')

            await page.get_by_label('Username').fill('john')
            await page.locator('#password').fill('SecretPass123')
            await page.get_by_role('button', name='Login').click()
            await page.wait_for_url('**/')

            print(await page.get_by_role('link', name='Logout').is_visible())
            await browser.close()

    asyncio.run(main())
    ```

像往常一样运行它。定位器依然是惰性且严格的，`get_by_role` 解析出同样的元素，动作会自动等待元素挂载、可见、稳定且可用，等待失败时抛出同样的 `TimeoutError`，带着同样的调用日志。

`chromium.launch()` 接受你已经在传的选项：`headless`、`args`、`executable_path`、`proxy`、`downloads_path`。`launch_persistent_context(user_data_dir)` 和 `connect_over_cdp(url)` 也能用。`firefox` 和 `webkit` 会抛出错误，因为 Pydoll 只驱动基于 Chromium 的浏览器。

!!! note "对自动化接口而言是即插即用"
    这一层覆盖脚本会用到的部分：`Playwright`、`Browser`、`BrowserContext`、`Page`、`Frame`、`Locator`、`ElementHandle`、`Keyboard`、`Mouse`、路由、对话框和下载。它不覆盖测试运行器：`expect()` 断言、fixture、pytest 插件、tracing 和视频都没有实现。[Playwright API](guides/playwright-api.md) 列出了每个类，标明完整、部分或缺失。

## 你的脚本底下发生了什么变化 {#what-changed-under-your-script}

Playwright 通过一个用 Node 写的驱动进程和浏览器对话。每次调用都要穿过那个进程，再由它用 CDP 和 Chrome 通信。Patchright 之类的隐身分支是事后给那个驱动打补丁，去掉暴露自动化的调用。

Pydoll 没有驱动。你的 `page.goto` 变成了直接从 Python 发出的 CDP 命令，走的是 Pydoll 自己的 API 使用的同一条连接。这从源头上去掉了传输层的破绽，而不是事后修补：

- `Runtime` 域的启用是最广为人知的自动化破绽，而它永远不会为你的脚本启用。选择器和可操作性检查在每个 frame 的隔离世界里运行，只求值一次，而你自己的 `page.evaluate` 代码在主世界运行，不经过 `eval`。
- 没有 `--enable-automation`，没有 `navigator.webdriver`，没有 console 钩子，没有每次导航都注入的初始化脚本。
- 求值不携带合成的用户手势，弹窗只会由真实的用户动作打开，`user_agent` 覆盖会附带一致的 Client Hints，就像有人在用的浏览器一样。

浏览器的其余部分就是真正的 Chrome：它的 TLS、HTTP/2 和渲染指纹都是 Chrome 本来的样子，因为它就是 Chrome。

## 从 Playwright 对象触达 Pydoll {#reach-pydoll-from-a-playwright-object}

每个 Playwright 对象都暴露了底下的 Pydoll 对象，所以 Playwright 叫不出名字的功能只隔着一个属性。你不需要为了用它们而重写脚本。

| Playwright 对象 | 底下的 Pydoll 对象 |
|-----------------|-------------------|
| `browser.chrome` | [Chrome](api/browser/chrome.md) |
| `page.tab` | [Tab](api/browser/tab.md) |
| `locator.element_handle().web_element` | [WebElement](api/elements/web_element.md) |

被拦截的脚本接下来通常需要的三件事，每件一行：

=== "Sync"

    ```python
    from pydoll.sync import ExtractionModel, Field
    from pydoll.playwright.sync_api import sync_playwright

    from examples.fingerprints import FINGERPRINTS


    class Quote(ExtractionModel):
        text: str = Field(selector='.text')
        author: str = Field(selector='.author')


    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        page.tab.apply_fingerprint(FINGERPRINTS['macos_m3_new_york'])
        page.tab.enable_cloudflare_turnstile_handling()
        page.goto('https://quotes.toscrape.com')

        quotes = page.tab.extract_all(Quote, scope='.quote')
        submit = page.get_by_role('link', name='Login').element_handle().web_element
        submit.click(humanize=True)
    ```

=== "Async"

    ```python
    from pydoll import ExtractionModel, Field
    from pydoll.playwright.async_api import async_playwright

    from examples.fingerprints import FINGERPRINTS


    class Quote(ExtractionModel):
        text: str = Field(selector='.text')
        author: str = Field(selector='.author')


    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        await page.tab.apply_fingerprint(FINGERPRINTS['macos_m3_new_york'])
        await page.tab.enable_cloudflare_turnstile_handling()
        await page.goto('https://quotes.toscrape.com')

        quotes = await page.tab.extract_all(Quote, scope='.quote')
        submit = (await page.get_by_role('link', name='Login').element_handle()).web_element
        await submit.click(humanize=True)
    ```

`apply_fingerprint` 在每一层设置一致的身份（[Fingerprint 注入](stealth/fingerprint-injection.md)），`enable_cloudflare_turnstile_handling` 在页面带着 Turnstile 组件加载时点击它（[Cloudflare Turnstile](stealth/captcha-bypass.md)），`extract_all` 返回类型化且经过校验的对象（[结构化提取](guides/structured-extraction.md)），`humanize=True` 让鼠标沿曲线路径以真人的节奏移动（[拟人化交互](stealth/human-like-interactions.md)）。原始 CDP 也只隔着一次调用：`page.tab.execute_command(...)`。

## 这不会改变什么 {#what-this-does-not-change}

!!! warning "检测仍然能看到什么"
    Pydoll 去掉的是库本身添加的自动化破绽；它不会把机器人变成人。无头浏览器仍然能通过渲染方式和缺失的媒体设备被认出来，所以要么有界面运行，要么应用一个覆盖无头信号的指纹配置。你的 IP 信誉和浏览器同样重要；数据中心 IP 过不了住宅 IP 能过的挑战。烧录在 Chrome 二进制里的信号不会被触碰。行为也很重要：瞬时点击和完全规律的输入看起来就是它们本来的样子，`humanize=True` 正是为此而存在。

[保持不被检测](stealth/index.md) 逐层讲解每一层的最小配置。

## 下一步

- [Playwright API](guides/playwright-api.md)：完整的兼容性矩阵，以及有差异的行为。
- [保持不被检测](stealth/index.md)：身份、行为和挑战，按这个顺序。
- [从 Selenium 和 Playwright 迁移](migrating.md)：同样的操作在 Pydoll 自己的 API 里怎么写，当你想转为原生时。
