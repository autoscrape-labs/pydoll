# 你的第一个自动化

真正的自动化不只是加载一个页面：你要填写表单、点击按钮、等待页面响应，并收集数据。在本页中，你将针对 [quotes.toscrape.com](https://quotes.toscrape.com)（一个专门用于练习抓取的站点）构建一个完整的流程：登录、确认登录成功，并把每一条名言提取为一个类型化对象。

**你将学到**

- [如何像真人一样填写表单并登录](#log-in-like-a-person)
- [如何确认页面已经响应](#confirm-the-login-worked)
- [如何用模型提取类型化数据](#extract-typed-data)
- [完整脚本长什么样](#the-full-script)

## 像真人一样登录 {#log-in-like-a-person}

`find()` 通过元素的属性定位它们，`type_text(humanize=True)` 以真实用户的可变节奏打字，其中包括偶尔出现并被修正的拼写错误。你无需先聚焦输入框；Pydoll 会在打字前先点击它。

```python
await tab.go_to('https://quotes.toscrape.com/login')

username = await tab.find(id='username')
await username.type_text('john', humanize=True)

password = await tab.find(id='password')
await password.type_text('SecretPass123', humanize=True)

submit = await tab.find(tag_name='input', type='submit')
await submit.click()
```

这个站点上的登录表单接受任意用户名和密码，所以这些值只需要看起来真实即可。

## 确认登录成功 {#confirm-the-login-worked}

提交后，页面会重新加载并显示一个 Logout 链接。找到那个链接就是你的确认依据。`find()` 会等待它出现，因此在点击和检查之间不需要 sleep：

```python
logout_link = await tab.find(text='Logout', timeout=5, raise_exc=False)
if logout_link:
    print('Logged in.')
else:
    print('Login failed.')
```

`raise_exc=False` 让 `find()` 在元素始终没有出现时返回 `None` 而不是抛出异常，从而把控制流保留在你手中。

## 提取类型化数据 {#extract-typed-data}

会话激活后，从交互切换到收集。只需一次声明一条名言长什么样，`extract_all()` 就会返回一组经过校验的对象：

```python
from pydoll.extractor import ExtractionModel, Field


class Quote(ExtractionModel):
    text: str = Field(selector='.text')
    author: str = Field(selector='.author')
    tags: list[str] = Field(selector='.tag')


quotes = await tab.extract_all(Quote, scope='.quote', timeout=5)

for quote in quotes:
    print(f'{quote.author}: {quote.text}')
    print(f'  tags: {", ".join(quote.tags)}')
```

每个 `quote` 都是一个真正的 Pydantic 对象：`quote.tags` 是一个 `list[str]`，你的 IDE 会自动补全字段，`quote.model_dump_json()` 会将它序列化。无需逐个元素查询，也无需手动类型转换。

## 完整脚本 {#the-full-script}

<iframe scrolling="no" src="/docs/resources/visuals/first-automation.html" aria-label="A read-along walkthrough of the first automation script: each line highlights as it runs while a browser window launches, navigates, finds elements, types, clicks, and extracts typed data" style="width: 100%; height: 860px; border: 0;" loading="lazy"></iframe>

创建 `first_automation.py`：

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

        await tab.go_to('https://quotes.toscrape.com/login')

        username = await tab.find(id='username')
        await username.type_text('john', humanize=True)

        password = await tab.find(id='password')
        await password.type_text('SecretPass123', humanize=True)

        submit = await tab.find(tag_name='input', type='submit')
        await submit.click()

        logout_link = await tab.find(text='Logout', timeout=5, raise_exc=False)
        if not logout_link:
            print('Login failed.')
            return

        quotes = await tab.extract_all(Quote, scope='.quote', timeout=5)
        for quote in quotes:
            print(f'{quote.author}: {quote.text}')

asyncio.run(main())
```

运行它：

```bash
python first_automation.py
```

你会看到浏览器输入凭据、登录，随后你的终端被作者和名言填满。

## 下一步

- [保持不被检测](stealth/index.md)：这段旅程的下一步，让你的自动化不像自动化。
- [元素查找](guides/element-finding.md)：`find()` 和 `query()` 支持的每一个属性、选择器和策略。
- [结构化提取](guides/structured-extraction.md)：属性、转换和嵌套模型。
