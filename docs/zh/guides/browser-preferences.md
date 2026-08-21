# 浏览器偏好设置

偏好设置是存在于 Chromium 配置文件内部的设置：下载文件夹、接受的语言、是否允许弹窗和通知，以及成百上千项其他设置。你在启动浏览器之前把它们设置在 `ChromiumOptions` 上，Pydoll 会把它们应用到它所启动的配置文件上。

偏好设置和 [命令行参数](browser-options.md) 不是一回事。参数是在启动时传给 Chromium 二进制文件的 flag（`--headless`、`--proxy-server`）；偏好设置则是配置文件设置中的条目，也就是设置界面所写入的那些。用参数决定进程如何启动，用偏好设置决定配置文件如何表现。

## 设置常见偏好 {#set-common-preferences}

日常的偏好设置都有辅助方法和属性，所以你无需记住 Chromium 的内部键名或那些魔数就能设置它们。

```python
import asyncio

from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions


async def main():
    options = ChromiumOptions()
    options.set_default_download_directory('/tmp/downloads')
    options.set_accept_languages('en-US,en')
    options.block_notifications = True
    options.block_popups = True

    async with Chrome(options=options) as browser:
        tab = await browser.start()
        await tab.go_to('https://news.ycombinator.com')

asyncio.run(main())
```

可用的辅助方法：

| 辅助方法 | 它设置什么 |
|--------|--------------|
| `options.set_default_download_directory(path)` | 下载文件的保存位置 |
| `options.set_accept_languages('en-US,en')` | `Accept-Language` 头和 `navigator.languages` |
| `options.prompt_for_download = False` | Chrome 是否在每次下载前询问 |
| `options.allow_automatic_downloads = True` | 页面是否可以触发多次下载 |
| `options.block_popups = True` | 阻止弹窗 |
| `options.block_notifications = True` | 阻止站点通知提示 |
| `options.password_manager_enabled = False` | 开启或关闭 Chrome 的密码管理器 |
| `options.open_pdf_externally = True` | 下载 PDF 而不是打开查看器 |

每个辅助方法都会用正确的值写入正确的嵌套键，所以 `block_notifications = True` 会变成 Chromium 所期望的那个通知设置，而不是一个你得去查的数字。

!!! tip "语言、下载与检测"
    `set_accept_languages` 应当与你在别处呈现的区域设置相匹配；在非美国 IP 上用美国语言，这种不匹配正是反机器人系统会检查的。请看 [保持不被检测](../stealth/index.md)。

## 设置任意偏好

对于没有辅助方法的偏好设置，赋值给 `options.browser_preferences`。它接受一个嵌套字典，并把它合并进已经设置的内容里，所以你可以通过多次赋值逐步构建它。

```python
options = ChromiumOptions()

options.browser_preferences = {
    'download': {'default_directory': '/tmp/downloads'},
    'intl': {'accept_languages': 'en-US,en'},
}

# 后续的赋值会合并，而不会替换
options.browser_preferences = {
    'profile': {'default_content_setting_values': {'images': 2}},
}
```

Chromium 以点分路径的形式记录偏好设置（例如 `download.default_directory`）。每一个点就是字典的一层：`download.default_directory` 变成 `{'download': {'default_directory': ...}}`。按路径嵌套这些键即可。

!!! note "不要把它包进 `prefs` 里"
    直接赋值这棵偏好设置树。把它包进一个顶层 `{'prefs': {...}}` 键会抛出错误；辅助方法和字典都期望真正的路径位于顶层。

## 为 stealth 构建一份逼真的配置文件 {#build-a-realistic-profile-for-stealth}

反机器人系统读取的是配置文件，而不只是页面。一个全新的、空白的、把每项便利功能都禁用了的配置文件，一点也不像真实用户，所以偏好设置是让自己看起来正常的一个杠杆。其指导思想与大多数隐私建议恰好相反：

- **启用，而不是禁用。** 真实用户会开着 Safe Browsing、自动填充和搜索建议。一个什么都关掉的配置文件本身就是一个信号。
- **给配置文件“做旧”。** 一个几秒前才创建的配置文件是个危险信号。把使用时间戳回拨，让它看起来有几周或几个月那么久。
- **匹配你真实的 Chrome。** 你设置的任何版本字符串（在 `profile` 或 `extensions` 中）都必须与你实际运行的 Chrome 二进制文件相符，否则这种不匹配会暴露你。

