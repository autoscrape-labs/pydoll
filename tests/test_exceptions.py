import pytest
from pydoll.exceptions import (
    # Base exceptions
    PydollException,
    ConnectionException,
    BrowserException,
    ProtocolException,
    ElementException,
    TimeoutException,
    ConfigurationException,
    DialogException,
    
    # Connection exceptions
    ConnectionFailed,
    ReconnectionFailed,
    WebSocketConnectionClosed,
    NetworkError,
    
    # Browser exceptions
    BrowserNotRunning,
    FailedToStartBrowser,
    UnsupportedOS,
    NoValidTabFound,
    
    # Protocol exceptions
    InvalidCommand,
    InvalidResponse,
    ResendCommandFailed,
    CommandExecutionTimeout,
    InvalidCallback,
    EventNotSupported,
    
    # Element exceptions
    ElementNotFound,
    ElementNotVisible,
    ElementNotInteractable,
    ClickIntercepted,
    ElementNotAFileInput,
    
    # Timeout exceptions
    PageLoadTimeout,
    WaitElementTimeout,
    
    # Configuration exceptions
    InvalidOptionsObject,
    InvalidBrowserPath,
    ArgumentAlreadyExistsInOptions,
    InvalidFileExtension,
    
    # Dialog exceptions
    NoDialogPresent,
    
    # IFrame exceptions
    NotAnIFrame,
    InvalidIFrame,
    IFrameNotFound,
)


class TestBaseExceptions:
    """Test base exception classes."""

    def test_pydoll_exception_default_message(self):
        """Test PydollException with default message."""
        with pytest.raises(PydollException) as exc_info:
            raise PydollException()
        assert str(exc_info.value) == 'An error occurred in Pydoll'

    def test_pydoll_exception_custom_message(self):
        """Test PydollException with custom message."""
        custom_message = 'Custom error occurred'
        with pytest.raises(PydollException) as exc_info:
            raise PydollException(custom_message)
        assert str(exc_info.value) == custom_message

    def test_connection_exception_default(self):
        """Test ConnectionException with default message."""
        with pytest.raises(ConnectionException) as exc_info:
            raise ConnectionException()
        assert str(exc_info.value) == 'A connection error occurred'

    def test_connection_exception_custom(self):
        """Test ConnectionException with custom message."""
        custom_message = 'Custom connection error'
        with pytest.raises(ConnectionException) as exc_info:
            raise ConnectionException(custom_message)
        assert str(exc_info.value) == custom_message

    def test_browser_exception_default(self):
        """Test BrowserException with default message."""
        with pytest.raises(BrowserException) as exc_info:
            raise BrowserException()
        assert str(exc_info.value) == 'A browser error occurred'

    def test_protocol_exception_default(self):
        """Test ProtocolException with default message."""
        with pytest.raises(ProtocolException) as exc_info:
            raise ProtocolException()
        assert str(exc_info.value) == 'A protocol error occurred'

    def test_element_exception_default(self):
        """Test ElementException with default message."""
        with pytest.raises(ElementException) as exc_info:
            raise ElementException()
        assert str(exc_info.value) == 'An element interaction error occurred'

    def test_timeout_exception_default(self):
        """Test TimeoutException with default message."""
        with pytest.raises(TimeoutException) as exc_info:
            raise TimeoutException()
        assert str(exc_info.value) == 'A timeout occurred'

    def test_configuration_exception_default(self):
        """Test ConfigurationException with default message."""
        with pytest.raises(ConfigurationException) as exc_info:
            raise ConfigurationException()
        assert str(exc_info.value) == 'A configuration error occurred'

    def test_dialog_exception_default(self):
        """Test DialogException with default message."""
        with pytest.raises(DialogException) as exc_info:
            raise DialogException()
        assert str(exc_info.value) == 'A dialog error occurred'


class TestConnectionExceptions:
    """Test connection-related exceptions."""

    def test_connection_failed(self):
        """Test ConnectionFailed exception."""
        with pytest.raises(ConnectionFailed) as exc_info:
            raise ConnectionFailed()
        assert str(exc_info.value) == 'Failed to connect to the browser'

    def test_reconnection_failed(self):
        """Test ReconnectionFailed exception."""
        with pytest.raises(ReconnectionFailed) as exc_info:
            raise ReconnectionFailed()
        assert str(exc_info.value) == 'Failed to reconnect to the browser'

    def test_websocket_connection_closed(self):
        """Test WebSocketConnectionClosed exception."""
        with pytest.raises(WebSocketConnectionClosed) as exc_info:
            raise WebSocketConnectionClosed()
        assert str(exc_info.value) == 'The WebSocket connection is closed'

    def test_websocket_connection_closed_custom(self):
        """Test WebSocketConnectionClosed with custom message."""
        custom_message = 'Connection closed unexpectedly'
        with pytest.raises(WebSocketConnectionClosed) as exc_info:
            raise WebSocketConnectionClosed(custom_message)
        assert str(exc_info.value) == custom_message

    def test_network_error(self):
        """Test NetworkError exception."""
        with pytest.raises(NetworkError) as exc_info:
            raise NetworkError()
        assert str(exc_info.value) == 'A network error occurred'


