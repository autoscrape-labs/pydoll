"""Synchronous facades over pydoll (generated, do not edit).

Regenerate with ``python scripts/generate_sync_api.py``.
"""

# ruff: noqa
# fmt: off
from __future__ import annotations

from contextlib import AbstractContextManager
from typing import Any, Generic, cast, overload

from pydoll.sync._runtime import SyncBase, mapping, run_sync

from pydoll.browser.chromium.chrome import Chrome as _ChromeImpl
from pydoll.browser.chromium.edge import Edge as _EdgeImpl
from pydoll.browser.tab import Tab as _TabImpl
from pydoll.browser.tab import DownloadHandle as _DownloadHandleImpl
from pydoll.browser.tab import RequestHandle as _RequestHandleImpl
from pydoll.browser.tab import ResponseHandle as _ResponseHandleImpl
from pydoll.elements.web_element import WebElement as _WebElementImpl
from pydoll.elements.shadow_root import ShadowRoot as _ShadowRootImpl
from pydoll.interactions.keyboard import Keyboard as _KeyboardImpl
from pydoll.interactions.mouse import Mouse as _MouseImpl
from pydoll.interactions.scroll import Scroll as _ScrollImpl
from pydoll.browser.requests.request import Request as _RequestImpl
from pydoll.browser.requests.response import Response as _ResponseImpl



import logging
import platform
from typing import TYPE_CHECKING
from pydoll.browser.chromium.base import Browser
from pydoll.browser.managers import ChromiumOptionsManager
from pydoll.exceptions import UnsupportedOS
from pydoll.utils import validate_browser_paths
from pydoll.browser.options import ChromiumOptions
import asyncio
import json
import os
import shutil
from abc import ABC, abstractmethod
from contextlib import suppress
from functools import partial
from typing import TYPE_CHECKING, Any, Awaitable, Callable, overload
from urllib.parse import urlsplit, urlunsplit
from pydoll.browser.managers import BrowserProcessManager, ProxyManager, TempDirectoryManager
from pydoll.commands import BrowserCommands, EmulationCommands, FetchCommands, RuntimeCommands, StorageCommands, TargetCommands
from pydoll.connection import ConnectionHandler
from pydoll.exceptions import BrowserNotRunning, CommandFailed, FailedToStartBrowser, InvalidConnectionPort, InvalidWebSocketAddress, MissingTargetOrWebSocket, NoValidTabFound
from pydoll.protocol.browser.types import DownloadBehavior
from pydoll.protocol.fetch.events import FetchEvent
from pydoll.protocol.fetch.types import AuthChallengeResponseType
from pydoll.protocol.target.events import TargetEvent
from pydoll.protocol.target.types import FilterEntry
from pydoll.utils import PollInterval, find_free_port
from pydoll.utils.fingerprint_builder import build_fingerprint_worker_js
from pydoll.utils.user_agent_parser import ParsedUserAgent, UserAgentParser
from tempfile import TemporaryDirectory
from pydoll.browser.interfaces import BrowserOptionsManager, Options
from pydoll.protocol.base import Command, T_CommandParams, T_CommandResponse
from pydoll.protocol.browser.methods import GetVersionResponse, GetVersionResult, GetWindowForTargetResponse
from pydoll.protocol.browser.types import Bounds, PermissionType
from pydoll.protocol.fetch.events import RequestPausedEvent
from pydoll.protocol.fetch.types import HeaderEntry
from pydoll.protocol.fingerprint.types import FingerprintConfig
from pydoll.protocol.network.types import Cookie, CookieParam, ErrorReason, RequestMethod, ResourceType
from pydoll.protocol.storage.methods import GetCookiesResponse
from pydoll.protocol.target.methods import CreateBrowserContextResponse, CreateTargetResponse, GetBrowserContextsResponse, GetTargetsResponse
from pydoll.protocol.target.types import TargetInfo
from pydoll.browser.options import Options
import base64 as _b64
import contextlib
import io
import zipfile
from contextlib import asynccontextmanager
from pathlib import Path
from tempfile import mkdtemp
from typing import TYPE_CHECKING, Any, AsyncGenerator, Awaitable, Callable, TypeVar, cast, overload
import aiofiles
from pydoll.browser.fingerprint_applier import FingerprintApplier
from pydoll.commands import DomCommands, FetchCommands, NetworkCommands, PageCommands, RuntimeCommands, StorageCommands, TargetCommands
from pydoll.constants import PageLoadState
from pydoll.elements.mixins import FindElementsMixin
from pydoll.exceptions import CommandExecutionTimeout, CommandFailed, DownloadTimeout, InvalidFileExtension, InvalidScriptWithElement, InvalidTabInitialization, MissingScreenshotPath, NavigationError, NetworkEventsNotEnabled, NoDialogPresent, PageLoadTimeout, ScriptEvaluationError, TopLevelTargetRequired, WaitElementTimeout, WaitTimeout, WebSocketConnectionClosed
from pydoll.extractor.engine import ExtractionEngine
from pydoll.interactions.iframe import IFrameContext
from pydoll.protocol.browser.types import DownloadBehavior, DownloadProgressState
from pydoll.protocol.dom.types import Node, ShadowRootType
from pydoll.protocol.network.events import NetworkEvent
from pydoll.protocol.network.types import ResourceType
from pydoll.protocol.page.events import PageEvent
from pydoll.protocol.page.types import FrameResourceTree, ScreenshotFormat
from pydoll.protocol.runtime.methods import EvaluateResponse, SerializationOptions
from pydoll.protocol.runtime.types import ExceptionDetails, RemoteObject
from pydoll.utils import PollInterval, UrlPattern, decode_base64_to_bytes, has_return_outside_function, url_matcher
from pydoll.utils.bundle import build_asset_filename, collect_frame_resources, filter_fetchable_resources, inline_all_assets, rewrite_html_urls
from pydoll.extractor.model import ExtractionModel
from pydoll.protocol.base import EmptyResponse
from pydoll.protocol.browser.events import DownloadProgressEvent, DownloadWillBeginEvent
from pydoll.protocol.dom.methods import DescribeNodeResponse, GetDocumentResponse, ResolveNodeResponse
from pydoll.protocol.fetch.types import AuthChallengeResponseType, HeaderEntry, RequestStage
from pydoll.protocol.network.events import RequestWillBeSentEvent
from pydoll.protocol.network.methods import GetCookiesResponse as NetworkGetCookiesResponse
from pydoll.protocol.network.methods import GetResponseBodyResponse
from pydoll.protocol.network.types import Cookie, CookieParam, ErrorReason, RequestMethod
from pydoll.protocol.page.events import FileChooserOpenedEvent
from pydoll.protocol.page.methods import CaptureScreenshotResponse, GetResourceContentResponse, GetResourceTreeResponse, NavigateResponse, PrintToPDFResponse
from pydoll.protocol.runtime.methods import EvaluateResponse
from pydoll.protocol.target.methods import AttachToTargetResponse, GetTargetsResponse
T = TypeVar('T', bound='ExtractionModel')
from typing import TYPE_CHECKING, Sequence, cast, overload
from pydoll.commands import DomCommands, RuntimeCommands
from pydoll.connection.connection_handler import ConnectionHandler
from pydoll.constants import By, Scripts
from pydoll.elements.utils import SelectorParser
from pydoll.exceptions import CommandFailed, ElementNotFound, ScriptException, WaitElementTimeout
from pydoll.utils import PollInterval
from typing import Literal
from pydoll.protocol.dom.methods import DescribeNodeResponse
from pydoll.protocol.dom.types import Node
from pydoll.protocol.runtime.methods import CallFunctionOnParams, CallFunctionOnResponse, EvaluateParams, EvaluateResponse, GetPropertiesResponse
from pydoll.protocol.runtime.types import CallArgument
from pydoll.elements.mixins.find_elements_mixin import FindElementsMixin
from pydoll.commands import DomCommands, InputCommands, PageCommands, RuntimeCommands
from pydoll.constants import PRESSED_POINTER_FORCE, Scripts
from pydoll.exceptions import CommandExecutionTimeout, CommandFailed, ElementNotAFileInput, ElementNotFound, ElementNotInteractable, ElementNotVisible, InvalidFileExtension, InvalidIFrame, MissingScreenshotPath, ShadowRootNotFound, WaitElementTimeout, WebSocketConnectionClosed
from pydoll.interactions.iframe import IFrameContext, IFrameContextResolver
from pydoll.protocol.dom.types import Rect, ShadowRootType
from pydoll.protocol.input.types import MOUSE_BUTTON_MASK, MouseButton, MouseEventType
from pydoll.protocol.page.types import ScreenshotFormat, Viewport
from pydoll.protocol.runtime.methods import CallFunctionOnResponse, EvaluateResponse, GetPropertiesResponse, SerializationOptions
from pydoll.utils import PollInterval, decode_base64_to_bytes, extract_text_from_html, is_script_already_function
from pydoll.protocol.dom.methods import DescribeNodeResponse, GetBoxModelResponse, GetOuterHTMLResponse, ResolveNodeResponse
from pydoll.protocol.dom.types import Quad
from pydoll.protocol.page.methods import CaptureScreenshotResponse
from pydoll.protocol.runtime.methods import GetPropertiesResponse
from pydoll.commands import DomCommands
from pydoll.protocol.dom.types import ShadowRootType
from pydoll.protocol.dom.methods import GetOuterHTMLResponse
import random
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol, cast
from pydoll.commands import InputCommands
from pydoll.constants import CHAR_TO_KEY_INFO, DEFAULT_TYPO_PROBABILITY, QWERTY_NEIGHBORS, Key, TypoType
from pydoll.protocol.input.types import KeyEventType, KeyModifier
from pydoll.protocol.base import Command
from pydoll.interactions.keyboard import CommandExecutor
from pydoll.interactions.keyboard import TypoResult
from pydoll.interactions.keyboard import TimingConfig
from pydoll.interactions.keyboard import TypoConfig
import math
from pydoll.commands import InputCommands, RuntimeCommands
from pydoll.constants import PRESSED_POINTER_FORCE
from pydoll.interactions.utils import bezier_2d, fitts_duration, minimum_jerk, random_control_points
from pydoll.interactions.mouse import MouseTimingConfig
from pydoll.constants import Scripts, ScrollPosition
from pydoll.interactions.utils import CubicBezier
from pydoll.protocol.input.types import MouseEventType
from pydoll.interactions.scroll import ScrollTimingConfig
import json as jsonlib
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any, Callable, cast
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
from pydoll.browser.requests.har_recorder import HarCapture, HarRecorder
from pydoll.commands.runtime_commands import RuntimeCommands
from pydoll.constants import Scripts
from pydoll.exceptions import HTTPError
from pydoll.protocol.network.events import NetworkEvent, RequestWillBeSentEvent, RequestWillBeSentExtraInfoEvent, ResponseReceivedEvent, ResponseReceivedExtraInfoEvent, ResponseReceivedExtraInfoEventParams
from pydoll.protocol.network.types import CookieParam, ResourceType
from pydoll.protocol.network.events import RequestWillBeSentEventParams, RequestWillBeSentExtraInfoEventParams, ResponseReceivedEventParams
from typing import TYPE_CHECKING, Any
from pydoll.protocol.network.types import CookieParam





