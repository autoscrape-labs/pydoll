# 自定义浏览器首选项

Pydoll 最强大的功能之一是直接访问 Chromium 的内部首选项系统。与传统的浏览器自动化工具只公开有限的选项不同，Pydoll 为您提供与扩展程序和企业管理员相同级别的控制权，允许您配置 Chromium 源代码中提供的**任何**浏览器设置。

## 为什么浏览器首选项很重要

浏览器首选项控制 Chromium 行为的方方面面：

- **性能**：禁用不需要的功能以加快页面加载速度
- **隐私**：控制浏览器收集和发送的数据
- **自动化**：删除破坏工作流程的用户提示和确认
- **隐身**：创建逼真的浏览器指纹以避免检测
- **企业**：应用通常只能通过组策略获得的策略

!!! info "直接访问的力量"
    大多数自动化工具只公开 10-20 个常见设置。Pydoll 为您提供**数百个**首选项的访问权限，从下载行为到搜索建议，从网络预测到插件管理。如果 Chromium 可以做到，您就可以配置它。

## 快速开始

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

async def preferences_example():
    options = ChromiumOptions()
    
    # 使用字典设置首选项
    options.browser_preferences = {
        'download': {
            'default_directory': '/tmp/downloads',
            'prompt_for_download': False
        },
        'profile': {
            'default_content_setting_values': {
                'notifications': 2  # 阻止通知
            }
        }
    }
    
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com')
        
        # 下载自动保存到 /tmp/downloads
        # 不会出现通知提示

asyncio.run(preferences_example())
```

## 了解浏览器首选项

### 什么是首选项？

Chromium 将所有用户可配置的设置存储在一个名为 `Preferences` 的 JSON 文件中，该文件位于浏览器的用户数据目录中。此文件包含**所有内容**，从您的主页 URL 到图像是否自动加载。

**典型位置：**

- **Linux**: `~/.config/google-chrome/Default/Preferences`
- **macOS**: `~/Library/Application Support/Google/Chrome/Default/Preferences`
- **Windows**: `%LOCALAPPDATA%\Google\Chrome\User Data\Default\Preferences`

### 首选项文件结构

首选项文件是一个嵌套的 JSON 对象：

```json
{
  "download": {
    "default_directory": "/home/user/Downloads",
    "prompt_for_download": true
  },
  "profile": {
    "default_content_setting_values": {
      "notifications": 1,
      "popups": 0
    },
    "password_manager_enabled": true
  },
  "search": {
    "suggest_enabled": true
  },
  "net": {
    "network_prediction_options": 1
  }
}
```

Chromium 源代码中的每个点分隔的首选项名称都映射到嵌套的 JSON 路径：

- `download.default_directory` → `{'download': {'default_directory': ...}}`
- `profile.password_manager_enabled` → `{'profile': {'password_manager_enabled': ...}}`

### Chromium 如何使用首选项

当 Chromium 启动时：

1. **读取**磁盘上的首选项文件
2. **应用**这些设置来配置浏览器行为
3. **更新**用户通过 UI 更改设置时的文件
4. **回退**到默认值（如果缺少首选项）

Pydoll 通过在浏览器启动前预填充首选项文件来拦截步骤 1，确保您的自定义设置从第一次页面加载开始就被应用。

## 在 Pydoll 中的工作原理

### 设置首选项

使用 `browser_preferences` 属性设置任何首选项：

```python
from pydoll.browser.options import ChromiumOptions

options = ChromiumOptions()

# 直接赋值 - 与现有首选项合并
options.browser_preferences = {
    'download': {'default_directory': '/tmp'},
    'intl': {'accept_languages': 'pt-BR,en-US'}
}

# 多次赋值会合并，而不是替换
options.browser_preferences = {
    'profile': {'password_manager_enabled': False}
}

# 现在两组首选项都处于活动状态
```

!!! warning "首选项是合并的，而不是替换的"
    当您多次设置 `browser_preferences` 时，新首选项会与现有首选项**合并**。只有您设置的特定键会被更新；其他所有内容都会保留。
    
    ```python
    options.browser_preferences = {'download': {'prompt': False}}
    options.browser_preferences = {'profile': {'password_manager_enabled': False}}
    
    # 结果：两个首选项都已设置
    # {'download': {'prompt': False}, 'profile': {'password_manager_enabled': False}}
    ```

### 嵌套路径语法

首选项使用嵌套字典，镜像 Chromium 的点表示法：

```python
# Chromium 源代码常量：
# const char kDownloadDefaultDirectory[] = "download.default_directory";

# 转换为 Python 字典：
options.browser_preferences = {
    'download': {
        'default_directory': '/path/to/downloads'
    }
}
```

嵌套越深，首选项越具体：

```python
# 顶层：profile
# 第二层：default_content_setting_values  
# 第三层：notifications

options.browser_preferences = {
    'profile': {
        'default_content_setting_values': {
            'notifications': 2,  # 阻止
            'geolocation': 2,    # 阻止
            'media_stream': 2    # 阻止
        }
    }
}
```

## 实际用例

### 1. 性能优化

禁用资源密集型功能以实现更快的自动化：

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

async def performance_optimized_browser():
    options = ChromiumOptions()
    options.browser_preferences = {
        # 禁用网络预测和预取
        'net': {
            'network_prediction_options': 2  # 2 = 从不预测
        },
        # 禁用图像加载
        'profile': {
            'default_content_setting_values': {
                'images': 2  # 2 = 阻止，1 = 允许
            }
        },
        # 禁用插件
        'webkit': {
            'webprefs': {
                'plugins_enabled': False
            }
        },
        # 禁用拼写检查
        'browser': {
            'enable_spellchecking': False
        }
    }
    
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        
        # 在没有图像和不必要功能的情况下，页面加载速度提高 3-5 倍
        await tab.go_to('https://example.com')
        print("快速加载完成！")

asyncio.run(performance_optimized_browser())
```

