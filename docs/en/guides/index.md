# Guides

One guide per capability, each with runnable examples. Start with [Core concepts](core-concepts.md) if you're new, or jump straight to the task you need.

## Core concepts

- [Core concepts](core-concepts.md): the tab and browser objects, the async model, and what "no webdriver" means in practice.

## Finding and extracting

- [Element finding](element-finding.md): locate elements with `find()` (by attributes) and `query()` (CSS or XPath).
- [DOM traversal](dom-traversal.md): move from an element to its children, siblings, and shadow roots.
- [Structured extraction](structured-extraction.md): pull typed, validated data from a page with a model.

## Interacting

- [Keyboard](keyboard.md): type text and press keys, with humanized timing.
- [Mouse](mouse.md): click elements or drive raw coordinates, with humanized movement.
- [File operations](file-operations.md): upload files and handle downloads.
- [Iframes](iframes.md): find and drive elements inside frames.
- [Screenshots and PDFs](screenshots-and-pdfs.md): capture the page, an element, or a PDF.

## Network

- [Network monitoring](network-monitoring.md): watch requests and responses as they happen.
- [Request interception](request-interception.md): block, modify, or mock requests.
- [Browser-context HTTP requests](http-requests.md): call APIs from the browser session, with its cookies and auth.
- [HAR recording](network-recording.md): record a session to a HAR file.

## Managing the browser

- [Tabs](tabs.md): open, close, and drive several tabs at once.
- [Browser contexts](browser-contexts.md): isolated sessions in one browser, each with its own cookies.
- [Cookies and sessions](cookies-and-sessions.md): read, set, and persist cookies across runs.
- [Browser options](browser-options.md): command-line flags, headless, and the launch configuration.
- [Browser preferences](browser-preferences.md): Chromium's internal preference dict.
- [Proxies](proxies.md): route traffic through a proxy, with authentication.
- [Remote connections](remote-connections.md): attach to an already-running browser.

## Reacting to events

- [Events](events.md): run callbacks when page and network events fire.
- [Retrying](retrying.md): retry flaky steps with the `retry` decorator.

## What's next

- [Staying undetected](../stealth/index.md): humanized behavior, captcha handling, and fingerprinting.
- [API Reference](../api/index.md): every public class and method.
