<p align="center">
    <img src="/docs/resources/images/logo.png" alt="Pydoll Logo" /> <br><br>
</p>

# Pydoll

Pydoll 通过 Chrome DevTools Protocol 自动化 Chromium 浏览器，无需 webdriver，也无需手动等待。用它来抓取数据、测试 Web 应用，以及在异步 Python 中自动化真实的浏览器工作流。

## 安装

<div class="termy">
```bash
$ pip install pydoll-python

---> 100%
```
</div>

Pydoll 驱动你机器上已安装的 Chrome 或 Edge。你无需下载 webdriver，也无需让 driver 版本与浏览器保持同步。

第一次使用 Pydoll？跟随 [快速开始](getting-started.md) 完成一次完整的上手演练。

## 快速上手

打开一个页面，用你向别人描述元素的方式来查找它们，并以拟人化的节奏进行交互：

```python
import asyncio

from pydoll.browser.chromium import Chrome


async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://github.com/autoscrape-labs/pydoll')

        star_button = await tab.find(
            tag_name='button',
            timeout=5,
            raise_exc=False
        )
        if not star_button:
            print('Button not found.')
            return

        await star_button.click()
        await asyncio.sleep(3)

asyncio.run(main())
```

当目标是数据而非交互时，定义一个模型，让 Pydoll 提取它，并完成类型标注与校验：

```python
import asyncio

from pydoll.browser.chromium import Chrome
from pydoll.extractor import ExtractionModel, Field


class Quote(ExtractionModel):
    text: str = Field(selector='.text')
    author: str = Field(selector='.author')
    tags: list[str] = Field(selector='.tag')


async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://quotes.toscrape.com')

        quotes = await tab.extract_all(Quote, scope='.quote', timeout=5)
        for quote in quotes:
            print(f'{quote.author}: {quote.text}')

asyncio.run(main())
```

模型支持 CSS 和 XPath 选择器、HTML 属性定位、自定义转换以及嵌套模型。更多内容见 [结构化提取](guides/structured-extraction.md)。

## 为什么选择 Pydoll

- **无需 webdriver**：Pydoll 通过 Chrome DevTools Protocol 直接连接浏览器。没有需要下载的东西，也没有版本不匹配需要排查。
- **拟人化交互**：点击沿着弯曲的鼠标轨迹移动，打字带有可变的节奏并偶尔出现随即被修正的拼写错误，因此你的自动化表现得像一个真人在键盘前操作。
- **异步为本**：基于 `asyncio` 构建，因此一个进程可以并发驱动多个标签页和浏览器。
- **Cloudflare Turnstile 处理**：Pydoll 检测 Turnstile 组件并原生点击它。无需付费或集成外部 captcha 服务。
- **网络控制**：在页面发起请求时监控、拦截并修改它们。
- **类型化提取**：声明一个 Pydantic 模型，得到经过校验、对 IDE 友好的对象，而不是原始元素。

## 下一步

- [快速开始](getting-started.md)：安装 Pydoll 并运行你的第一个脚本。
- [你的第一个自动化](first-automation.md)：登录站点并提取类型化数据。
- [从 Selenium 和 Playwright 迁移](migrating.md)：把你已经掌握的操作对应到 Pydoll。
- [保持不被检测](stealth/index.md)：避开明显机器人信号的最小配置。
- [指南](guides/index.md)：每种能力一篇指南，从元素查找到请求拦截。
- [API 参考](api/index.md)：每一个公开类和方法。

## Top Sponsors

