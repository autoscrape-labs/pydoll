from enum import Enum


class RuntimeEvent(str, Enum):
    """
    Events from the Runtime domain of the Chrome DevTools Protocol.

    This enumeration contains the names of Runtime-related events that can be
    received from the Chrome DevTools Protocol. These events provide information
    about JavaScript execution, console API calls, exceptions, and execution contexts.
    """

    CONSOLE_API_CALLED = 'Runtime.consoleAPICalled'
    """
    Issued when console API was called.

    Args:
        type (str): Type of the call.
            Allowed Values: log, debug, info, error, warning, dir, dirxml, table, trace,
            clear, startGroup, startGroupCollapsed, endGroup, assert, profile, profileEnd,
            count, timeEnd
        args (array[RemoteObject]): Call arguments.
        executionContextId (ExecutionContextId): Identifier of the context where the call was made.
        timestamp (Timestamp): Call timestamp.
        stackTrace (StackTrace): Stack trace captured when the call was made. The async stack
            chain is automatically reported for the following call types: assert, error,
            trace, warning. For other types the async call chain can be retrieved using
            Debugger.getStackTrace and stackTrace.parentId field.
        context (str): Console context descriptor for calls on non-default console context
            (not console.*): 'anonymous#unique-logger-id' for call on unnamed context,
            'name#unique-logger-id' for call on named context.
    """

    EXCEPTION_REVOKED = 'Runtime.exceptionRevoked'
    """
    Issued when unhandled exception was revoked.

    Args:
        reason (str): Reason describing why exception was revoked.
        exceptionId (int): The id of revoked exception, as reported in exceptionThrown.
    """

    EXCEPTION_THROWN = 'Runtime.exceptionThrown'
    """
    Issued when exception was thrown and unhandled.

    Args:
        timestamp (Timestamp): Timestamp of the exception.
        exceptionDetails (ExceptionDetails): Details about the exception.
    """

    EXECUTION_CONTEXT_CREATED = 'Runtime.executionContextCreated'
    """
    Issued when new execution context is created.

    Args:
        context (ExecutionContextDescription): A newly created execution context.
    """

    EXECUTION_CONTEXT_DESTROYED = 'Runtime.executionContextDestroyed'
    """
    Issued when execution context is destroyed.

    Args:
        executionContextId (ExecutionContextId): Id of the destroyed context.
        executionContextUniqueId (str): Unique Id of the destroyed context.
    """

    EXECUTION_CONTEXTS_CLEARED = 'Runtime.executionContextsCleared'
    """
    Issued when all executionContexts were cleared in browser.
    """

    INSPECT_REQUESTED = 'Runtime.inspectRequested'
    """
    Issued when object should be inspected
    (for example, as a result of inspect() command line API call).

    Args:
        object (RemoteObject): Object to inspect.
        hints (object): Hints.
        executionContextId (ExecutionContextId): Identifier of the context where the call was made.
    """

    BINDING_CALLED = 'Runtime.bindingCalled'
    """
    Notification is issued every time when binding is called.

    Args:
        name (str): Name of the binding.
        payload (str): Payload of the binding.
        executionContextId (ExecutionContextId): Identifier of the context where the call was made.
    """
