"""Manage button state and interactions."""

from typing import Dict, List, Optional, Callable

class ButtonManager:
    """Manages button state and click handling."""

    def __init__(self):
        self.buttons: List[dict] = []
        self.on_button_click: Optional[Callable[[str], None]] = None

    def register_button(self, button: dict):
        """Register or update a button."""
        for i, btn in enumerate(self.buttons):
            if btn['id'] == button['id']:
                self.buttons[i] = button
                return
        self.buttons.append(button)

    def clear_buttons(self):
        """Clear all buttons."""
        self.buttons.clear()

    def check_button_click(self, x: int, y: int) -> Optional[str]:
        """
        Check if a button was clicked.

        Returns: button_id if clicked, None otherwise
        """
        for btn in self.buttons:
            if (btn['x'] <= x <= btn['x'] + btn['width'] and
                btn['y'] <= y <= btn['y'] + btn['height']):
                return btn['id']
        return None

    def handle_click(self, x: int, y: int) -> bool:
        """
        Handle a click, triggering callback if button was clicked.

        Returns: True if a button was clicked
        """
        button_id = self.check_button_click(x, y)
        if button_id and self.on_button_click:
            self.on_button_click(button_id)
            return True
        return False

    def get_button(self, button_id: str) -> Optional[dict]:
        """Get a button by ID."""
        for btn in self.buttons:
            if btn['id'] == button_id:
                return btn
        return None
