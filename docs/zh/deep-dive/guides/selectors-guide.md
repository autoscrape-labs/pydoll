# CSS 选择器 vs XPath：完整指南

使用 `query()` 方法时，您有两种强大的选择器语言可供选择：CSS 选择器和 XPath。了解何时以及如何使用每种语言对于有效的元素定位至关重要。

## 根本差异

| 方面 | CSS 选择器 | XPath |
|---|---|---|
| **语法** | 简单，类似 CSS | XML 路径语言 |
| **性能** | 更快 (浏览器原生支持) | 稍慢 |
| **方向** | 只能向下和横向遍历 | 可以向任何方向遍历 |
| **文本匹配** | 有限 (伪选择器) | 强大的文本函数 |
| **复杂性** | 最适合简单到中等的情况 | 擅长处理复杂关系 |
| **可读性** | Web 开发人员更直观 | 学习曲线更陡峭 |

## 何时使用 CSS 选择器

CSS 选择器是以下情况的理想选择：

- 通过 ID、类或标签进行简单的元素选择
- 直接的父子关系
- 具有简单模式的属性匹配
- 对性能要求严格的场景
- 在 DOM 中向下遍历时

```python
# 简洁高效的 CSS 示例
await tab.query("#login-form")
await tab.query(".submit-button")
await tab.query("div.container > p.intro")
await tab.query("input[type='email'][required]")
await tab.query("ul.menu li:first-child")
```

## 何时使用 XPath

XPath 是以下情况的理想选择：

- 复杂的文本匹配和部分文本搜索
- 向上遍历到父元素
- 查找相对于兄弟元素的元素
- 选择器中的条件逻辑
- 复杂的 DOM 关系

```python
# 强大的 XPath 示例
await tab.query("//button[contains(text(), 'Submit')]")
await tab.query("//input[@name='email']/parent::div")
await tab.query("//td[text()='John']/following-sibling::td[2]")
await tab.query("//div[contains(@class, 'product') and @data-price > 100]")
```

## CSS 选择器语法参考

### 基本选择器

```python
# 元素选择器
await tab.query("div")              # 第一个 <div> 元素
await tab.query("div", find_all=True)  # 所有 <div> 元素
await tab.query("button")           # 第一个 <button> 元素

# ID 选择器
await tab.query("#username")        # id="username" 的元素

# 类选择器
await tab.query(".submit-btn")      # 第一个 class="submit-btn" 的元素
await tab.query(".submit-btn", find_all=True)  # 所有带该类的元素
await tab.query(".btn.primary")     # 第一个同时具有这两个类的元素

# 通用选择器
await tab.query("*", find_all=True) # 所有元素
```

### 组合器

```python
# 后代组合器 (空格)
await tab.query("div p")            # <div> 内的第一个 <p>
await tab.query("div p", find_all=True)  # <div> 内的所有 <p> (任何深度)

# 子组合器 (>)
await tab.query("div > p")          # <div> 直接子元素中的第一个 <p>
await tab.query("div > p", find_all=True)  # 所有作为直接子元素的 <p>

# 相邻兄弟组合器 (+)
await tab.query("h1 + p")           # 紧跟 <h1> 后的 <p>

# 通用兄弟组合器 (~)
await tab.query("h1 ~ p")           # <h1> 后的第一个 <p> 兄弟元素
await tab.query("h1 ~ p", find_all=True)  # <h1> 后的所有 <p> 兄弟元素
```

### 属性选择器

```python
# 属性存在
await tab.query("input[required]")                # 第一个带 'required' 的 input
await tab.query("input[required]", find_all=True) # 所有带 'required' 的 input

# 属性等于
await tab.query("input[type='email']")            # 第一个 email input
await tab.query("input[type='email']", find_all=True)  # 所有 email input

# 属性包含单词
await tab.query("div[class~='active']")           # 第一个 class 中包含 'active' 的 div

# 属性以...开头
await tab.query("a[href^='https://']")            # 第一个 HTTPS 链接
await tab.query("a[href^='https://']", find_all=True)  # 所有 HTTPS 链接

# 属性以...结尾
await tab.query("img[src$='.png']")               # 第一个 PNG 图像
await tab.query("img[src$='.png']", find_all=True)     # 所有 PNG 图像

# 属性包含子字符串
await tab.query("a[href*='example']")             # 第一个 href 中包含 'example' 的链接
await tab.query("a[href*='example']", find_all=True)   # 所有 href 中包含 'example' 的链接

# 不区分大小写匹配
await tab.query("input[type='text' i]")           # 不区分大小写匹配
```

