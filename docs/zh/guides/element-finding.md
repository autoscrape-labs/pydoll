# 查找元素

定位元素是一切自动化的基础。Pydoll 提供了两种方式：`find()`，通过 HTML 属性来描述元素；`query()`，直接传入 CSS 选择器或 XPath。两者都会等待元素出现，因此你永远不用手写 `sleep` 循环。

编辑下面的属性，实时观察 `find()` 如何定位元素。Pydoll 会把你传入的属性转换成选择器，匹配到的元素会高亮显示。

<iframe src="/docs/resources/visuals/element-find-playground.html" aria-label="Edit find() attributes and see which element it locates" style="width: 100%; height: 365px; border: 0;" loading="lazy"></iframe>

## 通过属性查找

`find()` 是日常首选工具。你像向别人描述元素那样传入属性，Pydoll 会为你构建选择器。

```python
import asyncio

from pydoll.browser.chromium import Chrome


async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://quotes.toscrape.com')

        quote = await tab.find(class_name='quote')
        text = await quote.find(class_name='text')
        author = await quote.find(class_name='author')
        print(f'{await author.text}: {await text.text}')

asyncio.run(main())
```

你可以通过下列任意属性来定位元素。每一种都返回第一个匹配项：

```python
await tab.find(id='username')        # 通过 id
await tab.find(class_name='quote')   # 通过 class 名
await tab.find(tag_name='h1')        # 通过标签名
await tab.find(name='username')      # 通过 name 属性
await tab.find(text='Login')         # 通过可见文本
```

## 组合属性以提高精度

传入多个属性时，`find()` 会匹配**同时**具备所有这些属性的元素（即 AND 关系）。对带连字符的属性名使用下划线：`data-testid` 写成 `data_testid`，`aria-label` 写成 `aria_label`。

```python
# 一个 <input type="password" name="password">
password = await tab.find(tag_name='input', type='password', name='password')

# 一个 <button class="btn" type="submit">
submit = await tab.find(tag_name='button', class_name='btn', type='submit')

# 一个 data 属性
card = await tab.find(tag_name='div', data_testid='product-card')
```

要实现 OR 逻辑（元素可能有这个属性，也可能有那个属性），用 `raise_exc=False` 串联两次调用，参见[处理缺失的元素](#handle-missing-elements)。

## 查找所有匹配项

传入 `find_all=True`，即可得到所有匹配元素组成的列表，而不只是第一个：

```python
await tab.go_to('https://books.toscrape.com')

books = await tab.find(class_name='product_pod', find_all=True)
print(f'{len(books)} books on this page')

for book in books:
    title = await book.find(tag_name='h3')
    price = await book.find(class_name='price_color')
    print(await title.text, await price.text)
```

## 等待延迟加载的元素

现代页面会在初次加载之后再渲染内容。传入 `timeout`（单位为秒），`find()` 会轮询直到元素出现或时间耗尽。你不用添加 `sleep` 调用，等待是内置的。

```python
# 最多等待 10 秒，等一个延迟加载的元素出现
content = await tab.find(class_name='dynamic-content', timeout=10)
```

!!! tip "有意识地选择 timeout"
    太短会错过加载慢的元素；太长则会在永远不会出现的东西上白等。五到十秒适用于大多数动态内容。对于只是偶尔存在的元素，用较短的 timeout 搭配 `raise_exc=False`（见下文）。

## 通过 CSS 选择器或 XPath 查找

当你已经有了选择器，或者需要 `find()` 无法表达的层级关系时，使用 `query()`。它会自动识别 CSS 还是 XPath。

```python
# CSS
submit = await tab.query("button[type='submit']")
required = await tab.query('input[required]', find_all=True)
nested = await tab.query('div.container > .content .item:nth-child(2)')

# XPath：CSS 无法实现的文本匹配和层级关系
button = await tab.query("//button[contains(text(), 'Submit')]")
label_input = await tab.query("//label[text()='Email:']/following-sibling::input")
```

`query()` 接受与 `find()` 相同的 `find_all`、`timeout` 和 `raise_exc` 参数。关于何时选用 CSS、何时选用 XPath，参见[选择器：CSS 和 XPath](../basics/selectors.md)。

## 在元素内部搜索

每个元素都支持限定在自身子树内的 `find()` 和 `query()`，这正是处理卡片、行等重复结构的方式。限定范围的搜索会查找该元素的**所有**后代，而不仅仅是直接子元素，这与 `querySelector` 的行为一致。

```python
await tab.go_to('https://books.toscrape.com')

book = await tab.find(class_name='product_pod')

title = await book.find(tag_name='h3')          # 这本书内部的任意位置
price = await book.find(class_name='price_color')
cover = await book.query('img.thumbnail')
```

要有意识地在 DOM 树中导航（仅直接子元素、兄弟元素、shadow 根），参见 [DOM 遍历](dom-traversal.md)。

## 处理缺失的元素 {#handle-missing-elements}

默认情况下，当没有匹配项时 `find()` 会抛出 `ElementNotFound`。传入 `raise_exc=False` 则改为返回 `None`，把可选元素和 OR 逻辑的控制权交给你。

```python
from pydoll.exceptions import ElementNotFound

# 必需的元素：让它抛出异常
submit = await tab.find(id='submit')

# 可选的元素：处理 None
banner = await tab.find(class_name='promo-banner', timeout=2, raise_exc=False)
if banner:
    close = await banner.find(class_name='close')
    await close.click()

# OR 逻辑：先试一个属性，再试另一个
checkbox = (
    await tab.find(id='terms', raise_exc=False)
    or await tab.find(name='accept_terms', raise_exc=False)
)
```

## 优先选择稳定的选择器

选择那些不太可能因为改版而变动的属性。DOM 结构经常变化，因此依赖结构的选择器很容易失效。

```python
# 语义化且稳定：能挺过改版
await tab.find(id='user-profile')
await tab.find(data_testid='submit-button')
await tab.find(name='username')

# 依附于结构：布局一变就失效
await tab.query('div > div > div:nth-child(3) > input')
```

选用能奏效的最简单选择器，只有当页面逼你这么做时才增加复杂度。对基于属性的查找用 `find()`，对 `find()` 无法表达的 CSS 或 XPath 模式用 `query()`。

## 完整示例：登录并读取结果

下面这段代码在 [quotes.toscrape.com](https://quotes.toscrape.com/login)（接受任意凭据）上登录，并通过找到 Logout 链接来确认结果。

```python
import asyncio

from pydoll.browser.chromium import Chrome


async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://quotes.toscrape.com/login')

        username = await tab.find(id='username')
        await username.type_text('tester', humanize=True)

        password = await tab.find(id='password')
        await password.type_text('secret', humanize=True)

        submit = await tab.find(tag_name='input', type='submit')
        await submit.click()

        logout = await tab.find(text='Logout', timeout=5, raise_exc=False)
        print('Logged in.' if logout else 'Login failed.')

asyncio.run(main())
```

## 下一步

- [DOM 遍历](dom-traversal.md)：从一个元素导航到它的子元素、兄弟元素和 shadow 根。
- [选择器：CSS 和 XPath](../basics/selectors.md)：挑选并写出正确的选择器。
- [结构化提取](structured-extraction.md)：用一个模型一次性从多个元素中拉取带类型的数据。
