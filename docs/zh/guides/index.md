# 指南

每项能力对应一篇指南，都配有可运行的示例。如果你是新手，请从 [核心概念](core-concepts.md) 开始，或者直接跳到你需要的任务。

## 核心概念

- [核心概念](core-concepts.md)：tab 和 browser 对象、异步模型，以及“无 webdriver”在实践中意味着什么。

## 查找与提取

- [元素查找](element-finding.md)：用 `find()`（按属性）和 `query()`（CSS 或 XPath）定位元素。
- [DOM 遍历](dom-traversal.md)：从一个元素移动到它的子元素、兄弟元素和 shadow root。
- [结构化提取](structured-extraction.md)：用模型从页面中提取带类型、经校验的数据。

## 交互

- [键盘](keyboard.md)：以拟人化的节奏输入文本、按下按键。
- [鼠标](mouse.md)：点击元素或直接操作原始坐标，配合拟人化的移动。
- [文件操作](file-operations.md)：上传文件、处理下载。
- [Iframe](iframes.md)：查找并操作 frame 内部的元素。
- [截图与 PDF](screenshots-and-pdfs.md)：截取页面、某个元素，或生成 PDF。

## 网络

- [网络监控](network-monitoring.md)：实时观察请求和响应。
- [请求拦截](request-interception.md)：拦截、修改或模拟请求。
- [浏览器上下文中的 HTTP 请求](http-requests.md)：在浏览器会话中调用 API，沿用它的 cookies 和认证。
- [HAR 录制](network-recording.md)：把一次会话录制成 HAR 文件。

## 管理浏览器

- [标签页](tabs.md)：同时打开、关闭并操作多个标签页。
- [浏览器上下文](browser-contexts.md)：一个浏览器内相互隔离的会话，每个都有独立的 cookies。
- [Cookies 与会话](cookies-and-sessions.md)：读取、设置 cookies，并在多次运行间保持它们。
- [浏览器选项](browser-options.md)：命令行 flag、headless 以及启动配置。
- [浏览器偏好设置](browser-preferences.md)：Chromium 内部的偏好设置字典。
- [Proxy](proxies.md)：让流量经过 proxy，并处理认证。
- [远程连接](remote-connections.md)：接入一个已在运行的浏览器。

## 响应事件

- [事件](events.md)：在页面和网络事件触发时运行回调。
- [重试](retrying.md)：用 `retry` 装饰器重试不稳定的步骤。

## 下一步

- [保持不被检测](../stealth/index.md)：拟人化行为、captcha 处理与 fingerprint。
- [API 参考](../api/index.md)：每一个公开类和方法。
