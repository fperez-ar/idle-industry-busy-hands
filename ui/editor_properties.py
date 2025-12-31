# ui/editor_properties.py

import pyglet
from pyglet.text import Label
from pyglet.shapes import Rectangle
from typing import Optional, Callable
from loader import Upgrade, Effect, ResourceCost


class PropertiesPanel:
    """Panel for editing node properties."""

    def __init__(self, x: int, y: int, width: int, height: int):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

        self.upgrade: Optional[Upgrade] = None
        self.buttons = []
        self.scroll_y = 0
        self.active_field: Optional[str] = None

        # Callbacks
        self.on_property_changed: Optional[Callable[[Upgrade], None]] = None
        self.on_delete_node: Optional[Callable[[], None]] = None

    def set_upgrade(self, upgrade: Optional[Upgrade]):
        """Set the upgrade to display/edit."""
        self.upgrade = upgrade
        self.active_field = None
        self.scroll_y = 0
        self._create_property_fields()

    def _create_property_fields(self):
        """Create buttons and fields for the current upgrade."""
        self.buttons = []

        if not self.upgrade:
            return

        # Delete button at the top
        self.buttons.append({
            'id': 'delete',
            'label': '🗑️ Delete Node',
            'x': self.x + 10,
            'y': self.y + self.height - 40,
            'width': self.width - 20,
            'height': 30,
            'color': (150, 50, 50)
        })

        # Add effect button
        self.buttons.append({
            'id': 'add_effect',
            'label': '+ Add Effect',
            'x': self.x + 10,
            'y': self.y + 200,
            'width': (self.width - 30) // 2,
            'height': 25,
            'color': (50, 100, 150)
        })

        # Add cost button
        self.buttons.append({
            'id': 'add_cost',
            'label': '+ Add Cost',
            'x': self.x + self.width // 2 + 5,
            'y': self.y + 200,
            'width': (self.width - 30) // 2,
            'height': 25,
            'color': (150, 100, 50)
        })

        # Remove buttons for effects
        for i in range(len(self.upgrade.effects)):
            self.buttons.append({
                'id': f'remove_effect_{i}',
                'label': '✕',
                'x': self.x + self.width - 35,
                'y': self.y + 150 - (i * 60),
                'width': 25,
                'height': 25,
                'color': (150, 50, 50)
            })

        # Remove buttons for costs
        for i in range(len(self.upgrade.cost)):
            self.buttons.append({
                'id': f'remove_cost_{i}',
                'label': '✕',
                'x': self.x + self.width - 35,
                'y': self.y + 150 - (len(self.upgrade.effects) * 60) - (i * 40),
                'width': 25,
                'height': 25,
                'color': (150, 50, 50)
            })

    def draw(self):
        """Draw the properties panel."""
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
            y=self.y + self.height - 15,
            anchor_x='center',
            anchor_y='center',
            font_size=14,
            color=(255, 255, 255, 255)
        )
        title.draw()

        if not self.upgrade:
            # No selection message
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

        # Draw buttons
        for button in self.buttons:
            self._draw_button(button)

        # Draw properties
        current_y = self.y + self.height - 80 + self.scroll_y
        padding = 10

        # ID (read-only)
        self._draw_field_label("ID:", self.upgrade.id, self.x + padding, current_y, read_only=True)
        current_y -= 40

        # Name
        self._draw_field_label("Name:", "", self.x + padding, current_y)
        current_y -= 20
        self._draw_field_input('name', self.upgrade.name, self.x + padding, current_y)
        current_y -= 40

        # Description
        self._draw_field_label("Description:", "", self.x + padding, current_y)
        current_y -= 20
        self._draw_field_input('description', self.upgrade.description, self.x + padding, current_y, multiline=True)
        current_y -= 60

        # Tier
        self._draw_field_label("Tier:", "", self.x + padding, current_y)
        current_y -= 20
        self._draw_field_input('tier', str(self.upgrade.tier), self.x + padding, current_y, width=100)
        current_y -= 40

        # Year
        self._draw_field_label("Year:", "", self.x + padding, current_y)
        current_y -= 20
        self._draw_field_input('year', str(self.upgrade.year), self.x + padding, current_y, width=100)
        current_y -= 40

        # Exclusive Group
        self._draw_field_label("Exclusive Group:", "", self.x + padding, current_y)
        current_y -= 20
        self._draw_field_input('exclusive_group', self.upgrade.exclusive_group or "", self.x + padding, current_y)
        current_y -= 60

        # Effects section
        effects_label = Label(
            "Effects:",
            x=self.x + padding,
            y=current_y,
            font_size=12,
            color=(100, 200, 255, 255)
        )
        effects_label.draw()
        current_y -= 30

        for i, effect in enumerate(self.upgrade.effects):
            self._draw_effect(i, effect, self.x + padding, current_y)
            current_y -= 60

        current_y -= 20

        # Costs section
        costs_label = Label(
            "Costs:",
            x=self.x + padding,
            y=current_y,
            font_size=12,
            color=(255, 220, 100, 255)
        )
        costs_label.draw()
        current_y -= 30

        for i, cost in enumerate(self.upgrade.cost):
            self._draw_cost(i, cost, self.x + padding, current_y)
            current_y -= 40

        # Requirements (read-only)
        current_y -= 20
        req_label = Label(
            "Requirements:",
            x=self.x + padding,
            y=current_y,
            font_size=12,
            color=(200, 200, 200, 255)
        )
        req_label.draw()
        current_y -= 25

        if self.upgrade.requires:
            req_text = ", ".join([str(r) if not isinstance(r, list) else f"[{', '.join(r)}]" for r in self.upgrade.requires])
            req_value = Label(
                req_text,
                x=self.x + padding + 5,
                y=current_y,
                font_size=10,
                color=(180, 180, 180, 255),
                width=self.width - 30,
                multiline=True
            )
            req_value.draw()

    def _draw_field_label(self, label: str, text: str, x: int, y: int, read_only: bool = False):
        """Draw a field label."""
        label_obj = Label(
            label,
            x=x,
            y=y,
            font_size=11,
            color=(200, 200, 200, 255)
        )
        label_obj.draw()

        if read_only and text:
            bg = Rectangle(
                x, y - 30,
                self.width - 30, 25,
                color=(50, 50, 55) if read_only else (60, 60, 70)
            )
            bg.draw()

            label = Label(
                text,
                x=x + 5,
                y=y - 10,
                font_size=10,
                color=(180, 180, 180, 255) if read_only else (255, 255, 255, 255)
            )
            label.draw()

    def _draw_field_input(self, field_id: str, text: str, x: int, y: int, width: int = None, multiline: bool = False):
        """Draw an editable input field."""
        if width is None:
            width = self.width - 30

        height = 50 if multiline else 30

        # Background
        is_active = self.active_field == field_id
        bg = Rectangle(
            x, y - height + 5,
            width, height,
            color=(70, 90, 110) if is_active else (60, 60, 70)
        )
        bg.draw()

        # Border for active field
        if is_active:
            border_color = (100, 150, 200)
            # Draw border as 4 lines
            top = Rectangle(x - 1, y + 6, width + 2, 1, color=border_color)
            bottom = Rectangle(x - 1, y - height + 4, width + 2, 1, color=border_color)
            left = Rectangle(x - 1, y - height + 4, 1, height + 2, color=border_color)
            right = Rectangle(x + width, y - height + 4, 1, height + 2, color=border_color)
            top.draw()
            bottom.draw()
            left.draw()
            right.draw()

        # Text with cursor
        display_text = text
        if is_active:
            display_text += "|"  # Simple cursor

        label = Label(
            display_text,
            x=x + 5,
            y=y - 10 if not multiline else y - 15,
            font_size=10,
            color=(255, 255, 255, 255),
            width=width - 10,
            multiline=multiline
        )
        label.draw()

    def _draw_cost(self, index: int, cost: ResourceCost, x: int, y: int):
        """Draw a cost entry."""
        # Background
        bg = Rectangle(
            x, y - 35,
            self.width - 80, 35,
            color=(55, 55, 60)
        )
        bg.draw()

        # Resource
        resource_label = Label(
            f"Resource: {cost.resource}",
            x=x + 5,
            y=y - 10,
            font_size=10,
            color=(255, 220, 100, 255)
        )
        resource_label.draw()

        # Amount
        amount_label = Label(
            f"Amount: {cost.amount}",
            x=x + 5,
            y=y - 25,
            font_size=10,
            color=(255, 220, 100, 255)
        )
        amount_label.draw()

    def _draw_effect(self, index: int, effect: Effect, x: int, y: int):
        """Draw an effect entry."""
        # Background
        bg = Rectangle(
            x, y - 55,
            self.width - 80, 55,
            color=(55, 55, 60)
        )
        bg.draw()

        # Resource
        resource_label = Label(
            f"Resource: {effect.resource}",
            x=x + 5,
            y=y - 10,
            font_size=10,
            color=(100, 200, 255, 255)
        )
        resource_label.draw()

        # Effect type
        effect_label = Label(
            f"Type: {effect.effect}",
            x=x + 5,
            y=y - 25,
            font_size=10,
            color=(100, 200, 255, 255)
        )
        effect_label.draw()

        # Value
        value_label = Label(
            f"Value: {effect.value}",
            x=x + 5,
            y=y - 40,
            font_size=10,
            color=(100, 200, 255, 255)
        )
        value_label.draw()

    def _draw_button(self, button: dict):
        """Draw a button."""
        # Button background
        bg = Rectangle(
            button['x'], button['y'],
            button['width'], button['height'],
            color=button.get('color', (60, 60, 70))
        )
        bg.draw()

        # Button label
        label = Label(
            button['label'],
            x=button['x'] + button['width'] // 2,
            y=button['y'] + button['height'] // 2,
            anchor_x='center',
            anchor_y='center',
            font_size=11,
            color=(255, 255, 255, 255)
        )
        label.draw()

    def on_mouse_press(self, x: int, y: int, button: int) -> bool:
        """Handle mouse press. Returns True if handled."""
        if not (self.x <= x <= self.x + self.width and self.y <= y <= self.y + self.height):
            return False

        # Check buttons
        for btn in self.buttons:
            if (btn['x'] <= x <= btn['x'] + btn['width'] and
                btn['y'] <= y <= btn['y'] + btn['height']):
                self._handle_button_click(btn['id'])
                return True

        # Check field clicks
        if self.upgrade:
            self._check_field_click(x, y)

        return True

    def _check_field_click(self, x: int, y: int):
        """Check if a field was clicked."""
        current_y = self.y + self.height - 140 + self.scroll_y
        padding = 10

        fields = [
            ('name', current_y, 30),
            ('description', current_y - 60, 50),
            ('tier', current_y - 140, 30),
            ('year', current_y - 200, 30),
            ('exclusive_group', current_y - 260, 30)
        ]

        for field_id, field_y, field_height in fields:
            if (self.x + padding <= x <= self.x + self.width - padding and
                field_y - field_height <= y <= field_y):
                self.active_field = field_id
                return

        self.active_field = None

    def _handle_button_click(self, button_id: str):
        """Handle button click."""
        if button_id == 'delete' and self.on_delete_node:
            self.on_delete_node()

        elif button_id == 'add_effect' and self.upgrade:
            # Add a new effect
            new_effect = Effect(
                resource="capital",
                effect="add",
                value=1.0
            )
            self.upgrade.effects.append(new_effect)
            self._create_property_fields()
            if self.on_property_changed:
                self.on_property_changed(self.upgrade)

        elif button_id == 'add_cost' and self.upgrade:
            # Add a new cost
            new_cost = ResourceCost(
                resource="capital",
                amount=10.0
            )
            self.upgrade.cost.append(new_cost)
            self._create_property_fields()
            if self.on_property_changed:
                self.on_property_changed(self.upgrade)

        elif button_id.startswith('remove_effect_') and self.upgrade:
            # Remove an effect
            index = int(button_id.split('_')[-1])
            if 0 <= index < len(self.upgrade.effects):
                self.upgrade.effects.pop(index)
                self._create_property_fields()
                if self.on_property_changed:
                    self.on_property_changed(self.upgrade)

        elif button_id.startswith('remove_cost_') and self.upgrade:
            # Remove a cost
            index = int(button_id.split('_')[-1])
            if 0 <= index < len(self.upgrade.cost):
                self.upgrade.cost.pop(index)
                self._create_property_fields()
                if self.on_property_changed:
                    self.on_property_changed(self.upgrade)

    def on_text(self, text: str):
        """Handle text input."""
        if not self.active_field or not self.upgrade:
            return

        if self.active_field == 'name':
            self.upgrade.name += text
        elif self.active_field == 'description':
            self.upgrade.description += text
        elif self.active_field == 'tier':
            try:
                current = str(self.upgrade.tier)
                self.upgrade.tier = int(current + text)
            except ValueError:
                pass
        elif self.active_field == 'year':
            try:
                current = str(self.upgrade.year)
                self.upgrade.year = int(current + text)
            except ValueError:
                pass
        elif self.active_field == 'exclusive_group':
            if self.upgrade.exclusive_group is None:
                self.upgrade.exclusive_group = text
            else:
                self.upgrade.exclusive_group += text

        if self.on_property_changed:
            self.on_property_changed(self.upgrade)

    def on_text_motion(self, motion: int):
        """Handle text motion (backspace, delete, etc.)."""
        if not self.active_field or not self.upgrade:
            return

        from pyglet.window import key

        if motion == key.MOTION_BACKSPACE:
            if self.active_field == 'name' and self.upgrade.name:
                self.upgrade.name = self.upgrade.name[:-1]
            elif self.active_field == 'description' and self.upgrade.description:
                self.upgrade.description = self.upgrade.description[:-1]
            elif self.active_field == 'tier':
                tier_str = str(self.upgrade.tier)[:-1]
                self.upgrade.tier = int(tier_str) if tier_str else 0
            elif self.active_field == 'year':
                year_str = str(self.upgrade.year)[:-1]
                self.upgrade.year = int(year_str) if year_str else 1800
            elif self.active_field == 'exclusive_group' and self.upgrade.exclusive_group:
                self.upgrade.exclusive_group = self.upgrade.exclusive_group[:-1]
                if not self.upgrade.exclusive_group:
                    self.upgrade.exclusive_group = None

            if self.on_property_changed:
                self.on_property_changed(self.upgrade)

    def on_mouse_scroll(self, x: int, y: int, scroll_x: float, scroll_y: float):
        """Handle mouse scroll."""
        if not (self.x <= x <= self.x + self.width):
            return

        # Scroll the properties panel
        self.scroll_y += scroll_y * 20
        self.scroll_y = max(-1000, min(0, self.scroll_y))
