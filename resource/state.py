from typing import List
from dataclasses import dataclass
from resource.effect import ResourceEffect
from resource.definition import ResourceDefinition

@dataclass
class ResourceState:
    """Tracks current value and production modifiers for a single resource."""
    definition: ResourceDefinition
    current_value: float = 0.0
    is_unlocked: bool = True

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

    def apply_effect(self, effect: ResourceEffect):
        """Apply a single effect to this resource."""
        if effect.effect == "add":
            self.base_additions += effect.value
        elif effect.effect == "mult":
            self.total_multiplier *= effect.value
