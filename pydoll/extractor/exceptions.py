"""Exception classes for the extractor module."""

from __future__ import annotations

from pydoll.exceptions import PydollException


class ExtractionException(PydollException):
    """Base class for exceptions related to data extraction."""

    message = 'An extraction error occurred'


class FieldExtractionFailed(ExtractionException):
    """Raised when a required field cannot be extracted and has no default."""

    message = 'Failed to extract required field'


class InvalidExtractionModel(ExtractionException):
    """Raised when an ExtractionModel definition is invalid."""

    message = 'Invalid extraction model definition'


class LLMExtractionFailed(ExtractionException):
    """Raised when LLM-based extraction fails (provider error, bad response)."""

    message = 'LLM extraction failed'


class LLMProviderNotConfigured(ExtractionException):
    """Raised when description-only fields exist but no LLM provider was given."""

    message = 'No LLM provider configured for description-only fields'
