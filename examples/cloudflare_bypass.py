import asyncio

from pydoll.browser import Chrome


async def example_with_context_manager():
    """
    Example using the context manager approach to handle Cloudflare captcha.

    This waits for the captcha to be processed before continuing.
    """
    browser = Chrome()
    await browser.start()
    page = await browser.get_page()

    print('Using context manager approach...')
    async with page.expect_and_bypass_cloudflare_captcha():
        await page.go_to('https://www.planetminecraft.com/account/sign_in/')
        print('Page loaded, waiting for captcha to be handled...')

    print('Captcha handling completed, now we can continue...')
    await asyncio.sleep(3)
    await browser.stop()


async def example_with_enable_disable():
    """
    Example using the enable/disable approach to handle Cloudflare captcha.

    This enables the auto-solving and continues execution immediately.
    The captcha will be solved in the background when it appears.
    """
    browser = Chrome()
    await browser.start()
    page = await browser.get_page()

    print('Using enable/disable approach...')

    # Enable automatic captcha solving before navigating
    await page.enable_auto_solve_cloudflare_captcha()

    # Navigate to the page - captcha will be handled automatically
    await page.go_to('https://www.planetminecraft.com/account/sign_in/')
    print('Page loaded, captcha will be handled in the background...')

    # Continue with other operations immediately
    # The captcha will be solved in the background when it appears
    await asyncio.sleep(5)

    # Disable auto-solving when no longer needed
    await page.disable_auto_solve_cloudflare_captcha()
    print('Auto-solving disabled')

    await browser.stop()


async def main():
    # Choose which example to run
    await example_with_context_manager()
    # Or uncomment the line below to run the enable/disable example
    # await example_with_enable_disable()


if __name__ == '__main__':
    asyncio.run(main())
