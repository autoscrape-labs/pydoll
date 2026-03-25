from enum import Enum

from typing_extensions import NotRequired, TypedDict

from pydoll.protocol.bidi.browser.types import UserContext
from pydoll.protocol.bidi.browsing_context.types import BrowsingContext

Channel = str
"""Unique identifier for a messaging channel."""

Handle = str
"""Handle to an object owned by the ECMAScript runtime."""

InternalId = str
"""Identifier for a previously serialized RemoteValue during serialization."""

PreloadScript = str
"""Handle to a script that will run on realm creation."""

Realm = str
"""Unique identifier for an ECMAScript realm."""

SharedId = str
"""Reference to a DOM Node usable in any realm."""


class RealmType(str, Enum):
    """Types of ECMAScript realms."""

    WINDOW = 'window'
    DEDICATED_WORKER = 'dedicated-worker'
    SHARED_WORKER = 'shared-worker'
    SERVICE_WORKER = 'service-worker'
    WORKER = 'worker'
    PAINT_WORKLET = 'paint-worklet'
    AUDIO_WORKLET = 'audio-worklet'
    WORKLET = 'worklet'


class ResultOwnership(str, Enum):
    """How serialized value ownership will be treated."""

    ROOT = 'root'
    NONE = 'none'


class SpecialNumber(str, Enum):
    """Special number string representations."""

    NAN = 'NaN'
    NEGATIVE_ZERO = '-0'
    INFINITY = 'Infinity'
    NEGATIVE_INFINITY = '-Infinity'


class SerializationOptions(TypedDict, total=False):
    """Options for serializing ECMAScript objects."""

    maxDomDepth: int | None  # default 0
    maxObjectDepth: int | None  # default null
    includeShadowTree: str  # "none" / "open" / "all", default "none"


class StackFrame(TypedDict):
    """A frame in a stack trace."""

    columnNumber: int
    functionName: str
    lineNumber: int
    url: str


class StackTrace(TypedDict):
    """JavaScript stack trace."""

    callFrames: list[StackFrame]


class Source(TypedDict):
    """Script source realm with optional context."""

    realm: Realm
    context: NotRequired[BrowsingContext]
    userContext: NotRequired[UserContext]


class RealmTarget(TypedDict):
    """Target specified by realm id."""

    realm: Realm


class ContextTarget(TypedDict):
    """Target specified by browsing context."""

    context: BrowsingContext
    sandbox: NotRequired[str]


Target = ContextTarget | RealmTarget


class SharedReference(TypedDict):
    """Reference to a DOM node by shared id."""

    sharedId: SharedId
    handle: NotRequired[Handle]


class RemoteObjectReference(TypedDict):
    """Reference to an ECMAScript object by handle."""

    handle: Handle
    sharedId: NotRequired[SharedId]


RemoteReference = SharedReference | RemoteObjectReference


class ChannelProperties(TypedDict):
    """Properties for a messaging channel."""

    channel: Channel
    serializationOptions: NotRequired[SerializationOptions]
    ownership: NotRequired[ResultOwnership]


class ChannelValue(TypedDict):
    """A channel argument value."""

    type: str  # "channel"
    value: ChannelProperties


class RegExpValue(TypedDict):
    """Regular expression pattern and flags."""

    pattern: str
    flags: NotRequired[str]


class NodeProperties(TypedDict):
    """Serialized properties of a DOM node."""

    nodeType: int
    childNodeCount: int
    attributes: NotRequired[dict[str, str]]
    children: NotRequired[list['NodeRemoteValue']]
    localName: NotRequired[str]
    mode: NotRequired[str]  # "open" / "closed"
    namespaceURI: NotRequired[str]
    nodeValue: NotRequired[str]
    shadowRoot: NotRequired['NodeRemoteValue | None']


class WindowProxyProperties(TypedDict):
    """Properties of a WindowProxy remote value."""

    context: BrowsingContext


class NodeRemoteValue(TypedDict):
    """Remote value representing a DOM node."""

    type: str  # "node"
    sharedId: NotRequired[SharedId]
    handle: NotRequired[Handle]
    internalId: NotRequired[InternalId]
    value: NotRequired[NodeProperties]


class WindowProxyRemoteValue(TypedDict):
    """Remote value representing a WindowProxy."""

    type: str  # "window"
    value: WindowProxyProperties
    handle: NotRequired[Handle]
    internalId: NotRequired[InternalId]


class RemoteValue(TypedDict, total=False):
    """Serialized ECMAScript value received from the remote end.

    The `type` field determines which variant this is (e.g. "string",
    "number", "array", "node", "function", etc). Fields present depend
    on the variant.
    """

    type: str
    value: object
    handle: Handle
    internalId: InternalId
    sharedId: SharedId


class ExceptionDetails(TypedDict):
    """Details of a JavaScript exception."""

    columnNumber: int
    exception: RemoteValue
    lineNumber: int
    stackTrace: StackTrace
    text: str


class EvaluateResultSuccess(TypedDict):
    """Successful script evaluation result."""

    type: str  # "success"
    result: RemoteValue
    realm: Realm


class EvaluateResultException(TypedDict):
    """Exception script evaluation result."""

    type: str  # "exception"
    exceptionDetails: ExceptionDetails
    realm: Realm


EvaluateResult = EvaluateResultSuccess | EvaluateResultException


class WindowRealmInfo(TypedDict):
    """Realm info for a window context."""

    realm: Realm
    origin: str
    type: str  # "window"
    context: BrowsingContext
    userContext: NotRequired[UserContext]
    sandbox: NotRequired[str]


class DedicatedWorkerRealmInfo(TypedDict):
    """Realm info for a dedicated worker."""

    realm: Realm
    origin: str
    type: str  # "dedicated-worker"
    owners: list[Realm]


class SharedWorkerRealmInfo(TypedDict):
    """Realm info for a shared worker."""

    realm: Realm
    origin: str
    type: str  # "shared-worker"


class ServiceWorkerRealmInfo(TypedDict):
    """Realm info for a service worker."""

    realm: Realm
    origin: str
    type: str  # "service-worker"


class WorkerRealmInfo(TypedDict):
    """Realm info for a generic worker."""

    realm: Realm
    origin: str
    type: str  # "worker"


class WorkletRealmInfo(TypedDict):
    """Realm info for a generic worklet."""

    realm: Realm
    origin: str
    type: str  # "worklet"


RealmInfo = (
    WindowRealmInfo
    | DedicatedWorkerRealmInfo
    | SharedWorkerRealmInfo
    | ServiceWorkerRealmInfo
    | WorkerRealmInfo
    | WorkletRealmInfo
)


LocalValue = dict
"""Value that can be deserialized into ECMAScript.

Represented as a dict since the structure varies significantly by type
(primitives, arrays, objects, maps, sets, regexp, date, channel, remote refs).
"""
