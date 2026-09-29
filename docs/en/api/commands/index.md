# Commands

Each module in `pydoll.commands` wraps one Chrome DevTools Protocol domain. Its functions take typed parameters and return the command dict that the browser understands, so the rest of Pydoll never builds CDP payloads by hand.

## Modules

| Module | Purpose | Reference |
|--------|---------|-----------|
| `browser_commands.py` | Browser-level operations and window management | [Browser Commands](browser.md) |
| `dom_commands.py` | DOM tree manipulation and element operations | [DOM Commands](dom.md) |
| `input_commands.py` | Input event simulation (keyboard, mouse, touch) | [Input Commands](input.md) |
| `network_commands.py` | Network monitoring and request interception | [Network Commands](network.md) |
| `page_commands.py` | Page lifecycle management and navigation | [Page Commands](page.md) |
| `runtime_commands.py` | JavaScript execution and runtime management | [Runtime Commands](runtime.md) |
| `storage_commands.py` | Browser storage access (cookies, local storage, etc.) | [Storage Commands](storage.md) |
| `target_commands.py` | Target management and tab operations | [Target Commands](target.md) |
| `fetch_commands.py` | Network request interception and modification | [Fetch Commands](fetch.md) |

Each function builds a typed command dict for one CDP method. `Tab`, `Browser` and `WebElement` call them internally; if you need a command they do not expose, build it here and send it with `tab.execute_command(...)` or `browser.execute_command(...)`.
