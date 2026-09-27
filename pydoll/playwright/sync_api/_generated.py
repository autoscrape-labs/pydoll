"""Synchronous Playwright-compatible API (generated, do not edit).

Regenerate with ``python scripts/generate_sync_api.py``.
"""

# ruff: noqa
# fmt: off
from __future__ import annotations

from contextlib import AbstractContextManager
from typing import Any, Generic, cast, overload

from pydoll.sync._runtime import SyncBase, mapping, run_sync

from pydoll.playwright._playwright import Playwright as _PlaywrightImpl
from pydoll.playwright._playwright import BrowserType as _BrowserTypeImpl
from pydoll.playwright._playwright import Selectors as _SelectorsImpl
from pydoll.playwright._playwright import PlaywrightContextManager as _PlaywrightContextManagerImpl
from pydoll.playwright._browser import Browser as _BrowserImpl
from pydoll.playwright._browser_context import BrowserContext as _BrowserContextImpl
from pydoll.playwright._page import Page as _PageImpl
from pydoll.playwright._frame import Frame as _FrameImpl
from pydoll.playwright._locator import Locator as _LocatorImpl
from pydoll.playwright._locator import FrameLocator as _FrameLocatorImpl
from pydoll.playwright._element_handle import JSHandle as _JSHandleImpl
from pydoll.playwright._element_handle import ElementHandle as _ElementHandleImpl
from pydoll.playwright._input import Keyboard as _KeyboardImpl
from pydoll.playwright._input import Mouse as _MouseImpl
from pydoll.playwright._input import Touchscreen as _TouchscreenImpl
from pydoll.playwright._network import Request as _RequestImpl
from pydoll.playwright._network import Response as _ResponseImpl
from pydoll.playwright._network import Route as _RouteImpl
from pydoll.playwright._network import APIResponse as _APIResponseImpl
from pydoll.playwright._dialog import Dialog as _DialogImpl
from pydoll.playwright._dialog import ConsoleMessage as _ConsoleMessageImpl
from pydoll.playwright._dialog import FileChooser as _FileChooserImpl
from pydoll.playwright._dialog import Download as _DownloadImpl
from pydoll.playwright._events import EventInfo as _EventInfoImpl



from pathlib import Path
from typing import Any, Optional, Sequence, Union
from pydoll.browser.chromium import Chrome
from pydoll.exceptions import PydollException
from pydoll.playwright._browser import build_options
from pydoll.playwright._errors import Error, translate
from pydoll.playwright._selectors import set_test_id_attribute_name
import asyncio
import logging
from typing import TYPE_CHECKING, Any, Optional, Sequence, Union, cast
from pydoll.browser.options import ChromiumOptions
from pydoll.commands import TargetCommands
from pydoll.playwright._events import EventEmitter
from pydoll.protocol.target.events import TargetEvent
from pydoll.protocol.target.types import TargetInfo
import inspect
import time
from typing import Any, Awaitable, Callable, Generic, Optional, TypeAlias, TypeVar
from pydoll.playwright._errors import TimeoutError
T = TypeVar('T')
Listener: TypeAlias = Callable[..., Any]
from pydoll.playwright._events import Deadline
from pydoll.playwright._events import EventContextManager
import json
import shutil
import tempfile
from typing import TYPE_CHECKING, Any, Callable, Optional, Sequence, Union
from pydoll.browser.tab import Tab
from pydoll.commands import BrowserCommands, EmulationCommands, PageCommands, RuntimeCommands
from pydoll.playwright._events import DEFAULT_TIMEOUT_MS, Deadline, EventContextManager, EventEmitter, create_future, schedule
from pydoll.playwright._glob import URLMatch
from pydoll.playwright._network import RouteEntry, RouteHandler, make_entry
from pydoll.protocol.browser.types import DownloadBehavior, PermissionType
from pydoll.utils.user_agent_parser import UserAgentParser
import base64
import secrets
import weakref
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Optional, Sequence, Union
from pydoll.commands import DomCommands, EmulationCommands, PageCommands, RuntimeCommands
from pydoll.elements.web_element import WebElement
from pydoll.playwright._errors import Error, TargetClosedError, translate
from pydoll.playwright._events import Deadline, EventContextManager, EventEmitter, create_future, schedule
from pydoll.playwright._navigation import NavigationTracker
from pydoll.playwright._network import NetworkManager, RouteEntry, RouteHandler, Router, make_entry, wait_for_matching
from pydoll.playwright._selectors import TextMatch
from pydoll.protocol.fetch.events import FetchEvent
from pydoll.protocol.fetch.types import AuthChallengeResponseType
from pydoll.protocol.network.events import NetworkEvent
from pydoll.protocol.page.events import PageEvent
from pydoll.protocol.runtime.events import RuntimeEvent
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Optional, Sequence, TypeVar, Union, cast
from pydoll.commands import DomCommands, PageCommands, RuntimeCommands
from pydoll.playwright._actions import Actions
from pydoll.playwright._element_handle import PrimitiveHandle
from pydoll.playwright._injected import engine_call, engine_source
from pydoll.playwright._locator import FilePayload
from pydoll.playwright._selectors import TextMatch, get_by_alt_text_selector, get_by_label_selector, get_by_placeholder_selector, get_by_role_selector, get_by_test_id_selector, get_by_text_selector, get_by_title_selector, split_by_frame
from pydoll.playwright._serialization import call_arguments, evaluate_source, parse_remote_value
from pydoll.protocol.runtime.types import CallArgument
import re
from typing import TYPE_CHECKING, Any, Optional, Pattern, Sequence, TypedDict, Union
from pydoll.playwright._actions import Resolver
from pydoll.playwright._errors import Error
from pydoll.playwright._selectors import ENTER_FRAME, TextMatch, get_by_alt_text_selector, get_by_label_selector, get_by_placeholder_selector, get_by_role_selector, get_by_test_id_selector, get_by_text_selector, get_by_title_selector, with_has, with_has_not, with_has_not_text, with_has_text, with_visible
from pydoll.playwright._locator import SelectOption
from typing import TYPE_CHECKING, Any, Optional, Sequence, Union
from pydoll.commands import RuntimeCommands
from pydoll.playwright._serialization import parse_remote_value
from typing import TYPE_CHECKING, Literal, Optional, TypeAlias
from pydoll.commands import InputCommands
from pydoll.playwright._keys import MODIFIER_NAMES, KeyDescription, describe_key, modifier_bits, resolve_smart_modifier, split_key_string
from pydoll.protocol.input.types import KeyEventType, KeyModifier, MouseButton, MouseEventType, TouchEventType
MouseButtonName: TypeAlias = Literal['left', 'right', 'middle']
import mimetypes
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Optional, Union, cast
from pydoll.commands import NetworkCommands
from pydoll.playwright._glob import URLMatch, URLMatcher
from pydoll.protocol.network.types import ErrorReason
from pydoll.playwright._network import NetworkManager
from pydoll.playwright._network import RouteEntry
from pydoll.playwright._network import Router
from pydoll.commands import PageCommands
from pydoll.playwright._dialog import _PrimitiveHandle





class Playwright(SyncBase):
    """The object yielded by ``async_playwright()``."""
    _impl: _PlaywrightImpl

    @property
    def chromium(self) -> BrowserType:
        return mapping.from_impl(self._impl.chromium)

    @property
    def firefox(self) -> BrowserType:
        return mapping.from_impl(self._impl.firefox)

    @property
    def webkit(self) -> BrowserType:
        return mapping.from_impl(self._impl.webkit)

    @property
    def selectors(self) -> Selectors:
        return mapping.from_impl(self._impl.selectors)

    @property
    def devices(self) -> dict[str, dict[str, Any]]:
        return mapping.from_impl(self._impl.devices)

    @property
    def request(self) -> Any:
        return mapping.from_impl(self._impl.request)

    def stop(self) -> None:
        self._run(self._impl.stop())

class BrowserType(SyncBase):
    """``playwright.chromium``: launches or connects to a Chromium driven by pydoll."""
    _impl: _BrowserTypeImpl

    @property
    def name(self) -> str:
        return mapping.from_impl(self._impl.name)

    @property
    def executable_path(self) -> str:
        return mapping.from_impl(self._impl.executable_path)

    def launch(self, executable_path: Union[str, Path, None]=None, channel: Optional[str]=None, args: Optional[Sequence[str]]=None, ignore_default_args: Union[bool, Sequence[str], None]=None, handle_sigint: Optional[bool]=None, handle_sigterm: Optional[bool]=None, handle_sighup: Optional[bool]=None, timeout: Optional[float]=None, env: Optional[dict[str, Any]]=None, headless: Optional[bool]=None, devtools: Optional[bool]=None, proxy: Optional[dict[str, Any]]=None, downloads_path: Union[str, Path, None]=None, slow_mo: Optional[float]=None, traces_dir: Union[str, Path, None]=None, chromium_sandbox: Optional[bool]=None, firefox_user_prefs: Optional[dict[str, Any]]=None) -> Browser:
        return mapping.from_impl(self._run(self._impl.launch(executable_path=mapping.to_impl(executable_path), channel=mapping.to_impl(channel), args=mapping.to_impl(args), ignore_default_args=mapping.to_impl(ignore_default_args), handle_sigint=mapping.to_impl(handle_sigint), handle_sigterm=mapping.to_impl(handle_sigterm), handle_sighup=mapping.to_impl(handle_sighup), timeout=mapping.to_impl(timeout), env=mapping.to_impl(env), headless=mapping.to_impl(headless), devtools=mapping.to_impl(devtools), proxy=mapping.to_impl(proxy), downloads_path=mapping.to_impl(downloads_path), slow_mo=mapping.to_impl(slow_mo), traces_dir=mapping.to_impl(traces_dir), chromium_sandbox=mapping.to_impl(chromium_sandbox), firefox_user_prefs=mapping.to_impl(firefox_user_prefs))))

    def launch_persistent_context(self, user_data_dir: Union[str, Path], **kwargs: Any) -> BrowserContext:
        return mapping.from_impl(self._run(self._impl.launch_persistent_context(user_data_dir=mapping.to_impl(user_data_dir), **kwargs)))

    def connect_over_cdp(self, endpoint_url: str, timeout: Optional[float]=None, slow_mo: Optional[float]=None, headers: Optional[dict[str, str]]=None) -> Browser:
        return mapping.from_impl(self._run(self._impl.connect_over_cdp(endpoint_url=mapping.to_impl(endpoint_url), timeout=mapping.to_impl(timeout), slow_mo=mapping.to_impl(slow_mo), headers=mapping.to_impl(headers))))

    def connect(self, ws_endpoint: str, **kwargs: Any) -> Browser:
        return mapping.from_impl(self._run(self._impl.connect(ws_endpoint=mapping.to_impl(ws_endpoint), **kwargs)))

class Selectors(SyncBase):
    """``playwright.selectors``: only the test id attribute is configurable."""
    _impl: _SelectorsImpl

    def register(self, name: str, script: Optional[str]=None, path: Union[str, Path, None]=None, content_script: Optional[bool]=None) -> None:
        self._run(self._impl.register(name=mapping.to_impl(name), script=mapping.to_impl(script), path=mapping.to_impl(path), content_script=mapping.to_impl(content_script)))

    def set_test_id_attribute(self, attribute_name: str) -> None:
        self._impl.set_test_id_attribute(attribute_name=mapping.to_impl(attribute_name))

class PlaywrightContextManager(SyncBase):
    """``async with async_playwright() as p:`` and ``await async_playwright().start()``."""
    _impl: _PlaywrightContextManagerImpl

    def __enter__(self) -> PlaywrightContextManager:
        return mapping.from_impl(self._run(self._impl.__aenter__()))

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> Any:
        return self._run(self._impl.__aexit__(exc_type, exc, tb))

    def start(self) -> Playwright:
        return mapping.from_impl(self._run(self._impl.start()))

