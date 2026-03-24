"""Extraction engine that orchestrates DOM querying and model building."""

from __future__ import annotations

import asyncio
import logging
import types
from collections.abc import Coroutine
from typing import TYPE_CHECKING, Optional, TypeVar, Union, get_args, get_origin

from pydoll.elements.mixins.find_elements_mixin import FindElementsMixin
from pydoll.elements.web_element import WebElement
from pydoll.extractor.exceptions import (
    FieldExtractionFailed,
    LLMExtractionFailed,
    LLMProviderNotConfigured,
)
from pydoll.extractor.field import ExtractionMetadata
from pydoll.extractor.llm import (
    ExtractionStrategy,
    LLMProvider,
    apply_transforms,
    build_extraction_prompt,
    build_field_schema,
)
from pydoll.extractor.model import ExtractionModel
from pydoll.utils.html_to_markdown import clean_html

if TYPE_CHECKING:
    from pydoll.browser.tab import Tab

logger = logging.getLogger(__name__)

T = TypeVar('T', bound='ExtractionModel')


class ExtractionEngine:
    """Orchestrates extraction by querying the DOM and building model instances.

    Internal engine used by Tab.extract() and Tab.extract_all().
    Users do not interact with it directly.
    """

    def __init__(self, tab: Tab) -> None:
        self._tab = tab
        self._llm_provider: Optional[LLMProvider] = None
        self._extraction_strategy: ExtractionStrategy = ExtractionStrategy.CSS

    @property
    def llm_provider(self) -> Optional[LLMProvider]:
        """Default LLM provider for description-only fields."""
        return self._llm_provider

    @llm_provider.setter
    def llm_provider(self, provider: Optional[LLMProvider]) -> None:
        self._llm_provider = provider

    @property
    def extraction_strategy(self) -> ExtractionStrategy:
        """Default extraction strategy."""
        return self._extraction_strategy

    @extraction_strategy.setter
    def extraction_strategy(self, strategy: ExtractionStrategy) -> None:
        self._extraction_strategy = strategy

    async def extract(
        self,
        model: type[T],
        *,
        scope: Optional[str] = None,
        timeout: int = 0,
        llm_provider: Optional[LLMProvider] = None,
        strategy: Optional[ExtractionStrategy] = None,
    ) -> T:
        """Extract a single model instance from the page.

        Args:
            model: ExtractionModel subclass to populate.
            scope: Optional CSS/XPath selector to limit extraction region.
            timeout: Seconds to wait for elements to appear (0 = no wait).
            llm_provider: LLM provider override for this call.
                Falls back to ``tab.llm_provider``.
            strategy: Extraction strategy override for this call.
                Falls back to ``tab.extraction_strategy`` (default: CSS).

        Returns:
            Populated model instance.

        Raises:
            FieldExtractionFailed: If a required field cannot be extracted.
            LLMProviderNotConfigured: If LLM-dependent fields exist
                but no LLM provider is available.
        """
        resolved_provider = llm_provider or self._llm_provider
        resolved_strategy = strategy or self._extraction_strategy
        validate_llm_provider(model, resolved_provider, resolved_strategy)

        context: FindElementsMixin = self._tab
        if scope is not None:
            result = await self._tab.query(scope, timeout=timeout)
            if not isinstance(result, WebElement):
                raise ValueError(
                    f'Expected a single element for scope "{scope}", got {type(result)}'
                )
            context = result

        values = await self._extract_fields(
            model, context, timeout, resolved_provider, resolved_strategy,
        )
        return _build_instance(model, values)

    async def extract_all(
        self,
        model: type[T],
        *,
        scope: str,
        timeout: int = 0,
        limit: Optional[int] = None,
        llm_provider: Optional[LLMProvider] = None,
        strategy: Optional[ExtractionStrategy] = None,
    ) -> list[T]:
        """Extract multiple model instances from the page.

        Each element matching ``scope`` generates one model instance.
        Fields are resolved relative to each container (DOM or LLM per item).

        Args:
            model: ExtractionModel subclass to populate.
            scope: CSS/XPath selector for repeated containers.
            timeout: Seconds to wait for elements to appear (0 = no wait).
            limit: Maximum number of items to extract (None = all).
            llm_provider: LLM provider override for this call.
                Falls back to ``tab.llm_provider``.
            strategy: Extraction strategy override for this call.
                Falls back to ``tab.extraction_strategy`` (default: CSS).

        Returns:
            List of populated model instances.
        """
        resolved_provider = llm_provider or self._llm_provider
        resolved_strategy = strategy or self._extraction_strategy
        validate_llm_provider(model, resolved_provider, resolved_strategy)

        return await self._extract_all_with_scope(
            model, scope, timeout, limit,
            resolved_provider, resolved_strategy,
        )

    async def _extract_all_with_scope(
        self,
        model: type[T],
        scope: str,
        timeout: int,
        limit: Optional[int],
        llm_provider: Optional[LLMProvider],
        strategy: ExtractionStrategy,
    ) -> list[T]:
        """Extract multiple items using scope containers."""
        found = await self._tab.query(
            scope, find_all=True, timeout=timeout, raise_exc=False,
        )
        if found is None or not found:
            return []

        containers: list[WebElement] = (
            found if isinstance(found, list) else [found]
        )
        if limit is not None:
            containers = containers[:limit]

        extraction_tasks = [
            self._extract_fields(
                model, container, timeout, llm_provider, strategy,
            )
            for container in containers
        ]
        all_values = await asyncio.gather(*extraction_tasks)
        return [_build_instance(model, values) for values in all_values]

    async def _extract_fields(
        self,
        model: type[T],
        context: FindElementsMixin,
        timeout: int,
        llm_provider: Optional[LLMProvider] = None,
        strategy: ExtractionStrategy = ExtractionStrategy.CSS,
    ) -> dict[str, Union[str, int, float, bool, list[str], object]]:
        """Extract fields according to the chosen strategy.

        - CSS: selector fields via DOM only.
        - LLM: all fields with descriptions via LLM only.
        - AUTO: selector fields via DOM, description-only fields via LLM.

        Args:
            model: ExtractionModel subclass with extraction fields.
            context: Tab or WebElement to scope queries within.
            timeout: Seconds to wait for each element to appear.
            llm_provider: Optional LLM provider.
            strategy: Extraction strategy to use.

        Returns:
            Dictionary of field name -> extracted value.
        """
        all_fields = model.get_extraction_fields()

        if strategy == ExtractionStrategy.LLM:
            return await self._extract_llm_fields(
                model, all_fields, context, llm_provider,
            )

        values = await self._extract_selector_fields(
            model, all_fields, context, timeout,
        )
        if strategy == ExtractionStrategy.AUTO:
            llm_values = await self._extract_description_fields(
                model, all_fields, context, llm_provider,
            )
            values.update(llm_values)

        return values

    async def _extract_selector_fields(
        self,
        model: type[T],
        all_fields: dict[str, ExtractionMetadata],
        context: FindElementsMixin,
        timeout: int,
    ) -> dict[str, Union[str, int, float, bool, list[str], object]]:
        """Extract fields that have selectors via DOM queries."""
        field_names: list[str] = []
        coroutines: list[
            Coroutine[None, None, Union[str, int, float, bool, list[str], object]]
        ] = []

        for name, metadata in all_fields.items():
            if not metadata.has_selector:
                continue
            field_info = model.model_fields[name]
            annotation = field_info.annotation
            if annotation is None:
                continue
            field_names.append(name)
            coroutines.append(
                self._extract_field(metadata, annotation, context, timeout),
            )

        results = await asyncio.gather(*coroutines, return_exceptions=True)

        values: dict[str, Union[str, int, float, bool, list[str], object]] = {}
        for name, result in zip(field_names, results):
            if isinstance(result, BaseException):
                field_info = model.model_fields[name]
                if not field_info.is_required():
                    logger.debug(
                        f'Optional field "{name}" extraction failed: {result}',
                    )
                    continue
                raise FieldExtractionFailed(
                    f'Required field "{name}" could not be extracted: {result}'
                ) from result
            values[name] = result
        return values

    async def _extract_llm_fields(
        self,
        model: type[T],
        all_fields: dict[str, ExtractionMetadata],
        context: FindElementsMixin,
        llm_provider: Optional[LLMProvider],
    ) -> dict[str, object]:
        """Extract ALL fields with descriptions via LLM (full LLM strategy).

        Unlike ``_extract_description_fields`` which only sends fields
        without selectors, this sends every field that has a description,
        regardless of whether it also has a selector.
        """
        llm_fields = {
            name: meta for name, meta in all_fields.items()
            if model.model_fields[name].description
        }
        if not llm_fields or llm_provider is None:
            return {}
        return await self._call_llm_provider(model, llm_fields, context, llm_provider)

    async def _extract_description_fields(
        self,
        model: type[T],
        all_fields: dict[str, ExtractionMetadata],
        context: FindElementsMixin,
        llm_provider: Optional[LLMProvider],
    ) -> dict[str, object]:
        """Extract description-only fields (no selector) via LLM."""
        description_fields = collect_description_fields(model, all_fields)
        if not description_fields or llm_provider is None:
            return {}
        return await self._call_llm_provider(
            model, description_fields, context, llm_provider,
        )

    async def _call_llm_provider(
        self,
        model: type[T],
        fields: dict[str, ExtractionMetadata],
        context: FindElementsMixin,
        provider: LLMProvider,
    ) -> dict[str, object]:
        """Execute LLM extraction for a set of fields."""
        html = await self._get_context_html(context)
        cleaned = clean_html(html)
        schema = build_field_schema(model, list(fields.keys()))
        prompt = build_extraction_prompt(cleaned, schema)

        try:
            raw_result = await provider.complete(prompt, schema)
        except LLMExtractionFailed:
            raise  # Don't wrap provider's own LLMExtractionFailed
        except Exception as exc:
            raise LLMExtractionFailed(
                f'LLM provider failed: {exc}'
            ) from exc

        return apply_transforms(raw_result, fields)

    async def _get_context_html(self, context: FindElementsMixin) -> str:
        """Get HTML content from the extraction context."""
        if isinstance(context, WebElement):
            return await context.inner_html
        return await self._tab.page_source

    async def _extract_field(
        self,
        metadata: ExtractionMetadata,
        annotation: type,
        context: FindElementsMixin,
        timeout: int,
    ) -> Union[str, int, float, bool, list[str], object]:
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
        selector = metadata.selector
        if selector is None:
            return []

        found = await context.query(selector, find_all=True, timeout=timeout, raise_exc=False)
        if found is None or not found:
            return []

        elements: list[WebElement] = found if isinstance(found, list) else [found]
        inner_type = _get_inner_type(annotation)

        if _is_extraction_model(inner_type):
            all_field_values = await asyncio.gather(
                *(self._extract_fields(inner_type, el, timeout) for el in elements)
            )
            return [_build_instance(inner_type, fv) for fv in all_field_values]

        all_raw = await asyncio.gather(*(_extract_value(el, metadata) for el in elements))
        return [_apply_transform(raw, metadata) for raw in all_raw]

    async def _extract_nested_model(
        self,
        metadata: ExtractionMetadata,
        model: type[T],
        context: FindElementsMixin,
        timeout: int,
    ) -> T:
        """Extract a nested ExtractionModel by scoping to the selector element."""
        selector = metadata.selector
        if selector is None:
            raise FieldExtractionFailed('Nested model field has no selector')

        result = await context.query(selector, timeout=timeout, raise_exc=True)
        if not isinstance(result, WebElement):
            raise ValueError(f'Expected a single element for "{selector}", got {type(result)}')
        values = await self._extract_fields(model, result, timeout)
        return _build_instance(model, values)


