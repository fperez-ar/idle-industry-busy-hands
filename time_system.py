from typing import Callable, List, Optional
from config import get_config


class TimeSystem:
    """Manages game time progression."""

    def __init__(self, start_year: int = None):
        # Load config
        config = get_config()
        time_config = config.get_time_config()

        # Use provided start_year or load from config
        self.start_year = start_year if start_year is not None else time_config.get('start_year', 1800)
        self.current_year = self.start_year
        self.year_progress = 0.0  # 0.0 to 1.0 progress through current year

        # Time scaling
        self.years_per_real_second = time_config.get('years_per_real_second', 1.0)
        self.time_multiplier = time_config.get('default_speed', 1.0)
        self.max_multiplier = time_config.get('max_speed', 16.0)
        self.min_multiplier = time_config.get('min_speed', 0.25)
        self.paused = False

        # Year change listeners
        self._year_listeners: List[Callable[[int], None]] = []

    def add_year_listener(self, callback: Callable[[int], None]):
        """Register a callback to be called when the year changes."""
        if callback not in self._year_listeners:
            self._year_listeners.append(callback)

    def remove_year_listener(self, callback: Callable[[int], None]):
        """Unregister a year change callback."""
        if callback in self._year_listeners:
            self._year_listeners.remove(callback)

    def _notify_year_change(self):
        """Notify all listeners that the year has changed."""
        for callback in self._year_listeners:
            try:
                callback(self.current_year)
            except Exception as e:
                print(f"Error in year change callback: {e}")

    def update(self, dt: float):
        """Update time progression."""
        if self.paused:
            return

        # Calculate year progression
        effective_speed = self.time_multiplier * self.years_per_real_second
        year_delta = dt * effective_speed

        old_year = self.current_year
        self.year_progress += year_delta

        # Check if we've completed a year
        while self.year_progress >= 1.0:
            self.year_progress -= 1.0
            self.current_year += 1

        # Notify listeners if year changed
        if self.current_year != old_year:
            self._notify_year_change()

    def get_effective_time_scale(self) -> float:
        """Get the current effective time scale (0 if paused)."""
        if self.paused:
            return 0.0
        return self.time_multiplier

    def set_speed(self, multiplier: float):
        """Set time speed multiplier."""
        self.time_multiplier = max(self.min_multiplier, min(self.max_multiplier, multiplier))

    def toggle_pause(self) -> bool:
        """Toggle pause state. Returns new pause state."""
        self.paused = not self.paused
        return self.paused

    def get_progress_percent(self) -> float:
        """Get progress through current year as percentage (0-100)."""
        return self.year_progress * 100

    def get_years_elapsed(self) -> int:
        """Get total years elapsed since start."""
        return self.current_year - self.start_year

    def set_year(self, year: int):
        """Manually set the current year."""
        old_year = self.current_year
        self.current_year = year
        self.year_progress = 0.0

        if year != old_year:
            self._notify_year_change()

    def advance_year(self):
        """Manually advance to the next year."""
        self.current_year += 1
        self.year_progress = 0.0
        self._notify_year_change()


class TimeControlUI:
    """UI component for controlling time."""

    def __init__(self, x: int, y: int, width: int, time_system: TimeSystem):
        self.x = x
        self.y = y
        self.width = width
        self.height = 80
        self.time_system = time_system

        import pyglet
        from pyglet.text import Label
        from pyglet.shapes import Rectangle

        self.batch = pyglet.graphics.Batch()

        # Background
        self.background = Rectangle(
            self.x, self.y, self.width, self.height,
            color=(40, 40, 45),
            batch=self.batch
        )

        # Year display
        self.year_label = Label(
            f"Year: {self.time_system.current_year}",
            x=self.x + self.width // 2,
            y=self.y + self.height - 20,
            anchor_x='center',
            font_size=16,
            color=(255, 255, 255, 255),
            batch=self.batch
        )

        # Speed display
        self.speed_label = Label(
            f"Speed: {self.time_system.time_multiplier:.1f}x",
            x=self.x + self.width // 2,
            y=self.y + self.height - 45,
            anchor_x='center',
            font_size=12,
            color=(200, 200, 200, 255),
            batch=self.batch
        )

        # Progress bar background
        self.progress_bg = Rectangle(
            self.x + 10, self.y + 15,
            self.width - 20, 10,
            color=(60, 60, 65),
            batch=self.batch
        )

        # Progress bar fill
        self.progress_fill = Rectangle(
            self.x + 10, self.y + 15,
            0, 10,
            color=(100, 150, 200),
            batch=self.batch
        )

        # Buttons (simple text buttons)
        self.pause_button = Label(
            "⏸" if not self.time_system.paused else "▶",
            x=self.x + 20,
            y=self.y + 40,
            font_size=20,
            color=(200, 200, 200, 255),
            batch=self.batch
        )

        self.slower_button = Label(
            "◀",
            x=self.x + 60,
            y=self.y + 40,
            font_size=16,
            color=(200, 200, 200, 255),
            batch=self.batch
        )

        self.faster_button = Label(
            "▶",
            x=self.x + 90,
            y=self.y + 40,
            font_size=16,
            color=(200, 200, 200, 255),
            batch=self.batch
        )

    def update(self):
        """Update displayed values."""
        self.year_label.text = f"Year: {self.time_system.current_year}"

        if self.time_system.paused:
            self.speed_label.text = "PAUSED"
            self.pause_button.text = "▶"
        else:
            self.speed_label.text = f"Speed: {self.time_system.time_multiplier:.1f}x"
            self.pause_button.text = "⏸"

        # Update progress bar
        progress = self.time_system.get_progress_percent() / 100
        self.progress_fill.width = (self.width - 20) * progress

    def draw(self):
        """Draw the time control UI."""
        self.batch.draw()

    def on_mouse_press(self, x: int, y: int) -> str:
        """Handle mouse press. Returns action string if a button was clicked."""
        if not (self.x <= x <= self.x + self.width and self.y <= y <= self.y + self.height):
            return None

        # Check pause button (approximate hit box)
        if self.x + 10 <= x <= self.x + 40 and self.y + 30 <= y <= self.y + 60:
            return "pause"

        # Check slower button
        if self.x + 50 <= x <= self.x + 70 and self.y + 30 <= y <= self.y + 60:
            return "slower"

        # Check faster button
        if self.x + 80 <= x <= self.x + 100 and self.y + 30 <= y <= self.y + 60:
            return "faster"

        return None

    def handle_action(self, action: str):
        """Handle a button action."""
        if action == "pause":
            self.time_system.toggle_pause()
        elif action == "slower":
            new_speed = self.time_system.time_multiplier / 2
            self.time_system.set_speed(new_speed)
        elif action == "faster":
            new_speed = self.time_system.time_multiplier * 2
            self.time_system.set_speed(new_speed)


