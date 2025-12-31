# ui/tree_selector.py

import pyglet
from pyglet.text import Label
from pyglet.shapes import Rectangle
from typing import Dict, Optional

from loader import UpgradeTree


class TreeSelector:
    """Sidebar for selecting which upgrade tree to display."""

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        trees: Dict[str, UpgradeTree]
    ):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.trees = trees

        self.batch = pyglet.graphics.Batch()
        self.buttons: Dict[str, dict] = {}
        self.active_tree_id: Optional[str] = None

        # Scrolling support
        self.scroll_y = 0
        self.button_height = 98
        self.button_spacing = 15
        self.top_padding = 120

        # Calculate content height
        num_trees = len(trees)
        self.content_height = self.top_padding + (num_trees * (self.button_height + self.button_spacing))
        self.max_scroll = max(0, self.content_height - self.height)

        self._create_ui()

        # Select first tree by default
        if trees:
            self.active_tree_id = list(trees.keys())[0]

    def _create_ui(self):
        """Create button UI for each tree."""
        # No background - removed for simplicity

        # Create buttons
        current_y = self.y + self.height - self.top_padding

        for tree_id, tree in self.trees.items():
            base_y = current_y

            # Button background
            bg = Rectangle(
                self.x + 8, base_y,
                self.width - 16, self.button_height,
                color=(60, 60, 65),
                batch=self.batch
            )

            # Icon (50% larger)
            icon_label = Label(
                tree.icon,
                x=self.x + 38,  # Adjusted for larger size
                y=base_y + self.button_height // 2,
                anchor_y='center',
                font_size=30,
                batch=self.batch
            )

            # Name (50% larger)
            name_label = Label(
                tree.name,
                x=self.x + 83,  # Adjusted for larger icon
                y=base_y + self.button_height // 2,
                anchor_y='center',
                font_size=20,
                color=(255, 255, 255, 255),
                batch=self.batch
            )

            self.buttons[tree_id] = {
                'background': bg,
                'icon': icon_label,
                'name': name_label,
                'base_y': base_y,
                'height': self.button_height
            }

            current_y -= self.button_height + self.button_spacing

    def _update_scroll_positions(self):
        """Update button positions based on scroll offset."""
        for tree_id, btn in self.buttons.items():
            base_y = btn['base_y']
            scrolled_y = base_y + self.scroll_y

            btn['background'].y = scrolled_y
            btn['icon'].y = scrolled_y + self.button_height // 2
            btn['name'].y = scrolled_y + self.button_height // 2

    def draw(self):
        """Draw the selector with clipping."""
        self._update_scroll_positions()

        # Enable scissor test for clipping
        pyglet.gl.glEnable(pyglet.gl.GL_SCISSOR_TEST)
        pyglet.gl.glScissor(int(self.x), int(self.y), int(self.width), int(self.height))

        # Update button colors based on active state
        for tree_id, btn in self.buttons.items():
            if tree_id == self.active_tree_id:
                btn['background'].color = (40, 100, 140)  # Active: blue
            else:
                btn['background'].color = (60, 60, 65)  # Inactive: dark gray

        self.batch.draw()

        # Draw scrollbar if needed
        if self.max_scroll > 0:
            self._draw_scrollbar()

        pyglet.gl.glDisable(pyglet.gl.GL_SCISSOR_TEST)

    def _draw_scrollbar(self):
        """Draw a scrollbar indicator."""
        scrollbar_width = 6
        scrollbar_x = self.x + self.width - scrollbar_width - 2

        # Scrollbar track
        track = Rectangle(
            scrollbar_x,
            self.y,
            scrollbar_width,
            self.height,
            color=(60, 60, 65)
        )
        track.draw()

        # Scrollbar thumb
        visible_ratio = self.height / self.content_height
        thumb_height = max(30, self.height * visible_ratio)

        scroll_ratio = abs(self.scroll_y) / self.max_scroll if self.max_scroll > 0 else 0
        thumb_y = self.y + ((self.height - thumb_height) * scroll_ratio)

        thumb = Rectangle(
            scrollbar_x,
            thumb_y,
            scrollbar_width,
            thumb_height,
            color=(100, 150, 200)
        )
        thumb.draw()

    def on_mouse_press(self, x: int, y: int) -> Optional[str]:
        """Handle click. Returns tree ID if a button was clicked."""
        if not (self.x <= x <= self.x + self.width and self.y <= y <= self.y + self.height):
            return None

        for tree_id, btn in self.buttons.items():
            btn_y = btn['base_y'] + self.scroll_y
            if btn_y <= y <= btn_y + btn['height']:
                self.active_tree_id = tree_id
                return tree_id

        return None

    def on_mouse_scroll(self, x: int, y: int, scroll_x: float, scroll_y: float):
        """Handle mouse scroll."""
        if not (self.x <= x <= self.x + self.width and self.y <= y <= self.y + self.height):
            return

        # Scroll by button height
        scroll_amount = scroll_y * 30  # Increased scroll speed for larger buttons
        self.scroll_y = max(-self.max_scroll, min(0, self.scroll_y + scroll_amount))

    def get_active_tree(self) -> Optional[UpgradeTree]:
        """Get currently selected tree."""
        if self.active_tree_id and self.active_tree_id in self.trees:
            return self.trees[self.active_tree_id]
        return None
