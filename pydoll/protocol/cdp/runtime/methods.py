from enum import Enum

from typing_extensions import NotRequired, TypedDict

from pydoll.protocol.cdp.base import Command, EmptyParams, EmptyResponse, Response
from pydoll.protocol.cdp.runtime.types import (
    CallArgument,
    ExceptionDetails,
    ExecutionContextId,
    InternalPropertyDescriptor,
    PrivatePropertyDescriptor,
    PropertyDescriptor,
    RemoteObject,
    RemoteObjectId,
    ScriptId,
    SerializationOptions,
    TimeDelta,
)


class RuntimeMethod(str, Enum):
    """Runtime domain method names."""

    ADD_BINDING = 'Runtime.addBinding'
    AWAIT_PROMISE = 'Runtime.awaitPromise'
    CALL_FUNCTION_ON = 'Runtime.callFunctionOn'
    COMPILE_SCRIPT = 'Runtime.compileScript'
    DISABLE = 'Runtime.disable'
    DISCARD_CONSOLE_ENTRIES = 'Runtime.discardConsoleEntries'
    ENABLE = 'Runtime.enable'
    EVALUATE = 'Runtime.evaluate'
    GET_EXCEPTION_DETAILS = 'Runtime.getExceptionDetails'
    GET_HEAP_USAGE = 'Runtime.getHeapUsage'
    GET_ISOLATE_ID = 'Runtime.getIsolateId'
    GET_PROPERTIES = 'Runtime.getProperties'
    GLOBAL_LEXICAL_SCOPE_NAMES = 'Runtime.globalLexicalScopeNames'
    QUERY_OBJECTS = 'Runtime.queryObjects'
    RELEASE_OBJECT = 'Runtime.releaseObject'
    RELEASE_OBJECT_GROUP = 'Runtime.releaseObjectGroup'
    REMOVE_BINDING = 'Runtime.removeBinding'
    RUN_IF_WAITING_FOR_DEBUGGER = 'Runtime.runIfWaitingForDebugger'
    RUN_SCRIPT = 'Runtime.runScript'
    SET_ASYNC_CALL_STACK_DEPTH = 'Runtime.setAsyncCallStackDepth'
    SET_CUSTOM_OBJECT_FORMATTER_ENABLED = 'Runtime.setCustomObjectFormatterEnabled'
    SET_MAX_CALL_STACK_SIZE_TO_CAPTURE = 'Runtime.setMaxCallStackSizeToCapture'
    TERMINATE_EXECUTION = 'Runtime.terminateExecution'


# Parameter types
class AddBindingParams(TypedDict):
    """Parameters for addBinding command."""

    name: str
    executionContextId: NotRequired[ExecutionContextId]
    executionContextName: NotRequired[str]


class AwaitPromiseParams(TypedDict):
    """Parameters for awaitPromise command."""

    promiseObjectId: RemoteObjectId
    returnByValue: NotRequired[bool]
    generatePreview: NotRequired[bool]


class CallFunctionOnParams(TypedDict):
    """Parameters for callFunctionOn command."""

    functionDeclaration: str
    objectId: NotRequired[RemoteObjectId]
    arguments: NotRequired[list[CallArgument]]
    silent: NotRequired[bool]
    returnByValue: NotRequired[bool]
    generatePreview: NotRequired[bool]
    userGesture: NotRequired[bool]
    awaitPromise: NotRequired[bool]
    executionContextId: NotRequired[ExecutionContextId]
    objectGroup: NotRequired[str]
    throwOnSideEffect: NotRequired[bool]
    uniqueContextId: NotRequired[str]
    serializationOptions: NotRequired[SerializationOptions]


class CompileScriptParams(TypedDict):
    """Parameters for compileScript command."""

    expression: str
    sourceURL: str
    persistScript: bool
    executionContextId: NotRequired[ExecutionContextId]


