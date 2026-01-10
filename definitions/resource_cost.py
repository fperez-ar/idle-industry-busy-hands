from dataclasses import dataclass

@dataclass
class ResourceCost:
    """A single resource cost for an upgrade."""
    resource: str
    amount: float