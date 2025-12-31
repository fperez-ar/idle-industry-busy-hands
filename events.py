# events.py

from dataclasses import dataclass
from typing import List, Dict, Optional, Callable
from loader import Effect, ResourceCost


@dataclass
class EventChoice:
    """A choice the player can make in response to an event."""
    id: str
    text: str
    description: str
    effects: List[Effect]
    costs: List[ResourceCost]
    requirements: List[str]  # Upgrade IDs that must be owned


@dataclass
class EventTrigger:
    """Conditions that trigger an event."""
    resource: str
    threshold: float
    comparison: str  # ">=", "<=", ">", "<", "=="

    def check(self, resource_manager) -> bool:
        """Check if trigger condition is met."""
        res_state = resource_manager.get(self.resource)
        if not res_state:
            return False

        value = res_state.current_value

        if self.comparison == ">=":
            return value >= self.threshold
        elif self.comparison == "<=":
            return value <= self.threshold
        elif self.comparison == ">":
            return value > self.threshold
        elif self.comparison == "<":
            return value < self.threshold
        elif self.comparison == "==":
            return abs(value - self.threshold) < 0.01

        return False


@dataclass
class Event:
    """A game event that requires player decision."""
    id: str
    title: str
    description: str
    icon: str
    triggers: List[EventTrigger]
    choices: List[EventChoice]
    one_time: bool  # If True, can only trigger once
    cooldown: float  # Minimum time (in seconds) between triggers


class EventSystem:
    """Manages game events and their triggers."""

    def __init__(self, resource_manager, game_state):
        self.resource_manager = resource_manager
        self.game_state = game_state
        self.events: Dict[str, Event] = {}
        self.triggered_events: set = set()  # IDs of one-time events that have triggered
        self.event_cooldowns: Dict[str, float] = {}  # event_id -> time remaining

        # Current active event
        self.active_event: Optional[Event] = None

        # Callbacks
        self.on_event_triggered: Optional[Callable[[Event], None]] = None

    def add_event(self, event: Event):
        """Add an event to the system."""
        self.events[event.id] = event

    def update(self, dt: float):
        """Update event system, checking triggers and cooldowns."""
        # Update cooldowns
        for event_id in list(self.event_cooldowns.keys()):
            self.event_cooldowns[event_id] -= dt
            if self.event_cooldowns[event_id] <= 0:
                del self.event_cooldowns[event_id]

        # Don't check for new events if one is already active
        if self.active_event:
            return

        # Check all events for triggers
        for event_id, event in self.events.items():
            # Skip if already triggered and is one-time
            if event.one_time and event_id in self.triggered_events:
                continue

            # Skip if on cooldown
            if event_id in self.event_cooldowns:
                continue

            # Check all triggers
            if self._check_triggers(event):
                self._trigger_event(event)
                break  # Only trigger one event at a time

    def _check_triggers(self, event: Event) -> bool:
        """Check if all triggers for an event are met."""
        if not event.triggers:
            return False

        for trigger in event.triggers:
            if not trigger.check(self.resource_manager):
                return False

        return True

    def _trigger_event(self, event: Event):
        """Trigger an event."""
        self.active_event = event

        # Mark as triggered if one-time
        if event.one_time:
            self.triggered_events.add(event.id)

        # Start cooldown
        if event.cooldown > 0:
            self.event_cooldowns[event.id] = event.cooldown

        # Notify callback
        if self.on_event_triggered:
            self.on_event_triggered(event)

        print(f"🎭 Event triggered: {event.title}")

    def make_choice(self, choice: EventChoice) -> bool:
        """Player makes a choice for the active event."""
        if not self.active_event:
            return False

        # Check requirements
        for req in choice.requirements:
            if req not in self.game_state.owned_upgrades:
                return False

        # Check costs
        if not self.resource_manager.can_afford(choice.costs):
            return False

        # Pay costs
        if not self.resource_manager.pay_costs(choice.costs):
            return False

        # Apply effects as temporary modifiers
        for effect in choice.effects:
            res_state = self.resource_manager.get(effect.resource)
            if res_state:
                res_state.apply_temp_effect(effect)

        print(f"✓ Choice made: {choice.text}")

        # Clear active event
        self.active_event = None

        return True

    def can_make_choice(self, choice: EventChoice) -> bool:
        """Check if a choice can be made."""
        # Check requirements
        for req in choice.requirements:
            if req not in self.game_state.owned_upgrades:
                return False

        # Check costs
        if not self.resource_manager.can_afford(choice.costs):
            return False

        return True