```python
import asyncio
import time

from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions


def realistic_options() -> ChromiumOptions:
    now = int(time.time())
    installed = now - (90 * 24 * 60 * 60)   # 90 天前
    last_used = now - (3 * 60 * 60)         # 3 小时前

    options = ChromiumOptions()
    options.browser_preferences = {
        'profile': {
            'created_by_version': '130.0.6723.91',   # 匹配你真实的 Chrome
            'creation_time': str(installed),
            'last_engagement_time': str(last_used),
            'exit_type': 'Normal',
            'name': 'Person 1',
            'default_content_setting_values': {
                'cookies': 1, 'images': 1, 'javascript': 1,
                'notifications': 2, 'geolocation': 0, 'media_stream': 0,
            },
        },
        'extensions': {'last_chrome_version': '130.0.6723.91'},
        'intl': {'selected_languages': 'en-US,en'},
        'spellcheck': {'dictionaries': ['en-US']},
        'session': {'restore_on_startup': 1, 'startup_urls': ['https://www.google.com']},
        'homepage': 'https://www.google.com',
        'safebrowsing': {'enabled': True},
        'autofill': {'enabled': True},
        'search': {'suggest_enabled': True},
        'dns_prefetching': {'enabled': True},
        'enable_do_not_track': False,
        'webrtc': {'ip_handling_policy': 'default', 'multiple_routes_enabled': True},
    }
    return options


async def main():
    async with Chrome(options=realistic_options()) as browser:
        tab = await browser.start()
        await tab.go_to('https://news.ycombinator.com')

asyncio.run(main())
```

!!! note "偏好设置只是其中一层，不是整个 fingerprint"
    偏好设置塑造的是配置文件的身份（使用历史、已启用的功能、语言）。它们不会改变 User-Agent、WebGL、canvas，或网络层的 fingerprint。要处理这些，以及让每一层都保持一致，请看 [Fingerprint 注入](../stealth/fingerprint-injection.md)。

## 偏好设置参考

