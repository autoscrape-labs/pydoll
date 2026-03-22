"""Field descriptor and extraction metadata for ExtractionModel fields."""

from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Callable, Optional, Union

from pydantic import Field as PydanticField
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined

from pydoll.extractor.exceptions import InvalidExtractionModel

# Module-level registry: stores ExtractionMetadata keyed by a unique int.
# Field() registers metadata and stores the key in pydantic's json_schema_extra.
# ExtractionModel.__init_subclass__ reads the key to retrieve metadata.
_FIELD_METADATA_REGISTRY: dict[int, ExtractionMetadata] = {}
_field_id_counter = itertools.count(1)


@dataclass(frozen=True)
class ExtractionMetadata:
    """Immutable extraction metadata attached to a pydantic field.

    Stored in a module-level registry by Field() and retrieved by
    ExtractionModel.__init_subclass__ via the registry key stored
    in the field's json_schema_extra.
    """

    selector: Optional[str] = None
    attribute: Optional[str] = None
    transform: Optional[Callable[[str], Union[str, int, float, bool, object]]] = None

    @property
    def has_selector(self) -> bool:
        """Whether this field has a CSS or XPath selector."""
        return self.selector is not None


def pop_field_metadata(key: int) -> Optional[ExtractionMetadata]:
    """Retrieve and remove ExtractionMetadata from the registry by key.

    Uses pop to prevent the registry from growing indefinitely.
    Each key is consumed exactly once during model class creation.

    Args:
        key: Registry key stored in json_schema_extra['_extraction_key'].

    Returns:
        ExtractionMetadata if found, None otherwise.
    """
    return _FIELD_METADATA_REGISTRY.pop(key, None)


def Field(
    *,
    selector: Optional[str] = None,
    attribute: Optional[str] = None,
    description: Optional[str] = None,
    default: object = PydanticUndefined,
    transform: Optional[Callable[[str], Union[str, int, float, bool, object]]] = None,
) -> FieldInfo:
    """Define extraction metadata for a model field.

    Wraps pydantic.Field() and registers ExtractionMetadata for the engine.
    Auto-detects CSS vs XPath from selector syntax (same logic as Tab.query()).

    At least one of ``selector`` or ``description`` must be provided:
    - selector only: extracted via CSS/XPath.
    - description only: metadata for future LLM extraction.
    - both: CSS extraction with LLM fallback in future auto strategy.

    Args:
        selector: CSS or XPath selector (auto-detected, like Tab.query()).
        attribute: HTML attribute to extract (default: innerText).
        description: Semantic description of the field.
        default: Default value if extraction fails. PydanticUndefined means required.
        transform: Post-processing callable applied to raw extracted string.

    Returns:
        Pydantic FieldInfo with extraction registry key in json_schema_extra.

    Raises:
        InvalidExtractionModel: If neither selector nor description is provided.
    """
    if selector is None and description is None:
        raise InvalidExtractionModel('Field must have at least a selector or a description')

    metadata = ExtractionMetadata(
        selector=selector,
        attribute=attribute,
        transform=transform,
    )

    key = _register_metadata(metadata)

    return PydanticField(
        default=default,
        description=description,
        json_schema_extra={'_extraction_key': key},
    )


def _register_metadata(metadata: ExtractionMetadata) -> int:
    """Register ExtractionMetadata and return its unique key."""
    key = next(_field_id_counter)
    _FIELD_METADATA_REGISTRY[key] = metadata
    return key
