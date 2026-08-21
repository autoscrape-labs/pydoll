# Browser preferences

Preferences are the settings that live inside a Chromium profile: the download folder, accepted languages, whether pop-ups and notifications are allowed, and hundreds more. You set them on `ChromiumOptions` before starting the browser, and Pydoll applies them to the profile it launches.

Preferences are not the same as [command-line arguments](browser-options.md). Arguments are flags passed to the Chromium binary at launch (`--headless`, `--proxy-server`); preferences are entries in the profile's settings, the same ones the Settings UI writes. Use arguments for how the process starts, and preferences for how the profile behaves.

## Set common preferences

The everyday preferences have helper methods and properties, so you set them without memorizing Chromium's internal keys or magic numbers.

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

The available helpers:

| Helper | What it sets |
|--------|--------------|
| `options.set_default_download_directory(path)` | Where downloads are saved |
| `options.set_accept_languages('en-US,en')` | The `Accept-Language` header and `navigator.languages` |
| `options.prompt_for_download = False` | Whether Chrome asks before each download |
| `options.allow_automatic_downloads = True` | Whether a page may trigger multiple downloads |
| `options.block_popups = True` | Block pop-up windows |
| `options.block_notifications = True` | Block site notification prompts |
| `options.password_manager_enabled = False` | Turn Chrome's password manager on or off |
| `options.open_pdf_externally = True` | Download PDFs instead of opening the viewer |

Each helper writes the right nested key with the right value, so `block_notifications = True` becomes the notification setting Chromium expects, not a number you have to look up.

!!! tip "Language, downloads, and detection"
    `set_accept_languages` should match the locale you present elsewhere; a US language on a non-US IP is a mismatch anti-bot systems check. See [Staying undetected](../stealth/index.md).

## Set any preference

For a preference without a helper, assign to `options.browser_preferences`. It takes a nested dict and merges it into whatever is already set, so you can build it up across several assignments.

```python
options = ChromiumOptions()

options.browser_preferences = {
    'download': {'default_directory': '/tmp/downloads'},
    'intl': {'accept_languages': 'en-US,en'},
}

# a later assignment merges, it does not replace
options.browser_preferences = {
    'profile': {'default_content_setting_values': {'images': 2}},
}
```

Chromium documents preferences as dotted paths (for example `download.default_directory`). Each dot is one level of the dict: `download.default_directory` becomes `{'download': {'default_directory': ...}}`. Nest the keys to match the path.

!!! note "Do not wrap it in `prefs`"
    Assign the preference tree directly. Wrapping it in a top-level `{'prefs': {...}}` key raises an error; the helpers and the dict both expect the real paths at the top level.

## Build a realistic profile for stealth

Anti-bot systems read the profile, not just the page. A fresh, empty profile with every convenience feature disabled looks nothing like a real user, so preferences are a lever for looking normal. The guiding idea runs opposite to most privacy advice:

- **Enable, don't disable.** Real users leave Safe Browsing, autofill, and search suggestions on. A profile with everything switched off is itself a signal.
- **Age the profile.** A profile created seconds ago is a red flag. Backdate the usage timestamps so it looks weeks or months old.
- **Match your real Chrome.** Any version string you set (in `profile` or `extensions`) must match the Chrome binary you are actually running, or the mismatch gives you away.

```python
import asyncio
import time

from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions


def realistic_options() -> ChromiumOptions:
    now = int(time.time())
    installed = now - (90 * 24 * 60 * 60)   # 90 days ago
    last_used = now - (3 * 60 * 60)         # 3 hours ago

    options = ChromiumOptions()
    options.browser_preferences = {
        'profile': {
            'created_by_version': '130.0.6723.91',   # match your real Chrome
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

!!! note "Preferences are one layer, not the whole fingerprint"
    Preferences shape the profile's identity (usage history, enabled features, languages). They do not change the User-Agent, WebGL, canvas, or the network-layer fingerprint. For those, and for keeping every layer consistent, see [Fingerprint Injection](../stealth/fingerprint-injection.md).

## Preferences reference

The blocks below list Chromium preferences worth knowing, grouped by area. They are Chromium's own settings, not Pydoll's, so the exact keys and accepted values are defined by Chromium and can change between versions; Pydoll passes whatever you set straight through. Content-setting values follow Chromium's convention: `0` = ask, `1` = allow, `2` = block. Treat this as a lookup, and reach for the [helper methods](#set-common-preferences) first when one exists.

??? example "Content & Media Settings"


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


??? example "Network & Performance"


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


??? example "Download Preferences"


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


??? example "Privacy & Security"


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


??? example "Autofill & Passwords"


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


??? example "Browser Behavior & UI"


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

    !!! note "Chrome Timestamp Format"
        Chrome uses Windows FILETIME format: microseconds since January 1, 1601 UTC.

        Convert Python timestamp:
        ```python
        import time
        chrome_time = int(time.time() * 1000000) + 11644473600000000
        ```


??? example "Spelling & Language"


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

    !!! note "Language Model Counters"
        These counters track language usage statistics for Chrome's machine learning models:

        - Used for predicting user language preferences
        - Affects search suggestions and autocomplete
        - Higher counts indicate more frequent use
        - Realistic values: 0-1000 for occasional use, 1000+ for heavy use


??? example "Accessibility"


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


??? example "Media & Audio"


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


??? example "Printing"


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


??? example "WebRTC & Peer-to-Peer"


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


??? example "Site Isolation & Security"


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


??? example "Installation & Country Metadata"


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

    !!! note "Country ID Values"
        `countryid_at_install` is a numeric code representing the country where Chrome was first installed:

        - **16978**: Brazil (BR)
        - **16965**: United States (US)
        - **16967**: Great Britain (GB)
        - **16966**: Germany (DE)
        - **16972**: Japan (JP)
        - And many others...

        This affects default language, currency, and regional settings. For realistic fingerprinting, match this to your target region.


??? example "Experimental Features"


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


??? example "DevTools & Developer Options"


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


??? example "Sync & Sign-In Control"


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


??? example "Optimization & Performance Tracking"


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

    !!! note "Performance Tracking Preferences"
        These preferences are typically used by Chrome to track and optimize performance. For automation, you can leave them empty or set realistic values to appear more like a normal browser.


??? example "Session Events & Crash Handling"


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

## What's next

- [Browser options](browser-options.md): the command-line flags that control how the browser launches.
- [Proxy configuration](proxies.md): route the browser through a proxy.
- [Fingerprint Injection](../stealth/fingerprint-injection.md): the User-Agent, WebGL, and canvas layer that preferences do not cover.
- [Staying undetected](../stealth/index.md): keep your profile settings consistent with the identity you present.
