import math

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from pydoll.interactions.mouse import Mouse, MouseAPI, MouseTimingConfig
from pydoll.interactions.utils import (
    bezier_2d,
    fitts_duration,
    minimum_jerk,
    random_control_points,
)
from pydoll.protocol.input.types import MouseButton, MouseEventType


@pytest_asyncio.fixture
async def mock_tab():
    """Mock Tab instance for Mouse tests."""
    tab = MagicMock()
    tab._execute_command = AsyncMock()
    return tab


@pytest_asyncio.fixture
async def mouse(mock_tab):
    """Create Mouse instance with mocked tab."""
    return Mouse(mock_tab)


# ── MouseTimingConfig ──────────────────────────────────────────────────


class TestMouseTimingConfig:
    """Test MouseTimingConfig dataclass."""

    def test_default_values(self):
        config = MouseTimingConfig()
        assert config.fitts_a == 0.070
        assert config.fitts_b == 0.150
        assert config.frame_interval == 0.012
        assert config.frame_interval_variance == 0.004
        assert config.curvature_min == 0.10
        assert config.curvature_max == 0.30
        assert config.curvature_asymmetry == 0.6
        assert config.short_distance_threshold == 50.0
        assert config.tremor_amplitude == 1.0
        assert config.overshoot_probability == 0.70
        assert config.overshoot_distance_min == 0.03
        assert config.overshoot_distance_max == 0.12
        assert config.overshoot_speed_threshold == 200.0
        assert config.pre_click_pause_min == 0.05
        assert config.pre_click_pause_max == 0.20
        assert config.click_hold_min == 0.05
        assert config.click_hold_max == 0.15
        assert config.double_click_interval_min == 0.05
        assert config.double_click_interval_max == 0.10
        assert config.drag_start_pause_min == 0.08
        assert config.drag_start_pause_max == 0.20
        assert config.drag_end_pause_min == 0.05
        assert config.drag_end_pause_max == 0.15
        assert config.micro_pause_probability == 0.03
        assert config.micro_pause_min == 0.015
        assert config.micro_pause_max == 0.04
        assert config.min_duration == 0.08
        assert config.max_duration == 2.5

    def test_custom_values(self):
        config = MouseTimingConfig(fitts_a=0.1, fitts_b=0.2, tremor_amplitude=2.0)
        assert config.fitts_a == 0.1
        assert config.fitts_b == 0.2
        assert config.tremor_amplitude == 2.0

    def test_frozen_dataclass(self):
        config = MouseTimingConfig()
        with pytest.raises(AttributeError):
            config.fitts_a = 1.0


# ── Mouse Initialization ──────────────────────────────────────────────


class TestMouseInitialization:
    """Test Mouse initialization."""

    def test_initialization(self, mock_tab):
        mouse = Mouse(mock_tab)
        assert mouse._tab == mock_tab
        assert isinstance(mouse._timing, MouseTimingConfig)
        assert mouse._position == (0.0, 0.0)

    def test_initialization_with_custom_timing(self, mock_tab):
        config = MouseTimingConfig(fitts_a=0.1)
        mouse = Mouse(mock_tab, timing=config)
        assert mouse._timing.fitts_a == 0.1

    def test_initial_position_is_origin(self, mock_tab):
        mouse = Mouse(mock_tab)
        assert mouse._position == (0.0, 0.0)


# ── Mouse.move() ──────────────────────────────────────────────────────


class TestMouseMove:
    """Test Mouse.move() method."""

    @pytest.mark.asyncio
    async def test_move_dispatches_mouse_moved(self, mouse, mock_tab):
        await mouse.move(100, 200, humanize=False)

        assert mock_tab._execute_command.called
        command = mock_tab._execute_command.call_args[0][0]
        assert command['method'] == 'Input.dispatchMouseEvent'
        assert command['params']['type'] == MouseEventType.MOUSE_MOVED
        assert command['params']['x'] == 100
        assert command['params']['y'] == 200

    @pytest.mark.asyncio
    async def test_move_updates_position(self, mouse):
        await mouse.move(150, 250, humanize=False)
        assert mouse._position == (150, 250)

    @pytest.mark.asyncio
    async def test_move_rounds_float_coordinates(self, mouse, mock_tab):
        await mouse.move(99.7, 200.3, humanize=False)

        command = mock_tab._execute_command.call_args[0][0]
        assert command['params']['x'] == 100
        assert command['params']['y'] == 200

    @pytest.mark.asyncio
    async def test_move_single_event_when_not_humanized(self, mouse, mock_tab):
        await mouse.move(100, 200, humanize=False)
        assert mock_tab._execute_command.call_count == 1

    @pytest.mark.asyncio
    async def test_move_humanize_delegates_to_humanized(self, mouse):
        with patch.object(mouse, '_move_humanized', new_callable=AsyncMock) as mock_method:
            await mouse.move(100, 200, humanize=True)
            mock_method.assert_called_once_with(100, 200)


