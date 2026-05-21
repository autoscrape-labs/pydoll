"""Tests for the retry decorator."""

import asyncio
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, call

from pydoll.decorators import retry, RetryConfig
from pydoll.exceptions import (
    ElementNotFound,
    WaitElementTimeout,
    NetworkError,
    PydollException,
)


class TestRetryConfigInitialization:
    """Test RetryConfig initialization."""

    def test_default_initialization(self):
        """Test RetryConfig is properly initialized with defaults."""
        config = RetryConfig()
        assert config.max_retries == 5
        assert config.exceptions == Exception
        assert config.on_retry is None
        assert config.delay == 0
        assert config.exponential_backoff is False

    def test_custom_initialization(self):
        """Test RetryConfig with custom parameters."""
        callback = AsyncMock()
        config = RetryConfig(
            max_retries=3,
            exceptions=[ElementNotFound, NetworkError],
            on_retry=callback,
            delay=2.0,
            exponential_backoff=True,
        )
        assert config.max_retries == 3
        assert config.exceptions == [ElementNotFound, NetworkError]
        assert config.on_retry == callback
        assert config.delay == 2.0
        assert config.exponential_backoff is True


class TestRetryConfigCalculateDelay:
    """Test delay calculation methods."""

    def test_no_delay(self):
        """Test calculate_delay with zero delay."""
        config = RetryConfig(delay=0)
        assert config.calculate_delay(1) == 0
        assert config.calculate_delay(5) == 0

    def test_constant_delay(self):
        """Test calculate_delay without exponential backoff."""
        config = RetryConfig(delay=2.0, exponential_backoff=False)
        assert config.calculate_delay(0) == 2.0
        assert config.calculate_delay(1) == 2.0
        assert config.calculate_delay(2) == 2.0

    def test_exponential_backoff(self):
        """Test calculate_delay with exponential backoff."""
        config = RetryConfig(delay=1.0, exponential_backoff=True)
        assert config.calculate_delay(0) == 1.0  # 1 * 2^0 = 1
        assert config.calculate_delay(1) == 2.0  # 1 * 2^1 = 2
        assert config.calculate_delay(2) == 4.0  # 1 * 2^2 = 4
        assert config.calculate_delay(3) == 8.0  # 1 * 2^3 = 8


class TestRetryConfigIsMatchingException:
    """Test exception matching logic."""

    def test_single_exception_match(self):
        """Test matching with single exception type."""
        config = RetryConfig(exceptions=ElementNotFound)
        assert config.is_matching_exception(ElementNotFound("test"))
        assert not config.is_matching_exception(NetworkError("test"))

    def test_list_exception_match(self):
        """Test matching with list of exception types."""
        config = RetryConfig(exceptions=[ElementNotFound, NetworkError])
        assert config.is_matching_exception(ElementNotFound("test"))
        assert config.is_matching_exception(NetworkError("test"))
        assert not config.is_matching_exception(WaitElementTimeout("test"))

    def test_parent_exception_match(self):
        """Test matching with parent exception class."""
        config = RetryConfig(exceptions=PydollException)
        assert config.is_matching_exception(ElementNotFound("test"))
        assert config.is_matching_exception(NetworkError("test"))
        assert not config.is_matching_exception(ValueError("test"))


class TestRetryConfigCallCallback:
    """Test on_retry callback execution."""

    @pytest.mark.asyncio
    async def test_no_callback(self):
        """Test call_callback with no callback set."""
        config = RetryConfig(on_retry=None)
        # Should not raise any error
        await config.call_callback(None)

    @pytest.mark.asyncio
    async def test_callback_with_instance(self):
        """Test callback receiving instance argument."""
        callback = AsyncMock()
        config = RetryConfig(on_retry=callback)
        
        instance = MagicMock()
        await config.call_callback(instance)
        
        callback.assert_called_once_with(instance)

    @pytest.mark.asyncio
    async def test_callback_without_instance(self):
        """Test callback that doesn't accept instance argument."""
        # Callback that doesn't accept arguments
        callback_called = False
        
        async def simple_callback():
            nonlocal callback_called
            callback_called = True
        
        config = RetryConfig(on_retry=simple_callback)
        await config.call_callback(MagicMock())
        
        assert callback_called


