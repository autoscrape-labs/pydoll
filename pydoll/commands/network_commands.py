from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from pydoll.protocol.base import Command
from pydoll.protocol.network.methods import (
    DeleteCookiesParams,
    EmulateNetworkConditionsParams,
    EnableReportingApiParams,
    GetCertificateParams,
    GetCookiesParams,
    GetRequestPostDataParams,
    GetResponseBodyForInterceptionParams,
    GetResponseBodyParams,
    GetSecurityIsolationStatusParams,
    LoadNetworkResourceParams,
    NetworkEnableParams,
    NetworkMethod,
    ReplayXHRParams,
    SearchInResponseBodyParams,
    SetAcceptedEncodingsParams,
    SetAttachDebugStackParams,
    SetBlockedURLsParams,
    SetBypassServiceWorkerParams,
    SetCacheDisabledParams,
    SetCookieControlsParams,
    SetCookieParams,
    SetCookiesParams,
    SetExtraHTTPHeadersParams,
    SetUserAgentOverrideParams,
    StreamResourceContentParams,
    TakeResponseBodyForInterceptionAsStreamParams,
)

if TYPE_CHECKING:
    from pydoll.protocol.emulation.types import UserAgentMetadata
    from pydoll.protocol.network.methods import (
        ClearAcceptedEncodingsOverrideCommand,
        ClearBrowserCacheCommand,
        ClearBrowserCookiesCommand,
        ClearCookiesCommand,
        DisableCommand,
        EmulateNetworkConditionsCommand,
        EnableCommand,
        EnableReportingApiCommand,
        GetCertificateCommand,
        GetCookiesCommand,
        GetRequestPostDataCommand,
        GetResponseBodyCommand,
        GetResponseBodyForInterceptionCommand,
        GetSecurityIsolationStatusCommand,
        HeaderEntry,
        LoadNetworkResourceCommand,
        ReplayXHRCommand,
        SearchInResponseBodyCommand,
        SetAcceptedEncodingsCommand,
        SetAttachDebugStackCommand,
        SetBlockedURLsCommand,
        SetBypassServiceWorkerCommand,
        SetCacheDisabledCommand,
        SetCookieCommand,
        SetCookieControlsCommand,
        SetCookiesCommand,
        SetExtraHTTPHeadersCommand,
        SetUserAgentOverrideCommand,
        StreamResourceContentCommand,
        TakeResponseBodyForInterceptionAsStreamCommand,
    )
    from pydoll.protocol.network.types import (
        ConnectionType,
        ContentEncoding,
        CookiePartitionKey,
        CookiePriority,
        CookieSameSite,
        CookieSourceScheme,
        LoadNetworkResourceOptions,
    )