class Browser(SyncBase):
    """A running Chromium controlled by pydoll, exposed with Playwright's API."""
    _impl: _BrowserImpl

    @property
    def browser_type(self) -> BrowserType:
        return mapping.from_impl(self._impl.browser_type)

    @property
    def contexts(self) -> list[BrowserContext]:
        return mapping.from_impl(self._impl.contexts)

    @property
    def version(self) -> str:
        return mapping.from_impl(self._impl.version)

    @property
    def chrome(self) -> Chrome:
        """The underlying pydoll Chrome, for code that mixes both APIs."""
        return mapping.from_impl(self._impl.chrome)

    def is_connected(self) -> bool:
        return mapping.from_impl(self._impl.is_connected())

    def new_context(self, **options: Any) -> BrowserContext:
        return mapping.from_impl(self._run(self._impl.new_context(**options)))

    def new_page(self, **options: Any) -> Page:
        return mapping.from_impl(self._run(self._impl.new_page(**options)))

    def close(self, reason: Optional[str]=None) -> None:
        self._run(self._impl.close(reason=mapping.to_impl(reason)))

    def new_browser_cdp_session(self) -> Any:
        return mapping.from_impl(self._run(self._impl.new_browser_cdp_session()))

    def start_tracing(self, **kwargs: Any) -> None:
        self._run(self._impl.start_tracing(**kwargs))

    def stop_tracing(self) -> bytes:
        return mapping.from_impl(self._run(self._impl.stop_tracing()))

    def on(self, event: str, listener: Listener) -> None:
        self._impl.on(event=mapping.to_impl(event), listener=mapping.wrap_handler(listener))

    def once(self, event: str, listener: Listener) -> None:
        self._impl.once(event=mapping.to_impl(event), listener=mapping.wrap_handler(listener))

    def remove_listener(self, event: str, listener: Listener) -> None:
        self._impl.remove_listener(event=mapping.to_impl(event), listener=mapping.wrap_handler(listener))

    def listener_count(self, event: str) -> int:
        return mapping.from_impl(self._impl.listener_count(event=mapping.to_impl(event)))

    def emit(self, event: str, *args: Any) -> None:
        self._impl.emit(mapping.to_impl(event), *args)

class BrowserContext(SyncBase):
    """An isolated browsing session; ``browser.new_context()`` creates one."""
    _impl: _BrowserContextImpl

    def new_page(self) -> Page:
        return mapping.from_impl(self._run(self._impl.new_page()))

    @property
    def pages(self) -> list[Page]:
        return mapping.from_impl(self._impl.pages)

    @property
    def browser(self) -> Optional[Browser]:
        return mapping.from_impl(self._impl.browser)

    @property
    def background_pages(self) -> list[Page]:
        return mapping.from_impl(self._impl.background_pages)

    @property
    def service_workers(self) -> list[Any]:
        return mapping.from_impl(self._impl.service_workers)

    @property
    def tracing(self) -> Any:
        return mapping.from_impl(self._impl.tracing)

    @property
    def request(self) -> Any:
        return mapping.from_impl(self._impl.request)

    @property
    def clock(self) -> Any:
        return mapping.from_impl(self._impl.clock)

    def set_default_timeout(self, timeout: float) -> None:
        self._impl.set_default_timeout(timeout=mapping.to_impl(timeout))

    def set_default_navigation_timeout(self, timeout: float) -> None:
        self._impl.set_default_navigation_timeout(timeout=mapping.to_impl(timeout))

    def cookies(self, urls: Union[str, Sequence[str], None]=None) -> list[dict[str, Any]]:
        return mapping.from_impl(self._run(self._impl.cookies(urls=mapping.to_impl(urls))))

    def add_cookies(self, cookies: Sequence[dict[str, Any]]) -> None:
        self._run(self._impl.add_cookies(cookies=mapping.to_impl(cookies)))

    def clear_cookies(self, **kwargs: Any) -> None:
        self._run(self._impl.clear_cookies(**kwargs))

    def storage_state(self, path: Union[str, Path, None]=None, indexed_db: Optional[bool]=None) -> dict[str, Any]:
        return mapping.from_impl(self._run(self._impl.storage_state(path=mapping.to_impl(path), indexed_db=mapping.to_impl(indexed_db))))

    def grant_permissions(self, permissions: Sequence[str], origin: Optional[str]=None) -> None:
        self._run(self._impl.grant_permissions(permissions=mapping.to_impl(permissions), origin=mapping.to_impl(origin)))

    def clear_permissions(self) -> None:
        self._run(self._impl.clear_permissions())

    def set_geolocation(self, geolocation: Optional[dict[str, float]]) -> None:
        self._run(self._impl.set_geolocation(geolocation=mapping.to_impl(geolocation)))

    def set_extra_http_headers(self, headers: dict[str, str]) -> None:
        self._run(self._impl.set_extra_http_headers(headers=mapping.to_impl(headers)))

    def set_offline(self, offline: bool) -> None:
        self._run(self._impl.set_offline(offline=mapping.to_impl(offline)))

    def add_init_script(self, script: Optional[str]=None, path: Union[str, Path, None]=None) -> None:
        self._run(self._impl.add_init_script(script=mapping.to_impl(script), path=mapping.to_impl(path)))

    def expose_function(self, name: str, callback: Callable[..., Any]) -> None:
        self._run(self._impl.expose_function(name=mapping.to_impl(name), callback=mapping.wrap_handler(callback)))

    def expose_binding(self, name: str, callback: Callable[..., Any], handle: Optional[bool]=None) -> None:
        self._run(self._impl.expose_binding(name=mapping.to_impl(name), callback=mapping.wrap_handler(callback), handle=mapping.to_impl(handle)))

    def route(self, url: URLMatch, handler: RouteHandler, times: Optional[int]=None) -> None:
        self._run(self._impl.route(url=mapping.to_impl(url), handler=mapping.wrap_handler(handler), times=mapping.to_impl(times)))

    def unroute(self, url: URLMatch, handler: Optional[RouteHandler]=None) -> None:
        self._run(self._impl.unroute(url=mapping.to_impl(url), handler=mapping.wrap_handler(handler)))

    def unroute_all(self, behavior: Optional[str]=None) -> None:
        self._run(self._impl.unroute_all(behavior=mapping.to_impl(behavior)))

    def wait_for_event(self, event: str, predicate: Optional[Callable[[Any], Any]]=None, timeout: Optional[float]=None) -> Any:
        return mapping.from_impl(self._run(self._impl.wait_for_event(event=mapping.to_impl(event), predicate=mapping.wrap_predicate(predicate), timeout=mapping.to_impl(timeout))))

    def expect_event(self, event: str, predicate: Optional[Callable[[Any], Any]]=None, timeout: Optional[float]=None) -> EventContextManager[Any]:
        return mapping.from_impl(self._impl.expect_event(event=mapping.to_impl(event), predicate=mapping.wrap_predicate(predicate), timeout=mapping.to_impl(timeout)))

    def expect_page(self, predicate: Optional[Callable[[Page], bool]]=None, timeout: Optional[float]=None) -> EventContextManager[Page]:
        return mapping.from_impl(self._impl.expect_page(predicate=mapping.wrap_predicate(predicate), timeout=mapping.to_impl(timeout)))

    def expect_console_message(self, predicate: Any=None, timeout: Optional[float]=None) -> EventContextManager[Any]:
        return mapping.from_impl(self._impl.expect_console_message(predicate=mapping.wrap_predicate(predicate), timeout=mapping.to_impl(timeout)))

    def close(self, reason: Optional[str]=None) -> None:
        self._run(self._impl.close(reason=mapping.to_impl(reason)))

    def new_cdp_session(self, page: Page) -> Any:
        return mapping.from_impl(self._run(self._impl.new_cdp_session(page=mapping.to_impl(page))))

    def on(self, event: str, listener: Listener) -> None:
        self._impl.on(event=mapping.to_impl(event), listener=mapping.wrap_handler(listener))

    def once(self, event: str, listener: Listener) -> None:
        self._impl.once(event=mapping.to_impl(event), listener=mapping.wrap_handler(listener))

    def remove_listener(self, event: str, listener: Listener) -> None:
        self._impl.remove_listener(event=mapping.to_impl(event), listener=mapping.wrap_handler(listener))

    def listener_count(self, event: str) -> int:
        return mapping.from_impl(self._impl.listener_count(event=mapping.to_impl(event)))

    def emit(self, event: str, *args: Any) -> None:
        self._impl.emit(mapping.to_impl(event), *args)