class Chrome(SyncBase):
    """Chrome browser implementation for CDP automation."""
    _impl: _ChromeImpl

    def __init__(self, options: ChromiumOptions | None=None, connection_port: int | None=None) -> None:
        """
        Initialize Chrome browser instance.

        Args:
            options: Chrome configuration options (default if None).
            connection_port: CDP WebSocket port (random if None).
        """
        super().__init__(_ChromeImpl(options=mapping.to_impl(options), connection_port=mapping.to_impl(connection_port)))

    def __enter__(self) -> Chrome:
        return mapping.from_impl(self._run(self._impl.__aenter__()))

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> Any:
        return self._run(self._impl.__aexit__(exc_type, exc, tb))

    @property
    def options(self) -> Options:
        return mapping.from_impl(self._impl.options)

    @options.setter
    def options(self, value: Options) -> None:
        self._impl.options = mapping.to_impl(value)

    def connect(self, ws_address: str) -> Tab:
        """
        Connect to browser using WebSocket address. When we set
        the _ws_address attribute, the connection handler will use
        this address instead of resolving it from the connection port.

        Args:
            ws_address: WebSocket address of the browser.

        Returns:
            The first tab in the list of opened tabs.

        Note:
            You are supposed to use this method only if you want to connect to a browser
            that is already running.
        """
        return mapping.from_impl(self._run(self._impl.connect(ws_address=mapping.to_impl(ws_address))))

    def start(self) -> Tab:
        """
        Start browser process and establish CDP connection.

        Returns:
            Initial tab for interaction.

        Raises:
            FailedToStartBrowser: If the browser fails to start or connect.
        """
        return mapping.from_impl(self._run(self._impl.start()))

    def stop(self):
        """
        Stop browser process and cleanup resources.

        Sends Browser.close command, terminates process, removes temp directories,
        and closes WebSocket connections.

        Raises:
            BrowserNotRunning: If the browser is not currently running.
        """
        return mapping.from_impl(self._run(self._impl.stop()))

    def close(self):
        """
        Closes the WebSocket connection and releases resources.
        """
        return mapping.from_impl(self._run(self._impl.close()))

    def create_browser_context(self, proxy_server: str | None=None, proxy_bypass_list: str | None=None) -> str:
        """
        Create isolated browser context (like incognito).

        Browser contexts provide isolated storage and don't share session data.
        Multiple contexts can exist simultaneously.

        Args:
            proxy_server: Optional proxy for this context only (scheme://host:port).
            proxy_bypass_list: Comma-separated hosts that bypass proxy.

        Returns:
            Browser context ID for use with other methods.
        """
        return mapping.from_impl(self._run(self._impl.create_browser_context(proxy_server=mapping.to_impl(proxy_server), proxy_bypass_list=mapping.to_impl(proxy_bypass_list))))

    def delete_browser_context(self, browser_context_id: str):
        """
        Delete browser context and all associated tabs/resources.

        Removes all storage (cookies, localStorage, etc.) and closes all tabs.
        The default browser context cannot be deleted.

        Note:
            Closes all associated tabs immediately.
        """
        return mapping.from_impl(self._run(self._impl.delete_browser_context(browser_context_id=mapping.to_impl(browser_context_id))))

    def get_browser_contexts(self) -> list[str]:
        """Get all browser context IDs including the default context."""
        return mapping.from_impl(self._run(self._impl.get_browser_contexts()))

    def new_tab(self, url: str='', browser_context_id: str | None=None) -> Tab:
        """
        Create new tab for page interaction.

        Args:
            url: Initial URL (about:blank if empty).
            browser_context_id: Context to create tab in (default if None).

        Returns:
            Tab instance for page navigation and element interaction.
        """
        return mapping.from_impl(self._run(self._impl.new_tab(url=mapping.to_impl(url), browser_context_id=mapping.to_impl(browser_context_id))))

    def get_targets(self) -> list[TargetInfo]:
        """
        Get all active targets/pages in browser.

        Targets include pages, service workers, shared workers, and browser process.
        Useful for debugging and managing multiple tabs.

        Returns:
            List of TargetInfo objects.
        """
        return mapping.from_impl(self._run(self._impl.get_targets()))

    def get_opened_tabs(self) -> list[Tab]:
        """
        Get all opened tabs that are not extensions and have the type 'page'.
        Tabs that are already opened will be returned as is. If a new target is opened,
        a new Tab instance will be created.

        Returns:
            List of Tab instances. The last tab is the most recent one.
        """
        return mapping.from_impl(self._run(self._impl.get_opened_tabs()))

    def get_tab_by_target(self, target: TargetInfo) -> Tab:
        return mapping.from_impl(self._run(self._impl.get_tab_by_target(target=mapping.to_impl(target))))

    def set_download_path(self, path: str, browser_context_id: str | None=None):
        """Set download directory path (convenience method for set_download_behavior)."""
        return mapping.from_impl(self._run(self._impl.set_download_path(path=mapping.to_impl(path), browser_context_id=mapping.to_impl(browser_context_id))))

    def set_download_behavior(self, behavior: DownloadBehavior, download_path: str | None=None, browser_context_id: str | None=None, events_enabled: bool=False):
        """
        Configure download handling.

        Args:
            behavior: ALLOW (save to path), DENY (cancel), or DEFAULT.
            download_path: Required if behavior is ALLOW.
            browser_context_id: Context to apply to (default if None).
            events_enabled: Generate download events for progress tracking.
        """
        return mapping.from_impl(self._run(self._impl.set_download_behavior(behavior=mapping.to_impl(behavior), download_path=mapping.to_impl(download_path), browser_context_id=mapping.to_impl(browser_context_id), events_enabled=mapping.to_impl(events_enabled))))

    def delete_all_cookies(self, browser_context_id: str | None=None):
        """Delete all cookies (session, persistent, third-party) from browser or context."""
        return mapping.from_impl(self._run(self._impl.delete_all_cookies(browser_context_id=mapping.to_impl(browser_context_id))))

    def set_cookies(self, cookies: list[CookieParam], browser_context_id: str | None=None):
        """Set multiple cookies in browser or context."""
        return mapping.from_impl(self._run(self._impl.set_cookies(cookies=mapping.to_impl(cookies), browser_context_id=mapping.to_impl(browser_context_id))))

    def get_cookies(self, browser_context_id: str | None=None) -> list[Cookie]:
        """Get all cookies from browser or context.

        Note:
            This method does not work with native incognito mode (--incognito flag).
            For incognito mode, use ``tab.get_cookies()`` instead.
        """
        return mapping.from_impl(self._run(self._impl.get_cookies(browser_context_id=mapping.to_impl(browser_context_id))))

    def get_version(self) -> GetVersionResult:
        """Get browser version and CDP protocol information."""
        return mapping.from_impl(self._run(self._impl.get_version()))

    def get_window_id_for_target(self, target_id: str) -> int:
        """Get window ID for target (used for window manipulation via CDP)."""
        return mapping.from_impl(self._run(self._impl.get_window_id_for_target(target_id=mapping.to_impl(target_id))))

    def get_window_id_for_tab(self, tab: Tab) -> int:
        """Get window ID for tab (convenience method)."""
        return mapping.from_impl(self._run(self._impl.get_window_id_for_tab(tab=mapping.to_impl(tab))))

    def get_window_id(self) -> int:
        """
        Get window ID for any valid tab.

        Raises:
            NoValidTabFound: If no valid attached tab can be found.
        """
        return mapping.from_impl(self._run(self._impl.get_window_id()))

    def set_window_maximized(self):
        """Maximize browser window (affects all tabs in window)."""
        return mapping.from_impl(self._run(self._impl.set_window_maximized()))

    def set_window_minimized(self):
        """Minimize browser window to taskbar/dock."""
        return mapping.from_impl(self._run(self._impl.set_window_minimized()))

    def set_window_bounds(self, bounds: Bounds):
        """
        Set window position and/or size.

        Args:
            bounds: Properties to modify (left, top, width, height, windowState).
                Only specified properties are changed.
        """
        return mapping.from_impl(self._run(self._impl.set_window_bounds(bounds=mapping.to_impl(bounds))))

    def grant_permissions(self, permissions: list[PermissionType], origin: str | None=None, browser_context_id: str | None=None):
        """
        Grant browser permissions (geolocation, notifications, camera, etc.).

        Bypasses normal permission prompts for automated testing.

        Args:
            permissions: Permissions to grant.
            origin: Origin to grant to (all origins if None).
            browser_context_id: Context to apply to (default if None).
        """
        return mapping.from_impl(self._run(self._impl.grant_permissions(permissions=mapping.to_impl(permissions), origin=mapping.to_impl(origin), browser_context_id=mapping.to_impl(browser_context_id))))

    def reset_permissions(self, browser_context_id: str | None=None):
        """Reset all permissions to defaults and restore prompting behavior."""
        return mapping.from_impl(self._run(self._impl.reset_permissions(browser_context_id=mapping.to_impl(browser_context_id))))

    def on(self, event_name: str, callback: Callable[[Any], Any], temporary: bool=False) -> int:
        """
        Register CDP event listener at browser level.

        Callback runs in background task to prevent blocking. Affects all pages/targets.

        Args:
            event_name: CDP event name (e.g., "Network.responseReceived").
            callback: Function called on event (sync or async).
            temporary: Remove after first invocation.

        Returns:
            Callback ID for removal.

        Note:
            For page-specific events, use Tab.on() instead.
        """
        return mapping.from_impl(self._run(cast('Any', self._impl).on(event_name=mapping.to_impl(event_name), callback=mapping.wrap_handler(callback), temporary=mapping.to_impl(temporary))))

    def remove_callback(self, callback_id: int):
        """Remove callback from browser."""
        return mapping.from_impl(self._run(self._impl.remove_callback(callback_id=mapping.to_impl(callback_id))))

    def enable_fetch_events(self, handle_auth_requests: bool=False, resource_type: ResourceType | None=None):
        """
        Enable network request interception via Fetch domain.

        Allows monitoring, modifying, or blocking requests before they're sent.
        All matching requests are paused until explicitly continued.

        Args:
            handle_auth_requests: Intercept authentication challenges.
            resource_type: Filter by type (XHR, Fetch, Document, etc.). Empty = all.

        Note:
            Paused requests must be continued or they will timeout.
        """
        return mapping.from_impl(self._run(self._impl.enable_fetch_events(handle_auth_requests=mapping.to_impl(handle_auth_requests), resource_type=mapping.to_impl(resource_type))))

    def disable_fetch_events(self):
        """Disable request interception and release any paused requests."""
        return mapping.from_impl(self._run(self._impl.disable_fetch_events()))

    def enable_runtime_events(self):
        """Enable runtime events."""
        return mapping.from_impl(self._run(self._impl.enable_runtime_events()))

    def disable_runtime_events(self):
        """Disable runtime events."""
        return mapping.from_impl(self._run(self._impl.disable_runtime_events()))

    def continue_request(self, request_id: str, url: str | None=None, method: RequestMethod | None=None, post_data: str | None=None, headers: list[HeaderEntry] | None=None, intercept_response: bool | None=None):
        """
        Continue paused request without modifications.
        """
        return mapping.from_impl(self._run(self._impl.continue_request(request_id=mapping.to_impl(request_id), url=mapping.to_impl(url), method=mapping.to_impl(method), post_data=mapping.to_impl(post_data), headers=mapping.to_impl(headers), intercept_response=mapping.to_impl(intercept_response))))

    def fail_request(self, request_id: str, error_reason: ErrorReason):
        """Fail request with error code."""
        return mapping.from_impl(self._run(self._impl.fail_request(request_id=mapping.to_impl(request_id), error_reason=mapping.to_impl(error_reason))))

    def fulfill_request(self, request_id: str, response_code: int, response_headers: list[HeaderEntry] | None=None, body: str | None=None, response_phrase: str | None=None):
        """Fulfill request with response data."""
        return mapping.from_impl(self._run(self._impl.fulfill_request(request_id=mapping.to_impl(request_id), response_code=mapping.to_impl(response_code), response_headers=mapping.to_impl(response_headers), body=mapping.to_impl(body), response_phrase=mapping.to_impl(response_phrase))))

    def execute_command(self, command: Command[T_CommandParams, T_CommandResponse], timeout: int=60) -> T_CommandResponse:
        """
        Send a raw CDP command on the browser-level session.

        Use it for browser-wide domains (Target, Browser, Storage, Emulation
        screens) that pydoll does not wrap. Build commands with the factories in
        ``pydoll.commands`` or pass a plain ``{'method': ..., 'params': ...}`` dict.

        Args:
            command: CDP command to send.
            timeout: Seconds to wait for the browser's answer.

        Returns:
            The browser's response, with the domain result under ``'result'``.

        Raises:
            CommandFailed: If the browser answers with an error.
            CommandExecutionTimeout: If no answer arrives within ``timeout``.
        """
        return mapping.from_impl(self._run(self._impl.execute_command(command=mapping.to_impl(command), timeout=mapping.to_impl(timeout))))

class Edge(SyncBase):
    """Edge browser implementation for CDP automation."""
    _impl: _EdgeImpl

    def __init__(self, options: Options | None=None, connection_port: int | None=None) -> None:
        """
        Initialize Edge browser instance.

        Args:
            options: Edge configuration options (default if None).
            connection_port: CDP WebSocket port (random if None).
        """
        super().__init__(_EdgeImpl(options=mapping.to_impl(options), connection_port=mapping.to_impl(connection_port)))

    def __enter__(self) -> Edge:
        return mapping.from_impl(self._run(self._impl.__aenter__()))

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> Any:
        return self._run(self._impl.__aexit__(exc_type, exc, tb))

    @property
    def options(self) -> Options:
        return mapping.from_impl(self._impl.options)

    @options.setter
    def options(self, value: Options) -> None:
        self._impl.options = mapping.to_impl(value)

    def connect(self, ws_address: str) -> Tab:
        """
        Connect to browser using WebSocket address. When we set
        the _ws_address attribute, the connection handler will use
        this address instead of resolving it from the connection port.

        Args:
            ws_address: WebSocket address of the browser.

        Returns:
            The first tab in the list of opened tabs.

        Note:
            You are supposed to use this method only if you want to connect to a browser
            that is already running.
        """
        return mapping.from_impl(self._run(self._impl.connect(ws_address=mapping.to_impl(ws_address))))

    def start(self) -> Tab:
        """
        Start browser process and establish CDP connection.

        Returns:
            Initial tab for interaction.

        Raises:
            FailedToStartBrowser: If the browser fails to start or connect.
        """
        return mapping.from_impl(self._run(self._impl.start()))

    def stop(self):
        """
        Stop browser process and cleanup resources.

        Sends Browser.close command, terminates process, removes temp directories,
        and closes WebSocket connections.

        Raises:
            BrowserNotRunning: If the browser is not currently running.
        """
        return mapping.from_impl(self._run(self._impl.stop()))

    def close(self):
        """
        Closes the WebSocket connection and releases resources.
        """
        return mapping.from_impl(self._run(self._impl.close()))

    def create_browser_context(self, proxy_server: str | None=None, proxy_bypass_list: str | None=None) -> str:
        """
        Create isolated browser context (like incognito).

        Browser contexts provide isolated storage and don't share session data.
        Multiple contexts can exist simultaneously.

        Args:
            proxy_server: Optional proxy for this context only (scheme://host:port).
            proxy_bypass_list: Comma-separated hosts that bypass proxy.

        Returns:
            Browser context ID for use with other methods.
        """
        return mapping.from_impl(self._run(self._impl.create_browser_context(proxy_server=mapping.to_impl(proxy_server), proxy_bypass_list=mapping.to_impl(proxy_bypass_list))))

    def delete_browser_context(self, browser_context_id: str):
        """
        Delete browser context and all associated tabs/resources.

        Removes all storage (cookies, localStorage, etc.) and closes all tabs.
        The default browser context cannot be deleted.

        Note:
            Closes all associated tabs immediately.
        """
        return mapping.from_impl(self._run(self._impl.delete_browser_context(browser_context_id=mapping.to_impl(browser_context_id))))

    def get_browser_contexts(self) -> list[str]:
        """Get all browser context IDs including the default context."""
        return mapping.from_impl(self._run(self._impl.get_browser_contexts()))

    def new_tab(self, url: str='', browser_context_id: str | None=None) -> Tab:
        """
        Create new tab for page interaction.

        Args:
            url: Initial URL (about:blank if empty).
            browser_context_id: Context to create tab in (default if None).

        Returns:
            Tab instance for page navigation and element interaction.
        """
        return mapping.from_impl(self._run(self._impl.new_tab(url=mapping.to_impl(url), browser_context_id=mapping.to_impl(browser_context_id))))

    def get_targets(self) -> list[TargetInfo]:
        """
        Get all active targets/pages in browser.

        Targets include pages, service workers, shared workers, and browser process.
        Useful for debugging and managing multiple tabs.

        Returns:
            List of TargetInfo objects.
        """
        return mapping.from_impl(self._run(self._impl.get_targets()))

    def get_opened_tabs(self) -> list[Tab]:
        """
        Get all opened tabs that are not extensions and have the type 'page'.
        Tabs that are already opened will be returned as is. If a new target is opened,
        a new Tab instance will be created.

        Returns:
            List of Tab instances. The last tab is the most recent one.
        """
        return mapping.from_impl(self._run(self._impl.get_opened_tabs()))

    def get_tab_by_target(self, target: TargetInfo) -> Tab:
        return mapping.from_impl(self._run(self._impl.get_tab_by_target(target=mapping.to_impl(target))))

    def set_download_path(self, path: str, browser_context_id: str | None=None):
        """Set download directory path (convenience method for set_download_behavior)."""
        return mapping.from_impl(self._run(self._impl.set_download_path(path=mapping.to_impl(path), browser_context_id=mapping.to_impl(browser_context_id))))

    def set_download_behavior(self, behavior: DownloadBehavior, download_path: str | None=None, browser_context_id: str | None=None, events_enabled: bool=False):
        """
        Configure download handling.

        Args:
            behavior: ALLOW (save to path), DENY (cancel), or DEFAULT.
            download_path: Required if behavior is ALLOW.
            browser_context_id: Context to apply to (default if None).
            events_enabled: Generate download events for progress tracking.
        """
        return mapping.from_impl(self._run(self._impl.set_download_behavior(behavior=mapping.to_impl(behavior), download_path=mapping.to_impl(download_path), browser_context_id=mapping.to_impl(browser_context_id), events_enabled=mapping.to_impl(events_enabled))))

    def delete_all_cookies(self, browser_context_id: str | None=None):
        """Delete all cookies (session, persistent, third-party) from browser or context."""
        return mapping.from_impl(self._run(self._impl.delete_all_cookies(browser_context_id=mapping.to_impl(browser_context_id))))

    def set_cookies(self, cookies: list[CookieParam], browser_context_id: str | None=None):
        """Set multiple cookies in browser or context."""
        return mapping.from_impl(self._run(self._impl.set_cookies(cookies=mapping.to_impl(cookies), browser_context_id=mapping.to_impl(browser_context_id))))

    def get_cookies(self, browser_context_id: str | None=None) -> list[Cookie]:
        """Get all cookies from browser or context.

        Note:
            This method does not work with native incognito mode (--incognito flag).
            For incognito mode, use ``tab.get_cookies()`` instead.
        """
        return mapping.from_impl(self._run(self._impl.get_cookies(browser_context_id=mapping.to_impl(browser_context_id))))

    def get_version(self) -> GetVersionResult:
        """Get browser version and CDP protocol information."""
        return mapping.from_impl(self._run(self._impl.get_version()))

    def get_window_id_for_target(self, target_id: str) -> int:
        """Get window ID for target (used for window manipulation via CDP)."""
        return mapping.from_impl(self._run(self._impl.get_window_id_for_target(target_id=mapping.to_impl(target_id))))

    def get_window_id_for_tab(self, tab: Tab) -> int:
        """Get window ID for tab (convenience method)."""
        return mapping.from_impl(self._run(self._impl.get_window_id_for_tab(tab=mapping.to_impl(tab))))

    def get_window_id(self) -> int:
        """
        Get window ID for any valid tab.

        Raises:
            NoValidTabFound: If no valid attached tab can be found.
        """
        return mapping.from_impl(self._run(self._impl.get_window_id()))

    def set_window_maximized(self):
        """Maximize browser window (affects all tabs in window)."""
        return mapping.from_impl(self._run(self._impl.set_window_maximized()))

    def set_window_minimized(self):
        """Minimize browser window to taskbar/dock."""
        return mapping.from_impl(self._run(self._impl.set_window_minimized()))

    def set_window_bounds(self, bounds: Bounds):
        """
        Set window position and/or size.

        Args:
            bounds: Properties to modify (left, top, width, height, windowState).
                Only specified properties are changed.
        """
        return mapping.from_impl(self._run(self._impl.set_window_bounds(bounds=mapping.to_impl(bounds))))

    def grant_permissions(self, permissions: list[PermissionType], origin: str | None=None, browser_context_id: str | None=None):
        """
        Grant browser permissions (geolocation, notifications, camera, etc.).

        Bypasses normal permission prompts for automated testing.

        Args:
            permissions: Permissions to grant.
            origin: Origin to grant to (all origins if None).
            browser_context_id: Context to apply to (default if None).
        """
        return mapping.from_impl(self._run(self._impl.grant_permissions(permissions=mapping.to_impl(permissions), origin=mapping.to_impl(origin), browser_context_id=mapping.to_impl(browser_context_id))))

    def reset_permissions(self, browser_context_id: str | None=None):
        """Reset all permissions to defaults and restore prompting behavior."""
        return mapping.from_impl(self._run(self._impl.reset_permissions(browser_context_id=mapping.to_impl(browser_context_id))))

    def on(self, event_name: str, callback: Callable[[Any], Any], temporary: bool=False) -> int:
        """
        Register CDP event listener at browser level.

        Callback runs in background task to prevent blocking. Affects all pages/targets.

        Args:
            event_name: CDP event name (e.g., "Network.responseReceived").
            callback: Function called on event (sync or async).
            temporary: Remove after first invocation.

        Returns:
            Callback ID for removal.

        Note:
            For page-specific events, use Tab.on() instead.
        """
        return mapping.from_impl(self._run(cast('Any', self._impl).on(event_name=mapping.to_impl(event_name), callback=mapping.wrap_handler(callback), temporary=mapping.to_impl(temporary))))

    def remove_callback(self, callback_id: int):
        """Remove callback from browser."""
        return mapping.from_impl(self._run(self._impl.remove_callback(callback_id=mapping.to_impl(callback_id))))

    def enable_fetch_events(self, handle_auth_requests: bool=False, resource_type: ResourceType | None=None):
        """
        Enable network request interception via Fetch domain.

        Allows monitoring, modifying, or blocking requests before they're sent.
        All matching requests are paused until explicitly continued.

        Args:
            handle_auth_requests: Intercept authentication challenges.
            resource_type: Filter by type (XHR, Fetch, Document, etc.). Empty = all.

        Note:
            Paused requests must be continued or they will timeout.
        """
        return mapping.from_impl(self._run(self._impl.enable_fetch_events(handle_auth_requests=mapping.to_impl(handle_auth_requests), resource_type=mapping.to_impl(resource_type))))

    def disable_fetch_events(self):
        """Disable request interception and release any paused requests."""
        return mapping.from_impl(self._run(self._impl.disable_fetch_events()))

    def enable_runtime_events(self):
        """Enable runtime events."""
        return mapping.from_impl(self._run(self._impl.enable_runtime_events()))

    def disable_runtime_events(self):
        """Disable runtime events."""
        return mapping.from_impl(self._run(self._impl.disable_runtime_events()))

    def continue_request(self, request_id: str, url: str | None=None, method: RequestMethod | None=None, post_data: str | None=None, headers: list[HeaderEntry] | None=None, intercept_response: bool | None=None):
        """
        Continue paused request without modifications.
        """
        return mapping.from_impl(self._run(self._impl.continue_request(request_id=mapping.to_impl(request_id), url=mapping.to_impl(url), method=mapping.to_impl(method), post_data=mapping.to_impl(post_data), headers=mapping.to_impl(headers), intercept_response=mapping.to_impl(intercept_response))))

    def fail_request(self, request_id: str, error_reason: ErrorReason):
        """Fail request with error code."""
        return mapping.from_impl(self._run(self._impl.fail_request(request_id=mapping.to_impl(request_id), error_reason=mapping.to_impl(error_reason))))

    def fulfill_request(self, request_id: str, response_code: int, response_headers: list[HeaderEntry] | None=None, body: str | None=None, response_phrase: str | None=None):
        """Fulfill request with response data."""
        return mapping.from_impl(self._run(self._impl.fulfill_request(request_id=mapping.to_impl(request_id), response_code=mapping.to_impl(response_code), response_headers=mapping.to_impl(response_headers), body=mapping.to_impl(body), response_phrase=mapping.to_impl(response_phrase))))

    def execute_command(self, command: Command[T_CommandParams, T_CommandResponse], timeout: int=60) -> T_CommandResponse:
        """
        Send a raw CDP command on the browser-level session.

        Use it for browser-wide domains (Target, Browser, Storage, Emulation
        screens) that pydoll does not wrap. Build commands with the factories in
        ``pydoll.commands`` or pass a plain ``{'method': ..., 'params': ...}`` dict.

        Args:
            command: CDP command to send.
            timeout: Seconds to wait for the browser's answer.

        Returns:
            The browser's response, with the domain result under ``'result'``.

        Raises:
            CommandFailed: If the browser answers with an error.
            CommandExecutionTimeout: If no answer arrives within ``timeout``.
        """
        return mapping.from_impl(self._run(self._impl.execute_command(command=mapping.to_impl(command), timeout=mapping.to_impl(timeout))))

