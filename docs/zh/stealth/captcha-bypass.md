# Cloudflare Turnstile

Pydoll 可以帮你点击 Cloudflare Turnstile 的复选框，就和真人在这个控件上的点击一样。它不会解决图片或拼图类挑战，而且这次点击是否被接受，取决于你的 IP 信誉和 fingerprint，而不取决于 Pydoll。请把它当作是自动化这次点击，而不是攻破 captcha。

<iframe src="/docs/resources/visuals/captcha-turnstile.html" aria-label="Pydoll 点击 Turnstile 复选框，结果取决于 IP 信誉" style="width: 100%; height: 345px; border: 0;" loading="lazy"></iframe>

## 在导航时处理 Turnstile

这个上下文管理器会在代码块执行期间等待 Turnstile 控件出现，点击它的复选框，并在完成操作后让你的代码继续运行。把触发挑战的导航放进这个代码块里。

```python
import asyncio

from pydoll.browser.chromium import Chrome


async def main():
    async with Chrome() as browser:
        tab = await browser.start()

        async with tab.expect_and_bypass_cloudflare_captcha():
            await tab.go_to('https://a-site-behind-turnstile.com')

        content = await tab.find(id='protected-content', timeout=10, raise_exc=False)
        print(await content.text if content else 'Still challenged.')

asyncio.run(main())
```

把 URL 替换成你正在自动化的网站。目前没有公开、稳定的 Turnstile 页面可供指向。

## 在后台处理 Turnstile

当你不想包裹某一次具体的导航时，可以启用后台处理：Pydoll 会在控件每次出现时点击它，直到你将其禁用。

```python
import asyncio

from pydoll.browser.chromium import Chrome


async def main():
    async with Chrome() as browser:
        tab = await browser.start()

        await tab.enable_auto_solve_cloudflare_captcha()
        await tab.go_to('https://a-site-behind-turnstile.com')
        await asyncio.sleep(5)   # 给控件出现并被点击的时间

        await tab.disable_auto_solve_cloudflare_captcha()

asyncio.run(main())
```

## 它如何找到复选框

Pydoll 通过轮询页面的 shadow DOM 来检测 Cloudflare 控件：它会查找承载 `challenges.cloudflare.com` 的 shadow root，进入其跨源 iframe，找到内部的 shadow root，并在复选框一出现就点击它。你不需要配置选择器，也没有需要调整的点击延迟。

## 给控件出现的时间

有些网站会在初始加载之后才渲染 Turnstile。`time_to_wait_captcha`（默认 5 秒）是 Pydoll 在放弃之前等待控件出现的时长。对于较慢的网站，可以把它调大。

```python
async with tab.expect_and_bypass_cloudflare_captcha(time_to_wait_captcha=15):
    await tab.go_to('https://a-site-behind-turnstile.com')
```

`time_to_wait_captcha` 是唯一的时序参数。如果控件在这个时间窗口内始终没有出现，这次交互就会被跳过。

!!! note "从旧版本迁移"
    `custom_selector` 和 `time_before_click` 在这些方法上仍然存在，但已被弃用并忽略。现在检测是自动的，所以请把它们从旧代码中移除。

## 哪些因素决定点击是否被接受

点击复选框只是其中一部分。Turnstile 会根据 Pydoll 无法控制的信号来决定是否接受它：

- **IP 信誉。** 干净的住宅或移动 IP 通常会被接受；数据中心 IP 往往会被挑战或封锁。没有任何浏览器配置能弥补一个被标记的 IP。参见 [Proxy](../guides/proxies.md)。
- **Fingerprint 一致性。** 你的浏览器所呈现的身份必须与自身一致，也要与你的 IP 一致。最容易让 Turnstile 出问题的有两点：
    - **Chrome 版本不匹配。** 如果你使用 [Fingerprint 注入](fingerprint-injection.md)，profile 所声明的版本必须与真实的二进制文件一致（请让它与 `await browser.get_version()` 对齐），否则页面会一直停留在 "Just a moment..." 上。
    - **只停留在页面这一层的身份。** 控件会在它自己的跨源 iframe 内部读取 fingerprint，所以 profile 也必须能作用到那里。`apply_fingerprint()` 默认就会这么做（`cross_origin_iframes`），再把 profile 的 locale、时区和地理位置与出口 IP 相匹配，就更完善了。
- **Headful 与 headless。** Headless 会发出较弱的显示信号，可能降低信任分，但这并不是一堵无法逾越的墙。只要 fingerprint 完全自洽（包括跨源 iframe），并且 locale 与 IP 相匹配，在一个不错的 IP 上 headless 也能通过 Turnstile。在勉强及格的 IP 上，优先使用 headful，或者在服务器上用虚拟帧缓冲（Xvfb）跑 headful，让显示信号不再对你不利。[Cloudflare 托管挑战](../deep-dive/fingerprinting/cloudflare-challenge.md) 深入解析里有完整的拆解。

如果复选框被点击了，但接着出现拼图或图片挑战，说明信任分太低了。Pydoll 无法解决那种挑战；应该改善 IP 和 fingerprint。

<iframe src="/docs/resources/visuals/turnstile-trust-score.html" aria-label="IP 信誉、fingerprint 一致性和浏览器模式共同构成一个信任分，最终得出接受、挑战或封锁的结果；Pydoll 自动完成的点击只是其中一个输入" style="width: 100%; height: 430px; border: 0;" loading="lazy"></iframe>

## 它不做什么

- 它不会解决图片选择或拼图类挑战。
- 它不处理 reCAPTCHA 或 hCaptcha。这个功能不支持它们。
- 它不会改变你的 IP 或 fingerprint。请把它与一个好的 proxy 和一致的 fingerprint 搭配使用，这次点击才能生效。

!!! warning "尊重网站的条款"
    自动化 captcha 可能违反网站的服务条款。请仅在你获得授权的场景下使用：测试你自己的应用、监控你所控制的服务，或经许可的研究。

## 下一步

- [保持不被检测](index.md)：captcha 处理如何与其余的 stealth 层配合。
- [Proxy](../guides/proxies.md)：决定大多数 Turnstile 结果的 IP 信誉。
- [拟人化交互](human-like-interactions.md)：点击前后的拟人化行为。
