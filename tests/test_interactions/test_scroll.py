import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch, call

from pydoll.interactions.scroll import ScrollAPI
from pydoll.constants import ScrollPosition, Scripts
from pydoll.commands import RuntimeCommands


@pytest_asyncio.fixture
async def mock_tab():
    """Mock Tab instance for ScrollAPI tests."""
    tab = MagicMock()
    tab._execute_command = AsyncMock()
    return tab


@pytest_asyncio.fixture
async def scroll_api(mock_tab):
    """Create ScrollAPI instance with mocked tab."""
    return ScrollAPI(mock_tab)


class TestScrollAPIInitialization:
    """Test ScrollAPI initialization."""

    def test_initialization(self, mock_tab):
        """Test ScrollAPI is properly initialized with tab."""
        scroll_api = ScrollAPI(mock_tab)
        assert scroll_api._tab == mock_tab


class TestScrollAPIBy:
    """Test scroll.by() method."""

    @pytest.mark.asyncio
    async def test_scroll_down_smooth(self, scroll_api, mock_tab):
        """Test scrolling down with smooth animation."""
        await scroll_api.by(ScrollPosition.DOWN, 500, smooth=True)

        # Verify execute_command was called
        assert mock_tab._execute_command.called
        call_args = mock_tab._execute_command.call_args

        # Verify the command is RuntimeCommands.evaluate with await_promise=True
        command = call_args[0][0]
        assert command['method'] == 'Runtime.evaluate'
        assert command['params']['awaitPromise'] is True

        # Verify the script contains expected values
        script = command['params']['expression']
        assert 'top: 5000' in script  # 500 * 10
        assert "behavior: 'smooth'" in script

    @pytest.mark.asyncio
    async def test_scroll_up_smooth(self, scroll_api, mock_tab):
        """Test scrolling up with smooth animation."""
        await scroll_api.by(ScrollPosition.UP, 300, smooth=True)

        call_args = mock_tab._execute_command.call_args
        command = call_args[0][0]
        script = command['params']['expression']

        assert 'top: -3000' in script  # -300 * 10
        assert "behavior: 'smooth'" in script

    @pytest.mark.asyncio
    async def test_scroll_right_smooth(self, scroll_api, mock_tab):
        """Test scrolling right with smooth animation."""
        await scroll_api.by(ScrollPosition.RIGHT, 200, smooth=True)

        call_args = mock_tab._execute_command.call_args
        command = call_args[0][0]
        script = command['params']['expression']

        assert 'left: 2000' in script  # 200 * 10
        assert "behavior: 'smooth'" in script

    @pytest.mark.asyncio
    async def test_scroll_left_smooth(self, scroll_api, mock_tab):
        """Test scrolling left with smooth animation."""
        await scroll_api.by(ScrollPosition.LEFT, 150, smooth=True)

        call_args = mock_tab._execute_command.call_args
        command = call_args[0][0]
        script = command['params']['expression']

        assert 'left: -1500' in script  # -150 * 10
        assert "behavior: 'smooth'" in script

    @pytest.mark.asyncio
    async def test_scroll_down_instant(self, scroll_api, mock_tab):
        """Test scrolling down without smooth animation."""
        await scroll_api.by(ScrollPosition.DOWN, 1000, smooth=False)

        call_args = mock_tab._execute_command.call_args
        command = call_args[0][0]
        script = command['params']['expression']

        assert 'top: 10000' in script  # 1000 * 10
        assert "behavior: 'auto'" in script

    @pytest.mark.asyncio
    async def test_scroll_with_float_distance(self, scroll_api, mock_tab):
        """Test scrolling with float distance."""
        await scroll_api.by(ScrollPosition.DOWN, 250.5, smooth=True)

        call_args = mock_tab._execute_command.call_args
        command = call_args[0][0]
        script = command['params']['expression']

        assert 'top: 2505.0' in script  # 250.5 * 10


