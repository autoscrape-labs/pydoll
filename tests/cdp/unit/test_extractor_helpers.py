"""Pure-logic tests for the extractor's typing-introspection helpers."""

from __future__ import annotations

from typing import Optional, Union

from pydoll.extractor import ExtractionModel, Field
from pydoll.extractor.engine import (
    _get_inner_type,
    _is_extraction_model,
    _is_list_type,
    _unwrap_optional,
)


class _Sample(ExtractionModel):
    title: str = Field(selector='h1')


def test_unwrap_optional_unwraps_single_member():
    assert _unwrap_optional(Optional[str]) is str
    assert _unwrap_optional(str | None) is str
    assert _unwrap_optional(str) is str


def test_unwrap_optional_leaves_multi_member_union_unchanged():
    annotation = Union[str, int]
    assert _unwrap_optional(annotation) == annotation


def test_is_list_type():
    assert _is_list_type(list[str]) is True
    assert _is_list_type(list) is False
    assert _is_list_type(str) is False


def test_get_inner_type():
    assert _get_inner_type(list[str]) is str
    assert _get_inner_type(list) is str


def test_is_extraction_model():
    assert _is_extraction_model(_Sample) is True
    assert _is_extraction_model(str) is False
    assert _is_extraction_model(Optional[str]) is False