class TestRetryDecoratorBasic:
    """Test basic retry decorator functionality."""

    @pytest.mark.asyncio
    async def test_successful_execution_no_retry(self):
        """Test function succeeds on first try."""
        call_count = 0
        
        @retry(max_retries=3, exceptions=[ElementNotFound])
        async def successful_function():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = await successful_function()
        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_on_matching_exception(self):
        """Test retry occurs when matching exception is raised."""
        call_count = 0
        
        @retry(max_retries=2, exceptions=[ElementNotFound], delay=0)
        async def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ElementNotFound("Element not found")
            return "success"
        
        result = await failing_function()
        assert result == "success"
        # max_retries=2 means 3 attempts (1 original + 2 retries)
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_no_retry_on_non_matching_exception(self):
        """Test no retry when non-matching exception is raised."""
        call_count = 0
        
        @retry(max_retries=3, exceptions=[ElementNotFound], delay=0)
        async def failing_function():
            nonlocal call_count
            call_count += 1
            raise NetworkError("Network error")
        
        with pytest.raises(NetworkError):
            await failing_function()
        
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_exhaust_all_retries(self):
        """Test all retries are exhausted before raising."""
        call_count = 0
        
        @retry(max_retries=2, exceptions=[ElementNotFound], delay=0)
        async def always_failing():
            nonlocal call_count
            call_count += 1
            raise ElementNotFound("Always fails")
        
        with pytest.raises(ElementNotFound):
            await always_failing()
        
        # max_retries=2 means 3 attempts (1 original + 2 retries)
        assert call_count == 3


class TestRetryDecoratorWithMultipleExceptions:
    """Test retry with multiple exception types."""

    @pytest.mark.asyncio
    async def test_retry_on_any_listed_exception(self):
        """Test retry occurs for any exception in the list."""
        exceptions_raised = []
        
        @retry(
            max_retries=3,
            exceptions=[ElementNotFound, NetworkError, WaitElementTimeout],
            delay=0
        )
        async def multi_exception_function():
            if len(exceptions_raised) == 0:
                exceptions_raised.append("ElementNotFound")
                raise ElementNotFound("First error")
            elif len(exceptions_raised) == 1:
                exceptions_raised.append("NetworkError")
                raise NetworkError("Second error")
            elif len(exceptions_raised) == 2:
                exceptions_raised.append("WaitElementTimeout")
                raise WaitElementTimeout("Third error")
            return "success"
        
        result = await multi_exception_function()
        assert result == "success"
        # max_retries=3 means 4 attempts total, success on 4th
        assert len(exceptions_raised) == 3


class TestRetryDecoratorWithDelay:
    """Test retry with delay between attempts."""

    @pytest.mark.asyncio
    async def test_constant_delay(self):
        """Test constant delay between retries."""
        call_times = []
        
        @retry(max_retries=2, exceptions=[ElementNotFound], delay=0.1)
        async def delayed_function():
            call_times.append(asyncio.get_event_loop().time())
            if len(call_times) < 3:
                raise ElementNotFound("Retry")
            return "success"
        
        await delayed_function()
        
        # max_retries=2 means 3 attempts (1 original + 2 retries)
        assert len(call_times) == 3
        # Check delays between calls (should be ~0.1s)
        # Allow 50ms tolerance for timing
        assert call_times[1] - call_times[0] >= 0.05
        assert call_times[2] - call_times[1] >= 0.05

    @pytest.mark.asyncio
    async def test_exponential_backoff(self):
        """Test exponential backoff increases delay."""
        call_times = []
        
        @retry(
            max_retries=3,
            exceptions=[ElementNotFound],
            delay=0.1,
            exponential_backoff=True
        )
        async def exponential_function():
            call_times.append(asyncio.get_event_loop().time())
            if len(call_times) < 4:
                raise ElementNotFound("Retry")
            return "success"
        
        await exponential_function()
        
        # max_retries=3 means 4 attempts (1 original + 3 retries)
        assert len(call_times) == 4
        # First delay: ~0.1s (2^0 * 0.1)
        # Second delay: ~0.2s (2^1 * 0.1)
        # Third delay: ~0.4s (2^2 * 0.1)
        delay1 = call_times[1] - call_times[0]
        delay2 = call_times[2] - call_times[1]
        delay3 = call_times[3] - call_times[2]
        
        # Each delay should roughly double (with tolerance)
        assert delay2 > delay1 * 1.5
        assert delay3 > delay2 * 1.5