!!! tip "性能影响"
    仅禁用图像就可以将图像密集型网站的页面加载时间减少 50-70%。结合禁用预取、拼写检查和插件，可实现最大速度。

### 2. 隐私与反跟踪

创建注重隐私的浏览器配置：

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

async def privacy_focused_browser():
    options = ChromiumOptions()
    options.browser_preferences = {
        # 启用请勿跟踪
        'enable_do_not_track': True,
        
        # 禁用引荐来源
        'enable_referrers': False,
        
        # 禁用安全浏览（将 URL 发送到 Google）
        'safebrowsing': {
            'enabled': False
        },
        
        # 禁用密码管理器
        'profile': {
            'password_manager_enabled': False
        },
        
        # 禁用自动填充
        'autofill': {
            'enabled': False,
            'profile_enabled': False
        },
        
        # 禁用搜索建议（将查询发送到搜索引擎）
        'search': {
            'suggest_enabled': False
        },
        
        # 禁用遥测和指标
        'user_experience_metrics': {
            'reporting_enabled': False
        },
        
        # 阻止第三方 cookie
        'profile': {
            'block_third_party_cookies': True,
            'cookie_controls_mode': 1
        }
    }
    
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com')
        print("注重隐私的浏览器已准备就绪！")

asyncio.run(privacy_focused_browser())
```

### 3. 静默下载

自动化文件下载，无需用户交互：

```python
import asyncio
from pathlib import Path
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

async def silent_download_automation():
    download_dir = Path.home() / 'automation_downloads'
    download_dir.mkdir(exist_ok=True)
    
    options = ChromiumOptions()
    options.browser_preferences = {
        'download': {
            'default_directory': str(download_dir),
            'prompt_for_download': False,
            'directory_upgrade': True
        },
        'profile': {
            'default_content_setting_values': {
                'automatic_downloads': 1  # 1 = 允许，2 = 阻止
            }
        },
        # 始终下载 PDF 而不是在查看器中打开
        'plugins': {
            'always_open_pdf_externally': True
        }
    }
    
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/downloads')
        
        # 点击下载链接 - 文件自动保存
        download_link = await tab.find(text='Download Report')
        await download_link.click()
        
        await asyncio.sleep(3)
        print(f"文件已下载到：{download_dir}")

asyncio.run(silent_download_automation())
```

### 4. 阻止侵入性 UI 元素

删除破坏自动化的弹出窗口、通知和提示：

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

async def clean_ui_browser():
    options = ChromiumOptions()
    options.browser_preferences = {
        'profile': {
            'default_content_setting_values': {
                'notifications': 2,      # 阻止通知
                'popups': 0,             # 阻止弹出窗口
                'geolocation': 2,        # 阻止位置请求
                'media_stream': 2,       # 阻止摄像头/麦克风访问
                'media_stream_mic': 2,   # 阻止麦克风
                'media_stream_camera': 2 # 阻止摄像头
            }
        },
        # 禁用翻译提示
        'translate': {
            'enabled': False
        },
        # 禁用保存密码提示
        'credentials_enable_service': False,
        
        # 禁用"Chrome 正在被自动化软件控制"信息栏
        'devtools': {
            'preferences': {
                'currentDockState': '"undocked"'
            }
        }
    }
    
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com')
        # 没有弹出窗口，没有提示，干净的自动化！

asyncio.run(clean_ui_browser())
```

### 5. 国际化与本地化

配置语言和区域设置首选项：

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

async def localized_browser():
    options = ChromiumOptions()
    options.browser_preferences = {
        # 接受语言（优先顺序）
        'intl': {
            'accept_languages': 'pt-BR,pt,en-US,en'
        },
        
        # 拼写检查语言
        'spellcheck': {
            'dictionaries': ['pt-BR', 'en-US']
        },
        
        # 翻译设置
        'translate': {
            'enabled': True
        },
        'translate_blocked_languages': ['en'],  # 不提供翻译英语
        
        # 默认字符编码
        'default_charset': 'UTF-8'
    }
    
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com')
        # 为巴西葡萄牙语配置的浏览器

asyncio.run(localized_browser())
```

## 辅助方法

对于常见场景，Pydoll 提供便利方法：

```python
from pydoll.browser.options import ChromiumOptions

options = ChromiumOptions()

# 下载管理
options.set_default_download_directory('/tmp/downloads')
options.prompt_for_download = False
options.allow_automatic_downloads = True
options.open_pdf_externally = True

# 内容阻止
options.block_notifications = True
options.block_popups = True

# 隐私
options.password_manager_enabled = False

# 国际化
options.set_accept_languages('pt-BR,en-US,en')
```

这些方法是为您设置正确嵌套首选项的快捷方式：

```python
# 这个辅助方法：
options.set_default_download_directory('/tmp')

