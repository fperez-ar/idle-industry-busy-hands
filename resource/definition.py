from typing import List
from dataclasses import dataclass

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