class Tab(SyncBase):
    """
    Controls a browser tab via Chrome DevTools Protocol.

    Primary interface for web page automation including navigation, DOM manipulation,
    JavaScript execution, event handling, network monitoring, and specialized tasks
    like Cloudflare Turnstile handling.
    """
    _impl: _TabImpl

    @property
    def target_id(self) -> str | None:
        """CDP target id of this tab, when known."""
        return mapping.from_impl(self._impl.target_id)

    @property
    def browser_context_id(self) -> str | None:
        """Browser context this tab belongs to (None for the default context)."""
        return mapping.from_impl(self._impl.browser_context_id)

    @property
    def page_events_enabled(self) -> bool:
        """Whether CDP Page domain events are enabled."""
        return mapping.from_impl(self._impl.page_events_enabled)

    @property
    def network_events_enabled(self) -> bool:
        """Whether CDP Network domain events are enabled."""
        return mapping.from_impl(self._impl.network_events_enabled)

    @property
    def fetch_events_enabled(self) -> bool:
        """Whether CDP Fetch domain events (request interception) are enabled."""
        return mapping.from_impl(self._impl.fetch_events_enabled)

    @property
    def dom_events_enabled(self) -> bool:
        """Whether CDP DOM domain events are enabled."""
        return mapping.from_impl(self._impl.dom_events_enabled)

    @property
    def runtime_events_enabled(self) -> bool:
        """Whether CDP Runtime domain events are enabled."""
        return mapping.from_impl(self._impl.runtime_events_enabled)

    @property
    def request(self) -> Request:
        """
        Get the request object for making HTTP requests using the browser's fetch API.

        Returns:
            Request: An instance of the Request class for making HTTP requests.
        """
        return mapping.from_impl(self._impl.request)

    @property
    def scroll(self) -> Scroll:
        """
        Get the scroll API for controlling page scroll behavior.

        Returns:
            ScrollAPI: An instance of the ScrollAPI class for scroll operations.
        """
        return mapping.from_impl(self._impl.scroll)

    @property
    def keyboard(self) -> Keyboard:
        """
        Get the keyboard API for controlling keyboard input at page level.

        Returns:
            KeyboardAPI: An instance of the KeyboardAPI class for keyboard operations.
        """
        return mapping.from_impl(self._impl.keyboard)

    @property
    def mouse(self) -> Mouse:
        """
        Get the mouse API for controlling mouse input.

        Returns:
            MouseAPI: An instance of the MouseAPI class for mouse operations.
        """
        return mapping.from_impl(self._impl.mouse)

    def extract(self, model: type[T], *, scope: str | None=None, timeout: int=0) -> T:
        """Extract structured data from the page into a typed model.

        Args:
            model: ExtractionModel subclass defining the extraction schema.
            scope: Optional CSS/XPath selector to limit extraction region.
            timeout: Seconds to wait for elements (0 = no wait).

        Returns:
            Populated model instance with extracted data.

        Raises:
            FieldExtractionFailed: If a required field cannot be extracted.
            InvalidExtractionModel: If model definition is invalid.
        """
        return mapping.from_impl(self._run(self._impl.extract(model=mapping.to_impl(model), scope=mapping.to_impl(scope), timeout=mapping.to_impl(timeout))))

    def extract_all(self, model: type[T], *, scope: str, timeout: int=0, limit: int | None=None) -> list[T]:
        """Extract multiple items from repeated containers on the page.

        Each element matching the scope selector generates one model instance.
        Fields are resolved relative to each scope container.

        Args:
            model: ExtractionModel subclass defining the extraction schema.
            scope: CSS/XPath selector for the repeated container (required).
            timeout: Seconds to wait for elements (0 = no wait).
            limit: Maximum number of items to extract (None = all).

        Returns:
            List of populated model instances.
        """
        return mapping.from_impl(self._run(self._impl.extract_all(model=mapping.to_impl(model), scope=mapping.to_impl(scope), timeout=mapping.to_impl(timeout), limit=mapping.to_impl(limit))))

    @property
    def intercept_file_chooser_dialog_enabled(self) -> bool:
        """Whether file chooser dialog interception is active."""
        return mapping.from_impl(self._impl.intercept_file_chooser_dialog_enabled)

    def current_url(self) -> str:
        """Get current page URL (reflects redirects and client-side navigation)."""
        return mapping.from_impl(self._run(self._impl.current_url()))

    def page_source(self) -> str:
        """Get complete HTML source of current page (live DOM state)."""
        return mapping.from_impl(self._run(self._impl.page_source()))

    def title(self) -> str:
        """Get current page title."""
        return mapping.from_impl(self._run(self._impl.title()))

    def enable_page_events(self):
        """Enable CDP Page domain events (load, navigation, dialogs, etc.)."""
        return mapping.from_impl(self._run(self._impl.enable_page_events()))

    def enable_network_events(self):
        """Enable CDP Network domain events (requests, responses, etc.)."""
        return mapping.from_impl(self._run(self._impl.enable_network_events()))

    def enable_fetch_events(self, handle_auth: bool=False, resource_type: ResourceType | None=None, request_stage: RequestStage | None=None):
        """
        Enable CDP Fetch domain for request interception.

        Args:
            handle_auth: Intercept authentication challenges.
            resource_type: Filter by resource type (all if None).
            request_stage: When to intercept (Request/Response).

        Note:
            Intercepted requests must be explicitly continued or timeout.
        """
        return mapping.from_impl(self._run(self._impl.enable_fetch_events(handle_auth=mapping.to_impl(handle_auth), resource_type=mapping.to_impl(resource_type), request_stage=mapping.to_impl(request_stage))))

    def enable_dom_events(self):
        """Enable CDP DOM domain events (document structure changes)."""
        return mapping.from_impl(self._run(self._impl.enable_dom_events()))

    def enable_runtime_events(self):
        """Enable CDP Runtime domain events."""
        return mapping.from_impl(self._run(self._impl.enable_runtime_events()))

    def enable_intercept_file_chooser_dialog(self):
        """
        Enable file chooser dialog interception for automated uploads.

        Note:
            Use expect_file_chooser context manager for convenience.
        """
        return mapping.from_impl(self._run(self._impl.enable_intercept_file_chooser_dialog()))

    def enable_cloudflare_turnstile_handling(self, time_to_wait_captcha: float=5):
        """
        Handle the Cloudflare Turnstile widget automatically.

        When a page finishes loading with the widget present, its checkbox is clicked.

        Args:
            time_to_wait_captcha: Timeout for captcha detection (default 5s).
        """
        return mapping.from_impl(self._run(self._impl.enable_cloudflare_turnstile_handling(time_to_wait_captcha=mapping.to_impl(time_to_wait_captcha))))

    def disable_fetch_events(self):
        """Disable CDP Fetch domain and release paused requests."""
        return mapping.from_impl(self._run(self._impl.disable_fetch_events()))

    def disable_page_events(self):
        """Disable CDP Page domain events."""
        return mapping.from_impl(self._run(self._impl.disable_page_events()))

    def disable_network_events(self):
        """Disable CDP Network domain events."""
        return mapping.from_impl(self._run(self._impl.disable_network_events()))

    def disable_dom_events(self):
        """Disable CDP DOM domain events."""
        return mapping.from_impl(self._run(self._impl.disable_dom_events()))

    def disable_runtime_events(self):
        """Disable CDP Runtime domain events."""
        return mapping.from_impl(self._run(self._impl.disable_runtime_events()))

    def disable_intercept_file_chooser_dialog(self):
        """Disable file chooser dialog interception."""
        return mapping.from_impl(self._run(self._impl.disable_intercept_file_chooser_dialog()))

    def disable_cloudflare_turnstile_handling(self):
        """Stop handling the Cloudflare Turnstile widget on page load."""
        return mapping.from_impl(self._run(self._impl.disable_cloudflare_turnstile_handling()))

    def close(self):
        """
        Close this browser tab.

        Note:
            Tab instance becomes invalid after calling this method.
        """
        return mapping.from_impl(self._run(self._impl.close()))

    def find_shadow_roots(self, deep: bool=False, timeout: float=0) -> list[ShadowRoot]:
        """
        Find all shadow roots in the page.

        Traverses the entire DOM tree (including iframes and nested shadow DOMs)
        to collect all shadow roots found. This is especially useful when the
        shadow host element selector is unknown or dynamic (e.g., Cloudflare
        challenge pages).

        Args:
            deep: If True, also traverses cross-origin iframes (OOPIFs) to
                discover shadow roots inside them. The returned ShadowRoot
                objects will automatically route CDP commands through the
                correct OOPIF session.
            timeout: Maximum seconds to wait for shadow roots to appear.
                When > 0, repeatedly polls the DOM (starting every 20 ms and backing
                off to 250 ms) until at least one shadow root is found or the timeout
                expires. Useful when shadow hosts are injected asynchronously (e.g.,
                Cloudflare Turnstile loading inside an OOPIF).

        Returns:
            List of ShadowRoot instances found in the page.

        Raises:
            WaitElementTimeout: If timeout > 0 and no shadow roots are found
                within the specified duration.
        """
        return mapping.from_impl(self._run(self._impl.find_shadow_roots(deep=mapping.to_impl(deep), timeout=mapping.to_impl(timeout))))

    def bring_to_front(self):
        """Brings the page to front."""
        return mapping.from_impl(self._run(self._impl.bring_to_front()))

    def get_cookies(self) -> list[Cookie]:
        """Get all cookies of this tab's browser context.

        A tab that lives in a browser context created with
        ``browser.create_browser_context()`` reads them through the browser
        connection, because Chrome only accepts ``browserContextId`` on the
        browser target, not on a page session.
        """
        return mapping.from_impl(self._run(self._impl.get_cookies()))

    def get_network_response_body(self, request_id: str) -> str:
        """
        Get the response body for a given request ID.

        Args:
            request_id: Request ID to get the response body for.

        Returns:
            The response body for the given request ID.

        Raises:
            NetworkEventsNotEnabled: If network events are not enabled.
        """
        return mapping.from_impl(self._run(self._impl.get_network_response_body(request_id=mapping.to_impl(request_id))))

    def get_network_logs(self, filter: str | None=None) -> list[RequestWillBeSentEvent]:
        """
        Get network logs.

        Args:
            filter: Filter to apply to the network logs.

        Returns:
            The network logs.

        Raises:
            NetworkEventsNotEnabled: If network events are not enabled.
        """
        return mapping.from_impl(self._run(self._impl.get_network_logs(filter=mapping.to_impl(filter))))

    def set_cookies(self, cookies: list[CookieParam]):
        """
        Set multiple cookies for current page.

        Args:
            cookies: Cookie parameters (name/value required, others optional).

        Note:
            Defaults to current page's domain if not specified.
        """
        return mapping.from_impl(self._run(self._impl.set_cookies(cookies=mapping.to_impl(cookies))))

    def delete_all_cookies(self):
        """Delete all cookies from current browser context."""
        return mapping.from_impl(self._run(self._impl.delete_all_cookies()))

    def apply_fingerprint(self, fingerprint: FingerprintConfig, *, cross_origin_iframes: bool=True) -> None:
        """Apply a browser fingerprint profile to this tab.

        Delegates to a per-tab :class:`FingerprintApplier` (created once and
        reused), which overrides browser identity signals via CDP commands and
        JavaScript injection and replays them on Web Worker targets and cross-site
        iframes. Call before navigating to any page for full effect, since JS
        overrides register via ``Page.addScriptToEvaluateOnNewDocument``.

        Args:
            fingerprint: Fingerprint configuration. Only specified fields
                are overridden; unspecified fields keep real browser values.
            cross_origin_iframes: When true (default), the identity is also
                replayed into every cross-site iframe (OOPIF), so a fingerprinting
                script embedded in a cross-origin challenge or captcha frame reads
                the same identity as the page. Set false to cover only the top
                page, same-origin frames, and workers.
        """
        self._run(self._impl.apply_fingerprint(fingerprint=mapping.to_impl(fingerprint), cross_origin_iframes=mapping.to_impl(cross_origin_iframes)))

    def go_to(self, url: str, timeout: int=300):
        """
        Navigate to URL and wait for loading to complete.

        Args:
            url: Target URL to navigate to.
            timeout: Maximum seconds to wait for page load (default 300).

        Raises:
            NavigationError: If the navigation fails (e.g., DNS error).
            PageLoadTimeout: If page doesn't finish loading within timeout.
        """
        return mapping.from_impl(self._run(self._impl.go_to(url=mapping.to_impl(url), timeout=mapping.to_impl(timeout))))

    def wait_for_url(self, url: UrlPattern, timeout: float=30) -> str:
        """
        Wait until the tab's URL matches a pattern and return it.

        Covers full navigations and in-page changes (``pushState``) alike,
        because it reads the live URL instead of listening to one event.

        Args:
            url: A glob (``'*/checkout/*'``), a compiled regular expression,
                or a callable that receives the URL and returns True to match.
            timeout: Maximum seconds to wait.

        Returns:
            The URL that matched.

        Raises:
            WaitTimeout: If no matching URL is seen within ``timeout``.
        """
        return mapping.from_impl(self._run(self._impl.wait_for_url(url=mapping.to_impl(url), timeout=mapping.to_impl(timeout))))

    def wait_for_script(self, script: str, timeout: float=30) -> Any:
        """
        Wait until a JavaScript expression evaluates to a truthy value and return it.

        Truthiness is JavaScript's, judged on the page side: a DOM node, a
        function, an object (even ``{}`` or ``[]``) and a non-empty string or
        non-zero number are truthy; ``undefined``, ``null``, ``false``, ``0``,
        ``NaN``, ``-0``, ``0n`` and ``''`` are falsy. A promise is awaited and
        its settled value is judged.

        Args:
            script: An expression such as ``'window.app && window.app.ready'``,
                or a script with a ``return``.
            timeout: Maximum seconds to wait.

        Returns:
            The value itself when it is a primitive (string, number, ``True``),
            ``True`` for any object, node or function.

        Raises:
            WaitTimeout: If the script stays falsy for ``timeout`` seconds.
            ScriptEvaluationError: As soon as the script throws or its promise
                rejects, with the JavaScript error text.
        """
        return mapping.from_impl(self._run(self._impl.wait_for_script(script=mapping.to_impl(script), timeout=mapping.to_impl(timeout))))

    def wait_for_absence(self, id: str | None=None, class_name: str | None=None, name: str | None=None, tag_name: str | None=None, text: str | None=None, timeout: float=30, **attributes: str) -> None:
        """
        Wait until no element matches the criteria, the same criteria ``find()`` takes.

        Use it for the thing that has to go away before you continue: a
        loading overlay, a "saving" badge, a modal that closes on its own.

        Args:
            id, class_name, name, tag_name, text, **attributes: Criteria, as in ``find()``.
            timeout: Maximum seconds to wait.

        Raises:
            WaitTimeout: If a matching element is still present after ``timeout``.
        """
        self._run(self._impl.wait_for_absence(id=mapping.to_impl(id), class_name=mapping.to_impl(class_name), name=mapping.to_impl(name), tag_name=mapping.to_impl(tag_name), text=mapping.to_impl(text), timeout=mapping.to_impl(timeout), **{kwarg: mapping.to_impl(kwarg_value) for kwarg, kwarg_value in attributes.items()}))

    def wait_for_network_idle(self, idle_time: float=0.5, timeout: float=30) -> None:
        """
        Wait until the page has had no network requests in flight for ``idle_time`` seconds.

        Requests are counted from the moment this method is called, so call
        it right after the action that starts them (a navigation, a click that
        loads data). A request that never finishes keeps the page busy until
        ``timeout``.

        Args:
            idle_time: Seconds without any request in flight that count as idle.
            timeout: Maximum seconds to wait.

        Raises:
            WaitTimeout: If the network is never idle for ``idle_time`` within ``timeout``.
        """
        self._run(self._impl.wait_for_network_idle(idle_time=mapping.to_impl(idle_time), timeout=mapping.to_impl(timeout)))

    def expect_navigation(self, url: UrlPattern | None=None, timeout: float=30) -> AbstractContextManager[None]:
        """
        Wait for a navigation started inside the block, and for the new page to load.

        Register before acting, act inside the block, and the block only
        exits once the main frame has navigated (to a URL matching ``url``,
        when given) and reached the load state set in ``options.page_load_state``.

        Args:
            url: Optional glob, regular expression or callable the new URL must match.
            timeout: Maximum seconds to wait after the block.

        Raises:
            WaitTimeout: If the navigation or the load does not happen in time.
        """
        return mapping.from_impl(self._impl.expect_navigation(url=mapping.to_impl(url), timeout=mapping.to_impl(timeout)))

    def expect_request(self, url: UrlPattern, timeout: float=30) -> AbstractContextManager[RequestHandle]:
        """
        Capture the first request whose URL matches, sent during the block.

        The handle is empty inside the block and filled when the block exits,
        which is when the wait happens.

        Args:
            url: A glob, a compiled regular expression, or a callable on the URL.
            timeout: Maximum seconds to wait after the block for the request.

        Yields:
            RequestHandle: URL, method, headers and body of the request.

        Raises:
            WaitTimeout: If no matching request is sent within ``timeout``.
        """
        return mapping.from_impl(self._impl.expect_request(url=mapping.to_impl(url), timeout=mapping.to_impl(timeout)))

    def expect_response(self, url: UrlPattern, timeout: float=30) -> AbstractContextManager[ResponseHandle]:
        """
        Capture the first response whose URL matches, received during the block.

        The block exits once the response has arrived and its body has been
        read, so ``response.json()`` is ready right after the block: the usual
        way to read the API call a click triggers instead of scraping the DOM.
        A 204, 205 or 304 response has no body by definition (Chrome reports
        its load as aborted), so it completes with an empty body.

        Args:
            url: A glob, a compiled regular expression, or a callable on the URL.
            timeout: Maximum seconds to wait after the block for the response.

        Yields:
            ResponseHandle: status, headers and body of the response.

        Raises:
            WaitTimeout: If no matching response completes within ``timeout``.
        """
        return mapping.from_impl(self._impl.expect_response(url=mapping.to_impl(url), timeout=mapping.to_impl(timeout)))

    def refresh(self, ignore_cache: bool=False, script_to_evaluate_on_load: str | None=None):
        """
        Reload current page and wait for completion.

        Args:
            ignore_cache: Bypass browser cache if True.
            script_to_evaluate_on_load: JavaScript to execute after load.

        Raises:
            PageLoadTimeout: If page doesn't finish loading within timeout.
        """
        return mapping.from_impl(self._run(self._impl.refresh(ignore_cache=mapping.to_impl(ignore_cache), script_to_evaluate_on_load=mapping.to_impl(script_to_evaluate_on_load))))

    def take_screenshot(self, path: str | Path | None=None, quality: int=100, beyond_viewport: bool=False, as_base64: bool=False) -> str | None:
        """
        Capture screenshot of current page.

        Args:
            path: File path for screenshot (extension determines format).
            quality: Image quality 0-100 (default 100).
            beyond_viewport: The page will be scrolled to the bottom and the screenshot will
                include the entire page
            as_base64: Return as base64 string instead of saving file.

        Returns:
            Base64 screenshot data if as_base64=True, None otherwise.

        Raises:
            InvalidFileExtension: If file extension not supported.
            MissingScreenshotPath: If path is None and as_base64 is False.
        """
        return mapping.from_impl(self._run(self._impl.take_screenshot(path=mapping.to_impl(path), quality=mapping.to_impl(quality), beyond_viewport=mapping.to_impl(beyond_viewport), as_base64=mapping.to_impl(as_base64))))

    def print_to_pdf(self, path: str | Path | None=None, landscape: bool=False, display_header_footer: bool=False, print_background: bool=True, scale: float=1.0, as_base64: bool=False) -> str | None:
        """
        Generate PDF of current page.

        Args:
            path: File path for PDF output. Required if as_base64=False.
            landscape: Use landscape orientation.
            display_header_footer: Include header/footer.
            print_background: Include background graphics.
            scale: Scale factor (0.1-2.0).
            as_base64: Return as base64 string instead of saving.

        Returns:
            Base64 PDF data if as_base64=True, None otherwise.

        Raises:
            ValueError: If path is not provided when as_base64=False.
        """
        return mapping.from_impl(self._run(self._impl.print_to_pdf(path=mapping.to_impl(path), landscape=mapping.to_impl(landscape), display_header_footer=mapping.to_impl(display_header_footer), print_background=mapping.to_impl(print_background), scale=mapping.to_impl(scale), as_base64=mapping.to_impl(as_base64))))

    def save_bundle(self, path: str | Path, inline_assets: bool=False) -> None:
        """
        Save current page and its assets as a .zip bundle for offline viewing.

        Captures the page HTML along with CSS, JS, images, fonts, and media
        into a single zip archive. The archive contains an ``index.html`` with
        URLs rewritten to reference local asset files.

        Args:
            path: Destination path for the ``.zip`` file.
            inline_assets: When True, embed all assets directly into
                ``index.html`` using data URIs, ``<style>``, and ``<script>``
                tags instead of saving them as separate files.

        Raises:
            InvalidFileExtension: If path does not end with ``.zip``.
        """
        self._run(self._impl.save_bundle(path=mapping.to_impl(path), inline_assets=mapping.to_impl(inline_assets)))

    def has_dialog(self) -> bool:
        """
        Check if JavaScript dialog is currently displayed.

        Note:
            Page events must be enabled to detect dialogs.
        """
        return mapping.from_impl(self._run(self._impl.has_dialog()))

    def get_dialog_message(self) -> str:
        """
        Get message text from current JavaScript dialog.

        Raises:
            NoDialogPresent: If no dialog is currently displayed.
        """
        return mapping.from_impl(self._run(self._impl.get_dialog_message()))

    def handle_dialog(self, accept: bool, prompt_text: str | None=None):
        """
        Respond to JavaScript dialog.

        Args:
            accept: Accept/confirm dialog if True, dismiss/cancel if False.
            prompt_text: Text for prompt dialogs (ignored for alert/confirm).

        Raises:
            NoDialogPresent: If no dialog is currently displayed.

        Note:
            Page events must be enabled to handle dialogs.
        """
        return mapping.from_impl(self._run(self._impl.handle_dialog(accept=mapping.to_impl(accept), prompt_text=mapping.to_impl(prompt_text))))

    def execute_script(self, script: str, *, object_group: str | None=None, include_command_line_api: bool | None=None, silent: bool | None=None, context_id: int | None=None, return_by_value: bool | None=None, generate_preview: bool | None=None, user_gesture: bool | None=None, await_promise: bool | None=None, throw_on_side_effect: bool | None=None, timeout: float | None=None, disable_breaks: bool | None=None, repl_mode: bool | None=None, allow_unsafe_eval_blocked_by_csp: bool | None=None, unique_context_id: str | None=None, serialization_options: SerializationOptions | None=None) -> EvaluateResponse:
        """
        Execute JavaScript in page context.

        Args:
            script (str): JavaScript code to execute.
            object_group (str | None): Symbolic group name for the result (Runtime.evaluate).
            include_command_line_api (bool | None): Whether to include command line API
                (Runtime.evaluate).
            silent (bool | None): Whether to silence exceptions (Runtime.evaluate).
            context_id (int | None): ID of the execution context to evaluate in
                (Runtime.evaluate).
            return_by_value (bool | None): Whether to return the result by value instead of
                reference (Runtime.evaluate).
            generate_preview (bool | None): Whether to generate a preview for the result
                (Runtime.evaluate).
            user_gesture (bool | None): Whether to treat evaluation as initiated by user
                gesture (Runtime.evaluate).
            await_promise (bool | None): Whether to promise result (Runtime.evaluate).
            throw_on_side_effect (bool | None): Whether to throw if side effect cannot be
                ruled out (Runtime.evaluate).
            timeout (float | None): Timeout in milliseconds (Runtime.evaluate).
            disable_breaks (bool | None): Whether to disable breakpoints during evaluation
                (Runtime.evaluate).
            repl_mode (bool | None): Whether to execute in REPL mode (Runtime.evaluate).
            allow_unsafe_eval_blocked_by_csp (bool | None): Allow unsafe evaluation
                (Runtime.evaluate).
            unique_context_id (str | None): Unique context ID for evaluation
                (Runtime.evaluate).
            serialization_options (SerializationOptions | None): Serialization options for
                the result (Runtime.evaluate).

        Returns:
            EvaluateResponse: The result of the script execution.

        Raises:
            InvalidScriptWithElement: If the script references ``argument``; run it through
                ``WebElement.execute_script()`` instead.

        Examples:
            # Execute a simple script to log a message
            tab.execute_script('console.log("Hello World")')

            # Execute a script that returns the page title
            tab.execute_script('return document.title')
        """
        return mapping.from_impl(self._run(self._impl.execute_script(script=mapping.to_impl(script), object_group=mapping.to_impl(object_group), include_command_line_api=mapping.to_impl(include_command_line_api), silent=mapping.to_impl(silent), context_id=mapping.to_impl(context_id), return_by_value=mapping.to_impl(return_by_value), generate_preview=mapping.to_impl(generate_preview), user_gesture=mapping.to_impl(user_gesture), await_promise=mapping.to_impl(await_promise), throw_on_side_effect=mapping.to_impl(throw_on_side_effect), timeout=mapping.to_impl(timeout), disable_breaks=mapping.to_impl(disable_breaks), repl_mode=mapping.to_impl(repl_mode), allow_unsafe_eval_blocked_by_csp=mapping.to_impl(allow_unsafe_eval_blocked_by_csp), unique_context_id=mapping.to_impl(unique_context_id), serialization_options=mapping.to_impl(serialization_options))))

    def continue_request(self, request_id: str, url: str | None=None, method: RequestMethod | None=None, post_data: str | None=None, headers: list[HeaderEntry] | None=None, intercept_response: bool | None=None):
        """
        Continue paused request without modifications.
        """
        return mapping.from_impl(self._run(self._impl.continue_request(request_id=mapping.to_impl(request_id), url=mapping.to_impl(url), method=mapping.to_impl(method), post_data=mapping.to_impl(post_data), headers=mapping.to_impl(headers), intercept_response=mapping.to_impl(intercept_response))))

    def fail_request(self, request_id: str, error_reason: ErrorReason):
        """Fail request with error code."""
        return mapping.from_impl(self._run(self._impl.fail_request(request_id=mapping.to_impl(request_id), error_reason=mapping.to_impl(error_reason))))

    def fulfill_request(self, request_id: str, response_code: int, response_headers: list[HeaderEntry] | None=None, body: str | None=None, response_phrase: str | None=None):
        """Fulfill request with response data."""
        return mapping.from_impl(self._run(self._impl.fulfill_request(request_id=mapping.to_impl(request_id), response_code=mapping.to_impl(response_code), response_headers=mapping.to_impl(response_headers), body=mapping.to_impl(body), response_phrase=mapping.to_impl(response_phrase))))

    def continue_with_auth(self, request_id: str, auth_challenge_response: AuthChallengeResponseType, proxy_username: str | None=None, proxy_password: str | None=None):
        """Continue a paused request replying to an authentication challenge.

        Useful for proxy auth (407) or server auth (401) when Fetch is enabled
        with handle_auth=True.
        """
        return mapping.from_impl(self._run(self._impl.continue_with_auth(request_id=mapping.to_impl(request_id), auth_challenge_response=mapping.to_impl(auth_challenge_response), proxy_username=mapping.to_impl(proxy_username), proxy_password=mapping.to_impl(proxy_password))))

    def expect_file_chooser(self, files: str | Path | list[str | Path]) -> AbstractContextManager[None]:
        """
        Context manager for automatic file upload handling.

        Args:
            files: File path(s) for upload.
        """
        return mapping.from_impl(self._impl.expect_file_chooser(files=mapping.to_impl(files)))

    def expect_cloudflare_turnstile(self, time_to_wait_captcha: float=5) -> AbstractContextManager[None]:
        """
        Handle the Cloudflare Turnstile widget if it appears while the block runs.

        Args:
            time_to_wait_captcha: Timeout for captcha detection (default 5s).
        """
        return mapping.from_impl(self._impl.expect_cloudflare_turnstile(time_to_wait_captcha=mapping.to_impl(time_to_wait_captcha)))

    def expect_download(self, keep_file_at: str | Path | None=None, timeout: float | None=None) -> AbstractContextManager[DownloadHandle]:
        """
        Context manager for handling a file download triggered inside the block.

        Behavior:
        - If keep_file_at is provided, configure browser to save into that directory and keep file.
        - Otherwise, a temporary directory is used and cleaned up after the context.

        Args:
            keep_file_at: Directory to persist the file. If None, uses a temporary
                directory and cleans it up afterwards.
            timeout: Max seconds to wait for download completion. Defaults to 60.

        Yields:
            DownloadHandle: Handle to read the downloaded file (bytes/base64) and check its path.
        """
        return mapping.from_impl(self._impl.expect_download(keep_file_at=mapping.to_impl(keep_file_at), timeout=mapping.to_impl(timeout)))

    def on(self, event_name: str, callback: Callable[[dict], Any], temporary: bool=False) -> int:
        """
        Register CDP event listener.

        Callback runs in background task to prevent blocking.

        Args:
            event_name: CDP event name (e.g., 'Page.loadEventFired').
            callback: Function called on event (sync or async).
            temporary: Remove after first invocation.

        Returns:
            Callback ID for removal.

        Note:
            Corresponding domain must be enabled before events fire.
        """
        return mapping.from_impl(self._run(cast('Any', self._impl).on(event_name=mapping.to_impl(event_name), callback=mapping.wrap_handler(callback), temporary=mapping.to_impl(temporary))))

    def remove_callback(self, callback_id: int):
        """Remove callback from tab."""
        return mapping.from_impl(self._run(self._impl.remove_callback(callback_id=mapping.to_impl(callback_id))))

    def clear_callbacks(self):
        """Clear all registered event callbacks."""
        return mapping.from_impl(self._run(self._impl.clear_callbacks()))

    @overload
    def find(self, id: str | None=..., class_name: str | None=..., name: str | None=..., tag_name: str | None=..., text: str | None=..., timeout: int=..., find_all: Literal[False]=False, raise_exc: Literal[True]=True, **attributes) -> WebElement: ...
    @overload
    def find(self, id: str | None=..., class_name: str | None=..., name: str | None=..., tag_name: str | None=..., text: str | None=..., timeout: int=..., find_all: Literal[False]=False, raise_exc: Literal[False]=False, **attributes) -> WebElement | None: ...
    @overload
    def find(self, id: str | None=..., class_name: str | None=..., name: str | None=..., tag_name: str | None=..., text: str | None=..., timeout: int=..., find_all: Literal[True]=True, raise_exc: Literal[True]=True, **attributes) -> list[WebElement]: ...
    @overload
    def find(self, id: str | None=..., class_name: str | None=..., name: str | None=..., tag_name: str | None=..., text: str | None=..., timeout: int=..., find_all: Literal[True]=True, raise_exc: Literal[False]=False, **attributes) -> list[WebElement] | None: ...
    @overload
    def find(self, id: str | None=..., class_name: str | None=..., name: str | None=..., tag_name: str | None=..., text: str | None=..., timeout: int=..., find_all: bool=..., raise_exc: bool=..., **attributes) -> WebElement | list[WebElement] | None: ...
    def find(self, id: str | None=None, class_name: str | None=None, name: str | None=None, tag_name: str | None=None, text: str | None=None, timeout: int=0, find_all: bool=False, raise_exc: bool=True, **attributes: dict[str, str]) -> WebElement | list[WebElement] | None:
        """
        Find element(s) using combination of common HTML attributes.

        Flexible element location using standard attributes. Multiple attributes
        can be combined for specific selectors (builds XPath when multiple specified).

        Args:
            id: Element ID attribute value.
            class_name: CSS class name to match.
            name: Element name attribute value.
            tag_name: HTML tag name (e.g., "div", "input").
            text: Text content to match within element.
            timeout: Maximum seconds to wait for elements to appear.
            find_all: If True, returns all matches; if False, first match only.
            raise_exc: Whether to raise exception if no elements found.
            **attributes: Additional HTML attributes to match.

        Returns:
            WebElement, list[WebElement], or None based on find_all and raise_exc.

        Raises:
            ValueError: If no search criteria provided.
            ElementNotFound: If no elements found and raise_exc=True.
            WaitElementTimeout: If timeout specified and no elements appear in time.
            NotImplementedError: If called on a ShadowRoot (use query() with CSS instead).
        """
        return mapping.from_impl(self._run(cast('Any', self._impl).find(id=mapping.to_impl(id), class_name=mapping.to_impl(class_name), name=mapping.to_impl(name), tag_name=mapping.to_impl(tag_name), text=mapping.to_impl(text), timeout=mapping.to_impl(timeout), find_all=mapping.to_impl(find_all), raise_exc=mapping.to_impl(raise_exc), **{kwarg: mapping.to_impl(kwarg_value) for kwarg, kwarg_value in attributes.items()})))

    @overload
    def query(self, expression: str, timeout: int=..., find_all: Literal[False]=False, raise_exc: Literal[True]=True) -> WebElement: ...
    @overload
    def query(self, expression: str, timeout: int=..., find_all: Literal[False]=False, raise_exc: Literal[False]=False) -> WebElement | None: ...
    @overload
    def query(self, expression: str, timeout: int=..., find_all: Literal[True]=True, raise_exc: Literal[True]=True) -> list[WebElement]: ...
    @overload
    def query(self, expression: str, timeout: int=..., find_all: Literal[True]=True, raise_exc: Literal[False]=False) -> list[WebElement] | None: ...
    @overload
    def query(self, expression: str, timeout: int=..., find_all: bool=..., raise_exc: bool=...) -> WebElement | list[WebElement] | None: ...
    def query(self, expression: str, timeout: int=0, find_all: bool=False, raise_exc: bool=True) -> WebElement | list[WebElement] | None:
        """
        Find element(s) using raw CSS selector or XPath expression.

        Direct access using CSS or XPath syntax. Selector type automatically
        determined based on expression pattern.

        Args:
            expression: Selector expression (CSS, XPath, ID with #, class with .).
            timeout: Maximum seconds to wait for elements to appear.
            find_all: If True, returns all matches; if False, first match only.
            raise_exc: Whether to raise exception if no elements found.

        Returns:
            WebElement, list[WebElement], or None based on find_all and raise_exc.

        Raises:
            ElementNotFound: If no elements found and raise_exc=True.
            WaitElementTimeout: If timeout specified and no elements appear in time.
            NotImplementedError: If called with XPath on a ShadowRoot.
        """
        return mapping.from_impl(self._run(cast('Any', self._impl).query(expression=mapping.to_impl(expression), timeout=mapping.to_impl(timeout), find_all=mapping.to_impl(find_all), raise_exc=mapping.to_impl(raise_exc))))

    def query_script(self, function_declaration: str, arguments: list[CallArgument] | None=None, execution_context_id: int | None=None) -> list[WebElement]:
        """
        Run a JavaScript function that returns elements and wrap them as WebElements.

        The function runs with the search root bound to ``this`` (``document`` on a
        Tab, the frame document on an iframe element, the element itself on a
        WebElement, the root on a ShadowRoot) in the same execution context and
        iframe routing that ``query()`` uses. It may return a single Element, a
        NodeList, an array of Elements, or ``null``.

        Args:
            function_declaration: JavaScript function source, e.g.
                ``function(tag) { return this.querySelectorAll(tag); }``.
            arguments: CDP call arguments passed positionally to the function.
            execution_context_id: Run in this execution context of the frame (for
                example an isolated world created with ``Page.createIsolatedWorld``)
                with ``this`` bound to that context's ``document``. Ignored when the
                root is a non-iframe element, whose object id already fixes the context.

        Returns:
            WebElements for every element the function returned, in return order.

        Raises:
            ScriptException: If the function throws or fails to compile.
            CommandFailed: If the browser rejects the command itself.
        """
        return mapping.from_impl(self._run(self._impl.query_script(function_declaration=mapping.to_impl(function_declaration), arguments=mapping.to_impl(arguments), execution_context_id=mapping.to_impl(execution_context_id))))

    def execute_command(self, command: Command[T_CommandParams, T_CommandResponse], timeout: int=60) -> T_CommandResponse:
        """
        Send a raw CDP command through this object's session.

        The command is routed exactly like the object's own operations: a Tab
        sends it to the page session, a WebElement inside an out-of-process
        iframe sends it to that frame's session. Build commands with the
        factories in ``pydoll.commands`` or pass a plain ``{'method': ..., 'params': ...}``
        dict for methods pydoll does not wrap.

        Args:
            command: CDP command to send.
            timeout: Seconds to wait for the browser's answer.

        Returns:
            The browser's response, with the domain result under ``'result'``.

        Raises:
            CommandFailed: If the browser answers with an error.
            CommandExecutionTimeout: If no answer arrives within ``timeout``.
        """
        return mapping.from_impl(self._run(self._impl.execute_command(command=mapping.to_impl(command), timeout=mapping.to_impl(timeout))))

