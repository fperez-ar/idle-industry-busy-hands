from typing import Dict
from dataclasses import dataclass, field

from .upgrade import Upgrade
from .resource_definition import ResourceDefinition

@dataclass
class UpgradeTree:
    """A collection of related upgrades."""
    id: str
    name: str
    icon: str
    description: str
    upgrades: Dict[str, Upgrade] = field(default_factory=dict)