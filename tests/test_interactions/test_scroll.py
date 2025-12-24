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
        assert 'top: 500' in script
        assert "behavior: 'smooth'" in script

    @pytest.mark.asyncio
    async def test_scroll_up_smooth(self, scroll_api, mock_tab):
        """Test scrolling up with smooth animation."""
        await scroll_api.by(ScrollPosition.UP, 300, smooth=True)

        call_args = mock_tab._execute_command.call_args
        command = call_args[0][0]
        script = command['params']['expression']

        assert 'top: -300' in script
        assert "behavior: 'smooth'" in script

    @pytest.mark.asyncio
    async def test_scroll_right_smooth(self, scroll_api, mock_tab):
        """Test scrolling right with smooth animation."""
        await scroll_api.by(ScrollPosition.RIGHT, 200, smooth=True)

        call_args = mock_tab._execute_command.call_args
        command = call_args[0][0]
        script = command['params']['expression']

        assert 'left: 200' in script
        assert "behavior: 'smooth'" in script

    @pytest.mark.asyncio
    async def test_scroll_left_smooth(self, scroll_api, mock_tab):
        """Test scrolling left with smooth animation."""
        await scroll_api.by(ScrollPosition.LEFT, 150, smooth=True)

        call_args = mock_tab._execute_command.call_args
        command = call_args[0][0]
        script = command['params']['expression']

        assert 'left: -150' in script
        assert "behavior: 'smooth'" in script

    @pytest.mark.asyncio
    async def test_scroll_down_instant(self, scroll_api, mock_tab):
        """Test scrolling down without smooth animation."""
        await scroll_api.by(ScrollPosition.DOWN, 1000, smooth=False)

        call_args = mock_tab._execute_command.call_args
        command = call_args[0][0]
        script = command['params']['expression']

        assert 'top: 1000' in script
        assert "behavior: 'auto'" in script

    @pytest.mark.asyncio
    async def test_scroll_with_float_distance(self, scroll_api, mock_tab):
        """Test scrolling with float distance."""
        await scroll_api.by(ScrollPosition.DOWN, 250.5, smooth=True)

        call_args = mock_tab._execute_command.call_args
        command = call_args[0][0]
        script = command['params']['expression']

        assert 'top: 250.5' in script


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
        assert distance == 100

    def test_get_axis_and_distance_up(self, scroll_api):
        """Test _get_axis_and_distance for UP direction."""
        axis, distance = scroll_api._get_axis_and_distance(ScrollPosition.UP, 100)
        assert axis == 'top'
        assert distance == -100

    def test_get_axis_and_distance_right(self, scroll_api):
        """Test _get_axis_and_distance for RIGHT direction."""
        axis, distance = scroll_api._get_axis_and_distance(ScrollPosition.RIGHT, 50)
        assert axis == 'left'
        assert distance == 50

    def test_get_axis_and_distance_left(self, scroll_api):
        """Test _get_axis_and_distance for LEFT direction."""
        axis, distance = scroll_api._get_axis_and_distance(ScrollPosition.LEFT, 50)
        assert axis == 'left'
        assert distance == -50

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


