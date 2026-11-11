# Intact Simulation 0.12 — priority 2/3 engineering tools

This release adds working, bounded implementations across the priority-2 and priority-3 categories. It does **not** complete every advanced capability described in the original roadmap. The table distinguishes shipped tools from remaining work; testing cannot establish universal reliability for arbitrary models or certify an engineering design.

## Shipped scope and remaining work

| Roadmap item | Working implementation | Remaining advanced scope |
| --- | --- | --- |
| Native CAD + implicit geometry | Double-precision Manifold union, difference and intersection between native tessellations and distance-offset lattices; other assembly parts preserved; export precision checked before commit | Smooth native/implicit transition blending and exact hybrid B-rep operations |
| TPMS thickness in mm | Sampled Euclidean distance-transform offsets, gradients, grid uncertainty, exported-mesh thickness chords | Certified global minimum/maximum wall thickness and exact continuous offsets |
| Adaptive sampling/convergence | Automatic global resolution refinement, volume/density comparison, explicit non-convergence and sample budgets | Spatial/local octree refinement |
| TPMS → CAD | Real sewn planar B-rep STEP, bounded face count, reopening/volume checks, separate native model | Smooth fitted analytic surfaces, compact editable TPMS feature recovery |
| Assembly joints | Fixed/revolute/slider chains, limits, rest placements, parameter edits and all pairwise overlap tests for <=11 parts | Dynamics, general mate solving and continuous swept collision detection |
| Freeform surfaces | Native periodic spline-section lofts; smooth/ruled choice; editable source/control points | Arbitrary patch editing and explicit G2 continuity constraints |
| Alternatives/comparison | Separate parameter candidates, measured size/volume, explicitly assumed mass, current verification reports | Automatic creativity/quality rankings without defined measurable criteria |
| Images/drawings/scans | Calibrated outline extrusion, 2–3 orthographic silhouette visual hulls, real STL-backed scan projects and portable/source exports; measured/inferred data labeled | Perspective photogrammetry, drawing-symbol interpretation and recovered hidden features |
| Standard components | Five ISO4762 screw envelopes and SKF608 envelope with dimension sources; existing supplier STEP import | Broad live supplier library, motor/connector catalog, modeled threads/bearing internals |
| Manufacturing | Sampled CNC visibility, mold draft and wall screening; measured orthographic reference PDFs; single cylindrical sheet bend and K-factor blank | Full CAM, arbitrary sheet unfolding, springback, production GD&T/hidden-line drawings or manufacturing certification |
| 3D simulation | Actual Gmsh tetrahedra + scikit-fem steady conduction, linear elasticity and creeping-flow Stokes; residual/conservation, mesh refinement, material/load records, VTU and scalar viewer | Inertial/turbulent CFD, nonlinear/contact mechanics, conjugate heat transfer and multiphysics |
| Optimization/graded lattices | Bounded parameter sweeps, exposed lattice gradients, geometric objectives or converged native-domain physics objectives; saved requirements and physical constraints respected | General topology optimization and automatic high-resolution graded-lattice multiphysics optimization |
| Larger models | Durable detached jobs, cancellation, progress, fixed resource budgets, selective feature-node caching, lightweight field summaries | Distributed/HPC processing, unbounded models and locally streamed level-of-detail meshing |

The plugin exposes **53 tools**. Complete argument contracts are in `plugin/skills/intact-cad/references/priority23.md`. Existing priority-1 functions and direct Ask AI remain available. Ask AI's model scope still prevents unrelated imports/new projects; the full ordinary ChatGPT plugin exposes creation/comparison workflows.

## Engineering evidence

`run_3d_simulation` needs a single connected native solid. End boundary planes are the selected axis extrema. For Stokes, the solid must represent the **fluid domain**, not metal hardware. CAD mm are converted to SI for assembly. Material constants, loads, prescribed temperatures, pressure and viscosity are recorded in the report; defaults are representative inputs, not supplier-certified properties.

A solve becomes `verified` only when its numerical checks, requested two-resolution metric comparison and applicable small-strain/creeping-flow regime checks pass. This is scoped numerical verification, not experimental validation or safety certification. Thermal convergence uses volume-average temperature, structural convergence maximum displacement, and Stokes convergence outlet flow. Reported stress maxima require their own stress convergence study.

The viewer's **Engineering results & jobs** panel shows scalar fields, units, input values, convergence state, PDF/VTU downloads and cancellation. Results retain their originating geometry artifact. Changing geometry marks older results stale and disables their overlay. Geometry updates and source exports keep immutable history behavior.

## Failures found and fixed

The audit exposed and corrected rigid-transform construction, disconnected-shell sewing, Gmsh/OCP runtime mixing, empty native intersections, NumPy Boolean serialization, task status races and float32 export degeneracies at coincident native/lattice intersections. Hybrid outputs are tested at STL/preview precision before committing. If a tiny alignment perturbation is needed, its actual XYZ mm values are recorded; this remains approximate mesh modeling. Unrepresentable results fail rather than being saved as verified designs.

Native glTF files intentionally split shading normals at CAD seams. The export audit welds positions while ignoring normal/texture seams before testing closure; it does not modify the delivered file. This corrects a test-harness assumption rather than disguising a geometry repair. Hybrid STL topology failures were genuine and required the separate boolean/export fix above.

## Audit artifacts

`outputs/priority23-audit/` contains the complete backend JUnit results, focused regressions, 50-case geometry/export matrix, all-tool MCP audit, browser reports/screenshots, installation hashes and live AI test. The 50 cases span all six distance-offset TPMS families, native/mesh booleans, six catalog components, spline lofts, three-axis joints and different sheet bend angles. STL, GLB and 3MF are reopened and checked. Independent PDE benchmarks compare a linear temperature field, axial displacement and square-duct flow against analytic solutions.

This evaluation improves software and instructions; it does not train foundation-model weights. Windows desktop GUI control is not available in this executor. Linux and Windows plugin files and WSL launch configuration are checked separately.

See [open-source runtime inventory](PRIORITY23_OPEN_SOURCE.md). No separate AI provider, LiteLLM setup, public deployment or public-directory submission is added by this release.

## Final measured results

- **153 distinct backend tests passed:** full 151-test regression suite plus the focused 45-test final suite (overlapping tests counted once).
- **50/50 geometry/export stress cases passed**, reopening STL/GLB/3MF.
- **53/53 installed MCP tools passed**, including error/recovery paths and both client protocol modes.
- **9/9 independent PDE benchmarks passed** across all three CAD axes: exact linear conduction, axial displacement and square-duct flow.
- **20 browser check groups passed**, with no browser errors, covering old viewer controls, priority-1 controls, installed scalar results, downloads, stale-result blocking, retained study types and cancellation.
- **44 runtime files and six plugin source/cache copies matched** the repository.
- A fresh signed-in AI client completed the new 3D-study/lattice workflow in **83.76 seconds**. One string-valued force vector was rejected and corrected. Independent review measured **1.728%** difference between the fine 3D displacement and the axial formula; the fully clamped 3D end conditions differ from the ideal axial reference.

Restart ChatGPT, enable Intact Simulation and start a new chat. In the viewer, open **Engineering results & jobs** and choose a field. The three tutorial studies are independent load cases, not coupled multiphysics.

Scalar overlays show the assembled domain surface. CAD section/explosion/render-mode controls are disabled while a field is displayed; **Show CAD** restores them. Download VTU for volumetric cutting and detailed postprocessing.
