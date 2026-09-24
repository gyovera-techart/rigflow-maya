# RigFlow Toolkit for Maya

**RigFlow** is a Character Technical Art portfolio project for Autodesk Maya. It turns repetitive rigging, skinning, validation, and animation-export checks into a small artist-facing toolkit.

> **Current release: v0.1.0 — stable historical baseline, functionally validated in Autodesk Maya 2026.3 on Windows.**

[![Python syntax](https://github.com/gyovera-techart/rigflow-maya/actions/workflows/python-syntax.yml/badge.svg)](https://github.com/gyovera-techart/rigflow-maya/actions/workflows/python-syntax.yml)

## Why RigFlow?

Technical artists routinely spend time checking naming, hierarchy, skinning settings, weight integrity, and animation-export conditions. RigFlow packages these checks into a repeatable workflow with readable results and conservative automation.

## MVP implemented in v0.1.0

### Scene / Rig Validator

- configurable joint naming regex
- non-unit joint-scale warnings
- independent joint-root detection
- meshes without `skinCluster`
- per-vertex maximum-influence scan

### Joint & Skin Audit

- joint `rotateAxis` audit without falsely treating zero `jointOrient` as an error
- skinCluster normalization state
- maximum-influence policy
- sampled vertex weight-sum validation
- one deliberately conservative safe fix: enable skin-weight normalization

### Animation Clip Exporter

- Start / End / clip name / destination
- optional bake
- non-destructive skeleton export copy driven by constraints, then baked and removed
- FBX export of the baked hierarchy
- clip-name sanitization

### PySide UI

- Validate / Rig Audit / Export tabs
- PASS / WARN / ERROR results
- Select Problem
- safe-fix button only where a fix is explicitly implemented

### Reports

- JSON and TXT
- UTC timestamp
- Maya version
- scene information
- validation checks
- export results

## Repository layout

```text
rigflow-maya/
├── .github/
│   └── workflows/
│       └── python-syntax.yml
├── docs/
│   ├── validation/
│   │   └── VALIDATION_v0.1.0.md
│   └── REPOSITORY_AUDIT.md
├── rigflow/
│   ├── __init__.py
│   ├── compat.py
│   ├── config.py
│   ├── launcher.py
│   ├── report.py
│   ├── result.py
│   ├── rig_audit.py
│   ├── ui.py
│   ├── validators.py
│   └── clip_exporter.py
├── sample/
│   └── rigflow_config.json
├── scripts/
│   └── build_demo_scene.py
├── .gitignore
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
├── README.md
├── RELEASE.md
└── SECURITY.md
```

## Requirements

- Autodesk Maya 2026.x
- Windows for the documented v0.1.0 validation environment
- Maya Python environment with PySide support

RigFlow does not require API keys, cloud credentials, passwords, or external service tokens.

## Launch in Maya

1. Clone or download this repository.
2. Add the repository root (the folder containing `rigflow/`) to Maya's Python path.
3. Run in Maya's Python Script Editor:

```python
import sys
sys.path.insert(0, r"C:/PATH/TO/rigflow-maya")

import rigflow
rigflow.show()
```

To reload while developing:

```python
import importlib
import rigflow.ui
importlib.reload(rigflow.ui)
rigflow.ui.show_window()
```

## Optional configuration

RigFlow can load a local JSON configuration through the `RIGFLOW_CONFIG` environment variable. The repository includes a non-secret example at `sample/rigflow_config.json`.

Example:

```text
RIGFLOW_CONFIG=C:/PATH/TO/rigflow-maya/sample/rigflow_config.json
```

Do not put credentials or private project paths into a tracked configuration file.

## Recruiter / portfolio demo

1. Run `scripts/build_demo_scene.py` inside Maya.
2. Open RigFlow and click **Validate → Run**.
3. Show PASS / WARN / ERROR results.
4. Select an error row and click **Select Problem**.
5. Open **Rig Audit** and demonstrate the safe normalization fix where applicable.
6. In **Export**, select the root joint, define a clip, and export an FBX.
7. Save and inspect the JSON report.

## Validation

The v0.1.0 baseline was functionally validated in Autodesk Maya 2026.3 on Windows. The original validation protocol T01–T15 completed with PASS status.

See [`docs/validation/VALIDATION_v0.1.0.md`](docs/validation/VALIDATION_v0.1.0.md) for the validation record.

**Important:** the historical v0.1.0 validation evidence is not a claim that future versions are validated. Each new release must be tested in Maya before being described as functionally validated.

## Design principles

- **Artist-facing:** readable messages and direct scene selection.
- **Non-destructive export:** the working rig is not frozen or stripped.
- **Conservative automation:** only explicitly safe fixes are exposed automatically.
- **Configurable:** naming and rig budgets live in JSON rather than being hard-coded into the UI.
- **Modular:** validators, audits, exporting, reports, compatibility, and UI are separated into modules.

## Known v0.1.0 limits

- Vertex audits use `cmds.skinPercent`, which is intentionally simple but can be slower on dense production characters. A later version should move heavy skin queries to `maya.api.OpenMaya` / `OpenMayaAnim`.
- The current export path targets animation skeleton clips. Exporting a duplicated skinned mesh with transferred weights is planned for a later phase.
- Hierarchy validation is intentionally generic; studio-specific required-joint schemas should be added via configuration.
- No automatic joint renaming or transform freezing is performed because those actions can break downstream rig logic.
- The report model is not yet a complete cumulative session report.
- No batch clip queue, engine presets, installer, or automated Maya integration suite is included in v0.1.0.

## Roadmap

### v0.2

- validator registry
- richer session reporting
- preflight / Run All dashboard
- OpenMaya skin-weight scanner
- export presets for Unreal / Unity / custom targets
- clip queue / batch export
- richer error details
- safe fixes with undo and revalidation
- Maya shelf / installer
- automated tests

### v0.3+

- bind-pose validation
- constraint audit
- animation-curve audit
- skeleton comparison / templates
- mirror and symmetry checks
- configurable required-joint schemas
- complete character export workflows

## Project status

| Version | Status |
|---|---|
| **v0.1.0** | **Stable historical baseline — functionally validated** |
| v0.2.0 | Development / pending Maya validation |
| v0.3.0 | Planned |
| v1.0.0 | Future production-oriented milestone |

## Security

Please read [`SECURITY.md`](SECURITY.md) before reporting a security issue. Never commit API keys, passwords, access tokens, private keys, production scene files, or private client assets.

## License

MIT — see [`LICENSE`](LICENSE).

## Author

**Gianfranco Yovera Infanzon**

Character Technical Art / Technical Art portfolio project.