class DownloadHandle(SyncBase):
    """Handle returned by expect_download to access the downloaded file."""
    _impl: _DownloadHandleImpl

    @property
    def file_path(self) -> str | None:
        return mapping.from_impl(self._impl.file_path)

    def wait_started(self, timeout: float | None=None) -> None:
        self._run(self._impl.wait_started(timeout=mapping.to_impl(timeout)))

    def wait_finished(self, timeout: float | None=None) -> None:
        self._run(self._impl.wait_finished(timeout=mapping.to_impl(timeout)))

    def read_bytes(self) -> bytes:
        return mapping.from_impl(self._run(self._impl.read_bytes()))

    def read_base64(self) -> str:
        return mapping.from_impl(self._run(self._impl.read_base64()))

class RequestHandle(SyncBase):
    """What ``expect_request()`` captured: filled when its block exits."""
    _impl: _RequestHandleImpl

    @property
    def request_id(self) -> str:
        """CDP request id, usable with ``tab.get_network_response_body()``."""
        return mapping.from_impl(self._impl.request_id)

    @property
    def url(self) -> str:
        return mapping.from_impl(self._impl.url)

    @property
    def method(self) -> str:
        return mapping.from_impl(self._impl.method)

    @property
    def headers(self) -> dict[str, str]:
        return mapping.from_impl(self._impl.headers)

    @property
    def post_data(self) -> str | None:
        """The request body, when it had one."""
        return mapping.from_impl(self._impl.post_data)

    @property
    def resource_type(self) -> str | None:
        """Chrome's resource type: Document, XHR, Fetch, Image, ..."""
        return mapping.from_impl(self._impl.resource_type)