class NetworkCommands:
    """
    Implementation of Chrome DevTools Protocol for the Network domain.

    This class provides commands for monitoring and manipulating network activities,
    enabling detailed inspection and control over HTTP requests and responses.
    The Network domain exposes comprehensive network-related information including:
    - Request/response headers and bodies
    - Resource timing and caching behavior
    - Cookie management and security details
    - Network conditions emulation
    - Traffic interception and modification

    The commands allow developers to analyze performance, debug network issues,
    and test application behavior under various network conditions.
    """

    @staticmethod
    def clear_browser_cache() -> ClearBrowserCacheCommand:
        """
        Clears browser cache storage.

        This command is essential for testing cache behavior and ensuring fresh
        resource loading. It affects all cached resources including:
        - CSS/JavaScript files
        - Images and media assets
        - API response caching

        Use cases:
        - Testing cache invalidation strategies
        - Reproducing issues with stale content
        - Performance benchmarking without cache influence

        Returns:
            Command: CDP command to clear the entire browser cache
        """
        return Command(method=NetworkMethod.CLEAR_BROWSER_CACHE)

    @staticmethod
    def clear_browser_cookies() -> ClearBrowserCookiesCommand:
        """
        Command to clear all cookies stored in the browser.

        This can be beneficial for testing scenarios where you need
        to simulate a fresh user session without any previously stored
        cookies that might affect the application's behavior.

        Returns:
            Command[Response]: A command to clear all cookies in the browser.
        """
        return Command(method=NetworkMethod.CLEAR_BROWSER_COOKIES)

    @staticmethod
    def delete_cookies(
        name: str,
        url: Optional[str] = None,
        domain: Optional[str] = None,
        path: Optional[str] = None,
        partition_key: Optional[CookiePartitionKey] = None,
    ) -> ClearCookiesCommand:
        """
        Deletes browser cookies with matching criteria.

        Provides granular control over cookie removal through multiple parameters:
        - Delete by name only (affects all matching cookies)
        - Scope deletion using URL, domain, or path
        - Handle partitioned cookies for privacy-aware applications

        Args:
            name: Name of the cookies to remove (required)
            url: Delete cookies for specific URL (domain/path must match)
            domain: Exact domain for cookie deletion
            path: Exact path for cookie deletion
            partition_key: Partition key attributes for cookie isolation

        Returns:
            Command: CDP command to execute selective cookie deletion
        """
        params = DeleteCookiesParams(name=name)
        if url is not None:
            params['url'] = url
        if domain is not None:
            params['domain'] = domain
        if path is not None:
            params['path'] = path
        if partition_key is not None:
            params['partitionKey'] = partition_key
        return Command(method=NetworkMethod.DELETE_COOKIES, params=params)

    @staticmethod
    def disable() -> DisableCommand:
        """
        Stops network monitoring and event reporting.

        Preserves network state but stops:
        - Request/response events
        - WebSocket message tracking
        - Loading progress notifications

        Use when:
        - Reducing overhead during non-network operations
        - Pausing monitoring temporarily
        - Finalizing network-related tests

        Returns:
            Command: CDP command to disable network monitoring
        """
        return Command(method=NetworkMethod.DISABLE)

    @staticmethod
    def enable(
        max_total_buffer_size: Optional[int] = None,
        max_resource_buffer_size: Optional[int] = None,
        max_post_data_size: Optional[int] = None,
    ) -> EnableCommand:
        """
        Enables network monitoring with configurable buffers.

        Args:
            max_total_buffer_size: Total memory buffer for network data (bytes)
            max_resource_buffer_size: Per-resource buffer limit (bytes)
            max_post_data_size: Maximum POST payload to capture (bytes)

        Recommended settings:
        - Increase buffers for long-running sessions
        - Adjust post size for API testing
        - Monitor memory usage with large buffers

        Returns:
            Command: CDP command to enable network monitoring
        """
        params = NetworkEnableParams()
        if max_total_buffer_size is not None:
            params['maxTotalBufferSize'] = max_total_buffer_size
        if max_resource_buffer_size is not None:
            params['maxResourceBufferSize'] = max_resource_buffer_size
        if max_post_data_size is not None:
            params['maxPostDataSize'] = max_post_data_size
        return Command(method=NetworkMethod.ENABLE, params=params)

    @staticmethod
    def get_cookies(
        urls: Optional[list[str]] = None,
    ) -> GetCookiesCommand:
        """
        Retrieves cookies matching specified URLs.

        Args:
            urls: list of URLs to scope cookie retrieval

        Returns:
            Command: CDP command returning cookie details including:
                - Name, value, and attributes
                - Security and scope parameters
                - Expiration and size information

        Usage notes:
        - Empty URL list returns all cookies
        - Includes HTTP-only and secure cookies
        - Shows partitioned cookie status
        """
        params = GetCookiesParams()
        if urls is not None:
            params['urls'] = urls
        return Command(method=NetworkMethod.GET_COOKIES, params=params)

    @staticmethod
    def get_request_post_data(
        request_id: str,
    ) -> GetRequestPostDataCommand:
        """
        Retrieves POST data from a specific network request.

        Essential for:
        - Form submission analysis
        - API request debugging
        - File upload monitoring
        - Security testing

        Args:
            request_id: Unique identifier for the network request

        Returns:
            Command: CDP command that returns:
                - Raw POST data content
                - Multipart form data (excluding file contents)
                - Content encoding information

        Note: Large POST bodies may be truncated based on buffer settings
        """
        params = GetRequestPostDataParams(requestId=request_id)
        return Command(method=NetworkMethod.GET_REQUEST_POST_DATA, params=params)

    @staticmethod
    def get_response_body(
        request_id: str,
    ) -> GetResponseBodyCommand:
        """
        Retrieves the full content of a network response.

        Supports various content types:
        - Text-based resources (HTML, CSS, JSON)
        - Base64-encoded binary content (images, media)
        - Gzip/deflate compressed responses

        Args:
            request_id: Unique network request identifier

        Important considerations:
        - Response must be available in browser memory
        - Large responses may require streaming approaches
        - Sensitive data should be handled securely

        Returns:
            Command: CDP command returning response body and encoding details
        """
        params = GetResponseBodyParams(requestId=request_id)
        return Command(method=NetworkMethod.GET_RESPONSE_BODY, params=params)

    @staticmethod
    def set_cache_disabled(cache_disabled: bool) -> SetCacheDisabledCommand:
        """
        Controls browser's cache mechanism.

        Use cases:
        - Testing resource update behavior
        - Forcing fresh content loading
        - Performance impact analysis
        - Cache-busting scenarios

        Args:
            cache_disabled: True to disable caching, False to enable

        Returns:
            Command: CDP command to modify cache behavior

        Note: Affects all requests until re-enabled
        """
        params = SetCacheDisabledParams(cacheDisabled=cache_disabled)
        return Command(method=NetworkMethod.SET_CACHE_DISABLED, params=params)

    @staticmethod
    def set_cookie(
        name: str,
        value: str,
        url: Optional[str] = None,
        domain: Optional[str] = None,
        path: Optional[str] = None,
        secure: Optional[bool] = None,
        http_only: Optional[bool] = None,
        same_site: Optional[CookieSameSite] = None,
        expires: Optional[float] = None,
        priority: Optional[CookiePriority] = None,
        same_party: Optional[bool] = None,
        source_scheme: Optional[CookieSourceScheme] = None,
        source_port: Optional[int] = None,
        partition_key: Optional[CookiePartitionKey] = None,
    ) -> SetCookieCommand:
        """
        Creates or updates a cookie with specified attributes.

        Comprehensive cookie control supporting:
        - Session and persistent cookies
        - Security attributes (Secure, HttpOnly)
        - SameSite policies
        - Cookie partitioning
        - Priority levels

        Args:
            name: Cookie name
            value: Cookie value
            url: Target URL for the cookie
            domain: Cookie domain scope
            path: Cookie path scope
            secure: Require HTTPS
            http_only: Prevent JavaScript access
            same_site: Cross-site access policy
            expires: Expiration timestamp
            priority: Cookie priority level
            same_party: First-Party Sets flag
            source_scheme: Cookie source context
            source_port: Source port restriction
            partition_key: Storage partition key

        Returns:
            Command: CDP command that returns success status

        Security considerations:
        - Use secure flag for sensitive data
        - Consider SameSite policies
        - Be aware of cross-site implications
        """
        params = SetCookieParams(name=name, value=value)

        if url is not None:
            params['url'] = url
        if domain is not None:
            params['domain'] = domain
        if path is not None:
            params['path'] = path
        if secure is not None:
            params['secure'] = secure
        if http_only is not None:
            params['httpOnly'] = http_only
        if same_site is not None:
            params['sameSite'] = same_site
        if expires is not None:
            params['expires'] = expires
        if priority is not None:
            params['priority'] = priority
        if same_party is not None:
            params['sameParty'] = same_party
        if source_scheme is not None:
            params['sourceScheme'] = source_scheme
        if source_port is not None:
            params['sourcePort'] = source_port
        if partition_key is not None:
            params['partitionKey'] = partition_key

        return Command(method=NetworkMethod.SET_COOKIE, params=params)

    @staticmethod
    def set_cookies(cookies: list[SetCookieParams]) -> SetCookiesCommand:
        """
        Sets multiple cookies in a single operation.

        Efficient for:
        - Batch cookie operations
        - Session state restoration
        - Testing multiple authentication states
        - Cross-domain cookie setup

        Args:
            cookies: list of cookie parameters including
                    name, value, and attributes

        Returns:
            Command: CDP command for bulk cookie setting

        Performance note:
        - More efficient than multiple set_cookie calls
        - Consider memory impact with large batches
        """
        params = SetCookiesParams(cookies=cookies)
        return Command(method=NetworkMethod.SET_COOKIES, params=params)

    @staticmethod
    def set_extra_http_headers(
        headers: list[HeaderEntry],
    ) -> SetExtraHTTPHeadersCommand:
        """
        Applies custom HTTP headers to all subsequent requests.

        Enables advanced scenarios:
        - A/B testing with custom headers
        - Authentication bypass for testing
        - Content negotiation simulations
        - Security header validation

        Args:
            headers: list of key-value header pairs

        Security notes:
        - Headers are applied browser-wide
        - Sensitive headers (e.g., Authorization) persist until cleared
        - Use with caution in shared environments

        Returns:
            Command: CDP command to set global HTTP headers
        """
        params = SetExtraHTTPHeadersParams(headers=headers)
        return Command(method=NetworkMethod.SET_EXTRA_HTTP_HEADERS, params=params)

    @staticmethod
    def set_useragent_override(
        user_agent: str,
        accept_language: Optional[str] = None,
        platform: Optional[str] = None,
        user_agent_metadata: Optional[UserAgentMetadata] = None,
    ) -> SetUserAgentOverrideCommand:
        """
        Overrides the browser's User-Agent string.

        Use cases:
        - Device/browser simulation
        - Compatibility testing
        - Content negotiation
        - Bot detection bypass

        Args:
            user_agent: Complete User-Agent string
            accept_language: Language preference header
            platform: Platform identifier
            user_agent_metadata: Detailed UA metadata

        Returns:
            Command: CDP command to override user agent

        Testing considerations:
        - Affects all subsequent requests
        - May impact server-side behavior
        - Consider mobile/desktop differences
        """
        params = SetUserAgentOverrideParams(userAgent=user_agent)
        if accept_language is not None:
            params['acceptLanguage'] = accept_language
        if platform is not None:
            params['platform'] = platform
        if user_agent_metadata is not None:
            params['userAgentMetadata'] = user_agent_metadata
        return Command(method=NetworkMethod.SET_USER_AGENT_OVERRIDE, params=params)

    @staticmethod
    def clear_accepted_encodings_override() -> ClearAcceptedEncodingsOverrideCommand:
        """
        Restores default content encoding acceptance.

        Effects:
        - Resets compression preferences
        - Restores default Accept-Encoding header
        - Allows server-chosen encoding

        Use when:
        - Testing encoding fallbacks
        - Debugging compression issues
        - Resetting after encoding tests

        Returns:
            Command: CDP command to clear encoding overrides
        """
        return Command(method=NetworkMethod.CLEAR_ACCEPTED_ENCODINGS_OVERRIDE)

    @staticmethod
    def enable_reporting_api(
        enabled: bool,
    ) -> EnableReportingApiCommand:
        """
        Controls the Reporting API functionality.

        Features:
        - Network error reporting
        - Deprecation notices
        - CSP violation reports
        - CORS issues

        Args:
            enabled: True to enable, False to disable

        Returns:
            Command: CDP command to configure Reporting API

        Note: Requires browser support for Reporting API
        """
        params = EnableReportingApiParams(enabled=enabled)
        return Command(method=NetworkMethod.ENABLE_REPORTING_API, params=params)

    @staticmethod
    def search_in_response_body(
        request_id: str,
        query: str,
        case_sensitive: bool = False,
        is_regex: bool = False,
    ) -> SearchInResponseBodyCommand:
        """
        Searches for content within response bodies.

        Powerful for:
        - Content verification
        - Security scanning
        - Data extraction
        - Response validation

        Args:
            request_id: Target response identifier
            query: Search string or pattern
            case_sensitive: Match case sensitivity
            is_regex: Use regular expression matching

        Returns:
            Command: CDP command returning match results

        Performance tip:
        - Use specific queries for large responses
        - Consider regex complexity
        """
        params = SearchInResponseBodyParams(requestId=request_id, query=query)
        if case_sensitive is not None:
            params['caseSensitive'] = case_sensitive
        if is_regex is not None:
            params['isRegex'] = is_regex
        return Command(method=NetworkMethod.SEARCH_IN_RESPONSE_BODY, params=params)

    @staticmethod
    def set_blocked_urls(urls: list[str]) -> SetBlockedURLsCommand:
        """
        Blocks specified URLs from loading.

        Key features:
        - Pattern-based URL blocking
        - Resource type filtering
        - Network request prevention
        - Error simulation

        Args:
            urls: list of URL patterns to block
                 Supports wildcards and pattern matching

        Returns:
            Command: CDP command to set URL blocking rules

        Common applications:
        - Ad/tracker blocking simulation
        - Resource loading control
        - Error handling testing
        - Network isolation testing
        """
        params = SetBlockedURLsParams(urls=urls)
        return Command(method=NetworkMethod.SET_BLOCKED_URLS, params=params)

    @staticmethod
    def set_bypass_service_worker(
        bypass: bool,
    ) -> SetBypassServiceWorkerCommand:
        """
        Controls Service Worker interception of network requests.

        Use cases:
        - Testing direct network behavior
        - Bypassing offline functionality
        - Debug caching issues
        - Performance comparison

        Args:
            bypass: True to skip Service Worker, False to allow

        Returns:
            Command: CDP command to configure Service Worker behavior

        Impact:
        - Affects offline capabilities
        - Changes caching behavior
        - Modifies push notifications
        """
        params = SetBypassServiceWorkerParams(bypass=bypass)
        return Command(method=NetworkMethod.SET_BYPASS_SERVICE_WORKER, params=params)

    @staticmethod
    def get_certificate(origin: str) -> GetCertificateCommand:
        """
        Retrieves SSL/TLS certificate information for a domain.

        Provides:
        - Certificate chain details
        - Validation status
        - Expiration information
        - Issuer details

        Args:
            origin: Target domain for certificate inspection

        Returns:
            Command: CDP command returning certificate data

        Security applications:
        - Certificate validation
        - SSL/TLS verification
        - Security assessment
        - Chain of trust verification
        """
        params = GetCertificateParams(origin=origin)
        return Command(method=NetworkMethod.GET_CERTIFICATE, params=params)

    @staticmethod
    def get_response_body_for_interception(
        interception_id: str,
    ) -> GetResponseBodyForInterceptionCommand:
        """
        Retrieves response body from an intercepted request.

        Essential for:
        - Response modification
        - Content inspection
        - Security testing
        - API response validation

        Args:
            interception_id: Identifier for intercepted request

        Returns:
            Command: CDP command providing intercepted response content

        Note:
        - Must be used with interception enabled
        - Supports streaming responses
        - Handles various content types
        """
        params = GetResponseBodyForInterceptionParams(interceptionId=interception_id)
        return Command(method=NetworkMethod.GET_RESPONSE_BODY_FOR_INTERCEPTION, params=params)

    @staticmethod
    def set_accepted_encodings(
        encodings: list[ContentEncoding],
    ) -> SetAcceptedEncodingsCommand:
        """
        Specifies accepted content encodings for requests.

        Controls:
        - Compression algorithms
        - Transfer encoding
        - Content optimization

        Args:
            encodings: list of accepted encoding methods
                     (gzip, deflate, br, etc.)

        Returns:
            Command: CDP command to set encoding preferences

        Performance implications:
        - Affects bandwidth usage
        - Impacts response time
        - Changes server behavior
        """
        params = SetAcceptedEncodingsParams(encodings=encodings)
        return Command(method=NetworkMethod.SET_ACCEPTED_ENCODINGS, params=params)

    @staticmethod
    def set_attach_debug_stack(enabled: bool) -> SetAttachDebugStackCommand:
        """
        Enables/disables debug stack attachment to requests.

        Debug features:
        - Stack trace collection
        - Request origin tracking
        - Initialization context
        - Call site identification

        Args:
            enabled: True to attach debug info, False to disable

        Returns:
            Command: CDP command to configure debug stack attachment

        Performance note:
        - May impact performance when enabled
        - Useful for development/debugging
        - Consider memory usage
        """
        params = SetAttachDebugStackParams(enabled=enabled)
        return Command(method=NetworkMethod.SET_ATTACH_DEBUG_STACK, params=params)

    @staticmethod
    def set_cookie_controls(
        enable_third_party_cookie_restriction: bool,
        disable_third_party_cookie_metadata: Optional[bool] = None,
        disable_third_party_cookie_heuristics: Optional[bool] = None,
    ) -> SetCookieControlsCommand:
        """
        Configures third-party cookie handling policies.

        Privacy features:
        - Cookie access control
        - Third-party restrictions
        - Tracking prevention
        - Privacy policy enforcement

        Args:
            enable_third_party_cookie_restriction: Enable restrictions
            disable_third_party_cookie_metadata: Skip metadata checks
            disable_third_party_cookie_heuristics: Disable detection logic

        Returns:
            Command: CDP command to set cookie control policies

        Security implications:
        - Affects cross-site tracking
        - Changes authentication behavior
        - Impacts embedded content
        """
        params = SetCookieControlsParams(
            enableThirdPartyCookieRestriction=enable_third_party_cookie_restriction
        )
        if disable_third_party_cookie_metadata is not None:
            params['disableThirdPartyCookieMetadata'] = disable_third_party_cookie_metadata
        if disable_third_party_cookie_heuristics is not None:
            params['disableThirdPartyCookieHeuristics'] = disable_third_party_cookie_heuristics
        return Command(method=NetworkMethod.SET_COOKIE_CONTROLS, params=params)

    @staticmethod
    def stream_resource_content(
        request_id: str,
    ) -> StreamResourceContentCommand:
        """
        Enables streaming of response content.

        Useful for:
        - Large file downloads
        - Progressive loading
        - Memory optimization
        - Real-time processing

        Args:
            request_id: Target request identifier

        Returns:
            Command: CDP command to initiate content streaming

        Best practices:
        - Monitor memory usage
        - Handle stream chunks efficiently
        - Consider error recovery
        """
        params = StreamResourceContentParams(requestId=request_id)
        return Command(method=NetworkMethod.STREAM_RESOURCE_CONTENT, params=params)

    @staticmethod
    def take_response_body_for_interception_as_stream(
        interception_id: str,
    ) -> TakeResponseBodyForInterceptionAsStreamCommand:
        """
        Creates a stream for intercepted response body.

        Applications:
        - Large response handling
        - Content modification
        - Bandwidth optimization
        - Progressive processing

        Args:
            interception_id: Intercepted response identifier

        Returns:
            Command: CDP command returning stream handle

        Stream handling:
        - Supports chunked transfer
        - Manages memory efficiently
        - Enables real-time processing
        """
        params = TakeResponseBodyForInterceptionAsStreamParams(interceptionId=interception_id)
        return Command(
            method=NetworkMethod.TAKE_RESPONSE_BODY_FOR_INTERCEPTION_AS_STREAM,
            params=params,
        )

    @staticmethod
    def emulate_network_conditions(
        offline: bool,
        latency: float,
        download_throughput: float,
        upload_throughput: float,
        connection_type: Optional[ConnectionType] = None,
        packet_loss: Optional[float] = None,
        packet_queue_length: Optional[int] = None,
        packet_reordering: Optional[bool] = None,
    ) -> EmulateNetworkConditionsCommand:
        """
        Emulates custom network conditions for realistic testing scenarios.

        Simulates various network profiles including:
        - Offline mode
        - High-latency connections
        - Bandwidth throttling
        - Unreliable network characteristics

        Args:
            offline: Simulate complete network disconnection
            latency: Minimum latency in milliseconds (round-trip time)
            download_throughput: Max download speed (bytes/sec, -1 to disable)
            upload_throughput: Max upload speed (bytes/sec, -1 to disable)
            connection_type: Network connection type (cellular, wifi, etc.)
            packet_loss: Simulated packet loss percentage (0-100)
            packet_queue_length: Network buffer size simulation
            packet_reordering: Enable packet order randomization

        Typical use cases:
        - Testing progressive loading states
        - Validating offline-first functionality
        - Performance optimization under constrained networks

        Returns:
            Command: CDP command to activate network emulation
        """
        params = EmulateNetworkConditionsParams(
            offline=offline,
            latency=latency,
            downloadThroughput=download_throughput,
            uploadThroughput=upload_throughput,
        )
        if connection_type is not None:
            params['connectionType'] = connection_type
        if packet_loss is not None:
            params['packetLoss'] = packet_loss
        if packet_queue_length is not None:
            params['packetQueueLength'] = packet_queue_length
        if packet_reordering is not None:
            params['packetReordering'] = packet_reordering
        return Command(method=NetworkMethod.EMULATE_NETWORK_CONDITIONS, params=params)

    @staticmethod
    def get_security_isolation_status(
        frame_id: Optional[str] = None,
    ) -> GetSecurityIsolationStatusCommand:
        """
        Retrieves security isolation information.

        Provides:
        - CORS status
        - Cross-origin isolation
        - Security context
        - Frame isolation

        Args:
            frame_id: Optional frame to check

        Returns:
            Command: CDP command returning isolation status

        Security aspects:
        - Cross-origin policies
        - Iframe security
        - Site isolation
        - Content protection
        """
        params = GetSecurityIsolationStatusParams()
        if frame_id is not None:
            params['frameId'] = frame_id
        return Command(method=NetworkMethod.GET_SECURITY_ISOLATION_STATUS, params=params)

    @staticmethod
    def load_network_resource(
        url: str,
        options: LoadNetworkResourceOptions,
        frame_id: Optional[str] = None,
    ) -> LoadNetworkResourceCommand:
        """
        Loads a network resource with specific options.

        Features:
        - Custom request configuration
        - Resource loading control
        - Frame-specific loading
        - Error handling

        Args:
            url: Resource URL to load
            options: Loading configuration
            frame_id: Target frame context

        Returns:
            Command: CDP command to load resource

        Usage considerations:
        - Respects CORS policies
        - Handles authentication
        - Manages redirects
        - Supports streaming
        """
        params = LoadNetworkResourceParams(url=url, options=options)
        if frame_id is not None:
            params['frameId'] = frame_id
        return Command(method=NetworkMethod.LOAD_NETWORK_RESOURCE, params=params)

    @staticmethod
    def replay_xhr(
        request_id: str,
    ) -> ReplayXHRCommand:
        """
        Replays an XHR request.

        Applications:
        - Request debugging
        - Response testing
        - Race condition analysis
        - API verification

        Args:
            request_id: XHR request to replay

        Returns:
            Command: CDP command to replay XHR

        Note:
        - Maintains original headers
        - Preserves request body
        - Updates timestamps
        - Creates new request ID
        """
        params = ReplayXHRParams(requestId=request_id)
        return Command(method=NetworkMethod.REPLAY_XHR, params=params)