# ── Mouse.click() ─────────────────────────────────────────────────────


class TestMouseClick:
    """Test Mouse.click() method."""

    @pytest.mark.asyncio
    async def test_click_dispatches_move_press_release(self, mouse, mock_tab):
        await mouse.click(300, 400, humanize=False)

        # 3 calls: move + pressed + released
        assert mock_tab._execute_command.call_count == 3

        commands = [call[0][0] for call in mock_tab._execute_command.call_args_list]
        assert commands[0]['params']['type'] == MouseEventType.MOUSE_MOVED
        assert commands[1]['params']['type'] == MouseEventType.MOUSE_PRESSED
        assert commands[2]['params']['type'] == MouseEventType.MOUSE_RELEASED

    @pytest.mark.asyncio
    async def test_click_left_button_default(self, mouse, mock_tab):
        await mouse.click(300, 400, humanize=False)

        commands = [call[0][0] for call in mock_tab._execute_command.call_args_list]
        assert commands[1]['params']['button'] == MouseButton.LEFT
        assert commands[2]['params']['button'] == MouseButton.LEFT

    @pytest.mark.asyncio
    async def test_click_right_button(self, mouse, mock_tab):
        await mouse.click(300, 400, button=MouseButton.RIGHT, humanize=False)

        commands = [call[0][0] for call in mock_tab._execute_command.call_args_list]
        assert commands[1]['params']['button'] == MouseButton.RIGHT

    @pytest.mark.asyncio
    async def test_click_with_click_count(self, mouse, mock_tab):
        await mouse.click(300, 400, click_count=2, humanize=False)

        commands = [call[0][0] for call in mock_tab._execute_command.call_args_list]
        assert commands[1]['params']['clickCount'] == 2
        assert commands[2]['params']['clickCount'] == 2

    @pytest.mark.asyncio
    async def test_click_updates_position(self, mouse):
        await mouse.click(300, 400, humanize=False)
        assert mouse._position == (300, 400)

    @pytest.mark.asyncio
    async def test_click_position_in_press_release(self, mouse, mock_tab):
        await mouse.click(300, 400, humanize=False)

        commands = [call[0][0] for call in mock_tab._execute_command.call_args_list]
        assert commands[1]['params']['x'] == 300
        assert commands[1]['params']['y'] == 400
        assert commands[2]['params']['x'] == 300
        assert commands[2]['params']['y'] == 400

    @pytest.mark.asyncio
    async def test_click_humanize_delegates(self, mouse):
        with patch.object(mouse, '_click_humanized', new_callable=AsyncMock) as mock_method:
            await mouse.click(300, 400, humanize=True)
            mock_method.assert_called_once_with(300, 400, MouseButton.LEFT, 1)


# ── Mouse.double_click() ──────────────────────────────────────────────


class TestMouseDoubleClick:
    """Test Mouse.double_click() method."""

    @pytest.mark.asyncio
    async def test_double_click_delegates_to_click(self, mouse):
        with patch.object(mouse, 'click', new_callable=AsyncMock) as mock_click:
            await mouse.double_click(500, 600)
            mock_click.assert_called_once_with(
                500, 600, button=MouseButton.LEFT, click_count=2, humanize=True
            )

    @pytest.mark.asyncio
    async def test_double_click_right_button(self, mouse):
        with patch.object(mouse, 'click', new_callable=AsyncMock) as mock_click:
            await mouse.double_click(500, 600, button=MouseButton.RIGHT)
            mock_click.assert_called_once_with(
                500, 600, button=MouseButton.RIGHT, click_count=2, humanize=True
            )

    @pytest.mark.asyncio
    async def test_double_click_humanized(self, mouse):
        with patch.object(mouse, 'click', new_callable=AsyncMock) as mock_click:
            await mouse.double_click(500, 600, humanize=True)
            mock_click.assert_called_once_with(
                500, 600, button=MouseButton.LEFT, click_count=2, humanize=True
            )


