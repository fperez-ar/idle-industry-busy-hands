# loader_events.py

import yaml
from typing import Dict
from events import Event, EventChoice, EventTrigger
from loader import Effect, ResourceCost


def load_events(filepath: str) -> Dict[str, Event]:
    """Load events from YAML file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Warning: Events file not found: {filepath}")
        return {}

    events: Dict[str, Event] = {}

    for item in data.get('events', []):
        event = _parse_event(item)
        events[event.id] = event

    return events


def _parse_event(item: dict) -> Event:
    """Parse a single event from dictionary."""
    # Parse triggers
    triggers = []
    for trigger_item in item.get('triggers', []):
        triggers.append(EventTrigger(
            resource=trigger_item['resource'],
            threshold=trigger_item['threshold'],
            comparison=trigger_item.get('comparison', '>=')
        ))

    # Parse choices
    choices = []
    for choice_item in item.get('choices', []):
        # Parse costs
        costs = []
        for cost_item in choice_item.get('costs', []):
            costs.append(ResourceCost(
                resource=cost_item['resource'],
                amount=cost_item['amount']
            ))

        # Parse effects
        effects = []
        for effect_item in choice_item.get('effects', []):
            effects.append(Effect(
                resource=effect_item['resource'],
                effect=effect_item['effect'],
                value=effect_item['value']
            ))

        choices.append(EventChoice(
            id=choice_item['id'],
            text=choice_item['text'],
            description=choice_item['description'],
            effects=effects,
            costs=costs,
            requirements=choice_item.get('requirements', [])
        ))

    event = Event(
        id=item['id'],
        title=item['title'],
        description=item['description'],
        icon=item.get('icon', '❗'),
        triggers=triggers,
        choices=choices,
        one_time=item.get('one_time', True),
        cooldown=item.get('cooldown', 0.0)
    )

    return event
