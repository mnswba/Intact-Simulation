# Intact Simulation: all 65 tools

Verified against the running **0.20.0** plugin's `list_commands` response. These are callable software operations, not 65 separate apps or 65 guaranteed installed engines. ChatGPT chooses and combines them from a user's design request; users do not need to memorize their names.

**Availability:** Windows native CAD and FreeCAD are ready on the development laptop. Optional PicoGK is not installed there and currently uses a separate Linux-only runtime. A tool's presence does not prove its optional dependencies are available. Check `status` before use.

## Discovery and model history (7)

| Tool | Purpose |
| --- | --- |
| `status` | Check runtime version, CAD readiness, exports and supported analysis. |
| `list_commands` | List the tools available to the current task. |
| `describe_command` | Read a tool's exact inputs and description. |
| `list_models` | List locally saved models. |
| `get_model` | Read a model or preview a saved revision. |
| `revisions` | List saved design revisions. |
| `restore_revision` | Restore a previous design as a new revision. |

## CAD creation, editing and import (7)

| Tool | Purpose |
| --- | --- |
| `build_model` | Create or edit native CAD using a parametric Python build program. |
| `update_parameters` | Change numeric parameters and rebuild while preserving unrelated geometry. |
| `build_freeform` | Loft closed B-spline sections into native CAD. |
| `build_sheet_metal` | Create a supported single bend and its neutral-axis flat blank. |
| `import_cad` | Import STEP/STP geometry, assembly parts and native topology. |
| `import_project` | Import and rebuild an Intact project JSON. |
| `reconstruct_geometry` | Build bounded geometry from calibrated silhouettes or import a closed scan mesh. |

## Requirements, sketches and features (8)

| Tool | Purpose |
| --- | --- |
| `set_design_requirements` | Save explicit acceptance criteria and engineering assumptions. |
| `get_design_requirements` | Read the saved requirements and accuracy settings. |
| `create_sketch` | Create a named sketch with line, circle or arc geometry. |
| `set_sketch_constraints` | Set dimensions and geometric constraints without silently changing saved solids. |
| `solve_sketch` | Use FreeCAD to solve constraints and report remaining degrees of freedom. |
| `get_feature_tree` | Read the explicit feature graph and its rebuild diagnostics. |
| `edit_feature_tree` | Edit supported extrude, revolve, hole, fillet, chamfer, pattern and other features. |
| `rebuild_features` | Re-solve and rebuild the saved graph into validated native CAD. |

## Measurements, audit and verification (8)

| Tool | Purpose |
| --- | --- |
| `audit_model` | Read the geometry/export audit and optionally recheck saved requirements. |
| `validate_model` | Independently reopen STEP/STL and compare exports with requested dimensions. |
| `verify_design` | Check saved dimensions, holes, placement, clearance and other supported criteria. |
| `measure_model` | Read measured native volumes, areas, bounds and topology counts. |
| `set_accuracy` | Set bounded tessellation and convergence targets. |
| `check_accuracy` | Measure native tolerances and supported export/convergence error evidence. |
| `resolve_references` | Resolve selected entities to native geometry facts; reject ambiguous references. |
| `bind_reference` | Assign a stable label to a native part, face or edge. |

## Lattices and mesh conversion (6)

| Tool | Purpose |
| --- | --- |
| `build_tpms` | Create one of six bounded sampled TPMS lattice families. |
| `build_lattice_mm` | Create sampled distance-offset lattices with a target wall thickness in millimeters. |
| `refine_lattice` | Refine lattice resolution and compare volume/density convergence. |
| `build_hybrid` | Combine a sampled lattice and a native component as a mesh result. |
| `convert_mesh_to_cad` | Convert a bounded mesh to faceted STEP; does not fit smooth analytic surfaces. |
| `build_picogk_tpms` | Use the optional pinned Linux PicoGK voxel engine when installed; unavailable on the current Windows runtime. |