class TestBrowserExceptions:
    """Test browser-related exceptions."""

    def test_browser_not_running(self):
        """Test BrowserNotRunning exception."""
        with pytest.raises(BrowserNotRunning) as exc_info:
            raise BrowserNotRunning()
        assert str(exc_info.value) == 'The browser is not running'

    def test_failed_to_start_browser(self):
        """Test FailedToStartBrowser exception."""
        with pytest.raises(FailedToStartBrowser) as exc_info:
            raise FailedToStartBrowser()
        assert str(exc_info.value) == 'Failed to start the browser'

    def test_failed_to_start_browser_custom(self):
        """Test FailedToStartBrowser with custom message."""
        custom_message = 'Browser executable not found'
        with pytest.raises(FailedToStartBrowser) as exc_info:
            raise FailedToStartBrowser(custom_message)
        assert str(exc_info.value) == custom_message

    def test_unsupported_os(self):
        """Test UnsupportedOS exception."""
        with pytest.raises(UnsupportedOS) as exc_info:
            raise UnsupportedOS()
        assert str(exc_info.value) == 'Unsupported OS'

    def test_unsupported_os_custom(self):
        """Test UnsupportedOS with custom message."""
        custom_message = 'This OS is not supported: FreeBSD'
        with pytest.raises(UnsupportedOS) as exc_info:
            raise UnsupportedOS(custom_message)
        assert str(exc_info.value) == custom_message

    def test_no_valid_tab_found(self):
        """Test NoValidTabFound exception."""
        with pytest.raises(NoValidTabFound) as exc_info:
            raise NoValidTabFound()
        assert str(exc_info.value) == 'No valid attached tab found'


class TestProtocolExceptions:
    """Test protocol-related exceptions."""

    def test_invalid_command(self):
        """Test InvalidCommand exception."""
        with pytest.raises(InvalidCommand) as exc_info:
            raise InvalidCommand()
        assert str(exc_info.value) == 'The command provided is invalid'

    def test_invalid_response(self):
        """Test InvalidResponse exception."""
        with pytest.raises(InvalidResponse) as exc_info:
            raise InvalidResponse()
        assert str(exc_info.value) == 'The response received is invalid'

    def test_resend_command_failed(self):
        """Test ResendCommandFailed exception."""
        with pytest.raises(ResendCommandFailed) as exc_info:
            raise ResendCommandFailed()
        assert str(exc_info.value) == 'Failed to resend the command'

    def test_command_execution_timeout(self):
        """Test CommandExecutionTimeout exception."""
        with pytest.raises(CommandExecutionTimeout) as exc_info:
            raise CommandExecutionTimeout()
        assert str(exc_info.value) == 'The command execution timed out'

    def test_command_execution_timeout_custom(self):
        """Test CommandExecutionTimeout with custom message."""
        custom_message = 'Command timed out after 30 seconds'
        with pytest.raises(CommandExecutionTimeout) as exc_info:
            raise CommandExecutionTimeout(custom_message)
        assert str(exc_info.value) == custom_message

    def test_invalid_callback(self):
        """Test InvalidCallback exception."""
        with pytest.raises(InvalidCallback) as exc_info:
            raise InvalidCallback()
        assert str(exc_info.value) == 'The callback provided is invalid'

    def test_event_not_supported(self):
        """Test EventNotSupported exception."""
        with pytest.raises(EventNotSupported) as exc_info:
            raise EventNotSupported('Custom error message')
        assert str(exc_info.value) == 'Custom error message'

        # Testing default message
        with pytest.raises(EventNotSupported) as exc_info:
            raise EventNotSupported()
        assert str(exc_info.value) == 'The event is not supported'


