# Technical Design Document: Pyglet Multi-Resource Idle/Tech Tree Game

This document outlines the technical architecture for an enhanced idle/incremental game using the Python `pyglet` library. Key improvements over the base design include:
- **Multiple resource types** with independent tracking
- **Multiple effects per upgrade** affecting different resources
- **Exclusive groups** for mutually exclusive choices
- **Prerequisite chains** with flexible requirements
- **Interactive tree visualization** with zoom and pan controls

---

## 1. Core Concept & Game Loop

The enhanced game loop accommodates multiple interacting resources:

1. **Generate Multiple Resources:** Each resource type (e.g., "manpower", "science", "capital") has its own generation rate.
2. **Spend Resources:** Upgrades may cost one or more resource types.
3. **Apply Multiple Effects:** Each upgrade can modify multiple resources—adding/subtracting flat values or applying multipliers.
4. **Handle Constraints:** Exclusive groups prevent selecting conflicting upgrades; prerequisites gate access.
5. **Repeat:** The player strategically balances resource generation and spending across multiple dimensions.

---

## 2. Project Structure & Dependencies

### Dependencies:
```
pyglet
PyYAML
```

### Proposed File Structure:

```
/pyglet_tech_tree_game/
├── main.py                 # Application entry point
├── game.py                 # Main Game window and core logic
├── state.py                # GameState: multi-resource tracking
├── loader.py               # YAML parsing and data classes
├── resources.py            # Resource definitions and calculations
├── ui/
│   ├── __init__.py
│   ├── tree_view.py        # Zoomable/pannable tree visualization
│   ├── upgrade_button.py   # Individual upgrade node UI
│   ├── resource_panel.py   # Resource display panel
│   └── tree_selector.py    # Tree/category selector sidebar
├── data/
│   ├── upgrades.yml        # Main upgrade definitions
│   └── resources.yml       # Resource type definitions
└── requirements.txt
```

---

## 3. Data-Driven Design

### 3.1 `resources.yml` Format

Defines all resource types available in the game:

```yaml
resources:
  - id: "capital"
    name: "Capital"
    description: "Financial resources for investments"
    icon: "💰"
    color: [255, 215, 0]  # Gold
    base_production: 1.0
    min_value: 0          # Can't go negative

  - id: "manpower"
    name: "Manpower"
    description: "Available workforce"
    icon: "👷"
    color: [100, 149, 237]  # Cornflower blue
    base_production: 0.5
    min_value: 0

  - id: "science"
    name: "Science"
    description: "Research points for technological advancement"
    icon: "🔬"
    color: [50, 205, 50]  # Lime green
    base_production: 0.0   # No passive generation by default
    min_value: 0

  - id: "influence"
    name: "Influence"
    description: "Political and social capital"
    icon: "🏛️"
    color: [148, 0, 211]  # Dark violet
    base_production: 0.1
    min_value: 0
```

### 3.2 `upgrades.yml` Format

The upgrade file now supports multiple trees, complex costs, and multiple effects:

```yaml
trees:
  - id: "technology"
    name: "Technology Tree"
    description: "Scientific and industrial advancements"
    icon: "⚙️"

  - id: "society"
    name: "Society Tree"
    description: "Social and political developments"
    icon: "🏛️"

upgrades:
  # === TECHNOLOGY TREE ===
  - id: "tech_basic_tools"
    tree: "technology"
    name: "Basic Tools"
    description: "Fundamental implements for production"
    tier: 0
    year: 1800
    cost:
      - resource: "capital"
        amount: 10
    effects:
      - resource: "capital"
        effect: "add"
        value: 0.5
      - resource: "manpower"
        effect: "mult"
        value: 1.1
    exclusive_group: null
    requires: []

  - id: "tech_research_lab"
    tree: "technology"
    name: "Research Lab"
    description: "Unlocks basic research capabilities"
    tier: 1
    year: 1850
    cost:
      - resource: "capital"
        amount: 50
      - resource: "manpower"
        amount: 5
    effects:
      - resource: "manpower"
        effect: "add"
        value: -1
      - resource: "science"
        effect: "add"
        value: 2
      - resource: "science"
        effect: "mult"
        value: 1.25
    exclusive_group: null
    requires: ["tech_basic_tools"]

  - id: "tech_steam_power"
    tree: "technology"
    name: "Steam Power"
    description: "Harness the power of steam for industry"
    tier: 2
    year: 1880
    cost:
      - resource: "capital"
        amount: 200
      - resource: "science"
        amount: 20
    effects:
      - resource: "capital"
        effect: "mult"
        value: 1.5
      - resource: "manpower"
        effect: "add"
        value: -2
    exclusive_group: "power_source"
    requires: ["tech_research_lab"]

  - id: "tech_hydroelectric"
    tree: "technology"
    name: "Hydroelectric Power"
    description: "Clean energy from flowing water"
    tier: 2
    year: 1890
    cost:
      - resource: "capital"
        amount: 300
      - resource: "science"
        amount: 30
    effects:
      - resource: "capital"
        effect: "mult"
        value: 1.3
      - resource: "influence"
        effect: "add"
        value: 1
    exclusive_group: "power_source"
    requires: ["tech_research_lab"]

  - id: "tech_advanced_manufacturing"
    tree: "technology"
    name: "Advanced Manufacturing"
    description: "Modern production techniques"
    tier: 3
    year: 1920
    cost:
      - resource: "capital"
        amount: 500
      - resource: "science"
        amount: 50
      - resource: "manpower"
        amount: 10
    effects:
      - resource: "capital"
        effect: "mult"
        value: 2.0
      - resource: "manpower"
        effect: "mult"
        value: 0.8
    exclusive_group: null
    requires:
      - ["tech_steam_power", "tech_hydroelectric"]  # ANY of these (OR condition)

  # === SOCIETY TREE ===
  - id: "soc_education"
    tree: "society"
    name: "Public Education"
    description: "Establish schools and universities"
    tier: 0
    year: 1800
    cost:
      - resource: "capital"
        amount: 30
      - resource: "influence"
        amount: 5
    effects:
      - resource: "science"
        effect: "add"
        value: 1
      - resource: "influence"
        effect: "mult"
        value: 1.2
    exclusive_group: null
    requires: []

  - id: "soc_democracy"
    tree: "society"
    name: "Democratic Reforms"
    description: "Empower citizens through representation"
    tier: 1
    year: 1850
    cost:
      - resource: "influence"
        amount: 50
    effects:
      - resource: "influence"
        effect: "mult"
        value: 1.5
      - resource: "capital"
        effect: "mult"
        value: 0.9
    exclusive_group: "government"
    requires: ["soc_education"]

  - id: "soc_autocracy"
    tree: "society"
    name: "Centralized Authority"
    description: "Efficient top-down governance"
    tier: 1
    year: 1850
    cost:
      - resource: "influence"
        amount: 30
      - resource: "manpower"
        amount: 10
    effects:
      - resource: "capital"
        effect: "mult"
        value: 1.3
      - resource: "influence"
        effect: "add"
        value: -0.5
    exclusive_group: "government"
    requires: ["soc_education"]
```

