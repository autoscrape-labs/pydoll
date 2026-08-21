# Selector：CSS 与 XPath

selector 是你交给 `tab.query()`（以及提取模型中 `selector=`）的字符串，用来指向某个元素。Pydoll 会说两种 selector 语言，CSS 和 XPath，并会替你挑选合适的引擎：如果字符串以 `/` 或 `./` 开头，它就作为 XPath 运行，否则作为 CSS selector 运行。这一页会教你足够的两种语言知识，让你能在页面上找到任何东西。

只有 `query()` 才需要 selector。`find()` 方法接受的是普通属性（参见 [Element finding](../guides/element-finding.md)）；当你需要表达一种 `find()` 无法表达的关系时，才动用 selector。

试试看：在下面输入一个 selector，匹配到的元素就会高亮。它运行的正是浏览器使用的那套 `querySelectorAll` / XPath，所以在这里匹配到什么，在你的自动化里就匹配到什么。

<iframe src="/docs/resources/visuals/selector-playground.html" aria-label="Type a CSS or XPath selector and see which elements it matches" style="width: 100%; height: 500px; border: 0;" loading="lazy"></iframe>

```python
import asyncio

from pydoll.browser.chromium import Chrome


async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://en.wikipedia.org/wiki/Python_(programming_language)')

        # CSS: 通过 id 定位文章标题
        title = await tab.query('#firstHeading')
        print(await title.text)

        # XPath: 第一个 href 中提到 python.org 的链接
        link = await tab.query("//a[contains(@href, 'python.org')]")
        print(link.get_attribute('href'))

asyncio.run(main())
```

上面两个查询都经过同一个 `query()` 调用。Pydoll 看到第二个查询开头的 `//`，就把它当作 XPath 处理。

## 什么时候用哪一种

大多数情况下 CSS 就够了，而且读起来更自然。当你需要 CSS 做不到的事情时，再动用 XPath。

- **CSS** 按 id、class、标签、属性和位置来选取，并能在页面中向下和横向移动。它是更简短、更常见的语言。
- **XPath** 能做到上述所有这些，此外还能按可见文本匹配、*向上*走到父节点或祖先节点，并表达诸如“包含这段文本的那一行”之类的条件。如果你需要按文本找到某个元素，或者从子节点往上导航回它所在的容器，那就是 XPath 的活儿。

一个粗略的规则：从 CSS 开始，一旦发现自己想说“文本是 X 的那个元素”或“Y 的父节点”，就切换到 XPath。

## CSS 参考

下面的代码片段都假定 `tab` 已经启动。给它们中的任何一个传入 `find_all=True`，就能得到一个列表而不是第一个匹配项。

### 按 id、class 和标签选取

```python
await tab.query('div')             # 第一个 <div>
await tab.query('#username')       # id="username" 的元素
await tab.query('.submit-btn')     # 第一个 class="submit-btn" 的元素
await tab.query('.btn.primary')    # 同时带两个 class 的元素
await tab.query('input')           # 第一个 <input>
```

### 组合符

组合符描述元素之间的关系。

```python
await tab.query('nav a')           # <nav> 内任意深度处的任何 <a>
await tab.query('nav > a')         # 作为 <nav> 直接子节点的 <a>
await tab.query('h1 + p')          # 紧跟在某个 <h1> 之后的 <p>
await tab.query('h1 ~ p')          # 作为兄弟节点跟在某个 <h1> 之后的第一个 <p>
```

### 属性 selector

```python
await tab.query('input[required]')            # 带有该属性
await tab.query("input[type='email']")        # 属性等于某个值
await tab.query("a[href^='https://']")        # 值以……开头
await tab.query("img[src$='.png']")           # 值以……结尾
await tab.query("a[href*='wikipedia']")       # 值包含
```

### 伪类

伪类按位置或状态来选取。

```python
await tab.query('li:first-child')             # 兄弟节点中第一个 <li>
await tab.query('li:nth-child(2)')            # 第二个 <li>
await tab.query('tr:nth-child(odd)', find_all=True)  # 每一个奇数行
await tab.query('input:checked')              # 被选中的 checkbox 或单选按钮
await tab.query('button:not([disabled])')     # 不带 disabled 属性的按钮
```

## XPath 参考

### 路径

```python
await tab.query('//div')           # 任何位置的任何 <div>
await tab.query('//nav/a')         # 作为某个 <nav> 直接子节点的 <a>
await tab.query('//nav//a')        # 某个 <nav> 内部任何位置的 <a>
await tab.query('(//div)[1]')      # 文档中第一个 <div>
await tab.query('//ul/li[last()]') # 某个 <ul> 中最后一个 <li>
```

### 按属性和文本匹配

这正是你需要 XPath 的地方。CSS 无法按可见文本选取，XPath 可以。

```python
await tab.query("//input[@type='email']")            # 属性等于
await tab.query("//input[@type='text' and @required]")  # 两个条件
await tab.query("//button[text()='Submit']")         # 精确文本
await tab.query("//p[contains(text(), 'welcome')]")  # 部分文本
await tab.query("//a[starts-with(@href, 'https://')]")  # 属性以……开头
```

