# Implemented simulation scope

`analyze_reference` creates a **new matching rectangular reference model** and solves one of two reduced problems:

- `beam`: uniform rectangular cantilever, small linear elastic deflection; force at its free end, fixed base; analytical formula plus 1D beam FEM and convergence/agreement checks.
- `fin`: single rectangular cooling fin, steady 1D conduction, prescribed base heat, ambient convection and insulated tip; analytical formula plus 1D finite-volume field and balance/convergence/agreement checks.

For a real design study, review dimensions, material provenance, load/heat, fixed/insulated faces, ambient, convection and assumptions with the user before `approved=true`. Existing task authorization to run a defined study still applies; do not ask repeatedly for the same approval. Fixed numerical regression fixtures in an explicitly requested software audit are tests, not an engineering design recommendation.

Report `scope=reduced_1d`, assumptions, verification results and warnings. Material constants are representative, not certified supplier data. The reference model must match the solved rectangle. Never attach beam/fin results to an arbitrary imported assembly, generated impeller, pressure vessel or heat sink and imply it received a 3D solve. For bounded 3D steady conduction, linear elasticity and creeping-flow Stokes, use run_3d_simulation and read priority23.md. Multiphysics, contact/nonlinear analysis, turbulent/inertial CFD, resolved boundary-layer models and fatigue are not implemented. A CAD model or an AI narrative cannot establish stresses, temperatures, safety factors or certification for those cases.