<div class="sponsor-grid-top">
  <a class="sponsor-card" href="http://serpapi.com/?utm_source=github_sponsorship&utm_campaign=pydoll" target="_blank" rel="noopener nofollow sponsored">
    <span class="sponsor-banner sponsor-banner--serpapi"><img src="/docs/resources/images/serp-api-banner.png" alt="SerpApi" /></span>
    <span class="sponsor-body">
      <span class="sponsor-name">SerpApi</span>
      <span class="sponsor-desc">面向 AI 应用的 Web Search API。提供 Markdown 和 JSON，适配任意集成。</span>
    </span>
  </a>
  <a class="sponsor-card" href="https://www.ipcook.com/?ref=16NLS&utm_source=github&utm_medium=referral&utm_campaign=pydoll" target="_blank" rel="noopener nofollow sponsored">
    <span class="sponsor-banner sponsor-banner--ipcook"><img src="/docs/resources/images/ipcook-banner.png" alt="IPCook" /></span>
    <span class="sponsor-body">
      <span class="sponsor-name">IPCook</span>
      <span class="sponsor-desc">面向隐身浏览器自动化的住宅代理：覆盖 185+ 地区的 5500 万+ IP，99.99% 可用率，平均响应低于 0.5 秒。</span>
      <span class="sponsor-chips">
        <span class="sponsor-chip"><code>WELCOME20</code> 20% 折扣</span>
      </span>
    </span>
  </a>
  <a class="sponsor-card" href="https://substack.thewebscraping.club/p/pydoll-webdriver-scraping?utm_source=github&utm_medium=repo&utm_campaign=pydoll" target="_blank" rel="noopener nofollow sponsored">
    <span class="sponsor-banner"><img src="/docs/resources/images/banner-the-webscraping-club.png" alt="The Web Scraping Club" /></span>
    <span class="sponsor-body">
      <span class="sponsor-name">The Web Scraping Club</span>
      <span class="sponsor-desc">The #1 newsletter dedicated to web scraping. Read their full review of Pydoll.</span>
    </span>
  </a>
  <a class="sponsor-card" href="https://go.nodemaven.com/pydollaugust" target="_blank" rel="noopener nofollow sponsored">
    <span class="sponsor-banner"><img src="/docs/resources/images/nodemaven-banner.png" alt="NodeMaven" /></span>
    <span class="sponsor-body">
      <span class="sponsor-name">NodeMaven</span>
      <span class="sponsor-desc">High-quality proxies for scraping and automation. ZIP targeting, 99.9% uptime, no KYC.</span>
      <span class="sponsor-chips">
        <span class="sponsor-chip"><code>PYDOLL35</code> 35% off</span>
        <span class="sponsor-chip"><code>PYDOLL40</code> 40% off ISP</span>
      </span>
    </span>
  </a>
  <a class="sponsor-card" href="https://niuproxy.com/?utm_source=pydoll&utm_medium=pydoll&ref=pydoll" target="_blank" rel="noopener nofollow sponsored">
    <span class="sponsor-banner sponsor-banner--niuproxy"><img src="/docs/resources/images/niuproxy-banner.jpg" alt="NiuProxy" /></span>
    <span class="sponsor-body">
      <span class="sponsor-name">NiuProxy</span>
      <span class="sponsor-desc">Rotating residential proxies: 10TB at $0.35/GB or 1TB at $0.50/GB for Pydoll users.</span>
      <span class="sponsor-chips">
        <span class="sponsor-chip"><code>PAY2</code> 10% off recharge</span>
      </span>
    </span>
  </a>
</div>

## Sponsors

赞助商让项目得以持续运转，并帮助资助后续开发。感谢每一位支持 Pydoll 的人。

<div class="sponsor-grid-mini">
  <a class="sponsor-card sponsor-tile" href="https://proxy-seller.com/?partner=8DES01TZ1QGWR3" target="_blank" rel="noopener nofollow sponsored">
    <span class="sponsor-tile-logo"><img src="/docs/resources/images/proxy-seller-logo-white.svg" alt="Proxy-Seller" /></span>
    <span class="sponsor-desc">Premium proxies for AI agents, scraping &amp; automation</span>
    <span class="sponsor-chip"><code>PYDOLL</code> 15% off</span>
  </a>
  <a class="sponsor-card sponsor-tile" href="https://www.thordata.com/?ls=github&lk=pydoll" target="_blank" rel="noopener nofollow sponsored">
    <span class="sponsor-tile-logo"><img src="/docs/resources/images/Thordata-logo.png" alt="Thordata" /></span>
    <span class="sponsor-desc">Residential proxy network with 190+ locations</span>
    <span class="sponsor-desc"><b>1GB free</b> via our link</span>
  </a>
  <a class="sponsor-card sponsor-tile" href="https://www.testmuai.com/?utm_medium=sponsor&utm_source=pydoll" target="_blank" rel="noopener nofollow sponsored">
    <span class="sponsor-tile-logo"><img src="/docs/resources/images/logo-lamda-test.svg" alt="TestMu AI by LambdaTest" /></span>
    <span class="sponsor-desc">AI-native testing cloud by LambdaTest</span>
  </a>
  <a class="sponsor-card sponsor-tile" href="https://www.swiftproxy.net/?ref=pydoll" target="_blank" rel="noopener nofollow sponsored">
    <span class="sponsor-tile-logo"><img src="/docs/resources/images/swiftproxy-logo.png" alt="Swiftproxy" /></span>
    <span class="sponsor-desc">Proxies for web scraping &amp; automation</span>
  </a>
  <a class="sponsor-card sponsor-tile sponsor-tile--ghost" href="https://github.com/sponsors/thalissonvs" target="_blank" rel="noopener">
    <span class="sponsor-ghost-plus">+</span>
    <span class="sponsor-name">Your logo here</span>
    <span class="sponsor-desc">Become a sponsor</span>
  </a>
</div>

<p>
  <a class="sponsor-cta" href="https://github.com/sponsors/thalissonvs" target="_blank" rel="noopener">&#10084;&#65039; Become a sponsor</a>
</p>

## 许可证

Pydoll 以 [MIT License](https://github.com/autoscrape-labs/pydoll/blob/main/LICENSE) 发布，因此你可以在个人和商业项目中自由使用它。
