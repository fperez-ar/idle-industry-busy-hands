from typing import Dict, Union, List, Optional, Set
from dataclasses import dataclass

from time_system import TimeSystem
from resource_manager import ResourceManager
from loader import Upgrade, UpgradeTree
from event_manager import EventManager, EventChoice


class GameState:
    """Central game state manager."""

    def __init__(
        self,
        resource_manager: ResourceManager,
        trees: Dict[str, UpgradeTree],
        all_upgrades: Dict[str, Upgrade],
        time_system: TimeSystem,
        event_manager: EventManager
    ):
        self.resource_manager = resource_manager
        self.trees = trees
        self.all_upgrades = all_upgrades
        self.time_system = time_system
        self.owned_upgrades: Set[str] = set()
        self.selected_exclusive: Dict[str, str] = {}  # group_id -> upgrade_id
        self.event_manager = event_manager
        self.active_event: Optional[Event] = None

    @property
    def current_year(self) -> int:
        """Get current year from time system."""
        return self.time_system.current_year

    def check_requirements_met(self, upgrade: Upgrade) -> bool:
        """Check if all requirements for an upgrade are met."""
        # Check prerequisite upgrades
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

        groups = upgrade.exclusive_group if isinstance(upgrade.exclusive_group, list) else [upgrade.exclusive_group]

        for group in groups:
          if group in self.selected_exclusive:
              # Only available if this specific upgrade was already selected
              if self.selected_exclusive[group] != upgrade.id:
                  return False

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

    def get_upgrades_by_year(self, year: int) -> List[Upgrade]:
        """Get all upgrades that unlock in a specific year."""
        return [
            upgrade for upgrade in self.all_upgrades.values()
            if upgrade.year == year
        ]

    def get_next_year_with_upgrades(self) -> Optional[int]:
        """Get the next year that has upgrades unlocking."""
        future_years = set()
        for upgrade in self.all_upgrades.values():
            if upgrade.year > self.current_year and upgrade.id not in self.owned_upgrades:
                future_years.add(upgrade.year)

        return min(future_years) if future_years else None

    def get_upgrades_locked_by_year(self) -> Dict[int, List[Upgrade]]:
        """Get all upgrades grouped by the year they unlock."""
        locked_by_year: Dict[int, List[Upgrade]] = {}

        for upgrade in self.all_upgrades.values():
            if upgrade.year > self.current_year and upgrade.id not in self.owned_upgrades:
                if upgrade.year not in locked_by_year:
                    locked_by_year[upgrade.year] = []
                locked_by_year[upgrade.year].append(upgrade)

        return locked_by_year

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

        # Check if we can afford it
        if not self.resource_manager.pay_costs(upgrade.cost):
            return False

        # Mark as owned
        self.owned_upgrades.add(upgrade_id)

        # Track exclusive group selection
        if upgrade.exclusive_group:
            groups = upgrade.exclusive_group if isinstance(upgrade.exclusive_group, list) else [upgrade.exclusive_group]
            for group in groups:
                self.selected_exclusive[group] = upgrade_id

        # Recalculate production with new upgrade
        self.resource_manager.recalculate_production(
            self.owned_upgrades,
            self.all_upgrades
        )

        return True


    def get_upgrade_status(self, upgrade_id: str) -> str:
        """Get a human-readable status for an upgrade."""
        if upgrade_id in self.owned_upgrades:
            return "owned"

        upgrade = self.all_upgrades.get(upgrade_id)
        if not upgrade:
            return "unknown"

        # Check year lock
        if upgrade.year > self.current_year:
            return f"locked_year_{upgrade.year}"

        # Check exclusive group
        if not self.check_exclusive_group_available(upgrade):
            return "exclusive_blocked"

        # Check requirements
        if not self.check_requirements_met(upgrade):
            return "requirements_not_met"

        # Check affordability
        if not self.resource_manager.can_afford(upgrade.cost):
            return "cannot_afford"

        return "available"

    def get_blocking_requirements(self, upgrade_id: str) -> List[str]:
        """Get list of requirement IDs that are blocking this upgrade."""
        upgrade = self.all_upgrades.get(upgrade_id)
        if not upgrade:
            return []

        blocking = []

        for req in upgrade.requires:
            if isinstance(req, list):
                # OR condition - check if ANY are satisfied
                if not any(r in self.owned_upgrades for r in req):
                    blocking.extend([r for r in req if r not in self.owned_upgrades])
            else:
                # Direct requirement
                if req not in self.owned_upgrades:
                    blocking.append(req)

        return blocking

    def get_statistics(self) -> Dict[str, any]:
        """Get game statistics."""
        total_upgrades = len(self.all_upgrades)
        owned_count = len(self.owned_upgrades)
        available_count = len(self.get_available_upgrade_ids())

        # Count upgrades by tree
        tree_stats = {}
        for tree_id, tree in self.trees.items():
            tree_total = len(tree.upgrades)
            tree_owned = sum(1 for uid in tree.upgrades if uid in self.owned_upgrades)
            tree_stats[tree_id] = {
                'total': tree_total,
                'owned': tree_owned,
                'percentage': (tree_owned / tree_total * 100) if tree_total > 0 else 0
            }

        # Get next milestone year
        next_year = self.get_next_year_with_upgrades()

        return {
            'current_year': self.current_year,
            'total_upgrades': total_upgrades,
            'owned_upgrades': owned_count,
            'available_upgrades': available_count,
            'completion_percentage': (owned_count / total_upgrades * 100) if total_upgrades > 0 else 0,
            'tree_statistics': tree_stats,
            'next_unlock_year': next_year,
            'years_until_next_unlock': (next_year - self.current_year) if next_year else None
        }

    def update(self, dt: float, time_scale: float = 1.0):
        """Update game state with time scaling."""
        # Scale dt by time_scale
        scaled_dt = dt * time_scale

        # Update resources with scaled time
        self.resource_manager.update(scaled_dt)

    def reset(self):
        """Reset game state to initial conditions."""
        self.owned_upgrades.clear()
        self.selected_exclusive.clear()

        # Reset resources to starting values
        for res_id, res_state in self.resource_manager.resources.items():
            res_state.current_value = res_state.definition.base_production * 10
            res_state.reset_modifiers()

        # Reset time
        self.time_system.current_year = 1800
        self.time_system.year_progress = 0.0
        self.time_system.paused = False
        self.time_system.time_multiplier = 1.0

    def get_exclusive_group_info(self, group_name: str) -> Dict[str, any]:
        """Get information about an exclusive group."""
        upgrades_in_group = []
        for upgrade in self.all_upgrades.values():
            if upgrade.exclusive_group:
                groups = upgrade.exclusive_group if isinstance(upgrade.exclusive_group, list) else [upgrade.exclusive_group]
                if group_name in groups:
                    upgrades_in_group.append(upgrade)

        selected_id = self.selected_exclusive.get(group_name)
        selected_upgrade = None
        if selected_id:
            selected_upgrade = self.all_upgrades.get(selected_id)

        return {
            'group_name': group_name,
            'total_options': len(upgrades_in_group),
            'selected': selected_upgrade.name if selected_upgrade else None,
            'selected_id': selected_id,
            'options': [
                {
                    'id': u.id,
                    'name': u.name,
                    'owned': u.id in self.owned_upgrades
                }
                for u in upgrades_in_group
            ]
        }

    def can_time_skip_to_year(self, target_year: int) -> bool:
        """Check if we can safely skip time to a target year."""
        # Don't allow skipping backwards
        if target_year <= self.current_year:
            return False

        # Check if we have enough resources to sustain until that year
        years_to_skip = target_year - self.current_year

        for res_id, res_state in self.resource_manager.resources.items():
            production_rate = res_state.get_production_per_second()
            # Assume 1 year = 2 seconds at normal speed
            projected_value = res_state.current_value + (production_rate * years_to_skip * 2)

            # Don't allow if any resource would go negative
            if projected_value < res_state.definition.min_value:
                return False

        return True

    def time_skip_to_year(self, target_year: int) -> bool:
        """Skip time forward to a specific year (if possible)."""
        if not self.can_time_skip_to_year(target_year):
            return False

        years_to_skip = target_year - self.current_year

        # Update resources
        for res_state in self.resource_manager.resources.values():
            production_rate = res_state.get_production_per_second()
            # Assume 1 year = 2 seconds at normal speed
            res_state.current_value += production_rate * years_to_skip * 2

            # Enforce minimum
            if res_state.current_value < res_state.definition.min_value:
                res_state.current_value = res_state.definition.min_value

        # Update year
        self.time_system.current_year = target_year
        self.time_system.year_progress = 0.0

        # Trigger year change callbacks for each year skipped
        for year in range(self.current_year + 1, target_year + 1):
            for callback in self.time_system.on_year_change:
                callback(year)

        return True

    def check_events(self):
        """Check for triggered events."""
        if self.active_event:
            return  # Already showing an event

        event = self.event_manager.check_triggers(
            self.current_year,
            self.owned_upgrades
        )
        if event:
            self.active_event = event
            print(f"🎭 Event triggered: {event.title}")

    def handle_event_choice(self, choice: EventChoice) -> bool:
        """Process an event choice."""
        # Check if can afford
        if not self.resource_manager.can_afford(choice.cost):
            return False

        # Deduct costs
        for cost in choice.cost:
            self.resource_manager.spend(cost.resource, cost.amount)

        # Apply effects
        for effect in choice.effects:
            self.resource_manager.apply_effect(effect)

        # Clear active event
        self.active_event = None
        self.event_manager.clear_pending()

        print(f"✓ Event choice selected: {choice.text}")
        return True