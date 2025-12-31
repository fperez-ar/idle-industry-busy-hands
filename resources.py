from typing import Dict
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
