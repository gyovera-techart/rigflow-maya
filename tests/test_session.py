from rigflow.result import CheckResult, Severity
from rigflow.session import RigFlowSession, summarize_results
from rigflow.preflight import evaluate_preflight, READY_WITH_WARNINGS, BLOCKED


def test_session_keeps_independent_sections():
    session = RigFlowSession({"x": 1})
    scene = [CheckResult("a", "A", Severity.PASS, "ok")]
    audit = [CheckResult("b", "B", Severity.WARN, "review")]
    session.set_scene_validation(scene)
    session.set_rig_audit(audit)
    payload = session.to_dict()
    assert payload["scene_validation"]["checks"][0]["code"] == "a"
    assert payload["rig_audit"]["checks"][0]["code"] == "b"


def test_summary_counts():
    results = [
        CheckResult("a", "A", Severity.PASS, ""),
        CheckResult("b", "B", Severity.WARN, ""),
        CheckResult("c", "C", Severity.ERROR, ""),
    ]
    assert summarize_results(results) == {"pass": 1, "warn": 1, "error": 1, "total": 3}


def test_preflight_warning_is_exportable():
    data = evaluate_preflight(
        [CheckResult("a", "A", Severity.PASS, "")],
        [CheckResult("b", "B", Severity.WARN, "")],
    )
    assert data["status"] == READY_WITH_WARNINGS
    assert data["ready_for_export"] is True


def test_preflight_error_blocks():
    data = evaluate_preflight(
        [CheckResult("a", "A", Severity.ERROR, "")],
        [CheckResult("b", "B", Severity.PASS, "")],
    )
    assert data["status"] == BLOCKED
    assert data["ready_for_export"] is False
