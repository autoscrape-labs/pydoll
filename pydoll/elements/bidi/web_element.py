from __future__ import annotations

import asyncio
import base64 as _b64
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Union

import aiofiles

from pydoll.commands.bidi.browsing_context_commands import BrowsingContextCommands
from pydoll.commands.bidi.script_commands import ScriptCommands
from pydoll.connection.bidi_connection_handler import BiDiConnectionHandler
from pydoll.constants import By
from pydoll.elements.mixins.bidi_find_elements_mixin import BidiFindElementsMixin
from pydoll.exceptions import (
    ElementNotInteractable,
    ElementNotVisible,
    MissingScreenshotPath,
    WaitElementTimeout,
)
from pydoll.protocol.bidi.base import Command, T_CommandParams, T_CommandResult
from pydoll.protocol.bidi.browsing_context.types import (
    BoxClipRectangle,
    ElementClipRectangle,
)
from pydoll.protocol.bidi.script.types import (
    ContextTarget,
    RemoteValue,
    SharedReference,
)

if TYPE_CHECKING:
    from pydoll.protocol.bidi.script.types import NodeProperties

logger = logging.getLogger(__name__)


class BiDiWebElement(BidiFindElementsMixin):
    """DOM element wrapper for Firefox automation via BiDi protocol.

    Elements are referenced by sharedId, which is cross-realm and
    persistent across navigations within the same document.
    """

    def __init__(
        self,
        shared_id: str,
        context_id: str,
        connection: BiDiConnectionHandler,
        attributes: dict[str, str],
        tag_name: str,
        method: Optional[By] = None,
        selector: Optional[str] = None,
    ):
        self._shared_id = shared_id
        self._context_id = context_id
        self._connection_handler = connection
        self._attributes = dict(attributes)
        self._attributes['tag_name'] = tag_name
        self._search_method = method
        self._selector = selector

    @property
    def attributes(self) -> dict[str, str]:
        """Read-only copy of the element's cached attributes."""
        return dict(self._attributes)

    @property
    def value(self) -> Optional[str]:
        """Element's value attribute (for form elements)."""
        return self._attributes.get('value')

    @property
    def class_name(self) -> Optional[str]:
        """Element's CSS class name(s)."""
        return self._attributes.get('class')

    @property
    def id(self) -> Optional[str]:
        """Element's ID attribute."""
        return self._attributes.get('id')

    @property
    def tag_name(self) -> Optional[str]:
        """Element's HTML tag name."""
        return self._attributes.get('tag_name')

    @property
    def is_iframe(self) -> bool:
        """Whether the element represents an iframe."""
        return self.tag_name in {'iframe', 'frame'}

    @property
    def is_enabled(self) -> bool:
        """Whether element is enabled (not disabled)."""
        return 'disabled' not in self._attributes

    @property
    async def text(self) -> str:
        """Visible text content of the element."""
        return await self._call_on_element('(el) => el.textContent || ""') or ''

    @property
    async def inner_html(self) -> str:
        """HTML content of the element."""
        return await self._call_on_element('(el) => el.outerHTML') or ''

    @property
    async def bounds(self) -> dict:
        """Element's bounding box coordinates."""
        return await self.get_bounds_using_js()

    def get_attribute(self, name: str) -> Optional[str]:
        """Get element attribute value from cache."""
        if name == 'class' and 'class' in self._attributes:
            return self._attributes.get('class')
        return self._attributes.get(name)

    async def get_bounds_using_js(self) -> dict[str, int]:
        """Get element bounding box via JavaScript."""
        return await self._call_on_element(
            '(el) => { const r = el.getBoundingClientRect();'
            ' return {x: r.x, y: r.y, width: r.width, height: r.height} }'
        ) or {}

    async def get_parent_element(self) -> BiDiWebElement:
        """Get parent element."""
        response = await self._execute_command(
            ScriptCommands.call_function(
                function_declaration='(el) => el.parentElement',
                await_promise=False,
                target=ContextTarget(context=self._context_id),
                arguments=[{'type': 'node', 'sharedId': self._shared_id}],
            )
        )
        result = response['result']
        remote = result.get('result', {})
        if remote.get('sharedId'):
            from pydoll.elements.mixins.bidi_find_elements_mixin import (
                create_bidi_web_element,
            )
            node_props = remote.get('value', {})
            return create_bidi_web_element(
                shared_id=remote['sharedId'],
                context_id=self._context_id,
                connection=self._connection_handler,
                attributes=node_props.get('attributes', {}),
                tag_name=node_props.get('localName', ''),
            )
        raise ElementNotFound('Parent element not found')

    async def take_screenshot(
        self,
        path: Optional[Union[str, Path]] = None,
        quality: int = 100,
        as_base64: bool = False,
    ) -> Optional[str]:
        """Capture screenshot of this element."""
        if not path and not as_base64:
            raise MissingScreenshotPath()

        clip = ElementClipRectangle(
            type='element',
            element=SharedReference(sharedId=self._shared_id),
        )

        response = await self._execute_command(
            BrowsingContextCommands.capture_screenshot(
                context=self._context_id,
                clip=clip,
            )
        )
        data = response['result']['data']

        if as_base64:
            return data

        if path:
            async with aiofiles.open(str(path), 'wb') as f:
                await f.write(_b64.b64decode(data))

        return None

    async def scroll_into_view(self):
        """Scroll element into visible viewport."""
        await self._call_on_element(
            '(el) => el.scrollIntoView({block: "center", inline: "center"})'
        )

    async def wait_until(
        self,
        *,
        is_visible: bool = False,
        is_interactable: bool = False,
        timeout: int = 0,
    ):
        """Wait for element to meet specified conditions."""
        checks = []
        if is_visible:
            checks.append(self.is_visible)
        if is_interactable:
            checks.append(self.is_interactable)
        if not checks:
            raise ValueError(
                'At least one of is_visible or is_interactable must be True'
            )

        start_time = asyncio.get_event_loop().time()
        while True:
            results = await asyncio.gather(*(check() for check in checks))
            if all(results):
                return
            if timeout and asyncio.get_event_loop().time() - start_time > timeout:
                raise WaitElementTimeout('Condition not met within timeout')
            await asyncio.sleep(0.5)

    async def click_using_js(self):
        """Click element using JavaScript."""
        if not await self.is_visible():
            raise ElementNotVisible()
        result = await self._call_on_element(
            '(el) => { el.click(); return true }'
        )
        if not result:
            raise ElementNotInteractable()

    async def click(
        self,
        x_offset: int = 0,
        y_offset: int = 0,
        hold_time: float = 0.1,
        humanize: bool = False,
    ):
        """Click element using JavaScript click."""
        await self.scroll_into_view()
        if not await self.is_visible():
            raise ElementNotVisible()
        await self._call_on_element('(el) => el.click()')

    async def focus(self):
        """Focus this element."""
        await self._call_on_element('(el) => el.focus()')

    async def clear(self):
        """Clear the current value of the element."""
        result = await self._call_on_element(
            '(el) => {'
            '  if (el.tagName === "INPUT" || el.tagName === "TEXTAREA") {'
            '    el.value = "";'
            '    el.dispatchEvent(new Event("input", {bubbles: true}));'
            '    el.dispatchEvent(new Event("change", {bubbles: true}));'
            '    return true;'
            '  } else if (el.isContentEditable) {'
            '    el.textContent = "";'
            '    return true;'
            '  }'
            '  return false;'
            '}'
        )
        if not result:
            raise ElementNotInteractable('Element does not accept text input')

    async def insert_text(self, text: str):
        """Insert text into the element."""
        await self._call_on_element(
            '(el, text) => {'
            '  el.focus();'
            '  if (el.tagName === "INPUT" || el.tagName === "TEXTAREA") {'
            '    el.value = text;'
            '  } else if (el.isContentEditable) {'
            '    el.textContent = text;'
            '  }'
            '  el.dispatchEvent(new Event("input", {bubbles: true}));'
            '  el.dispatchEvent(new Event("change", {bubbles: true}));'
            '}',
            {'type': 'string', 'value': text},
        )

    async def set_input_files(self, files: Union[str, Path, list[Union[str, Path]]]):
        """Set files on a file input element."""
        from pydoll.commands.bidi.input_commands import InputCommands

        if isinstance(files, (str, Path)):
            files = [files]
        file_paths = [str(f) for f in files]
        await self._execute_command(
            InputCommands.set_files(
                context=self._context_id,
                element=SharedReference(sharedId=self._shared_id),
                files=file_paths,
            )
        )

    async def type_text(
        self,
        text: str,
        humanize: bool = False,
        interval: float = 0.1,
    ):
        """Type text character by character."""
        await self.focus()
        for char in text:
            await self._call_on_element(
                '(el, c) => {'
                '  el.value = (el.value || "") + c;'
                '  el.dispatchEvent(new Event("input", {bubbles: true}));'
                '}',
                {'type': 'string', 'value': char},
            )
            if humanize:
                await asyncio.sleep(interval)

    async def is_editable(self) -> bool:
        """Check if element accepts text input."""
        return bool(await self._call_on_element(
            '(el) => !el.disabled && !el.readOnly && '
            '(el.tagName === "INPUT" || el.tagName === "TEXTAREA" || el.isContentEditable)'
        ))

    async def is_visible(self) -> bool:
        """Check if element is visible."""
        return bool(await self._call_on_element(
            '(el) => {'
            '  const s = getComputedStyle(el);'
            '  return s.display !== "none" && s.visibility !== "hidden" '
            '    && s.opacity !== "0" && el.offsetWidth > 0 && el.offsetHeight > 0'
            '}'
        ))

    async def is_on_top(self) -> bool:
        """Check if element is on top (not covered)."""
        return bool(await self._call_on_element(
            '(el) => {'
            '  const r = el.getBoundingClientRect();'
            '  const top = document.elementFromPoint(r.x + r.width/2, r.y + r.height/2);'
            '  return el === top || el.contains(top)'
            '}'
        ))

    async def is_interactable(self) -> bool:
        """Check if element is interactable."""
        visible = await self.is_visible()
        on_top = await self.is_on_top()
        return visible and on_top

    async def execute_script(self, script: str, **kwargs) -> RemoteValue:
        """Execute JavaScript with this element as first argument."""
        response = await self._execute_command(
            ScriptCommands.call_function(
                function_declaration=script,
                await_promise=kwargs.get('await_promise', False),
                target=ContextTarget(context=self._context_id),
                arguments=[{'type': 'node', 'sharedId': self._shared_id}],
            )
        )
        result = response['result']
        if result.get('type') == 'exception':
            raise RuntimeError(result['exceptionDetails']['text'])
        return result.get('result', {})

    async def _call_on_element(
        self, function_declaration: str, *extra_args: dict
    ) -> RemoteValue:
        """Call a JavaScript function with this element as first argument."""
        arguments: list[dict] = [
            {'type': 'node', 'sharedId': self._shared_id},
            *extra_args,
        ]
        response = await self._execute_command(
            ScriptCommands.call_function(
                function_declaration=function_declaration,
                await_promise=False,
                target=ContextTarget(context=self._context_id),
                arguments=arguments,
            )
        )
        from pydoll.browser.firefox.tab import BiDiTab

        result = response['result']
        if result.get('type') == 'exception':
            raise RuntimeError(result['exceptionDetails']['text'])
        remote_value = result.get('result', {})
        return BiDiTab._deserialize_remote_value(remote_value)
