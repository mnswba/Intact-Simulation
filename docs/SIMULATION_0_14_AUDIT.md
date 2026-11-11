# v0.14 Simulation verification

Tests use disposable projects, not user CAD. Design revision records are compared before/after solves. Installed user-project records are also hash-checked across installation.

## Numerical checks

- Thermal rod, conductivity 200 W/(m K), end flux 10,000 W/m² and 300 K opposite boundary: numerical range **300–301 K**, total input **1 W**, checked against the independent 1D solution.
- Flux/convection rod: h=100 W/(m² K), ambient 300 K, same flux: numerical range **400–401 K**.
- Native-face temperature selections: match the intended opposite B-rep faces, enforce 300/350 K, reject stale revision guards.
- Uniform tensile stress patch, E=1 GPa, nu=0, length 20 mm, area 100 mm², force 100 N: displacement **0.02 mm**, von Mises stress **1 MPa**, balanced reactions, refined stress comparison.
- Pressure and prescribed-displacement patches: compare numerical displacement and stress to independent axial solutions; reject unsupported rigid-body motion.
- Existing steady thermal, linear-elastic and creeping-flow benchmarks remain passing.
- Prescribed root translation: **100 mm in 1 s**. Gravity-only body falls with negative Z displacement; no CAD revisions change.
- Hinge pivot: check final rotation and part placement, initial position, prescribed velocity and null kinematic effort. Reject cyclic rigs.
- Four-wheel motor-driven vehicle with gravity/contact: **34.52598 mm** forward chassis displacement in 1 s, four active joints and up to **16 contact points**. This is one configured vehicle benchmark, not validation of every vehicle/controller.

## Interface and integration

The real browser harness runs background solver jobs, opens actual result fields, downloads CSV data and plays recorded motion. It checks simulation Ask AI intent with a mocked native annotation API, checks its persisted request, and restores Design camera/view/revision state. A second browser audit checks actual face picking/attachment, relevant per-condition inputs, stress fields and displacement display scale, full-screen return, simulation tutorial topics and a narrow layout.

Native annotation API acceptance in these tests is a contract mock. It does not claim that a live ChatGPT desktop conversation or an autonomous robot controller was exercised. No hosted AI numerical estimates replace solver outputs.

Regression coverage: **46 distinct backend tests**, **31 JavaScript tests**, two browser workflow groups, source publication validation and fresh MCP schema registration (**56 tools**). Additional installed-runtime checks enumerate tools and run both thermal and motion tools through the real stdio MCP transport.

Commands (prepared runtime and Linux sandbox prerequisites apply):

```bash
python -m pytest backend/tests/test_simulation_workspace.py backend/tests/test_ask_ai.py -q
python -m pytest backend/tests/test_priority23.py -k 'pde_benchmarks or job' -q
python -m pytest backend/tests/test_chat_handoff.py backend/tests/test_recent_models.py backend/tests/test_project_workspace.py -q
npm test
node scripts/build-plugin-viewer.mjs
node scripts/test-simulation-viewer.mjs DISPOSABLE_ROD_MODEL_BASE_URL
node scripts/test-simulation-boundaries.mjs DISPOSABLE_ROD_MODEL_BASE_URL
python3 scripts/check-publication.py
```

Set `PYTHONPATH=backend` when the package is not installed; `INTACT_PLAYWRIGHT_MODULE` can point to the local Playwright module. The browser test expects a disposable single-part model named `rod`; its base URL ends in `/` before `view`. It intentionally creates engineering jobs/studies and a saved mocked-annotation request.

See [scope, numerical limits and usage](SIMULATION_0_14.md). Passing benchmarks does not certify arbitrary geometry, material data, stress singularities, robot stability or manufacturing safety.
