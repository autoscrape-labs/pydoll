from __future__ import annotations

from typing import Optional

from pydoll.protocol.base import Command, Response
from typing_extensions import TypedDict, NotRequired


class ScriptTarget(TypedDict):
    context: str
    sandbox: NotRequired[str]


class EvaluateParams(TypedDict):
    expression: str
    target: ScriptTarget
    awaitPromise: bool
    resultOwnership: NotRequired[str]


class CallFunctionParams(TypedDict):
    functionDeclaration: str
    target: ScriptTarget
    arguments: NotRequired[list[dict]]
    awaitPromise: NotRequired[bool]
    resultOwnership: NotRequired[str]


class ScriptResult(TypedDict):
    type: str
    value: NotRequired[object]
    realm: NotRequired[str]


class EvaluateResult(TypedDict):
    result: ScriptResult
    realm: str


EvaluateResponse = Response[EvaluateResult]
CallFunctionResponse = Response[EvaluateResult]

EvaluateCommand = Command[EvaluateParams, EvaluateResponse]
CallFunctionCommand = Command[CallFunctionParams, CallFunctionResponse]


def evaluate(
    expression: str, context: str, await_promise: bool = True
) -> EvaluateCommand:
    return Command(
        method='script.evaluate',
        params=EvaluateParams(
            expression=expression,
            target=ScriptTarget(context=context),
            awaitPromise=await_promise,
            resultOwnership='root',
        ),
    )


def call_function(
    function_declaration: str,
    context: str,
    args: Optional[list[dict]] = None,
    await_promise: bool = True,
) -> CallFunctionCommand:
    params = CallFunctionParams(
        functionDeclaration=function_declaration,
        target=ScriptTarget(context=context),
        awaitPromise=await_promise,
        resultOwnership='root',
    )
    if args is not None:
        params['arguments'] = args
    return Command(method='script.callFunction', params=params)


class AddPreloadScriptParams(TypedDict):
    functionDeclaration: str
    contexts: NotRequired[Optional[list[str]]]


class AddPreloadScriptResult(TypedDict):
    script: str


AddPreloadScriptResponse = Response[AddPreloadScriptResult]
AddPreloadScriptCommand = Command[AddPreloadScriptParams, AddPreloadScriptResponse]


def add_preload_script(
    function_declaration: str,
    contexts: Optional[list[str]] = None,
) -> AddPreloadScriptCommand:
    params = AddPreloadScriptParams(functionDeclaration=function_declaration)
    if contexts is not None:
        params['contexts'] = contexts
    return Command(method='script.addPreloadScript', params=params)
