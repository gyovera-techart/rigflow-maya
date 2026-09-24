# Contributing to RigFlow Toolkit for Maya

Thank you for your interest in RigFlow.

## Development principles

- Preserve non-destructive behavior.
- Prefer explicit validation over silent assumptions.
- Do not introduce automatic fixes that can alter production rigs without a clearly defined safety model.
- Keep Maya-specific integration separated from pure-Python logic where practical.
- Document behavioral changes and validation evidence.

## Before opening a pull request

1. Run the available Python syntax checks.
2. Test Maya-dependent changes in a supported Autodesk Maya environment.
3. Document the Maya version used for validation.
4. Update `CHANGELOG.md` when behavior changes.
5. Do not commit scene files, generated reports, credentials, tokens, or private production assets.

## Scope of v0.1.0

The v0.1.0 branch is a historical validated baseline. Future feature development should occur in a new version rather than rewriting the baseline implementation.
