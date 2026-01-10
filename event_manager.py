from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from definitions.resource_cost import ResourceCost
from definitions.resource_effect import ResourceEffect
from definitions.event import EventChoice, Event

class EventManager:
    """Manages game events and their triggers."""

    def __init__(self, events: Dict[str, Event]):
        self.events = events
        self.pending_event: Optional[Event] = None

    def check_triggers(self, current_year: int, owned_upgrades: set) -> Optional[Event]:
        """Check if any events should trigger."""
        if self.pending_event:
            return None  # Already have a pending event

        for event_id, event in self.events.items():
            if event.triggered:
                continue

            if event.trigger_type == "year":
                if current_year >= event.trigger_value:
                    event.triggered = True
                    self.pending_event = event
                    return event

            elif event.trigger_type == "upgrades":
                required_upgrades = set(event.trigger_value)
                if required_upgrades.issubset(owned_upgrades):
                    event.triggered = True
                    self.pending_event = event
                    return event

        return None

    def clear_pending(self):
        """Clear the pending event after it's been handled."""
        self.pending_event = None
