from enum import Enum

from typing_extensions import TypedDict

from pydoll.protocol.bidi.base import BiDiEvent
from pydoll.protocol.bidi.script.types import (
    Channel,
    Realm,
    RealmInfo,
    RemoteValue,
    Source,
)


class ScriptEvent(str, Enum):
    """Script module event names."""

    MESSAGE = 'script.message'
    REALM_CREATED = 'script.realmCreated'
    REALM_DESTROYED = 'script.realmDestroyed'


class MessageParameters(TypedDict):
    """Parameters for script.message event."""

    channel: Channel
    data: RemoteValue
    source: Source


class RealmDestroyedParameters(TypedDict):
    """Parameters for script.realmDestroyed event."""

    realm: Realm


MessageEvent = BiDiEvent[MessageParameters]
RealmCreatedEvent = BiDiEvent[RealmInfo]
RealmDestroyedEvent = BiDiEvent[RealmDestroyedParameters]