# 等同于：
options.browser_preferences = {
    'download': {
        'default_directory': '/tmp'
    }
}
```

!!! tip "将辅助方法与直接首选项结合使用"
    使用辅助方法处理常见设置，使用 `browser_preferences` 处理高级配置：
    
    ```python
    # 从辅助方法开始
    options.block_notifications = True
    options.prompt_for_download = False
    
    # 添加高级首选项
    options.browser_preferences = {
        'net': {'network_prediction_options': 2},
        'webkit': {'webprefs': {'plugins_enabled': False}}
    }
    ```

## 在 Chromium 源代码中查找首选项

### 源代码参考

Chromium 在 `pref_names.cc` 中定义所有首选项常量：

**官方源代码**：[chromium/src/+/main/chrome/common/pref_names.cc](https://chromium.googlesource.com/chromium/src/+/main/chrome/common/pref_names.cc)

### 阅读源代码

首选项常量使用点表示法，直接映射到嵌套字典：

```cpp
// 来自 Chromium 源代码 (pref_names.cc)：
const char kDownloadDefaultDirectory[] = "download.default_directory";
const char kPromptForDownload[] = "download.prompt_for_download";
const char kSafeBrowsingEnabled[] = "safebrowsing.enabled";
const char kBlockThirdPartyCookies[] = "profile.block_third_party_cookies";
```

**转换为 Python：**

```python
options.browser_preferences = {
    'download': {
        'default_directory': '/path/to/dir',
        'prompt_for_download': False
    },
    'safebrowsing': {
        'enabled': False
    },
    'profile': {
        'block_third_party_cookies': True
    }
}
```

### 发现过程

1. **搜索源代码**：访问 [pref_names.cc](https://chromium.googlesource.com/chromium/src/+/main/chrome/common/pref_names.cc)
2. **找到您的首选项**：搜索关键字（例如 "download"、"password"、"notification"）
3. **记录常量名称**：例如 `kDownloadDefaultDirectory[] = "download.default_directory"`
4. **转换为字典**：按点分割并创建嵌套结构

**示例 - 查找通知首选项：**

```cpp
// 在 pref_names.cc 中搜索 "notification"：
const char kPushMessagingAppIdentifierMap[] = 
    "gcm.push_messaging_application_id_map";
const char kDefaultNotificationsSetting[] = 
    "profile.default_content_setting_values.notifications";
```

```python
# 变成：
options.browser_preferences = {
    'profile': {
        'default_content_setting_values': {
            'notifications': 2  # 2 = 阻止，1 = 允许，0 = 询问
        }
    }
}
```

### 常见首选项模式

| 类别 | 示例常量 | Python 字典路径 |
|----------|-----------------|------------------|
| 下载 | `download.default_directory` | `{'download': {'default_directory': ...}}` |
| 内容设置 | `profile.default_content_setting_values.X` | `{'profile': {'default_content_setting_values': {'X': ...}}}` |
| 网络 | `net.network_prediction_options` | `{'net': {'network_prediction_options': ...}}` |
| 隐私 | `safebrowsing.enabled` | `{'safebrowsing': {'enabled': ...}}` |
| 会话 | `session.restore_on_startup` | `{'session': {'restore_on_startup': ...}}` |

!!! warning "未记录的首选项"
    并非所有首选项都有文档。有些是：
    
    - **实验性**：可能在未来的 Chromium 版本中更改或删除
    - **内部**：由 Chromium 的内部系统使用
    - **平台特定**：仅在某些操作系统上工作
    
    在依赖未记录的首选项之前，请彻底测试。

## 有用的首选项参考

以下是从 Chromium 的 `pref_names.cc` 中精选的有趣且有用的首选项列表：

### 内容与媒体设置

```python
options.browser_preferences = {
    'profile': {
        'default_content_setting_values': {
            # 内容控制 (0=询问，1=允许，2=阻止)
            'cookies': 1,                    # 允许 cookie
            'images': 1,                     # 允许图像（2 为阻止）
            'javascript': 1,                 # 允许 JavaScript（2 为阻止）
            'plugins': 2,                    # 阻止插件（Flash 等）
            'popups': 0,                     # 阻止弹出窗口
            'geolocation': 2,                # 阻止位置请求
            'notifications': 2,              # 阻止通知
            'media_stream': 2,               # 阻止摄像头/麦克风
            'media_stream_mic': 2,           # 仅阻止麦克风
            'media_stream_camera': 2,        # 仅阻止摄像头
            'automatic_downloads': 1,        # 允许自动下载
            'midi_sysex': 2,                 # 阻止 MIDI 访问
            'clipboard': 1,                  # 允许剪贴板访问
            'sensors': 2,                    # 阻止运动传感器
            'usb_guard': 2,                  # 阻止 USB 设备访问
            'serial_guard': 2,               # 阻止串行端口访问
            'bluetooth_guard': 2,            # 阻止蓝牙
            'file_system_write_guard': 2,    # 阻止文件系统写入
        }
    }
}
```

### 网络与性能

```python
options.browser_preferences = {
    'net': {
        # 网络预测：0=始终，1=仅 WiFi，2=从不
        'network_prediction_options': 2,
        
        # 快速检查服务器可达性
        'quick_check_enabled': False
    },
    
    # DNS 预取
    'dns_prefetching': {
        'enabled': False  # 禁用以减少网络流量
    },
    
    # 预连接到搜索结果
    'search': {
        'suggest_enabled': False,           # 禁用搜索建议
        'instant_enabled': False            # 禁用即时结果
    },
    
    # 备用错误页面
    'alternate_error_pages': {
        'enabled': False  # 不建议 404 的替代方案
    }
}
```

### 下载首选项

```python
options.browser_preferences = {
    'download': {
        'default_directory': '/path/to/downloads',
        'prompt_for_download': False,
        'directory_upgrade': True,
        'extensions_to_open': '',           # 自动打开的文件类型
        'open_pdf_externally': True,        # 不使用内部 PDF 查看器
    },
    
    'download_bubble': {
        'partial_view_enabled': True        # 显示下载进度气泡
    },
    
    'safebrowsing': {
        'enabled': False  # 禁用安全浏览下载警告
    }
}
```

### 隐私与安全

```python
options.browser_preferences = {
    # 请勿跟踪
    'enable_do_not_track': True,
    
    # 引荐来源
    'enable_referrers': False,
    
    # 安全浏览
    'safebrowsing': {
        'enabled': False,                   # 禁用安全浏览
        'enhanced': False                   # 禁用增强保护
    },
    
    # 隐私沙盒（Google 的 cookie 替代品）
    'privacy_sandbox': {
        'apis_enabled': False,
        'topics_enabled': False,
        'fledge_enabled': False
    },
    
    # 第三方 cookie
    'profile': {
        'block_third_party_cookies': True,
        'cookie_controls_mode': 1,          # 在隐身模式下阻止第三方
        
        # 内容设置
        'default_content_setting_values': {
            'cookies': 1,
            'third_party_cookie_blocking_enabled': True
        }
    },
    
    # WebRTC（可能泄露真实 IP）
    'webrtc': {
        'ip_handling_policy': 'default_public_interface_only',
        'multiple_routes_enabled': False,
        'nonproxied_udp_enabled': False
    }
}
```

### 自动填充与密码

```python
options.browser_preferences = {
    'autofill': {
        'enabled': False,                   # 禁用表单自动填充
        'profile_enabled': False,           # 禁用地址自动填充
        'credit_card_enabled': False,       # 禁用信用卡自动填充
        'credit_card_fido_auth_enabled': False
    },
    
    'profile': {
        'password_manager_enabled': False,
        'password_manager_leak_detection': False
    },
    
    'credentials_enable_service': False,
    'credentials_enable_autosignin': False
}
```

### 浏览器行为与 UI

```python
import time

