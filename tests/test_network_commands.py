from pydoll.protocol.commands import NetworkCommands


def test_clear_browser_cache():
    assert NetworkCommands.clear_browser_cache() == {
        'method': 'Network.clearBrowserCache'
    }


def test_clear_browser_cookies():
    assert NetworkCommands.clear_browser_cookies() == {
        'method': 'Network.clearBrowserCookies'
    }


def test_delete_cookies():
    name = 'test_cookie'
    url = 'http://example.com'
    expected_command = {
        'method': 'Network.deleteCookies',
        'params': {'name': name, 'url': url},
    }
    assert NetworkCommands.delete_cookies(name, url) == expected_command

    expected_command_without_url = {
        'method': 'Network.deleteCookies',
        'params': {'name': name},
    }
    assert NetworkCommands.delete_cookies(name) == expected_command_without_url


def test_disable_network_events():
    assert NetworkCommands.disable_network_events() == {
        'method': 'Network.disable'
    }


def test_enable_network_events():
    assert NetworkCommands.enable_network_events() == {
        'method': 'Network.enable'
    }


def test_get_cookies():
    urls = ['http://example.com']
    expected_command = {
        'method': 'Network.getCookies',
        'params': {'urls': urls},
    }
    assert NetworkCommands.get_cookies(urls) == expected_command

    expected_command_without_urls = {
        'method': 'Network.getCookies',
        'params': {},
    }
    assert NetworkCommands.get_cookies() == expected_command_without_urls


def test_get_request_post_data():
    request_id = '12345'
    expected_command = {
        'method': 'Network.getRequestPostData',
        'params': {'requestId': request_id},
    }
    assert (
        NetworkCommands.get_request_post_data(request_id) == expected_command
    )


def test_get_response_body():
    request_id = '12345'
    expected_command = {
        'method': 'Network.getResponseBody',
        'params': {'requestId': request_id},
    }
    assert NetworkCommands.get_response_body(request_id) == expected_command


def test_set_cache_disabled():
    cache_disabled = True
    expected_command = {
        'method': 'Network.setCacheDisabled',
        'params': {'cacheDisabled': cache_disabled},
    }
    assert (
        NetworkCommands.set_cache_disabled(cache_disabled) == expected_command
    )


def test_set_cookie():
    name = 'test_cookie'
    value = 'test_value'
    url = 'http://example.com'
    expected_command = {
        'method': 'Network.setCookie',
        'params': {'name': name, 'value': value, 'url': url},
    }
    assert NetworkCommands.set_cookie(name, value, url) == expected_command

    expected_command_without_url = {
        'method': 'Network.setCookie',
        'params': {'name': name, 'value': value},
    }
    assert (
        NetworkCommands.set_cookie(name, value) == expected_command_without_url
    )


def test_set_cookies():
    cookies = [{'name': 'test_cookie', 'value': 'test_value'}]
    expected_command = {
        'method': 'Network.setCookies',
        'params': {'cookies': cookies},
    }
    assert NetworkCommands.set_cookies(cookies) == expected_command


def test_set_extra_http_headers():
    headers = {'Authorization': 'Bearer token'}
    expected_command = {
        'method': 'Network.setExtraHTTPHeaders',
        'params': {'headers': headers},
    }
    assert NetworkCommands.set_extra_http_headers(headers) == expected_command


def test_set_useragent_override():
    user_agent = 'Mozilla/5.0'
    expected_command = {
        'method': 'Network.setUserAgentOverride',
        'params': {'userAgent': user_agent},
    }
    assert (
        NetworkCommands.set_useragent_override(user_agent) == expected_command
    )


def test_get_all_cookies():
    assert NetworkCommands.get_all_cookies() == {
        'method': 'Network.getAllCookies'
    }


def test_search_in_response():
    request_id = '12345'
    query = 'test_query'
    case_sensitive = True
    is_regex = True
    expected_command = {
        'method': 'Network.searchInResponseBody',
        'params': {
            'requestId': request_id,
            'query': query,
            'caseSensitive': case_sensitive,
            'isRegex': is_regex,
        },
    }
    assert (
        NetworkCommands.search_in_response(
            request_id, query, case_sensitive, is_regex
        )
        == expected_command
    )


def test_set_blocked_urls():
    urls = ['http://example.com']
    expected_command = {
        'method': 'Network.setBlockedURLs',
        'params': {'urls': urls},
    }
    assert NetworkCommands.set_blocked_urls(urls) == expected_command