### 伪类

```python
# 结构伪类
await tab.query("li:first-child")                 # 作为第一个子元素的第一个 <li>
await tab.query("li:last-child")                  # 作为最后一个子元素的第一个 <li>
await tab.query("li:nth-child(2)")                # 作为第二个子元素的第一个 <li>
await tab.query("li:nth-child(odd)", find_all=True)  # 所有奇数位置的 <li>
await tab.query("li:nth-child(even)", find_all=True)  # 所有偶数位置的 <li>
await tab.query("li:nth-child(3n)", find_all=True)    # 每第 3 个 <li>

# 类型伪类
await tab.query("p:first-of-type")                # 兄弟元素中的第一个 <p>
await tab.query("p:last-of-type")                 # 兄弟元素中的最后一个 <p>
await tab.query("p:nth-of-type(2)")               # 兄弟元素中的第二个 <p>

# 状态伪类
await tab.query("input:enabled")                  # 第一个启用的 input
await tab.query("input:enabled", find_all=True)   # 所有启用的 input
await tab.query("input:disabled")                 # 第一个禁用的 input
await tab.query("input:checked")                  # 第一个选中的 checkbox/radio
await tab.query("input:focus")                    # 当前获得焦点的 input

# 其他有用的伪类
await tab.query("div:empty")                      # 第一个空元素
await tab.query("div:empty", find_all=True)       # 所有空元素
await tab.query("div:not(.exclude)")              # 第一个没有 'exclude' 类的 div
await tab.query("div:not(.exclude)", find_all=True)  # 所有没有 'exclude' 类的 div
```

## XPath 语法参考

### 基本路径表达式

```python
# 绝对路径 (从根开始)
await tab.query("/html/body/div")                 # 处于该精确路径的第一个 div

# 相对路径 (从任何地方开始)
await tab.query("//div")                          # 第一个 <div> 元素
await tab.query("//div", find_all=True)           # 所有 <div> 元素
await tab.query("//div/p")                        # 任何 <div> 内的第一个 <p>
await tab.query("//div/p", find_all=True)         # 任何 <div> 内的所有 <p>

# 当前节点
await tab.query("./div")                          # 相对于当前的第一个 <div>

# 父节点
await tab.query("..")                             # 当前节点的父节点
```

### 属性选择

```python
# 基本属性匹配
await tab.query("//input[@type='email']")         # 第一个 email input
await tab.query("//input[@type='email']", find_all=True)  # 所有 email input
await tab.query("//div[@id='content']")           # id='content' 的 div

# 多个属性
await tab.query("//input[@type='text' and @required]")  # 第一个匹配项
await tab.query("//input[@type='text' and @required]", find_all=True)  # 所有匹配项
await tab.query("//div[@class='card' or @class='panel']")  # 第一个 card 或 panel

# 属性存在
await tab.query("//button[@disabled]")            # 第一个 disabled button
await tab.query("//button[@disabled]", find_all=True)  # 所有 disabled button
```

## XPath 轴 (方向导航)

XPath 的真正威力来自于它能够在 DOM 树中向任何方向导航。

### 轴参考表

| 轴 | 方向 | 描述 | 示例 |
|---|---|---|---|
| `child::` | 向下 | 仅直接子元素 | `//div/child::p` |
| `descendant::` | 向下 | 所有后代 (任何深度) | `//div/descendant::a` |
| `parent::` | 向上 | 直接父元素 | `//input/parent::div` |
| `ancestor::` | 向上 | 所有祖先 (任何深度) | `//span/ancestor::div` |
| `following-sibling::` | 横向 | 当前元素之后的所有兄弟元素 | `//h1/following-sibling::p` |
| `preceding-sibling::` | 横向 | 当前元素之前的所有兄弟元素 | `//p/preceding-sibling::h1` |
| `following::` | 向前 | 当前节点之后的所有节点 | `//h1/following::*` |
| `preceding::` | 向后 | 当前节点之前的所有节点 | `//h1/preceding::*` |
| `ancestor-or-self::` | 向上 | 祖先 + 当前节点 | `//div/ancestor-or-self::*` |
| `descendant-or-self::` | 向下 | 后代 + 当前节点 | `//div/descendant-or-self::*` |
| `self::` | 当前 | 仅当前节点 | `//div/self::div` |
| `attribute::` | 属性 | 当前节点的属性 | `//div/attribute::class` |

