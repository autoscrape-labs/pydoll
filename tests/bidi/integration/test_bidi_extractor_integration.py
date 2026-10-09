"""Real-Firefox (WebDriver BiDi) integration tests for tab.extract / extract_all.

The same ExtractionEngine that powers CDP now drives BiDi (it only uses query +
get_attribute + text, all protocol-agnostic). Exercised against the shared
test_extractor.html — the BiDi counterpart of
tests/cdp/integration/test_extractor_integration.py.
"""

from __future__ import annotations

import pytest

from pydoll.extractor import ExtractionModel, Field


class SimpleArticle(ExtractionModel):
    title: str = Field(selector='h1.article-title', description='Title')
    body: str = Field(selector='.article-body', description='Body text')


class ArticleWithDate(ExtractionModel):
    title: str = Field(selector='h1.article-title', description='Title')
    published_at: str = Field(
        selector='time.published', attribute='datetime', description='Publication date'
    )


class ArticleWithTags(ExtractionModel):
    title: str = Field(selector='h1.article-title', description='Title')
    tags: list[str] = Field(selector='.tag', description='Tags')


class Quote(ExtractionModel):
    text: str = Field(selector='.text', description='Quote text')
    author: str = Field(selector='.author', description='Author')


@pytest.mark.asyncio(loop_scope='module')
async def test_extract_simple_fields(tab, page_url):
    await tab.go_to(page_url('test_extractor.html'))
    article = await tab.extract(SimpleArticle, timeout=5)
    assert article.title == 'Understanding Web Scraping'
    assert 'extracting data' in article.body


@pytest.mark.asyncio(loop_scope='module')
async def test_extract_attribute(tab, page_url):
    await tab.go_to(page_url('test_extractor.html'))
    article = await tab.extract(ArticleWithDate, timeout=5)
    assert article.published_at == '2025-03-15'


@pytest.mark.asyncio(loop_scope='module')
async def test_extract_list_field(tab, page_url):
    await tab.go_to(page_url('test_extractor.html'))
    article = await tab.extract(ArticleWithTags, timeout=5)
    assert article.tags == ['python', 'automation', 'web']


@pytest.mark.asyncio(loop_scope='module')
async def test_extract_all_repeated_containers(tab, page_url):
    await tab.go_to(page_url('test_extractor.html'))
    quotes = await tab.extract_all(Quote, scope='.quote', timeout=5)
    assert len(quotes) >= 2
    assert all(q.text for q in quotes)
