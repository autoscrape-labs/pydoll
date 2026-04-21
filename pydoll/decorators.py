import asyncio
import logging
import traceback
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Coroutine, List, Optional, Type, TypeVar, Union

from pydoll.browser.tab import Tab

logger = logging.getLogger(__name__)

T = TypeVar('T')


def debug_snapshot(save_dir: Union[str, Path] = 'debug_snapshots'):
    """
    Decorator to capture a debug snapshot (MHTML, HAR, and traceback) on failure.

    This decorator identifies the browser 'Tab' instance from the decorated function's
    arguments and automates the capture of the current page state if an exception occurs.

    Args:
        save_dir (Union[str, Path]): Directory where snapshots will be saved.

    Usage:
        @debug_snapshot()
        async def my_scraping_task(tab: Tab):
            await tab.go_to("https://example.com")
            # If this fails, a snapshot folder will be created.
    """

    def decorator(
        func: Callable[..., Coroutine[Any, Any, T]],
    ) -> Callable[..., Coroutine[Any, Any, T]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            # Try to find a Tab instance in args or kwargs
            tab: Optional[Tab] = None

            # Helper to extract Tab from an object
            def get_tab(obj: Any) -> Optional[Tab]:
                if isinstance(obj, Tab):
                    return obj
                for attr in ("tab", "browser"):
                    val = getattr(obj, attr, None)
                    if isinstance(val, Tab):
                        return val
                return None

            # Search in args first
            for arg in args:
                tab = get_tab(arg)
                if tab:
                    break

            # Then search in kwargs
            if not tab:
                for val in kwargs.values():
                    tab = get_tab(val)
                    if tab:
                        break

            if not tab:
                logger.warning(
                    f'debug_snapshot: Could not find a Tab instance for {func.__name__}. '
                    'Snapshot will not be captured.'
                )
                return await func(*args, **kwargs)

            # Start HAR recording
            async with tab.request.record() as capture:
                try:
                    return await func(*args, **kwargs)
                except Exception as exc:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    folder_name = f'{func.__name__}_{timestamp}'
                    base_path = Path(save_dir) / folder_name
                    base_path.mkdir(parents=True, exist_ok=True)

                    logger.error(f'Function {func.__name__} failed. Capturing debug snapshot...')

                    # 1. Save Page Snapshot (MHTML)
                    try:
                        await tab.save_page_snapshot(base_path / 'bundle.mhtml')
                    except Exception as snap_exc:
                        logger.error(f'Failed to save page snapshot: {snap_exc}')

                    # 2. Save Network HAR
                    try:
                        capture.save(base_path / 'network.har')
                    except Exception as har_exc:
                        logger.error(f'Failed to save network HAR: {har_exc}')

                    # 3. Save Traceback
                    try:
                        with open(base_path / 'traceback.log', 'w', encoding='utf-8') as f:
                            f.write(traceback.format_exc())
                    except Exception as log_exc:
                        logger.error(f'Failed to save traceback log: {log_exc}')

                    logger.info(f'Debug snapshot saved to {base_path}')
                    raise exc

        return wrapper

    return decorator


class RetryConfig:
    def __init__(
        self,
        max_retries: int = 5,
        exceptions: Union[Type[Exception], List[Type[Exception]]] = Exception,
        on_retry: Optional[Callable] = None,
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

    async def call_callback(self, caller_instance: Any) -> None:
        if not self.on_retry:
            return

        try:
            await self.on_retry(caller_instance)
        except TypeError as e:
            error_msg = str(e)
            if (
                'takes 1 positional argument but 2 were given' in error_msg
                or 'takes 0 positional arguments but 1 was given' in error_msg
            ):
                try:
                    await self.on_retry()
                    return
                except Exception as e_inner:
                    raise e_inner
            raise e
        except Exception as e:
            raise e

    async def handle_delay(self, attempt: int) -> None:
        """
        Wait for delay.

        Args:
            attempt (int): The current attempt number
        """
        wait_time = self.calculate_delay(attempt)
        if wait_time:
            await asyncio.sleep(wait_time)

    def is_matching_exception(self, exc: Exception) -> bool:
        if isinstance(self.exceptions, (list, tuple)):
            return any(isinstance(exc, e) for e in self.exceptions)
        return isinstance(exc, self.exceptions)


def retry(
    max_retries: int = 5,
    exceptions: Union[Type[Exception], List[Type[Exception]]] = Exception,
    on_retry: Optional[Callable] = None,
    delay: float = 0,
    exponential_backoff: bool = False,
    exception_to_raise: Optional[Exception] = None,
):
    """
    Decorator to try to execute a function again in case of exception.
    For greater control, it is a good practice to specify the exceptions that should be handled.

    Args:
        max_retries (int): Maximum number of attempts
        exceptions (Union[Type[Exception], List[Type[Exception]]]): Exception types that should be
            handled
        on_retry (Optional[Callable], optional): Function called after each failed attempt
        delay (float): Delay between attempts in seconds
        exponential_backoff (bool): If True, increase the delay exponentially

    Usage:
        @retry_on_exception(
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

    def decorator(
        func: Callable[..., Coroutine[Any, Any, T]],
    ) -> Callable[..., Coroutine[Any, Any, T]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception: Optional[Exception] = None
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

        return wrapper

    return decorator
