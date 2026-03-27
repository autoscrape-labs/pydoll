from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from pydoll.browser.firefox.find_mixin import _FirefoxFindMixin

if TYPE_CHECKING:
    from pydoll.connection.bidi_connection_handler import BiDiConnectionHandler

logger = logging.getLogger(__name__)


class FirefoxShadowRoot(_FirefoxFindMixin):
    """
    Represents a shadow root attached to a Firefox element.

    Provides ``find()`` and ``query()`` scoped inside the shadow DOM, using
    ``browsingContext.locateNodes`` with the shadow root's node reference as
    ``startNodes``.

    Obtain an instance via ``FirefoxElement.get_shadow_root()``.
    """

    def __init__(
        self,
        shared_id: str,
        context_id: str,
        connection_handler: BiDiConnectionHandler,
    ) -> None:
        self._shared_id = shared_id
        self._context_id = context_id
        self._connection_handler = connection_handler
        logger.debug(f'FirefoxShadowRoot initialized: sharedId={shared_id}')

    @property
    def shared_id(self) -> str:
        """BiDi shared reference ID for this shadow root node."""
        return self._shared_id

    @property
    def _find_start_nodes(self) -> list[dict]:
        return [{'type': 'node', 'sharedId': self._shared_id}]

    def __repr__(self) -> str:
        return f'FirefoxShadowRoot(sharedId={self._shared_id!r})'
