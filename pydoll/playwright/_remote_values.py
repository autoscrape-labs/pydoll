"""Conversion of a by-value CDP ``RemoteObject`` into a Python value."""

from __future__ import annotations

import math
from typing import Any


def parse_remote_value(remote_object: dict[str, Any]) -> Any:
    """Convert a by-value ``RemoteObject`` into a Python value.

    The few values JSON cannot carry (NaN, Infinity, -0, undefined) arrive as
    ``unserializableValue`` and are mapped back here.
    """
    unserializable = remote_object.get('unserializableValue')
    if unserializable is not None:
        return {
            'NaN': math.nan,
            'Infinity': math.inf,
            '-Infinity': -math.inf,
            '-0': -0.0,
        }.get(unserializable, unserializable)
    if remote_object.get('type') == 'undefined':
        return None
    return remote_object.get('value')
