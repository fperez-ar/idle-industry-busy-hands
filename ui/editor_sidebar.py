# ui/editor_sidebar.py

import pyglet
from pyglet.text import Label
from pyglet.shapes import Rectangle
from typing import Optional, Callable


class EditorSidebar:
    """Sidebar with editor tools and actions."""

    def __init__(self, x: int, y: int, width: int, height: int):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

        self.buttons = []

        # Callbacks
        self.on_new_tree: Optional[Callable[[], None]] = None
        self.on_load_tree: Optional[Callable[[str], None]] = None
        self.on_save_tree: Optional[Callable[[Optional[str]], None]] = None
        self.on_add_node: Optional[Callable[[], None]] = None

        self._create_ui()

    def _create_ui(self):
        """Create sidebar UI."""
        # Create buttons
        button_height = 50
        button_spacing = 10
        button_width = self.width - 20
        current_y = self.y + self.height - 80

        self.buttons.append({
            'id': 'new',
            'label': '📄 New Tree',
            'x': self.x + 10,
            'y': current_y,
            'width': button_width,
            'height': button_height
        })
        current_y -= button_height + button_spacing

        self.buttons.append({
            'id': 'load',
            'label': '📂 Load Tree',
            'x': self.x + 10,
            'y': current_y,
            'width': button_width,
            'height': button_height
        })
        current_y -= button_height + button_spacing

        self.buttons.append({
            'id': 'save',
            'label': '💾 Save Tree',
            'x': self.x + 10,
            'y': current_y,
            'width': button_width,
            'height': button_height
        })
        current_y -= button_height + button_spacing * 2

        self.buttons.append({
            'id': 'add_node',
            'label': '➕ Add Node',
            'x': self.x + 10,
            'y': current_y,
            'width': button_width,
            'height': button_height
        })

    def draw(self):
        """Draw the sidebar."""
        # Background
        bg = Rectangle(
            self.x, self.y,
            self.width, self.height,
            color=(40, 40, 45)
        )
        bg.draw()

        # Title
        title = Label(
            "Tech Tree Editor",
            x=self.x + self.width // 2,
            y=self.y + self.height - 30,
            anchor_x='center',
            font_size=16,
            color=(255, 255, 255, 255)
        )
        title.draw()

        # Draw buttons
        for button in self.buttons:
            self._draw_button(button)

        # Instructions
        instructions_y = self.y + 300
        instructions = [
            "Keyboard Shortcuts:",
            "",
            "C - Connect nodes",
            "Del - Delete node",
            "R - Reset camera",
            "Ctrl+S - Save",
            "Ctrl+N - New tree",
            "ESC - Cancel/Deselect",
            "",
            "Mouse:",
            "Drag node - Move",
            "Right-drag - Pan",
            "Scroll - Zoom"
        ]

        for i, text in enumerate(instructions):
            instr_label = Label(
                text,
                x=self.x + 10,
                y=instructions_y - i * 20,
                font_size=15,
                color=(150, 150, 150, 255)
            )
            instr_label.draw()

    def _draw_button(self, button: dict):
        """Draw a single button."""
        # Button background
        bg = Rectangle(
            button['x'], button['y'],
            button['width'], button['height'],
            color=(60, 60, 70)
        )
        bg.draw()

        # Button label
        label = Label(
            button['label'],
            x=button['x'] + button['width'] // 2,
            y=button['y'] + button['height'] // 2,
            anchor_x='center',
            anchor_y='center',
            font_size=12,
            color=(255, 255, 255, 255)
        )
        label.draw()

    def on_mouse_press(self, x: int, y: int, button: int) -> bool:
        """Handle mouse press. Returns True if handled."""
        if not (self.x <= x <= self.x + self.width):
            return False

        for btn in self.buttons:
            if (btn['x'] <= x <= btn['x'] + btn['width'] and
                btn['y'] <= y <= btn['y'] + btn['height']):
                self._handle_button_click(btn['id'])
                return True

        return False

    def _handle_button_click(self, button_id: str):
        """Handle button click."""
        if button_id == 'new' and self.on_new_tree:
            self.on_new_tree()
        elif button_id == 'load' and self.on_load_tree:
            # For now, use a default path - could add file dialog
            filepath = input("Enter file path to load: ")
            if filepath:
                self.on_load_tree(filepath)
        elif button_id == 'save' and self.on_save_tree:
            self.on_save_tree(None)
        elif button_id == 'add_node' and self.on_add_node:
            self.on_add_node()
