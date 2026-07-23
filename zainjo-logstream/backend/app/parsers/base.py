"""
Base vendor parser interface.
Subclass this for each vendor and implement `parse()`.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ParsedFields:
    """Structured fields extracted by a vendor-specific parser."""
    username: Optional[str] = None
    operation: Optional[str] = None
    device: Optional[str] = None
    result: Optional[str] = None
    action: Optional[str] = None
    command: Optional[str] = None
    object_name: Optional[str] = None
    activity: Optional[str] = None
    node: Optional[str] = None
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = {
            k: v for k, v in {
                "username": self.username,
                "operation": self.operation,
                "device": self.device,
                "result": self.result,
                "action": self.action,
                "command": self.command,
                "object_name": self.object_name,
                "activity": self.activity,
                "node": self.node,
            }.items() if v is not None
        }
        d.update(self.extra)
        return d


class BaseParser(ABC):
    """Abstract base parser."""

    @abstractmethod
    def parse(self, message: str) -> ParsedFields:
        """Parse a syslog message body and return extracted fields."""
        ...

    def can_parse(self, message: str) -> bool:
        """Quick heuristic check — override if needed."""
        return True
