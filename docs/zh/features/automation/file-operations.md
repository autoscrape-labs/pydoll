# 文件操作

文件上传是浏览器自动化中最具挑战性的方面之一。传统工具经常难以处理操作系统级别的文件对话框，需要复杂的解决方法或外部库。Pydoll 提供两种直接的文件上传方法，每种都适合不同的场景。

## 上传方法

Pydoll 支持两种主要的文件上传方法：

1. **直接文件输入**（`set_input_files()`）：快速直接，适用于 `<input type="file">` 元素
2. **文件选择器上下文管理器**（`expect_file_chooser()`）：拦截文件对话框，适用于任何上传触发器

## 直接文件输入

最简单的方法是直接在文件输入元素上使用 `set_input_files()`。这种方法快速、可靠，并完全绕过操作系统文件对话框。

### 基本用法

```python
import asyncio
from pathlib import Path
from pydoll.browser.chromium import Chrome

async def direct_file_upload():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/upload')
        
        # 查找文件输入元素
        file_input = await tab.find(tag_name='input', type='file')
        
        # 直接设置文件
        file_path = Path('path/to/document.pdf')
        await file_input.set_input_files(file_path)
        
        # 提交表单
        submit_button = await tab.find(id='submit-button')
        await submit_button.click()
        
        print("文件上传成功！")

asyncio.run(direct_file_upload())
```

!!! tip "Path 与字符串"
    虽然推荐使用 `pathlib` 中的 `Path` 对象作为最佳实践，以获得更好的路径处理和跨平台兼容性，但如果您喜欢，也可以使用纯字符串：
    ```python
    await file_input.set_input_files('path/to/document.pdf')  # 也可以！
    ```

### 多个文件

对于接受多个文件的输入（`<input type="file" multiple>`），传递文件路径列表：

```python
import asyncio
from pathlib import Path
from pydoll.browser.chromium import Chrome

async def upload_multiple_files():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/multi-upload')
        
        file_input = await tab.find(tag_name='input', type='file')
        
        # 一次上传多个文件
        files = [
            Path('documents/report.pdf'),
            Path('images/screenshot.png'),
            Path('data/results.csv')
        ]
        await file_input.set_input_files(files)
        
        # 正常处理
        upload_btn = await tab.find(id='upload-btn')
        await upload_btn.click()

asyncio.run(upload_multiple_files())
```

### 动态路径解析

`Path` 对象使动态构建路径和处理跨平台兼容性变得容易：

```python
import asyncio
from pathlib import Path
from pydoll.browser.chromium import Chrome

async def upload_with_dynamic_paths():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/upload')
        
        file_input = await tab.find(tag_name='input', type='file')
        
        # 动态构建路径
        project_dir = Path(__file__).parent
        file_path = project_dir / 'uploads' / 'data.json'

        await file_input.set_input_files(file_path)
        # 或使用主目录
        user_file = Path.home() / 'Documents' / 'report.pdf'
        await file_input.set_input_files(user_file)

asyncio.run(upload_with_dynamic_paths())
```

!!! tip "何时使用直接文件输入"
    在以下情况下使用 `set_input_files()`：
    
    - 文件输入在 DOM 中可直接访问
    - 您想要最大的速度和简单性
    - 上传不会触发文件选择器对话框
    - 您正在使用标准的 `<input type="file">` 元素

## 文件选择器上下文管理器

某些网站隐藏文件输入并使用自定义按钮或拖放区域来触发操作系统文件选择器对话框。对于这些情况，使用 `expect_file_chooser()` 上下文管理器。

### 工作原理

`expect_file_chooser()` 上下文管理器：

1. 启用文件选择器拦截
2. 等待文件选择器对话框打开
3. 在对话框出现时自动设置文件
4. 在操作完成后清理

### 基本用法

```python
import asyncio
from pathlib import Path
from pydoll.browser.chromium import Chrome

async def file_chooser_upload():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/custom-upload')
        
        # 准备文件路径
        file_path = Path.cwd() / 'document.pdf'
        
        # 使用上下文管理器处理文件选择器
        async with tab.expect_file_chooser(files=file_path):
            # 点击自定义上传按钮
            upload_button = await tab.find(class_name='custom-upload-btn')
            await upload_button.click()
            # 对话框打开时文件自动设置
        
        # 继续您的自动化
        print("通过选择器选择的文件！")

asyncio.run(file_chooser_upload())
```

### 使用文件选择器的多个文件