class EvaluateParams(TypedDict):
    """Parameters for evaluate command."""

    expression: str
    objectGroup: NotRequired[str]
    includeCommandLineAPI: NotRequired[bool]
    silent: NotRequired[bool]
    contextId: NotRequired[ExecutionContextId]
    returnByValue: NotRequired[bool]
    generatePreview: NotRequired[bool]
    userGesture: NotRequired[bool]
    awaitPromise: NotRequired[bool]
    throwOnSideEffect: NotRequired[bool]
    timeout: NotRequired[TimeDelta]
    disableBreaks: NotRequired[bool]
    replMode: NotRequired[bool]
    allowUnsafeEvalBlockedByCSP: NotRequired[bool]
    uniqueContextId: NotRequired[str]
    serializationOptions: NotRequired[SerializationOptions]


class GetExceptionDetailsParams(TypedDict):
    """Parameters for getExceptionDetails command."""

    errorObjectId: RemoteObjectId


class GetPropertiesParams(TypedDict):
    """Parameters for getProperties command."""

    objectId: RemoteObjectId
    ownProperties: NotRequired[bool]
    accessorPropertiesOnly: NotRequired[bool]
    generatePreview: NotRequired[bool]
    nonIndexedPropertiesOnly: NotRequired[bool]


class GlobalLexicalScopeNamesParams(TypedDict, total=False):
    """Parameters for globalLexicalScopeNames command."""

    executionContextId: ExecutionContextId


class QueryObjectsParams(TypedDict):
    """Parameters for queryObjects command."""

    prototypeObjectId: RemoteObjectId
    objectGroup: NotRequired[str]


class ReleaseObjectParams(TypedDict):
    """Parameters for releaseObject command."""

    objectId: RemoteObjectId


class ReleaseObjectGroupParams(TypedDict):
    """Parameters for releaseObjectGroup command."""

    objectGroup: str


class RemoveBindingParams(TypedDict):
    """Parameters for removeBinding command."""

    name: str


class RunScriptParams(TypedDict):
    """Parameters for runScript command."""

    scriptId: ScriptId
    executionContextId: NotRequired[ExecutionContextId]
    objectGroup: NotRequired[str]
    silent: NotRequired[bool]
    includeCommandLineAPI: NotRequired[bool]
    returnByValue: NotRequired[bool]
    generatePreview: NotRequired[bool]
    awaitPromise: NotRequired[bool]


class SetAsyncCallStackDepthParams(TypedDict):
    """Parameters for setAsyncCallStackDepth command."""

    maxDepth: int


class SetCustomObjectFormatterEnabledParams(TypedDict):
    """Parameters for setCustomObjectFormatterEnabled command."""

    enabled: bool


class SetMaxCallStackSizeToCaptureParams(TypedDict):
    """Parameters for setMaxCallStackSizeToCapture command."""

    size: int


# Result types
class AwaitPromiseResult(TypedDict):
    """Result for awaitPromise command."""

    result: RemoteObject
    exceptionDetails: NotRequired[ExceptionDetails]


class CallFunctionOnResult(TypedDict):
    """Result for callFunctionOn command."""

    result: RemoteObject
    exceptionDetails: NotRequired[ExceptionDetails]


class CompileScriptResult(TypedDict, total=False):
    """Result for compileScript command."""

    scriptId: ScriptId
    exceptionDetails: ExceptionDetails


class EvaluateResult(TypedDict):
    """Result for evaluate command."""

    result: RemoteObject
    exceptionDetails: NotRequired[ExceptionDetails]


class GetExceptionDetailsResult(TypedDict, total=False):
    """Result for getExceptionDetails command."""

    exceptionDetails: ExceptionDetails


class GetHeapUsageResult(TypedDict):
    """Result for getHeapUsage command."""

    usedSize: float
    totalSize: float
    embedderHeapUsedSize: float
    backingStorageSize: float


