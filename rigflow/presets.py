from __future__ import annotations

import json
import os
from copy import deepcopy
from typing import Any, Dict, List, Optional


def _deep_update(base: Dict[str, Any], patch: Dict[str, Any]) -> Dict[str, Any]:
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _deep_update(base[key], value)
        else:
            base[key] = deepcopy(value)
    return base


def default_preset_dir() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, "presets"))


def list_presets(preset_dir: Optional[str] = None) -> List[str]:
    preset_dir = preset_dir or default_preset_dir()
    if not os.path.isdir(preset_dir):
        return []
    return sorted(
        os.path.splitext(name)[0]
        for name in os.listdir(preset_dir)
        if name.lower().endswith(".json")
    )


def load_preset(name: str, preset_dir: Optional[str] = None) -> Dict[str, Any]:
    preset_dir = preset_dir or default_preset_dir()
    safe_name = os.path.basename(name)
    if safe_name.lower().endswith(".json"):
        safe_name = os.path.splitext(safe_name)[0]
    path = os.path.join(preset_dir, safe_name + ".json")
    if not os.path.isfile(path):
        raise ValueError("Unknown export preset: %s" % name)
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if "id" not in data:
        data["id"] = safe_name
    data.setdefault("label", data["id"])
    data.setdefault("export", {})
    return data


def apply_preset(config: Dict[str, Any], preset: Dict[str, Any]) -> Dict[str, Any]:
    merged = deepcopy(config)
    merged.setdefault("export", {})
    _deep_update(merged["export"], preset.get("export", {}))
    merged["active_export_preset"] = {
        "id": preset.get("id"),
        "label": preset.get("label", preset.get("id")),
    }
    return merged
