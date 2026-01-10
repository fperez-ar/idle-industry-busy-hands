from typing import List, Union, List, Optional
from dataclasses import dataclass
from .resource_cost import ResourceCost
from .resource_effect import ResourceEffect

@dataclass
class Upgrade:
    """A purchasable upgrade with costs and effects."""
    id: str
    tree: str
    name: str
    description: str
    tier: int
    year: int
    cost: List[ResourceCost]
    effects: List[ResourceEffect]
    exclusive_group: Optional[str]
    requires: List[Union[str, List[str]]]  # Supports AND/OR logic