class Page(SyncBase):
    """A single tab of a browser context."""
    _impl: _PageImpl

    @property
    def main_frame(self) -> Frame:
        return mapping.from_impl(self._impl.main_frame)

    @property
    def frames(self) -> list[Frame]:
        return mapping.from_impl(self._impl.frames)

    def frame(self, name: Optional[str]=None, url: Optional[URLMatch]=None) -> Optional[Frame]:
        return mapping.from_impl(self._impl.frame(name=mapping.to_impl(name), url=mapping.to_impl(url)))

    @property
    def context(self) -> BrowserContext:
        return mapping.from_impl(self._impl.context)

    @property
    def url(self) -> str:
        return mapping.from_impl(self._impl.url)

    @property
    def keyboard(self) -> Keyboard:
        return mapping.from_impl(self._impl.keyboard)

    @property
    def mouse(self) -> Mouse:
        return mapping.from_impl(self._impl.mouse)

    @property
    def touchscreen(self) -> Touchscreen:
        return mapping.from_impl(self._impl.touchscreen)

    @property
    def viewport_size(self) -> Optional[dict[str, int]]:
        return mapping.from_impl(self._impl.viewport_size)

    @property
    def workers(self) -> list[Any]:
        return mapping.from_impl(self._impl.workers)

    @property
    def video(self) -> None:
        return mapping.from_impl(self._impl.video)

    @property
    def request(self) -> Any:
        return mapping.from_impl(self._impl.request)

    @property
    def clock(self) -> Any:
        return mapping.from_impl(self._impl.clock)

    @property
    def tab(self) -> Tab:
        """The underlying pydoll Tab, for code that mixes both APIs."""
        return mapping.from_impl(self._impl.tab)

    def is_closed(self) -> bool:
        return mapping.from_impl(self._impl.is_closed())

    def opener(self) -> Optional[Page]:
        return mapping.from_impl(self._run(self._impl.opener()))

    def set_default_timeout(self, timeout: float) -> None:
        self._impl.set_default_timeout(timeout=mapping.to_impl(timeout))

    def set_default_navigation_timeout(self, timeout: float) -> None:
        self._impl.set_default_navigation_timeout(timeout=mapping.to_impl(timeout))

    def on(self, event: str, listener: Callable[..., Any]) -> None:
        self._impl.on(event=mapping.to_impl(event), listener=mapping.wrap_handler(listener))

    def once(self, event: str, listener: Callable[..., Any]) -> None:
        self._impl.once(event=mapping.to_impl(event), listener=mapping.wrap_handler(listener))

    def wait_for_event(self, event: str, predicate: Optional[Callable[[Any], Any]]=None, timeout: Optional[float]=None) -> Any:
        return mapping.from_impl(self._run(self._impl.wait_for_event(event=mapping.to_impl(event), predicate=mapping.wrap_predicate(predicate), timeout=mapping.to_impl(timeout))))

    def expect_event(self, event: str, predicate: Optional[Callable[[Any], Any]]=None, timeout: Optional[float]=None) -> EventContextManager[Any]:
        return mapping.from_impl(self._impl.expect_event(event=mapping.to_impl(event), predicate=mapping.wrap_predicate(predicate), timeout=mapping.to_impl(timeout)))

    def expect_console_message(self, predicate: Optional[Callable[[ConsoleMessage], bool]]=None, timeout: Optional[float]=None) -> EventContextManager[ConsoleMessage]:
        return mapping.from_impl(self._impl.expect_console_message(predicate=mapping.wrap_predicate(predicate), timeout=mapping.to_impl(timeout)))

    def expect_download(self, predicate: Optional[Callable[[Download], bool]]=None, timeout: Optional[float]=None) -> EventContextManager[Download]:
        return mapping.from_impl(self._impl.expect_download(predicate=mapping.wrap_predicate(predicate), timeout=mapping.to_impl(timeout)))

    def expect_file_chooser(self, predicate: Optional[Callable[[FileChooser], bool]]=None, timeout: Optional[float]=None) -> EventContextManager[FileChooser]:
        return mapping.from_impl(self._impl.expect_file_chooser(predicate=mapping.wrap_predicate(predicate), timeout=mapping.to_impl(timeout)))

    def expect_popup(self, predicate: Optional[Callable[[Page], bool]]=None, timeout: Optional[float]=None) -> EventContextManager[Page]:
        return mapping.from_impl(self._impl.expect_popup(predicate=mapping.wrap_predicate(predicate), timeout=mapping.to_impl(timeout)))

    def expect_worker(self, predicate: Any=None, timeout: Optional[float]=None) -> EventContextManager[Any]:
        return mapping.from_impl(self._impl.expect_worker(predicate=mapping.wrap_predicate(predicate), timeout=mapping.to_impl(timeout)))

    def expect_websocket(self, predicate: Any=None, timeout: Optional[float]=None) -> EventContextManager[Any]:
        return mapping.from_impl(self._impl.expect_websocket(predicate=mapping.wrap_predicate(predicate), timeout=mapping.to_impl(timeout)))

    def expect_request(self, url_or_predicate: Union[URLMatch, Callable[[Request], Any]], timeout: Optional[float]=None) -> EventContextManager[Request]:
        return mapping.from_impl(self._impl.expect_request(url_or_predicate=mapping.wrap_predicate(url_or_predicate), timeout=mapping.to_impl(timeout)))

    def expect_request_finished(self, predicate: Optional[Callable[[Request], Any]]=None, timeout: Optional[float]=None) -> EventContextManager[Request]:
        return mapping.from_impl(self._impl.expect_request_finished(predicate=mapping.wrap_predicate(predicate), timeout=mapping.to_impl(timeout)))

    def expect_response(self, url_or_predicate: Union[URLMatch, Callable[[Response], Any]], timeout: Optional[float]=None) -> EventContextManager[Response]:
        return mapping.from_impl(self._impl.expect_response(url_or_predicate=mapping.wrap_predicate(url_or_predicate), timeout=mapping.to_impl(timeout)))

    def expect_navigation(self, url: Optional[URLMatch]=None, wait_until: Optional[str]=None, timeout: Optional[float]=None) -> EventContextManager[Optional[Response]]:
        return mapping.from_impl(self._impl.expect_navigation(url=mapping.to_impl(url), wait_until=mapping.to_impl(wait_until), timeout=mapping.to_impl(timeout)))

    def goto(self, url: str, timeout: Optional[float]=None, wait_until: Optional[str]=None, referer: Optional[str]=None) -> Optional[Response]:
        return mapping.from_impl(self._run(self._impl.goto(url=mapping.to_impl(url), timeout=mapping.to_impl(timeout), wait_until=mapping.to_impl(wait_until), referer=mapping.to_impl(referer))))

    def reload(self, timeout: Optional[float]=None, wait_until: Optional[str]=None) -> Optional[Response]:
        return mapping.from_impl(self._run(self._impl.reload(timeout=mapping.to_impl(timeout), wait_until=mapping.to_impl(wait_until))))

    def go_back(self, timeout: Optional[float]=None, wait_until: Optional[str]=None) -> Optional[Response]:
        return mapping.from_impl(self._run(self._impl.go_back(timeout=mapping.to_impl(timeout), wait_until=mapping.to_impl(wait_until))))

    def go_forward(self, timeout: Optional[float]=None, wait_until: Optional[str]=None) -> Optional[Response]:
        return mapping.from_impl(self._run(self._impl.go_forward(timeout=mapping.to_impl(timeout), wait_until=mapping.to_impl(wait_until))))

    def wait_for_load_state(self, state: Optional[str]=None, timeout: Optional[float]=None) -> None:
        self._run(self._impl.wait_for_load_state(state=mapping.to_impl(state), timeout=mapping.to_impl(timeout)))

    def wait_for_url(self, url: URLMatch, wait_until: Optional[str]=None, timeout: Optional[float]=None) -> None:
        self._run(self._impl.wait_for_url(url=mapping.to_impl(url), wait_until=mapping.to_impl(wait_until), timeout=mapping.to_impl(timeout)))

    def wait_for_timeout(self, timeout: float) -> None:
        self._run(self._impl.wait_for_timeout(timeout=mapping.to_impl(timeout)))

    def wait_for_function(self, expression: str, arg: Any=None, timeout: Optional[float]=None, polling: Any=None) -> JSHandle:
        return mapping.from_impl(self._run(self._impl.wait_for_function(expression=mapping.to_impl(expression), arg=mapping.to_impl(arg), timeout=mapping.to_impl(timeout), polling=mapping.to_impl(polling))))

    def wait_for_selector(self, selector: str, timeout: Optional[float]=None, state: str='visible', strict: Optional[bool]=None) -> Optional[ElementHandle]:
        return mapping.from_impl(self._run(self._impl.wait_for_selector(selector=mapping.to_impl(selector), timeout=mapping.to_impl(timeout), state=mapping.to_impl(state), strict=mapping.to_impl(strict))))

    def content(self) -> str:
        return mapping.from_impl(self._run(self._impl.content()))

    def set_content(self, html: str, timeout: Optional[float]=None, wait_until: Optional[str]=None) -> None:
        self._run(self._impl.set_content(html=mapping.to_impl(html), timeout=mapping.to_impl(timeout), wait_until=mapping.to_impl(wait_until)))

    def title(self) -> str:
        return mapping.from_impl(self._run(self._impl.title()))

    def evaluate(self, expression: str, arg: Any=None) -> Any:
        return mapping.from_impl(self._run(self._impl.evaluate(expression=mapping.to_impl(expression), arg=mapping.to_impl(arg))))

    def evaluate_handle(self, expression: str, arg: Any=None) -> JSHandle:
        return mapping.from_impl(self._run(self._impl.evaluate_handle(expression=mapping.to_impl(expression), arg=mapping.to_impl(arg))))

    def query_selector(self, selector: str, strict: Optional[bool]=None) -> Optional[ElementHandle]:
        return mapping.from_impl(self._run(self._impl.query_selector(selector=mapping.to_impl(selector), strict=mapping.to_impl(strict))))

    def query_selector_all(self, selector: str) -> list[ElementHandle]:
        return mapping.from_impl(self._run(self._impl.query_selector_all(selector=mapping.to_impl(selector))))

    def eval_on_selector(self, selector: str, expression: str, arg: Any=None, strict: Optional[bool]=None) -> Any:
        return mapping.from_impl(self._run(self._impl.eval_on_selector(selector=mapping.to_impl(selector), expression=mapping.to_impl(expression), arg=mapping.to_impl(arg), strict=mapping.to_impl(strict))))

    def eval_on_selector_all(self, selector: str, expression: str, arg: Any=None) -> Any:
        return mapping.from_impl(self._run(self._impl.eval_on_selector_all(selector=mapping.to_impl(selector), expression=mapping.to_impl(expression), arg=mapping.to_impl(arg))))

    def add_script_tag(self, **kwargs: Any) -> ElementHandle:
        return mapping.from_impl(self._run(self._impl.add_script_tag(**kwargs)))

    def add_style_tag(self, **kwargs: Any) -> ElementHandle:
        return mapping.from_impl(self._run(self._impl.add_style_tag(**kwargs)))

    def add_init_script(self, script: Optional[str]=None, path: Union[str, Path, None]=None) -> None:
        self._run(self._impl.add_init_script(script=mapping.to_impl(script), path=mapping.to_impl(path)))

    def expose_function(self, name: str, callback: Callable[..., Any]) -> None:
        self._run(self._impl.expose_function(name=mapping.to_impl(name), callback=mapping.wrap_handler(callback)))

    def expose_binding(self, name: str, callback: Callable[..., Any], handle: Optional[bool]=None) -> None:
        self._run(self._impl.expose_binding(name=mapping.to_impl(name), callback=mapping.wrap_handler(callback), handle=mapping.to_impl(handle)))

    def set_extra_http_headers(self, headers: dict[str, str]) -> None:
        self._run(self._impl.set_extra_http_headers(headers=mapping.to_impl(headers)))

    def set_viewport_size(self, viewport_size: dict[str, int]) -> None:
        """Emulate a viewport, keeping ``screen`` at least as large as the viewport.

        A viewport wider than the screen is a contradiction no real device
        produces, so the screen size follows the context's ``screen`` option or
        a common desktop size that contains the viewport.
        """
        self._run(self._impl.set_viewport_size(viewport_size=mapping.to_impl(viewport_size)))

    def emulate_media(self, media: Optional[str]=None, color_scheme: Optional[str]=None, reduced_motion: Optional[str]=None, forced_colors: Optional[str]=None, contrast: Optional[str]=None) -> None:
        self._run(self._impl.emulate_media(media=mapping.to_impl(media), color_scheme=mapping.to_impl(color_scheme), reduced_motion=mapping.to_impl(reduced_motion), forced_colors=mapping.to_impl(forced_colors), contrast=mapping.to_impl(contrast)))

    def bring_to_front(self) -> None:
        self._run(self._impl.bring_to_front())

    def request_gc(self) -> None:
        self._run(self._impl.request_gc())

    def pause(self) -> None:
        self._run(self._impl.pause())

    def route(self, url: URLMatch, handler: RouteHandler, times: Optional[int]=None) -> None:
        self._run(self._impl.route(url=mapping.to_impl(url), handler=mapping.wrap_handler(handler), times=mapping.to_impl(times)))

    def unroute(self, url: URLMatch, handler: Optional[RouteHandler]=None) -> None:
        self._run(self._impl.unroute(url=mapping.to_impl(url), handler=mapping.wrap_handler(handler)))

    def unroute_all(self, behavior: Optional[str]=None) -> None:
        self._run(self._impl.unroute_all(behavior=mapping.to_impl(behavior)))

    def screenshot(self, timeout: Optional[float]=None, type: Optional[str]=None, path: Union[str, Path, None]=None, quality: Optional[int]=None, omit_background: Optional[bool]=None, full_page: Optional[bool]=None, clip: Optional[dict[str, float]]=None, animations: Optional[str]=None, caret: Optional[str]=None, scale: Optional[str]=None, mask: Optional[Sequence[Locator]]=None, mask_color: Optional[str]=None, style: Optional[str]=None) -> bytes:
        return mapping.from_impl(self._run(self._impl.screenshot(timeout=mapping.to_impl(timeout), type=mapping.to_impl(type), path=mapping.to_impl(path), quality=mapping.to_impl(quality), omit_background=mapping.to_impl(omit_background), full_page=mapping.to_impl(full_page), clip=mapping.to_impl(clip), animations=mapping.to_impl(animations), caret=mapping.to_impl(caret), scale=mapping.to_impl(scale), mask=mapping.to_impl(mask), mask_color=mapping.to_impl(mask_color), style=mapping.to_impl(style))))

    def pdf(self, scale: Optional[float]=None, display_header_footer: Optional[bool]=None, header_template: Optional[str]=None, footer_template: Optional[str]=None, print_background: Optional[bool]=None, landscape: Optional[bool]=None, page_ranges: Optional[str]=None, format: Optional[str]=None, width: Union[str, float, None]=None, height: Union[str, float, None]=None, prefer_css_page_size: Optional[bool]=None, margin: Optional[dict[str, Union[str, float]]]=None, path: Union[str, Path, None]=None, outline: Optional[bool]=None, tagged: Optional[bool]=None) -> bytes:
        return mapping.from_impl(self._run(self._impl.pdf(scale=mapping.to_impl(scale), display_header_footer=mapping.to_impl(display_header_footer), header_template=mapping.to_impl(header_template), footer_template=mapping.to_impl(footer_template), print_background=mapping.to_impl(print_background), landscape=mapping.to_impl(landscape), page_ranges=mapping.to_impl(page_ranges), format=mapping.to_impl(format), width=mapping.to_impl(width), height=mapping.to_impl(height), prefer_css_page_size=mapping.to_impl(prefer_css_page_size), margin=mapping.to_impl(margin), path=mapping.to_impl(path), outline=mapping.to_impl(outline), tagged=mapping.to_impl(tagged))))

    def close(self, run_before_unload: Optional[bool]=None, reason: Optional[str]=None) -> None:
        self._run(self._impl.close(run_before_unload=mapping.to_impl(run_before_unload), reason=mapping.to_impl(reason)))

    def locator(self, selector: str, **kwargs: Any) -> Locator:
        return mapping.from_impl(self._impl.locator(selector=mapping.to_impl(selector), **kwargs))

    def get_by_alt_text(self, text: TextMatch, exact: Optional[bool]=None) -> Locator:
        return mapping.from_impl(self._impl.get_by_alt_text(text=mapping.to_impl(text), exact=mapping.to_impl(exact)))

    def get_by_label(self, text: TextMatch, exact: Optional[bool]=None) -> Locator:
        return mapping.from_impl(self._impl.get_by_label(text=mapping.to_impl(text), exact=mapping.to_impl(exact)))

    def get_by_placeholder(self, text: TextMatch, exact: Optional[bool]=None) -> Locator:
        return mapping.from_impl(self._impl.get_by_placeholder(text=mapping.to_impl(text), exact=mapping.to_impl(exact)))

    def get_by_role(self, role: str, **kwargs: Any) -> Locator:
        return mapping.from_impl(self._impl.get_by_role(role=mapping.to_impl(role), **kwargs))

    def get_by_test_id(self, test_id: TextMatch) -> Locator:
        return mapping.from_impl(self._impl.get_by_test_id(test_id=mapping.to_impl(test_id)))

    def get_by_text(self, text: TextMatch, exact: Optional[bool]=None) -> Locator:
        return mapping.from_impl(self._impl.get_by_text(text=mapping.to_impl(text), exact=mapping.to_impl(exact)))

    def get_by_title(self, text: TextMatch, exact: Optional[bool]=None) -> Locator:
        return mapping.from_impl(self._impl.get_by_title(text=mapping.to_impl(text), exact=mapping.to_impl(exact)))

    def frame_locator(self, selector: str) -> FrameLocator:
        return mapping.from_impl(self._impl.frame_locator(selector=mapping.to_impl(selector)))

    def click(self, selector: str, **kwargs: Any) -> None:
        self._run(self._impl.click(selector=mapping.to_impl(selector), **kwargs))

    def dblclick(self, selector: str, **kwargs: Any) -> None:
        self._run(self._impl.dblclick(selector=mapping.to_impl(selector), **kwargs))

    def tap(self, selector: str, **kwargs: Any) -> None:
        self._run(self._impl.tap(selector=mapping.to_impl(selector), **kwargs))

    def hover(self, selector: str, **kwargs: Any) -> None:
        self._run(self._impl.hover(selector=mapping.to_impl(selector), **kwargs))

    def fill(self, selector: str, value: str, **kwargs: Any) -> None:
        self._run(self._impl.fill(selector=mapping.to_impl(selector), value=mapping.to_impl(value), **kwargs))

    def focus(self, selector: str, **kwargs: Any) -> None:
        self._run(self._impl.focus(selector=mapping.to_impl(selector), **kwargs))

    def type(self, selector: str, text: str, **kwargs: Any) -> None:
        self._run(self._impl.type(selector=mapping.to_impl(selector), text=mapping.to_impl(text), **kwargs))

    def press(self, selector: str, key: str, **kwargs: Any) -> None:
        self._run(self._impl.press(selector=mapping.to_impl(selector), key=mapping.to_impl(key), **kwargs))

    def check(self, selector: str, **kwargs: Any) -> None:
        self._run(self._impl.check(selector=mapping.to_impl(selector), **kwargs))

    def uncheck(self, selector: str, **kwargs: Any) -> None:
        self._run(self._impl.uncheck(selector=mapping.to_impl(selector), **kwargs))

    def set_checked(self, selector: str, checked: bool, **kwargs: Any) -> None:
        self._run(self._impl.set_checked(selector=mapping.to_impl(selector), checked=mapping.to_impl(checked), **kwargs))

    def select_option(self, selector: str, value: Any=None, **kwargs: Any) -> list[str]:
        return mapping.from_impl(self._run(self._impl.select_option(selector=mapping.to_impl(selector), value=mapping.to_impl(value), **kwargs)))

    def set_input_files(self, selector: str, files: Any, **kwargs: Any) -> None:
        self._run(self._impl.set_input_files(selector=mapping.to_impl(selector), files=mapping.to_impl(files), **kwargs))

    def dispatch_event(self, selector: str, type: str, event_init: Optional[dict[str, Any]]=None, **kwargs: Any) -> None:
        self._run(self._impl.dispatch_event(selector=mapping.to_impl(selector), type=mapping.to_impl(type), event_init=mapping.to_impl(event_init), **kwargs))

    def drag_and_drop(self, source: str, target: str, **kwargs: Any) -> None:
        self._run(self._impl.drag_and_drop(source=mapping.to_impl(source), target=mapping.to_impl(target), **kwargs))

    def get_attribute(self, selector: str, name: str, **kwargs: Any) -> Optional[str]:
        return mapping.from_impl(self._run(self._impl.get_attribute(selector=mapping.to_impl(selector), name=mapping.to_impl(name), **kwargs)))

    def text_content(self, selector: str, **kwargs: Any) -> Optional[str]:
        return mapping.from_impl(self._run(self._impl.text_content(selector=mapping.to_impl(selector), **kwargs)))

    def inner_text(self, selector: str, **kwargs: Any) -> str:
        return mapping.from_impl(self._run(self._impl.inner_text(selector=mapping.to_impl(selector), **kwargs)))

    def inner_html(self, selector: str, **kwargs: Any) -> str:
        return mapping.from_impl(self._run(self._impl.inner_html(selector=mapping.to_impl(selector), **kwargs)))

    def input_value(self, selector: str, **kwargs: Any) -> str:
        return mapping.from_impl(self._run(self._impl.input_value(selector=mapping.to_impl(selector), **kwargs)))

    def is_checked(self, selector: str, **kwargs: Any) -> bool:
        return mapping.from_impl(self._run(self._impl.is_checked(selector=mapping.to_impl(selector), **kwargs)))

    def is_disabled(self, selector: str, **kwargs: Any) -> bool:
        return mapping.from_impl(self._run(self._impl.is_disabled(selector=mapping.to_impl(selector), **kwargs)))

    def is_editable(self, selector: str, **kwargs: Any) -> bool:
        return mapping.from_impl(self._run(self._impl.is_editable(selector=mapping.to_impl(selector), **kwargs)))

    def is_enabled(self, selector: str, **kwargs: Any) -> bool:
        return mapping.from_impl(self._run(self._impl.is_enabled(selector=mapping.to_impl(selector), **kwargs)))

    def is_hidden(self, selector: str, **kwargs: Any) -> bool:
        return mapping.from_impl(self._run(self._impl.is_hidden(selector=mapping.to_impl(selector), **kwargs)))

    def is_visible(self, selector: str, **kwargs: Any) -> bool:
        return mapping.from_impl(self._run(self._impl.is_visible(selector=mapping.to_impl(selector), **kwargs)))

    def remove_listener(self, event: str, listener: Listener) -> None:
        self._impl.remove_listener(event=mapping.to_impl(event), listener=mapping.wrap_handler(listener))

    def listener_count(self, event: str) -> int:
        return mapping.from_impl(self._impl.listener_count(event=mapping.to_impl(event)))

    def emit(self, event: str, *args: Any) -> None:
        self._impl.emit(mapping.to_impl(event), *args)