options.browser_preferences = {
    # 主页和启动
    'homepage': 'https://www.google.com',
    'homepage_is_newtabpage': False,
    'newtab_page_location_override': 'https://www.google.com',
    
    'session': {
        'restore_on_startup': 1,            # 0=新标签页，1=恢复，4=特定 URL，5=新标签页
        'startup_urls': ['https://www.google.com'],
        'session_data_status': 3            # 会话数据状态（内部）
    },
    
    # 欢迎页面和窗口
    'browser': {
        'has_seen_welcome_page': True,      # 跳过欢迎屏幕
        'window_placement': {
            'bottom': 1032,                 # 窗口底部位置
            'left': 2247,                   # 窗口左侧位置
            'right': 3192,                  # 窗口右侧位置
            'top': 31,                      # 窗口顶部位置
            'maximized': False,             # 窗口最大化
            'work_area_bottom': 1080,       # 屏幕工作区底部
            'work_area_left': 1920,         # 屏幕工作区左侧
            'work_area_right': 3840,        # 屏幕工作区右侧
            'work_area_top': 0              # 屏幕工作区顶部
        }
    },
    
    # 扩展
    'extensions': {
        'ui': {
            'developer_mode': False
        },
        'alerts': {
            'initialized': True
        },
        'theme': {
            'system_theme': 2               # 0=默认，1=浅色，2=深色
        },
        'last_chrome_version': '130.0.6723.91'  # 必须与您的版本匹配
    },
    
    # 翻译
    'translate': {
        'enabled': False                    # 禁用翻译提示
    },
    'translate_blocked_languages': ['en'],  # 从不翻译英语
    'translate_site_blacklist': [],         # 旧版（使用 blocklist_with_time）
    
    # 书签
    'bookmark_bar': {
        'show_on_all_tabs': False
    },
    
    # 标签页
    'tabs': {
        'new_tab_position': 0               # 0=右侧，1=当前之后
    },
    'pinned_tabs': [],                      # 固定标签页 URL 列表
    
    # 新标签页（Chrome 格式的时间戳）
    'NewTabPage': {
        'PrevNavigationTime': str(int(time.time() * 1000000) + 11644473600000000)  # Chrome 时间戳
    },
    'ntp': {
        'num_personal_suggestions': 6       # 建议数量（0-10）
    },
    
    # 工具栏自定义
    'toolbar': {
        'pinned_chrome_labs_migration_complete': True
    }
}
```

!!! info "Chrome 时间戳格式"
    Chrome 使用 Windows FILETIME 格式：自 1601 年 1 月 1 日 UTC 以来的微秒。
    
    转换 Python 时间戳：
    ```python
    import time
    chrome_time = int(time.time() * 1000000) + 11644473600000000
    ```

### 拼写与语言

```python
options.browser_preferences = {
    'browser': {
        'enable_spellchecking': False       # 禁用拼写检查
    },
    
    'spellcheck': {
        'dictionaries': ['en-US', 'pt-BR'], # 拼写检查语言
        'dictionary': '',                   # 旧版首选项（保持为空）
        'use_spelling_service': False       # 不发送到 Google
    },
    
    'intl': {
        'accept_languages': 'pt-BR,pt,en-US,en',
        'selected_languages': 'pt-BR,pt,en-US,en'  # 明确选择的
    },
    
    # 翻译行为和历史
    'translate': {
        'enabled': True
    },
    'translate_accepted_count': {
        'pt-BR': 0,
        'es': 5                             # 接受了 5 次西班牙语翻译
    },
    'translate_denied_count_for_language': {
        'en': 10                            # 从不翻译英语
    },
    'translate_ignored_count_for_language': {
        'en': 1
    },
    'translate_site_blocklist_with_time': {},  # 从不翻译的网站
    
    # 无障碍字幕语言
    'accessibility': {
        'captions': {
            'live_caption_language': 'pt-BR'
        }
    },
    
    # 语言模型计数器（使用统计）
    'language_model_counters': {
        'en': 2,                            # 英语单词计数
        'pt': 10                            # 葡萄牙语单词计数
    }
}
```

!!! info "语言模型计数器"
    这些计数器跟踪 Chrome 机器学习模型的语言使用统计信息：
    
    - 用于预测用户语言偏好
    - 影响搜索建议和自动完成
    - 更高的计数表示更频繁的使用
    - 真实值：偶尔使用 0-1000，大量使用 1000+

### 无障碍

```python
options.browser_preferences = {
    'accessibility': {
        'image_labels_enabled': False       # 不从 Google 获取图像标签
    },
    
    # 字体设置
    'webkit': {
        'webprefs': {
            'default_font_size': 16,
            'default_fixed_font_size': 13,
            'minimum_font_size': 0,
            'minimum_logical_font_size': 6,
            'fonts': {
                'standard': {
                    'Zyyy': 'Arial'
                },
                'serif': {
                    'Zyyy': 'Times New Roman'
                }
            }
        }
    }
}
```

### 媒体与音频

```python
options.browser_preferences = {
    # 音频
    'audio': {
        'mute_enabled': False               # 启动时音频开/关
    },
    
    # 自动播放
    'media': {
        'autoplay_policy': 0,               # 0=允许，1=用户手势，2=文档用户激活
        'video_fullscreen_orientation_lock': False
    },
    
    # WebGL
    'webkit': {
        'webprefs': {
            'webgl_enabled': True,          # 启用/禁用 WebGL
            'webgl2_enabled': True
        }
    }
}
```

### 打印

```python
options.browser_preferences = {
    'printing': {
        'print_preview_sticky_settings': {
            'appState': '{\"version\":2,\"recentDestinations\":[{\"id\":\"Save as PDF\",\"origin\":\"local\"}],\"marginsType\":3,\"customMargins\":{\"marginTop\":63,\"marginRight\":192,\"marginBottom\":240,\"marginLeft\":260}}'
        }
    },
    
    'savefile': {
        'default_directory': '/tmp'         # PDF 的默认保存位置
    }
}
```

!!! tip "打印 appState 格式"
    `appState` 是一个 JSON 编码的字符串。为了更容易操作：
    
    ```python
    import json
    
    app_state = {
        'version': 2,
        'recentDestinations': [{
            'id': 'Save as PDF',
            'origin': 'local'
        }],
        'marginsType': 3,                   # 0=默认，1=无边距，2=最小，3=自定义
        'customMargins': {
            'marginTop': 63,
            'marginRight': 192,
            'marginBottom': 240,
            'marginLeft': 260
        },
        'isHeaderFooterEnabled': False,
        'scaling': '100',
        'scalingType': 3,                   # 0=默认，1=适合页面，2=适合纸张，3=自定义
        'isColorEnabled': True,
        'isDuplexEnabled': False,
        'isCssBackgroundEnabled': True,
        'dpi': {
            'horizontal_dpi': 300,
            'vertical_dpi': 300,
            'is_default': True
        },
        'mediaSize': {
            'name': 'ISO_A4',
            'width_microns': 210000,
            'height_microns': 297000,
            'custom_display_name': 'A4',
            'is_default': True
        }
    }
    
    # 转换为字符串用于 appState
    options.browser_preferences = {
        'printing': {
            'print_preview_sticky_settings': {
                'appState': json.dumps(app_state)
            }
        }
    }
    ```

### WebRTC 与点对点

```python
options.browser_preferences = {
    'webrtc': {
        # IP 处理策略
        'ip_handling_policy': 'default_public_interface_only',
        
        # UDP 传输选项
        'udp_port_range': '10000-10100',    # 限制 UDP 端口范围
        
        # 禁用点对点
        'multiple_routes_enabled': False,
        'nonproxied_udp_enabled': False,
        
        # 文本日志收集
        'text_log_collection_allowed': False
    }
}
```

### 站点隔离与安全

```python
options.browser_preferences = {
    # 站点隔离
    'site_isolation': {
        'isolate_origins': '',              # 要隔离的逗号分隔的源
        'site_per_process': True            # 完整站点隔离
    },
    
    # 混合内容
    'mixed_content': {
        'auto_upgrade_enabled': True        # 将 HTTP 升级到 HTTPS
    },
    
    # SSL/TLS
    'ssl': {
        'rev_checking': {
            'enabled': True                 # 检查证书吊销
        }
    }
}
```

### 安装与国家元数据

```python
import uuid
from pydoll.browser.options import ChromiumOptions

