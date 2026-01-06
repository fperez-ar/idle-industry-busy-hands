"""Common UI drawing utilities for the tech tree editor."""

import pyglet
from pyglet.text import Label
from pyglet.shapes import Rectangle
from typing import Tuple, Optional


class UIColors:
    """Standard color palette for the editor."""
    BACKGROUND_DARK = (25, 25, 30)
    BACKGROUND_MEDIUM = (35, 35, 40)
    BACKGROUND_LIGHT = (45, 45, 50)
    PANEL_BG = (40, 40, 45)

    FIELD_INACTIVE = (60, 60, 70)
    FIELD_ACTIVE = (70, 90, 110)
    FIELD_READONLY = (50, 50, 55)

    BORDER_ACTIVE = (100, 150, 200)
    BORDER_NORMAL = (100, 100, 100)

    BUTTON_DEFAULT = (60, 60, 70)
    BUTTON_DELETE = (150, 50, 50)
    BUTTON_ADD_EFFECT = (50, 100, 150)
    BUTTON_ADD_COST = (150, 100, 50)
    BUTTON_CONFIRM = (60, 100, 80)
    BUTTON_CANCEL = (80, 60, 60)

    TEXT_PRIMARY = (255, 255, 255, 255)
    TEXT_SECONDARY = (200, 200, 200, 255)
    TEXT_DISABLED = (150, 150, 150, 255)
    TEXT_MUTED = (100, 100, 100, 255)

    CONNECTION_NORMAL = (100, 150, 200)
    CONNECTION_OR = (200, 180, 50)
    CONNECTION_PREVIEW = (255, 255, 100)


def draw_border(x: int, y: int, width: int, height: int,
                color: Tuple[int, int, int], thickness: int = 2):
    """Draw a border rectangle around a region."""
    Rectangle(x, y + height - thickness, width, thickness, color=color).draw()
    Rectangle(x, y, width, thickness, color=color).draw()
    Rectangle(x, y, thickness, height, color=color).draw()
    Rectangle(x + width - thickness, y, thickness, height, color=color).draw()


def draw_button(button: dict, default_color: Optional[Tuple] = None):
    """
    Draw a button with label.

    Expected button dict format:
    {
        'x': int, 'y': int, 'width': int, 'height': int,
        'label': str, 'color': tuple (optional)
    }
    """
    color = button.get('color', default_color or UIColors.BUTTON_DEFAULT)

    bg = Rectangle(
        button['x'], button['y'],
        button['width'], button['height'],
        color=color
    )
    bg.draw()

    label = Label(
        button['label'],
        x=button['x'] + button['width'] // 2,
        y=button['y'] + button['height'] // 2,
        anchor_x='center',
        anchor_y='center',
        font_size=button.get('font_size', 11),
        color=UIColors.TEXT_PRIMARY
    )
    label.draw()


def draw_labeled_field(label_text: str, value: str, x: int, y: int,
                       width: int, height: int = 30,
                       is_active: bool = False,
                       is_readonly: bool = False,
                       multiline: bool = False,
                       font_size: int = 11) -> Tuple[int, int, int, int]:
    """
    Draw a labeled input field.

    Returns: (field_x, field_y, field_width, field_height) for click detection
    """
    # Label
    Label(
        label_text,
        x=x,
        y=y + height + 5,
        font_size=font_size,
        color=UIColors.TEXT_SECONDARY
    ).draw()

    # Field background
    field_y = y
    if is_readonly:
        bg_color = UIColors.FIELD_READONLY
    elif is_active:
        bg_color = UIColors.FIELD_ACTIVE
    else:
        bg_color = UIColors.FIELD_INACTIVE

    bg = Rectangle(x, field_y, width, height, color=bg_color)
    bg.draw()

    # Border for active field
    if is_active:
        draw_border(x, field_y, width, height, UIColors.BORDER_ACTIVE)

    # Text with cursor
    display_text = value + ("|" if is_active else "")
    text_color = UIColors.TEXT_DISABLED if is_readonly else UIColors.TEXT_PRIMARY

    Label(
        display_text,
        x=x + 8,
        y=field_y + height // 2,
        anchor_y='center',
        font_size=font_size,
        color=text_color,
        width=width - 16,
        multiline=multiline
    ).draw()

    return (x, field_y, width, height)


def is_point_in_rect(px: int, py: int, x: int, y: int,
                     width: int, height: int) -> bool:
    """Check if a point is inside a rectangle."""
    return x <= px <= x + width and y <= py <= y + height


def create_button_dict(button_id: str, label: str, x: int, y: int,
                       width: int, height: int,
                       color: Optional[Tuple] = None) -> dict:
    """Create a standardized button dictionary."""
    return {
        'id': button_id,
        'label': label,
        'x': x,
        'y': y,
        'width': width,
        'height': height,
        'color': color or UIColors.BUTTON_DEFAULT
    }
