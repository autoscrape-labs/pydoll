"""Polling helpers for flake-resistant integration tests.

These replace fixed ``asyncio.sleep`` calls: instead of guessing how long an
action takes, poll the real browser state (an element's text, a live JS value,
or an arbitrary condition) until it holds or a timeout elapses. Combined with
``find(..., timeout=...)`` for element appearance, they remove timing guesses
from the suite. Module name is underscore-prefixed so pytest does not collect it.
"""

from __future__ import annotations

import asyncio
from typing import Awaitable, Callable


async def wait_until(
    predicate: Callable[[], Awaitable[bool]],
    timeout: float = 10.0,
    interval: float = 0.05,
    message: str = 'condition not met',
) -> None:
    """Poll an async predicate until it returns truthy or *timeout* elapses."""
    loop = asyncio.get_event_loop()
    deadline = loop.time() + timeout
    while True:
        if await predicate():
            return
        if loop.time() >= deadline:
            raise AssertionError(f'{message} within {timeout}s')
        await asyncio.sleep(interval)


async def wait_for_js(
    ctx,
    expression: str,
    predicate: Callable[[object], bool],
    timeout: float = 10.0,
    message: str = 'js condition not met',
) -> None:
    """Poll a live JS expression (via execute_script) until *predicate* holds."""

    async def check() -> bool:
        result = await ctx.execute_script(f'return {expression}', return_by_value=True)
        return bool(predicate(result['result']['result']['value']))

    await wait_until(check, timeout, message=message)


async def wait_for_js_value(ctx, expression: str, expected, timeout: float = 10.0) -> None:
    """Poll a live JS expression until it equals *expected*."""
    await wait_for_js(
        ctx,
        expression,
        lambda value: value == expected,
        timeout,
        message=f'{expression!r} != {expected!r}',
    )


async def wait_for_element_text(element, expected: str, timeout: float = 10.0) -> None:
    """Poll an element's (stripped) text until it equals *expected*."""

    async def check() -> bool:
        return (await element.text).strip() == expected

    await wait_until(check, timeout, message=f'element text != {expected!r}')
