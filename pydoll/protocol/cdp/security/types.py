from enum import Enum


class MixedContentType(str, Enum):
    """
    The mixed content type of the request.
    """

    BLOCKABLE = 'blockable'
    OPTIONALLY_BLOCKABLE = 'optionally-blockable'
    NONE = 'none'


class SecurityState(str, Enum):
    """
    The security state of the page.
    """

    UNKNOWN = 'unknown'
    NEUTRAL = 'neutral'
    SAFE = 'safe'
    INSECURE = 'insecure'
    SECURE = 'secure'
    INFO = 'info'
    INSECURE_BROKEN = 'insecure-broken'
