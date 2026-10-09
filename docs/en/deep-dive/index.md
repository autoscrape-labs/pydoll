# Deep Dive

The guides show you how to use Pydoll. This section goes into the subjects around it: the background knowledge that makes serious automation work. You don't need any of it to get started, but when a scraper gets blocked, or a proxy behaves strangely, or you want to understand what a detection system actually sees, this is where the explanations live.

It covers three areas:

## Chrome DevTools Protocol

[Chrome DevTools Protocol](cdp.md) is what Pydoll speaks to the browser. Understanding it explains why there is no webdriver, what a CDP command and event are, and where Pydoll's capabilities come from.

## Network and proxies

How traffic actually moves, and how proxies fit in.

- [Network fundamentals](network/network-fundamentals.md): the layers a request passes through, from TCP to TLS to HTTP.
- [HTTP/HTTPS proxies](network/http-proxies.md) and [SOCKS proxies](network/socks-proxies.md): how each proxy type works and when to use it.
- [Proxy detection](network/proxy-detection.md): the signals that give a proxy away.
- [Building a proxy server](network/build-proxy.md): a working proxy from scratch, to understand the mechanics.
- [Legal and ethical use](network/proxy-legal.md): the boundaries worth knowing.

## Fingerprinting

How detection systems identify a browser, layer by layer. This is the theory behind the [Stealth](../stealth/index.md) guides.

- [Network fingerprinting](fingerprinting/network-fingerprinting.md): TCP/IP, TLS (JA3/JA4), and HTTP/2 signatures.
- [Browser fingerprinting](fingerprinting/browser-fingerprinting.md): canvas, WebGL, fonts, and navigator properties.
- [Behavioral fingerprinting](fingerprinting/behavioral-fingerprinting.md): mouse, keyboard, and timing analysis.
