from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from pydoll.protocol.base import Command
from pydoll.protocol.runtime.methods import (
    AddBindingParams,
    AwaitPromiseParams,
    CallFunctionOnParams,
    CompileScriptParams,
    EvaluateParams,
    GetPropertiesParams,
    GlobalLexicalScopeNamesParams,
    QueryObjectsParams,
    ReleaseObjectGroupParams,
    ReleaseObjectParams,
    RemoveBindingParams,
    RunScriptParams,
    RuntimeMethod,
    SetAsyncCallStackDepthParams,
    SetCustomObjectFormatterEnabledParams,
    SetMaxCallStackSizeToCaptureParams,
)

if TYPE_CHECKING:
    from pydoll.protocol.runtime.methods import (
        AddBindingCommand,
        AwaitPromiseCommand,
        CallArgument,
        CallFunctionOnCommand,
        CompileScriptCommand,
        DisableCommand,
        EnableCommand,
        EvaluateCommand,
        GetPropertiesCommand,
        GlobalLexicalScopeNamesCommand,
        QueryObjectsCommand,
        ReleaseObjectCommand,
        ReleaseObjectGroupCommand,
        RemoveBindingCommand,
        RunScriptCommand,
        SerializationOptions,
        SetAsyncCallStackDepthCommand,
        SetCustomObjectFormatterEnabledCommand,
        SetMaxCallStackSizeToCaptureCommand,
    )


