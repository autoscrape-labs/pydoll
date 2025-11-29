# 元素mixins

mixins 模块提供可复用的功能，可以将其混合到元素类中以扩展其功能。

## 元素定位mixins

`FindElementsMixin` 为包含它的类提供元素查找功能。

::: pydoll.elements.mixins.find_elements_mixin
    options:
      show_root_heading: true
      show_source: false
      heading_level: 2
      filters:
        - "!^_"
        - "!^__"

## 用法

Mixin 通常由库内部使用，用于组合功能。`Tab` 和 `WebElement` 等类使用 `FindElementsMixin` 来提供元素定位方法：

```python
# 这些方法来自 FindElementsMixin
element = await tab.find(id="username")
elements = await tab.find(class_name="item", find_all=True)
element = await tab.query("#submit-button")
```


## 可用方法

`FindElementsMixin` 提供了多种元素定位的方法：

- `find()` - 使用关键字参数的现代元素查找方法
- `query()` - CSS 选择器和 XPath 查询
- `find_element()` - 旧版元素定位方法
- `find_elements()` - 查找多个元素的旧版方法

!!! 提示“现代 vs 传统”
`find()` 方法是最新的、推荐的查找元素的方法。`find_element()` 和 `find_elements()` 方法保留下来，以实现向后兼容。