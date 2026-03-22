"""Extraction engine that orchestrates DOM querying and model building."""

from __future__ import annotations

import logging
import types
from typing import TYPE_CHECKING, Optional, TypeVar, Union, get_args, get_origin

from pydoll.extractor.exceptions import FieldExtractionFailed
from pydoll.extractor.field import ExtractionMetadata
from pydoll.extractor.model import ExtractionModel

if TYPE_CHECKING:
    from pydoll.browser.tab import Tab
    from pydoll.elements.mixins.find_elements_mixin import FindElementsMixin
    from pydoll.elements.web_element import WebElement

logger = logging.getLogger(__name__)

T = TypeVar('T', bound='ExtractionModel')


class ExtractionEngine:
    """Orchestrates extraction by querying the DOM and building model instances.

    Internal engine used by Tab.extract() and Tab.extract_all().
    Users do not interact with it directly.
    """

    def __init__(self, tab: Tab) -> None:
        self._tab = tab

    async def extract(
        self,
        model: type[T],
        *,
        scope: Optional[str] = None,
        timeout: int = 0,
    ) -> T:
        """Extract a single model instance from the page.

        Args:
            model: ExtractionModel subclass to populate.
            scope: Optional CSS/XPath selector to limit extraction region.
            timeout: Seconds to wait for elements to appear (0 = no wait).

        Returns:
            Populated model instance.

        Raises:
            FieldExtractionFailed: If a required field cannot be extracted.
        """
        context: FindElementsMixin = self._tab
        if scope is not None:
            context = await self._tab.query(scope, timeout=timeout)

        values = await self._extract_fields(model, context, timeout)
        return _build_instance(model, values)

    async def extract_all(
        self,
        model: type[T],
        *,
        scope: str,
        timeout: int = 0,
        limit: Optional[int] = None,
    ) -> list[T]:
        """Extract multiple model instances from repeated containers.

        Each element matching scope generates one model instance.

        Args:
            model: ExtractionModel subclass to populate.
            scope: CSS/XPath selector for the repeated container (required).
            timeout: Seconds to wait for elements to appear (0 = no wait).
            limit: Maximum number of items to extract (None = all).

        Returns:
            List of populated model instances.
        """
        containers = await self._tab.query(scope, find_all=True, timeout=timeout, raise_exc=False)
        if not containers:
            return []

        if limit is not None:
            containers = containers[:limit]

        results: list[T] = []
        for container in containers:
            values = await self._extract_fields(model, container, timeout)
            results.append(_build_instance(model, values))

        return results

    async def _extract_fields(
        self,
        model: type[T],
        context: FindElementsMixin,
        timeout: int,
    ) -> dict[str, str | list[str] | object]:
        """Extract all fields from the DOM within the given context.

        Args:
            model: ExtractionModel subclass with extraction fields.
            context: Tab or WebElement to scope queries within.
            timeout: Seconds to wait for each element to appear.

        Returns:
            Dictionary of field name -> extracted value.
        """
        values: dict[str, str | list[str] | object] = {}

        for name, metadata in model.get_extraction_fields().items():
            if not metadata.has_selector:
                logger.debug(f'Skipping field "{name}" (no selector)')
                continue

            field_info = model.model_fields[name]
            annotation = field_info.annotation

            try:
                value = await self._extract_field(metadata, annotation, context, timeout)
                values[name] = value
            except Exception as exc:
                if not field_info.is_required():
                    logger.debug(f'Optional field "{name}" extraction failed: {exc}')
                    continue
                raise FieldExtractionFailed(
                    f'Required field "{name}" could not be extracted: {exc}'
                ) from exc

        return values

    async def _extract_field(
        self,
        metadata: ExtractionMetadata,
        annotation: type,
        context: FindElementsMixin,
        timeout: int,
    ) -> str | list[str] | object:
        """Extract a single field value from the DOM.

        Handles scalar types, list types, nested ExtractionModel,
        and list[ExtractionModel].

        Args:
            metadata: Extraction metadata with selector/attribute/transform.
            annotation: The field's resolved type annotation.
            context: Tab or WebElement to query within.
            timeout: Seconds to wait for the element to appear.

        Returns:
            Extracted and optionally transformed value.
        """
        unwrapped = _unwrap_optional(annotation)

        if _is_list_type(unwrapped):
            return await self._extract_list_field(metadata, unwrapped, context, timeout)

        if _is_extraction_model(unwrapped):
            return await self._extract_nested_model(metadata, unwrapped, context, timeout)

        return await _extract_scalar_field(metadata, context, timeout)

    async def _extract_list_field(
        self,
        metadata: ExtractionMetadata,
        annotation: type,
        context: FindElementsMixin,
        timeout: int,
    ) -> list[Union[str, int, float, bool, object]]:
        """Extract a list of values from multiple matching elements."""
        elements = await context.query(
            metadata.selector, find_all=True, timeout=timeout, raise_exc=False
        )
        if not elements:
            return []

        inner_type = _get_inner_type(annotation)

        if _is_extraction_model(inner_type):
            results: list[Union[str, int, float, bool, object]] = []
            for element in elements:
                field_values = await self._extract_fields(inner_type, element, timeout)
                results.append(_build_instance(inner_type, field_values))
            return results

        scalar_values: list[Union[str, int, float, bool, object]] = []
        for element in elements:
            raw = await _extract_value(element, metadata)
            scalar_values.append(_apply_transform(raw, metadata))
        return scalar_values

    async def _extract_nested_model(
        self,
        metadata: ExtractionMetadata,
        model: type[T],
        context: FindElementsMixin,
        timeout: int,
    ) -> T:
        """Extract a nested ExtractionModel by scoping to the selector element."""
        scope_element = await context.query(metadata.selector, timeout=timeout, raise_exc=True)
        values = await self._extract_fields(model, scope_element, timeout)
        return _build_instance(model, values)


