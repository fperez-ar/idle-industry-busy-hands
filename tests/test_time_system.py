import pytest
from time_system import TimeSystem


class TestTimeSystem:
    """Test TimeSystem functionality."""

    @pytest.fixture
    def time_system(self):
        """Create a TimeSystem instance."""
        return TimeSystem()

    def test_initialization(self, time_system):
        """Test time system initialization."""
        assert time_system.current_year == 0
        assert time_system.year_progress == 0.0
        assert time_system.paused is False
        assert time_system.time_multiplier == 1.0

    def test_update_year_progress(self, time_system):
        """Test year progress update."""
        initial_year = time_system.current_year

        # Update for half a year (1 second at normal speed)
        time_system.update(1.0)

        assert time_system.year_progress > 0.0
        assert time_system.current_year == initial_year

    def test_year_change(self, time_system):
        """Test year change trigger."""
        year_changed = False
        new_year_value = None

        def on_year_change(year):
            nonlocal year_changed, new_year_value
            year_changed = True
            new_year_value = year

        time_system.add_year_listener(on_year_change)

        # Update for 2 years
        time_system.update(5.0)

        assert year_changed is True
        assert new_year_value > 0

    def test_pause_toggle(self, time_system):
        """Test pause functionality."""
        assert time_system.paused is False

        time_system.toggle_pause()
        assert time_system.paused is True

        time_system.toggle_pause()
        assert time_system.paused is False

    def test_paused_no_update(self, time_system):
        """Test that time doesn't progress when paused."""
        time_system.toggle_pause()

        initial_progress = time_system.year_progress
        time_system.update(1.0)

        assert time_system.year_progress == initial_progress

    def test_time_multiplier(self, time_system):
        """Test time speed multiplier."""
        time_system.set_speed(2.0)
        assert time_system.time_multiplier == 2.0

        time_system.update(1.0)
        total_progress = time_system.year_progress + time_system.current_year
        assert total_progress > 0  # Some progress was made

        # reset
        time_system.current_year = 0
        time_system.year_progress = 0

        target_progress = 0.6
        dt = target_progress / (time_system.time_multiplier * time_system.years_per_real_second)
        time_system.update(dt)
        assert time_system.year_progress > 0

        # Should still be in year 0 with progress 0.6
        assert abs(time_system.year_progress - target_progress) < 0.01

    def test_get_effective_time_scale(self, time_system):
        """Test effective time scale calculation."""
        assert time_system.get_effective_time_scale() == 1.0

        time_system.set_speed(2.0)
        assert time_system.get_effective_time_scale() == 2.0

        time_system.toggle_pause()
        assert time_system.get_effective_time_scale() == 0.0
