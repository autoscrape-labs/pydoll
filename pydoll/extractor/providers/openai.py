"""OpenAI LLM provider for extraction using the Chat Completions API.

Uses aiohttp to call the OpenAI API directly — no SDK required.
Supports structured output via ``response_format`` with ``json_schema``.

Compatible with any OpenAI-compatible endpoint (Azure, local LLMs, etc.)
by setting ``base_url``.

Example::

    from pydoll.extractor.providers.openai import OpenAIProvider

    provider = OpenAIProvider(api_key='sk-...')
    article = await tab.extract(Article, llm_provider=provider)
"""

from __future__ import annotations

import json

import aiohttp

from pydoll.extractor.exceptions import LLMExtractionFailed

_DEFAULT_TIMEOUT = 120


class OpenAIProvider:
    """LLM provider using OpenAI's Chat Completions API.

    Args:
        api_key: OpenAI API key.
        model: Model name (default: gpt-4o-mini).
        base_url: API base URL. Change for Azure or compatible endpoints.
        timeout: Request timeout in seconds (default: 120).
    """

    def __init__(
        self,
        *,
        api_key: str,
        model: str = 'gpt-4o-mini',
        base_url: str = 'https://api.openai.com/v1',
        timeout: int = _DEFAULT_TIMEOUT,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip('/')
        self._timeout = aiohttp.ClientTimeout(total=timeout)

    def __repr__(self) -> str:
        return f'OpenAIProvider(model={self._model!r}, base_url={self._base_url!r})'

    async def complete(
        self,
        prompt: str,
        schema: dict[str, object],
    ) -> dict[str, object]:
        """Send prompt to OpenAI and return structured extraction result.

        Uses ``response_format`` with ``json_schema`` for guaranteed
        schema conformance (structured outputs).

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
            'messages': [{'role': 'user', 'content': prompt}],
            'response_format': {
                'type': 'json_schema',
                'json_schema': {
                    'name': 'extraction',
                    'strict': True,
                    'schema': schema,
                },
            },
        }
        headers = {
            'Authorization': f'Bearer {self._api_key}',
            'Content-Type': 'application/json',
        }
        return await self._request(payload, headers)

    async def _request(
        self,
        payload: dict[str, object],
        headers: dict[str, str],
    ) -> dict[str, object]:
        """Execute HTTP request and parse response."""
        url = f'{self._base_url}/chat/completions'
        async with aiohttp.ClientSession(timeout=self._timeout) as session:
            async with session.post(url, json=payload, headers=headers) as resp:
                body = await resp.text()
                if not resp.ok:
                    raise LLMExtractionFailed(
                        f'OpenAI API error {resp.status}: {body}'
                    )
                return self._parse_response(body)

    @staticmethod
    def _parse_response(body: str) -> dict[str, object]:
        """Extract structured data from OpenAI response."""
        try:
            data = json.loads(body)
            content = data['choices'][0]['message']['content']
            return json.loads(content)
        except (json.JSONDecodeError, KeyError, IndexError) as exc:
            raise LLMExtractionFailed(
                f'Failed to parse OpenAI response: {exc}'
            ) from exc
