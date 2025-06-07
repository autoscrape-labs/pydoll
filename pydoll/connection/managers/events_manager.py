import asyncio
import logging
from typing import Any, Callable, Dict, List, cast

from pydoll.protocol.base import Event
from pydoll.protocol.page.types import (
    JavascriptDialogOpeningEvent,
    JavascriptDialogOpeningEventParams,
)

logger = logging.getLogger(__name__)


class EventsManager:
    """
    Manages event callbacks, processing, and network logs.

    Handles event callback registration, triggering, and maintains state
    for network logs and dialog information.
    """

    def __init__(self) -> None:
        """Initialize events manager with empty state."""
        self._event_callbacks: Dict[int, Dict] = {}
        self._callback_id = 0
        self.network_logs: List[Event] = []
        self.dialog = JavascriptDialogOpeningEvent(method='')
        logger.info('EventsManager initialized')

    def register_callback(
        self, event_name: str, callback: Callable[[Dict], Any], temporary: bool = False
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
        return self._callback_id

    def remove_callback(self, callback_id: int) -> bool:
        """Remove callback by ID."""
        if callback_id not in self._event_callbacks:
            logger.warning(f'Callback ID {callback_id} not found')
            return False

        del self._event_callbacks[callback_id]
        logger.info(f'Removed callback ID {callback_id}')
        return True

    def clear_callbacks(self):
        """Remove all registered callbacks."""
        self._event_callbacks.clear()
        logger.info('All callbacks cleared')

    async def process_event(self, event_data: Event):
        """
        Process received event and trigger callbacks.

        Handles special events (network requests, dialogs) and updates
        internal state before triggering registered callbacks.
        """
        event_name = event_data['method']
        logger.debug(f'Processing event: {event_name}')

        if 'Network.requestWillBeSent' in event_name:
            self._update_network_logs(event_data)

        if 'Page.javascriptDialogOpening' in event_name:
            self.dialog = JavascriptDialogOpeningEvent(
                method=event_data['method'],
                params=cast(JavascriptDialogOpeningEventParams, event_data['params']),
            )

        if 'Page.javascriptDialogClosed' in event_name:
            self.dialog = JavascriptDialogOpeningEvent(method='')

        await self._trigger_callbacks(event_name, event_data)

    def _update_network_logs(self, event_data: Event):
        """Add network event to logs (keeps last 10000 entries)."""
        self.network_logs.append(event_data)
        self.network_logs = self.network_logs[-10000:]  # keep only last 10000 logs

    async def _trigger_callbacks(self, event_name: str, event_data: Event):
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