options = ChromiumOptions()
options.browser_preferences = {
    # 安装时的国家 ID（影响默认设置和语言环境）
    'countryid_at_install': 16978,          # 因国家而异（例如，巴西为 16978）
    
    # 默认应用安装状态
    'default_apps_install_state': 3,        # 0=未安装，1=已安装，3=已迁移
    
    # 企业配置文件 GUID（用于托管浏览器）
    'enterprise_profile_guid': str(uuid.uuid4()),
    
    # 默认搜索提供商
    'default_search_provider': {
        'guid': ''                          # 空表示默认（Google）
    }
}
```

!!! info "国家 ID 值"
    `countryid_at_install` 是一个数字代码，表示首次安装 Chrome 的国家：
    
    - **16978**：巴西 (BR)
    - **16965**：美国 (US)
    - **16967**：英国 (GB)
    - **16966**：德国 (DE)
    - **16972**：日本 (JP)
    - 还有许多其他...
    
    这会影响默认语言、货币和区域设置。为了实现逼真的指纹识别，请将其与目标区域匹配。

### 实验性功能

```python
options.browser_preferences = {
    # Chrome Labs 实验
    'browser': {
        'labs': {
            'enabled': False
        }
    },
    
    # 预加载
    'preload': {
        'enabled': False                    # 禁用页面预加载
    },
    
    # 平滑滚动
    'smooth_scrolling': {
        'enabled': True
    },
    
    # 硬件加速
    'hardware_acceleration_mode': {
        'enabled': True                     # 禁用以提高无头性能
    }
}
```

### DevTools 与开发者选项

```python
options.browser_preferences = {
    'devtools': {
        'preferences': {
            # DevTools 外观
            'currentDockState': '"right"',              # "bottom"、"right"、"undocked"
            'uiTheme': '"dark"',                        # "dark"、"light"、"system"
            
            # 控制台设置
            'consoleTimestampsEnabled': 'true',
            'preserveConsoleLog': 'true',
            
            # 网络面板
            'network.disableCache': 'false',
            'network.color-code-resource-types': 'true',
            'network-panel-split-view-state': '{"vertical":{"size":0}}',
            
            # 源映射
            'cssSourceMapsEnabled': 'true',
            'jsSourceMapsEnabled': 'true',
            
            # 元素面板
            'elements.styles.sidebar.width': '{"vertical":{"size":0,"showMode":"OnlyMain"}}',
            
            # 检查器版本控制
            'inspectorVersion': '37',
            
            # 选定的面板
            'panel-selected-tab': '"network"',          # 最后打开的面板
            
            # 请求信息展开的类别
            'request-info-general-category-expanded': 'true',
            'request-info-request-headers-category-expanded': 'true',
            'request-info-response-headers-category-expanded': 'true'
        },
        'synced_preferences_sync_disabled': {
            'adorner-settings': '[{"adorner":"grid","isEnabled":true},{"adorner":"flex","isEnabled":true}]',
            'syncedInspectorVersion': '37'
        }
    },
    
    # GCM（Google Cloud Messaging）
    'gcm': {
        'product_category_for_subtypes': 'com.chrome.linux'  # com.chrome.windows、com.chrome.macos
    }
}
```

!!! tip "DevTools 首选项格式"
    DevTools 首选项使用独特的格式，其中布尔值和字符串值存储为 **JSON 编码的字符串**（例如 `'true'` 而不是 `True`，`'"dark"'` 而不是 `'dark'`）。这是因为 DevTools 设置直接序列化为 JSON。
    
    对于复杂对象，双重编码：
    ```python
    import json
    
    # 创建对象
    split_view = {'vertical': {'size': 0}}
    
    # 为 DevTools 双重编码
    devtools_value = json.dumps(json.dumps(split_view))
    # 结果：'"{\\"vertical\\":{\\"size\\":0}}"'
    ```

### 同步与登录控制

```python
import time
from pydoll.browser.options import ChromiumOptions

