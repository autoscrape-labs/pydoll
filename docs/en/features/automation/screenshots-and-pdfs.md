# Screenshots and PDFs

Pydoll provides powerful screenshot and PDF generation capabilities through direct Chrome DevTools Protocol commands. Capture full pages, specific elements, or generate PDFs with fine-grained control.

## Screenshots

### Basic Page Screenshot

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def take_page_screenshot():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com')
        
        # Save screenshot to file
        await tab.take_screenshot('page.png', quality=100)

asyncio.run(take_page_screenshot())
```

### Supported Formats

Pydoll supports three image formats based on file extension:

```python
# PNG format (lossless, larger file size)
await tab.take_screenshot('screenshot.png', quality=100)

# JPEG format (lossy, smaller file size)
await tab.take_screenshot('screenshot.jpeg', quality=85)

# WebP format (modern, efficient)
await tab.take_screenshot('screenshot.webp', quality=90)
```

!!! info "Format Detection"
    The image format is automatically determined by the file extension. Using an unsupported extension raises `InvalidFileExtension`.
    
    Both `.jpg` and `.jpeg` are supported for JPEG format (`.jpg` is automatically normalized to `.jpeg` internally to match CDP requirements).

### Screenshot Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `path` | `Optional[str]` | `None` | File path to save screenshot. Required if `as_base64=False`. |
| `quality` | `int` | `100` | Image quality (0-100). Higher values mean better quality and larger files. |
| `beyond_viewport` | `bool` | `False` | Capture entire scrollable page, not just visible area. |
| `as_base64` | `bool` | `False` | Return base64-encoded string instead of saving to file. |

### Full Page Screenshot

Capture content beyond the visible viewport:

```python
async def full_page_screenshot():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/long-page')
        
        # Capture entire page including content below the fold
        await tab.take_screenshot(
            'full-page.png',
            beyond_viewport=True,
            quality=90
        )
```

!!! warning "Performance Note"
    Using `beyond_viewport=True` on very long pages can consume significant memory and take longer to process.

### Base64 Screenshot

Get screenshot as base64 string for embedding or sending via API:

```python
async def base64_screenshot():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com')
        
        # Get screenshot as base64 string
        screenshot_base64 = await tab.take_screenshot(
            as_base64=True
        )
        
        # Use in HTML img tag
        html = f'<img src="data:image/png;base64,{screenshot_base64}" />'
        
        # Or send via API
        import aiohttp
        async with aiohttp.ClientSession() as session:
            await session.post(
                'https://api.example.com/upload',
                json={'image': screenshot_base64}
            )
```

### Element Screenshot

Capture specific elements instead of the entire page:

```python
async def element_screenshot():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com')
        
        # Screenshot a specific element (PNG)
        header = await tab.find(tag_name='header')
        await header.take_screenshot('header.png', quality=100)
        
        # Screenshot a form (JPEG)
        form = await tab.find(id='login-form')
        await form.take_screenshot('login-form.jpeg', quality=85)
        
        # Screenshot a chart or graph (WebP)
        chart = await tab.find(class_name='data-visualization')
        await chart.take_screenshot('chart.webp', quality=90)
```

!!! info "Format Detection"
    The image format is automatically detected from the file extension (`.png`, `.jpeg`/`.jpg`, or `.webp`). Using an unsupported extension raises `InvalidFileExtension`.

!!! tip "Automatic Scrolling"
    When capturing element screenshots, Pydoll automatically scrolls the element into view before taking the screenshot.

### Element vs Page Screenshots

| Feature | `tab.take_screenshot()` | `element.take_screenshot()` |
|---------|------------------------|----------------------------|
| **Scope** | Entire viewport or page | Specific element only |
| **Format Support** | PNG, JPEG, WebP | PNG, JPEG, WebP |
| **Beyond Viewport** | ✅ Supported | ❌ Not applicable |
| **Base64 Output** | ✅ Supported | ✅ Supported |
| **Auto-Scroll** | ❌ Not applicable | ✅ Yes |
| **Use Case** | Full page captures | Component isolation, testing |


## PDF Generation

### Basic PDF Export

Convert pages to PDF with print-quality output:

```python
import asyncio
from pathlib import Path
from pydoll.browser.chromium import Chrome

async def generate_pdf():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/document')
        
        # Generate PDF with Path
        await tab.print_to_pdf(Path('document.pdf'))
        
        # Or with string
        await tab.print_to_pdf('document.pdf')

asyncio.run(generate_pdf())
```

### PDF Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `path` | `Optional[str \| Path]` | `None` | File path to save PDF. Required if `as_base64=False`. |
| `landscape` | `bool` | `False` | Use landscape orientation (vs portrait). |
| `display_header_footer` | `bool` | `False` | Include browser-generated header/footer with title, URL, page numbers. |
| `print_background` | `bool` | `True` | Include background graphics and colors. |
| `scale` | `float` | `1.0` | Page scale factor (0.1-2.0). Useful for zoom/shrink effects. |
| `as_base64` | `bool` | `False` | Return base64-encoded string instead of saving to file. |

!!! tip "Path vs String"
    While `Path` objects from `pathlib` are recommended as best practice for better path handling and cross-platform compatibility, you can also use plain strings if preferred.

### Advanced PDF Options

```python
import asyncio
from pathlib import Path
from pydoll.browser.chromium import Chrome