class TestRetryDecoratorWithCallback:
    """Test retry with on_retry callback."""

    @pytest.mark.asyncio
    async def test_callback_called_on_retry(self):
        """Test callback is called before each retry."""
        callback_count = 0
        
        async def retry_callback():
            nonlocal callback_count
            callback_count += 1
        
        call_count = 0
        
        @retry(
            max_retries=2,
            exceptions=[ElementNotFound],
            on_retry=retry_callback,
            delay=0
        )
        async def function_with_callback():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ElementNotFound("Retry")
            return "success"
        
        await function_with_callback()
        
        # max_retries=2 means 3 attempts (1 original + 2 retries)
        # Function called 3 times, callback called 2 times (before retry 1 and 2)
        assert call_count == 3
        assert callback_count == 2

    @pytest.mark.asyncio
    async def test_callback_receives_instance(self):
        """Test callback receives instance when used with class method."""
        class TestClass:
            def __init__(self):
                self.callback_count = 0
                self.instance_received = None
                self.call_count = 0
            
            async def recovery_callback(self):
                self.callback_count += 1
                self.instance_received = self
            
            @retry(
                max_retries=2,
                exceptions=[ElementNotFound],
                on_retry=recovery_callback,
                delay=0
            )
            async def method_with_callback(self):
                self.call_count += 1
                if self.call_count < 3:
                    raise ElementNotFound("Retry")
                return "success"
        
        instance = TestClass()
        result = await instance.method_with_callback()
        
        assert result == "success"
        # max_retries=2 means 3 attempts, callback called 2 times
        assert instance.callback_count == 2
        assert instance.instance_received is instance


class TestRetryDecoratorEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_zero_retries_succeeds(self):
        """Test with max_retries=0 succeeds on first attempt."""
        call_count = 0
        
        @retry(max_retries=0, exceptions=[ElementNotFound], delay=0)
        async def zero_retry_function():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = await zero_retry_function()
        assert result == "success"
        # max_retries=0 means 1 attempt (no retries)
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_zero_retries_fails_immediately(self):
        """Test with max_retries=0 fails without retry."""
        call_count = 0
        
        @retry(max_retries=0, exceptions=[ElementNotFound], delay=0)
        async def zero_retry_function():
            nonlocal call_count
            call_count += 1
            raise ElementNotFound("Fail")
        
        with pytest.raises(ElementNotFound):
            await zero_retry_function()
        
        # max_retries=0 means 1 attempt, no retries
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_one_retry_succeeds_on_second_attempt(self):
        """Test with max_retries=1 succeeds on second attempt."""
        call_count = 0
        
        @retry(max_retries=1, exceptions=[ElementNotFound], delay=0)
        async def one_retry_function():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ElementNotFound("Fail")
            return "success"
        
        result = await one_retry_function()
        assert result == "success"
        # max_retries=1 means 2 attempts (1 original + 1 retry)
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_exception_to_raise_parameter(self):
        """Test custom exception can be raised instead of original."""
        call_count = 0
        
        custom_exception = NetworkError("Custom error message")
        
        @retry(
            max_retries=1,
            exceptions=[ElementNotFound],
            delay=0,
            exception_to_raise=custom_exception
        )
        async def function_with_custom_exception():
            nonlocal call_count
            call_count += 1
            raise ElementNotFound("Original error")
        
        with pytest.raises(NetworkError) as exc_info:
            await function_with_custom_exception()
        
        assert str(exc_info.value) == "Custom error message"
        # max_retries=1 means 2 attempts (1 original + 1 retry)
        assert call_count == 2


