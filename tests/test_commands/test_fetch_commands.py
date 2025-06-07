import pytest
from pydoll.commands.fetch_commands import FetchCommands
from pydoll.constants import (
    AuthChallengeResponseValues,
    NetworkErrorReason,
    RequestMethod,
    RequestStage,
    ResourceType,
)
from pydoll.protocol.fetch.methods import FetchMethod


class TestFetchCommands:
    """Tests for the FetchCommands class."""

    def test_continue_request_minimal(self):
        """Test continue_request command with minimal parameters."""
        request_id = 'req123'
        result = FetchCommands.continue_request(request_id=request_id)
        
        assert result['method'] == FetchMethod.CONTINUE_REQUEST
        assert result['params']['requestId'] == request_id

    def test_continue_request_with_url(self):
        """Test continue_request command with URL."""
        request_id = 'req123'
        url = 'https://example.com'
        result = FetchCommands.continue_request(request_id=request_id, url=url)
        
        assert result['method'] == FetchMethod.CONTINUE_REQUEST
        assert result['params']['requestId'] == request_id
        assert result['params']['url'] == url

    def test_continue_request_with_method(self):
        """Test continue_request command with HTTP method."""
        request_id = 'req123'
        method = RequestMethod.POST
        result = FetchCommands.continue_request(request_id=request_id, method=method)
        
        assert result['method'] == FetchMethod.CONTINUE_REQUEST
        assert result['params']['requestId'] == request_id
        assert result['params']['method'] == method

    def test_continue_request_with_post_data(self):
        """Test continue_request command with POST data."""
        request_id = 'req123'
        post_data = '{"key": "value"}'
        result = FetchCommands.continue_request(request_id=request_id, post_data=post_data)
        
        assert result['method'] == FetchMethod.CONTINUE_REQUEST
        assert result['params']['requestId'] == request_id
        assert result['params']['postData'] == post_data

    def test_continue_request_with_headers(self):
        """Test continue_request command with headers."""
        request_id = 'req123'
        headers = [{'name': 'Content-Type', 'value': 'application/json'}]
        result = FetchCommands.continue_request(request_id=request_id, headers=headers)
        
        assert result['method'] == FetchMethod.CONTINUE_REQUEST
        assert result['params']['requestId'] == request_id
        assert result['params']['headers'] == headers

    def test_continue_request_with_intercept_response(self):
        """Test continue_request command with intercept_response."""
        request_id = 'req123'
        intercept_response = True
        result = FetchCommands.continue_request(
            request_id=request_id, 
            intercept_response=intercept_response
        )
        
        assert result['method'] == FetchMethod.CONTINUE_REQUEST
        assert result['params']['requestId'] == request_id
        assert result['params']['interceptResponse'] == intercept_response

    def test_continue_request_with_all_params(self):
        """Test continue_request command with all parameters."""
        request_id = 'req123'
        url = 'https://example.com'
        method = RequestMethod.PUT
        post_data = '{"data": "test"}'
        headers = [{'name': 'Authorization', 'value': 'Bearer token'}]
        intercept_response = False
        
        result = FetchCommands.continue_request(
            request_id=request_id,
            url=url,
            method=method,
            post_data=post_data,
            headers=headers,
            intercept_response=intercept_response
        )
        
        assert result['method'] == FetchMethod.CONTINUE_REQUEST
        assert result['params']['requestId'] == request_id
        assert result['params']['url'] == url
        assert result['params']['method'] == method
        assert result['params']['postData'] == post_data
        assert result['params']['headers'] == headers
        assert result['params']['interceptResponse'] == intercept_response

    def test_continue_request_with_auth_minimal(self):
        """Test continue_request_with_auth command with minimal parameters."""
        request_id = 'req123'
        auth_response = AuthChallengeResponseValues.PROVIDE_CREDENTIALS
        result = FetchCommands.continue_request_with_auth(
            request_id=request_id,
            auth_challenge_response=auth_response
        )
        
        assert result['method'] == FetchMethod.CONTINUE_WITH_AUTH
        assert result['params']['requestId'] == request_id
        assert result['params']['authChallengeResponse']['response'] == auth_response

    def test_continue_request_with_auth_credentials(self):
        """Test continue_request_with_auth command with credentials."""
        request_id = 'req123'
        auth_response = AuthChallengeResponseValues.PROVIDE_CREDENTIALS
        username = 'testuser'
        password = 'testpass'
        
        result = FetchCommands.continue_request_with_auth(
            request_id=request_id,
            auth_challenge_response=auth_response,
            proxy_username=username,
            proxy_password=password
        )
        
        assert result['method'] == FetchMethod.CONTINUE_WITH_AUTH
        assert result['params']['requestId'] == request_id
        assert result['params']['authChallengeResponse']['response'] == auth_response
        assert result['params']['authChallengeResponse']['username'] == username
        assert result['params']['authChallengeResponse']['password'] == password

    def test_continue_request_with_auth_cancel(self):
        """Test continue_request_with_auth command with cancel response."""
        request_id = 'req123'
        auth_response = AuthChallengeResponseValues.CANCEL_AUTH
        
        result = FetchCommands.continue_request_with_auth(
            request_id=request_id,
            auth_challenge_response=auth_response
        )
        
        assert result['method'] == FetchMethod.CONTINUE_WITH_AUTH
        assert result['params']['requestId'] == request_id
        assert result['params']['authChallengeResponse']['response'] == auth_response

    def test_disable(self):
        """Test disable command."""
        result = FetchCommands.disable()
        
        assert result['method'] == FetchMethod.DISABLE
        assert 'params' not in result

    def test_enable_minimal(self):
        """Test enable command with minimal parameters."""
        handle_auth = True
        result = FetchCommands.enable(handle_auth_requests=handle_auth)
        
        assert result['method'] == FetchMethod.ENABLE
        assert result['params']['handleAuthRequests'] == handle_auth
        assert result['params']['patterns'][0]['urlPattern'] == '*'

    def test_enable_with_url_pattern(self):
        """Test enable command with custom URL pattern."""
        handle_auth = False
        url_pattern = 'https://api.example.com/*'
        result = FetchCommands.enable(
            handle_auth_requests=handle_auth,
            url_pattern=url_pattern
        )
        
        assert result['method'] == FetchMethod.ENABLE
        assert result['params']['handleAuthRequests'] == handle_auth
        assert result['params']['patterns'][0]['urlPattern'] == url_pattern

    def test_enable_with_resource_type(self):
        """Test enable command with resource type."""
        handle_auth = True
        resource_type = ResourceType.DOCUMENT
        result = FetchCommands.enable(
            handle_auth_requests=handle_auth,
            resource_type=resource_type
        )
        
        assert result['method'] == FetchMethod.ENABLE
        assert result['params']['handleAuthRequests'] == handle_auth
        assert result['params']['patterns'][0]['resourceType'] == resource_type

    def test_enable_with_request_stage(self):
        """Test enable command with request stage."""
        handle_auth = True
        request_stage = RequestStage.REQUEST
        result = FetchCommands.enable(
            handle_auth_requests=handle_auth,
            request_stage=request_stage
        )
        
        assert result['method'] == FetchMethod.ENABLE
        assert result['params']['handleAuthRequests'] == handle_auth
        assert result['params']['patterns'][0]['requestStage'] == request_stage

    def test_enable_with_all_params(self):
        """Test enable command with all parameters."""
        handle_auth = True
        url_pattern = 'https://test.com/*'
        resource_type = ResourceType.XHR
        request_stage = RequestStage.RESPONSE
        
        result = FetchCommands.enable(
            handle_auth_requests=handle_auth,
            url_pattern=url_pattern,
            resource_type=resource_type,
            request_stage=request_stage
        )
        
        assert result['method'] == FetchMethod.ENABLE
        assert result['params']['handleAuthRequests'] == handle_auth
        assert result['params']['patterns'][0]['urlPattern'] == url_pattern
        assert result['params']['patterns'][0]['resourceType'] == resource_type
        assert result['params']['patterns'][0]['requestStage'] == request_stage

    def test_fail_request(self):
        """Test fail_request command."""
        request_id = 'req123'
        error_reason = NetworkErrorReason.FAILED
        result = FetchCommands.fail_request(
            request_id=request_id,
            error_reason=error_reason
        )
        
        assert result['method'] == FetchMethod.FAIL_REQUEST
        assert result['params']['requestId'] == request_id
        assert result['params']['errorReason'] == error_reason

    def test_fail_request_with_different_error(self):
        """Test fail_request command with different error reason."""
        request_id = 'req123'
        error_reason = NetworkErrorReason.TIMED_OUT
        result = FetchCommands.fail_request(
            request_id=request_id,
            error_reason=error_reason
        )
        
        assert result['method'] == FetchMethod.FAIL_REQUEST
        assert result['params']['requestId'] == request_id
        assert result['params']['errorReason'] == error_reason

    def test_fulfill_request_minimal(self):
        """Test fulfill_request command with minimal parameters."""
        request_id = 'req123'
        response_code = 200
        result = FetchCommands.fulfill_request(
            request_id=request_id,
            response_code=response_code
        )
        
        assert result['method'] == FetchMethod.FULFILL_REQUEST
        assert result['params']['requestId'] == request_id
        assert result['params']['responseCode'] == response_code

    def test_fulfill_request_with_headers(self):
        """Test fulfill_request command with response headers."""
        request_id = 'req123'
        response_code = 201
        headers = [{'name': 'Content-Type', 'value': 'application/json'}]
        result = FetchCommands.fulfill_request(
            request_id=request_id,
            response_code=response_code,
            response_headers=headers
        )
        
        assert result['method'] == FetchMethod.FULFILL_REQUEST
        assert result['params']['requestId'] == request_id
        assert result['params']['responseCode'] == response_code
        assert result['params']['responseHeaders'] == headers

    def test_fulfill_request_with_body(self):
        """Test fulfill_request command with response body."""
        request_id = 'req123'
        response_code = 200
        body = {'message': 'success'}
        result = FetchCommands.fulfill_request(
            request_id=request_id,
            response_code=response_code,
            body=body
        )
        
        assert result['method'] == FetchMethod.FULFILL_REQUEST
        assert result['params']['requestId'] == request_id
        assert result['params']['responseCode'] == response_code
        assert result['params']['body'] == body

    def test_fulfill_request_with_response_phrase(self):
        """Test fulfill_request command with response phrase."""
        request_id = 'req123'
        response_code = 404
        response_phrase = 'Not Found'
        result = FetchCommands.fulfill_request(
            request_id=request_id,
            response_code=response_code,
            response_phrase=response_phrase
        )
        
        assert result['method'] == FetchMethod.FULFILL_REQUEST
        assert result['params']['requestId'] == request_id
        assert result['params']['responseCode'] == response_code
        assert result['params']['responsePhrase'] == response_phrase

    def test_fulfill_request_with_all_params(self):
        """Test fulfill_request command with all parameters."""
        request_id = 'req123'
        response_code = 500
        headers = [{'name': 'Server', 'value': 'nginx'}]
        body = {'error': 'Internal Server Error'}
        response_phrase = 'Internal Server Error'
        
        result = FetchCommands.fulfill_request(
            request_id=request_id,
            response_code=response_code,
            response_headers=headers,
            body=body,
            response_phrase=response_phrase
        )
        
        assert result['method'] == FetchMethod.FULFILL_REQUEST
        assert result['params']['requestId'] == request_id
        assert result['params']['responseCode'] == response_code
        assert result['params']['responseHeaders'] == headers
        assert result['params']['body'] == body
        assert result['params']['responsePhrase'] == response_phrase

    def test_get_response_body(self):
        """Test get_response_body command."""
        request_id = 'req123'
        result = FetchCommands.get_response_body(request_id=request_id)
        
        assert result['method'] == FetchMethod.GET_RESPONSE_BODY
        assert result['params']['requestId'] == request_id

    def test_continue_response_minimal(self):
        """Test continue_response command with minimal parameters."""
        request_id = 'req123'
        result = FetchCommands.continue_response(request_id=request_id)
        
        assert result['method'] == FetchMethod.CONTINUE_RESPONSE
        assert result['params']['requestId'] == request_id

    def test_continue_response_with_code(self):
        """Test continue_response command with response code."""
        request_id = 'req123'
        response_code = 302
        result = FetchCommands.continue_response(
            request_id=request_id,
            response_code=response_code
        )
        
        assert result['method'] == FetchMethod.CONTINUE_RESPONSE
        assert result['params']['requestId'] == request_id
        assert result['params']['responseCode'] == response_code

    def test_continue_response_with_headers(self):
        """Test continue_response command with headers."""
        request_id = 'req123'
        headers = [{'name': 'Location', 'value': 'https://redirect.com'}]
        result = FetchCommands.continue_response(
            request_id=request_id,
            response_headers=headers
        )
        
        assert result['method'] == FetchMethod.CONTINUE_RESPONSE
        assert result['params']['requestId'] == request_id
        assert result['params']['responseHeaders'] == headers

    def test_continue_response_with_phrase(self):
        """Test continue_response command with response phrase."""
        request_id = 'req123'
        response_phrase = 'Found'
        result = FetchCommands.continue_response(
            request_id=request_id,
            response_phrase=response_phrase
        )
        
        assert result['method'] == FetchMethod.CONTINUE_RESPONSE
        assert result['params']['requestId'] == request_id
        assert result['params']['responsePhrase'] == response_phrase

    def test_continue_response_with_all_params(self):
        """Test continue_response command with all parameters."""
        request_id = 'req123'
        response_code = 301
        headers = [{'name': 'Location', 'value': 'https://new-location.com'}]
        response_phrase = 'Moved Permanently'
        
        result = FetchCommands.continue_response(
            request_id=request_id,
            response_code=response_code,
            response_headers=headers,
            response_phrase=response_phrase
        )
        
        assert result['method'] == FetchMethod.CONTINUE_RESPONSE
        assert result['params']['requestId'] == request_id
        assert result['params']['responseCode'] == response_code
        assert result['params']['responseHeaders'] == headers
        assert result['params']['responsePhrase'] == response_phrase

    def test_take_response_body_as_stream(self):
        """Test take_response_body_as_stream command."""
        request_id = 'req123'
        result = FetchCommands.take_response_body_as_stream(request_id=request_id)
        
        assert result['method'] == FetchMethod.TAKE_RESPONSE_BODY_AS_STREAM
        assert result['params']['requestId'] == request_id
