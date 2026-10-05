# Changelog

## 0.2.0 - 2026-09-19

- Added cumulative `RigFlowSession` state; Validate, Rig Audit, fixes and exports now coexist in one report.
- Added Session Report v2 with RigFlow/Maya/API/OS/FBX metadata, config snapshot and per-section summaries.
- Added Preflight dashboard and one-click **Run All** with READY / READY_WITH_WARNINGS / BLOCKED states.
- Added pluggable `ValidatorRegistry`; validators no longer need to be hard-wired into the main UI.
- Added clip queue with sequential batch export and per-clip status/history.
- Added JSON export presets for Unreal Engine, Unity and Custom/Studio targets.
- Added Safe Fix framework using a single Maya undo chunk, revalidation and rollback on failed validation.
- Added bulk OpenMayaAnim skin-weight scanner with conservative fallback to `cmds.skinPercent`.
- Added result details panel with full metadata/copy support.
- Added Maya `.mod` / shelf installer helpers.
- Added pure-Python tests for session state, preflight, registry and presets.
- Preserved `import rigflow; rigflow.show()` and the v0.1 public validation/audit/report entry points.
