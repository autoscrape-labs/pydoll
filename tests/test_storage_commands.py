from pydoll.protocol.commands import StorageCommands


def test_clear_cookies():
    expected = {'method': 'Storage.clearCookies', 'params': {}}
    assert StorageCommands.clear_cookies() == expected


def test_set_cookies():
    cookies = [
        {'name': 'cookie1', 'value': 'value1'},
        {'name': 'cookie2', 'value': 'value2'},
    ]
    expected = {'method': 'Storage.setCookies', 'params': {'cookies': cookies}}
    assert StorageCommands.set_cookies(cookies) == expected


def test_get_cookies():
    expected = {'method': 'Storage.getCookies', 'params': {}}
    assert StorageCommands.get_cookies() == expected
