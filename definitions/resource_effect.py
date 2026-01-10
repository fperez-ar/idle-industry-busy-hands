from dataclasses import dataclass

@dataclass
class ResourceEffect:
    """A single effect that an upgrade applies to a resource."""
    resource: str
    effect: str  # "add" or "mult"
    value: float