async def advanced_pdf():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/report')
        
        # Landscape PDF with headers/footers
        await tab.print_to_pdf(
            Path('report-landscape.pdf'),
            landscape=True,
            display_header_footer=True,
            print_background=True,
            scale=0.9
        )
        
        # Portrait PDF without backgrounds (ink-friendly)
        await tab.print_to_pdf(
            Path('report-ink-friendly.pdf'),
            landscape=False,
            print_background=False,
            scale=1.0
        )

asyncio.run(advanced_pdf())
```

### PDF Scale Factor

Control the zoom level of PDF output:

```python
import asyncio
from pathlib import Path
from pydoll.browser.chromium import Chrome

async def scaled_pdfs():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/content')
        
        # Shrink content to fit more on each page
        await tab.print_to_pdf(Path('compact.pdf'), scale=0.7)
        
        # Normal scale
        await tab.print_to_pdf(Path('normal.pdf'), scale=1.0)
        
        # Enlarge content (fewer pages)
        await tab.print_to_pdf(Path('large.pdf'), scale=1.5)

asyncio.run(scaled_pdfs())
```

!!! warning "Scale Limits"
    The `scale` parameter accepts values between `0.1` and `2.0`. Values outside this range may produce unexpected results.

### Base64 PDF

Generate PDF as base64 string for API transmission:

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def base64_pdf():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/invoice')
        
        # Get PDF as base64 (no path needed)
        pdf_base64 = await tab.print_to_pdf(as_base64=True)
        
        # Send via API
        import aiohttp
        async with aiohttp.ClientSession() as session:
            await session.post(
                'https://api.example.com/invoices',
                json={'pdf': pdf_base64}
            )

asyncio.run(base64_pdf())
```


!!! info "CDP Reference"
    For complete CDP documentation on these commands, see:
    
    - [Page.captureScreenshot](https://chromedevtools.github.io/devtools-protocol/tot/Page/#method-captureScreenshot)
    - [Page.printToPDF](https://chromedevtools.github.io/devtools-protocol/tot/Page/#method-printToPDF)

### Error Handling

```python
from pydoll.exceptions import (
    InvalidFileExtension,
    MissingScreenshotPath,
    TopLevelTargetRequired
)

async def safe_screenshot():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com')
        
        try:
            # Missing path and as_base64=False
            await tab.take_screenshot()
        except MissingScreenshotPath:
            print("Error: Must provide path or set as_base64=True")
        
        try:
            # Invalid extension
            await tab.take_screenshot('image.bmp')
        except InvalidFileExtension as e:
            print(f"Error: {e}")
        
        # IFrame screenshot limitation
        iframe_element = await tab.find(tag_name='iframe')

        # This still won't work: top-level screenshots ignore iframe content
        # await tab.take_screenshot('frame.png')

        # Screenshot an element inside the iframe WebElement
        content = await iframe_element.find(id='content')
        await content.take_screenshot('iframe-content.png')
```

## Page Bundle Export

Save an entire page with all its assets (CSS, JS, images, fonts) as a `.zip` archive for offline viewing.

### Basic Usage

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def save_page():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com')

        # Save page with assets as separate files
        await tab.save_bundle('page.zip')

asyncio.run(save_page())
```

The resulting zip contains an `index.html` with all URLs rewritten to reference local files under an `assets/` directory.

### Inline Mode

Embed everything directly into a single `index.html` using data URIs, `<style>`, and `<script>` tags:

```python
# Single self-contained HTML file inside the zip
await tab.save_bundle('page-inline.zip', inline_assets=True)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `path` | `str \| Path` | *(required)* | Destination path. Must end with `.zip`. |
| `inline_assets` | `bool` | `False` | Embed all assets inline instead of saving as separate files. |

!!! info "What Gets Bundled"
    The bundle includes resources of type: Document, Stylesheet, Script, Image, Font, and Media. Resources that failed to load, were canceled, or use `data:` URIs are automatically skipped.

## Learn More

For additional context on how screenshots and PDFs integrate with Pydoll's architecture:

- **[Deep Dive: CDP](../../deep-dive/cdp.md)**: Understanding Chrome DevTools Protocol commands
- **[API Reference: Tab](../../api/browser/tab.md#take_screenshot)**: Complete method signatures and parameters
- **[API Reference: WebElement](../../api/elements/web-element.md#take_screenshot)**: Element-specific screenshot capabilities

Screenshots and PDFs are essential tools for automation, testing, and documentation. Pydoll's direct CDP integration provides professional-grade output with fine-grained control.

