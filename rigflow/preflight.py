from __future__ import annotations

from typing import Dict, Iterable, List

from .result import CheckResult, Severity
from .session import summarize_results


READY = "READY"
READY_WITH_WARNINGS = "READY_WITH_WARNINGS"
BLOCKED = "BLOCKED"
NOT_RUN = "NOT_RUN"


def evaluate_preflight(
    scene_results: Iterable[CheckResult],
    audit_results: Iterable[CheckResult],
) -> Dict:
    scene = list(scene_results)
    audit = list(audit_results)
    combined: List[CheckResult] = scene + audit
    summary = summarize_results(combined)

    if not combined:
        status = NOT_RUN
    elif any(item.severity == Severity.ERROR for item in combined):
        status = BLOCKED
    elif any(item.severity == Severity.WARN for item in combined):
        status = READY_WITH_WARNINGS
    else:
        status = READY

    blocking = [item for item in combined if item.severity == Severity.ERROR]
    warnings = [item for item in combined if item.severity == Severity.WARN]
    return {
        "status": status,
        "ready_for_export": status in (READY, READY_WITH_WARNINGS),
        "blocking_errors": len(blocking),
        "warnings": len(warnings),
        "summary": summary,
        "blocking_codes": [item.code for item in blocking],
    }
