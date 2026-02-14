# 截图与PDF

Pydoll通过直接使用Chrome DevTools Protocol命令提供强大的截图和PDF生成功能。可以捕获完整页面、特定元素或生成具有精细控制的PDF。

## 截图

### 基础页面截图

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def take_page_screenshot():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com')
        
        # 保存截图到文件
        await tab.take_screenshot('page.png', quality=100)

asyncio.run(take_page_screenshot())
```

### 支持的格式

Pydoll基于文件扩展名支持三种图像格式：

```python
# PNG格式（无损，文件较大）
await tab.take_screenshot('screenshot.png', quality=100)

# JPEG格式（有损，文件较小）
await tab.take_screenshot('screenshot.jpeg', quality=85)

# WebP格式（现代、高效）
await tab.take_screenshot('screenshot.webp', quality=90)
```

!!! info "格式检测"
    图像格式由文件扩展名自动确定。使用不支持的扩展名会引发`InvalidFileExtension`异常。
    
    JPEG格式同时支持`.jpg`和`.jpeg`（`.jpg`会自动在内部标准化为`.jpeg`以匹配CDP要求）。

### 截图参数

| 参数 | 类型 | 默认值 | 描述 |
|-----------|------|---------|-------------|
| `path` | `Optional[str]` | `None` | 保存截图的文件路径。如果`as_base64=False`则为必需。 |
| `quality` | `int` | `100` | 图像质量（0-100）。值越高质量越好，文件越大。 |
| `beyond_viewport` | `bool` | `False` | 捕获整个可滚动页面，而不仅仅是可见区域。 |
| `as_base64` | `bool` | `False` | 返回base64编码的字符串而不是保存到文件。 |

### 完整页面截图

捕获超出可见视口的内容：

```python
async def full_page_screenshot():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/long-page')
        
        # 捕获整个页面，包括折叠下方的内容
        await tab.take_screenshot(
            'full-page.png',
            beyond_viewport=True,
            quality=90
        )
```

!!! warning "性能注意"
    在非常长的页面上使用`beyond_viewport=True`可能会消耗大量内存并需要更长的处理时间。

### Base64截图

获取截图的base64字符串用于嵌入或通过API发送：

```python
async def base64_screenshot():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com')
        
        # 获取截图的base64字符串
        screenshot_base64 = await tab.take_screenshot(
            as_base64=True
        )
        
        # 在HTML img标签中使用
        html = f'<img src="data:image/png;base64,{screenshot_base64}" />'
        
        # 或通过API发送
        import aiohttp
        async with aiohttp.ClientSession() as session:
            await session.post(
                'https://api.example.com/upload',
                json={'image': screenshot_base64}
            )
```

### 元素截图

捕获特定元素而非整个页面：

```python
async def element_screenshot():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com')
        
        # 截取特定元素（PNG）
        header = await tab.find(tag_name='header')
        await header.take_screenshot('header.png', quality=100)
        
        # 截取表单（JPEG）
        form = await tab.find(id='login-form')
        await form.take_screenshot('login-form.jpeg', quality=85)
        
        # 截取图表或图形（WebP）
        chart = await tab.find(class_name='data-visualization')
        await chart.take_screenshot('chart.webp', quality=90)
```

!!! info "格式检测"
    图像格式自动从文件扩展名（`.png`、`.jpeg`/`.jpg`或`.webp`）检测。使用不支持的扩展名会引发`InvalidFileExtension`异常。

!!! tip "自动滚动"
    捕获元素截图时，Pydoll会在截图前自动将元素滚动到视图中。

### 元素截图 vs 页面截图

| 功能 | `tab.take_screenshot()` | `element.take_screenshot()` |
|---------|------------------------|----------------------------|
| **范围** | 整个视口或页面 | 仅特定元素 |
| **格式支持** | PNG, JPEG, WebP | PNG, JPEG, WebP |
| **超出视口** | ✅ 支持 | ❌ 不适用 |
| **Base64输出** | ✅ 支持 | ✅ 支持 |
| **自动滚动** | ❌ 不适用 | ✅ 是 |
| **使用场景** | 完整页面捕获 | 组件隔离、测试 |


## PDF生成

### 基础PDF导出

将页面转换为打印质量的PDF输出：

```python
import asyncio
from pathlib import Path
from pydoll.browser.chromium import Chrome

async def generate_pdf():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/document')
        
        # 使用Path生成PDF
        await tab.print_to_pdf(Path('document.pdf'))
        
        # 或使用字符串
        await tab.print_to_pdf('document.pdf')

asyncio.run(generate_pdf())
```

### PDF参数

| 参数 | 类型 | 默认值 | 描述 |
|-----------|------|---------|-------------|
| `path` | `Optional[str \| Path]` | `None` | 保存PDF的文件路径。如果`as_base64=False`则为必需。 |
| `landscape` | `bool` | `False` | 使用横向方向（相对于纵向）。 |
| `display_header_footer` | `bool` | `False` | 包含浏览器生成的页眉/页脚，带有标题、URL、页码。 |
| `print_background` | `bool` | `True` | 包含背景图形和颜色。 |
| `scale` | `float` | `1.0` | 页面缩放因子（0.1-2.0）。用于放大/缩小效果。 |
| `as_base64` | `bool` | `False` | 返回base64编码的字符串而不是保存到文件。 |

!!! tip "Path vs 字符串"
    虽然推荐使用`pathlib`的`Path`对象作为最佳实践以获得更好的路径处理和跨平台兼容性，但如果您愿意，也可以使用普通字符串。

### 高级PDF选项

```python
import asyncio
from pathlib import Path
from pydoll.browser.chromium import Chrome

