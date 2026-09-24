# Changelog

All notable changes to RigFlow Toolkit for Maya are documented here.

## [0.1.0] - 2026-09-18

### Added
- Scene Validator for joint naming, scale, hierarchy roots, skinCluster presence, and maximum skin influences.
- Rig Audit for joint orientation, skin normalization, maximum-influence settings, and weight-sum validation.
- Conservative Safe Fix for enabling skin-weight normalization.
- Non-destructive animation clip exporter with clip-range validation and filename sanitization.
- PySide-based Validate / Rig Audit / Export interface.
- JSON and TXT session reports.
- Reproducible demo-scene script with intentional validation errors.
- Configurable validation settings through JSON.

### Validation
- Functionally validated in Autodesk Maya 2026.3 on Windows for the documented MVP scope.
- Validation protocol T01–T15 completed with PASS status.

### Known limitations
- Skin-weight scanning uses `cmds.skinPercent` and may be slow on dense production meshes.
- Export is focused on animation skeleton clips rather than complete character packages with skinned meshes.
- Hierarchy validation is intentionally generic.
- Safe Fix is intentionally conservative and limited in this release.
- No batch clip queue, engine presets, installer, or automated Maya integration suite in this release.

[0.1.0]: https://github.com/
