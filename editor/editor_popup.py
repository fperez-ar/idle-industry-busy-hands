import pyglet
from pyglet.text import Label
from pyglet.shapes import Rectangle
from pyglet.window import key
from typing import Optional, Callable, Dict, Any
from loader import Upgrade, Effect, ResourceCost


class PopupWindow:
    """Base class for popup dialogs."""

    def __init__(self, title: str, width: int = 400, height: int = 300):
        self.title = title
        self.width = width
        self.height = height
        self.visible = False

        # Callbacks
        self.on_confirm: Optional[Callable[[Dict[str, Any]], None]] = None
        self.on_cancel: Optional[Callable[[], None]] = None

        # Fields
        self.fields: Dict[str, Any] = {}
        self.active_field: Optional[str] = None
        self.field_order: list = []

        # Buttons
        self.buttons = []

    def show(self, parent_width: int, parent_height: int):
        """Show the popup centered on screen."""
        self.visible = True
        self.x = (parent_width - self.width) // 2
        self.y = (parent_height - self.height) // 2
        self.active_field = self.field_order[0] if self.field_order else None

    def hide(self):
        """Hide the popup."""
        self.visible = False
        self.active_field = None

    def draw(self):
        """Draw the popup."""
        if not self.visible:
            return

        # Semi-transparent overlay
        overlay = Rectangle(0, 0, 10000, 10000, color=(0, 0, 0, 180))
        overlay.draw()

        # Popup background
        bg = Rectangle(self.x, self.y, self.width, self.height, color=(45, 45, 50))
        bg.draw()

        # Border
        border_color = (100, 150, 200)
        self._draw_border(self.x, self.y, self.width, self.height, border_color, 3)

        # Title
        title_label = Label(
            self.title,
            x=self.x + self.width // 2,
            y=self.y + self.height - 30,
            anchor_x='center',
            anchor_y='center',
            font_size=14,
            color=(255, 255, 255, 255)
        )
        title_label.draw()

        # Draw fields (implemented by subclasses)
        self._draw_fields()

        # Draw buttons
        for button in self.buttons:
            self._draw_button(button)

    def _draw_border(self, x: int, y: int, width: int, height: int, color: tuple, thickness: int):
        """Draw a border rectangle."""
        Rectangle(x, y + height - thickness, width, thickness, color=color).draw()
        Rectangle(x, y, width, thickness, color=color).draw()
        Rectangle(x, y, thickness, height, color=color).draw()
        Rectangle(x + width - thickness, y, thickness, height, color=color).draw()

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
            font_size=12,
            color=(255, 255, 255, 255)
        ).draw()

    def _draw_fields(self):
        """Draw input fields. Override in subclasses."""
        pass

    def _draw_field(self, label: str, field_id: str, value: str, x: int, y: int,
                    width: int, height: int = 30, multiline: bool = False):
        """Draw a labeled input field."""
        # Label
        Label(
            label,
            x=x,
            y=y + height + 5,
            font_size=11,
            color=(200, 200, 200, 255)
        ).draw()

        # Input box
        is_active = self.active_field == field_id
        bg_color = (70, 90, 110) if is_active else (55, 55, 60)

        bg = Rectangle(x, y, width, height, color=bg_color)
        bg.draw()

        if is_active:
            self._draw_border(x, y, width, height, (100, 150, 200), 2)

        # Text with cursor
        display_text = value + ("|" if is_active else "")

        Label(
            display_text,
            x=x + 8,
            y=y + height // 2,
            anchor_y='center',
            font_size=11,
            color=(255, 255, 255, 255),
            width=width - 16,
            multiline=multiline
        ).draw()

    def on_mouse_press(self, x: int, y: int, button: int) -> bool:
        """Handle mouse press. Returns True if handled."""
        if not self.visible:
            return False

        # Check if click is outside popup (cancel)
        if not (self.x <= x <= self.x + self.width and
                self.y <= y <= self.y + self.height):
            self._handle_cancel()
            return True

        # Check buttons
        for btn in self.buttons:
            if (btn['x'] <= x <= btn['x'] + btn['width'] and
                btn['y'] <= y <= btn['y'] + btn['height']):
                self._handle_button_click(btn['id'])
                return True

        # Check field clicks (implemented by subclasses)
        self._check_field_click(x, y)
        return True

    def _check_field_click(self, x: int, y: int):
        """Check if a field was clicked. Override in subclasses."""
        pass

    def _handle_button_click(self, button_id: str):
        """Handle button click."""
        if button_id == 'cancel':
            self._handle_cancel()
        elif button_id == 'create':
            self._handle_confirm()

    def _handle_cancel(self):
        """Handle cancel action."""
        self.hide()
        if self.on_cancel:
            self.on_cancel()

    def _handle_confirm(self):
        """Handle confirm action."""
        if self.on_confirm:
            self.on_confirm(self.fields)
        self.hide()

    def on_key_press(self, symbol: int, modifiers: int) -> bool:
        """Handle key press. Returns True if handled."""
        if not self.visible:
            return False

        if symbol == key.ESCAPE:
            self._handle_cancel()
            return True
        elif symbol == key.ENTER or symbol == key.RETURN:
            self._handle_confirm()
            return True
        elif symbol == key.TAB:
            # Move to next field
            if self.field_order and self.active_field:
                current_idx = self.field_order.index(self.active_field)
                next_idx = (current_idx + 1) % len(self.field_order)
                self.active_field = self.field_order[next_idx]
            return True
        elif symbol == key.DELETE or symbol == key.BACKSPACE:
            return True

        return False

    def on_text(self, text: str):
        """Handle text input."""
        if not self.visible or not self.active_field:
            return

        if self.active_field in self.fields:
            self.fields[self.active_field] += text

    def on_text_motion(self, motion: int):
        """Handle text motion (backspace, etc.)."""
        if not self.visible or not self.active_field:
            return

        if motion == key.MOTION_BACKSPACE:
            if self.active_field in self.fields and self.fields[self.active_field]:
                self.fields[self.active_field] = self.fields[self.active_field][:-1]


