import pyglet
from pyglet.text import Label
from pyglet.shapes import Rectangle
from typing import Optional, Callable
from events import Event, EventChoice


class EventPopup:
    """Modal popup for displaying events and choices."""

    UI_SCALE = 1.2

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.visible = False
        self.event: Optional[Event] = None

        # Dimensions (scaled)
        self.popup_width = int(700 * self.UI_SCALE)
        self.popup_height = int(500 * self.UI_SCALE)
        self.padding = int(20 * self.UI_SCALE)
        self.button_height = int(80 * self.UI_SCALE)
        self.button_spacing = int(12 * self.UI_SCALE)

        # Font sizes (scaled)
        self.title_font_size = int(20 * self.UI_SCALE)
        self.desc_font_size = int(13 * self.UI_SCALE)
        self.choice_font_size = int(12 * self.UI_SCALE)
        self.effect_font_size = int(10 * self.UI_SCALE)

        # Callbacks
        self.on_choice_selected: Optional[Callable[[EventChoice], None]] = None

        # UI state
        self.choice_buttons = []
        self.hovered_choice_id: Optional[str] = None

    def show(self, event: Event):
        """Show the popup with an event."""
        self.event = event
        self.visible = True
        self._create_buttons()

    def hide(self):
        """Hide the popup."""
        self.visible = False
        self.event = None
        self.choice_buttons = []
        self.hovered_choice_id = None

    def _create_buttons(self):
        """Create button areas for choices."""
        if not self.event:
            return

        self.choice_buttons = []

        popup_x = (self.width - self.popup_width) // 2
        popup_y = (self.height - self.popup_height) // 2

        # Calculate button area
        content_height = int(180 * self.UI_SCALE)  # Space for title and description
        button_area_height = self.popup_height - content_height - self.padding * 2

        num_choices = len(self.event.choices)
        total_button_height = num_choices * self.button_height + (num_choices - 1) * self.button_spacing

        button_start_y = popup_y + self.padding + (button_area_height - total_button_height) // 2
        current_y = button_start_y

        for choice in self.event.choices:
            button_info = {
                'choice': choice,
                'x': popup_x + self.padding,
                'y': current_y,
                'width': self.popup_width - self.padding * 2,
                'height': self.button_height
            }
            self.choice_buttons.append(button_info)
            current_y += self.button_height + self.button_spacing

    def draw(self, can_afford_callback: Callable[[EventChoice], bool]):
        """Draw the event popup."""
        if not self.visible or not self.event:
            return

        # Calculate popup position
        popup_x = (self.width - self.popup_width) // 2
        popup_y = (self.height - self.popup_height) // 2

        # Draw overlay (darken background)
        overlay = Rectangle(0, 0, self.width, self.height, color=(0, 0, 0))
        overlay.opacity = 200
        overlay.draw()

        # Draw popup border
        border = Rectangle(
            popup_x - 3, popup_y - 3,
            self.popup_width + 6, self.popup_height + 6,
            color=(150, 150, 160)
        )
        border.draw()

        # Draw popup background
        bg = Rectangle(
            popup_x, popup_y,
            self.popup_width, self.popup_height,
            color=(30, 30, 35)
        )
        bg.draw()

        # Draw icon
        icon_label = Label(
            self.event.icon,
            x=popup_x + self.padding,
            y=popup_y + self.popup_height - self.padding - int(35 * self.UI_SCALE),
            font_size=int(40 * self.UI_SCALE),
            color=(255, 255, 255, 255)
        )
        icon_label.draw()

        # Draw title
        title_label = Label(
            self.event.title,
            x=popup_x + self.padding + int(60 * self.UI_SCALE),
            y=popup_y + self.popup_height - self.padding - int(25 * self.UI_SCALE),
            font_size=self.title_font_size,
            color=(255, 255, 255, 255),
            width=self.popup_width - self.padding * 2 - int(60 * self.UI_SCALE),
            multiline=True
        )
        title_label.draw()