## Assembly components and appearance (4)

| Tool | Purpose |
| --- | --- |
| `set_assembly_joints` | Pose supported fixed, revolute or slider joints and check this pose for overlap. |
| `component_catalog` | List the limited provenance-bearing nominal screw and bearing envelopes. |
| `insert_component` | Insert a supported catalog component into an assembly. |
| `set_appearance` | Save a component's label, color or material assignment. |

## Viewer and delivery (6)

| Tool | Purpose |
| --- | --- |
| `open_viewer` | Open or reuse the local model viewer. |
| `control_view` | Set camera, section, visibility, explosion and named view bookmarks. |
| `snapshot_model` | Render an actual model image without changing the user's saved camera. |
| `export_model` | Export supported CAD, mesh, scene, source or project formats. |
| `create_presentation` | Create a revision-bound PPTX with rendered views and measured model context. |
| `engineering_drawing` | Create an orthographic reference PDF with native overall dimensions. |

## Configurations and design alternatives (5)

| Tool | Purpose |
| --- | --- |
| `parameter_configuration` | Save, list or delete named parameter sets. |
| `preview_parameters` | Build a disposable parameter preview without committing a CAD revision. |
| `apply_configuration` | Rebuild and commit a selected named configuration with revision guards. |
| `compare_designs` | Compare measured geometry and available evidence across saved alternatives. |
| `optimize_design` | Evaluate a bounded set of parameter candidates; does not guarantee a global optimum. |

## Viewer Ask AI requests (4)

| Tool | Purpose |
| --- | --- |
| `list_edit_requests` | List queued viewer questions/edits and their status. |
| `read_edit_request` | Read the request, selected references and attached images. |
| `respond_to_edit_request` | Return an answer or ask a clarification in the viewer. |
| `apply_edit_request` | Apply a scoped source edit, preserve previous CAD on failure and report its result. |

## Simulation, manufacturing and jobs (10)

| Tool | Purpose |
| --- | --- |
| `configure_simulation` | Save a validated mechanical or virtual study definition. |
| `get_simulation_workspace` | Read study definitions, source identity and job/result summaries. |
| `run_virtual_analysis` | Create prescribed motion previews; does not calculate physical dynamics. |
| `run_3d_simulation` | Run supported conduction, linear elasticity or creeping-flow Stokes studies. |
| `manufacturing_review` | Screen sampled geometry for supported CNC, molding or additive concerns. |
| `measure_mesh_quality` | Measure mesh bounds, volume, watertightness and sampled wall chords. |
| `engineering_evidence` | Read reports and identify evidence stale relative to the current geometry. |
| `submit_engineering_job` | Start a bounded background engineering task. |
| `get_engineering_job` | Read job progress, status and available results. |
| `cancel_engineering_job` | Request job cancellation while preserving completed valid artifacts. |

## Scope and use

- Geometry audit and saved design verification provide measured evidence; they do not certify manufacturing or physical safety.
- Lattice tools generally return sampled meshes. Faceted STEP conversion does not recover smooth parametric CAD.
- Virtual motion is a prescribed animation, separate from physical numerical simulation.
- Physical studies need actual material properties and boundary conditions. Turbulent CFD, nonlinear/contact mechanics and multiphysics remain unavailable.
- Manufacturing screening, reconstruction, freeform modeling and drawings have explicitly bounded domains. Ask `describe_command` for the exact schema and limits.
- Some operations create files or update study/view state without changing the CAD revision. Read the tool contract rather than treating every non-CAD operation as globally side-effect-free.

Example request: **Create a flange, save its acceptance dimensions, verify the exported STEP and show me the model.** ChatGPT can combine `build_model`, requirements/verification, viewer and export tools to complete the workflow.

[Installation](INSTALL_WINDOWS_PRIVATE.md) · [Architecture](architecture.md) · [Verification and known issues](QA_0_20.md)