class Frame(SyncBase):
    """A document inside a page: the main frame or an ``<iframe>``."""
    _impl: _FrameImpl

    @property
    def page(self) -> Page:
        return mapping.from_impl(self._impl.page)

    @property
    def name(self) -> str:
        return mapping.from_impl(self._impl.name)

    @property
    def url(self) -> str:
        return mapping.from_impl(self._impl.url)

    @property
    def parent_frame(self) -> Optional[Frame]:
        return mapping.from_impl(self._impl.parent_frame)

    @property
    def child_frames(self) -> list[Frame]:
        return mapping.from_impl(self._impl.child_frames)

    def is_detached(self) -> bool:
        return mapping.from_impl(self._impl.is_detached())

    def frame_element(self) -> ElementHandle:
        return mapping.from_impl(self._run(self._impl.frame_element()))

    def wait_for_selector(self, selector: str, timeout: Optional[float]=None, state: str='visible', strict: Optional[bool]=None, root: Optional[WebElement]=None) -> Optional[ElementHandle]:
        return mapping.from_impl(self._run(self._impl.wait_for_selector(selector=mapping.to_impl(selector), timeout=mapping.to_impl(timeout), state=mapping.to_impl(state), strict=mapping.to_impl(strict), root=mapping.to_impl(root))))

    def evaluate(self, expression: str, arg: Any=None) -> Any:
        return mapping.from_impl(self._run(self._impl.evaluate(expression=mapping.to_impl(expression), arg=mapping.to_impl(arg))))

    def evaluate_handle(self, expression: str, arg: Any=None) -> JSHandle:
        return mapping.from_impl(self._run(self._impl.evaluate_handle(expression=mapping.to_impl(expression), arg=mapping.to_impl(arg))))

    def wait_for_function(self, expression: str, arg: Any=None, timeout: Optional[float]=None, polling: Any=None) -> JSHandle:
        return mapping.from_impl(self._run(self._impl.wait_for_function(expression=mapping.to_impl(expression), arg=mapping.to_impl(arg), timeout=mapping.to_impl(timeout), polling=mapping.to_impl(polling))))

    def wait_for_timeout(self, timeout: float) -> None:
        self._run(self._impl.wait_for_timeout(timeout=mapping.to_impl(timeout)))

    def content(self) -> str:
        return mapping.from_impl(self._run(self._impl.content()))

    def set_content(self, html: str, timeout: Optional[float]=None, wait_until: Optional[str]=None) -> None:
        self._run(self._impl.set_content(html=mapping.to_impl(html), timeout=mapping.to_impl(timeout), wait_until=mapping.to_impl(wait_until)))

    def title(self) -> str:
        return mapping.from_impl(self._run(self._impl.title()))

    def query_selector(self, selector: str, strict: Optional[bool]=None) -> Optional[ElementHandle]:
        return mapping.from_impl(self._run(self._impl.query_selector(selector=mapping.to_impl(selector), strict=mapping.to_impl(strict))))

    def query_selector_all(self, selector: str) -> list[ElementHandle]:
        return mapping.from_impl(self._run(self._impl.query_selector_all(selector=mapping.to_impl(selector))))

    def eval_on_selector(self, selector: str, expression: str, arg: Any=None, strict: Optional[bool]=None) -> Any:
        return mapping.from_impl(self._run(self._impl.eval_on_selector(selector=mapping.to_impl(selector), expression=mapping.to_impl(expression), arg=mapping.to_impl(arg), strict=mapping.to_impl(strict))))

    def eval_on_selector_all(self, selector: str, expression: str, arg: Any=None) -> Any:
        return mapping.from_impl(self._run(self._impl.eval_on_selector_all(selector=mapping.to_impl(selector), expression=mapping.to_impl(expression), arg=mapping.to_impl(arg))))

    def add_script_tag(self, url: Optional[str]=None, path: Optional[Union[str, Path]]=None, content: Optional[str]=None, type: Optional[str]=None) -> ElementHandle:
        return mapping.from_impl(self._run(self._impl.add_script_tag(url=mapping.to_impl(url), path=mapping.to_impl(path), content=mapping.to_impl(content), type=mapping.to_impl(type))))

    def add_style_tag(self, url: Optional[str]=None, path: Optional[Union[str, Path]]=None, content: Optional[str]=None) -> ElementHandle:
        return mapping.from_impl(self._run(self._impl.add_style_tag(url=mapping.to_impl(url), path=mapping.to_impl(path), content=mapping.to_impl(content))))

    def goto(self, url: str, timeout: Optional[float]=None, wait_until: Optional[str]=None, referer: Optional[str]=None) -> Optional[Response]:
        return mapping.from_impl(self._run(self._impl.goto(url=mapping.to_impl(url), timeout=mapping.to_impl(timeout), wait_until=mapping.to_impl(wait_until), referer=mapping.to_impl(referer))))

    def wait_for_load_state(self, state: Optional[str]=None, timeout: Optional[float]=None) -> None:
        self._run(self._impl.wait_for_load_state(state=mapping.to_impl(state), timeout=mapping.to_impl(timeout)))

    def wait_for_url(self, url: Any, wait_until: Optional[str]=None, timeout: Optional[float]=None) -> None:
        self._run(self._impl.wait_for_url(url=mapping.to_impl(url), wait_until=mapping.to_impl(wait_until), timeout=mapping.to_impl(timeout)))

    def expect_navigation(self, url: Any=None, wait_until: Optional[str]=None, timeout: Optional[float]=None) -> Any:
        return mapping.from_impl(self._impl.expect_navigation(url=mapping.to_impl(url), wait_until=mapping.to_impl(wait_until), timeout=mapping.to_impl(timeout)))

    def locator(self, selector: str, has_text: Optional[TextMatch]=None, has_not_text: Optional[TextMatch]=None, has: Optional[Locator]=None, has_not: Optional[Locator]=None) -> Locator:
        return mapping.from_impl(self._impl.locator(selector=mapping.to_impl(selector), has_text=mapping.to_impl(has_text), has_not_text=mapping.to_impl(has_not_text), has=mapping.to_impl(has), has_not=mapping.to_impl(has_not)))

    def get_by_alt_text(self, text: TextMatch, exact: Optional[bool]=None) -> Locator:
        return mapping.from_impl(self._impl.get_by_alt_text(text=mapping.to_impl(text), exact=mapping.to_impl(exact)))

    def get_by_label(self, text: TextMatch, exact: Optional[bool]=None) -> Locator:
        return mapping.from_impl(self._impl.get_by_label(text=mapping.to_impl(text), exact=mapping.to_impl(exact)))

    def get_by_placeholder(self, text: TextMatch, exact: Optional[bool]=None) -> Locator:
        return mapping.from_impl(self._impl.get_by_placeholder(text=mapping.to_impl(text), exact=mapping.to_impl(exact)))

    def get_by_role(self, role: str, **kwargs: Any) -> Locator:
        return mapping.from_impl(self._impl.get_by_role(role=mapping.to_impl(role), **kwargs))

    def get_by_test_id(self, test_id: TextMatch) -> Locator:
        return mapping.from_impl(self._impl.get_by_test_id(test_id=mapping.to_impl(test_id)))

    def get_by_text(self, text: TextMatch, exact: Optional[bool]=None) -> Locator:
        return mapping.from_impl(self._impl.get_by_text(text=mapping.to_impl(text), exact=mapping.to_impl(exact)))

    def get_by_title(self, text: TextMatch, exact: Optional[bool]=None) -> Locator:
        return mapping.from_impl(self._impl.get_by_title(text=mapping.to_impl(text), exact=mapping.to_impl(exact)))

    def frame_locator(self, selector: str) -> FrameLocator:
        return mapping.from_impl(self._impl.frame_locator(selector=mapping.to_impl(selector)))

    def click(self, selector: str, strict: Optional[bool]=None, **kwargs: Any) -> None:
        self._run(self._impl.click(selector=mapping.to_impl(selector), strict=mapping.to_impl(strict), **kwargs))

    def dblclick(self, selector: str, strict: Optional[bool]=None, **kwargs: Any) -> None:
        self._run(self._impl.dblclick(selector=mapping.to_impl(selector), strict=mapping.to_impl(strict), **kwargs))

    def tap(self, selector: str, strict: Optional[bool]=None, **kwargs: Any) -> None:
        self._run(self._impl.tap(selector=mapping.to_impl(selector), strict=mapping.to_impl(strict), **kwargs))

    def hover(self, selector: str, strict: Optional[bool]=None, **kwargs: Any) -> None:
        self._run(self._impl.hover(selector=mapping.to_impl(selector), strict=mapping.to_impl(strict), **kwargs))

    def fill(self, selector: str, value: str, strict: Optional[bool]=None, **kwargs: Any) -> None:
        self._run(self._impl.fill(selector=mapping.to_impl(selector), value=mapping.to_impl(value), strict=mapping.to_impl(strict), **kwargs))

    def focus(self, selector: str, strict: Optional[bool]=None, timeout: Optional[float]=None) -> None:
        self._run(self._impl.focus(selector=mapping.to_impl(selector), strict=mapping.to_impl(strict), timeout=mapping.to_impl(timeout)))

    def type(self, selector: str, text: str, strict: Optional[bool]=None, **kwargs: Any) -> None:
        self._run(self._impl.type(selector=mapping.to_impl(selector), text=mapping.to_impl(text), strict=mapping.to_impl(strict), **kwargs))

    def press(self, selector: str, key: str, strict: Optional[bool]=None, **kwargs: Any) -> None:
        self._run(self._impl.press(selector=mapping.to_impl(selector), key=mapping.to_impl(key), strict=mapping.to_impl(strict), **kwargs))

    def check(self, selector: str, strict: Optional[bool]=None, **kwargs: Any) -> None:
        self._run(self._impl.check(selector=mapping.to_impl(selector), strict=mapping.to_impl(strict), **kwargs))

    def uncheck(self, selector: str, strict: Optional[bool]=None, **kwargs: Any) -> None:
        self._run(self._impl.uncheck(selector=mapping.to_impl(selector), strict=mapping.to_impl(strict), **kwargs))

    def set_checked(self, selector: str, checked: bool, strict: Optional[bool]=None, **kwargs: Any) -> None:
        self._run(self._impl.set_checked(selector=mapping.to_impl(selector), checked=mapping.to_impl(checked), strict=mapping.to_impl(strict), **kwargs))

    def select_option(self, selector: str, value: Any=None, strict: Optional[bool]=None, **kwargs: Any) -> list[str]:
        return mapping.from_impl(self._run(self._impl.select_option(selector=mapping.to_impl(selector), value=mapping.to_impl(value), strict=mapping.to_impl(strict), **kwargs)))

    def set_input_files(self, selector: str, files: Union[str, Path, FilePayload, Sequence[Any]], strict: Optional[bool]=None, **kwargs: Any) -> None:
        self._run(self._impl.set_input_files(selector=mapping.to_impl(selector), files=mapping.to_impl(files), strict=mapping.to_impl(strict), **kwargs))

    def dispatch_event(self, selector: str, type: str, event_init: Optional[dict[str, Any]]=None, strict: Optional[bool]=None, **kwargs: Any) -> None:
        self._run(self._impl.dispatch_event(selector=mapping.to_impl(selector), type=mapping.to_impl(type), event_init=mapping.to_impl(event_init), strict=mapping.to_impl(strict), **kwargs))

    def drag_and_drop(self, source: str, target: str, strict: Optional[bool]=None, **kwargs: Any) -> None:
        self._run(self._impl.drag_and_drop(source=mapping.to_impl(source), target=mapping.to_impl(target), strict=mapping.to_impl(strict), **kwargs))

    def get_attribute(self, selector: str, name: str, strict: Optional[bool]=None, timeout: Optional[float]=None) -> Optional[str]:
        return mapping.from_impl(self._run(self._impl.get_attribute(selector=mapping.to_impl(selector), name=mapping.to_impl(name), strict=mapping.to_impl(strict), timeout=mapping.to_impl(timeout))))

    def text_content(self, selector: str, strict: Optional[bool]=None, timeout: Optional[float]=None) -> Optional[str]:
        return mapping.from_impl(self._run(self._impl.text_content(selector=mapping.to_impl(selector), strict=mapping.to_impl(strict), timeout=mapping.to_impl(timeout))))

    def inner_text(self, selector: str, strict: Optional[bool]=None, timeout: Optional[float]=None) -> str:
        return mapping.from_impl(self._run(self._impl.inner_text(selector=mapping.to_impl(selector), strict=mapping.to_impl(strict), timeout=mapping.to_impl(timeout))))

    def inner_html(self, selector: str, strict: Optional[bool]=None, timeout: Optional[float]=None) -> str:
        return mapping.from_impl(self._run(self._impl.inner_html(selector=mapping.to_impl(selector), strict=mapping.to_impl(strict), timeout=mapping.to_impl(timeout))))

    def input_value(self, selector: str, strict: Optional[bool]=None, timeout: Optional[float]=None) -> str:
        return mapping.from_impl(self._run(self._impl.input_value(selector=mapping.to_impl(selector), strict=mapping.to_impl(strict), timeout=mapping.to_impl(timeout))))

    def is_checked(self, selector: str, strict: Optional[bool]=None, timeout: Optional[float]=None) -> bool:
        return mapping.from_impl(self._run(self._impl.is_checked(selector=mapping.to_impl(selector), strict=mapping.to_impl(strict), timeout=mapping.to_impl(timeout))))

    def is_disabled(self, selector: str, strict: Optional[bool]=None, timeout: Optional[float]=None) -> bool:
        return mapping.from_impl(self._run(self._impl.is_disabled(selector=mapping.to_impl(selector), strict=mapping.to_impl(strict), timeout=mapping.to_impl(timeout))))

    def is_editable(self, selector: str, strict: Optional[bool]=None, timeout: Optional[float]=None) -> bool:
        return mapping.from_impl(self._run(self._impl.is_editable(selector=mapping.to_impl(selector), strict=mapping.to_impl(strict), timeout=mapping.to_impl(timeout))))

    def is_enabled(self, selector: str, strict: Optional[bool]=None, timeout: Optional[float]=None) -> bool:
        return mapping.from_impl(self._run(self._impl.is_enabled(selector=mapping.to_impl(selector), strict=mapping.to_impl(strict), timeout=mapping.to_impl(timeout))))

    def is_hidden(self, selector: str, strict: Optional[bool]=None, timeout: Optional[float]=None) -> bool:
        return mapping.from_impl(self._run(self._impl.is_hidden(selector=mapping.to_impl(selector), strict=mapping.to_impl(strict), timeout=mapping.to_impl(timeout))))

    def is_visible(self, selector: str, strict: Optional[bool]=None, timeout: Optional[float]=None) -> bool:
        return mapping.from_impl(self._run(self._impl.is_visible(selector=mapping.to_impl(selector), strict=mapping.to_impl(strict), timeout=mapping.to_impl(timeout))))

