# RigFlow Toolkit for Maya

**RigFlow** is a Character Technical Art toolkit for Autodesk Maya. It
converts recurring rigging, skinning and animation-export checks into an
artist-facing preflight workflow with conservative automation and
traceable FBX delivery.

## Version 0.2.0

v0.2 builds on the functionally validated v0.1 baseline and adds the
production-oriented architecture planned in the project roadmap:

-   **Session Report v2** --- Scene Validation, Rig Audit, Safe Fix
    events and multiple exports remain accumulated in one session.
-   **Preflight Dashboard / Run All** --- one click runs all registered
    scene + rig checks and returns `READY`, `READY_WITH_WARNINGS` or
    `BLOCKED`.
-   **Validator Registry** --- new validators can be registered without
    changing the main UI.
-   **Clip Queue + Batch Export** --- queue multiple clips,
    enable/disable rows and export sequentially with per-clip status.
-   **Export Presets** --- packaged JSON profiles for Unreal Engine,
    Unity and Custom/Studio; additional presets can be added without UI
    edits.
-   **Safe Fix Framework** --- confirmation, one Maya undo chunk,
    automatic revalidation and rollback when the target error is not
    cleared.
-   **OpenMaya Skin Scanner** --- bulk weight reads through
    `maya.api.OpenMayaAnim.MFnSkinCluster`, with automatic fallback to
    the v0.1 `cmds.skinPercent` path.
-   **Details Panel** --- full result metadata/nodes plus
    copy-to-clipboard.
-   **Installer helpers** --- Maya `.mod` writer and shelf-button
    installer.
-   **Automated pure-Python tests** for session state, preflight,
    registry and presets.

> **Validation status:** v0.2.0 has completed manual QA in Autodesk Maya
> 2026.3 on Windows for the tested production workflows, including
> Preflight / Run All, Validate, Rig Audit, Safe Fix + Maya Undo,
> clip-range validation, export blocking, multi-clip FBX batch export,
> Unity/Unreal preset-side FBX generation, post-export scene integrity,
> and the OpenMaya skin-weight scanner. The scanner was benchmarked on a
> 10,201-vertex skinned mesh with a T19C median of **8.092 ms**
> (reported median throughput: **1,260,612 vertices/sec**). Unity and
> Unreal Engine were not installed, so engine-side FBX import remains
> unverified. See `docs/V0.2_VALIDATION_CHECKLIST.md` for the evidence
> status and remaining unverified checklist items.

## Repository layout

``` text
rigflow-maya/
├─ README.md
├─ CHANGELOG.md
├─ LICENSE
├─ rigflow/
│  ├─ __init__.py
│  ├─ version.py
│  ├─ compat.py
│  ├─ config.py
│  ├─ result.py
│  ├─ session.py
│  ├─ preflight.py
│  ├─ registry.py
│  ├─ validators.py
│  ├─ rig_audit.py
│  ├─ skin_scanner.py
│  ├─ safe_fix.py
│  ├─ presets.py
│  ├─ clip_exporter.py
│  ├─ report.py
│  ├─ installer.py
│  ├─ ui.py
│  └─ launcher.py
├─ presets/
│  ├─ unreal.json
│  ├─ unity.json
│  └─ custom.json
├─ sample/
│  └─ rigflow_config.json
├─ scripts/
│  ├─ build_demo_scene.py
│  └─ install_rigflow.py
├─ modules/
│  └─ RigFlow.mod.template
├─ tests/
└─ docs/
   └─ V0.2_VALIDATION_CHECKLIST.md
```

## Launch in Maya

The v0.1-compatible launch path remains valid:

``` python
import sys
sys.path.insert(0, r"C:/PATH/TO/rigflow-maya")

import rigflow
rigflow.show()
```

To reload during development:

``` python
import importlib
import rigflow.ui
importlib.reload(rigflow.ui)
rigflow.ui.show_window()
```

## Optional installation

Once the repository root is on `sys.path`, run inside Maya:

``` python
from rigflow.installer import write_module_file, install_shelf_button
write_module_file()
install_shelf_button()
```

`write_module_file()` creates `RigFlow.mod` in the current Maya user
modules folder. Restart Maya once so the module is discovered
automatically. The shelf button opens RigFlow directly.

## Recommended v0.2 demo flow

1.  Run `scripts/build_demo_scene.py` inside Maya.
2.  Open RigFlow and choose **Preflight → Run All**.
3.  Show the accumulated PASS/WARN/ERROR counts and the blocking state.
4.  Open **Validate**, select a problem, and use **Select Problem**.
5.  Open **Rig Audit**, force `normalizeWeights=0`, run the audit, and
    demonstrate **Safe Fix** + automatic revalidation + Maya Undo.
6.  Open **Export**, choose the root joint and target preset.
7.  Add at least three clips to the queue and use **Export Enabled**.
8.  Save the JSON report and show the independent `scene_validation`,
    `rig_audit`, `safe_fixes`, `exports`, `preflight` and
    `config_snapshot` sections.

## Design principles

-   **Artist-facing:** readable checks, direct selection, explicit
    preflight state.
-   **Non-destructive export:** animation export uses a temporary baked
    skeleton copy and removes it after export.
-   **Conservative automation:** only explicitly approved fixes are
    exposed automatically.
-   **Traceable:** checks, fixes, environment metadata, presets and
    per-clip outcomes are reportable.
-   **Extensible:** validators and export profiles are registries/data
    rather than UI hard-coding.
-   **Performance-aware:** OpenMaya bulk scanning is used where possible
    while retaining a conservative fallback.

## Current scope boundary

v0.2 still exports animation skeleton clips rather than a full
duplicated skinned-character package. Full skeleton + skinned mesh
export, bind-pose validation, constraint audits, animation-curve audits,
template skeleton comparison and mirror/symmetry checks remain v0.3
work.

## Tests outside Maya

From the repository root:

``` bash
python -m pytest -q
```

The automated tests intentionally cover Maya-independent logic only.
Maya-dependent workflows were also exercised manually in Autodesk Maya
2026.3; the evidence status and remaining unverified items are recorded
in `docs/V0.2_VALIDATION_CHECKLIST.md`.

## License

MIT --- see `LICENSE`.
