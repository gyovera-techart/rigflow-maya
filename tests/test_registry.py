from rigflow.registry import ValidatorRegistry, ValidatorSpec
from rigflow.result import CheckResult, Severity


def test_registry_adds_validator_without_ui_dependency():
    registry = ValidatorRegistry()
    registry.register(ValidatorSpec(
        "demo",
        "scene_validation",
        "Demo",
        lambda cfg: CheckResult("demo", "Demo", Severity.PASS, "ok"),
    ))
    results = registry.run_category("scene_validation", {})
    assert len(results) == 1
    assert results[0].code == "demo"


def test_registry_converts_exception_to_error_result():
    def boom(cfg):
        raise RuntimeError("boom")

    registry = ValidatorRegistry()
    registry.register(ValidatorSpec("boom", "scene_validation", "Boom", boom))
    result = registry.run_category("scene_validation", {})[0]
    assert result.severity == Severity.ERROR
    assert "boom" in result.message
