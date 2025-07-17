from typing import Any, Union

try:
    from typing import NotRequired, TypedDict
except ImportError:
    from typing_extensions import NotRequired, TypedDict

from pydoll.constants import (
    DeepSerializedValueType,
    ObjectPreviewSubtype,
    ObjectPreviewType,
    PropertyPreviewSubtype,
    PropertyPreviewType,
    RemoteObjectSubtype,
    RemoteObjectType,
    SerializationValue,
    UnserializableEnum,
)


class PropertyPreview(TypedDict):
    name: str
    type: PropertyPreviewType
    value: NotRequired[str]
    valuePreview: NotRequired['ObjectPreview']
    subtype: NotRequired[PropertyPreviewSubtype]


class EntryPreview(TypedDict):
    key: 'ObjectPreview'
    value: 'ObjectPreview'


class DeepSerializedValue(TypedDict):
    type: DeepSerializedValueType
    value: NotRequired[Any]
    objectId: NotRequired[str]
    weakLocalObjectReference: NotRequired[int]


class ObjectPreview(TypedDict):
    type: ObjectPreviewType
    subtype: NotRequired[ObjectPreviewSubtype]
    description: NotRequired[str]
    overflow: bool
    properties: list[PropertyPreview]
    entries: NotRequired[list[EntryPreview]]


class CustomPreview(TypedDict):
    header: str
    bodyGetterId: NotRequired[str]


class RemoteObject(TypedDict):
    type: RemoteObjectType
    subtype: NotRequired[RemoteObjectSubtype]
    className: NotRequired[str]
    value: NotRequired[Any]
    unserializableValue: NotRequired[Union[UnserializableEnum, str]]
    description: NotRequired[str]
    deepSerializedValue: NotRequired[DeepSerializedValue]
    objectId: NotRequired[str]
    preview: NotRequired[ObjectPreview]
    customPreview: NotRequired[CustomPreview]


class CallFrame(TypedDict):
    functionName: str
    scriptId: str
    url: str
    lineNumber: int
    columnNumber: int


class StackTraceId(TypedDict):
    id: str
    debuggerId: str


class StackTrace(TypedDict):
    description: NotRequired[str]
    callFrames: list[CallFrame]
    parent: NotRequired['StackTrace']
    parentId: NotRequired[StackTraceId]


class ExceptionDetails(TypedDict):
    exceptionId: int
    text: str
    lineNumber: int
    columnNumber: int
    scriptId: NotRequired[str]
    url: NotRequired[str]
    stackTrace: NotRequired[StackTrace]
    exception: NotRequired[RemoteObject]
    executionContextId: NotRequired[int]
    exceptionMetaData: NotRequired[dict]


class PropertyDescriptor(TypedDict):
    name: str
    value: NotRequired[RemoteObject]
    writable: bool
    get: NotRequired[RemoteObject]
    set: NotRequired[RemoteObject]
    configurable: bool
    enumerable: bool
    wasThrown: NotRequired[bool]
    isOwn: NotRequired[bool]
    symbol: NotRequired[RemoteObject]


class InternalPropertyDescriptor(TypedDict):
    name: str
    value: NotRequired[RemoteObject]


class PrivatePropertyDescriptor(TypedDict):
    name: str
    value: NotRequired[RemoteObject]
    get: NotRequired[RemoteObject]
    set: NotRequired[RemoteObject]


class CallArgument(TypedDict):
    value: NotRequired[str]
    unserializableValue: NotRequired[Union[UnserializableEnum, str]]
    objectId: NotRequired[str]


class SerializationOptions(TypedDict):
    serialization: SerializationValue
    maxDepth: NotRequired[int]
    additionalParameters: NotRequired[dict]
