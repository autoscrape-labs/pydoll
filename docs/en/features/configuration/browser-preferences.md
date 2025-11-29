# Custom Browser Preferences

One of Pydoll's most powerful features is direct access to Chromium's internal preference system. Unlike traditional browser automation tools that only expose a limited set of options, Pydoll gives you the same level of control that extensions and enterprise administrators have, allowing you to configure **any** browser setting available in Chromium's source code.

## Why Browser Preferences Matter

Browser preferences control every aspect of how Chromium behaves:

- **Performance**: Disable features you don't need for faster page loads
- **Privacy**: Control what data the browser collects and sends
- **Automation**: Remove user prompts and confirmations that break workflows
- **Stealth**: Create realistic browser fingerprints to avoid detection
- **Enterprise**: Apply policies typically only available through Group Policy

!!! info "The Power of Direct Access"
    Most automation tools only expose 10-20 common settings. Pydoll gives you access to **hundreds** of preferences, from download behavior to search suggestions, from network prediction to plugin management. If Chromium can do it, you can configure it.

## Quick Start

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

async def preferences_example():
    options = ChromiumOptions()
    
    # Set preferences using a dict
    options.browser_preferences = {
        'download': {
            'default_directory': '/tmp/downloads',
            'prompt_for_download': False
        },
        'profile': {
            'default_content_setting_values': {
                'notifications': 2  # Block notifications
            }
        }
    }
    
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com')
        
        # Downloads go to /tmp/downloads automatically
        # No notification prompts will appear

asyncio.run(preferences_example())
```

## Understanding Browser Preferences

### What Are Preferences?

Chromium stores all user-configurable settings in a JSON file called `Preferences`, located in the browser's user data directory. This file contains **everything** from your homepage URL to whether images load automatically.

**Typical location:**

- **Linux**: `~/.config/google-chrome/Default/Preferences`
- **macOS**: `~/Library/Application Support/Google/Chrome/Default/Preferences`
- **Windows**: `%LOCALAPPDATA%\Google\Chrome\User Data\Default\Preferences`

### Preferences File Structure

The Preferences file is a nested JSON object:

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

Each dot-separated preference name in Chromium's source maps to a nested JSON path:

- `download.default_directory` → `{'download': {'default_directory': ...}}`
- `profile.password_manager_enabled` → `{'profile': {'password_manager_enabled': ...}}`

### How Chromium Uses Preferences

When Chromium starts:

1. **Reads** the Preferences file from disk
2. **Applies** these settings to configure browser behavior
3. **Updates** the file when users change settings via UI
4. **Falls back** to defaults if preferences are missing

Pydoll intercepts step 1 by pre-populating the Preferences file before the browser starts, ensuring your custom settings are applied from the very first page load.

## How It Works in Pydoll

### Setting Preferences

Use the `browser_preferences` property to set any preference:

```python
from pydoll.browser.options import ChromiumOptions

options = ChromiumOptions()

# Direct assignment - merges with existing preferences
options.browser_preferences = {
    'download': {'default_directory': '/tmp'},
    'intl': {'accept_languages': 'pt-BR,en-US'}
}

# Multiple assignments are merged, not replaced
options.browser_preferences = {
    'profile': {'password_manager_enabled': False}
}

# Both sets of preferences are now active
```

!!! warning "Preferences Are Merged, Not Replaced"
    When you set `browser_preferences` multiple times, the new preferences are **merged** with existing ones. Only the specific keys you set are updated; everything else is preserved.
    
    ```python
    options.browser_preferences = {'download': {'prompt': False}}
    options.browser_preferences = {'profile': {'password_manager_enabled': False}}
    
    # Result: BOTH preferences are set
    # {'download': {'prompt': False}, 'profile': {'password_manager_enabled': False}}
    ```

### Nested Path Syntax

Preferences use nested dictionaries that mirror Chromium's dot-notation:

```python
# Chromium source code constant:
# const char kDownloadDefaultDirectory[] = "download.default_directory";

# Translates to Python dict:
options.browser_preferences = {
    'download': {
        'default_directory': '/path/to/downloads'
    }
}
```

The deeper the nesting, the more specific the preference:

```python
# Top-level: profile
# Second-level: default_content_setting_values  
# Third-level: notifications

options.browser_preferences = {
    'profile': {
        'default_content_setting_values': {
            'notifications': 2,  # Block
            'geolocation': 2,    # Block
            'media_stream': 2    # Block
        }
    }
}
```

## Practical Use Cases

### 1. Performance Optimization

Disable resource-intensive features for faster automation:

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

async def performance_optimized_browser():
    options = ChromiumOptions()
    options.browser_preferences = {
        # Disable network prediction and prefetching
        'net': {
            'network_prediction_options': 2  # 2 = Never predict
        },
        # Disable image loading
        'profile': {
            'default_content_setting_values': {
                'images': 2  # 2 = Block, 1 = Allow
            }
        },
        # Disable plugins
        'webkit': {
            'webprefs': {
                'plugins_enabled': False
            }
        },
        # Disable spell check
        'browser': {
            'enable_spellchecking': False
        }
    }
    
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        
        # Pages load 3-5x faster without images and unnecessary features
        await tab.go_to('https://example.com')
        print("Fast loading complete!")

asyncio.run(performance_optimized_browser())
```

