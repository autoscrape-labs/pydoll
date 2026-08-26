# Fingerprint 注入

## 简介

`tab.apply_fingerprint()` 给浏览器一个新身份。它在第一次导航之前，覆盖 fingerprinting 脚本读取的信号，User-Agent 和 Client Hints、`navigator`、WebGL、屏幕参数、字体、音频、时区和 locale，覆盖范围包括页面、它的 workers 以及它的 cross-origin iframes。你不用手写 fingerprint，也不用给 `navigator` 打补丁；你传入一个 profile，Pydoll 会一致地应用它。

收益很具体。配上一个匹配的 profile，headless Chrome 就从一眼被判为 bot 变成读起来像一台普通桌面机，足以[在 headless 模式下通过 Cloudflare 的托管挑战](#clear-cloudflares-challenge-headless)。

先说清楚一个界限：这是身份替换，不是匿名。它不改变你的出口 IP，也不改变网络层 fingerprint，而且一个不一致的 profile 比未经修改的浏览器更容易被检测。让 profile *匹配*你的机器和 IP 才是全部的工作，[下面的规则](#making-a-profile-pass)就是这份清单。

**你将学到**

- [如何应用一个 fingerprint](#quick-start)
- [它如何在 headless 下通过 Cloudflare](#clear-cloudflares-challenge-headless)
- [如何证明它在起作用](#prove-it-with-a-bot-score)
- [如何让一个 profile 通过](#making-a-profile-pass)
- [如何使用你自己的 profile](#bring-your-own-profiles)

## 快速开始 {#quick-start}

在第一次导航之前调用 `apply_fingerprint()`。只有 profile 中存在的字段会被覆盖；其余保持浏览器的真实值。

```python
import asyncio

from pydoll.browser.chromium import Chrome

from examples.fingerprints import FINGERPRINTS

async def spoof_fingerprint():
    async with Chrome() as browser:
        tab = await browser.start()

        # 在第一次导航之前应用。
        await tab.apply_fingerprint(FINGERPRINTS['macos_m3_new_york'])

        await tab.go_to('https://abrahamjuliot.github.io/creepjs/')
        await asyncio.sleep(5)

asyncio.run(spoof_fingerprint())
```

!!! note "`FINGERPRINTS` 从哪来"
    Pydoll 不附带 fingerprint profile。`FINGERPRINTS` 位于 [pydoll 仓库](https://github.com/autoscrape-labs/pydoll) 的 `examples/fingerprints.py`，是 `FingerprintConfig` 结构（来自 `pydoll.protocol.fingerprint.types` 的一个 typed dict）的参考 profile。把这个文件复制到你的项目里，再把每个 profile 适配到你自己的机器和 IP，[下面的规则](#making-a-profile-pass)会解释原因。原样复用一个 profile 是一个共享签名，而不是伪装。

## 在 headless 下通过 Cloudflare 挑战 {#clear-cloudflares-challenge-headless}

headless Chrome 通常一上来就通不过 bot 检查：软件 WebGL 渲染器、写死的 800x600 屏幕、空的插件列表。一个匹配的 profile 会中和这些渲染信号，于是 headless 会话读起来就像 headful。再把身份也复制进 cross-origin 挑战 iframe（`cross_origin_iframes`，默认开启），这就足以通过 Cloudflare 的托管挑战，完全不需要 captcha solver。

<p align="center">
  <img src="/docs/resources/images/cloudflare-headless-bypass.gif" alt="Pydoll 在 headless 模式下加载一个受 Cloudflare 保护的站点，并在应用了 fingerprint 后通过托管挑战" width="760" />
</p>
<p align="center"><sub>Headless，配上一个匹配的 fingerprint：托管挑战通过。</sub></p>

```python
async with Chrome() as browser:
    tab = await browser.start(headless=True)

    # 把 profile 匹配到这台 host 和这个 IP（见下面的规则）。
    await tab.apply_fingerprint(FINGERPRINTS['macos_m3_new_york'])

    await tab.go_to('https://a-site-behind-cloudflare.com')
    # 身份一致时，interstitial 就会通过。
```

让它成立有两个条件，都来自[下面的规则](#making-a-profile-pass)：profile 必须一致（OS、Chrome 版本和 locale 都要匹配你的 host 和 IP），并且 IP 要干净。信誉差的机房 IP 在 headless 和 headful 下一样会被挑战。IP 不理想时，优先用 headful，或在 Xvfb 下跑 headful。

在底层，headless 还有一个 cross-origin frame 会直接读取的 client-side 泄漏：它自己的 `window.screen`。不做 reshape，这个 frame 会读到原始的 800x600 headless 屏幕，与页面矛盾；做了 reshape，两者就一致。

<iframe scrolling="no" src="/docs/resources/visuals/headless-screen-oopif.html" aria-label="一个 headless 页面和它的 cross-origin iframe 各自读取 window.screen；切换 reshape 会让 iframe 从原始的 800x600 headless 屏幕翻转到与页面一致" style="width: 100%; height: 460px; border: 0;" loading="lazy"></iframe>

关于挑战究竟读取了什么，以及为什么一致就能通过的完整拆解，见 [Cloudflare 的托管挑战](../deep-dive/fingerprinting/cloudflare-challenge.md)。

## 用 bot score 来证明 {#prove-it-with-a-bot-score}

一个 fingerprint 是帮忙还是帮倒忙，是可以量化的。[fingerprint-scan.com](https://fingerprint-scan.com/) 由 Castle 反 bot 博客背后的工程师打造，给出一个 0 到 100 的 **bot score**，越低越像人。headless 是最鲜明的演示：没有 profile 时，headless Chrome 拿满分；一个匹配的 profile 会把它降到 headful 的水平。

| 运行（同一台 Mac，Chrome 151） | Bot score |
|---|---|
| Headless，无 profile | 100 / 100 |
| Headless，匹配的 macOS profile | 15 / 100 |
| Headful，无 profile | 15 / 100 |
| Headful，匹配的 macOS profile | 15 / 100 |
| Headful，不匹配的 Windows profile | 57 / 100 |

<p align="center">
  <img src="/docs/resources/images/fp-scan-headless-nofp.png" alt="fingerprint-scan.com 对没有 fingerprint 的 headless Chrome 报告 100/100 的 bot score" width="380" />
  <img src="/docs/resources/images/fp-scan-headless-mac.png" alt="fingerprint-scan.com 对应用了 macOS fingerprint 的 headless Chrome 报告 15/100 的 bot score" width="380" />
</p>
<p align="center"><sub>Headless：无 profile 时 100/100，匹配的 macOS profile 时 15/100。</sub></p>

这证明了两点。profile 不会让浏览器隐形：即便匹配，也是 15，不是 0（CDP 上的真实 Chrome 本来就读起来像人，把最后这点差距抹平是一个开放问题）。而一个*不匹配*的 profile 比完全没有 profile 还差，最后一行跳到 57，因为有一个字段（OS）和底层硬件矛盾。这正是这些规则存在的原因。

!!! warning "这些数字只是一个快照"
    一台机器、一个 IP、一个 Chrome build、一个时间点。你的会不同，检测站点也会改评分。把它当成方向（匹配的偏低，不匹配的跳高），而不是保证的结果。

完整的审计方法，读回一个信号、比较各个 realm，见 [审计一个 fingerprint](../deep-dive/fingerprinting/auditing.md)。

## 让一个 profile 通过 {#making-a-profile-pass}

一个 profile 能通过，是因为它和运行它的机器与 IP 相符。这些规则大多描述的是 `apply_fingerprint()` 触及不到的层，所以你要去匹配它，而不是硬碰。它们本质上是同一条规则：**每一层都要一致**。

### 让 profile 的 OS 匹配你的 host OS

内核的 TCP/IP 栈和 OS 的文本渲染，会在任何 override 都触及不到的层里暴露真实的 OS。在 Mac 上用 Windows profile 是一个矛盾，Cloudflare 会据此拦截，也正是上面把 bot score 推到 57 的那个不匹配。在 macOS 上跑 macOS profile，在 Windows 上跑 Windows profile。转发代理会从代理的内核重新发起 TCP 连接，所以 Windows profile 这时就需要一个跑在 Windows 上的代理。完整测量：[The OS must match the host](../deep-dive/fingerprinting/cloudflare-challenge.md#the-os-must-match-the-host)。

### 让 Chrome 版本匹配你的二进制

TLS 握手和 JavaScript 引擎会报告二进制的真实版本；User-Agent 是 `apply_fingerprint()` 唯一改动的部分。一个声称 Chrome 145 却跑在 Chrome 151 二进制上的 profile 是一个矛盾，也是应用 fingerprint 后 Turnstile 失败最常见的原因。读出二进制的版本，把 profile 的 `CHROME_DESKTOP` / `CHROME_MOBILE` 主版本号与之保持一致，并在每次 Chrome 升级时更新。

```python
version = await browser.get_version()
print(version['product'])  # 例如 'Chrome/151.0.7922.137'
```

完整拆解：[The Chrome version must match the binary](../deep-dive/fingerprinting/cloudflare-challenge.md#the-chrome-version-must-match-the-binary)。

### 让 locale 和时区匹配你的出口 IP

`Accept-Language`、`navigator.languages` 和时区会和 IP 所在国家做交叉核对。一个 US profile 在巴西 IP 后面，会让一次普通的 Google 搜索返回 captcha；改成巴西的 locale、和 IP 相符，就在不做任何其他改动的情况下解除了拦截。

<p align="center">
  <img src="/docs/resources/images/fingerprint-inconsistent-captcha.png" alt="Google 返回一个 captcha，因为注入的 fingerprint 的 US locale 与巴西出口 IP 矛盾" width="640" />
</p>
<p align="center"><sub>US locale 配巴西 IP：Google 返回一个 captcha。</sub></p>

### 覆盖 cross-origin iframes

保持 `cross_origin_iframes` 开启（默认），让在自己进程里的挑战或 captcha frame 读到注入的身份，而不是真实机器。它只作用于真正会读 fingerprint 的 frame，所以不会拖慢普通的第三方 iframe。

```python
# 默认：身份也覆盖 cross-origin iframes。
await tab.apply_fingerprint(FINGERPRINTS['macos_m3_new_york'])

# 关掉后只覆盖顶层页面、same-origin frame 和 workers。
await tab.apply_fingerprint(FINGERPRINTS['macos_m3_new_york'], cross_origin_iframes=False)
```

身份如何抵达每个 realm：[Workers and cross-origin iframes](../deep-dive/fingerprinting/execution-realms.md)。

### 每个 browser context 一个 fingerprint

service 和 shared workers 在一个 browser context 内共享，所以一个 context 持有一个身份。给已经有身份的同一个 context 再应用第二个 fingerprint，会抛出 `FingerprintContextConflict`。把不同身份放到各自独立的 context 里跑。

```python
ctx_id = await browser.create_browser_context()
tab_us = await browser.start()
tab_br = await browser.new_tab(browser_context_id=ctx_id)

await tab_us.apply_fingerprint(FINGERPRINTS['windows11_rtx3060_nyc'])
await tab_br.apply_fingerprint(FINGERPRINTS['android_s24_ultra_sao_paulo'])
```

见 [Browser contexts](../guides/browser-contexts.md)。

还有几条小规则：在第一次导航之前应用 fingerprint；不要把 `--user-agent` 选项和 `apply_fingerprint()` 一起用（User-Agent 由 profile 掌管）；让 WebGL 的 vendor/renderer 和 color-gamut 匹配 host 的 GPU 和显示器；用一个干净的住宅 IP。关于哪些信号可以安全覆盖、哪些根本无法伪造，见 [The limits of spoofing](../deep-dive/fingerprinting/spoofing-limits.md)。

## 使用你自己的 profile {#bring-your-own-profiles}

Pydoll 不生成也不附带 fingerprint。`examples/fingerprints.py` 里的 profile 是一份参考，说明一个 profile 需要怎样的一致性以及 `FingerprintConfig` 的结构，而不是一份可以原样部署的目录。一个 profile 必须匹配在用的 Chrome 二进制（网络层是真实的，无法覆盖）和出口 IP 的地理位置（locale、时区、地理定位）。一个被广泛复用的公开 profile，会变成共享签名，而不是伪装。

## 下一步

- [审计一个 fingerprint](../deep-dive/fingerprinting/auditing.md)：读回一个信号、比较各个 realm，确认一个 profile 生效了。
- [Cloudflare 的托管挑战](../deep-dive/fingerprinting/cloudflare-challenge.md)：按层拆解 headless 下什么能通过、为什么。
- [The limits of spoofing](../deep-dive/fingerprinting/spoofing-limits.md)：哪些信号可以安全覆盖，哪些无法伪造。
- [Workers and cross-origin iframes](../deep-dive/fingerprinting/execution-realms.md)：身份如何被复制到每个 realm。
- [Network fingerprinting](../deep-dive/fingerprinting/network-fingerprinting.md)：注入触及不到的 TLS/TCP/HTTP2 层。
- [Evasion techniques](evasion-techniques.md)：User-Agent 一致性、WebRTC 泄漏防护，以及 Pydoll 免费给你的东西。