class TestScrollTimingConfig:
    """Test ScrollTimingConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        from pydoll.interactions.scroll import ScrollTimingConfig

        config = ScrollTimingConfig()

        assert config.min_duration == 0.5
        assert config.max_duration == 1.5
        assert config.bezier_points == (0.645, 0.045, 0.355, 1.0)
        assert config.frame_interval == 0.012
        assert config.delta_jitter == 3
        assert config.micro_pause_probability == 0.05
        assert config.micro_pause_min == 0.02
        assert config.micro_pause_max == 0.05
        assert config.overshoot_probability == 0.15
        assert config.overshoot_factor_min == 1.02
        assert config.overshoot_factor_max == 1.08

    def test_custom_values(self):
        """Test custom configuration values."""
        from pydoll.interactions.scroll import ScrollTimingConfig

        config = ScrollTimingConfig(
            min_duration=0.3,
            max_duration=2.0,
            bezier_points=(0.5, 0.0, 0.5, 1.0),
            frame_interval=0.016,
            delta_jitter=5,
            micro_pause_probability=0.1,
            overshoot_probability=0.2,
        )

        assert config.min_duration == 0.3
        assert config.max_duration == 2.0
        assert config.bezier_points == (0.5, 0.0, 0.5, 1.0)
        assert config.frame_interval == 0.016
        assert config.delta_jitter == 5
        assert config.micro_pause_probability == 0.1
        assert config.overshoot_probability == 0.2

    def test_frozen_dataclass(self):
        """Test that config is immutable (frozen)."""
        from pydoll.interactions.scroll import ScrollTimingConfig

        config = ScrollTimingConfig()

        with pytest.raises(AttributeError):
            config.min_duration = 1.0


class TestCubicBezier:
    """Test CubicBezier curve solver."""

    def test_initialization(self):
        """Test CubicBezier initialization with control points."""
        from pydoll.interactions.scroll import CubicBezier

        bezier = CubicBezier(0.25, 0.1, 0.25, 1.0)

        # Verify coefficients are calculated
        assert hasattr(bezier, 'coefficient_a_x')
        assert hasattr(bezier, 'coefficient_b_x')
        assert hasattr(bezier, 'coefficient_c_x')
        assert hasattr(bezier, 'coefficient_a_y')
        assert hasattr(bezier, 'coefficient_b_y')
        assert hasattr(bezier, 'coefficient_c_y')

    def test_sample_curve_x_at_zero(self):
        """Test sample_curve_x returns 0 at t=0."""
        from pydoll.interactions.scroll import CubicBezier

        bezier = CubicBezier(0.25, 0.1, 0.25, 1.0)

        assert bezier.sample_curve_x(0.0) == 0.0

    def test_sample_curve_x_at_one(self):
        """Test sample_curve_x returns 1 at t=1."""
        from pydoll.interactions.scroll import CubicBezier

        bezier = CubicBezier(0.25, 0.1, 0.25, 1.0)

        assert abs(bezier.sample_curve_x(1.0) - 1.0) < 1e-10

    def test_sample_curve_y_at_zero(self):
        """Test sample_curve_y returns 0 at t=0."""
        from pydoll.interactions.scroll import CubicBezier

        bezier = CubicBezier(0.25, 0.1, 0.25, 1.0)

        assert bezier.sample_curve_y(0.0) == 0.0

    def test_sample_curve_y_at_one(self):
        """Test sample_curve_y returns 1 at t=1."""
        from pydoll.interactions.scroll import CubicBezier

        bezier = CubicBezier(0.25, 0.1, 0.25, 1.0)

        assert abs(bezier.sample_curve_y(1.0) - 1.0) < 1e-10

    def test_sample_curve_derivative_x(self):
        """Test sample_curve_derivative_x returns derivative."""
        from pydoll.interactions.scroll import CubicBezier

        bezier = CubicBezier(0.25, 0.1, 0.25, 1.0)

        # Derivative at t=0 should equal coefficient_c_x
        assert bezier.sample_curve_derivative_x(0.0) == bezier.coefficient_c_x

    def test_solve_curve_x_finds_t_for_x(self):
        """Test solve_curve_x finds t value for given x."""
        from pydoll.interactions.scroll import CubicBezier

        bezier = CubicBezier(0.25, 0.1, 0.25, 1.0)

        # For x=0, t should be 0
        assert abs(bezier.solve_curve_x(0.0)) < 1e-6

        # For x=1, t should be 1
        assert abs(bezier.solve_curve_x(1.0) - 1.0) < 1e-6

    def test_solve_returns_y_for_given_x(self):
        """Test solve returns y value for given x (time)."""
        from pydoll.interactions.scroll import CubicBezier

        bezier = CubicBezier(0.25, 0.1, 0.25, 1.0)

        # At x=0, y should be 0
        assert abs(bezier.solve(0.0)) < 1e-6

        # At x=1, y should be 1
        assert abs(bezier.solve(1.0) - 1.0) < 1e-6

    def test_solve_returns_values_between_0_and_1(self):
        """Test solve returns values in valid range for valid inputs."""
        from pydoll.interactions.scroll import CubicBezier

        bezier = CubicBezier(0.645, 0.045, 0.355, 1.0)

        for x in [0.1, 0.25, 0.5, 0.75, 0.9]:
            y = bezier.solve(x)
            assert 0.0 <= y <= 1.0, f"y={y} out of range for x={x}"

    def test_solve_curve_x_with_out_of_range_values(self):
        """Test solve_curve_x behavior with out of range values."""
        from pydoll.interactions.scroll import CubicBezier

        bezier = CubicBezier(0.25, 0.1, 0.25, 1.0)

        # Newton's method will try to find t even for out-of-range x values
        # Just verify it returns a numeric result without crashing
        result_negative = bezier.solve_curve_x(-0.5)
        assert isinstance(result_negative, float)

        result_over_one = bezier.solve_curve_x(1.5)
        assert isinstance(result_over_one, float)

    def test_ease_in_out_bezier(self):
        """Test standard ease-in-out bezier curve."""
        from pydoll.interactions.scroll import CubicBezier

        # Standard CSS ease-in-out
        bezier = CubicBezier(0.42, 0.0, 0.58, 1.0)

        # At midpoint (x=0.5), y should be approximately 0.5
        y_at_half = bezier.solve(0.5)
        assert 0.4 <= y_at_half <= 0.6

    def test_linear_bezier(self):
        """Test linear bezier curve (identity)."""
        from pydoll.interactions.scroll import CubicBezier

        # Linear: control points on the diagonal
        bezier = CubicBezier(0.0, 0.0, 1.0, 1.0)

        # Should be approximately linear
        for x in [0.1, 0.3, 0.5, 0.7, 0.9]:
            y = bezier.solve(x)
            assert abs(y - x) < 0.1, f"Expected y≈{x}, got {y}"


class TestScrollHumanizedMethods:
    """Test humanized scroll methods."""

    @pytest.mark.asyncio
    async def test_scroll_by_with_humanize_true(self, mock_tab):
        """Test scroll.by with humanize=True calls _scroll_humanized."""
        from pydoll.interactions.scroll import Scroll

        scroll = Scroll(mock_tab)

        # Mock _scroll_humanized
        scroll._scroll_humanized = AsyncMock()

        await scroll.by(ScrollPosition.DOWN, 500, humanize=True)

        scroll._scroll_humanized.assert_called_once_with(ScrollPosition.DOWN, 500)

    @pytest.mark.asyncio
    async def test_scroll_to_top_with_humanize_true(self, mock_tab):
        """Test scroll.to_top with humanize=True calls _scroll_to_end_humanized."""
        from pydoll.interactions.scroll import Scroll

        scroll = Scroll(mock_tab)

        # Mock _scroll_to_end_humanized
        scroll._scroll_to_end_humanized = AsyncMock()

        await scroll.to_top(humanize=True)

        scroll._scroll_to_end_humanized.assert_called_once_with(ScrollPosition.UP)

    @pytest.mark.asyncio
    async def test_scroll_to_bottom_with_humanize_true(self, mock_tab):
        """Test scroll.to_bottom with humanize=True calls _scroll_to_end_humanized."""
        from pydoll.interactions.scroll import Scroll

        scroll = Scroll(mock_tab)

        # Mock _scroll_to_end_humanized
        scroll._scroll_to_end_humanized = AsyncMock()

        await scroll.to_bottom(humanize=True)

        scroll._scroll_to_end_humanized.assert_called_once_with(ScrollPosition.DOWN)

    @pytest.mark.asyncio
    async def test_calculate_effective_distance_without_overshoot(self, mock_tab):
        """Test _calculate_effective_distance without overshoot."""
        from pydoll.interactions.scroll import Scroll, ScrollTimingConfig

        # Config with 0% overshoot probability
        config = ScrollTimingConfig(overshoot_probability=0.0)
        scroll = Scroll(mock_tab, timing=config)

        distance = scroll._calculate_effective_distance(100.0)

        assert distance == 100.0

    @pytest.mark.asyncio
    async def test_calculate_effective_distance_with_overshoot(self, mock_tab):
        """Test _calculate_effective_distance with overshoot."""
        from pydoll.interactions.scroll import Scroll, ScrollTimingConfig

        # Config with 100% overshoot probability
        config = ScrollTimingConfig(
            overshoot_probability=1.0,
            overshoot_factor_min=1.1,
            overshoot_factor_max=1.2,
        )
        scroll = Scroll(mock_tab, timing=config)

        distance = scroll._calculate_effective_distance(100.0)

        # Should be between 110 and 120
        assert 110.0 <= distance <= 120.0

    @pytest.mark.asyncio
    async def test_calculate_duration(self, mock_tab):
        """Test _calculate_duration returns value in expected range."""
        from pydoll.interactions.scroll import Scroll, ScrollTimingConfig

        config = ScrollTimingConfig(min_duration=0.5, max_duration=1.5)
        scroll = Scroll(mock_tab, timing=config)

        duration = scroll._calculate_duration(500.0)

        # Should be between min_duration and capped max (3.0)
        assert 0.5 <= duration <= 3.0

    @pytest.mark.asyncio
    async def test_calculate_duration_increases_with_distance(self, mock_tab):
        """Test that longer distances result in longer durations."""
        from pydoll.interactions.scroll import Scroll, ScrollTimingConfig
        from unittest.mock import patch

        config = ScrollTimingConfig(min_duration=0.5, max_duration=1.5)
        scroll = Scroll(mock_tab, timing=config)

        # Patch random.uniform to return a constant base duration
        # This ensures we are testing only the distance scaling logic
        with patch('random.uniform', return_value=1.0):
            short_duration = scroll._calculate_duration(100.0)
            long_duration = scroll._calculate_duration(5000.0)

        # With constant base duration, the formula ensures longer distance -> longer duration
        # Formula: base_duration * (1 + 0.2 * (distance / 1000))
        assert long_duration > short_duration

    @pytest.mark.asyncio
    async def test_get_viewport_center(self, mock_tab):
        """Test _get_viewport_center returns coordinates."""
        from pydoll.interactions.scroll import Scroll

        mock_tab._execute_command.return_value = {
            'result': {'result': {'value': '[800, 600]'}}
        }

        scroll = Scroll(mock_tab)
        result = await scroll._get_viewport_center()

        assert result == (800, 600)

    @pytest.mark.asyncio
    async def test_get_viewport_center_fallback(self, mock_tab):
        """Test _get_viewport_center returns fallback on error."""
        from pydoll.interactions.scroll import Scroll

        mock_tab._execute_command.return_value = {
            'result': {'result': {'value': 'invalid'}}
        }

        scroll = Scroll(mock_tab)
        result = await scroll._get_viewport_center()

        # Should return fallback values
        assert result == (400, 300)

    @pytest.mark.asyncio
    async def test_get_viewport_center_empty_response(self, mock_tab):
        """Test _get_viewport_center handles empty response."""
        from pydoll.interactions.scroll import Scroll

        mock_tab._execute_command.return_value = {}

        scroll = Scroll(mock_tab)
        result = await scroll._get_viewport_center()

        assert result == (400, 300)

    @pytest.mark.asyncio
    async def test_get_current_scroll_y(self, mock_tab):
        """Test _get_current_scroll_y returns scroll position."""
        from pydoll.interactions.scroll import Scroll

        mock_tab._execute_command.return_value = {
            'result': {'result': {'value': 250}}
        }

        scroll = Scroll(mock_tab)
        result = await scroll._get_current_scroll_y()

        assert result == 250.0

    @pytest.mark.asyncio
    async def test_get_current_scroll_y_default(self, mock_tab):
        """Test _get_current_scroll_y returns 0 on missing value."""
        from pydoll.interactions.scroll import Scroll

        mock_tab._execute_command.return_value = {}

        scroll = Scroll(mock_tab)
        result = await scroll._get_current_scroll_y()

        assert result == 0.0

    @pytest.mark.asyncio
    async def test_get_remaining_scroll_to_bottom(self, mock_tab):
        """Test _get_remaining_scroll_to_bottom returns remaining distance."""
        from pydoll.interactions.scroll import Scroll

        mock_tab._execute_command.return_value = {
            'result': {'result': {'value': 1500}}
        }

        scroll = Scroll(mock_tab)
        result = await scroll._get_remaining_scroll_to_bottom()

        assert result == 1500.0

    @pytest.mark.asyncio
    async def test_dispatch_scroll_event(self, mock_tab):
        """Test _dispatch_scroll_event sends mouse wheel event."""
        from pydoll.interactions.scroll import Scroll
        from pydoll.protocol.input.types import MouseEventType

        mock_tab._execute_command.return_value = {
            'result': {'result': {'value': '[400, 300]'}}
        }

        scroll = Scroll(mock_tab)
        await scroll._dispatch_scroll_event(delta_x=0, delta_y=100)

        # Should have called execute_command twice:
        # 1. _get_viewport_center
        # 2. dispatch_mouse_event
        assert mock_tab._execute_command.call_count == 2

        # Check the second call (dispatch_mouse_event)
        second_call = mock_tab._execute_command.call_args_list[1]
        command = second_call[0][0]
        assert command['method'] == 'Input.dispatchMouseEvent'
        assert command['params']['type'] == MouseEventType.MOUSE_WHEEL
        assert command['params']['deltaY'] == 100


class TestScrollWithCustomTiming:
    """Test Scroll with custom timing configuration."""

    def test_scroll_with_custom_timing(self, mock_tab):
        """Test Scroll accepts custom timing configuration."""
        from pydoll.interactions.scroll import Scroll, ScrollTimingConfig

        custom_timing = ScrollTimingConfig(
            min_duration=1.0,
            max_duration=2.0,
        )

        scroll = Scroll(mock_tab, timing=custom_timing)

        assert scroll._timing == custom_timing
        assert scroll._timing.min_duration == 1.0
        assert scroll._timing.max_duration == 2.0

    def test_scroll_uses_default_timing(self, mock_tab):
        """Test Scroll uses default timing if none provided."""
        from pydoll.interactions.scroll import Scroll, ScrollTimingConfig

        scroll = Scroll(mock_tab)

        # Should use default values
        assert scroll._timing.min_duration == 0.5
        assert scroll._timing.max_duration == 1.5


class TestCubicBezierBisectionFallback:
    """Test CubicBezier bisection fallback when Newton's method fails."""

    def test_bisection_fallback_triggered_by_out_of_range_derivative(self):
        """Test that bisection is used when derivative is out of valid range."""
        from pydoll.interactions.scroll import CubicBezier

        # Create a bezier with extreme control points
        # that might cause derivative issues
        bezier = CubicBezier(0.0, 0.0, 1.0, 1.0)  # Linear

        # Should still work correctly
        for x in [0.0, 0.25, 0.5, 0.75, 1.0]:
            result = bezier.solve_curve_x(x)
            assert isinstance(result, float)
            # For linear bezier, t should be close to x
            assert abs(result - x) < 0.1

    def test_bisection_converges_for_edge_cases(self):
        """Test bisection fallback converges for edge case inputs."""
        from pydoll.interactions.scroll import CubicBezier

        bezier = CubicBezier(0.25, 0.1, 0.25, 1.0)

        # Very small values near 0
        result_small = bezier.solve_curve_x(0.001)
        assert isinstance(result_small, float)

        # Values near 1
        result_near_one = bezier.solve_curve_x(0.999)
        assert isinstance(result_near_one, float)

    def test_solve_with_zero_derivative_fallback(self):
        """Test bezier handles cases where derivative could be zero."""
        from pydoll.interactions.scroll import CubicBezier

        # Bezier that starts flat (potential zero derivative at start)
        bezier = CubicBezier(0.0, 0.5, 1.0, 0.5)

        # Should still produce valid results
        for x in [0.1, 0.5, 0.9]:
            result = bezier.solve(x)
            assert 0.0 <= result <= 1.0


