"""Example: extracting quotes from quotes.toscrape.com using pydoll extractor."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime

from pydoll.browser.chromium.chrome import Chrome
from pydoll.extractor import ExtractionModel, Field


@dataclass
class BirthInfo:
    """Structured birth information parsed from a raw date string."""

    date: datetime

    def __str__(self) -> str:
        return f'{self.date.strftime("%B %d, %Y")}'


def parse_birth_info(raw: str) -> BirthInfo:
    """Transform raw date string into BirthInfo custom type."""
    return BirthInfo(
        date=datetime.strptime(raw.strip(), '%B %d, %Y'),
    )


def clean_location(raw: str) -> str:
    """Remove 'in ' prefix from birth location."""
    return raw.strip().removeprefix('in ')


class Quote(ExtractionModel):
    text: str = Field(selector='.text', description='The quote text')
    author: str = Field(selector='.author', description='Who said the quote')
    tags: list[str] = Field(selector='.tag', description='Associated tags')


class AuthorInfo(ExtractionModel):
    name: str = Field(selector='.author-title', description='Author full name')
    birth: BirthInfo = Field(
        selector='.author-born-date',
        description='Author birth info as custom type',
        transform=parse_birth_info,
    )
    birth_location: str = Field(
        selector='.author-born-location',
        description='Author birth location',
        transform=clean_location,
    )
    bio: str = Field(
        selector='.author-description',
        description='Author biography',
    )


async def main():
    async with Chrome() as browser:
        tab = await browser.start()

        await tab.go_to('https://quotes.toscrape.com')
        quotes = await tab.extract_all(Quote, scope='.quote', timeout=5)
        print(f'Found {len(quotes)} quotes\n')
        for i, quote in enumerate(quotes, 1):
            print(f'{i}. "{quote.text}"')
            print(f'   — {quote.author}')
            print(f'   Tags: {", ".join(quote.tags)}\n')

        author_link = await tab.query('.quote .author + a')
        href = author_link.get_attribute('href')
        await tab.go_to(f'https://quotes.toscrape.com{href}')

        author = await tab.extract(AuthorInfo, timeout=5)
        print('--- Author info ---')
        print(f'Name: {author.name}')
        print(f'Birth: {author.birth}')
        print(f'  type: {type(author.birth).__name__}')
        print(f'  date.year: {author.birth.date.year}')
        print(f'  date.month: {author.birth.date.month}')
        print(f'Location: {author.birth_location}')
        print(f'Bio: {author.bio[:100]}...\n')


if __name__ == '__main__':
    asyncio.run(main())