async def _extract_scalar_field(
    metadata: ExtractionMetadata,
    context: FindElementsMixin,
    timeout: int,
) -> Union[str, int, float, bool, object]:
    """Extract a single scalar value from the DOM."""
    selector = metadata.selector
    if selector is None:
        raise FieldExtractionFailed('Scalar field has no selector')

    result = await context.query(selector, timeout=timeout, raise_exc=True)
    if not isinstance(result, WebElement):
        raise ValueError(f'Expected a single element for "{selector}", got {type(result)}')
    raw = await _extract_value(result, metadata)
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
) -> Union[str, int, float, bool, object]:
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
    values: dict[str, Union[str, int, float, bool, list[str], object]],
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


def validate_llm_provider(
    model: type[ExtractionModel],
    provider: Optional[LLMProvider],
    strategy: ExtractionStrategy = ExtractionStrategy.CSS,
) -> None:
    """Fail fast if strategy requires LLM but no provider is available.

    - CSS strategy: validates that description-only required fields have a provider.
    - LLM strategy: always requires a provider.
    - AUTO strategy: validates that description-only required fields have a provider.

    Raises:
        LLMProviderNotConfigured: If LLM is needed but no provider is available.
    """
    if provider is not None:
        return
    if strategy == ExtractionStrategy.LLM:
        raise LLMProviderNotConfigured(
            'Strategy is LLM but no provider is available. '
            'Set tab.llm_provider or pass llm_provider= to extract().'
        )
    # CSS and AUTO: only fail if there are required description-only fields
    description_fields = collect_description_fields(
        model, model.get_extraction_fields(),
    )
    required_names = [
        name for name in description_fields
        if model.model_fields[name].is_required()
    ]
    if required_names:
        raise LLMProviderNotConfigured(
            f'Fields {required_names} require an LLM provider '
            f'(description-only, no selector). '
            f'Set tab.llm_provider or pass llm_provider= to extract().'
        )


def collect_description_fields(
    model: type[ExtractionModel],
    all_fields: dict[str, ExtractionMetadata],
) -> dict[str, ExtractionMetadata]:
    """Collect fields that have a description but no selector."""
    result: dict[str, ExtractionMetadata] = {}
    for name, metadata in all_fields.items():
        if metadata.has_selector:
            continue
        field_info = model.model_fields[name]
        if field_info.description:
            result[name] = metadata
    return result
