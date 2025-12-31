# ui/editor_canvas.py

import pyglet
from pyglet.text import Label
from pyglet.shapes import Rectangle, Circle, Line
from typing import Dict, Optional, Callable
import math


class Camera:
    """Simple 2D camera for panning and zooming."""

    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.zoom = 1.5

    def screen_to_world(self, screen_x: float, screen_y: float, canvas_width: int, canvas_height: int) -> tuple:
        """Convert screen coordinates to world coordinates."""
        world_x = (screen_x - canvas_width / 2) / self.zoom + self.x
        world_y = (screen_y - canvas_height / 2) / self.zoom + self.y
        return world_x, world_y

    def world_to_screen(self, world_x: float, world_y: float, canvas_width: int, canvas_height: int) -> tuple:
        """Convert world coordinates to screen coordinates."""
        screen_x = (world_x - self.x) * self.zoom + canvas_width / 2
        screen_y = (world_y - self.y) * self.zoom + canvas_height / 2
        return screen_x, screen_y


class EditorCanvas:
    """Canvas for editing the tech tree visually."""

    NODE_RADIUS = 30

    def __init__(self, x: int, y: int, width: int, height: int, nodes: Dict):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.nodes = nodes

        self.camera = Camera()
        self.batch = pyglet.graphics.Batch()

        # Interaction state
        self.dragging_node_id: Optional[str] = None
        self.panning = False
        self.last_mouse_x = 0
        self.last_mouse_y = 0
        self.connecting_from: Optional[str] = None
        self._selected_node_id: Optional[str] = None

        # Callbacks
        self.on_node_selected: Optional[Callable[[Optional[str]], None]] = None
        self.on_node_moved: Optional[Callable[[str, float, float], None]] = None

    def draw(self):
        """Draw the canvas."""
        # Enable scissor test for clipping
        pyglet.gl.glEnable(pyglet.gl.GL_SCISSOR_TEST)
        pyglet.gl.glScissor(int(self.x), int(self.y), int(self.width), int(self.height))

        # Draw background
        bg = Rectangle(
            self.x, self.y, self.width, self.height,
            color=(25, 25, 30)
        )
        bg.draw()

        # Draw grid
        self._draw_grid()

        # Draw connections
        self._draw_connections()

        # Draw nodes
        self._draw_nodes()

        # Draw connection preview
        if self.connecting_from and self.connecting_from in self.nodes:
            self._draw_connection_preview()

        pyglet.gl.glDisable(pyglet.gl.GL_SCISSOR_TEST)

    def _draw_grid(self):
        """Draw background grid."""
        grid_spacing = 100 * self.camera.zoom

        if grid_spacing < 20:
            return  # Don't draw grid if too zoomed out

        # Calculate visible grid range
        start_x = int((self.camera.x - self.width / (2 * self.camera.zoom)) / 100) * 100
        end_x = int((self.camera.x + self.width / (2 * self.camera.zoom)) / 100) * 100 + 100
        start_y = int((self.camera.y - self.height / (2 * self.camera.zoom)) / 100) * 100
        end_y = int((self.camera.y + self.height / (2 * self.camera.zoom)) / 100) * 100 + 100

        # Draw vertical lines
        for world_x in range(start_x, end_x + 1, 100):
            screen_x, _ = self.camera.world_to_screen(world_x, 0, self.width, self.height)
            screen_x += self.x

            if self.x <= screen_x <= self.x + self.width:
                line = Line(
                    screen_x, self.y,
                    screen_x, self.y + self.height,
                    color=(40, 40, 45)
                )
                line.draw()

        # Draw horizontal lines
        for world_y in range(start_y, end_y + 1, 100):
            _, screen_y = self.camera.world_to_screen(0, world_y, self.width, self.height)
            screen_y += self.y
            if self.y <= screen_y <= self.y + self.height:
                line = Line(
                    self.x, screen_y,
                    self.x + self.width, screen_y,
                    color=(40, 40, 45)
                )
                line.draw()

    def _draw_connections(self):
        """Draw connections between nodes."""
        for node_id, node in self.nodes.items():
            for req in node.upgrade.requires:
                if isinstance(req, list):
                    # OR requirement - draw to all
                    for sub_req in req:
                        if sub_req in self.nodes:
                            self._draw_connection(node, self.nodes[sub_req], is_or=True)
                else:
                    # Direct requirement
                    if req in self.nodes:
                        self._draw_connection(node, self.nodes[req], is_or=False)

    def _draw_connection(self, from_node, to_node, is_or: bool = False):
        """Draw a connection line between two nodes."""
        # Convert to screen coordinates
        from_screen = self.camera.world_to_screen(from_node.x, from_node.y, self.width, self.height)
        to_screen = self.camera.world_to_screen(to_node.x, to_node.y, self.width, self.height)

        # Offset by canvas position
        from_x = from_screen[0] + self.x
        from_y = from_screen[1] + self.y
        to_x = to_screen[0] + self.x
        to_y = to_screen[1] + self.y

        # Draw line
        color = (200, 180, 50) if is_or else (100, 150, 200)
        line = Line(from_x, from_y, to_x, to_y, color=color)
        line.draw()

        # Draw arrow head
        self._draw_arrow_head(from_x, from_y, to_x, to_y, color)

    def _draw_arrow_head(self, from_x: float, from_y: float, to_x: float, to_y: float, color: tuple):
        """Draw an arrow head at the end of a line."""
        # Calculate angle
        dx = to_x - from_x
        dy = to_y - from_y
        angle = math.atan2(dy, dx)

        # Arrow head size
        arrow_size = 10
        arrow_angle = math.pi / 6  # 30 degrees

        # Calculate arrow head points
        point1_x = to_x - arrow_size * math.cos(angle - arrow_angle)
        point1_y = to_y - arrow_size * math.sin(angle - arrow_angle)
        point2_x = to_x - arrow_size * math.cos(angle + arrow_angle)
        point2_y = to_y - arrow_size * math.sin(angle + arrow_angle)

        # Draw arrow head lines
        line1 = Line(to_x, to_y, point1_x, point1_y, color=color)
        line1.draw()
        line2 = Line(to_x, to_y, point2_x, point2_y, color=color)
        line2.draw()

    def _draw_connection_preview(self):
        """Draw a preview line when connecting nodes."""
        if not self.connecting_from or self.connecting_from not in self.nodes:
            return

        from_node = self.nodes[self.connecting_from]
        from_screen = self.camera.world_to_screen(from_node.x, from_node.y, self.width, self.height)
        from_x = from_screen[0] + self.x
        from_y = from_screen[1] + self.y

        # Draw to mouse position
        line = Line(
            from_x, from_y,
            self.last_mouse_x, self.last_mouse_y,
            color=(255, 255, 100)
        )
        line.draw()

    def _draw_nodes(self):
        """Draw all nodes."""
        for node_id, node in self.nodes.items():
            self._draw_node(node_id, node)

    def _draw_node(self, node_id: str, node):
        """Draw a single node."""
        # Convert to screen coordinates
        screen_pos = self.camera.world_to_screen(node.x, node.y, self.width, self.height)
        screen_x = screen_pos[0] + self.x
        screen_y = screen_pos[1] + self.y

        # Draw node circle
        radius = self.NODE_RADIUS * self.camera.zoom

        # Outer glow for selected
        if node_id == self._selected_node_id:
            glow = Circle(
                screen_x, screen_y,
                radius + 5,
                color=(100, 150, 200)
            )
            glow.draw()

        # Node background
        circle = Circle(
            screen_x, screen_y,
            radius,
            color=(60, 80, 100)
        )
        circle.draw()

        # Node label (only if zoomed in enough)
        if self.camera.zoom >= 0.5:
            font_size = max(8, int(10 * self.camera.zoom))
            label = Label(
                node.upgrade.name[:15] + "..." if len(node.upgrade.name) > 15 else node.upgrade.name,
                x=screen_x,
                y=screen_y - radius - 10,
                anchor_x='center',
                anchor_y='top',
                font_size=font_size,
                color=(255, 255, 255, 255)
            )
            label.draw()

            # Tier indicator
            tier_label = Label(
                f"T{node.upgrade.tier}",
                x=screen_x,
                y=screen_y,
                anchor_x='center',
                anchor_y='center',
                font_size=font_size,
                color=(255, 255, 255, 255)
            )
            tier_label.draw()

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        """Handle mouse press."""
        if not (self.x <= x <= self.x + self.width and self.y <= y <= self.y + self.height):
            return

        from pyglet.window import mouse as mouse_buttons

        # Convert to world coordinates
        local_x = x - self.x
        local_y = y - self.y
        world_x, world_y = self.camera.screen_to_world(local_x, local_y, self.width, self.height)

        if button == mouse_buttons.LEFT:
            # Check if clicking on a node
            clicked_node = None
            for node_id, node in self.nodes.items():
                if node.contains_point(world_x, world_y):
                    clicked_node = node_id
                    break

            if clicked_node:
                # Check if in connection mode
                if self.connecting_from:
                    # Create connection
                    if clicked_node != self.connecting_from:
                        from_node = self.nodes[self.connecting_from]
                        if clicked_node not in from_node.upgrade.requires:
                            from_node.upgrade.requires.append(clicked_node)
                            print(f"🔗 Connected {self.connecting_from} -> {clicked_node}")
                    self.connecting_from = None
                else:
                    # Start dragging
                    self.dragging_node_id = clicked_node
                    if self.on_node_selected:
                        self.on_node_selected(clicked_node)
            else:
                # Clicked empty space
                if self.on_node_selected:
                    self.on_node_selected(None)

        elif button == mouse_buttons.RIGHT:
            # Start panning
            self.panning = True
            self.last_mouse_x = x
            self.last_mouse_y = y

    def on_mouse_drag(self, x: int, y: int, dx: int, dy: int, buttons: int, modifiers: int):
        """Handle mouse drag."""
        from pyglet.window import mouse as mouse_buttons

        if self.dragging_node_id and buttons & mouse_buttons.LEFT:
            # Drag node
            local_x = x - self.x
            local_y = y - self.y
            world_x, world_y = self.camera.screen_to_world(local_x, local_y, self.width, self.height)

            if self.dragging_node_id in self.nodes:
                node = self.nodes[self.dragging_node_id]
                node.x = world_x
                node.y = world_y

                if self.on_node_moved:
                    self.on_node_moved(self.dragging_node_id, world_x, world_y)

        elif self.panning and buttons & mouse_buttons.RIGHT:
            # Pan camera
            self.camera.x -= dx / self.camera.zoom
            self.camera.y -= dy / self.camera.zoom

        # Update mouse position for connection preview
        self.last_mouse_x = x
        self.last_mouse_y = y

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int):
        """Handle mouse release."""
        from pyglet.window import mouse as mouse_buttons

        if button == mouse_buttons.LEFT:
            self.dragging_node_id = None
        elif button == mouse_buttons.RIGHT:
            self.panning = False

    def on_mouse_scroll(self, x: int, y: int, scroll_x: float, scroll_y: float):
        """Handle mouse scroll for zooming."""
        if not (self.x <= x <= self.x + self.width and self.y <= y <= self.y + self.height):
            return

        # Zoom centered on mouse position
        local_x = x - self.x
        local_y = y - self.y

        # Get world position under mouse before zoom
        world_x, world_y = self.camera.screen_to_world(local_x, local_y, self.width, self.height)

        # Apply zoom
        old_zoom = self.camera.zoom
        zoom_factor = 1.1 if scroll_y > 0 else 0.9
        self.camera.zoom *= zoom_factor
        self.camera.zoom = max(0.1, min(3.0, self.camera.zoom))

        # Adjust camera position to keep point under mouse stationary
        if self.camera.zoom != old_zoom:
            new_world_x, new_world_y = self.camera.screen_to_world(local_x, local_y, self.width, self.height)
            self.camera.x += world_x - new_world_x
            self.camera.y += world_y - new_world_y

    def set_selected_node(self, node_id):
      """Set the currently selected node and update visual state."""
      self.selected_node_id = node_id

      # Clear previous selection highlight if needed
      if hasattr(self, 'selection_highlight'):
        self.selection_highlight.delete()

      # Add visual feedback for the selected node
      if node_id is not None:
        # Add your highlighting logic here
        pass

    def set_connecting_from(self, node):
        self.connecting_from = node