from __future__ import annotations

import re
from typing import Dict, Iterable, List, Optional

import maya.cmds as cmds

from .result import CheckResult, Severity


def _short(node: str) -> str:
    return node.rsplit("|", 1)[-1]


def _mesh_transforms() -> List[str]:
    result = []
    for shape in cmds.ls(type="mesh", long=True) or []:
        if cmds.getAttr(shape + ".intermediateObject"):
            continue
        parents = cmds.listRelatives(shape, parent=True, fullPath=True) or []
        if parents:
            result.append(parents[0])
    return sorted(set(result))


def _skin_cluster_for_mesh(transform: str) -> Optional[str]:
    shapes = cmds.listRelatives(transform, shapes=True, noIntermediate=True, fullPath=True) or []
    if not shapes:
        return None
    history = cmds.listHistory(shapes[0], pruneDagObjects=True) or []
    skins = cmds.ls(history, type="skinCluster") or []
    return skins[0] if skins else None


def check_joint_naming(config: Dict) -> CheckResult:
    pattern = config["naming"]["joint_regex"]
    ignored = set(config["naming"].get("ignore_joints", []))
    regex = re.compile(pattern)
    bad = []
    for joint in cmds.ls(type="joint", long=True) or []:
        name = _short(joint)
        if name in ignored:
            continue
        if not regex.match(name):
            bad.append(joint)
    if bad:
        return CheckResult(
            "joint_naming", "Joint naming", Severity.ERROR,
            f"{len(bad)} joint(s) do not match regex: {pattern}", bad,
            {"pattern": pattern},
        )
    return CheckResult("joint_naming", "Joint naming", Severity.PASS,
                       "All joints match the configured naming convention.")


def check_joint_scales(config: Dict) -> CheckResult:
    tol = float(config["validation"].get("warn_joint_scale_tolerance", 0.0001))
    bad = []
    values = {}
    for joint in cmds.ls(type="joint", long=True) or []:
        scale = cmds.getAttr(joint + ".scale")[0]
        if any(abs(v - 1.0) > tol for v in scale):
            bad.append(joint)
            values[joint] = [round(v, 6) for v in scale]
    if bad:
        return CheckResult(
            "joint_scale", "Joint scale", Severity.WARN,
            f"{len(bad)} joint(s) have non-unit scale.", bad,
            {"scales": values},
        )
    return CheckResult("joint_scale", "Joint scale", Severity.PASS,
                       "All joints have unit scale.")


def check_joint_roots(config: Dict) -> CheckResult:
    roots = []
    for joint in cmds.ls(type="joint", long=True) or []:
        parent = cmds.listRelatives(joint, parent=True, fullPath=True, type="joint") or []
        if not parent:
            roots.append(joint)
    if not roots:
        return CheckResult("joint_roots", "Joint hierarchy", Severity.WARN,
                           "No joints were found in the scene.")
    allow_multiple = bool(config["validation"].get("allow_multiple_joint_roots", False))
    if len(roots) > 1 and not allow_multiple:
        return CheckResult(
            "joint_roots", "Joint hierarchy", Severity.ERROR,
            f"Found {len(roots)} independent joint roots; expected one.", roots,
        )
    return CheckResult("joint_roots", "Joint hierarchy", Severity.PASS,
                       f"Joint hierarchy root count: {len(roots)}.", roots)


def check_unskinned_meshes(config: Dict) -> CheckResult:
    unskinned = [m for m in _mesh_transforms() if not _skin_cluster_for_mesh(m)]
    if unskinned:
        return CheckResult(
            "unskinned_meshes", "SkinCluster presence", Severity.WARN,
            f"{len(unskinned)} renderable mesh(es) have no skinCluster.", unskinned,
        )
    return CheckResult("unskinned_meshes", "SkinCluster presence", Severity.PASS,
                       "All renderable meshes have a skinCluster.")


def _over_influenced_vertices(mesh: str, skin: str, max_influences: int, limit: int) -> List[str]:
    verts = cmds.ls(mesh + ".vtx[*]", flatten=True) or []
    offenders = []
    for vtx in verts[:limit]:
        values = cmds.skinPercent(skin, vtx, query=True, value=True) or []
        active = sum(1 for value in values if value > 1e-8)
        if active > max_influences:
            offenders.append(vtx)
    return offenders


def check_max_influences(config: Dict) -> CheckResult:
    max_influences = int(config["validation"].get("max_influences", 4))
    scan_limit = int(config["validation"].get("max_vertices_to_scan", 5000))
    offenders = []
    per_mesh = {}
    for mesh in _mesh_transforms():
        skin = _skin_cluster_for_mesh(mesh)
        if not skin:
            continue
        found = _over_influenced_vertices(mesh, skin, max_influences, scan_limit)
        if found:
            offenders.extend(found)
            per_mesh[mesh] = len(found)
    if offenders:
        return CheckResult(
            "max_influences", "Maximum skin influences", Severity.ERROR,
            f"{len(offenders)} scanned vertex/vertices exceed {max_influences} influences.",
            offenders,
            {"max_influences": max_influences, "per_mesh": per_mesh, "scan_limit": scan_limit},
        )
    return CheckResult(
        "max_influences", "Maximum skin influences", Severity.PASS,
        f"No scanned vertices exceed {max_influences} influences.",
        details={"scan_limit": scan_limit},
    )


CHECKS = [
    check_joint_naming,
    check_joint_scales,
    check_joint_roots,
    check_unskinned_meshes,
    check_max_influences,
]


def run_scene_validation(config: Dict) -> List[CheckResult]:
    results = []
    for check in CHECKS:
        try:
            results.append(check(config))
        except Exception as exc:
            results.append(CheckResult(
                code=f"{check.__name__}_exception",
                title=check.__name__.replace("check_", "").replace("_", " ").title(),
                severity=Severity.ERROR,
                message=f"Validator failed: {exc}",
                details={"exception": repr(exc)},
            ))
    return results
