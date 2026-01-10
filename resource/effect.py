from dataclasses import dataclass
from typing import Literal

@dataclass
class ResourceEffect:
    """A single effect that an upgrade applies to a resource."""
    resource: str
    effect: Literal["add", "mult"]
    value: float