!!! tip "Performance Impact"
    Disabling images alone can reduce page load time by 50-70% for image-heavy sites. Combine with disabling prefetch, spell check, and plugins for maximum speed.

### 2. Privacy & Anti-Tracking

Create a privacy-focused browser configuration:

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

async def privacy_focused_browser():
    options = ChromiumOptions()
    options.browser_preferences = {
        # Enable Do Not Track
        'enable_do_not_track': True,
        
        # Disable referrers
        'enable_referrers': False,
        
        # Disable Safe Browsing (sends URLs to Google)
        'safebrowsing': {
            'enabled': False
        },
        
        # Disable password manager
        'profile': {
            'password_manager_enabled': False
        },
        
        # Disable autofill
        'autofill': {
            'enabled': False,
            'profile_enabled': False
        },
        
        # Disable search suggestions (sends queries to search engine)
        'search': {
            'suggest_enabled': False
        },
        
        # Disable telemetry and metrics
        'user_experience_metrics': {
            'reporting_enabled': False
        },
        
        # Block third-party cookies
        'profile': {
            'block_third_party_cookies': True,
            'cookie_controls_mode': 1
        }
    }
    
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com')
        print("Privacy-focused browser ready!")

asyncio.run(privacy_focused_browser())
```

### 3. Silent Downloads

Automate file downloads without user interaction:

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
                'automatic_downloads': 1  # 1 = Allow, 2 = Block
            }
        },
        # Always download PDFs instead of opening in viewer
        'plugins': {
            'always_open_pdf_externally': True
        }
    }
    
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/downloads')
        
        # Click download links - files save automatically
        download_link = await tab.find(text='Download Report')
        await download_link.click()
        
        await asyncio.sleep(3)
        print(f"File downloaded to: {download_dir}")

asyncio.run(silent_download_automation())
```

### 4. Block Intrusive UI Elements

Remove popups, notifications, and prompts that break automation:

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

async def clean_ui_browser():
    options = ChromiumOptions()
    options.browser_preferences = {
        'profile': {
            'default_content_setting_values': {
                'notifications': 2,      # Block notifications
                'popups': 0,             # Block popups
                'geolocation': 2,        # Block location requests
                'media_stream': 2,       # Block camera/mic access
                'media_stream_mic': 2,   # Block microphone
                'media_stream_camera': 2 # Block camera
            }
        },
        # Disable translation prompts
        'translate': {
            'enabled': False
        },
        # Disable save password prompt
        'credentials_enable_service': False,
        
        # Disable "Chrome is being controlled by automation" infobar
        'devtools': {
            'preferences': {
                'currentDockState': '"undocked"'
            }
        }
    }
    
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com')
        # No popups, no prompts, clean automation!

asyncio.run(clean_ui_browser())
```

### 5. Internationalization & Localization

Configure language and locale preferences:

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

async def localized_browser():
    options = ChromiumOptions()
    options.browser_preferences = {
        # Accept languages (priority order)
        'intl': {
            'accept_languages': 'pt-BR,pt,en-US,en'
        },
        
        # Spellcheck languages
        'spellcheck': {
            'dictionaries': ['pt-BR', 'en-US']
        },
        
        # Translate settings
        'translate': {
            'enabled': True
        },
        'translate_blocked_languages': ['en'],  # Don't offer to translate English
        
        # Default character encoding
        'default_charset': 'UTF-8'
    }
    
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com')
        # Browser configured for Brazilian Portuguese

asyncio.run(localized_browser())
```

## Helper Methods

For common scenarios, Pydoll provides convenience methods:

```python
from pydoll.browser.options import ChromiumOptions

options = ChromiumOptions()

# Download management
options.set_default_download_directory('/tmp/downloads')
options.prompt_for_download = False
options.allow_automatic_downloads = True
options.open_pdf_externally = True

# Content blocking
options.block_notifications = True
options.block_popups = True

# Privacy
options.password_manager_enabled = False

# Internationalization
options.set_accept_languages('pt-BR,en-US,en')
```

These methods are shortcuts that set the correct nested preferences for you:

```python
# This helper:
options.set_default_download_directory('/tmp')

# Is equivalent to:
options.browser_preferences = {
    'download': {
        'default_directory': '/tmp'
    }
}
```

!!! tip "Combine Helpers with Direct Preferences"
    Use helpers for common settings and `browser_preferences` for advanced configuration:
    
    ```python
    # Start with helpers
    options.block_notifications = True
    options.prompt_for_download = False
    
    # Add advanced preferences
    options.browser_preferences = {
        'net': {'network_prediction_options': 2},
        'webkit': {'webprefs': {'plugins_enabled': False}}
    }
    ```

