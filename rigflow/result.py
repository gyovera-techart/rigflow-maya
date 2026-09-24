from dataclasses import dataclass, field
from enum import IntEnum
from typing import List, Optional, Callable, Dict, Any


class Severity(IntEnum):
    PASS = 0
    WARN = 1
    ERROR = 2

    @property
    def label(self) -> str:
        return self.name


@dataclass
class CheckResult:
    code: str
    title: str
    severity: Severity
    message: str
    nodes: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)
    fix_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "title": self.title,
            "severity": self.severity.label,
            "message": self.message,
            "nodes": list(self.nodes),
            "details": dict(self.details),
            "fix_id": self.fix_id,
        }
