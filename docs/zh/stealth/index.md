# 保持不被检测

当爬虫被封锁时，问题通常不在代码，而在信号。网站会读取三个层面：你的浏览器自称是什么（User-Agent、headless 标记、fingerprint）、它如何行动（瞬间点击、完全规律的打字），以及它如何应对挑战（Cloudflare Turnstile）。本页为每一层设置最基本的配置，并指向更深入的指南。

有些困难的部分你可以免费获得：因为 Pydoll 通过 CDP 驱动真实的 Chrome，网络和浏览器 fingerprint 都是真实的，而且 `navigator.webdriver` 无需任何修补就是 `false`。接下来讲的是你仍然需要掌控的部分。

**你将学到**

- [如何保持浏览器身份的一致性](#keep-the-identity-consistent)
- [如何像真人一样交互](#interact-like-a-person)
- [如何处理 Cloudflare Turnstile](#handle-cloudflare-turnstile)

## 保持身份一致 {#keep-the-identity-consistent}

身份是最难的一层，因为这些信号必须彼此一致，还要与你的 IP 和操作系统一致。User-Agent、Client Hints、语言、时区、WebGL renderer 和字体都会被交叉比对；孤立地覆盖其中一个，通常会让你更容易被检测，而不是更难。Pydoll 已经帮你保持了其中一部分的一致性（当你设置 `--user-agent=` 时，它会把 User-Agent 和 Client Hints 一起修正），并通过 `apply_fingerprint()` 应用一套完整且连贯的身份。

先从 [规避技术](evasion-techniques.md) 开始，了解你能掌控的各个杠杆（User-Agent、语言、WebRTC、真实的 profile），再看 [Fingerprint 注入](fingerprint-injection.md)，学习如何从一个 profile 应用一套完整的身份。

## 像真人一样交互 {#interact-like-a-person}

在元素正中心的瞬间点击，以及每 50ms 一次的按键，都是行为 fingerprint。传入 `humanize=True`，Pydoll 会在点击前以拟人的节奏沿曲线路径移动光标，并以变化的节奏打字，偶尔还会出现被纠正的拼写错误：

```python
search_box = await tab.find(id='search')
await search_box.type_text('browser automation', humanize=True)

submit = await tab.find(tag_name='button', type='submit')
await submit.click(humanize=True)
```

拟人化是按交互逐个选择启用的，所以你可以在行为被监视的地方保留它，在追求速度的地方跳过它。[拟人化交互](human-like-interactions.md) 解释了时序模型以及如何调整它。

## 处理 Cloudflare Turnstile {#handle-cloudflare-turnstile}

当受保护的页面显示 Turnstile 复选框时，Pydoll 可以帮你检测并点击它：

```python
async with tab.expect_and_bypass_cloudflare_captcha():
    await tab.go_to('https://site-protected-by-cloudflare.com')

print('Challenge handled, page loaded.')
```

点击这个控件只是其中一部分：Cloudflare 是否接受这次点击，还取决于你的 IP 信誉，以及浏览器其余部分看起来有多一致。如果挑战一直失败，请仔细阅读 [Captcha 绕过](captcha-bypass.md)，并考虑 [使用住宅 proxy](../guides/proxies.md)。

## 下一步

- [规避技术](evasion-techniques.md)：完整的检测模型以及你能掌控的各个杠杆。
- [拟人化交互](human-like-interactions.md)：`humanize=True` 背后的时序模型。
- [Captcha 绕过](captcha-bypass.md)：深入讲解 Cloudflare Turnstile 的处理。
- [Fingerprint 注入](fingerprint-injection.md)：在每一层应用一套连贯的身份。
