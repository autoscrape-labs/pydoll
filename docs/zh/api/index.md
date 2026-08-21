# API Reference

本节记录你直接使用的公共类。指南教你如何使用它们；本参考说明每个类暴露了什么。每个页面都会链接回对应的指南。

## 浏览器

| 类 | 作用 | 指南 |
|----|------|------|
| [`Chrome`](browser/chrome.md) | 启动并控制 Chrome 浏览器 | [快速上手](../getting-started.md) |
| [`Edge`](browser/edge.md) | 启动并控制 Microsoft Edge 浏览器 | [快速上手](../getting-started.md) |
| [`ChromiumOptions`](browser/options.md) | 在启动前配置浏览器 | [浏览器选项](../guides/browser-options.md) |
| [`Tab`](browser/tab.md) | 驱动标签页：导航、查找、输入、事件、网络 | [核心概念](../guides/core-concepts.md) |
| [`Request`](browser/requests.md) | 在浏览器会话内发起 HTTP 请求 | [HTTP 请求](../guides/http-requests.md) |

## 元素

| 类 | 作用 | 指南 |
|----|------|------|
| [`WebElement`](elements/web_element.md) | 与已定位的元素交互 | [查找元素](../guides/element-finding.md) |
| [`ShadowRoot`](elements/shadow_root.md) | 在 shadow root 内部查询 | [DOM 遍历](../guides/dom-traversal.md#shadow-dom) |

## 提取与连接

| 类 | 作用 | 指南 |
|----|------|------|
| [`ExtractionModel`, `Field`](extraction.md) | 将 DOM 映射为类型化、经过校验的对象 | [结构化提取](../guides/structured-extraction.md) |
| [`ConnectionHandler`](connection/connection.md) | 管理 CDP 的 WebSocket 连接 | [远程连接](../guides/remote-connections.md) |

## 核心

| 参考 | 内容 | 指南 |
|------|------|------|
| [Constants](core/constants.md) | `By`、`Key`、`PermissionType` 等枚举 | [选择器](../basics/selectors.md) |
| [Exceptions](core/exceptions.md) | Pydoll 抛出的错误，如 `ElementNotFound` | [查找元素](../guides/element-finding.md#handle-missing-elements) |

Pydoll 的每个操作都是异步且完全类型化的。异步基础请见 [Async Python](../basics/async-python.md)。