options = ChromiumOptions()
options.browser_preferences = {
    'signin': {
        'allowed': True,                        # 允许登录 Google
        'cookie_clear_on_exit_migration_notice_complete': True
    },
    
    'sync': {
        'data_type_status_for_sync_to_signin': {
            'bookmarks': False,
            'history': False,
            'passwords': False,
            'preferences': False
        },
        'encryption_bootstrap_token_per_account_migration_done': True,
        'passwords_per_account_pref_migration_done': True,
        'feature_status_for_sync_to_signin': 5
    },
    
    # Google 服务
    'google': {
        'services': {
            'signin_scoped_device_id': '<your-device-id>'  # 生成唯一 ID
        }
    },
    
    # GAIA（Google 帐户基础架构）
    'gaia_cookie': {
        'changed_time': str(int(time.time())),
        'hash': '',
        'last_list_accounts_data': '[]'
    }
}
```

### 优化与性能跟踪

```python
import time
from pydoll.browser.options import ChromiumOptions

options = ChromiumOptions()
options.browser_preferences = {
    # 优化指南（Google 的性能提示）
    'optimization_guide': {
        'hintsfetcher': {
            'hosts_successfully_fetched': {}
        },
        'predictionmodelfetcher': {
            'last_fetch_attempt': str(int(time.time())),
            'last_fetch_success': str(int(time.time()))
        },
        'previously_registered_optimization_types': {}
    },
    
    # 历史群集（分组相关浏览）
    'history_clusters': {
        'all_cache': {
            'all_keywords': {},
            'all_timestamp': str(int(time.time()))
        },
        'last_selected_tab': 0,
        'short_cache': {
            'short_keywords': {},
            'short_timestamp': '0'
        }
    },
    
    # 域多样性指标
    'domain_diversity': {
        'last_reporting_timestamp': str(int(time.time()))
    },
    
    # 分段平台（用户行为分析）
    'segmentation_platform': {
        'device_switcher_util': {
            'result': {
                'labels': ['NotSynced']
            }
        },
        'last_db_compaction_time': str(int(time.time()))
    },
    
    # 零建议（地址栏预测）
    'zerosuggest': {
        'cachedresults': '',
        'cachedresults_with_url': {}
    }
}
```

!!! info "性能跟踪首选项"
    这些首选项通常由 Chrome 用于跟踪和优化性能。对于自动化，您可以将它们留空或设置真实值以使其看起来更像正常浏览器。

### 会话事件与崩溃处理

Chrome 跟踪会话历史以进行恢复和遥测：

```python
import time
from pydoll.browser.options import ChromiumOptions

