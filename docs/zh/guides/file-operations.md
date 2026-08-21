# 文件操作

上传和下载文件意味着要应付操作系统层面的对话框，而大多数自动化工具都够不着这些。Pydoll 替你搞定两者：它设置选择器索要的文件，并捕获下载，你不用轮询文件系统去等它完成。

## 上传到文件输入框

当页面有一个真正的 `<input type="file">` 时，找到它并调用 `set_input_files()`。这会直接设置文件，不打开操作系统对话框。

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

`set_input_files()` 接受一个 `str`、一个 `pathlib.Path`，或它们组成的列表。`Path` 是更具可移植性的选择，但一个普通字符串也行：

```python
await file_input.set_input_files('report.pdf')
await file_input.set_input_files(Path.home() / 'Documents' / 'report.pdf')
```

### 一次上传多个文件

对于标记了 `multiple` 的输入框，传入一个列表。你可以任意方式构建这个列表，包括用 `Path.glob()`：

```python
await file_input.set_input_files([
    Path('report.pdf'),
    Path('cover.png'),
])

# 一个文件夹里的每一个 CSV
csv_files = list(Path('data').glob('*.csv'))
await file_input.set_input_files(csv_files)
```

## 通过文件选择对话框上传

许多站点把文件输入框藏在一个带样式的按钮或一个拖放区域后面，于是点击它会打开操作系统的文件选择器。在那种情况下 `set_input_files()` 没有可作用的目标。改为把点击包裹在 `expect_file_chooser()` 里：它会拦截对话框，并在其打开时设置你的文件。

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

打开对话框的那次点击要放在 `async with` 块**里面**。当选择器打开时，Pydoll 用你的文件把它填上；你从头到尾都看不到原生对话框。`files` 接受 `set_input_files()` 所接受的同样的 `str`、`Path` 或列表。

!!! tip "该用哪种上传方法？"
    当一个真正的 `<input type="file">` 就在 DOM 里时，选用 `set_input_files()`；它是瞬时的、不需要对话框。当输入框被隐藏、由一个自定义控件打开操作系统选择器时，使用 `expect_file_chooser()`。

## 下载文件

把启动下载的动作包裹在 `expect_download()` 里。Pydoll 会等待下载完成，并把一个句柄交给你去读取它，因此你不用轮询某个目录、等文件出现。

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

在块**里面**读取文件。默认情况下，下载会落到一个临时目录，块退出时该目录会被清理，所以 `read_bytes()`（或 `read_base64()`）就是你捕获内容的方式。触发动作，这里是一次链接点击，也要放在块里面。

### 把文件保留在磁盘上

传入 `keep_file_at` 并给一个目录，以持久化下载，而不使用一次性的临时目录。文件在块结束后仍然保留，`download.file_path` 会告诉你它落在哪里：

```python
async with tab.expect_download(keep_file_at='downloads/') as download:
    link = await tab.query('.example a')
    await link.click()
    await download.wait_finished()

print(f'Saved to {download.file_path}')
```

`expect_download()` 默认最多等待 60 秒；传入以秒为单位的 `timeout` 来改变它。当你需要把内容作为 base64 字符串获取时，句柄还提供了 `read_base64()`。

## 下一步

- [事件](events.md)：`expect_file_chooser()` 和 `expect_download()` 所依托的页面事件。
- [截图和 PDF](screenshots-and-pdfs.md)：把页面保存为 PDF，而不是下载一个。
- [查找元素](element-finding.md)：定位这些操作所作用的输入框和链接。
