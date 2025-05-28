import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from pydoll.browser.chromium.base import Browser
from pydoll.protocol.commands import BrowserCommands


class ConcreteBrowser(Browser):
    def _get_default_binary_location(self) -> str:
        return '/fake/path/to/browser'


@pytest_asyncio.fixture
async def mock_browser():
    with (
        patch.multiple(
            Browser,
            _get_default_binary_location=MagicMock(
                return_value='/fake/path/to/browser'
            ),
        ),
        patch(
            'pydoll.connection.ConnectionHandler',
            autospec=True,
        ) as mock_conn_handler,
    ):
        browser = ConcreteBrowser()
        browser._connection_handler = mock_conn_handler.return_value
        browser._connection_handler.execute_command = AsyncMock()
        browser._connection_handler.register_callback = AsyncMock()

        browser._pages = ['page1']

        yield browser


@pytest.mark.asyncio
async def test_get_window_id_success(mock_browser):
    mock_browser._connection_handler.execute_command.return_value = {
        'result': {'windowId': 123}
    }
    result = await mock_browser.get_window_id()
    assert result == 123


@pytest.mark.asyncio
async def test_get_window_id_with_error_and_retry(mock_browser):
    mock_browser._execute_command = AsyncMock(
        side_effect=[
            {'error': 'some error'},
            {
                'result': {
                    'targetInfos': [
                        {
                            'type': 'page',
                            'attached': True,
                            'targetId': 'target1',
                        }
                    ]
                }
            },
            {'result': {'windowId': 123}},
        ]
    )

    result = await mock_browser.get_window_id()
    assert result == 123


@pytest.mark.asyncio
async def test_get_window_id_failure(mock_browser):
    mock_browser._connection_handler.execute_command.return_value = {
        'error': 'some error'
    }
    mock_browser.get_targets = AsyncMock(return_value=[])
    with pytest.raises(RuntimeError):
        await mock_browser.get_window_id()


@pytest.mark.asyncio
async def test_get_valid_target_id_success(mock_browser):
    pages = [{'type': 'page', 'attached': True, 'targetId': 'target1'}]
    result = await mock_browser._get_valid_target_id(pages)
    assert result == 'target1'


@pytest.mark.asyncio
async def test_get_valid_target_id_no_valid_page(mock_browser):
    pages = []
    with pytest.raises(
        RuntimeError, match='No valid attached browser page found.'
    ):
        await mock_browser._get_valid_target_id(pages)


@pytest.mark.asyncio
async def test_get_valid_target_id_missing_target_id(mock_browser):
    pages = [{'type': 'page', 'attached': True, 'targetId': None}]
    with pytest.raises(
        RuntimeError, match="Valid page found but missing 'targetId'."
    ):
        await mock_browser._get_valid_target_id(pages)


@pytest.mark.asyncio
async def test_get_window_id_by_target(mock_browser):
    expected_command = {
        'method': 'Browser.getWindowForTarget',
        'params': {
            'targetId': 'target1',
        },
    }
    assert (
        BrowserCommands.get_window_id_by_target('target1') == expected_command
    )
