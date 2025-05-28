from enum import Enum


class FetchEvent(str, Enum):
    """
    Events from the Fetch domain of the Chrome DevTools Protocol.

    This enumeration contains the names of Fetch-related events that can be
    received from the Chrome DevTools Protocol. These events provide information
    about network requests that can be intercepted, modified, or responded to
    by the client.
    """

    AUTH_REQUIRED = 'Fetch.authRequired'
    """
    Issued when the domain is enabled with handleAuthRequests set to true.
    The request is paused until client responds with continueWithAuth.

    Args:
        requestId (RequestId): Each request the page makes will have a unique id.
        request (Network.Request): The details of the request.
        frameId (Page.FrameId): The id of the frame that initiated the request.
        resourceType (Network.ResourceType): How the requested resource will be used.
        authChallenge (AuthChallenge): Details of the Authorization Challenge encountered.
            If this is set, client should respond with continueRequest that contains
            AuthChallengeResponse.
    """

    REQUEST_PAUSED = 'Fetch.requestPaused'
    """
    Issued when the domain is enabled and the request URL matches the specified filter.

    The request is paused until the client responds with one of continueRequest,
    failRequest or fulfillRequest. The stage of the request can be determined by
    presence of responseErrorReason and responseStatusCode -- the request is at the
    response stage if either of these fields is present and in the request stage otherwise.

    Redirect responses and subsequent requests are reported similarly to regular responses
    and requests. Redirect responses may be distinguished by the value of responseStatusCode
    (which is one of 301, 302, 303, 307, 308) along with presence of the location header.
    Requests resulting from a redirect will have redirectedRequestId field set.

    Args:
        requestId (RequestId): Each request the page makes will have a unique id.
        request (Network.Request): The details of the request.
        frameId (Page.FrameId): The id of the frame that initiated the request.
        resourceType (Network.ResourceType): How the requested resource will be used.
        responseErrorReason (Network.ErrorReason): Response error if intercepted at response stage.
        responseStatusCode (int): Response code if intercepted at response stage.
        responseStatusText (str): Response status text if intercepted at response stage.
        responseHeaders (array[HeaderEntry]): Response headers if intercepted at the response stage.
        networkId (Network.RequestId): If the intercepted request had a corresponding
            Network.requestWillBeSent event fired for it, then this networkId will be
            the same as the requestId present in the requestWillBeSent event.
        redirectedRequestId (RequestId): If the request is due to a redirect response
            from the server, the id of the request that has caused the redirect.
    """
