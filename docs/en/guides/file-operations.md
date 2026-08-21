# File operations

Uploading and downloading files means dealing with OS-level dialogs that most automation tools can't reach. Pydoll handles both for you: it sets the files a chooser asks for, and it captures a download without you polling the filesystem for it to finish.

## Upload to a file input

When the page has a real `<input type="file">`, find it and call `set_input_files()`. This sets the files directly, without opening the OS dialog.

```python
import asyncio
from pathlib import Path

from pydoll.browser.chromium import Chrome


async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://the-internet.herokuapp.com/upload')

        file_input = await tab.find(id='file-upload')
        await file_input.set_input_files(Path('report.pdf'))

        submit = await tab.find(id='file-submit')
        await submit.click()

        result = await tab.find(tag_name='h3')
        print(await result.text)   # "File Uploaded!"

asyncio.run(main())
```

`set_input_files()` accepts a `str`, a `pathlib.Path`, or a list of them. A `Path` is the more portable choice, but a plain string works too:

```python
await file_input.set_input_files('report.pdf')
await file_input.set_input_files(Path.home() / 'Documents' / 'report.pdf')
```

### Upload several files at once

For an input marked `multiple`, pass a list. You can build that list however you like, including with `Path.glob()`:

```python
await file_input.set_input_files([
    Path('report.pdf'),
    Path('cover.png'),
])

# every CSV in a folder
csv_files = list(Path('data').glob('*.csv'))
await file_input.set_input_files(csv_files)
```

## Upload through a file chooser dialog

Many sites hide the file input behind a styled button or a drag-and-drop zone, so clicking it opens the OS file chooser. `set_input_files()` has nothing to target there. Wrap the click in `expect_file_chooser()` instead: it intercepts the dialog and sets your files when it opens.

```python
import asyncio
from pathlib import Path

from pydoll.browser.chromium import Chrome


async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example-uploads.test/gallery')

        async with tab.expect_file_chooser(files=Path('cover.png')):
            upload_button = await tab.find(class_name='upload-button')
            await upload_button.click()

        print('File selected through the chooser.')

asyncio.run(main())
```

The click that opens the dialog goes **inside** the `async with` block. When the chooser opens, Pydoll fills it with your files; you never see the native dialog. `files` takes the same `str`, `Path`, or list that `set_input_files()` accepts.

!!! tip "Which upload method?"
    Reach for `set_input_files()` when a real `<input type="file">` is in the DOM; it is instant and needs no dialog. Use `expect_file_chooser()` when the input is hidden and a custom control opens the OS chooser.

## Download a file

Wrap the action that starts a download in `expect_download()`. Pydoll waits for the download to complete and hands you a handle to read it, so you don't poll a directory waiting for the file to appear.

```python
import asyncio

from pydoll.browser.chromium import Chrome


async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://the-internet.herokuapp.com/download')

        async with tab.expect_download() as download:
            link = await tab.query('.example a')
            await link.click()
            data = await download.read_bytes()

        print(f'Downloaded {len(data)} bytes')

asyncio.run(main())
```

Read the file **inside** the block. By default the download lands in a temporary directory that is cleaned up when the block exits, so `read_bytes()` (or `read_base64()`) is how you capture the contents. The trigger, here a link click, also goes inside the block.

### Keep the file on disk

Pass `keep_file_at` with a directory to persist the download instead of using a throwaway temp dir. The file remains after the block ends, and `download.file_path` tells you where it landed:

```python
async with tab.expect_download(keep_file_at='downloads/') as download:
    link = await tab.query('.example a')
    await link.click()
    await download.wait_finished()

print(f'Saved to {download.file_path}')
```

`expect_download()` waits up to 60 seconds by default; pass `timeout` in seconds to change that. The handle also offers `read_base64()` when you need the contents as a base64 string.

## What's next

- [Events](events.md): the page events that `expect_file_chooser()` and `expect_download()` build on.
- [Screenshots and PDFs](screenshots-and-pdfs.md): save a page as a PDF instead of downloading one.
- [Element finding](element-finding.md): locate the inputs and links these operations act on.
