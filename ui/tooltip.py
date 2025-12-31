# ui/tooltip.py

import pyglet
from pyglet.text import Label
from pyglet.shapes import Rectangle
from typing import Optional
from loader import Upgrade


class Tooltip:
    """Displays detailed information about an upgrade on hover."""

    # Scale factor for all UI elements (1.0 = normal, 1.5 = 50% larger, etc.)
    UI_SCALE = 1.5

    # Base dimensions (will be scaled)
    BASE_MAX_WIDTH = 320
    BASE_PADDING = 12
    BASE_LINE_HEIGHT = 18
    BASE_BORDER_WIDTH = 2

    def __init__(self):
        self.visible = False
        self.x = 0
        self.y = 0
        self.upgrade: Optional[Upgrade] = None
        self.is_owned = False
        self.is_available = False

        # Apply scaling
        self.MAX_WIDTH = int(self.BASE_MAX_WIDTH * self.UI_SCALE)
        self.PADDING = int(self.BASE_PADDING * self.UI_SCALE)
        self.LINE_HEIGHT = int(self.BASE_LINE_HEIGHT * self.UI_SCALE)
        self.BORDER_WIDTH = int(self.BASE_BORDER_WIDTH * self.UI_SCALE)

        # Font sizes (scaled)
        self.FONT_SIZE_TITLE = int(14 * self.UI_SCALE)
        self.FONT_SIZE_NORMAL = int(12 * self.UI_SCALE)
        self.FONT_SIZE_SMALL = int(11 * self.UI_SCALE)
        self.FONT_SIZE_TINY = int(10 * self.UI_SCALE)

        # Cursor offset (scaled)
        self.CURSOR_OFFSET = int(15 * self.UI_SCALE)

        # Hover delay tracking
        self.hover_time = 0.0
        self.hover_delay = 1.2
        self.current_hover_upgrade_id: Optional[str] = None

    def start_hover(self, upgrade: Upgrade, x: int, y: int, is_owned: bool, is_available: bool):
        """Start tracking hover over an upgrade."""
        if self.current_hover_upgrade_id != upgrade.id:
            # Reset timer if hovering over a different upgrade
            self.hover_time = 0.0
            self.current_hover_upgrade_id = upgrade.id

        self.upgrade = upgrade
        self.x = x + self.CURSOR_OFFSET
        self.y = y + self.CURSOR_OFFSET
        self.is_owned = is_owned
        self.is_available = is_available

    def update(self, dt: float):
        """Update hover timer."""
        if self.current_hover_upgrade_id:
            self.hover_time += dt
            if self.hover_time >= self.hover_delay:
                self.visible = True
        else:
            self.visible = False
            self.hover_time = 0.0

    def cancel_hover(self):
        """Cancel current hover."""
        self.visible = False
        self.hover_time = 0.0
        self.current_hover_upgrade_id = None
        self.upgrade = None

    def draw(self, window_width: int, window_height: int):
        """Draw the tooltip."""
        if not self.visible or not self.upgrade:
            return

        # Build content
        lines = self._build_content()

        # Calculate dimensions
        total_height = 50 + len(lines) * self.LINE_HEIGHT + self.PADDING * 2

        # Adjust position to keep tooltip on screen
        draw_x = self.x
        draw_y = self.y

        screen_margin = int(10 * self.UI_SCALE)

        if draw_x + self.MAX_WIDTH > window_width:
            draw_x = window_width - self.MAX_WIDTH - screen_margin
        if draw_y - total_height < 0:
            draw_y = total_height + screen_margin

        # Draw border
        border = Rectangle(
            draw_x - self.BORDER_WIDTH,
            draw_y - total_height - self.BORDER_WIDTH,
            self.MAX_WIDTH + self.BORDER_WIDTH * 2,
            total_height + self.BORDER_WIDTH * 2,
            color=(100, 100, 110)
        )
        border.draw()

        # Draw background
        bg = Rectangle(
            draw_x, draw_y - total_height,
            self.MAX_WIDTH, total_height,
            color=(20, 20, 25)
        )
        bg.draw()

        # Draw text lines
        current_y = draw_y - self.PADDING - self.LINE_HEIGHT
        for text, color, font_size, bold in lines:
            label = Label(
                text,
                x=draw_x + self.PADDING,
                y=current_y,
                font_size=font_size,
                color=color,
                width=self.MAX_WIDTH - self.PADDING * 2,
                multiline=True
            )
            label.draw()

            # Account for multiline text (scaled character width estimate)
            chars_per_line = int(40 / self.UI_SCALE * 1.0)
            num_lines = max(1, len(text) // chars_per_line + 1)
            current_y -= self.LINE_HEIGHT * num_lines

    def _build_content(self) -> list:
        """Build tooltip content lines. Returns list of (text, color, font_size, bold)."""
        lines = []
        upgrade = self.upgrade

        # Name (larger, bold effect via color)
        lines.append((upgrade.name, (255, 255, 255, 255), self.FONT_SIZE_TITLE, True))

        # Status
        if self.is_owned:
            lines.append(("✓ Owned", (100, 200, 100, 255), self.FONT_SIZE_NORMAL, False))
        elif not self.is_available:
            lines.append(("✗ Locked", (200, 100, 100, 255), self.FONT_SIZE_NORMAL, False))
        else:
            lines.append(("Available", (100, 200, 255, 255), self.FONT_SIZE_NORMAL, False))

        # Spacer
        # lines.append(("", (255, 255, 255, 255), self.FONT_SIZE_NORMAL, False))

        # Year and Tier
        lines.append((f"Year: {upgrade.year} | Tier: {upgrade.tier}", (180, 180, 180, 255), self.FONT_SIZE_SMALL, False))

        # Description
        # lines.append(("", (255, 255, 255, 255), self.FONT_SIZE_NORMAL, False))
        lines.append((upgrade.description, (200, 200, 200, 255), self.FONT_SIZE_SMALL, False))

        # Costs
        if upgrade.cost:
            # lines.append(("", (255, 255, 255, 255), self.FONT_SIZE_NORMAL, False))
            lines.append(("Costs:", (255, 220, 100, 255), self.FONT_SIZE_NORMAL, True))
            for cost in upgrade.cost:
                lines.append((f"  • {cost.amount:.0f} {cost.resource}", (255, 220, 100, 255), self.FONT_SIZE_SMALL, False))

        # Effects
        if upgrade.effects:
            # lines.append(("", (255, 255, 255, 255), self.FONT_SIZE_NORMAL, False))
            lines.append(("Effects:", (100, 200, 255, 255), self.FONT_SIZE_NORMAL, True))
            for effect in upgrade.effects:
                effect_text, effect_color = self._format_effect(effect)
                lines.append((effect_text, effect_color, self.FONT_SIZE_SMALL, False))

        # Requirements
        # if upgrade.requires:
        #     lines.append(("", (255, 255, 255, 255), self.FONT_SIZE_NORMAL, False))
        #     lines.append(("Requires:", (200, 150, 255, 255), self.FONT_SIZE_NORMAL, True))
        #     for req in upgrade.requires:
        #         if isinstance(req, list):
        #             req_text = f"  • Any of: {', '.join(req)}"
        #         else:
        #             req_text = f"  • {req}"
        #         lines.append((req_text, (200, 150, 255, 255), self.FONT_SIZE_SMALL, False))

        # Exclusive group
        if upgrade.exclusive_group:
            lines.append(("", (255, 255, 255, 255), self.FONT_SIZE_NORMAL, False))
            lines.append((f"⚠ Exclusive: {upgrade.exclusive_group}", (255, 180, 50, 255), self.FONT_SIZE_SMALL, False))
            lines.append(("(Only one from this group)", (255, 180, 50, 255), self.FONT_SIZE_TINY, False))

        return lines

    def _format_effect(self, effect) -> tuple:
        """Format an effect for display. Returns (text, color)."""
        resource = effect.resource
        value = effect.value

        if effect.effect == "add":
            # Additive effect
            if value >= 0:
                text = f"  • +{value:.1f} {resource}/s"
                color = (100, 255, 100, 255)  # Green for positive
            else:
                text = f"  • {value:.1f} {resource}/s"
                color = (255, 150, 100, 255)  # Orange for negative

        elif effect.effect == "mult":
            # Multiplicative effect
            if value > 1.0:
                # Multiplier (increase)
                percentage = (value - 1.0) * 100
                text = f"  • +{percentage:.0f}% {resource}"
                color = (100, 255, 100, 255)  # Green
            elif value < 1.0:
                # Divider (decrease)
                percentage = (1.0 - value) * 100
                text = f"  • -{percentage:.0f}% {resource}"
                color = (255, 150, 100, 255)  # Orange
            else:
                # No change (value == 1.0)
                text = f"  • No change to {resource}"
                color = (200, 200, 200, 255)  # Gray

        else:
            # Unknown effect type
            text = f"  • {effect.effect} {value} {resource}"
            color = (200, 200, 200, 255)

        return text, color
