"""Dialog, ConsoleMessage, FileChooser and Download objects surfaced by page events."""

from __future__ import annotations

import asyncio
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Any, Sequence

from pydoll.commands import PageCommands
from pydoll.playwright._element_handle import ElementHandle, JSHandle
from pydoll.playwright._errors import Error
from pydoll.playwright._remote_values import parse_remote_value

if TYPE_CHECKING:
    from pydoll.playwright._page import Page


class Dialog:
    """A JavaScript ``alert``, ``confirm``, ``prompt`` or ``beforeunload`` dialog."""

    def __init__(self, page: Page, params: dict[str, Any]) -> None:
        self._page = page
        self._type: str = params.get('type', 'alert')
        self._message: str = params.get('message', '')
        self._default_value: str = params.get('defaultPrompt', '')
        self._handled = False

    @property
    def type(self) -> str:
        return self._type

    @property
    def message(self) -> str:
        return self._message

    @property
    def default_value(self) -> str:
        return self._default_value

    @property
    def page(self) -> Page | None:
        return self._page

    async def accept(self, prompt_text: str | None = None) -> None:
        await self._handle(True, prompt_text)

    async def dismiss(self) -> None:
        await self._handle(False, None)

    async def _handle(self, accept: bool, prompt_text: str | None) -> None:
        if self._handled:
            raise Error('Cannot accept dialog which is already handled!')
        self._handled = True
        await self._page._send(
            PageCommands.handle_javascript_dialog(accept=accept, prompt_text=prompt_text)
        )


class ConsoleMessage:
    """A ``console.*`` call made by the page."""

    def __init__(self, page: Page, params: dict[str, Any]) -> None:
        self._page = page
        self._type: str = params.get('type', 'log')
        self._args = [
            page.main_frame._handle_from_remote_object(arg)
            if arg.get('objectId')
            else _PrimitiveHandle(arg)
            for arg in params.get('args', [])
        ]
        self._text = ' '.join(_describe(arg) for arg in params.get('args', []))
        frames = params.get('stackTrace', {}).get('callFrames', [])
        top = frames[0] if frames else {}
        self._location = {
            'url': top.get('url', ''),
            'lineNumber': top.get('lineNumber', 0),
            'columnNumber': top.get('columnNumber', 0),
        }
        self._timestamp = params.get('timestamp')

    @property
    def type(self) -> str:
        return self._type

    @property
    def text(self) -> str:
        return self._text

    @property
    def args(self) -> list[Any]:
        return list(self._args)

    @property
    def location(self) -> dict[str, Any]:
        return dict(self._location)

    @property
    def page(self) -> Page | None:
        return self._page

    @property
    def timestamp(self) -> Any:
        return self._timestamp

    def __str__(self) -> str:
        return self._text


class _PrimitiveHandle:
    """Stand-in for console arguments that were passed by value."""

    def __init__(self, remote: dict[str, Any]) -> None:
        self._remote = remote

    async def json_value(self) -> Any:
        return parse_remote_value(self._remote)

    async def dispose(self) -> None:
        return None

    def as_element(self) -> None:
        return None


def _describe(remote: dict[str, Any]) -> str:
    if 'value' in remote:
        value = remote['value']
        return value if isinstance(value, str) else str(value)
    if remote.get('unserializableValue'):
        return str(remote['unserializableValue'])
    if remote.get('type') == 'undefined':
        return 'undefined'
    return remote.get('description') or remote.get('className') or remote.get('type', '')


class FileChooser:
    """A file input that opened its picker; call ``set_files`` to answer it."""

    def __init__(self, page: Page, element: ElementHandle, is_multiple: bool) -> None:
        self._page = page
        self._element = element
        self._is_multiple = is_multiple

    @property
    def page(self) -> Page:
        return self._page

    @property
    def element(self) -> ElementHandle:
        return self._element

    def is_multiple(self) -> bool:
        return self._is_multiple

    async def set_files(
        self,
        files: str | Path | Sequence[str | Path] | Any,
        timeout: float | None = None,
    ) -> None:
        await self._element.set_input_files(files, timeout=timeout)


class Download:
    """A download that started in the page; the file lands in the context's download directory."""

    def __init__(self, page: Page, params: dict[str, Any], directory: Path) -> None:
        self._page = page
        self._guid: str = params['guid']
        self._url: str = params.get('url', '')
        self._suggested_filename: str = params.get('suggestedFilename', '')
        self._directory = directory
        self._done: asyncio.Future[str | None] = page._loop.create_future()
        self._cancelled = False

    @property
    def page(self) -> Page:
        return self._page

    @property
    def url(self) -> str:
        return self._url

    @property
    def suggested_filename(self) -> str:
        return self._suggested_filename

    def _on_progress(self, params: dict[str, Any]) -> None:
        state = params.get('state')
        if self._done.done():
            return
        if state == 'completed':
            self._done.set_result(None)
        elif state == 'canceled':
            self._done.set_result('canceled')

    async def failure(self) -> str | None:
        return await self._done

    async def path(self) -> Path:
        error = await self._done
        if error:
            raise Error(f'Download failed: {error}')
        return self._directory / self._guid

    async def save_as(self, path: str | Path) -> None:
        source = await self.path()
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)

    async def delete(self) -> None:
        error = await self._done
        if error:
            return
        target = self._directory / self._guid
        if target.exists():
            target.unlink()

    async def cancel(self) -> None:
        if self._done.done():
            return
        await self._page.context._browser._chrome.execute_command({
            'method': 'Browser.cancelDownload',
            'params': {'guid': self._guid},
        })
        self._cancelled = True


__all__ = ['ConsoleMessage', 'Dialog', 'Download', 'FileChooser', 'JSHandle']