## Finding Preferences in Chromium Source

### Source Code Reference

Chromium defines all preference constants in `pref_names.cc`:

**Official source**: [chromium/src/+/main/chrome/common/pref_names.cc](https://chromium.googlesource.com/chromium/src/+/main/chrome/common/pref_names.cc)

### Reading the Source

Preference constants use dot-notation that maps directly to nested dicts:

```cpp
// From Chromium source (pref_names.cc):
const char kDownloadDefaultDirectory[] = "download.default_directory";
const char kPromptForDownload[] = "download.prompt_for_download";
const char kSafeBrowsingEnabled[] = "safebrowsing.enabled";
const char kBlockThirdPartyCookies[] = "profile.block_third_party_cookies";
```

**Converts to Python:**

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

### Discovery Process

1. **Search the source**: Go to [pref_names.cc](https://chromium.googlesource.com/chromium/src/+/main/chrome/common/pref_names.cc)
2. **Find your preference**: Search for keywords (e.g., "download", "password", "notification")
3. **Note the constant name**: e.g., `kDownloadDefaultDirectory[] = "download.default_directory"`
4. **Convert to dict**: Split by dots and create nested structure

**Example - Finding notification preferences:**

```cpp
// Search for "notification" in pref_names.cc:
const char kPushMessagingAppIdentifierMap[] = 
    "gcm.push_messaging_application_id_map";
const char kDefaultNotificationsSetting[] = 
    "profile.default_content_setting_values.notifications";
```

```python
# Becomes:
options.browser_preferences = {
    'profile': {
        'default_content_setting_values': {
            'notifications': 2  # 2 = block, 1 = allow, 0 = ask
        }
    }
}
```

### Common Preference Patterns

| Category | Example Constant | Python Dict Path |
|----------|-----------------|------------------|
| Downloads | `download.default_directory` | `{'download': {'default_directory': ...}}` |
| Content Settings | `profile.default_content_setting_values.X` | `{'profile': {'default_content_setting_values': {'X': ...}}}` |
| Network | `net.network_prediction_options` | `{'net': {'network_prediction_options': ...}}` |
| Privacy | `safebrowsing.enabled` | `{'safebrowsing': {'enabled': ...}}` |
| Session | `session.restore_on_startup` | `{'session': {'restore_on_startup': ...}}` |

!!! warning "Undocumented Preferences"
    Not all preferences are documented. Some are:
    
    - **Experimental**: May change or be removed in future Chromium versions
    - **Internal**: Used by Chromium's internal systems
    - **Platform-specific**: Only work on certain operating systems
    
    Test thoroughly before relying on undocumented preferences.

## Useful Preferences Reference

Here's a curated list of interesting and useful preferences from Chromium's `pref_names.cc`:

### Content & Media Settings

```python
options.browser_preferences = {
    'profile': {
        'default_content_setting_values': {
            # Content control (0=ask, 1=allow, 2=block)
            'cookies': 1,                    # Allow cookies
            'images': 1,                     # Allow images (2 to block)
            'javascript': 1,                 # Allow JavaScript (2 to block)
            'plugins': 2,                    # Block plugins (Flash, etc.)
            'popups': 0,                     # Block popups
            'geolocation': 2,                # Block location requests
            'notifications': 2,              # Block notifications
            'media_stream': 2,               # Block camera/microphone
            'media_stream_mic': 2,           # Block microphone only
            'media_stream_camera': 2,        # Block camera only
            'automatic_downloads': 1,        # Allow automatic downloads
            'midi_sysex': 2,                 # Block MIDI access
            'clipboard': 1,                  # Allow clipboard access
            'sensors': 2,                    # Block motion sensors
            'usb_guard': 2,                  # Block USB device access
            'serial_guard': 2,               # Block serial port access
            'bluetooth_guard': 2,            # Block Bluetooth
            'file_system_write_guard': 2,    # Block file system writes
        }
    }
}
```

### Network & Performance

```python
options.browser_preferences = {
    'net': {
        # Network prediction: 0=always, 1=wifi only, 2=never
        'network_prediction_options': 2,
        
        # Quick check for server reachability
        'quick_check_enabled': False
    },
    
    # DNS prefetching
    'dns_prefetching': {
        'enabled': False  # Disable to reduce network traffic
    },
    
    # Preconnect to search results
    'search': {
        'suggest_enabled': False,           # Disable search suggestions
        'instant_enabled': False            # Disable instant results
    },
    
    # Alternate error pages
    'alternate_error_pages': {
        'enabled': False  # Don't suggest alternatives for 404s
    }
}
```

### Download Preferences

```python
options.browser_preferences = {
    'download': {
        'default_directory': '/path/to/downloads',
        'prompt_for_download': False,
        'directory_upgrade': True,
        'extensions_to_open': '',           # File types to auto-open
        'open_pdf_externally': True,        # Don't use internal PDF viewer
    },
    
    'download_bubble': {
        'partial_view_enabled': True        # Show download progress bubble
    },
    
    'safebrowsing': {
        'enabled': False  # Disable Safe Browsing download warnings
    }
}
```

### Privacy & Security

```python
options.browser_preferences = {
    # Do Not Track
    'enable_do_not_track': True,
    
    # Referrers
    'enable_referrers': False,
    
    # Safe Browsing
    'safebrowsing': {
        'enabled': False,                   # Disable Safe Browsing
        'enhanced': False                   # Disable enhanced protection
    },
    
    # Privacy Sandbox (Google's cookie replacement)
    'privacy_sandbox': {
        'apis_enabled': False,
        'topics_enabled': False,
        'fledge_enabled': False
    },
    
    # Third-party cookies
    'profile': {
        'block_third_party_cookies': True,
        'cookie_controls_mode': 1,          # Block third-party in incognito
        
        # Content settings
        'default_content_setting_values': {
            'cookies': 1,
            'third_party_cookie_blocking_enabled': True
        }
    },
    
    # WebRTC (can leak real IP)
    'webrtc': {
        'ip_handling_policy': 'default_public_interface_only',
        'multiple_routes_enabled': False,
        'nonproxied_udp_enabled': False
    }
}
```

### Autofill & Passwords

```python
options.browser_preferences = {
    'autofill': {
        'enabled': False,                   # Disable form autofill
        'profile_enabled': False,           # Disable address autofill
        'credit_card_enabled': False,       # Disable credit card autofill
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

### Browser Behavior & UI

```python
import time

options.browser_preferences = {
    # Homepage and startup
    'homepage': 'https://www.google.com',
    'homepage_is_newtabpage': False,
    'newtab_page_location_override': 'https://www.google.com',
    
    'session': {
        'restore_on_startup': 1,            # 0=new tab, 1=restore, 4=specific URLs, 5=new tab page
        'startup_urls': ['https://www.google.com'],
        'session_data_status': 3            # Session data status (internal)
    },
    
    # Welcome page and window
    'browser': {
        'has_seen_welcome_page': True,      # Skip welcome screen
        'window_placement': {
            'bottom': 1032,                 # Window bottom position
            'left': 2247,                   # Window left position
            'right': 3192,                  # Window right position
            'top': 31,                      # Window top position
            'maximized': False,             # Window is maximized
            'work_area_bottom': 1080,       # Screen work area bottom
            'work_area_left': 1920,         # Screen work area left
            'work_area_right': 3840,        # Screen work area right
            'work_area_top': 0              # Screen work area top
        }
    },
    
    # Extensions
    'extensions': {
        'ui': {
            'developer_mode': False
        },
        'alerts': {
            'initialized': True
        },
        'theme': {
            'system_theme': 2               # 0=default, 1=light, 2=dark
        },
        'last_chrome_version': '130.0.6723.91'  # Must match your version
    },
    
    # Translate
    'translate': {
        'enabled': False                    # Disable translation prompts
    },
    'translate_blocked_languages': ['en'],  # Never translate English
    'translate_site_blacklist': [],         # Legacy (use blocklist_with_time)
    
    # Bookmarks
    'bookmark_bar': {
        'show_on_all_tabs': False
    },
    
    # Tabs
    'tabs': {
        'new_tab_position': 0               # 0=right, 1=after current
    },
    'pinned_tabs': [],                      # List of pinned tab URLs
    
    # New Tab Page (timestamps in Chrome format)
    'NewTabPage': {
        'PrevNavigationTime': str(int(time.time() * 1000000) + 11644473600000000)  # Chrome timestamp
    },
    'ntp': {
        'num_personal_suggestions': 6       # Number of suggestions (0-10)
    },
    
    # Toolbar customization
    'toolbar': {
        'pinned_chrome_labs_migration_complete': True
    }
}
```

!!! info "Chrome Timestamp Format"
    Chrome uses Windows FILETIME format: microseconds since January 1, 1601 UTC.
    
    Convert Python timestamp:
    ```python
    import time
    chrome_time = int(time.time() * 1000000) + 11644473600000000
    ```

### Spelling & Language

```python
options.browser_preferences = {
    'browser': {
        'enable_spellchecking': False       # Disable spell check
    },
    
    'spellcheck': {
        'dictionaries': ['en-US', 'pt-BR'], # Spell check languages
        'dictionary': '',                   # Legacy preference (keep empty)
        'use_spelling_service': False       # Don't send to Google
    },
    
    'intl': {
        'accept_languages': 'pt-BR,pt,en-US,en',
        'selected_languages': 'pt-BR,pt,en-US,en'  # Explicitly selected
    },
    
    # Translation behavior and history
    'translate': {
        'enabled': True
    },
    'translate_accepted_count': {
        'pt-BR': 0,
        'es': 5                             # Accepted 5 Spanish translations
    },
    'translate_denied_count_for_language': {
        'en': 10                            # Never translate English
    },
    'translate_ignored_count_for_language': {
        'en': 1
    },
    'translate_site_blocklist_with_time': {},  # Sites never to translate
    
    # Accessibility caption language
    'accessibility': {
        'captions': {
            'live_caption_language': 'pt-BR'
        }
    },
    
    # Language model counters (usage statistics)
    'language_model_counters': {
        'en': 2,                            # English word count
        'pt': 10                            # Portuguese word count
    }
}
```

!!! info "Language Model Counters"
    These counters track language usage statistics for Chrome's machine learning models:
    
    - Used for predicting user language preferences
    - Affects search suggestions and autocomplete
    - Higher counts indicate more frequent use
    - Realistic values: 0-1000 for occasional use, 1000+ for heavy use

### Accessibility

```python
options.browser_preferences = {
    'accessibility': {
        'image_labels_enabled': False       # Don't get image labels from Google
    },
    
    # Font settings
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

### Media & Audio

```python
options.browser_preferences = {
    # Audio
    'audio': {
        'mute_enabled': False               # Start with audio on/off
    },
    
    # Autoplay
    'media': {
        'autoplay_policy': 0,               # 0=allow, 1=user gesture, 2=document user activation
        'video_fullscreen_orientation_lock': False
    },
    
    # WebGL
    'webkit': {
        'webprefs': {
            'webgl_enabled': True,          # Enable/disable WebGL
            'webgl2_enabled': True
        }
    }
}
```

### Printing

```python
options.browser_preferences = {
    'printing': {
        'print_preview_sticky_settings': {
            'appState': '{\"version\":2,\"recentDestinations\":[{\"id\":\"Save as PDF\",\"origin\":\"local\"}],\"marginsType\":3,\"customMargins\":{\"marginTop\":63,\"marginRight\":192,\"marginBottom\":240,\"marginLeft\":260}}'
        }
    },
    
    'savefile': {
        'default_directory': '/tmp'         # Default save location for PDFs
    }
}
```

!!! tip "Printing appState Format"
    The `appState` is a JSON-encoded string. For easier manipulation:
    
    ```python
    import json
    
    app_state = {
        'version': 2,
        'recentDestinations': [{
            'id': 'Save as PDF',
            'origin': 'local'
        }],
        'marginsType': 3,                   # 0=default, 1=no margins, 2=minimum, 3=custom
        'customMargins': {
            'marginTop': 63,
            'marginRight': 192,
            'marginBottom': 240,
            'marginLeft': 260
        },
        'isHeaderFooterEnabled': False,
        'scaling': '100',
        'scalingType': 3,                   # 0=default, 1=fit to page, 2=fit to paper, 3=custom
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
    
    # Convert to string for appState
    options.browser_preferences = {
        'printing': {
            'print_preview_sticky_settings': {
                'appState': json.dumps(app_state)
            }
        }
    }
    ```

### WebRTC & Peer-to-Peer

```python
options.browser_preferences = {
    'webrtc': {
        # IP handling policy
        'ip_handling_policy': 'default_public_interface_only',
        
        # UDP transport options
        'udp_port_range': '10000-10100',    # Restrict UDP port range
        
        # Disable peer-to-peer
        'multiple_routes_enabled': False,
        'nonproxied_udp_enabled': False,
        
        # Text log collection
        'text_log_collection_allowed': False
    }
}
```

### Site Isolation & Security

```python
options.browser_preferences = {
    # Site isolation
    'site_isolation': {
        'isolate_origins': '',              # Comma-separated origins to isolate
        'site_per_process': True            # Full site isolation
    },
    
    # Mixed content
    'mixed_content': {
        'auto_upgrade_enabled': True        # Upgrade HTTP to HTTPS
    },
    
    # SSL/TLS
    'ssl': {
        'rev_checking': {
            'enabled': True                 # Check certificate revocation
        }
    }
}
```

### Installation & Country Metadata

```python
import uuid
from pydoll.browser.options import ChromiumOptions

options = ChromiumOptions()
options.browser_preferences = {
    # Country ID at install (affects default settings and locale)
    'countryid_at_install': 16978,          # Varies by country (e.g., 16978 for Brazil)
    
    # Default apps installation state
    'default_apps_install_state': 3,        # 0=not installed, 1=installed, 3=migrated
    
    # Enterprise profile GUID (for managed browsers)
    'enterprise_profile_guid': str(uuid.uuid4()),
    
    # Default search provider
    'default_search_provider': {
        'guid': ''                          # Empty for default (Google)
    }
}
```

!!! info "Country ID Values"
    `countryid_at_install` is a numeric code representing the country where Chrome was first installed:
    
    - **16978**: Brazil (BR)
    - **16965**: United States (US)
    - **16967**: Great Britain (GB)
    - **16966**: Germany (DE)
    - **16972**: Japan (JP)
    - And many others...
    
    This affects default language, currency, and regional settings. For realistic fingerprinting, match this to your target region.

### Experimental Features

```python
options.browser_preferences = {
    # Chrome Labs experiments
    'browser': {
        'labs': {
            'enabled': False
        }
    },
    
    # Preloading
    'preload': {
        'enabled': False                    # Disable page preloading
    },
    
    # Smooth scrolling
    'smooth_scrolling': {
        'enabled': True
    },
    
    # Hardware acceleration
    'hardware_acceleration_mode': {
        'enabled': True                     # Disable for headless performance
    }
}
```

### DevTools & Developer Options

```python
options.browser_preferences = {
    'devtools': {
        'preferences': {
            # DevTools appearance
            'currentDockState': '"right"',              # "bottom", "right", "undocked"
            'uiTheme': '"dark"',                        # "dark", "light", "system"
            
            # Console settings
            'consoleTimestampsEnabled': 'true',
            'preserveConsoleLog': 'true',
            
            # Network panel
            'network.disableCache': 'false',
            'network.color-code-resource-types': 'true',
            'network-panel-split-view-state': '{"vertical":{"size":0}}',
            
            # Source maps
            'cssSourceMapsEnabled': 'true',
            'jsSourceMapsEnabled': 'true',
            
            # Elements panel
            'elements.styles.sidebar.width': '{"vertical":{"size":0,"showMode":"OnlyMain"}}',
            
            # Inspector versioning
            'inspectorVersion': '37',
            
            # Selected panel
            'panel-selected-tab': '"network"',          # Last opened panel
            
            # Request info expanded categories
            'request-info-general-category-expanded': 'true',
            'request-info-request-headers-category-expanded': 'true',
            'request-info-response-headers-category-expanded': 'true'
        },
        'synced_preferences_sync_disabled': {
            'adorner-settings': '[{"adorner":"grid","isEnabled":true},{"adorner":"flex","isEnabled":true}]',
            'syncedInspectorVersion': '37'
        }
    },
    
    # GCM (Google Cloud Messaging)
    'gcm': {
        'product_category_for_subtypes': 'com.chrome.linux'  # com.chrome.windows, com.chrome.macos
    }
}
```

!!! tip "DevTools Preferences Format"
    DevTools preferences use a unique format where boolean and string values are stored as **JSON-encoded strings** (e.g., `'true'` not `True`, `'"dark"'` not `'dark'`). This is because DevTools settings are serialized directly to JSON.
    
    For complex objects, double-encode:
    ```python
    import json
    
    # Create the object
    split_view = {'vertical': {'size': 0}}
    
    # Double-encode for DevTools
    devtools_value = json.dumps(json.dumps(split_view))
    # Result: '"{\\"vertical\\":{\\"size\\":0}}"'
    ```

### Sync & Sign-In Control

```python
import time
from pydoll.browser.options import ChromiumOptions

options = ChromiumOptions()
options.browser_preferences = {
    'signin': {
        'allowed': True,                        # Allow sign-in to Google
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
    
    # Google services
    'google': {
        'services': {
            'signin_scoped_device_id': '<your-device-id>'  # Generate unique ID
        }
    },
    
    # GAIA (Google Accounts Infrastructure)
    'gaia_cookie': {
        'changed_time': str(int(time.time())),
        'hash': '',
        'last_list_accounts_data': '[]'
    }
}
```

### Optimization & Performance Tracking

```python
import time
from pydoll.browser.options import ChromiumOptions

options = ChromiumOptions()
options.browser_preferences = {
    # Optimization guide (Google's performance hints)
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
    
    # History clusters (grouping related browsing)
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
    
    # Domain diversity metrics
    'domain_diversity': {
        'last_reporting_timestamp': str(int(time.time()))
    },
    
    # Segmentation platform (user behavior analysis)
    'segmentation_platform': {
        'device_switcher_util': {
            'result': {
                'labels': ['NotSynced']
            }
        },
        'last_db_compaction_time': str(int(time.time()))
    },
    
    # Zero suggest (omnibox predictions)
    'zerosuggest': {
        'cachedresults': '',
        'cachedresults_with_url': {}
    }
}
```

!!! info "Performance Tracking Preferences"
    These preferences are typically used by Chrome to track and optimize performance. For automation, you can leave them empty or set realistic values to appear more like a normal browser.

### Session Events & Crash Handling

Chrome tracks session history for recovery and telemetry:

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
                'type': 0                   # 0=session start
            },
            {
                'crashed': False,
                'did_schedule_command': True,
                'first_session_service': True,
                'tab_count': 1,
                'time': str(int(time.time() * 1000000) + 11644473600000000),
                'type': 2,                  # 2=session data saved
                'window_count': 1
            }
        ],
        'session_data_status': 3            # 0=unknown, 1=no data, 2=some data, 3=full data
    },
    
    # Profile exit type (important for fingerprinting)
    'profile': {
        'exit_type': 'Crashed'              # 'Normal', 'Crashed', 'SessionEnded'
    }
}
```

!!! warning "Crashed vs Normal"
    Most real browsers **crash occasionally**. Always showing `'Normal'` exit is suspicious.
    
    **Realistic strategy**: Set `'Crashed'` for ~10-20% of profiles to simulate normal user experience. Ironically, having occasional "crashes" makes your automation look more human.

!!! tip "Session Event Types"
    - **Type 0**: Session start
    - **Type 1**: Session ended normally
    - **Type 2**: Session data saved (tabs, windows)
    - **Type 3**: Session restored
    
    The `event_log` builds a history of browser sessions over time.

## Stealth & Fingerprinting

Creating a realistic browser fingerprint is crucial for avoiding bot detection systems. This section covers both basic and advanced techniques.

### Quick Stealth Setup

For most use cases, this simple configuration provides good anti-detection:

```python
import asyncio
import time
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

