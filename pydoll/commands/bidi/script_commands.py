from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from pydoll.protocol.bidi.base import Command
from pydoll.protocol.bidi.script.methods import (
    AddPreloadScriptParameters,
    CallFunctionParameters,
    DisownParameters,
    EvaluateParameters,
    GetRealmsParameters,
    RemovePreloadScriptParameters,
    ScriptMethod,
)
from pydoll.protocol.bidi.script.types import (
    RealmType,
    ResultOwnership,
    SerializationOptions,
    Target,
)

if TYPE_CHECKING:
    from pydoll.protocol.bidi.script.methods import (
        AddPreloadScriptCommand,
        CallFunctionCommand,
        DisownCommand,
        EvaluateCommand,
        GetRealmsCommand,
        RemovePreloadScriptCommand,
    )
    from pydoll.protocol.bidi.script.types import ChannelValue, LocalValue


class ScriptCommands:
    """Command builders for the BiDi script module."""

    @staticmethod
    def add_preload_script(
        function_declaration: str,
        arguments: Optional[list[ChannelValue]] = None,
        contexts: Optional[list[str]] = None,
        user_contexts: Optional[list[str]] = None,
        sandbox: Optional[str] = None,
    ) -> AddPreloadScriptCommand:
        """Generates a command to add a preload script."""
        params = AddPreloadScriptParameters(
            functionDeclaration=function_declaration
        )
        if arguments is not None:
            params['arguments'] = arguments
        if contexts is not None:
            params['contexts'] = contexts
        if user_contexts is not None:
            params['userContexts'] = user_contexts
        if sandbox is not None:
            params['sandbox'] = sandbox
        return Command(method=ScriptMethod.ADD_PRELOAD_SCRIPT, params=params)

    @staticmethod
    def disown(handles: list[str], target: Target) -> DisownCommand:
        """Generates a command to disown script handles."""
        return Command(
            method=ScriptMethod.DISOWN,
            params=DisownParameters(handles=handles, target=target),
        )

    @staticmethod
    def call_function(
        function_declaration: str,
        await_promise: bool,
        target: Target,
        arguments: Optional[list[LocalValue]] = None,
        result_ownership: Optional[ResultOwnership] = None,
        serialization_options: Optional[SerializationOptions] = None,
        this: Optional[LocalValue] = None,
        user_activation: Optional[bool] = None,
    ) -> CallFunctionCommand:
        """Generates a command to call a function in a realm."""
        params = CallFunctionParameters(
            functionDeclaration=function_declaration,
            awaitPromise=await_promise,
            target=target,
        )
        if arguments is not None:
            params['arguments'] = arguments
        if result_ownership is not None:
            params['resultOwnership'] = result_ownership
        if serialization_options is not None:
            params['serializationOptions'] = serialization_options
        if this is not None:
            params['this'] = this
        if user_activation is not None:
            params['userActivation'] = user_activation
        return Command(method=ScriptMethod.CALL_FUNCTION, params=params)

    @staticmethod
    def evaluate(
        expression: str,
        target: Target,
        await_promise: bool,
        result_ownership: Optional[ResultOwnership] = None,
        serialization_options: Optional[SerializationOptions] = None,
        user_activation: Optional[bool] = None,
    ) -> EvaluateCommand:
        """Generates a command to evaluate an expression in a realm."""
        params = EvaluateParameters(
            expression=expression,
            target=target,
            awaitPromise=await_promise,
        )
        if result_ownership is not None:
            params['resultOwnership'] = result_ownership
        if serialization_options is not None:
            params['serializationOptions'] = serialization_options
        if user_activation is not None:
            params['userActivation'] = user_activation
        return Command(method=ScriptMethod.EVALUATE, params=params)

    @staticmethod
    def get_realms(
        context: Optional[str] = None,
        type: Optional[RealmType] = None,
    ) -> GetRealmsCommand:
        """Generates a command to get all realms."""
        params = GetRealmsParameters()
        if context is not None:
            params['context'] = context
        if type is not None:
            params['type'] = type
        return Command(method=ScriptMethod.GET_REALMS, params=params)

    @staticmethod
    def remove_preload_script(script: str) -> RemovePreloadScriptCommand:
        """Generates a command to remove a preload script."""
        return Command(
            method=ScriptMethod.REMOVE_PRELOAD_SCRIPT,
            params=RemovePreloadScriptParameters(script=script),
        )