class Locator(SyncBase):
    """A way to find element(s) on the page at any moment."""
    _impl: _LocatorImpl

    @property
    def page(self) -> Page:
        return mapping.from_impl(self._impl.page)

    @property
    def selector(self) -> str:
        """The resolved selector string, in Playwright's ``>>`` syntax."""
        return mapping.from_impl(self._impl.selector)

    def locator(self, selector_or_locator: Union[str, Locator], has_text: Optional[TextMatch]=None, has_not_text: Optional[TextMatch]=None, has: Optional[Locator]=None, has_not: Optional[Locator]=None) -> Locator:
        return mapping.from_impl(self._impl.locator(selector_or_locator=mapping.to_impl(selector_or_locator), has_text=mapping.to_impl(has_text), has_not_text=mapping.to_impl(has_not_text), has=mapping.to_impl(has), has_not=mapping.to_impl(has_not)))

    def get_by_alt_text(self, text: TextMatch, exact: Optional[bool]=None) -> Locator:
        return mapping.from_impl(self._impl.get_by_alt_text(text=mapping.to_impl(text), exact=mapping.to_impl(exact)))

    def get_by_label(self, text: TextMatch, exact: Optional[bool]=None) -> Locator:
        return mapping.from_impl(self._impl.get_by_label(text=mapping.to_impl(text), exact=mapping.to_impl(exact)))

    def get_by_placeholder(self, text: TextMatch, exact: Optional[bool]=None) -> Locator:
        return mapping.from_impl(self._impl.get_by_placeholder(text=mapping.to_impl(text), exact=mapping.to_impl(exact)))

    def get_by_role(self, role: str, **kwargs: Any) -> Locator:
        return mapping.from_impl(self._impl.get_by_role(role=mapping.to_impl(role), **kwargs))

    def get_by_test_id(self, test_id: TextMatch) -> Locator:
        return mapping.from_impl(self._impl.get_by_test_id(test_id=mapping.to_impl(test_id)))

    def get_by_text(self, text: TextMatch, exact: Optional[bool]=None) -> Locator:
        return mapping.from_impl(self._impl.get_by_text(text=mapping.to_impl(text), exact=mapping.to_impl(exact)))

    def get_by_title(self, text: TextMatch, exact: Optional[bool]=None) -> Locator:
        return mapping.from_impl(self._impl.get_by_title(text=mapping.to_impl(text), exact=mapping.to_impl(exact)))

    def frame_locator(self, selector: str) -> FrameLocator:
        return mapping.from_impl(self._impl.frame_locator(selector=mapping.to_impl(selector)))

    @property
    def first(self) -> Locator:
        return mapping.from_impl(self._impl.first)

    @property
    def last(self) -> Locator:
        return mapping.from_impl(self._impl.last)

    def nth(self, index: int) -> Locator:
        return mapping.from_impl(self._impl.nth(index=mapping.to_impl(index)))

    @property
    def content_frame(self) -> FrameLocator:
        return mapping.from_impl(self._impl.content_frame)

    def describe(self, description: str) -> Locator:
        return mapping.from_impl(self._impl.describe(description=mapping.to_impl(description)))

    @property
    def description(self) -> Optional[str]:
        return mapping.from_impl(self._impl.description)

    def filter(self, has_text: Optional[TextMatch]=None, has_not_text: Optional[TextMatch]=None, has: Optional[Locator]=None, has_not: Optional[Locator]=None, visible: Optional[bool]=None) -> Locator:
        return mapping.from_impl(self._impl.filter(has_text=mapping.to_impl(has_text), has_not_text=mapping.to_impl(has_not_text), has=mapping.to_impl(has), has_not=mapping.to_impl(has_not), visible=mapping.to_impl(visible)))

    def or_(self, locator: Locator) -> Locator:
        return mapping.from_impl(self._impl.or_(locator=mapping.to_impl(locator)))

    def and_(self, locator: Locator) -> Locator:
        return mapping.from_impl(self._impl.and_(locator=mapping.to_impl(locator)))

    def element_handle(self, timeout: Optional[float]=None) -> ElementHandle:
        return mapping.from_impl(self._run(self._impl.element_handle(timeout=mapping.to_impl(timeout))))

    def element_handles(self) -> list[ElementHandle]:
        return mapping.from_impl(self._run(self._impl.element_handles()))

    def all(self) -> list[Locator]:
        return mapping.from_impl(self._run(self._impl.all()))

    def count(self) -> int:
        return mapping.from_impl(self._run(self._impl.count()))

    def all_inner_texts(self) -> list[str]:
        return mapping.from_impl(self._run(self._impl.all_inner_texts()))

    def all_text_contents(self) -> list[str]:
        return mapping.from_impl(self._run(self._impl.all_text_contents()))

    def wait_for(self, timeout: Optional[float]=None, state: str='visible') -> None:
        self._run(self._impl.wait_for(timeout=mapping.to_impl(timeout), state=mapping.to_impl(state)))

    def wait_for_function(self, expression: str, arg: Any=None, timeout: Optional[float]=None, polling: Any=None) -> Any:
        return mapping.from_impl(self._run(self._impl.wait_for_function(expression=mapping.to_impl(expression), arg=mapping.to_impl(arg), timeout=mapping.to_impl(timeout), polling=mapping.to_impl(polling))))

    def evaluate(self, expression: str, arg: Any=None, timeout: Optional[float]=None) -> Any:
        return mapping.from_impl(self._run(self._impl.evaluate(expression=mapping.to_impl(expression), arg=mapping.to_impl(arg), timeout=mapping.to_impl(timeout))))

    def evaluate_handle(self, expression: str, arg: Any=None, timeout: Optional[float]=None) -> Any:
        return mapping.from_impl(self._run(self._impl.evaluate_handle(expression=mapping.to_impl(expression), arg=mapping.to_impl(arg), timeout=mapping.to_impl(timeout))))

    def evaluate_all(self, expression: str, arg: Any=None) -> Any:
        return mapping.from_impl(self._run(self._impl.evaluate_all(expression=mapping.to_impl(expression), arg=mapping.to_impl(arg))))

    def click(self, **kwargs: Any) -> None:
        self._run(self._impl.click(**kwargs))

    def dblclick(self, **kwargs: Any) -> None:
        self._run(self._impl.dblclick(**kwargs))

    def hover(self, **kwargs: Any) -> None:
        self._run(self._impl.hover(**kwargs))

    def tap(self, **kwargs: Any) -> None:
        self._run(self._impl.tap(**kwargs))

    def fill(self, value: str, timeout: Optional[float]=None, force: Optional[bool]=None, no_wait_after: Optional[bool]=None) -> None:
        self._run(self._impl.fill(value=mapping.to_impl(value), timeout=mapping.to_impl(timeout), force=mapping.to_impl(force), no_wait_after=mapping.to_impl(no_wait_after)))

    def clear(self, timeout: Optional[float]=None, force: Optional[bool]=None, no_wait_after: Optional[bool]=None) -> None:
        self._run(self._impl.clear(timeout=mapping.to_impl(timeout), force=mapping.to_impl(force), no_wait_after=mapping.to_impl(no_wait_after)))

    def type(self, text: str, delay: Optional[float]=None, timeout: Optional[float]=None, no_wait_after: Optional[bool]=None) -> None:
        self._run(self._impl.type(text=mapping.to_impl(text), delay=mapping.to_impl(delay), timeout=mapping.to_impl(timeout), no_wait_after=mapping.to_impl(no_wait_after)))

    def press_sequentially(self, text: str, delay: Optional[float]=None, timeout: Optional[float]=None, no_wait_after: Optional[bool]=None) -> None:
        self._run(self._impl.press_sequentially(text=mapping.to_impl(text), delay=mapping.to_impl(delay), timeout=mapping.to_impl(timeout), no_wait_after=mapping.to_impl(no_wait_after)))

    def press(self, key: str, delay: Optional[float]=None, timeout: Optional[float]=None, no_wait_after: Optional[bool]=None) -> None:
        self._run(self._impl.press(key=mapping.to_impl(key), delay=mapping.to_impl(delay), timeout=mapping.to_impl(timeout), no_wait_after=mapping.to_impl(no_wait_after)))

    def focus(self, timeout: Optional[float]=None) -> None:
        self._run(self._impl.focus(timeout=mapping.to_impl(timeout)))

    def blur(self, timeout: Optional[float]=None) -> None:
        self._run(self._impl.blur(timeout=mapping.to_impl(timeout)))

    def check(self, **kwargs: Any) -> None:
        self._run(self._impl.check(**kwargs))

    def uncheck(self, **kwargs: Any) -> None:
        self._run(self._impl.uncheck(**kwargs))

    def set_checked(self, checked: bool, **kwargs: Any) -> None:
        self._run(self._impl.set_checked(checked=mapping.to_impl(checked), **kwargs))

    def select_option(self, value: Union[str, Sequence[str], None]=None, *, index: Union[int, Sequence[int], None]=None, label: Union[str, Sequence[str], None]=None, element: Union[ElementHandle, Sequence[ElementHandle], None]=None, timeout: Optional[float]=None, force: Optional[bool]=None, no_wait_after: Optional[bool]=None) -> list[str]:
        return mapping.from_impl(self._run(self._impl.select_option(value=mapping.to_impl(value), index=mapping.to_impl(index), label=mapping.to_impl(label), element=mapping.to_impl(element), timeout=mapping.to_impl(timeout), force=mapping.to_impl(force), no_wait_after=mapping.to_impl(no_wait_after))))

    def select_text(self, force: Optional[bool]=None, timeout: Optional[float]=None) -> None:
        self._run(self._impl.select_text(force=mapping.to_impl(force), timeout=mapping.to_impl(timeout)))

    def set_input_files(self, files: Union[str, Path, FilePayload, Sequence[Union[str, Path]], Sequence[FilePayload]], timeout: Optional[float]=None, no_wait_after: Optional[bool]=None) -> None:
        self._run(self._impl.set_input_files(files=mapping.to_impl(files), timeout=mapping.to_impl(timeout), no_wait_after=mapping.to_impl(no_wait_after)))

    def dispatch_event(self, type: str, event_init: Optional[dict[str, Any]]=None, timeout: Optional[float]=None) -> None:
        self._run(self._impl.dispatch_event(type=mapping.to_impl(type), event_init=mapping.to_impl(event_init), timeout=mapping.to_impl(timeout)))

    def scroll_into_view_if_needed(self, timeout: Optional[float]=None) -> None:
        self._run(self._impl.scroll_into_view_if_needed(timeout=mapping.to_impl(timeout)))

    def drag_to(self, target: Locator, **kwargs: Any) -> None:
        self._run(self._impl.drag_to(target=mapping.to_impl(target), **kwargs))

    def highlight(self) -> None:
        self._run(self._impl.highlight())

    def hide_highlight(self) -> None:
        self._run(self._impl.hide_highlight())

    def get_attribute(self, name: str, timeout: Optional[float]=None) -> Optional[str]:
        return mapping.from_impl(self._run(self._impl.get_attribute(name=mapping.to_impl(name), timeout=mapping.to_impl(timeout))))

    def text_content(self, timeout: Optional[float]=None) -> Optional[str]:
        return mapping.from_impl(self._run(self._impl.text_content(timeout=mapping.to_impl(timeout))))

    def inner_text(self, timeout: Optional[float]=None) -> str:
        return mapping.from_impl(self._run(self._impl.inner_text(timeout=mapping.to_impl(timeout))))

    def inner_html(self, timeout: Optional[float]=None) -> str:
        return mapping.from_impl(self._run(self._impl.inner_html(timeout=mapping.to_impl(timeout))))

    def input_value(self, timeout: Optional[float]=None) -> str:
        return mapping.from_impl(self._run(self._impl.input_value(timeout=mapping.to_impl(timeout))))

    def is_checked(self, timeout: Optional[float]=None) -> bool:
        return mapping.from_impl(self._run(self._impl.is_checked(timeout=mapping.to_impl(timeout))))

    def is_disabled(self, timeout: Optional[float]=None) -> bool:
        return mapping.from_impl(self._run(self._impl.is_disabled(timeout=mapping.to_impl(timeout))))

    def is_editable(self, timeout: Optional[float]=None) -> bool:
        return mapping.from_impl(self._run(self._impl.is_editable(timeout=mapping.to_impl(timeout))))

    def is_enabled(self, timeout: Optional[float]=None) -> bool:
        return mapping.from_impl(self._run(self._impl.is_enabled(timeout=mapping.to_impl(timeout))))

    def is_hidden(self, timeout: Optional[float]=None) -> bool:
        return mapping.from_impl(self._run(self._impl.is_hidden(timeout=mapping.to_impl(timeout))))

    def is_visible(self, timeout: Optional[float]=None) -> bool:
        return mapping.from_impl(self._run(self._impl.is_visible(timeout=mapping.to_impl(timeout))))

    def bounding_box(self, timeout: Optional[float]=None) -> Optional[dict[str, float]]:
        return mapping.from_impl(self._run(self._impl.bounding_box(timeout=mapping.to_impl(timeout))))

    def screenshot(self, **kwargs: Any) -> bytes:
        return mapping.from_impl(self._run(self._impl.screenshot(**kwargs)))

