from enum import Enum
from typing import Any

from typing_extensions import NotRequired, TypedDict

ScriptId = str
RemoteObjectId = str
UnserializableValue = str
ExecutionContextId = int
Timestamp = float
TimeDelta = float
UniqueDebuggerId = str


class SerializationType(str, Enum):
    """Serialization types."""

    DEEP = 'deep'
    JSON = 'json'
    ID_ONLY = 'idOnly'


class DeepSerializedValueType(str, Enum):
    """Deep serialized value types."""

    UNDEFINED = 'undefined'
    NULL = 'null'
    STRING = 'string'
    NUMBER = 'number'
    BOOLEAN = 'boolean'
    BIGINT = 'bigint'
    REGEXP = 'regexp'
    DATE = 'date'
    SYMBOL = 'symbol'
    ARRAY = 'array'
    OBJECT = 'object'
    FUNCTION = 'function'
    MAP = 'map'
    SET = 'set'
    WEAKMAP = 'weakmap'
    WEAKSET = 'weakset'
    ERROR = 'error'
    PROXY = 'proxy'
    PROMISE = 'promise'
    TYPEDARRAY = 'typedarray'
    ARRAYBUFFER = 'arraybuffer'
    NODE = 'node'
    WINDOW = 'window'
    GENERATOR = 'generator'


class RemoteObjectType(str, Enum):
    """Remote object types."""

    OBJECT = 'object'
    FUNCTION = 'function'
    UNDEFINED = 'undefined'
    STRING = 'string'
    NUMBER = 'number'
    BOOLEAN = 'boolean'
    SYMBOL = 'symbol'
    BIGINT = 'bigint'


class RemoteObjectSubtype(str, Enum):
    """Remote object subtypes."""

    ARRAY = 'array'
    NULL = 'null'
    NODE = 'node'
    REGEXP = 'regexp'
    DATE = 'date'
    MAP = 'map'
    SET = 'set'
    WEAKMAP = 'weakmap'
    WEAKSET = 'weakset'
    ITERATOR = 'iterator'
    GENERATOR = 'generator'
    ERROR = 'error'
    PROXY = 'proxy'
    PROMISE = 'promise'
    TYPEDARRAY = 'typedarray'
    ARRAYBUFFER = 'arraybuffer'
    DATAVIEW = 'dataview'
    WEBASSEMBLYMEMORY = 'webassemblymemory'
    WASMVALUE = 'wasmvalue'


class ObjectPreviewType(str, Enum):
    """Object preview types."""

    OBJECT = 'object'
    FUNCTION = 'function'
    UNDEFINED = 'undefined'
    STRING = 'string'
    NUMBER = 'number'
    BOOLEAN = 'boolean'
    SYMBOL = 'symbol'
    BIGINT = 'bigint'


class ObjectPreviewSubtype(str, Enum):
    """Object preview subtypes."""

    ARRAY = 'array'
    NULL = 'null'
    NODE = 'node'
    REGEXP = 'regexp'
    DATE = 'date'
    MAP = 'map'
    SET = 'set'
    WEAKMAP = 'weakmap'
    WEAKSET = 'weakset'
    ITERATOR = 'iterator'
    GENERATOR = 'generator'
    ERROR = 'error'
    PROXY = 'proxy'
    PROMISE = 'promise'
    TYPEDARRAY = 'typedarray'
    ARRAYBUFFER = 'arraybuffer'
    DATAVIEW = 'dataview'
    WEBASSEMBLYMEMORY = 'webassemblymemory'
    WASMVALUE = 'wasmvalue'


class PropertyPreviewType(str, Enum):
    """Property preview types."""

    OBJECT = 'object'
    FUNCTION = 'function'
    UNDEFINED = 'undefined'
    STRING = 'string'
    NUMBER = 'number'
    BOOLEAN = 'boolean'
    SYMBOL = 'symbol'
    ACCESSOR = 'accessor'
    BIGINT = 'bigint'


class PropertyPreviewSubtype(str, Enum):
    """Property preview subtypes."""

    ARRAY = 'array'
    NULL = 'null'
    NODE = 'node'
    REGEXP = 'regexp'
    DATE = 'date'
    MAP = 'map'
    SET = 'set'
    WEAKMAP = 'weakmap'
    WEAKSET = 'weakset'
    ITERATOR = 'iterator'
    GENERATOR = 'generator'
    ERROR = 'error'
    PROXY = 'proxy'
    PROMISE = 'promise'
    TYPEDARRAY = 'typedarray'
    ARRAYBUFFER = 'arraybuffer'
    DATAVIEW = 'dataview'
    WEBASSEMBLYMEMORY = 'webassemblymemory'
    WASMVALUE = 'wasmvalue'