class TestScrollHumanized:
    """Test _scroll_humanized method."""

    @pytest.mark.asyncio
    async def test_scroll_humanized_calls_perform_scroll_loop(self, mock_tab):
        """Test _scroll_humanized delegates to _perform_scroll_loop."""
        from pydoll.interactions.scroll import Scroll, ScrollTimingConfig
        from pydoll.constants import ScrollPosition
        from unittest.mock import patch, AsyncMock

        config = ScrollTimingConfig(overshoot_probability=0.0)  # No overshoot
        scroll = Scroll(mock_tab, timing=config)

        # Mock the internal method
        scroll._perform_scroll_loop = AsyncMock(return_value=100.0)

        with patch('asyncio.sleep', new_callable=AsyncMock):
            await scroll._scroll_humanized(ScrollPosition.DOWN, 100.0)

        scroll._perform_scroll_loop.assert_called_once()

    @pytest.mark.asyncio
    async def test_scroll_humanized_with_overshoot_triggers_correction(self, mock_tab):
        """Test _scroll_humanized calls correction when overshoot occurs."""
        from pydoll.interactions.scroll import Scroll, ScrollTimingConfig
        from pydoll.constants import ScrollPosition
        from unittest.mock import patch, AsyncMock

        # Force overshoot
        config = ScrollTimingConfig(
            overshoot_probability=1.0,
            overshoot_factor_min=1.1,
            overshoot_factor_max=1.2,
        )
        scroll = Scroll(mock_tab, timing=config)

        # Mock scroll_loop to return more than target (simulating overshoot)
        scroll._perform_scroll_loop = AsyncMock(return_value=120.0)
        scroll._scroll_correction = AsyncMock()

        with patch('asyncio.sleep', new_callable=AsyncMock):
            await scroll._scroll_humanized(ScrollPosition.DOWN, 100.0)

        # Correction should be called because scrolled (120) > target (100)
        scroll._scroll_correction.assert_called_once()