class FrameLocator(SyncBase):
    """Entry point to a child frame found by a selector, with the same lazy semantics."""
    _impl: _FrameLocatorImpl

    def locator(self, selector_or_locator: Union[str, Locator], has_text: Optional[TextMatch]=None, has_not_text: Optional[TextMatch]=None, has: Optional[Locator]=None, has_not: Optional[Locator]=None) -> Locator:
        return mapping.from_impl(self._impl.locator(selector_or_locator=mapping.to_impl(selector_or_locator), has_text=mapping.to_impl(has_text), has_not_text=mapping.to_impl(has_not_text), has=mapping.to_impl(has), has_not=mapping.to_impl(has_not)))

    def get_by_alt_text(self, text: TextMatch, exact: Optional[bool]=None) -> Locator:
        return mapping.from_impl(self._impl.get_by_alt_text(text=mapping.to_impl(text), exact=mapping.to_impl(exact)))

    def get_by_label(self, text: TextMatch, exact: Optional[bool]=None) -> Locator:
        return mapping.from_impl(self._impl.get_by_label(text=mapping.to_impl(text), exact=mapping.to_impl(exact)))

    def get_by_placeholder(self, text: TextMatch, exact: Optional[bool]=None) -> Locator:
        return mapping.from_impl(self._impl.get_by_placeholder(text=mapping.to_impl(text), exact=mapping.to_impl(exact)))

    def get_by_role(self, role: str, **kwargs: Any) -> Locator:
        return mapping.from_impl(self._impl.get_by_role(role=mapping.to_impl(role), **kwargs))

    def get_by_test_id(self, test_id: TextMatch) -> Locator:
        return mapping.from_impl(self._impl.get_by_test_id(test_id=mapping.to_impl(test_id)))

    def get_by_text(self, text: TextMatch, exact: Optional[bool]=None) -> Locator:
        return mapping.from_impl(self._impl.get_by_text(text=mapping.to_impl(text), exact=mapping.to_impl(exact)))

    def get_by_title(self, text: TextMatch, exact: Optional[bool]=None) -> Locator:
        return mapping.from_impl(self._impl.get_by_title(text=mapping.to_impl(text), exact=mapping.to_impl(exact)))

    def frame_locator(self, selector: str) -> FrameLocator:
        return mapping.from_impl(self._impl.frame_locator(selector=mapping.to_impl(selector)))

    @property
    def first(self) -> FrameLocator:
        return mapping.from_impl(self._impl.first)

    @property
    def last(self) -> FrameLocator:
        return mapping.from_impl(self._impl.last)

    def nth(self, index: int) -> FrameLocator:
        return mapping.from_impl(self._impl.nth(index=mapping.to_impl(index)))

    @property
    def owner(self) -> Locator:
        return mapping.from_impl(self._impl.owner)

