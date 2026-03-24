"""LLM provider protocol, extraction strategy enum, and helpers."""

from __future__ import annotations

import json
from enum import Enum
from typing import Protocol, runtime_checkable

from pydoll.extractor.field import ExtractionMetadata
from pydoll.extractor.model import ExtractionModel


class ExtractionStrategy(str, Enum):
    """Strategy used to extract data from the page.

    Attributes:
        CSS: Extract using CSS/XPath selectors only. Fast and deterministic.
            Fields without selectors are skipped.
        LLM: Extract using LLM only. All fields with descriptions are sent
            to the LLM provider. Selectors are ignored.
        AUTO: Selectors first, LLM for description-only fields.
            Combines speed of CSS with flexibility of LLM.
    """

    CSS = 'css'
    LLM = 'llm'
    AUTO = 'auto'


@runtime_checkable
class LLMProvider(Protocol):
    """Protocol for LLM providers used in extraction.

    Any object implementing ``complete()`` works — no inheritance needed.
    Pydoll ships built-in providers for OpenAI and Anthropic in
    ``pydoll.extractor.providers``, but you can use any LLM by
    implementing this single method.

    Example::

        class MyLocalLLM:
            async def complete(
                self, prompt: str, schema: dict[str, object],
            ) -> dict[str, object]:
                resp = await my_client.post(url, json={'prompt': prompt})
                return resp.json()

        article = await tab.extract(Article, llm_provider=MyLocalLLM())
    """

    async def complete(
        self,
        prompt: str,
        schema: dict[str, object],
    ) -> dict[str, object]:
        """Send extraction prompt to LLM and return structured data.

        Args:
            prompt: Complete prompt with HTML content and extraction instructions.
            schema: JSON Schema describing the expected output structure.

        Returns:
            Dictionary with extracted field values matching the schema.
        """
        ...

_EXTRACTION_PROMPT = (
    'Extract structured data from the following HTML content.\n'
    'Return a JSON object matching the provided schema exactly.\n'
    'Only include data that is explicitly present in the HTML.\n'
    'If a field value cannot be found, use null.\n'
    '\n'
    'JSON Schema:\n'
    '{schema}\n'
    '\n'
    'HTML Content:\n'
    '{html}'
)

def build_field_schema(
    model: type[ExtractionModel],
    field_names: list[str],
) -> dict[str, object]:
    """Build JSON Schema for specific fields using pydantic.

    Filters ``model.model_json_schema()`` to include only the requested
    fields. Adds ``additionalProperties: false`` on every object for
    OpenAI structured output compatibility.

    Args:
        model: ExtractionModel subclass.
        field_names: Names of fields to include in the schema.

    Returns:
        JSON Schema dict ready to send to an LLM provider.
    """
    full_schema = model.model_json_schema()
    properties = full_schema.get('properties', {})
    original_required = set(full_schema.get('required', []))
    filtered_properties: dict[str, object] = {}
    for name in field_names:
        if name not in properties:
            continue
        prop = dict(properties[name])
        if name not in original_required:
            prop = _make_nullable(prop)
        filtered_properties[name] = prop
    schema: dict[str, object] = {
        'type': 'object',
        'properties': filtered_properties,
        'required': list(filtered_properties.keys()),
        'additionalProperties': False,
    }
    if '$defs' in full_schema:
        schema['$defs'] = full_schema['$defs']
    return schema



def _make_nullable(prop: dict[str, object]) -> dict[str, object]:
    """Make a JSON Schema property nullable for strict mode compatibility.

    OpenAI strict mode requires all properties in ``required``.
    Optional fields are represented with ``anyOf: [original, null]``.
    """
    if 'anyOf' in prop:
        types = prop['anyOf']
        if not isinstance(types, list):
            return prop
        has_null = any(
            isinstance(t, dict) and t.get('type') == 'null' for t in types
        )
        if has_null:
            return prop
        return {**prop, 'anyOf': [*types, {'type': 'null'}]}
    return {'anyOf': [prop, {'type': 'null'}]}


def build_extraction_prompt(
    html: str,
    schema: dict[str, object],
) -> str:
    """Build extraction prompt with clean HTML and JSON schema.

    Args:
        html: Clean HTML content (boilerplate already removed).
        schema: JSON Schema for the expected output.

    Returns:
        Complete prompt string ready to send to an LLM provider.
    """
    return _EXTRACTION_PROMPT.format(
        schema=json.dumps(schema, indent=2),
        html=html,
    )


def apply_transforms(
    raw: dict[str, object],
    fields: dict[str, ExtractionMetadata],
) -> dict[str, object]:
    """Apply field transforms to LLM output values.

    Only includes fields that were requested (filters out extra keys
    the LLM may have hallucinated). Transforms receive the raw value
    as-is — for scalar fields this is typically a string, for structured
    fields it may be a list or dict.

    Args:
        raw: Raw dictionary returned by the LLM provider.
        fields: Field metadata with optional transforms.

    Returns:
        Dictionary with transforms applied, filtered to requested fields.
    """
    result: dict[str, object] = {}
    for name, metadata in fields.items():
        if name not in raw:
            continue
        value = raw[name]
        if metadata.transform is not None:
            result[name] = metadata.transform(str(value))
        else:
            result[name] = value
    return result
