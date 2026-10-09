"""A stock Playwright script running on pydoll.

The only change from the original is the import line: ``playwright.async_api``
became ``pydoll.playwright.async_api``. Everything else is plain Playwright.
"""

import asyncio

from pydoll.playwright.async_api import async_playwright


async def main() -> None:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 800})
        page = await context.new_page()

        response = await page.goto('https://quotes.toscrape.com/')
        print('status:', response.status if response else None)
        print('title:', await page.title())

        quotes = page.locator('.quote')
        print('quotes on page:', await quotes.count())
        first = quotes.first
        print('first quote:', await first.locator('.text').inner_text())
        print('by:', await first.locator('.author').inner_text())
        print('tags:', await first.locator('.tag').all_inner_texts())

        await page.get_by_role('link', name='Login').click()
        await page.wait_for_url('**/login')
        await page.get_by_label('Username').fill('demo')
        await page.get_by_label('Password').fill('demo')
        await page.get_by_role('button', name='Login').click()
        await page.wait_for_load_state('networkidle')
        print('logged in:', await page.get_by_role('link', name='Logout').is_visible())

        await page.screenshot(path='quotes.png', full_page=True)
        await browser.close()


if __name__ == '__main__':
    asyncio.run(main())
