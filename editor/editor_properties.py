import pyglet
from pyglet.window import key
from pyglet.text import Label
from pyglet.shapes import Rectangle
from typing import Optional, Callable, Dict, Tuple
from loader import Upgrade, Effect, ResourceCost

# Import helper modules
from helpers.ui_helpers import (
    UIColors, draw_border, draw_button, draw_labeled_field,
    is_point_in_rect, create_button_dict
)
from helpers.validation_helpers import (
    validate_numeric_field, format_numeric_input, is_numeric_field
)
from helpers.field_manager import FieldManager
from helpers.button_manager import ButtonManager

# Layout constants
PADDING = 25
FIELD_HEIGHT = 35
MULTILINE_HEIGHT = 60
SECTION_SPACING = 40
EFFECT_HEIGHT = 100
COST_HEIGHT = 70

class PropertiesPanel:
    """Panel for editing node properties."""

    def __init__(self, x: int, y: int, width: int, height: int, overrides: Dict):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.upgrade: Optional[Upgrade] = None
        self.scroll_y = 0
        self.overrides = overrides

        # Use helper managers
        self.field_manager = FieldManager()
        self.button_manager = ButtonManager()

        # Set up callbacks
        self.field_manager.on_field_changed = self._on_field_changed
        # self.field_manager.on_field_validated = self._on_field_validated
        self.button_manager.on_button_click = self._handle_button_click

        # External callbacks
        self.on_property_changed: Optional[Callable[[Upgrade], None]] = None
        self.on_delete_node: Optional[Callable[[], None]] = None
        self.on_show_effect_popup: Optional[Callable[[], None]] = None
        self.on_show_cost_popup: Optional[Callable[[], None]] = None

        # Temporary storage for editing values
        self._editing_values: Dict[str, str] = {}
        self.field_selected_for_replacement = False

    @property
    def is_editing(self) -> bool:
        """Check if currently editing a field."""
        return self.field_manager.is_editing

    @property
    def active_field(self) -> Optional[str]:
        """Get the currently active field."""
        return self.field_manager.active_field

    def _on_field_changed(self, field_id: str, value: str):
        """Handle field value change."""
        if self.upgrade:
            # Don't call _set_field_value_string here as it's already been called
            # Just trigger the property changed callback
            if self.on_property_changed:
                self.on_property_changed(self.upgrade)

    def _on_field_validated(self, field_id: str, value: str):
        """Handle field validation on blur."""
        if not self.upgrade:
            return

        is_numeric, is_integer = is_numeric_field(field_id)

        if is_numeric:
            # Determine validation parameters
            if field_id == 'year':
                min_val = self._get_from_overrides('year', 'min')
                max_val = self._get_from_overrides('year', 'max')

            elif field_id == 'tier':
                min_val, max_val = -100, 100
            else:
                min_val, max_val = -100.0, 100.0

            validated = validate_numeric_field(value, is_integer, min_val, max_val)
            self._set_field_value_string(field_id, str(validated))

            if self.on_property_changed:
                self.on_property_changed(self.upgrade)

    def _get_from_overrides(self, attr_name: str, attr_val_name: str):
      return self.overrides.get(attr_name, {}).get(attr_val_name, -1)

    def _get_field_value_string(self, field: str) -> str:
        """Get the current string value for a field."""
        # Priority 1: Return editing value if available (for numeric fields during editing)
        if field in self._editing_values:
            return self._editing_values[field]

        # Priority 2: Check field_manager for non-numeric fields during editing
        if hasattr(self, 'field_manager') and field in self.field_manager.fields:
            value = self.field_manager.fields[field]
            if value:  # Only return if not empty
                return value

        # Priority 3: Fall back to upgrade object values
        if not self.upgrade:
            return ''

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
        print(f"DEBUG: Setting field '{field}' to value '{value}'")  # ADD THIS
        is_numeric, is_integer = is_numeric_field(field)

        # For numeric fields, store the raw string during editing
        if is_numeric:
            self._editing_values[field] = value
            # ALSO store in field_manager for consistency
            self.field_manager.fields[field] = value

            # Also update the upgrade object with a temporary conversion
            # (will be properly validated on blur)
            try:
                if value in ('-', '.', '-.', ''):
                    temp_value = 0
                else:
                    temp_value = float(value)
                    if is_integer:
                        temp_value = int(temp_value)
            except ValueError:
                temp_value = 0

            # Update the actual upgrade object
            if field == 'tier':
                self.upgrade.tier = int(temp_value)

            elif field == 'year':
                self.upgrade.year = int(temp_value)

            elif field.endswith('_value'):
                parts = field.split('_')
                index = int(parts[1])
                if 0 <= index < len(self.upgrade.effects):
                    self.upgrade.effects[index].value = float(temp_value)

            elif field.endswith('_amount'):
                parts = field.split('_')
                index = int(parts[1])
                if 0 <= index < len(self.upgrade.cost):
                    self.upgrade.cost[index].amount = float(temp_value)

            return

        # For non-numeric fields, set directly AND store in field_manager
        self.field_manager.fields[field] = value

        if field == 'name':
            self.upgrade.name = value

        elif field == 'description':
            self.upgrade.description = value

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

        elif field.startswith('cost_'):
            parts = field.split('_')
            index = int(parts[1])
            subfield = parts[2]
            if 0 <= index < len(self.upgrade.cost):
                cost = self.upgrade.cost[index]
                if subfield == 'resource':
                    cost.resource = value

    def _get_content_start_y(self) -> int:
        """Get the starting Y position for content below the delete button."""
        return self.y + self.height - 100 + self.scroll_y

    def _register_field(self, field_id: str, x: int, y: int, width: int, height: int):
        """Register a clickable field area."""
        self.field_manager.register_field(field_id, x, y, width, height)

    def _register_button(self, button: dict):
        """Register a button, updating if it exists."""
        self.button_manager.register_button(button)

    def _draw_labeled_field(self, label: str, field_id: str, value: str, y: int,
                            read_only: bool = False, multiline: bool = False, width: int = None) -> int:
        """Draw a labeled input field. Returns the Y position after drawing."""
        if width is None:
            width = self.width - PADDING * 2

        field_height = MULTILINE_HEIGHT if multiline else FIELD_HEIGHT
        is_active = self.field_manager.active_field == field_id and not read_only

        # Use helper function
        field_rect = draw_labeled_field(
            label, value,
            self.x + PADDING, y - 20 - field_height,
            width, field_height,
            is_active=is_active,
            is_readonly=read_only,
            multiline=multiline
        )

        # Register with field manager
        if not read_only:
            self.field_manager.register_field(field_id, *field_rect)

        return field_rect[1]  # Return bottom Y

    def _draw_field_border(self, x: int, y: int, width: int, height: int):
        """Draw a border around an active field."""
        draw_border(x, y, width, height, UIColors.BORDER_ACTIVE, thickness=2)

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
        box_width = self.width - PADDING * 2 - 35
        box_height = EFFECT_HEIGHT
        box_bottom = y - box_height

        # Background box
        Rectangle(box_x, box_bottom, box_width, box_height,
                color=(45, 55, 65)).draw()

        # Remove button using helpers
        remove_btn = create_button_dict(
            f'remove_effect_{index}', '✕',
            box_x + box_width + 5, y - 35, 25, 25,
            color=UIColors.BUTTON_DELETE
        )
        self.button_manager.register_button(remove_btn)
        draw_button(remove_btn)


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
        draw_button(button)

    def _validate_and_blur_field(self):
        """Validate the current active field and apply formatting."""
        if not self.field_manager.active_field or not self.upgrade:
            return

        is_numeric, is_integer = is_numeric_field(self.field_manager.active_field)

        if is_numeric:
            # Get the raw editing value
            current_value = self._editing_values.get(
                self.field_manager.active_field,
                self._get_field_value_string(self.field_manager.active_field)
            )

            # Determine validation parameters
            if self.field_manager.active_field == 'year':
                min_val = self._get_from_overrides('year', 'min')
                max_val = self._get_from_overrides('year', 'max')
                validated_value = validate_numeric_field(
                    current_value, is_integer=True, min_val=min_val, max_val=max_val
                )
            elif self.field_manager.active_field == 'tier':
                min_val = self._get_from_overrides('tier', 'min')
                max_val = self._get_from_overrides('tier', 'max')
                validated_value = validate_numeric_field(
                    current_value, is_integer=True, min_val=-min_val, max_val=max_val
                )
            else:
                validated_value = validate_numeric_field(
                    current_value, is_integer=False, min_val=0.0, max_val=100.0
                )

            # Update the actual upgrade object with validated value DIRECTLY
            # Don't call _set_field_value_string to avoid re-storing in _editing_values
            if self.field_manager.active_field == 'tier':
                self.upgrade.tier = int(validated_value)
            elif self.field_manager.active_field == 'year':
                self.upgrade.year = int(validated_value)
            elif self.field_manager.active_field.endswith('_value'):
                parts = self.field_manager.active_field.split('_')
                index = int(parts[1])
                if 0 <= index < len(self.upgrade.effects):
                    self.upgrade.effects[index].value = validated_value
            elif self.field_manager.active_field.endswith('_amount'):
                parts = self.field_manager.active_field.split('_')
                index = int(parts[1])
                if 0 <= index < len(self.upgrade.cost):
                    self.upgrade.cost[index].amount = validated_value

            # Clear the editing value
            if self.field_manager.active_field in self._editing_values:
                del self._editing_values[self.field_manager.active_field]

            # Clear from field_manager too
            if self.field_manager.active_field in self.field_manager.fields:
                del self.field_manager.fields[self.field_manager.active_field]

            if self.on_property_changed:
                self.on_property_changed(self.upgrade)


    def _handle_button_click(self, button_id: str):
        """Handle button click."""
        if button_id == 'delete' and self.on_delete_node:
            if not self.is_editing:
                self.on_delete_node()


        elif button_id == 'add_effect' and self.upgrade:
            # Show popup instead of directly adding
            if hasattr(self, 'on_show_effect_popup') and self.on_show_effect_popup:
                self.on_show_effect_popup()


        elif button_id == 'add_cost' and self.upgrade:
            # Show popup instead of directly adding
            if hasattr(self, 'on_show_cost_popup') and self.on_show_cost_popup:
                self.on_show_cost_popup()


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

            #
            # elif button_id == 'add_effect' and self.upgrade:
            #     new_effect = Effect(resource="capital", effect="add", value=0.0)
            #     self.upgrade.effects.append(new_effect)
            #     if self.on_property_changed:
            #         self.on_property_changed(self.upgrade)

            #
            # elif button_id == 'add_cost' and self.upgrade:
            #     new_cost = ResourceCost(resource="capital", amount=10.0)
            #     self.upgrade.cost.append(new_cost)
            #     if self.on_property_changed:
            #         self.on_property_changed(self.upgrade)

            #
            # elif button_id.startswith('remove_effect_') and self.upgrade:
            #     index = int(button_id.split('_')[-1])
            #     if 0 <= index < len(self.upgrade.effects):
            #         self.upgrade.effects.pop(index)
            #         if self.on_property_changed:
            #             self.on_property_changed(self.upgrade)

            #
            # elif button_id.startswith('remove_cost_') and self.upgrade:
            #     index = int(button_id.split('_')[-1])
            #     if 0 <= index < len(self.upgrade.cost):
            #         self.upgrade.cost.pop(index)
            #         if self.on_property_changed:
            #             self.on_property_changed(self.upgrade)

      ### public

  # public
    def set_upgrade(self, upgrade: Optional[Upgrade]):
        """Set the upgrade to display/edit."""
        self.upgrade = upgrade
        self.field_manager.activate_field(None)
        self.field_manager.fields.clear()  # ADD THIS LINE
        self.scroll_y = 0
        self._editing_values.clear()
        self.field_selected_for_replacement = False

    def draw(self):
      """Draw the properties panel."""
      # Clear managers each frame
      self.field_manager.clear_field_rects()
      self.button_manager.clear_buttons()

      # Background
      Rectangle(self.x, self.y, self.width, self.height,
              color=UIColors.BACKGROUND_MEDIUM).draw()

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

  # on_* handlers
    def on_mouse_press(self, x: int, y: int, button: int) -> bool:
        """Handle mouse press. Returns True if handled."""
        if not is_point_in_rect(x, y, self.x, self.y, self.width, self.height):
            if self.field_manager.active_field and self.upgrade:
                self._validate_and_blur_field()
            self.field_manager.activate_field(None)
            return False

        # Check buttons using button manager
        if self.button_manager.handle_click(x, y):
            if self.field_manager.active_field and self.upgrade:
                self._validate_and_blur_field()
            return True

        # Check field clicks using field manager
        if self.upgrade:
            clicked_field = self.field_manager.check_field_click(x, y)

            if clicked_field:
                if self.field_manager.active_field and self.field_manager.active_field != clicked_field:
                    self._validate_and_blur_field()

                self.field_manager.activate_field(clicked_field)

                # Mark numeric fields for replacement
                is_numeric, _ = is_numeric_field(clicked_field)
                if is_numeric:
                    self.field_selected_for_replacement = True
            else:
                if self.field_manager.active_field:
                    self._validate_and_blur_field()
                self.field_manager.activate_field(None)

        return True

    def on_text(self, text: str):
        """Handle text input."""
        if not self.field_manager.active_field or not self.upgrade:
            return

        is_numeric, is_integer = is_numeric_field(self.field_manager.active_field)

        if is_numeric:
            current_value = self._get_field_value_string(self.field_manager.active_field)

            if self.field_selected_for_replacement and text.isdigit():
                self.field_selected_for_replacement = False
                self._set_field_value_string(self.field_manager.active_field, text)
            else:
                self.field_selected_for_replacement = False
                formatted = format_numeric_input(current_value, text, is_integer)
                if formatted is not None:
                    self._set_field_value_string(self.field_manager.active_field, formatted)
                else:
                    return  # Don't trigger callback if input was invalid
        else:
            current_value = self._get_field_value_string(self.field_manager.active_field)
            self._set_field_value_string(self.field_manager.active_field, current_value + text)

        # Trigger callback after successful update
        if self.on_property_changed:
            self.on_property_changed(self.upgrade)

    def on_text_motion(self, motion: int):
        """Handle text motion (backspace, delete, etc.)."""
        if not self.field_manager.active_field or not self.upgrade:
            return

        if motion == key.MOTION_BACKSPACE:
            # Get current value
            current_value = self._get_field_value_string(self.field_manager.active_field)

            if current_value:
                new_value = current_value[:-1]

                # For numeric fields, ensure they don't become empty
                is_numeric, _ = is_numeric_field(self.field_manager.active_field)
                if not new_value and is_numeric:
                    new_value = "0"

                # Update the field value
                self._set_field_value_string(self.field_manager.active_field, new_value)

                if self.on_property_changed:
                    self.on_property_changed(self.upgrade)


    def on_mouse_scroll(self, x: int, y: int, scroll_x: float, scroll_y: float):
        """Handle mouse scroll."""
        if not (self.x <= x <= self.x + self.width):
            return

        self.scroll_y += scroll_y * 30
        self.scroll_y = max(-1500, min(0, self.scroll_y))
