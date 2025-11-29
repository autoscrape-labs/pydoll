# Storage Commands

Storage commands provide comprehensive browser storage management including cookies, localStorage, sessionStorage, and IndexedDB.

## Overview

The storage commands module enables management of all browser storage mechanisms, providing functionality for data persistence and retrieval.

::: pydoll.commands.storage_commands
    options:
      show_root_heading: true
      show_source: false
      heading_level: 2
      filters:
        - "!^_"
        - "!^__"

## Usage

Storage commands are used for managing browser storage across different mechanisms:

```python
from pydoll.commands.storage_commands import get_cookies, set_cookies, clear_data_for_origin
from pydoll.connection.connection_handler import ConnectionHandler

# Get cookies for a domain
connection = ConnectionHandler()
cookies = await get_cookies(connection, urls=["https://example.com"])

# Set a new cookie
await set_cookies(connection, cookies=[{
    "name": "session_id",
    "value": "abc123",
    "domain": "example.com",
    "path": "/",
    "httpOnly": True,
    "secure": True
}])

# Clear all storage for an origin
await clear_data_for_origin(
    connection,
    origin="https://example.com",
    storage_types="all"
)
```

## Key Functionality

The storage commands module provides functions for:

### Cookie Management
- `get_cookies()` - Get cookies by URL or domain
- `set_cookies()` - Set new cookies
- `delete_cookies()` - Delete specific cookies
- `clear_cookies()` - Clear all cookies

### Local Storage
- `get_dom_storage_items()` - Get localStorage items
- `set_dom_storage_item()` - Set localStorage item
- `remove_dom_storage_item()` - Remove localStorage item
- `clear_dom_storage()` - Clear localStorage

### Session Storage
- Session storage operations (similar to localStorage)
- Session-specific data management
- Tab-isolated storage

### IndexedDB
- `get_database_names()` - Get IndexedDB databases
- `request_database()` - Access database structure
- `request_data()` - Query database data
- `clear_object_store()` - Clear object stores

### Cache Storage
- `request_cache_names()` - Get cache names
- `request_cached_response()` - Get cached responses
- `delete_cache()` - Delete cache entries

### Application Cache (Deprecated)
- Legacy application cache support
- Manifest-based caching

## Advanced Features

### Bulk Operations
```python
# Clear all storage types for multiple origins
origins = ["https://example.com", "https://api.example.com"]
for origin in origins:
    await clear_data_for_origin(
        connection,
        origin=origin,
        storage_types="cookies,local_storage,session_storage,indexeddb"
    )
```

### Storage Quotas
```python
# Get storage quota information
quota_info = await get_usage_and_quota(connection, origin="https://example.com")
print(f"Used: {quota_info.usage} bytes")
print(f"Quota: {quota_info.quota} bytes")
```

### Cross-Origin Storage
```python
# Manage storage across different origins
await set_cookies(connection, cookies=[{
    "name": "cross_site_token",
    "value": "token123",
    "domain": ".example.com",  # Applies to all subdomains
    "sameSite": "None",
    "secure": True
}])
```

## Storage Types

The module supports various storage mechanisms:

| Storage Type | Persistence | Scope | Capacity |
|--------------|-------------|-------|----------|
| Cookies | Persistent | Domain/Path | ~4KB per cookie |
| localStorage | Persistent | Origin | ~5-10MB |
| sessionStorage | Session | Tab | ~5-10MB |
| IndexedDB | Persistent | Origin | Large (GB+) |
| Cache API | Persistent | Origin | Large |

!!! warning "Privacy Considerations"
    Storage operations can affect user privacy. Always handle storage data responsibly and in compliance with privacy regulations. 