# ── Mouse.down() ──────────────────────────────────────────────────────


class TestMouseDown:
    """Test Mouse.down() method."""

    @pytest.mark.asyncio
    async def test_down_dispatches_mouse_pressed(self, mouse, mock_tab):
        await mouse.down()

        command = mock_tab._execute_command.call_args[0][0]
        assert command['params']['type'] == MouseEventType.MOUSE_PRESSED
        assert command['params']['button'] == MouseButton.LEFT

    @pytest.mark.asyncio
    async def test_down_at_current_position(self, mouse, mock_tab):
        mouse._position = (100.0, 200.0)
        await mouse.down()

        command = mock_tab._execute_command.call_args[0][0]
        assert command['params']['x'] == 100
        assert command['params']['y'] == 200

    @pytest.mark.asyncio
    async def test_down_with_right_button(self, mouse, mock_tab):
        await mouse.down(button=MouseButton.RIGHT)

        command = mock_tab._execute_command.call_args[0][0]
        assert command['params']['button'] == MouseButton.RIGHT


# ── Mouse.up() ────────────────────────────────────────────────────────


class TestMouseUp:
    """Test Mouse.up() method."""

    @pytest.mark.asyncio
    async def test_up_dispatches_mouse_released(self, mouse, mock_tab):
        await mouse.up()

        command = mock_tab._execute_command.call_args[0][0]
        assert command['params']['type'] == MouseEventType.MOUSE_RELEASED
        assert command['params']['button'] == MouseButton.LEFT

    @pytest.mark.asyncio
    async def test_up_at_current_position(self, mouse, mock_tab):
        mouse._position = (100.0, 200.0)
        await mouse.up()

        command = mock_tab._execute_command.call_args[0][0]
        assert command['params']['x'] == 100
        assert command['params']['y'] == 200

    @pytest.mark.asyncio
    async def test_up_with_right_button(self, mouse, mock_tab):
        await mouse.up(button=MouseButton.RIGHT)

        command = mock_tab._execute_command.call_args[0][0]
        assert command['params']['button'] == MouseButton.RIGHT


# ── Mouse.drag() ──────────────────────────────────────────────────────


class TestMouseDrag:
    """Test Mouse.drag() method."""

    @pytest.mark.asyncio
    async def test_drag_dispatches_correct_sequence(self, mouse, mock_tab):
        await mouse.drag(100, 200, 500, 600, humanize=False)

        assert mock_tab._execute_command.call_count == 4
        commands = [call[0][0] for call in mock_tab._execute_command.call_args_list]

        # move to start, press, move to end, release
        assert commands[0]['params']['type'] == MouseEventType.MOUSE_MOVED
        assert commands[0]['params']['x'] == 100
        assert commands[0]['params']['y'] == 200
        assert commands[1]['params']['type'] == MouseEventType.MOUSE_PRESSED
        assert commands[2]['params']['type'] == MouseEventType.MOUSE_MOVED
        assert commands[2]['params']['x'] == 500
        assert commands[2]['params']['y'] == 600
        assert commands[3]['params']['type'] == MouseEventType.MOUSE_RELEASED

    @pytest.mark.asyncio
    async def test_drag_updates_position_to_end(self, mouse):
        await mouse.drag(100, 200, 500, 600, humanize=False)
        assert mouse._position == (500, 600)

    @pytest.mark.asyncio
    async def test_drag_uses_left_button(self, mouse, mock_tab):
        await mouse.drag(100, 200, 500, 600, humanize=False)

        commands = [call[0][0] for call in mock_tab._execute_command.call_args_list]
        assert commands[1]['params']['button'] == MouseButton.LEFT
        assert commands[3]['params']['button'] == MouseButton.LEFT

    @pytest.mark.asyncio
    async def test_drag_humanize_delegates(self, mouse):
        with patch.object(mouse, '_drag_humanized', new_callable=AsyncMock) as mock_method:
            await mouse.drag(100, 200, 500, 600, humanize=True)
            mock_method.assert_called_once_with(100, 200, 500, 600)


# ── Helper Functions ──────────────────────────────────────────────────