### 3.3 Requirements Syntax

The `requires` field supports flexible prerequisite definitions:

```yaml
# Simple: ALL required (AND)
requires: ["tech_a", "tech_b"]  # Must have BOTH tech_a AND tech_b

# Nested list: ANY required (OR)
requires:
  - ["tech_a", "tech_b"]  # Must have tech_a OR tech_b

# Mixed: Complex conditions
requires:
  - "tech_base"              # Must have this (AND)
  - ["tech_opt_1", "tech_opt_2"]  # AND must have ONE of these (OR)
```

---

## 4. Technical Implementation Details

### Task 4.1: Data Classes and Loading (`loader.py`)

```python
import yaml
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Union

@dataclass
class ResourceDefinition:
    """Defines a resource type available in the game."""
    id: str
    name: str
    description: str
    icon: str
    color: List[int]
    base_production: float
    min_value: float = 0

@dataclass
class ResourceCost:
    """A single resource cost for an upgrade."""
    resource: str
    amount: float

@dataclass
class Effect:
    """A single effect that an upgrade applies to a resource."""
    resource: str
    effect: str  # "add" or "mult"
    value: float

@dataclass
class Upgrade:
    """A purchasable upgrade with costs and effects."""
    id: str
    tree: str
    name: str
    description: str
    tier: int
    year: int
    cost: List[ResourceCost]
    effects: List[Effect]
    exclusive_group: Optional[str]
    requires: List[Union[str, List[str]]]  # Supports AND/OR logic

@dataclass
class UpgradeTree:
    """A collection of related upgrades."""
    id: str
    name: str
    description: str
    icon: str
    upgrades: Dict[str, Upgrade] = field(default_factory=dict)


def load_resources(filepath: str) -> Dict[str, ResourceDefinition]:
    """Load resource definitions from YAML."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    resources = {}
    for item in data.get('resources', []):
        res = ResourceDefinition(
            id=item['id'],
            name=item['name'],
            description=item['description'],
            icon=item.get('icon', ''),
            color=item.get('color', [255, 255, 255]),
            base_production=item.get('base_production', 0.0),
            min_value=item.get('min_value', 0)
        )
        resources[res.id] = res
    return resources


def load_upgrades(filepath: str) -> tuple[Dict[str, UpgradeTree], Dict[str, Upgrade]]:
    """Load upgrade trees and upgrades from YAML."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    # Parse trees
    trees: Dict[str, UpgradeTree] = {}
    for item in data.get('trees', []):
        tree = UpgradeTree(
            id=item['id'],
            name=item['name'],
            description=item.get('description', ''),
            icon=item.get('icon', '')
        )
        trees[tree.id] = tree

    # Parse upgrades
    all_upgrades: Dict[str, Upgrade] = {}
    for item in data.get('upgrades', []):
        # Parse costs
        costs = []
        for cost_item in item.get('cost', []):
            costs.append(ResourceCost(
                resource=cost_item['resource'],
                amount=cost_item['amount']
            ))

        # Parse effects
        effects = []
        for effect_item in item.get('effects', []):
            effects.append(Effect(
                resource=effect_item['resource'],
                effect=effect_item['effect'],
                value=effect_item['value']
            ))

        upgrade = Upgrade(
            id=item['id'],
            tree=item['tree'],
            name=item['name'],
            description=item['description'],
            tier=item.get('tier', 0),
            year=item.get('year', 0),
            cost=costs,
            effects=effects,
            exclusive_group=item.get('exclusive_group'),
            requires=item.get('requires', [])
        )

        all_upgrades[upgrade.id] = upgrade

        # Add to appropriate tree
        if upgrade.tree in trees:
            trees[upgrade.tree].upgrades[upgrade.id] = upgrade

    return trees, all_upgrades
```

### Task 4.2: Resource Management (`resources.py`)

```python
from dataclasses import dataclass, field
from typing import Dict, Set
from loader import ResourceDefinition, Upgrade, Effect

@dataclass
class ResourceState:
    """Tracks current value and production modifiers for a single resource."""
    definition: ResourceDefinition
    current_value: float = 0.0

    # Production modifiers
    base_additions: float = 0.0    # Sum of all additive effects
    total_multiplier: float = 1.0  # Product of all multiplicative effects

    def get_production_per_second(self) -> float:
        """Calculate net production rate."""
        base = self.definition.base_production + self.base_additions
        return base * self.total_multiplier

    def update(self, dt: float):
        """Update resource value based on production rate."""
        production = self.get_production_per_second()
        self.current_value += production * dt

        # Enforce minimum value
        if self.current_value < self.definition.min_value:
            self.current_value = self.definition.min_value

    def reset_modifiers(self):
        """Reset modifiers to base values (called before recalculating)."""
        self.base_additions = 0.0
        self.total_multiplier = 1.0

    def apply_effect(self, effect: Effect):
        """Apply a single effect to this resource."""
        if effect.effect == "add":
            self.base_additions += effect.value
        elif effect.effect == "mult":
            self.total_multiplier *= effect.value


class ResourceManager:
    """Manages all resources and their interactions."""

    def __init__(self, resource_definitions: Dict[str, ResourceDefinition]):
        self.resources: Dict[str, ResourceState] = {}

        for res_id, definition in resource_definitions.items():
            self.resources[res_id] = ResourceState(
                definition=definition,
                current_value=definition.base_production * 10  # Starting amount
            )

    def get(self, resource_id: str) -> ResourceState:
        """Get a specific resource state."""
        return self.resources.get(resource_id)

    def get_value(self, resource_id: str) -> float:
        """Get current value of a resource."""
        res = self.resources.get(resource_id)
        return res.current_value if res else 0.0

    def spend(self, resource_id: str, amount: float) -> bool:
        """Attempt to spend resources. Returns True if successful."""
        res = self.resources.get(resource_id)
        if res and res.current_value >= amount:
            res.current_value -= amount
            return True
        return False

    def can_afford(self, costs: list) -> bool:
        """Check if all costs can be paid."""
        for cost in costs:
            res = self.resources.get(cost.resource)
            if not res or res.current_value < cost.amount:
                return False
        return True

    def pay_costs(self, costs: list) -> bool:
        """Pay all costs. Returns True if successful."""
        if not self.can_afford(costs):
            return False

        for cost in costs:
            self.spend(cost.resource, cost.amount)
        return True

    def recalculate_production(self, owned_upgrades: Set[str], all_upgrades: Dict[str, Upgrade]):
        """Recalculate all production modifiers based on owned upgrades."""
        # Reset all modifiers
        for res in self.resources.values():
            res.reset_modifiers()

        # Apply effects from all owned upgrades
        for upgrade_id in owned_upgrades:
            if upgrade_id in all_upgrades:
                upgrade = all_upgrades[upgrade_id]
                for effect in upgrade.effects:
                    res = self.resources.get(effect.resource)
                    if res:
                        res.apply_effect(effect)

    def update(self, dt: float):
        """Update all resources."""
        for res in self.resources.values():
            res.update(dt)
```

