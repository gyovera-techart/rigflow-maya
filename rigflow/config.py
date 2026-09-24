from __future__ import annotations

import json
import os
from copy import deepcopy
from typing import Any, Dict, Optional

DEFAULT_CONFIG: Dict[str, Any] = {
    "naming": {
        "joint_regex": r"^(root|jnt|JNT)_[A-Za-z0-9_]+$",
        "ignore_joints": [],
    },
    "validation": {
        "max_influences": 4,
        "weight_sum_tolerance": 0.001,
        "max_vertices_to_scan": 5000,
        "warn_joint_scale_tolerance": 0.0001,
        "allow_multiple_joint_roots": False,
    },
    "export": {
        "fbx_ascii": False,
        "fbx_version": "FBX202000",
        "bake_step": 1.0,
        "include_constraints": False,
        "include_cameras": False,
        "include_lights": False,
    },
}


def _deep_update(base: Dict[str, Any], patch: Dict[str, Any]) -> Dict[str, Any]:
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _deep_update(base[key], value)
        else:
            base[key] = value
    return base


def load_config(path: Optional[str] = None) -> Dict[str, Any]:
    cfg = deepcopy(DEFAULT_CONFIG)
    if not path:
        env_path = os.environ.get("RIGFLOW_CONFIG")
        if env_path:
            path = env_path
    if path and os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as handle:
            user_cfg = json.load(handle)
        _deep_update(cfg, user_cfg)
    return cfg