class TestScrollAPIToTop:
    """Test scroll.to_top() method."""

    @pytest.mark.asyncio
    async def test_scroll_to_top_smooth(self, scroll_api, mock_tab):
        """Test scrolling to top with smooth animation."""
        await scroll_api.to_top(smooth=True)

        assert mock_tab._execute_command.called
        call_args = mock_tab._execute_command.call_args
        command = call_args[0][0]

        assert command['method'] == 'Runtime.evaluate'
        assert command['params']['awaitPromise'] is True

        script = command['params']['expression']
        assert 'top: 0' in script
        assert "behavior: 'smooth'" in script

    @pytest.mark.asyncio
    async def test_scroll_to_top_instant(self, scroll_api, mock_tab):
        """Test scrolling to top without smooth animation."""
        await scroll_api.to_top(smooth=False)

        call_args = mock_tab._execute_command.call_args
        command = call_args[0][0]
        script = command['params']['expression']

        assert 'top: 0' in script
        assert "behavior: 'auto'" in script


class TestScrollAPIToBottom:
    """Test scroll.to_bottom() method."""

    @pytest.mark.asyncio
    async def test_scroll_to_bottom_smooth(self, scroll_api, mock_tab):
        """Test scrolling to bottom with smooth animation."""
        await scroll_api.to_bottom(smooth=True)

        assert mock_tab._execute_command.called
        call_args = mock_tab._execute_command.call_args
        command = call_args[0][0]

        assert command['method'] == 'Runtime.evaluate'
        assert command['params']['awaitPromise'] is True

        script = command['params']['expression']
        assert 'top: document.body.scrollHeight' in script
        assert "behavior: 'smooth'" in script

    @pytest.mark.asyncio
    async def test_scroll_to_bottom_instant(self, scroll_api, mock_tab):
        """Test scrolling to bottom without smooth animation."""
        await scroll_api.to_bottom(smooth=False)

        call_args = mock_tab._execute_command.call_args
        command = call_args[0][0]
        script = command['params']['expression']

        assert 'top: document.body.scrollHeight' in script
        assert "behavior: 'auto'" in script


class TestScrollAPIHelperMethods:
    """Test ScrollAPI private helper methods."""

    def test_get_axis_and_distance_down(self, scroll_api):
        """Test _get_axis_and_distance for DOWN direction."""
        axis, distance = scroll_api._get_axis_and_distance(ScrollPosition.DOWN, 100)
        assert axis == 'top'
        assert distance == 1000  # 100 * 10

    def test_get_axis_and_distance_up(self, scroll_api):
        """Test _get_axis_and_distance for UP direction."""
        axis, distance = scroll_api._get_axis_and_distance(ScrollPosition.UP, 100)
        assert axis == 'top'
        assert distance == -1000  # -100 * 10

    def test_get_axis_and_distance_right(self, scroll_api):
        """Test _get_axis_and_distance for RIGHT direction."""
        axis, distance = scroll_api._get_axis_and_distance(ScrollPosition.RIGHT, 50)
        assert axis == 'left'
        assert distance == 500  # 50 * 10

    def test_get_axis_and_distance_left(self, scroll_api):
        """Test _get_axis_and_distance for LEFT direction."""
        axis, distance = scroll_api._get_axis_and_distance(ScrollPosition.LEFT, 50)
        assert axis == 'left'
        assert distance == -500  # -50 * 10

    def test_get_behavior_smooth(self, scroll_api):
        """Test _get_behavior with smooth=True."""
        behavior = scroll_api._get_behavior(True)
        assert behavior == 'smooth'

    def test_get_behavior_instant(self, scroll_api):
        """Test _get_behavior with smooth=False."""
        behavior = scroll_api._get_behavior(False)
        assert behavior == 'auto'