class AddNodePopup(PopupWindow):
    """Popup for adding a new node."""

    def __init__(self):
        super().__init__("Add New Node", width=450, height=400)

        self.fields = {
            'name': '',
            'description': '',
            'tier': '0',
            'year': '1800',
            'exclusive_group': ''
        }

        self.field_order = ['name', 'description', 'tier', 'year', 'exclusive_group']

        # Field positions (set in show())
        self.field_rects = {}

    def show(self, parent_width: int, parent_height: int):
        """Show the popup."""
        super().show(parent_width, parent_height)

        # Reset fields
        self.fields = {
            'name': 'New Upgrade',
            'description': 'Description here',
            'tier': '0',
            'year': '1800',
            'exclusive_group': ''
        }

        # Create buttons
        button_y = self.y + 20
        button_width = 100
        button_spacing = 20

        self.buttons = [
            {
                'id': 'cancel',
                'label': 'Cancel',
                'x': self.x + self.width // 2 - button_width - button_spacing // 2,
                'y': button_y,
                'width': button_width,
                'height': 35,
                'color': (80, 60, 60)
            },
            {
                'id': 'create',
                'label': 'Create',
                'x': self.x + self.width // 2 + button_spacing // 2,
                'y': button_y,
                'width': button_width,
                'height': 35,
                'color': (60, 100, 80)
            }
        ]

    def _draw_fields(self):
        """Draw input fields."""
        self.field_rects.clear()

        padding = 30
        field_width = self.width - padding * 2
        current_y = self.y + self.height - 80

        # Name
        field_height = 30
        self._draw_field("Name:", 'name', self.fields['name'],
                        self.x + padding, current_y - field_height, field_width, field_height)
        self.field_rects['name'] = (self.x + padding, current_y - field_height, field_width, field_height)
        current_y -= field_height + 45

        # Description
        field_height = 60
        self._draw_field("Description:", 'description', self.fields['description'],
                        self.x + padding, current_y - field_height, field_width, field_height, multiline=True)
        self.field_rects['description'] = (self.x + padding, current_y - field_height, field_width, field_height)
        current_y -= field_height + 45

        # Tier and Year (side by side)
        field_height = 30
        half_width = (field_width - 20) // 2

        self._draw_field("Tier:", 'tier', self.fields['tier'],
                        self.x + padding, current_y - field_height, half_width, field_height)
        self.field_rects['tier'] = (self.x + padding, current_y - field_height, half_width, field_height)

        self._draw_field("Year:", 'year', self.fields['year'],
                        self.x + padding + half_width + 20, current_y - field_height, half_width, field_height)
        self.field_rects['year'] = (self.x + padding + half_width + 20, current_y - field_height, half_width, field_height)
        current_y -= field_height + 45

        # Exclusive Group
        field_height = 30
        self._draw_field("Exclusive Group (optional):", 'exclusive_group', self.fields['exclusive_group'],
                        self.x + padding, current_y - field_height, field_width, field_height)
        self.field_rects['exclusive_group'] = (self.x + padding, current_y - field_height, field_width, field_height)

    def _check_field_click(self, x: int, y: int):
        """Check if a field was clicked."""
        for field_id, (fx, fy, fw, fh) in self.field_rects.items():
            if fx <= x <= fx + fw and fy <= y <= fy + fh:
                self.active_field = field_id
                return
        self.active_field = None