class SerializationOptions(TypedDict):
    """Represents options for serialization."""

    serialization: SerializationType
    maxDepth: NotRequired[int]
    additionalParameters: NotRequired[dict[str, Any]]


class DeepSerializedValue(TypedDict):
    """Represents deep serialized value."""

    type: DeepSerializedValueType
    value: NotRequired[Any]
    objectId: NotRequired[str]
    weakLocalObjectReference: NotRequired[int]


class CustomPreview(TypedDict):
    """Custom preview for objects."""

    header: str
    bodyGetterId: NotRequired[RemoteObjectId]


class PropertyPreview(TypedDict):
    """Property preview for objects."""

    name: str
    type: PropertyPreviewType
    value: NotRequired[str]
    valuePreview: NotRequired['ObjectPreview']
    subtype: NotRequired[PropertyPreviewSubtype]


class EntryPreview(TypedDict):
    """Entry preview for collections."""

    value: 'ObjectPreview'
    key: NotRequired['ObjectPreview']


class ObjectPreview(TypedDict):
    """Object containing abbreviated remote object value."""

    type: ObjectPreviewType
    overflow: bool
    properties: list[PropertyPreview]
    subtype: NotRequired[ObjectPreviewSubtype]
    description: NotRequired[str]
    entries: NotRequired[list[EntryPreview]]


class RemoteObject(TypedDict):
    """Mirror object referencing original JavaScript object."""

    type: RemoteObjectType
    subtype: NotRequired[RemoteObjectSubtype]
    className: NotRequired[str]
    value: NotRequired[Any]
    unserializableValue: NotRequired[UnserializableValue]
    description: NotRequired[str]
    deepSerializedValue: NotRequired[DeepSerializedValue]
    objectId: NotRequired[RemoteObjectId]
    preview: NotRequired[ObjectPreview]
    customPreview: NotRequired[CustomPreview]


class PropertyDescriptor(TypedDict):
    """Object property descriptor."""

    name: str
    configurable: bool
    enumerable: bool
    value: NotRequired[RemoteObject]
    writable: NotRequired[bool]
    get: NotRequired[RemoteObject]
    set: NotRequired[RemoteObject]
    wasThrown: NotRequired[bool]
    isOwn: NotRequired[bool]
    symbol: NotRequired[RemoteObject]


class InternalPropertyDescriptor(TypedDict):
    """Object internal property descriptor."""

    name: str
    value: NotRequired[RemoteObject]


class PrivatePropertyDescriptor(TypedDict):
    """Object private field descriptor."""

    name: str
    value: NotRequired[RemoteObject]
    get: NotRequired[RemoteObject]
    set: NotRequired[RemoteObject]


class CallArgument(TypedDict, total=False):
    """Represents function call argument."""

    value: Any
    unserializableValue: UnserializableValue
    objectId: RemoteObjectId


class ExecutionContextDescription(TypedDict):
    """Description of an isolated world."""

    id: ExecutionContextId
    origin: str
    name: str
    uniqueId: str
    auxData: NotRequired[dict[str, Any]]


class ExceptionDetails(TypedDict):
    """Detailed information about exception."""

    exceptionId: int
    text: str
    lineNumber: int
    columnNumber: int
    scriptId: NotRequired[ScriptId]
    url: NotRequired[str]
    stackTrace: NotRequired['StackTrace']
    exception: NotRequired[RemoteObject]
    executionContextId: NotRequired[ExecutionContextId]
    exceptionMetaData: NotRequired[dict[str, Any]]


class CallFrame(TypedDict):
    """Stack entry for runtime errors and assertions."""

    functionName: str
    scriptId: ScriptId
    url: str
    lineNumber: int
    columnNumber: int


class StackTraceId(TypedDict):
    """Stack trace identifier."""

    id: str
    debuggerId: NotRequired[UniqueDebuggerId]


class StackTrace(TypedDict):
    """Call frames for assertions or error messages."""

    callFrames: list[CallFrame]
    description: NotRequired[str]
    parent: NotRequired['StackTrace']
    parentId: NotRequired[StackTraceId]
