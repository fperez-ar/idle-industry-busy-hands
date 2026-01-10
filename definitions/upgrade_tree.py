from typing import Dict, List, Union
from dataclasses import dataclass, field

from .upgrade import Upgrade
from resource.definition import ResourceDefinition

@dataclass
class UpgradeTree:
    """A collection of related upgrades."""
    id: str
    name: str
    icon: str
    description: str
    upgrades: Dict[str, Upgrade] = field(default_factory=dict)
    requires: List[Union[str, List[str]]] = field(default_factory=list)
    year: int = 0