class TestMinimumJerk:
    """Test minimum_jerk function."""

    def test_at_zero(self):
        assert minimum_jerk(0.0) == pytest.approx(0.0)

    def test_at_one(self):
        assert minimum_jerk(1.0) == pytest.approx(1.0)

    def test_at_half(self):
        result = minimum_jerk(0.5)
        assert result == pytest.approx(0.5, abs=0.01)

    def test_monotonic(self):
        values = [minimum_jerk(t / 100.0) for t in range(101)]
        for i in range(len(values) - 1):
            assert values[i + 1] >= values[i]

    def test_stays_in_range(self):
        for t in [i / 20.0 for i in range(21)]:
            result = minimum_jerk(t)
            assert 0.0 <= result <= 1.0


class TestBezier2D:
    """Test bezier_2d function."""

    def test_at_t_zero_returns_p0(self):
        result = bezier_2d(0.0, (0, 0), (1, 1), (2, 2), (3, 3))
        assert result == pytest.approx((0, 0))

    def test_at_t_one_returns_p3(self):
        result = bezier_2d(1.0, (0, 0), (1, 1), (2, 2), (3, 3))
        assert result == pytest.approx((3, 3))

    def test_straight_line_midpoint(self):
        result = bezier_2d(0.5, (0, 0), (1, 0), (2, 0), (3, 0))
        assert result[0] == pytest.approx(1.5, abs=0.01)
        assert result[1] == pytest.approx(0.0, abs=0.01)

    def test_curved_path(self):
        result = bezier_2d(0.5, (0, 0), (0, 10), (10, 10), (10, 0))
        assert 0 < result[0] < 10
        assert result[1] > 0


class TestFittsDuration:
    """Test fitts_duration function."""

    def test_zero_distance(self):
        result = fitts_duration(0, 20, 0.07, 0.15)
        assert result == 0.07

    def test_negative_distance(self):
        result = fitts_duration(-10, 20, 0.07, 0.15)
        assert result == 0.07

    def test_increases_with_distance(self):
        d1 = fitts_duration(100, 20, 0.07, 0.15)
        d2 = fitts_duration(500, 20, 0.07, 0.15)
        assert d2 > d1

    def test_decreases_with_target_width(self):
        d1 = fitts_duration(200, 10, 0.07, 0.15)
        d2 = fitts_duration(200, 50, 0.07, 0.15)
        assert d1 > d2

    def test_known_value(self):
        # D=400, W=20: log2(400/20 + 1) = log2(21) ≈ 4.39
        result = fitts_duration(400, 20, 0.07, 0.15)
        expected = 0.07 + 0.15 * math.log2(21)
        assert result == pytest.approx(expected)


class TestRandomControlPoints:
    """Test random_control_points function."""

    def _call(self, start, end, config=None):
        config = config or MouseTimingConfig()
        return random_control_points(
            start, end,
            config.curvature_min, config.curvature_max,
            config.curvature_asymmetry, config.short_distance_threshold,
        )

    def test_returns_two_points(self):
        cp1, cp2 = self._call((0, 0), (100, 0))
        assert len(cp1) == 2
        assert len(cp2) == 2

    def test_short_distance_returns_start_end(self):
        result = self._call((0, 0), (0.5, 0))
        assert result == ((0, 0), (0.5, 0))

    def test_control_points_not_on_line(self):
        results = []
        for _ in range(20):
            cp1, cp2 = self._call((0, 0), (500, 0))
            results.append(abs(cp1[1]) > 0 or abs(cp2[1]) > 0)
        assert any(results)

    def test_short_distance_reduced_curvature(self):
        short_offsets = []
        long_offsets = []
        for _ in range(50):
            cp1_short, _ = self._call((0, 0), (20, 0))
            cp1_long, _ = self._call((0, 0), (500, 0))
            short_offsets.append(abs(cp1_short[1]))
            long_offsets.append(abs(cp1_long[1]))
        avg_short = sum(short_offsets) / len(short_offsets)
        avg_long = sum(long_offsets) / len(long_offsets)
        assert avg_short < avg_long


# ── Tremor Computation ────────────────────────────────────────────────


