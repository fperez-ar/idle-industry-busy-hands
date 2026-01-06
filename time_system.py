# time_system.py

from typing import Callable, List, Optional

class TimeSystem:
    """Manages in-game time progression."""

    def __init__(self, start_year: int = 1800):
        self.current_year = start_year
        self.year_progress = 0.0  # Progress toward next year (0.0 to 1.0)
        self.years_per_second = 0.1  # Base time speed (0.5 = 2 seconds per year)
        self.time_multiplier = 1.0
        self.paused = False

        # Callbacks for year change events
        self.on_year_change: List[Callable[[int], None]] = []

    def update(self, dt: float):
        """Update time progression."""
        if self.paused:
            return

        self.year_progress += dt * self.years_per_second * self.time_multiplier

        while self.year_progress >= 1.0:
            self.year_progress -= 1.0
            self.current_year += 1

            # Notify listeners
            for callback in self.on_year_change:
                callback(self.current_year)

    def set_speed(self, multiplier: float):
        """Set time speed multiplier (0.5 = half speed, 2.0 = double speed)."""
        self.time_multiplier = max(0.1, min(10.0, multiplier))

    def toggle_pause(self):
        """Toggle pause state."""
        self.paused = not self.paused
        return self.paused

    def add_year_listener(self, callback: Callable[[int], None]):
        """Add a callback to be notified when year changes."""
        self.on_year_change.append(callback)

    def get_progress_percent(self) -> float:
        """Get progress to next year as percentage (0-100)."""
        return self.year_progress * 100

    def get_effective_time_scale(self) -> float:
        """Get the effective time scale (0.0 when paused, multiplier otherwise)."""
        if self.paused:
            return 0.0
        return self.time_multiplier

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