class ResponseHandle(SyncBase):
    """What ``expect_response()`` captured: filled, body included, when its block exits."""
    _impl: _ResponseHandleImpl

    @property
    def request_id(self) -> str:
        return mapping.from_impl(self._impl.request_id)

    @property
    def url(self) -> str:
        return mapping.from_impl(self._impl.url)

    @property
    def status(self) -> int:
        return mapping.from_impl(self._impl.status)

    @property
    def ok(self) -> bool:
        """True for a 2xx status."""
        return mapping.from_impl(self._impl.ok)

    @property
    def headers(self) -> dict[str, str]:
        return mapping.from_impl(self._impl.headers)

    @property
    def mime_type(self) -> str:
        return mapping.from_impl(self._impl.mime_type)

    def body(self) -> bytes:
        """The raw body, empty for a 204, 205 or 304.

        Raises when loading failed, so there was no body to read.
        """
        return mapping.from_impl(self._impl.body())

    def text(self, encoding: str='utf-8') -> str:
        return mapping.from_impl(self._impl.text(encoding=mapping.to_impl(encoding)))

    def json(self) -> Any:
        return mapping.from_impl(self._impl.json())

class WebElement(SyncBase):
    """
    DOM element wrapper for browser automation.

    Provides comprehensive functionality for element interaction, inspection,
    and manipulation using Chrome DevTools Protocol commands.
    """
    _impl: _WebElementImpl

    @property
    def attributes(self) -> dict[str, str]:
        """Read-only copy of the element's cached attributes."""
        return mapping.from_impl(self._impl.attributes)

    @property
    def value(self) -> str | None:
        """Element's value attribute (for form elements)."""
        return mapping.from_impl(self._impl.value)

    @property
    def class_name(self) -> str | None:
        """Element's CSS class name(s)."""
        return mapping.from_impl(self._impl.class_name)

    @property
    def id(self) -> str | None:
        """Element's ID attribute."""
        return mapping.from_impl(self._impl.id)

    @property
    def tag_name(self) -> str | None:
        """Element's HTML tag name."""
        return mapping.from_impl(self._impl.tag_name)

    @property
    def is_iframe(self) -> bool:
        """Whether the element represents an iframe."""
        return mapping.from_impl(self._impl.is_iframe)

    @property
    def is_enabled(self) -> bool:
        """Whether element is enabled (not disabled)."""
        return mapping.from_impl(self._impl.is_enabled)

    def text(self) -> str:
        """Visible text content of the element."""
        return mapping.from_impl(self._run(self._impl.text()))

    def bounds(self) -> Quad:
        """
        Element's bounding box coordinates.

        Returns coordinates in CSS pixels relative to document origin.
        """
        return mapping.from_impl(self._run(self._impl.bounds()))

    def inner_html(self) -> str:
        return mapping.from_impl(self._run(self._impl.inner_html()))

    def iframe_context(self) -> IFrameContext | None:
        """
        Return the resolved iframe context for this element when it is an ``<iframe>``.

        The context includes: frame_id, document_url, execution_context_id,
        document_object_id and, for OOPIF targets, the session_id and
        session_handler used for routing commands. A context resolved earlier is
        reused while it still describes the frame's current document, so the
        elements already found inside the frame keep a live session; after a
        navigation or reload it is resolved afresh and the old one is closed.
        Non-iframe elements return None.

        Returns:
            IFrameContext | None: Resolved iframe context or None for non-iframes.
        """
        return mapping.from_impl(self._run(self._impl.iframe_context()))

    def get_attribute(self, name: str) -> str | None:
        """
        Get element attribute value.

        Note:
            Only provides attributes available when element was located.
            For dynamic attributes, consider using JavaScript execution.
        """
        return mapping.from_impl(self._impl.get_attribute(name=mapping.to_impl(name)))

    def get_bounds_using_js(self) -> dict[str, int]:
        """
        Get element bounds using JavaScript getBoundingClientRect().

        Returns coordinates relative to viewport (alternative to bounds property).
        """
        return mapping.from_impl(self._run(self._impl.get_bounds_using_js()))

    def get_parent_element(self) -> WebElement:
        """Element's parent element."""
        return mapping.from_impl(self._run(self._impl.get_parent_element()))

    def get_shadow_root(self, timeout: float=0) -> ShadowRoot:
        """
        Get the shadow root attached to this element.

        Args:
            timeout: Maximum seconds to wait for the shadow root to appear.
                When > 0, repeatedly polls (starting every 20 ms and backing off to
                250 ms) until a shadow root is found or the timeout expires.

        Returns:
            ShadowRoot instance for traversing the shadow DOM.

        Raises:
            ShadowRootNotFound: If no shadow root is attached (when timeout=0).
            WaitElementTimeout: If timeout > 0 and no shadow root appears
                within the specified duration.
        """
        return mapping.from_impl(self._run(self._impl.get_shadow_root(timeout=mapping.to_impl(timeout))))

    def get_children_elements(self, max_depth: int=1, tag_filter: list[str]=[], raise_exc: bool=False) -> list[WebElement]:
        """
        Retrieve all direct and nested child elements of this element.

        Args:
            max_depth (int, optional): Maximum depth to traverse when finding children.
                Defaults to 1 for direct children only.
            tag_filter (list[str], optional): List of HTML tag names to filter results.
                If empty, returns all child elements regardless of tag. Defaults to [].

        Returns:
            list[WebElement]: List of child WebElement objects found within the specified
                depth and matching the tag filter criteria.

        Raises:
            ElementNotFound: If no child elements are found for this element and raise_exc is True.
        """
        return mapping.from_impl(self._run(self._impl.get_children_elements(max_depth=mapping.to_impl(max_depth), tag_filter=mapping.to_impl(tag_filter), raise_exc=mapping.to_impl(raise_exc))))

    def get_siblings_elements(self, tag_filter: list[str]=[], raise_exc: bool=False) -> list[WebElement]:
        """
        Retrieve all sibling elements of this element (elements at the same DOM level).

        Args:
            tag_filter (list[str], optional): List of HTML tag names to filter results.
                If empty, returns all sibling elements regardless of tag. Defaults to [].

        Returns:
            list[WebElement]: List of sibling WebElement objects that share the same
                parent as this element and match the tag filter criteria.

        Raises:
            ElementNotFound: If no sibling elements are found for this element
            and raise_exc is True.
        """
        return mapping.from_impl(self._run(self._impl.get_siblings_elements(tag_filter=mapping.to_impl(tag_filter), raise_exc=mapping.to_impl(raise_exc))))

    def take_screenshot(self, path: str | Path | None=None, quality: int=100, as_base64: bool=False) -> str | None:
        """
        Capture screenshot of this element only.

        Automatically scrolls element into view before capturing.

        Args:
            path: File path for screenshot (extension determines format).
            quality: Image quality 0-100 (default 100).
            as_base64: Return as base64 string instead of saving file.

        Returns:
            Base64 screenshot data if as_base64=True, None otherwise.

        Raises:
            InvalidFileExtension: If file extension not supported.
            MissingScreenshotPath: If path is None and as_base64 is False.
        """
        return mapping.from_impl(self._run(self._impl.take_screenshot(path=mapping.to_impl(path), quality=mapping.to_impl(quality), as_base64=mapping.to_impl(as_base64))))

    def scroll_into_view(self):
        """Scroll element into the viewport, keeping a margin from every edge.

        ``DOM.scrollIntoViewIfNeeded`` aligns a partially visible element with the
        closest viewport edge. That leaves it under the overlay scrollbar the scroll
        itself reveals on macOS, so the mouse events that follow land on the
        scrollbar instead of the element. Asking for the element's box plus a
        margin keeps it clear of the edges. When the box cannot be read the plain
        behaviour is kept.
        """
        return mapping.from_impl(self._run(self._impl.scroll_into_view()))

    def wait_until(self, *, is_visible: bool=False, is_interactable: bool=False, is_hidden: bool=False, is_detached: bool=False, is_enabled: bool=False, timeout: float=0):
        """Wait for the element to meet every condition you set to True.

        ``is_visible`` and ``is_interactable`` wait for the element to show up
        and accept input; ``is_hidden`` waits for it to leave the screen (a
        spinner finishing), ``is_detached`` for it to leave the DOM, and
        ``is_enabled`` for its ``disabled`` attribute to be cleared. With the
        default ``timeout`` of 0 the conditions are checked once.

        Raises:
            ValueError: If no condition is set to True.
            WaitElementTimeout: If the conditions are not all met within ``timeout``.
        """
        return mapping.from_impl(self._run(self._impl.wait_until(is_visible=mapping.to_impl(is_visible), is_interactable=mapping.to_impl(is_interactable), is_hidden=mapping.to_impl(is_hidden), is_detached=mapping.to_impl(is_detached), is_enabled=mapping.to_impl(is_enabled), timeout=mapping.to_impl(timeout))))

    def click_using_js(self):
        """
        Click element using JavaScript click() method.

        Raises:
            ElementNotVisible: If element is not visible.
            ElementNotInteractable: If element couldn't be clicked.

        Note:
            For <option> elements, uses specialized selection approach.
            Element is automatically scrolled into view.
        """
        return mapping.from_impl(self._run(self._impl.click_using_js()))

    def click(self, x_offset: int=0, y_offset: int=0, hold_time: float=0, humanize: bool=False):
        """
        Click element using simulated mouse events.

        Args:
            x_offset: Horizontal offset from element center.
            y_offset: Vertical offset from element center.
            hold_time: Seconds to keep the button down between press and release
                (used when humanize=False). Zero by default, so a plain click is
                two back-to-back events; pass humanize=True for human timing.
            humanize: When True and a Mouse instance is available, uses humanized
                Bezier curve movement from the current tracked position to the
                element center before clicking. When False, dispatches raw CDP
                mousePressed/mouseReleased events directly.

        Raises:
            ElementNotVisible: If element is not visible.

        Note:
            For <option> elements, delegates to specialized JavaScript approach.
            Element is automatically scrolled into view.
        """
        return mapping.from_impl(self._run(self._impl.click(x_offset=mapping.to_impl(x_offset), y_offset=mapping.to_impl(y_offset), hold_time=mapping.to_impl(hold_time), humanize=mapping.to_impl(humanize))))

    def hover(self, x_offset: int=0, y_offset: int=0, humanize: bool=False):
        """
        Move the mouse over the element without clicking.

        Scrolls the element into view and moves the pointer to its center plus
        the offsets, so hover styles, tooltips and menus that open on
        ``mouseover`` react as they would for a person.

        Args:
            x_offset: Horizontal offset from the element center.
            y_offset: Vertical offset from the element center.
            humanize: Move along a curved path with human timing instead of
                jumping straight to the point.

        Raises:
            ElementNotVisible: If the element is not visible.
        """
        return mapping.from_impl(self._run(self._impl.hover(x_offset=mapping.to_impl(x_offset), y_offset=mapping.to_impl(y_offset), humanize=mapping.to_impl(humanize))))

    def double_click(self, x_offset: int=0, y_offset: int=0, humanize: bool=False):
        """
        Double-click the element.

        Sends the two press-and-release pairs a real double click produces,
        with the second pair carrying ``clickCount=2``, so the page receives
        ``dblclick`` as well as the two ``click`` events.

        Args:
            x_offset: Horizontal offset from the element center.
            y_offset: Vertical offset from the element center.
            humanize: Move the mouse along a curved path before clicking.

        Raises:
            ElementNotVisible: If the element is not visible.
        """
        return mapping.from_impl(self._run(self._impl.double_click(x_offset=mapping.to_impl(x_offset), y_offset=mapping.to_impl(y_offset), humanize=mapping.to_impl(humanize))))

    def focus(self):
        """Focus this element via CDP DOM.focus command."""
        return mapping.from_impl(self._run(self._impl.focus()))

    def clear(self):
        """
        Clear the current value of the element.

        Supports standard inputs, textareas, and contenteditable elements.
        Dispatches ``input`` and ``change`` events so frameworks detect the update.

        Raises:
            ElementNotInteractable: If the element does not accept text input.
        """
        return mapping.from_impl(self._run(self._impl.clear()))

    def insert_text(self, text: str):
        """
        Insert text into element using JavaScript.

        Supports standard inputs, textareas, contenteditable elements, and rich text editors.
        Inserts text at cursor position or replaces selected text.

        Args:
            text: Text to insert.

        Raises:
            ElementNotInteractable: If element does not accept text input.

        Note:
            Uses JavaScript for maximum compatibility with all input types.
            Automatically handles input/textarea and contenteditable elements.
        """
        return mapping.from_impl(self._run(self._impl.insert_text(text=mapping.to_impl(text))))

    def set_input_files(self, files: str | Path | list[str | Path]):
        """
        Set file paths for file input element.

        Args:
            files: list of absolute file paths to existing files.

        Raises:
            ElementNotAFileInput: If element is not a file input.
        """
        return mapping.from_impl(self._run(self._impl.set_input_files(files=mapping.to_impl(files))))

    def type_text(self, text: str, humanize: bool=False):
        """
        Type text character by character.

        Args:
            text: Text to type into the element.
            humanize: When True, simulates human-like typing.
        """
        return mapping.from_impl(self._run(self._impl.type_text(text=mapping.to_impl(text), humanize=mapping.to_impl(humanize))))

    def is_editable(self) -> bool:
        """
        Check if element can accept text input.

        Returns:
            True if element is editable (input, textarea, or contenteditable).
        """
        return mapping.from_impl(self._run(self._impl.is_editable()))

    def is_visible(self):
        """Check if element is visible using comprehensive JavaScript visibility test."""
        return mapping.from_impl(self._run(self._impl.is_visible()))

    def is_detached(self) -> bool:
        """Whether the element is no longer part of a document (removed or replaced)."""
        return mapping.from_impl(self._run(self._impl.is_detached()))

    def is_on_top(self):
        """Check if element is topmost at its center point (not covered by overlays)."""
        return mapping.from_impl(self._run(self._impl.is_on_top()))

    def is_interactable(self):
        """Check if element is interactable based on visibility and position."""
        return mapping.from_impl(self._run(self._impl.is_interactable()))

    def execute_script(self, script: str, *, arguments: list[CallArgument] | None=None, silent: bool | None=None, return_by_value: bool | None=None, generate_preview: bool | None=None, user_gesture: bool | None=None, await_promise: bool | None=None, execution_context_id: int | None=None, object_group: str | None=None, throw_on_side_effect: bool | None=None, unique_context_id: str | None=None, serialization_options: SerializationOptions | None=None) -> CallFunctionOnResponse:
        """
        Execute JavaScript in element context.

        Args:
            script (str): JavaScript code to execute. Use 'this' to reference this element.
            arguments (list[CallArgument] | None): Arguments to pass to the function
                (Runtime.callFunctionOn).
            silent (bool | None): Whether to silence exceptions (Runtime.callFunctionOn).
            return_by_value (bool | None): Whether to return the result by value instead of
                reference (Runtime.callFunctionOn).
            generate_preview (bool | None): Whether to generate a preview for the result
                (Runtime.callFunctionOn).
            user_gesture (bool | None): Whether to treat the call as initiated by user
                gesture (Runtime.callFunctionOn).
            await_promise (bool | None): Whether to promise result
                (Runtime.callFunctionOn).
            execution_context_id (int | None): ID of the execution context to call the
                function in (Runtime.callFunctionOn).
            object_group (str | None): Symbolic group name for the result
                (Runtime.callFunctionOn).
            throw_on_side_effect (bool | None): Whether to throw if side effect cannot be
                ruled out (Runtime.callFunctionOn).
            unique_context_id (str | None): Unique context ID for the function call
                (Runtime.callFunctionOn).
            serialization_options (SerializationOptions | None): Serialization options for
                the result (Runtime.callFunctionOn).

        Returns:
            CallFunctionOnResponse: The result of the script execution.

        Examples:
            # Click the element
            element.execute_script('this.click()')

            # Modify element style
            element.execute_script('this.style.border = "2px solid red"')

            # Get element text
            result = element.execute_script('return this.textContent', return_by_value=True)

            # Set element content
            element.execute_script('this.textContent = "Hello World"')
        """
        return mapping.from_impl(self._run(self._impl.execute_script(script=mapping.to_impl(script), arguments=mapping.to_impl(arguments), silent=mapping.to_impl(silent), return_by_value=mapping.to_impl(return_by_value), generate_preview=mapping.to_impl(generate_preview), user_gesture=mapping.to_impl(user_gesture), await_promise=mapping.to_impl(await_promise), execution_context_id=mapping.to_impl(execution_context_id), object_group=mapping.to_impl(object_group), throw_on_side_effect=mapping.to_impl(throw_on_side_effect), unique_context_id=mapping.to_impl(unique_context_id), serialization_options=mapping.to_impl(serialization_options))))

    @overload
    def find(self, id: str | None=..., class_name: str | None=..., name: str | None=..., tag_name: str | None=..., text: str | None=..., timeout: int=..., find_all: Literal[False]=False, raise_exc: Literal[True]=True, **attributes) -> WebElement: ...
    @overload
    def find(self, id: str | None=..., class_name: str | None=..., name: str | None=..., tag_name: str | None=..., text: str | None=..., timeout: int=..., find_all: Literal[False]=False, raise_exc: Literal[False]=False, **attributes) -> WebElement | None: ...
    @overload
    def find(self, id: str | None=..., class_name: str | None=..., name: str | None=..., tag_name: str | None=..., text: str | None=..., timeout: int=..., find_all: Literal[True]=True, raise_exc: Literal[True]=True, **attributes) -> list[WebElement]: ...
    @overload
    def find(self, id: str | None=..., class_name: str | None=..., name: str | None=..., tag_name: str | None=..., text: str | None=..., timeout: int=..., find_all: Literal[True]=True, raise_exc: Literal[False]=False, **attributes) -> list[WebElement] | None: ...
    @overload
    def find(self, id: str | None=..., class_name: str | None=..., name: str | None=..., tag_name: str | None=..., text: str | None=..., timeout: int=..., find_all: bool=..., raise_exc: bool=..., **attributes) -> WebElement | list[WebElement] | None: ...
    def find(self, id: str | None=None, class_name: str | None=None, name: str | None=None, tag_name: str | None=None, text: str | None=None, timeout: int=0, find_all: bool=False, raise_exc: bool=True, **attributes: dict[str, str]) -> WebElement | list[WebElement] | None:
        """
        Find element(s) using combination of common HTML attributes.

        Flexible element location using standard attributes. Multiple attributes
        can be combined for specific selectors (builds XPath when multiple specified).

        Args:
            id: Element ID attribute value.
            class_name: CSS class name to match.
            name: Element name attribute value.
            tag_name: HTML tag name (e.g., "div", "input").
            text: Text content to match within element.
            timeout: Maximum seconds to wait for elements to appear.
            find_all: If True, returns all matches; if False, first match only.
            raise_exc: Whether to raise exception if no elements found.
            **attributes: Additional HTML attributes to match.

        Returns:
            WebElement, list[WebElement], or None based on find_all and raise_exc.

        Raises:
            ValueError: If no search criteria provided.
            ElementNotFound: If no elements found and raise_exc=True.
            WaitElementTimeout: If timeout specified and no elements appear in time.
            NotImplementedError: If called on a ShadowRoot (use query() with CSS instead).
        """
        return mapping.from_impl(self._run(cast('Any', self._impl).find(id=mapping.to_impl(id), class_name=mapping.to_impl(class_name), name=mapping.to_impl(name), tag_name=mapping.to_impl(tag_name), text=mapping.to_impl(text), timeout=mapping.to_impl(timeout), find_all=mapping.to_impl(find_all), raise_exc=mapping.to_impl(raise_exc), **{kwarg: mapping.to_impl(kwarg_value) for kwarg, kwarg_value in attributes.items()})))

    @overload
    def query(self, expression: str, timeout: int=..., find_all: Literal[False]=False, raise_exc: Literal[True]=True) -> WebElement: ...
    @overload
    def query(self, expression: str, timeout: int=..., find_all: Literal[False]=False, raise_exc: Literal[False]=False) -> WebElement | None: ...
    @overload
    def query(self, expression: str, timeout: int=..., find_all: Literal[True]=True, raise_exc: Literal[True]=True) -> list[WebElement]: ...
    @overload
    def query(self, expression: str, timeout: int=..., find_all: Literal[True]=True, raise_exc: Literal[False]=False) -> list[WebElement] | None: ...
    @overload
    def query(self, expression: str, timeout: int=..., find_all: bool=..., raise_exc: bool=...) -> WebElement | list[WebElement] | None: ...
    def query(self, expression: str, timeout: int=0, find_all: bool=False, raise_exc: bool=True) -> WebElement | list[WebElement] | None:
        """
        Find element(s) using raw CSS selector or XPath expression.

        Direct access using CSS or XPath syntax. Selector type automatically
        determined based on expression pattern.

        Args:
            expression: Selector expression (CSS, XPath, ID with #, class with .).
            timeout: Maximum seconds to wait for elements to appear.
            find_all: If True, returns all matches; if False, first match only.
            raise_exc: Whether to raise exception if no elements found.

        Returns:
            WebElement, list[WebElement], or None based on find_all and raise_exc.

        Raises:
            ElementNotFound: If no elements found and raise_exc=True.
            WaitElementTimeout: If timeout specified and no elements appear in time.
            NotImplementedError: If called with XPath on a ShadowRoot.
        """
        return mapping.from_impl(self._run(cast('Any', self._impl).query(expression=mapping.to_impl(expression), timeout=mapping.to_impl(timeout), find_all=mapping.to_impl(find_all), raise_exc=mapping.to_impl(raise_exc))))

    def query_script(self, function_declaration: str, arguments: list[CallArgument] | None=None, execution_context_id: int | None=None) -> list[WebElement]:
        """
        Run a JavaScript function that returns elements and wrap them as WebElements.

        The function runs with the search root bound to ``this`` (``document`` on a
        Tab, the frame document on an iframe element, the element itself on a
        WebElement, the root on a ShadowRoot) in the same execution context and
        iframe routing that ``query()`` uses. It may return a single Element, a
        NodeList, an array of Elements, or ``null``.

        Args:
            function_declaration: JavaScript function source, e.g.
                ``function(tag) { return this.querySelectorAll(tag); }``.
            arguments: CDP call arguments passed positionally to the function.
            execution_context_id: Run in this execution context of the frame (for
                example an isolated world created with ``Page.createIsolatedWorld``)
                with ``this`` bound to that context's ``document``. Ignored when the
                root is a non-iframe element, whose object id already fixes the context.

        Returns:
            WebElements for every element the function returned, in return order.

        Raises:
            ScriptException: If the function throws or fails to compile.
            CommandFailed: If the browser rejects the command itself.
        """
        return mapping.from_impl(self._run(self._impl.query_script(function_declaration=mapping.to_impl(function_declaration), arguments=mapping.to_impl(arguments), execution_context_id=mapping.to_impl(execution_context_id))))

    def execute_command(self, command: Command[T_CommandParams, T_CommandResponse], timeout: int=60) -> T_CommandResponse:
        """
        Send a raw CDP command through this object's session.

        The command is routed exactly like the object's own operations: a Tab
        sends it to the page session, a WebElement inside an out-of-process
        iframe sends it to that frame's session. Build commands with the
        factories in ``pydoll.commands`` or pass a plain ``{'method': ..., 'params': ...}``
        dict for methods pydoll does not wrap.

        Args:
            command: CDP command to send.
            timeout: Seconds to wait for the browser's answer.

        Returns:
            The browser's response, with the domain result under ``'result'``.

        Raises:
            CommandFailed: If the browser answers with an error.
            CommandExecutionTimeout: If no answer arrives within ``timeout``.
        """
        return mapping.from_impl(self._run(self._impl.execute_command(command=mapping.to_impl(command), timeout=mapping.to_impl(timeout))))