### Task 4.3: Game State Management (`state.py`)

```python
from typing import Dict, Set, List, Union
from loader import Upgrade, UpgradeTree
from resources import ResourceManager

class GameState:
    """Central game state manager."""

    def __init__(
        self,
        resource_manager: ResourceManager,
        trees: Dict[str, UpgradeTree],
        all_upgrades: Dict[str, Upgrade]
    ):
        self.resource_manager = resource_manager
        self.trees = trees
        self.all_upgrades = all_upgrades
        self.owned_upgrades: Set[str] = set()
        self.selected_exclusive: Dict[str, str] = {}  # group_id -> upgrade_id
        self.current_year: int = 1800  # For year-gated content

    def check_requirements_met(self, upgrade: Upgrade) -> bool:
        """Check if all requirements for an upgrade are met."""
        for req in upgrade.requires:
            if isinstance(req, list):
                # OR condition: at least one must be owned
                if not any(r in self.owned_upgrades for r in req):
                    return False
            else:
                # Direct requirement: must be owned
                if req not in self.owned_upgrades:
                    return False

        # Check year requirement
        if upgrade.year > self.current_year:
            return False

        return True

    def check_exclusive_group_available(self, upgrade: Upgrade) -> bool:
        """Check if the upgrade's exclusive group slot is available."""
        if not upgrade.exclusive_group:
            return True

        # Check if another upgrade from this group is already owned
        group = upgrade.exclusive_group
        if group in self.selected_exclusive:
            return self.selected_exclusive[group] == upgrade.id

        return True

    def is_upgrade_available(self, upgrade_id: str) -> bool:
        """Check if an upgrade can be purchased (requirements met, not owned, group available)."""
        if upgrade_id in self.owned_upgrades:
            return False

        upgrade = self.all_upgrades.get(upgrade_id)
        if not upgrade:
            return False

        if not self.check_requirements_met(upgrade):
            return False

        if not self.check_exclusive_group_available(upgrade):
            return False

        return True

    def get_available_upgrade_ids(self) -> Set[str]:
        """Get all upgrade IDs that are currently available for purchase."""
        available = set()
        for upgrade_id in self.all_upgrades:
            if self.is_upgrade_available(upgrade_id):
                available.add(upgrade_id)
        return available

    def can_afford_upgrade(self, upgrade_id: str) -> bool:
        """Check if player can afford an upgrade."""
        upgrade = self.all_upgrades.get(upgrade_id)
        if not upgrade:
            return False
        return self.resource_manager.can_afford(upgrade.cost)

    def purchase_upgrade(self, upgrade_id: str) -> bool:
        """Attempt to purchase an upgrade. Returns True if successful."""
        if not self.is_upgrade_available(upgrade_id):
            return False

        upgrade = self.all_upgrades.get(upgrade_id)
        if not upgrade:
            return False

        if not self.resource_manager.pay_costs(upgrade.cost):
            return False

        # Mark as owned
        self.owned_upgrades.add(upgrade_id)

        # Track exclusive group selection
        if upgrade.exclusive_group:
            self.selected_exclusive[upgrade.exclusive_group] = upgrade_id

        # Recalculate production
        self.resource_manager.recalculate_production(
            self.owned_upgrades,
            self.all_upgrades
        )

        return True

    def update(self, dt: float):
        """Update game state each frame."""
        self.resource_manager.update(dt)
```

### Task 4.4: Zoomable/Pannable Tree View (`ui/tree_view.py`)