class TestScrollToEndHumanized:
    """Test _scroll_to_end_humanized method."""

    @pytest.mark.asyncio
    async def test_scroll_to_end_down_calls_humanized_scroll(self, mock_tab):
        """Test scrolling to bottom uses _scroll_humanized in loop."""
        from pydoll.interactions.scroll import Scroll
        from pydoll.constants import ScrollPosition
        from unittest.mock import patch, AsyncMock

        scroll = Scroll(mock_tab)

        # First call: lots remaining, second call: none remaining
        call_count = [0]
        async def mock_remaining():
            call_count[0] += 1
            return 500.0 if call_count[0] == 1 else 0.0

        scroll._get_remaining_scroll_to_bottom = mock_remaining
        scroll._scroll_humanized = AsyncMock()

        with patch('asyncio.sleep', new_callable=AsyncMock):
            await scroll._scroll_to_end_humanized(ScrollPosition.DOWN)

        # Should have called _scroll_humanized at least once
        assert scroll._scroll_humanized.call_count >= 1

    @pytest.mark.asyncio
    async def test_scroll_to_end_up_uses_current_scroll_y(self, mock_tab):
        """Test scrolling to top checks current scroll position."""
        from pydoll.interactions.scroll import Scroll
        from pydoll.constants import ScrollPosition
        from unittest.mock import patch, AsyncMock

        scroll = Scroll(mock_tab)

        # First call: has scroll position, second call: at top
        call_count = [0]
        async def mock_scroll_y():
            call_count[0] += 1
            return 300.0 if call_count[0] == 1 else 0.0

        scroll._get_current_scroll_y = mock_scroll_y
        scroll._scroll_humanized = AsyncMock()

        with patch('asyncio.sleep', new_callable=AsyncMock):
            await scroll._scroll_to_end_humanized(ScrollPosition.UP)

        # Should have called _scroll_humanized
        assert scroll._scroll_humanized.call_count >= 1

    @pytest.mark.asyncio
    async def test_scroll_to_end_stops_when_threshold_reached(self, mock_tab):
        """Test loop stops when remaining distance is below threshold."""
        from pydoll.interactions.scroll import Scroll
        from pydoll.constants import ScrollPosition
        from unittest.mock import patch, AsyncMock

        scroll = Scroll(mock_tab)

        # Return value below threshold (30)
        scroll._get_remaining_scroll_to_bottom = AsyncMock(return_value=10.0)
        scroll._scroll_humanized = AsyncMock()

        with patch('asyncio.sleep', new_callable=AsyncMock):
            await scroll._scroll_to_end_humanized(ScrollPosition.DOWN)

        # Should NOT have called _scroll_humanized (already at end)
        scroll._scroll_humanized.assert_not_called()

    @pytest.mark.asyncio
    async def test_scroll_to_end_stops_when_stuck(self, mock_tab):
        """Test loop stops when scroll progress is stuck."""
        from pydoll.interactions.scroll import Scroll
        from pydoll.constants import ScrollPosition
        from unittest.mock import patch, AsyncMock

        scroll = Scroll(mock_tab)

        # Always return same remaining distance (stuck)
        scroll._get_remaining_scroll_to_bottom = AsyncMock(return_value=500.0)
        scroll._scroll_humanized = AsyncMock()

        with patch('asyncio.sleep', new_callable=AsyncMock):
            await scroll._scroll_to_end_humanized(ScrollPosition.DOWN)

        # Should have tried a few times then given up
        # We set max_stuck_attempts = 10, so it should be around 10 calls
        assert scroll._scroll_humanized.call_count >= 10
        assert scroll._scroll_humanized.call_count < 20  # Should not loop infinitely


