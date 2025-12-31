# ui/tab_panel.py
import pyglet
from pyglet.text import Label
from pyglet.shapes import Rectangle
from typing import Dict, List, Optional, Callable

TAB_LABEL_SIZE = 16
TAB_LABEL_COLOR = (200, 200, 200, 255)
class Tab:
    """Represents a single tab."""

    def __init__(self, id: str, label: str, icon: str = ""):
        self.id = id
        self.label = label
        self.icon = icon


class TabPanel:
    """A tabbed panel interface."""

    def __init__(self, x: int, y: int, width: int, height: int, tabs: List[Tab]):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.tabs = tabs
        self.active_tab_id: Optional[str] = tabs[0].id if tabs else None

        self.tab_height = 80
        self.batch = pyglet.graphics.Batch()
        self.tab_buttons: Dict[str, dict] = {}

        self._create_tabs()

    def _create_tabs(self):
        """Create tab buttons."""
        if not self.tabs:
            return

        tab_width = self.width // len(self.tabs)
        current_x = self.x

        for tab in self.tabs:
            # Tab background
            bg = Rectangle(
                current_x, self.y + self.height - self.tab_height,
                tab_width, self.tab_height,
                color=(50, 50, 55),
                batch=self.batch
            )

            # Tab label
            label_text = f"{tab.icon} {tab.label}" if tab.icon else tab.label
            label = Label(
                label_text,
                x = current_x + tab_width // 2,
                y = self.y + self.height - self.tab_height // 2,
                anchor_x='center',
                anchor_y='center',
                font_size = TAB_LABEL_SIZE,
                color = TAB_LABEL_COLOR,
                batch=self.batch
            )

            self.tab_buttons[tab.id] = {
                'background': bg,
                'label': label,
                'x': current_x,
                'width': tab_width
            }

            current_x += tab_width

    def draw(self):
        """Draw the tab panel."""
        # Update active tab appearance
        for tab_id, btn in self.tab_buttons.items():
            if tab_id == self.active_tab_id:
                btn['background'].color = (70, 100, 140)
                btn['label'].color = (255, 255, 255, 255)
            else:
                btn['background'].color = (50, 50, 55)
                btn['label'].color = (200, 200, 200, 255)

        self.batch.draw()

    def on_mouse_press(self, x: int, y: int) -> Optional[str]:
        """Handle mouse press. Returns tab ID if clicked."""
        tab_y = self.y + self.height - self.tab_height

        if not (self.y + self.height - self.tab_height <= y <= self.y + self.height):
            return None

        for tab_id, btn in self.tab_buttons.items():
            if btn['x'] <= x <= btn['x'] + btn['width']:
                self.active_tab_id = tab_id
                return tab_id

        return None

    def get_content_area(self) -> tuple:
        """Get the content area dimensions (x, y, width, height)."""
        return (
            self.x,
            self.y,
            self.width,
            self.height - self.tab_height
        )