!!! info "简写语法"
    - `//div` 是 `//descendant-or-self::div` 的简写
    - `//div/p` 是 `//div/child::p` 的简写
    - `@id` 是 `attribute::id` 的简写
    - `..` 是 `parent::node()` 的简写

### 实用轴示例

```python
# 导航到父元素
await tab.query("//input[@name='email']/parent::div")
await tab.query("//span[@class='error']/..")       # 简写

# 查找祖先元素
await tab.query("//input/ancestor::form")          # 第一个祖先 <form>
await tab.query("//button/ancestor::div[@class='modal']")

# 兄弟元素导航
await tab.query("//label[text()='Email:']/following-sibling::input")
await tab.query("//h2/following-sibling::p[1]")    # <h2> 后的第一个 <p>
await tab.query("//h2/following-sibling::p", find_all=True)  # <h2> 后的所有 <p>
await tab.query("//button/preceding-sibling::input[last()]")

# 复杂关系
await tab.query("//tr/td[1]/following-sibling::td[2]")  # 第一行中的第 3 个单元格
await tab.query("//tr/td[1]/following-sibling::td[2]", find_all=True)  # 所有行中的第 3 个单元格
```

## XPath 函数

### 文本函数

```python
# 精确文本匹配
await tab.query("//button[text()='Submit']")

# 包含文本
await tab.query("//p[contains(text(), 'welcome')]")

# 以...开头
await tab.query("//a[starts-with(@href, 'https://')]")

# 文本规范化 (移除多余的空白)
await tab.query("//button[normalize-space(text())='Submit']")

# 字符串长度
await tab.query("//input[string-length(@value) > 5]")

# 字符串连接
await tab.query("//div[concat(@data-first, @data-last)='JohnDoe']")
```

### 数字函数

```python
# 位置匹配
await tab.query("//li[position()=1]")              # 第一个 <li>
await tab.query("//li[position() > 3]", find_all=True)  # 第 3 个之后的所有 <li>
await tab.query("//li[last()]")                    # 最后一个 <li>
await tab.query("//li[last()-1]")                  # 倒数第二个

# 计数
await tab.query("//ul[count(li) > 5]")             # 第一个包含超过 5 个 li 的 <ul>
await tab.query("//ul[count(li) > 5]", find_all=True)  # 所有包含超过 5 个 li 的 <ul>

# 数值运算
await tab.query("//div[@data-price > 100]")        # 第一个 price > 100 的 div
await tab.query("//div[@data-price > 100]", find_all=True)  # 所有
await tab.query("//div[number(@data-stock) = 0]")  # 第一个 stock = 0 的
```

### 布尔函数

```python
# 布尔逻辑
await tab.query("//div[@visible='true' and @enabled='true']")  # 第一个匹配项
await tab.query("//input[@type='text' or @type='email']")  # 第一个 text 或 email
await tab.query("//input[@type='text' or @type='email']", find_all=True)  # 所有
await tab.query("//button[not(@disabled)]")        # 第一个启用的 button
await tab.query("//button[not(@disabled)]", find_all=True)  # 所有启用的 button

# 存在性检查
await tab.query("//div[child::p]")                 # 第一个有 <p> 子元素的 div
await tab.query("//div[child::p]", find_all=True)  # 所有有 <p> 子元素的 div
await tab.query("//div[not(child::*)]")            # 第一个空 div
await tab.query("//div[not(child::*)]", find_all=True)  # 所有空 div
```

## XPath 谓词 (Predicates)

谓词使用方括号 `[]` 中的条件来过滤节点集。

```python
# 位置谓词
await tab.query("(//div)[1]")                      # 文档中的第一个 <div>
await tab.query("(//div)[last()]")                 # 文档中的最后一个 <div>
await tab.query("//ul/li[3]")                      # <ul> 中的第一个第 3 个 <li>
await tab.query("//ul/li[3]", find_all=True)       # 每个 <ul> 中的所有第 3 个 <li>

# 多个谓词 (AND 逻辑)
await tab.query("//input[@type='text'][@required]")  # 第一个匹配项
await tab.query("//div[@class='product'][position() < 4]", find_all=True)  # 前 3 个

# 属性谓词
await tab.query("//div[@data-id='123']")
await tab.query("//a[contains(@class, 'button')]")  # 第一个匹配的链接
await tab.query("//input[starts-with(@name, 'user')]")  # 第一个匹配的 input
```

