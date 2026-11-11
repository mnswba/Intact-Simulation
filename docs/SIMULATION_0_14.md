# Simulation workspace — v0.14.0

The **Design** tab retains the existing modeling workspace, exports, appearance, annotation, inspection and revision workflows. **Simulation** holds independent study definitions and results; solving or playing motion does not create a design revision. Returning to Design restores its camera and display preferences. Existing saved models are preserved.

## Mechanical Analysis

Choose a native solid and one of:

- **Steady-state thermal:** isotropic conductivity, volumetric heating, temperature (K), inward-positive heat flux (W/m²), convection coefficient and ambient temperature. Unassigned faces are insulated.
- **Static stress / displacement:** isotropic Young’s modulus and Poisson ratio, density/gravity, fixed supports, prescribed component displacements (mm), total face force (N), or inward-positive pressure (Pa). Supports must constrain all six rigid-body modes. Results include displacement magnitude/components, reaction forces, element-average peak von Mises stress and a volume-weighted nodal stress display.
- **Creeping-flow CFD:** incompressible Stokes with pressure-traction inlet, zero-traction outlet and no-slip walls. This is only valid at very low Reynolds number; the conservative acceptance bound is Re ≤ 0.1. General vehicle aerodynamics is outside this solver.

The default thermal setup prescribes temperatures at opposite axis-end planes. Default structural loading fixes the low end and applies a total force to the high end. **Adding custom conditions replaces these defaults**. Select a condition’s axis end, or pick native faces in the viewer (Ctrl/Cmd-click for multiple selection) and click **Use selected faces**. Conditions on an older CAD artifact cannot run against new geometry. Missing or ambiguous face mappings fail explicitly.

Material values are representative inputs, not certified material properties. Supply values for the actual material and temperature range. Use absolute temperatures in K, SI material/load values, and mm for CAD geometry and prescribed displacements.

Use **Advanced settings → Mesh & accuracy** to adjust refinement if needed, then **Run analysis**. Run saves the setup automatically. Jobs run in isolated workers; their status and Cancel controls appear below. Open a result to see scalar fields and their blue-to-red minimum/maximum legend. Structural displacement magnification is a display option only. Download `results.csv`, `results.vtu` or `report.json` for numerical data.

The solver checks residual and conservation, compares mesh-refinement metrics and flags invalid strain/flow regimes. Stress refinement is reported separately: displacement convergence does not certify a local stress peak. Nodal stress colors are averaged values; use the reported element peak and stress convergence for interpretation. This is bounded single-solid linear analysis, not contact, plasticity, buckling, transient heat transfer, radiation, turbulence or coupled multiphysics.

Mesh limits: 18,000 tetrahedra / 6,000 vertices; Stokes has a separate 24,000 mixed-DOF limit. Increase mesh size if a limit is exceeded. Unconverged results remain available but must not be described as verified.

## Virtual Analysis

Choose **Rigid-body dynamics** for PyBullet gravity, motors and contact, or **Prescribed motion / gait preview** for explicit trajectories.

1. Assign a mass and friction to every CAD component. Mark stationary root bodies fixed. Set ground elevation and gravity as appropriate. Root velocities use mm/s and deg/s.
2. Create joints between separate components: fixed, hinge, continuous wheel or slider. Set the CAD-space pivot, axis, limits and initial state. A child has one parent; cycles are rejected.
3. Select position, velocity, sine/gait or torque/force drive. Angular coordinates use degrees, sliders use mm, and motor effort is N m or N. A continuous wheel velocity drives a vehicle only when the wheel orientation, mass, ground contact and friction are physically suitable. The software does not infer or certify a vehicle controller.
4. For a robot/machine cycle, set sine amplitude, frequency and phase on the relevant joints. Prescribed motion can show a walking sequence but does not predict balance. Dynamically stable walking needs a suitable controller and physical model, which this version does not automatically synthesize.
5. Run, open the result, then play/pause or scrub frames. Joint positions/velocities, motor effort and contact data are recorded. Download trajectory/joint CSV files, the report, or a ZIP containing the generated URDF rig, collision meshes and settings.

Dynamics approximates each part with a convex hull or bounding box. Holes and concave contact surfaces are not retained by these approximations. Default inertia uses the component bounding box and supplied mass. **Advanced study settings** accepts explicit center of mass and physical inertia tensor `[Ixx,Iyy,Izz,Ixy,Ixz,Iyz]` in kg m²; the tensor is validated. Virtual Analysis is not flexible-body stress analysis or a stability certificate. Kinematic contact queries do not represent predicted contact forces; motor effort is null. Position targets ramp from the initial value over the preview duration.

Runs use a 240 Hz internal step, at most 10 seconds and 600 recorded intervals, with a bounded total body-pose recording budget. Separate isolated engineering jobs have concurrency and timeout limits.

## Ask AI

Click **Ask AI** in Simulation; the setup is saved automatically. The Ask AI panel opens in **Simulate · preserve Design** mode with a study-aware request. Describe additional needs, then click Ask AI. In a compatible ChatGPT viewer, review/send the native annotation and reply in the conversation. Outside that viewer, the existing locally signed-in scoped task workflow is used. No separate model API account is required.

AI tools:

- `get_simulation_workspace(model_id)` reads study definitions, part IDs, revision identity and compact job/report summaries.
- `configure_simulation(model_id, operation, settings)` validates/saves `simulate` or `motion` settings, with matching `source_revision` and `source_artifact`.
- `run_3d_simulation` and `run_virtual_analysis` execute their typed schemas synchronously.
- `submit_engineering_job(operation='simulate'|'motion', ...)`, `get_engineering_job`, and `cancel_engineering_job` support background work.

AI must explain missing physical inputs or ask for clarification; it must not invent numerical results. Simulation-mode scoped tasks cannot change CAD or submit design-mutating jobs. Native conversational tools follow the same instruction in the plugin skill. Creating a new CAD revision requires a separate design request.

A stale study can be replaced with **Advanced settings → Reset study**. This clears its local definition and result display; prior exported results remain saved on disk.
