"""
Pydoll Exception Classes

This module contains all exception classes used throughout the Pydoll library,
organized into logical categories based on their function and usage patterns.
Each category uses a base class to provide common functionality for related exceptions.
"""


class PydollException(Exception):
    """Base class for all Pydoll exceptions."""

    message = 'An error occurred in Pydoll'

    def __init__(self, message: str = ''):
        self.message = message or self.message

    def __str__(self):
        return self.message


class ConnectionException(PydollException):
    """Base class for exceptions related to browser connection."""

    message = 'A connection error occurred'


class ConnectionFailed(ConnectionException):
    """Raised when connection to the browser cannot be established."""

    message = 'Failed to connect to the browser'


class ReconnectionFailed(ConnectionException):
    """Raised when an attempt to reconnect to the browser fails."""

    message = 'Failed to reconnect to the browser'


class WebSocketConnectionClosed(ConnectionException):
    """Raised when the WebSocket connection to the browser is closed unexpectedly."""

    message = 'The WebSocket connection is closed'


class NetworkError(ConnectionException):
    """Raised when a general network error occurs during browser communication."""

    message = 'A network error occurred'


class BrowserException(PydollException):
    """Base class for exceptions related to browser process management."""

    message = 'A browser error occurred'


class BrowserNotRunning(BrowserException):
    """Raised when attempting to interact with a browser that is not running."""

    message = 'The browser is not running'


class FailedToStartBrowser(BrowserException):
    """Raised when the browser process cannot be started."""

    message = 'Failed to start the browser'


class UnsupportedOS(BrowserException):
    """Raised when attempting to run on an unsupported operating system."""

    message = 'Unsupported OS'


class NoValidTabFound(BrowserException):
    """Raised when no valid browser tab can be found or created."""

    message = 'No valid attached tab found'


class ProtocolException(PydollException):
    """Base class for exceptions related to CDP protocol communication."""

    message = 'A protocol error occurred'


class InvalidCommand(ProtocolException):
    """Raised when an invalid command is sent to the browser."""

    message = 'The command provided is invalid'


class InvalidResponse(ProtocolException):
    """Raised when an invalid response is received from the browser."""

    message = 'The response received is invalid'


class ResendCommandFailed(ProtocolException):
    """Raised when an attempt to resend a failed command fails."""

    message = 'Failed to resend the command'


class CommandExecutionTimeout(ProtocolException):
    """Raised when a command execution times out."""

    message = 'The command execution timed out'


class InvalidCallback(ProtocolException):
    """Raised when an invalid callback is provided for an event."""

    message = 'The callback provided is invalid'


class EventNotSupported(ProtocolException):
    """Raised when an attempt is made to subscribe to an unsupported event."""

    message = 'The event is not supported'


class ElementException(PydollException):
    """Base class for exceptions related to element interactions."""

    message = 'An element interaction error occurred'


class ElementNotFound(ElementException):
    """Raised when an element cannot be found in the DOM."""

    message = 'The specified element was not found'


class ElementNotVisible(ElementException):
    """Raised when attempting to interact with an element that is not visible."""

    message = 'The element is not visible'


class ElementNotInteractable(ElementException):
    """Raised when attempting to interact with an element that cannot receive interaction."""

    message = 'The element is not interactable'


class ClickIntercepted(ElementException):
    """Raised when a click operation is intercepted by another element."""

    message = 'The click was intercepted'


class ElementNotAFileInput(ElementException):
    """Raised when attempting to use file input methods on a non-file input element."""

    message = 'The element is not a file input'


class TimeoutException(PydollException):
    """Base class for exceptions related to timeouts."""

    message = 'A timeout occurred'


class PageLoadTimeout(TimeoutException):
    """Raised when a page load operation times out."""

    message = 'Page load timed out'


class WaitElementTimeout(TimeoutException):
    """Raised when waiting for an element times out."""

    message = 'Timed out waiting for element to appear'


class ConfigurationException(PydollException):
    """Base class for exceptions related to configuration and options."""

    message = 'A configuration error occurred'


class InvalidOptionsObject(ConfigurationException):
    """Raised when an invalid options object is provided."""

    message = 'The options object provided is invalid'


class InvalidBrowserPath(ConfigurationException):
    """Raised when an invalid browser executable path is provided."""

    message = 'The browser path provided is invalid'


class ArgumentAlreadyExistsInOptions(ConfigurationException):
    """Raised when attempting to add a duplicate argument to browser options."""

    message = 'The argument already exists in the options'


class InvalidFileExtension(ConfigurationException):
    """Raised when an unsupported file extension is provided."""

    message = 'The file extension provided is not supported'


class DialogException(PydollException):
    """Base class for exceptions related to browser dialogs."""

    message = 'A dialog error occurred'


class NoDialogPresent(DialogException):
    """Raised when attempting to interact with a dialog that doesn't exist."""

    message = 'No dialog present on the page'


class NotAnIFrame(PydollException):
    """Raised when an element is not an iframe."""

    message = 'The element is not an iframe'


class InvalidIFrame(PydollException):
    """Raised when an iframe is not valid."""

    message = 'The iframe is not valid'


class IFrameNotFound(PydollException):
    """Raised when an iframe is not found."""

    message = 'The iframe was not found'


class NetworkEventsNotEnabled(PydollException):
    """Raised when network events are not enabled."""

    message = 'Network events not enabled'


class ScriptException(PydollException):
    """Base class for exceptions related to JavaScript execution."""

    message = 'A script execution error occurred'


class InvalidScriptWithElement(ScriptException):
    """Raised when a script contains 'argument' but no element is provided."""

    message = 'Script contains "argument" but no element was provided'