async def _extract_scalar_field(
    metadata: ExtractionMetadata,
    context: FindElementsMixin,
    timeout: int,
) -> Union[str, int, float, bool]:
    """Extract a single scalar value from the DOM."""
    element = await context.query(metadata.selector, timeout=timeout, raise_exc=True)
    raw = await _extract_value(element, metadata)
    return _apply_transform(raw, metadata)


async def _extract_value(
    element: WebElement,
    metadata: ExtractionMetadata,
) -> str:
    """Read raw string value from a WebElement.

    If metadata.attribute is set, reads that HTML attribute.
    Otherwise reads element.text (innerText).

    Args:
        element: WebElement to read from.
        metadata: Field metadata with optional attribute name.

    Returns:
        Raw string value before transform.
    """
    if metadata.attribute is not None:
        return element.get_attribute(metadata.attribute) or ''
    return await element.text


def _apply_transform(
    raw: str,
    metadata: ExtractionMetadata,
) -> Union[str, int, float, bool]:
    """Apply metadata.transform to the raw extracted string.

    Args:
        raw: Raw string from the DOM.
        metadata: Field metadata with optional transform callable.

    Returns:
        Transformed value, or raw string if no transform.
    """
    if metadata.transform is not None:
        return metadata.transform(raw)
    return raw


def _build_instance(
    model: type[T],
    values: dict[str, str | list[str] | object],
) -> T:
    """Build model instance from extracted values.

    Pydantic handles validation, type coercion, and defaults.

    Args:
        model: ExtractionModel subclass.
        values: Field name -> value mapping.

    Returns:
        Populated model instance.

    Raises:
        FieldExtractionFailed: If pydantic validation fails.
    """
    try:
        return model(**values)
    except Exception as exc:
        raise FieldExtractionFailed(f'Failed to build {model.__name__}: {exc}') from exc


def _unwrap_optional(annotation: type) -> type:
    """Unwrap Optional[X] or X | None to X. Returns annotation unchanged otherwise.

    Handles both typing.Optional (Union) and PEP 604 syntax (types.UnionType).
    """
    origin = get_origin(annotation)
    if origin is Union or isinstance(annotation, types.UnionType):
        args = get_args(annotation)
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1:
            return non_none[0]
    return annotation


def _is_list_type(annotation: type) -> bool:
    """Check if annotation is list[X]."""
    return get_origin(annotation) is list


def _get_inner_type(annotation: type) -> type:
    """Get X from list[X]."""
    args = get_args(annotation)
    if args:
        return args[0]
    return str


def _is_extraction_model(annotation: type) -> bool:
    """Check if annotation is an ExtractionModel subclass."""
    try:
        return isinstance(annotation, type) and issubclass(annotation, ExtractionModel)
    except TypeError:
        return False
