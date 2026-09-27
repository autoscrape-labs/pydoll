import asyncio
import inspect
import logging
import time
import traceback
from functools import wraps
from typing import Any, Callable, List, Type, TypeVar, cast

logger = logging.getLogger(__name__)

T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])


class RetryConfig:
    def __init__(
        self,
        max_retries: int = 5,
        exceptions: Type[Exception] | List[Type[Exception]] = Exception,
        on_retry: Callable | None = None,
        delay: float = 0,
        exponential_backoff: bool = False,
    ):
        self.max_retries = max_retries
        self.exceptions = exceptions
        self.on_retry = on_retry
        self.delay = delay
        self.exponential_backoff = exponential_backoff

    def calculate_delay(self, attempt: int) -> float:
        if not self.delay:
            return 0
        return self.delay * (2**attempt if self.exponential_backoff else 1)

    def _invoke_on_retry(self, caller_instance: Any) -> Any:
        """Call ``on_retry`` with the decorated method's instance, or with no arguments
        when the callback does not take one."""
        if not self.on_retry:
            return None
        try:
            return self.on_retry(caller_instance)
        except TypeError as e:
            error_msg = str(e)
            if (
                'takes 1 positional argument but 2 were given' in error_msg
                or 'takes 0 positional arguments but 1 was given' in error_msg
            ):
                return self.on_retry()
            raise

    async def call_callback(self, caller_instance: Any) -> None:
        result = self._invoke_on_retry(caller_instance)
        if inspect.isawaitable(result):
            await result

    def call_callback_sync(self, caller_instance: Any) -> None:
        """Run ``on_retry`` for a synchronous decorated function."""
        self._invoke_on_retry(caller_instance)

    async def handle_delay(self, attempt: int) -> None:
        """
        Wait for delay.

        Args:
            attempt (int): The current attempt number
        """
        wait_time = self.calculate_delay(attempt)
        if wait_time:
            await asyncio.sleep(wait_time)

    def handle_delay_sync(self, attempt: int) -> None:
        """Block for the delay of a synchronous decorated function."""
        wait_time = self.calculate_delay(attempt)
        if wait_time:
            time.sleep(wait_time)

    def is_matching_exception(self, exc: Exception) -> bool:
        if isinstance(self.exceptions, (list, tuple)):
            return any(isinstance(exc, e) for e in self.exceptions)
        return isinstance(exc, self.exceptions)


def retry(
    max_retries: int = 5,
    exceptions: Type[Exception] | List[Type[Exception]] = Exception,
    on_retry: Callable | None = None,
    delay: float = 0,
    exponential_backoff: bool = False,
    exception_to_raise: Exception | None = None,
):
    """
    Decorator to try to execute a function again in case of exception.
    For greater control, it is a good practice to specify the exceptions that should be handled.

    Works on both ``async def`` and plain ``def`` functions. A synchronous function gets a
    synchronous wrapper, so ``on_retry`` must then be synchronous as well.

    Args:
        max_retries (int): Maximum number of attempts
        exceptions (type[Exception] | list[type[Exception]]): Exception types that should be
            handled
        on_retry (Callable | None, optional): Function called after each failed attempt
        delay (float): Delay between attempts in seconds
        exponential_backoff (bool): If True, increase the delay exponentially

    Usage:
        @retry(
            max_retries=3,
            exceptions=[ValueError, TypeError],
            delay=1
        )
        def my_function():
            ...
    """
    config = RetryConfig(
        max_retries=max_retries,
        exceptions=exceptions,
        on_retry=on_retry,
        delay=delay,
        exponential_backoff=exponential_backoff,
    )

    def decorator(func: F) -> F:
        if not inspect.iscoroutinefunction(func):
            return _sync_retry(func, config, exception_to_raise)

        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: Exception | None = None
            caller_instance = args[0] if args else None

            for attempt in range(config.max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as exc:
                    logger.error(
                        f'Error trying to execute the function {func.__name__}: '
                        f'{traceback.format_exc()}'
                    )
                    if not config.is_matching_exception(exc):
                        raise exc

                    last_exception = exc

                    if attempt < config.max_retries:
                        await config.handle_delay(attempt + 1)
                        await config.call_callback(caller_instance)
                    continue

            if last_exception is not None:
                raise exception_to_raise or last_exception

            raise RuntimeError('Unreachable: all retries exhausted without exception')

        return cast(F, wrapper)

    return decorator


def _sync_retry(func: F, config: RetryConfig, exception_to_raise: Exception | None) -> F:
    """Build the retry wrapper for a synchronous function."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        last_exception: Exception | None = None
        caller_instance = args[0] if args else None

        for attempt in range(config.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                logger.error(
                    f'Error trying to execute the function {func.__name__}: '
                    f'{traceback.format_exc()}'
                )
                if not config.is_matching_exception(exc):
                    raise exc

                last_exception = exc

                if attempt < config.max_retries:
                    config.handle_delay_sync(attempt + 1)
                    config.call_callback_sync(caller_instance)
                continue

        if last_exception is not None:
            raise exception_to_raise or last_exception

        raise RuntimeError('Unreachable: all retries exhausted without exception')

    return cast(F, wrapper)