options = ChromiumOptions()
options.browser_preferences = {
    'sessions': {
        'event_log': [
            {
                'crashed': False,
                'time': str(int(time.time() * 1000000) + 11644473600000000),
                'type': 0                   # 0=会话开始
            },
            {
                'crashed': False,
                'did_schedule_command': True,
                'first_session_service': True,
                'tab_count': 1,
                'time': str(int(time.time() * 1000000) + 11644473600000000),
                'type': 2,                  # 2=会话数据已保存
                'window_count': 1
            }
        ],
        'session_data_status': 3            # 0=未知，1=无数据，2=部分数据，3=完整数据
    },
    
    # 配置文件退出类型（对指纹识别很重要）
    'profile': {
        'exit_type': 'Crashed'              # 'Normal'、'Crashed'、'SessionEnded'
    }
}
```

!!! warning "崩溃与正常"
    大多数真实浏览器**偶尔会崩溃**。始终显示 `'Normal'` 退出是可疑的。
    
    **真实策略**：为约 10-20% 的配置文件设置 `'Crashed'` 以模拟正常用户体验。具有讽刺意味的是，偶尔出现"崩溃"会使您的自动化看起来更像人类。

!!! tip "会话事件类型"
    - **类型 0**：会话开始
    - **类型 1**：会话正常结束
    - **类型 2**：会话数据已保存（标签页、窗口）
    - **类型 3**：会话已恢复
    
    `event_log` 会随着时间的推移建立浏览器会话的历史记录。

## 隐身与指纹识别

创建逼真的浏览器指纹对于避免机器人检测系统至关重要。本节涵盖基本和高级技术。

### 快速隐身设置

对于大多数用例，这种简单的配置提供了良好的反检测：

```python
import asyncio
import time
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

async def quick_stealth():
    options = ChromiumOptions()
    
    # 模拟 60 天前的浏览器
    fake_timestamp = int(time.time()) - (60 * 24 * 60 * 60)
    
    options.browser_preferences = {
        # 虚假使用历史
        'profile': {
            'last_engagement_time': fake_timestamp,
            'exited_cleanly': True,
            'exit_type': 'Normal'
        },
        
        # 真实主页
        'homepage': 'https://www.google.com',
        'session': {
            'restore_on_startup': 1,
            'startup_urls': ['https://www.google.com']
        },
        
        # 启用真实用户拥有的功能
        'enable_do_not_track': False,  # 大多数用户不启用此功能
        'safebrowsing': {'enabled': True},
        'autofill': {'enabled': True},
        'search': {'suggest_enabled': True},
        'dns_prefetching': {'enabled': True}
    }
    
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        await tab.go_to('https://bot-detection-site.com')
        print("隐身模式已激活！")

asyncio.run(quick_stealth())
```

!!! tip "关键隐身原则"
    **启用，而不是禁用**：真实用户启用了安全浏览、自动填充和搜索建议。禁用所有内容看起来可疑。
    
    **老化您的配置文件**：全新安装是一个危险信号。模拟已使用数周或数月的浏览器。
    
    **匹配大多数**：使用 90% 的用户拥有的默认设置，而不是注重隐私的配置。

### 高级指纹识别

为了实现最大的真实性，模拟详细的浏览器使用历史：

```python
import time
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

def create_realistic_browser() -> ChromiumOptions:
    """创建具有全面指纹识别抵抗力的浏览器。"""
    options = ChromiumOptions()
    
    # 时间戳
    current_time = int(time.time())
    install_time = current_time - (90 * 24 * 60 * 60)  # 90 天前
    last_use = current_time - (3 * 60 * 60)            # 3 小时前
    
    options.browser_preferences = {
        # 配置文件元数据（对指纹识别至关重要）
        'profile': {
            'created_by_version': '130.0.6723.91',      # 必须与您的 Chrome 版本匹配
            'creation_time': str(install_time),
            'last_engagement_time': str(last_use),
            'exit_type': 'Crashed',                     # 'Normal'、'Crashed'、'SessionEnded'
            'name': 'Pessoa 1',                         # 真实的配置文件名称
            'avatar_index': 26,                         # 0-26 可用头像
            
            # 真实的内容设置
            'default_content_setting_values': {
                'cookies': 1,
                'images': 1,
                'javascript': 1,
                'popups': 0,
                'notifications': 2,
                'geolocation': 0,           # 询问（不阻止）
                'media_stream': 0           # 询问（真实）
            },
            
            'password_manager_enabled': False,
            'cookie_controls_mode': 0,
            'content_settings': {
                'pref_version': 1,
                'enable_quiet_permission_ui': {
                    'notifications': False
                },
                'enable_quiet_permission_ui_enabling_method': {
                    'notifications': 1
                }
            },
            
            # 安全元数据
            'family_member_role': 'not_in_family',
            'managed_user_id': '',
            'were_old_google_logins_removed': True
        },
        
        # 浏览器使用元数据
        'browser': {
            'has_seen_welcome_page': True,
            'window_placement': {
                'work_area_bottom': 1080,
                'work_area_left': 0,
                'work_area_right': 1920,
                'work_area_top': 0
            }
        },
        
        # 安装元数据
        'countryid_at_install': 16978,              # 因国家而异
        'default_apps_install_state': 3,
        
        # 扩展元数据
        'extensions': {
            'last_chrome_version': '130.0.6723.91',  # 必须与您的版本匹配
            'alerts': {'initialized': True},
            'theme': {'system_theme': 2}
        },
        
        # 会话活动（显示定期使用）
        'in_product_help': {
            'session_start_time': str(current_time),
            'session_last_active_time': str(current_time),
            'recent_session_start_times': [
                str(current_time - (24 * 60 * 60)),
                str(current_time - (48 * 60 * 60)),
                str(current_time - (72 * 60 * 60))
            ]
        },
        
        # 会话恢复
        'session': {
            'restore_on_startup': 1,
            'startup_urls': ['https://www.google.com']
        },
        
        # 主页
        'homepage': 'https://www.google.com',
        'homepage_is_newtabpage': False,
        
        # 翻译历史（显示多语言使用）
        'translate': {'enabled': True},
        'translate_accepted_count': {'es': 2, 'fr': 1},
        'translate_denied_count_for_language': {'en': 1},
        
        # 拼写检查
        'spellcheck': {
            'dictionaries': ['en-US', 'pt-BR'],
            'dictionary': ''
        },
        
        # 语言
        'intl': {
            'selected_languages': 'en-US,en,pt-BR'
        },
        
        # 登录元数据
        'signin': {
            'allowed': True,
            'cookie_clear_on_exit_migration_notice_complete': True
        },
        
        # 安全浏览（大多数用户拥有此功能）
        'safebrowsing': {
            'enabled': True,
            'enhanced': False
        },
        
        # 自动填充（真实用户常见）
        'autofill': {
            'enabled': True,
            'profile_enabled': True
        },
        
        # 搜索建议
        'search': {'suggest_enabled': True},
        
        # DNS 预取
        'dns_prefetching': {'enabled': True},
        
        # 请勿跟踪（通常关闭）
        'enable_do_not_track': False,
        
        # WebRTC（默认设置）
        'webrtc': {
            'ip_handling_policy': 'default',
            'multiple_routes_enabled': True
        },
        
        # 隐私沙盒（Google 的 cookie 替代品 - 真实用户拥有此功能）
        'privacy_sandbox': {
            'first_party_sets_data_access_allowed_initialized': True,
            'm1': {
                'ad_measurement_enabled': True,
                'fledge_enabled': True,
                'row_notice_acknowledged': True,
                'topics_enabled': True
            }
        },
        
        # 媒体参与度
        'media': {
            'engagement': {'schema_version': 5}
        },
        
        # Web 应用
        'web_apps': {
            'did_migrate_default_chrome_apps': ['app-id'],
            'last_preinstall_synchronize_version': '130'
        }
    }
    
    return options