```python
import asyncio
from pathlib import Path
from pydoll.browser.chromium import Chrome

async def multiple_files_chooser():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/gallery-upload')
        
        # 准备多个文件
        photos_dir = Path.home() / 'photos'
        files = [
            photos_dir / 'img1.jpg',
            photos_dir / 'img2.jpg',
            photos_dir / 'img3.jpg'
        ]
        
        async with tab.expect_file_chooser(files=files):
            # 通过自定义按钮触发上传
            add_photos_btn = await tab.find(text='Add Photos')
            await add_photos_btn.click()
        
        print(f"已选择 {len(files)} 个文件！")

asyncio.run(multiple_files_chooser())
```

### 动态文件选择

```python
import asyncio
from pathlib import Path
from pydoll.browser.chromium import Chrome

async def dynamic_file_selection():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/batch-upload')
        
        # 使用 Path.glob() 查找目录中的所有 CSV 文件
        data_dir = Path('data')
        csv_files = list(data_dir.glob('*.csv'))
        
        async with tab.expect_file_chooser(files=csv_files):
            upload_area = await tab.find(class_name='drop-zone')
            await upload_area.click()
        
        print(f"已选择 {len(csv_files)} 个 CSV 文件")

asyncio.run(dynamic_file_selection())
```

!!! tip "何时使用文件选择器"
    在以下情况下使用 `expect_file_chooser()`：
    
    - 文件输入被隐藏或不可直接访问
    - 自定义按钮触发文件选择器对话框
    - 使用拖放上传区域
    - 站点使用 JavaScript 打开文件对话框

## 比较：直接与文件选择器

| 特性 | `set_input_files()` | `expect_file_chooser()` |
|---------|---------------------|-------------------------|
| **速度** | ⚡ 即时 | 🕐 等待对话框 |
| **复杂性** | 简单 | 需要上下文管理器 |
| **要求** | 可见的文件输入 | 任何上传触发器 |
| **用例** | 标准表单 | 自定义上传 UI |
| **事件处理** | 不需要 | 使用页面事件 |

## 完整示例

这是一个结合两种方法的综合示例：

```python
import asyncio
from pathlib import Path
from pydoll.browser.chromium import Chrome

async def comprehensive_upload_example():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/upload-form')
        
        # 场景 1：个人资料图片的直接输入（单个文件）
        avatar_input = await tab.find(id='avatar-upload')
        avatar_path = Path.home() / 'Pictures' / 'profile.jpg'
        await avatar_input.set_input_files(avatar_path)
        
        # 等待预览加载
        await asyncio.sleep(1)
        
        # 场景 2：文档上传的文件选择器
        document_path = Path.cwd() / 'documents' / 'resume.pdf'
        async with tab.expect_file_chooser(files=document_path):
            # 触发文件选择器的自定义样式按钮
            upload_btn = await tab.find(class_name='btn-upload-document')
            await upload_btn.click()
        
        # 等待上传确认
        await asyncio.sleep(2)
        
        # 场景 3：通过文件选择器的多个文件
        certs_dir = Path('certs')
        certificates = [
            certs_dir / 'certificate1.pdf',
            certs_dir / 'certificate2.pdf',
            certs_dir / 'certificate3.pdf'
        ]
        async with tab.expect_file_chooser(files=certificates):
            add_certs_btn = await tab.find(text='Add Certificates')
            await add_certs_btn.click()
        
        # 提交完整表单
        submit_button = await tab.find(type='submit')
        await submit_button.click()
        
        # 等待成功消息
        success_msg = await tab.find(class_name='success-message', timeout=10)
        message_text = await success_msg.text
        print(f"上传结果: {message_text}")

asyncio.run(comprehensive_upload_example())
```

!!! info "方法摘要"
    此示例演示了 Pydoll 文件上传系统的灵活性：
    
    - **单个文件**：直接传递 `Path` 或 `str`（不需要列表）
    - **多个文件**：传递 `Path` 或 `str` 对象的列表
    - **直接输入**：对可见的 `<input>` 元素快速
    - **文件选择器**：适用于自定义上传按钮和隐藏输入

## 了解更多

要更深入地了解文件上传机制：

- **[事件系统](../advanced/event-system.md)**：了解 `expect_file_chooser()` 使用的页面事件
- **[深入探讨：Tab 域](../../deep-dive/tab-domain.md#file-chooser-handling)**：文件选择器拦截的技术细节
- **[深入探讨：事件系统](../../deep-dive/event-system.md#file-chooser-events)**：文件选择器事件如何在底层工作

Pydoll 中的文件操作消除了浏览器自动化中最大的痛点之一，为简单和复杂的上传场景提供了干净、可靠的方法。