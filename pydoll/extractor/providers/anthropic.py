"""Anthropic LLM provider for extraction using the Messages API.

Uses aiohttp to call the Anthropic API directly — no SDK required.
Supports structured output via ``tool_use`` with forced tool choice.

Example::

    from pydoll.extractor.providers.anthropic import AnthropicProvider

    provider = AnthropicProvider(api_key='sk-ant-...')
    article = await tab.extract(Article, llm_provider=provider)
"""

from __future__ import annotations

import json

import aiohttp

from pydoll.extractor.exceptions import LLMExtractionFailed

_ANTHROPIC_VERSION = '2023-06-01'
_TOOL_NAME = 'extract_data'
_DEFAULT_TIMEOUT = 120
_DEFAULT_MAX_TOKENS = 4096


class AnthropicProvider:
    """LLM provider using Anthropic's Messages API.

    Uses the tool_use pattern for structured output: defines a tool
    whose ``input_schema`` is the extraction schema, then forces Claude
    to call it via ``tool_choice``.

    Args:
        api_key: Anthropic API key.
        model: Model name (default: claude-sonnet-4-5-20250514).
        base_url: API base URL.
        max_tokens: Maximum tokens in the response.
        timeout: Request timeout in seconds (default: 120).
    """

    def __init__(
        self,
        *,
        api_key: str,
        model: str = 'claude-sonnet-4-5-20250514',
        base_url: str = 'https://api.anthropic.com',
        max_tokens: int = _DEFAULT_MAX_TOKENS,
        timeout: int = _DEFAULT_TIMEOUT,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip('/')
        self._max_tokens = max_tokens
        self._timeout = aiohttp.ClientTimeout(total=timeout)

    def __repr__(self) -> str:
        return f'AnthropicProvider(model={self._model!r}, base_url={self._base_url!r})'

    async def complete(
        self,
        prompt: str,
        schema: dict[str, object],
    ) -> dict[str, object]:
        """Send prompt to Anthropic and return structured extraction result.

        Uses ``tool_use`` with ``tool_choice`` to force structured output.
        The schema is passed as the tool's ``input_schema``.

        Args:
            prompt: Complete extraction prompt with HTML and instructions.
            schema: JSON Schema for the expected output.

        Returns:
            Dictionary with extracted field values.

        Raises:
            LLMExtractionFailed: On HTTP error or malformed response.
        """
        payload = {
            'model': self._model,
            'max_tokens': self._max_tokens,
            'messages': [{'role': 'user', 'content': prompt}],
            'tools': [
                {
                    'name': _TOOL_NAME,
                    'description': 'Extract structured data from HTML content',
                    'input_schema': schema,
                },
            ],
            'tool_choice': {'type': 'tool', 'name': _TOOL_NAME},
        }
        headers = {
            'x-api-key': self._api_key,
            'anthropic-version': _ANTHROPIC_VERSION,
            'content-type': 'application/json',
        }
        return await self._request(payload, headers)

    async def _request(
        self,
        payload: dict[str, object],
        headers: dict[str, str],
    ) -> dict[str, object]:
        """Execute HTTP request and parse response."""
        url = f'{self._base_url}/v1/messages'
        async with aiohttp.ClientSession(timeout=self._timeout) as session:
            async with session.post(url, json=payload, headers=headers) as resp:
                body = await resp.text()
                if not resp.ok:
                    raise LLMExtractionFailed(
                        f'Anthropic API error {resp.status}: {body}'
                    )
                return self._parse_response(body)

    @staticmethod
    def _parse_response(body: str) -> dict[str, object]:
        """Extract structured data from Anthropic tool_use response."""
        try:
            data = json.loads(body)
            for block in data['content']:
                if block.get('type') == 'tool_use':
                    return block['input']
            raise LLMExtractionFailed(
                'No tool_use block found in Anthropic response'
            )
        except (json.JSONDecodeError, KeyError) as exc:
            raise LLMExtractionFailed(
                f'Failed to parse Anthropic response: {exc}'
            ) from exc
