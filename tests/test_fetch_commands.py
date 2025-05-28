from pydoll.protocol.commands import FetchCommands


def test_continue_request():
    request_id = '123'
    url = 'http://example.com'
    method = 'POST'
    post_data = 'data'
    headers = {'Content-Type': 'application/json'}
    intercept_response = True

    expected_result = {
        'method': 'Fetch.continueRequest',
        'params': {
            'requestId': request_id,
            'url': url,
            'method': method,
            'postData': post_data,
            'headers': [{'name': 'Content-Type', 'value': 'application/json'}],
            'interceptResponse': intercept_response,
        },
    }

    result = FetchCommands.continue_request(
        request_id, url, method, post_data, headers, intercept_response
    )
    assert result == expected_result


def test_continue_request_with_auth():
    request_id = '123'
    proxy_username = 'user'
    proxy_password = 'pass'

    expected_result = {
        'method': 'Fetch.continueWithAuth',
        'params': {
            'requestId': request_id,
            'authChallengeResponse': {
                'response': 'ProvideCredentials',
                'username': proxy_username,
                'password': proxy_password,
            },
        },
    }

    result = FetchCommands.continue_request_with_auth(
        request_id, proxy_username, proxy_password
    )
    assert result == expected_result


def test_disable_fetch_events():
    expected_result = {'method': 'Fetch.disable', 'params': {}}
    result = FetchCommands.disable_fetch_events()
    assert result == expected_result


def test_enable_fetch_events():
    handle_auth_requests = True
    resource_type = 'Document'

    expected_result = {
        'method': 'Fetch.enable',
        'params': {
            'patterns': [{'urlPattern': '*', 'resourceType': resource_type}],
            'handleAuthRequests': handle_auth_requests,
        },
    }

    result = FetchCommands.enable_fetch_events(
        handle_auth_requests, resource_type
    )
    assert result == expected_result


def test_fail_request():
    request_id = '123'
    error_reason = 'Failed'

    expected_result = {
        'method': 'Fetch.failRequest',
        'params': {
            'requestId': request_id,
            'errorReason': error_reason,
        },
    }

    result = FetchCommands.fail_request(request_id, error_reason)
    assert result == expected_result


def test_fulfill_request():
    request_id = '123'
    response_code = 200
    response_headers = {'Content-Type': 'application/json'}
    binary_response_headers = 'binary_headers'
    body = 'response_body'
    response_phrase = 'OK'

    expected_result = {
        'method': 'Fetch.fulfillRequest',
        'params': {
            'requestId': request_id,
            'responseCode': response_code,
            'responseHeaders': response_headers,
            'binaryResponseHeaders': binary_response_headers,
            'body': body,
            'responsePhrase': response_phrase,
        },
    }

    result = FetchCommands.fulfill_request(
        request_id,
        response_code,
        response_headers,
        binary_response_headers,
        body,
        response_phrase,
    )
    assert result == expected_result


def test_get_response_body():
    request_id = '123'

    expected_result = {
        'method': 'Fetch.getResponseBody',
        'params': {
            'requestId': request_id,
        },
    }

    result = FetchCommands.get_response_body(request_id)
    assert result == expected_result


def test_continue_response():
    request_id = '123'
    response_code = 200
    response_headers = {'Content-Type': 'application/json'}
    binary_response_headers = 'binary_headers'
    response_phrase = 'OK'

    expected_result = {
        'method': 'Fetch.continueResponse',
        'params': {
            'requestId': request_id,
            'responseCode': response_code,
            'responseHeaders': response_headers,
            'binaryResponseHeaders': binary_response_headers,
            'responsePhrase': response_phrase,
        },
    }

    result = FetchCommands.continue_response(
        request_id,
        response_code,
        response_headers,
        binary_response_headers,
        response_phrase,
    )
    assert result == expected_result
