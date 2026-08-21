# 深入探究

指南教你如何使用 Pydoll。本章节则深入围绕它的诸多主题：让严肃的自动化真正跑起来所需的背景知识。入门阶段你完全用不到这些，但当一个爬虫被封锁、一个 proxy 行为古怪，或者你想搞清楚一套检测系统实际看到的是什么时，这里就是相关解释的所在。

它涵盖三个领域：

## Chrome DevTools Protocol

[Chrome DevTools Protocol](cdp.md) 是 Pydoll 与浏览器对话所用的协议。理解它，就能明白为什么这里没有 webdriver、CDP 的命令和事件是什么，以及 Pydoll 的各项能力从何而来。

## 网络与 proxy

流量实际是如何流动的，以及 proxy 如何融入其中。

- [网络基础](network/network-fundamentals.md)：一个请求所经过的各个层，从 TCP 到 TLS 再到 HTTP。
- [HTTP/HTTPS proxy](network/http-proxies.md) 和 [SOCKS proxy](network/socks-proxies.md)：每种 proxy 类型如何工作，以及何时使用它们。
- [Proxy 检测](network/proxy-detection.md)：暴露 proxy 的那些信号。
- [搭建一个 proxy 服务器](network/build-proxy.md)：从零实现一个可用的 proxy，以理解其内部机制。
- [合法与合规使用](network/proxy-legal.md)：值得了解的边界。

## 指纹识别

检测系统如何逐层识别一个浏览器。这是 [隐匿](../stealth/index.md) 系列指南背后的理论。

- [网络指纹](fingerprinting/network-fingerprinting.md)：TCP/IP、TLS（JA3/JA4）和 HTTP/2 签名。
- [浏览器指纹](fingerprinting/browser-fingerprinting.md)：canvas、WebGL、字体和 navigator 属性。
- [行为指纹](fingerprinting/behavioral-fingerprinting.md)：鼠标、键盘和时序分析。
