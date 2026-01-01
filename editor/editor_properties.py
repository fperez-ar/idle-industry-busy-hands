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

MIN_YEAR = 0.0
MAX_YEAR = 10000000.0

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

    def _format_numeric_input(self, current_value: str, new_char: str, is_integer: bool = False) -> Optional[str]:
        """
        Format numeric input for text fields.

        Args:
            current_value: Current string value in the field
            new_char: New character being added
            is_integer: If True, only allow integers; if False, allow floats

        Returns:
            Formatted string if valid, None if invalid
        """
        # Handle empty field
        if current_value in ('0', '0.0', ''):
            if new_char == '-':
                return '-'
            elif new_char == '.' and not is_integer:
                return '0.'
            elif new_char.isdigit():
                return new_char
            else:
                return None

        # Build potential new value
        potential = current_value + new_char

        # For integers, only allow digits and leading minus
        if is_integer:
            if new_char.isdigit():
                return potential
            elif new_char == '-' and current_value == '':
                return '-'
            else:
                return None

        # For floats, validate format
        if new_char.isdigit():
            return potential
        elif new_char == '-' and current_value == '':
            return '-'
        elif new_char == '.' and '.' not in current_value:
            return potential
        else:
            return None

    def _validate_numeric_field(self, value_str: str, is_integer: bool = False, min_val = -100.0, max_val = 100.0) -> float or int:
        """
        Validate and convert numeric field value on blur.

        Args:
            value_str: String value to validate
            is_integer: If True, return integer; if False, return float

        Returns:
            Validated numeric value (defaults to 0 if invalid)
        """
        if not value_str or value_str in ('-', '.', '-.'):
            return 0.0 if not is_integer else 0

        try:
            value = float(value_str)
            value = max(float(min_val), min(float(max_val), value))
            if is_integer:
                return int(value)
            else:
                # Round to 2 decimal places
                return round(value, 2)
        except ValueError:
            return 0.0 if not is_integer else 0

    def _get_field_value_string(self, field: str) -> str:
        """Get the current string value for a field."""
        if field == 'name':
            return self.upgrade.name
        elif field == 'description':
            return self.upgrade.description
        elif field == 'tier':
            return str(self.upgrade.tier)
        elif field == 'year':
            return str(self.upgrade.year)
        elif field == 'exclusive_group':
            return self.upgrade.exclusive_group or ''
        elif field.startswith('effect_'):
            parts = field.split('_')
            index = int(parts[1])
            subfield = parts[2]
            if 0 <= index < len(self.upgrade.effects):
                effect = self.upgrade.effects[index]
                if subfield == 'resource':
                    return effect.resource
                elif subfield == 'effect':
                    return effect.effect
                elif subfield == 'value':
                    return str(effect.value)
        elif field.startswith('cost_'):
            parts = field.split('_')
            index = int(parts[1])
            subfield = parts[2]
            if 0 <= index < len(self.upgrade.cost):
                cost = self.upgrade.cost[index]
                if subfield == 'resource':
                    return cost.resource
                elif subfield == 'amount':
                    return str(cost.amount)
        return ''

    def _set_field_value_string(self, field: str, value: str):
        """Set the string value for a field."""
        if field == 'name':
            self.upgrade.name = value
        elif field == 'description':
            self.upgrade.description = value
        elif field == 'tier':
            self.upgrade.tier = self._validate_numeric_field(value, is_integer=True)
        elif field == 'year':
            print('年　YEAR ', value)
            self.upgrade.year = int(self._validate_numeric_field(value, is_integer=True, min_val=MIN_YEAR, max_val=MAX_YEAR))
        elif field == 'exclusive_group':
            self.upgrade.exclusive_group = value if value else None
        elif field.startswith('effect_'):
            parts = field.split('_')
            index = int(parts[1])
            subfield = parts[2]
            if 0 <= index < len(self.upgrade.effects):
                effect = self.upgrade.effects[index]
                if subfield == 'resource':
                    effect.resource = value
                elif subfield == 'effect':
                    effect.effect = value
                elif subfield == 'value':
                    effect.value = self._validate_numeric_field(value, is_integer=False)
        elif field.startswith('cost_'):
            parts = field.split('_')
            index = int(parts[1])
            subfield = parts[2]
            if 0 <= index < len(self.upgrade.cost):
                cost = self.upgrade.cost[index]
                if subfield == 'resource':
                    cost.resource = value
                elif subfield == 'amount':
                    cost.amount = self._validate_numeric_field(value, is_integer=False)

    def _is_numeric_field(self, field: str) -> tuple[bool, bool]:
        """
        Check if a field is numeric.

        Returns:
            (is_numeric, is_integer) tuple
        """
        if field in ('tier', 'year'):
            return (True, True)
        elif field.endswith('_value') or field.endswith('_amount'):
            return (True, False)
        return (False, False)

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
            # Clicked outside panel - validate and deactivate editing
            if self.active_field and self.upgrade:
                self._validate_and_blur_field()
            self.active_field = None
            self.is_editing = False
            return False

        # Check buttons first
        for btn in self.buttons:
            if (btn['x'] <= x <= btn['x'] + btn['width'] and
                btn['y'] <= y <= btn['y'] + btn['height']):
                # Validate current field before handling button
                if self.active_field and self.upgrade:
                    self._validate_and_blur_field()
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
                # Validate previous field before switching
                if self.active_field and self.active_field != clicked_field:
                    self._validate_and_blur_field()

                self.active_field = clicked_field
                self.is_editing = True
            else:
                # Clicked in panel but not on a field - validate and deactivate
                if self.active_field:
                    self._validate_and_blur_field()
                self.active_field = None
                self.is_editing = False

        return True

    def _validate_and_blur_field(self):
        """Validate the current active field and apply formatting."""
        if not self.active_field or not self.upgrade:
            return

        is_numeric, is_integer = self._is_numeric_field(self.active_field)

        if is_numeric:
            current_value = self._get_field_value_string(self.active_field)

            # Determine validation parameters based on field
            if self.active_field == 'year':
                validated_value = self._validate_numeric_field(
                    current_value,
                    is_integer=True,
                    min_val=MIN_YEAR,
                    max_val=MAX_YEAR
                )
            elif self.active_field == 'tier':
                validated_value = self._validate_numeric_field(
                    current_value,
                    is_integer=True,
                    min_val=-100,
                    max_val=100
                )
            else:
                # For effect values and cost amounts
                validated_value = self._validate_numeric_field(
                    current_value,
                    is_integer=False,
                    min_val=-100,
                    max_val=100
                )

            # Update the field with validated value
            if self.active_field == 'tier':
                self.upgrade.tier = int(validated_value)
            elif self.active_field == 'year':
                self.upgrade.year = int(validated_value)
            elif self.active_field.endswith('_value'):
                parts = self.active_field.split('_')
                index = int(parts[1])
                if 0 <= index < len(self.upgrade.effects):
                    self.upgrade.effects[index].value = validated_value
            elif self.active_field.endswith('_amount'):
                parts = self.active_field.split('_')
                index = int(parts[1])
                if 0 <= index < len(self.upgrade.cost):
                    self.upgrade.cost[index].amount = validated_value

            if self.on_property_changed:
                self.on_property_changed(self.upgrade)

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

        is_numeric, is_integer = self._is_numeric_field(self.active_field)

        if is_numeric:
            # Handle numeric fields with formatting
            current_value = self._get_field_value_string(self.active_field)
            formatted = self._format_numeric_input(current_value, text, is_integer)

            if formatted is not None:
                self._set_field_value_string(self.active_field, formatted)
        else:
            # Handle text fields normally
            current_value = self._get_field_value_string(self.active_field)
            self._set_field_value_string(self.active_field, current_value + text)

        if self.on_property_changed:
            self.on_property_changed(self.upgrade)

    def on_text_motion(self, motion: int):
        """Handle text motion (backspace, delete, etc.)."""
        if not self.active_field or not self.upgrade:
            return

        from pyglet.window import key

        if motion == key.MOTION_BACKSPACE:
            current_value = self._get_field_value_string(self.active_field)

            if current_value:
                new_value = current_value[:-1]
                self._set_field_value_string(self.active_field, new_value)

                if self.on_property_changed:
                    self.on_property_changed(self.upgrade)

    def on_mouse_scroll(self, x: int, y: int, scroll_x: float, scroll_y: float):
        """Handle mouse scroll."""
        if not (self.x <= x <= self.x + self.width):
            return

        self.scroll_y += scroll_y * 30
        self.scroll_y = max(-1500, min(0, self.scroll_y))