class TestRetryDecoratorWithClassMethods:
    """Test retry decorator with class methods."""

    @pytest.mark.asyncio
    async def test_instance_method(self):
        """Test decorator on instance method."""
        class Counter:
            def __init__(self):
                self.count = 0
            
            @retry(max_retries=2, exceptions=[ElementNotFound], delay=0)
            async def increment(self):
                self.count += 1
                if self.count < 3:
                    raise ElementNotFound("Retry")
                return self.count
        
        counter = Counter()
        result = await counter.increment()
        
        # max_retries=2 means 3 attempts (1 original + 2 retries)
        assert result == 3
        assert counter.count == 3

    @pytest.mark.asyncio
    async def test_method_with_arguments(self):
        """Test decorated method with arguments."""
        class Calculator:
            @retry(max_retries=3, exceptions=[ValueError], delay=0)
            async def divide(self, a: int, b: int):
                if b == 0:
                    raise ValueError("Division by zero")
                return a / b
        
        calc = Calculator()
        result = await calc.divide(10, 2)
        assert result == 5.0

    @pytest.mark.asyncio
    async def test_method_with_state_restoration(self):
        """Test method that restores state in callback."""
        class StatefulClass:
            def __init__(self):
                self.attempts = 0
                self.state = "initial"
            
            async def restore_state(self):
                self.state = "restored"
            
            @retry(
                max_retries=2,
                exceptions=[ElementNotFound],
                on_retry=restore_state,
                delay=0
            )
            async def process(self):
                self.attempts += 1
                if self.attempts < 3:
                    self.state = "broken"
                    raise ElementNotFound("Retry")
                return "success"
        
        obj = StatefulClass()
        result = await obj.process()
        
        assert result == "success"
        # max_retries=2 means 3 attempts (1 original + 2 retries)
        assert obj.attempts == 3
        assert obj.state == "restored"


class TestRetryConfigHandleDelay:
    """Test handle_delay method."""

    @pytest.mark.asyncio
    async def test_handle_delay_no_delay(self):
        """Test handle_delay with zero delay."""
        config = RetryConfig(delay=0)
        
        start_time = asyncio.get_event_loop().time()
        await config.handle_delay(1)
        end_time = asyncio.get_event_loop().time()
        
        # Should be nearly instant
        assert end_time - start_time < 0.01

    @pytest.mark.asyncio
    async def test_handle_delay_with_delay(self):
        """Test handle_delay waits for specified time."""
        config = RetryConfig(delay=0.1, exponential_backoff=False)
        
        start_time = asyncio.get_event_loop().time()
        await config.handle_delay(1)
        end_time = asyncio.get_event_loop().time()
        
        # Should wait approximately 0.1 seconds
        assert end_time - start_time >= 0.05


class TestRetryDecoratorRealWorldScenarios:
    """Test real-world usage scenarios."""

    @pytest.mark.asyncio
    async def test_network_retry_scenario(self):
        """Simulate network retry scenario."""
        class NetworkClient:
            def __init__(self):
                self.attempt_count = 0
                self.reconnect_count = 0
            
            async def reconnect(self):
                """Simulate reconnection logic."""
                await asyncio.sleep(0.01)
                self.reconnect_count += 1
            
            @retry(
                max_retries=2,
                exceptions=[NetworkError],
                on_retry=reconnect,
                delay=0.05,
                exponential_backoff=True
            )
            async def fetch_data(self, url: str):
                self.attempt_count += 1
                # Fail on first 2 attempts, succeed on 3rd
                if self.attempt_count < 3:
                    raise NetworkError(f"Connection failed (attempt {self.attempt_count})")
                return f"Data from {url}"
        
        client = NetworkClient()
        result = await client.fetch_data("https://example.com")
        
        assert result == "Data from https://example.com"
        # max_retries=2 means 3 attempts (1 original + 2 retries)
        assert client.attempt_count == 3
        # Callback called 2 times (before retry 1 and retry 2)
        assert client.reconnect_count == 2

    @pytest.mark.asyncio
    async def test_element_search_retry_scenario(self):
        """Simulate element search with page refresh."""
        class PageScraper:
            def __init__(self):
                self.page_refreshed = False
                self.search_count = 0
            
            async def refresh_page(self):
                """Simulate page refresh."""
                await asyncio.sleep(0.01)
                self.page_refreshed = True
            
            @retry(
                max_retries=2,
                exceptions=[ElementNotFound, WaitElementTimeout],
                on_retry=refresh_page,
                delay=0.05
            )
            async def find_element(self, selector: str):
                self.search_count += 1
                if not self.page_refreshed:
                    raise ElementNotFound(f"Element '{selector}' not found")
                return f"Element: {selector}"
        
        scraper = PageScraper()
        result = await scraper.find_element("#content")
        
        assert result == "Element: #content"
        # max_retries=2 means up to 3 attempts, succeeds on 2nd
        assert scraper.search_count == 2
        assert scraper.page_refreshed is True