class JSHandle(SyncBase):
    """A reference to a JavaScript object living in a frame."""
    _impl: _JSHandleImpl

    @property
    def object_id(self) -> str:
        return mapping.from_impl(self._impl.object_id)

    def evaluate(self, expression: str, arg: Any=None) -> Any:
        return mapping.from_impl(self._run(self._impl.evaluate(expression=mapping.to_impl(expression), arg=mapping.to_impl(arg))))

    def evaluate_handle(self, expression: str, arg: Any=None) -> JSHandle:
        return mapping.from_impl(self._run(self._impl.evaluate_handle(expression=mapping.to_impl(expression), arg=mapping.to_impl(arg))))

    def get_property(self, property_name: str) -> JSHandle:
        return mapping.from_impl(self._run(self._impl.get_property(property_name=mapping.to_impl(property_name))))

    def get_properties(self) -> dict[str, JSHandle]:
        return mapping.from_impl(self._run(self._impl.get_properties()))

    def as_element(self) -> Optional[ElementHandle]:
        return mapping.from_impl(self._impl.as_element())

    def dispose(self) -> None:
        self._run(self._impl.dispose())

    def json_value(self) -> Any:
        return mapping.from_impl(self._run(self._impl.json_value()))

class ElementHandle(SyncBase):
    """A reference to a DOM element, wrapping a pydoll WebElement."""
    _impl: _ElementHandleImpl

    @property
    def web_element(self) -> WebElement:
        """The underlying pydoll element, for code that mixes both APIs."""
        return mapping.from_impl(self._impl.web_element)

    @property
    def object_id(self) -> str:
        return mapping.from_impl(self._impl.object_id)

    def as_element(self) -> Optional[ElementHandle]:
        return mapping.from_impl(self._impl.as_element())

    def evaluate(self, expression: str, arg: Any=None) -> Any:
        return mapping.from_impl(self._run(self._impl.evaluate(expression=mapping.to_impl(expression), arg=mapping.to_impl(arg))))

    def evaluate_handle(self, expression: str, arg: Any=None) -> JSHandle:
        return mapping.from_impl(self._run(self._impl.evaluate_handle(expression=mapping.to_impl(expression), arg=mapping.to_impl(arg))))

    def json_value(self) -> Any:
        return mapping.from_impl(self._run(self._impl.json_value()))

    def dispose(self) -> None:
        self._run(self._impl.dispose())

    @property
    def page(self) -> Page:
        return mapping.from_impl(self._impl.page)

    def owner_frame(self) -> Optional[Frame]:
        return mapping.from_impl(self._run(self._impl.owner_frame()))

    def content_frame(self) -> Optional[Frame]:
        return mapping.from_impl(self._run(self._impl.content_frame()))

    def get_attribute(self, name: str) -> Optional[str]:
        return mapping.from_impl(self._run(self._impl.get_attribute(name=mapping.to_impl(name))))

    def text_content(self) -> Optional[str]:
        return mapping.from_impl(self._run(self._impl.text_content()))

    def inner_text(self) -> str:
        return mapping.from_impl(self._run(self._impl.inner_text()))

    def inner_html(self) -> str:
        return mapping.from_impl(self._run(self._impl.inner_html()))

    def input_value(self, timeout: Optional[float]=None) -> str:
        return mapping.from_impl(self._run(self._impl.input_value(timeout=mapping.to_impl(timeout))))

    def is_checked(self) -> bool:
        return mapping.from_impl(self._run(self._impl.is_checked()))

    def is_disabled(self) -> bool:
        return mapping.from_impl(self._run(self._impl.is_disabled()))

    def is_editable(self) -> bool:
        return mapping.from_impl(self._run(self._impl.is_editable()))

    def is_enabled(self) -> bool:
        return mapping.from_impl(self._run(self._impl.is_enabled()))

    def is_hidden(self) -> bool:
        return mapping.from_impl(self._run(self._impl.is_hidden()))

    def is_visible(self) -> bool:
        return mapping.from_impl(self._run(self._impl.is_visible()))

    def dispatch_event(self, type: str, event_init: Optional[dict[str, Any]]=None) -> None:
        self._run(self._impl.dispatch_event(type=mapping.to_impl(type), event_init=mapping.to_impl(event_init)))

    def scroll_into_view_if_needed(self, timeout: Optional[float]=None) -> None:
        self._run(self._impl.scroll_into_view_if_needed(timeout=mapping.to_impl(timeout)))

    def hover(self, **kwargs: Any) -> None:
        self._run(self._impl.hover(**kwargs))

    def click(self, **kwargs: Any) -> None:
        self._run(self._impl.click(**kwargs))

    def dblclick(self, **kwargs: Any) -> None:
        self._run(self._impl.dblclick(**kwargs))

    def tap(self, **kwargs: Any) -> None:
        self._run(self._impl.tap(**kwargs))

    def select_option(self, value: Union[str, Sequence[str], None]=None, *, index: Union[int, Sequence[int], None]=None, label: Union[str, Sequence[str], None]=None, element: Union[ElementHandle, Sequence[ElementHandle], None]=None, timeout: Optional[float]=None, force: Optional[bool]=None) -> list[str]:
        return mapping.from_impl(self._run(self._impl.select_option(value=mapping.to_impl(value), index=mapping.to_impl(index), label=mapping.to_impl(label), element=mapping.to_impl(element), timeout=mapping.to_impl(timeout), force=mapping.to_impl(force))))

    def fill(self, value: str, timeout: Optional[float]=None, force: Optional[bool]=None) -> None:
        self._run(self._impl.fill(value=mapping.to_impl(value), timeout=mapping.to_impl(timeout), force=mapping.to_impl(force)))

    def select_text(self, timeout: Optional[float]=None, force: Optional[bool]=None) -> None:
        self._run(self._impl.select_text(timeout=mapping.to_impl(timeout), force=mapping.to_impl(force)))

    def set_input_files(self, files: Union[str, Path, FilePayload, Sequence[Union[str, Path]], Sequence[FilePayload]], timeout: Optional[float]=None) -> None:
        self._run(self._impl.set_input_files(files=mapping.to_impl(files), timeout=mapping.to_impl(timeout)))

    def focus(self) -> None:
        self._run(self._impl.focus())

    def type(self, text: str, delay: Optional[float]=None, timeout: Optional[float]=None) -> None:
        self._run(self._impl.type(text=mapping.to_impl(text), delay=mapping.to_impl(delay), timeout=mapping.to_impl(timeout)))

    def press(self, key: str, delay: Optional[float]=None, timeout: Optional[float]=None) -> None:
        self._run(self._impl.press(key=mapping.to_impl(key), delay=mapping.to_impl(delay), timeout=mapping.to_impl(timeout)))

    def set_checked(self, checked: bool, **kwargs: Any) -> None:
        self._run(self._impl.set_checked(checked=mapping.to_impl(checked), **kwargs))

    def check(self, **kwargs: Any) -> None:
        self._run(self._impl.check(**kwargs))

    def uncheck(self, **kwargs: Any) -> None:
        self._run(self._impl.uncheck(**kwargs))

    def bounding_box(self) -> Optional[dict[str, float]]:
        return mapping.from_impl(self._run(self._impl.bounding_box()))

    def screenshot(self, **kwargs: Any) -> bytes:
        return mapping.from_impl(self._run(self._impl.screenshot(**kwargs)))

    def query_selector(self, selector: str) -> Optional[ElementHandle]:
        return mapping.from_impl(self._run(self._impl.query_selector(selector=mapping.to_impl(selector))))

    def query_selector_all(self, selector: str) -> list[ElementHandle]:
        return mapping.from_impl(self._run(self._impl.query_selector_all(selector=mapping.to_impl(selector))))

    def eval_on_selector(self, selector: str, expression: str, arg: Any=None) -> Any:
        return mapping.from_impl(self._run(self._impl.eval_on_selector(selector=mapping.to_impl(selector), expression=mapping.to_impl(expression), arg=mapping.to_impl(arg))))

    def eval_on_selector_all(self, selector: str, expression: str, arg: Any=None) -> Any:
        return mapping.from_impl(self._run(self._impl.eval_on_selector_all(selector=mapping.to_impl(selector), expression=mapping.to_impl(expression), arg=mapping.to_impl(arg))))

    def wait_for_element_state(self, state: str, timeout: Optional[float]=None) -> None:
        self._run(self._impl.wait_for_element_state(state=mapping.to_impl(state), timeout=mapping.to_impl(timeout)))

    def wait_for_selector(self, selector: str, **kwargs: Any) -> Optional[ElementHandle]:
        return mapping.from_impl(self._run(self._impl.wait_for_selector(selector=mapping.to_impl(selector), **kwargs)))

    def get_property(self, property_name: str) -> JSHandle:
        return mapping.from_impl(self._run(self._impl.get_property(property_name=mapping.to_impl(property_name))))

    def get_properties(self) -> dict[str, JSHandle]:
        return mapping.from_impl(self._run(self._impl.get_properties()))

class Keyboard(SyncBase):
    """``page.keyboard``: low-level key events routed to the focused element."""
    _impl: _KeyboardImpl

    def down(self, key: str) -> None:
        self._run(self._impl.down(key=mapping.to_impl(key)))

    def up(self, key: str) -> None:
        self._run(self._impl.up(key=mapping.to_impl(key)))

    def insert_text(self, text: str) -> None:
        self._run(self._impl.insert_text(text=mapping.to_impl(text)))

    def type(self, text: str, delay: Optional[float]=None) -> None:
        self._run(self._impl.type(text=mapping.to_impl(text), delay=mapping.to_impl(delay)))

    def press(self, key: str, delay: Optional[float]=None) -> None:
        self._run(self._impl.press(key=mapping.to_impl(key), delay=mapping.to_impl(delay)))

class Mouse(SyncBase):
    """``page.mouse``: pointer events in main-frame CSS pixels."""
    _impl: _MouseImpl

    def move(self, x: float, y: float, steps: Optional[int]=None) -> None:
        self._run(self._impl.move(x=mapping.to_impl(x), y=mapping.to_impl(y), steps=mapping.to_impl(steps)))

    def down(self, button: MouseButtonName='left', click_count: Optional[int]=None) -> None:
        self._run(self._impl.down(button=mapping.to_impl(button), click_count=mapping.to_impl(click_count)))

    def up(self, button: MouseButtonName='left', click_count: Optional[int]=None) -> None:
        self._run(self._impl.up(button=mapping.to_impl(button), click_count=mapping.to_impl(click_count)))

    def click(self, x: float, y: float, delay: Optional[float]=None, button: MouseButtonName='left', click_count: Optional[int]=None) -> None:
        self._run(self._impl.click(x=mapping.to_impl(x), y=mapping.to_impl(y), delay=mapping.to_impl(delay), button=mapping.to_impl(button), click_count=mapping.to_impl(click_count)))

    def dblclick(self, x: float, y: float, delay: Optional[float]=None, button: MouseButtonName='left') -> None:
        self._run(self._impl.dblclick(x=mapping.to_impl(x), y=mapping.to_impl(y), delay=mapping.to_impl(delay), button=mapping.to_impl(button)))

    def wheel(self, delta_x: float, delta_y: float) -> None:
        self._run(self._impl.wheel(delta_x=mapping.to_impl(delta_x), delta_y=mapping.to_impl(delta_y)))

class Touchscreen(SyncBase):
    """``page.touchscreen``: a single-finger tap."""
    _impl: _TouchscreenImpl

    def tap(self, x: float, y: float) -> None:
        self._run(self._impl.tap(x=mapping.to_impl(x), y=mapping.to_impl(y)))

