# API Reference

This section documents the public classes you work with directly. The guides teach how to use them; this reference specifies what each one exposes. Every page links back to the guide that covers it.

## Browser

| Class | What it does | Guide |
|-------|--------------|-------|
| [`Chrome`](browser/chrome.md) | Launch and control a Chrome browser | [Getting started](../getting-started.md) |
| [`Edge`](browser/edge.md) | Launch and control a Microsoft Edge browser | [Getting started](../getting-started.md) |
| [`ChromiumOptions`](browser/options.md) | Configure the browser before launch | [Browser options](../guides/browser-options.md) |
| [`Tab`](browser/tab.md) | Drive a tab: navigate, find, input, events, network | [Core concepts](../guides/core-concepts.md) |
| [`Request`](browser/requests.md) | Make HTTP requests inside the browser session | [HTTP requests](../guides/http-requests.md) |

## Elements

| Class | What it does | Guide |
|-------|--------------|-------|
| [`WebElement`](elements/web_element.md) | Interact with a located element | [Element finding](../guides/element-finding.md) |
| [`ShadowRoot`](elements/shadow_root.md) | Query inside a shadow root | [DOM traversal](../guides/dom-traversal.md#shadow-dom) |

## Extraction and connection

| Class | What it does | Guide |
|-------|--------------|-------|
| [`ExtractionModel`, `Field`](extraction.md) | Map the DOM into typed, validated objects | [Structured extraction](../guides/structured-extraction.md) |
| [`ConnectionHandler`](connection/connection.md) | Manage the CDP WebSocket connection | [Remote connections](../guides/remote-connections.md) |

## Core

| Reference | What it holds | Guide |
|-----------|---------------|-------|
| [Constants](core/constants.md) | Enums like `By`, `Key`, and `PermissionType` | [Selectors](../basics/selectors.md) |
| [Exceptions](core/exceptions.md) | Errors Pydoll raises, like `ElementNotFound` | [Element finding](../guides/element-finding.md#handle-missing-elements) |

Every Pydoll operation is asynchronous and fully typed. See [Async Python](../basics/async-python.md) for the `async`/`await` basics.
