from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Optional, Union

from .result import CheckResult, Severity

ValidatorReturn = Union[CheckResult, Iterable[CheckResult]]
ValidatorCallable = Callable[[Dict], ValidatorReturn]


@dataclass(frozen=True)
class ValidatorSpec:
    id: str
    category: str
    label: str
    callable: ValidatorCallable


class ValidatorRegistry:
    """Registry decoupling checks from the UI.

    Adding a validator requires registering a new spec; the UI consumes categories
    generically and therefore does not need to be edited for each new check.
    """

    def __init__(self) -> None:
        self._specs: Dict[str, ValidatorSpec] = {}

    def register(self, spec: ValidatorSpec) -> None:
        if spec.id in self._specs:
            raise ValueError("Validator already registered: %s" % spec.id)
        self._specs[spec.id] = spec

    def specs(self, category: Optional[str] = None) -> List[ValidatorSpec]:
        values = list(self._specs.values())
        if category is not None:
            values = [item for item in values if item.category == category]
        return values

    def run_category(self, category: str, config: Dict) -> List[CheckResult]:
        results: List[CheckResult] = []
        for spec in self.specs(category):
            try:
                raw = spec.callable(config)
                if isinstance(raw, CheckResult):
                    results.append(raw)
                else:
                    results.extend(list(raw))
            except Exception as exc:
                results.append(CheckResult(
                    code=spec.id + "_exception",
                    title=spec.label,
                    severity=Severity.ERROR,
                    message="Validator failed: %s" % exc,
                    details={"exception": repr(exc)},
                ))
        return results


def build_default_registry() -> ValidatorRegistry:
    # Imported lazily to keep registry.py pure-Python and easy to unit test.
    from . import validators
    from . import rig_audit

    registry = ValidatorRegistry()
    scene_specs = [
        ("joint_naming", "Joint naming", validators.check_joint_naming),
        ("joint_scale", "Joint scale", validators.check_joint_scales),
        ("joint_roots", "Joint hierarchy", validators.check_joint_roots),
        ("unskinned_meshes", "SkinCluster presence", validators.check_unskinned_meshes),
        ("max_influences", "Maximum skin influences", validators.check_max_influences),
    ]
    for validator_id, label, callable_ in scene_specs:
        registry.register(ValidatorSpec(validator_id, "scene_validation", label, callable_))

    audit_specs = [
        ("joint_orientation", "Joint orientation", rig_audit.audit_joint_orientation),
        ("skin_settings", "Skin settings", rig_audit.audit_skin_settings),
        ("weight_sums", "Weight sums", rig_audit.audit_weight_sums),
    ]
    for validator_id, label, callable_ in audit_specs:
        registry.register(ValidatorSpec(validator_id, "rig_audit", label, callable_))
    return registry