class TestPerformScrollLoop:
    """Test _perform_scroll_loop method."""

    @pytest.mark.asyncio
    async def test_perform_scroll_loop_dispatches_events(self, mock_tab):
        """Test scroll loop dispatches mouse wheel events."""
        from pydoll.interactions.scroll import Scroll, ScrollTimingConfig
        from unittest.mock import patch, AsyncMock, MagicMock

        mock_tab._execute_command.return_value = {
            'result': {'result': {'value': '[400, 300]'}}
        }

        config = ScrollTimingConfig(
            min_duration=0.01,
            max_duration=0.02,
            frame_interval=0.001,
            micro_pause_probability=0.0,
        )
        scroll = Scroll(mock_tab, timing=config)

        # Mock time to advance in steps
        # Start at 0, then 0.005 (halfway), then 0.02 (end)
        mock_loop = MagicMock()
        mock_loop.time.side_effect = [0.0, 0.005, 0.02]

        with patch('asyncio.get_running_loop', return_value=mock_loop):
            with patch('asyncio.sleep', new_callable=AsyncMock):
                scrolled = await scroll._perform_scroll_loop(
                    effective_distance=100.0,
                    duration=0.01,
                    is_vertical=True,
                    direction=1,
                )

        # Should have dispatched at least one event
        assert mock_tab._execute_command.call_count >= 1
        assert isinstance(scrolled, float)

    @pytest.mark.asyncio
    async def test_perform_scroll_loop_horizontal(self, mock_tab):
        """Test scroll loop handles horizontal scrolling."""
        from pydoll.interactions.scroll import Scroll, ScrollTimingConfig
        from unittest.mock import patch, AsyncMock

        mock_tab._execute_command.return_value = {
            'result': {'result': {'value': '[400, 300]'}}
        }

        config = ScrollTimingConfig(
            min_duration=0.01,
            max_duration=0.02,
            frame_interval=0.001,
            micro_pause_probability=0.0,
        )
        scroll = Scroll(mock_tab, timing=config)

        with patch('asyncio.sleep', new_callable=AsyncMock):
            scrolled = await scroll._perform_scroll_loop(
                effective_distance=50.0,
                duration=0.01,
                is_vertical=False,  # Horizontal
                direction=-1,  # Left
            )

        assert isinstance(scrolled, float)

    @pytest.mark.asyncio
    async def test_perform_scroll_loop_returns_scrolled_amount(self, mock_tab):
        """Test scroll loop returns total scrolled distance."""
        from pydoll.interactions.scroll import Scroll, ScrollTimingConfig
        from unittest.mock import patch, AsyncMock

        mock_tab._execute_command.return_value = {
            'result': {'result': {'value': '[400, 300]'}}
        }

        config = ScrollTimingConfig(
            min_duration=0.05,
            max_duration=0.05,
            frame_interval=0.001,
            micro_pause_probability=0.0,
            delta_jitter=0,  # No jitter for predictable test
        )
        scroll = Scroll(mock_tab, timing=config)

        with patch('asyncio.sleep', new_callable=AsyncMock):
            scrolled = await scroll._perform_scroll_loop(
                effective_distance=100.0,
                duration=0.05,
                is_vertical=True,
                direction=1,
            )

        # Should have scrolled some amount
        assert scrolled > 0



