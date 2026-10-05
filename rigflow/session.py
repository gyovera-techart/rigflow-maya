from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

from .result import CheckResult, Severity


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def summarize_results(results: Iterable[CheckResult]) -> Dict[str, int]:
    summary = {"pass": 0, "warn": 0, "error": 0, "total": 0}
    for result in results:
        summary["total"] += 1
        if result.severity == Severity.PASS:
            summary["pass"] += 1
        elif result.severity == Severity.WARN:
            summary["warn"] += 1
        elif result.severity == Severity.ERROR:
            summary["error"] += 1
    return summary


@dataclass
class RigFlowSession:
    """In-memory state for one RigFlow UI session.

    v0.1 kept only the latest result set. v0.2 stores independent sections so
    Validate, Rig Audit, Safe Fix and multiple exports can coexist in one report.
    """

    config_snapshot: Dict[str, Any]
    started_at: str = field(default_factory=_utc_now)
    updated_at: str = field(default_factory=_utc_now)
    scene_validation: List[CheckResult] = field(default_factory=list)
    rig_audit: List[CheckResult] = field(default_factory=list)
    exports: List[Dict[str, Any]] = field(default_factory=list)
    fixes: List[Dict[str, Any]] = field(default_factory=list)
    preflight: Dict[str, Any] = field(default_factory=dict)

    def touch(self) -> None:
        self.updated_at = _utc_now()

    def set_scene_validation(self, results: Iterable[CheckResult]) -> None:
        self.scene_validation = list(results)
        self.touch()

    def set_rig_audit(self, results: Iterable[CheckResult]) -> None:
        self.rig_audit = list(results)
        self.touch()

    def add_export(self, result: Dict[str, Any]) -> None:
        self.exports.append(deepcopy(result))
        self.touch()

    def add_fix(self, event: Dict[str, Any]) -> None:
        payload = deepcopy(event)
        payload.setdefault("timestamp_utc", _utc_now())
        self.fixes.append(payload)
        self.touch()

    def set_preflight(self, data: Dict[str, Any]) -> None:
        self.preflight = deepcopy(data)
        self.touch()

    def all_results(self) -> List[CheckResult]:
        return list(self.scene_validation) + list(self.rig_audit)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "started_at": self.started_at,
            "updated_at": self.updated_at,
            "scene_validation": {
                "summary": summarize_results(self.scene_validation),
                "checks": [item.to_dict() for item in self.scene_validation],
            },
            "rig_audit": {
                "summary": summarize_results(self.rig_audit),
                "checks": [item.to_dict() for item in self.rig_audit],
            },
            "safe_fixes": deepcopy(self.fixes),
            "exports": deepcopy(self.exports),
            "preflight": deepcopy(self.preflight),
            "config_snapshot": deepcopy(self.config_snapshot),
        }
