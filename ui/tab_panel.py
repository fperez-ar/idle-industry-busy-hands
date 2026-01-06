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


class DynamicButton:
    """A button that appears based on upgrade conditions."""

    def __init__(
        self,
        id: str,
        label: str,
        icon: str = "",
        required_upgrades: Optional[List[str]] = None,
        required_any: bool = False,
        action: Optional[Callable] = None,
        tooltip: str = ""
    ):
        self.id = id
        self.label = label
        self.icon = icon
        self.required_upgrades = required_upgrades or []
        self.required_any = required_any
        self.action = action
        self.tooltip = tooltip
        self.is_visible = False
        self.is_enabled = True


class TabPanel:
    """A tabbed panel interface with dynamic upgrade-based buttons."""

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

        # Dynamic buttons per tab
        self.tab_dynamic_buttons: Dict[str, List[DynamicButton]] = {}
        self.button_ui: Dict[str, Dict[str, dict]] = {}  # tab_id -> button_id -> ui elements

        # Button layout settings
        self.button_height = 50
        self.button_spacing = 10
        self.button_margin = 15

        # Callbacks
        self.on_button_click: Optional[Callable[[str, str], None]] = None  # (tab_id, button_id)

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

    def register_dynamic_buttons(self, tab_id: str, buttons: List[DynamicButton]):
        """Register dynamic buttons for a specific tab."""
        self.tab_dynamic_buttons[tab_id] = buttons
        self._update_button_visibility(tab_id)
        self._create_button_ui(tab_id)

    def _update_button_visibility(self, tab_id: str):
        """Update visibility of dynamic buttons based on upgrades."""
        if tab_id not in self.tab_dynamic_buttons:
            return

        for button in self.tab_dynamic_buttons[tab_id]:
            button.is_visible = self._check_upgrade_requirements(
                button.required_upgrades,
                button.required_any
            )

    def _create_button_ui(self, tab_id: str):
        """Create UI elements for dynamic buttons in a tab."""
        if tab_id not in self.tab_dynamic_buttons:
            return

        self.button_ui[tab_id] = {}
        content_x, content_y, content_width, content_height = self.get_content_area()

        visible_buttons = [b for b in self.tab_dynamic_buttons[tab_id] if b.is_visible]
        current_y = content_y + content_height - self.button_margin - self.button_height

        for button in visible_buttons:
            button_width = content_width - (2 * self.button_margin)

            bg = Rectangle(
                content_x + self.button_margin,
                current_y,
                button_width,
                self.button_height,
                color=(60, 80, 100) if button.is_enabled else (50, 50, 55)
            )

            label_text = f"{button.icon} {button.label}" if button.icon else button.label
            label = Label(
                label_text,
                x=content_x + content_width // 2,
                y=current_y + self.button_height // 2,
                anchor_x='center',
                anchor_y='center',
                font_size=14,
                color=(255, 255, 255,  255) if button.is_enabled else (150, 150, 150, 255)
            )

            self.button_ui[tab_id][button.id] = {
                'background': bg,
                'label': label,
                'x': content_x + self.button_margin,
                'y': current_y,
                'width': button_width,
                'height': self.button_height,
                'button': button
            }

            current_y -= self.button_height + self.button_spacing

    def update_owned_upgrades(self, owned_upgrades: Set[str]):
        """Update owned upgrades and refresh visibility."""
        old_visible_tabs = [t.id for t in self.visible_tabs]
        self.owned_upgrades = owned_upgrades

        # Update tab visibility
        self._update_visible_tabs()

        # Check if tabs changed
        new_visible_tabs = [t.id for t in self.visible_tabs]
        if old_visible_tabs != new_visible_tabs:
            self._create_tabs()

        # Update button visibility for all tabs
        for tab_id in self.tab_dynamic_buttons:
            self._update_button_visibility(tab_id)
            self._create_button_ui(tab_id)

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

        # Draw dynamic buttons for active tab
        if self.active_tab_id and self.active_tab_id in self.button_ui:
            for button_id, btn_ui in self.button_ui[self.active_tab_id].items():
                button = btn_ui['button']
                if button.is_visible:
                    btn_ui['background'].draw()
                    btn_ui['label'].draw()

    def on_mouse_press(self, x: int, y: int) -> Optional[str]:
        """Handle mouse press. Returns tab ID if tab clicked, or triggers button action."""
        # Check tab clicks
        tab_y = self.y + self.height - self.tab_height
        if self.y + self.height - self.tab_height <= y <= self.y + self.height:
            for tab_id, btn in self.tab_buttons.items():
                if btn['x'] <= x <= btn['x'] + btn['width']:
                    self.active_tab_id = tab_id
                    return tab_id

        # Check dynamic button clicks in active tab
        if self.active_tab_id and self.active_tab_id in self.button_ui:
            for button_id, btn_ui in self.button_ui[self.active_tab_id].items():
                button = btn_ui['button']
                if not button.is_visible or not button.is_enabled:
                    continue

                btn_x = btn_ui['x']
                btn_y = btn_ui['y']
                btn_w = btn_ui['width']
                btn_h = btn_ui['height']

                if btn_x <= x <= btn_x + btn_w and btn_y <= y <= btn_y + btn_h:
                    # Trigger button action
                    if button.action:
                        button.action()
                    if self.on_button_click:
                        self.on_button_click(self.active_tab_id, button_id)
                    return f"button:{button_id}"

        return None

    def on_mouse_motion(self, x: int, y: int) -> Optional[str]:
        """Handle mouse motion for hover effects. Returns tooltip text if hovering over button."""
        if self.active_tab_id and self.active_tab_id in self.button_ui:
            for button_id, btn_ui in self.button_ui[self.active_tab_id].items():
                button = btn_ui['button']
                if not button.is_visible:
                    continue

                btn_x = btn_ui['x']
                btn_y = btn_ui['y']
                btn_w = btn_ui['width']
                btn_h = btn_ui['height']

                if btn_x <= x <= btn_x + btn_w and btn_y <= y <= btn_y + btn_h:
                    # Update hover state
                    if button.is_enabled:
                        btn_ui['background'].color = (80, 100, 130)
                    return button.tooltip if button.tooltip else None
                else:
                    # Reset hover state
                    if button.is_enabled:
                        btn_ui['background'].color = (60, 80, 100)
                    else:
                        btn_ui['background'].color = (50, 50, 55)

        return None

    def get_content_area(self) -> tuple:
        """Get the content area dimensions (x, y, width, height)."""
        return (
            self.x,
            self.y,
            self.width,
            self.height - self.tab_height
        )

    def set_button_enabled(self, tab_id: str, button_id: str, enabled: bool):
        """Enable or disable a specific button."""
        if tab_id in self.tab_dynamic_buttons:
            for button in self.tab_dynamic_buttons[tab_id]:
                if button.id == button_id:
                    button.is_enabled = enabled
                    # Update UI if exists
                    if tab_id in self.button_ui and button_id in self.button_ui[tab_id]:
                        btn_ui = self.button_ui[tab_id][button_id]
                        btn_ui['background'].color = (60, 80, 100) if enabled else (50, 50, 55)
                        btn_ui['label'].color = (255, 255, 255, 255) if enabled else (150, 150, 150, 255)
                    break

    def add_dynamic_button(self, tab_id: str, button: DynamicButton):
        """Add a new dynamic button to a tab at runtime."""
        if tab_id not in self.tab_dynamic_buttons:
            self.tab_dynamic_buttons[tab_id] = []

        self.tab_dynamic_buttons[tab_id].append(button)
        self._update_button_visibility(tab_id)
        self._create_button_ui(tab_id)

    def remove_dynamic_button(self, tab_id: str, button_id: str):
        """Remove a dynamic button from a tab."""
        if tab_id in self.tab_dynamic_buttons:
            self.tab_dynamic_buttons[tab_id] = [
                b for b in self.tab_dynamic_buttons[tab_id] if b.id != button_id
            ]
            self._create_button_ui(tab_id)