class TestScrollCorrection:
    """Test _scroll_correction method."""

    @pytest.mark.asyncio
    async def test_scroll_correction_dispatches_scroll_events(self, mock_tab):
        """Test correction dispatches scroll events progressively."""
        from pydoll.interactions.scroll import Scroll, ScrollTimingConfig
        from unittest.mock import AsyncMock
        import asyncio

        config = ScrollTimingConfig(frame_interval=0.001)
        scroll = Scroll(mock_tab, timing=config)

        # Track calls to _dispatch_scroll_event
        dispatch_calls = []
        original_dispatch = scroll._dispatch_scroll_event

        async def tracking_dispatch(delta_x, delta_y):
            dispatch_calls.append((delta_x, delta_y))

        scroll._dispatch_scroll_event = tracking_dispatch

        # Run with timeout to prevent hanging
        try:
            await asyncio.wait_for(
                scroll._scroll_correction(
                    is_vertical=True,
                    direction=-1,
                    distance=10.0,
                ),
                timeout=2.0,
            )
        except asyncio.TimeoutError:
            pass  # Test passed if we got here with some calls

        # Should have dispatched at least one event
        assert len(dispatch_calls) >= 1

    @pytest.mark.asyncio
    async def test_scroll_correction_horizontal(self, mock_tab):
        """Test correction works for horizontal scrolling."""
        from pydoll.interactions.scroll import Scroll, ScrollTimingConfig
        import asyncio

        # Use larger frame_interval so delta is >= 1
        config = ScrollTimingConfig(frame_interval=0.01)
        scroll = Scroll(mock_tab, timing=config)

        dispatch_calls = []

        async def tracking_dispatch(delta_x, delta_y):
            dispatch_calls.append((delta_x, delta_y))

        scroll._dispatch_scroll_event = tracking_dispatch

        try:
            await asyncio.wait_for(
                scroll._scroll_correction(
                    is_vertical=False,
                    direction=1,
                    distance=10.0,
                ),
                timeout=2.0,
            )
        except asyncio.TimeoutError:
            pass

        # Should have dispatched at least one event
        assert len(dispatch_calls) >= 1

    @pytest.mark.asyncio
    async def test_scroll_correction_velocity_decreases(self, mock_tab):
        """Test correction velocity decreases over time."""
        from pydoll.interactions.scroll import Scroll, ScrollTimingConfig
        import asyncio

        config = ScrollTimingConfig(frame_interval=0.001)
        scroll = Scroll(mock_tab, timing=config)

        call_deltas = []

        async def tracking_dispatch(delta_x, delta_y):
            call_deltas.append(abs(delta_y))

        scroll._dispatch_scroll_event = tracking_dispatch

        try:
            await asyncio.wait_for(
                scroll._scroll_correction(
                    is_vertical=True,
                    direction=1,
                    distance=50.0,
                ),
                timeout=2.0,
            )
        except asyncio.TimeoutError:
            pass

        # Velocity should be decreasing (later deltas smaller)
        if len(call_deltas) >= 2:
            assert call_deltas[0] >= call_deltas[-1]