```python
import pyglet
from pyglet.text import Label
from pyglet.shapes import Rectangle, Line, Circle
from pyglet.graphics import Batch, Group
from typing import Dict, List, Optional, Tuple
import math

from loader import Upgrade, UpgradeTree


class Camera:
    """Handles zoom and pan transformations for the tree view."""

    def __init__(self, viewport_width: int, viewport_height: int):
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height

        # Camera position (center of view in world coordinates)
        self.x: float = 0.0
        self.y: float = 0.0

        # Zoom level (1.0 = 100%)
        self.zoom: float = 1.0
        self.min_zoom: float = 0.25
        self.max_zoom: float = 2.0

        # Pan state
        self.is_panning: bool = False
        self.pan_start_x: float = 0.0
        self.pan_start_y: float = 0.0
        self.camera_start_x: float = 0.0
        self.camera_start_y: float = 0.0

    def screen_to_world(self, screen_x: float, screen_y: float) -> Tuple[float, float]:
        """Convert screen coordinates to world coordinates."""
        # Offset from viewport center
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
        # Get world position under mouse before zoom
        world_x, world_y = self.screen_to_world(focus_x, focus_y)

        # Apply zoom
        old_zoom = self.zoom
        self.zoom *= (1.0 + delta * 0.1)
        self.zoom = max(self.min_zoom, min(self.max_zoom, self.zoom))

        # Adjust camera position to keep the point under mouse stationary
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

    def get_top_center(self) -> Tuple[float, float]:
        """Get top center point for incoming connections."""
        return (
            self.world_x + self.NODE_WIDTH / 2,
            self.world_y + self.NODE_HEIGHT
        )

    def get_bottom_center(self) -> Tuple[float, float]:
        """Get bottom center point for outgoing connections."""
        return (
            self.world_x + self.NODE_WIDTH / 2,
            self.world_y
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
        self.is_or_connection = is_or_connection  # Part of an OR requirement group

    def get_points(self) -> Tuple[float, float, float, float]:
        """Get start and end points for the line."""
        start = self.from_node.get_top_center()
        end = self.to_node.get_bottom_center()
        return (*start, *end)

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
        tree: UpgradeTree
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
        self._center_camera()

    def _layout_tree(self):
        """Calculate positions for all nodes in the tree."""
        if not self.tree.upgrades:
            return

        # Group upgrades by tier
        tiers: Dict[int, List[Upgrade]] = {}
        for upgrade in self.tree.upgrades.values():
            tier = upgrade.tier
            if tier not in tiers:
                tiers[tier] = []
            tiers[tier].append(upgrade)

        # Layout parameters
        node_width = TreeNode.NODE_WIDTH
        node_height = TreeNode.NODE_HEIGHT
        h_spacing = 50
        v_spacing = 80

        # Position nodes by tier (bottom-up: tier 0 at bottom)
        max_tier = max(tiers.keys()) if tiers else 0

        for tier, upgrades in tiers.items():
            # Sort by exclusive group for consistent layout
            upgrades.sort(key=lambda u: (u.exclusive_group or '', u.id))

            # Calculate row width
            row_width = len(upgrades) * node_width + (len(upgrades) - 1) * h_spacing
            start_x = -row_width / 2

            # Vertical position (tier 0 at y=0, higher tiers above)
            tier_y = tier * (node_height + v_spacing)

            # Position each node
            for i, upgrade in enumerate(upgrades):
                node_x = start_x + i * (node_width + h_spacing)
                node = TreeNode(upgrade, node_x, tier_y)
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

    def draw(self, batch: Batch):
        """Draw the tree view."""
        # Enable scissor test for clipping
        pyglet.gl.glEnable(pyglet.gl.GL_SCISSOR_TEST)
        pyglet.gl.glScissor(int(self.x), int(self.y), int(self.width), int(self.height))

        # Draw background
        bg = Rectangle(self.x, self.y, self.width, self.height, color=(25, 25, 30))
        bg.draw()

        # Draw connections
        for conn in self.connections:
            start_x, start_y, end_x, end_y = conn.get_points()

            # Transform to screen coordinates
            screen_start = self.camera.world_to_screen(start_x, start_y)
            screen_end = self.camera.world_to_screen(end_x, end_y)

            # Offset by view position
            line = Line(
                self.x + screen_start[0] - self.camera.viewport_width/2 + self.width/2,
                self.y + screen_start[1] - self.camera.viewport_height/2 + self.height/2,
                self.x + screen_end[0] - self.camera.viewport_width/2 + self.width/2,
                self.y + screen_end[1] - self.camera.viewport_height/2 + self.height/2,
                width=2 if conn.is_or_connection else 1,
                color=conn.get_color()
            )
            line.draw()

        # Draw nodes
        for node in self.nodes.values():
            self._draw_node(node)

        # Draw zoom indicator
        zoom_label = Label(
            f"Zoom: {self.camera.zoom:.0%}",
            x=self.x + 10,
            y=self.y + self.height - 25,
            font_size=10,
            color=(200, 200, 200, 255)
        )
        zoom_label.draw()

        pyglet.gl.glDisable(pyglet.gl.GL_SCISSOR_TEST)

    def _draw_node(self, node: TreeNode):
        """Draw a single node."""
        # Transform world coordinates to screen coordinates
        screen_x, screen_y = self.camera.world_to_screen(node.world_x, node.world_y)

        # Apply viewport offset
        draw_x = self.x + screen_x - self.camera.viewport_width/2 + self.width/2
        draw_y = self.y + screen_y - self.camera.viewport_height/2 + self.height/2

        # Scale dimensions by zoom
        scaled_width = TreeNode.NODE_WIDTH * self.camera.zoom
        scaled_height = TreeNode.NODE_HEIGHT * self.camera.zoom

        # Draw background
        color = node.get_color()
        bg = Rectangle(draw_x, draw_y, scaled_width, scaled_height, color=color)
        bg.draw()

        # Draw border for exclusive groups
        if node.upgrade.exclusive_group:
            border = Rectangle(
                draw_x - 2, draw_y - 2,
                scaled_width + 4, scaled_height + 4,
                color=(200, 150, 50)
            )
            # Draw as outline by drawing background on top
            border.draw()
            bg.draw()

        # Draw text (only if zoom is sufficient to read)
        if self.camera.zoom >= 0.5:
            font_size = max(8, int(11 * self.camera.zoom))

            # Name
            name_label = Label(
                node.upgrade.name,
                x=draw_x + 8 * self.camera.zoom,
                y=draw_y + scaled_height - 20 * self.camera.zoom,
                font_size=font_size,
                bold=True,
                color=(255, 255, 255, 255)
            )
            name_label.draw()

            # Year
            year_label = Label(
                f"Year: {node.upgrade.year}",
                x=draw_x + 8 * self.camera.zoom,
                y=draw_y + 8 * self.camera.zoom,
                font_size=max(7, int(9 * self.camera.zoom)),
                color=(180, 180, 180, 255)
            )
            year_label.draw()

            # Cost summary
            cost_text = ", ".join(
                f"{int(c.amount)} {c.resource}"
                for c in node.upgrade.cost
            )
            cost_label = Label(
                cost_text,
                x=draw_x + 8 * self.camera.zoom,
                y=draw_y + scaled_height - 40 * self.camera.zoom,
                font_size=max(7, int(9 * self.camera.zoom)),
                color=(255, 220, 100, 255)
            )
            cost_label.draw()

    def on_mouse_scroll(self, x: int, y: int, scroll_x: float, scroll_y: float):
        """Handle mouse scroll for zooming."""
        if not self._is_point_inside(x, y):
            return

        # Zoom centered on mouse position
        local_x = x - self.x
        local_y = y - self.y
        self.camera.apply_zoom(scroll_y, local_x, local_y)

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> Optional[str]:
        """Handle mouse press. Returns upgrade ID if a node was clicked."""
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
            world_x, world_y = self.camera.screen_to_world(
                local_x + self.camera.viewport_width/2 - self.width/2,
                local_y + self.camera.viewport_height/2 - self.height/2
            )

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

    def _is_point_inside(self, x: int, y: int) -> bool:
        """Check if a point is inside the view bounds."""
        return (
            self.x <= x <= self.x + self.width and
            self.y <= y <= self.y + self.height
        )

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

    def resize(self, width: int, height: int):
        """Handle resize of the view."""
        self.width = width
        self.height = height
        self.camera.resize(width, height)
```

### Task 4.5: Resource Display Panel (`ui/resource_panel.py`)