class ShadowRoot(SyncBase):
    """
    Shadow root wrapper for shadow DOM traversal.

    Provides element finding capabilities within shadow DOM boundaries
    using query() with CSS selectors. Use query() instead of find() —
    find() and XPath are not supported inside shadow roots.

    Usage:
        shadow_host = tab.find(id='my-component')
        shadow_root = shadow_host.get_shadow_root()
        button = shadow_root.query('#internal-button')
        button.click()
    """
    _impl: _ShadowRootImpl

    @property
    def mode(self) -> ShadowRootType:
        """Shadow root mode (open, closed, or user-agent)."""
        return mapping.from_impl(self._impl.mode)

    @property
    def host_element(self) -> WebElement | None:
        """Reference to the shadow host element, if available."""
        return mapping.from_impl(self._impl.host_element)

    def inner_html(self) -> str:
        """HTML content of the shadow root."""
        return mapping.from_impl(self._run(self._impl.inner_html()))

    @overload
    def find(self, id: str | None=..., class_name: str | None=..., name: str | None=..., tag_name: str | None=..., text: str | None=..., timeout: int=..., find_all: Literal[False]=False, raise_exc: Literal[True]=True, **attributes) -> WebElement: ...
    @overload
    def find(self, id: str | None=..., class_name: str | None=..., name: str | None=..., tag_name: str | None=..., text: str | None=..., timeout: int=..., find_all: Literal[False]=False, raise_exc: Literal[False]=False, **attributes) -> WebElement | None: ...
    @overload
    def find(self, id: str | None=..., class_name: str | None=..., name: str | None=..., tag_name: str | None=..., text: str | None=..., timeout: int=..., find_all: Literal[True]=True, raise_exc: Literal[True]=True, **attributes) -> list[WebElement]: ...
    @overload
    def find(self, id: str | None=..., class_name: str | None=..., name: str | None=..., tag_name: str | None=..., text: str | None=..., timeout: int=..., find_all: Literal[True]=True, raise_exc: Literal[False]=False, **attributes) -> list[WebElement] | None: ...
    @overload
    def find(self, id: str | None=..., class_name: str | None=..., name: str | None=..., tag_name: str | None=..., text: str | None=..., timeout: int=..., find_all: bool=..., raise_exc: bool=..., **attributes) -> WebElement | list[WebElement] | None: ...
    def find(self, id: str | None=None, class_name: str | None=None, name: str | None=None, tag_name: str | None=None, text: str | None=None, timeout: int=0, find_all: bool=False, raise_exc: bool=True, **attributes: dict[str, str]) -> WebElement | list[WebElement] | None:
        """
        Find element(s) using combination of common HTML attributes.

        Flexible element location using standard attributes. Multiple attributes
        can be combined for specific selectors (builds XPath when multiple specified).

        Args:
            id: Element ID attribute value.
            class_name: CSS class name to match.
            name: Element name attribute value.
            tag_name: HTML tag name (e.g., "div", "input").
            text: Text content to match within element.
            timeout: Maximum seconds to wait for elements to appear.
            find_all: If True, returns all matches; if False, first match only.
            raise_exc: Whether to raise exception if no elements found.
            **attributes: Additional HTML attributes to match.

        Returns:
            WebElement, list[WebElement], or None based on find_all and raise_exc.

        Raises:
            ValueError: If no search criteria provided.
            ElementNotFound: If no elements found and raise_exc=True.
            WaitElementTimeout: If timeout specified and no elements appear in time.
            NotImplementedError: If called on a ShadowRoot (use query() with CSS instead).
        """
        return mapping.from_impl(self._run(cast('Any', self._impl).find(id=mapping.to_impl(id), class_name=mapping.to_impl(class_name), name=mapping.to_impl(name), tag_name=mapping.to_impl(tag_name), text=mapping.to_impl(text), timeout=mapping.to_impl(timeout), find_all=mapping.to_impl(find_all), raise_exc=mapping.to_impl(raise_exc), **{kwarg: mapping.to_impl(kwarg_value) for kwarg, kwarg_value in attributes.items()})))

    @overload
    def query(self, expression: str, timeout: int=..., find_all: Literal[False]=False, raise_exc: Literal[True]=True) -> WebElement: ...
    @overload
    def query(self, expression: str, timeout: int=..., find_all: Literal[False]=False, raise_exc: Literal[False]=False) -> WebElement | None: ...
    @overload
    def query(self, expression: str, timeout: int=..., find_all: Literal[True]=True, raise_exc: Literal[True]=True) -> list[WebElement]: ...
    @overload
    def query(self, expression: str, timeout: int=..., find_all: Literal[True]=True, raise_exc: Literal[False]=False) -> list[WebElement] | None: ...
    @overload
    def query(self, expression: str, timeout: int=..., find_all: bool=..., raise_exc: bool=...) -> WebElement | list[WebElement] | None: ...
    def query(self, expression: str, timeout: int=0, find_all: bool=False, raise_exc: bool=True) -> WebElement | list[WebElement] | None:
        """
        Find element(s) using raw CSS selector or XPath expression.

        Direct access using CSS or XPath syntax. Selector type automatically
        determined based on expression pattern.

        Args:
            expression: Selector expression (CSS, XPath, ID with #, class with .).
            timeout: Maximum seconds to wait for elements to appear.
            find_all: If True, returns all matches; if False, first match only.
            raise_exc: Whether to raise exception if no elements found.

        Returns:
            WebElement, list[WebElement], or None based on find_all and raise_exc.

        Raises:
            ElementNotFound: If no elements found and raise_exc=True.
            WaitElementTimeout: If timeout specified and no elements appear in time.
            NotImplementedError: If called with XPath on a ShadowRoot.
        """
        return mapping.from_impl(self._run(cast('Any', self._impl).query(expression=mapping.to_impl(expression), timeout=mapping.to_impl(timeout), find_all=mapping.to_impl(find_all), raise_exc=mapping.to_impl(raise_exc))))

    def query_script(self, function_declaration: str, arguments: list[CallArgument] | None=None, execution_context_id: int | None=None) -> list[WebElement]:
        """
        Run a JavaScript function that returns elements and wrap them as WebElements.

        The function runs with the search root bound to ``this`` (``document`` on a
        Tab, the frame document on an iframe element, the element itself on a
        WebElement, the root on a ShadowRoot) in the same execution context and
        iframe routing that ``query()`` uses. It may return a single Element, a
        NodeList, an array of Elements, or ``null``.

        Args:
            function_declaration: JavaScript function source, e.g.
                ``function(tag) { return this.querySelectorAll(tag); }``.
            arguments: CDP call arguments passed positionally to the function.
            execution_context_id: Run in this execution context of the frame (for
                example an isolated world created with ``Page.createIsolatedWorld``)
                with ``this`` bound to that context's ``document``. Ignored when the
                root is a non-iframe element, whose object id already fixes the context.

        Returns:
            WebElements for every element the function returned, in return order.

        Raises:
            ScriptException: If the function throws or fails to compile.
            CommandFailed: If the browser rejects the command itself.
        """
        return mapping.from_impl(self._run(self._impl.query_script(function_declaration=mapping.to_impl(function_declaration), arguments=mapping.to_impl(arguments), execution_context_id=mapping.to_impl(execution_context_id))))

    def execute_command(self, command: Command[T_CommandParams, T_CommandResponse], timeout: int=60) -> T_CommandResponse:
        """
        Send a raw CDP command through this object's session.

        The command is routed exactly like the object's own operations: a Tab
        sends it to the page session, a WebElement inside an out-of-process
        iframe sends it to that frame's session. Build commands with the
        factories in ``pydoll.commands`` or pass a plain ``{'method': ..., 'params': ...}``
        dict for methods pydoll does not wrap.

        Args:
            command: CDP command to send.
            timeout: Seconds to wait for the browser's answer.

        Returns:
            The browser's response, with the domain result under ``'result'``.

        Raises:
            CommandFailed: If the browser answers with an error.
            CommandExecutionTimeout: If no answer arrives within ``timeout``.
        """
        return mapping.from_impl(self._run(self._impl.execute_command(command=mapping.to_impl(command), timeout=mapping.to_impl(timeout))))