class TestComputeTremorSigma:
    """Test Mouse._compute_tremor_sigma static method."""

    def test_zero_dt_returns_full_amplitude(self):
        config = MouseTimingConfig(tremor_amplitude=2.0)
        sigma = Mouse._compute_tremor_sigma(10, 20, 1.0, (5, 10, 1.0), config)
        assert sigma == 2.0

    def test_high_velocity_reduces_tremor(self):
        config = MouseTimingConfig(tremor_amplitude=1.0)
        # High velocity: distance=100px in dt=0.01s -> velocity=10000
        sigma = Mouse._compute_tremor_sigma(100, 0, 1.01, (0, 0, 1.0), config)
        assert sigma == pytest.approx(0.2)  # min speed_factor

    def test_low_velocity_high_tremor(self):
        config = MouseTimingConfig(tremor_amplitude=1.0)
        # Low velocity: distance=1px in dt=0.1s -> velocity=10
        sigma = Mouse._compute_tremor_sigma(1, 0, 1.1, (0, 0, 1.0), config)
        assert sigma > 0.9


# ── Humanized Move ────────────────────────────────────────────────────


class TestMouseHumanizedMove:
    """Test Mouse._move_humanized method."""

    @pytest.mark.asyncio
    async def test_short_distance_single_dispatch(self, mouse, mock_tab):
        mouse._position = (100, 100)
        await mouse._move_humanized(100.5, 100.5)
        assert mock_tab._execute_command.call_count == 1

    @pytest.mark.asyncio
    async def test_dispatches_multiple_events(self, mouse, mock_tab):
        # Use fast timing to reduce test runtime
        mouse._timing = MouseTimingConfig(
            min_duration=0.02,
            max_duration=0.05,
            frame_interval=0.005,
            overshoot_probability=0.0,
            micro_pause_probability=0.0,
        )
        mouse._position = (0, 0)
        await mouse._move_humanized(500, 500)
        # Should have dispatched multiple mouseMoved events
        assert mock_tab._execute_command.call_count > 2

    @pytest.mark.asyncio
    async def test_final_position_is_target(self, mouse, mock_tab):
        mouse._timing = MouseTimingConfig(
            min_duration=0.02,
            max_duration=0.05,
            frame_interval=0.005,
            overshoot_probability=0.0,
            micro_pause_probability=0.0,
        )
        await mouse._move_humanized(300, 400)
        assert mouse._position == (300, 400)

    @pytest.mark.asyncio
    async def test_all_events_are_mouse_moved(self, mouse, mock_tab):
        mouse._timing = MouseTimingConfig(
            min_duration=0.02,
            max_duration=0.05,
            frame_interval=0.005,
            overshoot_probability=0.0,
            micro_pause_probability=0.0,
        )
        await mouse._move_humanized(200, 200)
        for call_item in mock_tab._execute_command.call_args_list:
            command = call_item[0][0]
            assert command['params']['type'] == MouseEventType.MOUSE_MOVED

    @pytest.mark.asyncio
    async def test_longer_distance_more_events(self, mouse, mock_tab):
        mouse._timing = MouseTimingConfig(
            min_duration=0.02,
            max_duration=0.5,
            frame_interval=0.005,
            overshoot_probability=0.0,
            micro_pause_probability=0.0,
        )
        await mouse._move_humanized(50, 50)
        short_count = mock_tab._execute_command.call_count

        mock_tab._execute_command.reset_mock()
        mouse._position = (0, 0)
        await mouse._move_humanized(800, 800)
        long_count = mock_tab._execute_command.call_count

        assert long_count > short_count

    @pytest.mark.asyncio
    async def test_overshoot_moves_past_target(self, mouse, mock_tab):
        mouse._timing = MouseTimingConfig(
            min_duration=0.05,
            max_duration=0.10,
            frame_interval=0.005,
            overshoot_probability=1.0,
            overshoot_speed_threshold=0,
            overshoot_distance_min=0.10,
            overshoot_distance_max=0.15,
            micro_pause_probability=0.0,
        )
        await mouse._move_humanized(500, 0)

        x_coords = [
            call[0][0]['params']['x']
            for call in mock_tab._execute_command.call_args_list
        ]
        assert max(x_coords) > 500


# ── Humanized Click ───────────────────────────────────────────────────


