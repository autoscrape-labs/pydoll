# Features Guide

Welcome to Pydoll's comprehensive features documentation! This is where you'll discover everything that makes Pydoll a powerful and flexible browser automation tool. Whether you're just starting out or looking to leverage advanced capabilities, you'll find detailed guides, practical examples, and best practices for each feature.

## What You'll Find Here

This guide is organized into logical sections that reflect your automation journey: from basic concepts to advanced techniques. Each page is designed to be self-contained, so you can jump directly to what interests you or follow along sequentially.

## Core Concepts

Before diving into specific features, it's worth understanding what sets Pydoll apart. These foundational concepts inform how the entire library works.

**[Core Concepts](core-concepts.md)**: Discover the architectural decisions that make Pydoll different: the zero-webdriver approach that eliminates compatibility headaches, the async-first design that enables true concurrent operations, and native support for multiple Chromium-based browsers.

## Element Finding & Interaction

Finding and interacting with page elements is the bread and butter of automation. Pydoll makes this surprisingly intuitive with modern APIs that just make sense.

**[Element Finding](element-finding.md)**: Master Pydoll's element location strategies, from the intuitive `find()` method that uses natural HTML attributes, to the powerful `query()` method for CSS selectors and XPath. You'll also learn about DOM traversal helpers that let you navigate the page structure efficiently.

## Automation Capabilities

These are the features that bring your automation to life: simulating user interactions, keyboard control, handling file operations, working with iframes, and capturing visual content.

**[Human-Like Interactions](automation/human-interactions.md)**: Learn how to create interactions that feel genuinely human: typing with natural timing variations, clicking with realistic mouse movements, and using keyboard shortcuts just like a real user would. This is crucial for avoiding detection in automation-sensitive sites.

**[Keyboard Control](automation/keyboard-control.md)**: Master keyboard interactions with comprehensive support for key combinations, modifiers, and special keys. Essential for forms, shortcuts, and accessibility testing.

**[File Operations](automation/file-operations.md)**: File handling can be tricky in browser automation. Pydoll provides robust solutions for both uploads and downloads, with the `expect_download` context manager offering elegant handling of asynchronous download completion.

**[IFrame Interaction](automation/iframes.md)**: Treat iframes like regular elements—find the iframe and keep searching inside it. No extra targets, no extra tabs.

**[Screenshots & PDF](automation/screenshots-and-pdfs.md)**: Capture visual content from your automation sessions. Whether you need full-page screenshots for visual regression testing, element-specific captures for debugging, or PDF exports for archival, Pydoll has you covered.

## Network Features

Pydoll's network capabilities are where it truly shines, giving you unprecedented visibility and control over HTTP traffic.

**[Network Monitoring](network/monitoring.md)**: Observe and analyze all network activity in your browser session. Extract API responses, track request timing, identify failed requests, and understand exactly what data is being exchanged. Essential for debugging, testing, and data extraction.

**[Request Interception](network/interception.md)**: Go beyond observation to actively modify network behavior. Block unwanted resources, inject custom headers, modify request payloads, or even fulfill requests with mock data. This is powerful for testing, optimization, and privacy control.

**[Browser-Context HTTP Requests](network/http-requests.md)**: Make HTTP requests that execute within the browser's JavaScript context, automatically inheriting session state, cookies, and authentication. This hybrid approach combines the familiarity of Python's `requests` library with browser-context execution benefits.

## Browser Management

Effective browser and tab management is essential for complex automation scenarios, parallel processing, and multi-user testing.

**[Multi-Tab Management](browser-management/tabs.md)**: Work with multiple browser tabs simultaneously, ensuring efficient resource usage while giving you full control over tab lifecycle, detection of user-opened tabs, and concurrent scraping operations.

**[Browser Contexts](browser-management/contexts.md)**: Create completely isolated browsing environments within a single browser process. Each context maintains separate cookies, storage, cache, and permissions: perfect for multi-account testing, A/B testing, or parallel scraping with different configurations.


**[Cookies & Sessions](browser-management/cookies-sessions.md)**: Manage session state at both browser and tab levels. Set cookies programmatically, extract session data, and maintain different sessions across browser contexts for sophisticated testing scenarios.


## Configuration

Customize every aspect of browser behavior to match your automation needs, from low-level Chromium preferences to command-line arguments and page loading strategies.

**[Browser Options](configuration/browser-options.md)**: Configure Chromium's launch parameters, command-line arguments, and page load state control. Fine-tune browser behavior, enable experimental features, and optimize performance for your automation needs.

**[Browser Preferences](configuration/browser-preferences.md)**: Direct access to Chromium's internal preference system gives you control over hundreds of settings. Configure downloads, disable features, optimize performance, or create realistic browser fingerprints for stealth automation.

**[Proxy Configuration](configuration/proxy.md)**: Native proxy support with full authentication capabilities. Essential for web scraping projects requiring IP rotation, geo-targeted testing, or privacy-focused automation.


## Advanced Features

These sophisticated capabilities address complex automation challenges and specialized use cases.

**[Behavioral Captcha Bypass](advanced/behavioral-captcha-bypass.md)**: Pydoll's native behavioral captcha handling is one of its most requested features. Learn how to interact with Cloudflare Turnstile, reCAPTCHA v3, and hCaptcha invisible challenges using two approaches - synchronous context manager for guaranteed completion, and background processing for non-blocking operation.

**[Event System](advanced/event-system.md)**: Build reactive automation that responds to browser events in real-time. Monitor page loads, network activity, DOM changes, and JavaScript execution to create intelligent, adaptive automation scripts.

**[Remote Connections](advanced/remote-connections.md)**: Connect to already-running browsers via WebSocket for hybrid automation scenarios. Perfect for CI/CD pipelines, containerized environments, or integrating Pydoll into existing CDP tooling.


## How to Use This Guide

Each feature page follows a consistent structure:

1. **Overview** - What the feature does and why it matters
2. **Basic Usage** - Get started quickly with simple examples
3. **Advanced Patterns** - Leverage the feature's full potential
4. **Best Practices** - Tips for effective and efficient usage
5. **Common Pitfalls** - Learn from common mistakes

Feel free to explore features in any order based on your needs. Code examples are complete and ready to run - just copy, paste, and adapt to your use case.

Ready to dive deep into Pydoll's capabilities? Pick a feature that interests you and start exploring! 🚀