class Keyboard(SyncBase):
    """
    Keyboard input controller for Tab and WebElement.

    Provides methods for:
    - Tab: Public keyboard simulation (press, down, up, hotkey)
    - WebElement: Private text typing with optional humanization
    """
    _impl: _KeyboardImpl
    PAUSE_CHARS = _KeyboardImpl.PAUSE_CHARS

    def press(self, key: Key, modifiers: KeyModifier | None=None, interval: float=0):
        """
        Press and release a key (down + optional hold + up).

        Args:
            key: Key to press (from Key enum).
            modifiers: Optional key modifiers (Alt=1, Ctrl=2, Meta=4, Shift=8).
            interval: Seconds to keep the key down. Zero by default, so the
                release follows the press immediately.

        Example:
            tab.keyboard.press(Key.ENTER)
            tab.keyboard.press(Key.A, modifiers=KeyModifier.CTRL)
        """
        return mapping.from_impl(self._run(self._impl.press(key=mapping.to_impl(key), modifiers=mapping.to_impl(modifiers), interval=mapping.to_impl(interval))))

    def down(self, key: Key, modifiers: KeyModifier | None=None):
        """
        Press a key down (without releasing).

        Args:
            key: Key to press down (from Key enum).
            modifiers: Optional key modifiers.
        """
        return mapping.from_impl(self._run(self._impl.down(key=mapping.to_impl(key), modifiers=mapping.to_impl(modifiers))))

    def up(self, key: Key):
        """
        Release a key (key up event).

        Args:
            key: Key to release (from Key enum).
        """
        return mapping.from_impl(self._run(self._impl.up(key=mapping.to_impl(key))))

    def hotkey(self, key1: Key, key2: Key, key3: Key | None=None):
        """
        Execute a key combination (hotkey) with up to 3 keys.

        Args:
            key1: First key (usually a modifier like Ctrl, Shift, Alt).
            key2: Second key.
            key3: Optional third key.

        Example:
            tab.keyboard.hotkey(Key.CONTROL, Key.C)  # Ctrl+C
        """
        return mapping.from_impl(self._run(self._impl.hotkey(key1=mapping.to_impl(key1), key2=mapping.to_impl(key2), key3=mapping.to_impl(key3))))

    def type_text(self, text: str, humanize: bool=False):
        """
        Type text character by character.

        The plain path focuses the element once and sends every key event in
        one batch, so a page that moves focus mid-typing receives the rest of
        the text wherever focus went; the humanized path re-focuses before
        each character.

        Args:
            text: Text to type.
            humanize: When True, simulates human-like typing with
                variable delays and occasional typos (~2%).

        Example:
            tab.keyboard.type_text("Hello World", humanize=True)
            tab.keyboard.type_text("Hello World")
        """
        return mapping.from_impl(self._run(self._impl.type_text(text=mapping.to_impl(text), humanize=mapping.to_impl(humanize))))

class Mouse(SyncBase):
    """
    Mouse input controller with realistic humanized simulation.

    Provides methods for mouse movement, clicking, double-clicking,
    and dragging with optional humanized simulation using Bezier curves,
    Fitts's Law timing, minimum-jerk velocity profiles, physiological
    tremor, and overshoot correction.

    A mouse belongs to one CDP session: the tab's for the main document and
    its same-process iframes, or an out-of-process iframe's own session, which
    has its own viewport coordinates. Elements pick the mouse of their frame,
    so the cursor position it tracks always lives in the coordinate space the
    events are dispatched in. Intermediate humanized moves are sent without
    waiting for their answers, so the cadence between two moves is the frame
    interval rather than the frame interval plus a network round trip.
    """
    _impl: _MouseImpl

    @property
    def connection_handler(self) -> ConnectionHandler:
        """The connection this mouse dispatches its events through."""
        return mapping.from_impl(self._impl.connection_handler)

    @property
    def session_id(self) -> str | None:
        """The flattened CDP session this mouse addresses, if any."""
        return mapping.from_impl(self._impl.session_id)

    @property
    def timing(self) -> MouseTimingConfig:
        """Current timing configuration for humanized movement."""
        return mapping.from_impl(self._impl.timing)
    @timing.setter
    def timing(self, config: MouseTimingConfig) -> None:
        self._impl.timing = mapping.to_impl(config)

    @property
    def debug(self) -> bool:
        """Whether to draw debug dots on the page."""
        return mapping.from_impl(self._impl.debug)
    @debug.setter
    def debug(self, value: bool) -> None:
        self._impl.debug = mapping.to_impl(value)

    def move(self, x: float, y: float, *, humanize: bool=False) -> None:
        """
        Move mouse cursor to the specified position.

        Args:
            x: Target X coordinate (CSS pixels).
            y: Target Y coordinate (CSS pixels).
            humanize: Simulate human-like curved movement with natural timing.
        """
        self._run(self._impl.move(x=mapping.to_impl(x), y=mapping.to_impl(y), humanize=mapping.to_impl(humanize)))

    def click(self, x: float, y: float, *, button: MouseButton=MouseButton.LEFT, click_count: int=1, humanize: bool=False) -> None:
        """
        Click at the specified position.

        Args:
            x: Target X coordinate (CSS pixels).
            y: Target Y coordinate (CSS pixels).
            button: Mouse button to click.
            click_count: Number of clicks (2 for double-click).
            humanize: Simulate human-like movement and click timing.
        """
        self._run(self._impl.click(x=mapping.to_impl(x), y=mapping.to_impl(y), button=mapping.to_impl(button), click_count=mapping.to_impl(click_count), humanize=mapping.to_impl(humanize)))

    def double_click(self, x: float, y: float, *, button: MouseButton=MouseButton.LEFT, humanize: bool=False) -> None:
        """
        Double-click at the specified position.

        Args:
            x: Target X coordinate (CSS pixels).
            y: Target Y coordinate (CSS pixels).
            button: Mouse button to click.
            humanize: Simulate human-like movement and click timing.
        """
        self._run(self._impl.double_click(x=mapping.to_impl(x), y=mapping.to_impl(y), button=mapping.to_impl(button), humanize=mapping.to_impl(humanize)))

    def down(self, button: MouseButton=MouseButton.LEFT) -> None:
        """
        Press mouse button down at the current position.

        Args:
            button: Mouse button to press.
        """
        self._run(self._impl.down(button=mapping.to_impl(button)))

    def up(self, button: MouseButton=MouseButton.LEFT) -> None:
        """
        Release mouse button at the current position.

        Args:
            button: Mouse button to release.
        """
        self._run(self._impl.up(button=mapping.to_impl(button)))

    def drag(self, start_x: float, start_y: float, end_x: float, end_y: float, *, humanize: bool=False) -> None:
        """
        Drag from one position to another.

        Args:
            start_x: Start X coordinate.
            start_y: Start Y coordinate.
            end_x: End X coordinate.
            end_y: End Y coordinate.
            humanize: Simulate human-like drag movement.
        """
        self._run(self._impl.drag(start_x=mapping.to_impl(start_x), start_y=mapping.to_impl(start_y), end_x=mapping.to_impl(end_x), end_y=mapping.to_impl(end_y), humanize=mapping.to_impl(humanize)))