class GetIsolateIdResult(TypedDict):
    """Result for getIsolateId command."""

    id: str


class GetPropertiesResult(TypedDict):
    """Result for getProperties command."""

    result: list[PropertyDescriptor]
    internalProperties: NotRequired[list[InternalPropertyDescriptor]]
    privateProperties: NotRequired[list[PrivatePropertyDescriptor]]
    exceptionDetails: NotRequired[ExceptionDetails]


class GlobalLexicalScopeNamesResult(TypedDict):
    """Result for globalLexicalScopeNames command."""

    names: list[str]


class QueryObjectsResult(TypedDict):
    """Result for queryObjects command."""

    objects: RemoteObject


class RunScriptResult(TypedDict):
    """Result for runScript command."""

    result: RemoteObject
    exceptionDetails: NotRequired[ExceptionDetails]


# Response types
AwaitPromiseResponse = Response[AwaitPromiseResult]
CallFunctionOnResponse = Response[CallFunctionOnResult]
CompileScriptResponse = Response[CompileScriptResult]
EvaluateResponse = Response[EvaluateResult]
GetExceptionDetailsResponse = Response[GetExceptionDetailsResult]
GetHeapUsageResponse = Response[GetHeapUsageResult]
GetIsolateIdResponse = Response[GetIsolateIdResult]
GetPropertiesResponse = Response[GetPropertiesResult]
GlobalLexicalScopeNamesResponse = Response[GlobalLexicalScopeNamesResult]
QueryObjectsResponse = Response[QueryObjectsResult]
RunScriptResponse = Response[RunScriptResult]


# Command types
AddBindingCommand = Command[AddBindingParams, Response[EmptyResponse]]
AwaitPromiseCommand = Command[AwaitPromiseParams, AwaitPromiseResponse]
CallFunctionOnCommand = Command[CallFunctionOnParams, CallFunctionOnResponse]
CompileScriptCommand = Command[CompileScriptParams, CompileScriptResponse]
DisableCommand = Command[EmptyParams, Response[EmptyResponse]]
DiscardConsoleEntriesCommand = Command[EmptyParams, Response[EmptyResponse]]
EnableCommand = Command[EmptyParams, Response[EmptyResponse]]
EvaluateCommand = Command[EvaluateParams, EvaluateResponse]
GetExceptionDetailsCommand = Command[GetExceptionDetailsParams, GetExceptionDetailsResponse]
GetHeapUsageCommand = Command[EmptyParams, GetHeapUsageResponse]
GetIsolateIdCommand = Command[EmptyParams, GetIsolateIdResponse]
GetPropertiesCommand = Command[GetPropertiesParams, GetPropertiesResponse]
GlobalLexicalScopeNamesCommand = Command[
    GlobalLexicalScopeNamesParams, GlobalLexicalScopeNamesResponse
]
QueryObjectsCommand = Command[QueryObjectsParams, QueryObjectsResponse]
ReleaseObjectCommand = Command[ReleaseObjectParams, Response[EmptyResponse]]
ReleaseObjectGroupCommand = Command[ReleaseObjectGroupParams, Response[EmptyResponse]]
RemoveBindingCommand = Command[RemoveBindingParams, Response[EmptyResponse]]
RunIfWaitingForDebuggerCommand = Command[EmptyParams, Response[EmptyResponse]]
RunScriptCommand = Command[RunScriptParams, RunScriptResponse]
SetAsyncCallStackDepthCommand = Command[SetAsyncCallStackDepthParams, Response[EmptyResponse]]
SetCustomObjectFormatterEnabledCommand = Command[
    SetCustomObjectFormatterEnabledParams, Response[EmptyResponse]
]
SetMaxCallStackSizeToCaptureCommand = Command[
    SetMaxCallStackSizeToCaptureParams, Response[EmptyResponse]
]
TerminateExecutionCommand = Command[EmptyParams, Response[EmptyResponse]]
