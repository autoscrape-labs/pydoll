"""Integration tests for the extractor module using a real browser."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

import pytest

from pydoll.browser.chromium import Chrome
from pydoll.extractor import (
    ExtractionModel,
    Field,
    FieldExtractionFailed,
    InvalidExtractionModel,
)

TEST_PAGE = Path(__file__).parent.parent / 'pages' / 'test_extractor.html'
FILE_URL = f'file://{TEST_PAGE.absolute()}'


# ---------------------------------------------------------------------------
# Model definitions
# ---------------------------------------------------------------------------


def parse_price(raw: str) -> float:
    """Parse Brazilian currency format to float."""
    return float(raw.replace('R$', '').replace('.', '').replace(',', '.').strip())


class SimpleArticle(ExtractionModel):
    title: str = Field(selector='h1.article-title', description='Title')
    body: str = Field(selector='.article-body', description='Body text')


class ArticleWithAttributes(ExtractionModel):
    title: str = Field(selector='h1.article-title', description='Title')
    published_at: str = Field(
        selector='time.published',
        attribute='datetime',
        description='Publication date',
    )
    image_src: str = Field(
        selector='.hero-image',
        attribute='src',
        description='Hero image URL',
    )
    image_alt: str = Field(
        selector='.hero-image',
        attribute='alt',
        description='Hero image alt text',
    )
    image_data_id: str = Field(
        selector='.hero-image',
        attribute='data-id',
        description='Hero image data-id',
    )
    link_href: str = Field(
        selector='.source-link',
        attribute='href',
        description='Source link URL',
    )


class ArticleWithTags(ExtractionModel):
    title: str = Field(selector='h1.article-title', description='Title')
    tags: list[str] = Field(selector='.tag-list .tag', description='Tags')


class ArticleWithTransform(ExtractionModel):
    title: str = Field(selector='h1.article-title', description='Title')
    price: float = Field(
        selector='.price',
        description='Product price in BRL',
        transform=parse_price,
    )


class AuthorModel(ExtractionModel):
    name: str = Field(selector='.name', description='Author name')
    avatar_url: str = Field(
        selector='img.avatar',
        attribute='src',
        description='Avatar URL',
    )
    bio: str = Field(selector='.bio', description='Short author bio')


class ArticleWithNestedAuthor(ExtractionModel):
    title: str = Field(selector='h1.article-title', description='Title')
    author: AuthorModel = Field(
        selector='.author-card',
        description='Author info block',
    )


class ArticleWithOptional(ExtractionModel):
    title: str = Field(selector='h1.article-title', description='Title')
    subtitle: Optional[str] = Field(
        selector='.nonexistent-subtitle',
        description='Optional subtitle',
        default=None,
    )
    missing_with_default: str = Field(
        selector='.nonexistent-field',
        description='Missing field with default',
        default='fallback_value',
    )


class QuoteModel(ExtractionModel):
    text: str = Field(selector='.text', description='Quote text')
    author: str = Field(selector='.author', description='Quote author')


class QuoteWithYear(ExtractionModel):
    text: str = Field(selector='.text', description='Quote text')
    author: str = Field(selector='.author', description='Quote author')
    year: int = Field(
        selector='.year',
        description='Year of the quote',
        transform=int,
    )


class ProductMeta(ExtractionModel):
    brand: str = Field(selector='.brand', description='Brand name')
    sku: str = Field(selector='.sku', description='Product SKU')


class ProductModel(ExtractionModel):
    name: str = Field(selector='.product-name', description='Product name')
    price: float = Field(
        selector='.product-price',
        description='Product price',
        transform=parse_price,
    )
    meta: ProductMeta = Field(
        selector='.product-meta',
        description='Product metadata',
    )


class Contributor(ExtractionModel):
    name: str = Field(selector='.name', description='Contributor name')
    role: str = Field(selector='.role', description='Contributor role')


class MultiAuthorArticle(ExtractionModel):
    title: str = Field(selector='.title', description='Article title')
    contributors: list[Contributor] = Field(
        selector='.contributor',
        description='List of contributors',
    )


class XPathModel(ExtractionModel):
    value: str = Field(
        selector='//*[@id="xpath-section"]//span[@class="deep-value"]',
        description='Value found via XPath',
    )


class DescriptionOnlyField(ExtractionModel):
    title: str = Field(selector='h1.article-title', description='Title')
    sentiment: str = Field(
        description='Article sentiment (future LLM field)',
        default='unknown',
    )


class RequiredFieldMissing(ExtractionModel):
    title: str = Field(selector='h1.article-title', description='Title')
    nonexistent: str = Field(
        selector='.this-does-not-exist',
        description='Required field that will not be found',
    )


class PEP604OptionalModel(ExtractionModel):
    title: str = Field(selector='h1.article-title', description='Title')
    subtitle: str | None = Field(
        selector='.nonexistent-subtitle',
        description='PEP 604 optional',
        default=None,
    )


class BaseArticle(ExtractionModel):
    title: str = Field(selector='h1.article-title', description='Title')


class ExtendedArticle(BaseArticle):
    body: str = Field(selector='.article-body', description='Body text')


class ArticleWithBadTransform(ExtractionModel):
    title: str = Field(selector='h1.article-title', description='Title')
    broken_price: Optional[float] = Field(
        selector='#empty-element',
        description='Empty element with bad transform',
        transform=lambda s: float(s),
        default=None,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestExtractSingle:
    """Tests for tab.extract() — single item extraction."""

    @pytest.mark.asyncio
    async def test_extract_simple_text_fields(self, ci_chrome_options):
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(FILE_URL)
            await asyncio.sleep(0.5)

            article = await tab.extract(SimpleArticle)
            assert article.title == 'Understanding Web Scraping'
            assert 'extracting data' in article.body

    @pytest.mark.asyncio
    async def test_extract_multiple_attributes(self, ci_chrome_options):
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(FILE_URL)
            await asyncio.sleep(0.5)

            article = await tab.extract(ArticleWithAttributes)
            assert article.published_at == '2025-03-15'
            assert article.image_src == 'https://example.com/hero.jpg'
            assert article.image_alt == 'Hero image'
            assert article.image_data_id == 'img-42'
            assert article.link_href == 'https://example.com/article/1'

    @pytest.mark.asyncio
    async def test_extract_list_of_strings(self, ci_chrome_options):
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(FILE_URL)
            await asyncio.sleep(0.5)

            article = await tab.extract(ArticleWithTags)
            assert article.tags == ['python', 'automation', 'web']

    @pytest.mark.asyncio
    async def test_extract_with_transform(self, ci_chrome_options):
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(FILE_URL)
            await asyncio.sleep(0.5)

            article = await tab.extract(ArticleWithTransform)
            assert article.price == 1234.56

    @pytest.mark.asyncio
    async def test_extract_nested_model(self, ci_chrome_options):
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(FILE_URL)
            await asyncio.sleep(0.5)

            article = await tab.extract(ArticleWithNestedAuthor)
            assert article.title == 'Understanding Web Scraping'
            assert article.author.name == 'Jane Doe'
            assert article.author.avatar_url == 'https://example.com/jane.jpg'
            assert 'open source' in article.author.bio

    @pytest.mark.asyncio
    async def test_extract_optional_missing_fields(self, ci_chrome_options):
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(FILE_URL)
            await asyncio.sleep(0.5)

            article = await tab.extract(ArticleWithOptional)
            assert article.title == 'Understanding Web Scraping'
            assert article.subtitle is None
            assert article.missing_with_default == 'fallback_value'

    @pytest.mark.asyncio
    async def test_extract_with_xpath_selector(self, ci_chrome_options):
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(FILE_URL)
            await asyncio.sleep(0.5)

            result = await tab.extract(XPathModel)
            assert result.value == 'Found via XPath'

    @pytest.mark.asyncio
    async def test_extract_with_scope(self, ci_chrome_options):
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(FILE_URL)
            await asyncio.sleep(0.5)

            article = await tab.extract(
                SimpleArticle, scope='#main-article'
            )
            assert article.title == 'Understanding Web Scraping'

    @pytest.mark.asyncio
    async def test_extract_description_only_field_uses_default(self, ci_chrome_options):
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(FILE_URL)
            await asyncio.sleep(0.5)

            article = await tab.extract(DescriptionOnlyField)
            assert article.title == 'Understanding Web Scraping'
            assert article.sentiment == 'unknown'

    @pytest.mark.asyncio
    async def test_extract_required_field_missing_raises(self, ci_chrome_options):
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(FILE_URL)
            await asyncio.sleep(0.5)

            with pytest.raises(FieldExtractionFailed):
                await tab.extract(RequiredFieldMissing)

    @pytest.mark.asyncio
    async def test_extract_model_dump(self, ci_chrome_options):
        """Verify pydantic serialization works on extracted models."""
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(FILE_URL)
            await asyncio.sleep(0.5)

            article = await tab.extract(ArticleWithNestedAuthor)
            data = article.model_dump()
            assert isinstance(data, dict)
            assert data['title'] == 'Understanding Web Scraping'
            assert isinstance(data['author'], dict)
            assert data['author']['name'] == 'Jane Doe'


class TestExtractAll:
    """Tests for tab.extract_all() — multiple item extraction."""

    @pytest.mark.asyncio
    async def test_extract_all_basic(self, ci_chrome_options):
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(FILE_URL)
            await asyncio.sleep(0.5)

            quotes = await tab.extract_all(QuoteModel, scope='.quote')
            assert len(quotes) == 3
            assert quotes[0].text == 'The only way to do great work is to love what you do.'
            assert quotes[0].author == 'Steve Jobs'
            assert quotes[2].text == 'Stay hungry, stay foolish.'

    @pytest.mark.asyncio
    async def test_extract_all_with_transform(self, ci_chrome_options):
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(FILE_URL)
            await asyncio.sleep(0.5)

            quotes = await tab.extract_all(QuoteWithYear, scope='.quote')
            assert len(quotes) == 3
            assert quotes[0].year == 2005
            assert quotes[1].year == 2001
            assert isinstance(quotes[0].year, int)

    @pytest.mark.asyncio
    async def test_extract_all_with_limit(self, ci_chrome_options):
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(FILE_URL)
            await asyncio.sleep(0.5)

            quotes = await tab.extract_all(
                QuoteModel, scope='.quote', limit=2
            )
            assert len(quotes) == 2

    @pytest.mark.asyncio
    async def test_extract_all_with_nested_model(self, ci_chrome_options):
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(FILE_URL)
            await asyncio.sleep(0.5)

            products = await tab.extract_all(
                ProductModel, scope='.product-card'
            )
            assert len(products) == 2
            assert products[0].name == 'Laptop Pro'
            assert products[0].price == 5999.00
            assert products[0].meta.brand == 'TechCorp'
            assert products[0].meta.sku == 'SKU-001'
            assert products[1].name == 'Mouse Wireless'
            assert products[1].meta.brand == 'PeripheralCo'

    @pytest.mark.asyncio
    async def test_extract_all_no_matches_returns_empty(self, ci_chrome_options):
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(FILE_URL)
            await asyncio.sleep(0.5)

            results = await tab.extract_all(
                QuoteModel, scope='.nonexistent-container'
            )
            assert results == []


class TestValidation:
    """Tests for model validation at definition time."""

    def test_field_without_selector_or_description_raises(self):
        with pytest.raises(InvalidExtractionModel):
            Field(selector=None, description=None)

    def test_model_with_invalid_field_raises(self):
        """Field with _extraction_metadata but no selector and no description should fail."""
        # This is caught at Field() call time, not at class definition time,
        # because Field() validates its arguments immediately.
        with pytest.raises(InvalidExtractionModel):

            class BadModel(ExtractionModel):
                bad_field: str = Field()  # type: ignore[call-arg]


class TestEdgeCases:
    """Tests for edge cases and inheritance."""

    @pytest.mark.asyncio
    async def test_model_inheritance_includes_parent_fields(self, ci_chrome_options):
        """ExtendedArticle should have both parent's title and own body fields."""
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(FILE_URL)
            await asyncio.sleep(0.5)

            article = await tab.extract(ExtendedArticle)
            assert article.title == 'Understanding Web Scraping'
            assert 'extracting data' in article.body

    @pytest.mark.asyncio
    async def test_failed_transform_on_optional_field_uses_default(self, ci_chrome_options):
        """Transform that throws on Optional field should fall back to default."""
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(FILE_URL)
            await asyncio.sleep(0.5)

            article = await tab.extract(ArticleWithBadTransform)
            assert article.title == 'Understanding Web Scraping'
            assert article.broken_price is None

    @pytest.mark.asyncio
    async def test_extract_all_with_scope_returns_correct_count(self, ci_chrome_options):
        """extract_all should only match elements within the page."""
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(FILE_URL)
            await asyncio.sleep(0.5)

            products = await tab.extract_all(ProductModel, scope='.product-card')
            assert len(products) == 2
            # Verify each product has correct nested data
            for product in products:
                assert product.meta.brand
                assert product.meta.sku

    @pytest.mark.asyncio
    async def test_empty_list_field(self, ci_chrome_options):
        """list field with no matching elements should return empty list."""

        class ModelWithEmptyList(ExtractionModel):
            title: str = Field(selector='h1.article-title', description='Title')
            items: list[str] = Field(
                selector='.nonexistent-items .item',
                description='Items that do not exist',
            )

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(FILE_URL)
            await asyncio.sleep(0.5)

            result = await tab.extract(ModelWithEmptyList)
            assert result.title == 'Understanding Web Scraping'
            assert result.items == []

    @pytest.mark.asyncio
    async def test_pep604_optional_syntax(self, ci_chrome_options):
        """str | None (PEP 604) should be handled the same as Optional[str]."""
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(FILE_URL)
            await asyncio.sleep(0.5)

            result = await tab.extract(PEP604OptionalModel)
            assert result.title == 'Understanding Web Scraping'
            assert result.subtitle is None

    @pytest.mark.asyncio
    async def test_list_of_nested_models(self, ci_chrome_options):
        """list[ExtractionModel] should extract each item as a nested model."""
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(FILE_URL)
            await asyncio.sleep(0.5)

            article = await tab.extract(
                MultiAuthorArticle, scope='#multi-author-article'
            )
            assert article.title == 'Collaborative Research Paper'
            assert len(article.contributors) == 3
            assert article.contributors[0].name == 'Alice Smith'
            assert article.contributors[0].role == 'Lead Researcher'
            assert article.contributors[1].name == 'Bob Johnson'
            assert article.contributors[1].role == 'Data Analyst'
            assert article.contributors[2].name == 'Carol Williams'
            assert article.contributors[2].role == 'Reviewer'


