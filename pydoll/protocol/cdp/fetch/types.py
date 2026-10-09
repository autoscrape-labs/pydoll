from enum import Enum

from typing_extensions import NotRequired, TypedDict

from pydoll.protocol.cdp.network.types import ResourceType


class RequestStage(str, Enum):
    """Stages of the request to handle."""

    REQUEST = 'Request'
    RESPONSE = 'Response'


class AuthChallengeSource(str, Enum):
    """Source of the authentication challenge."""

    SERVER = 'Server'
    PROXY = 'Proxy'


class AuthChallengeResponseType(str, Enum):
    """The decision on what to do in response to the authorization challenge."""

    DEFAULT = 'Default'
    CANCEL_AUTH = 'CancelAuth'
    PROVIDE_CREDENTIALS = 'ProvideCredentials'


class RequestPattern(TypedDict, total=False):
    """Pattern for request interception."""

    urlPattern: str  # Wildcards allowed. Omitting is equivalent to "*".
    resourceType: ResourceType
    requestStage: RequestStage


class HeaderEntry(TypedDict):
    """Response HTTP header entry."""

    name: str
    value: str


class AuthChallenge(TypedDict):
    """Authorization challenge for HTTP status code 401 or 407."""

    source: NotRequired[AuthChallengeSource]
    origin: str
    scheme: str  # e.g. basic, digest
    realm: str


class AuthChallengeResponse(TypedDict):
    """Response to an AuthChallenge."""

    response: AuthChallengeResponseType
    username: NotRequired[str]
    password: NotRequired[str]