class AddEffectPopup(PopupWindow):
    """Popup for adding an effect."""

    def __init__(self):
        super().__init__("Add Effect", width=400, height=300)

        self.fields = {
            'resource': 'capital',
            'effect': 'add',
            'value': ''
        }

        self.field_order = ['resource', 'effect', 'value']
        self.field_rects = {}

    def show(self, parent_width: int, parent_height: int):
        """Show the popup."""
        super().show(parent_width, parent_height)

        # Reset fields
        self.fields = {
            'resource': 'capital',
            'effect': 'add',
            'value': ''
        }

        # Create buttons
        button_y = self.y + 20
        button_width = 100
        button_spacing = 20

        self.buttons = [
            {
                'id': 'cancel',
                'label': 'Cancel',
                'x': self.x + self.width // 2 - button_width - button_spacing // 2,
                'y': button_y,
                'width': button_width,
                'height': 35,
                'color': (80, 60, 60)
            },
            {
                'id': 'create',
                'label': 'Add Effect',
                'x': self.x + self.width // 2 + button_spacing // 2,
                'y': button_y,
                'width': button_width,
                'height': 35,
                'color': (50, 100, 150)
            }
        ]

    def _draw_fields(self):
        """Draw input fields."""
        self.field_rects.clear()

        padding = 30
        field_width = self.width - padding * 2
        field_height = 30
        current_y = self.y + self.height - 80

        # Resource
        self._draw_field("Resource:", 'resource', self.fields['resource'],
                        self.x + padding, current_y - field_height, field_width, field_height)
        self.field_rects['resource'] = (self.x + padding, current_y - field_height, field_width, field_height)
        current_y -= field_height + 45

        # Effect type
        self._draw_field("Effect Type (add/mult):", 'effect', self.fields['effect'],
                        self.x + padding, current_y - field_height, field_width, field_height)
        self.field_rects['effect'] = (self.x + padding, current_y - field_height, field_width, field_height)
        current_y -= field_height + 45

        # Value
        self._draw_field("Value:", 'value', self.fields['value'],
                        self.x + padding, current_y - field_height, field_width, field_height)
        self.field_rects['value'] = (self.x + padding, current_y - field_height, field_width, field_height)

    def _check_field_click(self, x: int, y: int):
        """Check if a field was clicked."""
        for field_id, (fx, fy, fw, fh) in self.field_rects.items():
            if fx <= x <= fx + fw and fy <= y <= fy + fh:
                self.active_field = field_id
                return
        self.active_field = None

    def on_text(self, text: str):
        """Handle text input with validation."""
        if not self.visible or not self.active_field:
            return

        # For value field, only allow numbers, dots, and minus
        if self.active_field == 'value':
            if text.isdigit() or text in ('.', '-'):
                self.fields[self.active_field] += text
        else:
            self.fields[self.active_field] += text


class AddCostPopup(PopupWindow):
    """Popup for adding a cost."""

    def __init__(self):
        super().__init__("Add Cost", width=400, height=250)

        self.fields = {
            'resource': 'capital',
            'amount': '10.0'
        }

        self.field_order = ['resource', 'amount']
        self.field_rects = {}

    def show(self, parent_width: int, parent_height: int):
        """Show the popup."""
        super().show(parent_width, parent_height)

        # Reset fields
        self.fields = {
            'resource': 'capital',
            'amount': '10.0'
        }

        # Create buttons
        button_y = self.y + 20
        button_width = 100
        button_spacing = 20

        self.buttons = [
            {
                'id': 'cancel',
                'label': 'Cancel',
                'x': self.x + self.width // 2 - button_width - button_spacing // 2,
                'y': button_y,
                'width': button_width,
                'height': 35,
                'color': (80, 60, 60)
            },
            {
                'id': 'create',
                'label': 'Add Cost',
                'x': self.x + self.width // 2 + button_spacing // 2,
                'y': button_y,
                'width': button_width,
                'height': 35,
                'color': (150, 100, 50)
            }
        ]

    def _draw_fields(self):
        """Draw input fields."""
        self.field_rects.clear()

        padding = 30
        field_width = self.width - padding * 2
        field_height = 30
        current_y = self.y + self.height - 80

        # Resource
        self._draw_field("Resource:", 'resource', self.fields['resource'],
                        self.x + padding, current_y - field_height, field_width, field_height)
        self.field_rects['resource'] = (self.x + padding, current_y - field_height, field_width, field_height)
        current_y -= field_height + 45

        # Amount
        self._draw_field("Amount:", 'amount', self.fields['amount'],
                        self.x + padding, current_y - field_height, field_width, field_height)
        self.field_rects['amount'] = (self.x + padding, current_y - field_height, field_width, field_height)

    def _check_field_click(self, x: int, y: int):
        """Check if a field was clicked."""
        for field_id, (fx, fy, fw, fh) in self.field_rects.items():
            if fx <= x <= fx + fw and fy <= y <= fy + fh:
                self.active_field = field_id
                return
        self.active_field = None

    def on_text(self, text: str):
        """Handle text input with validation."""
        if not self.visible or not self.active_field:
            return

        # For amount field, only allow numbers, dots, and minus
        if self.active_field == 'amount':
            if text.isdigit() or text in ('.', '-'):
                self.fields[self.active_field] += text
        else:
            self.fields[self.active_field] += text