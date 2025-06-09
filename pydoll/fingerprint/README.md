# Pydoll Browser Fingerprint Spoofing

## 概述

Pydoll 的指纹伪装功能为您提供了一套完整的浏览器指纹防护解决方案。通过生成随机但真实的浏览器指纹，它能够有效防止网站通过指纹技术追踪您的浏览行为。

## 主要特性

- 🎭 **一键启用** - 只需设置一个参数即可启用指纹伪装
- 🔄 **智能生成** - 自动生成随机但真实的浏览器指纹
- 🛡️ **全面防护** - 覆盖所有主流指纹技术（User-Agent、WebGL、Canvas、音频等）
- 💾 **指纹持久化** - 支持保存和重用指纹配置
- ⚙️ **高度可定制** - 支持自定义各种浏览器属性
- 🚀 **自动注入** - 使用 CDP 自动注入脚本，无需手动操作

## 快速开始

### 基础用法

```python
import asyncio
from pydoll.fingerprint import Chrome

async def basic_example():
    # 启用指纹伪装只需要设置一个参数
    async with Chrome(enable_fingerprint_spoofing=True) as browser:
        tab = await browser.start()
        
        # 正常使用浏览器，指纹伪装自动生效
        await tab.go_to('https://fingerprintjs.github.io/fingerprintjs/')
        
        # 查看生成的指纹信息
        summary = browser.get_fingerprint_summary()
        print("当前指纹:", summary)

asyncio.run(basic_example())
```

### 自定义配置

```python
from pydoll.fingerprint import Chrome, FingerprintConfig

async def custom_example():
    # 创建自定义指纹配置
    config = FingerprintConfig(
        browser_type="chrome",
        preferred_os="windows",  # 强制使用 Windows
        min_screen_width=1920,   # 固定屏幕分辨率
        max_screen_width=1920,
        min_screen_height=1080,
        max_screen_height=1080,
        enable_webgl_spoofing=True,
        enable_canvas_spoofing=True,
        enable_audio_spoofing=True,
    )
    
    async with Chrome(
        enable_fingerprint_spoofing=True,
        fingerprint_config=config
    ) as browser:
        tab = await browser.start()
        await tab.go_to('https://amiunique.org/fp')

asyncio.run(custom_example())
```

### Edge 浏览器支持

```python
from pydoll.fingerprint import Edge

async def edge_example():
    # Edge 浏览器也支持指纹伪装
    async with Edge(enable_fingerprint_spoofing=True) as browser:
        tab = await browser.start()
        await tab.go_to('https://browserleaks.com/javascript')

asyncio.run(edge_example())
```

## 高级功能

### 指纹持久化

```python
async def persistence_example():
    # 第一次会话：生成并保存指纹
    async with Chrome(enable_fingerprint_spoofing=True) as browser:
        tab = await browser.start()
        
        # 保存当前指纹
        if browser.fingerprint_manager:
            path = browser.fingerprint_manager.save_fingerprint("my_identity")
            print(f"指纹已保存到: {path}")
    
    # 第二次会话：重用保存的指纹
    async with Chrome(enable_fingerprint_spoofing=True) as browser:
        if browser.fingerprint_manager:
            browser.fingerprint_manager.load_fingerprint("my_identity")
            print("已加载保存的指纹")
        
        tab = await browser.start()
        await tab.go_to('https://fingerprintjs.github.io/fingerprintjs/')

asyncio.run(persistence_example())
```

### 指纹管理

```python
from pydoll.fingerprint import FingerprintManager, FingerprintConfig

# 直接使用指纹管理器
manager = FingerprintManager()

# 生成多个不同的指纹
for i in range(3):
    fingerprint = manager.generate_new_fingerprint(force=True)
    manager.save_fingerprint(f"fingerprint_{i}")
    print(f"指纹 {i}: {fingerprint.user_agent}")

# 查看所有保存的指纹
saved_fingerprints = manager.list_saved_fingerprints()
print("已保存的指纹:", saved_fingerprints)

# 删除指纹
manager.delete_fingerprint("fingerprint_0")
```

## 配置选项