```python
import pyglet
from pyglet.text import Label
from pyglet.shapes import Rectangle
from typing import Dict

from resources import ResourceManager, ResourceState


class ResourcePanel:
    """Displays all resources and their production rates."""

    def __init__(self, x: int, y: int, width: int, height: int, resource_manager: ResourceManager):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.resource_manager = resource_manager

        self.batch = pyglet.graphics.Batch()
        self.labels: Dict[str, Dict[str, Label]] = {}

        self._create_ui()

    def _create_ui(self):
        """Create labels for each resource."""
        # Background
        self.background = Rectangle(
            self.x, self.y, self.width, self.height,
            color=(40, 40, 45),
            batch=self.batch
        )

        # Title
        self.title = Label(
            "Resources",
            x=self.x + 10,
            y=self.y + self.height - 25,
            font_size=14,
            bold=True,
            color=(255, 255, 255, 255),
            batch=self.batch
        )

        # Create labels for each resource
        row_height = 45
        current_y = self.y + self.height - 60

        for res_id, res_state in self.resource_manager.resources.items():
            definition = res_state.definition

            # Resource icon and name
            name_label = Label(
                f"{definition.icon} {definition.name}",
                x=self.x + 10,
                y=current_y + 20,
                font_size=11,
                color=(*definition.color, 255),
                batch=self.batch
            )

            # Current value
            value_label = Label(
                "0",
                x=self.x + 10,
                y=current_y,
                font_size=12,
                bold=True,
                color=(255, 255, 255, 255),
                batch=self.batch
            )

            # Production rate
            rate_label = Label(
                "+0.0/s",
                x=self.x + 120,
                y=current_y,
                font_size=10,
                color=(150, 255, 150, 255),
                batch=self.batch
            )

            self.labels[res_id] = {
                'name': name_label,
                'value': value_label,
                'rate': rate_label
            }

            current_y -= row_height

    def update(self):
        """Update displayed values."""
        for res_id, labels in self.labels.items():
            res_state = self.resource_manager.get(res_id)
            if res_state:
                # Format large numbers
                value = res_state.current_value
                if value >= 1_000_000:
                    value_text = f"{value/1_000_000:.2f}M"
                elif value >= 1_000:
                    value_text = f"{value/1_000:.2f}K"
                else:
                    value_text = f"{value:.1f}"

                labels['value'].text = value_text

                # Production rate
                rate = res_state.get_production_per_second()
                rate_color = (150, 255, 150, 255) if rate >= 0 else (255, 150, 150, 255)
                sign = "+" if rate >= 0 else ""
                labels['rate'].text = f"{sign}{rate:.2f}/s"
                labels['rate'].color = rate_color

    def draw(self):
        """Draw the resource panel."""
        self.batch.draw()
```

### Task 4.6: Tree Selector Sidebar (`ui/tree_selector.py`)

```python
import pyglet
from pyglet.text import Label
from pyglet.shapes import Rectangle
from typing import Dict, Optional

from loader import UpgradeTree


class TreeSelector:
    """Sidebar for selecting which upgrade tree to display."""

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        trees: Dict[str, UpgradeTree]
    ):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.trees = trees

        self.batch = pyglet.graphics.Batch()
        self.buttons: Dict[str, dict] = {}
        self.active_tree_id: Optional[str] = None

        self._create_ui()

        # Select first tree by default
        if trees:
            self.active_tree_id = list(trees.keys())[0]

    def _create_ui(self):
        """Create button UI for each tree."""
        # Background
        self.background = Rectangle(
            self.x, self.y, self.width, self.height,
            color=(35, 35, 40),
            batch=self.batch
        )

        # Title
        self.title = Label(
            "Tech Trees",
            x=self.x + self.width // 2,
            y=self.y + self.height - 25,
            anchor_x='center',
            font_size=12,
            bold=True,
            color=(255, 255, 255, 255),
            batch=self.batch
        )

        # Create buttons
        button_height = 50
        button_spacing = 8
        current_y = self.y + self.height - 60

        for tree_id, tree in self.trees.items():
            bg = Rectangle(
                self.x + 8, current_y,
                self.width - 16, button_height,
                color=(60, 60, 65),
                batch=self.batch
            )

            icon_label = Label(
                tree.icon,
                x=self.x + 20,
                y=current_y + button_height // 2,
                anchor_y='center',
                font_size=16,
                batch=self.batch
            )

            name_label = Label(
                tree.name,
                x=self.x + 45,
                y=current_y + button_height // 2,
                anchor_y='center',
                font_size=11,
                color=(255, 255, 255, 255),
                batch=self.batch
            )

            self.buttons[tree_id] = {
                'background': bg,
                'icon': icon_label,
                'name': name_label,
                'y': current_y,
                'height': button_height
            }

            current_y -= button_height + button_spacing

    def draw(self):
        """Draw the selector."""
        # Update button colors based on active state
        for tree_id, btn in self.buttons.items():
            if tree_id == self.active_tree_id:
                btn['background'].color = (40, 100, 140)
            else:
                btn['background'].color = (60, 60, 65)

        self.batch.draw()

    def on_mouse_press(self, x: int, y: int) -> Optional[str]:
        """Handle click. Returns tree ID if a button was clicked."""
        if not (self.x <= x <= self.x + self.width):
            return None

        for tree_id, btn in self.buttons.items():
            if btn['y'] <= y <= btn['y'] + btn['height']:
                self.active_tree_id = tree_id
                return tree_id

        return None

    def get_active_tree(self) -> Optional[UpgradeTree]:
        """Get currently selected tree."""
        if self.active_tree_id and self.active_tree_id in self.trees:
            return self.trees[self.active_tree_id]
        return None
```

### Task 4.7: Main Game Window (`game.py`)

