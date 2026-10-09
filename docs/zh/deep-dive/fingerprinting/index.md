# Fingerprinting

Fingerprinting 是网站在没有 cookie 或 IP 地址的情况下识别浏览器的手段，它读取连接本身暴露出的各种特征。单独看，每个特征都无害；组合起来，它们就能识别一台设备或一个浏览器实例，并且当各部分对不上时，会暴露出自动化的痕迹。

本章是 [Stealth](../../stealth/index.md) 指南背后的理论。在实践中你并不需要它就能保持不被发现，但它解释了检测系统究竟测量了什么，以及为什么单个不一致就会暴露你。

## 检测发生在三个层次

一个请求会在三个层次上被 fingerprint，现代反机器人系统会把它们全部关联起来：

- **网络（Network）**：TCP/IP 栈、TLS 握手和 HTTP/2 设置，这些都在任何 JavaScript 运行之前就被读取。
- **浏览器（Browser）**：canvas 和 WebGL 渲染、字体、音频以及 `navigator` 属性，在页面加载后被读取。
- **行为（Behavioral）**：鼠标移动、按键时序和滚动模式，在你交互时被读取。

这些层次会被交叉核对。一个 Chrome 的 User-Agent 却搭配着 Firefox 的 TLS fingerprint，或者一个完美的浏览器 fingerprint 配上机械般的鼠标移动，都会被任何比对信号的系统抓住。三个层次之间的一致性，比其中任何单个层次的完美更重要。

!!! note "核心规则"
    每一层都必须讲同一个故事。如果你的 TLS fingerprint 说是 Chrome 120，那么你的 HTTP/2 设置、你的 User-Agent 以及你渲染出的 canvas 也都必须说是 Chrome 120。一处矛盾就足以标记这个会话。

## 深入三个层次

- [Network fingerprinting](network-fingerprinting.md)：在渲染之前，于传输层和会话层进行识别。TCP/IP（TTL、窗口大小、选项顺序）、TLS（JA3/JA4、cipher suites、ALPN）以及 HTTP/2（SETTINGS、优先级）。这是最难改变的一层，因为它来自操作系统和真实的二进制程序。
- [Browser fingerprinting](browser-fingerprinting.md)：通过 JavaScript API 和渲染进行识别。来自真实 GPU 的 canvas 与 WebGL 痕迹、音频、字体枚举以及 `navigator` 属性。大多数检测事件都落在这一层。
- [Behavioral fingerprinting](behavioral-fingerprinting.md)：从你如何交互来识别。鼠标轨迹与速度、按键节奏以及滚动动态，有时会由在大型行为数据集上训练的模型来打分。即使其他层次都干净，它也能抓住自动化。

## 相关内容

本章解释的是检测。关于 Pydoll 对此做了什么以及你能控制哪些杠杆，请参见 Stealth 指南：

- [Evasion techniques](../../stealth/evasion-techniques.md)：Pydoll 免费给你的东西，以及如何保持各层次一致。
- [Fingerprint injection](../../stealth/fingerprint-injection.md)：在各层次之间应用一致的身份。
- [Human-like interactions](../../stealth/human-like-interactions.md)：行为层。

!!! warning "没有哪一层能让你无法被检测"
    Fingerprinting 知识能缩小差距；它无法消除差距。把一层做对，却让另一层与它矛盾，比一个未经修改的浏览器还要糟糕。请把它当作理解你所面对之物的工具，而不是一种保证。
