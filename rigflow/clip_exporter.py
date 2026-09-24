from __future__ import annotations

import os
import re
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple

import maya.cmds as cmds
import maya.mel as mel


@dataclass
class AnimationClip:
    name: str
    start: float
    end: float
    output_dir: str
    bake: bool = True

    def validated(self) -> "AnimationClip":
        if not self.name.strip():
            raise ValueError("Clip name cannot be empty.")
        if self.end < self.start:
            raise ValueError("Clip end must be >= start.")
        safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", self.name.strip())
        return AnimationClip(safe_name, self.start, self.end, self.output_dir, self.bake)


def ensure_fbx_plugin() -> None:
    if not cmds.pluginInfo("fbxmaya", query=True, loaded=True):
        cmds.loadPlugin("fbxmaya", quiet=True)


def _hierarchy_joints(root: str) -> List[str]:
    descendants = cmds.listRelatives(root, allDescendents=True, type="joint", fullPath=True) or []
    return [root] + list(reversed(descendants))


def _pair_hierarchies(original_root: str, duplicate_root: str) -> List[Tuple[str, str]]:
    originals = _hierarchy_joints(original_root)
    duplicates = _hierarchy_joints(duplicate_root)
    if len(originals) != len(duplicates):
        raise RuntimeError("Duplicated skeleton hierarchy does not match the source skeleton.")
    return list(zip(originals, duplicates))


def prepare_export_skeleton(root_joint: str, start: float, end: float, step: float = 1.0) -> str:
    """Create a non-destructive baked copy of a skeleton for export.

    The working rig is never frozen or stripped. A duplicate skeleton is constrained
    to the source, baked over the requested range, then constraints are removed.
    """
    if not cmds.objExists(root_joint) or cmds.nodeType(root_joint) != "joint":
        raise ValueError("A valid root joint is required.")

    duplicate = cmds.duplicate(root_joint, renameChildren=True, returnRootsOnly=True)[0]
    duplicate = cmds.rename(duplicate, root_joint.rsplit("|", 1)[-1] + "_RF_EXPORT")
    pairs = _pair_hierarchies(root_joint, duplicate)
    constraints = []

    try:
        for source, target in pairs:
            constraints.extend(cmds.parentConstraint(source, target, maintainOffset=False) or [])
            constraints.extend(cmds.scaleConstraint(source, target, maintainOffset=False) or [])

        bake_nodes = [target for _, target in pairs]
        cmds.bakeResults(
            bake_nodes,
            time=(start, end),
            simulation=True,
            sampleBy=step,
            preserveOutsideKeys=False,
            sparseAnimCurveBake=False,
            disableImplicitControl=True,
            minimizeRotation=True,
            at=["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz"],
        )
    finally:
        if constraints:
            cmds.delete([c for c in constraints if cmds.objExists(c)])

    return duplicate


def _configure_fbx(config: Dict) -> None:
    export_cfg = config.get("export", {})
    mel.eval("FBXResetExport;")
    mel.eval("FBXExportAnimationOnly -v false;")
    mel.eval("FBXExportBakeComplexAnimation -v true;")
    mel.eval(f"FBXExportBakeComplexStep -v {float(export_cfg.get('bake_step', 1.0))};")
    mel.eval(f"FBXExportInAscii -v {'true' if export_cfg.get('fbx_ascii', False) else 'false'};")
    version = export_cfg.get("fbx_version")
    if version:
        try:
            mel.eval(f'FBXExportFileVersion -v "{version}";')
        except RuntimeError:
            # FBX plug-in versions differ in supported version strings.
            pass
    mel.eval(f"FBXExportConstraints -v {'true' if export_cfg.get('include_constraints', False) else 'false'};")
    mel.eval(f"FBXExportCameras -v {'true' if export_cfg.get('include_cameras', False) else 'false'};")
    mel.eval(f"FBXExportLights -v {'true' if export_cfg.get('include_lights', False) else 'false'};")


def export_clip(root_joint: str, clip: AnimationClip, config: Dict) -> Dict:
    clip = clip.validated()
    ensure_fbx_plugin()
    os.makedirs(clip.output_dir, exist_ok=True)
    output_path = os.path.normpath(os.path.join(clip.output_dir, clip.name + ".fbx"))
    export_root = None

    try:
        if clip.bake:
            export_root = prepare_export_skeleton(
                root_joint, clip.start, clip.end,
                float(config.get("export", {}).get("bake_step", 1.0)),
            )
        else:
            export_root = root_joint

        _configure_fbx(config)
        mel.eval(f"FBXExportBakeComplexStart -v {clip.start};")
        mel.eval(f"FBXExportBakeComplexEnd -v {clip.end};")
        cmds.select(export_root, replace=True, hierarchy=True)
        path_for_mel = output_path.replace("\\", "/").replace('"', '\\"')
        mel.eval(f'FBXExport -f "{path_for_mel}" -s;')
    finally:
        if clip.bake and export_root and cmds.objExists(export_root):
            cmds.delete(export_root)

    return {
        "clip": asdict(clip),
        "output": output_path,
        "success": os.path.isfile(output_path),
    }