class TestConcurrentExtraction:
    """Tests that validate concurrent field and container extraction."""

    @pytest.mark.asyncio
    async def test_many_fields_extracted_concurrently(self, ci_chrome_options):
        """Model with many fields should extract them all concurrently."""

        class FullArticle(ExtractionModel):
            title: str = Field(selector='h1.article-title', description='Title')
            body: str = Field(selector='.article-body', description='Body')
            author_name: str = Field(selector='.author-card .name', description='Author')
            author_bio: str = Field(selector='.author-card .bio', description='Bio')
            avatar: str = Field(
                selector='.author-card img.avatar',
                attribute='src',
                description='Avatar',
            )
            published: str = Field(
                selector='time.published',
                attribute='datetime',
                description='Date',
            )
            image_src: str = Field(
                selector='.hero-image',
                attribute='src',
                description='Image',
            )
            image_alt: str = Field(
                selector='.hero-image',
                attribute='alt',
                description='Alt',
            )
            price: str = Field(selector='.price', description='Price')
            link: str = Field(
                selector='.source-link',
                attribute='href',
                description='Link',
            )
            tags: list[str] = Field(selector='.tag-list .tag', description='Tags')

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(FILE_URL)
            await asyncio.sleep(0.5)

            article = await tab.extract(FullArticle)
            assert article.title == 'Understanding Web Scraping'
            assert article.author_name == 'Jane Doe'
            assert article.published == '2025-03-15'
            assert article.image_src == 'https://example.com/hero.jpg'
            assert article.image_alt == 'Hero image'
            assert 'R$' in article.price
            assert len(article.tags) == 3

    @pytest.mark.asyncio
    async def test_extract_all_containers_concurrently(self, ci_chrome_options):
        """extract_all should process all containers concurrently."""
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(FILE_URL)
            await asyncio.sleep(0.5)

            quotes = await tab.extract_all(QuoteWithYear, scope='.quote')
            assert len(quotes) == 3
            # All quotes should have been extracted correctly
            assert quotes[0].year == 2005
            assert quotes[1].year == 2001
            assert quotes[2].year == 2005
            assert quotes[0].author == 'Steve Jobs'
            assert quotes[1].author == 'Steve Jobs'

    @pytest.mark.asyncio
    async def test_concurrent_nested_with_multiple_containers(self, ci_chrome_options):
        """extract_all with nested models should handle concurrency correctly."""
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(FILE_URL)
            await asyncio.sleep(0.5)

            products = await tab.extract_all(ProductModel, scope='.product-card')
            assert len(products) == 2
            # Both products extracted concurrently with nested meta
            assert products[0].name == 'Laptop Pro'
            assert products[0].meta.brand == 'TechCorp'
            assert products[1].name == 'Mouse Wireless'
            assert products[1].meta.brand == 'PeripheralCo'

    @pytest.mark.asyncio
    async def test_concurrent_with_mixed_required_optional(self, ci_chrome_options):
        """Concurrent extraction with mix of required and optional fields."""

        class MixedModel(ExtractionModel):
            title: str = Field(selector='h1.article-title', description='Title')
            missing_1: Optional[str] = Field(
                selector='.nonexistent-1', description='Missing 1', default=None
            )
            body: str = Field(selector='.article-body', description='Body')
            missing_2: Optional[str] = Field(
                selector='.nonexistent-2', description='Missing 2', default=None
            )
            tags: list[str] = Field(selector='.tag-list .tag', description='Tags')

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(FILE_URL)
            await asyncio.sleep(0.5)

            result = await tab.extract(MixedModel)
            assert result.title == 'Understanding Web Scraping'
            assert result.missing_1 is None
            assert 'extracting data' in result.body
            assert result.missing_2 is None
            assert len(result.tags) == 3
