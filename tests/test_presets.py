import json

from rigflow.presets import apply_preset, list_presets, load_preset


def test_packaged_presets_exist():
    names = list_presets()
    assert {"unreal", "unity", "custom"}.issubset(set(names))


def test_apply_preset_does_not_mutate_source_config():
    config = {"export": {"fbx_ascii": False, "bake_step": 1.0}}
    preset = {"id": "x", "label": "X", "export": {"bake_step": 2.0}}
    merged = apply_preset(config, preset)
    assert merged["export"]["bake_step"] == 2.0
    assert config["export"]["bake_step"] == 1.0
    assert merged["active_export_preset"]["id"] == "x"
