# 审计一个 fingerprint

你无法改进你无法测量的东西。一旦应用了一个 profile，问题就变成：现在哪些信号会被读作一个真实设备，哪些仍然在泄露，而无论你怎么读代码，都不如把一个检测器对准浏览器来得管用。本页讲的就是如何测量这一点，从一个免费的 bot score，到精确读取一个商业检测器所收集的内容。

它建立在 [伪造的极限](spoofing-limits.md) 之上：那一页解释了什么能被伪造、什么不能，这一页展示如何检查你的配置实际做到了什么。

## 读取 bot score

[fingerprint-scan.com](https://fingerprint-scan.com/) 会在页面内运行一项 fingerprinting 和机器人检测测试，并给出一个从 0 到 100 的得分，越低意味着越像人类。用 Pydoll 驱动它，并对结果截图：

```python
import asyncio
from pydoll.browser.chromium import Chrome
from examples.fingerprints import FINGERPRINTS

async def scan(profile):
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.apply_fingerprint(FINGERPRINTS[profile])
        await tab.go_to('https://fingerprint-scan.com/')
        await asyncio.sleep(15)          # let the score finish computing
        await tab.take_screenshot(f'{profile}.png')

asyncio.run(scan('macos_m3_new_york'))
```

这个数字本身意义不大。它的价值在于比较：在同一台机器上，分别在应用和不应用 profile 的情况下运行，以及用一个匹配的 profile 对比一个故意不匹配的 profile 来运行，然后对这些得分做差。这就是你如何把一次变化归因到某个具体信号，而不是靠猜。

最清楚的例子是 headless。在没有 profile 的情况下，headless Chrome 会拿到最高分：

<p align="center">
  <img src="/docs/resources/images/fp-scan-headless-nofp.png" alt="fingerprint-scan.com 显示没有 fingerprint 的 headless Chrome 的 bot score 为 100/100" width="720" />
</p>

应用一个匹配的 profile 后，同样的 headless 运行会降到 headful 的分数：

<p align="center">
  <img src="/docs/resources/images/fp-scan-headless-mac.png" alt="fingerprint-scan.com 显示应用了 macOS fingerprint 的 headless Chrome 的 bot score 为 15/100" width="720" />
</p>

!!! warning "一个 bot score 只是一个快照"
    一台机器、一个 IP、一个 Chrome 构建、一个时间点。检测网站也会改变它们的评分。请读一次变化把得分推向的*方向*，而不是那个绝对数值。

## 交叉验证那些谎言检测器

一个 bot score 只是一种意见。[CreepJS](https://abrahamjuliot.github.io/creepjs/) 是第二种、也是更严格的一种：它不只是读取每个信号，还会检查每个信号是如何被定义的，并在一个 Web Worker 内部把整个 fingerprint 再读一遍，然后把那些矛盾作为*谎言*报告出来。

那一趟 worker 检查正是一个幼稚的覆盖会失败的地方。CreepJS 会在页面中读取身份，再在一个 `WorkerNavigator` 中读取一次，那是一个主线程 hook 永远触及不到的独立 realm。如果页面说是 Windows，而 worker 说的是真实的 macOS，那个不一致就是谎言。一个被正确应用的 profile 会在两者中报告相同的身份：

<p align="center">
  <img src="/docs/resources/images/creepjs-worker-windows.png" alt="CreepJS 的 worker 面板重放注入的 Windows 身份：一个 Windows User-Agent、一颗 NVIDIA GeForce RTX 3060、Win32 和 Windows 11，全都在一台 Apple Mac 上的 service worker 内部" width="720" />
</p>

[SannySoft](https://bot.sannysoft.com/) 和 [BrowserScan](https://www.browserscan.net/bot-detection) 是针对 headless 和自动化标志的更快捷的检查。把它们当作一次快速过筛，而不是最终定论。

## 自己比较各条读取路径

最强的审计并不需要第三方网站。对于任何信号，用两种方式读取它并检查它们是否一致，因为一个不一致通常就是你自己的覆盖所制造出来的一处泄露：

```python
result = await tab.execute_script('''
    document.head.insertAdjacentHTML('beforeend',
        '<style>.probe{--g: srgb} @media (color-gamut: p3){.probe{--g: p3}}</style>');
    const probe = document.createElement('div');
    probe.className = 'probe';
    document.body.appendChild(probe);
    return {
        matchMedia: matchMedia('(color-gamut: p3)').matches ? 'p3' : 'srgb',
        css: getComputedStyle(probe).getPropertyValue('--g').trim(),
    };
''', return_by_value=True)
```

如果 `matchMedia` 和 CSS 路径不一致，那就是有一个覆盖只在一条路径上撒谎，也就是 [伪造的极限](spoofing-limits.md) 所讲解的那种失败模式。同样的测试也适用于跨 realm（页面对比 worker）以及跨 API（WebGL 字符串对比 WebGPU adapter）。一个连贯的 profile 会通过所有这些测试；而一个矛盾就是一个由你引入的信号。

## 读取一个真实检测器所收集的内容

最深入的审计，是不再去猜哪些信号重要，而是去读一个生产环境检测器实际读取的那份清单。这些代理发布时都经过了重度混淆，但它们所测量的那个面是公开的浏览器 API，所以它可以被逆向工程。

一次对 **Fingerprint Pro v4**（构建 `jsl/4.0.0`）的公开拆解，于 2026 年 8 月在一台机器上针对该厂商的公开演示租户进行测量，编目了大约 **143 个独立信号**，横跨屏幕与显示、硬件、`navigator`、GPU（WebGL 和 WebGPU）、音频、字体、媒体、存储以及自动化标志。这些数字是那个构建、那个租户、那个时刻所特有的，并不是一条普适定律，但其中有两个发现重塑了你审计的方式：

- **这个面的大部分并不能独自决定身份。** 在测试的那些运行中，把 canvas、WebGL、User-Agent、屏幕和 locale 一起改动，并不会独立地铸造出一个新访客；模糊匹配容忍了它。改变 canvas 的摘要确实让所报告的置信度发生了移动，从大约 0.99 降到 0.97，但并没有铸造出一个新的 id。所以大部分伪造精力在身份上都是浪费的。
- **最强的那个身份信号并不是一个 fingerprint。** 它是一个 bearer token，`s56`，由租户在代理的初始 GET 上签发，而客户端会在每一次 POST 上重放它。一旦它被绑定，无论 canvas、GPU 还是 User-Agent 是什么，这个负载都会以那个访客的身份来应答。

!!! note "身份是一个会话令牌问题，而不是一个 fingerprint 问题"
    要以一个新访客的身份出现，就从一个干净的 [浏览器上下文](../../guides/browser-contexts.md) 开始，这样就不会重放任何先前的 `s56` token，代理会签发一个新的。要持久保持一个身份，就复用这个 context，这样同一个 token 会再次回来。在这次拆解中，伪造 canvas、WebGL 和 User-Agent 并不会独立地改变访客 id，所以那份精力更应该花在连贯性上，而不是花在一个新身份上。出口 IP 被排除在身份分析之外；它供给的是一个单独的机器人和 proxy 信号，所以单单轮换 IP，并不会改变 token 所说的你是谁。

## 捕获代理所发送的内容

!!! warning "小心处理捕获到的负载"
    一个捕获到的负载会携带会话令牌、存储标识符、你的 IP 以及其他能识别你的数据。只针对一个你有授权去测试的网站进行捕获，在一个你可以丢弃的一次性身份下运行它，并在你把这个负载存储、分享或粘贴到任何地方之前，先把其中的令牌、存储 id 和 IP 抹去。

代理不只是读取那些信号，它还会把它们打包并 POST 到它的服务器，而那个负载是可读的。一个典型的代理会把信号序列化为 JSON，编码成一种紧凑的字节形式，用 raw DEFLATE 压缩任何超过大约一千字节的部分，再把结果包进一个带帧的信封里，而它的密钥就随着帧一起传输。最后那一步是混淆，而不是加密；并没有什么你所缺失的秘密。

所以最深入的审计就是一次捕获。用 [请求拦截](../../guides/request-interception.md) 抓取代理那次 POST 的 body，把帧还原，再把它解压。出来的东西就是检测器为你的会话所构建的那个确切的信号集合，直接从给你打分的代码里读出来。对于你的哪些覆盖站住了、哪些泄露了，这就是那个基准真相，而且它比任何 bot score 都更可靠，因为它是那个得分的输入，而不是输出。

## 相关

- [伪造的极限](spoofing-limits.md)：一次伪造能改动什么、不能改动什么。
- [Fingerprint 注入](../../stealth/fingerprint-injection.md)：应用一个连贯的 profile。
- [浏览器上下文](../../guides/browser-contexts.md)：每个 context 一个身份，也就是获得一个全新访客的真正杠杆。
