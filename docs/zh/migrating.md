# 从 Selenium 和 Playwright 迁移

如果你已经在做浏览器自动化，你所掌握的大部分内容都可以沿用。本页把你每天使用的操作对应到它们的 Pydoll 等价写法，并指出 Pydoll 在哪些地方工作方式不同。

无论你从哪个工具而来，有三件事都会改变：

- **没有 webdriver 或捆绑的浏览器。** Pydoll 通过 DevTools Protocol 驱动你机器上已有的 Chrome 或 Edge。没有需要安装或版本匹配的 `chromedriver`。
- **没有显式等待。** `find()` 和 `query()` 自己等待元素，所以 `WebDriverWait` 和 `expected_conditions` 那一套繁琐操作就没有了。
- **默认异步。** 每个调用都在 `async def` 内部被 `await`，并由 `asyncio.run()` 启动。第一次接触？见 [实践中的异步 Python](basics/async-python.md)。

## 从 Selenium 迁移

| 任务 | Selenium | Pydoll |
|------|----------|--------|
| 启动 | `driver = webdriver.Chrome()` | `async with Chrome() as browser: tab = await browser.start()` |
| 打开一个 URL | `driver.get(url)` | `await tab.go_to(url)` |
| 按 id 查找 | `driver.find_element(By.ID, 'q')` | `await tab.find(id='q')` |
| 按 CSS 查找 | `driver.find_element(By.CSS_SELECTOR, '.item')` | `await tab.query('.item')` |
| 按 XPath 查找 | `driver.find_element(By.XPATH, '//a')` | `await tab.query('//a')` |
| 按文本查找 | `driver.find_element(By.XPATH, "//*[text()='Login']")` | `await tab.find(text='Login')` |
| 查找多个 | `driver.find_elements(By.CSS_SELECTOR, '.item')` | `await tab.query('.item', find_all=True)` |
| 等待某个元素 | `WebDriverWait(driver, 10).until(EC.presence_of_element_located(...))` | `await tab.find(id='q', timeout=10)` |
| 点击 | `el.click()` | `await el.click()` |
| 输入 | `el.send_keys('text')` | `await el.type_text('text')` |
| 按一个键 | `el.send_keys(Keys.ENTER)` | `await tab.keyboard.press(Key.ENTER)` |
| 读取文本 | `el.text` | `await el.text` |
| 读取一个属性 | `el.get_attribute('href')` | `el.get_attribute('href')` |
| 截图 | `driver.save_screenshot('s.png')` | `await tab.take_screenshot('s.png')` |
| 运行 JavaScript | `driver.execute_script('return document.title')` | `await tab.execute_script('return document.title')` |
| 退出 | `driver.quit()` | 离开 `async with` 代码块，或 `await browser.stop()` |

一个 Selenium 登录流程及其 Pydoll 版本：

```python
# Selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

driver = webdriver.Chrome()
driver.get('https://quotes.toscrape.com/login')
driver.find_element(By.ID, 'username').send_keys('tester')
driver.find_element(By.ID, 'password').send_keys('secret')
driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()
WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.LINK_TEXT, 'Logout')))
driver.quit()
```

```python
# Pydoll
import asyncio

from pydoll.browser.chromium import Chrome


async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://quotes.toscrape.com/login')

        await (await tab.find(id='username')).type_text('tester')
        await (await tab.find(id='password')).type_text('secret')
        await (await tab.find(tag_name='input', type='submit')).click()

        await tab.find(text='Logout', timeout=5)

asyncio.run(main())
```

!!! note "`get_attribute` 是同步的"
    与 Selenium 不同（在 Selenium 中，元素上的一切都是一次网络往返），Pydoll 从它已经定位到的元素上读取属性，所以 `get_attribute()` 是一个普通方法，无需 `await`。文本仍然需要 await（`await el.text`）。

## 从 Playwright 迁移

| 任务 | Playwright | Pydoll |
|------|------------|--------|
| 启动 | `browser = await p.chromium.launch(); page = await browser.new_page()` | `async with Chrome() as browser: tab = await browser.start()` |
| 打开一个 URL | `await page.goto(url)` | `await tab.go_to(url)` |
| 按 CSS 查找 | `page.locator('.item')` | `await tab.query('.item')` |
| 按文本查找 | `page.get_by_text('Login')` | `await tab.find(text='Login')` |
| 按 role/label 查找 | `page.get_by_role('button')` | `await tab.find(tag_name='button')` |
| 查找多个 | `page.locator('.item').all()` | `await tab.query('.item', find_all=True)` |
| 点击 | `await page.locator('.btn').click()` | `await (await tab.find(class_name='btn')).click()` |
| 填写一个输入框 | `await page.fill('#q', 'text')` | `await (await tab.find(id='q')).type_text('text')` |
| 读取文本 | `await page.locator('.title').text_content()` | `await (await tab.find(class_name='title')).text` |
| 读取一个属性 | `await loc.get_attribute('href')` | `el.get_attribute('href')` |
| 新建标签页 | `await context.new_page()` | `await browser.new_tab()` |
| 截图 | `await page.screenshot(path='s.png')` | `await tab.take_screenshot('s.png')` |
| 关闭 | `await browser.close()` | 离开 `async with` 代码块，或 `await browser.stop()` |

两者都是异步的，也都会自动等待，所以迁移大多只是重命名。主要的概念差异在于一次查找返回的是什么：

- Playwright 的 **locator** 是惰性的：每次你对它进行操作时，它都会重新解析元素。
- Pydoll 的 `find()` / `query()` 返回一个当场解析一次的 **`WebElement`**。如果页面替换了该元素，就再次调用 `find()`。

```python
# Playwright
from playwright.async_api import async_playwright

async with async_playwright() as p:
    browser = await p.chromium.launch()
    page = await browser.new_page()
    await page.goto('https://quotes.toscrape.com')
    quote = await page.locator('.quote .text').first.text_content()
    print(quote)
    await browser.close()
```

```python
# Pydoll
import asyncio

from pydoll.browser.chromium import Chrome


async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://quotes.toscrape.com')

        quote = await tab.query('.quote .text')
        print(await quote.text)

asyncio.run(main())
```

!!! tip "你从 Playwright 保留的行为，以及新获得的一个"
    自动等待和异步会直接沿用过来。Pydoll 新增的是点击和打字上的 `humanize=True`，它让光标沿着弯曲的轨迹移动，并以可变的节奏打字。见 [拟人化交互](stealth/human-like-interactions.md)。

## 下一步

- [你的第一个自动化](first-automation.md)：一个完整流程，从登录到类型化提取。
- [元素查找](guides/element-finding.md)：在 Pydoll 中定位元素的每一种方式。
- [保持不被检测](stealth/index.md)：反机器人方面的介绍，如果这是你切换的原因。
