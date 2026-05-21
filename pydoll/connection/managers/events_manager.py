from __future__ import annotations

import asyncio
import logging
from collections import deque
from contextlib import suppress
from typing import TYPE_CHECKING, Optional, cast

from pydoll.protocol.page.events import (
    JavascriptDialogOpeningEvent,
    JavascriptDialogOpeningEventParams,
)

if TYPE_CHECKING:
    from typing import Any, Callable

    from pydoll.protocol.base import CDPEvent
    from pydoll.protocol.network.events import RequestWillBeSentEvent

logger = logging.getLogger(__name__)

MAX_NETWORK_LOGS = 10000


class EventsManager:
    """
    Manages event callbacks, processing, and network logs.

    Handles event callback registration, triggering, and maintains state
    for network logs and dialog information.
    """

    def __init__(self) -> None:
        """Initialize events manager with empty state."""
        self._event_callbacks: dict[int, dict] = {}
        self._callback_id = 0
        self.network_logs: deque[RequestWillBeSentEvent] = deque(maxlen=MAX_NETWORK_LOGS)
        self.dialog = JavascriptDialogOpeningEvent()  # type: ignore
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._worker_task: Optional[asyncio.Task] = None
        logger.info('EventsManager initialized')
        logger.debug('Initial state: callbacks=0, logs=0, dialog=empty')

    def start(self) -> None:
        """Start the event-processing worker if not already running.

        Called when a connection is established. The worker drains queued events
        in arrival order so event handling never blocks the WebSocket read loop.
        Its lifetime is bound to the connection: stop() is invoked from the
        receive loop's finally block, so the worker can never outlive the socket.
        """
        if self._worker_task is None or self._worker_task.done():
            self._worker_task = asyncio.create_task(self._process_event_queue())

    def enqueue_event(self, event_data: CDPEvent) -> None:
        """Queue an event for ordered, non-blocking processing.

        Queuing is O(1) and never awaits, so a slow event callback can never
        delay delivery of command responses on the read loop.
        """
        self._event_queue.put_nowait(event_data)

    async def stop(self) -> None:
        """Cancel the worker, await its exit, and drop any queued events.

        Awaiting the cancelled task is what prevents "Task was destroyed but it
        is pending" warnings: the task is never garbage-collected while pending.
        """
        if self._worker_task and not self._worker_task.done():
            self._worker_task.cancel()
            with suppress(asyncio.CancelledError, Exception):
                await self._worker_task
        self._worker_task = None
        self._clear_queue()

    def _clear_queue(self) -> None:
        """Discard events left over from a dead connection."""
        while True:
            try:
                self._event_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
            else:
                self._event_queue.task_done()

    async def _process_event_queue(self) -> None:
        """Drain queued events in order, isolating per-event failures."""
        while True:
            event_data = await self._event_queue.get()
            try:
                await self.process_event(event_data)
            except Exception:
                logger.exception('Error processing CDP event')
            finally:
                self._event_queue.task_done()

    def register_callback(
        self, event_name: str, callback: Callable[[dict], Any], temporary: bool = False
    ) -> int:
        """
        Register callback for specific event type.

        Args:
            event_name: Event name to listen for.
            callback: Function called when event occurs.
            temporary: If True, callback removed after first trigger.

        Returns:
            Callback ID for later removal.
        """
        self._callback_id += 1
        self._event_callbacks[self._callback_id] = {
            'event': event_name,
            'callback': callback,
            'temporary': temporary,
        }
        logger.info(f"Registered callback '{event_name}' with ID {self._callback_id}")
        logger.debug(
            f'Callback details: temporary={temporary}, total_callbacks={len(self._event_callbacks)}'
        )
        return self._callback_id

    def remove_callback(self, callback_id: int) -> bool:
        """Remove callback by ID."""
        if callback_id not in self._event_callbacks:
            logger.warning(f'Callback ID {callback_id} not found')
            return False

        del self._event_callbacks[callback_id]
        logger.info(f'Removed callback ID {callback_id}')
        logger.debug(f'Remaining callbacks: {len(self._event_callbacks)}')
        return True

    def clear_callbacks(self):
        """Remove all registered callbacks."""
        self._event_callbacks.clear()
        logger.info('All callbacks cleared')
        logger.debug('Callbacks store is now empty')

    async def process_event(self, event_data: CDPEvent):
        """
        Process received event and trigger callbacks.

        Handles special events (network requests, dialogs) and updates
        internal state before triggering registered callbacks.
        """
        event_name = event_data.get('method')
        if not event_name:
            logger.warning(f'Discarding event without method: {str(event_data)[:200]}')
            return
        logger.debug(f'Processing event: {event_name}')

        if 'Network.requestWillBeSent' in event_name:
            self._update_network_logs(event_data)

        if 'Page.javascriptDialogOpening' in event_name and 'params' in event_data:
            self.dialog = JavascriptDialogOpeningEvent(
                method=event_name,
                params=cast(JavascriptDialogOpeningEventParams, event_data['params']),
            )

        if 'Page.javascriptDialogClosed' in event_name:
            self.dialog = JavascriptDialogOpeningEvent()  # type: ignore

        await self._trigger_callbacks(event_name, event_data)

    def _update_network_logs(self, event_data: RequestWillBeSentEvent):
        """Add network event to logs (bounded deque keeps the last MAX_NETWORK_LOGS)."""
        self.network_logs.append(event_data)

    async def _trigger_callbacks(self, event_name: str, event_data: CDPEvent):
        """Trigger all registered callbacks for event, removing temporary ones."""
        callbacks_to_remove = []

        for cb_id, cb_data in list(self._event_callbacks.items()):
            if cb_data['event'] == event_name:
                try:
                    if asyncio.iscoroutinefunction(cb_data['callback']):
                        await cb_data['callback'](event_data)
                    else:
                        cb_data['callback'](event_data)
                except Exception as e:
                    logger.error(f'Error in callback {cb_id}: {str(e)}')

                if cb_data['temporary']:
                    callbacks_to_remove.append(cb_id)

        for cb_id in callbacks_to_remove:
            self.remove_callback(cb_id)
        logger.debug(
            f"Triggered callbacks for '{event_name}'. Removed temporaries: {callbacks_to_remove}"
        )
