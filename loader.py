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

    # Parse upgrades from main file and individual tree files
    all_upgrades: Dict[str, Upgrade] = {}

    # First, load upgrades from main file (if any)
    for item in data.get('upgrades', []):
        upgrade = _parse_upgrade(item)
        all_upgrades[upgrade.id] = upgrade

        # Add to appropriate tree
        if upgrade.tree in trees:
            trees[upgrade.tree].upgrades[upgrade.id] = upgrade

    # Then, load upgrades from individual tree files
    for item in data.get('trees', []):
        if 'filepath' in item:
            tree_filepath = item['filepath']
            tree_id = item['id']

            # Load upgrades from the tree's file
            try:
                with open(tree_filepath, 'r', encoding='utf-8') as tree_file:
                    tree_data = yaml.safe_load(tree_file)

                    for upgrade_item in tree_data.get('upgrades', []):
                        # Set the tree id if not specified
                        if 'tree' not in upgrade_item:
                            upgrade_item['tree'] = tree_id

                        upgrade = _parse_upgrade(upgrade_item)
                        all_upgrades[upgrade.id] = upgrade

                        # Add to appropriate tree
                        if upgrade.tree in trees:
                            trees[upgrade.tree].upgrades[upgrade.id] = upgrade
            except FileNotFoundError:
                print(f"Warning: Tree file not found: {tree_filepath}")
            except Exception as e:
                print(f"Error loading tree file {tree_filepath}: {e}")

    return trees, all_upgrades


def _parse_upgrade(item: dict) -> Upgrade:
    """Parse a single upgrade from dictionary."""
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

    return upgrade