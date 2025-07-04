from enum import Enum


class NetworkMethod(str, Enum):
    CLEAR_BROWSER_CACHE = 'Network.clearBrowserCache'
    CLEAR_BROWSER_COOKIES = 'Network.clearBrowserCookies'
    DELETE_COOKIES = 'Network.deleteCookies'
    DISABLE = 'Network.disable'
    EMULATE_NETWORK_CONDITIONS = 'Network.emulateNetworkConditions'
    ENABLE = 'Network.enable'
    GET_COOKIES = 'Network.getCookies'
    GET_REQUEST_POST_DATA = 'Network.getRequestPostData'
    GET_RESPONSE_BODY = 'Network.getResponseBody'
    SET_BYPASS_SERVICE_WORKER = 'Network.setBypassServiceWorker'
    SET_CACHE_DISABLED = 'Network.setCacheDisabled'
    SET_COOKIE = 'Network.setCookie'
    SET_COOKIES = 'Network.setCookies'
    SET_EXTRA_HTTP_HEADERS = 'Network.setExtraHTTPHeaders'
    SET_USER_AGENT_OVERRIDE = 'Network.setUserAgentOverride'
    CLEAR_ACCEPTED_ENCODINGS_OVERRIDE = 'Network.clearAcceptedEncodingsOverride'
    ENABLE_REPORTING_API = 'Network.enableReportingApi'
    GET_CERTIFICATE = 'Network.getCertificate'
    GET_RESPONSE_BODY_FOR_INTERCEPTION = 'Network.getResponseBodyForInterception'
    GET_SECURITY_ISOLATION_STATUS = 'Network.getSecurityIsolationStatus'
    LOAD_NETWORK_RESOURCE = 'Network.loadNetworkResource'
    REPLAY_XHR = 'Network.replayXHR'
    SEARCH_IN_RESPONSE_BODY = 'Network.searchInResponseBody'
    SET_ACCEPTED_ENCODINGS = 'Network.setAcceptedEncodings'
    SET_ATTACH_DEBUG_STACK = 'Network.setAttachDebugStack'
    SET_BLOCKED_URLS = 'Network.setBlockedURLs'
    SET_COOKIE_CONTROLS = 'Network.setCookieControls'
    STREAM_RESOURCE_CONTENT = 'Network.streamResourceContent'
    TAKE_RESPONSE_BODY_FOR_INTERCEPTION_AS_STREAM = (
        'Network.takeResponseBodyForInterceptionAsStream'
    )