```python
import pyglet
from pyglet.window import Window, mouse
from typing import Dict

from loader import load_resources, load_upgrades, UpgradeTree, Upgrade
from resources import ResourceManager
from state import GameState
from ui.tree_view import InteractiveTreeView
from ui.resource_panel import ResourcePanel
from ui.tree_selector import TreeSelector


class Game(Window):
    """Main game window."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Load data
        self.resource_definitions = load_resources('data/resources.yml')
        self.trees, self.all_upgrades = load_upgrades('data/upgrades.yml')

        # Initialize systems
        self.resource_manager = ResourceManager(self.resource_definitions)
        self.game_state = GameState(
            self.resource_manager,
            self.trees,
            self.all_upgrades
        )

        # Create UI components
        self._create_ui()

        # Schedule update
        pyglet.clock.schedule_interval(self.update, 1/60.0)

    def _create_ui(self):
        """Initialize all UI components."""
        # Layout constants
        sidebar_width = 160
        resource_panel_height = 250
        tree_selector_width = 140

        # Resource panel (top-left)
        self.resource_panel = ResourcePanel(
            x=0,
            y=self.height - resource_panel_height,
            width=sidebar_width,
            height=resource_panel_height,
            resource_manager=self.resource_manager
        )

        # Tree selector (left side, below resources)
        self.tree_selector = TreeSelector(
            x=0,
            y=0,
            width=sidebar_width,
            height=self.height - resource_panel_height,
            trees=self.trees
        )

        # Tree views (main area)
        self.tree_views: Dict[str, InteractiveTreeView] = {}
        tree_area_x = sidebar_width
        tree_area_width = self.width - sidebar_width

        for tree_id, tree in self.trees.items():
            self.tree_views[tree_id] = InteractiveTreeView(
                x=tree_area_x,
                y=0,
                width=tree_area_width,
                height=self.height,
                tree=tree
            )

        # Batch for misc drawing
        self.batch = pyglet.graphics.Batch()

    def update(self, dt: float):
        """Main update loop."""
        # Update game state
        self.game_state.update(dt)

        # Update UI
        self.resource_panel.update()

        # Update active tree view
        active_tree_id = self.tree_selector.active_tree_id
        if active_tree_id and active_tree_id in self.tree_views:
            available = self.game_state.get_available_upgrade_ids()
            self.tree_views[active_tree_id].update_nodes(
                self.game_state.owned_upgrades,
                available,
                self.resource_manager
            )

    def on_draw(self):
        """Render the game."""
        self.clear()

        # Draw active tree view
        active_tree_id = self.tree_selector.active_tree_id
        if active_tree_id and active_tree_id in self.tree_views:
            self.tree_views[active_tree_id].draw(self.batch)

        # Draw UI panels on top
        self.resource_panel.draw()
        self.tree_selector.draw()

        # Draw instructions
        instructions = pyglet.text.Label(
            "Scroll: Zoom | Right-drag: Pan | Left-click: Purchase",
            x=self.width - 10,
            y=10,
            anchor_x='right',
            font_size=9,
            color=(150, 150, 150, 255)
        )
        instructions.draw()

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        """Handle mouse clicks."""
        # Check tree selector
        selected_tree = self.tree_selector.on_mouse_press(x, y)
        if selected_tree:
            return

        # Check active tree view
        active_tree_id = self.tree_selector.active_tree_id
        if active_tree_id and active_tree_id in self.tree_views:
            clicked_upgrade = self.tree_views[active_tree_id].on_mouse_press(
                x, y, button, modifiers
            )

            if clicked_upgrade and button == mouse.LEFT:
                # Attempt to purchase
                success = self.game_state.purchase_upgrade(clicked_upgrade)
                if success:
                    print(f"Purchased: {clicked_upgrade}")
                else:
                    print(f"Cannot purchase: {clicked_upgrade}")

    def on_mouse_drag(self, x: int, y: int, dx: int, dy: int, buttons: int, modifiers: int):
        """Handle mouse drag for panning."""
        active_tree_id = self.tree_selector.active_tree_id
        if active_tree_id and active_tree_id in self.tree_views:
            self.tree_views[active_tree_id].on_mouse_drag(
                x, y, dx, dy, buttons, modifiers
            )

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int):
        """Handle mouse release."""
        active_tree_id = self.tree_selector.active_tree_id
        if active_tree_id and active_tree_id in self.tree_views:
            self.tree_views[active_tree_id].on_mouse_release(x, y, button, modifiers)

    def on_mouse_scroll(self, x: int, y: int, scroll_x: float, scroll_y: float):
        """Handle mouse scroll for zooming."""
        active_tree_id = self.tree_selector.active_tree_id
        if active_tree_id and active_tree_id in self.tree_views:
            self.tree_views[active_tree_id].on_mouse_scroll(x, y, scroll_x, scroll_y)

    def on_resize(self, width: int, height: int):
        """Handle window resize."""
        super().on_resize(width, height)

        # Recreate UI with new dimensions
        self._create_ui()
```

### Task 4.8: Application Entry Point (`main.py`)

```python
import pyglet
from game import Game

if __name__ == '__main__':
    # Configure pyglet
    pyglet.options['debug_gl'] = False

    # Create and run game
    window = Game(
        width=1280,
        height=720,
        caption='Tech Tree Game',
        resizable=True
    )

    pyglet.app.run()
```

---

## 5. Visual Design Specifications

### 5.1 Node Color Coding

| State | Color | Description |
|-------|-------|-------------|
| Owned | Blue (30, 100, 180) | Already purchased |
| Available + Affordable | Green (40, 160, 60) | Can be purchased now |
| Available + Unaffordable | Red (180, 60, 40) | Requirements met but insufficient resources |
| Unavailable | Dark Gray (70, 70, 70) | Requirements not met |
| Exclusive Blocked | Purple (100, 50, 100) | Another option in group selected |

### 5.2 Connection Line Styling

| Type | Style | Color |
|------|-------|-------|
| Satisfied Requirement | Solid | Green (100, 200, 100) |
| OR Connection (Unsatisfied) | Thick | Yellow (200, 180, 50) |
| AND Connection (Unsatisfied) | Normal | Gray (120, 120, 120) |

### 5.3 Exclusive Group Indicator

Nodes belonging to an exclusive group should have a colored border (e.g., golden/orange) to indicate mutual exclusivity.

---

## 6. Summary of Execution Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         main.py                                  │
│                            │                                     │
│                     Creates Game()                               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Game.__init__()                            │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 1. load_resources() → ResourceDefinitions                │    │
│  │ 2. load_upgrades() → Trees, All Upgrades                 │    │
│  │ 3. Create ResourceManager                                │    │
│  │ 4. Create GameState                                      │    │
│  │ 5. Create UI (ResourcePanel, TreeSelector, TreeViews)    │    │
│  │ 6. Schedule update loop at 60 FPS                        │    │
│  └─────────────────────────────────────────────────────────┘    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    pyglet.app.run()                              │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    Event Loop                             │   │
│  │                                                           │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐   │   │
│  │  │  update()   │  │  on_draw()  │  │  Input Events   │   │   │
│  │  │  (60 FPS)   │  │             │  │                 │   │   │
│  │  │             │  │             │  │ - mouse_press   │   │   │
│  │  │ • Update    │  │ • Clear     │  │ - mouse_drag    │   │   │
│  │  │   resources │  │ • Draw tree │  │ - mouse_scroll  │   │   │
│  │  │ • Update UI │  │ • Draw UI   │  │ - mouse_release │   │   │
│  │  │   states    │  │ • Draw HUD  │  │                 │   │   │
│  │  └─────────────┘  └─────────────┘  └─────────────────┘   │   │
│  │         │                                    │            │   │
│  │         ▼                                    ▼            │   │
│  │  ┌─────────────────────────────────────────────────────┐ │   │
│  │  │              GameState                               │ │   │
│  │  │  • owned_upg                                         │ │   │
│  │  │              GameState                               │ │   │
│  │  │  • owned_upgrades: Set[str]                          │ │   │
│  │  │  • selected_exclusive: Dict[str, str]                │ │   │
│  │  │  • check_requirements_met()                          │ │   │
│  │  │  • purchase_upgrade()                                │ │   │
│  │  └─────────────────────────────────────────────────────┘ │   │
│  │                          │                                │   │
│  │                          ▼                                │   │
│  │  ┌─────────────────────────────────────────────────────┐ │   │
│  │  │           ResourceManager                            │ │   │
│  │  │  • resources: Dict[str, ResourceState]               │ │   │
│  │  │  • recalculate_production()                          │ │   │
│  │  │  • can_afford() / pay_costs()                        │ │   │
│  │  │  • update(dt) → applies production rates             │ │   │
│  │  └─────────────────────────────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. Advanced Features & Extensions