class RuntimeCommands:
    """
    A class for interacting with the JavaScript runtime using Chrome
    DevTools Protocol.

    This class provides methods to create commands for evaluating JavaScript
    expressions, calling functions on JavaScript objects, and retrieving
    object properties through CDP.

    Attributes:
        EVALUATE_TEMPLATE (dict): Template for the Runtime.evaluate command.
        CALL_FUNCTION_ON_TEMPLATE (dict): Template for the
            Runtime.callFunctionOn command.
        GET_PROPERTIES (dict): Template for the Runtime.getProperties command.
    """

    @staticmethod
    def add_binding(name: str, execution_context_name: Optional[str] = None) -> AddBindingCommand:
        """
        Creates a command to add a JavaScript binding.

        Args:
            name (str): Name of the binding to add.
            execution_context_name (Optional[str]): Name of the execution context to bind to.

        Returns:
            AddBindingCommand: Command object to add a JavaScript binding.
        """
        params = AddBindingParams(name=name)
        if execution_context_name is not None:
            params['executionContextName'] = execution_context_name

        return Command(method=RuntimeMethod.ADD_BINDING, params=params)

    @staticmethod
    def await_promise(
        promise_object_id: str,
        return_by_value: Optional[bool] = None,
        generate_preview: Optional[bool] = None,
    ) -> AwaitPromiseCommand:
        """
        Creates a command to await a JavaScript promise and return its result.

        Args:
            promise_object_id (str): ID of the promise to await.
            return_by_value (Optional[bool]): Whether to return the result by value instead
                of reference.
            generate_preview (Optional[bool]): Whether to generate a preview for the result.

        Returns:
            AwaitPromiseCommand: Command object to await a promise.
        """
        params = AwaitPromiseParams(promiseObjectId=promise_object_id)
        if return_by_value is not None:
            params['returnByValue'] = return_by_value
        if generate_preview is not None:
            params['generatePreview'] = generate_preview

        return Command(method=RuntimeMethod.AWAIT_PROMISE, params=params)

    @staticmethod
    def call_function_on(
        function_declaration: str,
        object_id: Optional[str] = None,
        arguments: Optional[list[CallArgument]] = None,
        silent: Optional[bool] = None,
        return_by_value: Optional[bool] = None,
        generate_preview: Optional[bool] = None,
        user_gesture: Optional[bool] = None,
        await_promise: Optional[bool] = None,
        execution_context_id: Optional[int] = None,
        object_group: Optional[str] = None,
        throw_on_side_effect: Optional[bool] = None,
        unique_context_id: Optional[str] = None,
        serialization_options: Optional[SerializationOptions] = None,
    ) -> CallFunctionOnCommand:
        """
        Creates a command to call a function with a given declaration on a specific object.

        Args:
            function_declaration (str): Declaration of the function to call.
            object_id (Optional[str]): ID of the object to call the function on.
            arguments (Optional[list[CallArgument]]): Arguments to pass to the function.
            silent (Optional[bool]): Whether to silence exceptions.
            return_by_value (Optional[bool]): Whether to return the result by value instead
                of reference.
            generate_preview (Optional[bool]): Whether to generate a preview for the result.
            user_gesture (Optional[bool]): Whether to treat the call as initiated by user gesture.
            await_promise (Optional[bool]): Whether to await promise result.
            execution_context_id (Optional[int]): ID of the execution context to call the
                function in.
            object_group (Optional[str]): Symbolic group name for the result.
            throw_on_side_effect (Optional[bool]): Whether to throw if side effect cannot be
                ruled out.
            unique_context_id (Optional[str]): Unique context ID for the function call.
            serialization_options (Optional[SerializationOptions]): Serialization options for
                the result.

        Returns:
            CallFunctionOnCommand: Command object to call a function on an object.
        """
        params = CallFunctionOnParams(functionDeclaration=function_declaration)
        if object_id is not None:
            params['objectId'] = object_id
        if arguments is not None:
            params['arguments'] = arguments
        if silent is not None:
            params['silent'] = silent
        if return_by_value is not None:
            params['returnByValue'] = return_by_value
        if generate_preview is not None:
            params['generatePreview'] = generate_preview
        if user_gesture is not None:
            params['userGesture'] = user_gesture
        if await_promise is not None:
            params['awaitPromise'] = await_promise
        if execution_context_id is not None:
            params['executionContextId'] = execution_context_id
        if object_group is not None:
            params['objectGroup'] = object_group
        if throw_on_side_effect is not None:
            params['throwOnSideEffect'] = throw_on_side_effect
        if unique_context_id is not None:
            params['uniqueContextId'] = unique_context_id
        if serialization_options is not None:
            params['serializationOptions'] = serialization_options

        return Command(method=RuntimeMethod.CALL_FUNCTION_ON, params=params)

    @staticmethod
    def compile_script(
        expression: str,
        source_url: str,
        persist_script: bool = False,
        execution_context_id: Optional[int] = None,
    ) -> CompileScriptCommand:
        """
        Creates a command to compile a JavaScript expression.

        Args:
            expression (str): JavaScript expression to compile.
            source_url (str): URL of the source file for the script.
            persist_script (bool): Whether to persist the compiled script.
            execution_context_id (Optional[int]): ID of the execution context to compile
                the script in.

        Returns:
            CompileScriptCommand: Command object to compile a script.
        """
        params = CompileScriptParams(
            expression=expression, sourceURL=source_url, persistScript=persist_script
        )
        if execution_context_id is not None:
            params['executionContextId'] = execution_context_id

        return Command(method=RuntimeMethod.COMPILE_SCRIPT, params=params)

    @staticmethod
    def disable() -> DisableCommand:
        """
        Disables the runtime domain.

        Returns:
            DisableCommand: Command object to disable the runtime domain.
        """
        return Command(method=RuntimeMethod.DISABLE)

    @staticmethod
    def enable() -> EnableCommand:
        """
        Enables the runtime domain.

        Returns:
            EnableCommand: Command object to enable the runtime domain.
        """
        return Command(method=RuntimeMethod.ENABLE)

    @staticmethod
    def evaluate(  # noqa: PLR0912
        expression: str,
        object_group: Optional[str] = None,
        include_command_line_api: Optional[bool] = None,
        silent: Optional[bool] = None,
        context_id: Optional[int] = None,
        return_by_value: Optional[bool] = None,
        generate_preview: Optional[bool] = None,
        user_gesture: Optional[bool] = None,
        await_promise: Optional[bool] = None,
        throw_on_side_effect: Optional[bool] = None,
        timeout: Optional[float] = None,
        disable_breaks: Optional[bool] = None,
        repl_mode: Optional[bool] = None,
        allow_unsafe_eval_blocked_by_csp: Optional[bool] = None,
        unique_context_id: Optional[str] = None,
        serialization_options: Optional[SerializationOptions] = None,
    ) -> EvaluateCommand:
        """
        Creates a command to evaluate a JavaScript expression in the global context.

        Args:
            expression (str): JavaScript expression to evaluate.
            object_group (Optional[str]): Symbolic group name for the result.
            include_command_line_api (Optional[bool]): Whether to include command line API.
            silent (Optional[bool]): Whether to silence exceptions.
            context_id (Optional[int]): ID of the execution context to evaluate in.
            return_by_value (Optional[bool]): Whether to return the result by value instead
                of reference.
            generate_preview (Optional[bool]): Whether to generate a preview for the result.
            user_gesture (Optional[bool]): Whether to treat evaluation as initiated by user gesture.
            await_promise (Optional[bool]): Whether to await promise result.
            throw_on_side_effect (Optional[bool]): Whether to throw if side effect cannot be
                ruled out.
            timeout (Optional[float]): Timeout in milliseconds.
            disable_breaks (Optional[bool]): Whether to disable breakpoints during evaluation.
            repl_mode (Optional[bool]): Whether to execute in REPL mode.
            allow_unsafe_eval_blocked_by_csp (Optional[bool]): Allow unsafe evaluation.
            unique_context_id (Optional[str]): Unique context ID for evaluation.
            serialization_options (Optional[SerializationOptions]): Serialization
                for the result.

        Returns:
            EvaluateCommand: Command object to evaluate JavaScript.
        """
        params = EvaluateParams(expression=expression)
        if object_group is not None:
            params['objectGroup'] = object_group
        if include_command_line_api is not None:
            params['includeCommandLineAPI'] = include_command_line_api
        if silent is not None:
            params['silent'] = silent
        if context_id is not None:
            params['contextId'] = context_id
        if return_by_value is not None:
            params['returnByValue'] = return_by_value
        if generate_preview is not None:
            params['generatePreview'] = generate_preview
        if user_gesture is not None:
            params['userGesture'] = user_gesture
        if await_promise is not None:
            params['awaitPromise'] = await_promise
        if throw_on_side_effect is not None:
            params['throwOnSideEffect'] = throw_on_side_effect
        if timeout is not None:
            params['timeout'] = timeout
        if disable_breaks is not None:
            params['disableBreaks'] = disable_breaks
        if repl_mode is not None:
            params['replMode'] = repl_mode
        if allow_unsafe_eval_blocked_by_csp is not None:
            params['allowUnsafeEvalBlockedByCSP'] = allow_unsafe_eval_blocked_by_csp
        if unique_context_id is not None:
            params['uniqueContextId'] = unique_context_id
        if serialization_options is not None:
            params['serializationOptions'] = serialization_options

        return Command(method=RuntimeMethod.EVALUATE, params=params)

    @staticmethod
    def get_properties(
        object_id: str,
        own_properties: Optional[bool] = None,
        accessor_properties_only: Optional[bool] = None,
        generate_preview: Optional[bool] = None,
        non_indexed_properties_only: Optional[bool] = None,
    ) -> GetPropertiesCommand:
        """
        Creates a command to get properties of a JavaScript object.

        Args:
            object_id (str): ID of the object to get properties for.
            own_properties (Optional[bool]): Whether to return only own properties.
            accessor_properties_only (Optional[bool]): Whether to return only accessor properties.
            generate_preview (Optional[bool]): Whether to generate previews for property values.
            non_indexed_properties_only (Optional[bool]): Whether to return only non-indexed
                properties.

        Returns:
            GetPropertiesCommand: Command object to get object properties.
        """
        params = GetPropertiesParams(objectId=object_id)
        if own_properties is not None:
            params['ownProperties'] = own_properties
        if accessor_properties_only is not None:
            params['accessorPropertiesOnly'] = accessor_properties_only
        if generate_preview is not None:
            params['generatePreview'] = generate_preview
        if non_indexed_properties_only is not None:
            params['nonIndexedPropertiesOnly'] = non_indexed_properties_only

        return Command(method=RuntimeMethod.GET_PROPERTIES, params=params)

    @staticmethod
    def global_lexical_scope_names(
        execution_context_id: Optional[int] = None,
    ) -> GlobalLexicalScopeNamesCommand:
        """
        Creates a command to retrieve names of variables from global lexical scope.

        Args:
            execution_context_id (Optional[int]): ID of the execution context to get scope
                names from.

        Returns:
            GlobalLexicalScopeNamesCommand: Command object to get global lexical
                scope names.
        """
        params = GlobalLexicalScopeNamesParams()
        if execution_context_id is not None:
            params['executionContextId'] = execution_context_id

        return Command(method=RuntimeMethod.GLOBAL_LEXICAL_SCOPE_NAMES, params=params)

    @staticmethod
    def query_objects(
        prototype_object_id: str,
        object_group: Optional[str] = None,
    ) -> QueryObjectsCommand:
        """
        Creates a command to query objects with a given prototype.

        Args:
            prototype_object_id (str): ID of the prototype object.
            object_group (Optional[str]): Symbolic group name for the results.

        Returns:
            QueryObjectsCommand: Command object to query objects.
        """
        params = QueryObjectsParams(prototypeObjectId=prototype_object_id)
        if object_group is not None:
            params['objectGroup'] = object_group

        return Command(method=RuntimeMethod.QUERY_OBJECTS, params=params)

    @staticmethod
    def release_object(
        object_id: str,
    ) -> ReleaseObjectCommand:
        """
        Creates a command to release a JavaScript object.

        Args:
            object_id (str): ID of the object to release.

        Returns:
            ReleaseObjectCommand: Command object to release an object.
        """
        params = ReleaseObjectParams(objectId=object_id)

        return Command(method=RuntimeMethod.RELEASE_OBJECT, params=params)

    @staticmethod
    def release_object_group(
        object_group: str,
    ) -> ReleaseObjectGroupCommand:
        """
        Creates a command to release all objects in a group.

        Args:
            object_group (str): Name of the object group to release.

        Returns:
            ReleaseObjectGroupCommand: Command object to release an object group.
        """
        params = ReleaseObjectGroupParams(objectGroup=object_group)
        return Command(method=RuntimeMethod.RELEASE_OBJECT_GROUP, params=params)

    @staticmethod
    def remove_binding(
        name: str,
    ) -> RemoveBindingCommand:
        """
        Creates a command to remove a JavaScript binding.

        Args:
            name (str): Name of the binding to remove.

        Returns:
            RemoveBindingCommand: Command object to remove a JavaScript binding.
        """
        params = RemoveBindingParams(name=name)
        return Command(method=RuntimeMethod.REMOVE_BINDING, params=params)

    @staticmethod
    def run_script(
        script_id: str,
        execution_context_id: Optional[int] = None,
        object_group: Optional[str] = None,
        silent: Optional[bool] = None,
        include_command_line_api: Optional[bool] = None,
        return_by_value: Optional[bool] = None,
        generate_preview: Optional[bool] = None,
        await_promise: Optional[bool] = None,
    ) -> RunScriptCommand:
        """
        Creates a command to run a compiled script.

        Args:
            script_id (str): ID of the compiled script to run.
            execution_context_id (Optional[int]): ID of the execution context to run the script in.
            object_group (Optional[str]): Symbolic group name for the result.
            silent (Optional[bool]): Whether to silence exceptions.
            include_command_line_api (Optional[bool]): Whether to include command line API.
            return_by_value (Optional[bool]): Whether to return the result by value instead
                of reference.
            generate_preview (Optional[bool]): Whether to generate a preview for the result.
            await_promise (Optional[bool]): Whether to await promise result.

        Returns:
            RunScriptCommand: Command object to run a script.
        """
        params = RunScriptParams(scriptId=script_id)
        if execution_context_id is not None:
            params['executionContextId'] = execution_context_id
        if object_group is not None:
            params['objectGroup'] = object_group
        if silent is not None:
            params['silent'] = silent
        if include_command_line_api is not None:
            params['includeCommandLineAPI'] = include_command_line_api
        if return_by_value is not None:
            params['returnByValue'] = return_by_value
        if generate_preview is not None:
            params['generatePreview'] = generate_preview
        if await_promise is not None:
            params['awaitPromise'] = await_promise

        return Command(method=RuntimeMethod.RUN_SCRIPT, params=params)

    @staticmethod
    def set_async_call_stack_depth(
        max_depth: int,
    ) -> SetAsyncCallStackDepthCommand:
        """
        Creates a command to set the async call stack depth.

        Args:
            max_depth (int): Maximum depth of async call stacks.

        Returns:
            SetAsyncCallStackDepthCommand: Command object to set async call stack depth.
        """
        params = SetAsyncCallStackDepthParams(maxDepth=max_depth)
        return Command(method=RuntimeMethod.SET_ASYNC_CALL_STACK_DEPTH, params=params)

    @staticmethod
    def set_custom_object_formatter_enabled(
        enabled: bool,
    ) -> SetCustomObjectFormatterEnabledCommand:
        """
        Creates a command to enable or disable custom object formatters.

        Args:
            enabled (bool): Whether to enable custom object formatters.

        Returns:
            SetCustomObjectFormatterEnabledCommand: Command object to enable/disable custom
                object formatters.
        """
        params = SetCustomObjectFormatterEnabledParams(enabled=enabled)
        return Command(method=RuntimeMethod.SET_CUSTOM_OBJECT_FORMATTER_ENABLED, params=params)

    @staticmethod
    def set_max_call_stack_size_to_capture(
        size: int,
    ) -> SetMaxCallStackSizeToCaptureCommand:
        """
        Creates a command to set the maximum call stack size to capture.

        Args:
            size (int): Maximum call stack size to capture.

        Returns:
            SetMaxCallStackSizeToCaptureCommand: Command object to set max call stack size.
        """
        params = SetMaxCallStackSizeToCaptureParams(size=size)
        return Command(method=RuntimeMethod.SET_MAX_CALL_STACK_SIZE_TO_CAPTURE, params=params)
