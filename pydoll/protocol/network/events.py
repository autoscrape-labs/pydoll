from enum import Enum


class NetworkEvent(str, Enum):
    """
    Events from the Network domain of the Chrome DevTools Protocol.

    This enumeration contains the names of Network-related events that can be
    received from the Chrome DevTools Protocol. These events provide information
    about network activities, such as requests, responses, and WebSocket communications.
    """

    DATA_RECEIVED = 'Network.dataReceived'
    """
    Fired when data chunk was received over the network.

    Args:
        requestId (RequestId): Request identifier.
        timestamp (MonotonicTime): Timestamp.
        dataLength (int): Data chunk length.
        encodedDataLength (int): Actual bytes received (might be less than dataLength
            for compressed encodings).
        data (str): Data that was received. (Encoded as a base64 string when passed over JSON)
    """

    EVENT_SOURCE_MESSAGE_RECEIVED = 'Network.eventSourceMessageReceived'
    """
    Fired when EventSource message is received.

    Args:
        requestId (RequestId): Request identifier.
        timestamp (MonotonicTime): Timestamp.
        eventName (str): Message type.
        eventId (str): Message identifier.
        data (str): Message content.
    """

    LOADING_FAILED = 'Network.loadingFailed'
    """
    Fired when HTTP request has failed to load.

    Args:
        requestId (RequestId): Request identifier.
        timestamp (MonotonicTime): Timestamp.
        type (ResourceType): Resource type.
        errorText (str): Error message. List of network errors: https://cs.chromium.org/chromium/src/net/base/net_error_list.h
        canceled (bool): True if loading was canceled.
        blockedReason (BlockedReason): The reason why loading was blocked, if any.
        corsErrorStatus (CorsErrorStatus): The reason why loading was blocked by CORS, if any.
    """

    LOADING_FINISHED = 'Network.loadingFinished'
    """
    Fired when HTTP request has finished loading.

    Args:
        requestId (RequestId): Request identifier.
        timestamp (MonotonicTime): Timestamp.
        encodedDataLength (number): Total number of bytes received for this request.
    """

    REQUEST_SERVED_FROM_CACHE = 'Network.requestServedFromCache'
    """
    Fired if request ended up loading from cache.

    Args:
        requestId (RequestId): Request identifier.
    """

    REQUEST_WILL_BE_SENT = 'Network.requestWillBeSent'
    """
    Fired when page is about to send HTTP request.

    Args:
        requestId (RequestId): Request identifier.
        loaderId (LoaderId): Loader identifier. Empty string if the request is fetched from worker.
        documentURL (str): URL of the document this request is loaded for.
        request (Request): Request data.
        timestamp (MonotonicTime): Timestamp.
        wallTime (TimeSinceEpoch): Timestamp.
        initiator (Initiator): Request initiator.
        redirectHasExtraInfo (bool): In the case that redirectResponse is populated, this flag
            indicates whether requestWillBeSentExtraInfo and responseReceivedExtraInfo events
            will be or were emitted for the request which was just redirected.
        redirectResponse (Response): Redirect response data.
        type (ResourceType): Type of this resource.
        frameId (Page.FrameId): Frame identifier.
        hasUserGesture (bool): Whether the request is initiated by a user gesture.
            Defaults to false.
    """

    RESPONSE_RECEIVED = 'Network.responseReceived'
    """
    Fired when HTTP response is available.

    Args:
        requestId (RequestId): Request identifier.
        loaderId (LoaderId): Loader identifier. Empty string if the request is fetched from worker.
        timestamp (MonotonicTime): Timestamp.
        type (ResourceType): Resource type.
        response (Response): Response data.
        hasExtraInfo (bool): Indicates whether requestWillBeSentExtraInfo and
            responseReceivedExtraInfo events will be or were emitted for this request.
        frameId (Page.FrameId): Frame identifier.
    """

    WEBSOCKET_CLOSED = 'Network.webSocketClosed'
    """
    Fired when WebSocket is closed.

    Args:
        requestId (RequestId): Request identifier.
        timestamp (MonotonicTime): Timestamp.
    """

    WEBSOCKET_CREATED = 'Network.webSocketCreated'
    """
    Fired upon WebSocket creation.

    Args:
        requestId (RequestId): Request identifier.
        url (str): WebSocket request URL.
        initiator (Initiator): Request initiator.
    """

    WEBSOCKET_FRAME_ERROR = 'Network.webSocketFrameError'
    """
    Fired when WebSocket message error occurs.

    Args:
        requestId (RequestId): Request identifier.
        timestamp (MonotonicTime): Timestamp.
        errorMessage (str): WebSocket error message.
    """

    WEBSOCKET_FRAME_RECEIVED = 'Network.webSocketFrameReceived'
    """
    Fired when WebSocket message is received.

    Args:
        requestId (RequestId): Request identifier.
        timestamp (MonotonicTime): Timestamp.
        response (WebSocketFrame): WebSocket response data.
    """

    WEBSOCKET_FRAME_SENT = 'Network.webSocketFrameSent'
    """
    Fired when WebSocket message is sent.

    Args:
        requestId (RequestId): Request identifier.
        timestamp (MonotonicTime): Timestamp.
        response (WebSocketFrame): WebSocket response data.
    """

    WEBSOCKET_HANDSHAKE_RESPONSE_RECEIVED = 'Network.webSocketHandshakeResponseReceived'
    """
    Fired when WebSocket handshake response becomes available.

    Args:
        requestId (RequestId): Request identifier.
        timestamp (MonotonicTime): Timestamp.
        response (WebSocketResponse): WebSocket response data.
    """

    WEBSOCKET_WILL_SEND_HANDSHAKE_REQUEST = 'Network.webSocketWillSendHandshakeRequest'
    """
    Fired when WebSocket is about to initiate handshake.

    Args:
        requestId (RequestId): Request identifier.
        timestamp (MonotonicTime): Timestamp.
        wallTime (TimeSinceEpoch): UTC Timestamp.
        request (WebSocketRequest): WebSocket request data.
    """

    WEBTRANSPORT_CLOSED = 'Network.webTransportClosed'
    """
    Fired when WebTransport is disposed.

    Args:
        transportId (RequestId): WebTransport identifier.
        timestamp (MonotonicTime): Timestamp.
    """

    WEBTRANSPORT_CONNECTION_ESTABLISHED = 'Network.webTransportConnectionEstablished'
    """
    Fired when WebTransport handshake is finished.

    Args:
        transportId (RequestId): WebTransport identifier.
        timestamp (MonotonicTime): Timestamp.
    """

    WEBTRANSPORT_CREATED = 'Network.webTransportCreated'
    """
    Fired upon WebTransport creation.

    Args:
        transportId (RequestId): WebTransport identifier.
        url (str): WebTransport request URL.
        timestamp (MonotonicTime): Timestamp.
        initiator (Initiator): Request initiator.
    """

    DIRECT_TCP_SOCKET_ABORTED = 'Network.directTCPSocketAborted'
    """
    Fired when direct_socket.TCPSocket is aborted.

    Args:
        identifier (RequestId): Request identifier.
        errorMessage (str): Error message.
        timestamp (MonotonicTime): Timestamp.
    """

    DIRECT_TCP_SOCKET_CHUNK_RECEIVED = 'Network.directTCPSocketChunkReceived'
    """
    Fired when data is received from tcp direct socket stream.

    Args:
        identifier (RequestId): Request identifier.
        data (str): Data received.
        timestamp (MonotonicTime): Timestamp.
    """

    DIRECT_TCP_SOCKET_CHUNK_SENT = 'Network.directTCPSocketChunkSent'
    """
    Fired when data is sent to tcp direct socket stream.

    Args:
        identifier (RequestId): Request identifier.
        data (str): Data sent.
        timestamp (MonotonicTime): Timestamp.
    """

    DIRECT_TCP_SOCKET_CLOSED = 'Network.directTCPSocketClosed'
    """
    Fired when direct_socket.TCPSocket is closed.

    Args:
        identifier (RequestId): Request identifier.
        timestamp (MonotonicTime): Timestamp.
    """

    DIRECT_TCP_SOCKET_CREATED = 'Network.directTCPSocketCreated'
    """
    Fired upon direct_socket.TCPSocket creation.

    Args:
        identifier (RequestId): Request identifier.
        remoteAddr (str): Remote address.
        remotePort (int): Remote port. Unsigned int 16.
        options (DirectTCPSocketOptions): Socket options.
        timestamp (MonotonicTime): Timestamp.
        initiator (Initiator): Request initiator.
    """

    DIRECT_TCP_SOCKET_OPENED = 'Network.directTCPSocketOpened'
    """
    Fired when direct_socket.TCPSocket connection is opened.

    Args:
        identifier (RequestId): Request identifier.
        remoteAddr (str): Remote address.
        remotePort (int): Remote port. Expected to be unsigned integer.
        timestamp (MonotonicTime): Timestamp.
        localAddr (str): Local address.
        localPort (int): Local port. Expected to be unsigned integer.
    """

    DIRECT_UDP_SOCKET_ABORTED = 'Network.directUDPSocketAborted'
    """
    Fired when direct_socket.UDPSocket is aborted.

    Args:
        identifier (RequestId): Request identifier.
        errorMessage (str): Error message.
        timestamp (MonotonicTime): Timestamp.
    """

    DIRECT_UDP_SOCKET_CHUNK_RECEIVED = 'Network.directUDPSocketChunkReceived'
    """
    Fired when message is received from udp direct socket stream.

    Args:
        identifier (RequestId): Request identifier.
        message (DirectUDPMessage): Message data.
        timestamp (MonotonicTime): Timestamp.
    """

    DIRECT_UDP_SOCKET_CHUNK_SENT = 'Network.directUDPSocketChunkSent'
    """
    Fired when message is sent to udp direct socket stream.

    Args:
        identifier (RequestId): Request identifier.
        message (DirectUDPMessage): Message data.
        timestamp (MonotonicTime): Timestamp.
    """

    DIRECT_UDP_SOCKET_CLOSED = 'Network.directUDPSocketClosed'
    """
    Fired when direct_socket.UDPSocket is closed.

    Args:
        identifier (RequestId): Request identifier.
        timestamp (MonotonicTime): Timestamp.
    """

    DIRECT_UDP_SOCKET_CREATED = 'Network.directUDPSocketCreated'
    """
    Fired upon direct_socket.UDPSocket creation.

    Args:
        identifier (RequestId): Request identifier.
        options (DirectUDPSocketOptions): Socket options.
        timestamp (MonotonicTime): Timestamp.
        initiator (Initiator): Request initiator.
    """

    DIRECT_UDP_SOCKET_OPENED = 'Network.directUDPSocketOpened'
    """
    Fired when direct_socket.UDPSocket connection is opened.

    Args:
        identifier (RequestId): Request identifier.
        localAddr (str): Local address.
        localPort (int): Local port. Expected to be unsigned integer.
        timestamp (MonotonicTime): Timestamp.
        remoteAddr (str): Remote address.
        remotePort (int): Remote port. Expected to be unsigned integer.
    """

    POLICY_UPDATED = 'Network.policyUpdated'
    """
    Fired once security policy has been updated.
    """

    REPORTING_API_ENDPOINTS_CHANGED_FOR_ORIGIN = 'Network.reportingApiEndpointsChangedForOrigin'
    """
    Fired when Reporting API endpoints change for an origin.

    Args:
        origin (str): Origin of the document(s) which configured the endpoints.
        endpoints (array[ReportingApiEndpoint]): The endpoints configured for the origin.
    """

    REPORTING_API_REPORT_ADDED = 'Network.reportingApiReportAdded'
    """
    Is sent whenever a new report is added. And after 'enableReportingApi' for all existing reports.

    Args:
        report (ReportingApiReport): The report that was added.
    """

    REPORTING_API_REPORT_UPDATED = 'Network.reportingApiReportUpdated'
    """
    Fired when a report is updated.

    Args:
        report (ReportingApiReport): The report that was updated.
    """

    REQUEST_WILL_BE_SENT_EXTRA_INFO = 'Network.requestWillBeSentExtraInfo'
    """
    Fired when additional information about a requestWillBeSent event is available from the network
    stack.
    Not every requestWillBeSent event will have an additional requestWillBeSentExtraInfo fired for
    it, and there is no guarantee whether requestWillBeSent or requestWillBeSentExtraInfo will be
    fired first for the same request.

    Args:
        requestId (RequestId): Request identifier. Used to match this information to an existing
            requestWillBeSent event.
        associatedCookies (array[AssociatedCookie]): A list of cookies potentially associated to
            the requested URL. This includes both cookies sent with the request and the ones
            not sent; the latter are distinguished by having blockedReasons field set.
        headers (Headers): Raw request headers as they will be sent over the wire.
        connectTiming (ConnectTiming): Connection timing information for the request.
        clientSecurityState (ClientSecurityState): The client security state set for the request.
        siteHasCookieInOtherPartition (bool): Whether the site has partitioned cookies stored
            in a partition different than the current one.
    """

    RESOURCE_CHANGED_PRIORITY = 'Network.resourceChangedPriority'
    """
    Fired when resource loading priority is changed.

    Args:
        requestId (RequestId): Request identifier.
        newPriority (ResourcePriority): New priority.
        timestamp (MonotonicTime): Timestamp.
    """

    RESPONSE_RECEIVED_EARLY_HINTS = 'Network.responseReceivedEarlyHints'
    """
    Fired when 103 Early Hints headers is received in addition to the common response.
    Not every responseReceived event will have an responseReceivedEarlyHints fired.
    Only one responseReceivedEarlyHints may be fired for eached responseReceived event.

    Args:
        requestId (RequestId): Request identifier. Used to match this information to another
            responseReceived event.
        headers (Headers): Raw response headers as they were received over the wire. Duplicate
            headers in the response are represented as a single key with their values
            concatentated using \\n as the separator. See also headersText that contains
            verbatim text for HTTP/1.*.
    """

    RESPONSE_RECEIVED_EXTRA_INFO = 'Network.responseReceivedExtraInfo'
    """
    Fired when additional information about a responseReceived event is available from the
    network stack.
    Not every responseReceived event will have an additional responseReceivedExtraInfo for it,
    and responseReceivedExtraInfo may be fired before or after responseReceived.

    Args:
        requestId (RequestId): Request identifier. Used to match this information to another
            responseReceived event.
        blockedCookies (array[BlockedSetCookieWithReason]): A list of cookies which were
            not stored from the response along with the corresponding reasons for blocking.
            The cookies here may not be valid due to syntax errors, which are represented by
            the invalid cookie line string instead of a proper cookie.
        headers (Headers): Raw response headers as they were received over the wire. Duplicate
            headers in the response are represented as a single key with their values concatentated
            using \\n as the separator. See also headersText that contains verbatim
            text for HTTP/1.*.
        resourceIPAddressSpace (IPAddressSpace): The IP address space of the resource. The address
            space can only be determined once the transport established the connection, so we
            can't send it in requestWillBeSentExtraInfo.
        statusCode (int): The status code of the response. This is useful in cases the request
            failed and no responseReceived event is triggered, which is the case for, e.g.,
            CORS errors. This is also the correct status code for cached requests, where the
            status in responseReceived is a 200 and this will be 304.
        headersText (str): Raw response header text as it was received over the wire. The raw text
            may not always be available, such as in the case of HTTP/2 or QUIC.
        cookiePartitionKey (CookiePartitionKey): The cookie partition key that will be used to
            store partitioned cookies set in this response. Only sent when partitioned
            cookies are enabled.
        cookiePartitionKeyOpaque (bool): True if partitioned cookies are enabled, but the
            partition key is not serializable to string.
        exemptedCookies (array[ExemptedSetCookieWithReason]): A list of cookies which should have
            been blocked by 3PCD but are exempted and stored from the response with the
            corresponding reason.
    """

    SIGNED_EXCHANGE_RECEIVED = 'Network.signedExchangeReceived'
    """
    Fired when a signed exchange was received over the network.

    Args:
        requestId (RequestId): Request identifier.
        info (SignedExchangeInfo): Information about the signed exchange response.
    """

    SUBRESOURCE_WEB_BUNDLE_INNER_RESPONSE_ERROR = 'Network.subresourceWebBundleInnerResponseError'
    """
    Fired when request for resources within a .wbn file failed.

    Args:
        innerRequestId (RequestId): Request identifier of the subresource request.
        innerRequestURL (str): URL of the subresource resource.
        errorMessage (str): Error message.
        bundleRequestId (RequestId): Bundle request identifier. Used to match this information
            to another event. This made be absent in case when the instrumentation was enabled
            only after webbundle was parsed.
    """

    SUBRESOURCE_WEB_BUNDLE_INNER_RESPONSE_PARSED = 'Network.subresourceWebBundleInnerResponseParsed'
    """
    Fired when handling requests for resources within a .wbn file.
    Note: this will only be fired for resources that are requested by the webpage.

    Args:
        innerRequestId (RequestId): Request identifier of the subresource request.
        innerRequestURL (str): URL of the subresource resource.
        bundleRequestId (RequestId): Bundle request identifier. Used to match this information
            to another event. This made be absent in case when the instrumentation was enabled
            only after webbundle was parsed.
    """

    SUBRESOURCE_WEB_BUNDLE_METADATA_ERROR = 'Network.subresourceWebBundleMetadataError'
    """
    Fired once when parsing the .wbn file has failed.

    Args:
        requestId (RequestId): Request identifier. Used to match this information to another event.
        errorMessage (str): Error message.
    """

    SUBRESOURCE_WEB_BUNDLE_METADATA_RECEIVED = 'Network.subresourceWebBundleMetadataReceived'
    """
    Fired once when parsing the .wbn file has succeeded. The event contains the information
    about the web bundle contents.

    Args:
        requestId (RequestId): Request identifier. Used to match this information to another event.
        urls (array[str]): A list of URLs of resources in the subresource Web Bundle.
    """

    TRUST_TOKEN_OPERATION_DONE = 'Network.trustTokenOperationDone'
    """
    Fired exactly once for each Trust Token operation. Depending on the type of the operation
    and whether the operation succeeded or failed, the event is fired before the corresponding
    request was sent or after the response was received.

    Args:
        status (str): Detailed success or error status of the operation.
            Allowed Values: Ok, InvalidArgument, MissingIssuerKeys, FailedPrecondition,
            ResourceExhausted, AlreadyExists, ResourceLimited, Unauthorized, BadResponse,
            InternalError, UnknownError, FulfilledLocally, SiteIssuerLimit
        type (TrustTokenOperationType): Type of Trust Token operation.
        requestId (RequestId): Request identifier.
        topLevelOrigin (str): Top level origin. The context in which the operation was attempted.
        issuerOrigin (str): Origin of the issuer in case of a "Issuance" or "Redemption" operation.
        issuedTokenCount (int): The number of obtained Trust Tokens on a successful
            "Issuance" operation.
    """
