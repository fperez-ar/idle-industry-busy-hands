# ui/tree_view.py (continued and complete)
from typing import Dict, List, Optional, Tuple, Set

import pyglet
from pyglet.text import Label
from pyglet.shapes import Rectangle, Line
from pyglet.graphics import Batch

from loader import Upgrade, UpgradeTree
from ui.tooltip import Tooltip

TREE_BG_COLOR = (25, 25, 30)
EXCLUSIVE_GROUP_COLOR = (200, 150, 50)

TREE_HORIZONTAL_SPACING = 80
TREE_VERTICAL_SPACING = 40

class Camera:
    """Handles zoom and pan transformations for the tree view."""

    def __init__(self, viewport_width: int, viewport_height: int):
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height

        # Camera position (center of view in world coordinates)
        self.x: float = 0.0
        self.y: float = 0.0

        # Zoom level (1.0 = 100%)
        self.zoom: float = 1.5
        self.min_zoom: float = 0.1
        self.max_zoom: float = 5.0

        # Pan state
        self.is_panning: bool = False
        self.pan_start_x: float = 0.0
        self.pan_start_y: float = 0.0
        self.camera_start_x: float = 0.0
        self.camera_start_y: float = 0.0

    def screen_to_world(self, screen_x: float, screen_y: float) -> Tuple[float, float]:
        """Convert screen coordinates to world coordinates."""
        offset_x = (screen_x - self.viewport_width / 2) / self.zoom
        offset_y = (screen_y - self.viewport_height / 2) / self.zoom

        world_x = self.x + offset_x
        world_y = self.y + offset_y

        return world_x, world_y

    def world_to_screen(self, world_x: float, world_y: float) -> Tuple[float, float]:
        """Convert world coordinates to screen coordinates."""
        screen_x = (world_x - self.x) * self.zoom + self.viewport_width / 2
        screen_y = (world_y - self.y) * self.zoom + self.viewport_height / 2

        return screen_x, screen_y

    def apply_zoom(self, delta: float, focus_x: float, focus_y: float):
        """Zoom in/out centered on a point."""
        world_x, world_y = self.screen_to_world(focus_x, focus_y)

        old_zoom = self.zoom
        self.zoom *= (1.0 + delta * 0.1)
        self.zoom = max(self.min_zoom, min(self.max_zoom, self.zoom))

        if self.zoom != old_zoom:
            new_world_x, new_world_y = self.screen_to_world(focus_x, focus_y)
            self.x += world_x - new_world_x
            self.y += world_y - new_world_y

    def start_pan(self, screen_x: float, screen_y: float):
        """Begin panning operation."""
        self.is_panning = True
        self.pan_start_x = screen_x
        self.pan_start_y = screen_y
        self.camera_start_x = self.x
        self.camera_start_y = self.y

    def update_pan(self, screen_x: float, screen_y: float):
        """Update camera position during pan."""
        if not self.is_panning:
            return

        dx = (self.pan_start_x - screen_x) / self.zoom
        dy = (self.pan_start_y - screen_y) / self.zoom

        self.x = self.camera_start_x + dx
        self.y = self.camera_start_y + dy

    def end_pan(self):
        """End panning operation."""
        self.is_panning = False

    def resize(self, width: int, height: int):
        """Handle viewport resize."""
        self.viewport_width = width
        self.viewport_height = height


