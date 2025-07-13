import pytest

from pydoll.browser.options import ChromiumOptions as Options

from pydoll.exceptions import ArgumentAlreadyExistsInOptions

def test_initial_arguments():
    options = Options()
    assert options.arguments == []


def test_initial_binary_location():
    options = Options()
    assert not options.binary_location


def test_set_binary_location():
    options = Options()
    options.binary_location = '/path/to/browser'
    assert options.binary_location == '/path/to/browser'

def test_set_start_timeout():
    options = Options() 
    options.start_timeout = 30 
    assert options.start_timeout == 30 

def test_add_argument():
    options = Options()
    options.add_argument('--headless')
    assert options.arguments == ['--headless']


def test_add_duplicate_argument():
    options = Options()
    options.add_argument('--headless')
    with pytest.raises(
        ArgumentAlreadyExistsInOptions, match='Argument already exists: --headless'
    ):
        options.add_argument('--headless')


def test_add_multiple_arguments():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    assert options.arguments == ['--headless', '--no-sandbox']
