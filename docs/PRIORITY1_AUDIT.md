# Intact Simulation 0.10 — priority 1

The six priority-1 areas now have executable implementations: saved design requirements, real constraint-based sketches, an explicit editable feature graph, named geometry references, design-specific checks of exported geometry, and requested accuracy/mesh convergence controls. ChatGPT remains the AI interface. No LiteLLM or separate model service is required.

## What changed

- **Requirements:** source intent, assumptions, numeric parameters and typed acceptance checks persist with the design. A new design can begin as an empty draft rather than an unrelated solid.
- **Sketches:** FreeCAD 1.1.4 solves lines, circles and arcs with geometric and dimensional constraints. Tools expose actual degrees of freedom, conflicts and redundancy. Rebuilding normally requires fully constrained sketches.
- **Feature history:** extrusion, revolution, hole cuts, fillets, chamfers, booleans, linear patterns and transforms have explicit IDs/dependencies, suppression and editable parameters. Failed rebuilds preserve the last valid graph/solid. Existing arbitrary Python CAD remains available for other modeling operations.
- **References:** named handles retain immutable-artifact identity, follow supported hole features or unique geometric signatures, and reject missing or ambiguous matches. They do not promise universal topological naming.
- **Verification:** exported STEP checks cover bounds, part counts, hole count/diameter/axis/centers/cylindrical depth/through state, part clearance and interference volume. Missing or unsupported criteria remain unverified. Finite wall samples are explicitly distinguished from a proof of global minimum thickness.
- **Accuracy:** requested numerical/meshing targets are stored and applied. Checks measure kernel tolerances, STL volume approximation, and two-resolution mesh volume/area changes. A refinement limit produces an unverified result. These measurements do not certify manufacturing accuracy or a global surface-error bound.

The viewer now includes solved sketch previews, linked dimension editing, feature suppression/property editing, rebuild and verification controls, accuracy targets/results and native document download. Historical feature controls are read-only.

Structured designs export STEP, STL, GLB, 3MF, project JSON, standalone FreeCAD Python and a native FCStd document. The FCStd file contains solved sketches and recorded PartDesign feature steps; Intact's JSON graph is the parametric rebuilding driver. The standalone Python export was actually executed without its original STEP asset.

## Verification evidence

Final result: **97 distinct backend checks passed** (96-test full suite plus the added refinement-floor regression); the final 17 native workflow tests were also rerun successfully after the reference guard update. All **33 installed tools**, **5 structured viewer groups** and **7 existing viewer groups** passed. Installation hashes match all **36 runtime files** and all **6 Linux/Windows plugin source/cache copies**. The fresh local AI client completed its real design/edit/verify/export workflow in 94.74 seconds; an independent analytic-volume and native geometry review passed.

The installed MCP audit exposed a bind_reference keyword mapping error; the dispatcher was fixed, reinstalled and all 33 tools rerun. The live AI client initially sent two malformed sketch requests; validation rejected them, the client corrected them, and the final design passed. These recoveries are retained in the evidence rather than treated as unqualified first-attempt success.

Machine-readable reports and screenshots are in `outputs/priority1-audit/`. Backend tests use real isolated CAD engines. `tools_p1.py` exercises every installed MCP tool through the actual SDK client with PYTHONPATH removed. `viewer_p1.py` and `viewer_controls_p1.py` use Chromium and interact with the rendered application. `host_p1.py` tests a fresh signed-in OpenAI local client with the personal plugin enabled.

The audit includes analytic volume comparisons, real solver conflicts/DoF, diameter-driven rebuilds, through and blind bores, ambiguous selectors, invalid/stale edits, native document and self-contained Python exports, project round trips, interference, wall-sampling limits, accuracy refinement limits, parameter-linked viewer edits and historical revision controls. It is regression testing and instruction improvement, not model-weight training.

The Windows desktop GUI cannot be controlled by this executor. Installed Windows plugin files and WSL launch configuration are checked separately. The fresh client test covers local plugin loading and real tool use, not a click-through of the Windows ChatGPT application.

## Scope

Opaque imported STEP/Python designs do not automatically gain recovered sketches or feature history. Advanced shapes remain available through the existing Python CAD route. TPMS remains sampled mesh geometry; exact TPMS STEP, general CFD, 3D FEA and multiphysics are not added by this release. See [the open-source inventory](PRIORITY1_OPEN_SOURCE.md) and [the structured operation contract](../plugin/skills/intact-cad/references/structured-modeling.md).

To use the installed update, restart ChatGPT, enable **Intact Simulation**, and start a new conversation. Ask for a constrained sketch, named feature history and saved acceptance checks when those are required. Existing model files remain in their original locations.