class TestElementExceptions:
    """Test element-related exceptions."""

    def test_element_not_found(self):
        """Test ElementNotFound exception."""
        with pytest.raises(ElementNotFound) as exc_info:
            raise ElementNotFound()
        assert str(exc_info.value) == 'The specified element was not found'

    def test_element_not_found_custom(self):
        """Test ElementNotFound with custom message."""
        custom_message = 'Button with ID "submit" not found'
        with pytest.raises(ElementNotFound) as exc_info:
            raise ElementNotFound(custom_message)
        assert str(exc_info.value) == custom_message

    def test_element_not_visible(self):
        """Test ElementNotVisible exception."""
        with pytest.raises(ElementNotVisible) as exc_info:
            raise ElementNotVisible()
        assert str(exc_info.value) == 'The element is not visible'

    def test_element_not_interactable(self):
        """Test ElementNotInteractable exception."""
        with pytest.raises(ElementNotInteractable) as exc_info:
            raise ElementNotInteractable()
        assert str(exc_info.value) == 'The element is not interactable'

    def test_click_intercepted(self):
        """Test ClickIntercepted exception."""
        with pytest.raises(ClickIntercepted) as exc_info:
            raise ClickIntercepted()
        assert str(exc_info.value) == 'The click was intercepted'

    def test_click_intercepted_custom(self):
        """Test ClickIntercepted with custom message."""
        custom_message = 'Click intercepted by overlay element'
        with pytest.raises(ClickIntercepted) as exc_info:
            raise ClickIntercepted(custom_message)
        assert str(exc_info.value) == custom_message

    def test_element_not_a_file_input(self):
        """Test ElementNotAFileInput exception."""
        with pytest.raises(ElementNotAFileInput) as exc_info:
            raise ElementNotAFileInput()
        assert str(exc_info.value) == 'The element is not a file input'

    def test_element_not_a_file_input_custom(self):
        """Test ElementNotAFileInput with custom message."""
        custom_message = 'Expected file input, got text input'
        with pytest.raises(ElementNotAFileInput) as exc_info:
            raise ElementNotAFileInput(custom_message)
        assert str(exc_info.value) == custom_message


class TestTimeoutExceptions:
    """Test timeout-related exceptions."""

    def test_page_load_timeout(self):
        """Test PageLoadTimeout exception."""
        with pytest.raises(PageLoadTimeout) as exc_info:
            raise PageLoadTimeout()
        assert str(exc_info.value) == 'Page load timed out'

    def test_page_load_timeout_custom(self):
        """Test PageLoadTimeout with custom message."""
        custom_message = 'Page load timed out after 30 seconds'
        with pytest.raises(PageLoadTimeout) as exc_info:
            raise PageLoadTimeout(custom_message)
        assert str(exc_info.value) == custom_message

    def test_wait_element_timeout(self):
        """Test WaitElementTimeout exception."""
        with pytest.raises(WaitElementTimeout) as exc_info:
            raise WaitElementTimeout()
        assert str(exc_info.value) == 'Timed out waiting for element to appear'

    def test_wait_element_timeout_custom(self):
        """Test WaitElementTimeout with custom message."""
        custom_message = 'Element with selector "#button" did not appear within 10 seconds'
        with pytest.raises(WaitElementTimeout) as exc_info:
            raise WaitElementTimeout(custom_message)
        assert str(exc_info.value) == custom_message


class TestConfigurationExceptions:
    """Test configuration-related exceptions."""

    def test_invalid_options_object(self):
        """Test InvalidOptionsObject exception."""
        with pytest.raises(InvalidOptionsObject) as exc_info:
            raise InvalidOptionsObject()
        assert str(exc_info.value) == 'The options object provided is invalid'

    def test_invalid_options_object_custom(self):
        """Test InvalidOptionsObject with custom message."""
        custom_message = 'Options must be a dictionary'
        with pytest.raises(InvalidOptionsObject) as exc_info:
            raise InvalidOptionsObject(custom_message)
        assert str(exc_info.value) == custom_message

    def test_invalid_browser_path(self):
        """Test InvalidBrowserPath exception."""
        with pytest.raises(InvalidBrowserPath) as exc_info:
            raise InvalidBrowserPath()
        assert str(exc_info.value) == 'The browser path provided is invalid'

    def test_invalid_browser_path_custom(self):
        """Test InvalidBrowserPath with custom message."""
        custom_message = 'Browser not found at /usr/bin/chrome'
        with pytest.raises(InvalidBrowserPath) as exc_info:
            raise InvalidBrowserPath(custom_message)
        assert str(exc_info.value) == custom_message

    def test_argument_already_exists_in_options(self):
        """Test ArgumentAlreadyExistsInOptions exception."""
        with pytest.raises(ArgumentAlreadyExistsInOptions) as exc_info:
            raise ArgumentAlreadyExistsInOptions()
        assert str(exc_info.value) == 'The argument already exists in the options'

    def test_argument_already_exists_custom(self):
        """Test ArgumentAlreadyExistsInOptions with custom message."""
        custom_message = 'Argument --headless already exists'
        with pytest.raises(ArgumentAlreadyExistsInOptions) as exc_info:
            raise ArgumentAlreadyExistsInOptions(custom_message)
        assert str(exc_info.value) == custom_message

    def test_invalid_file_extension(self):
        """Test InvalidFileExtension exception."""
        with pytest.raises(InvalidFileExtension) as exc_info:
            raise InvalidFileExtension()
        assert str(exc_info.value) == 'The file extension provided is not supported'