下面各个代码块列出了值得了解的 Chromium 偏好设置，按领域分组。它们是 Chromium 自己的设置，而不是 Pydoll 的，所以确切的键名和可接受的值由 Chromium 定义，并且可能在不同版本间变化；Pydoll 会把你设置的内容原样传递过去。内容设置值遵循 Chromium 的约定：`0` = 询问，`1` = 允许，`2` = 阻止。把这当作一份查询表，当某项有对应的 [辅助方法](#set-common-preferences) 时优先使用它。

??? example "内容与媒体设置"


    ```python
    options.browser_preferences = {
        'profile': {
            'default_content_setting_values': {
                # 内容控制（0=询问，1=允许，2=阻止）
                'cookies': 1,                    # 允许 cookies
                'images': 1,                     # 允许图片（2 表示阻止）
                'javascript': 1,                 # 允许 JavaScript（2 表示阻止）
                'plugins': 2,                    # 阻止插件（Flash 等）
                'popups': 0,                     # 阻止弹窗
                'geolocation': 2,                # 阻止定位请求
                'notifications': 2,              # 阻止通知
                'media_stream': 2,               # 阻止摄像头/麦克风
                'media_stream_mic': 2,           # 仅阻止麦克风
                'media_stream_camera': 2,        # 仅阻止摄像头
                'automatic_downloads': 1,        # 允许自动下载
                'midi_sysex': 2,                 # 阻止 MIDI 访问
                'clipboard': 1,                  # 允许剪贴板访问
                'sensors': 2,                    # 阻止运动传感器
                'usb_guard': 2,                  # 阻止 USB 设备访问
                'serial_guard': 2,               # 阻止串口访问
                'bluetooth_guard': 2,            # 阻止蓝牙
                'file_system_write_guard': 2,    # 阻止文件系统写入
            }
        }
    }
    ```


??? example "网络与性能"


    ```python
    options.browser_preferences = {
        'net': {
            # 网络预测：0=始终，1=仅 wifi，2=从不
            'network_prediction_options': 2,

            # 对服务器可达性的快速检查
            'quick_check_enabled': False
        },

        # DNS 预取
        'dns_prefetching': {
            'enabled': False  # 关闭以减少网络流量
        },

        # 预连接到搜索结果
        'search': {
            'suggest_enabled': False,           # 关闭搜索建议
            'instant_enabled': False            # 关闭即时结果
        },

        # 备用错误页面
        'alternate_error_pages': {
            'enabled': False  # 不为 404 建议替代页
        }
    }
    ```


??? example "下载偏好"


    ```python
    options.browser_preferences = {
        'download': {
            'default_directory': '/path/to/downloads',
            'prompt_for_download': False,
            'directory_upgrade': True,
            'extensions_to_open': '',           # 自动打开的文件类型
            'open_pdf_externally': True,        # 不使用内置 PDF 查看器
        },

        'download_bubble': {
            'partial_view_enabled': True        # 显示下载进度气泡
        },

        'safebrowsing': {
            'enabled': False  # 关闭 Safe Browsing 下载警告
        }
    }
    ```


??? example "隐私与安全"


    ```python
    options.browser_preferences = {
        # Do Not Track
        'enable_do_not_track': True,

        # 引荐来源
        'enable_referrers': False,

        # Safe Browsing
        'safebrowsing': {
            'enabled': False,                   # 关闭 Safe Browsing
            'enhanced': False                   # 关闭增强保护
        },

        # Privacy Sandbox（Google 对 cookie 的替代方案）
        'privacy_sandbox': {
            'apis_enabled': False,
            'topics_enabled': False,
            'fledge_enabled': False
        },

        # 第三方 cookies
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


??? example "自动填充与密码"


    ```python
    options.browser_preferences = {
        'autofill': {
            'enabled': False,                   # 关闭表单自动填充
            'profile_enabled': False,           # 关闭地址自动填充
            'credit_card_enabled': False,       # 关闭信用卡自动填充
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


??? example "浏览器行为与界面"


    ```python
    import time

    options.browser_preferences = {
        # 主页与启动
        'homepage': 'https://www.google.com',
        'homepage_is_newtabpage': False,
        'newtab_page_location_override': 'https://www.google.com',

        'session': {
            'restore_on_startup': 1,            # 0=新标签页，1=恢复，4=指定 URL，5=新标签页
            'startup_urls': ['https://www.google.com'],
            'session_data_status': 3            # 会话数据状态（内部）
        },

        # 欢迎页与窗口
        'browser': {
            'has_seen_welcome_page': True,      # 跳过欢迎界面
            'window_placement': {
                'bottom': 1032,                 # 窗口底部位置
                'left': 2247,                   # 窗口左侧位置
                'right': 3192,                  # 窗口右侧位置
                'top': 31,                      # 窗口顶部位置
                'maximized': False,             # 窗口是否最大化
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
            'last_chrome_version': '130.0.6723.91'  # 必须匹配你的版本
        },

        # 翻译
        'translate': {
            'enabled': False                    # 关闭翻译提示
        },
        'translate_blocked_languages': ['en'],  # 从不翻译英文
        'translate_site_blacklist': [],         # 旧字段（使用 blocklist_with_time）

        # 书签
        'bookmark_bar': {
            'show_on_all_tabs': False
        },

        # 标签页
        'tabs': {
            'new_tab_position': 0               # 0=右侧，1=当前之后
        },
        'pinned_tabs': [],                      # 固定标签页的 URL 列表

        # 新标签页（时间戳采用 Chrome 格式）
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

    !!! note "Chrome 时间戳格式"
        Chrome 使用 Windows FILETIME 格式：自 1601 年 1 月 1 日 UTC 起的微秒数。

        转换 Python 时间戳：
        ```python
        import time
        chrome_time = int(time.time() * 1000000) + 11644473600000000
        ```


??? example "拼写与语言"


    ```python
    options.browser_preferences = {
        'browser': {
            'enable_spellchecking': False       # 关闭拼写检查
        },

        'spellcheck': {
            'dictionaries': ['en-US', 'pt-BR'], # 拼写检查语言
            'dictionary': '',                   # 旧偏好（保持为空）
            'use_spelling_service': False       # 不发送给 Google
        },

        'intl': {
            'accept_languages': 'pt-BR,pt,en-US,en',
            'selected_languages': 'pt-BR,pt,en-US,en'  # 显式选择的语言
        },

        # 翻译行为与历史
        'translate': {
            'enabled': True
        },
        'translate_accepted_count': {
            'pt-BR': 0,
            'es': 5                             # 接受过 5 次西班牙语翻译
        },
        'translate_denied_count_for_language': {
            'en': 10                            # 从不翻译英文
        },
        'translate_ignored_count_for_language': {
            'en': 1
        },
        'translate_site_blocklist_with_time': {},  # 从不翻译的站点

        # 无障碍字幕语言
        'accessibility': {
            'captions': {
                'live_caption_language': 'pt-BR'
            }
        },

        # 语言模型计数器（使用统计）
        'language_model_counters': {
            'en': 2,                            # 英文词数
            'pt': 10                            # 葡萄牙文词数
        }
    }
    ```

    !!! note "语言模型计数器"
        这些计数器为 Chrome 的机器学习模型追踪语言使用统计：

        - 用于预测用户的语言偏好
        - 影响搜索建议和自动补全
        - 计数越高表示使用越频繁
        - 逼真的值：偶尔使用为 0-1000，重度使用为 1000+


??? example "无障碍"


    ```python
    options.browser_preferences = {
        'accessibility': {
            'image_labels_enabled': False       # 不从 Google 获取图片标签
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


??? example "媒体与音频"


    ```python
    options.browser_preferences = {
        # 音频
        'audio': {
            'mute_enabled': False               # 启动时音频开/关
        },

        # 自动播放
        'media': {
            'autoplay_policy': 0,               # 0=允许，1=需用户手势，2=需文档用户激活
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


??? example "打印"


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
        `appState` 是一个 JSON 编码的字符串。为了便于操作：

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
            'scalingType': 3,                   # 0=默认，1=适应页面，2=适应纸张，3=自定义
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

        # 转换为字符串供 appState 使用
        options.browser_preferences = {
            'printing': {
                'print_preview_sticky_settings': {
                    'appState': json.dumps(app_state)
                }
            }
        }
        ```


??? example "WebRTC 与点对点"


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


??? example "站点隔离与安全"


    ```python
    options.browser_preferences = {
        # 站点隔离
        'site_isolation': {
            'isolate_origins': '',              # 以逗号分隔、需要隔离的来源
            'site_per_process': True            # 完全站点隔离
        },

        # 混合内容
        'mixed_content': {
            'auto_upgrade_enabled': True        # 把 HTTP 升级为 HTTPS
        },

        # SSL/TLS
        'ssl': {
            'rev_checking': {
                'enabled': True                 # 检查证书吊销
            }
        }
    }
    ```


??? example "安装与国家/地区元数据"


    ```python
    import uuid
    from pydoll.browser.options import ChromiumOptions

    options = ChromiumOptions()
    options.browser_preferences = {
        # 安装时的国家 ID（影响默认设置和区域）
        'countryid_at_install': 16978,          # 因国家而异（例如巴西为 16978）

        # 默认应用的安装状态
        'default_apps_install_state': 3,        # 0=未安装，1=已安装，3=已迁移

        # 企业配置文件 GUID（用于受管浏览器）
        'enterprise_profile_guid': str(uuid.uuid4()),

        # 默认搜索提供商
        'default_search_provider': {
            'guid': ''                          # 留空表示默认（Google）
        }
    }
    ```

    !!! note "国家 ID 值"
        `countryid_at_install` 是一个数字代码，表示 Chrome 首次安装所在的国家：

        - **16978**：巴西（BR）
        - **16965**：美国（US）
        - **16967**：英国（GB）
        - **16966**：德国（DE）
        - **16972**：日本（JP）
        - 以及其他许多……

        这会影响默认语言、货币和区域设置。为了逼真的 fingerprinting，把它与你的目标地区相匹配。


??? example "实验性功能"


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
            'enabled': False                    # 关闭页面预加载
        },

        # 平滑滚动
        'smooth_scrolling': {
            'enabled': True
        },

        # 硬件加速
        'hardware_acceleration_mode': {
            'enabled': True                     # 为 headless 性能可将其关闭
        }
    }
    ```


??? example "DevTools 与开发者选项"


    ```python
    options.browser_preferences = {
        'devtools': {
            'preferences': {
                # DevTools 外观
                'currentDockState': '"right"',              # "bottom"、"right"、"undocked"
                'uiTheme': '"dark"',                        # "dark"、"light"、"system"

                # Console 设置
                'consoleTimestampsEnabled': 'true',
                'preserveConsoleLog': 'true',

                # Network 面板
                'network.disableCache': 'false',
                'network.color-code-resource-types': 'true',
                'network-panel-split-view-state': '{"vertical":{"size":0}}',

                # Source map
                'cssSourceMapsEnabled': 'true',
                'jsSourceMapsEnabled': 'true',

                # Elements 面板
                'elements.styles.sidebar.width': '{"vertical":{"size":0,"showMode":"OnlyMain"}}',

                # Inspector 版本
                'inspectorVersion': '37',

                # 选中的面板
                'panel-selected-tab': '"network"',          # 上次打开的面板

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

    !!! tip "DevTools 偏好格式"
        DevTools 偏好使用一种独特的格式，其中布尔值和字符串值都以 **JSON 编码的字符串** 存储（例如是 `'true'` 而不是 `True`，是 `'"dark"'` 而不是 `'dark'`）。这是因为 DevTools 设置会被直接序列化为 JSON。

        对于复杂对象，需双重编码：
        ```python
        import json

        # 创建对象
        split_view = {'vertical': {'size': 0}}

        # 为 DevTools 双重编码
        devtools_value = json.dumps(json.dumps(split_view))
        # 结果： '"{\\"vertical\\":{\\"size\\":0}}"'
        ```


??? example "同步与登录控制"


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

        # GAIA（Google Accounts Infrastructure）
        'gaia_cookie': {
            'changed_time': str(int(time.time())),
            'hash': '',
            'last_list_accounts_data': '[]'
        }
    }
    ```


??? example "优化与性能追踪"


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

        # 历史聚类（把相关浏览分组）
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

        # 域名多样性指标
        'domain_diversity': {
            'last_reporting_timestamp': str(int(time.time()))
        },

        # 分群平台（用户行为分析）
        'segmentation_platform': {
            'device_switcher_util': {
                'result': {
                    'labels': ['NotSynced']
                }
            },
            'last_db_compaction_time': str(int(time.time()))
        },

        # Zero suggest（omnibox 预测）
        'zerosuggest': {
            'cachedresults': '',
            'cachedresults_with_url': {}
        }
    }
    ```

    !!! note "性能追踪偏好"
        这些偏好通常被 Chrome 用来追踪和优化性能。对于自动化，你可以把它们留空，或设置逼真的值让它更像一个正常的浏览器。


??? example "会话事件与崩溃处理"


    Chrome 会追踪会话历史用于恢复和遥测：

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

        # 配置文件退出类型（对 fingerprinting 很重要）
        'profile': {
            'exit_type': 'Crashed'              # 'Normal'、'Crashed'、'SessionEnded'
        }
    }
    ```

    !!! warning "Crashed 与 Normal"
        大多数真实浏览器 **偶尔会崩溃**。总是显示 `'Normal'` 退出反而可疑。

        **逼真的策略**：为约 10-20% 的配置文件设置 `'Crashed'`，以模拟正常的用户体验。讽刺的是，偶尔出现“崩溃”反而会让你的自动化更像真人。

    !!! tip "会话事件类型"
        - **Type 0**：会话开始
        - **Type 1**：会话正常结束
        - **Type 2**：会话数据已保存（标签页、窗口）
        - **Type 3**：会话已恢复

        `event_log` 会随时间构建出一份浏览器会话的历史。

## 下一步

- [浏览器选项](browser-options.md)：控制浏览器如何启动的命令行 flag。
- [Proxy 配置](proxies.md)：让浏览器经过 proxy。
- [Fingerprint 注入](../stealth/fingerprint-injection.md)：偏好设置未覆盖的 User-Agent、WebGL 和 canvas 层。
- [保持不被检测](../stealth/index.md)：让你的配置文件设置与你呈现的身份保持一致。
