from typing import List
from dataclasses import dataclass
from definitions.resource_cost import ResourceCost
from definitions.resource_effect import ResourceEffect

@dataclass
class EventChoice:
    """Represents a choice in an event."""
    id: str
    text: str
    description: str
    cost: List[ResourceCost]
    effects: List[ResourceEffect]

@dataclass
class Event:
    """Represents a game event with multiple choices."""
    id: str
    title: str
    description: str
    icon: str
    trigger_type: str  # "year" or "upgrades"
    trigger_value: int | List[str]  # int for year, List[str] for upgrade IDs
    choices: List[EventChoice]
    triggered: bool = False  # Track if event has been triggered
