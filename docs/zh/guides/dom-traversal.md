# DOM 遍历

拿到一个元素后，你常常还需要它周围的元素：它的子元素、兄弟元素、shadow 根内部的元素，或者 iframe 里的内容。本指南讲的是从一个已知起点在 DOM 树中移动。至于如何先定位到那个起始元素，参见[查找元素](element-finding.md)。

<iframe scrolling="no" src="/docs/resources/visuals/dom-traversal-tree.html" aria-label="Move a focus through a DOM tree with parent, child, and sibling methods" style="width: 100%; height: 480px; border: 0;" loading="lazy"></iframe>

## 获取子元素

`get_children_elements()` 返回一个元素的后代。`max_depth` 控制深入的层数（1 表示只取直接子元素），`tag_filter` 只保留你指定的标签。

```python
import asyncio

from pydoll.browser.chromium import Chrome


async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://books.toscrape.com')

        container = await tab.find(class_name='row', tag_name='ol')

        direct = await container.get_children_elements(max_depth=1)
        print(f'{len(direct)} direct children')

        # 向下最多 2 层的后代，仅保留链接
        links = await container.get_children_elements(max_depth=2, tag_filter=['a'])
        print(f'{len(links)} links within two levels')

asyncio.run(main())
```

## 获取兄弟元素

`get_siblings_elements()` 返回与你的元素处于同一层级的元素，不包括它自身。`tag_filter` 把结果收窄到特定标签。

```python
active = await tab.find(class_name='active')

siblings = await active.get_siblings_elements()
print(f'{len(siblings)} siblings')

link_siblings = await active.get_siblings_elements(tag_filter=['a'])
```

## 限定范围的搜索 vs 直接子元素

限定范围的 `find()` 或 `query()` 会搜索一个元素的**所有**后代。当你只想要直接子元素时，使用 CSS 子代组合器 `>` 或一个 XPath 步进，`query()` 都能接受：

```python
container = await tab.find(id='cards')

# 子树中任意位置的每一个 .card
all_cards = await container.find(class_name='card', find_all=True)

# 只有那些作为直接子元素的 .card
direct_cards = await container.query('> .card', find_all=True)
```

当你想探查结构或按标签过滤时，用 `get_children_elements()`；当你想在子树中任意位置匹配特定属性的元素时，用限定范围的 `find()`/`query()`。

## 读取文本和属性

从任何元素上你都能读取它的可见文本和 HTML 属性：

```python
book = await tab.find(class_name='product_pod')

title = await book.find(tag_name='h3')
print(await title.text)                       # 可见文本

link = await title.find(tag_name='a')
print(link.get_attribute('href'))             # 某个属性值
print(link.get_attribute('title'))
```

`text` 是一个可 await 的属性；`get_attribute(name)` 返回属性字符串，属性不存在时返回 `None`。

## shadow DOM {#shadow-dom}

许多组件把内部结构藏在 [shadow 根](https://developer.mozilla.org/en-US/docs/Web/API/Web_components/Using_shadow_DOM)里，常规 DOM 查询看不到它们。先取得 shadow 宿主，获取它的 shadow 根，然后在里面搜索。

```python
host = await tab.find(id='my-component')
shadow = await host.get_shadow_root()

button = await shadow.query('.internal-btn')
await button.click()
```

!!! warning "在 shadow 根内部，用 `query()` 配合 CSS"
    `ShadowRoot` 上不支持 `find()` 和 XPath，会抛出 `NotImplementedError`。搜索 shadow 根时只能用 `query()` 配合 CSS 选择器。

在 shadow 根内部的 `query()` 同样接受 `find_all`、`timeout` 和 `raise_exc` 参数：

```python
items = await shadow.query('.item', find_all=True)
dynamic = await shadow.query('#late', timeout=5, raise_exc=False)
```

Web 组件是可以嵌套的，因此一个 shadow 根里可以包含另一个 shadow 宿主：

```python
outer = await tab.find(tag_name='outer-component')
outer_shadow = await outer.get_shadow_root()

inner = await outer_shadow.query('inner-component')
inner_shadow = await inner.get_shadow_root()

deep = await inner_shadow.query('.deep-btn')
```

### 发现页面上的 shadow 根

当你不知道存在哪些 shadow 根时（比如调试，或者像 Cloudflare Turnstile 这样的动态组件），`find_shadow_roots()` 会返回全部。shadow 宿主经常延迟加载，因此传入 `timeout` 以轮询直到它们出现：

```python
shadow_roots = await tab.find_shadow_roots(timeout=10)

for sr in shadow_roots:
    print(f'mode={sr.mode}, host={sr.host_element}')
    checkbox = await sr.query('input[type="checkbox"]', raise_exc=False)
    if checkbox:
        await checkbox.click()
```

默认情况下，搜索覆盖主文档（包括同源 iframe）。传入 `deep=True` 还可触及跨源 iframe（OOPIF）内部的 shadow 根，Turnstile 这类组件用的正是这种：

```python
shadow_roots = await tab.find_shadow_roots(deep=True, timeout=10)
```

## 在 iframe 内部工作

iframe 有它自己的 DOM 上下文。先找到 iframe 元素，然后在它上面调用 `find()` 或 `query()`；Pydoll 会自动把搜索路由进该框架。对嵌套的 iframe 继续串联即可。

```python
iframe = await tab.query('iframe.embedded-content', timeout=10)

button = await iframe.find(tag_name='button', class_name='submit')
await button.click()

# 嵌套的 iframe
inner = await iframe.find(tag_name='iframe')
link = await inner.find(text='Download PDF')
await link.click()
```

关于完整的 iframe 指南，包括 CAPTCHA 框架和故障排查，参见 [Iframes](iframes.md)。

!!! note "iframe 内部的截图"
    `tab.take_screenshot()` 只捕获顶层页面。要捕获 iframe 内容，找到框架内部的一个元素，然后调用 `element.take_screenshot()`。

## 下一步

- [查找元素](element-finding.md)：定位你从中开始遍历的元素。
- [Iframes](iframes.md)：关于框架上下文的完整指南。
- [结构化提取](structured-extraction.md)：让一个模型替你遍历重复结构。
