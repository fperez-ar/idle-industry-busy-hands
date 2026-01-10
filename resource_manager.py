from typing import Dict
from dataclasses import dataclass, field
from typing import Dict, Set

from definitions.upgrade import Upgrade
from resource.state import ResourceState
from resource.effect import ResourceEffect
from resource.definition import ResourceDefinition

class ResourceManager:
    """Manages all resources and their interactions."""

    def __init__(self, resource_definitions: Dict[str, ResourceDefinition]):
          self.definitions = resource_definitions
          self.resources: Dict[str, ResourceState] = {}

          # Initialize all resources
          for res_id, definition in resource_definitions.items():
              initial_value = definition.base_production * 10
              is_unlocked = not definition.is_dynamic  # Use the property

              self.resources[res_id] = ResourceState(
                  definition=definition,
                  current_value=initial_value,
                  is_unlocked=is_unlocked
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

    def apply_effect(self, effect: ResourceEffect):
        """Apply a single resource effect."""
        res = self.resources.get(effect.resource)
        if res:
            res.apply_effect(effect)

    def check_and_unlock_resources(self, current_year: int, owned_upgrades: Set[str]) -> bool:
        """Check and unlock dynamic resources based on year and upgrades.
        Returns True if any resource was unlocked."""
        any_unlocked = False

        for res_id, res_state in self.resources.items():
            if res_state.is_unlocked:
                continue  # Already unlocked

            definition = res_state.definition

            # Check year requirement
            if definition.unlock_year < current_year:
                continue

            # Check upgrade requirements
            if definition.requires:
                requirements_met = all(
                    upgrade_id in owned_upgrades
                    for upgrade_id in definition.requires
                )
                if not requirements_met:
                    continue

            # Unlock the resource
            res_state.is_unlocked = True
            any_unlocked = True
            print(f"🔓 Resource unlocked: {definition.name}")

        return any_unlocked


    def get_unlocked_resources(self) -> Dict[str, ResourceState]:
        """Get only unlocked resources."""
        return {
            res_id: res_state
            for res_id, res_state in self.resources.items()
            if res_state.is_unlocked
        }

    def get_locked_resources(self) -> Dict[str, ResourceState]:
        """Get only locked resources."""
        return {
            res_id: res_state
            for res_id, res_state in self.resources.items()
            if not res_state.is_unlocked
        }