class TreeNode:
    """Visual representation of an upgrade in the tree."""

    NODE_WIDTH = 220
    NODE_HEIGHT = 90

    def __init__(self, upgrade: Upgrade, world_x: float, world_y: float):
        self.upgrade = upgrade
        self.world_x = world_x
        self.world_y = world_y

        # Visual state
        self.is_owned = False
        self.is_available = False
        self.is_affordable = False
        self.is_hovered = False

        # Colors
        self.color_owned = (30, 100, 180)
        self.color_available_affordable = (40, 160, 60)
        self.color_available_unaffordable = (180, 60, 40)
        self.color_unavailable = (70, 70, 70)
        self.color_exclusive_blocked = (100, 50, 100)

    def get_color(self) -> Tuple[int, int, int]:
        """Get current background color based on state."""
        if self.is_owned:
            return self.color_owned
        elif not self.is_available:
            return self.color_unavailable
        elif self.is_affordable:
            return self.color_available_affordable
        else:
            return self.color_available_unaffordable

    def get_center(self) -> Tuple[float, float]:
        """Get center point of the node in world coordinates."""
        return (
            self.world_x + self.NODE_WIDTH / 2,
            self.world_y + self.NODE_HEIGHT / 2
        )

    @DeprecationWarning
    def get_top_center(self) -> Tuple[float, float]:
        """Get top center point for incoming connections."""
        return (
            self.world_x + self.NODE_WIDTH / 2,
            self.world_y + self.NODE_HEIGHT
        )

    @DeprecationWarning
    def get_bottom_center(self) -> Tuple[float, float]:
        """Get bottom center point for outgoing connections."""
        return (
            self.world_x + self.NODE_WIDTH / 2,
            self.world_y
        )

    def get_left_center(self) -> Tuple[float, float]:
        """Get left center point for incoming connections."""
        return (
            self.world_x,
            self.world_y + self.NODE_HEIGHT / 2
        )

    def get_right_center(self) -> Tuple[float, float]:
        """Get right center point for outgoing connections."""
        return (
            self.world_x + self.NODE_WIDTH,
            self.world_y + self.NODE_HEIGHT / 2
        )

    def contains_point(self, world_x: float, world_y: float) -> bool:
        """Check if a world coordinate is within this node."""
        return (
            self.world_x <= world_x <= self.world_x + self.NODE_WIDTH and
            self.world_y <= world_y <= self.world_y + self.NODE_HEIGHT
        )

    def update_state(self, is_owned: bool, is_available: bool, is_affordable: bool):
        """Update visual state."""
        self.is_owned = is_owned
        self.is_available = is_available
        self.is_affordable = is_affordable


class ConnectionLine:
    """A line connecting two nodes in the tree."""

    def __init__(
        self,
        from_node: TreeNode,
        to_node: TreeNode,
        is_or_connection: bool = False
    ):
        self.from_node = from_node
        self.to_node = to_node
        self.is_or_connection = is_or_connection

    def get_points(self) -> List[Tuple[float, float]]:
        """Get points for the connection line (may include intermediate points for curves)."""
        start_x, start_y = self.from_node.get_right_center()
        end_x, end_y = self.to_node.get_left_center()

        # Calculate control points for a smooth curve
        mid_x = (start_x + end_x) / 2

        return [
            (start_x, start_y),
            (mid_x, start_y),
            (mid_x, end_y),
            (end_x, end_y)
        ]

    def get_color(self) -> Tuple[int, int, int]:
        """Get line color based on connection type and node states."""
        if self.from_node.is_owned:
            return (100, 200, 100)  # Green for satisfied
        elif self.is_or_connection:
            return (200, 180, 50)   # Yellow for OR connections
        else:
            return (120, 120, 120)  # Gray for unsatisfied

