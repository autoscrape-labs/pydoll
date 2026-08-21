# Your first automation

Real automation is more than loading a page: you fill forms, click buttons, wait for the page to react, and collect data. In this page you'll build a complete flow against [quotes.toscrape.com](https://quotes.toscrape.com), a site made for practicing scraping: log in, confirm it worked, and extract every quote as a typed object.

**You will learn**

- [How to fill a form and log in like a person](#log-in-like-a-person)
- [How to confirm the page reacted](#confirm-the-login-worked)
- [How to extract typed data with a model](#extract-typed-data)
- [How the full script looks](#the-full-script)

## Log in like a person

`find()` locates elements by their attributes, and `type_text(humanize=True)` types with the variable rhythm of a real user, occasional corrected typos included. You don't need to focus the field first; Pydoll clicks it before typing.

```python
await tab.go_to('https://quotes.toscrape.com/login')

username = await tab.find(id='username')
await username.type_text('john', humanize=True)

password = await tab.find(id='password')
await password.type_text('SecretPass123', humanize=True)

submit = await tab.find(tag_name='input', type='submit')
await submit.click()
```

The login form on this site accepts any username and password, so the values only need to look real.

## Confirm the login worked

After submitting, the page reloads and shows a Logout link. Finding that link is your confirmation. `find()` waits for it, so there is no sleep between clicking and checking:

```python
logout_link = await tab.find(text='Logout', timeout=5, raise_exc=False)
if logout_link:
    print('Logged in.')
else:
    print('Login failed.')
```

`raise_exc=False` makes `find()` return `None` instead of raising when the element never appears, which keeps control flow in your hands.

## Extract typed data

With the session active, switch from interacting to collecting. Declare what a quote looks like once, and `extract_all()` returns a list of validated objects:

```python
from pydoll.extractor import ExtractionModel, Field


class Quote(ExtractionModel):
    text: str = Field(selector='.text')
    author: str = Field(selector='.author')
    tags: list[str] = Field(selector='.tag')


quotes = await tab.extract_all(Quote, scope='.quote', timeout=5)

for quote in quotes:
    print(f'{quote.author}: {quote.text}')
    print(f'  tags: {", ".join(quote.tags)}')
```

Each `quote` is a real Pydantic object: `quote.tags` is a `list[str]`, your IDE autocompletes the fields, and `quote.model_dump_json()` serializes it. No element-by-element querying, no manual casting.

## The full script

Create `first_automation.py`:

```python
import asyncio

from pydoll.browser.chromium import Chrome
from pydoll.extractor import ExtractionModel, Field


class Quote(ExtractionModel):
    text: str = Field(selector='.text')
    author: str = Field(selector='.author')
    tags: list[str] = Field(selector='.tag')


async def main():
    async with Chrome() as browser:
        tab = await browser.start()

        await tab.go_to('https://quotes.toscrape.com/login')

        username = await tab.find(id='username')
        await username.type_text('john', humanize=True)

        password = await tab.find(id='password')
        await password.type_text('SecretPass123', humanize=True)

        submit = await tab.find(tag_name='input', type='submit')
        await submit.click()

        logout_link = await tab.find(text='Logout', timeout=5, raise_exc=False)
        if not logout_link:
            print('Login failed.')
            return

        quotes = await tab.extract_all(Quote, scope='.quote', timeout=5)
        for quote in quotes:
            print(f'{quote.author}: {quote.text}')

asyncio.run(main())
```

Run it:

```bash
python first_automation.py
```

You'll watch the browser type the credentials, log in, and then your terminal fills with authors and quotes.

## What's next

- [Staying undetected](stealth/index.md): the next step of the journey, keeping your automation from looking like one.
- [Element finding](guides/element-finding.md): every attribute, selector, and strategy `find()` and `query()` support.
- [Structured extraction](guides/structured-extraction.md): attributes, transforms, and nested models.