class Request(SyncBase):
    """One HTTP request issued by the page."""
    _impl: _RequestImpl

    @property
    def url(self) -> str:
        return mapping.from_impl(self._impl.url)

    @property
    def resource_type(self) -> str:
        return mapping.from_impl(self._impl.resource_type)

    @property
    def method(self) -> str:
        return mapping.from_impl(self._impl.method)

    @property
    def post_data(self) -> Optional[str]:
        return mapping.from_impl(self._impl.post_data)

    @property
    def post_data_json(self) -> Any:
        return mapping.from_impl(self._impl.post_data_json)

    @property
    def post_data_buffer(self) -> Optional[bytes]:
        return mapping.from_impl(self._impl.post_data_buffer)

    @property
    def headers(self) -> dict[str, str]:
        return mapping.from_impl(self._impl.headers)

    def all_headers(self) -> dict[str, str]:
        return mapping.from_impl(self._run(self._impl.all_headers()))

    def headers_array(self) -> list[dict[str, str]]:
        return mapping.from_impl(self._run(self._impl.headers_array()))

    def header_value(self, name: str) -> Optional[str]:
        return mapping.from_impl(self._run(self._impl.header_value(name=mapping.to_impl(name))))

    @property
    def frame(self) -> Frame:
        return mapping.from_impl(self._impl.frame)

    @property
    def service_worker(self) -> None:
        return mapping.from_impl(self._impl.service_worker)

    @property
    def redirected_from(self) -> Optional[Request]:
        return mapping.from_impl(self._impl.redirected_from)

    @property
    def redirected_to(self) -> Optional[Request]:
        return mapping.from_impl(self._impl.redirected_to)

    @property
    def failure(self) -> Optional[str]:
        return mapping.from_impl(self._impl.failure)

    @property
    def timing(self) -> dict[str, Any]:
        return mapping.from_impl(self._impl.timing)

    def is_navigation_request(self) -> bool:
        return mapping.from_impl(self._impl.is_navigation_request())

    def response(self) -> Optional[Response]:
        return mapping.from_impl(self._run(self._impl.response()))

    def sizes(self) -> dict[str, int]:
        return mapping.from_impl(self._run(self._impl.sizes()))

class Response(SyncBase):
    """The response to a request, with lazy body access."""
    _impl: _ResponseImpl

    @property
    def url(self) -> str:
        return mapping.from_impl(self._impl.url)

    @property
    def ok(self) -> bool:
        return mapping.from_impl(self._impl.ok)

    @property
    def status(self) -> int:
        return mapping.from_impl(self._impl.status)

    @property
    def status_text(self) -> str:
        return mapping.from_impl(self._impl.status_text)

    @property
    def headers(self) -> dict[str, str]:
        return mapping.from_impl(self._impl.headers)

    def all_headers(self) -> dict[str, str]:
        return mapping.from_impl(self._run(self._impl.all_headers()))

    def headers_array(self) -> list[dict[str, str]]:
        return mapping.from_impl(self._run(self._impl.headers_array()))

    def header_value(self, name: str) -> Optional[str]:
        return mapping.from_impl(self._run(self._impl.header_value(name=mapping.to_impl(name))))

    def header_values(self, name: str) -> list[str]:
        return mapping.from_impl(self._run(self._impl.header_values(name=mapping.to_impl(name))))

    @property
    def from_service_worker(self) -> bool:
        return mapping.from_impl(self._impl.from_service_worker)

    @property
    def request(self) -> Request:
        return mapping.from_impl(self._impl.request)

    @property
    def frame(self) -> Frame:
        return mapping.from_impl(self._impl.frame)

    def server_addr(self) -> Optional[dict[str, Any]]:
        return mapping.from_impl(self._run(self._impl.server_addr()))

    def security_details(self) -> Optional[dict[str, Any]]:
        return mapping.from_impl(self._run(self._impl.security_details()))

    def http_version(self) -> str:
        return mapping.from_impl(self._run(self._impl.http_version()))

    def finished(self) -> Optional[str]:
        return mapping.from_impl(self._run(self._impl.finished()))

    def body(self) -> bytes:
        return mapping.from_impl(self._run(self._impl.body()))

    def text(self) -> str:
        return mapping.from_impl(self._run(self._impl.text()))

    def json(self) -> Any:
        return mapping.from_impl(self._run(self._impl.json()))

class Route(SyncBase):
    """A paused request that a route handler decides how to serve."""
    _impl: _RouteImpl

    @property
    def request(self) -> Request:
        return mapping.from_impl(self._impl.request)

    def abort(self, error_code: Optional[str]=None) -> None:
        self._run(self._impl.abort(error_code=mapping.to_impl(error_code)))

    def continue_(self, url: Optional[str]=None, method: Optional[str]=None, headers: Optional[dict[str, str]]=None, post_data: Union[str, bytes, dict[str, Any], None]=None) -> None:
        self._run(self._impl.continue_(url=mapping.to_impl(url), method=mapping.to_impl(method), headers=mapping.to_impl(headers), post_data=mapping.to_impl(post_data)))

    def fallback(self, url: Optional[str]=None, method: Optional[str]=None, headers: Optional[dict[str, str]]=None, post_data: Union[str, bytes, dict[str, Any], None]=None) -> None:
        self._run(self._impl.fallback(url=mapping.to_impl(url), method=mapping.to_impl(method), headers=mapping.to_impl(headers), post_data=mapping.to_impl(post_data)))

    def fulfill(self, status: Optional[int]=None, headers: Optional[dict[str, str]]=None, body: Union[str, bytes, None]=None, json: Any=None, path: Union[str, Path, None]=None, content_type: Optional[str]=None, response: Optional[APIResponse]=None) -> None:
        self._run(self._impl.fulfill(status=mapping.to_impl(status), headers=mapping.to_impl(headers), body=mapping.to_impl(body), json=mapping.to_impl(json), path=mapping.to_impl(path), content_type=mapping.to_impl(content_type), response=mapping.to_impl(response)))

    def fetch(self, url: Optional[str]=None, method: Optional[str]=None, headers: Optional[dict[str, str]]=None, post_data: Union[str, bytes, dict[str, Any], None]=None, max_redirects: Optional[int]=None, max_retries: Optional[int]=None, timeout: Optional[float]=None) -> APIResponse:
        """Let the request reach the network and capture its response for ``fulfill``.

        The request continues with the given overrides and pauses again at the
        response stage, so the handler can inspect or rewrite the body before
        answering the page.
        """
        return mapping.from_impl(self._run(self._impl.fetch(url=mapping.to_impl(url), method=mapping.to_impl(method), headers=mapping.to_impl(headers), post_data=mapping.to_impl(post_data), max_redirects=mapping.to_impl(max_redirects), max_retries=mapping.to_impl(max_retries), timeout=mapping.to_impl(timeout))))

class APIResponse(SyncBase):
    """A fetched response that ``route.fulfill(response=...)`` can replay."""
    _impl: _APIResponseImpl

    @property
    def url(self) -> str:
        return mapping.from_impl(self._impl.url)

    @property
    def status(self) -> int:
        return mapping.from_impl(self._impl.status)

    @property
    def ok(self) -> bool:
        return mapping.from_impl(self._impl.ok)

    @property
    def headers(self) -> dict[str, str]:
        return mapping.from_impl(self._impl.headers)

    def body(self) -> bytes:
        return mapping.from_impl(self._run(self._impl.body()))

    def text(self) -> str:
        return mapping.from_impl(self._run(self._impl.text()))

    def json(self) -> Any:
        return mapping.from_impl(self._run(self._impl.json()))

class Dialog(SyncBase):
    """A JavaScript ``alert``, ``confirm``, ``prompt`` or ``beforeunload`` dialog."""
    _impl: _DialogImpl

    @property
    def type(self) -> str:
        return mapping.from_impl(self._impl.type)

    @property
    def message(self) -> str:
        return mapping.from_impl(self._impl.message)

    @property
    def default_value(self) -> str:
        return mapping.from_impl(self._impl.default_value)

    @property
    def page(self) -> Optional[Page]:
        return mapping.from_impl(self._impl.page)

    def accept(self, prompt_text: Optional[str]=None) -> None:
        self._run(self._impl.accept(prompt_text=mapping.to_impl(prompt_text)))

    def dismiss(self) -> None:
        self._run(self._impl.dismiss())

class ConsoleMessage(SyncBase):
    """A ``console.*`` call made by the page."""
    _impl: _ConsoleMessageImpl

    @property
    def type(self) -> str:
        return mapping.from_impl(self._impl.type)

    @property
    def text(self) -> str:
        return mapping.from_impl(self._impl.text)

    @property
    def args(self) -> list[Any]:
        return mapping.from_impl(self._impl.args)

    @property
    def location(self) -> dict[str, Any]:
        return mapping.from_impl(self._impl.location)

    @property
    def page(self) -> Optional[Page]:
        return mapping.from_impl(self._impl.page)

    @property
    def timestamp(self) -> Any:
        return mapping.from_impl(self._impl.timestamp)

class FileChooser(SyncBase):
    """A file input that opened its picker; call ``set_files`` to answer it."""
    _impl: _FileChooserImpl

    @property
    def page(self) -> Page:
        return mapping.from_impl(self._impl.page)

    @property
    def element(self) -> ElementHandle:
        return mapping.from_impl(self._impl.element)

    def is_multiple(self) -> bool:
        return mapping.from_impl(self._impl.is_multiple())

    def set_files(self, files: Union[str, Path, Sequence[Union[str, Path]], Any], timeout: Optional[float]=None) -> None:
        self._run(self._impl.set_files(files=mapping.to_impl(files), timeout=mapping.to_impl(timeout)))

class Download(SyncBase):
    """A download that started in the page; the file lands in the context's download directory."""
    _impl: _DownloadImpl

    @property
    def page(self) -> Page:
        return mapping.from_impl(self._impl.page)

    @property
    def url(self) -> str:
        return mapping.from_impl(self._impl.url)

    @property
    def suggested_filename(self) -> str:
        return mapping.from_impl(self._impl.suggested_filename)

    def failure(self) -> Optional[str]:
        return mapping.from_impl(self._run(self._impl.failure()))

    def path(self) -> Path:
        return mapping.from_impl(self._run(self._impl.path()))

    def save_as(self, path: Union[str, Path]) -> None:
        self._run(self._impl.save_as(path=mapping.to_impl(path)))

    def delete(self) -> None:
        self._run(self._impl.delete())

    def cancel(self) -> None:
        self._run(self._impl.cancel())

class EventInfo(SyncBase, Generic[T]):
    """Result placeholder returned by ``expect_*`` context managers."""
    _impl: _EventInfoImpl

    @property
    def value(self) -> T:
        return mapping.from_impl(self._run(self._impl.value))

    def is_done(self) -> bool:
        return mapping.from_impl(self._impl.is_done())

mapping.register(_PlaywrightImpl, Playwright)
mapping.register(_BrowserTypeImpl, BrowserType)
mapping.register(_SelectorsImpl, Selectors)
mapping.register(_PlaywrightContextManagerImpl, PlaywrightContextManager)
mapping.register(_BrowserImpl, Browser)
mapping.register(_BrowserContextImpl, BrowserContext)
mapping.register(_PageImpl, Page)
mapping.register(_FrameImpl, Frame)
mapping.register(_LocatorImpl, Locator)
mapping.register(_FrameLocatorImpl, FrameLocator)
mapping.register(_JSHandleImpl, JSHandle)
mapping.register(_ElementHandleImpl, ElementHandle)
mapping.register(_KeyboardImpl, Keyboard)
mapping.register(_MouseImpl, Mouse)
mapping.register(_TouchscreenImpl, Touchscreen)
mapping.register(_RequestImpl, Request)
mapping.register(_ResponseImpl, Response)
mapping.register(_RouteImpl, Route)
mapping.register(_APIResponseImpl, APIResponse)
mapping.register(_DialogImpl, Dialog)
mapping.register(_ConsoleMessageImpl, ConsoleMessage)
mapping.register(_FileChooserImpl, FileChooser)
mapping.register(_DownloadImpl, Download)
mapping.register(_EventInfoImpl, EventInfo)


def sync_playwright() -> PlaywrightContextManager:
    """``with sync_playwright() as p:`` entry point."""
    from pydoll.playwright._playwright import async_playwright  # noqa: PLC0415

    return PlaywrightContextManager(async_playwright())

__all__ = ['Playwright', 'BrowserType', 'Selectors', 'PlaywrightContextManager', 'Browser', 'BrowserContext', 'Page', 'Frame', 'Locator', 'FrameLocator', 'JSHandle', 'ElementHandle', 'Keyboard', 'Mouse', 'Touchscreen', 'Request', 'Response', 'Route', 'APIResponse', 'Dialog', 'ConsoleMessage', 'FileChooser', 'Download', 'EventInfo', 'sync_playwright']
