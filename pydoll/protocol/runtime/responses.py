from typing import List, NotRequired, TypedDict

from pydoll.protocol.runtime.types import (
    ExceptionDetails,
    InternalPropertyDescriptor,
    PrivatePropertyDescriptor,
    PropertyDescriptor,
    RemoteObject,
)


class AwaitPromiseResultDict(TypedDict):
    result: RemoteObject
    exceptionDetails: NotRequired[ExceptionDetails]


class CallFunctionOnResultDict(TypedDict):
    result: RemoteObject
    exceptionDetails: NotRequired[ExceptionDetails]


class CompileScriptResultDict(TypedDict):
    scriptId: NotRequired[str]
    exceptionDetails: NotRequired[ExceptionDetails]


class EvaluateResultDict(TypedDict):
    result: RemoteObject
    exceptionDetails: NotRequired[ExceptionDetails]


class GetPropertiesResultDict(TypedDict):
    result: List[PropertyDescriptor]
    internalProperties: NotRequired[List[InternalPropertyDescriptor]]
    privateProperties: NotRequired[List[PrivatePropertyDescriptor]]
    exceptionDetails: NotRequired[ExceptionDetails]


class GlobalLexicalScopeNamesResultDict(TypedDict):
    names: List[str]


class QueryObjectsResultDict(TypedDict):
    objects: List[RemoteObject]


class RunScriptResultDict(TypedDict):
    result: RemoteObject
    exceptionDetails: NotRequired[ExceptionDetails]


class GetExceptionDetailsResultDict(TypedDict):
    exceptionDetails: ExceptionDetails


class GetHeapUsageResultDict(TypedDict):
    usedSize: float
    totalSize: float
    embedderHeapUsedSize: float
    backingStorageSize: float


class GetIsolateIdResultDict(TypedDict):
    id: str


class AwaitPromiseResponse(TypedDict):
    result: AwaitPromiseResultDict


class CallFunctionOnResponse(TypedDict):
    result: CallFunctionOnResultDict


class CompileScriptResponse(TypedDict):
    result: CompileScriptResultDict


class EvaluateResponse(TypedDict):
    result: EvaluateResultDict


class GetPropertiesResponse(TypedDict):
    result: GetPropertiesResultDict


class GlobalLexicalScopeNamesResponse(TypedDict):
    result: GlobalLexicalScopeNamesResultDict


class QueryObjectsResponse(TypedDict):
    result: QueryObjectsResultDict


class RunScriptResponse(TypedDict):
    result: RunScriptResultDict


class GetHeapUsageResponse(TypedDict):
    result: GetHeapUsageResultDict


class GetIsolateIdResponse(TypedDict):
    result: GetIsolateIdResultDict