class TestPublicMethodsWithHumanize:
    """Test that public methods correctly route to humanized methods."""

    @pytest.mark.asyncio
    async def test_by_with_humanize_calls_scroll_humanized(self, mock_tab):
        """Test by() with humanize=True routes to _scroll_humanized."""
        from pydoll.interactions.scroll import Scroll
        from pydoll.constants import ScrollPosition
        from unittest.mock import AsyncMock

        scroll = Scroll(mock_tab)
        scroll._scroll_humanized = AsyncMock()

        await scroll.by(ScrollPosition.DOWN, 100, humanize=True)

        scroll._scroll_humanized.assert_called_once_with(ScrollPosition.DOWN, 100)

    @pytest.mark.asyncio
    async def test_to_top_with_humanize_calls_scroll_to_end_humanized(self, mock_tab):
        """Test to_top() with humanize=True routes to _scroll_to_end_humanized."""
        from pydoll.interactions.scroll import Scroll
        from pydoll.constants import ScrollPosition
        from unittest.mock import AsyncMock

        scroll = Scroll(mock_tab)
        scroll._scroll_to_end_humanized = AsyncMock()

        await scroll.to_top(humanize=True)

        scroll._scroll_to_end_humanized.assert_called_once_with(ScrollPosition.UP)

    @pytest.mark.asyncio
    async def test_to_bottom_with_humanize_calls_scroll_to_end_humanized(self, mock_tab):
        """Test to_bottom() with humanize=True routes to _scroll_to_end_humanized."""
        from pydoll.interactions.scroll import Scroll
        from pydoll.constants import ScrollPosition
        from unittest.mock import AsyncMock

        scroll = Scroll(mock_tab)
        scroll._scroll_to_end_humanized = AsyncMock()

        await scroll.to_bottom(humanize=True)

        scroll._scroll_to_end_humanized.assert_called_once_with(ScrollPosition.DOWN)


class TestScrollAPIBackwardCompatibility:
    """Test backward compatibility alias."""

    def test_scroll_api_alias(self):
        """Test ScrollAPI is an alias for Scroll."""
        from pydoll.interactions.scroll import Scroll, ScrollAPI

        assert ScrollAPI is Scroll
