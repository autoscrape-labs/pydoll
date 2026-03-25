from enum import Enum

from typing_extensions import NotRequired, TypedDict

from pydoll.protocol.bidi.base import Command, CommandResponse, EmptyResult
from pydoll.protocol.bidi.browser.types import UserContext
from pydoll.protocol.bidi.browsing_context.types import BrowsingContext
from pydoll.protocol.bidi.script.types import (
    ChannelValue,
    EvaluateResult,
    Handle,
    LocalValue,
    PreloadScript,
    RealmInfo,
    RealmType,
    ResultOwnership,
    SerializationOptions,
    Target,
)


class ScriptMethod(str, Enum):
    """Script module method names."""

    ADD_PRELOAD_SCRIPT = 'script.addPreloadScript'
    DISOWN = 'script.disown'
    CALL_FUNCTION = 'script.callFunction'
    EVALUATE = 'script.evaluate'
    GET_REALMS = 'script.getRealms'
    REMOVE_PRELOAD_SCRIPT = 'script.removePreloadScript'


class AddPreloadScriptParameters(TypedDict):
    """Parameters for script.addPreloadScript command."""

    functionDeclaration: str
    arguments: NotRequired[list[ChannelValue]]
    contexts: NotRequired[list[BrowsingContext]]
    userContexts: NotRequired[list[UserContext]]
    sandbox: NotRequired[str]


class AddPreloadScriptResult(TypedDict):
    """Result for script.addPreloadScript command."""

    script: PreloadScript


class DisownParameters(TypedDict):
    """Parameters for script.disown command."""

    handles: list[Handle]
    target: Target


class CallFunctionParameters(TypedDict):
    """Parameters for script.callFunction command."""

    functionDeclaration: str
    awaitPromise: bool
    target: Target
    arguments: NotRequired[list[LocalValue]]
    resultOwnership: NotRequired[ResultOwnership]
    serializationOptions: NotRequired[SerializationOptions]
    this: NotRequired[LocalValue]
    userActivation: NotRequired[bool]  # default false


class EvaluateParameters(TypedDict):
    """Parameters for script.evaluate command."""

    expression: str
    target: Target
    awaitPromise: bool
    resultOwnership: NotRequired[ResultOwnership]
    serializationOptions: NotRequired[SerializationOptions]
    userActivation: NotRequired[bool]  # default false


class GetRealmsParameters(TypedDict, total=False):
    """Parameters for script.getRealms command."""

    context: BrowsingContext
    type: RealmType


class GetRealmsResult(TypedDict):
    """Result for script.getRealms command."""

    realms: list[RealmInfo]


class RemovePreloadScriptParameters(TypedDict):
    """Parameters for script.removePreloadScript command."""

    script: PreloadScript


AddPreloadScriptCommand = Command[AddPreloadScriptParameters, AddPreloadScriptResult]
AddPreloadScriptResponse = CommandResponse[AddPreloadScriptResult]

DisownCommand = Command[DisownParameters, EmptyResult]
DisownResponse = CommandResponse[EmptyResult]

CallFunctionCommand = Command[CallFunctionParameters, EvaluateResult]
CallFunctionResponse = CommandResponse[EvaluateResult]

EvaluateCommand = Command[EvaluateParameters, EvaluateResult]
EvaluateResponse = CommandResponse[EvaluateResult]

GetRealmsCommand = Command[GetRealmsParameters, GetRealmsResult]
GetRealmsResponse = CommandResponse[GetRealmsResult]

RemovePreloadScriptCommand = Command[RemovePreloadScriptParameters, EmptyResult]
RemovePreloadScriptResponse = CommandResponse[EmptyResult]
