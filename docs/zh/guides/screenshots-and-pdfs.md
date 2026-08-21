# 截图和 PDF

捕获页面的样子：整页或单个元素的截图，或者把整个页面导出为 PDF。Pydoll 驱动的是 Chrome 自身的渲染，所以输出与浏览器所显示的一致，你也不用运行单独的渲染工具。

## 给页面截图

用一个文件路径调用 `take_screenshot()`。扩展名决定格式。

```python
import asyncio

from pydoll.browser.chromium import Chrome


async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://en.wikipedia.org/wiki/Python_(programming_language)')

        await tab.take_screenshot('python.png')

asyncio.run(main())
```

<p align="center">
  <img src="/docs/resources/images/screenshot-python-wikipedia.png" alt="Pydoll 捕获的 Wikipedia Python 文章" width="760" />
</p>
<p align="center"><sub>生成的 python.png：Pydoll 捕获的 Wikipedia 文章。</sub></p>

### 选择格式

格式跟随文件扩展名：PNG（无损）、JPEG（更小，有损）或 WebP。`quality` 取值 0 到 100，适用于有损格式。

```python
await tab.take_screenshot('page.png')               # 无损
await tab.take_screenshot('page.jpeg', quality=85)  # 更小的文件
await tab.take_screenshot('page.webp', quality=90)
```

!!! note "格式来自扩展名"
    不支持的扩展名会抛出 `InvalidFileExtension`。`.jpg` 和 `.jpeg` 都可用；`.jpg` 在内部会被规范化为 `.jpeg`。

### 捕获整个可滚动页面

默认你得到的是可见的视口。传入 `beyond_viewport=True` 可捕获折叠线以下、一直到底的所有内容。

```python
await tab.take_screenshot('full-article.png', beyond_viewport=True)
```

!!! warning "长页面消耗内存"
    在非常长的页面上，`beyond_viewport=True` 耗时更久、占用更多内存，因为整个页面是一次性渲染的。

### 在内存中获取图像

传入 `as_base64=True` 可拿回一个 base64 字符串，而不写文件。用它来嵌入图像或把它发到别处，没有临时文件需要清理。

```python
data = await tab.take_screenshot(as_base64=True)

html = f'<img src="data:image/png;base64,{data}" />'
```

## 给单个元素截图

在一个元素上调用 `take_screenshot()`，只捕获那个元素。Pydoll 会先把它滚动到可见区域。

```python
await tab.go_to('https://en.wikipedia.org/wiki/Python_(programming_language)')

infobox = await tab.find(class_name='infobox')
await infobox.take_screenshot('infobox.png')
```

这也是你捕获 iframe 内部内容的方式：`tab.take_screenshot()` 只能看到顶层页面，所以找到框架内部的一个元素，改为给它截图。

```python
iframe = await tab.find(tag_name='iframe')
content = await iframe.find(id='content')
await content.take_screenshot('iframe-content.png')
```

| | `tab.take_screenshot()` | `element.take_screenshot()` |
|---|---|---|
| 范围 | 视口或整页 | 单个元素 |
| `beyond_viewport` | 支持 | 不适用 |
| `as_base64` | 支持 | 支持 |
| 滚动到可见区域 | 否 | 是 |
| 能触及 iframe 内容 | 否 | 是 |

## 把页面导出为 PDF

`print_to_pdf()` 通过 Chrome 的打印管线渲染页面。传入一个路径，或者用 `as_base64=True` 得到内存中的字节。

```python
import asyncio
from pathlib import Path

from pydoll.browser.chromium import Chrome


async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://en.wikipedia.org/wiki/Python_(programming_language)')

        await tab.print_to_pdf(Path('python.pdf'))

asyncio.run(main())
```

### 控制输出

| 参数 | 默认值 | 作用 |
|---|---|---|
| `path` | `None` | 保存位置。除非 `as_base64=True`，否则必填。 |
| `landscape` | `False` | 横向而非纵向。 |
| `display_header_footer` | `False` | 添加 Chrome 的标题、URL 和页码。 |
| `print_background` | `True` | 包含背景图形和颜色。 |
| `scale` | `1.0` | 缩放系数，0.1 到 2.0。小于 1.0 时每页容纳更多内容。 |
| `as_base64` | `False` | 返回一个 base64 字符串，而不写文件。 |

```python
# 带页眉页脚、略微缩小的横向报告
await tab.print_to_pdf(
    Path('report.pdf'),
    landscape=True,
    display_header_footer=True,
    scale=0.9,
)

# 省墨：不带背景图形
await tab.print_to_pdf(Path('draft.pdf'), print_background=False)

# 内存中的字节，不写文件
pdf_data = await tab.print_to_pdf(as_base64=True)
```

## 保存页面以供离线查看

`save_bundle()` 把页面及其资源（CSS、JS、图片、字体、媒体）写入一个 `.zip`，你可以稍后打开。归档中包含一个 `index.html`，其中的 URL 已被改写为指向本地文件。

```python
await tab.save_bundle('page.zip')
```

传入 `inline_assets=True`，可用 data URI 以及内联的 `<style>`/`<script>` 标签把一切嵌入到单个自包含的 `index.html` 中：

```python
await tab.save_bundle('page-inline.zip', inline_assets=True)
```

!!! note "哪些内容会被打包"
    文档、样式表、脚本、图片、字体和媒体。加载失败、被取消或使用 `data:` URI 的资源会被跳过。

## 处理常见错误

```python
from pydoll.exceptions import InvalidFileExtension, MissingScreenshotPath

# 没有路径且 as_base64 为 False
try:
    await tab.take_screenshot()
except MissingScreenshotPath:
    print('Pass a path, or set as_base64=True.')

# 不支持的扩展名
try:
    await tab.take_screenshot('image.bmp')
except InvalidFileExtension as error:
    print(error)
```

## 下一步

- [DOM 遍历](dom-traversal.md)：找到你想截图的元素，包括 iframe 内部的。
- [Iframes](iframes.md)：深入处理框架内容。
- [Tab API 参考](../api/browser/tab.md)：`take_screenshot`、`print_to_pdf` 和 `save_bundle` 的完整签名。
