from __future__ import annotations

from typing import TYPE_CHECKING

from pydoll.protocol.bidi.base import Command
from pydoll.protocol.bidi.network.methods import (
    AddDataCollectorParameters,
    AddInterceptParameters,
    ContinueRequestParameters,
    ContinueResponseParameters,
    ContinueWithAuthParameters,
    DisownDataParameters,
    FailRequestParameters,
    GetDataParameters,
    NetworkMethod,
    ProvideResponseParameters,
    RemoveDataCollectorParameters,
    RemoveInterceptParameters,
    SetCacheBehaviorParameters,
    SetExtraHeadersParameters,
)
from pydoll.protocol.bidi.network.types import (
    DataType,
    InterceptPhase,
    UrlPattern,
)

if TYPE_CHECKING:
    from pydoll.protocol.bidi.network.methods import (
        AddDataCollectorCommand,
        AddInterceptCommand,
        ContinueRequestCommand,
        ContinueResponseCommand,
        ContinueWithAuthCommand,
        DisownDataCommand,
        FailRequestCommand,
        GetDataCommand,
        ProvideResponseCommand,
        RemoveDataCollectorCommand,
        RemoveInterceptCommand,
        SetCacheBehaviorCommand,
        SetExtraHeadersCommand,
    )
    from pydoll.protocol.bidi.network.types import (
        AuthCredentials,
        BytesValue,
        CollectorType,
        CookieHeader,
        Header,
        SetCookieHeader,
    )


