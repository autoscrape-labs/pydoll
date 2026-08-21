# Migrating from Selenium and Playwright

If you already automate browsers, most of what you know carries over. This page maps the moves you use every day to their Pydoll equivalents, and points out where Pydoll works differently.

Three things change no matter which tool you come from:

- **No webdriver or bundled browser.** Pydoll drives the Chrome or Edge already on your machine over the DevTools Protocol. There is no `chromedriver` to install or version-match.
- **No explicit waits.** `find()` and `query()` wait for the element themselves, so the `WebDriverWait` and `expected_conditions` dance goes away.
- **Async by default.** Every call is `await`ed inside an `async def`, started with `asyncio.run()`. New to that? See [Async Python in practice](basics/async-python.md).

## From Selenium

| Task | Selenium | Pydoll |
|------|----------|--------|
| Launch | `driver = webdriver.Chrome()` | `async with Chrome() as browser: tab = await browser.start()` |
| Open a URL | `driver.get(url)` | `await tab.go_to(url)` |
| Find by id | `driver.find_element(By.ID, 'q')` | `await tab.find(id='q')` |
| Find by CSS | `driver.find_element(By.CSS_SELECTOR, '.item')` | `await tab.query('.item')` |
| Find by XPath | `driver.find_element(By.XPATH, '//a')` | `await tab.query('//a')` |
| Find by text | `driver.find_element(By.XPATH, "//*[text()='Login']")` | `await tab.find(text='Login')` |
| Find many | `driver.find_elements(By.CSS_SELECTOR, '.item')` | `await tab.query('.item', find_all=True)` |
| Wait for an element | `WebDriverWait(driver, 10).until(EC.presence_of_element_located(...))` | `await tab.find(id='q', timeout=10)` |
| Click | `el.click()` | `await el.click()` |
| Type | `el.send_keys('text')` | `await el.type_text('text')` |
| Press a key | `el.send_keys(Keys.ENTER)` | `await tab.keyboard.press(Key.ENTER)` |
| Read text | `el.text` | `await el.text` |
| Read an attribute | `el.get_attribute('href')` | `el.get_attribute('href')` |
| Screenshot | `driver.save_screenshot('s.png')` | `await tab.take_screenshot('s.png')` |
| Run JavaScript | `driver.execute_script('return document.title')` | `await tab.execute_script('return document.title')` |
| Quit | `driver.quit()` | leave the `async with` block, or `await browser.stop()` |

A Selenium login flow and its Pydoll version:

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

!!! note "`get_attribute` is synchronous"
    Unlike Selenium, where everything on the element is a network round-trip, Pydoll reads attributes from the element it already located, so `get_attribute()` is a plain method with no `await`. Text is still awaited (`await el.text`).

## From Playwright

| Task | Playwright | Pydoll |
|------|------------|--------|
| Launch | `browser = await p.chromium.launch(); page = await browser.new_page()` | `async with Chrome() as browser: tab = await browser.start()` |
| Open a URL | `await page.goto(url)` | `await tab.go_to(url)` |
| Find by CSS | `page.locator('.item')` | `await tab.query('.item')` |
| Find by text | `page.get_by_text('Login')` | `await tab.find(text='Login')` |
| Find by role/label | `page.get_by_role('button')` | `await tab.find(tag_name='button')` |
| Find many | `page.locator('.item').all()` | `await tab.query('.item', find_all=True)` |
| Click | `await page.locator('.btn').click()` | `await (await tab.find(class_name='btn')).click()` |
| Fill an input | `await page.fill('#q', 'text')` | `await (await tab.find(id='q')).type_text('text')` |
| Read text | `await page.locator('.title').text_content()` | `await (await tab.find(class_name='title')).text` |
| Read an attribute | `await loc.get_attribute('href')` | `el.get_attribute('href')` |
| New tab | `await context.new_page()` | `await browser.new_tab()` |
| Screenshot | `await page.screenshot(path='s.png')` | `await tab.take_screenshot('s.png')` |
| Close | `await browser.close()` | leave the `async with` block, or `await browser.stop()` |

Both are async and both auto-wait, so migration is mostly renaming. The main conceptual difference is what a lookup returns:

- A Playwright **locator** is lazy: it re-resolves the element every time you act on it.
- A Pydoll `find()` / `query()` returns a **`WebElement`** resolved once, then and there. Call `find()` again if the page replaced the element.

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

!!! tip "Behavior you keep from Playwright, and one you gain"
    Auto-waiting and async carry over directly. What Pydoll adds is `humanize=True` on clicks and typing, which moves the cursor along a curved path and types with variable timing. See [Human-like interactions](stealth/human-like-interactions.md).

## What's next

- [Your first automation](first-automation.md): a full flow, from login to typed extraction.
- [Element finding](guides/element-finding.md): every way to locate elements in Pydoll.
- [Staying undetected](stealth/index.md): the anti-bot story, if that's why you're switching.