class TestDialogExceptions:
    """Test dialog-related exceptions."""

    def test_no_dialog_present(self):
        """Test NoDialogPresent exception."""
        with pytest.raises(NoDialogPresent) as exc_info:
            raise NoDialogPresent()
        assert str(exc_info.value) == 'No dialog present on the page'

    def test_no_dialog_present_custom(self):
        """Test NoDialogPresent with custom message."""
        custom_message = 'Expected alert dialog but none found'
        with pytest.raises(NoDialogPresent) as exc_info:
            raise NoDialogPresent(custom_message)
        assert str(exc_info.value) == custom_message


class TestIFrameExceptions:
    """Test iframe-related exceptions."""

    def test_not_an_iframe(self):
        """Test NotAnIFrame exception."""
        with pytest.raises(NotAnIFrame) as exc_info:
            raise NotAnIFrame()
        assert str(exc_info.value) == 'The element is not an iframe'

    def test_not_an_iframe_custom(self):
        """Test NotAnIFrame with custom message."""
        custom_message = 'Expected iframe element, got div'
        with pytest.raises(NotAnIFrame) as exc_info:
            raise NotAnIFrame(custom_message)
        assert str(exc_info.value) == custom_message

    def test_invalid_iframe(self):
        """Test InvalidIFrame exception."""
        with pytest.raises(InvalidIFrame) as exc_info:
            raise InvalidIFrame()
        assert str(exc_info.value) == 'The iframe is not valid'

    def test_invalid_iframe_custom(self):
        """Test InvalidIFrame with custom message."""
        custom_message = 'IFrame has no src attribute'
        with pytest.raises(InvalidIFrame) as exc_info:
            raise InvalidIFrame(custom_message)
        assert str(exc_info.value) == custom_message

    def test_iframe_not_found(self):
        """Test IFrameNotFound exception."""
        with pytest.raises(IFrameNotFound) as exc_info:
            raise IFrameNotFound()
        assert str(exc_info.value) == 'The iframe was not found'

    def test_iframe_not_found_custom(self):
        """Test IFrameNotFound with custom message."""
        custom_message = 'IFrame with name "content" not found'
        with pytest.raises(IFrameNotFound) as exc_info:
            raise IFrameNotFound(custom_message)
        assert str(exc_info.value) == custom_message


class TestExceptionInheritance:
    """Test exception inheritance hierarchy."""

    def test_all_exceptions_inherit_from_pydoll_exception(self):
        """Test that all custom exceptions inherit from PydollException."""
        exceptions_to_test = [
            ConnectionFailed, ReconnectionFailed, WebSocketConnectionClosed, NetworkError,
            BrowserNotRunning, FailedToStartBrowser, UnsupportedOS, NoValidTabFound,
            InvalidCommand, InvalidResponse, ResendCommandFailed, CommandExecutionTimeout,
            InvalidCallback, EventNotSupported, ElementNotFound, ElementNotVisible,
            ElementNotInteractable, ClickIntercepted, ElementNotAFileInput,
            PageLoadTimeout, WaitElementTimeout, InvalidOptionsObject, InvalidBrowserPath,
            ArgumentAlreadyExistsInOptions, InvalidFileExtension, NoDialogPresent,
            NotAnIFrame, InvalidIFrame, IFrameNotFound
        ]
        
        for exception_class in exceptions_to_test:
            assert issubclass(exception_class, PydollException), f"{exception_class.__name__} should inherit from PydollException"

    def test_base_exception_categories(self):
        """Test that base exception categories inherit from PydollException."""
        base_exceptions = [
            ConnectionException, BrowserException, ProtocolException,
            ElementException, TimeoutException, ConfigurationException, DialogException
        ]
        
        for exception_class in base_exceptions:
            assert issubclass(exception_class, PydollException), f"{exception_class.__name__} should inherit from PydollException"

    def test_connection_exceptions_inherit_from_connection_exception(self):
        """Test that connection exceptions inherit from ConnectionException."""
        connection_exceptions = [ConnectionFailed, ReconnectionFailed, WebSocketConnectionClosed, NetworkError]
        
        for exception_class in connection_exceptions:
            assert issubclass(exception_class, ConnectionException), f"{exception_class.__name__} should inherit from ConnectionException"