class TestScrollAPIIntegrationWithTab:
    """Test ScrollAPI integration with Tab."""

    @pytest.mark.asyncio
    async def test_tab_has_scroll_property(self):
        """Test that Tab has scroll property."""
        with patch('pydoll.connection.ConnectionHandler', autospec=True):
            from pydoll.browser.tab import Tab

            mock_browser = MagicMock()
            tab = Tab(mock_browser, target_id='test-id')

            # Access scroll property
            scroll = tab.scroll

            # Verify it's a ScrollAPI instance
            assert isinstance(scroll, ScrollAPI)
            assert scroll._tab == tab

    @pytest.mark.asyncio
    async def test_tab_scroll_property_is_lazy(self):
        """Test that scroll property is created lazily."""
        with patch('pydoll.connection.ConnectionHandler', autospec=True):
            from pydoll.browser.tab import Tab

            mock_browser = MagicMock()
            tab = Tab(mock_browser, target_id='test-id')

            # Initially None
            assert tab._scroll is None

            # Access creates instance
            scroll1 = tab.scroll
            assert tab._scroll is not None

            # Second access returns same instance
            scroll2 = tab.scroll
            assert scroll1 is scroll2

    @pytest.mark.asyncio
    async def test_scroll_execute_command_integration(self):
        """Test that scroll methods properly call tab._execute_command."""
        with patch('pydoll.connection.ConnectionHandler', autospec=True):
            from pydoll.browser.tab import Tab

            mock_browser = MagicMock()
            tab = Tab(mock_browser, target_id='test-id')
            tab._execute_command = AsyncMock()

            # Call scroll method
            await tab.scroll.by(ScrollPosition.DOWN, 500, smooth=True)

            # Verify _execute_command was called
            assert tab._execute_command.called

            # Verify command structure
            call_args = tab._execute_command.call_args
            command = call_args[0][0]
            assert command['method'] == 'Runtime.evaluate'
            assert command['params']['awaitPromise'] is True


class TestScrollAPIScriptGeneration:
    """Test that correct JavaScript scripts are generated."""

    @pytest.mark.asyncio
    async def test_scroll_by_script_structure(self, scroll_api, mock_tab):
        """Test that scroll.by generates correct script structure."""
        await scroll_api.by(ScrollPosition.DOWN, 500, smooth=True)

        call_args = mock_tab._execute_command.call_args
        command = call_args[0][0]
        script = command['params']['expression']

        # Verify script has Promise structure
        assert 'new Promise' in script or 'Promise' in script
        assert 'scrollend' in script or 'scrollBy' in script
        assert 'resolve' in script

    @pytest.mark.asyncio
    async def test_to_top_script_structure(self, scroll_api, mock_tab):
        """Test that scroll.to_top generates correct script structure."""
        await scroll_api.to_top(smooth=True)

        call_args = mock_tab._execute_command.call_args
        command = call_args[0][0]
        script = command['params']['expression']

        # Verify script has Promise structure and scrollTo
        assert 'new Promise' in script or 'Promise' in script
        assert 'scrollTo' in script
        assert 'top: 0' in script

    @pytest.mark.asyncio
    async def test_to_bottom_script_structure(self, scroll_api, mock_tab):
        """Test that scroll.to_bottom generates correct script structure."""
        await scroll_api.to_bottom(smooth=True)

        call_args = mock_tab._execute_command.call_args
        command = call_args[0][0]
        script = command['params']['expression']

        # Verify script has Promise structure and scrollHeight
        assert 'new Promise' in script or 'Promise' in script
        assert 'scrollTo' in script
        assert 'scrollHeight' in script


class TestScrollAPIAwaitPromise:
    """Test that awaitPromise parameter is correctly set."""

    @pytest.mark.asyncio
    async def test_scroll_by_uses_await_promise(self, scroll_api, mock_tab):
        """Test that scroll.by uses awaitPromise parameter."""
        await scroll_api.by(ScrollPosition.DOWN, 100, smooth=True)

        call_args = mock_tab._execute_command.call_args
        command = call_args[0][0]

        # Verify awaitPromise is True
        assert command['params']['awaitPromise'] is True

    @pytest.mark.asyncio
    async def test_to_top_uses_await_promise(self, scroll_api, mock_tab):
        """Test that scroll.to_top uses awaitPromise parameter."""
        await scroll_api.to_top(smooth=True)

        call_args = mock_tab._execute_command.call_args
        command = call_args[0][0]

        assert command['params']['awaitPromise'] is True

    @pytest.mark.asyncio
    async def test_to_bottom_uses_await_promise(self, scroll_api, mock_tab):
        """Test that scroll.to_bottom uses awaitPromise parameter."""
        await scroll_api.to_bottom(smooth=True)

        call_args = mock_tab._execute_command.call_args
        command = call_args[0][0]

        assert command['params']['awaitPromise'] is True

