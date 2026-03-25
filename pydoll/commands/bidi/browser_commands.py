from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from pydoll.protocol.bidi.base import Command
from pydoll.protocol.bidi.browser.methods import (
    BrowserMethod,
    CreateUserContextParameters,
    RemoveUserContextParameters,
    SetClientWindowStateParameters,
    SetDownloadBehaviorParameters,
)
from pydoll.protocol.bidi.browser.types import (
    ClientWindowState,
    DownloadBehavior,
)

if TYPE_CHECKING:
    from pydoll.protocol.bidi.browser.methods import (
        CloseCommand,
        CreateUserContextCommand,
        GetClientWindowsCommand,
        GetUserContextsCommand,
        RemoveUserContextCommand,
        SetClientWindowStateCommand,
        SetDownloadBehaviorCommand,
    )
    from pydoll.protocol.bidi.session.types import (
        ProxyConfiguration,
        UserPromptHandler,
    )


class BrowserCommands:
    """Command builders for the BiDi browser module."""

    @staticmethod
    def close() -> CloseCommand:
        """Generates a command to close the browser."""
        return Command(method=BrowserMethod.CLOSE, params={})

    @staticmethod
    def create_user_context(
        accept_insecure_certs: Optional[bool] = None,
        proxy: Optional[ProxyConfiguration] = None,
        unhandled_prompt_behavior: Optional[UserPromptHandler] = None,
    ) -> CreateUserContextCommand:
        """Generates a command to create a new user context."""
        params = CreateUserContextParameters()
        if accept_insecure_certs is not None:
            params['acceptInsecureCerts'] = accept_insecure_certs
        if proxy is not None:
            params['proxy'] = proxy
        if unhandled_prompt_behavior is not None:
            params['unhandledPromptBehavior'] = unhandled_prompt_behavior
        return Command(method=BrowserMethod.CREATE_USER_CONTEXT, params=params)

    @staticmethod
    def get_client_windows() -> GetClientWindowsCommand:
        """Generates a command to get all client windows."""
        return Command(method=BrowserMethod.GET_CLIENT_WINDOWS, params={})

    @staticmethod
    def get_user_contexts() -> GetUserContextsCommand:
        """Generates a command to get all user contexts."""
        return Command(method=BrowserMethod.GET_USER_CONTEXTS, params={})

    @staticmethod
    def remove_user_context(user_context: str) -> RemoveUserContextCommand:
        """Generates a command to remove a user context."""
        params = RemoveUserContextParameters(userContext=user_context)
        return Command(method=BrowserMethod.REMOVE_USER_CONTEXT, params=params)

    @staticmethod
    def set_client_window_state(
        client_window: str,
        state: ClientWindowState,
        width: Optional[int] = None,
        height: Optional[int] = None,
        x: Optional[int] = None,
        y: Optional[int] = None,
    ) -> SetClientWindowStateCommand:
        """Generates a command to set the state of a client window."""
        params = SetClientWindowStateParameters(
            clientWindow=client_window,
            state=state,
        )
        if width is not None:
            params['width'] = width
        if height is not None:
            params['height'] = height
        if x is not None:
            params['x'] = x
        if y is not None:
            params['y'] = y
        return Command(method=BrowserMethod.SET_CLIENT_WINDOW_STATE, params=params)

    @staticmethod
    def set_download_behavior(
        download_behavior: DownloadBehavior | None,
        user_contexts: Optional[list[str]] = None,
    ) -> SetDownloadBehaviorCommand:
        """Generates a command to set the download behavior."""
        params = SetDownloadBehaviorParameters(
            downloadBehavior=download_behavior,
        )
        if user_contexts is not None:
            params['userContexts'] = user_contexts
        return Command(method=BrowserMethod.SET_DOWNLOAD_BEHAVIOR, params=params)