## 真实世界示例：复杂元素查找

让我们使用一个真实的 HTML 结构来演示高级选择器。

### 示例 HTML 结构

```html
<div class="dashboard">
    <header>
        <h1>User Dashboard</h1>
        <nav class="menu">
            <a href="/home" class="active">Home</a>
            <a href="/profile">Profile</a>
            <a href="/settings">Settings</a>
        </nav>
    </header>
    
    <main>
        <section class="products">
            <h2>Available Products</h2>
            <table id="products-table">
                <thead>
                    <tr>
                        <th>Product Name</th>
                        <th>Price</th>
                        <th>Stock</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    <tr data-product-id="101">
                        <td>Laptop</td>
                        <td class="price">$999</td>
                        <td class="stock">15</td>
                        <td>
                            <button class="btn-edit">Edit</button>
                            <button class="btn-delete">Delete</button>
                        </td>
                    </tr>
                    <tr data-product-id="102">
                        <td>Mouse</td>
                        <td class="price">$25</td>
                        <td class="stock">0</td>
                        <td>
                            <button class="btn-edit">Edit</button>
                            <button class="btn-delete" disabled>Delete</button>
                        </td>
                    </tr>
                    <tr data-product-id="103">
                        <td>Keyboard</td>
                        <td class="price">$75</td>
                        <td class="stock">8</td>
                        <td>
                            <button class="btn-edit">Edit</button>
                            <button class="btn-delete">Delete</button>
                        </td>
                    </tr>
                </tbody>
            </table>
        </section>
        
        <section class="user-form">
            <h2>User Information</h2>
            <form id="user-form">
                <div class="form-group">
                    <label for="username">Username:</label>
                    <input type="text" id="username" name="username" required>
                    <span class="error-message" style="display:none;">Invalid username</span>
                </div>
                <div class="form-group">
                    <label for="email">Email:</label>
                    <input type="email" id="email" name="email" required>
                    <span class="error-message" style="display:none;">Invalid email</span>
                </div>
                <div class="form-group">
                    <input type="checkbox" id="newsletter" name="newsletter">
                    <label for="newsletter">Subscribe to newsletter</label>
                </div>
                <button type="submit" class="btn-primary">Save Changes</button>
                <button type="button" class="btn-secondary">Cancel</button>
            </form>
        </section>
    </main>
</div>
```

### 挑战 1：查找活动的导航链接

**目标**：找到当前活动的导航链接。

```python
# CSS 选择器
active_link = await tab.query("nav.menu a.active")

# XPath
active_link = await tab.query("//nav[@class='menu']//a[@class='active']")

# 获取其文本
text = await active_link.text
print(text)  # "Home"
```

### 挑战 2：查找特定产品的编辑按钮

**目标**：找到产品 "Mouse" 的编辑按钮 (不知道其行位置)。

```python
# XPath (推荐用于此情况)
edit_button = await tab.query(
    "//tr[td[text()='Mouse']]//button[contains(@class, 'btn-edit')]"
)

# 备选方案：使用 following-sibling
edit_button = await tab.query(
    "//td[text()='Mouse']/following-sibling::td//button[@class='btn-edit']"
)
```

!!! tip "为什么这里使用 XPath？"
    CSS 选择器无法向上遍历找到行，然后再向下找到按钮。XPath 在 DOM 中自由移动的能力使这变得微不足道。

### 挑战 3：查找所有价格超过 $50 的产品

**目标**：获取价格大于 $50 的所有表格行。

```python
# 带有数值比较的 XPath
expensive_products = await tab.query(
    "//tr[number(translate(td[@class='price'], '$,', '')) > 50]",
    find_all=True
)

# 更易读的版本：对于更简单的情况使用 contains
# 这会查找价格包含特定金额的产品
products = await tab.query("//tr[contains(td[@class='price'], '$75')]", find_all=True)
```

