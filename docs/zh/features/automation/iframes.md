# 处理 IFrame

现代网页经常使用 `<iframe>` 嵌入其他文档。旧版本的 Pydoll 需要手动调用 `tab.get_frame()` 把 iframe 转成 `Tab` 并管理 CDP target。**现在不再需要这样做。**  
iframe 现在和其他 `WebElement` 一样：可以直接调用 `find()`、`query()`、`execute_script()`、`inner_html`、`text` 等方法，Pydoll 会自动在正确的浏览上下文中执行（无论是否跨域）。

!!! info "更轻松的心智模型"
    把 iframe 当成页面上的普通 `div`。找到它后，就以它为起点继续查找内部元素。Pydoll 会自动创建隔离执行环境，缓存上下文，并处理多层嵌套。

## 快速入门

### 与页面上的第一个 iframe 交互

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def interact_with_iframe():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/page-with-iframe')

        iframe = await tab.find(tag_name='iframe', id='content-frame')

        # 以下调用都会在 iframe 内部执行
        title = await iframe.find(tag_name='h1')
        await title.click()

        form = await iframe.find(id='login-form')
        username = await form.find(name='username')
        await username.type_text('john_doe')

asyncio.run(interact_with_iframe())
```

### 多层 iframe

逐层查找即可：

```python
outer = await tab.find(id='outer-frame')
inner = await outer.find(tag_name='iframe')  # 在外层 iframe 内继续查找

submit_button = await inner.find(id='submit')
await submit_button.click()
```

流程始终相同：

1. 找到需要的 iframe 元素。
2. 使用该 `WebElement` 作为新的查找范围。
3. 如果还有内层 iframe，重复以上步骤。

### 在 iframe 中执行 JavaScript

```python
iframe = await tab.find(tag_name='iframe')
result = await iframe.execute_script('return document.title', return_by_value=True)
print(result['result']['result']['value'])
```

Pydoll 会自动在 iframe 的隔离上下文中执行脚本，同样适用于跨域 iframe。

## 为什么这样更好？

- **直观：** DOM 树是什么样子，就怎么编写脚本。
- **无需了解 CDP 细节：** 隔离世界、执行上下文、target 缓存全部由 Pydoll 处理。
- **天然支持嵌套：** 每次查找都以当前元素为范围，多层结构依然清晰。
- **统一 API：** 不再需要在 `Tab` 与 `WebElement` 方法之间切换。

!!! tip "`Tab.get_frame()` 将被移除"
    现在调用 `Tab.get_frame()` 会抛出 `DeprecationWarning`，并将在未来版本删除。请尽快改为直接使用 iframe 元素。

## 常见模式

### 截取 iframe 内部元素的截图

```python
iframe = await tab.find(tag_name='iframe')
chart = await iframe.find(id='sales-chart')
await chart.take_screenshot('chart.png')
```

### 遍历多个 iframe

```python
iframes = await tab.find(tag_name='iframe', find_all=True)
for frame in iframes:
    heading = await frame.find(tag_name='h2')
    print(await heading.text)
```

### 等待 iframe 内容加载

```python
iframe = await tab.find(tag_name='iframe')
await iframe.wait_until(is_visible=True, timeout=10)
banner = await iframe.find(id='promo-banner')
```

## 跨 iframe 选择器

无需手动逐个查找 iframe 再在其中搜索，您可以编写一个**单一选择器**来跨越 iframe 边界。Pydoll 会自动检测 XPath 或 CSS 选择器中的 `iframe` 步骤，将其拆分为片段，并依次遍历 iframe 链。

### CSS 选择器

在 `iframe` 复合选择器后使用任意标准组合器（`>`、空格）：

```python
# 单个 iframe 穿越
button = await tab.query('iframe > .submit-btn')

# iframe 上带属性选择器
button = await tab.query('iframe[src*="checkout"] > #pay-button')

# 嵌套 iframe
element = await tab.query('iframe.outer > iframe.inner > div.content')

# iframe 后的多步查找
link = await tab.query('iframe > nav > a.home-link')

# iframe 在其他元素内部（不在根位置）
button = await tab.query('div > iframe > button.submit')
content = await tab.query('.wrapper iframe > div.content')
```

### XPath 表达式

在 `iframe` 步骤后使用 `/` —— Pydoll 会在 iframe 节点处拆分：

```python
# 单个 iframe 穿越
button = await tab.query('//iframe/body/button[@id="submit"]')

# iframe 在其他元素内部（不在根位置）
div = await tab.query('//div/iframe/div')
item = await tab.query('//div[@class="wrapper"]/iframe/body/div')

# iframe 上带谓词
heading = await tab.query('//iframe[@src*="cloudflare"]//h1')

# 嵌套 iframe
element = await tab.query('//iframe[@id="outer"]//iframe[@id="inner"]//div')
```

### 工作原理

当 Pydoll 遇到类似 `iframe[src*="checkout"] > form > button` 的选择器时：

1. **解析**选择器为片段：`iframe[src*="checkout"]` 和 `form > button`
2. 使用第一个片段**查找** iframe 元素
3. 使用第二个片段**在 iframe 内部搜索**
4. 对于嵌套 iframe，在每个边界重复此过程

这等同于手动方式，但只需一次调用：

```python
# 手动方式（仍然有效）
iframe = await tab.find(tag_name='iframe', src='*checkout*')
button = await iframe.query('form > button')

# 自动方式（相同结果，一行代码）
button = await tab.query('iframe[src*="checkout"] > form > button')
```

### 不进行拆分的情况

只有当 `iframe` 作为**标签名**出现时才会进行拆分。以下选择器保持不变：

- `.iframe > body` —— 类选择器，不是标签
- `#iframe > body` —— ID 选择器
- `div.iframe > body` —— 标签是 `div`，不是 `iframe`
- `[data-type="iframe"] > body` —— 属性选择器
- `iframe` 或 `//iframe` —— iframe 后无内容（没有需要搜索的内容）

### find_all 支持

最后一个片段支持 `find_all=True`，返回最终 iframe 内所有匹配的元素：

```python
# 获取 iframe 内的所有链接
links = await tab.query('iframe > a', find_all=True)
```

## 最佳实践

- **把 iframe 作为作用域：** 在 iframe `WebElement` 上调用 `find`、`query`、`execute_script` 等方法。
- **避免 `tab.find` 查找内部元素：** 它只能访问顶级文档。
- **复用引用：** Pydoll 会缓存 iframe 的上下文，可重复使用。
- **现有工作流保持一致：** 滚动、截图、等待、脚本执行、读取属性等操作与普通元素完全一致。

## 延伸阅读

- **[元素查找](../element-finding.md)** —— 介绍查找范围与链式查询。
- **[截图与 PDF](screenshots-and-pdfs.md)** —— 讲解如何获取视觉输出。
- **[事件系统](../advanced/event-system.md)** —— 以事件驱动方式监听页面变化（包括 iframe）。

在新模型下，iframe 不再是“特殊情况”。把它视为普通 DOM 节点，专注于自动化逻辑，其余复杂度交给 Pydoll 处理。