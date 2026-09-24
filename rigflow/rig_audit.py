from __future__ import annotations

from typing import Dict, List, Optional

import maya.cmds as cmds

from .result import CheckResult, Severity
from .validators import _mesh_transforms, _skin_cluster_for_mesh


def audit_joint_orientation(config: Dict) -> CheckResult:
    suspicious = []
    details = {}
    for joint in cmds.ls(type="joint", long=True) or []:
        children = cmds.listRelatives(joint, children=True, type="joint", fullPath=True) or []
        orient = cmds.getAttr(joint + ".jointOrient")[0]
        rotate_axis = cmds.getAttr(joint + ".rotateAxis")[0]
        # We avoid declaring zero jointOrient intrinsically wrong. The audit flags
        # non-zero rotateAxis because it often hides an extra orientation layer.
        if any(abs(v) > 1e-5 for v in rotate_axis):
            suspicious.append(joint)
            details[joint] = {
                "jointOrient": [round(v, 4) for v in orient],
                "rotateAxis": [round(v, 4) for v in rotate_axis],
                "childJointCount": len(children),
            }
    if suspicious:
        return CheckResult(
            "joint_orientation", "Joint orientation", Severity.WARN,
            f"{len(suspicious)} joint(s) use non-zero rotateAxis; review orientation intent.",
            suspicious, details,
        )
    return CheckResult(
        "joint_orientation", "Joint orientation", Severity.PASS,
        "No joints use a non-zero rotateAxis. Zero jointOrient is not treated as an error by itself.",
    )


def audit_skin_settings(config: Dict) -> List[CheckResult]:
    max_inf = int(config["validation"].get("max_influences", 4))
    non_normalized = []
    bad_max = []
    data = {}
    seen = set()
    for mesh in _mesh_transforms():
        skin = _skin_cluster_for_mesh(mesh)
        if not skin or skin in seen:
            continue
        seen.add(skin)
        normalize = int(cmds.getAttr(skin + ".normalizeWeights"))
        maintain = int(cmds.getAttr(skin + ".maintainMaxInfluences"))
        max_attr = int(cmds.getAttr(skin + ".maxInfluences"))
        data[skin] = {
            "normalizeWeights": normalize,
            "maintainMaxInfluences": maintain,
            "maxInfluences": max_attr,
        }
        if normalize == 0:
            non_normalized.append(skin)
        if max_attr > max_inf or maintain == 0:
            bad_max.append(skin)

    results = []
    if non_normalized:
        results.append(CheckResult(
            "skin_normalization", "Normalized weights", Severity.ERROR,
            f"{len(non_normalized)} skinCluster(s) have normalization disabled.",
            non_normalized, {k: data[k] for k in non_normalized}, fix_id="enable_normalization",
        ))
    else:
        results.append(CheckResult("skin_normalization", "Normalized weights", Severity.PASS,
                                   "All audited skinClusters have normalization enabled."))

    if bad_max:
        results.append(CheckResult(
            "skin_max_settings", "Skin max-influence settings", Severity.WARN,
            f"{len(bad_max)} skinCluster(s) do not enforce the configured max influence policy ({max_inf}).",
            bad_max, {k: data[k] for k in bad_max},
        ))
    else:
        results.append(CheckResult(
            "skin_max_settings", "Skin max-influence settings", Severity.PASS,
            f"All audited skinClusters enforce maxInfluences <= {max_inf}.",
        ))
    return results


def audit_weight_sums(config: Dict) -> CheckResult:
    tolerance = float(config["validation"].get("weight_sum_tolerance", 0.001))
    scan_limit = int(config["validation"].get("max_vertices_to_scan", 5000))
    offenders = []
    for mesh in _mesh_transforms():
        skin = _skin_cluster_for_mesh(mesh)
        if not skin:
            continue
        verts = cmds.ls(mesh + ".vtx[*]", flatten=True) or []
        for vtx in verts[:scan_limit]:
            weights = cmds.skinPercent(skin, vtx, query=True, value=True) or []
            total = sum(weights)
            if abs(total - 1.0) > tolerance:
                offenders.append(vtx)
    if offenders:
        return CheckResult(
            "weight_sums", "Weight sums", Severity.ERROR,
            f"{len(offenders)} scanned vertex/vertices do not sum to 1.0 within tolerance {tolerance}.",
            offenders, {"scan_limit": scan_limit, "tolerance": tolerance},
        )
    return CheckResult("weight_sums", "Weight sums", Severity.PASS,
                       "Scanned vertex weights are normalized within tolerance.")


def run_rig_audit(config: Dict) -> List[CheckResult]:
    results = [audit_joint_orientation(config)]
    results.extend(audit_skin_settings(config))
    results.append(audit_weight_sums(config))
    return results


def apply_fix(fix_id: str, nodes: List[str]) -> str:
    if fix_id == "enable_normalization":
        changed = 0
        for skin in nodes:
            if cmds.objExists(skin) and cmds.nodeType(skin) == "skinCluster":
                cmds.setAttr(skin + ".normalizeWeights", 1)
                changed += 1
        return f"Enabled interactive weight normalization on {changed} skinCluster(s)."
    raise ValueError(f"Unknown or unsafe fix: {fix_id}")
