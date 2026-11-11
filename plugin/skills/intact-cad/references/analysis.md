# Implemented simulation scope

Use `run_3d_simulation` for supported native-solid steady conduction, linear elasticity and creeping-flow Stokes. Read [engineering tool contracts](priority23.md) before preparing a study. Establish materials, loads, geometry, units and boundary conditions; inspect mesh quality and convergence evidence. Unsupported turbulent/inertial CFD, nonlinear/contact mechanics and multiphysics remain unavailable.

The older `analyze_reference` MCP tool was removed in 0.12.2. Reduced beam/fin solvers remain internal numerical benchmarks and optional legacy HTTP functionality; do not call them as a public MCP tool or attach their results to arbitrary geometry.

The compact viewer omits manual engineering panels. Read `engineering_evidence`, `get_engineering_job` and returned report/VTU/PDF paths through the AI conversation; use `cancel_engineering_job` to stop a job. Preserve revision/artifact provenance and label stale results. Representative material constants are not certified supplier data.
