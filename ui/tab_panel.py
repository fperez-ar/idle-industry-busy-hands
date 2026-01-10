import pyglet
from pyglet.text import Label
from pyglet.shapes import Rectangle
from typing import Dict, List, Optional, Callable, Set, Any

TAB_LABEL_SIZE = 16
TAB_LABEL_COLOR = (200, 200, 200, 255)
TAB_ACTIVE_COLOR = (70, 100, 140)
TAB_INACTIVE_COLOR = (50, 50, 55)

class Tab:
    """Represents a single tab."""

    def __init__(
        self,
        id: str,
        label: str,
        icon: str = "",
        required_upgrades: Optional[List[str]] = None,
        required_any: bool = False,  # If True, any upgrade unlocks; if False, all required
        visible_by_default: bool = True
    ):
        self.id = id
        self.label = label
        self.icon = icon
        self.required_upgrades = required_upgrades or []
        self.required_any = required_any
        self.visible_by_default = visible_by_default

class TabPanel:
    """A tabbed panel interface."""

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        tabs: List[Tab],
        owned_upgrades: Optional[Set[str]] = None
    ):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.all_tabs = tabs
        self.owned_upgrades: Set[str] = owned_upgrades or set()

        self.active_tab_id: Optional[str] = None
        self.tab_height = 80
        self.batch = pyglet.graphics.Batch()
        self.tab_buttons: Dict[str, dict] = {}

        self._update_visible_tabs()
        self._create_tabs()

    def _check_upgrade_requirements(
        self,
        required_upgrades: List[str],
        required_any: bool
    ) -> bool:
        """Check if upgrade requirements are met."""
        if not required_upgrades:
            return True

        if required_any:
            # Any one of the upgrades unlocks this
            return any(upg in self.owned_upgrades for upg in required_upgrades)
        else:
            # All upgrades required
            return all(upg in self.owned_upgrades for upg in required_upgrades)

    def _update_visible_tabs(self):
        """Update which tabs are visible based on owned upgrades."""
        self.visible_tabs = []

        for tab in self.all_tabs:
            if tab.visible_by_default:
                is_visible = True
            else:
                is_visible = self._check_upgrade_requirements(
                    tab.required_upgrades,
                    tab.required_any
                )

            if is_visible:
                self.visible_tabs.append(tab)

        # Set active tab if none selected or current is hidden
        if self.visible_tabs:
            if self.active_tab_id is None or not any(t.id == self.active_tab_id for t in self.visible_tabs):
                self.active_tab_id = self.visible_tabs[0].id

    def _create_tabs(self):
        """Create tab buttons for visible tabs."""
        self.tab_buttons.clear()
        self.batch = pyglet.graphics.Batch()

        if not self.visible_tabs:
            return

        tab_width = self.width // len(self.visible_tabs)
        current_x = self.x

        for tab in self.visible_tabs:
            bg = Rectangle(
                current_x, self.y + self.height - self.tab_height,
                tab_width, self.tab_height,
                color=TAB_INACTIVE_COLOR,
                batch=self.batch
            )

            label_text = f"{tab.icon} {tab.label}" if tab.icon else tab.label
            label = Label(
                label_text,
                x=current_x + tab_width // 2,
                y=self.y + self.height - self.tab_height // 2,
                anchor_x='center',
                anchor_y='center',
                font_size=TAB_LABEL_SIZE,
                color=TAB_LABEL_COLOR,
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
                btn['background'].color = TAB_ACTIVE_COLOR
                btn['label'].color = (255, 255, 255, 255)
            else:
                btn['background'].color = TAB_INACTIVE_COLOR
                btn['label'].color = TAB_LABEL_COLOR

        self.batch.draw()

        # Draw content area background
        content_x, content_y, content_width, content_height = self.get_content_area()
        content_bg = Rectangle(
            content_x, content_y,
            content_width, content_height,
            color=(35, 35, 40)
        )
        content_bg.draw()



    def on_mouse_press(self, x: int, y: int) -> Optional[str]:
        """Handle mouse press. Returns tab ID if a tab is clicked."""
        # Check tab clicks
        if self.y + self.height - self.tab_height <= y <= self.y + self.height:
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