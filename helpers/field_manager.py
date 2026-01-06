"""Manage field state and interactions for forms."""

from typing import Dict, Tuple, Optional, Callable, Any


class FieldManager:
    """Manages field state, validation, and interactions."""

    def __init__(self):
        self.fields: Dict[str, str] = {}
        self.field_rects: Dict[str, Tuple[int, int, int, int]] = {}
        self.field_order: list = []
        self.active_field: Optional[str] = None
        self.is_editing: bool = False

        # Callbacks
        self.on_field_changed: Optional[Callable[[str, Any], None]] = None
        self.on_field_validated: Optional[Callable[[str, Any], None]] = None

    def register_field(self, field_id: str, x: int, y: int,
                      width: int, height: int):
        """Register a clickable field area."""
        self.field_rects[field_id] = (x, y, width, height)

    def clear_field_rects(self):
        """Clear field rectangles (call at start of each draw)."""
        self.field_rects.clear()

    def check_field_click(self, x: int, y: int) -> Optional[str]:
        """
        Check if a field was clicked.

        Returns: field_id if clicked, None otherwise
        """
        for field_id, (fx, fy, fw, fh) in self.field_rects.items():
            if fx <= x <= fx + fw and fy <= y <= fy + fh:
                return field_id
        return None

    def activate_field(self, field_id: Optional[str]):
        """Activate a field for editing."""
        if self.active_field and self.active_field != field_id:
            # Validate previous field before switching
            if self.on_field_validated:
                self.on_field_validated(self.active_field,
                                       self.fields.get(self.active_field))

        self.active_field = field_id
        self.is_editing = field_id is not None

    def get_field_value(self, field_id: str) -> str:
        """Get the current value of a field."""
        return self.fields.get(field_id, '')

    def set_field_value(self, field_id: str, value: str):
        """Set the value of a field."""
        self.fields[field_id] = value
        if self.on_field_changed:
            self.on_field_changed(field_id, value)

    def handle_text_input(self, text: str,
                         validator: Optional[Callable[[str, str], Optional[str]]] = None):
        """Handle text input for the active field."""
        if not self.active_field:
            return

        current_value = self.get_field_value(self.active_field)

        if validator:
            new_value = validator(current_value, text)
            if new_value is not None:
                self.set_field_value(self.active_field, new_value)
        else:
            self.set_field_value(self.active_field, current_value + text)

    def handle_backspace(self):
        """Handle backspace for the active field."""
        if not self.active_field:
            return

        current_value = self.get_field_value(self.active_field)
        if current_value:
            self.set_field_value(self.active_field, current_value[:-1])

    def move_to_next_field(self):
        """Move focus to the next field in order."""
        if not self.field_order or not self.active_field:
            return

        try:
            current_idx = self.field_order.index(self.active_field)
            next_idx = (current_idx + 1) % len(self.field_order)
            self.activate_field(self.field_order[next_idx])
        except ValueError:
            pass

    def move_to_previous_field(self):
        """Move focus to the previous field in order."""
        if not self.field_order or not self.active_field:
            return

        try:
            current_idx = self.field_order.index(self.active_field)
            prev_idx = (current_idx - 1) % len(self.field_order)
            self.activate_field(self.field_order[prev_idx])
        except ValueError:
            pass