!!! note "文本到数字的转换"
    `translate()` 函数移除了 `$` 和 `,` 字符，然后 `number()` 将其转换为数值进行比较。

### 挑战 4：查找所有缺货产品

**目标**：找到所有库存为 0 的产品。

```python
# XPath
out_of_stock = await tab.query(
    "//tr[td[@class='stock' and text()='0']]",
    find_all=True
)

# 备选方案：查找所有行并检查库存
rows = await tab.query("//tbody/tr[td[@class='stock']/text()='0']", find_all=True)
```

### 挑战 5：通过标签查找输入字段

**目标**：首先定位其标签，然后找到 email 输入字段。

```python
# XPath 使用 label 的 'for' 属性
email_input = await tab.query("//label[text()='Email:']/following-sibling::input")

# 备选方案：使用 for 属性
email_input = await tab.query("//input[@id=(//label[text()='Email:']/@for)]")

# 更通用的：按标签文本查找
username_input = await tab.query(
    "//label[contains(text(), 'Username')]/following-sibling::input"
)
```

### 挑战 6：查找 Email 字段旁的错误消息

**目标**：获取出现在 email 输入字段旁边的错误消息 span。

```python
# XPath - 查找 email input 的错误兄弟元素
error_span = await tab.query(
    "//input[@id='email']/following-sibling::span[@class='error-message']"
)

# 备选方案：从父 div 导航
error_span = await tab.query(
    "//input[@id='email']/parent::div//span[@class='error-message']"
)

# 检查可见性
is_visible = await error_span.is_visible()
```

### 挑战 7：查找提交按钮 (而不是取消按钮)

**目标**：找到提交按钮，排除取消按钮。

```python
# CSS 选择器 (简单)
submit_button = await tab.query("button[type='submit']")
submit_button = await tab.query("button.btn-primary")

# 带文本的 XPath
submit_button = await tab.query("//button[text()='Save Changes']")

# 排除其他的 XPath
submit_button = await tab.query(
    "//button[@type='submit' and not(@class='btn-secondary')]"
)
```

### 挑战 8：查找所有必填的表单字段

**目标**：获取表单中所有必填的 input 字段。

```python
# CSS 选择器 (简洁)
required_fields = await tab.query(
    "#user-form input[required]",
    find_all=True
)

# XPath
required_fields = await tab.query(
    "//form[@id='user-form']//input[@required]",
    find_all=True
)

# 验证
for field in required_fields:
    field_name = await field.get_attribute("name")
    print(f"Required: {field_name}")
```

### 挑战 9：查找第一个未禁用的删除按钮

**目标**：找到第一个未被禁用的删除按钮。

```python
# CSS 选择器
first_enabled_delete = await tab.query("button.btn-delete:not([disabled])")

# XPath
first_enabled_delete = await tab.query(
    "//button[contains(@class, 'btn-delete') and not(@disabled)]"
)

# 获取所有启用的删除按钮
all_enabled = await tab.query(
    "//button[@class='btn-delete' and not(@disabled)]",
    find_all=True
)
```

### 挑战 10：按多个条件查找表格行

**目标**：查找库存 > 0 且价格 < $100 的产品。

```python
# 具有复杂逻辑的 XPath
available_affordable = await tab.query(
    """
    //tr[
        number(td[@class='stock']) > 0 
        and 
        number(translate(td[@class='price'], '$', '')) < 100
    ]
    """,
    find_all=True
)

# 对于每个匹配的产品
for row in available_affordable:
    cells = await row.query("td", find_all=True)
    product_name = await cells[0].text
    print(f"Available: {product_name}")
```

### 挑战 11：导航复杂关系

**目标**：从删除按钮获取同一行中的产品名称。

```python
# 从删除按钮开始
delete_button = await tab.query("//tr[@data-product-id='101']//button[@class='btn-delete']")

# 导航到父行，然后到第一个单元格
product_name_cell = await delete_button.query("./ancestor::tr/td[1]")
product_name = await product_name_cell.text
print(product_name)  # "Laptop"

# 备选方案：首先获取整行
row = await delete_button.query("./ancestor::tr")
product_id = await row.get_attribute("data-product-id")
print(product_id)  # "101"
```

### 挑战 12：同时查找复选框及其标签

**目标**：找到 newsletter 复选框并验证其标签。

