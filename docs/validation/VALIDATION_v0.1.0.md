# RigFlow v0.1.0 — Validation Record

**Baseline:** v0.1.0  
**Validation environment:** Autodesk Maya 2026.3, Windows  
**Validation date:** 2026-09-18  
**Scope:** MVP functional validation

## Result

RigFlow v0.1.0 was functionally validated for the documented MVP scope. The original validation protocol recorded T01–T15 as PASS.

## Validation coverage

| ID | Area | Result |
|---|---|---|
| T01 | UI load | PASS |
| T02 | Invalid joint naming detection | PASS |
| T03 | Naming revalidation | PASS |
| T04 | Joint scale detection/fix | PASS |
| T05 | Joint hierarchy root validation | PASS |
| T06 | Missing skinCluster warning | PASS |
| T07 | Rig audit | PASS |
| T08 | Forced normalization error detection | PASS |
| T09 | Safe normalization fix | PASS |
| T10 | Unsafe fix blocked | PASS |
| T11 | Invalid clip range blocked | PASS |
| T12 | FBX export | PASS |
| T13 | Clip-name sanitization | PASS |
| T14 | Temporary skeleton cleanup | PASS |
| T15 | JSON report generation | PASS |

## Important scope note

This repository packaging step does not constitute a new Maya integration test. The functional validation above is the historical validation evidence for the v0.1.0 baseline.

The next development version must be revalidated in Maya before it is described as functionally validated.