class TimeControlUI:
    """UI for controlling time progression."""

    def __init__(self, x: int, y: int, width: int, time_system: TimeSystem):
        self.x = x
        self.y = y
        self.width = width
        self.time_system = time_system
        self.height = 80

        import pyglet
        from pyglet.text import Label
        from pyglet.shapes import Rectangle

        self.batch = pyglet.graphics.Batch()

        # Background
        self.background = Rectangle(
            x, y, width, self.height,
            color=(45, 45, 50),
            batch=self.batch
        )

        # Year display
        self.year_label = Label(
            f"Year: {time_system.current_year}",
            x=x + 10,
            y=y + self.height - 25,
            font_size=16,
            color=(255, 255, 255, 255),
            batch=self.batch
        )

        # Speed display
        self.speed_label = Label(
            f"Speed: {time_system.time_multiplier:.1f}x",
            x=x + 10,
            y=y + self.height - 50,
            font_size=12,
            color=(200, 200, 200, 255),
            batch=self.batch
        )

        # Progress bar background
        self.progress_bg = Rectangle(
            x + 10, y + 10,
            width - 20, 15,
            color=(30, 30, 35),
            batch=self.batch
        )

        # Progress bar (will be updated each frame)
        self.progress_bar = Rectangle(
            x + 10, y + 10,
            0, 15,
            color=(100, 150, 255),
            batch=self.batch
        )

        # Pause indicator
        self.pause_label = Label(
            "",
            x=x + width - 10,
            y=y + self.height - 25,
            anchor_x='right',
            font_size=14,
            color=(255, 100, 100, 255),
            batch=self.batch
        )

        # Speed buttons (invisible clickable areas)
        self.button_areas = {
            'pause': {'x': x + width - 80, 'y': y + 35, 'w': 70, 'h': 25},
            'slower': {'x': x + 10, 'y': y + 35, 'w': 30, 'h': 25},
            'faster': {'x': x + 45, 'y': y + 35, 'w': 30, 'h': 25},
        }

        # Button labels
        self.pause_button_label = Label(
            "⏸ Pause",
            x=x + width - 45,
            y=y + 47,
            anchor_x='center',
            anchor_y='center',
            font_size=10,
            color=(200, 200, 200, 255),
            batch=self.batch
        )

        self.slower_button_label = Label(
            "<<",
            x=x + 25,
            y=y + 47,
            anchor_x='center',
            anchor_y='center',
            font_size=12,
            color=(200, 200, 200, 255),
            batch=self.batch
        )

        self.faster_button_label = Label(
            ">>",
            x=x + 60,
            y=y + 47,
            anchor_x='center',
            anchor_y='center',
            font_size=12,
            color=(200, 200, 200, 255),
            batch=self.batch
        )

    def update(self):
        """Update UI elements."""
        # Update year
        self.year_label.text = f"Year: {self.time_system.current_year}"

        # Update speed
        self.speed_label.text = f"Speed: {self.time_system.time_multiplier:.1f}x"

        # Update progress bar
        progress = self.time_system.get_progress_percent()
        bar_width = (self.width - 20) * (progress / 100)
        self.progress_bar.width = bar_width

        # Update pause indicator
        if self.time_system.paused:
            self.pause_label.text = "⏸ PAUSED"
            self.pause_button_label.text = "▶ Resume"
        else:
            self.pause_label.text = ""
            self.pause_button_label.text = "⏸ Pause"

    def draw(self):
        """Draw the time control UI."""
        self.batch.draw()

    def on_mouse_press(self, x: int, y: int) -> Optional[str]:
        """Handle mouse clicks on buttons. Returns action name if clicked."""
        for action, area in self.button_areas.items():
            if (area['x'] <= x <= area['x'] + area['w'] and
                area['y'] <= y <= area['y'] + area['h']):
                return action
        return None

    def handle_action(self, action: str):
        """Handle button actions."""
        if action == 'pause':
            self.time_system.toggle_pause()
        elif action == 'slower':
            new_speed = self.time_system.time_multiplier / 2
            self.time_system.set_speed(new_speed)
        elif action == 'faster':
            new_speed = self.time_system.time_multiplier * 2
            self.time_system.set_speed(new_speed)
