# ui/editor_properties.py

import pyglet
from pyglet.text import Label
from pyglet.shapes import Rectangle
from typing import Optional, Callable, Dict, Tuple
from loader import Upgrade, Effect, ResourceCost

# Layout constants
PADDING = 25
FIELD_HEIGHT = 35
MULTILINE_HEIGHT = 60
SECTION_SPACING = 40
EFFECT_HEIGHT = 100
COST_HEIGHT = 70


class PropertiesPanel:
    """Panel for editing node properties."""

    def __init__(self, x: int, y: int, width: int, height: int):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

        self.upgrade: Optional[Upgrade] = None
        self.buttons: list = []
        self.scroll_y = 0
        self.active_field: Optional[str] = None

        # State machine for editing
        self.is_editing = False

        # Track clickable field rectangles: field_id -> (x, y, width, height)
        self.field_rects: Dict[str, Tuple[int, int, int, int]] = {}

        # Callbacks
        self.on_property_changed: Optional[Callable[[Upgrade], None]] = None
        self.on_delete_node: Optional[Callable[[], None]] = None

    def set_upgrade(self, upgrade: Optional[Upgrade]):
        """Set the upgrade to display/edit."""
        self.upgrade = upgrade
        self.active_field = None
        self.is_editing = False
        self.scroll_y = 0
        self.field_rects.clear()
        self.buttons = []

    def _get_content_start_y(self) -> int:
        """Get the starting Y position for content below the delete button."""
        return self.y + self.height - 100 + self.scroll_y

    def _register_field(self, field_id: str, x: int, y: int, width: int, height: int):
        """Register a clickable field area."""
        self.field_rects[field_id] = (x, y, width, height)

    def _register_button(self, button: dict):
        """Register a button, updating if it exists."""
        for i, btn in enumerate(self.buttons):
            if btn['id'] == button['id']:
                self.buttons[i] = button
                return
        self.buttons.append(button)

    def draw(self):
        """Draw the properties panel."""
        # Clear field rects each frame (they get re-registered during draw)
        self.field_rects.clear()
        self.buttons = []

        # Background
        bg = Rectangle(
            self.x, self.y,
            self.width, self.height,
            color=(35, 35, 40)
        )
        bg.draw()

        # Title
        title = Label(
            "Properties",
            x=self.x + self.width // 2,
            y=self.y + self.height - 20,
            anchor_x='center',
            anchor_y='center',
            font_size=14,
            color=(255, 255, 255, 255)
        )
        title.draw()

        if not self.upgrade:
            no_selection = Label(
                "No node selected",
                x=self.x + self.width // 2,
                y=self.y + self.height // 2,
                anchor_x='center',
                anchor_y='center',
                font_size=12,
                color=(150, 150, 150, 255)
            )
            no_selection.draw()
            return

        # Delete button
        delete_btn = {
            'id': 'delete',
            'label': '🗑️ Delete Node',
            'x': self.x + PADDING,
            'y': self.y + self.height - 55,
            'width': self.width - PADDING * 2,
            'height': 35,
            'color': (150, 50, 50)
        }
        self._draw_button(delete_btn)
        self._register_button(delete_btn)

        current_y = self._get_content_start_y()

        # ID (read-only)
        current_y = self._draw_labeled_field("ID:", 'id', self.upgrade.id, current_y, read_only=True)
        current_y -= PADDING

        # Name
        current_y = self._draw_labeled_field("Name:", 'name', self.upgrade.name, current_y)
        current_y -= PADDING

        # Description
        current_y = self._draw_labeled_field("Description:", 'description', self.upgrade.description, current_y, multiline=True)
        current_y -= PADDING

        # Tier
        current_y = self._draw_labeled_field("Tier:", 'tier', str(self.upgrade.tier), current_y, width=120)
        current_y -= PADDING

        # Year
        current_y = self._draw_labeled_field("Year:", 'year', str(self.upgrade.year), current_y, width=120)
        current_y -= PADDING

        # Exclusive Group
        current_y = self._draw_labeled_field("Exclusive Group:", 'exclusive_group', self.upgrade.exclusive_group or "", current_y)
        current_y -= SECTION_SPACING

        # Effects section
        current_y = self._draw_effects_section(current_y)
        current_y -= SECTION_SPACING

        # Costs section
        current_y = self._draw_costs_section(current_y)
        current_y -= SECTION_SPACING

        # Requirements (read-only)
        self._draw_requirements_section(current_y)

    def _draw_labeled_field(self, label: str, field_id: str, value: str, y: int,
                            read_only: bool = False, multiline: bool = False, width: int = None) -> int:
        """Draw a labeled input field. Returns the Y position after drawing."""
        if width is None:
            width = self.width - PADDING * 2

        field_height = MULTILINE_HEIGHT if multiline else FIELD_HEIGHT

        # Label
        label_obj = Label(
            label,
            x=self.x + PADDING,
            y=y,
            font_size=11,
            color=(200, 200, 200, 255)
        )
        label_obj.draw()

        # Input field below label
        field_top = y - 20
        field_bottom = field_top - field_height

        is_active = self.active_field == field_id and not read_only
        bg_color = (50, 50, 55) if read_only else ((70, 90, 110) if is_active else (60, 60, 70))

        field_x = self.x + PADDING
        bg = Rectangle(
            field_x, field_bottom,
            width, field_height,
            color=bg_color
        )
        bg.draw()

        # Register clickable area (not for read-only fields)
        if not read_only:
            self._register_field(field_id, field_x, field_bottom, width, field_height)

        # Border for active field
        if is_active:
            self._draw_field_border(field_x, field_bottom, width, field_height)

        # Text with cursor
        display_text = value
        if is_active:
            display_text += "|"

        text_color = (150, 150, 150, 255) if read_only else (255, 255, 255, 255)
        text_label = Label(
            display_text,
            x=field_x + 8,
            y=field_bottom + field_height // 2,
            anchor_y='center',
            font_size=11,
            color=text_color,
            width=width - 16,
            multiline=multiline
        )
        text_label.draw()

        return field_bottom

    def _draw_field_border(self, x: int, y: int, width: int, height: int):
        """Draw a border around an active field."""
        border_color = (100, 150, 200)
        thickness = 2
        Rectangle(x, y + height - thickness, width, thickness, color=border_color).draw()
        Rectangle(x, y, width, thickness, color=border_color).draw()
        Rectangle(x, y, thickness, height, color=border_color).draw()
        Rectangle(x + width - thickness, y, thickness, height, color=border_color).draw()

    def _draw_effects_section(self, start_y: int) -> int:
        """Draw the effects section with editable fields."""
        # Section label
        Label(
            "Effects:",
            x=self.x + PADDING,
            y=start_y,
            font_size=12,

            color=(100, 200, 255, 255)
        ).draw()

        # Add effect button
        add_btn_y = start_y - 35
        add_btn = {
            'id': 'add_effect',
            'label': '+ Add Effect',
            'x': self.x + PADDING,
            'y': add_btn_y,
            'width': self.width - PADDING * 2,
            'height': 28,
            'color': (50, 100, 150)
        }
        self._draw_button(add_btn)
        self._register_button(add_btn)

        current_y = add_btn_y - 15

        for i, effect in enumerate(self.upgrade.effects):
            current_y = self._draw_effect_editor(i, effect, current_y)

        return current_y

    def _draw_effect_editor(self, index: int, effect: Effect, y: int) -> int:
        """Draw an editable effect entry. Returns Y position after drawing."""
        box_x = self.x + PADDING
        box_width = self.width - PADDING * 2 - 35  # Room for X button
        box_height = EFFECT_HEIGHT
        box_bottom = y - box_height

        # Background box
        bg = Rectangle(box_x, box_bottom, box_width, box_height, color=(45, 55, 65))
        bg.draw()

        # X button - aligned to the right of this effect box
        remove_btn = {
            'id': f'remove_effect_{index}',
            'label': '✕',
            'x': box_x + box_width + 5,
            'y': y - 35,
            'width': 25,
            'height': 25,
            'color': (150, 50, 50)
        }
        self._draw_button(remove_btn)
        self._register_button(remove_btn)

        inner_x = box_x + 8
        inner_width = box_width - 16
        field_y = y - 10

        # Resource field
        Label("Resource:", x=inner_x, y=field_y, font_size=9, color=(150, 150, 150, 255)).draw()
        field_y -= 15
        field_y = self._draw_inline_input(f'effect_{index}_resource', effect.resource, inner_x, field_y, inner_width)
        field_y -= 8

        # Effect type and Value on same row
        half_width = (inner_width - 10) // 2

        Label("Type:", x=inner_x, y=field_y, font_size=9, color=(150, 150, 150, 255)).draw()
        Label("Value:", x=inner_x + half_width + 10, y=field_y, font_size=9, color=(150, 150, 150, 255)).draw()
        field_y -= 15

        self._draw_inline_input(f'effect_{index}_effect', effect.effect, inner_x, field_y, half_width)
        self._draw_inline_input(f'effect_{index}_value', str(effect.value), inner_x + half_width + 10, field_y, half_width)

        return box_bottom - PADDING

    def _draw_costs_section(self, start_y: int) -> int:
        """Draw the costs section with editable fields."""
        # Section label
        Label(
            "Costs:",
            x=self.x + PADDING,
            y=start_y,
            font_size=12,
            color=(255, 200, 100, 255)
        ).draw()

        # Add cost button
        add_btn_y = start_y - 35
        add_btn = {
            'id': 'add_cost',
            'label': '+ Add Cost',
            'x': self.x + PADDING,
            'y': add_btn_y,
            'width': self.width - PADDING * 2,
            'height': 28,
            'color': (150, 100, 50)
        }
        self._draw_button(add_btn)
        self._register_button(add_btn)

        current_y = add_btn_y - 15

        for i, cost in enumerate(self.upgrade.cost):
            current_y = self._draw_cost_editor(i, cost, current_y)

        return current_y

    def _draw_cost_editor(self, index: int, cost: ResourceCost, y: int) -> int:
        """Draw an editable cost entry. Returns Y position after drawing."""
        box_x = self.x + PADDING
        box_width = self.width - PADDING * 2 - 35
        box_height = COST_HEIGHT
        box_bottom = y - box_height

        # Background box
        bg = Rectangle(box_x, box_bottom, box_width, box_height, color=(55, 50, 45))
        bg.draw()

        # X button
        remove_btn = {
            'id': f'remove_cost_{index}',
            'label': '✕',
            'x': box_x + box_width + 5,
            'y': y - 35,
            'width': 25,
            'height': 25,
            'color': (150, 50, 50)
        }
        self._draw_button(remove_btn)
        self._register_button(remove_btn)

        inner_x = box_x + 8
        inner_width = box_width - 16
        half_width = (inner_width - 10) // 2
        field_y = y - 10

        # Resource and Amount on same row
        Label("Resource:", x=inner_x, y=field_y, font_size=9, color=(150, 150, 150, 255)).draw()
        Label("Amount:", x=inner_x + half_width + 10, y=field_y, font_size=9, color=(150, 150, 150, 255)).draw()
        field_y -= 15

        self._draw_inline_input(f'cost_{index}_resource', cost.resource, inner_x, field_y, half_width)
        self._draw_inline_input(f'cost_{index}_amount', str(cost.amount), inner_x + half_width + 10, field_y, half_width)

        return box_bottom - PADDING

    def _draw_inline_input(self, field_id: str, value: str, x: int, y: int, width: int) -> int:
        """Draw a small inline input field. Returns the bottom Y position."""
        height = 24
        field_bottom = y - height

        is_active = self.active_field == field_id
        bg_color = (70, 90, 110) if is_active else (55, 55, 60)

        bg = Rectangle(x, field_bottom, width, height, color=bg_color)
        bg.draw()

        # Register clickable area
        self._register_field(field_id, x, field_bottom, width, height)

        if is_active:
            self._draw_field_border(x, field_bottom, width, height)

        display_text = value + ("|" if is_active else "")
        Label(
            display_text,
            x=x + 5,
            y=field_bottom + height // 2,
            anchor_y='center',
            font_size=10,
            color=(255, 255, 255, 255)
        ).draw()

        return field_bottom

    def _draw_requirements_section(self, y: int):
        """Draw the requirements section (read-only)."""
        Label(
            "Requirements:",
            x=self.x + PADDING,
            y=y,
            font_size=12,
            color=(200, 200, 200, 255)
        ).draw()

        if self.upgrade.requires:
            req_text = ", ".join([
                str(r) if not isinstance(r, list) else f"[{', '.join(r)}]"
                for r in self.upgrade.requires
            ])
            Label(
                req_text,
                x=self.x + PADDING,
                y=y - 25,
                font_size=10,
                color=(150, 150, 150, 255),
                width=self.width - PADDING * 2,
                multiline=True
            ).draw()
        else:
            Label(
                "(none)",
                x=self.x + PADDING,
                y=y - 25,
                font_size=10,
                color=(100, 100, 100, 255)
            ).draw()

    def _draw_button(self, button: dict):
        """Draw a button."""
        bg = Rectangle(
            button['x'], button['y'],
            button['width'], button['height'],
            color=button.get('color', (60, 60, 70))
        )
        bg.draw()

        Label(
            button['label'],
            x=button['x'] + button['width'] // 2,
            y=button['y'] + button['height'] // 2,
            anchor_x='center',
            anchor_y='center',
            font_size=11,
            color=(255, 255, 255, 255)
        ).draw()

    def on_mouse_press(self, x: int, y: int, button: int) -> bool:
        """Handle mouse press. Returns True if handled."""
        if not (self.x <= x <= self.x + self.width and self.y <= y <= self.y + self.height):
            # Clicked outside panel - deactivate editing
            self.active_field = None
            self.is_editing = False
            return False

        # Check buttons first
        for btn in self.buttons:
            if (btn['x'] <= x <= btn['x'] + btn['width'] and
                btn['y'] <= y <= btn['y'] + btn['height']):
                self._handle_button_click(btn['id'])
                return True

        # Check field clicks using registered rectangles
        if self.upgrade:
            clicked_field = None
            for field_id, (fx, fy, fw, fh) in self.field_rects.items():
                if fx <= x <= fx + fw and fy <= y <= fy + fh:
                    clicked_field = field_id
                    break

            if clicked_field:
                self.active_field = clicked_field
                self.is_editing = True
            else:
                self.active_field = None
                self.is_editing = False

        return True

    def _handle_button_click(self, button_id: str):
        """Handle button click."""
        if button_id == 'delete' and self.on_delete_node:
            if not self.is_editing:
                self.on_delete_node()

        elif button_id == 'add_effect' and self.upgrade:
            new_effect = Effect(resource="capital", effect="add", value=1.0)
            self.upgrade.effects.append(new_effect)
            if self.on_property_changed:
                self.on_property_changed(self.upgrade)

        elif button_id == 'add_cost' and self.upgrade:
            new_cost = ResourceCost(resource="capital", amount=10.0)
            self.upgrade.cost.append(new_cost)
            if self.on_property_changed:
                self.on_property_changed(self.upgrade)

        elif button_id.startswith('remove_effect_') and self.upgrade:
            index = int(button_id.split('_')[-1])
            if 0 <= index < len(self.upgrade.effects):
                self.upgrade.effects.pop(index)
                if self.on_property_changed:
                    self.on_property_changed(self.upgrade)

        elif button_id.startswith('remove_cost_') and self.upgrade:
            index = int(button_id.split('_')[-1])
            if 0 <= index < len(self.upgrade.cost):
                self.upgrade.cost.pop(index)
                if self.on_property_changed:
                    self.on_property_changed(self.upgrade)

    def on_text(self, text: str):
        """Handle text input."""
        if not self.active_field or not self.upgrade:
            return

        field = self.active_field

        # Main fields
        if field == 'name':
            self.upgrade.name += text
        elif field == 'description':
            self.upgrade.description += text
        elif field == 'tier':
            if text.isdigit() or (text == '-' and str(self.upgrade.tier) == '0'):
                try:
                    current = str(self.upgrade.tier)
                    if current == '0':
                        self.upgrade.tier = int(text)
                    else:
                        self.upgrade.tier = int(current + text)
                except ValueError:
                    pass
        elif field == 'year':
            if text.isdigit():
                try:
                    current = str(self.upgrade.year)
                    self.upgrade.year = int(current + text)
                except ValueError:
                    pass
        elif field == 'exclusive_group':
            if self.upgrade.exclusive_group is None:
                self.upgrade.exclusive_group = text
            else:
                self.upgrade.exclusive_group += text

        # Effect fields
        elif field.startswith('effect_'):
            parts = field.split('_')
            index = int(parts[1])
            subfield = parts[2]
            if 0 <= index < len(self.upgrade.effects):
                effect = self.upgrade.effects[index]
                if subfield == 'resource':
                    effect.resource += text
                elif subfield == 'effect':
                    effect.effect += text
                elif subfield == 'value':
                    try:
                        current = str(effect.value)
                        if text.isdigit() or text == '.' or (text == '-' and current == '0.0'):
                            if current == '0.0' or current == '0':
                                effect.value = float(text) if text != '.' else 0.0
                            else:
                                effect.value = float(current + text)
                    except ValueError:
                        pass

        # Cost fields
        elif field.startswith('cost_'):
            parts = field.split('_')
            index = int(parts[1])
            subfield = parts[2]
            if 0 <= index < len(self.upgrade.cost):
                cost = self.upgrade.cost[index]
                if subfield == 'resource':
                    cost.resource += text
                elif subfield == 'amount':
                    try:
                        current = str(cost.amount)
                        if text.isdigit() or text == '.' or (text == '-' and current == '0.0'):
                            if current == '0.0' or current == '0':
                                cost.amount = float(text) if text != '.' else 0.0
                            else:
                                cost.amount = float(current + text)
                    except ValueError:
                        pass

        if self.on_property_changed:
            self.on_property_changed(self.upgrade)

    def on_text_motion(self, motion: int):
        """Handle text motion (backspace, delete, etc.)."""
        if not self.active_field or not self.upgrade:
            return

        from pyglet.window import key

        if motion == key.MOTION_BACKSPACE:
            field = self.active_field

            if field == 'name' and self.upgrade.name:
                self.upgrade.name = self.upgrade.name[:-1]
            elif field == 'description' and self.upgrade.description:
                self.upgrade.description = self.upgrade.description[:-1]
            elif field == 'tier':
                tier_str = str(self.upgrade.tier)[:-1]
                self.upgrade.tier = int(tier_str) if tier_str and tier_str != '-' else 0
            elif field == 'year':
                year_str = str(self.upgrade.year)[:-1]
                self.upgrade.year = int(year_str) if year_str else 1800
            elif field == 'exclusive_group' and self.upgrade.exclusive_group:
                self.upgrade.exclusive_group = self.upgrade.exclusive_group[:-1] or None

            # Effect fields
            elif field.startswith('effect_'):
                parts = field.split('_')
                index = int(parts[1])
                subfield = parts[2]
                if 0 <= index < len(self.upgrade.effects):
                    effect = self.upgrade.effects[index]
                    if subfield == 'resource' and effect.resource:
                        effect.resource = effect.resource[:-1]
                    elif subfield == 'effect' and effect.effect:
                        effect.effect = effect.effect[:-1]
                    elif subfield == 'value':
                        val_str = str(effect.value)[:-1]
                        try:
                            effect.value = float(val_str) if val_str and val_str not in ('-', '.', '-.') else 0.0
                        except ValueError:
                            effect.value = 0.0

            # Cost fields
            elif field.startswith('cost_'):
                parts = field.split('_')
                index = int(parts[1])
                subfield = parts[2]
                if 0 <= index < len(self.upgrade.cost):
                    cost = self.upgrade.cost[index]
                    if subfield == 'resource' and cost.resource:
                        cost.resource = cost.resource[:-1]
                    elif subfield == 'amount':
                        amt_str = str(cost.amount)[:-1]
                        try:
                            cost.amount = float(amt_str) if amt_str and amt_str not in ('-', '.', '-.') else 0.0
                        except ValueError:
                            cost.amount = 0.0

            if self.on_property_changed:
                self.on_property_changed(self.upgrade)

    def on_mouse_scroll(self, x: int, y: int, scroll_x: float, scroll_y: float):
        """Handle mouse scroll."""
        if not (self.x <= x <= self.x + self.width):
            return

        self.scroll_y += scroll_y * 30
        self.scroll_y = max(-1500, min(0, self.scroll_y))