async def quick_stealth():
    options = ChromiumOptions()
    
    # Simulate a 60-day-old browser
    fake_timestamp = int(time.time()) - (60 * 24 * 60 * 60)
    
    options.browser_preferences = {
        # Fake usage history
        'profile': {
            'last_engagement_time': fake_timestamp,
            'exited_cleanly': True,
            'exit_type': 'Normal'
        },
        
        # Realistic homepage
        'homepage': 'https://www.google.com',
        'session': {
            'restore_on_startup': 1,
            'startup_urls': ['https://www.google.com']
        },
        
        # Enable features real users have
        'enable_do_not_track': False,  # Most users don't enable this
        'safebrowsing': {'enabled': True},
        'autofill': {'enabled': True},
        'search': {'suggest_enabled': True},
        'dns_prefetching': {'enabled': True}
    }
    
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        await tab.go_to('https://bot-detection-site.com')
        print("Stealth mode activated!")

asyncio.run(quick_stealth())
```

!!! tip "Key Stealth Principles"
    **Enable, don't disable**: Real users have Safe Browsing, autofill, and search suggestions enabled. Disabling everything looks suspicious.
    
    **Age your profile**: Fresh installs are a red flag. Simulate a browser that's been used for weeks or months.
    
    **Match the majority**: Use default settings that 90% of users have, not privacy-focused configurations.

### Advanced Fingerprinting

For maximum realism, simulate detailed browser usage history:

```python
import time
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

