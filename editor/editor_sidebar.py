import pyglet
from pyglet.text import Label
from pyglet.shapes import Rectangle
from typing import Optional, Callable
import os
import glob

DATA_FOLDER = 'data'
OFFSET_TREE_FILE_BTNS = 12

class EditorSidebar:
    """Sidebar with editor tools and actions."""

    def __init__(self, x: int, y: int, width: int, height: int):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

        self.buttons = []
        self.tree_file_buttons = []
        self.scroll_y = 0

        # Callbacks
        self.on_new_tree: Optional[Callable[[], None]] = None
        self.on_load_tree: Optional[Callable[[str], None]] = None
        self.on_save_tree: Optional[Callable[[Optional[str]], None]] = None
        self.on_add_node: Optional[Callable[[], None]] = None
        self.on_auto_layout: Optional[Callable[[], None]] = None

        self._create_ui()
        self._scan_tree_files()
        self._auto_load_first_tree()

    def _create_ui(self):
        """Create sidebar UI."""
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
        current_y -= button_height + button_spacing

        self.buttons.append({
            'id': 'auto_layout',
            'label': '🎨 Auto Layout',
            'x': self.x + 10,
            'y': current_y,
            'width': button_width,
            'height': button_height
        })
        current_y -= button_height + button_spacing

        self.buttons.append({
            'id': 'refresh',
            'label': '🔄 Refresh Files',
            'x': self.x + 10,
            'y': current_y,
            'width': button_width,
            'height': button_height
        })

    def _draw_button(self, button: dict):
        """Draw a single button."""
        bg = Rectangle(
            button['x'], button['y'],
            button['width'], button['height'],
            color=(60, 60, 70)
        )
        bg.draw()

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

    def _handle_button_click(self, button_id: str):
        """Handle button click."""
        if button_id == 'new' and self.on_new_tree:
            self.on_new_tree()
        elif button_id == 'load' and self.on_load_tree:
            filepath = input("Enter file path to load: ")
            if filepath:
                self.on_load_tree(filepath)
        elif button_id == 'save' and self.on_save_tree:
            self.on_save_tree(None)
        elif button_id == 'add_node' and self.on_add_node:
            self.on_add_node()
        elif button_id == 'auto_layout' and self.on_auto_layout:
            self.on_auto_layout()
        elif button_id == 'refresh':
            print("🔄 Refreshed tree file list")
            self._scan_tree_files()

    def _scan_tree_files(self):
        """Scan data/ folder for YAML tree files."""
        self.tree_file_buttons = []

        if not os.path.exists(DATA_FOLDER):
            print(f"⚠️ Data folder '{DATA_FOLDER}' not found")
            return

        tree_files = glob.glob(os.path.join(DATA_FOLDER, "*.yml"))
        tree_files.extend(glob.glob(os.path.join(DATA_FOLDER, "*.yaml")))
        tree_files = list(filter(lambda t: 'tree' in t, tree_files))

        if not tree_files:
            print(f"⚠️ No YAML files found in '{DATA_FOLDER}'")
            return

        button_height = 40
        button_spacing = 5
        button_width = self.width - 20
        current_y = 250

        for filepath in sorted(tree_files):
            filename = os.path.basename(filepath)
            tree_name = filename.replace(".yml", "").replace(".yaml", "")
            tree_name = tree_name.replace("_", " ").title()

            self.tree_file_buttons.append({
                'filepath': filepath,
                'label': f"📁 {tree_name}",
                'x': self.x + 10,
                'y': current_y,
                'width': button_width,
                'height': button_height
            })
            current_y -= button_height + button_spacing

        print(f"✅ Found {len(tree_files)} tree file(s)")

    def _auto_load_first_tree(self):
        """Auto-load the first tree file on startup."""
        if self.tree_file_buttons and self.on_load_tree:
            first_tree = self.tree_file_buttons[0]['filepath']
            print(f"🚀 Auto-loading: {first_tree}")
            self.on_load_tree(first_tree)

    def on_mouse_press(self, x: int, y: int, button: int) -> bool:
        """Handle mouse press. Returns True if handled."""
        if not (self.x <= x <= self.x + self.width):
            return False

        for btn in self.buttons:
            if (btn['x'] <= x <= btn['x'] + btn['width'] and
                btn['y'] <= y <= btn['y'] + btn['height']):
                self._handle_button_click(btn['id'])
                return True

        # Calculate the same offset as in draw()
        if self.buttons:
            offset_y = self.buttons[-1]['y'] - OFFSET_TREE_FILE_BTNS
        else:
            offset_y = self.y + self.height - 100

        tree_buttons_start_y = offset_y - 25

        for i, btn in enumerate(self.tree_file_buttons):
            # Calculate the same adjusted Y as in draw()
            adjusted_y = tree_buttons_start_y - (i * (btn['height'] + 5)) + self.scroll_y

            if (btn['x'] <= x <= btn['x'] + btn['width'] and
                adjusted_y <= y <= adjusted_y + btn['height']):
                if self.on_load_tree:
                    self.on_load_tree(btn['filepath'])
                return True

        return False

    def on_mouse_scroll(self, x: int, y: int, scroll_x: float, scroll_y: float):
        """Handle mouse scroll for tree file list."""
        if not (self.x <= x <= self.x + self.width):
            return

        self.scroll_y += scroll_y * 10
        max_scroll = max(0, len(self.tree_file_buttons) * 45 - 200)
        self.scroll_y = max(-max_scroll, min(0, self.scroll_y))

    def draw(self):
        """Draw the sidebar."""
        bg = Rectangle(
            self.x, self.y,
            self.width, self.height,
            color=(40, 40, 45)
        )
        bg.draw()

        title = Label(
            "Tech Tree Editor",
            x=self.x + self.width // 2,
            y=self.y + self.height - 30,
            anchor_x='center',
            font_size=16,
            color=(255, 255, 255, 255)
        )
        title.draw()

        for button in self.buttons:
            self._draw_button(button)

        # Calculate offset based on last button position
        if self.buttons:
            offset_y = self.buttons[-1]['y'] - OFFSET_TREE_FILE_BTNS
        else:
            offset_y = self.y + self.height - 100

        section_label = Label(
            "Load Tree:",
            x=self.x + 10,
            y=offset_y,
            font_size=12,
            color=(200, 200, 200, 255)
        )
        section_label.draw()

        # Adjust tree file buttons to start below section label
        tree_buttons_start_y = offset_y - 25

        for i, button in enumerate(self.tree_file_buttons):
            adjusted_button = button.copy()
            # Position relative to the calculated start position
            adjusted_button['y'] = tree_buttons_start_y - (i * (button['height'] + 5)) + self.scroll_y

            if self.y < adjusted_button['y'] < self.y + self.height:
                self._draw_button(adjusted_button)

        # Position instructions below tree file buttons
        if self.tree_file_buttons:
            last_button_y = tree_buttons_start_y - (len(self.tree_file_buttons) * 45)
            instructions_y = last_button_y - 30
        else:
            instructions_y = tree_buttons_start_y - 30

        instructions = [
            "Keyboard Shortcuts:",
            "",
            "C - Connect nodes",
            "Del - Delete node",
            "L - Auto layout",
            "R - Reset camera",
            "H - Show help",
            "Ctrl+S - Save",
            "Ctrl+N - New tree",
            "ESC - Cancel/Deselect",
            "ESC (2x) - Quit",
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
                y=instructions_y - i * 15,  # Reduced spacing to 15px
                font_size=9,  # Reduced font size to fit better
                color=(150, 150, 150, 255)
            )
            instr_label.draw()