class TestMouseHumanizedClick:
    """Test Mouse._click_humanized method."""

    @pytest.mark.asyncio
    async def test_includes_move_press_release(self, mouse, mock_tab):
        mouse._timing = MouseTimingConfig(
            min_duration=0.01,
            max_duration=0.02,
            frame_interval=0.005,
            overshoot_probability=0.0,
            micro_pause_probability=0.0,
            pre_click_pause_min=0.001,
            pre_click_pause_max=0.001,
            click_hold_min=0.001,
            click_hold_max=0.001,
        )
        await mouse._click_humanized(300, 400, MouseButton.LEFT, 1)

        event_types = [
            call[0][0]['params']['type']
            for call in mock_tab._execute_command.call_args_list
        ]
        # Should contain: multiple MOUSE_MOVED, then MOUSE_PRESSED, then MOUSE_RELEASED
        assert MouseEventType.MOUSE_PRESSED in event_types
        assert MouseEventType.MOUSE_RELEASED in event_types
        moved_count = event_types.count(MouseEventType.MOUSE_MOVED)
        assert moved_count >= 1

    @pytest.mark.asyncio
    async def test_double_click_has_two_press_release_pairs(self, mouse, mock_tab):
        mouse._timing = MouseTimingConfig(
            min_duration=0.01,
            max_duration=0.02,
            frame_interval=0.005,
            overshoot_probability=0.0,
            micro_pause_probability=0.0,
            pre_click_pause_min=0.001,
            pre_click_pause_max=0.001,
            click_hold_min=0.001,
            click_hold_max=0.001,
            double_click_interval_min=0.001,
            double_click_interval_max=0.001,
        )
        await mouse._click_humanized(300, 400, MouseButton.LEFT, 2)

        event_types = [
            call[0][0]['params']['type']
            for call in mock_tab._execute_command.call_args_list
        ]
        assert event_types.count(MouseEventType.MOUSE_PRESSED) == 2
        assert event_types.count(MouseEventType.MOUSE_RELEASED) == 2

    @pytest.mark.asyncio
    async def test_click_count_in_commands(self, mouse, mock_tab):
        mouse._timing = MouseTimingConfig(
            min_duration=0.01,
            max_duration=0.02,
            frame_interval=0.005,
            overshoot_probability=0.0,
            micro_pause_probability=0.0,
            pre_click_pause_min=0.001,
            pre_click_pause_max=0.001,
            click_hold_min=0.001,
            click_hold_max=0.001,
            double_click_interval_min=0.001,
            double_click_interval_max=0.001,
        )
        await mouse._click_humanized(300, 400, MouseButton.LEFT, 2)

        press_commands = [
            call[0][0] for call in mock_tab._execute_command.call_args_list
            if call[0][0]['params']['type'] == MouseEventType.MOUSE_PRESSED
        ]
        assert press_commands[0]['params']['clickCount'] == 1
        assert press_commands[1]['params']['clickCount'] == 2

    @pytest.mark.asyncio
    async def test_click_lands_at_exact_position(self, mouse, mock_tab):
        mouse._timing = MouseTimingConfig(
            min_duration=0.01,
            max_duration=0.02,
            frame_interval=0.005,
            overshoot_probability=0.0,
            micro_pause_probability=0.0,
            pre_click_pause_min=0.001,
            pre_click_pause_max=0.001,
            click_hold_min=0.001,
            click_hold_max=0.001,
        )
        await mouse._click_humanized(300, 400, MouseButton.LEFT, 1)

        press_commands = [
            call[0][0] for call in mock_tab._execute_command.call_args_list
            if call[0][0]['params']['type'] == MouseEventType.MOUSE_PRESSED
        ]
        # Click must land at the exact target position
        assert press_commands[0]['params']['x'] == 300
        assert press_commands[0]['params']['y'] == 400


# ── Humanized Drag ────────────────────────────────────────────────────