class Scroll(SyncBase):
    """
    API for controlling page scroll behavior.

    Provides methods for scrolling the page in different directions,
    to specific positions, or by relative distances. Supports humanized
    scrolling with realistic physics simulation.
    """
    _impl: _ScrollImpl

    def by(self, position: ScrollPosition, distance: int | float, smooth: bool=True, humanize: bool=False):
        """
        Scroll the page by a relative distance in the specified direction.

        Args:
            position: Direction to scroll (UP, DOWN, LEFT, RIGHT).
            distance: Number of pixels to scroll.
            smooth: Use smooth scrolling animation if True, instant if False.
            humanize: Simulate human-like scrolling with momentum and inertia.
        """
        return mapping.from_impl(self._run(self._impl.by(position=mapping.to_impl(position), distance=mapping.to_impl(distance), smooth=mapping.to_impl(smooth), humanize=mapping.to_impl(humanize))))

    def to_top(self, smooth: bool=True, humanize: bool=False):
        """
        Scroll to the top of the page (Y=0).

        Args:
            smooth: Use smooth scrolling animation if True, instant if False.
            humanize: Simulate human-like scrolling with momentum and inertia.
        """
        return mapping.from_impl(self._run(self._impl.to_top(smooth=mapping.to_impl(smooth), humanize=mapping.to_impl(humanize))))

    def to_bottom(self, smooth: bool=True, humanize: bool=False):
        """
        Scroll to the bottom of the page (Y=document.body.scrollHeight).

        Args:
            smooth: Use smooth scrolling animation if True, instant if False.
            humanize: Simulate human-like scrolling with momentum and inertia.
        """
        return mapping.from_impl(self._run(self._impl.to_bottom(smooth=mapping.to_impl(smooth), humanize=mapping.to_impl(humanize))))

class Request(SyncBase):
    """High-level interface for making HTTP requests using the browser's fetch API.

    This class provides a requests-like interface that executes HTTP requests in the
    browser's JavaScript context. All requests inherit the browser's current session
    state including cookies, authentication headers, and other automatic browser
    behaviors. This allows for seamless interaction with websites that require
    authentication or have complex cookie management.

    Key Features:
    - Executes requests in the browser's JavaScript context using fetch API
    - Automatically includes browser cookies and session state
    - Preserves browser's security context and CORS policies
    - Captures both request and response headers for analysis
    - Supports all standard HTTP methods (GET, POST, PUT, DELETE, etc.)

    Note:
    - Headers passed to methods are additional headers, not replacements
    - Browser's automatic headers (User-Agent, Accept, etc.) are preserved
    - Cookies are managed automatically by the browser
    """
    _impl: _RequestImpl

    @property
    def tab(self) -> Any:
        return mapping.from_impl(self._impl.tab)

    @tab.setter
    def tab(self, value: Any) -> None:
        self._impl.tab = mapping.to_impl(value)

    def request(self, method: str, url: str, params: dict[str, str] | None=None, data: dict | list | tuple | str | bytes | None=None, json: dict[str, Any] | None=None, headers: list[HeaderEntry] | None=None, **kwargs) -> Response:
        """Execute an HTTP request in the browser's JavaScript context.

        This method uses the browser's fetch API to make requests, inheriting all
        browser session state including cookies, authentication, and security context.
        The request is executed as if made by the browser itself.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.). Case insensitive.
            url: Target URL for the request. Can be relative or absolute.
            params: Query parameters to append to the URL. These are URL-encoded
                and merged with any existing query string in the URL.
            data: Request body data. Behavior depends on type:
                - dict/list/tuple: URL-encoded as form data (application/x-www-form-urlencoded)
                - str/bytes: Sent as-is with no Content-Type modification
                Mutually exclusive with 'json' parameter.
            json: Data to be JSON-serialized as request body. Automatically sets
                Content-Type to application/json. Mutually exclusive with 'data'.
            headers: Additional headers to include. These are ADDED to browser's
                automatic headers, not replacements.
                Format: [{'name': 'X-Custom', 'value': 'value'}]
            **kwargs: Additional fetch API options (e.g., credentials, mode, cache).

        Returns:
            Response object containing status, headers, content, and cookies from
            both the request and response phases.

        Raises:
            HTTPError: If the request execution fails or network error occurs.

        Note:
            - Browser cookies are automatically included
            - CORS policies are enforced by the browser
            - Authentication headers are preserved from browser session
        """
        return mapping.from_impl(self._run(self._impl.request(method=mapping.to_impl(method), url=mapping.to_impl(url), params=mapping.to_impl(params), data=mapping.to_impl(data), json=mapping.to_impl(json), headers=mapping.to_impl(headers), **{kwarg: mapping.to_impl(kwarg_value) for kwarg, kwarg_value in kwargs.items()})))

    def get(self, url: str, params: dict[str, str] | None=None, **kwargs) -> Response:
        """Execute a GET request for retrieving data.

        Args:
            url: Target URL to retrieve data from.
            params: Query parameters to append to URL.
            **kwargs: Additional fetch options.

        Returns:
            Response object with retrieved data.
        """
        return mapping.from_impl(self._run(self._impl.get(url=mapping.to_impl(url), params=mapping.to_impl(params), **{kwarg: mapping.to_impl(kwarg_value) for kwarg, kwarg_value in kwargs.items()})))

    def post(self, url: str, data: dict | list | tuple | str | bytes | None=None, json: dict[str, Any] | None=None, **kwargs) -> Response:
        """Execute a POST request for creating or submitting data.

        Args:
            url: Target URL for data submission.
            data: Form data to submit (URL-encoded).
            json: JSON data to submit.
            **kwargs: Additional fetch options.

        Returns:
            Response object with server's response to the submission.
        """
        return mapping.from_impl(self._run(self._impl.post(url=mapping.to_impl(url), data=mapping.to_impl(data), json=mapping.to_impl(json), **{kwarg: mapping.to_impl(kwarg_value) for kwarg, kwarg_value in kwargs.items()})))

    def put(self, url: str, data: dict | list | tuple | str | bytes | None=None, json: dict[str, Any] | None=None, **kwargs) -> Response:
        """Execute a PUT request for updating/replacing resources.

        Args:
            url: Target URL of resource to update.
            data: Form data for the update.
            json: JSON data for the update.
            **kwargs: Additional fetch options.

        Returns:
            Response object confirming the update operation.
        """
        return mapping.from_impl(self._run(self._impl.put(url=mapping.to_impl(url), data=mapping.to_impl(data), json=mapping.to_impl(json), **{kwarg: mapping.to_impl(kwarg_value) for kwarg, kwarg_value in kwargs.items()})))

    def patch(self, url: str, data: dict | list | tuple | str | bytes | None=None, json: dict[str, Any] | None=None, **kwargs) -> Response:
        """Execute a PATCH request for partial resource updates.

        Args:
            url: Target URL of resource to partially update.
            data: Form data with changes to apply.
            json: JSON data with changes to apply.
            **kwargs: Additional fetch options.

        Returns:
            Response object confirming the partial update.
        """
        return mapping.from_impl(self._run(self._impl.patch(url=mapping.to_impl(url), data=mapping.to_impl(data), json=mapping.to_impl(json), **{kwarg: mapping.to_impl(kwarg_value) for kwarg, kwarg_value in kwargs.items()})))

    def delete(self, url: str, **kwargs) -> Response:
        """Execute a DELETE request for removing resources.

        Args:
            url: Target URL of resource to delete.
            **kwargs: Additional fetch options.

        Returns:
            Response object confirming the deletion.
        """
        return mapping.from_impl(self._run(self._impl.delete(url=mapping.to_impl(url), **{kwarg: mapping.to_impl(kwarg_value) for kwarg, kwarg_value in kwargs.items()})))

    def head(self, url: str, **kwargs) -> Response:
        """Execute a HEAD request to retrieve only response headers.

        Useful for checking resource existence, size, or modification date
        without downloading the full content.

        Args:
            url: Target URL to check headers for.
            **kwargs: Additional fetch options.

        Returns:
            Response object with headers but no body content.
        """
        return mapping.from_impl(self._run(self._impl.head(url=mapping.to_impl(url), **{kwarg: mapping.to_impl(kwarg_value) for kwarg, kwarg_value in kwargs.items()})))

    def options(self, url: str, **kwargs) -> Response:
        """Execute an OPTIONS request to check allowed methods and capabilities.

        Used for CORS preflight checks and discovering server capabilities.

        Args:
            url: Target URL to check options for.
            **kwargs: Additional fetch options.

        Returns:
            Response object with allowed methods and CORS headers.
        """
        return mapping.from_impl(self._run(self._impl.options(url=mapping.to_impl(url), **{kwarg: mapping.to_impl(kwarg_value) for kwarg, kwarg_value in kwargs.items()})))

    def record(self, resource_types: list[ResourceType] | None=None) -> AbstractContextManager[HarCapture]:
        """Record network traffic as HAR.

        Context manager that captures all network activity on the tab
        and produces a HarCapture object for export.

        Args:
            resource_types: Optional list of resource types to capture.
                When provided, only requests matching these types are
                recorded. When None (default), all resource types are
                captured.

        Usage::

            with tab.request.record() as capture:
                tab.go_to('https://example.com')
            capture.save('flow.har')

            # Record only fetch and XHR requests
            with tab.request.record(
                resource_types=[ResourceType.FETCH, ResourceType.XHR]
            ) as capture:
                tab.go_to('https://example.com')
            capture.save('api_calls.har')

        Yields:
            HarCapture: Object with .save(), .to_dict(), and .entries.
        """
        return mapping.from_impl(self._impl.record(resource_types=mapping.to_impl(resource_types)))

class Response(SyncBase):
    """HTTP response object for browser-based fetch requests.

    This class provides a standardized interface for handling HTTP responses
    obtained through the browser's fetch API. It mimics the requests.Response
    interface while preserving all browser-specific metadata including cookies,
    headers, and network timing information.

    Key Features:
    - Compatible with requests.Response API for easy migration
    - Preserves both request and response headers for analysis
    - Automatic cookie extraction from Set-Cookie headers
    - Lazy JSON parsing with caching
    - Browser-context aware (respects CORS, security policies)
    - Content available in multiple formats (text, bytes, JSON)

    The response contains all data captured during the browser's fetch execution,
    including redirects, authentication flows, and any browser-applied transformations.
    """
    _impl: _ResponseImpl

    @property
    def ok(self) -> bool:
        """Check if the request was successful (2xx status codes).

        Returns:
            True if status code is in the 200-399 range, False otherwise.

        Note:
            This follows HTTP conventions where 2xx codes indicate success
            and 3xx codes indicate redirection (still considered "ok").
        """
        return mapping.from_impl(self._impl.ok)

    @property
    def cookies(self) -> list[CookieParam]:
        """Get cookies that were set by the server during this response.

        Returns:
            List of cookies extracted from Set-Cookie headers. Each cookie
            contains name and value, with cookie attributes (Path, Domain, etc.)
            automatically handled by the browser.

        Note:
            These are only NEW/UPDATED cookies from this response. Existing
            browser cookies are managed automatically by the browser context.
        """
        return mapping.from_impl(self._impl.cookies)

    @property
    def request_headers(self) -> list[HeaderEntry]:
        """Get headers that were actually sent in the HTTP request.

        Returns:
            List of headers sent to the server, including both custom headers
            provided by the user and automatic headers added by the browser
            (User-Agent, Accept, Authorization, etc.).

        Note:
            This shows the ACTUAL headers sent, which may differ from what
            was originally specified due to browser modifications.
        """
        return mapping.from_impl(self._impl.request_headers)

    @property
    def headers(self) -> list[HeaderEntry]:
        """Get headers received from the server in the HTTP response.

        Returns:
            List of response headers sent by the server, including standard
            headers (Content-Type, Content-Length, etc.) and any custom headers.

        Note:
            Some security-sensitive headers may be filtered by the browser
            and not appear in this list due to CORS policies.
        """
        return mapping.from_impl(self._impl.headers)

    @property
    def status_code(self) -> int:
        """Get the HTTP status code returned by the server.

        Returns:
            Integer status code (e.g., 200 for OK, 404 for Not Found, 500 for Server Error).
        """
        return mapping.from_impl(self._impl.status_code)

    @property
    def text(self) -> str:
        """Get the response content as a decoded string.

        Returns:
            Response body decoded as UTF-8 string. If no text was provided
            during initialization, it will be decoded from the raw content.

        Note:
            Decoding uses 'replace' error handling to avoid crashes on
            invalid UTF-8 sequences.
        """
        return mapping.from_impl(self._impl.text)

    @property
    def content(self) -> bytes:
        """Get the raw response content as bytes.

        Returns:
            Unmodified response body as bytes. Useful for binary data
            (images, files, etc.) or when you need to handle encoding manually.
        """
        return mapping.from_impl(self._impl.content)

    @property
    def url(self) -> str:
        """Get the final URL of the response after any redirects.

        Returns:
            The final URL that was accessed, which may differ from the
            original request URL if redirects occurred.
        """
        return mapping.from_impl(self._impl.url)

    def json(self) -> dict[str, Any] | list:
        """Parse and return the response content as JSON data.

        Attempts to parse the response text as JSON. Uses caching to avoid
        re-parsing the same content multiple times.

        Returns:
            Parsed JSON data as dictionary, list, or other JSON-compatible type.

        Raises:
            ValueError: If the response content is not valid JSON or if parsing fails.

        Note:
            - Uses lazy parsing: JSON is only parsed when first accessed
            - Subsequent calls return cached result for better performance
            - If JSON was pre-parsed during initialization, that result is returned
        """
        return mapping.from_impl(self._impl.json())

    def raise_for_status(self) -> None:
        """Raise an HTTPError if the response indicates an HTTP error status.

        Checks the status code and raises an exception for client errors (4xx)
        and server errors (5xx). Successful responses (2xx) and redirects (3xx)
        do not raise an exception.

        Raises:
            HTTPError: If status code is 400 or higher, indicating an error.

        Note:
            This method is compatible with requests.Response.raise_for_status()
            for easy migration from the requests library.
        """
        self._impl.raise_for_status()

mapping.register(_ChromeImpl, Chrome)
mapping.register(_EdgeImpl, Edge)
mapping.register(_TabImpl, Tab)
mapping.register(_DownloadHandleImpl, DownloadHandle)
mapping.register(_RequestHandleImpl, RequestHandle)
mapping.register(_ResponseHandleImpl, ResponseHandle)
mapping.register(_WebElementImpl, WebElement)
mapping.register(_ShadowRootImpl, ShadowRoot)
mapping.register(_KeyboardImpl, Keyboard)
mapping.register(_MouseImpl, Mouse)
mapping.register(_ScrollImpl, Scroll)
mapping.register(_RequestImpl, Request)
mapping.register(_ResponseImpl, Response)



__all__ = ['Chrome', 'Edge', 'Tab', 'DownloadHandle', 'RequestHandle', 'ResponseHandle', 'WebElement', 'ShadowRoot', 'Keyboard', 'Mouse', 'Scroll', 'Request', 'Response']