```python
# 查找复选框
checkbox = await tab.query("#newsletter")

# 使用 'for' 属性获取关联的标签
label = await tab.query("//label[@for='newsletter']")
label_text = await label.text
print(label_text)  # "Subscribe to newsletter"

# 备选方案：从复选框导航到标签
label = await checkbox.query("//following::label[@for='newsletter']")

# 检查是否选中
is_checked = await checkbox.is_checked()
```

## 高级模式：动态构建选择器

处理动态内容时，您可能需要以编程方式构建选择器：

```python
async def find_product_by_name(tab, product_name: str):
    """通过名称动态查找产品行。"""
    # 转义产品名称中的引号以防止 XPath 注入
    safe_name = product_name.replace("'", "\\'")
    
    xpath = f"//tr[td[text()='{safe_name}']]"
    return await tab.query(xpath)

async def find_table_cell(tab, row_text: str, column_index: int):
    """通过行内容和列位置查找特定单元格。"""
    xpath = f"//tr[td[contains(text(), '{row_text}')]]/td[{column_index}]"
    return await tab.query(xpath)

# 用法
product_row = await find_product_by_name(tab, "Laptop")
price_cell = await find_table_cell(tab, "Laptop", 2)
price = await price_cell.text
print(price)  # "$999"
```

## 性能比较

```python
import asyncio
import time

async def benchmark_selectors(tab):
    """比较 CSS 与 XPath 的性能。"""
    
    # 预热
    await tab.query("#products-table")
    
    # 基准测试 CSS
    start = time.time()
    for _ in range(100):
        await tab.query("#products-table tbody tr", find_all=True)
    css_time = time.time() - start
    
    # 基准测试 XPath
    start = time.time()
    for _ in range(100):
        await tab.query("//table[@id='products-table']//tbody//tr", find_all=True)
    xpath_time = time.time() - start
    
    print(f"CSS: {css_time:.3f}s")
    print(f"XPath: {xpath_time:.3f}s")
    print(f"CSS is {xpath_time/css_time:.2f}x faster")

# 典型结果：对于简单选择器，CSS 快 1.2-1.5 倍
```

!!! warning "性能 vs 可读性"
    虽然 CSS 选择器通常更快，但对于单个查询，差异通常可以忽略不计（毫秒级）。请选择使您的代码更具可读性和可维护性的选择器，特别是对于 XPath 擅长的复杂关系。

## 选择器最佳实践

### 1. 优先使用稳定的选择器

```python
# 好的：使用语义属性
await tab.query("#user-email")
await tab.query("[data-testid='submit-button']")
await tab.query("input[name='username']")

# 避免：基于结构的脆弱选择器
await tab.query("div > div > div:nth-child(3) > input")
await tab.query("body > div:nth-child(2) > form > div:first-child")
```

### 2. 使用能工作的最简单的选择器

```python
# 好的：简单高效
await tab.query("#login-form")
await tab.query(".submit-button")

# 避免：在不必要时过度复杂化
await tab.query("//div[@id='content']/descendant::form[@id='login-form']")
```

### 3. 适当组合 find() 和 query()

```python
# 使用 find() 进行简单的属性匹配
username = await tab.find(id="username")
submit = await tab.find(tag_name="button", type="submit")

# 使用 query() 处理复杂模式
active_link = await tab.query("nav.menu a.active")
error_msg = await tab.query("//input[@name='email']/following-sibling::span[@class='error']")
```

### 4. 为复杂的选择器添加注释

```python
# 查找包含产品 "Laptop" 的行中的 "Edit" 按钮
# XPath: 导航到带有 "Laptop" 文本的行, 然后查找编辑按钮
edit_button = await tab.query(
    "//tr[td[text()='Laptop']]//button[@class='btn-edit']"
)
```

## 结论

通过理解 CSS 选择器和 XPath，以及它们各自的优势和用例，您可以创建出健壮且可维护的浏览器自动化，以处理现代 Web 应用程序的复杂性。请记住：

- **使用 CSS 选择器** 进行简单的、对性能要求严格的选择
- **使用 XPath** 处理复杂关系、文本匹配和向上导航
- 编写选择器时，**选择稳定性** 而非简洁性
- **注释复杂的查询** 以保持代码的可读性

有关 Pydoll 内部如何使用这些选择器的更多信息，请参阅 [FindElements Mixin](find-elements-mixin.md) 文档。