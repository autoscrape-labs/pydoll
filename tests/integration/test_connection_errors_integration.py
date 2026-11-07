"""What a tab command raises once the browser it talks to is gone.

Code that catches ``PydollException`` or ``ConnectionException`` to notice a
lost browser has to see a Pydoll exception here, not the socket layer's
``OSError``.
"""

from __future__ import annotations

import asyncio

import pytest

from pydoll.browser.chromium import Chrome
from pydoll.browser.tab import Tab
from pydoll.exceptions import ConnectionFailed, PydollException


@pytest.mark.asyncio
async def test_tab_commands_after_the_browser_died_raise_connection_failed(
    ci_chrome_options, tmp_path
):
    ci_chrome_options.add_argument(f'--user-data-dir={tmp_path}')
    browser = Chrome(options=ci_chrome_options)
    tab = await browser.start()
    try:
        await tab.execute_script('return 1')
        process = browser._browser_process_manager._process
        process.kill()
        process.wait(timeout=10)
        await asyncio.wait_for(tab._connection_handler.wait_disconnected(), timeout=5)
        for _ in range(3):
            with pytest.raises(ConnectionFailed) as raised:
                await tab.execute_script('return 1 + 1')
            assert isinstance(raised.value, PydollException)
            assert isinstance(raised.value.__cause__, OSError)
    finally:
        await browser.close()


@pytest.mark.asyncio
async def test_tab_for_a_target_that_does_not_exist_raises_connection_failed(browser):
    tab = Tab(browser, target_id='0' * 32, connection_port=browser._connection_port)
    with pytest.raises(ConnectionFailed):
        await tab.execute_script('return 1')