class NetworkCommands:
    """Command builders for the BiDi network module."""

    @staticmethod
    def add_data_collector(
        data_types: list[DataType],
        max_encoded_data_size: int,
        collector_type: CollectorType | None = None,
        contexts: list[str] | None = None,
        user_contexts: list[str] | None = None,
    ) -> AddDataCollectorCommand:
        """Generates a command to add a network data collector."""
        params = AddDataCollectorParameters(
            dataTypes=data_types,
            maxEncodedDataSize=max_encoded_data_size,
        )
        if collector_type is not None:
            params['collectorType'] = collector_type
        if contexts is not None:
            params['contexts'] = contexts
        if user_contexts is not None:
            params['userContexts'] = user_contexts
        return Command(method=NetworkMethod.ADD_DATA_COLLECTOR, params=params)

    @staticmethod
    def add_intercept(
        phases: list[InterceptPhase],
        contexts: list[str] | None = None,
        url_patterns: list[UrlPattern] | None = None,
    ) -> AddInterceptCommand:
        """Generates a command to add a network intercept."""
        params = AddInterceptParameters(phases=phases)
        if contexts is not None:
            params['contexts'] = contexts
        if url_patterns is not None:
            params['urlPatterns'] = url_patterns
        return Command(method=NetworkMethod.ADD_INTERCEPT, params=params)

    @staticmethod
    def continue_request(
        request: str,
        body: BytesValue | None = None,
        cookies: list[CookieHeader] | None = None,
        headers: list[Header] | None = None,
        method: str | None = None,
        url: str | None = None,
    ) -> ContinueRequestCommand:
        """Generates a command to continue a blocked request."""
        params = ContinueRequestParameters(request=request)
        if body is not None:
            params['body'] = body
        if cookies is not None:
            params['cookies'] = cookies
        if headers is not None:
            params['headers'] = headers
        if method is not None:
            params['method'] = method
        if url is not None:
            params['url'] = url
        return Command(method=NetworkMethod.CONTINUE_REQUEST, params=params)

    @staticmethod
    def continue_response(
        request: str,
        cookies: list[SetCookieHeader] | None = None,
        credentials: AuthCredentials | None = None,
        headers: list[Header] | None = None,
        reason_phrase: str | None = None,
        status_code: int | None = None,
    ) -> ContinueResponseCommand:
        """Generates a command to continue a blocked response."""
        params = ContinueResponseParameters(request=request)
        if cookies is not None:
            params['cookies'] = cookies
        if credentials is not None:
            params['credentials'] = credentials
        if headers is not None:
            params['headers'] = headers
        if reason_phrase is not None:
            params['reasonPhrase'] = reason_phrase
        if status_code is not None:
            params['statusCode'] = status_code
        return Command(method=NetworkMethod.CONTINUE_RESPONSE, params=params)

    @staticmethod
    def continue_with_auth(
        request: str,
        action: str | None = None,
        credentials: AuthCredentials | None = None,
    ) -> ContinueWithAuthCommand:
        """Generates a command to continue a request blocked at auth phase."""
        params = ContinueWithAuthParameters(request=request)
        if action is not None:
            params['action'] = action
        if credentials is not None:
            params['credentials'] = credentials
        return Command(method=NetworkMethod.CONTINUE_WITH_AUTH, params=params)

    @staticmethod
    def disown_data(
        data_type: DataType,
        collector: str,
        request: str,
    ) -> DisownDataCommand:
        """Generates a command to release collected network data."""
        return Command(
            method=NetworkMethod.DISOWN_DATA,
            params=DisownDataParameters(
                dataType=data_type,
                collector=collector,
                request=request,
            ),
        )

    @staticmethod
    def fail_request(request: str) -> FailRequestCommand:
        """Generates a command to fail a blocked request."""
        return Command(
            method=NetworkMethod.FAIL_REQUEST,
            params=FailRequestParameters(request=request),
        )

    @staticmethod
    def get_data(
        data_type: DataType,
        request: str,
        collector: str | None = None,
        disown: bool | None = None,
    ) -> GetDataCommand:
        """Generates a command to retrieve collected network data."""
        params = GetDataParameters(dataType=data_type, request=request)
        if collector is not None:
            params['collector'] = collector
        if disown is not None:
            params['disown'] = disown
        return Command(method=NetworkMethod.GET_DATA, params=params)

    @staticmethod
    def provide_response(
        request: str,
        body: BytesValue | None = None,
        cookies: list[SetCookieHeader] | None = None,
        headers: list[Header] | None = None,
        reason_phrase: str | None = None,
        status_code: int | None = None,
    ) -> ProvideResponseCommand:
        """Generates a command to provide a complete response for a blocked request."""
        params = ProvideResponseParameters(request=request)
        if body is not None:
            params['body'] = body
        if cookies is not None:
            params['cookies'] = cookies
        if headers is not None:
            params['headers'] = headers
        if reason_phrase is not None:
            params['reasonPhrase'] = reason_phrase
        if status_code is not None:
            params['statusCode'] = status_code
        return Command(method=NetworkMethod.PROVIDE_RESPONSE, params=params)

    @staticmethod
    def remove_data_collector(collector: str) -> RemoveDataCollectorCommand:
        """Generates a command to remove a data collector."""
        return Command(
            method=NetworkMethod.REMOVE_DATA_COLLECTOR,
            params=RemoveDataCollectorParameters(collector=collector),
        )

    @staticmethod
    def remove_intercept(intercept: str) -> RemoveInterceptCommand:
        """Generates a command to remove a network intercept."""
        return Command(
            method=NetworkMethod.REMOVE_INTERCEPT,
            params=RemoveInterceptParameters(intercept=intercept),
        )

    @staticmethod
    def set_cache_behavior(
        cache_behavior: str,
        contexts: list[str] | None = None,
    ) -> SetCacheBehaviorCommand:
        """Generates a command to configure network cache behavior."""
        params = SetCacheBehaviorParameters(cacheBehavior=cache_behavior)
        if contexts is not None:
            params['contexts'] = contexts
        return Command(method=NetworkMethod.SET_CACHE_BEHAVIOR, params=params)

    @staticmethod
    def set_extra_headers(
        headers: list[Header],
        contexts: list[str] | None = None,
        user_contexts: list[str] | None = None,
    ) -> SetExtraHeadersCommand:
        """Generates a command to set extra request headers."""
        params = SetExtraHeadersParameters(headers=headers)
        if contexts is not None:
            params['contexts'] = contexts
        if user_contexts is not None:
            params['userContexts'] = user_contexts
        return Command(method=NetworkMethod.SET_EXTRA_HEADERS, params=params)
