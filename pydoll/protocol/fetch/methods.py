from enum import Enum


class FetchMethod(str, Enum):
    CONTINUE_REQUEST = 'Fetch.continueRequest'
    CONTINUE_WITH_AUTH = 'Fetch.continueWithAuth'
    DISABLE = 'Fetch.disable'
    ENABLE = 'Fetch.enable'
    FAIL_REQUEST = 'Fetch.failRequest'
    FULFILL_REQUEST = 'Fetch.fulfillRequest'
    GET_RESPONSE_BODY = 'Fetch.getResponseBody'
    TAKE_RESPONSE_BODY_AS_STREAM = 'Fetch.takeResponseBodyAsStream'
    CONTINUE_RESPONSE = 'Fetch.continueResponse'