class InteractiveTreeView:
    """A zoomable, pannable view of an upgrade tree."""

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        tree: UpgradeTree,
        game_state=None
    ):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.tree = tree

        # Camera for pan/zoom
        self.camera = Camera(width, height)

        # Tree structure
        self.nodes: Dict[str, TreeNode] = {}
        self.connections: List[ConnectionLine] = []

        # Build the tree layout
        self._layout_tree()
        self._create_connections()

        # Center camera on tree
        self._center_camera_on_tier(0) # self._center_camera()

        # Tooltip
        self.tooltip = Tooltip()
        self.hovered_node_id: Optional[str] = None
        self.game_state = game_state

    def _get_root_nodes(self) -> List[Upgrade]:
      """Find all root nodes (nodes with no requirements)."""
      roots = []
      for upgrade in self.tree.upgrades.values():
          if not upgrade.requires:
              roots.append(upgrade)
      return sorted(roots, key=lambda u: (u.tier, u.exclusive_group or '', u.id))

    def _get_children(self, parent_id: str) -> List[Upgrade]:
        """Get all upgrades that directly require this upgrade."""
        children = []
        for upgrade in self.tree.upgrades.values():
            # Check if parent_id is in requirements
            for req in upgrade.requires:
                if isinstance(req, list):
                    # OR requirement
                    if parent_id in req:
                        children.append(upgrade)
                        break
                else:
                    # Direct requirement
                    if req == parent_id:
                        children.append(upgrade)
                        break
        return sorted(children, key=lambda u: (u.tier, u.exclusive_group or '', u.id))

    def _calculate_subtree_height(self, upgrade_id: str, memo: Dict[str, int]) -> int:
        """Calculate the number of leaf nodes in a subtree (for spacing)."""
        if upgrade_id in memo:
            return memo[upgrade_id]

        children = self._get_children(upgrade_id)
        if not children:
            memo[upgrade_id] = 1
            return 1

        total_height = sum(self._calculate_subtree_height(child.id, memo) for child in children)
        memo[upgrade_id] = total_height
        return total_height

    def _layout_tree(self):
        """Calculate positions for all nodes using a tree layout algorithm."""
        if not self.tree.upgrades:
            return

        # Layout parameters
        node_width = TreeNode.NODE_WIDTH
        node_height = TreeNode.NODE_HEIGHT
        h_spacing = 80
        v_spacing = 20

        # Find root nodes
        roots = self._get_root_nodes()
        if not roots:
            self._layout_tree_by_tier()
            return

        # Calculate subtree heights for all nodes
        subtree_heights: Dict[str, int] = {}
        for upgrade in self.tree.upgrades.values():
            self._calculate_subtree_height(upgrade.id, subtree_heights)

        # Track which nodes have been positioned
        positioned: Set[str] = set()

        # Position nodes level by level
        def position_node(upgrade: Upgrade, x: float, y_start: float, y_end: float) -> float:
            """Position a node and its children. Returns the actual space used."""
            if upgrade.id in positioned:
                return y_start  # No space used if already positioned

            # Calculate this node's y position (centered in its allocated space)
            node_y = (y_start + y_end) / 2 - node_height / 2

            # Create the node
            self.nodes[upgrade.id] = TreeNode(upgrade, x, node_y)
            positioned.add(upgrade.id)

            # Get children that haven't been positioned yet
            children = [c for c in self._get_children(upgrade.id) if c.id not in positioned]

            if not children:
                return y_start + node_height + v_spacing

            # Calculate space for children
            child_x = x + node_width + h_spacing
            current_y = y_start

            for child in children:
                child_height = subtree_heights.get(child.id, 1)
                child_space = child_height * (node_height + v_spacing)
                actual_space_used = position_node(child, child_x, current_y, current_y + child_space)
                current_y = actual_space_used

            return current_y

        # Position all root nodes and their subtrees
        start_x = 0
        current_y = 0

        for root in roots:
            if root.id not in positioned:
                root_height = subtree_heights.get(root.id, 1)
                root_space = root_height * (node_height + v_spacing)
                actual_space = position_node(root, start_x, current_y, current_y + root_space)
                current_y = actual_space + v_spacing  # Use actual space instead of allocated space

        # Handle any orphaned nodes (nodes with requirements but not connected)
        orphans = [u for u in self.tree.upgrades.values() if u.id not in positioned]
        if orphans:
            # Position orphans to the right
            orphan_x = start_x + (node_width + h_spacing) * 3
            orphan_y = 0
            for orphan in orphans:
                self.nodes[orphan.id] = TreeNode(orphan, orphan_x, orphan_y)
                positioned.add(orphan.id)
                orphan_y += node_height + v_spacing

    def _layout_tree_by_tier(self):
        """Fallback layout method using tiers."""
        tiers: Dict[int, List[Upgrade]] = {}
        for upgrade in self.tree.upgrades.values():
            tier = upgrade.tier
            if tier not in tiers:
                tiers[tier] = []
            tiers[tier].append(upgrade)

        node_width = TreeNode.NODE_WIDTH
        node_height = TreeNode.NODE_HEIGHT
        h_spacing = TREE_HORIZONTAL_SPACING
        v_spacing = TREE_VERTICAL_SPACING

        for tier, upgrades in sorted(tiers.items()):
            upgrades.sort(key=lambda u: (u.exclusive_group or '', u.id))
            column_height = len(upgrades) * node_height + (len(upgrades) - 1) * v_spacing
            start_y = -column_height / 2
            tier_x = tier * (node_width + h_spacing)

            for i, upgrade in enumerate(upgrades):
                node_y = start_y + i * (node_height + v_spacing)
                node = TreeNode(upgrade, tier_x, node_y)
                self.nodes[upgrade.id] = node

    def _create_connections(self):
        """Create connection lines between nodes based on requirements."""
        for upgrade_id, node in self.nodes.items():
            upgrade = node.upgrade

            for req in upgrade.requires:
                if isinstance(req, list):
                    # OR requirement - connect to all possibilities
                    for sub_req in req:
                        if sub_req in self.nodes:
                            conn = ConnectionLine(
                                node,
                                self.nodes[sub_req],
                                is_or_connection=True
                            )
                            self.connections.append(conn)
                else:
                    # Direct requirement
                    if req in self.nodes:
                        conn = ConnectionLine(node, self.nodes[req])
                        self.connections.append(conn)

    def _center_camera(self):
        """Center the camera on the tree content."""
        if not self.nodes:
            return

        # Calculate bounding box
        min_x = min(n.world_x for n in self.nodes.values())
        max_x = max(n.world_x + TreeNode.NODE_WIDTH for n in self.nodes.values())
        min_y = min(n.world_y for n in self.nodes.values())
        max_y = max(n.world_y + TreeNode.NODE_HEIGHT for n in self.nodes.values())

        # Center camera
        self.camera.x = (min_x + max_x) / 2
        self.camera.y = (min_y + max_y) / 2

    def _center_camera_on_tier(self, tier: int = 0):
        """Center the camera on a specific tier."""
        if not self.nodes:
            return

        # Find all nodes in the specified tier
        tier_nodes = [node for node in self.nodes.values() if node.upgrade.tier == tier]

        if not tier_nodes:
            # If no nodes in that tier, fall back to centering on all nodes
            self._center_camera()
            return

        # Calculate bounding box for this tier
        min_x = min(n.world_x for n in tier_nodes)
        max_x = max(n.world_x + TreeNode.NODE_WIDTH for n in tier_nodes)
        min_y = min(n.world_y for n in tier_nodes)
        max_y = max(n.world_y + TreeNode.NODE_HEIGHT for n in tier_nodes)

        # Center camera on this tier
        self.camera.x = (min_x + max_x) / 2
        self.camera.y = (min_y + max_y) / 2

    def _get_view_offset(self) -> Tuple[float, float]:
        """Get the offset to apply for view-local coordinates."""
        return (
            self.x + self.width / 2 - self.camera.viewport_width / 2,
            self.y + self.height / 2 - self.camera.viewport_height / 2
        )

    def _is_point_inside(self, x: int, y: int) -> bool:
        """Check if a point is inside the view bounds."""
        return (
            self.x <= x <= self.x + self.width and
            self.y <= y <= self.y + self.height
        )

    def _draw_connection(self, conn: ConnectionLine, offset_x: float, offset_y: float):
        """Draw a single connection line."""
        points = conn.get_points()
        color = conn.get_color()

        # Draw line segments
        for i in range(len(points) - 1):
            start_x, start_y = points[i]
            end_x, end_y = points[i + 1]

            # Unpack the tuples when calling world_to_screen
            screen_start_x, screen_start_y = self.camera.world_to_screen(start_x, start_y)
            screen_end_x, screen_end_y = self.camera.world_to_screen(end_x, end_y)

            draw_start_x = offset_x + screen_start_x
            draw_start_y = offset_y + screen_start_y
            draw_end_x = offset_x + screen_end_x
            draw_end_y = offset_y + screen_end_y

            line = Line(draw_start_x, draw_start_y, draw_end_x, draw_end_y, color=color)
            line.draw()

            if conn.is_or_connection:
                for offset_val in [-1, 1]:
                    line2 = Line(
                        draw_start_x + offset_val, draw_start_y,
                        draw_end_x + offset_val, draw_end_y,
                        color=color
                    )
                    line2.draw()

        # Draw OR indicator at midpoint
        if conn.is_or_connection:
            mid_idx = len(points) // 2
            mid_x, mid_y = points[mid_idx]
            screen_mid_x, screen_mid_y = self.camera.world_to_screen(mid_x, mid_y)

            label_x = offset_x + screen_mid_x
            label_y = offset_y + screen_mid_y

            or_label = Label(
                "OR",
                x=label_x,
                y=label_y,
                anchor_x='center',
                anchor_y='center',
                font_size=8,
                color=(200, 180, 50, 255)
            )
            or_label.draw()

    def _draw_node(self, node: TreeNode, offset_x: float, offset_y: float):
        """Draw a single node."""
        # Transform world coordinates to screen coordinates
        screen_x, screen_y = self.camera.world_to_screen(node.world_x, node.world_y)

        # Apply offset
        draw_x = offset_x + screen_x
        draw_y = offset_y + screen_y

        # Scale dimensions by zoom
        scaled_width = TreeNode.NODE_WIDTH * self.camera.zoom
        scaled_height = TreeNode.NODE_HEIGHT * self.camera.zoom

        # Get node color based on state
        color = node.get_color()

        # Draw border for exclusive groups
        if node.upgrade.exclusive_group:
            border_rect = Rectangle(
                draw_x - 3, draw_y - 3,
                scaled_width + 6, scaled_height + 6,
                color=EXCLUSIVE_GROUP_COLOR
            )
            border_rect.draw()

        # Draw background
        bg = Rectangle(draw_x, draw_y, scaled_width, scaled_height, color=color)
        bg.draw()

        # Draw text (only if zoom is sufficient to read)
        if self.camera.zoom >= 0.5:
            font_size = max(8, int(11 * self.camera.zoom))
            small_font_size = max(7, int(9 * self.camera.zoom))
            padding = 8 * self.camera.zoom

            # Name
            name_label = Label(
                node.upgrade.name,
                x=draw_x + padding,
                y=draw_y + scaled_height - 20 * self.camera.zoom,
                font_size=font_size,
                color=(255, 255, 255, 255)
            )
            name_label.draw()

            # Year
            year_label = Label(
                f"Year: {node.upgrade.year}",
                x=draw_x + padding,
                y=draw_y + padding,
                font_size=small_font_size,
                color=(180, 180, 180, 255)
            )
            year_label.draw()

            # Cost summary
            cost_parts = []
            for cost in node.upgrade.cost:
                cost_parts.append(f"{int(cost.amount)} {cost.resource}")
            cost_text = ", ".join(cost_parts)

            cost_label = Label(
                cost_text,
                x=draw_x + padding,
                y=draw_y + scaled_height - 40 * self.camera.zoom,
                font_size=small_font_size,
                color=(255, 220, 100, 255)
            )
            cost_label.draw()

            # Effects summary (if space allows)
            if self.camera.zoom >= 0.75:
                effect_parts = []
                for effect in node.upgrade.effects[:2]:  # Show max 2 effects
                    if effect.effect == "add":
                        sign = "+" if effect.value >= 0 else ""
                        effect_parts.append(f"{sign}{effect.value:.1f} {effect.resource}")
                    else:
                        effect_parts.append(f"x{effect.value:.1f} {effect.resource}")

                if len(node.upgrade.effects) > 2:
                    effect_parts.append("...")

                effect_text = ", ".join(effect_parts)

                effect_label = Label(
                    effect_text,
                    x=draw_x + padding,
                    y=draw_y + scaled_height - 58 * self.camera.zoom,
                    font_size=max(6, int(8 * self.camera.zoom)),
                    color=(150, 200, 255, 255)
                )
                effect_label.draw()

            # Exclusive group indicator
            if node.upgrade.exclusive_group and self.camera.zoom >= 0.6:
                exclusive_label = Label(
                    f"[{node.upgrade.exclusive_group}]",
                    x=draw_x + scaled_width - padding,
                    y=draw_y + padding,
                    anchor_x='right',
                    font_size=max(6, int(7 * self.camera.zoom)),
                    color=(200, 150, 50, 255)
                )
                exclusive_label.draw()

    def _get_all_descendants(self, upgrade_id: str, exclusive_only: bool = False) -> Set[str]:
        """Get all descendants of an upgrade (recursively).
        If exclusive_only is True, only include descendants that ONLY require this upgrade."""
        descendants = set()

        def collect_descendants(current_id: str):
            children = self._get_children(current_id)
            for child in children:
                if child.id in descendants:
                    continue  # Already processed

                # If exclusive_only, check if this child has other requirements
                if exclusive_only:
                    other_reqs = []
                    for req in child.requires:
                        if isinstance(req, list):
                            # OR requirement - check if current_id is the only option
                            if current_id not in req:
                                other_reqs.extend(req)
                        else:
                            # Direct requirement
                            if req != current_id:
                                other_reqs.append(req)

                    # Skip this child if it has other requirements
                    if other_reqs:
                        continue

                descendants.add(child.id)
                collect_descendants(child.id)

        collect_descendants(upgrade_id)
        return descendants

    def _get_hidden_nodes(self) -> Set[str]:
        """Get set of node IDs that should be hidden based on exclusive group selections."""
        hidden = set()
        # if no game state return empty set
        if not hasattr(self, 'game_state'):
            return hidden

        # Find all exclusive groups
        exclusive_groups: Dict[str, List[str]] = {}
        for upgrade_id, node in self.nodes.items():
            if node.upgrade.exclusive_group:
                groups = node.upgrade.exclusive_group if isinstance(node.upgrade.exclusive_group, list) else [node.upgrade.exclusive_group]
                for group in groups:
                    if group not in exclusive_groups:
                        exclusive_groups[group] = []
                    exclusive_groups[group].append(upgrade_id)

        # For each exclusive group, hide unselected branches
        for group, upgrade_ids in exclusive_groups.items():
            selected_id = self.game_state.selected_exclusive.get(group)

            if selected_id:
                # Hide all other options in this group and their exclusive descendants
                for upgrade_id in upgrade_ids:
                    if upgrade_id != selected_id:
                        hidden.add(upgrade_id)
                        # Add all exclusive descendants
                        descendants = self._get_all_descendants(upgrade_id, exclusive_only=True)
                        hidden.update(descendants)

        return hidden

    def draw(self, batch: Batch):
        """Draw the tree view."""
        # Enable scissor test for clipping
        pyglet.gl.glEnable(pyglet.gl.GL_SCISSOR_TEST)
        pyglet.gl.glScissor(int(self.x), int(self.y), int(self.width), int(self.height))

        # Draw background
        bg = Rectangle(self.x, self.y, self.width, self.height, color=TREE_BG_COLOR)
        bg.draw()

        offset_x, offset_y = self._get_view_offset()

        # Determine which nodes to hide based on exclusive group selections
        hidden_nodes = self._get_hidden_nodes()

        # Draw connections first (behind nodes) - skip hidden ones
        for conn in self.connections:
            if conn.from_node.upgrade.id not in hidden_nodes and conn.to_node.upgrade.id not in hidden_nodes:
                self._draw_connection(conn, offset_x, offset_y)

        # Draw nodes - skip hidden ones
        for node in self.nodes.values():
            if node.upgrade.id not in hidden_nodes:
                self._draw_node(node, offset_x, offset_y)

        # Draw zoom indicator
        zoom_label = Label(
            f"Zoom: {self.camera.zoom:.0%}",
            x=self.x + 10,
            y=self.y + self.height - 25,
            font_size=10,
            color=(200, 200, 200, 255)
        )
        zoom_label.draw()

        # Draw pan instructions
        help_label = Label(
            "Right-drag: Pan | Scroll: Zoom",
            x=self.x + 10,
            y=self.y + 10,
            font_size=9,
            color=(150, 150, 150, 255)
        )
        help_label.draw()

        pyglet.gl.glDisable(pyglet.gl.GL_SCISSOR_TEST)

        # Draw tooltip (outside scissor test so it can extend beyond tree area)
        window_width = self.x + self.width
        window_height = self.y + self.height
        self.tooltip.draw(window_width * 2, window_height * 2)

    def on_mouse_scroll(self, x: int, y: int, scroll_x: float, scroll_y: float):
        """Handle mouse scroll for zooming."""
        if not self._is_point_inside(x, y):
            return

        # Zoom centered on mouse position
        local_x = x - self.x
        local_y = y - self.y
        self.camera.apply_zoom(scroll_y, local_x, local_y)

    def on_mouse_motion(self, x: int, y: int):
        """Handle mouse motion for tooltip hover detection."""
        if not self._is_point_inside(x, y):
            if self.hovered_node_id:
                self.tooltip.cancel_hover()
                self.hovered_node_id = None
            return

        # Convert to world coordinates
        local_x = x - self.x
        local_y = y - self.y
        world_x, world_y = self.camera.screen_to_world(
            local_x + self.camera.viewport_width / 2 - self.width / 2,
            local_y + self.camera.viewport_height / 2 - self.height / 2
        )

        # Check which node we're hovering over
        hovered_id = None
        for upgrade_id, node in self.nodes.items():
            if node.contains_point(world_x, world_y):
                hovered_id = upgrade_id
                break

        # Update tooltip state
        if hovered_id != self.hovered_node_id:
            if hovered_id:
                # Started hovering over a new node
                node = self.nodes[hovered_id]
                self.tooltip.start_hover(
                    node.upgrade,
                    x, y,
                    node.is_owned,
                    node.is_available
                )
            else:
                # Stopped hovering
                self.tooltip.cancel_hover()

            self.hovered_node_id = hovered_id
        elif hovered_id:
            # Continue hovering over same node, update position
            node = self.nodes[hovered_id]
            self.tooltip.start_hover(
                node.upgrade,
                x, y,
                node.is_owned,
                node.is_available
            )

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> Optional[str]:
        """Handle mouse press. Returns upgrade ID if a node was clicked."""

        self.tooltip.cancel_hover()
        self.hovered_node_id = None

        if not self._is_point_inside(x, y):
            return None

        # Middle mouse button or right button for panning
        if button == pyglet.window.mouse.MIDDLE or button == pyglet.window.mouse.RIGHT:
            local_x = x - self.x
            local_y = y - self.y
            self.camera.start_pan(local_x, local_y)
            return None

        # Left click - check for node clicks
        if button == pyglet.window.mouse.LEFT:
            local_x = x - self.x
            local_y = y - self.y

            # Convert screen position to world position
            world_x, world_y = self.camera.screen_to_world(
                local_x + self.camera.viewport_width / 2 - self.width / 2,
                local_y + self.camera.viewport_height / 2 - self.height / 2
            )

            # Check each node for click
            for upgrade_id, node in self.nodes.items():
                if node.contains_point(world_x, world_y):
                    return upgrade_id

        return None

    def on_mouse_drag(self, x: int, y: int, dx: int, dy: int, buttons: int, modifiers: int):
        """Handle mouse drag for panning."""
        if self.camera.is_panning:
            local_x = x - self.x
            local_y = y - self.y
            self.camera.update_pan(local_x, local_y)

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int):
        """Handle mouse release."""
        if button == pyglet.window.mouse.MIDDLE or button == pyglet.window.mouse.RIGHT:
            self.camera.end_pan()

    def resize(self, width: int, height: int):
        """Handle resize of the view."""
        self.width = width
        self.height = height
        self.camera.resize(width, height)

    def update(self, dt: float):
        """Update tree view (for tooltip timing)."""
        self.tooltip.update(dt)

    def update_nodes(
        self,
        owned_upgrades: set,
        available_upgrade_ids: set,
        resource_manager
    ):
        """Update visual state of all nodes."""
        for upgrade_id, node in self.nodes.items():
            is_owned = upgrade_id in owned_upgrades
            is_available = upgrade_id in available_upgrade_ids
            is_affordable = resource_manager.can_afford(node.upgrade.cost)
            node.update_state(is_owned, is_available, is_affordable)