!!! tip "匹配前先规范化文本"
    渲染出来的文本常常带有多余的空白。`//button[normalize-space(text())='Submit']` 会把连续的空格折叠成一个并去掉两端的空白，所以即使 HTML 的缩进参差不齐，它也能匹配。

### 轴：向任意方向移动

轴指明从当前节点出发要往哪个方向走。这是 XPath 的优势：你可以往上走到父节点，或横向走到兄弟节点，而这是 CSS 做不到的。

| 轴 | 方向 | 找到 |
|------|-----------|-------|
| `parent::` | 向上 | 直接父节点 |
| `ancestor::` | 向上 | 任意深度处的任何祖先节点 |
| `following-sibling::` | 横向 | 该节点之后的兄弟节点 |
| `preceding-sibling::` | 横向 | 该节点之前的兄弟节点 |
| `child::` | 向下 | 直接子节点 |
| `descendant::` | 向下 | 任何后代节点 |

你会经常见到的简写：`//div/p` 就是 `//div/child::p`，`@id` 就是 `attribute::id`，而 `..` 就是 `parent::node()`。

```python
await tab.query("//input[@name='email']/parent::div")   # 向上到包裹它的 div
await tab.query('//button/ancestor::form')              # 向上到外层的 form
await tab.query("//label[text()='Email:']/following-sibling::input")  # 紧挨着某个 label 的 input
```

## 实例演练

下面这些用到了后面这个示例表单。它展示了你在真实页面中最常碰到的模式：通过旁边的文本找到某个元素，以及从一个控件往上走到它所在的行。

```html
<form id="signup">
  <div class="field">
    <label for="email">Email:</label>
    <input type="email" id="email" name="email" required>
    <span class="error" style="display:none;">Invalid email</span>
  </div>
  <div class="field">
    <input type="checkbox" id="newsletter" name="newsletter">
    <label for="newsletter">Subscribe to the newsletter</label>
  </div>
  <button type="submit">Save</button>
  <button type="button">Cancel</button>
</form>
```

### 通过 label 找到 input

你知道 label 的文本，却不知道 input 的 id。先找到 label，再横向走一步到 input：

```python
email = await tab.query("//label[text()='Email:']/following-sibling::input")
```

### 找到某个字段旁边的错误信息

```python
error = await tab.query("//input[@id='email']/following-sibling::span[@class='error']")
if await error.is_visible():
    print('Email was rejected')
```

`is_visible()` 报告的是该元素是否真的显示出来了，这在这里很重要，因为这个 span 一开始是隐藏的。

### 区分两个按钮

提交按钮就是那个 `type='submit'` 的，所以你永远不必依赖它的位置：

```python
save = await tab.query("button[type='submit']")          # 这里 CSS 就够了
save = await tab.query("//button[text()='Save']")        # 或者按 label 文本匹配
```

### 读取某个 checkbox 的 label

`for` 属性把一个 label 和它的控件绑在一起，所以你可以直接跳到它：

```python
label = await tab.query("//label[@for='newsletter']")
print(await label.text)   # "Subscribe to the newsletter"
```

### 从一个控件往上走到它所在的行

在表格中，你常常拿着一个按钮，想要它所在的那一行。从该元素出发，用一个沿树向上攀爬的 XPath 来查询：

```python
delete = await tab.query("//tr[@data-product-id='101']//button[@class='delete']")

row = await delete.query('./ancestor::tr')
print(row.get_attribute('data-product-id'))   # "101", get_attribute 不需要 await
```

`get_attribute()` 从你已经定位到的元素上同步读取一个值，所以它不需要 `await`。

## 用变量构建 selector

当你要匹配的值来自你的程序时，用 f-string 来构建这个字符串。把值中的任何引号转义掉，以免它们破坏表达式：

```python
async def row_for(tab, product_name):
    safe = product_name.replace("'", "\\'")
    return await tab.query(f"//tr[td[text()='{safe}']]")


laptop_row = await row_for(tab, 'Laptop')
```

## 让 selector 保持稳定

挑选那些改版不太可能动到的属性，并尽量依靠最简单能奏效的表达式。

```python
# 稳定：name 和 id 能挺过布局变动
await tab.query('#signup')
await tab.query("[data-testid='save-button']")
await tab.query("input[name='email']")

# 脆弱：基于位置的链条会在标记发生变化时失效
await tab.query('div > div > div:nth-child(3) > input')
```

对于简单的查找，CSS 比 XPath 略快一点，但这个差距是每次查询几毫秒，很少值得为它去优化。选那个读起来清晰、又能挺过页面变化的 selector。

## 下一步

- [Element finding](../guides/element-finding.md)：把这些 selector 用到 `query()`，以及基于属性的 `find()`。
- [DOM traversal](../guides/dom-traversal.md)：从你已经拿到的某个元素出发遍历这棵树。
- [Structured extraction](../guides/structured-extraction.md)：把这些 selector 放进模型的 `Field(selector=...)` 里，以拉取带类型的数据。
