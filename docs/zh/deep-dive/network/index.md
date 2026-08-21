# 网络与 proxy

Proxy 是你改变流量表面来源、以及改变它在链路上呈现方式的手段。用好它们（并理解它们是如何被抓到的）意味着你要清楚一个请求在每一层实际发生了什么。本章节是背景知识；在 Pydoll 中设置 proxy 的方法，见 [Proxy](../../guides/proxies.md) 指南。

## 从这里开始

- [网络基础](network-fundamentals.md)：一个请求所经过的各个层，从 TCP 到 TLS 再到 HTTP，以及一个 proxy 能触及哪一层。

## Proxy 类型

- [HTTP/HTTPS proxy](http-proxies.md)：正向 proxy 与 CONNECT 隧道，各自能看到什么，以及 MITM 拦截如何改变 TLS 指纹。
- [SOCKS proxy](socks-proxies.md)：传输层握手、SOCKS4 与 SOCKS5 的区别、远程 DNS，以及 Chrome 的 SOCKS5 认证局限。

## 检测与机制

- [Proxy 检测](proxy-detection.md)：暴露 proxy 的那些信号，从 IP 信誉到 header 与指纹的不一致。
- [搭建一个 proxy 服务器](build-proxy.md)：用 Python 实现一个最小的 HTTP 和 SOCKS5 proxy，以看清转发到底是怎么回事。
- [合法与合规使用](proxy-legal.md)：服务条款、隐私，以及负责任的爬取。

## 相关内容

- [Proxy](../../guides/proxies.md)：在 Pydoll 中配置 proxy 的实践指南。
- [网络指纹](../fingerprinting/network-fingerprinting.md)：网络层暴露了客户端的哪些信息。
