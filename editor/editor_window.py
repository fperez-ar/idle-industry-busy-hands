# ui/editor_window.py
import pyglet
from pyglet.window import Window, key, mouse
from pyglet.text import Label
from pyglet.shapes import Rectangle, Line, Circle
from typing import Dict, List, Optional, Set
import yaml, time
import os

from loader import Upgrade, Effect, ResourceCost, UpgradeTree
from editor.editor_sidebar import EditorSidebar
from editor.editor_properties import PropertiesPanel
from editor.editor_canvas import EditorCanvas


class EditorWindow(Window):
    """Main editor window."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Editor state
        self.current_tree: Optional[UpgradeTree] = None
        self.current_tree_file: Optional[str] = None
        self.nodes: Dict[str, 'EditorNode'] = {}  # upgrade_id -> EditorNode
        self.selected_node_id: Optional[str] = None
        self.connecting_from: Optional[str] = None  # For creating dependencies

        # Layout
        self.sidebar_width = 250
        self.properties_width = 350

        # Create UI components
        self.sidebar = EditorSidebar(
            x=0,
            y=0,
            width=self.sidebar_width,
            height=self.height
        )

        self.properties_panel = PropertiesPanel(
            x=self.width - self.properties_width,
            y=0,
            width=self.properties_width,
            height=self.height
        )

        self.canvas = EditorCanvas(
            x=self.sidebar_width,
            y=0,
            width=self.width - self.sidebar_width - self.properties_width,
            height=self.height,
            nodes=self.nodes
        )

        # Batch for drawing
        self.batch = pyglet.graphics.Batch()

        # Set up callbacks
        self.sidebar.on_new_tree = self.new_tree
        self.sidebar.on_load_tree = self.load_tree
        self.sidebar.on_save_tree = self.save_tree
        self.sidebar.on_add_node = self.add_node
        self.sidebar.on_auto_layout = self.auto_layout_tree

        self.properties_panel.on_property_changed = self.on_property_changed
        self.properties_panel.on_delete_node = self.delete_selected_node

        self.canvas.on_node_selected = self.select_node
        self.canvas.on_node_moved = self.on_node_moved

        # Create a default tree
        self.new_tree()

    def new_tree(self):
        """Create a new empty tree."""
        self.current_tree = UpgradeTree(
            id="new_tree",
            name="New Tech Tree",
            description="A new technology tree",
            icon="🌲"
        )
        self.current_tree_file = None
        self.nodes.clear()
        self.selected_node_id = None
        self.connecting_from = None
        self.canvas.camera.x = 0
        self.canvas.camera.y = 0
        print("📄 New tree created")

    def load_tree(self, filepath: str):
        """Load a tree from file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            # Parse tree metadata
            tree_data = data.get('tree', {})
            self.current_tree = UpgradeTree(
                id=tree_data.get('id', 'loaded_tree'),
                name=tree_data.get('name', 'Loaded Tree'),
                description=tree_data.get('description', ''),
                icon=tree_data.get('icon', '🌲')
            )

            # Parse upgrades
            self.nodes.clear()
            for upgrade_data in data.get('upgrades', []):
                upgrade = self._parse_upgrade(upgrade_data)

                # Get position
                pos = upgrade_data.get('editor_position', {'x': 0, 'y': 0})

                node = EditorNode(
                    upgrade=upgrade,
                    x=pos['x'],
                    y=pos['y']
                )
                self.nodes[upgrade.id] = node

            self.current_tree_file = filepath
            self.selected_node_id = None
            self.connecting_from = None
            self.auto_layout_tree()
            print(f"✓ Loaded tree from: {filepath}")

        except Exception as e:
            print(f"✗ Error loading tree: {e}")

    def save_tree(self, filepath: Optional[str] = None):
        """Save the current tree to file."""
        if filepath is None:
            filepath = self.current_tree_file

        if filepath is None:
            # Generate default filename
            filepath = f"data/tech_tree_{self.current_tree.id}.yml"

        try:
            data = {
                'tree': {
                    'id': self.current_tree.id,
                    'name': self.current_tree.name,
                    'description': self.current_tree.description,
                    'icon': self.current_tree.icon
                },
                'upgrades': []
            }

            for node in self.nodes.values():
                upgrade_data = self._serialize_upgrade(node.upgrade)
                upgrade_data['editor_position'] = {
                    'x': node.x,
                    'y': node.y
                }
                data['upgrades'].append(upgrade_data)

            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            with open(filepath, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

            self.current_tree_file = filepath
            print(f"✓ Saved tree to: {filepath}")

        except Exception as e:
            print(f"✗ Error saving tree: {e}")

    def add_node(self):
        """Add a new node to the tree."""
        # Generate unique ID
        node_num = len(self.nodes) + 1
        while f"upgrade_{node_num}" in self.nodes:
            node_num += 1

        upgrade_id = f"upgrade_{node_num}"

        # Create new upgrade
        upgrade = Upgrade(
            id=upgrade_id,
            tree=self.current_tree.id,
            name=f"New Upgrade {node_num}",
            description="Description here",
            tier=0,
            year=1800,
            cost=[],
            effects=[],
            exclusive_group=None,
            requires=[]
        )

        # Create node at center of canvas
        node = EditorNode(
            upgrade=upgrade,
            x=self.canvas.camera.x,
            y=self.canvas.camera.y
        )

        self.nodes[upgrade_id] = node
        self.select_node(upgrade_id)
        self.auto_layout_tree()

        print(f"➕ Added node: {upgrade_id}")

    def select_node(self, node_id: Optional[str]):
        """Select a node."""
        self.selected_node_id = node_id

        if node_id and node_id in self.nodes:
            self.properties_panel.set_upgrade(self.nodes[node_id].upgrade)
        else:
            self.properties_panel.set_upgrade(None)

    def delete_selected_node(self):
        """Delete the currently selected node."""
        if not self.selected_node_id:
            return

        # Remove from nodes
        if self.selected_node_id in self.nodes:
            del self.nodes[self.selected_node_id]

        # Remove from other nodes' requirements
        for node in self.nodes.values():
            # Remove direct requirements
            node.upgrade.requires = [
                req for req in node.upgrade.requires
                if req != self.selected_node_id and
                (not isinstance(req, list) or self.selected_node_id not in req)
            ]

        print(f"🗑️ Deleted node: {self.selected_node_id}")
        self.selected_node_id = None
        self.properties_panel.set_upgrade(None)

    def on_property_changed(self, upgrade: Upgrade):
        """Handle property changes from the properties panel."""
        if self.selected_node_id and self.selected_node_id in self.nodes:
            self.nodes[self.selected_node_id].upgrade = upgrade

    def on_node_moved(self, node_id: str, x: float, y: float):
        """Handle node movement."""
        if node_id in self.nodes:
            self.nodes[node_id].x = x
            self.nodes[node_id].y = y

    def _parse_upgrade(self, data: dict) -> Upgrade:
        """Parse upgrade from dictionary."""
        costs = []
        for cost_data in data.get('cost', []):
            costs.append(ResourceCost(
                resource=cost_data['resource'],
                amount=cost_data['amount']
            ))

        effects = []
        for effect_data in data.get('effects', []):
            effects.append(Effect(
                resource=effect_data['resource'],
                effect=effect_data['effect'],
                value=effect_data['value']
            ))

        return Upgrade(
            id=data['id'],
            tree=data.get('tree', self.current_tree.id if self.current_tree else 'unknown'),
            name=data['name'],
            description=data['description'],
            tier=data.get('tier', 0),
            year=data.get('year', 1800),
            cost=costs,
            effects=effects,
            exclusive_group=data.get('exclusive_group'),
            requires=data.get('requires', [])
        )

    def _serialize_upgrade(self, upgrade: Upgrade) -> dict:
        """Serialize upgrade to dictionary."""
        return {
            'id': upgrade.id,
            'tree': upgrade.tree,
            'name': upgrade.name,
            'description': upgrade.description,
            'tier': upgrade.tier,
            'year': upgrade.year,
            'cost': [
                {'resource': c.resource, 'amount': c.amount}
                for c in upgrade.cost
            ],
            'effects': [
                {'resource': e.resource, 'effect': e.effect, 'value': e.value}
                for e in upgrade.effects
            ],
            'exclusive_group': upgrade.exclusive_group,
            'requires': upgrade.requires
        }

    def on_draw(self):
        """Draw the editor."""
        self.clear()

        # Update canvas state
        self.canvas.set_selected_node(self.selected_node_id)
        self.canvas.set_connecting_from(self.connecting_from)

        # Draw canvas (nodes and connections)
        self.canvas.draw()

        # Draw UI panels
        self.sidebar.draw()
        self.properties_panel.draw()

        # Draw mode indicator
        if self.connecting_from:
            mode_label = Label(
                f"🔗 Connecting from: {self.connecting_from} (click target node or ESC to cancel)",
                x=self.width // 2,
                y=self.height - 10,
                anchor_x='center',
                anchor_y='top',
                font_size=15,
                color=(255, 200, 100, 255)
            )
            mode_label.draw()

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        """Handle mouse press."""
        # Check sidebar
        if self.sidebar.on_mouse_press(x, y, button):
            return

        # Check properties panel
        if self.properties_panel.on_mouse_press(x, y, button):
            return

        # Check canvas
        self.canvas.on_mouse_press(x, y, button, modifiers)

    def on_mouse_drag(self, x: int, y: int, dx: int, dy: int, buttons: int, modifiers: int):
        """Handle mouse drag."""
        self.canvas.on_mouse_drag(x, y, dx, dy, buttons, modifiers)

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int):
        """Handle mouse release."""
        self.canvas.on_mouse_release(x, y, button, modifiers)

    def on_mouse_scroll(self, x: int, y: int, scroll_x: float, scroll_y: float):
      """Handle mouse scroll."""
      if self.sidebar.on_mouse_scroll(x, y, scroll_x, scroll_y):
          return
      self.canvas.on_mouse_scroll(x, y, scroll_x, scroll_y)

    def on_key_press(self, symbol: int, modifiers: int):
        """Handle key press."""

        # Check if properties panel is in editing mode
        if self.properties_panel.is_editing:
            # Only handle ESC to exit editing mode
            if symbol == key.ESCAPE:
                self.properties_panel.active_field = None
                self.properties_panel.is_editing = False
            return  # Don't process other keys while editing

        if symbol == key.ESCAPE:
            current_time = time.time()
            if hasattr(self, '_last_escape_time') and current_time - self._last_escape_time < 0.3:
                pyglet.app.exit()
            else:
                if self.connecting_from:
                    self.connecting_from = None
                    print("Connection cancelled")
                else:
                    self.select_node(None)
            self._last_escape_time = current_time

        elif symbol == key.DELETE or symbol == key.BACKSPACE:
            if self.selected_node_id:
                self.delete_selected_node()

        elif symbol == key.S and (modifiers & key.MOD_CTRL):
            self.save_tree()

        elif symbol == key.N and (modifiers & key.MOD_CTRL):
            self.new_tree()

        elif symbol == key.C:
            if self.selected_node_id:
                self.connecting_from = self.selected_node_id
                print(f"🔗 Connecting from: {self.connecting_from}")

        elif symbol == key.R:
            self.canvas.camera.x = 0
            self.canvas.camera.y = 0
            self.canvas.camera.zoom = 1.0
            print("📷 Camera reset")

        elif symbol == key.L:
            self.auto_layout_tree()

    def on_resize(self, width: int, height: int):
        """Handle window resize."""
        super().on_resize(width, height)

        # Update component sizes
        self.sidebar.height = height
        self.properties_panel.x = width - self.properties_width
        self.properties_panel.height = height
        self.canvas.width = width - self.sidebar_width - self.properties_width
        self.canvas.height = height

    def on_text(self, text: str):
        """Handle text input."""
        self.properties_panel.on_text(text)

    def on_text_motion(self, motion: int):
        """Handle text motion."""
        self.properties_panel.on_text_motion(motion)

    def auto_layout_tree(self):
        """Automatically layout nodes in a tree structure based on tiers and dependencies."""
        if not self.nodes:
            return

        # Group nodes by tier
        tiers = {}
        for node_id, node in self.nodes.items():
            tier = node.upgrade.tier
            if tier not in tiers:
                tiers[tier] = []
            tiers[tier].append(node)

        # Layout parameters (matching game view)
        node_width = 220
        node_height = 90
        h_spacing = 50
        v_spacing = 80

        # Position nodes by tier (bottom-up: tier 0 at bottom)
        for tier, nodes_in_tier in tiers.items():
            # Sort by exclusive group for consistent layout
            nodes_in_tier.sort(key=lambda n: (n.upgrade.exclusive_group or '', n.upgrade.id))

            # Calculate row width
            row_width = len(nodes_in_tier) * node_width + (len(nodes_in_tier) - 1) * h_spacing
            start_x = -row_width / 2

            # Vertical position (tier 0 at y=0, higher tiers above)
            tier_y = tier * (node_height + v_spacing)

            # Position each node
            for i, node in enumerate(nodes_in_tier):
                node_x = start_x + i * (node_width + h_spacing)
                node.x = node_x
                node.y = tier_y

                if self.on_node_moved:
                    self.on_node_moved(node.upgrade.id, node_x, tier_y)

        # Center camera on the tree
        if self.nodes:
            min_x = min(n.x for n in self.nodes.values())
            max_x = max(n.x for n in self.nodes.values())
            min_y = min(n.y for n in self.nodes.values())
            max_y = max(n.y for n in self.nodes.values())

            self.canvas.camera.x = (min_x + max_x) / 2
            self.canvas.camera.y = (min_y + max_y) / 2

        print("\tAuto-layout applied")

class EditorNode:
    """A node in the editor representing an upgrade."""

    NODE_RADIUS = 30

    def __init__(self, upgrade: Upgrade, x: float, y: float):
        self.upgrade = upgrade
        self.x = x
        self.y = y

    def contains_point(self, x: float, y: float) -> bool:
        """Check if a point is within this node."""
        dx = x - self.x
        dy = y - self.y
        return (dx * dx + dy * dy) <= (self.NODE_RADIUS * self.NODE_RADIUS)
