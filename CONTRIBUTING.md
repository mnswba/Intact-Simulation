# Contributing

Start with [installation](docs/install.md) and [architecture](docs/architecture.md). Keep pull requests focused and describe the concrete behavior change and validation. Do not commit personal CAD projects, access tokens, runtime binaries, browser profiles, `.env` files or generated `outputs/` artifacts.

## Development checks

```bash
uv sync --project backend --extra cad --extra dev --frozen
uv run --project backend --extra cad --extra dev --frozen python -m pytest backend/tests -q
npm ci
npm test
node scripts/build-plugin-viewer.mjs
```

The full CAD suite requires Linux bubblewrap and a working user namespace. Structured feature tests additionally need the installed FreeCAD runtime. Engineering tests need the native meshing libraries. Snapshot/browser tests require Playwright Chromium and OS libraries. Older scripts under `scripts/audit/` record particular release/development environments and may require path/version changes; they are not the portable CI entry point.

For a small change, run the relevant tests first. Rebuild `backend/intact_backend/viewer.js` after editing viewer modules. Keep source modules and their distributed bundle together. Use `python models/run.py NAME` from the prepared environment to verify example exports; add dimensions/volume checks that can catch wrong geometry.

## Design rules

Preserve unrelated parts and revision history. Check current model/artifact identity before editing. Do not silently resolve ambiguous face references. Keep generated Python inside OS isolation and use workers for heavy kernels/solvers. Never replace measured solver outputs with AI estimates or weaken requirements to hide failures. Explain unsupported or sampled results in the UI and documentation.

## Issues and examples

Bug reports should include a minimal reproducible model script, parameters, expected/actual results, host/client versions and redacted errors. Please remove personal paths, private model data and tokenized viewer URLs. Add original demonstration programs to `models/` with numeric parameters in `catalog.json` and an expected check in `models/README.md`.

The repository's workflow resembles text-to-cad's separation of plugins, skills, examples and tests, but the projects are independent. Preserve attribution and dependency notices when importing any external code. Contributions to original Intact files use the repository's Apache-2.0 license; third-party files retain their existing notices.