class TestMouseHumanizedDrag:
    """Test Mouse._drag_humanized method."""

    @pytest.mark.asyncio
    async def test_drag_includes_press_and_release(self, mouse, mock_tab):
        mouse._timing = MouseTimingConfig(
            min_duration=0.01,
            max_duration=0.02,
            frame_interval=0.005,
            overshoot_probability=0.0,
            micro_pause_probability=0.0,
            drag_start_pause_min=0.001,
            drag_start_pause_max=0.001,
            drag_end_pause_min=0.001,
            drag_end_pause_max=0.001,
        )
        await mouse._drag_humanized(100, 200, 500, 600)

        event_types = [
            call[0][0]['params']['type']
            for call in mock_tab._execute_command.call_args_list
        ]
        assert MouseEventType.MOUSE_PRESSED in event_types
        assert MouseEventType.MOUSE_RELEASED in event_types
        assert event_types.count(MouseEventType.MOUSE_MOVED) >= 2

    @pytest.mark.asyncio
    async def test_drag_ends_at_target(self, mouse, mock_tab):
        mouse._timing = MouseTimingConfig(
            min_duration=0.01,
            max_duration=0.02,
            frame_interval=0.005,
            overshoot_probability=0.0,
            micro_pause_probability=0.0,
            drag_start_pause_min=0.001,
            drag_start_pause_max=0.001,
            drag_end_pause_min=0.001,
            drag_end_pause_max=0.001,
        )
        await mouse._drag_humanized(100, 200, 500, 600)
        assert mouse._position == (500, 600)

    @pytest.mark.asyncio
    async def test_drag_press_before_release(self, mouse, mock_tab):
        mouse._timing = MouseTimingConfig(
            min_duration=0.01,
            max_duration=0.02,
            frame_interval=0.005,
            overshoot_probability=0.0,
            micro_pause_probability=0.0,
            drag_start_pause_min=0.001,
            drag_start_pause_max=0.001,
            drag_end_pause_min=0.001,
            drag_end_pause_max=0.001,
        )
        await mouse._drag_humanized(100, 200, 500, 600)

        event_types = [
            call[0][0]['params']['type']
            for call in mock_tab._execute_command.call_args_list
        ]
        press_idx = event_types.index(MouseEventType.MOUSE_PRESSED)
        release_idx = len(event_types) - 1 - event_types[::-1].index(MouseEventType.MOUSE_RELEASED)
        assert press_idx < release_idx


# ── Dispatch Helpers ──────────────────────────────────────────────────


class TestDispatchMove:
    """Test Mouse._dispatch_move method."""

    @pytest.mark.asyncio
    async def test_dispatches_correct_command(self, mouse, mock_tab):
        await mouse._dispatch_move(150.7, 250.3)

        command = mock_tab._execute_command.call_args[0][0]
        assert command['method'] == 'Input.dispatchMouseEvent'
        assert command['params']['type'] == MouseEventType.MOUSE_MOVED
        assert command['params']['x'] == 151
        assert command['params']['y'] == 250

    @pytest.mark.asyncio
    async def test_updates_position_with_float(self, mouse):
        await mouse._dispatch_move(150.7, 250.3)
        assert mouse._position == (150.7, 250.3)


class TestDispatchButton:
    """Test Mouse._dispatch_button method."""

    @pytest.mark.asyncio
    async def test_dispatches_pressed(self, mouse, mock_tab):
        mouse._position = (100.0, 200.0)
        await mouse._dispatch_button(MouseEventType.MOUSE_PRESSED, MouseButton.LEFT, 1)

        command = mock_tab._execute_command.call_args[0][0]
        assert command['params']['type'] == MouseEventType.MOUSE_PRESSED
        assert command['params']['button'] == MouseButton.LEFT
        assert command['params']['clickCount'] == 1
        assert command['params']['x'] == 100
        assert command['params']['y'] == 200

    @pytest.mark.asyncio
    async def test_dispatches_released(self, mouse, mock_tab):
        mouse._position = (100.0, 200.0)
        await mouse._dispatch_button(MouseEventType.MOUSE_RELEASED, MouseButton.LEFT)

        command = mock_tab._execute_command.call_args[0][0]
        assert command['params']['type'] == MouseEventType.MOUSE_RELEASED


# ── Backward Compatibility ────────────────────────────────────────────


class TestMouseAPIAlias:
    """Test MouseAPI backward compatibility alias."""

    def test_mouse_api_is_mouse(self):
        assert MouseAPI is Mouse


# ── Tab Integration ───────────────────────────────────────────────────


class TestTabMouseProperty:
    """Test tab.mouse lazy property."""

    def test_tab_mouse_property_exists(self):
        from pydoll.browser.tab import Tab
        assert hasattr(Tab, 'mouse')

    def test_tab_mouse_returns_mouse_api(self):
        from pydoll.interactions import MouseAPI
        tab = MagicMock()
        tab._execute_command = AsyncMock()
        tab._mouse = None
        # Access the property descriptor directly
        mouse_obj = MouseAPI(tab)
        assert isinstance(mouse_obj, MouseAPI)
