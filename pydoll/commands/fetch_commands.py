from typing import Optional

from pydoll.constants import (
    AuthChallengeResponseValues,
    NetworkErrorReason,
    RequestMethod,
    RequestStage,
    ResourceType,
)
from pydoll.protocol.base import Command, Response
from pydoll.protocol.fetch.methods import FetchMethod
from pydoll.protocol.fetch.params import (
    AuthChallengeResponseDict,
    ContinueRequestParams,
    ContinueResponseParams,
    ContinueWithAuthParams,
    FailRequestParams,
    FetchEnableParams,
    FulfillRequestParams,
    GetResponseBodyParams,
    HeaderEntry,
    RequestPattern,
    TakeResponseBodyAsStreamParams,
)
from pydoll.protocol.fetch.responses import (
    GetResponseBodyResponse,
    TakeResponseBodyAsStreamResponse,
)


class FetchCommands:
    """
    This class encapsulates the fetch commands of the Chrome DevTools Protocol (CDP).

    CDP's Fetch domain allows interception and modification of network requests
    at the application layer. This enables developers to examine, modify, and
    control network traffic, which is particularly useful for testing, debugging,
    and advanced automation scenarios.

    The commands defined in this class provide functionality for:
    - Enabling and disabling fetch request interception
    - Continuing, fulfilling, or failing intercepted requests
    - Handling authentication challenges
    - Retrieving and modifying response bodies
    - Processing response data as streams
    """

    @staticmethod
    def continue_request(  # noqa: PLR0913, PLR0917
        request_id: str,
        url: Optional[str] = None,
        method: Optional[RequestMethod] = None,
        post_data: Optional[str] = None,
        headers: Optional[list[HeaderEntry]] = None,
        intercept_response: Optional[bool] = None,
    ) -> Command[Response]:
        """
        Creates a command to continue a paused fetch request.

        This command allows the browser to resume a fetch operation that has
        been intercepted. You can modify the fetch request URL, method,
        headers, and body before continuing.

        Args:
            request_id (str): The ID of the fetch request to continue.
            url (Optional[str]): The new URL for the fetch request. Defaults to None.
            method (Optional[RequestMethod]): The HTTP method to use (e.g., 'GET',
                'POST'). Defaults to None.
            post_data (Optional[dict]): The body data to send with the fetch
                request. Defaults to None.
            headers (Optional[list[HeaderEntry]]): A list of HTTP headers to include
                in the fetch request. Defaults to None.
            intercept_response (Optional[bool]): Indicates if the response
                should be intercepted. Defaults to None.

        Returns:
            Command[Response]: A command for continuing the fetch request.
        """
        params = ContinueRequestParams(requestId=request_id)
        if url is not None:
            params['url'] = url
        if method is not None:
            params['method'] = method
        if post_data is not None:
            params['postData'] = post_data
        if headers is not None:
            params['headers'] = headers
        if intercept_response is not None:
            params['interceptResponse'] = intercept_response
        return Command(method=FetchMethod.CONTINUE_REQUEST, params=params)

    @staticmethod
    def continue_request_with_auth(
        request_id: str,
        auth_challenge_response: AuthChallengeResponseValues,
        proxy_username: Optional[str] = None,
        proxy_password: Optional[str] = None,
    ) -> Command[Response]:
        """
        Creates a command to continue a paused fetch request with
        authentication.

        This command is used when the fetch operation requires authentication.
        It provides the necessary credentials to continue the request.

        Args:
            request_id (str): The ID of the fetch request to continue.
            auth_challenge_response (AuthChallengeResponseValues): The authentication
                challenge response type.
            proxy_username (Optional[str]): The username for proxy authentication.
                Defaults to None.
            proxy_password (Optional[str]): The password for proxy authentication.
                Defaults to None.

        Returns:
            Command[Response]: A command for continuing the fetch request with
                authentication.
        """
        auth_challenge_response_dict = AuthChallengeResponseDict(response=auth_challenge_response)
        if proxy_username is not None:
            auth_challenge_response_dict['username'] = proxy_username
        if proxy_password is not None:
            auth_challenge_response_dict['password'] = proxy_password

        params = ContinueWithAuthParams(
            requestId=request_id,
            authChallengeResponse=auth_challenge_response_dict,
        )
        return Command(method=FetchMethod.CONTINUE_WITH_AUTH, params=params)

    @staticmethod
    def disable() -> Command[Response]:
        """
        Creates a command to disable fetch interception.

        This command stops the browser from intercepting fetch requests.

        Returns:
            Command[Response]: A command for disabling fetch interception.
        """
        return Command(method=FetchMethod.DISABLE)

    @staticmethod
    def enable(
        handle_auth_requests: bool,
        url_pattern: str = '*',
        resource_type: Optional[ResourceType] = None,
        request_stage: Optional[RequestStage] = None,
    ) -> Command[Response]:
        """
        Creates a command to enable fetch interception.

        This command allows the browser to start intercepting fetch requests.
        You can specify whether to handle authentication challenges and the
        types of resources to intercept.

        Args:
            handle_auth_requests (bool): Indicates if authentication requests
                should be handled.
            url_pattern (str): Pattern to match URLs for interception. Defaults to '*'.
            resource_type (Optional[ResourceType]): The type of resource to intercept.
                Defaults to None.
            request_stage (Optional[RequestStage]): The stage of the request to intercept.
                Defaults to None.

        Returns:
            Command[Response]: A command for enabling fetch interception.
        """
        request_pattern = RequestPattern(urlPattern=url_pattern)
        if resource_type is not None:
            request_pattern['resourceType'] = resource_type
        if request_stage is not None:
            request_pattern['requestStage'] = request_stage

        params = FetchEnableParams(
            patterns=[request_pattern], handleAuthRequests=handle_auth_requests
        )
        return Command(method=FetchMethod.ENABLE, params=params)

    @staticmethod
    def fail_request(request_id: str, error_reason: NetworkErrorReason) -> Command[Response]:
        """
        Creates a command to simulate a failure in a fetch request.

        This command allows you to simulate a failure for a specific fetch
        operation, providing a reason for the failure.

        Args:
            request_id (str): The ID of the fetch request to fail.
            error_reason (NetworkErrorReason): The reason for the failure.

        Returns:
            Command[Response]: A command for failing the fetch request.
        """
        params = FailRequestParams(requestId=request_id, errorReason=error_reason)
        return Command(method=FetchMethod.FAIL_REQUEST, params=params)

    @staticmethod
    def fulfill_request(  # noqa: PLR0913, PLR0917
        request_id: str,
        response_code: int,
        response_headers: Optional[list[HeaderEntry]] = None,
        body: Optional[str] = None,
        response_phrase: Optional[str] = None,
    ) -> Command[Response]:
        """
        Creates a command to fulfill a fetch request with a custom response.

        This command allows you to provide a custom response for a fetch
        operation, including the HTTP status code, headers, and body content.

        Args:
            request_id (str): The ID of the fetch request to fulfill.
            response_code (int): The HTTP status code to return.
            response_headers (Optional[list[HeaderEntry]]): A list of response headers.
                Defaults to None.
            body (Optional[dict]): The body content of the response. Defaults to None.
            response_phrase (Optional[str]): The response phrase (e.g., 'OK',
                'Not Found'). Defaults to None.

        Returns:
            Command[Response]: A command for fulfilling the fetch request.
        """
        params = FulfillRequestParams(
            requestId=request_id,
            responseCode=response_code,
        )
        if response_headers is not None:
            params['responseHeaders'] = response_headers
        if body is not None:
            params['body'] = body
        if response_phrase is not None:
            params['responsePhrase'] = response_phrase
        return Command(method=FetchMethod.FULFILL_REQUEST, params=params)

    @staticmethod
    def get_response_body(request_id: str) -> Command[GetResponseBodyResponse]:
        """
        Creates a command to retrieve the response body of a fetch request.

        This command allows you to access the body of a completed fetch
        operation, which can be useful for analyzing the response data.

        Args:
            request_id (str): The ID of the fetch request to retrieve the body
                from.

        Returns:
            Command[GetResponseBodyResponse]: A command for getting the response body.
        """
        params = GetResponseBodyParams(requestId=request_id)
        return Command(method=FetchMethod.GET_RESPONSE_BODY, params=params)

    @staticmethod
    def continue_response(
        request_id: str,
        response_code: Optional[int] = None,
        response_headers: Optional[list[HeaderEntry]] = None,
        response_phrase: Optional[str] = None,
    ) -> Command[Response]:
        """
        Creates a command to continue a fetch response for an intercepted
        request.

        This command allows the browser to continue the response flow for a
        specific fetch request, including customizing the HTTP status code,
        headers, and response phrase.

        Args:
            request_id (str): The ID of the fetch request to continue the
                response for.
            response_code (Optional[int]): The HTTP status code to send.
                Defaults to None.
            response_headers (Optional[list[HeaderEntry]]): A list of response headers.
                Defaults to None.
            response_phrase (Optional[str]): The response phrase (e.g., 'OK').
                Defaults to None.

        Returns:
            Command[Response]: A command for continuing the fetch response.
        """
        params = ContinueResponseParams(requestId=request_id)
        if response_code is not None:
            params['responseCode'] = response_code
        if response_headers is not None:
            params['responseHeaders'] = response_headers
        if response_phrase is not None:
            params['responsePhrase'] = response_phrase
        return Command(method=FetchMethod.CONTINUE_RESPONSE, params=params)

    @staticmethod
    def take_response_body_as_stream(
        request_id: str,
    ) -> Command[TakeResponseBodyAsStreamResponse]:
        """
        Creates a command to take the response body as a stream.

        This command allows you to receive the response body as a stream
        which can be useful for handling large responses.

        Args:
            request_id (str): The ID of the fetch request to take the response
                body stream from.

        Returns:
            Command[TakeResponseBodyAsStreamResponse]: A command for taking the response
                body as a stream.
        """
        params = TakeResponseBodyAsStreamParams(requestId=request_id)
        return Command(method=FetchMethod.TAKE_RESPONSE_BODY_AS_STREAM, params=params)
