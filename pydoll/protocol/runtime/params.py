
try:
    from typing import NotRequired
except ImportError:
    from typing_extensions import NotRequired

from pydoll.protocol.base import CommandParams
from pydoll.protocol.runtime.types import CallArgument, SerializationOptions


class AddBindingParams(CommandParams):
    name: str
    executionContextName: NotRequired[str]


class AwaitPromiseParams(CommandParams):
    promiseObjectId: str
    returnByValue: NotRequired[bool]
    generatePreview: NotRequired[bool]


class CallFunctionOnParams(CommandParams):
    functionDeclaration: str
    objectId: NotRequired[str]
    arguments: NotRequired[list[CallArgument]]
    silent: NotRequired[bool]
    returnByValue: NotRequired[bool]
    generatePreview: NotRequired[bool]
    userGesture: NotRequired[bool]
    awaitPromise: NotRequired[bool]
    executionContextId: NotRequired[str]
    objectGroup: NotRequired[str]
    throwOnSideEffect: NotRequired[bool]
    uniqueContextId: NotRequired[str]
    serializationOptions: NotRequired[SerializationOptions]


class CompileScriptParams(CommandParams):
    expression: str
    sourceURL: NotRequired[str]
    persistScript: NotRequired[bool]
    executionContextId: NotRequired[str]


class EvaluateParams(CommandParams):
    expression: str
    objectGroup: NotRequired[str]
    includeCommandLineAPI: NotRequired[bool]
    silent: NotRequired[bool]
    contextId: NotRequired[str]
    returnByValue: NotRequired[bool]
    generatePreview: NotRequired[bool]
    userGesture: NotRequired[bool]
    awaitPromise: NotRequired[bool]
    throwOnSideEffect: NotRequired[bool]
    timeout: NotRequired[float]
    disableBreaks: NotRequired[bool]
    replMode: NotRequired[bool]
    allowUnsafeEvalBlockedByCSP: NotRequired[bool]
    uniqueContextId: NotRequired[str]
    serializationOptions: NotRequired[SerializationOptions]


class GetPropertiesParams(CommandParams):
    objectId: str
    ownProperties: NotRequired[bool]
    accessorPropertiesOnly: NotRequired[bool]
    generatePreview: NotRequired[bool]
    nonIndexedPropertiesOnly: NotRequired[bool]


class GlobalLexicalScopeNamesParams(CommandParams):
    executionContextId: NotRequired[str]


class QueryObjectsParams(CommandParams):
    prototypeObjectId: str
    objectGroup: NotRequired[str]


class ReleaseObjectParams(CommandParams):
    objectId: str


class ReleaseObjectGroupParams(CommandParams):
    objectGroup: str


class RemoveBindingParams(CommandParams):
    name: str


class RunScriptParams(CommandParams):
    scriptId: str
    executionContextId: NotRequired[str]
    objectGroup: NotRequired[str]
    silent: NotRequired[bool]
    includeCommandLineAPI: NotRequired[bool]
    returnByValue: NotRequired[bool]
    generatePreview: NotRequired[bool]
    awaitPromise: NotRequired[bool]


class SetAsyncCallStackDepthParams(CommandParams):
    maxDepth: int


class GetExceptionDetailsParams(CommandParams):
    errorObjectId: str


class SetCustomObjectFormatterEnabledParams(CommandParams):
    enabled: bool


class SetMaxCallStackSizeToCaptureParams(CommandParams):
    size: int