### 7.1 Save/Load System

Add persistence to allow players to save and resume progress:

```python
# save_system.py
import json
from datetime import datetime
from typing import Dict, Any
from state import GameState
from resources import ResourceManager

class SaveSystem:
    """Handles saving and loading game state."""

    SAVE_VERSION = 1

    @staticmethod
    def save(game_state: GameState, resource_manager: ResourceManager, filepath: str):
        """Save current game state to file."""
        save_data = {
            'version': SaveSystem.SAVE_VERSION,
            'timestamp': datetime.now().isoformat(),
            'resources': {
                res_id: res.current_value
                for res_id, res in resource_manager.resources.items()
            },
            'owned_upgrades': list(game_state.owned_upgrades),
            'selected_exclusive': game_state.selected_exclusive,
            'current_year': game_state.current_year
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2)

    @staticmethod
    def load(filepath: str) -> Dict[str, Any]:
        """Load game state from file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    @staticmethod
    def apply_save(
        save_data: Dict[str, Any],
        game_state: GameState,
        resource_manager: ResourceManager
    ):
        """Apply loaded save data to game state."""
        # Restore resources
        for res_id, value in save_data.get('resources', {}).items():
            if res_id in resource_manager.resources:
                resource_manager.resources[res_id].current_value = value

        # Restore owned upgrades
        game_state.owned_upgrades = set(save_data.get('owned_upgrades', []))
        game_state.selected_exclusive = save_data.get('selected_exclusive', {})
        game_state.current_year = save_data.get('current_year', 1800)

        # Recalculate production based on owned upgrades
        resource_manager.recalculate_production(
            game_state.owned_upgrades,
            game_state.all_upgrades
        )
```

### 7.2 Tooltip System

Display detailed information when hovering over nodes:

```python
# ui/tooltip.py
import pyglet
from pyglet.text import Label
from pyglet.shapes import Rectangle
from typing import Optional, List
from loader import Upgrade

class Tooltip:
    """Displays detailed information about an upgrade on hover."""

    MAX_WIDTH = 280
    PADDING = 12

    def __init__(self):
        self.visible = False
        self.x = 0
        self.y = 0
        self.upgrade: Optional[Upgrade] = None
        self.is_owned = False
        self.is_available = False

    def show(self, upgrade: Upgrade, x: int, y: int, is_owned: bool, is_available: bool):
        """Show tooltip for an upgrade at the specified position."""
        self.upgrade = upgrade
        self.x = x + 15  # Offset from cursor
        self.y = y + 15
        self.is_owned = is_owned
        self.is_available = is_available
        self.visible = True

    def hide(self):
        """Hide the tooltip."""
        self.visible = False
        self.upgrade = None

    def draw(self):
        """Draw the tooltip."""
        if not self.visible or not self.upgrade:
            return

        # Build content
        lines = self._build_content()

        # Calculate dimensions
        line_height = 18
        total_height = len(lines) * line_height + self.PADDING * 2

        # Draw background
        bg = Rectangle(
            self.x, self.y - total_height,
            self.MAX_WIDTH, total_height,
            color=(20, 20, 25)
        )
        bg.draw()

        # Draw border
        border = Rectangle(
            self.x - 1, self.y - total_height - 1,
            self.MAX_WIDTH + 2, total_height + 2,
            color=(80, 80, 90)
        )
        # Draw border behind background

        # Draw text lines
        current_y = self.y - self.PADDING - line_height
        for text, color, bold in lines:
            label = Label(
                text,
                x=self.x + self.PADDING,
                y=current_y,
                font_size=10,
                bold=bold,
                color=color
            )
            label.draw()
            current_y -= line_height

    def _build_content(self) -> List[tuple]:
        """Build tooltip content lines. Returns list of (text, color, bold)."""
        lines = []
        upgrade = self.upgrade

        # Name
        lines.append((upgrade.name, (255, 255, 255, 255), True))

        # Status
        if self.is_owned:
            lines.append(("✓ Owned", (100, 200, 100, 255), False))
        elif not self.is_available:
            lines.append(("✗ Requirements not met", (200, 100, 100, 255), False))

        # Year
        lines.append((f"Year: {upgrade.year}", (180, 180, 180, 255), False))

        # Description
        lines.append(("", (255, 255, 255, 255), False))  # Spacer
        lines.append((upgrade.description, (200, 200, 200, 255), False))

        # Costs
        lines.append(("", (255, 255, 255, 255), False))  # Spacer
        lines.append(("Costs:", (255, 220, 100, 255), True))
        for cost in upgrade.cost:
            lines.append((f"  • {cost.amount:.0f} {cost.resource}", (255, 220, 100, 255), False))

        # Effects
        lines.append(("", (255, 255, 255, 255), False))  # Spacer
        lines.append(("Effects:", (100, 200, 255, 255), True))
        for effect in upgrade.effects:
            if effect.effect == "add":
                sign = "+" if effect.value >= 0 else ""
                effect_text = f"  • {sign}{effect.value:.1f} {effect.resource}/s"
            else:  # mult
                effect_text = f"  • ×{effect.value:.2f} {effect.resource}"

            color = (100, 255, 100, 255) if effect.value >= 1 else (255, 150, 100, 255)
            lines.append((effect_text, color, False))

        # Requirements
        if upgrade.requires:
            lines.append(("", (255, 255, 255, 255), False))  # Spacer
            lines.append(("Requires:", (200, 150, 255, 255), True))
            for req in upgrade.requires:
                if isinstance(req, list):
                    req_text = f"  • Any of: {', '.join(req)}"
                else:
                    req_text = f"  • {req}"
                lines.append((req_text, (200, 150, 255, 255), False))

        # Exclusive group
        if upgrade.exclusive_group:
            lines.append(("", (255, 255, 255, 255), False))  # Spacer
            lines.append((f"⚠ Exclusive: {upgrade.exclusive_group}", (255, 180, 50, 255), False))

        return lines
```

### 7.3 Time Progression System

Implement year advancement to gate content:

```python
# time_system.py
from typing import Callable, List

class TimeSystem:
    """Manages in-game time progression."""

    def __init__(self, start_year: int = 1800):
        self.current_year = start_year
        self.year_progress = 0.0  # Progress toward next year (0.0 to 1.0)
        self.years_per_second = 0.1  # Base time speed
        self.time_multiplier = 1.0
        self.paused = False

        # Callbacks for year change events
        self.on_year_change: List[Callable[[int], None]] = []

    def update(self, dt: float):
        """Update time progression."""
        if self.paused:
            return

        self.year_progress += dt * self.years_per_second * self.time_multiplier

        while self.year_progress >= 1.0:
            self.year_progress -= 1.0
            self.current_year += 1

            # Notify listeners
            for callback in self.on_year_change:
                callback(self.current_year)

    def set_speed(self, multiplier: float):
        """Set time speed multiplier."""
        self.time_multiplier = max(0.0, min(10.0, multiplier))

    def toggle_pause(self):
        """Toggle pause state."""
        self.paused = not self.paused

    def add_year_listener(self, callback: Callable[[int], None]):
        """Add a callback to be notified when year changes."""
        self.on_year_change.append(callback)
```

### 7.4 Achievement System

```python
# achievements.py
from dataclasses import dataclass
from typing import Dict, Set, Callable, Optional
from state import GameState
from resources import ResourceManager

@dataclass
class Achievement:
    """Definition of an achievement."""
    id: str
    name: str
    description: str
    icon: str
    hidden: bool = False  # Hidden until unlocked

class AchievementSystem:
    """Tracks and awards achievements."""

    def __init__(self):
        self.achievements: Dict[str, Achievement] = {}
        self.unlocked: Set[str] = set()
        self.on_unlock: Optional[Callable[[Achievement], None]] = None

        self._define_achievements()

    def _define_achievements(self):
        """Define all achievements."""
        self._add(Achievement(
            id="first_upgrade",
            name="First Steps",
            description="Purchase your first upgrade",
            icon="🎯"
        ))

        self._add(Achievement(
            id="ten_upgrades",
            name="Growing Empire",
            description="Own 10 upgrades",
            icon="🏗️"
        ))

        self._add(Achievement(
            id="reach_1000_capital",
            name="Wealthy",
            description="Accumulate 1,000 capital",
            icon="💰"
        ))

        self._add(Achievement(
            id="complete_tree",
            name="Master Technologist",
            description="Complete an entire tech tree",
            icon="🏆",
            hidden=True
        ))

    def _add(self, achievement: Achievement):
        """Add an achievement to the system."""
        self.achievements[achievement.id] = achievement

    def check_achievements(self, game_state: GameState, resource_manager: ResourceManager):
        """Check and award any newly earned achievements."""
        # First upgrade
        if len(game_state.owned_upgrades) >= 1:
            self._unlock("first_upgrade")

        # Ten upgrades
        if len(game_state.owned_upgrades) >= 10:
            self._unlock("ten_upgrades")

        # Resource milestones
        if resource_manager.get_value("capital") >= 1000:
            self._unlock("reach_1000_capital")

        # Complete tree
        for tree in game_state.trees.values():
            if all(uid in game_state.owned_upgrades for uid in tree.upgrades):
                self._unlock("complete_tree")
                break

    def _unlock(self, achievement_id: str):
        """Unlock an achievement."""
        if achievement_id in self.unlocked:
            return

        if achievement_id not in self.achievements:
            return

        self.unlocked.add(achievement_id)

        if self.on_unlock:
            self.on_unlock(self.achievements[achievement_id])
```

---

## 8. Performance Considerations

### 8.1 Batched Rendering

Use pyglet's `Batch` system to minimize draw calls:

```python
# All shapes and labels in a view should share a batch
self.batch = pyglet.graphics.Batch()

# Use groups for z-ordering within a batch
self.background_group = pyglet.graphics.Group(order=0)
self.connection_group = pyglet.graphics.Group(order=1)
self.node_group = pyglet.graphics.Group(order=2)
self.text_group = pyglet.graphics.Group(order=3)

# Create shapes with batch and group
bg = Rectangle(x, y, w, h, batch=self.batch, group=self.background_group)
```

### 8.2 Culling Off-Screen Elements

Only draw nodes visible within the viewport:

```python
def _is_node_visible(self, node: TreeNode) -> bool:
    """Check if a node is within the visible viewport."""
    screen_x, screen_y = self.camera.world_to_screen(node.world_x, node.world_y)

    # Add margin for partially visible nodes
    margin = 50

    return (
        -margin <= screen_x <= self.width + margin and
        -margin <= screen_y <= self.height + margin
    )
```

### 8.3 Label Caching

Avoid recreating labels every frame by updating text only when values change:

```python
class CachedLabel:
    """A label that only updates when its value changes."""

    def __init__(self, **kwargs):
        self.label = Label(**kwargs)
        self._cached_text = kwargs.get('text', '')

    def set_text(self, text: str):
        if text != self._cached_text:
            self._cached_text = text
            self.label.text = text
```

---

## 9. Testing Checklist

### 9.1 Unit Tests

- [ ] `loader.py`: YAML parsing with various edge cases
- [ ] `resources.py`: Production calculations with add/mult effects
- [ ] `state.py`: Requirement checking (AND/OR logic)
- [ ] `state.py`: Exclusive group handling
- [ ] `state.py`: Purchase flow validation

### 9.2 Integration Tests

- [ ] Full game loop with multiple resources
- [ ] Save/load preserves all state correctly
- [ ] UI updates reflect state changes

### 9.3 Manual Testing

- [ ] Pan/zoom feels responsive and intuitive
- [ ] Node colors update correctly on state changes
- [ ] Exclusive groups properly block alternatives
- [ ] Large tech trees (50+ nodes) perform well
- [ ] Window resize maintains proper layout

---

## 10. Complete File Reference

| File | Purpose |
|------|---------|
| `main.py` | Application entry point |
| `game.py` | Main window, event handling, game loop |
| `state.py` | Central game state management |
| `loader.py` | YAML parsing and data classes |
| `resources.py` | Multi-resource tracking and calculations |
| `ui/tree_view.py` | Zoomable/pannable tree visualization |
| `ui/resource_panel.py` | Resource display panel |
| `ui/tree_selector.py` | Tree category selector |
| `ui/upgrade_button.py` | Individual node rendering |
| `ui/tooltip.py` | Hover information display |
| `save_system.py` | Game persistence |
| `time_system.py` | Year progression |
| `achievements.py` | Achievement tracking |
| `data/resources.yml` | Resource definitions |
| `data/upgrades.yml` | Upgrade and tree definitions |
| `requirements.txt` | Python dependencies |

---

## 11. Quick Start Guide

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Create data files** in `data/` directory using the formats specified in Section 3.

3. **Run the game:**
   ```bash
   python main.py
   ```

4. **Controls:**
   - **Left-click** on a node to purchase (if available and affordable)
   - **Right-click + drag** or **Middle-click + drag** to pan
   - **Scroll wheel** to zoom in/out
   - **Click tree buttons** on the left to switch between tech trees