async def advanced_pdf():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/report')
        
        # 带页眉/页脚的横向PDF
        await tab.print_to_pdf(
            Path('report-landscape.pdf'),
            landscape=True,
            display_header_footer=True,
            print_background=True,
            scale=0.9
        )
        
        # 无背景的纵向PDF（节省墨水）
        await tab.print_to_pdf(
            Path('report-ink-friendly.pdf'),
            landscape=False,
            print_background=False,
            scale=1.0
        )

asyncio.run(advanced_pdf())
```

### PDF缩放因子

控制PDF输出的缩放级别：

```python
import asyncio
from pathlib import Path
from pydoll.browser.chromium import Chrome

async def scaled_pdfs():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/content')
        
        # 缩小内容以在每页上容纳更多
        await tab.print_to_pdf(Path('compact.pdf'), scale=0.7)
        
        # 正常缩放
        await tab.print_to_pdf(Path('normal.pdf'), scale=1.0)
        
        # 放大内容（页数更少）
        await tab.print_to_pdf(Path('large.pdf'), scale=1.5)

asyncio.run(scaled_pdfs())
```

!!! warning "缩放限制"
    `scale`参数接受`0.1`到`2.0`之间的值。超出此范围的值可能产生意外结果。

### Base64 PDF

生成PDF的base64字符串用于API传输：

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def base64_pdf():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/invoice')
        
        # 获取PDF的base64（无需路径）
        pdf_base64 = await tab.print_to_pdf(as_base64=True)
        
        # 通过API发送
        import aiohttp
        async with aiohttp.ClientSession() as session:
            await session.post(
                'https://api.example.com/invoices',
                json={'pdf': pdf_base64}
            )

asyncio.run(base64_pdf())
```


!!! info "CDP参考"
    有关这些命令的完整CDP文档，请参阅：
    
    - [Page.captureScreenshot](https://chromedevtools.github.io/devtools-protocol/tot/Page/#method-captureScreenshot)
    - [Page.printToPDF](https://chromedevtools.github.io/devtools-protocol/tot/Page/#method-printToPDF)

### 错误处理

```python
from pydoll.exceptions import (
    InvalidFileExtension,
    MissingScreenshotPath,
    TopLevelTargetRequired
)

async def safe_screenshot():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com')
        
        try:
            # 缺少路径且as_base64=False
            await tab.take_screenshot()
        except MissingScreenshotPath:
            print("错误：必须提供路径或设置as_base64=True")
        
        try:
            # 无效的扩展名
            await tab.take_screenshot('image.bmp')
        except InvalidFileExtension as e:
            print(f"错误：{e}")
        
        # IFrame截图限制
        iframe_element = await tab.find(tag_name='iframe')

        # 仍然无效：顶层截图不会包含 iframe 内容
        # await tab.take_screenshot('frame.png')

        # 选择 iframe 内部的元素进行截图
        content = await iframe_element.find(id='content')
        await content.take_screenshot('iframe-content.png')
```

## 页面打包导出

将整个页面及其所有资源（CSS、JS、图片、字体）保存为 `.zip` 压缩包，支持离线查看。

### 基本用法

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def save_page():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com')

        # 将页面和资源保存为独立文件
        await tab.save_bundle('page.zip')

asyncio.run(save_page())
```

生成的 zip 包含一个 `index.html`，所有 URL 已被重写为引用 `assets/` 目录下的本地文件。

### 内联模式

使用 data URI、`<style>` 和 `<script>` 标签将所有内容直接嵌入到单个 `index.html` 中：

```python
# zip 中只包含一个自包含的 HTML 文件
await tab.save_bundle('page-inline.zip', inline_assets=True)
```

### 参数

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `path` | `str \| Path` | *（必填）* | 目标路径，必须以 `.zip` 结尾。 |
| `inline_assets` | `bool` | `False` | 将所有资源内联嵌入，而非保存为独立文件。 |

!!! info "打包包含的内容"
    打包包括以下类型的资源：Document、Stylesheet、Script、Image、Font 和 Media。加载失败、已取消或使用 `data:` URI 的资源会被自动跳过。

## 了解更多

有关截图和PDF如何与Pydoll架构集成的更多信息：

- **[深入探讨：CDP](../../deep-dive/fundamentals/cdp.md)**：理解Chrome DevTools Protocol命令
- **[API参考：Tab](../../api/browser/tab.md#take_screenshot)**：完整的方法签名和参数
- **[API参考：WebElement](../../api/elements/web-element.md#take_screenshot)**：元素特定的截图能力

截图和PDF是自动化、测试和文档编制的必备工具。Pydoll的直接CDP集成提供专业级输出和精细控制。

