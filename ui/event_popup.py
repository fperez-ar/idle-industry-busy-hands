import pyglet
from pyglet.text import Label
from pyglet.shapes import Rectangle
from typing import Optional, Callable
from time_system import TimeSystem
from event_manager import Event, EventChoice


class EventPopup:
    """Modal popup for displaying events and choices."""

    UI_SCALE = 1.2

    def __init__(self, width: int, height: int, time_system: TimeSystem):
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
        self.time_system = time_system
        self._paused_by_popup = False


    def show(self, event: Event):
        """Show the popup with an event."""
        self.event = event
        self.visible = True
        self._create_buttons()

        # Pause time
        if self.time_system and not self.time_system.paused:
            self.time_system.toggle_pause()
            self._paused_by_popup = True

    def hide(self):
        """Hide the popup."""
        self.visible = False
        self.event = None
        self.choice_buttons = []
        self.hovered_choice_id = None

        # Resume time if we paused it
        if self.time_system and self._paused_by_popup:
            self.time_system.toggle_pause()
            self._paused_by_popup = False

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

        # Draw description
        desc_y = popup_y + self.popup_height - int(80 * self.UI_SCALE)
        desc_label = Label(
            self.event.description,
            x=popup_x + self.padding,
            y=desc_y,
            font_size=self.desc_font_size,
            color=(200, 200, 200, 255),
            width=self.popup_width - self.padding * 2,
            multiline=True
        )
        desc_label.draw()

        # Draw choice buttons
        for button_info in self.choice_buttons:
            self._draw_choice_button(button_info, can_afford_callback)

    def _draw_choice_button(self, button_info: dict, can_afford_callback: Callable[[EventChoice], bool]):
        """Draw a single choice button with hover effect."""
        choice = button_info['choice']
        x, y, width, height = button_info['x'], button_info['y'], button_info['width'], button_info['height']

        is_hovered = self.hovered_choice_id == choice.id
        can_afford = can_afford_callback(choice)

        # Button background color
        if not can_afford:
            bg_color = (60, 40, 40)  # Red tint for unaffordable
            border_color = (100, 60, 60)
        elif is_hovered:
            bg_color = (70, 90, 120)  # Blue highlight
            border_color = (100, 140, 180)
        else:
            bg_color = (50, 55, 60)
            border_color = (80, 85, 90)

        # Draw border
        border = Rectangle(x - 2, y - 2, width + 4, height + 4, color=border_color)
        border.draw()

        # Draw background
        bg = Rectangle(x, y, width, height, color=bg_color)
        bg.draw()

        # Draw choice text
        text_label = Label(
            choice.text,
            x=x + self.padding,
            y=y + height - int(20 * self.UI_SCALE),
            font_size=self.choice_font_size,
            color=(255, 255, 255, 255) if can_afford else (150, 150, 150, 255)
        )
        text_label.draw()

        # Draw description
        desc_label = Label(
            choice.description,
            x=x + self.padding,
            y=y + height - int(40 * self.UI_SCALE),
            font_size=self.effect_font_size,
            color=(180, 180, 180, 255) if can_afford else (120, 120, 120, 255),
            width=width - self.padding * 2,
            multiline=True
        )
        desc_label.draw()

        # Draw costs and effects
        info_y = y + int(15 * self.UI_SCALE)

        # Costs
        if choice.cost:
            cost_text = "Cost: " + ", ".join([f"{c.amount} {c.resource}" for c in choice.cost])
            cost_label = Label(
                cost_text,
                x=x + self.padding,
                y=info_y,
                font_size=self.effect_font_size,
                color=(255, 200, 200, 255) if can_afford else (150, 120, 120, 255)
            )
            cost_label.draw()
            info_y += int(15 * self.UI_SCALE)

        # Effects
        if choice.effects:
            effect_text = "Effect: " + ", ".join([
                f"{'+' if e.value > 0 else ''}{e.value} {e.resource} ({e.effect})"
                for e in choice.effects
            ])
            effect_label = Label(
                effect_text,
                x=x + self.padding,
                y=info_y,
                font_size=self.effect_font_size,
                color=(200, 255, 200, 255) if can_afford else (120, 150, 120, 255)
            )
            effect_label.draw()

    def on_mouse_motion(self, x: int, y: int):
        """Handle mouse motion for hover effects."""
        if not self.visible:
            return

        self.hovered_choice_id = None
        for button_info in self.choice_buttons:
            bx, by, bw, bh = button_info['x'], button_info['y'], button_info['width'], button_info['height']
            if bx <= x <= bx + bw and by <= y <= by + bh:
                self.hovered_choice_id = button_info['choice'].id
                break

    def on_mouse_press(self, x: int, y: int) -> Optional[EventChoice]:
        """Handle mouse click on choices."""
        if not self.visible:
            return None

        for button_info in self.choice_buttons:
            bx, by, bw, bh = button_info['x'], button_info['y'], button_info['width'], button_info['height']
            if bx <= x <= bx + bw and by <= y <= by + bh:
                return button_info['choice']

        return None