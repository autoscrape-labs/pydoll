"""ExtractionModel base class for declarative data extraction."""

from __future__ import annotations

from typing import ClassVar, Optional

from pydantic import BaseModel, ConfigDict

from pydoll.extractor.exceptions import InvalidExtractionModel
from pydoll.extractor.field import ExtractionMetadata, pop_field_metadata


class ExtractionModel(BaseModel):
    """Base class for declarative extraction models.

    Inherits from pydantic.BaseModel, gaining automatic validation,
    type coercion, serialization (model_dump, model_dump_json), and
    JSON Schema generation (model_json_schema).

    Subclasses define fields using Field() descriptors with selectors
    and/or semantic descriptions. The extraction engine uses this
    metadata to extract structured data from web pages.

    Example::

        class Article(ExtractionModel):
            title: str = Field(selector='h1', description='Article title')
            author: str = Field(selector='.author', description='Author name')
    """

    _extraction_fields_cache: ClassVar[Optional[dict[str, ExtractionMetadata]]] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @classmethod
    def get_extraction_fields(cls) -> dict[str, ExtractionMetadata]:
        """Get extraction metadata for all fields, collecting lazily on first access.

        Each subclass gets its own cache, even if a parent class has already
        been collected. This ensures inherited fields are included correctly.

        Returns:
            Dictionary mapping field name to ExtractionMetadata.

        Raises:
            InvalidExtractionModel: If a field has metadata but lacks
                both selector and description.
        """
        # Check own __dict__ to avoid inheriting parent's cache via MRO
        own_cache = cls.__dict__.get('_extraction_fields_cache')
        if own_cache is not None:
            return own_cache

        result = _collect_extraction_metadata(cls)
        cls._extraction_fields_cache = result
        return result


def _collect_extraction_metadata(
    cls: type[ExtractionModel],
) -> dict[str, ExtractionMetadata]:
    """Read ExtractionMetadata from pydantic FieldInfo objects via registry.

    For each field, checks if json_schema_extra contains an _extraction_key
    that maps to a registered ExtractionMetadata. Validates that each
    extraction field has at least a selector or a description.

    Args:
        cls: ExtractionModel subclass to inspect.

    Returns:
        Dictionary mapping field name to ExtractionMetadata.

    Raises:
        InvalidExtractionModel: If a field has metadata but lacks
            both selector and description.
    """
    result: dict[str, ExtractionMetadata] = {}
    for name, field_info in cls.model_fields.items():
        extra = field_info.json_schema_extra
        if not isinstance(extra, dict):
            continue

        key = extra.get('_extraction_key')
        if not isinstance(key, int):
            continue

        metadata = pop_field_metadata(key)
        if metadata is None:
            continue

        if not metadata.has_selector and not field_info.description:
            raise InvalidExtractionModel(
                f'Field "{name}" must have at least a selector or a description'
            )

        result[name] = metadata
    return result