def create_realistic_browser() -> ChromiumOptions:
    """Create a browser with comprehensive fingerprinting resistance."""
    options = ChromiumOptions()
    
    # Timestamps
    current_time = int(time.time())
    install_time = current_time - (90 * 24 * 60 * 60)  # 90 days ago
    last_use = current_time - (3 * 60 * 60)            # 3 hours ago
    
    options.browser_preferences = {
        # Profile metadata (critical for fingerprinting)
        'profile': {
            'created_by_version': '130.0.6723.91',      # Must match your Chrome version
            'creation_time': str(install_time),
            'last_engagement_time': str(last_use),
            'exit_type': 'Crashed',                     # 'Normal', 'Crashed', 'SessionEnded'
            'name': 'Pessoa 1',                         # Realistic profile name
            'avatar_index': 26,                         # 0-26 available avatars
            
            # Realistic content settings
            'default_content_setting_values': {
                'cookies': 1,
                'images': 1,
                'javascript': 1,
                'popups': 0,
                'notifications': 2,
                'geolocation': 0,           # Ask (not block)
                'media_stream': 0           # Ask (realistic)
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
            
            # Security metadata
            'family_member_role': 'not_in_family',
            'managed_user_id': '',
            'were_old_google_logins_removed': True
        },
        
        # Browser usage metadata
        'browser': {
            'has_seen_welcome_page': True,
            'window_placement': {
                'work_area_bottom': 1080,
                'work_area_left': 0,
                'work_area_right': 1920,
                'work_area_top': 0
            }
        },
        
        # Installation metadata
        'countryid_at_install': 16978,              # Varies by country
        'default_apps_install_state': 3,
        
        # Extensions metadata
        'extensions': {
            'last_chrome_version': '130.0.6723.91',  # Must match your version
            'alerts': {'initialized': True},
            'theme': {'system_theme': 2}
        },
        
        # Session activity (shows regular usage)
        'in_product_help': {
            'session_start_time': str(current_time),
            'session_last_active_time': str(current_time),
            'recent_session_start_times': [
                str(current_time - (24 * 60 * 60)),
                str(current_time - (48 * 60 * 60)),
                str(current_time - (72 * 60 * 60))
            ]
        },
        
        # Session restore
        'session': {
            'restore_on_startup': 1,
            'startup_urls': ['https://www.google.com']
        },
        
        # Homepage
        'homepage': 'https://www.google.com',
        'homepage_is_newtabpage': False,
        
        # Translation history (shows multilingual usage)
        'translate': {'enabled': True},
        'translate_accepted_count': {'es': 2, 'fr': 1},
        'translate_denied_count_for_language': {'en': 1},
        
        # Spell check
        'spellcheck': {
            'dictionaries': ['en-US', 'pt-BR'],
            'dictionary': ''
        },
        
        # Languages
        'intl': {
            'selected_languages': 'en-US,en,pt-BR'
        },
        
        # Sign-in metadata
        'signin': {
            'allowed': True,
            'cookie_clear_on_exit_migration_notice_complete': True
        },
        
        # Safe Browsing (most users have this)
        'safebrowsing': {
            'enabled': True,
            'enhanced': False
        },
        
        # Autofill (common for real users)
        'autofill': {
            'enabled': True,
            'profile_enabled': True
        },
        
        # Search suggestions
        'search': {'suggest_enabled': True},
        
        # DNS prefetch
        'dns_prefetching': {'enabled': True},
        
        # Do NOT Track (usually off)
        'enable_do_not_track': False,
        
        # WebRTC (default settings)
        'webrtc': {
            'ip_handling_policy': 'default',
            'multiple_routes_enabled': True
        },
        
        # Privacy Sandbox (Google's cookie replacement - realistic users have this)
        'privacy_sandbox': {
            'first_party_sets_data_access_allowed_initialized': True,
            'm1': {
                'ad_measurement_enabled': True,
                'fledge_enabled': True,
                'row_notice_acknowledged': True,
                'topics_enabled': True
            }
        },
        
        # Media engagement
        'media': {
            'engagement': {'schema_version': 5}
        },
        
        # Web apps
        'web_apps': {
            'did_migrate_default_chrome_apps': ['app-id'],
            'last_preinstall_synchronize_version': '130'
        }
    }
    
    return options

# Usage
async def advanced_stealth():
    options = create_realistic_browser()
    
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        await tab.go_to('https://advanced-bot-detection.com')
        # Browser appears as a genuine 90-day-old installation
```

!!! warning "Version Consistency is Critical"
    **Always match Chrome versions**: Ensure `profile.created_by_version` and `extensions.last_chrome_version` match your actual Chrome version. Mismatched versions are an instant red flag.
    
    ```python
    # Get your Chrome version programmatically:
    async with Chrome() as browser:
        tab = await browser.start()
        version = await browser.get_version()
        chrome_version = version['product'].split('/')[1]  # e.g., '130.0.6723.91'
        print(f"Use this version: {chrome_version}")
    ```

!!! info "What Fingerprinting Preferences Do"
    **Profile age**: `creation_time` and `last_engagement_time` prove the browser isn't a fresh install.
    
    **Usage history**: `recent_session_start_times` shows regular browsing patterns.
    
    **Translation history**: `translate_accepted_count` indicates a real person using multiple languages.
    
    **Window placement**: Realistic screen dimensions that match actual monitor resolutions.
    
    **Privacy Sandbox**: Google's new tracking system. Disabling it is unusual and suspicious.

## Performance Impact

Understanding the performance implications of browser preferences helps you optimize for your specific use case:

| Preference Category | Expected Impact | Use Case |
|---------------------|----------------|----------|
| Disable images | 50-70% faster loads | Scraping text content |
| Disable prefetch | 10-20% faster loads | Reduce bandwidth usage |
| Disable plugins | 5-10% faster loads | Security and performance |
| Block notifications | Eliminates popups | Clean automation |
| Silent downloads | Eliminates prompts | Automated file downloads |

!!! tip "Speed vs Stealth Trade-off"
    **For speed**: Disable images, prefetch, plugins, and spell check.
    
    **For stealth**: Enable Safe Browsing, autofill, search suggestions, and DNS prefetch (even though they slow things down).
    
    **Balanced approach**: Enable stealth features but disable images and plugins. This gives 40-50% speedup while maintaining realistic fingerprint.

## See Also

- **[Deep Dive: Browser Preferences](../../deep-dive/browser-preferences.md)** - Architectural details and internals
- **[Page Load State](page-load-state.md)** - Control when pages are considered loaded
- **[Proxy Configuration](proxy.md)** - Configure network proxies
- **[Cookies & Sessions](../browser-management/cookies-sessions.md)** - Manage browser state
- **[Chromium Source: pref_names.cc](https://chromium.googlesource.com/chromium/src/+/main/chrome/common/pref_names.cc)** - Official preference constants
- **[Chromium Source: pref_names.h](https://github.com/chromium/chromium/blob/main/chrome/common/pref_names.h)** - Header file with definitions

Custom browser preferences give you unprecedented control over browser behavior, enabling sophisticated automation, performance optimization, and privacy configuration that simply isn't possible with traditional automation tools. This level of access transforms Pydoll from a simple automation library into a complete browser control system.
