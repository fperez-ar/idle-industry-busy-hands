from typing import List, Optional
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

    unlock_year: Optional[int] = 0  # NEW: Year when resource becomes available
    requires: Optional[list] = None  # NEW: Upgrades required to unlock

    def __post_init__(self):
        if self.requires is None:
            self.requires = []

    @property
    def is_dynamic(self) -> bool:
        """Resource is dynamic if it has any unlock requirements."""
        return self.unlock_year > 0 or len(self.requires) > 0