# 使用
async def advanced_stealth():
    options = create_realistic_browser()
    
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        await tab.go_to('https://advanced-bot-detection.com')
        # 浏览器显示为 90 天前的真实安装
```

!!! warning "版本一致性至关重要"
    **始终匹配 Chrome 版本**：确保 `profile.created_by_version` 和 `extensions.last_chrome_version` 与您的实际 Chrome 版本匹配。版本不匹配是一个立即的危险信号。
    
    ```python
    # 以编程方式获取您的 Chrome 版本：
    async with Chrome() as browser:
        tab = await browser.start()
        version = await browser.get_version()
        chrome_version = version['product'].split('/')[1]  # 例如 '130.0.6723.91'
        print(f"使用此版本：{chrome_version}")
    ```

!!! info "指纹识别首选项的作用"
    **配置文件年龄**：`creation_time` 和 `last_engagement_time` 证明浏览器不是全新安装。
    
    **使用历史**：`recent_session_start_times` 显示定期浏览模式。
    
    **翻译历史**：`translate_accepted_count` 表明真实的人使用多种语言。
    
    **窗口放置**：与实际显示器分辨率匹配的真实屏幕尺寸。
    
    **隐私沙盒**：Google 的新跟踪系统。禁用它是不寻常的和可疑的。

## 性能影响

了解浏览器首选项的性能影响可以帮助您针对特定用例进行优化：

| 首选项类别 | 预期影响 | 用例 |
|---------------------|----------------|----------|
| 禁用图像 | 加载速度提高 50-70% | 抓取文本内容 |
| 禁用预取 | 加载速度提高 10-20% | 减少带宽使用 |
| 禁用插件 | 加载速度提高 5-10% | 安全性和性能 |
| 阻止通知 | 消除弹出窗口 | 干净的自动化 |
| 静默下载 | 消除提示 | 自动化文件下载 |

!!! tip "速度与隐身的权衡"
    **追求速度**：禁用图像、预取、插件和拼写检查。
    
    **追求隐身**：启用安全浏览、自动填充、搜索建议和 DNS 预取（即使它们会减慢速度）。
    
    **平衡方法**：启用隐身功能但禁用图像和插件。这可以提供 40-50% 的加速，同时保持真实的指纹。

## 另请参阅

- **[深入探讨：浏览器首选项](../../deep-dive/browser-preferences.md)** - 架构细节和内部原理
- **[页面加载状态](page-load-state.md)** - 控制何时认为页面已加载
- **[代理配置](proxy.md)** - 配置网络代理
- **[Cookie 与会话](../browser-management/cookies-sessions.md)** - 管理浏览器状态
- **[Chromium 源代码：pref_names.cc](https://chromium.googlesource.com/chromium/src/+/main/chrome/common/pref_names.cc)** - 官方首选项常量
- **[Chromium 源代码：pref_names.h](https://github.com/chromium/chromium/blob/main/chrome/common/pref_names.h)** - 带有定义的头文件

自定义浏览器首选项为您提供了对浏览器行为的前所未有的控制，使复杂的自动化、性能优化和隐私配置成为可能，而这些在传统自动化工具中是根本不可能实现的。这种访问级别将 Pydoll 从一个简单的自动化库转变为一个完整的浏览器控制系统。