### FingerprintConfig 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `browser_type` | str | "chrome" | 浏览器类型 ("chrome" 或 "edge") |
| `is_mobile` | bool | False | 是否模拟移动设备 |
| `preferred_os` | str | None | 首选操作系统 ("windows", "macos", "linux") |
| `preferred_languages` | List[str] | None | 首选语言列表 |
| `min_screen_width` | int | 1024 | 最小屏幕宽度 |
| `max_screen_width` | int | 2560 | 最大屏幕宽度 |
| `min_screen_height` | int | 768 | 最小屏幕高度 |
| `max_screen_height` | int | 1440 | 最大屏幕高度 |
| `enable_webgl_spoofing` | bool | True | 启用 WebGL 伪装 |
| `enable_canvas_spoofing` | bool | True | 启用 Canvas 伪装 |
| `enable_audio_spoofing` | bool | True | 启用音频伪装 |
| `include_plugins` | bool | True | 包含插件信息 |
| `enable_webrtc_spoofing` | bool | True | 启用 WebRTC 伪装 |

## 伪装的指纹技术

本模块能够伪装以下指纹技术：

### 🔧 Navigator 属性
- User-Agent 字符串
- 平台信息 (platform)
- 语言设置 (language, languages)
- 硬件并发数 (hardwareConcurrency)
- 设备内存 (deviceMemory)
- Cookie 启用状态

### 🖥️ 屏幕和窗口属性
- 屏幕分辨率 (screen.width/height)
- 可用屏幕区域 (screen.availWidth/availHeight)
- 颜色深度 (colorDepth, pixelDepth)
- 窗口内部尺寸 (innerWidth/innerHeight)
- 窗口外部尺寸 (outerWidth/outerHeight)

### 🎨 WebGL 指纹
- WebGL 供应商信息 (VENDOR)
- WebGL 渲染器信息 (RENDERER)
- WebGL 版本信息
- 支持的 WebGL 扩展列表

### 🖼️ Canvas 指纹
- Canvas 绘制结果伪装
- 图像数据噪声注入

### 🔊 音频指纹
- AudioContext 采样率
- 音频上下文状态
- 最大声道数

### 🌍 地理和时区
- 时区设置
- 时区偏移量
- 国际化 API (Intl)

### 🔌 插件信息
- 浏览器插件列表
- 插件详细信息

### 🛡️ 自动化检测防护
- 移除 `navigator.webdriver` 属性
- 清除 Selenium 相关标识
- 隐藏 WebDriver 自动化痕迹
- 覆盖 `toString` 方法以隐藏修改

## 工作原理

### 1. 命令行级防护
当启用指纹伪装时，系统会自动添加以下浏览器启动参数：
- 自定义 User-Agent
- 语言设置
- 硬件并发数
- 视口大小
- 禁用自动化检测功能

### 2. JavaScript 级防护
浏览器启动后，系统会自动注入 JavaScript 脚本，修改或覆盖以下浏览器特性：
- Navigator 对象属性
- Screen 对象属性  
- WebGL 参数和渲染信息
- Canvas 绘制行为
- AudioContext 音频处理
- 浏览器插件列表
- 时区和地理信息

### 3. 每次会话的唯一指纹
每次创建新的浏览器实例时，系统都会生成全新的随机指纹。这确保了即使多次访问同一网站，每次访问都会被识别为不同的访客。

## 验证效果

访问以下网站测试指纹伪装效果：

1. **FingerprintJS**: https://fingerprintjs.github.io/fingerprintjs/
2. **AmIUnique**: https://amiunique.org/fp  
3. **BrowserLeaks**: https://browserleaks.com/javascript

如果指纹伪装成功，使用不同浏览器实例访问这些网站应该会生成不同的指纹 ID。

## 最佳实践

1. **定期更换指纹**: 虽然每次会话都会生成新指纹，但对于长期使用建议定期手动生成新指纹。

2. **合理配置**: 根据目标网站的特点选择合适的指纹配置，避免过于异常的指纹组合。

3. **指纹一致性**: 在同一个浏览会话中保持指纹一致，避免在页面跳转过程中指纹发生变化。

4. **保存重要指纹**: 对于需要保持身份一致性的场景，及时保存和重用指纹。

## 注意事项

- 指纹伪装不能保证 100% 防止所有指纹识别技术，但能有效对抗大部分常见的指纹方法。
- 某些高级指纹技术可能绕过常规伪装方法，如有需要可以注入额外的自定义保护脚本。
- 指纹伪装可能与某些网站功能产生冲突，在此情况下可以选择性禁用某些伪装功能。

## 许可证

本功能基于 MIT 许可证发布，与 pydoll 项目许可证保持一致。 