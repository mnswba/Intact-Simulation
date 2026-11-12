# Intact v0.15 — AI simulation and kinematic previews

## Viewer

The selection menu contains Part, Face and Edge. Native browser click counts distinguish double-click (named part) from triple-click (clicked native solid body), independent of the menu. CAD body metadata and revision guards remain available to AI. Presentation and Auto orbit stay accessible in fullscreen. Active previews have fullscreen play/pause, replay, scrubbing and Close controls.

## Virtual Analysis

Virtual Analysis replaces the former rigid-body/PyBullet workflow with kinematic previews. Describe driving, a walking robot or a machine cycle, then use Ask AI. AI inspects the actual stable part IDs, identifies moving components and supplies a `PreviewStudy` to `run_virtual_analysis`. Recognized wheel assemblies can start a driving preview directly. Articulated walking needs separate limb/link parts and explicit pivots; fused geometry does not acquire invented joints. Clarifications remain in ChatGPT and can also be answered in the Simulation response/reply panel.

The supplied `scout-driving-source/src/driving-controller.mjs` is reused, with a bounded 1–16-wheel binding adaptation. Its original eight-second acceleration/cruise/braking/stopped timeline remains intact. At 0.30 m/s the final visual travel is 1.80 m. The native CAD model, its parameters, geometry, revisions and exports are unchanged.

Coordinate contract: preview pivots use assembled **CAD metres, +X forward, +Y left, +Z up**. The display adapter maps these to Intact's mm, Y-up display. Existing part objects are temporarily reparented with identity preserved, and the viewer's existing render loop supplies frame deltas. Play, pause, replay and seek derive poses from timeline time, rather than accumulated wheel spin. Closing the preview restores original parents, child order, local matrices, transforms and camera. Preview stops before rebuilds, model changes, section/explosion changes, downloads/project exports and AI edit annotations. A hidden tab pauses playback, and reduced-motion preference suppresses automatic playback.

Walking and machine joints use prescribed sine trajectories; whole-object translation/rotation are also available. These are **visual kinematic trajectories**, not traction, collision, motor-torque, suspension-force, dynamic-stability or balance predictions. The old dynamics worker and PyBullet dependency have been retired. Saved historical reports are preserved on disk.

## Mechanical Analysis

Enter the intended analysis, material, supports, loads and requested results. The two primary actions are **Ask AI** and **Run Analysis**. There are no manual analysis/material/mesh forms in this section.

AI reads `get_simulation_workspace`, clarifies critical missing physical inputs, then calls `configure_simulation(operation="simulate")` using the existing typed `Simulation` schema. It must copy the user's description exactly into `settings.user_request` and bind the current source revision/artifact. Ask AI prepares/explains the study. Run Analysis executes a matching prepared study; when no matching study exists, it asks AI to prepare and run it. An old default study is never silently substituted for a new description. AI can submit a `simulate` engineering job and inspect its result. Numerical fields, ranges, convergence/residual checks, actual mesh size, CSV and VTU downloads appear in Mechanical Analysis. AI responses and clarification replies also appear there.

The actual numerical domains remain steady isotropic conduction, small-strain linear elasticity and creeping-flow Stokes. Their documented material, support and flow-regime limits still apply. This is not general turbulent CFD, contact/nonlinear FEA or multiphysics.

### Mesh budget recovery

Overly fine requests now receive a geometry-volume-based initial sizing estimate and bounded coarsening retries. Gmsh point-based refinement and boundary-size propagation no longer defeat the requested global size. Limits remain **18,000 tetrahedra / 6,000 vertices**, with a separate Stokes mixed-DOF limit. No native geometry is simplified or changed to fit a budget.

`mesh_adaptation` records requested size, effective size and attempts. The UI shows effective size and whether it was automatically sized. Refined-mesh comparison uses a genuinely finer mesh; when refinement exceeds a budget, convergence stays false and the accepted coarse result remains available. A geometry that still exceeds the budget fails explicitly with an isolation/simplification instruction. Automatic sizing is not an accuracy certificate. `auto_mesh=false` remains available through the typed AI tool when a fixed mesh request is required.

## Optional PicoGK TPMS

Install with:

```bash
python3 scripts/install-picogk.py
# or
python3 scripts/install-chatgpt-plugin.py --with-picogk --windows-home /mnt/c/Users/YOUR_WINDOWS_USER
```

The optional bridge uses official PicoGK **2.4.0-alpha04** because that package supplies the Linux native runtime needed by this installation. It is a pinned **prerelease**, with an exact NuGet package reference and dependency content hashes. The bridge targets .NET 9. It runs headlessly in the existing no-network sandbox; arbitrary C# from an AI is not accepted. `status.picogk` reports readiness, and `build_picogk_tpms` creates a **new** mesh model while preserving prior models. The built-in Intact TPMS engine remains available; no silent fallback masquerades as PicoGK.

Six families are supported: gyroid, Schwarz P, diamond, neovius, lidinoid and split P. Inputs include envelope size, cell size, nominal wall, thickness gradient and voxel size. Validation bounds the sampling domain to four million voxels and requires at least three voxels across the thinnest nominal wall. PicoGK evaluates an implicit shell using a local-gradient distance approximation, clips it to the envelope, and exports an actual voxel mesh. The adapter verifies closed positive-volume geometry and a bounded triangle count before importing it into Intact. Reports identify engine, package version, voxel size and approximation scope.

STL/GLB/3MF and the existing mesh scene exports are available. This does **not** produce a smooth analytic STEP surface or certify constant wall thickness. An explicit bounded faceted STEP conversion is a separate operation and may require a coarser mesh.

Upstream: [PicoGK](https://github.com/leap71/PicoGK), [official build/distribution source](https://github.com/leap71/PicoGK.Legacy). PicoGK retains Apache-2.0 and its dependencies' notices. No native binaries or user SCOUT geometry are committed to this repository.

## Verification

- Exact scene graph, transforms, child order, geometry-buffer and identity restoration under non-identity display transforms; deterministic seek/replay and prescribed walking joints.
- Browser test on an isolated copy of the existing **110-component SCOUT CAD**, not a replacement primitive: actual wheel IDs, eight-second timeline, ~1.80 m travel, replay/scrubbing/fullscreen controls and restoration. Original user model records remain untouched.
- Actual description-matched thermal job with an initially excessive mesh request: automatic sizing, valid node/cell budget, 300–350 K patch solution, real result overlay and numerical metadata.
- Existing independent thermal, elastic and Stokes benchmarks; selected-face, reaction/load, revision and Ask AI permission regressions.
- Real sandboxed PicoGK gyroid and Schwarz-P meshes with positive volume, closed geometry and GLB exports. STEP is rejected for these mesh models unless explicitly converted.
- Native annotation behavior is exercised with a browser API mock; no claim is made that an unattended live ChatGPT conversation supplied material data or ran these tests.

Useful commands:

```bash
node --experimental-strip-types --test tests/*.test.ts
PYTHONPATH=backend python -m pytest backend/tests/test_ai_simulation_015.py backend/tests/test_simulation_workspace.py backend/tests/test_ask_ai.py -q
PYTHONPATH=backend python -m pytest backend/tests/test_priority23.py -k pde_benchmarks -q
python3 scripts/check-publication.py
```
