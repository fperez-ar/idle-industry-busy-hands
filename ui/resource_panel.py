import pyglet
from pyglet.text import Label
from pyglet.shapes import Rectangle
from typing import Dict, Optional

from resources import ResourceManager, ResourceState
from config import get_config

class ResourcePanel:
    """Displays all resources with auto-extending width and conditional scrolling."""

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        resource_manager: ResourceManager,
        max_width: Optional[int] = None
    ):
        # Load UI scale from config
        config = get_config()
        self.UI_SCALE = config.get('ui.resource_panel_scale', 1.5)

        self.x = x
        self.y = y
        self.base_width = width
        self.height = height
        self.resource_manager = resource_manager
        self.max_width = max_width  # Will be set by parent

        self.batch = pyglet.graphics.Batch()
        self.labels: Dict[str, Dict[str, Label]] = {}

        # Scrolling (horizontal)
        self.scroll_x = 0
        self.column_width = int(140 * self.UI_SCALE)
        self.padding = int(15 * self.UI_SCALE)

        # Font sizes - scaled
        self.icon_font_size = int(20 * self.UI_SCALE)
        self.name_font_size = int(11 * self.UI_SCALE)
        self.value_font_size = int(18 * self.UI_SCALE)
        self.rate_font_size = int(10 * self.UI_SCALE)

        # Vertical spacing - scaled
        self.icon_y_offset = int(25 * self.UI_SCALE)
        self.name_y_offset = int(45 * self.UI_SCALE)
        self.value_y_offset = int(35 * self.UI_SCALE)
        self.rate_y_offset = int(12 * self.UI_SCALE)

        # Border height - scaled
        self.border_height = int(2 * self.UI_SCALE)

        # Scrollbar dimensions - scaled
        self.scrollbar_height = int(4 * self.UI_SCALE)
        self.scrollbar_margin = int(10 * self.UI_SCALE)
        self.scrollbar_y_offset = int(2 * self.UI_SCALE)

        # Scroll indicator size - scaled
        self.indicator_font_size = int(16 * self.UI_SCALE)
        self.indicator_margin = int(10 * self.UI_SCALE)

        # Calculate dimensions
        self._calculate_dimensions()
        self._create_ui()

    def _calculate_dimensions(self):
        """Calculate content width and actual panel width."""
        num_resources = len(self.resource_manager.resources)

        # Calculate required content width
        self.content_width = (num_resources * self.column_width) + ((num_resources + 1) * self.padding)

        # Determine actual panel width (auto-extend up to max_width)
        if self.max_width is not None:
            # Auto-extend: use content width if it fits, otherwise use max_width
            self.width = min(self.content_width, self.max_width)
        else:
            # No max specified, use base width
            self.width = self.base_width

        # Calculate if scrolling is needed
        self.scrolling_enabled = self.content_width > self.width
        self.max_scroll = max(0, self.content_width - self.width)

        # Center the panel if it's smaller than max_width
        if self.max_width is not None and self.width < self.max_width:
            self.x = (self.max_width - self.width) // 2

    def set_max_width(self, max_width: int):
        """Update the maximum width and recalculate dimensions."""
        self.max_width = max_width
        self._calculate_dimensions()
        self._recreate_ui()

    def _recreate_ui(self):
        """Recreate UI elements after dimension change."""
        self.labels.clear()
        self.batch = pyglet.graphics.Batch()
        self._create_ui()

    def _create_ui(self):
        """Create labels for each resource in horizontal layout."""
        # Background
        self.background = Rectangle(
            self.x, self.y, self.width, self.height,
            color=(40, 40, 45),
            batch=self.batch
        )

        # Border
        self.border = Rectangle(
            self.x, self.y + self.height - self.border_height,
            self.width, self.border_height,
            color=(80, 80, 90),
            batch=self.batch
        )

        # Calculate starting X to center content if not scrolling
        if not self.scrolling_enabled:
            # Center the content within the panel
            total_content = self.content_width - self.padding  # Remove extra padding
            start_x = self.x + (self.width - total_content) // 2 + self.padding
        else:
            start_x = self.x + self.padding

        current_x = start_x

        for res_id, res_state in self.resource_manager.resources.items():
            definition = res_state.definition
            base_x = current_x

            # Resource icon
            icon_label = Label(
                definition.icon,
                x=base_x + self.column_width // 2,
                y=self.y + self.height - self.icon_y_offset,
                anchor_x='center',
                font_size=self.icon_font_size,
                batch=self.batch
            )

            # Resource name
            name_label = Label(
                definition.name,
                x=base_x + self.column_width // 2,
                y=self.y + self.height - self.name_y_offset,
                anchor_x='center',
                font_size=self.name_font_size,
                color=(*definition.color, 255),
                batch=self.batch
            )

            # Current value
            value_label = Label(
                "0",
                x=base_x + self.column_width // 2,
                y=self.y + self.value_y_offset,
                anchor_x='center',
                font_size=self.value_font_size,
                color=(255, 255, 255, 255),
                batch=self.batch
            )

            # Production rate
            rate_label = Label("+0.0/s",
                x=base_x + self.column_width // 2,
                y=self.y + self.rate_y_offset,
                anchor_x='center',
                font_size=self.rate_font_size,
                color=(150, 255, 150, 255),
                batch=self.batch
            )

            self.labels[res_id] = {
                'icon': icon_label,
                'name': name_label,
                'value': value_label,
                'rate': rate_label,
                'base_x': base_x
            }

            current_x += self.column_width + self.padding

    def _update_scroll_positions(self):
        """Update label positions based on scroll offset."""
        if not self.scrolling_enabled:
            return  # No scrolling needed, positions are fixed

        for res_id, labels in self.labels.items():
            base_x = labels['base_x']
            scrolled_x = base_x - self.scroll_x
            center_x = scrolled_x + self.column_width // 2

            labels['icon'].x = center_x
            labels['name'].x = center_x
            labels['value'].x = center_x
            labels['rate'].x = center_x

    def update(self):
        """Update displayed values."""
        if self.scrolling_enabled:
            self._update_scroll_positions()

        for res_id, labels in self.labels.items():
            res_state = self.resource_manager.get(res_id)
            if res_state:
                # Format large numbers
                value = res_state.current_value
                if value >= 1_000_000_000:
                    value_text = f"{value/1_000_000_000:.2f}B"
                elif value >= 1_000_000:
                    value_text = f"{value/1_000_000:.2f}M"
                elif value >= 1_000:
                    value_text = f"{value/1_000:.2f}K"
                else:
                    value_text = f"{value:.1f}"

                labels['value'].text = value_text

                # Production rate
                rate = res_state.get_production_per_second()
                rate_color = (150, 255, 150, 255) if rate >= 0 else (255, 150, 150, 255)
                sign = "+" if rate >= 0 else ""

                if abs(rate) >= 1000:
                    rate_text = f"{sign}{rate/1000:.1f}K/s"
                elif abs(rate) >= 1:
                    rate_text = f"{sign}{rate:.1f}/s"
                else:
                    rate_text = f"{sign}{rate:.2f}/s"

                labels['rate'].text = rate_text
                labels['rate'].color = rate_color

    def draw(self):
        """Draw the resource panel with clipping."""
        pyglet.gl.glEnable(pyglet.gl.GL_SCISSOR_TEST)
        pyglet.gl.glScissor(int(self.x), int(self.y), int(self.width), int(self.height))

        self.batch.draw()

        # Only draw scrollbar if scrolling is enabled
        if self.scrolling_enabled and self.max_scroll > 0:
            self._draw_scrollbar()
            self._draw_scroll_indicators()

        pyglet.gl.glDisable(pyglet.gl.GL_SCISSOR_TEST)

    def _draw_scrollbar(self):
        """Draw a horizontal scrollbar indicator."""
        scrollbar_y = self.y + self.scrollbar_y_offset

        track = Rectangle(
            self.x + self.scrollbar_margin,
            scrollbar_y,
            self.width - (2 * self.scrollbar_margin),
            self.scrollbar_height,
            color=(60, 60, 65)
        )
        track.draw()

        visible_ratio = self.width / self.content_width
        thumb_width = max(int(30 * self.UI_SCALE), int((self.width - 2 * self.scrollbar_margin) * visible_ratio))

        scroll_ratio = self.scroll_x / self.max_scroll if self.max_scroll > 0 else 0
        thumb_x = self.x + self.scrollbar_margin + int(((self.width - 2 * self.scrollbar_margin - thumb_width) * scroll_ratio))

        thumb = Rectangle(
            thumb_x,
            scrollbar_y,
            thumb_width,
            self.scrollbar_height,
            color=(100, 150, 200)
        )
        thumb.draw()

    def _draw_scroll_indicators(self):
        """Draw left/right scroll indicators."""
        if self.scroll_x > 0:
            left_arrow = Label(
                "◀",
                x=self.x + self.indicator_margin,
                y=self.y + self.height // 2,
                anchor_x='left',
                anchor_y='center',
                font_size=self.indicator_font_size,
                color=(200, 200, 200, 200)
            )
            left_arrow.draw()

        if self.scroll_x < self.max_scroll:
            right_arrow = Label(
                "▶",
                x=self.x + self.width - self.indicator_margin,
                y=self.y + self.height // 2,
                anchor_x='right',
                anchor_y='center',
                font_size=self.indicator_font_size,
                color=(200, 200, 200, 200)
            )
            right_arrow.draw()

    def on_mouse_scroll(self, x: int, y: int, scroll_x: float, scroll_y: float) -> bool:
        """Handle mouse scroll (horizontal scrolling)."""
        if not (self.x <= x <= self.x + self.width and self.y <= y <= self.y + self.height):
            return False

        # Only scroll if scrolling is enabled
        if not self.scrolling_enabled:
            return False

        scroll_amount = scroll_y * int(30 * self.UI_SCALE)
        self.scroll_x = max(0, min(self.max_scroll, self.scroll_x - scroll_amount))

        return True

    def on_resize(self, new_max_width: int, new_y: int = None):
        """Handle window resize - recalculate auto-extend."""
        if new_y is not None:
            self.y = new_y
        self.set_max_width(new_max_width)
